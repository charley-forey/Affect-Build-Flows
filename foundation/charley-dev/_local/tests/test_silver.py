"""Assertions over the bronze -> silver transforms.

Bronze holds the raw Procore payload as an unparsed JSON string; silver parses, types and
trims it. These fixtures are the shapes procore_extract actually writes - `_key`,
`_project_id`, `payload` and the audit columns - so the test exercises the real contract
between the two layers.

The single most important check here is the COLUMN CONTRACT: silver must expose exactly
what sql/silver/01_source_views_cd.sql expects, because that is what lets gold switch
source with no gold file changing.

Run:  python test_silver.py
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from seedrunner import CHARLEY_DEV, MACROS, split_statements  # noqa: E402

CHECKS: list[str] = []
SILVER_SQL = CHARLEY_DEV / "02-transformation" / "sql" / "silver" / "10_procore_silver.sql"
SWITCH_SQL = CHARLEY_DEV / "02-transformation" / "sql" / "silver" / "01_source_views_cd.sql"


def check(label: str) -> None:
    CHECKS.append(label)


def bronze_row(key: str, payload: dict, project_id: str | None = None) -> str:
    """One bronze row, exactly as procore_extract.to_bronze_row writes it."""
    p = json.dumps(payload).replace("'", "''")
    pid = f"'{project_id}'" if project_id else "NULL"
    return f"('{key}', {pid}, '{p}', TIMESTAMP '2026-08-01 12:00:00', 'batch-1')"


BRONZE = {
    "cd_bronze_procore_projects": [
        bronze_row("7", {"id": 7, "name": "  Tower A  ", "project_number": "26-001",
                         "display_name": "Tower A", "status_name": "Active", "active": True}),
        # No id: must be REJECTED, not silently dropped.
        bronze_row("", {"name": "Broken project"}),
    ],
    "cd_bronze_procore_vendors": [
        bronze_row("V1", {"id": "V1", "name": "  Acme Concrete  ",
                          "abbreviated_name": "ACME", "is_active": True}),
    ],
    "cd_bronze_procore_cost_codes": [
        bronze_row("CC1", {"id": "CC1", "full_code": "03-100", "name": "  Concrete  ",
                           "parent": {"id": "CC0"}}),
    ],
    "cd_bronze_procore_prime_contracts": [
        bronze_row("C1", {"id": "C1", "number": "PC-1", "title": "Prime",
                          "grand_total": 8800000.0, "retainage_percent": 10.0,
                          "start_date": "2025-01-01",
                          "estimated_completion_date": "2026-06-30",
                          "status": "Approved"}, project_id="7"),
    ],
    "cd_bronze_procore_prime_change_orders": [
        bronze_row("CO1", {"id": "CO1", "contract_id": "C1", "number": "1",
                           "title": "CO one", "grand_total": 316960.48,
                           "created_at": "2025-05-02", "status": "Approved"},
                   project_id="7"),
    ],
    # The REAL shape of Procore's budget_views/{id}/detail_rows under Affect's own
    # "STANDARD BUDGET VIEW - CM": flat cost_code_id, plain-string category, and money
    # columns named by the configured view rather than by an API schema. The first version
    # of this fixture used the existing warehouse's already-shaped names, which is exactly
    # how the parser came to return NULL for every money column against live data.
    "cd_bronze_procore_budget_detail_rows": [
        bronze_row("B1", {"cost_code_id": "CC1",
                          "cost_code": "03-100 - CONCRETE",
                          "category": "Hard Costs",
                          "original_budget_amount": 1000000.0,
                          "budget_modifications": 50000.0,
                          "UPDATED PRIME CONTRACT BUDGET (D = A+B+C)": 1050000.0,
                          "PROJECTED PRIME CONTRACT BUDGET (F=D+E)": 1100000.0,
                          "TOTAL COMMITTED TO DATE (K=G+H+I+J)": 900000.0,
                          "DIRECT COSTS (J)": 400000.0,
                          "INVOICED TO DATE (P)": 350000.0,
                          "COST TO COMPLETE (Q=K-P)": 550000.0}, project_id="7"),
    ],
    "cd_bronze_procore_submittals": [
        bronze_row("SB1", {"id": "SB1", "number": "001", "title": "  Rebar  ",
                           "status": {"name": "Open"}, "cost_code": {"id": "CC1"},
                           "created_at": "2025-05-01",
                           "required_on_site_date": "2025-05-20"}, project_id="7"),
        # A sentinel date - the class of value that made Spark refuse the read entirely.
        bronze_row("SB2", {"id": "SB2", "number": "002", "title": "Sentinel",
                           "status": {"name": "Open"},
                           "created_at": "0001-01-01"}, project_id="7"),
    ],
    "cd_bronze_procore_rfis": [
        bronze_row("R1", {"id": "R1", "number": "RFI-1", "subject": "  Slab edge  ",
                          "status": "Open", "priority": "High",
                          "cost_code": {"id": "CC1"}, "created_at": "2025-05-03",
                          "due_date": "2025-05-17"}, project_id="7"),
        bronze_row("R2", {"id": "R2", "number": "RFI-2", "subject": "Closed one",
                          "status": "Closed", "priority": "Normal",
                          "created_at": "2025-04-01", "time_resolved": "2025-04-10"},
                   project_id="7"),
    ],
}

COLUMNS = "_key, _project_id, payload, _ingested_at, _batch_id"


def build():
    import duckdb

    con = duckdb.connect()
    for macro in MACROS:
        con.execute(macro)
    for table, rows in BRONZE.items():
        con.execute(
            f"CREATE OR REPLACE TABLE {table} AS "
            f"SELECT * FROM (VALUES {', '.join(rows)}) AS t({COLUMNS})"
        )
    for statement in split_statements(SILVER_SQL.read_text(encoding="utf-8")):
        try:
            con.execute(statement)
        except Exception as exc:
            raise RuntimeError(f"silver SQL failed: {exc}") from exc
    return con


def one(con, sql):
    row = con.execute(sql).fetchone()
    return row[0] if row else None


def test_parsing(con) -> None:
    assert one(con, "SELECT COUNT(*) FROM cd_silver_projects") == 1
    assert one(con, "SELECT project_id FROM cd_silver_projects") == "7"
    check("bronze JSON payload parses into typed silver columns")

    # TRIM on the way in. "Tower A  " never equals "Tower A" in a join (defect #9).
    assert one(con, "SELECT project_name FROM cd_silver_projects") == "Tower A"
    assert one(con, "SELECT vendor_name FROM cd_silver_vendors") == "Acme Concrete"
    assert one(con, "SELECT cost_code_name FROM cd_silver_cost_codes") == "Concrete"
    check("every text value is trimmed at the silver boundary")

    # Nested JSON must resolve, not come back NULL.
    assert one(con, "SELECT cost_code_id FROM cd_silver_budgets") == "CC1"
    assert one(con, "SELECT category FROM cd_silver_budgets") == "Hard Costs"
    assert one(con, "SELECT status_label FROM cd_silver_submittals WHERE item_id='SB1'") == "Open"
    check("nested JSON (cost_code.id, category.name, status.name) resolves")

    # EVERY money column on the budget grid must be non-NULL. This is the regression guard
    # for the defect that made this remap necessary: the parser read the existing
    # warehouse's already-shaped names, none of which exist in Procore's raw payload, so
    # all eight silently parsed to NULL and the budget measures went blank in a model that
    # otherwise looked healthy. A NULL here is indistinguishable from a zero budget.
    money = ["original_budget", "budget_modifications", "updated_budget", "forecast_budget",
             "committed_to_date", "direct_costs", "invoiced_to_date", "cost_to_complete"]
    for column in money:
        value = one(con, f"SELECT {column} FROM cd_silver_budgets")
        assert value is not None, f"{column} parsed to NULL - check the view's column name"
    assert one(con, "SELECT updated_budget FROM cd_silver_budgets") == 1050000.0
    assert one(con, "SELECT invoiced_to_date FROM cd_silver_budgets") == 350000.0
    check(f"all {len(money)} budget money columns parse from the view's own column names")

    assert one(con, "SELECT contract_value FROM cd_silver_prime_contracts") == 8800000.0
    assert one(con, "SELECT amount FROM cd_silver_prime_change_orders") == 316960.48
    check("money parses as DOUBLE, not text")

    assert one(con, "SELECT start_date FROM cd_silver_prime_contracts") == date(2025, 1, 1)
    check("dates parse as DATE")


def test_sentinel_dates(con) -> None:
    # 0001-01-01 is a placeholder for "unknown". Floored to NULL so it cannot reach a
    # report as a real date - the same class of problem as the workbook's "NA" string
    # sentinels (defect #7), and the exact value class that made Spark refuse the read.
    assert one(con, "SELECT created_date FROM cd_silver_submittals WHERE item_id='SB2'") is None
    assert one(con, "SELECT created_date FROM cd_silver_submittals WHERE item_id='SB1'") == date(2025, 5, 1)
    check("sentinel dates before 1990 become NULL, real dates survive")


def test_rejects(con) -> None:
    # The project with no id must be RECORDED, not dropped. Silent drops are how the
    # workbook's defects survived for months.
    assert one(con, "SELECT COUNT(*) FROM cd_dq_rejects") == 1
    assert one(con, "SELECT target_table FROM cd_dq_rejects") == "cd_silver_projects"
    assert one(con, "SELECT reason FROM cd_dq_rejects") == "missing id"
    check("a row missing its natural key is rejected with a reason, not dropped")


def test_rfis(con) -> None:
    assert one(con, "SELECT COUNT(*) FROM cd_silver_rfis") == 2
    assert one(con, "SELECT subject FROM cd_silver_rfis WHERE item_id='R1'") == "Slab edge"
    # An unanswered RFI has no responded_date - that is what fct_RfiSubmittal[IsOpen] reads.
    assert one(con, "SELECT responded_date FROM cd_silver_rfis WHERE item_id='R1'") is None
    assert one(con, "SELECT responded_date FROM cd_silver_rfis WHERE item_id='R2'") == date(2025, 4, 10)
    check("RFIs parse - the half of the workbook's chart never automated before")

    # priority is carried through so "critical" can be answered from data once Affect
    # defines it (open question #5), rather than being guessed now.
    assert one(con, "SELECT priority FROM cd_silver_rfis WHERE item_id='R1'") == "High"
    check("RFI priority is carried through for the unresolved 'critical' definition")


def test_column_contract(con) -> None:
    """Silver must expose exactly what the switch file expects.

    This is the check that makes the migration safe. If silver drifts from the sv_*
    contract, switching gold's source breaks nine gold files at once - and it would break
    in Fabric, not here.
    """
    # The switch file reads through abfss, not bare table names - gold's notebook runs with
    # CD_Gold_Lakehouse as its default catalog, so an unqualified cd_silver_projects does
    # not resolve. Match the table name wherever it appears in the FROM clause:
    #     FROM delta.`{CD_SILVER_ABFSS}/cd_silver_projects`
    import re

    required = {}
    for statement in split_statements(SWITCH_SQL.read_text(encoding="utf-8")):
        match = re.search(r"FROM\s+\S*?(cd_silver_\w+)", statement)
        if not match:
            continue                     # a view still sourced from the existing warehouse
        table = match.group(1).removeprefix("cd_silver_")
        body = statement.split("SELECT", 1)[1].split("FROM")[0]
        cols = {
            part.split(" AS ")[-1].strip() if " AS " in part else part.strip()
            for part in body.split(",")
            if part.strip() and "CAST(NULL" not in part and "'PROCORE'" not in part
        }
        required.setdefault(f"cd_silver_{table}", set()).update(cols)

    checked = 0
    for table, cols in required.items():
        actual = {
            r[0] for r in con.execute(
                "SELECT column_name FROM information_schema.columns "
                f"WHERE table_name = '{table}'"
            ).fetchall()
        }
        if not actual:
            continue  # sourced elsewhere (Sage AR, Outbuild) - not built by this file
        missing = {c for c in cols if c and c not in actual}
        assert not missing, f"{table} is missing {sorted(missing)} required by the switch"
        checked += 1

    assert checked >= 6, f"only {checked} tables cross-checked"
    check(f"all {checked} silver tables satisfy the sv_* column contract")


def main() -> int:
    con = build()
    for fn in (test_parsing, test_sentinel_dates, test_rejects, test_rfis,
               test_column_contract):
        fn(con)
    for label in CHECKS:
        print(f"  ok  {label}")
    print(f"\ntest_silver: {len(CHECKS)} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
