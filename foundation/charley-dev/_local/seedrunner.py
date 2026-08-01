"""Run the gold seed SQL through DuckDB so it can be verified without Fabric.

The .sql files are written in Spark SQL because Fabric is the production target. DuckDB
executes them unchanged given the compatibility macros below - the same trick
src/procore/run_local.py already uses for get_json_object and datediff.

That means the local run verifies the actual production SQL, not a re-implementation of
it. What it does NOT verify is Spark dialect edge cases; those get checked on the first
Fabric run.

Usage:
    python seedrunner.py           # build the seeds and print row counts
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
CHARLEY_DEV = HERE.parent
REPO = CHARLEY_DEV.parent.parent

# Seeds live in two places, deliberately:
#   src/procore/sql  - dim_Trade / dim_Status, already written and tested for slice 1.
#                      Reused rather than duplicated; two copies of a seed is two seeds
#                      that drift.
#   charley-dev      - the five the earlier work did not cover.
SEED_DIRS = (
    (REPO / "src" / "procore" / "sql", ("20_gold_dim_trade.sql", "21_gold_dim_status.sql")),
    (CHARLEY_DEV / "02-transformation" / "sql" / "gold", None),  # None = every .sql
)

# Spark -> DuckDB. Both are exact 1:1 mappings, which is why one .sql serves both.
MACROS = (
    # Spark builds a date range with explode(sequence(...)); DuckDB spells the same two
    # operations unnest(generate_series(...)).
    "CREATE OR REPLACE MACRO sequence(a, b, c) AS generate_series(a, b, c)",
    "CREATE OR REPLACE MACRO explode(l) AS unnest(l)",
    # Used by dim_Status to read Procore's raw payloads. Same macro src/procore uses.
    "CREATE OR REPLACE MACRO get_json_object(j, p) AS json_extract_string(j, p)",
)

# dim_Status is not a pure seed: it unions its 32 static rows with Procore's OWN status
# vocabulary, read from bronze. Empty stubs let the static block be verified standalone -
# which is also exactly the shape of a first run, before any Procore data has landed.
#
# The populated path is already covered by src/procore/tests/test_pipeline.py against
# fixtures; duplicating that here would test the same SQL twice.
UPSTREAM_STUBS = (
    "CREATE OR REPLACE TABLE bronze_procore_rfi_statuses (payload VARCHAR)",
    "CREATE OR REPLACE TABLE silver_rfi_submittal (ItemType VARCHAR, StatusLabel VARCHAR)",
)


def seed_files() -> list[Path]:
    """Every seed file, in the order the pipeline runs them."""
    files: list[Path] = []
    for directory, only in SEED_DIRS:
        found = sorted(directory.glob("*.sql"))
        if only is not None:
            found = [p for p in found if p.name in only]
        missing = set(only or ()) - {p.name for p in found}
        if missing:
            raise FileNotFoundError(f"expected seed(s) not found in {directory}: {sorted(missing)}")
        files.extend(found)
    return files


def split_statements(sql: str) -> list[str]:
    """Split a .sql file into statements, stripping comments first.

    A `;` inside a `--` comment is otherwise read as a statement boundary and tears the
    statement in half. Same approach as procore_extract.split_sql_statements.
    """
    body = "\n".join(line.split("--", 1)[0] for line in sql.splitlines())
    return [s.strip() for s in body.split(";") if s.strip()]


def build(verbose: bool = False) -> Any:
    """Create an in-memory database with every seed table built."""
    import duckdb

    con = duckdb.connect()
    for statement in (*MACROS, *UPSTREAM_STUBS):
        con.execute(statement)

    for path in seed_files():
        for statement in split_statements(path.read_text(encoding="utf-8")):
            try:
                con.execute(statement)
            except Exception as exc:  # noqa: BLE001 - which file failed is the useful part
                raise RuntimeError(f"{path.name}: {exc}") from exc
        if verbose:
            print(f"  ran {path.name}")
    return con


def table_names(con: Any) -> list[str]:
    return [r[0] for r in con.execute(
        "SELECT table_name FROM information_schema.tables ORDER BY table_name"
    ).fetchall()]


def main() -> int:
    con = build(verbose=True)
    print()
    for name in table_names(con):
        count = con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
        print(f"  {name:<26} {count:>6} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
