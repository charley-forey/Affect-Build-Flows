"""Deploy and run the Outbuild ingestion - the Fabric twin of deploy_ingestion.py.

    python deploy_outbuild.py            # dry run
    python deploy_outbuild.py --apply    # upload library + config, deploy notebook
    python deploy_outbuild.py --run      # ...and execute it against Outbuild

Uploads fabric_common.py, extract_outbuild_local.py and the Outbuild registry to
CD_Bronze_Lakehouse/Files/, then creates `cd_02_extract_outbuild` bound to that lakehouse.
The registry lands as Files/config/outbuild_endpoints.yml: Files/config/endpoints.yml is
Procore's.

CREDENTIALS. The notebook reads OUTBUILD_API_TOKEN through fabric_common.get_secret(), which
resolves AffectKeyVault secret `OutbuildToken` inside Fabric and fails closed. Nothing is
read or written by this script.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deploy as dp  # noqa: E402
import deploy_seeds as ds  # noqa: E402
from deploy_ingestion import bronze, storage_token, upload  # noqa: E402
from make_notebooks import EXTRACT_OUTBUILD, notebook  # noqa: E402

HERE = Path(__file__).resolve().parent
CHARLEY_DEV = HERE.parent

NOTEBOOK_NAME = "cd_02_extract_outbuild"

UPLOADS = [
    (CHARLEY_DEV / "00-platform" / "lib" / "fabric_common.py", "Files/lib/fabric_common.py"),
    (HERE / "extract_outbuild_local.py", "Files/lib/extract_outbuild_local.py"),
    (CHARLEY_DEV / "01-ingestion" / "Outbuild" / "config" / "endpoints.yml",
     "Files/config/outbuild_endpoints.yml"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="upload and deploy")
    parser.add_argument("--run", action="store_true", help="...and execute the notebook")
    args = parser.parse_args()

    tok = dp.token()
    lh = bronze()
    print(f"bronze lakehouse {lh['id']}")

    print(f"{len(UPLOADS)} file(s) to upload:")
    for local, remote in UPLOADS:
        if not local.exists():
            print(f"  MISSING {local}")
            return 1
        print(f"  {remote:<40} {local.stat().st_size:>7,} bytes")
    print("\ncredentials: read in Fabric from AffectKeyVault secret 'OutbuildToken'")

    existing = ds.find_item(tok, NOTEBOOK_NAME, "Notebook")
    print(f"would {'update' if existing else 'create'} {NOTEBOOK_NAME} ({len(EXTRACT_OUTBUILD)} cells)")

    if not (args.apply or args.run):
        print("\nDRY RUN - nothing uploaded. Re-run with --apply.")
        return 0

    stok = storage_token()
    print()
    for local, remote in UPLOADS:
        size = upload(lh["id"], stok, local, remote)
        print(f"  uploaded {remote} ({size:,} bytes)")

    nb = ds.attach(notebook(EXTRACT_OUTBUILD), lh, dp.WORKSPACE_ID)
    nb["metadata"]["dependencies"]["lakehouse"]["default_lakehouse_name"] = "CD_Bronze_Lakehouse"
    definition = {
        "format": "ipynb",
        "parts": [{"path": "notebook-content.ipynb", "payload": ds.payload(nb),
                   "payloadType": "InlineBase64"}],
    }

    if existing:
        status, _, headers = dp.call(
            "POST", f"/workspaces/{dp.WORKSPACE_ID}/items/{existing['id']}/updateDefinition",
            tok, {"definition": definition})
        if status == 202:
            dp.wait_for_operation(headers, tok)
        item_id = existing["id"]
        print(f"  updated {NOTEBOOK_NAME}")
    else:
        status, _, headers = dp.call(
            "POST", f"/workspaces/{dp.WORKSPACE_ID}/items", tok,
            {"displayName": NOTEBOOK_NAME, "type": "Notebook",
             "folderId": dp.FOLDER_ID, "definition": definition})
        if status == 202:
            dp.wait_for_operation(headers, tok)
        item_id = ds.find_item(tok, NOTEBOOK_NAME, "Notebook")["id"]
        print(f"  created {NOTEBOOK_NAME} ({item_id})")

    if not args.run:
        print("\nDeployed but not run. Re-run with --run to execute against Outbuild.")
        return 0

    print("  running ...", end=" ", flush=True)
    print(ds.run_notebook(tok, item_id))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except dp.FabricError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
