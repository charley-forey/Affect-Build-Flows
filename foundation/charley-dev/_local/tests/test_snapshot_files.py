"""Snapshot replay rejects corrupted saved values and mismatched runs."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import seedrunner
import deploy_dq
import validate_snapshot_files as validator

con = seedrunner.build()
run = "20260914T083429Z"
con.execute("CREATE TABLE meta_PipelineRun AS SELECT ? AS RunId, 'ok' AS Status, 0 AS Blocking", [run])
stage, swap = deploy_dq.snapshot_phases()
for sql in stage + swap:
    con.execute(sql.replace("{SNAPSHOT_DATE}", "2026-09-14").replace("{RUN_ID}", run).replace(") USING DELTA", ")"))
assert validator.validate(con, "2026-09-14", run)["passed"]
assert not validator.validate(con, "2026-09-14", "20260914T083430Z")["passed"]
con.execute("UPDATE fct_DailySnapshot SET ArOutstanding = COALESCE(ArOutstanding, 0) + 1")
assert not validator.validate(con, "2026-09-14", run)["passed"]
print("snapshot file replay checks passed")
