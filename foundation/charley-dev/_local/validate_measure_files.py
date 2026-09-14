"""Read-only OneLake file comparison; emits aggregates, never source rows or credentials."""
import json
import argparse
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from deltalake import DeltaTable

WORKSPACE = "1f7caed6-f88a-4e52-bc83-9a498a165301"
GOLD = "812ec953-5517-447e-95aa-062f7cf89b28"
EVIDENCE = Path(__file__).resolve().parents[1] / "_docs/production-measure-file-evidence.json"


def average(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def durations(rows):
    closed = [r for r in rows if r["IsOpen"] is False]
    return (average([r["DaysOpen"] for r in closed]),
            average([r["DaysOpen"] for r in closed if r["ItemType"] == "Observation"]))


def summarize_groups(rows, keys):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[k] for k in keys)].append(row)
    values = [durations(group) for group in groups.values()]
    changed = [(old, new) for old, new in values if old != new]
    deltas = [new - old for old, new in changed if old is not None and new is not None]
    return {"groups": len(groups), "changed_groups": len(changed),
            "changed_to_unknown": sum(new is None for old, new in changed),
            "numeric_delta_min_days": min(deltas) if deltas else None,
            "numeric_delta_max_days": max(deltas) if deltas else None}


def self_check():
    rows = [dict(IsOpen=False, ItemType="Observation", DaysOpen=4),
            dict(IsOpen=False, ItemType="Observation", DaysOpen=8),
            dict(IsOpen=False, ItemType="PunchItem", DaysOpen=90),
            dict(IsOpen=True, ItemType="Observation", DaysOpen=100)]
    assert durations(rows) == (34, 6)
    assert durations(rows[2:]) == (90, None)


def main():
    self_check()
    # Azure CLI credential remains in process memory; never include it in evidence/errors.
    import shutil
    token = subprocess.run([shutil.which("az"), "account", "get-access-token", "--resource",
                            "https://storage.azure.com/", "--query", "accessToken", "-o", "tsv"],
                           capture_output=True, text=True, check=True).stdout.strip()
    options = {"bearer_token": token, "use_fabric_endpoint": "true"}
    specs = {"fct_qualityitem": ["ProjectKey", "MonthStart", "ItemType", "IsOpen", "DaysOpen"],
             "dim_project": ["ProjectKey", "OriginalContractAmount", "HasPrimeContract"],
             "fct_financialperiod": ["ProjectKey", "MonthStart", "OriginalContract", "CurrentContract"]}
    tables, rows, versions = {}, {}, {}
    for name, columns in specs.items():
        table = DeltaTable(f"abfss://{WORKSPACE}@onelake.dfs.fabric.microsoft.com/{GOLD}/Tables/dbo/{name}",
                           storage_options=options)
        tables[name] = table
        versions[name] = {"before": table.version()}
        rows[name] = table.to_pyarrow_table(columns=columns).to_pylist()
        versions[name]["rows"] = len(rows[name])
    quality = rows["fct_qualityitem"]
    old, new = durations(quality)
    projects = rows["dim_project"]
    unknown = {r["ProjectKey"] for r in projects if r["OriginalContractAmount"] is None}
    periods = rows["fct_financialperiod"]
    affected = [r for r in periods if r["ProjectKey"] in unknown and r["CurrentContract"] is not None]
    latest = {}
    for row in periods:
        key = row["ProjectKey"]
        if row["MonthStart"] is not None and (key not in latest or row["MonthStart"] > latest[key]["MonthStart"]):
            latest[key] = row
    latest_affected = [r for r in latest.values() if r["ProjectKey"] in unknown and r["CurrentContract"] is not None]
    result = {"captured_at": datetime.now(timezone.utc).isoformat(), "tables": versions,
              "scope": "Direct OneLake Delta files, pinned versions read locally; does not prove service measures, source completeness, or a common pipeline run.",
              "observation_duration": {"old_all_closed_quality_days": old, "corrected_closed_observation_days": new,
                  "by_project": summarize_groups(quality, ["ProjectKey"]),
                  "by_creation_month": summarize_groups(quality, ["MonthStart"]),
                  "by_project_creation_month": summarize_groups(quality, ["ProjectKey", "MonthStart"])},
              "unknown_contract": {"named_projects_with_unknown_original": len(unknown - {"UNMATCHED", None}),
                  "unmatched_member_original_unknown": "UNMATCHED" in unknown,
                  "financial_period_rows_with_numeric_current_on_unknown_original": len(affected),
                  "affected_named_projects": len({r["ProjectKey"] for r in affected} - {"UNMATCHED", None}),
                  "affected_unmatched_period_rows": sum(r["ProjectKey"] == "UNMATCHED" for r in affected),
                  "latest_affected_projects": len(latest_affected),
                  "latest_numeric_amount_removed_if_unknown_preserved": sum(r["CurrentContract"] for r in latest_affected)}}
    for name, table in tables.items():
        table.update_incremental()
        versions[name]["after"] = table.version()
    result["versions_stable_during_read"] = all(v["before"] == v["after"] for v in versions.values())
    result["status"] = "FINDINGS" if result["versions_stable_during_read"] else "UNSTABLE"
    EVIDENCE.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["versions_stable_during_read"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_check:
            self_check()
            print("measure-file self-check passed")
            code = 0
        else:
            code = main()
    except Exception as exc:
        failure = {"status": "ERROR", "error_type": type(exc).__name__,
                   "captured_at": datetime.now(timezone.utc).isoformat()}
        if not args.self_check:
            try:
                EVIDENCE.write_text(json.dumps(failure, indent=2), encoding="utf-8")
            except OSError:
                failure["evidence_write_failed"] = True
        print(json.dumps(failure))
        code = 1
    raise SystemExit(code)
