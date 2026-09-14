"""Build and deploy the orchestration pipeline.

    python deploy_pipeline.py            # dry run
    python deploy_pipeline.py --apply    # create/update the pipeline
    python deploy_pipeline.py --run      # ...and trigger a run

CD_Master_Pipeline wires the notebooks into a DAG with real dependencies, so the medallion
runs in the right order and stops when a stage fails:

    cd_05_land_to_bronze ──┐
                           ├─► cd_10_bronze_to_silver ─► cd_30_build_gold ─► cd_40_dq_checks
    cd_20_seed_gold ───────┘

(Current, serial: Land To Bronze -> Land Manual Input -> Extract Outbuild -> Extract Procore
-> Bronze To Silver; see STAGES.)

Landing and seeding are independent and run in parallel. Silver waits for landing. Gold
waits for BOTH, because it needs the seed dimensions and the silver facts.

DEPENDENCY CONDITION IS "Succeeded", NOT "Completed". A failed stage must stop the run
rather than let gold rebuild over stale bronze and publish numbers that look current. This
is the same principle as the notebooks asserting their own output: the failure has to be
loud, because a quietly stale report is worse than a missing one.

WHY cd_01_extract_procore IS NOW THE HEAD OF THIS DAG (2026-08-25)
------------------------------------------------------------------
It is in, and the history below is kept because it explains what "in" had to mean.

Extraction now authenticates inside Fabric against production Procore, reading its
credentials from AffectKeyVault. Proven by a green run, not by a deploy succeeding.

The condition this file always stated has been met: extraction is in the DAG the day it can
actually authenticate, and not one day earlier. Everything downstream now gates on real data
having been fetched rather than on whatever a laptop last landed.

cd_05_land_to_bronze stays, and (since 2026-09-13) runs BEFORE extraction - see STAGES. It merges anything in
Files/_landing and needs no credential, so it remains the way a one-off backfill or a manual
re-land reaches bronze. It is no longer the only way new data arrives.

THE ORIGINAL REASONING, KEPT
----------------------------
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
-- done, 2026-08-25. See the note at the top.
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
    # SERIAL, not parallel (2026-09-13). All notebooks starting at 06:00 starved the Spark
    # session pool: Extract holds a session for 80-100 min (mostly sleeping on Procore
    # quota) and Land To Bronze / Land Manual Input were cancelled without ever starting.
    # Landing re-merges the NEWEST landing batch every night, and merge_sql overwrites
    # matched rows - so it can overwrite fresher payloads in any table that batch touches.
    # What keeps that safe today: the current landing batches are Outbuild-only, and
    # extraction (Procore) runs after landing. A Procore landing batch must never be left
    # as the newest one in Files/_landing, or it replays stale Procore rows over live ones.
    ("Land To Bronze", "cd_05_land_to_bronze", []),
    # Silver PARSES cd_bronze_man_*, and this notebook is what creates them - typed and
    # empty when there is no CSV. Without this stage the nightly run rebuilt silver and gold
    # off whatever manual bronze happened to be there from the last manual deploy. Harmless
    # while all 17 man_* tables are empty; a silent staleness bug the day somebody enters
    # data, because nothing errors - the report just keeps showing yesterday's answer.
    # Same ordering that, run by hand in the wrong order, fails with
    # System_Cancelled_Session_Statements_Failed and names no table.
    ("Land Manual Input", "cd_06_land_manual", ["Land To Bronze"]),
    # Outbuild extraction (2026-09-13): the ONLY milestone source, previously refreshed
    # only by a laptop script. Serial, before Procore: it takes minutes, so it does not
    # compete with Procore's long session, and it runs AFTER Land To Bronze so a replayed
    # Outbuild landing batch is overwritten by the live pull rather than the reverse.
    # Now that this exists, replaying Outbuild landing batches is redundant - Land To Bronze
    # stays for manual backfill. Coupling: Succeeded-only means a blocking Outbuild failure
    # (a consumed endpoint: projects/activities) skips Procore that night; unconsumed
    # endpoint failures are warnings and do not.
    ("Extract Outbuild", "cd_02_extract_outbuild", ["Land Manual Input"]),
    # Extraction. Reads Key Vault, calls Procore, merges straight into bronze.
    ("Extract Procore", "cd_01_extract_procore", ["Extract Outbuild"]),
    ("Bronze To Silver", "cd_10_bronze_to_silver",
     ["Extract Procore", "Extract Outbuild", "Ingest Sage", "Land To Bronze", "Land Manual Input"]),
    # Seeds after silver, not in parallel with landing (2026-09-14): started at 06:00 beside
    # Land To Bronze it waited for a Spark session and hit its 30-min timeout twice. Gold is
    # the only consumer, so running it immediately before gold costs nothing.
    ("Seed Gold Dimensions", "cd_20_seed_gold", ["Bronze To Silver"]),
    ("Build Gold", "cd_30_build_gold", ["Bronze To Silver", "Seed Gold Dimensions"]),
    # THE GATE. Runs last and raises on a blocking violation, so a Succeeded dependency
    # means the numbers were checked - not merely that the tables were written. Anything
    # downstream (a model refresh, a subscription) hangs off this rather than off Build
    # Gold. On its own this does not isolate Direct Lake readers: with automatic update ON
    # the models frame gold as it is written. set_autosync.py turns that off, which makes
    # Publish Models below the only frame - and it only runs on a passed gate.
    ("Data Quality Gate", "cd_40_dq_checks", ["Build Gold"]),
    # Refreshes both models serially and fails if they end up on different pipeline runs.
    ("Publish Models", "cd_50_publish_models", ["Data Quality Gate"]),
]

# A timeout that is too generous hides a hung run; too tight kills a working one.
# Extraction is now the long pole: 44 endpoints, most fanned out across 19 projects, at 100
# records per page. A full first pull measured ~11 minutes; the 2-hour allowance covers a
# cold start plus the retry.
TIMEOUTS = {"cd_01_extract_procore": "0.02:00:00", "cd_05_land_to_bronze": "0.01:00:00",
            "cd_50_publish_models": "0.01:00:00"}
DEFAULT_TIMEOUT = "0.00:30:00"
# No retry on extraction: attempt 1 spends the hourly Procore quota, so a retry 60s later
# can only fail on 429s while holding a Spark session for another hour.
# No retry on publish: a retry resubmits a refresh whose first request may still be running.
RETRIES = {"cd_01_extract_procore": 0, "cd_50_publish_models": 0}

# Session tag (Notebook activity > Advanced settings > Session tag). With workspace
# highConcurrency.notebookPipelineRunEnabled on (deploy_spark_settings.py), notebooks with the
# same tag pack into one high-concurrency session instead of starting one each - less startup
# CU on an F2. Sharing also needs the same default lakehouse, so it only packs neighbours on
# the same lakehouse; max 5 notebooks per session, then Fabric opens another. Without the
# workspace switch the tag has no effect.
# https://learn.microsoft.com/fabric/data-engineering/configure-high-concurrency-session-notebooks-in-pipelines
# Property name as exported by Fabric (typeProperties.sessionTag); the pipeline JSON schema
# itself is not in the REST reference.
SESSION_TAG = "cd_master"


# Dataflow Gen2 stages. Separate from STAGES because a dataflow activity is a different
# activity TYPE with different typeProperties - not a notebook with a different id.
#
# CD_Sage_Ingest went live 2026-08-25. It runs parallel to Procore extraction rather than
# after it: the two sources are independent, and serialising them would add Sage's four
# minutes to the critical path for no benefit. Bronze To Silver waits for both.
DATAFLOW_STAGES = [
    ("Ingest Sage", "9d1dc6db-405b-4cc6-bd3e-a8fdb8795ab8", []),
]


def dataflow_activity(name: str, dataflow_id: str, upstream: list[str]) -> dict:
    return {
        "name": name,
        "type": "RefreshDataflow",
        "dependsOn": [
            {"activity": u, "dependencyConditions": ["Succeeded"]} for u in upstream
        ],
        "policy": {
            "timeout": "0.01:00:00",
            "retry": 1,
            "retryIntervalInSeconds": 60,
            "secureOutput": False,
            "secureInput": False,
        },
        "typeProperties": {
            "dataflowId": dataflow_id,
            "workspaceId": dp.WORKSPACE_ID,
            "notifyOption": "NoNotification",
        },
    }


def activity(name: str, notebook_id: str, upstream: list[str], timeout: str, retry: int = 1) -> dict:
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
            "retry": retry,
            "retryIntervalInSeconds": 60,
            "secureOutput": False,
            "secureInput": False,
        },
        "typeProperties": {
            "notebookId": notebook_id,
            "workspaceId": dp.WORKSPACE_ID,
            "sessionTag": SESSION_TAG,
        },
    }


def build(notebook_ids: dict[str, str]) -> dict[str, str]:
    activities = [
        activity(name, notebook_ids[nb], upstream, TIMEOUTS.get(nb, DEFAULT_TIMEOUT), RETRIES.get(nb, 1))
        for name, nb, upstream in STAGES
    ] + [
        dataflow_activity(name, dataflow_id, upstream)
        for name, dataflow_id, upstream in DATAFLOW_STAGES
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
    parser.add_argument("--procore-python", action="store_true",
                        help="run Extract Procore on cd_01_extract_procore_py (Python kernel); "
                             "omit to roll back to the Spark notebook")
    args = parser.parse_args()
    # Same stage, same timeout/retry policy; only the notebook item behind it changes.
    item_names = {"cd_01_extract_procore": "cd_01_extract_procore_py"} if args.procore_python else {}

    tok = dp.token()

    # Resolve notebook ids. A missing notebook must fail HERE - a pipeline referencing a
    # notebook that does not exist deploys fine and fails at run time.
    notebook_ids = {}
    for _, nb, _ in STAGES:
        item = ds.find_item(tok, item_names.get(nb, nb), "Notebook")
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
        print("This DAG now FETCHES from Procore before it rebuilds - Extract Procore runs "
              "first, authenticating from Key Vault. The report is fresh to the nightly "
              "run, not to whenever somebody last ran a script on a laptop.")
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
