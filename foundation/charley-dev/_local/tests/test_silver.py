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
# 30_manual_silver.sql and 31_qc_manual_silver.sql are IN now, matching deploy_silver.py.
# They were excluded while the manual bronze tables did not exist; cd_06_land_manual
# creates them, so the parsers are deployed and must be tested.
SILVER_SQL = sorted(p for p in SILVER_DIR.glob("*.sql") if p.name[:2] not in ("00", "01"))
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
    # Outbuild. Two projects: OB1 is integrated with Procore, OB2 is NOT - which is the
    # live shape (only 3 of 15 carry a procore_id). Schedules are a nested JSON array, and
    # the activity's ONLY route to a project is through them.
    "cd_bronze_outbuild_projects": [
        bronze_row("OB1", {"id": 4001, "name": "Tower A", "procore_id": "7",
                           "schedules": [{"id": 9001, "name": "Main Schedule",
                                          "is_current_schedule": True}]}),
        bronze_row("OB2", {"id": 4002, "name": "Unintegrated Site", "procore_id": None,
                           "schedules": [{"id": 9002, "name": "Main Schedule",
                                          "is_current_schedule": True}]}),
    ],
    "cd_bronze_outbuild_activities": [
        # progress 50 on the wire. Gold's contract is a 0-1 fraction, so silver must land
        # 0.5 - the single most consequential line in this parser.
        bronze_row("A1", {"id": 14971, "name": "  Foundation complete  ", "schedule_id": 9001,
                          "start_date": "2025-05-01T08:00:00.000",
                          "end_date": "2025-06-30T17:00:00.000",
                          "progress": 50, "duration": 60, "is_critical": True,
                          "activity_type": "task",
                          "baseline_start_date": "2025-05-01T08:00:00.000",
                          "baseline_end_date": "2025-06-20T17:00:00.000",
                          "baseline_duration": 50}),
        # 100 on the wire must become exactly 1.0, or IsOverdue's `progress < 1` misfires.
        bronze_row("A2", {"id": 14972, "name": "Done", "schedule_id": 9001,
                          "start_date": "2025-05-01T08:00:00.000",
                          "end_date": "2025-06-30T17:00:00.000",
                          "progress": 100, "duration": 10, "is_critical": True,
                          "activity_type": "task"}),
        # Belongs to the UNINTEGRATED project: must survive silver with a NULL project_id
        # and a named Outbuild project, not be dropped.
        bronze_row("A3", {"id": 14973, "name": "Orphan", "schedule_id": 9002,
                          "start_date": "2025-05-01T08:00:00.000",
                          "end_date": "2025-06-30T17:00:00.000",
                          "progress": 25, "duration": 5, "is_critical": True,
                          "activity_type": "task"}),
    ],
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
    # Commitments: a subcontract and a purchase order, with their line items. Procore
    # spells the vendor NAME as vendor.company on these endpoints, not vendor.name.
    "cd_bronze_procore_work_order_contracts": [
        bronze_row("SC1", {"id": "SC1", "number": "SC-1", "title": "  HVAC  ",
                           "status": "approved", "grand_total": "390000.0",
                           "total_payments": "30485.0",
                           "total_requisitions_amount": "30485.0", "executed": True,
                           "vendor": {"id": "V1", "company": "  Demar Plumbing  "}},
                   project_id="7"),
    ],
    "cd_bronze_procore_purchase_order_contracts": [
        bronze_row("PO1", {"id": "PO1", "number": "PO-1", "title": "Equipment",
                           "status": "approved", "grand_total": "28000.0",
                           "executed": True,
                           "vendor": {"id": "V3", "company": "Daikin"}}, project_id="7"),
    ],
    "cd_bronze_procore_work_order_contract_line_items": [
        bronze_row("CL1", {"id": "CL1",
                           "holder": {"id": "SC1", "holder_type": "WorkOrderContract"},
                           "cost_code": {"id": "CC1", "full_code": "03-100",
                                         "name": "03-100 - CONCRETE"},
                           "description": "HVAC", "line_item_type": {"name": "Material"},
                           "amount": "390000.0", "total_amount": "390000.0"},
                   project_id="7"),
    ],
    "cd_bronze_procore_purchase_order_contract_line_items": [
        bronze_row("CL2", {"id": "CL2",
                           "holder": {"id": "PO1", "holder_type": "PurchaseOrderContract"},
                           "cost_code": {"id": "CC2", "full_code": "06-100",
                                         "name": "06-100 - CARPENTRY"},
                           "description": "DAIKIN", "line_item_type": {"name": "Material"},
                           "amount": "28000.0", "total_amount": "28000.0",
                           "quantity": "1.0", "unit_cost": "28000.0"}, project_id="7"),
    ],
    # Phase 0 items 3 and 4: the vendor <-> cost-code bridge, and insurance.
    "cd_bronze_procore_direct_cost_line_items": [
        bronze_row("L1", {"id": "L1", "holder": {"id": "D1", "holder_type": "DirectCost::Item"},
                          "cost_code": {"id": "CC1", "full_code": "03-100",
                                        "name": "03-100 - CONCRETE"},
                          "description": "Slab pour", "line_item_type": {"name": "Material"},
                          "amount": "1000.0", "total_amount": "1100.0",
                          "quantity": "1.0", "unit_cost": "1000.0", "uom": "ls"},
                   project_id="7"),
        # Same vendor, same cost code, second line - must roll up rather than double-row.
        bronze_row("L2", {"id": "L2", "holder": {"id": "D1", "holder_type": "DirectCost::Item"},
                          "cost_code": {"id": "CC1", "full_code": "03-100",
                                        "name": "03-100 - CONCRETE"},
                          "description": "Slab pour 2", "amount": "500.0",
                          "total_amount": "500.0"}, project_id="7"),
        # A holder that is NOT a direct cost. Procore reuses `holder` across object types,
        # and joining this to a direct cost id would attribute it to the wrong vendor.
        bronze_row("L3", {"id": "L3", "holder": {"id": "D1", "holder_type": "Commitment::Item"},
                          "cost_code": {"id": "CC1", "full_code": "03-100"},
                          "amount": "9999.0", "total_amount": "9999.0"}, project_id="7"),
    ],
    "cd_bronze_procore_company_insurances": [
        bronze_row("I1", {"id": "I1", "vendor_id": "V1", "insurance_type": "  GL  ",
                          "insurance_provider": "Farm Family", "policy_number": "PN-1",
                          "status": "non_compliant", "effective_date": "2022-08-26",
                          "expiration_date": "2023-08-26", "limit": "24.0",
                          "exempt": False, "info_received": True,
                          "additional_insured": True, "notes": ""}, project_id=None),
        bronze_row("I2", {"id": "I2", "vendor_id": "V2", "insurance_type": "Auto",
                          "status": "compliant", "expiration_date": "2030-01-01",
                          "exempt": False, "policy_number": ""}, project_id=None),
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
    # Procore Inspections. The one genuinely new payload the PQP work landed, and the
    # candidate that could eventually retire the 26 hand-kept trade checklist sheets -
    # it IS a per-project instance of a checklist template.
    "cd_bronze_procore_checklist_lists": [
        bronze_row("IN1", {"id": "IN1", "number": "1", "name": "  Slab pour pre-check  ",
                           "inspection_type": {"name": "Quality"},
                           "list_template": {"name": "Concrete Pre-Pour"},
                           "trade": {"name": "  Concrete Formwork  "},
                           "inspector": {"name": "J. Alvarez"}, "status": "closed",
                           "inspection_date": "2025-05-08", "due_date": "2025-05-08",
                           "percent_complete": "100.0"}, project_id="7"),
        # No id: REJECTED by the WHERE, not silently typed into a NULL-keyed row.
        bronze_row("", {"name": "Broken inspection"}, project_id="7"),
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


# --------------------------------------------------------------------------
# Manual bronze - a DIFFERENT shape, which is exactly why it needs its own fixtures.
#
# The Procore tables above hold one JSON string. The manual tables hold one typed column
# per list column, with ProjectKey and Editor as SharePoint's {Title: ...} struct. A stub
# of NULL scalars cannot satisfy `ProjectKey.Title`, which is why these parsers went
# untested for as long as they did.
#
# GENERATED from the same two sources the pipeline uses - make_sharepoint.tables() for the
# columns and deploy_manual.EXAMPLES for the values - rather than hand-written. Seventeen
# hand-kept fixtures is seventeen more things to forget when a column is added, and the
# failure would be silent: the parser would still run, just not over the new column.
#
# TWO ROWS PER LIST. Project '7' exists in cd_silver_projects and must survive; '26-001'
# does not and must be rejected. That pair is the whole point of the silver layer here.
# --------------------------------------------------------------------------
GOOD_PROJECT = "7"
BAD_PROJECT = "26-001"


NULL_AS = {"STRING": "VARCHAR", "INT": "INTEGER", "DOUBLE": "DOUBLE",
           "DATE": "DATE", "BOOLEAN": "BOOLEAN"}


def _literal(value: str, sql_type: str) -> str:
    value = (value or "").strip()
    if value == "":
        # A bare NULL comes out INTEGER, and TRIM(INTEGER) is a binder error rather than
        # the empty column it is meant to stand for.
        return f"CAST(NULL AS {NULL_AS[sql_type]})"
    if sql_type == "STRING":
        return "'" + value.replace("'", "''") + "'"
    if sql_type == "DATE":
        return f"DATE '{value}'"
    if sql_type == "BOOLEAN":
        return value.upper()
    return f"CAST('{value}' AS {'INT' if sql_type == 'INT' else 'DOUBLE'})"


def manual_bronze() -> dict[str, str]:
    """cd_bronze_man_* table name -> the CREATE statement that fixtures it."""
    import deploy_manual as dm
    import make_sharepoint as ms

    out: dict[str, str] = {}
    for table, cols in ms.tables().items():
        example = dm.EXAMPLES[ms.csv_name(table)]
        names = ", ".join(c for c, _ in cols) + ", Modified, Editor"
        rows = []
        for project in (GOOD_PROJECT, BAD_PROJECT):
            values = [f"{{'Title': '{project}'}}"]
            values += [_literal(v, t) for (c, t), v in zip(cols, example) if c != "ProjectKey"]
            values.append("TIMESTAMP '2026-08-01 12:00:00'")
            values.append("{'Title': 'csv:fixture'}")
            rows.append("(" + ", ".join(values) + ")")
        out[ms.bronze_table(table)] = (
            f"CREATE OR REPLACE TABLE {ms.bronze_table(table)} AS "
            f"SELECT * FROM (VALUES {', '.join(rows)}) AS t({names})"
        )

    # The Job Register, off the BUILD site. Not driven by ms.tables() because it is not a
    # man_* table - the Power Automate flows own it, not the CSV templates.
    #
    # The fixture is built around the one thing this parser has to get right: rows 2 and 4
    # are DIFFERENT JOBS THAT WERE BOTH ISSUED 26-002, which is what a race between two
    # flow runs produces. Both must survive to gold so the DQ gate can fail on them.
    # Deduplicating on JobNumber instead of Id would discard one and hide the collision.
    # Row 3 is a job somebody has just asked for and the flow has not numbered yet - the
    # normal resting state of a healthy register, and it must not be dropped either.
    # Row 5 repeats Id 4 at an older timestamp: THAT is what dedup is for.
    url = "{{'Url': '{}'}}"
    none_url = "CAST(NULL AS STRUCT(Url VARCHAR))"
    editor = "{'Title': 'flow:EstimatingSetup'}"
    # DuckDB types a bare NULL in a VALUES list as INTEGER, and a column that is NULL in
    # every fixture row then reaches TRIM() as an integer. Spelled out rather than relying
    # on inference from whichever row happens to be first.
    ns, ni, nt = "CAST(NULL AS VARCHAR)", "CAST(NULL AS INTEGER)", "CAST(NULL AS TIMESTAMP)"
    register_rows = [
        f"(1, 'Fulton Street Fit-Out', 26, 1, '26-001', 'Estimating', "
        f"{url.format('/sites/BUILD/01 ESTIMATING/E-26-001-Fulton Street Fit-Out')}, "
        f"{none_url}, 'pm@example.com', TIMESTAMP '2026-07-01 09:00:00', "
        f"TIMESTAMP '2026-07-01 09:01:00', 'Copied 12 item(s)', {ns}, "
        f"TIMESTAMP '2026-07-01 09:01:00', {editor})",

        f"(2, 'Bergen Street Retail', 26, 2, '26-002', 'Bidding', "
        f"{url.format('/sites/BUILD/01 ESTIMATING/E-26-002-Bergen Street Retail')}, "
        f"{url.format('/sites/BUILD/00 PROJECTS/26-002-Bergen Street Retail')}, "
        f"'pm@example.com', TIMESTAMP '2026-07-02 09:00:00', "
        f"TIMESTAMP '2026-07-02 09:02:00', 'Copied 31 item(s)', {ns}, "
        f"TIMESTAMP '2026-07-02 09:02:00', {editor})",

        f"(3, 'Not Numbered Yet', {ni}, {ni}, {ns}, 'Requested', {none_url}, {none_url}, "
        f"'pm@example.com', TIMESTAMP '2026-07-03 09:00:00', {nt}, {ns}, {ns}, "
        f"TIMESTAMP '2026-07-03 09:00:00', {editor})",

        f"(4, 'Court Square Lobby', 26, 2, '26-002', 'Estimating', "
        f"{url.format('/sites/BUILD/01 ESTIMATING/E-26-002-Court Square Lobby')}, "
        f"{none_url}, 'pm2@example.com', TIMESTAMP '2026-07-02 09:00:01', "
        f"TIMESTAMP '2026-07-02 09:00:09', 'Copied 12 item(s)', {ns}, "
        f"TIMESTAMP '2026-07-02 09:00:09', {editor})",

        f"(4, 'Court Square Lobby', 26, 2, '26-002', 'Requested', {none_url}, {none_url}, "
        f"'pm2@example.com', TIMESTAMP '2026-07-02 09:00:01', {nt}, {ns}, {ns}, "
        f"TIMESTAMP '2026-07-02 09:00:02', {editor})",
    ]
    out["cd_bronze_man_job_register"] = (
        "CREATE OR REPLACE TABLE cd_bronze_man_job_register AS "
        f"SELECT * FROM (VALUES {', '.join(register_rows)}) AS t("
        "Id, Title, JobYear, JobSeq, JobNumber, Stage, EstimatingFolderUrl, "
        "ProjectFolderUrl, RequestedBy, RequestedAt, CompletedAt, CopyJobStatus, "
        "ErrorDetail, Modified, Editor)"
    )
    return out


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
    for statement in manual_bronze().values():
        con.execute(statement)
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


def test_vendor_costcode_and_insurance(con) -> None:
    """Phase 0 items 3 and 4 - the bridge, and the certificates."""
    assert one(con, "SELECT COUNT(*) FROM cd_silver_direct_cost_lines") == 3
    # full_code is the CSI code; `name` repeats it with a description glued on. Reading the
    # code out of the name is the defect that left 5,429 of 5,433 divisions unparsed.
    assert one(con, "SELECT cost_code FROM cd_silver_direct_cost_lines WHERE line_item_id='L1'") \
        == "03-100"
    assert one(con, "SELECT direct_cost_id FROM cd_silver_direct_cost_lines "
                    "WHERE line_item_id='L1'") == "D1"
    check("direct cost lines carry the cost code AND the header that owns them")

    assert one(con, "SELECT holder_type FROM cd_silver_direct_cost_lines "
                    "WHERE line_item_id='L3'") == "Commitment::Item"
    check("holder_type is kept, so a non-direct-cost line can be excluded downstream")

    assert one(con, "SELECT COUNT(*) FROM cd_silver_vendor_insurance") == 2
    assert one(con, "SELECT insurance_type FROM cd_silver_vendor_insurance "
                    "WHERE insurance_id='I1'") == "GL"
    assert one(con, "SELECT expiration_date FROM cd_silver_vendor_insurance "
                    "WHERE insurance_id='I1'") == date(2023, 8, 26)
    check("insurance certificates parse with their expiry date")

    # Procore writes "" for an unrecorded policy number. Left as-is it reads on a
    # compliance report as a policy that exists and happens to be blank.
    assert one(con, "SELECT policy_number FROM cd_silver_vendor_insurance "
                    "WHERE insurance_id='I2'") is None
    check("blank policy numbers become real nulls, not empty strings")


def test_commitments(con) -> None:
    """Subcontracts and purchase orders - the committed half of the bridge."""
    # Two endpoints, one table, same reason requisitions and payment applications union.
    assert one(con, "SELECT COUNT(*) FROM cd_silver_commitments") == 2
    assert one(con, "SELECT commitment_type FROM cd_silver_commitments "
                    "WHERE commitment_id='SC1'") == "Subcontract"
    assert one(con, "SELECT commitment_type FROM cd_silver_commitments "
                    "WHERE commitment_id='PO1'") == "Purchase Order"
    check("work orders and purchase orders union into one commitment table")

    # vendor.company, not vendor.name. Procore uses "company" for the vendor's name on
    # these endpoints and for a nested object elsewhere - assuming rather than reading it
    # is how a column silently becomes NULL.
    assert one(con, "SELECT vendor_name FROM cd_silver_commitments "
                    "WHERE commitment_id='SC1'") == "Demar Plumbing"
    assert one(con, "SELECT vendor_id FROM cd_silver_commitments "
                    "WHERE commitment_id='SC1'") == "V1"
    check("the vendor resolves from vendor.company, trimmed")

    assert one(con, "SELECT COUNT(*) FROM cd_silver_commitment_lines") == 2
    assert one(con, "SELECT cost_code FROM cd_silver_commitment_lines "
                    "WHERE line_item_id='CL1'") == "03-100"
    assert one(con, "SELECT commitment_id FROM cd_silver_commitment_lines "
                    "WHERE line_item_id='CL1'") == "SC1"
    check("commitment lines carry the cost code and the contract that owns them")

    # holder_type distinguishes the two id spaces. Without it a work order line can be
    # joined to a purchase order that happens to share the id.
    assert one(con, "SELECT holder_type FROM cd_silver_commitment_lines "
                    "WHERE line_item_id='CL2'") == "PurchaseOrderContract"
    check("holder_type is kept so colliding contract ids cannot cross-join")

def test_manual_parsers(con) -> None:
    """30_manual_silver.sql and 31_qc_manual_silver.sql - the parsers that were never run.

    Both were excluded from the deploy and from this suite while the manual bronze tables
    did not exist. They exist (cd_06_land_manual creates them), so these run now, and the
    thing worth asserting is that a hand-typed row survives the trip and a bad one does not.
    """
    import make_sharepoint as ms

    # Every list produces exactly ONE silver row: the '7' row survives, the '26-001' row
    # is rejected for pointing at a project that does not exist.
    for table in ms.tables():
        silver = "cd_silver_man_" + ms.bronze_table(table)[len("cd_bronze_man_"):]
        n = one(con, f"SELECT COUNT(*) FROM {silver}")
        assert n == 1, f"{silver}: {n} row(s), expected 1 (the unknown project must reject)"
        assert one(con, f"SELECT project_id FROM {silver}") == GOOD_PROJECT
    check(f"all {len(ms.tables())} manual lists parse, and an unknown project is rejected")

    # The four columns that used to disagree with gold. Each one is why man_* could not be
    # populated: the parser simply did not produce what the DDL asked for.
    assert one(con, "SELECT logs_missed_same_day FROM cd_silver_man_daily_log_compliance") == 3
    assert one(con, "SELECT surveyed_party FROM cd_silver_man_survey") == "ANONYMOUS"
    assert one(con, "SELECT month_end_closed_out FROM cd_silver_man_flags") is True
    assert one(con, "SELECT contract_finish FROM cd_silver_man_milestones") == date(2027, 3, 31)
    check("the four columns that had drifted from the gold DDL now parse")

    # ProfitabilityCode matches dim_ScorecardBand[MatchValue], which holds LABELS.
    # Upper-casing it would match nothing, silently.
    assert one(con, "SELECT profitability_code FROM cd_silver_man_flags") == "Within Range"
    check("ProfitabilityCode keeps its label casing, so the band join still resolves")

    # MonthStart floored to the 1st - the dim_Date join. The example rows are already the
    # 1st, so this asserts the floor did not MOVE them, which a wrong trunc() would.
    assert one(con, "SELECT month_start FROM cd_silver_man_wins") == date(2026, 7, 1)
    check("MonthStart is floored to the 1st of the reporting month")

    # ------------------------------------------------------------- the Job Register
    #
    # THE ASSERTION THAT MATTERS: two different jobs both issued 26-002 BOTH SURVIVE.
    #
    # That collision is what happens when somebody switches off trigger concurrency on the
    # Power Automate flows, and it is the whole reason dim_Job is worth building. If this
    # parser deduplicated on JobNumber - the obvious thing to do to a column called
    # "number" - one of the two real jobs would vanish here and the DQ gate downstream
    # would have nothing left to fail on. The bug would then surface weeks later, as two
    # folder trees with real documents in both.
    n = one(con, "SELECT COUNT(*) FROM cd_silver_man_job_register WHERE job_number = '26-002'")
    assert n == 2, f"the 26-002 collision collapsed to {n} row(s) - dedup is on the wrong key"
    check("two jobs issued the same number both survive, so the DQ gate can fail on them")

    # Dedup IS applied, just on the right key: Id 4 appears twice and collapses to its
    # latest Modified.
    assert one(con, "SELECT COUNT(*) FROM cd_silver_man_job_register") == 4
    assert one(con, "SELECT stage FROM cd_silver_man_job_register WHERE register_id = 4") \
        == "ESTIMATING"
    check("the same register row landed twice collapses to its latest version")

    # A job somebody has just asked for has no number yet. That is the normal resting state
    # of a healthy register, not a defect, and dropping it would under-count the pipeline.
    assert one(con, "SELECT job_number FROM cd_silver_man_job_register "
                    "WHERE register_id = 3") is None
    check("a job still awaiting its number is kept, not dropped")

    # URL columns arrive as records; silver takes .Url or the link is lost.
    assert one(con, "SELECT project_folder_url FROM cd_silver_man_job_register "
                    "WHERE register_id = 2").endswith("26-002-Bergen Street Retail")
    check("SharePoint URL columns are unwrapped to the link itself")

    # And the half-run flow reaches the reject log with a reason, rather than nowhere.
    assert one(con, "SELECT COUNT(*) FROM cd_dq_rejects_manual "
                    "WHERE target_table = 'cd_silver_man_job_register'") == 0, \
        "no fixture row is past Requested without a number, so nothing should reject"
    check("a healthy register produces no job-register rejects")

    # An unknown project is REJECTED WITH A REASON, not dropped. Two of the eight PQP
    # lists log it, plus the gate collapse's own new failure mode.
    assert one(con, "SELECT COUNT(*) FROM cd_dq_rejects_qc "
                    "WHERE reason LIKE 'unknown project%'") == 3
    check("PQP rows for an unknown project land in cd_dq_rejects_qc with a reason")


def test_qc_procore_parser(con) -> None:
    """24_qc_procore_silver.sql - Procore's status text mapped to the workbook's codes."""
    # One row in, one row out - no filtering to "quality" observations. The workbook's NCR
    # log and Procore's observation list are the same population viewed differently, and
    # filtering here would make the two counts disagree by an amount nobody can reconcile.
    assert one(con, "SELECT COUNT(*) FROM cd_silver_qc_ncr") == 1
    assert one(con, "SELECT status_code FROM cd_silver_qc_ncr WHERE ncr_id='O1'") == "CLOSED"
    check("Procore observation status maps to the workbook's NCR vocabulary")

    # Procore's own text is KEPT alongside the mapped code. Without it an unmapped value is
    # a NULL with nothing to look at, and the mapping cannot be corrected from the data.
    assert one(con, "SELECT source_status FROM cd_silver_qc_ncr WHERE ncr_id='O1'") == "CLOSED"
    check("the raw Procore status is carried next to the mapped code")

    # Observation type 'Safety' says nothing about COR/NCR/WIP, so the class is NULL rather
    # than defaulted to 'NCR'. A default here would report every safety observation as a
    # non-conformance, which is a number leadership would act on.
    assert one(con, "SELECT item_class_code FROM cd_silver_qc_ncr WHERE ncr_id='O1'") is None
    check("an observation type that implies no NCR class stays NULL, not defaulted")

    assert one(con, "SELECT status_code FROM cd_silver_qc_punch "
                    "WHERE punch_id='PI1'") == "CLOSED"
    assert one(con, "SELECT item_class_code FROM cd_silver_qc_punch "
                    "WHERE punch_id='PI1'") == "PUNCH_ITEM"
    check("punch items classify into the Punch & RCL vocabulary")

    assert one(con, "SELECT status_code FROM cd_silver_qc_submittal "
                    "WHERE submittal_id='SB1'") == "OPEN"
    check("submittal disposition maps to the Submittals & Mockups vocabulary")

    # The new endpoint parses, and a payload with no id is rejected by the WHERE.
    assert one(con, "SELECT COUNT(*) FROM cd_silver_qc_inspection") == 1
    assert one(con, "SELECT trade FROM cd_silver_qc_inspection") == "Concrete Formwork"
    check("Procore Inspections (checklist/lists) parses, trimmed, keyless rows dropped")


def test_outbuild_parser(con) -> None:
    """25_outbuild_silver.sql - the parser fct_Milestone reads, and its two traps."""
    # Nothing is dropped. Three activities in, three out - including the one whose project
    # has no Procore integration.
    assert one(con, "SELECT COUNT(*) FROM cd_silver_outbuild_activities") == 3
    check("every Outbuild activity survives silver, attributed or not")

    # THE TRAP. Outbuild sends progress as 0-100; gold documents its contract as a 0-1
    # fraction and the gold fixture uses 0.5. Landing 50 here would make
    # `Avg Milestone Progress` read 5000%, and IsOverdue - which tests
    # `COALESCE(progress,0) < 1` - would call every activity past 1% complete and report
    # ZERO overdue milestones on a late job.
    assert one(con, "SELECT progress FROM cd_silver_outbuild_activities "
                    "WHERE activity_id='14971'") == 0.5
    assert one(con, "SELECT progress FROM cd_silver_outbuild_activities "
                    "WHERE activity_id='14972'") == 1.0
    check("progress is normalised from Outbuild's 0-100 to the 0-1 fraction gold expects")

    # An activity carries no project. The route is schedule_id -> project.schedules[].id
    # -> project.procore_id, and it must land the PROCORE id, not Outbuild's own.
    assert one(con, "SELECT project_id FROM cd_silver_outbuild_activities "
                    "WHERE activity_id='14971'") == "7"
    check("an activity resolves to its PROCORE project through the schedule map")

    # The unintegrated project: NULL project_id, but named, so "which schedules are we
    # failing to attribute" is a query rather than a re-extract. Gold's
    # `WHERE project_id IS NOT NULL` is what excludes it - that decision is not silver's.
    assert one(con, "SELECT project_id FROM cd_silver_outbuild_activities "
                    "WHERE activity_id='14973'") is None
    assert one(con, "SELECT outbuild_project_name FROM cd_silver_outbuild_activities "
                    "WHERE activity_id='14973'") == "Unintegrated Site"
    check("an activity on a project with no procore_id keeps a NULL key and a real name")

    # Outbuild has no status on an activity; Rebecca's `Status` column was hers. NULL
    # rather than derived from progress, which would be a guess dressed as data.
    assert one(con, "SELECT status FROM cd_silver_outbuild_activities "
                    "WHERE activity_id='14971'") is None
    check("status stays NULL - Outbuild has no such field, and it is not invented")

    assert one(con, "SELECT activity_name FROM cd_silver_outbuild_activities "
                    "WHERE activity_id='14971'") == "Foundation complete"
    # Baselines exist on the wire and are landed, so wiring StartVariance later is a gold
    # change rather than another extract.
    assert one(con, "SELECT baseline_duration FROM cd_silver_outbuild_activities "
                    "WHERE activity_id='14971'") == 50.0
    check("names are trimmed and baseline dates are landed for later variance work")


def main() -> int:
    con = build()
    for fn in (test_parsing, test_sentinel_dates, test_rejects, test_rfis,
               test_column_contract, test_billing_and_costs, test_fieldops, test_vendor_costcode_and_insurance, test_commitments,
               test_manual_parsers, test_qc_procore_parser, test_outbuild_parser):
        fn(con)
    for label in CHECKS:
        print(f"  ok  {label}")
    print(f"\ntest_silver: {len(CHECKS)} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
