"""Build and deploy the orchestration pipeline.

    python deploy_pipeline.py            # dry run
    python deploy_pipeline.py --apply    # create/update the pipeline
    python deploy_pipeline.py --run      # ...and trigger a run

CD_Master_Pipeline wires the notebooks into a DAG with real dependencies, so the medallion
runs in the right order and stops when a stage fails:

    cd_05_land_to_bronze ──┐
                           ├─► cd_10_bronze_to_silver ─► cd_30_build_gold ─► cd_40_dq_checks
    cd_20_seed_gold ───────┘

Landing and seeding are independent and run in parallel. Silver waits for landing. Gold
waits for BOTH, because it needs the seed dimensions and the silver facts.

DEPENDENCY CONDITION IS "Succeeded", NOT "Completed". A failed stage must stop the run
rather than let gold rebuild over stale bronze and publish numbers that look current. This
is the same principle as the notebooks asserting their own output: the failure has to be
loud, because a quietly stale report is worse than a missing one.

WHY cd_01_extract_procore IS NOT IN THIS DAG
--------------------------------------------
It used to be, as the first stage, and that made the scheduled pipeline fail every single
night. The notebook needs a Procore secret, the only safe way to give a Fabric notebook one
is Key Vault, and this tenant has no Azure subscription (security-findings.md, F1). So it
failed 4 runs out of 4 - and because it gated Bronze To Silver on "Succeeded", the entire
medallion never ran on a schedule at all. Silver, gold and the DQ gate had only ever run
when somebody triggered them by hand.

That is the exact failure this platform is built to refuse: a schedule that exists, is
enabled, reports itself as configured, and produces nothing.

Leaving it in with a "Completed" condition would be worse, not better - the pipeline would
still be marked Failed every night, so the alert that is supposed to mean something would
fire daily and stop meaning anything.

So extraction is out of the DAG until it can actually authenticate. In its place is
cd_05_land_to_bronze, which merges whatever has been landed in Files/_landing and needs no
credential at all - it has succeeded on all 8 of its runs.

The honest consequence, which belongs in front of the client rather than buried: the
pipeline is fresh to the last LANDING, not to the last Procore change. Until Key Vault
exists, somebody runs extract_procore_local.py to refresh the landing files. The nightly
run still earns its place - it re-applies every transform, rebuilds gold and re-runs the
47-expectation gate - but it does not go and fetch new data.

Put cd_01_extract_procore back at the head of STAGES the day Key Vault is available.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deploy as dp  # noqa: E402
import deploy_seeds as ds  # noqa: E402

HERE = Path(__file__).resolve().parent
CHARLEY_DEV = HERE.parent
PIPELINE_DIR = CHARLEY_DEV / "06-orchestration" / "CD_Master_Pipeline.DataPipeline"

PIPELINE_NAME = "CD_Master_Pipeline"

# (activity name, notebook, [upstream activities])
STAGES = [
    # cd_01_extract_procore belongs here and cannot be here yet - see the module docstring.
    # This merges the already-landed files into bronze and needs no credential.
    ("Land To Bronze", "cd_05_land_to_bronze", []),
    ("Seed Gold Dimensions", "cd_20_seed_gold", []),
    # Silver PARSES cd_bronze_man_*, and this notebook is what creates them - typed and
    # empty when there is no CSV. Without this stage the nightly run rebuilt silver and gold
    # off whatever manual bronze happened to be there from the last manual deploy. Harmless
    # while all 17 man_* tables are empty; a silent staleness bug the day somebody enters
    # data, because nothing errors - the report just keeps showing yesterday's answer.
    # Same ordering that, run by hand in the wrong order, fails with
    # System_Cancelled_Session_Statements_Failed and names no table.
    ("Land Manual Input", "cd_06_land_manual", []),
    ("Bronze To Silver", "cd_10_bronze_to_silver", ["Land To Bronze", "Land Manual Input"]),
    ("Build Gold", "cd_30_build_gold", ["Bronze To Silver", "Seed Gold Dimensions"]),
    # THE GATE. Runs last and raises on a blocking violation, so a Succeeded dependency
    # means the numbers were checked - not merely that the tables were written. Anything
    # downstream (a model refresh, a subscription) hangs off this rather than off Build
    # Gold, which is the difference between "published" and "published and correct".
    ("Data Quality Gate", "cd_40_dq_checks", ["Build Gold"]),
]

# A timeout that is too generous hides a hung run; too tight kills a working one. Landing
# is the long pole while extraction is out of the DAG - it merges every landed endpoint
# into bronze. Extraction's 2-hour allowance is kept ready for the day it rejoins.
TIMEOUTS = {"cd_01_extract_procore": "0.02:00:00", "cd_05_land_to_bronze": "0.01:00:00"}
DEFAULT_TIMEOUT = "0.00:30:00"


def activity(name: str, notebook_id: str, upstream: list[str], timeout: str) -> dict:
    return {
        "name": name,
        "type": "TridentNotebook",
        "dependsOn": [
            {"activity": u, "dependencyConditions": ["Succeeded"]} for u in upstream
        ],
        "policy": {
            "timeout": timeout,
            # One retry, because a Spark session can fail to start for reasons that have
            # nothing to do with the code. More than one just delays a real failure.
            "retry": 1,
            "retryIntervalInSeconds": 60,
            "secureOutput": False,
            "secureInput": False,
        },
        "typeProperties": {
            "notebookId": notebook_id,
            "workspaceId": dp.WORKSPACE_ID,
        },
    }


def build(notebook_ids: dict[str, str]) -> dict[str, str]:
    activities = [
        activity(name, notebook_ids[nb], upstream, TIMEOUTS.get(nb, DEFAULT_TIMEOUT))
        for name, nb, upstream in STAGES
    ]
    content = {"properties": {
        "activities": activities,
        "annotations": [],
        "description": (
            "charley-dev medallion: extract -> silver -> gold. Fails the run on any stage "
            "failure rather than rebuilding over stale data."
        ),
    }}

    files = {
        ".platform": json.dumps({
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/"
                       "platformProperties/2.0.0/schema.json",
            "metadata": {"type": "DataPipeline", "displayName": PIPELINE_NAME},
            "config": {"version": "2.0", "logicalId": "00000000-0000-0000-0000-000000000000"},
        }, indent=2),
        "pipeline-content.json": json.dumps(content, indent=2),
    }
    for rel, body in files.items():
        path = PIPELINE_DIR / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8", newline="")
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()

    tok = dp.token()

    # Resolve notebook ids. A missing notebook must fail HERE - a pipeline referencing a
    # notebook that does not exist deploys fine and fails at run time.
    notebook_ids = {}
    for _, nb, _ in STAGES:
        item = ds.find_item(tok, nb, "Notebook")
        if not item:
            print(f"ERROR: notebook {nb!r} not found - deploy it before the pipeline")
            return 1
        notebook_ids[nb] = item["id"]

    build(notebook_ids)
    print(f"{len(STAGES)} stage(s):")
    for name, nb, upstream in STAGES:
        after = f"  after {', '.join(upstream)}" if upstream else "  (no dependencies)"
        print(f"  {name:<22} {nb:<26}{after}")

    if not (args.apply or args.run):
        print("\nDRY RUN - written to disk only. Re-run with --apply.")
        return 0

    files = build(notebook_ids)
    definition = {"parts": [
        {"path": rel, "payload": base64.b64encode(body.encode()).decode(),
         "payloadType": "InlineBase64"}
        for rel, body in files.items() if rel != ".platform"
    ]}

    existing = ds.find_item(tok, PIPELINE_NAME, "DataPipeline")
    if existing:
        status, _, headers = dp.call(
            "POST", f"/workspaces/{dp.WORKSPACE_ID}/items/{existing['id']}/updateDefinition",
            tok, {"definition": definition})
        if status == 202:
            dp.wait_for_operation(headers, tok)
        item_id = existing["id"]
        print(f"\n  updated {PIPELINE_NAME}")
    else:
        status, _, headers = dp.call(
            "POST", f"/workspaces/{dp.WORKSPACE_ID}/items", tok,
            {"displayName": PIPELINE_NAME, "type": "DataPipeline",
             "folderId": dp.FOLDER_ID, "definition": definition})
        if status == 202:
            dp.wait_for_operation(headers, tok)
        item_id = ds.find_item(tok, PIPELINE_NAME, "DataPipeline")["id"]
        print(f"\n  created {PIPELINE_NAME} ({item_id})")

    if not args.run:
        print("\nDeployed but not triggered. Re-run with --run to execute.")
        print("NOTE: this DAG reprocesses what is already landed. It does NOT fetch new "
              "data from Procore - extraction runs locally until Key Vault exists, so the "
              "report is fresh to the last run of extract_procore_local.py.")
        return 0

    status, _, headers = dp.call(
        "POST",
        f"/workspaces/{dp.WORKSPACE_ID}/items/{item_id}/jobs/instances?jobType=Pipeline",
        tok, {})
    print(f"  triggered (status {status})")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except dp.FabricError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
