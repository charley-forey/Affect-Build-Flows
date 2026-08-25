"""Deploy CD_Sage_Ingest from the committed definition, and fix its destination binding.

    python deploy_sage.py                  # dry run - show what would change
    python deploy_sage.py --apply          # push the definition
    python deploy_sage.py --apply --run    # push, then refresh
    python deploy_sage.py --status         # last refresh outcome, no writes

WHY THIS EXISTS
---------------
Every other item in this tree has a deploy script and this one did not. It was pushed by
hand on 2026-08-02, which is exactly how the defect below survived: nothing in the repo
could put the dataflow back into a known state, so nobody noticed the state was wrong.

THE DEFECT THIS FIXES
---------------------
`queryMetadata.json` binds two connections. The SQL one is right. The Lakehouse one -
the DESTINATION, where the eight tables get written - carried

    ClusterId    e1e7d5c7-3440-4dbe-8eec-b19ed40d1cd1
    DatasourceId 44379bed-e62c-42c4-9166-ad233992586a

which is somebody else's connection. `GET /connections/44379bed-...` returns
403 InsufficientPermissionsToManageConnection for us; the cluster id returns 404. Those
ids were almost certainly copied from Build_Sage_Test when this dataflow was written.

The 2026-08-25 refresh proved it. It ran 82 seconds, read Sage, and failed on
`cd_bronze_sage_apivln_WriteToDataDestination` with "Data source credentials are missing
or invalid" (error 999999). The SOURCE was never the problem once the gateway grant landed
- the write end was, and it had been wrong since the day the dataflow was authored.

The mashup itself is correct and is not touched: `Lakehouse.Contents` already names the
right workspace and lakehouse (CD_Bronze_Lakehouse, fa946636-...). Only the binding is
wrong, so only the binding is rewritten - by DROPPING it. A Lakehouse destination in the
same workspace does not need an explicit shareable connection; Fabric resolves it against
the publishing identity. Pinning it to a specific connection id is what broke it.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deploy as dp  # noqa: E402

HERE = Path(__file__).resolve().parent
CHARLEY_DEV = HERE.parent
DATAFLOW_DIR = CHARLEY_DEV / "01-ingestion" / "Sage" / "CD_Sage_Ingest.Dataflow"

DATAFLOW_NAME = "CD_Sage_Ingest"
DATAFLOW_ID = "9d1dc6db-405b-4cc6-bd3e-a8fdb8795ab8"

# The connection kinds we keep a binding for. SQL must stay - it names the on-premises
# gateway datasource and there is no way to infer it. Lakehouse is deliberately absent:
# see the module docstring.
KEEP_CONNECTION_KINDS = {"SQL"}

# Drop the dataflow-level gateway binding too.
#
# Seen in the Power Query UI on 2026-08-25: the "Connect to data source" dialog for the
# LAKEHOUSE destination showed "Data gateway: [On-premises][User] AffectGroup-Sage-Gateway".
# The top-level gatewayObjectId drags EVERY connection in the dataflow through the
# on-premises gateway, destination included - so Fabric was trying to reach OneLake via a
# machine in Affect's server room, and reported it as "you are not signed in".
#
# TRIED AND WRONG, kept as a record. Removing it made the refresh fail in five seconds -
# the old "cannot see any gateway" signature - because the dataflow-level binding is what
# routes the on-premises SOURCE. It is all-or-nothing: with it, the Lakehouse destination
# gets dragged through the gateway too; without it, Sage is unreachable.
#
# The resolution is not here. Build_Sage_Test's definition is byte-identical to ours -
# same gatewayObjectId, same SQL connection, same Lakehouse connection 44379bed on cluster
# e1e7d5c7 - and it works, because it runs as Rebecca and 44379bed is HER connection.
# e1e7d5c7 returns 404 for us: it is a per-user cloud cluster, so 44379bed is a personal
# connection and personal connections cannot be shared. Whoever owns the dataflow needs
# their OWN Lakehouse connection, created through the Power Query "Configure connection"
# dialog, which is the one thing the REST API will not do.
STRIP_GATEWAY = False


def b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def live_metadata(tok: str) -> dict | None:
    """The queryMetadata.json currently deployed, or None if it cannot be read."""
    status, body, headers = dp.call(
        "POST", f"/workspaces/{dp.WORKSPACE_ID}/items/{DATAFLOW_ID}/getDefinition", tok, {})
    if status == 202:
        body = dp.wait_for_operation(headers, tok) or {}
    for part in body.get("definition", {}).get("parts", []):
        if part.get("path") == "queryMetadata.json":
            return json.loads(base64.b64decode(part["payload"]))
    return None


def build_definition(tok: str) -> tuple[dict, list[str]]:
    """The committed mashup, with the LIVE connection bindings preserved.

    CONNECTION BINDINGS ARE ENVIRONMENT STATE, NOT SOURCE. This script used to write
    `connections` and `gatewayObjectId` from the committed file, which meant deploying it
    destroyed whatever the portal had configured. That is exactly what happened on
    2026-08-25: the Lakehouse destination was fixed by hand in Power Query, and the next
    `--apply` silently reverted it and took Sage down again.

    The mashup is the versioned artifact - it is the logic, it is diffable, and it belongs in
    git. The connection ids are not: they are per-user (`Lakehouse cforey-c` is a personal
    cloud connection; the one we inherited from Build_Sage_Test was Rebecca's, which is what
    caused the original defect) and they differ per environment. Committing them is how this
    dataflow came to be pointing at a connection nobody here could use.

    So the live bindings win, always. If the item does not exist yet, the committed file is
    the fallback.
    """
    notes = []
    metadata = json.loads((DATAFLOW_DIR / "queryMetadata.json").read_text(encoding="utf-8"))

    deployed = live_metadata(tok)
    if deployed is not None:
        for key in ("connections", "gatewayObjectId"):
            if key in deployed:
                metadata[key] = deployed[key]
            else:
                metadata.pop(key, None)
        conns = metadata.get("connections", [])
        notes.append(f"preserve {len(conns)} live connection binding(s) and the gateway")
    else:
        notes.append("item has no live definition - using the committed bindings")

    parts = [
        {"path": "queryMetadata.json",
         "payload": b64(json.dumps(metadata, indent=1)), "payloadType": "InlineBase64"},
        {"path": "mashup.pq",
         "payload": b64((DATAFLOW_DIR / "mashup.pq").read_text(encoding="utf-8")),
         "payloadType": "InlineBase64"},
    ]
    return {"parts": parts}, notes


def last_run(tok: str) -> dict | None:
    _, body, _ = dp.call(
        "GET", f"/workspaces/{dp.WORKSPACE_ID}/items/{DATAFLOW_ID}/jobs/instances", tok)
    runs = body.get("value", [])
    return runs[0] if runs else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--run", action="store_true", help="refresh after deploying")
    parser.add_argument("--status", action="store_true", help="last refresh outcome only")
    args = parser.parse_args()

    tok = dp.token()

    if args.status:
        run = last_run(tok)
        if not run:
            print("no runs")
            return 0
        print(f"{run.get('status')}  {run.get('startTimeUtc')} -> {run.get('endTimeUtc')}")
        if run.get("failureReason"):
            print(json.dumps(run["failureReason"], indent=1)[:600])
        return 0

    definition, notes = build_definition(tok)
    print(f"{DATAFLOW_NAME}  ({DATAFLOW_ID})")
    for note in notes:
        print(f"  {note}")
    for part in definition["parts"]:
        raw = base64.b64decode(part["payload"])
        print(f"  {part['path']:<22} {len(raw):>7,} bytes")

    if not args.apply:
        print("\nDRY RUN - nothing pushed. Re-run with --apply.")
        return 0

    status, _, headers = dp.call(
        # No updateMetadata=True: that flag requires a .platform part, and the display name,
        # description and folder are already right on the item. Only the two content parts
        # need to move.
        "POST", f"/workspaces/{dp.WORKSPACE_ID}/items/{DATAFLOW_ID}/updateDefinition",
        tok, {"definition": definition})
    if status == 202:
        dp.wait_for_operation(headers, tok)
    print(f"\n  updated {DATAFLOW_NAME}")

    if not args.run:
        print("Deployed but not refreshed. Re-run with --run.")
        return 0

    status, body, headers = dp.call(
        "POST", f"/workspaces/{dp.WORKSPACE_ID}/items/{DATAFLOW_ID}"
                "/jobs/instances?jobType=Refresh", tok, {})
    job = (headers.get("Location") or "").rstrip("/").split("/")[-1]
    print(f"  refresh started: {job}")
    print("  poll with:  python deploy_sage.py --status")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
