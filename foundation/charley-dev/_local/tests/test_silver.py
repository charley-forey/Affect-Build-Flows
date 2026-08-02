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
# The SAME selection deploy_silver.py makes, for the same reason: a test that runs one
# hand-named file while the deploy runs six is not testing the deploy. 20_fieldops_silver
# and 21_financial_silver were both invisible here until this became a glob.
SILVER_DIR = CHARLEY_DEV / "02-transformation" / "sql" / "silver"
SILVER_SQL = sorted(p for p in SILVER_DIR.glob("*.sql") if p.name[:2] not in ("00", "01", "30"))
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
    # Field ops. These parsers shipped with no offline fixture at all - the test named one
    # SQL file by hand and never reached them. The glob that replaced it found this.
    "cd_bronze_procore_observations": [
        bronze_row("O1", {"id": "O1", "number": "1", "name": "  Missing guardrail  ",
                          "type": {"name": "Safety"}, "category": {"name": "Fall"},
                          # lowercase here...
                          "status": "closed", "priority": "High", "trade": "Concrete",
                          "assignee": {"name": "A Foreman"},
                          "created_at": "2025-05-01", "due_date": "2025-05-08",
                          "closed_at": "2025-05-05"}, project_id="7"),
    ],
    "cd_bronze_procore_punch_items": [
        bronze_row("PI1", {"id": "PI1", "position": "1", "name": "Touch up paint",
                           "punch_item_type": {"name": "Finish"},
                           # ...and title case here, on the same concept one endpoint over.
                           "status": "Closed", "workflow_status": "closed",
                           "priority": "Low", "trade": "Painting",
                           "cost_code": {"id": "CC1"},
                           "punch_item_manager": {"name": "A PM"},
                           "created_at": "2025-05-01", "due_date": "2025-05-20",
                           "closed_at": None, "overdue": True}, project_id="7"),
    ],
    "cd_bronze_procore_incidents": [
        bronze_row("I1", {"id": "I1", "title": "Cut hand", "status": "closed",
                          "recordable": True, "event_date": "2025-05-10",
                          "time_of_event": "09:30", "created_at": "2025-05-10"},
                   project_id="7"),
    ],
    "cd_bronze_procore_manpower_logs": [
        # One row PER VENDOR PER DAY. Two vendors on the same day must roll into one
        # project-day or every safety rate double-counts its own denominator.
        bronze_row("M1", {"date": "2025-05-01", "man_hours": "24.0",
                          "num_workers": "3"}, project_id="7"),
        bronze_row("M2", {"date": "2025-05-01", "man_hours": "16.0",
                          "num_workers": "2"}, project_id="7"),
    ],
    # Progress billing. Two endpoints, one silver table - and the percent format differs
    # between them, which is the whole reason this fixture has both.
    "cd_bronze_procore_requisitions": [
        bronze_row("Q1", {"id": "Q1", "invoice_number": "1", "number": 1,
                          "status": "approved", "vendor_id": "V1", "vendor_name": "Demar",
                          "commitment_id": "SC1", "contract_name": "Contract SC-1",
                          "commitment_type": "WorkOrderContract",
                          "billing_date": "2025-05-31", "requisition_start": "2025-05-01",
                          "requisition_end": "2025-05-31",
                          # WITH a percent sign. A bare CAST of this is NULL.
                          "percent_complete": "9.28%",
                          "summary": {"original_contract_sum": "1000000.00", "net_change_by_change_orders": "0.00", "contract_sum_to_date": "1000000.00", "total_completed_and_stored_to_date": "250000.00", "less_previous_certificates_for_payment": "0.00", "completed_work_retainage_percent": "5.00", "stored_materials_retainage_amount": "0.00", "total_retainage": "12500.00", "total_earned_less_retainage": "237500.00", "current_payment_due": "237500.00", "balance_to_finish_including_retainage": "762500.00", "completed_work_retainage_amount": "12500.00"}}, project_id="7"),
    ],
    "cd_bronze_procore_payment_applications": [
        bronze_row("PA1", {"id": "PA1", "invoice_number": "1", "number": 1,
                           "status": "approved",
                           "formatted_contract_company": "Friends of Prospect",
                           "contract": {"id": "PC1", "title": "Prime",
                                        "type": "PrimeContract"},
                           "billing_date": "2025-05-31", "period_start": "2025-05-01",
                           "period_end": "2025-05-31",
                           # WITHOUT one, on the same concept, from the same API.
                           "percent_complete": "25.07",
                           "g702": {"original_contract_sum": "1000000.00", "net_change_by_change_orders": "0.00", "contract_sum_to_date": "1000000.00", "total_completed_and_stored_to_date": "250000.00", "less_previous_certificates_for_payment": "0.00", "completed_work_retainage_percent": "5.00", "stored_materials_retainage_amount": "0.00", "total_retainage": "12514.28", "total_earned_less_retainage": "237500.00", "current_payment_due": "237500.00", "balance_to_finish_including_retainage": "762500.00", "completed_work_retainage_amount": "12514.28"}}, project_id="7"),
    ],
    "cd_bronze_procore_direct_costs": [
        bronze_row("D1", {"id": "D1", "description": "  PM Payroll  ",
                          "direct_cost_type": "payroll", "status": "approved",
                          "vendor_id": "V1", "vendor_name": "Affect",
                          "employee": {"id": "E1", "name": "A Foreman"},
                          "direct_cost_date": "2025-05-31",
                          "amount": "11275.5", "grand_total": "11400.0"}, project_id="7"),
    ],
    "cd_bronze_procore_project_vendors": [
        bronze_row("V1", {"id": "V1", "name": "  Demar Plumbing  ",
                          "trade_name": "Demar LLC", "city": "New York",
                          "state_code": "NY", "prequalified": True, "is_active": True,
                          "union_member": False, "synced_to_erp": False,
                          # Empty strings, not nulls, is how Procore spells "not recorded".
                          "license_number": "", "labor_union": "",
                          "project_ids": ["7", "999"]}, project_id="7"),
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
    for path in SILVER_SQL:
        for statement in split_statements(path.read_text(encoding="utf-8")):
            try:
                con.execute(statement)
            except Exception as exc:
                # Named, because "silver SQL failed" across six files is a search, not a
                # diagnosis.
                raise RuntimeError(f"{path.name}: {exc}") from exc
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



def test_billing_and_costs(con) -> None:
    """Progress billing, direct costs and the vendor bridge - none previously parsed."""
    # One table from two endpoints. They describe opposite directions of the same AIA G702
    # form, so they union rather than living as two near-identical tables.
    assert one(con, "SELECT COUNT(*) FROM cd_silver_billing") == 2
    assert one(con, "SELECT billing_type FROM cd_silver_billing WHERE billing_id='Q1'") \
        == "Subcontractor"
    assert one(con, "SELECT billing_type FROM cd_silver_billing WHERE billing_id='PA1'") \
        == "Owner"
    check("requisitions and payment applications union into one billing table")

    # THE SILENT ONE. Procore writes "9.28%" on requisitions and "25.07" on payment
    # applications - same concept, same API, different format. An uncleaned CAST of the
    # first returns NULL, and a NULL percent complete reads on a card as a job that has
    # not started rather than as a parse failure.
    assert one(con, "SELECT percent_complete FROM cd_silver_billing WHERE billing_id='Q1'") == 9.28
    assert one(con, "SELECT percent_complete FROM cd_silver_billing WHERE billing_id='PA1'") == 25.07
    check("percent parses whether or not the endpoint writes a % sign")

    # Retainage, read from `summary` on one endpoint and `g702` on the other. This is the
    # figure Sage cannot supply - its invoice header is zero across all 940 rows.
    assert one(con, "SELECT retainage_amount FROM cd_silver_billing WHERE billing_id='Q1'") == 12500.0
    assert one(con, "SELECT retainage_amount FROM cd_silver_billing WHERE billing_id='PA1'") == 12514.28
    assert one(con, "SELECT contract_sum_to_date FROM cd_silver_billing WHERE billing_id='PA1'") \
        == 1000000.0
    check("the G702 block resolves under both its parent names")

    assert one(con, "SELECT cost_type FROM cd_silver_direct_costs") == "payroll"
    assert one(con, "SELECT description FROM cd_silver_direct_costs") == "PM Payroll"
    assert one(con, "SELECT grand_total FROM cd_silver_direct_costs") == 11400.0
    assert one(con, "SELECT employee_name FROM cd_silver_direct_costs") == "A Foreman"
    check("direct costs carry self-performed labour, which no other feed does")

    # The pair comes from _project_id, stamped by the extractor from the path it called -
    # not from the payload's project_ids array, which lists project 999 that we never read.
    assert one(con, "SELECT COUNT(*) FROM cd_silver_project_vendors") == 1
    assert one(con, "SELECT project_id FROM cd_silver_project_vendors") == "7"
    assert one(con, "SELECT vendor_name FROM cd_silver_project_vendors") == "Demar Plumbing"
    check("the vendor bridge pairs only projects we actually read")

    # "" is how Procore spells "not recorded". Left as an empty string it reads on a report
    # as a licence number that exists and happens to be blank.
    assert one(con, "SELECT license_number FROM cd_silver_project_vendors") is None
    check("Procore's empty-string placeholders become real nulls")


def test_fieldops(con) -> None:
    """The field-ops parsers, which had no offline coverage until the glob found them."""
    # `status` is lowercase on observations and title case on punch items - same concept,
    # one endpoint apart. UPPER on both means a downstream comparison cannot be defeated
    # by casing that varies per endpoint.
    assert one(con, "SELECT status_label FROM cd_silver_observations") == "CLOSED"
    assert one(con, "SELECT status_label FROM cd_silver_punch_items") == "CLOSED"
    check("status casing is normalised across endpoints that disagree about it")

    assert one(con, "SELECT title FROM cd_silver_observations") == "Missing guardrail"
    assert one(con, "SELECT observation_type FROM cd_silver_observations") == "Safety"
    assert one(con, "SELECT punch_item_type FROM cd_silver_punch_items") == "Finish"
    check("nested type and category names resolve on field-ops payloads")

    assert one(con, "SELECT is_recordable FROM cd_silver_incidents") is True
    check("the OSHA recordable flag survives as a boolean, not a string")

    # man_hours arrives as a STRING ("24.0"). Summed without an explicit cast this is the
    # kind of thing that concatenates quietly rather than failing.
    assert one(con, "SELECT total_hours FROM cd_silver_manpower_daily") == 40.0
    assert one(con, "SELECT total_workers FROM cd_silver_manpower_daily") == 5.0
    assert one(con, "SELECT vendor_entries FROM cd_silver_manpower_daily") == 2
    check("manpower sums per vendor per day into one project-day, from string hours")

def main() -> int:
    con = build()
    for fn in (test_parsing, test_sentinel_dates, test_rejects, test_rfis,
               test_column_contract, test_billing_and_costs, test_fieldops):
        fn(con)
    for label in CHECKS:
        print(f"  ok  {label}")
    print(f"\ntest_silver: {len(CHECKS)} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
