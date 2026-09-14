"""Shrink the Build workspace's Spark footprint so it fits an F2 (48 CU-h/day).

    python deploy_spark_settings.py                 # dry run: read, record, print the PATCH
    python deploy_spark_settings.py --apply         # PATCH workspace Spark settings, read back
    python deploy_spark_settings.py --small-pool    # dry run, also proposing a Small custom pool
    python deploy_spark_settings.py --small-pool --apply

WHY. Background (Spark) CU is smoothed over 24 h, so every session-hour stays on the capacity
for a day. On the Starter Pool a running job holds 1-2 Medium nodes (8 vCores each = 4-8 CU)
- 2-4x an F2. See _docs/capacity-operations.md.

WHAT (only properties in the REST reference, nothing inferred):
  Workspace Settings - Update Spark Settings
  https://learn.microsoft.com/rest/api/fabric/spark/workspace-settings/update-spark-settings
    pool.starterPool.maxNodeCount        2  -> 1   single node: driver+executor share one
                                                   Medium node, ~4 CU instead of ~8. The
                                                   starter-pool docs list 1 as the F2 maximum.
    pool.starterPool.maxExecutors        1  -> 1   (unchanged, asserted)
    job.sessionTimeoutInMinutes          20 -> 10  idle interactive sessions stop sooner
    highConcurrency.notebookPipelineRunEnabled  false -> true
                                                   pipeline notebooks pack into one session
                                                   (same user, default lakehouse, compute
                                                   config, libraries) instead of one each.
  --small-pool (opt-in):
  Custom Pools - Create Workspace Custom Pool
  https://learn.microsoft.com/rest/api/fabric/spark/custom-pools/create-workspace-custom-pool
    POST a MemoryOptimized Small pool, autoscale off 1-1, executors off 1-1, then PATCH
    pool.defaultPool to it. ~2 CU per job, but: custom pools start on demand (2-5 min, not
    billed), single-node halves the 32 GB node for driver/executor, and the capacity admin
    must allow workspace-sized pools. Try it on one notebook before making it the default.

Refuses any workspace other than Build. Writes _docs/spark-settings-before.json once (never
overwritten, so a later run cannot erase the pre-change record). Settings hold no secrets.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deploy as dp  # noqa: E402

ALLOWED_WORKSPACE = "1f7caed6-f88a-4e52-bc83-9a498a165301"   # Build
BEFORE = dp.CHARLEY_DEV / "_docs" / "spark-settings-before.json"
SMALL_POOL = {
    "name": "cd_small",
    "nodeFamily": "MemoryOptimized",
    "nodeSize": "Small",
    "autoScale": {"enabled": False, "minNodeCount": 1, "maxNodeCount": 1},
    "dynamicExecutorAllocation": {"enabled": False, "minExecutors": 1, "maxExecutors": 1},
}
TARGET = {
    "pool": {"starterPool": {"maxNodeCount": 1, "maxExecutors": 1}},
    "job": {"sessionTimeoutInMinutes": 10},
    "highConcurrency": {"notebookPipelineRunEnabled": True},
}


def diff(target: dict, current: dict) -> dict:
    """The subset of target whose leaves differ from current. Empty dict = nothing to do."""
    out = {}
    for key, want in target.items():
        have = current.get(key) if isinstance(current, dict) else None
        if key == "defaultPool":        # a pool reference is sent whole (name + type), never half
            if not isinstance(have, dict) or any(have.get(k) != v for k, v in want.items()):
                out[key] = want
        elif isinstance(want, dict):
            sub = diff(want, have if isinstance(have, dict) else {})
            if sub:
                out[key] = sub
        elif have != want:
            out[key] = want
    return out


def proposal(settings: dict, small_pool: bool) -> dict:
    target = json.loads(json.dumps(TARGET))
    if small_pool:
        target["pool"]["defaultPool"] = {"name": SMALL_POOL["name"], "type": "Workspace"}
    return diff(target, settings)


def read(tok: str, ws: str) -> dict:
    return {
        "workspaceId": ws,
        "settings": dp.call("GET", f"/workspaces/{ws}/spark/settings", tok)[1],
        "pools": dp.call("GET", f"/workspaces/{ws}/spark/pools", tok)[1].get("value", []),
        "environments": [{"id": i["id"], "displayName": i["displayName"]}
                         for i in dp.list_collection(f"/workspaces/{ws}/items?type=Environment", tok)],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workspace", default=dp.WORKSPACE_ID)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--small-pool", action="store_true")
    args = parser.parse_args()
    if args.workspace != ALLOWED_WORKSPACE:
        print(f"REFUSED: {args.workspace} is not the Build workspace {ALLOWED_WORKSPACE}")
        return 2

    tok = dp.token()
    ws = args.workspace
    current = read(tok, ws)
    if BEFORE.exists():
        print(f"  {BEFORE.name} exists - kept as the pre-change record")
    else:
        BEFORE.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
        print(f"  recorded {BEFORE.name}")
    print("current settings:\n" + json.dumps(current["settings"], indent=2))

    pool_exists = any(p.get("name") == SMALL_POOL["name"] for p in current["pools"])
    patch = proposal(current["settings"], args.small_pool)
    if args.small_pool and not pool_exists:
        print(f"\nwould POST /workspaces/{ws}/spark/pools\n" + json.dumps(SMALL_POOL, indent=2))
    print(f"\nwould PATCH /workspaces/{ws}/spark/settings\n" + json.dumps(patch, indent=2))

    if not args.apply:
        print("\nDRY RUN - nothing changed. Re-run with --apply (workspace admin role required).")
        return 0
    if args.small_pool and not pool_exists:
        dp.call("POST", f"/workspaces/{ws}/spark/pools", tok, SMALL_POOL)
        print(f"  created pool {SMALL_POOL['name']}")
    if patch:
        dp.call("PATCH", f"/workspaces/{ws}/spark/settings", tok, patch)
    after = dp.call("GET", f"/workspaces/{ws}/spark/settings", tok)[1]
    left = proposal(after, args.small_pool)
    if left:
        print("ERROR: read-back does not match the target:\n" + json.dumps(left, indent=2))
        return 1
    print("\napplied and read back:\n" + json.dumps(after, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except dp.FabricError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
