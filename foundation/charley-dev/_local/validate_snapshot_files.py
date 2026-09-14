"""Read production Delta files into local DuckDB and replay snapshot checks; no remote writes."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import duckdb
from deltalake import DeltaTable
import deploy
import deploy_dq

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "02-transformation/dq"))
import expectations

TABLES = ("dim_Project", "fct_RfiSubmittal", "fct_QualityItem", "fct_Invoice",
          "fct_BudgetLine", "fct_FinancialPeriod", "fct_ChangeOrder", "meta_PipelineRun", "fct_DailySnapshot")
GOLD = "812ec953-5517-447e-95aa-062f7cf89b28"


def validate(con, snapshot_date, run_id):
    date.fromisoformat(snapshot_date)
    datetime.strptime(run_id, "%Y%m%dT%H%M%SZ")
    # Only CREATE TEMP VIEW statements are replayed, in local memory. Never execute the swap.
    stage, _ = deploy_dq.snapshot_phases()
    for statement in stage:
        if statement.startswith("CREATE OR REPLACE TEMP VIEW"):
            con.execute(statement.replace("{SNAPSHOT_DATE}", snapshot_date).replace("{RUN_ID}", run_id))
    checks = []
    for table in ("v_DailySnapshotStage", "fct_DailySnapshot"):
        for rule in expectations.snapshot_suite(snapshot_date, table).expectations:
            count = con.execute("SELECT COUNT(*) FROM (" + rule.failing_sql.replace(chr(96), chr(34)) + ") failures").fetchone()[0]
            checks.append(dict(name=rule.name, severity=rule.severity, failing_rows=count,
                               passed=count == 0, blocking=count > 0 and rule.severity == "error"))
    actual = con.execute("SELECT COUNT(*), COUNT(*) FILTER (WHERE RunId IS DISTINCT FROM ?) "
                         "FROM fct_DailySnapshot WHERE SnapshotDate = ?", [run_id, snapshot_date]).fetchone()
    expected = con.execute("SELECT COUNT(*) FROM v_DailySnapshotStage").fetchone()[0]
    return dict(checks=checks, snapshot_rows=actual[0], expected_rows=expected, wrong_run_rows=actual[1],
                passed=actual[0] == expected and expected > 0 and actual[1] == 0
                       and not any(c["blocking"] for c in checks))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    date.fromisoformat(args.date)
    # RunId is embedded in trusted SQL templates, so accept only the pipeline timestamp form.
    datetime.strptime(args.run_id, "%Y%m%dT%H%M%SZ")
    token = subprocess.check_output([shutil.which("az") or "az", "account", "get-access-token",
                                   "--resource", "https://storage.azure.com/", "--query", "accessToken", "-o", "tsv"],
                                   text=True).strip()
    options = {"bearer_token": token, "use_fabric_endpoint": "true"}
    con = duckdb.connect()
    evidence = dict(captured_at=datetime.now(timezone.utc).isoformat(), workspace_id=deploy.WORKSPACE_ID,
                    lakehouse_id=GOLD, snapshot_date=args.date, run_id=args.run_id, tables={}, passed=False,
                    snapshot_sql_sha256=hashlib.sha256(deploy_dq.SNAPSHOT_SQL.read_bytes()).hexdigest(),
                    scope="Read-only Delta files replayed in local DuckDB using production snapshot SQL. Stage checks exercise the template; stored snapshot checks compare persisted values against recomputation. Current gold compared to saved capture; "
                          "not Spark, semantic model, rendering, source completeness or historical-time certification.")
    handles = {}
    try:
        for table in TABLES:
            uri = f"abfss://{deploy.WORKSPACE_ID}@onelake.dfs.fabric.microsoft.com/{GOLD}/Tables/dbo/{table.lower()}"
            handle = handles[table] = DeltaTable(uri, storage_options=options)
            version = handle.version()
            arrow = handle.to_pyarrow_table()
            con.register(table, arrow)
            evidence["tables"][table] = dict(version_before=version, rows=arrow.num_rows,
                schema_sha256=hashlib.sha256(str(arrow.schema).encode()).hexdigest())
        evidence.update(validate(con, args.date, args.run_id))
        for table, handle in handles.items():
            handle.update_incremental()
            evidence["tables"][table]["version_after"] = handle.version()
        evidence["stable_versions"] = all(t["version_before"] == t["version_after"] for t in evidence["tables"].values())
        evidence["passed"] = evidence["passed"] and evidence["stable_versions"]
    except Exception as exc:
        # Do not serialize SDK errors: they may contain signed request details.
        evidence["error_type"] = type(exc).__name__
        raise RuntimeError("snapshot file validation failed: " + type(exc).__name__) from None
    finally:
        evidence["finished_at"] = datetime.now(timezone.utc).isoformat()
        args.output.write_text(json.dumps(evidence, indent=2))
    print(json.dumps({k: evidence[k] for k in ("passed", "snapshot_rows", "expected_rows", "stable_versions")}))
    if not evidence["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

