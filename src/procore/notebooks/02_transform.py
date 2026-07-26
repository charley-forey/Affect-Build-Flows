# Fabric notebook source

# MARKDOWN ********************

# ## bronze -> silver -> gold
#
# Runs every `.sql` file in `sql/` in filename order. There is no orchestration layer -
# ordering lives in the numeric prefix, and the transform logic lives in version-
# controlled SQL rather than a dataflow, so it can be reviewed in a pull request.
#
# `run_local.py` executes these exact same files against DuckDB, so what is tested
# locally is what runs here.

# CELL ********************

import sys
from pathlib import Path

CODE_PATH = "/lakehouse/default/Files/procore"
if CODE_PATH not in sys.path:
    sys.path.append(CODE_PATH)

from procore_extract import split_sql_statements

# CELL ********************

for path in sorted(Path(f"{CODE_PATH}/sql").glob("*.sql")):
    statements = split_sql_statements(path.read_text(encoding="utf-8"))
    for statement in statements:
        spark.sql(statement)  # noqa: F821
    print(f"{path.name:34s} {len(statements)} statement(s)")

# CELL ********************

# Fail the run loudly if anything was rejected outright. A warn is fine - it surfaces on
# the report's Data Quality page - but a reject means rows never reached the model, and
# that should never pass silently into a leadership report.
summary = spark.sql(  # noqa: F821
    "SELECT Severity, Issue, COUNT(*) AS n FROM data_quality_log GROUP BY 1, 2 ORDER BY 1, 3 DESC"
)
display(summary)  # noqa: F821

rejects = spark.sql(  # noqa: F821
    "SELECT COUNT(*) AS n FROM data_quality_log WHERE Severity = 'reject'"
).collect()[0]["n"]
if rejects:
    print(f"WARNING: {rejects} row(s) rejected - see data_quality_log")
