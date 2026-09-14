"""Actual-file DQ runner fails closed and only loads referenced source dependencies."""
import sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import duckdb
import validate_production_files as v
con = duckdb.connect()
rules = [SimpleNamespace(name="one", severity="error", failing_sql="SELECT * FROM sv_used")]
views, needed = v.plan(con, rules, "CREATE OR REPLACE TEMPORARY VIEW sv_used AS SELECT * FROM delta.`{CD_SILVER_ABFSS}/real_table`; CREATE OR REPLACE TEMPORARY VIEW sv_unused AS SELECT * FROM ignored;")
assert needed == {"sv_used", "input_real_table"}
try:
    v.plan(con, rules, "CREATE OR REPLACE TEMPORARY VIEW sv_used AS SELECT * FROM delta.`{SILVER_ABFSS}/real_table`;")
except RuntimeError:
    pass
else:
    raise AssertionError("unknown lakehouse was silently remapped")
assert v.evaluate(con, rules)[0]["failing_rows"] == -1
con.execute("CREATE TABLE sv_used (id INTEGER)")
assert v.evaluate(con, rules)[0]["passed"]
con.execute("INSERT INTO sv_used VALUES (1)")
assert v.evaluate(con, rules)[0]["blocking"]
rules[0].severity = "warn"
assert not v.evaluate(con, rules)[0]["blocking"]
print("production file runner checks passed")
