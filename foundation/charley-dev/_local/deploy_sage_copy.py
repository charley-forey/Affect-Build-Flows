"""Sage 100 -> CD_Bronze_Lakehouse as a pipeline of Copy activities.

    python deploy_sage_copy.py             # dry run
    python deploy_sage_copy.py --apply     # create/update CD_Sage_Copy
    python deploy_sage_copy.py --apply --run
    python deploy_sage_copy.py --status

WHY THIS REPLACES THE DATAFLOW
------------------------------
`CD_Sage_Ingest` (Dataflow Gen2) reads Sage correctly - once the gateway grant landed on
2026-08-25 it ran for minutes rather than the five seconds it used to - but it cannot
WRITE. Its destination binding pointed at Lakehouse connection
44379bed-e62c-42c4-9166-ad233992586a, which belongs to somebody else: we get
403 InsufficientPermissionsToManageConnection on it, and the refresh fails with
"Data source credentials are missing or invalid" on `*_WriteToDataDestination`.

Dropping the binding did not help, and a Lakehouse connection cannot be created from the
API without an interactive OAuth2 consent (`POST /connections` returns OAuthTokenLoginFailed
once the shape is right). Fixing it means clicking through Power Query in the portal, which
is exactly the kind of state this repo refuses to depend on - the dataflow had no deploy
script, and that is why the wrong connection id survived from 2026-08-02 to now unnoticed.

A Copy activity has none of that problem:

- The SOURCE uses the on-premises gateway connection by id. We hold "Can use" on it, proven
  by `GET /connections` returning it.
- The SINK is a `linkedService` naming the workspace and lakehouse artifact directly. Same
  workspace, so there is NO shareable connection object to own, share or get 403 on. That
  single difference is the whole reason this works and the dataflow does not.
- It is JSON in git, deployed by this script, diffable in a pull request. The dataflow was
  a hand-published black box.

It is also whitelisted at the database. Section 9 of the Nerds That Care handoff lists the
approved applications for login FabricReader from %LOCALHOST%, and a Copy activity connects
as `.Net SqlClient Data Provider` / `Framework Microsoft SqlClient Data Provider` - two of
the three entries. (The third, `Mashup Engine (TridentDataflowNative)`, is the dataflow's.)
So this route is sanctioned by the same XML the dataflow route is.

WHAT IT DOES NOT DO
-------------------
Bronze here is a straight table copy, same as the dataflow intended: no filtering, no
renaming, no type coercion. Shaping belongs in sql/silver where it is testable offline.
Overwrite rather than append, because Sage is the system of record and a full re-copy of
eight small tables is cheaper than reasoning about a watermark on a database we do not
control.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deploy as dp  # noqa: E402

PIPELINE_NAME = "CD_Sage_Copy"

# The gateway datasource for the "Affect Group" database. NOT the ABMI one the handoff
# document names - see _docs/access-model.md for why ABMI is the wrong database.
SAGE_CONNECTION_ID = "835e72c8-7995-4171-91cb-2a32fbd2050a"

BRONZE_LAKEHOUSE_ID = "fa946636-e143-417b-b598-5cbd31ed9990"
BRONZE_LAKEHOUSE_NAME = "CD_Bronze_Lakehouse"

# (sage table, bronze table). The two line tables are the point of this whole exercise:
# the existing Build_Sage_Test dataflow does not merely omit them, it explicitly removes
# the columns that point at them, so nobody has ever queried the line detail where
# retainage and cost codes actually live.
TABLES = [
    ("acrinv", "cd_bronze_sage_acrinv"),   # AR invoice headers
    ("arivln", "cd_bronze_sage_arivln"),   # AR invoice LINES
    ("acrpmt", "cd_bronze_sage_acrpmt"),   # AR payments
    ("acpinv", "cd_bronze_sage_acpinv"),   # AP invoice headers
    ("apivln", "cd_bronze_sage_apivln"),   # AP invoice LINES
    ("acppmt", "cd_bronze_sage_acppmt"),   # AP payments
    ("actrec", "cd_bronze_sage_actrec"),   # Jobs / receivable accounts
    ("actpay", "cd_bronze_sage_actpay"),   # Payable accounts
]

SOURCE_SCHEMA = "dbo"


def copy_activity(sage_table: str, bronze_table: str) -> dict:
    return {
        "name": f"Copy {sage_table}",
        "type": "Copy",
        "dependsOn": [],
        "policy": {
            "timeout": "0.01:00:00",
            # One retry. A gateway can drop a connection for reasons that have nothing to
            # do with the query; more than one retry just delays a real failure.
            "retry": 1,
            "retryIntervalInSeconds": 60,
            "secureOutput": False,
            "secureInput": False,
        },
        "typeProperties": {
            "source": {
                "type": "SqlServerSource",
                "queryTimeout": "0.02:00:00",
                "partitionOption": "None",
                "datasetSettings": {
                    "type": "SqlServerTable",
                    "typeProperties": {
                        "schema": SOURCE_SCHEMA,
                        "table": sage_table,
                    },
                    "externalReferences": {"connection": SAGE_CONNECTION_ID},
                    "annotations": [],
                },
            },
            "sink": {
                "type": "LakehouseTableSink",
                # Overwrite: Sage is the system of record and these tables are small.
                "tableActionOption": "Overwrite",
                "datasetSettings": {
                    "type": "LakehouseTable",
                    "typeProperties": {"table": bronze_table},
                    "linkedService": {
                        "name": BRONZE_LAKEHOUSE_NAME,
                        "properties": {
                            "type": "Lakehouse",
                            "typeProperties": {
                                "workspaceId": dp.WORKSPACE_ID,
                                "artifactId": BRONZE_LAKEHOUSE_ID,
                                "rootFolder": "Tables",
                            },
                            "annotations": [],
                        },
                    },
                    "annotations": [],
                },
            },
            "enableStaging": False,
            "translator": {"type": "TabularTranslator", "typeConversion": True},
        },
    }


def build() -> dict:
    content = {
        "properties": {
            "activities": [copy_activity(s, b) for s, b in TABLES],
            "annotations": [],
            "description": (
                "Sage 100 Contractor -> CD_Bronze_Lakehouse. Replaces CD_Sage_Ingest, whose "
                "Gen2 destination binding pointed at a connection we cannot use."
            ),
        }
    }
    return {
        "parts": [{
            "path": "pipeline-content.json",
            "payload": base64.b64encode(
                json.dumps(content, indent=2).encode("utf-8")).decode("ascii"),
            "payloadType": "InlineBase64",
        }]
    }


def find_pipeline(tok: str) -> dict | None:
    _, body, _ = dp.call("GET", f"/workspaces/{dp.WORKSPACE_ID}/items?type=DataPipeline", tok)
    for item in body.get("value", []):
        if item.get("displayName") == PIPELINE_NAME:
            return item
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()

    tok = dp.token()
    existing = find_pipeline(tok)

    if args.status:
        if not existing:
            print(f"{PIPELINE_NAME} does not exist")
            return 1
        _, body, _ = dp.call(
            "GET", f"/workspaces/{dp.WORKSPACE_ID}/items/{existing['id']}/jobs/instances", tok)
        for run in body.get("value", [])[:3]:
            print(f"{run.get('status'):<12} {run.get('startTimeUtc')} -> {run.get('endTimeUtc')}")
            if run.get("failureReason"):
                print("   " + json.dumps(run["failureReason"])[:400])
        return 0

    print(f"{PIPELINE_NAME}: {len(TABLES)} copy activities")
    for sage_table, bronze_table in TABLES:
        print(f"  {SOURCE_SCHEMA}.{sage_table:<8} -> {bronze_table}")
    print(f"\n  source connection {SAGE_CONNECTION_ID}  (on-prem gateway)")
    print(f"  sink lakehouse    {BRONZE_LAKEHOUSE_ID}  ({BRONZE_LAKEHOUSE_NAME}, no connection needed)")

    if not args.apply:
        print("\nDRY RUN - nothing pushed. Re-run with --apply.")
        return 0

    definition = build()
    if existing:
        status, _, headers = dp.call(
            "POST", f"/workspaces/{dp.WORKSPACE_ID}/items/{existing['id']}/updateDefinition",
            tok, {"definition": definition})
        if status == 202:
            dp.wait_for_operation(headers, tok)
        pipeline_id = existing["id"]
        print(f"\n  updated {PIPELINE_NAME}")
    else:
        status, body, headers = dp.call(
            "POST", f"/workspaces/{dp.WORKSPACE_ID}/items", tok,
            {"displayName": PIPELINE_NAME, "type": "DataPipeline",
             "folderId": dp.FOLDER_ID, "definition": definition})
        if status == 202:
            dp.wait_for_operation(headers, tok)
            existing = find_pipeline(tok)
            pipeline_id = existing["id"]
        else:
            pipeline_id = body["id"]
        print(f"\n  created {PIPELINE_NAME} ({pipeline_id})")

    if not args.run:
        print("Deployed but not run. Re-run with --run.")
        return 0

    status, _, headers = dp.call(
        "POST", f"/workspaces/{dp.WORKSPACE_ID}/items/{pipeline_id}"
                "/jobs/instances?jobType=Pipeline", tok, {})
    job = (headers.get("Location") or "").rstrip("/").split("/")[-1]
    print(f"  run started: {job}")
    print("  poll with:  python deploy_sage_copy.py --status")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
