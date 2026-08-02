"""Build and deploy the orchestration pipeline.

    python deploy_pipeline.py            # dry run
    python deploy_pipeline.py --apply    # create/update the pipeline
    python deploy_pipeline.py --run      # ...and trigger a run

CD_Master_Pipeline wires the notebooks into a DAG with real dependencies, so the medallion
runs in the right order and stops when a stage fails:

    cd_01_extract_procore ──┐
                            ├─► cd_10_bronze_to_silver ─► cd_30_build_gold
    cd_20_seed_gold ────────┘

Extraction and seeding are independent and run in parallel. Silver waits for extraction.
Gold waits for BOTH, because it needs the seed dimensions and the silver facts.

DEPENDENCY CONDITION IS "Succeeded", NOT "Completed". A failed extract must stop the run
rather than let gold rebuild over stale bronze and publish numbers that look current. This
is the same principle as the notebooks asserting their own output: the failure has to be
loud, because a quietly stale report is worse than a missing one.
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
    ("Extract Procore", "cd_01_extract_procore", []),
    ("Seed Gold Dimensions", "cd_20_seed_gold", []),
    ("Bronze To Silver", "cd_10_bronze_to_silver", ["Extract Procore"]),
    ("Build Gold", "cd_30_build_gold", ["Bronze To Silver", "Seed Gold Dimensions"]),
]

# Extraction is the long pole - 36 endpoints across every active project. The others are
# minutes. A timeout that is too generous hides a hung run; too tight kills a working one.
TIMEOUTS = {"cd_01_extract_procore": "0.02:00:00"}
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
        print("NOTE: Extract Procore will fail without credentials, and because the "
              "dependency is Succeeded, that correctly stops silver and gold.")
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
