"""Put CD_Master_Pipeline and the semantic model on a schedule.

    python deploy_schedule.py            # dry run - shows the cadence, changes nothing
    python deploy_schedule.py --apply    # create/replace the schedules
    python deploy_schedule.py --list     # what is scheduled right now

THE CADENCE, AND WHY EACH ONE

  Pipeline   02:00 America/New_York, daily
             Overnight so a run that takes an hour is finished before anyone opens the
             report, and in Affect's timezone rather than UTC because "yesterday's numbers"
             has to mean yesterday to a person in New York. A month-end close on the 1st
             would otherwise read a UTC day boundary five hours early.

  Model      04:00 America/New_York, daily
             Two hours after the pipeline starts. Direct Lake reframing is cheap, but it
             must not run WHILE gold is being rebuilt - a reframe mid-write binds to a
             half-written table. The gap is the pipeline's worst observed runtime plus
             headroom, not an estimate of its average.

WHY DAILY AND NOT HOURLY. The business rhythm is monthly; the data changes daily at most.
Hourly would multiply Procore API usage against a 600/hour ceiling for no one's benefit -
nobody is watching a construction budget move at 11am. The one thing that genuinely wants
to be faster is manual input, and that is a separate dataflow on its own hourly schedule
(see _docs/manual-input.md) precisely so it does not drag the whole medallion with it.

WHAT IS NOT SCHEDULED YET, and why that is correct:

  Procore extraction runs LOCALLY (no Key Vault - see _docs/procore-ingestion.md), so the
  pipeline's Extract step still fails without credentials. Because the pipeline gates on
  Succeeded, a scheduled run today would stop at that step rather than rebuild gold over
  stale bronze. That is the right failure: a scheduled job that quietly republishes old
  numbers is worse than one that stops.

  So this schedule is correct and inert until either Key Vault lands or the local
  extraction runs before it. It is deployed now because a schedule that appears the same
  day credentials do is a schedule nobody has reviewed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deploy as dp  # noqa: E402
import deploy_seeds as ds  # noqa: E402

HERE = Path(__file__).resolve().parent

# Affect is in New York. Scheduling in UTC would drift an hour twice a year relative to the
# working day, and put month-end on the wrong side of midnight for five months of the year.
TIMEZONE = "Eastern Standard Time"

# (item name, item type, jobType, local time, why)
SCHEDULES = [
    ("CD_Master_Pipeline", "DataPipeline", "Pipeline", "02:00",
     "overnight, so an hour-long run finishes before anyone opens the report"),
]

# The semantic model is NOT on Fabric's job scheduler - it has no schedulable job type
# (DefaultJob returns ItemNotFound). Direct Lake refresh is the Power BI refreshSchedule
# API on a different host, so it gets its own function below.
MODEL = ("Affect Project Report", "04:00",
         "two hours after the pipeline starts - a reframe mid-write binds to a half-written table")


def existing_schedules(tok: str, item_id: str, job_type: str) -> list[dict]:
    try:
        _, body, _ = dp.call(
            "GET",
            f"/workspaces/{dp.WORKSPACE_ID}/items/{item_id}/jobs/{job_type}/schedules", tok)
        return body.get("value", [])
    except dp.FabricError:
        return []


def schedule_model(tok_pbi: str, dataset_id: str, at: str, apply: bool) -> None:
    """Direct Lake reframe, via the Power BI refreshSchedule API.

    Two things differ from a Fabric item schedule and both are easy to get wrong: it is a
    different host (api.powerbi.com) needing a different token audience, and the day list
    is explicit rather than a "Daily" type.
    """
    import json as _json
    import urllib.error
    import urllib.request

    url = (f"https://api.powerbi.com/v1.0/myorg/datasets/{dataset_id}/refreshSchedule")
    body = {
        "value": {
            "enabled": True,
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday",
                     "Friday", "Saturday", "Sunday"],
            "times": [at],
            # Power BI wants a Windows timezone id, not an IANA one.
            "localTimeZoneId": TIMEZONE,
            # Mail on failure only. A daily success email is how failure emails get filtered.
            "notifyOption": "MailOnFailure",
        }
    }
    if not apply:
        print(f"  {'':<26} would set refreshSchedule {at} daily")
        return
    request = urllib.request.Request(
        url, method="PATCH", data=_json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {tok_pbi}", "Content-Type": "application/json"})
    try:
        urllib.request.urlopen(request, timeout=60)
        print(f"  {'':<26} refresh scheduled")
    except urllib.error.HTTPError as exc:
        print(f"  {'':<26} FAILED: {exc.code} {exc.read().decode()[:200]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    tok = dp.token()
    print(f"timezone: {TIMEZONE}\n")

    for name, kind, job_type, at, why in SCHEDULES:
        item = ds.find_item(tok, name, kind)
        if not item:
            print(f"  {name:<26} NOT FOUND - deploy it first")
            continue

        current = existing_schedules(tok, item["id"], job_type)
        state = f"{len(current)} existing" if current else "none"
        print(f"  {name:<26} {at} daily   ({state})")
        print(f"  {'':<26} {why}")

        if args.list:
            for s in current:
                cfg = s.get("configuration", {})
                print(f"  {'':<26} -> {cfg.get('type')} {cfg.get('times')} "
                      f"enabled={s.get('enabled')}")
            continue

        if not args.apply:
            continue

        payload = {
            "enabled": True,
            "configuration": {
                "type": "Daily",
                "times": [at],
                "localTimeZoneId": TIMEZONE,
                # No end date. A schedule that silently expires is worse than none - the
                # report goes stale and nothing says why.
                "startDateTime": "2026-08-03T00:00:00",
                "endDateTime": "2099-12-31T00:00:00",
            },
        }

        # Replace rather than accumulate. Re-running this script must be idempotent, and
        # two schedules on one item means two runs a night racing each other.
        for s in current:
            dp.call("DELETE",
                    f"/workspaces/{dp.WORKSPACE_ID}/items/{item['id']}/jobs/{job_type}"
                    f"/schedules/{s['id']}", tok)
            print(f"  {'':<26} removed a previous schedule")

        dp.call("POST",
                f"/workspaces/{dp.WORKSPACE_ID}/items/{item['id']}/jobs/{job_type}/schedules",
                tok, payload)
        print(f"  {'':<26} scheduled")

    # The model, on the Power BI API.
    name, at, why = MODEL
    item = ds.find_item(tok, name, "SemanticModel")
    print("")
    print(f"  {name:<26} {at} daily   (Power BI refreshSchedule)")
    print(f"  {'':<26} {why}")
    if item and (args.apply or not args.list):
        from validate_model import pbi_token
        schedule_model(pbi_token(), item["id"], at, args.apply)

    if not (args.apply or args.list):
        print("\nDRY RUN - nothing scheduled. Re-run with --apply.")
        return 0

    if args.apply:
        print("\nNOTE: the pipeline's Extract step still fails without Procore credentials,")
        print("and the Succeeded gating means that correctly STOPS the run rather than")
        print("rebuilding gold over stale bronze. See _docs/procore-ingestion.md.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except dp.FabricError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
