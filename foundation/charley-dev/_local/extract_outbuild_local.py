"""Pull the Outbuild Datahub API and land it in OneLake.

    python extract_outbuild_local.py --list      # the registry, no calls
    python extract_outbuild_local.py --probe     # auth check only, one page of /projects
    python extract_outbuild_local.py             # full run, dry
    python extract_outbuild_local.py --apply     # full run, lands in OneLake

Needs `OUTBUILD_API_TOKEN` in the environment or .env. **Not yet supplied** - Outbuild issues
it through a Customer Success rep (resources/outbuild/api/DatahubAPI/Introduction.md). Until
it arrives this runs as far as the token check and stops with a clear message; everything
else is built and testable.

Same split as the Procore side, for the same reason: extraction runs here where the secret
lives, and `cd_05_land_to_bronze` merges the files into Delta in Fabric where no secret is
needed. It writes the identical manifest + NDJSON shape, so the landing notebook does not
need to know Outbuild exists.

WHY THIS SOURCE MATTERS
Outbuild is the ONLY source of milestone data anywhere in the estate - Procore's OAS has no
milestone endpoint. fct_Milestone and the whole Schedule page have no other path to real
numbers.

WHY NOT REUSE procore_extract
Three things differ, and each would need a conditional inside shared code:

    auth      `authorizationToken: <token>`, not `Authorization: Bearer <token>`
    paging    `?page=N` only - no per_page, and 500 rows per page is fixed
    envelope  a bare JSON array, not Procore's {"data": [...]} wrapper

That is a different client, not a flag. The registry pattern is what carries over, and the
bronze row shape is identical so both sources land through one notebook.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deploy as dp  # noqa: E402
from extract_procore_local import find_env, put_file, storage_token  # noqa: E402

HERE = Path(__file__).resolve().parent
CHARLEY_DEV = HERE.parent
ENDPOINTS_YML = CHARLEY_DEV / "01-ingestion" / "Outbuild" / "config" / "endpoints.yml"

BASE = "https://datahub.outbuild.com"
PAGE_SIZE = 500          # fixed by the API; documented, not configurable
MAX_PAGES = 200          # 100k rows on one endpoint means something is wrong, not big


def token() -> str:
    env_file = find_env()
    if env_file:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    value = os.environ.get("OUTBUILD_API_TOKEN")
    if not value:
        raise SystemExit(
            "OUTBUILD_API_TOKEN is not set.\n"
            "  Outbuild issues it through a Customer Success rep - see\n"
            "  resources/outbuild/api/DatahubAPI/Introduction.md.\n"
            "  Put it in .env as OUTBUILD_API_TOKEN=... and re-run.\n"
            "  Everything else here is built; this is the only thing missing."
        )
    return value


def load_registry() -> list[dict]:
    import yaml

    raw = yaml.safe_load(ENDPOINTS_YML.read_text(encoding="utf-8"))
    endpoints = raw["endpoints"]

    names = [e["name"] for e in endpoints]
    tables = [e["bronze_table"] for e in endpoints]
    for label, values in (("name", names), ("bronze_table", tables)):
        dupes = {v for v in values if values.count(v) > 1}
        if dupes:
            raise SystemExit(f"duplicate {label} in registry: {sorted(dupes)}")
    return endpoints


def fetch_page(path: str, tok: str, page: int) -> list[dict]:
    url = f"{BASE}{path}?{urllib.parse.urlencode({'page': page})}"
    request = urllib.request.Request(url, headers={
        "authorizationToken": tok,          # NOT Authorization: Bearer
        "Accept": "application/json",
    })
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                body = json.loads(response.read() or "[]")
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < 3:
                retry_after = exc.headers.get("Retry-After")
                time.sleep(float(retry_after) if retry_after else 2.0 ** attempt)
                continue
            raise
        # The docs show a bare array; tolerate a wrapped shape rather than assume.
        if isinstance(body, dict):
            for key in ("data", "items", "results"):
                if isinstance(body.get(key), list):
                    return body[key]
            return [body]
        return body
    return []


def pull(endpoint: dict, tok: str) -> list[dict]:
    """Every page of one endpoint.

    Stops on a short page rather than on an empty one: the last full page is followed by an
    empty request that costs a round trip for nothing.
    """
    records, page = [], 1
    while page <= MAX_PAGES:
        batch = fetch_page(endpoint["path"], tok, page)
        records.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        page += 1
    return records


def to_bronze_row(record: dict, endpoint: dict, ingested_at: datetime, batch: str) -> dict:
    """Identical shape to procore_extract.to_bronze_row, so one landing notebook serves both.

    The full payload stays an unparsed JSON string: bronze cannot drop a column it never
    parsed, so a transform bug is a re-run rather than a re-extract.
    """
    return {
        "_key": str(record.get(endpoint.get("key", "id"), "")),
        "_project_id": str(record["projectId"]) if record.get("projectId") is not None else None,
        "_source_endpoint": endpoint["name"],
        "_ingested_at": ingested_at.isoformat(),
        "_batch_id": batch,
        "payload": json.dumps(record, default=str),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--only", default="")
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    endpoints = load_registry()
    if args.only:
        wanted = {n.strip() for n in args.only.split(",") if n.strip()}
        unknown = wanted - {e["name"] for e in endpoints}
        if unknown:
            print(f"unknown endpoint(s): {', '.join(sorted(unknown))}")
            return 1
        endpoints = [e for e in endpoints if e["name"] in wanted]

    if args.list:
        print(f"{len(endpoints)} Outbuild endpoint(s):\n")
        for e in endpoints:
            print(f"  {e['name']:<28} {BASE}{e['path']:<28} -> {e['bronze_table']}")
        return 0

    tok = token()
    print(f"{BASE}  ({len(tok)} char token)")

    if args.probe:
        rows = fetch_page("/projects", tok, 1)
        print(f"  /projects page 1: {len(rows)} row(s)")
        for r in rows[:5]:
            print(f"      {r.get('id')}  {str(r.get('name'))[:50]}")
        return 0

    batch = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ingested_at = datetime.now(timezone.utc)
    lakehouse_id = json.loads((HERE / "fabric_ids.json").read_text())["CD_Bronze_Lakehouse"]["id"]
    stok = storage_token() if args.apply else ""
    outdir = Path(args.out) if args.out else None
    if outdir:
        outdir.mkdir(parents=True, exist_ok=True)

    print(f"\nbatch {batch} -> {'OneLake Files/_landing' if args.apply else 'DRY RUN'}")
    manifest, failures, total = [], [], 0

    for endpoint in endpoints:
        started = time.time()
        try:
            records = pull(endpoint, tok)
        except Exception as exc:                                    # noqa: BLE001
            note = f"{type(exc).__name__}: {str(exc)[:160]}"
            print(f"  {endpoint['name']:<30} FAILED  {note}")
            failures.append({"endpoint": endpoint["name"], "error": note})
            continue

        rows = [to_bronze_row(r, endpoint, ingested_at, batch) for r in records]
        body = "\n".join(json.dumps(r) for r in rows).encode("utf-8")
        print(f"  {endpoint['name']:<30} {len(rows):>7} rows  {len(body) / 1024:>8.1f} KB  "
              f"{time.time() - started:>5.1f}s")

        if outdir:
            (outdir / f"{endpoint['bronze_table']}.jsonl").write_bytes(body)
        if args.apply:
            put_file(lakehouse_id,
                     f"Files/_landing/{batch}/{endpoint['bronze_table']}.jsonl", body, stok)

        manifest.append({"endpoint": endpoint["name"], "table": endpoint["bronze_table"],
                         "rows": len(rows), "bytes": len(body),
                         "key": endpoint.get("key", "id")})
        total += len(rows)

    summary = {"batch": batch, "host": BASE, "source": "outbuild",
               "projects": 0, "total_rows": total,
               "endpoints": manifest, "failures": failures}
    blob = json.dumps(summary, indent=1).encode("utf-8")
    if outdir:
        (outdir / "_manifest.json").write_bytes(blob)
    if args.apply:
        put_file(lakehouse_id, f"Files/_landing/{batch}/_manifest.json", blob, stok)

    print(f"\n{total} row(s) across {len(manifest)} endpoint(s); {len(failures)} failed")
    if not args.apply:
        print("\nDRY RUN - nothing landed. Re-run with --apply.")
        return 0
    print(f"\nlanded to Files/_landing/{batch}/")
    print("Next: python deploy_landing.py --apply")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
