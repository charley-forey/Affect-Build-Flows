"""Run the Procore extraction HERE, and land the raw payloads in OneLake.

    python extract_procore_local.py --list                  # the registry, no calls
    python extract_procore_local.py --probe                 # auth + project count only
    python extract_procore_local.py --only projects,vendors # a couple of endpoints
    python extract_procore_local.py --apply                 # all 36, land to OneLake

WHY THIS EXISTS
---------------
`cd_01_extract_procore` is the real, scheduled ingestion and it runs inside Fabric. It needs
Procore credentials, and the only safe way to give a Fabric notebook a credential is Key
Vault - which needs an Azure subscription this tenant does not currently have
(`az account list` reports a tenant-level account only). The alternatives inside Fabric -
a Spark property, a workspace environment variable - are all plaintext-readable by any
workspace member, which is exactly finding F1 in _docs/security-findings.md. Reproducing the
finding we just reported would be an odd way to fix it.

So the split is: the half that needs a secret runs here, where the secret already lives; the
half that needs Spark runs in Fabric, where no secret is needed. Nothing is written to Fabric
except data.

    .env (local)  ->  Procore REST  ->  OneLake Files/_landing/<batch>/*.jsonl
                                                      |
                                     cd_05_land_to_bronze (no credentials)
                                                      v
                                              cd_bronze_procore_* (Delta)

This is a bridge, not the destination. When a subscription lands: `setup_keyvault.py --apply`,
point `PROCORE_KEYVAULT_URL` at the vault, and `cd_01_extract_procore` takes over on a
schedule. The landing notebook keeps working either way, because it only ever reads files.

The extractor itself is NOT reimplemented here - `src/procore/procore_extract.py` is imported
whole, the same module `deploy_ingestion.py` uploads to `Files/lib/`. Auth, pagination, the
v2.0 company-header rule and the 429 `Retry-After` handling are shared, so this runner cannot
drift from what Fabric will eventually do.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deploy as dp  # noqa: E402

HERE = Path(__file__).resolve().parent
CHARLEY_DEV = HERE.parent
REPO = CHARLEY_DEV.parent.parent
ENDPOINTS_YML = CHARLEY_DEV / "01-ingestion" / "Procore" / "config" / "endpoints.yml"

DFS = "https://onelake.dfs.fabric.microsoft.com"
PRODUCTION = "https://api.procore.com"


def find_env() -> Path | None:
    for directory in [REPO, *REPO.parents]:
        candidate = directory / ".env"
        if candidate.is_file():
            return candidate
    return None


def load_env() -> None:
    """Populate os.environ so the shared extractor's get_secret() finds the values.

    setdefault, not overwrite: a real environment variable should always beat a file.
    """
    env_file = find_env()
    if not env_file:
        raise SystemExit("no .env found - the extractor needs PROCORE_CLIENT_ID/SECRET/COMPANY_ID")
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    # The extractor defaults to sandbox.procore.com. Affect's data is in production, and a
    # silent sandbox run would land a convincing set of empty tables.
    os.environ.setdefault("PROCORE_BASE_URL", PRODUCTION)


def import_extractor():
    """The shared extractor plus charley-dev's scope extension.

    Two modules on purpose. `procore_extract` owns auth, pagination, retry and the bronze
    row shape and is shared with Fabric verbatim. `procore_scope` adds `scope: parent`
    ALONGSIDE it rather than forking it - its Endpoint is duck-compatible with the helpers
    that matter (`needs_company_header`, `key`, `name`, `incremental`), so both can be used
    in one loop without either knowing about the other.
    """
    sys.path.insert(0, str(REPO / "src" / "procore"))
    sys.path.insert(0, str(CHARLEY_DEV / "00-platform" / "lib"))
    import procore_extract  # type: ignore[import-not-found]
    import procore_scope  # type: ignore[import-not-found]

    return procore_extract, procore_scope


# ------------------------------------------------------------------ OneLake landing

def storage_token() -> str:
    result = subprocess.run(
        [dp.az_path(), "account", "get-access-token",
         "--resource", "https://storage.azure.com",
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"az storage token failed - run `az login`.\n{result.stderr.strip()}")
    return result.stdout.strip()


def _dfs(method: str, url: str, tok: str, body: bytes | None = None) -> int:
    request = urllib.request.Request(url, method=method, data=body,
                                     headers={"Authorization": f"Bearer {tok}"})
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"{method} {url.split('?')[0]} -> {exc.code}: "
                           f"{exc.read().decode()[:300]}") from exc


def put_file(lakehouse_id: str, rel_path: str, content: bytes, tok: str) -> None:
    """Create-append-flush, the three-step ADLS Gen2 write OneLake speaks.

    ponytail: single append, so one file must fit one request. The largest endpoint here is
    a few MB. Chunk the append loop if an endpoint ever outgrows that.
    """
    base = f"{DFS}/{dp.WORKSPACE_ID}/{lakehouse_id}/{rel_path}"
    _dfs("PUT", f"{base}?resource=file", tok)
    if content:
        _dfs("PATCH", f"{base}?action=append&position=0", tok, content)
    _dfs("PATCH", f"{base}?action=flush&position={len(content)}", tok)


# ------------------------------------------------------------------ pull one endpoint

def pull(px, ps, session, settings, token, endpoint, project_ids: list[int],
         harvested: dict[str, list[dict]]) -> tuple[list[dict], list[dict]]:
    """Pull one endpoint across its scope. Returns (bronze rows, raw records).

    The raw records come back too so a `scope: parent` child can take its ids from them.
    Everything except path expansion is the shared extractor, unchanged.
    """
    headers = px.build_headers(token, settings.company_id, endpoint)
    params = px.watermark_params(endpoint, None)   # None = full pull; watermarks live in Fabric
    if endpoint.scope == "company":
        params = {**params, "company_id": settings.company_id}

    parent_ids = None
    if endpoint.parent:
        parent_ids = ps.collect_parent_ids(
            harvested.get(endpoint.parent.endpoint, []), endpoint.parent)

    ingested_at = datetime.now(timezone.utc)
    rows, raw, skipped = [], [], 0
    for path, project_id in ps.expand_paths(endpoint, settings.company_id,
                                            project_ids, parent_ids):
        try:
            for record in px.iter_records(session, settings.base_url, path, headers,
                                          params=params):
                raw.append(record)
                rows.append(px.to_bronze_row(record, endpoint, project_id, ingested_at))
        except Exception as exc:                                    # noqa: BLE001
            # A 404/403 on ONE project means that project does not have the tool enabled -
            # normal across a 19-project portfolio, and not a reason to lose the other 18.
            # Anything else is a real failure and is re-raised.
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status not in (403, 404):
                raise
            skipped += 1
    if skipped:
        print(f"      ({skipped} project(s) skipped - tool not enabled)")
    return rows, raw


# ------------------------------------------------------------------ run

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="land the results in OneLake")
    parser.add_argument("--list", action="store_true", help="show the registry, call nothing")
    parser.add_argument("--probe", action="store_true", help="auth + project count only")
    parser.add_argument("--only", default="", help="comma-separated endpoint names")
    parser.add_argument("--out", default="", help="also write the .jsonl files to this dir")
    args = parser.parse_args()

    load_env()
    px, ps = import_extractor()
    endpoints = ps.load_registry(str(ENDPOINTS_YML))
    ps.validate_registry(endpoints)          # duplicate names, missing parents, cycles
    endpoints = ps.resolution_order(endpoints)   # parents before the children that need them

    if args.only:
        wanted = {n.strip() for n in args.only.split(",") if n.strip()}
        unknown = wanted - {e.name for e in endpoints}
        if unknown:
            print(f"unknown endpoint(s): {', '.join(sorted(unknown))}")
            return 1
        endpoints = [e for e in endpoints if e.name in wanted]

    if args.list:
        print(f"{len(endpoints)} endpoint(s) in {ENDPOINTS_YML.name}, in resolution order:\n")
        for e in endpoints:
            inc = e.incremental or "full reload"
            src = f"<- {e.parent.endpoint}.{e.parent.field}" if e.parent else ""
            print(f"  {e.name:<32} {e.scope:<8} v{e.api_version:<4} {inc:<22} {src}")
        return 0

    import requests

    settings = px.load_settings()
    session = requests.Session()
    print(f"host {settings.base_url}  company {settings.company_id}")

    token = px.fetch_token(settings, session)
    print(f"  authenticated ({len(token)} char token)")

    projects = list(px.iter_active_projects(session, settings, token))
    project_ids = [p["id"] for p in projects]
    print(f"  {len(project_ids)} active project(s)")

    if args.probe:
        for p in projects[:8]:
            print(f"      {p['id']}  {str(p.get('name'))[:50]}")
        return 0

    batch = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lakehouse_id = json.loads((HERE / "fabric_ids.json").read_text())["CD_Bronze_Lakehouse"]["id"]
    tok = storage_token() if args.apply else ""
    outdir = Path(args.out) if args.out else None
    if outdir:
        outdir.mkdir(parents=True, exist_ok=True)

    print(f"\nbatch {batch} -> {'OneLake Files/_landing' if args.apply else 'DRY RUN'}")
    manifest, failures, total = [], [], 0

    # Raw records per endpoint, so a scope:parent child can read its parent's ids. Kept only
    # for endpoints something actually depends on - holding all 36 payloads in memory would
    # be wasteful and pointless.
    needed_as_parent = {e.parent.endpoint for e in endpoints if e.parent}
    harvested: dict[str, list[dict]] = {}

    for endpoint in endpoints:
        started = time.time()
        try:
            rows, raw = pull(px, ps, session, settings, token, endpoint,
                             project_ids, harvested)
            if endpoint.name in needed_as_parent:
                harvested[endpoint.name] = raw
        except Exception as exc:                                    # noqa: BLE001
            # One endpoint failing must not abandon the other 35 - a partial landing is
            # useful and re-runnable; an aborted run is neither.
            note = f"{type(exc).__name__}: {str(exc)[:160]}"
            print(f"  {endpoint.name:<32} FAILED  {note}")
            failures.append({"endpoint": endpoint.name, "error": note})
            continue

        for row in rows:
            row["_batch_id"] = batch
            row["_ingested_at"] = row["_ingested_at"].isoformat()

        body = "\n".join(json.dumps(r, default=str) for r in rows).encode("utf-8")
        elapsed = time.time() - started
        print(f"  {endpoint.name:<32} {len(rows):>7} rows  {len(body) / 1024:>8.1f} KB  "
              f"{elapsed:>5.1f}s")

        if outdir:
            (outdir / f"{endpoint.bronze_table}.jsonl").write_bytes(body)
        if args.apply:
            put_file(lakehouse_id,
                     f"Files/_landing/{batch}/{endpoint.bronze_table}.jsonl", body, tok)

        manifest.append({"endpoint": endpoint.name, "table": endpoint.bronze_table,
                         "rows": len(rows), "bytes": len(body), "key": endpoint.key})
        total += len(rows)

    summary = {"batch": batch, "host": settings.base_url, "company": settings.company_id,
               "projects": len(project_ids), "total_rows": total,
               "endpoints": manifest, "failures": failures}
    blob = json.dumps(summary, indent=1).encode("utf-8")
    if outdir:
        (outdir / "_manifest.json").write_bytes(blob)
    if args.apply:
        put_file(lakehouse_id, f"Files/_landing/{batch}/_manifest.json", blob, tok)

    print(f"\n{total} row(s) across {len(manifest)} endpoint(s); {len(failures)} failed")
    if failures:
        for f in failures:
            print(f"  FAILED {f['endpoint']}: {f['error']}")
    if not args.apply:
        print("\nDRY RUN - nothing landed. Re-run with --apply.")
        return 0

    print(f"\nlanded to Files/_landing/{batch}/ in CD_Bronze_Lakehouse")
    print("Next: python deploy_landing.py --apply    (merges the files into cd_bronze_*)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
