"""Deploy and run the Procore ingestion.

    python deploy_ingestion.py            # dry run
    python deploy_ingestion.py --apply    # upload library + config, deploy notebook
    python deploy_ingestion.py --run      # ...and execute it against Procore
    python deploy_ingestion.py --apply --python-kernel     # cd_01_extract_procore_py (no Spark)
    python deploy_ingestion.py --apply --python-kernel --validation-lakehouse NAME:ID
                                          # ...bound to a validation lakehouse copy instead

--python-kernel deploys a SEPARATE item, so the Spark notebook stays deployed for rollback;
the pipeline switches between them with deploy_pipeline.py --procore-python.
See _docs/procore-python-kernel.md.

Uploads the shared library and the endpoint registry to CD_Bronze_Lakehouse/Files/, then
creates `cd_01_extract_procore` bound to that lakehouse.

The library ships as Files/ rather than being pasted into the notebook, so auth,
pagination, the v2.0 header rule, 429 retry and watermarking exist in exactly ONE place.
The Jul 23 warehouse review found the opposite pattern - the same logic copied into every
notebook, which is one bug duplicated seventeen times.

CREDENTIALS. The notebook reads PROCORE_CLIENT_ID / _SECRET / _COMPANY_ID through
get_secret(), which resolves Key Vault inside Fabric and environment variables locally.
Nothing is read or written by this script; it only checks whether they are reachable and
says so plainly.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deploy as dp  # noqa: E402
import deploy_seeds as ds  # noqa: E402
from make_notebooks import EXTRACT_PROCORE, extract_procore_python, notebook  # noqa: E402

HERE = Path(__file__).resolve().parent
CHARLEY_DEV = HERE.parent
REPO = CHARLEY_DEV.parent.parent

NOTEBOOK_NAME = "cd_01_extract_procore"
PYTHON_NOTEBOOK_NAME = "cd_01_extract_procore_py"

# What goes into the lakehouse, and where.
UPLOADS = [
    (REPO / "src" / "procore" / "procore_extract.py", "Files/lib/procore_extract.py"),
    (CHARLEY_DEV / "00-platform" / "lib" / "procore_scope.py", "Files/lib/procore_scope.py"),
    (CHARLEY_DEV / "00-platform" / "lib" / "fabric_common.py", "Files/lib/fabric_common.py"),
    (CHARLEY_DEV / "00-platform" / "lib" / "watermark.py", "Files/lib/watermark.py"),
    (CHARLEY_DEV / "00-platform" / "lib" / "ratelimit.py", "Files/lib/ratelimit.py"),
    (CHARLEY_DEV / "00-platform" / "lib" / "deltars.py", "Files/lib/deltars.py"),
    (CHARLEY_DEV / "01-ingestion" / "Procore" / "config" / "endpoints.yml",
     "Files/config/endpoints.yml"),
]

REQUIRED_SECRETS = ("PROCORE_CLIENT_ID", "PROCORE_CLIENT_SECRET", "PROCORE_COMPANY_ID")


def storage_token() -> str:
    """OneLake speaks the ADLS Gen2 DFS API, which needs a storage-scoped token."""
    import subprocess

    result = subprocess.run(
        [dp.az_path(), "account", "get-access-token",
         "--resource", "https://storage.azure.com", "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise dp.FabricError(f"storage token failed: {result.stderr.strip()[:200]}")
    return result.stdout.strip()


def upload(lakehouse_id: str, tok: str, local: Path, remote: str) -> int:
    """Write one file to OneLake: create, append, flush - the DFS three-step."""
    base = (f"https://onelake.dfs.fabric.microsoft.com/{dp.WORKSPACE_ID}/"
            f"{lakehouse_id}/{remote}")
    data = local.read_bytes()
    auth = {"Authorization": f"Bearer {tok}"}

    def call(url: str, method: str, body: bytes | None = None, headers: dict | None = None):
        request = urllib.request.Request(
            url, method=method, data=body, headers={**auth, **(headers or {})}
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.status
        except urllib.error.HTTPError as exc:
            raise dp.FabricError(
                f"{method} {remote} -> {exc.code}: {exc.read().decode()[:200]}"
            ) from exc

    call(f"{base}?resource=file", "PUT")
    if data:
        call(f"{base}?action=append&position=0", "PATCH", data,
             {"Content-Type": "application/octet-stream"})
    call(f"{base}?action=flush&position={len(data)}", "PATCH")
    return len(data)


def bronze() -> dict:
    ids = json.loads((HERE / "fabric_ids.json").read_text())
    return ids["CD_Bronze_Lakehouse"]


def credentials_available() -> tuple[bool, list[str]]:
    """Locally, secrets come from the environment. Inside Fabric, from Key Vault."""
    missing = [s for s in REQUIRED_SECRETS if not os.environ.get(s)]
    return (not missing and bool(os.environ.get("PROCORE_BASE_URL"))), missing


def build_notebook(python_kernel: bool, lakehouse_id: str) -> dict:
    if python_kernel:
        return notebook(extract_procore_python(dp.WORKSPACE_ID, lakehouse_id), "python")
    return notebook(EXTRACT_PROCORE)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="upload and deploy")
    parser.add_argument("--run", action="store_true", help="...and execute the notebook")
    parser.add_argument("--python-kernel", action="store_true",
                        help=f"deploy {PYTHON_NOTEBOOK_NAME}: Python kernel, delta-rs writes")
    parser.add_argument("--validation-lakehouse", metavar="NAME:ID",
                        help="with --python-kernel: bind to this lakehouse (Files and Tables) "
                             "and deploy as <name>_validation, for a side-by-side run")
    args = parser.parse_args()
    if args.validation_lakehouse and not args.python_kernel:
        parser.error("--validation-lakehouse requires --python-kernel")

    lh, lh_name, name = bronze(), "CD_Bronze_Lakehouse", NOTEBOOK_NAME
    if args.python_kernel:
        name = PYTHON_NOTEBOOK_NAME
    if args.validation_lakehouse:
        lh_name, _, lh_id = args.validation_lakehouse.partition(":")
        if not lh_id or lh_id == lh["id"]:
            parser.error("--validation-lakehouse must be NAME:ID of a lakehouse other than bronze")
        lh, name = {"id": lh_id}, f"{PYTHON_NOTEBOOK_NAME}_validation"

    tok = dp.token()
    print(f"{name} -> {lh_name} {lh['id']}")

    total = sum(p.stat().st_size for p, _ in UPLOADS)
    print(f"{len(UPLOADS)} file(s) to upload ({total:,} bytes):")
    for local, remote in UPLOADS:
        if not local.exists():
            print(f"  MISSING {local}")
            return 1
        print(f"  {remote:<36} {local.stat().st_size:>7,} bytes")

    have_creds, missing = credentials_available()
    print(f"\ncredentials: {'available' if have_creds else 'NOT available'}")
    if missing:
        print(f"  missing from the environment: {', '.join(missing)}")

    if not (args.apply or args.run):
        print("\nDRY RUN - nothing uploaded. Re-run with --apply.")
        return 0

    stok = storage_token()
    print()
    for local, remote in UPLOADS:
        size = upload(lh["id"], stok, local, remote)
        print(f"  uploaded {remote} ({size:,} bytes)")

    nb = ds.attach(build_notebook(args.python_kernel, lh["id"]), lh, dp.WORKSPACE_ID)
    nb["metadata"]["dependencies"]["lakehouse"]["default_lakehouse_name"] = lh_name
    definition = {
        "format": "ipynb",
        "parts": [{"path": "notebook-content.ipynb", "payload": ds.payload(nb),
                   "payloadType": "InlineBase64"}],
    }

    existing = ds.find_item(tok, name, "Notebook")
    if existing:
        status, _, headers = dp.call(
            "POST", f"/workspaces/{dp.WORKSPACE_ID}/items/{existing['id']}/updateDefinition",
            tok, {"definition": definition},
        )
        if status == 202:
            dp.wait_for_operation(headers, tok)
        item_id = existing["id"]
        print(f"  updated {name}")
    else:
        status, _, headers = dp.call(
            "POST", f"/workspaces/{dp.WORKSPACE_ID}/items", tok,
            {"displayName": name, "type": "Notebook",
             "folderId": dp.FOLDER_ID, "definition": definition},
        )
        if status == 202:
            dp.wait_for_operation(headers, tok)
        item_id = ds.find_item(tok, name, "Notebook")["id"]
        print(f"  created {name} ({item_id})")

    if not args.run:
        print("\nDeployed but not run. Re-run with --run to execute against Procore.")
        return 0

    print("  running ...", end=" ", flush=True)
    try:
        print(ds.run_notebook(tok, item_id))
    except dp.FabricError as exc:
        print("FAILED")
        print(f"\n{exc}")
        print(
            "\nIf this is a secret-resolution failure, the pipeline is deployed correctly "
            "and only the credentials are missing. See _docs/procore-ingestion.md."
        )
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except dp.FabricError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
