"""Generate and deploy the DirectLake semantic model over CD_Gold_Lakehouse.

    python deploy_model.py            # dry run - write TMDL to disk only
    python deploy_model.py --apply    # create/update the model in Fabric

The TMDL is GENERATED from the schema cd_30_build_gold publishes to the lakehouse on
every run, so the model's columns and types cannot drift from the tables. Read from
FABRIC rather than from the offline build on purpose: DuckDB infers DECIMAL where Spark
has DOUBLE, and a declared type that does not match makes Direct Lake drop the table
silently.

DirectLake, matching the existing workspace models (`mode: directLake`,
`schemaName: dbo`). Direct Lake framing determines which table versions readers see.
Automatic updates, explicit refreshes and failure isolation require separate verification;
a successful model deployment does not establish a validated publication boundary.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deploy as dp  # noqa: E402
import scorecard  # noqa: E402
import deploy_seeds as ds  # noqa: E402
from seedrunner import build  # noqa: E402

HERE = Path(__file__).resolve().parent
CHARLEY_DEV = HERE.parent
MODEL_DIR = CHARLEY_DEV / "04-semantic_models" / "Affect Project Report.SemanticModel"

MODEL_NAME = "Affect Project Report"

# DuckDB type -> TMDL dataType. Anything unmapped falls back to string, which is lossy but
# never breaks the model - and the assertion below catches it so it gets mapped properly.
TYPE_MAP = {
    # Spark simpleString() names, as published by cd_30_build_gold.
    "STRING": "string", "BIGINT": "int64", "INT": "int64", "SMALLINT": "int64",
    "DOUBLE": "double", "FLOAT": "double", "DATE": "dateTime", "TIMESTAMP": "dateTime",
    "BOOLEAN": "boolean",
    # Spark decimal(p,s) is fixed-point and exact, which is what money wants - float
    # dollars accumulate rounding error across thousands of rows.
    "DECIMAL": "decimal",
}

# Tables the model exposes, in field-list order. dim_Date first because it is the date
# table and everything hangs off it.
MODEL_TABLES = [
    "dim_Date", "dim_Project", "dim_Vendor", "dim_CostCode", "dim_Trade", "dim_Status",
    "dim_Owner", "dim_ActivityCategory", "dim_ScorecardWeight", "dim_ScorecardBand",
    "fct_BudgetLine", "fct_ChangeOrder", "fct_Invoice", "fct_RfiSubmittal",
    "fct_Milestone", "fct_FinancialPeriod", "fct_QualityItem", "fct_SafetyMonthly", "fct_Billing", "fct_DirectCost",
    "bridge_ProjectVendor", "bridge_VendorCostCode", "fct_VendorInsurance",
    # Sage AP lines - the ERP side of the cost reconciliation, never added to Spent To Date.
    "fct_ApInvoice",
    # The ~40% that lives nowhere but the spreadsheet. Empty today; bound now so the model
    # and the scorecard are complete in shape before a single row is entered.
    "man_Wins", "man_Risks", "man_PriorityItems", "man_Flags", "man_Survey",
    "man_SafetyMonthly", "man_QualityMonthly", "man_Milestones", "man_DailyLogCompliance",
    # Cross-source coverage. These answer "is this project actually in Sage and Outbuild,
    # or is it silently reading as zero revenue?" - which nothing else in the model can.
    "dim_ProjectCrosswalk", "dim_VendorCrosswalk", "dim_CostCodeCrosswalk",
    # Every known data gap in one register - silver rejects included - for the DQ page.
    "dq_DataGap",
    # The pipeline heartbeat. Not project data - it is how the report answers
    # "are these numbers from last night, or from three weeks ago?".
    "meta_PipelineRun",
    # Saved point-in-time KPIs, one row-set per passing nightly run. The only honest source
    # for "as of month X": every other fact is current state.
    "fct_DailySnapshot",
]

# fact.column -> dimension.column. Single direction, no bidirectional filters: they create
# ambiguity and hurt performance (powerbi/semantic-model.md:443).
RELATIONSHIPS = [
    # NOTE: the two scorecard config tables are deliberately NOT related. Relating them so
    # the band table could show a category name made Power BI add a blank unknown-member
    # row to dim_ScorecardWeight - which rendered as an empty row on the Scorecard page, an
    # empty column on the Portfolio heatmap, and broke the "weights sum to 1.00" assertion
    # because the blank row's weight is NULL. Verified against the deployed model, not
    # guessed. dim_ScorecardBand carries CategoryName as a column instead.
    ("fct_BudgetLine", "ProjectKey", "dim_Project", "ProjectKey"),
    ("fct_BudgetLine", "CostCodeKey", "dim_CostCode", "CostCodeKey"),
    ("fct_BudgetLine", "MonthStart", "dim_Date", "Date"),
    ("fct_ChangeOrder", "ProjectKey", "dim_Project", "ProjectKey"),
    ("fct_ChangeOrder", "MonthStart", "dim_Date", "Date"),
    ("fct_Invoice", "ProjectKey", "dim_Project", "ProjectKey"),
    ("fct_Invoice", "MonthStart", "dim_Date", "Date"),
    ("fct_RfiSubmittal", "ProjectKey", "dim_Project", "ProjectKey"),
    ("fct_QualityItem", "ProjectKey", "dim_Project", "ProjectKey"),
    ("fct_QualityItem", "MonthStart", "dim_Date", "Date"),
    ("fct_SafetyMonthly", "ProjectKey", "dim_Project", "ProjectKey"),
    ("fct_SafetyMonthly", "MonthStart", "dim_Date", "Date"),
    ("fct_Billing", "ProjectKey", "dim_Project", "ProjectKey"),
    ("fct_Billing", "MonthStart", "dim_Date", "Date"),
    ("fct_DirectCost", "ProjectKey", "dim_Project", "ProjectKey"),
    ("fct_DirectCost", "MonthStart", "dim_Date", "Date"),
    ("fct_ApInvoice", "ProjectKey", "dim_Project", "ProjectKey"),
    ("fct_ApInvoice", "VendorKey", "dim_Vendor", "VendorKey"),
    ("fct_ApInvoice", "MonthStart", "dim_Date", "Date"),
    ("bridge_ProjectVendor", "ProjectKey", "dim_Project", "ProjectKey"),
    ("bridge_VendorCostCode", "ProjectKey", "dim_Project", "ProjectKey"),
    ("bridge_VendorCostCode", "VendorKey", "dim_Vendor", "VendorKey"),
    ("bridge_VendorCostCode", "CostCodeKey", "dim_CostCode", "CostCodeKey"),
    ("fct_VendorInsurance", "VendorKey", "dim_Vendor", "VendorKey"),
    ("fct_RfiSubmittal", "CostCodeKey", "dim_CostCode", "CostCodeKey"),
    ("fct_RfiSubmittal", "MonthStart", "dim_Date", "Date"),
    ("fct_Milestone", "ProjectKey", "dim_Project", "ProjectKey"),
    ("fct_Milestone", "MonthStart", "dim_Date", "Date"),
    ("fct_FinancialPeriod", "ProjectKey", "dim_Project", "ProjectKey"),
    ("fct_FinancialPeriod", "MonthStart", "dim_Date", "Date"),
    ("dim_ProjectCrosswalk", "ProjectKey", "dim_Project", "ProjectKey"),
    ("dq_DataGap", "ProjectKey", "dim_Project", "ProjectKey"),
    ("man_Wins", "ProjectKey", "dim_Project", "ProjectKey"),
    ("man_Wins", "MonthStart", "dim_Date", "Date"),
    ("man_Risks", "ProjectKey", "dim_Project", "ProjectKey"),
    ("man_Risks", "MonthStart", "dim_Date", "Date"),
    ("man_PriorityItems", "ProjectKey", "dim_Project", "ProjectKey"),
    ("man_PriorityItems", "MonthStart", "dim_Date", "Date"),
    ("man_Flags", "ProjectKey", "dim_Project", "ProjectKey"),
    ("man_Flags", "MonthStart", "dim_Date", "Date"),
    ("man_Survey", "ProjectKey", "dim_Project", "ProjectKey"),
    ("man_Survey", "MonthStart", "dim_Date", "Date"),
    ("man_SafetyMonthly", "ProjectKey", "dim_Project", "ProjectKey"),
    ("man_SafetyMonthly", "MonthStart", "dim_Date", "Date"),
    ("man_QualityMonthly", "ProjectKey", "dim_Project", "ProjectKey"),
    ("man_QualityMonthly", "MonthStart", "dim_Date", "Date"),
    ("man_DailyLogCompliance", "ProjectKey", "dim_Project", "ProjectKey"),
    ("man_DailyLogCompliance", "MonthStart", "dim_Date", "Date"),
    ("man_Milestones", "ProjectKey", "dim_Project", "ProjectKey"),
    ("fct_DailySnapshot", "ProjectKey", "dim_Project", "ProjectKey"),
    ("fct_DailySnapshot", "SnapshotDate", "dim_Date", "Date"),
]

# Inactive: reachable only through USERELATIONSHIP in a measure. fct_Invoice already reaches
# dim_Date on MonthStart (sent month); a second active path would be ambiguous.
INACTIVE_RELATIONSHIPS = [
    ("fct_Invoice", "PaidDate", "dim_Date", "Date"),
]

# Measures. Each carries the workbook cell it replaces, so anyone reading the model can
# trace a number back to the spreadsheet it came from.
PIPELINE_STATUS_DAX = '''VAR Last = MAX ( meta_PipelineRun[RunAt] )
VAR Built = [Last Refresh]
VAR Latest = FILTER ( ALL ( meta_PipelineRun ), meta_PipelineRun[RunAt] = Last )
VAR Blocked = COUNTROWS ( FILTER ( Latest, meta_PipelineRun[Status] <> "ok" || meta_PipelineRun[Blocking] > 0 ) )
VAR Warnings = SUMX ( Latest, meta_PipelineRun[Failing] )
VAR Hrs = DATEDIFF ( Last, UTCNOW (), HOUR )
RETURN SWITCH ( TRUE (),
    ISBLANK ( Last ), "Unknown - no checked run",
    Built > Last, "Unvalidated - data built after last check",
    Blocked > 0, "BLOCKED - validation failed",
    Hrs < 0, "Unknown - check timestamp is in the future",
    Hrs > 72, "STALE - no checked run in over 72 hours",
    Hrs > 30, "Late - no checked run in over 30 hours",
    Warnings > 0, "Gold checked with warnings; source completeness unverified",
    "Gold checks passed; source completeness unverified" )'''

# ---- Month-end snapshots ---------------------------------------------------
#
# Current-state facts grouped by month are NOT month-end figures: closing a record rewrites
# every past month it was open in. These read fct_DailySnapshot, which the DQ gate appends
# after each passing run, and take the LAST capture inside the filter context - the month
# end for a month, the latest capture with no month selected.
#
# BLANK, never zero, when no capture exists in the context: months before capture started
# are unavailable, and a zero there would be fabricated history. No COALESCE on purpose.
SNAPSHOT_KPIS = [
    ("Open Submittals", "OpenSubmittals", '"#,0"'),
    ("Open Submittals Past Due", "SubmittalsPastDue", '"#,0"'),
    ("Open RFIs", "OpenRfis", '"#,0"'),
    ("Open Observations", "OpenObservations", '"#,0"'),
    ("Open Punch Items", "OpenPunchItems", '"#,0"'),
    ("AR Outstanding", "ArOutstanding", '"$#,0"'),
    ("Total Billed", "BilledToDate", '"$#,0"'),
    ("Budget", "BudgetAmount", '"$#,0"'),
    ("Spent To Date", "SpentToDate", '"$#,0"'),
    ("Committed", "CommittedAmount", '"$#,0"'),
    ("Current Contract", "CurrentContract", '"$#,0"'),
    ("Pending Change Orders", "PendingChangeOrders", '"$#,0"'),
    ("Approved Change Orders", "ApprovedChangeOrders", '"$#,0"'),
]
# SnapshotDate semantics, stated wherever a reader meets a snapshot measure.
SNAPSHOT_DATE_NOTE = ("SnapshotDate is the UTC date of the DQ batch that saved it, not a source "
                      "freshness guarantee. The last available capture may precede month end")
SNAPSHOT_MEASURES = [
    (f"{name} (Month End)",
     "VAR D = MAX ( fct_DailySnapshot[SnapshotDate] )\n"
     "RETURN IF ( ISBLANK ( D ), BLANK (),\n"
     f"CALCULATE ( SUM ( fct_DailySnapshot[{col}] ), fct_DailySnapshot[SnapshotDate] = D ) )",
     fmt, f"no workbook equivalent - [{name}] as saved at the last capture in the period. {SNAPSHOT_DATE_NOTE}")
    for name, col, fmt in SNAPSHOT_KPIS
] + [
    ("Snapshot History Starts",
     "CALCULATE ( MIN ( fct_DailySnapshot[SnapshotDate] ), REMOVEFILTERS ( dim_Date ) )",
     '"yyyy-mm-dd"', f"no workbook equivalent - first saved capture. {SNAPSHOT_DATE_NOTE}"),
    ("Snapshot History Note",
     "VAR F = CALCULATE ( MIN ( fct_DailySnapshot[SnapshotDate] ), REMOVEFILTERS ( dim_Date ) )\n"
     'RETURN IF ( ISBLANK ( F ), "No month-end history captured yet",\n'
     '"History starts " & FORMAT ( F, "yyyy-MM-dd" ) & "; earlier months are unavailable, not zero" )',
     None, "no workbook equivalent - states where saved history begins"),
]


REPORT_MONTH_LABEL_DAX = (
    'VAR L = MIN ( dim_Date[MonthStart] )\n'
    'VAR H = MAX ( dim_Date[MonthStart] )\n'
    'RETURN IF ( NOT ISFILTERED ( dim_Date ), "All months", IF ( L = H, FORMAT ( L, "MMMM YYYY" ), '
    'FORMAT ( L, "MMMM YYYY" ) & " - " & FORMAT ( H, "MMMM YYYY" ) ) )')


BALANCE_AT_PERIOD_END = (
    "VAR EndDate = MAX ( dim_Date[Date] )\n"
    "RETURN CALCULATE ( SUMX ( VALUES ( fct_FinancialPeriod[ProjectKey] ),\n"
    "CALCULATE ( LASTNONBLANKVALUE ( dim_Date[Date], SUM ( fct_FinancialPeriod[{column}] ) ) ) ),\n"
    "REMOVEFILTERS ( dim_Date ), dim_Date[Date] <= EndDate )")


def _project_vendors(expression: str) -> str:
    """Scope an insurance count to the selected project's vendors; company-wide otherwise."""
    return ("COALESCE ( IF ( ISFILTERED ( dim_Project ), CALCULATE ( " + expression + ", "
            "TREATAS ( VALUES ( bridge_ProjectVendor[VendorKey] ), fct_VendorInsurance[VendorKey] ) ), "
            + expression + " ), 0 )")


MEASURES = [
    # BALANCES, NOT FLOWS. fct_FinancialPeriod is one row per project per MONTH, and
    # OriginalContract on it is dim_Project's contract amount repeated on every one of
    # those rows. SUM therefore multiplies each project's contract by its month count.
    #
    # Unfiltered, that made the Overview card read $355,059,734 against prime contracts
    # totalling about $34M - one project with 19 monthly rows contributed $168M against a
    # real $9.0M. It reconciles when filtered to one project and one month, which is
    # exactly what the reconciliation gate does, and is why it survived this long.
    #
    # So: per project take the value at the last date in filter context, then add up
    # across projects. One month selected gives that month; none gives the current
    # position rather than a running total of history.
    #
    # CARRIED FORWARD. fct_FinancialPeriod only has a row in months with budget, invoice or
    # CO activity, so inside a month filter a project with no row that month vanished:
    # Aug 2026 read $24.9M against $35.3M. The window is every date up to the end of the
    # selected period, so each project contributes its last value on or before it.
    ("Original Contract",
     BALANCE_AT_PERIOD_END.format(column="OriginalContract"),
     '"$#,0"', "FINANCIALS!C3"),
    ("Current Contract",
     BALANCE_AT_PERIOD_END.format(column="CurrentContract"),
     '"$#,0"', "FINANCIALS!C4"),
    ("Contract Growth %",
     "DIVIDE ( [Current Contract] - [Original Contract], [Original Contract] )",
     '"0.0%"', "DASHBOARD!AT11"),
    # Also a balance. What is pending in a month is a standing amount, not that month's
    # new change orders - adding twelve months of it counts the same open CO twelve times.
    ("Pending Change Orders",
     BALANCE_AT_PERIOD_END.format(column="PendingChangeOrders"),
     '"$#,0"', "FINANCIALS!C5 - was =65000+3158.46+11550+4620 typed in a value cell"),
    ("Age Of Oldest Unapproved CO", "MAX ( fct_FinancialPeriod[AgeOfOldestUnapprovedCO] )",
     '"#,0"', "FINANCIALS!C6 - typed by hand"),
    # The Project Detail change-order table asked for this by name and it had never been
    # written, so the visual rendered as "there's something wrong with one or more fields".
    # Summed from the fact rather than derived as [Current Contract] - [Original Contract],
    # because the table shows it PER CHANGE ORDER - the contract measures are balances that
    # collapse to one value per project and would repeat that value down every row.
    ("Approved Change Orders",
     'CALCULATE ( SUM ( fct_ChangeOrder[Amount] ), NOT fct_ChangeOrder[IsPending], fct_ChangeOrder[StatusLabel] <> "void" )',
     '"$#,0"', "derived - approved COs, the complement of [Pending Change Orders]"),
    ("Change Order Amount", "SUM ( fct_ChangeOrder[Amount] )", '"$#,0"',
     "change-order grain; responds to status and item filters"),
    # AS OF THE LAST SNAPSHOT. fct_BudgetLine is one current-state snapshot keyed to the
    # ingestion month, so a month slicer used to blank every budget card while contract and
    # billing cards beside them still showed values. REMOVEFILTERS(dim_Date) makes the
    # cards say what the data is: the budget position as last ingested, whatever month is
    # selected. The Financial page titles them that way.
    ("Budget", "CALCULATE ( SUM ( fct_BudgetLine[BudgetAmount] ), REMOVEFILTERS ( dim_Date ) )",
     '"$#,0"', "FINANCIALS!C19:C20 - as of the last budget snapshot"),
    ("Forecast", "CALCULATE ( SUM ( fct_BudgetLine[ForecastAmount] ), REMOVEFILTERS ( dim_Date ) )",
     '"$#,0"', "FINANCIALS!D19:D20 - as of the last budget snapshot"),
    ("Committed", "CALCULATE ( SUM ( fct_BudgetLine[CommittedAmount] ), REMOVEFILTERS ( dim_Date ) )",
     '"$#,0"', "FINANCIALS!D61 - as of the last budget snapshot"),
    ("Spent To Date", "CALCULATE ( SUM ( fct_BudgetLine[SpentToDate] ), REMOVEFILTERS ( dim_Date ) )",
     '"$#,0"', "FINANCIALS!E19:E20 - as of the last budget snapshot"),
    ("Cost To Complete", "CALCULATE ( SUM ( fct_BudgetLine[CostToComplete] ), REMOVEFILTERS ( dim_Date ) )",
     '"$#,0"', "FINANCIALS!C15 - as of the last budget snapshot"),
    # REMAINING, not variance: budget less spend to date is what is left to spend. The
    # variance a PM means - will we finish over - is budget less FORECAST, below.
    ("Budget Remaining", "[Budget] - [Spent To Date]", '"$#,0"', "derived - budget less spend to date"),
    ("Budget Remaining %", "DIVIDE ( [Budget Remaining], [Budget] )", '"0.0%"',
     "the rule written out in FINANCIALS!H18:J21 but hand-picked from a dropdown"),
    ("Forecast Variance", "[Budget] - [Forecast]", '"$#,0"',
     "derived - budget less forecast final cost; negative = forecast over budget"),
    ("Forecast Variance %", "DIVIDE ( [Forecast Variance], [Budget] )", '"0.0%"', "derived"),
    # The rule the workbook wrote down and then ignored. SWITCH(TRUE(),...) is the
    # idiomatic DAX for banded IFs - flat instead of nested.
    ("Budget Status",
     'VAR V = [Budget Remaining %]\n'
     '\t\t\tRETURN SWITCH ( TRUE(), ISBLANK ( V ), BLANK (), V >= 0, "Spend within budget", '
     'V >= -0.05, "Spend over budget up to 5%", "Spend over budget above 5%" )',
     None, "FINANCIALS!F19:F20 bands applied to spend-to-date; not a forecast or completion assessment"),
    ("Forecast Status",
     'VAR V = [Forecast Variance %]\n'
     '\t\t\tRETURN SWITCH ( TRUE(), ISBLANK ( V ), BLANK (), V >= 0, "Forecast within budget", '
     'V >= -0.05, "Forecast over budget up to 5%", "Forecast over budget above 5%" )',
     None, "FINANCIALS!F19:F20 bands applied to forecast final cost against budget"),
    ("Percent Bought Out", "DIVIDE ( [Committed], [Budget] )", '"0.0%"', "FINANCIALS!D62"),

    # ---- Sage AP vs Procore cost (fct_ApInvoice) -----------------------------
    #
    # A CHECK ON Spent To Date, never an addition to it: most AP is the same vendor bill
    # Procore already carries as a requisition, so summing the two counts it twice. Mapped
    # projects only (a blank ProjectKey is an unmapped Sage job, listed in dq_DataGap), and
    # as of the last load - REMOVEFILTERS(dim_Date) like the budget measures it is set against.
    ("AP Job Cost",
     "CALCULATE ( SUM ( fct_ApInvoice[LineTotal] ), fct_ApInvoice[IsJobCost] = TRUE (),\n"
     "\t\t\tNOT ISBLANK ( fct_ApInvoice[ProjectKey] ), REMOVEFILTERS ( dim_Date ) )",
     '"$#,0"', "no workbook equivalent - Sage AP job cost (GL 50000-50999 on a job mapped to a Procore "
     "project), to date. AP history starts 2025-03-11. NOT added to Spent To Date (no double counting)"),
    ("AP vs Procore Spent Variance",
     "VAR AP = [AP Job Cost]\nVAR Spent = [Spent To Date]\n"
     "RETURN IF ( ISBLANK ( AP ) || ISBLANK ( Spent ), BLANK (), AP - Spent )",
     '"$#,0"', "no workbook equivalent - [AP Job Cost] minus [Spent To Date], BLANK when either is blank. "
     "AP history starts 2025-03-11, so older jobs read Procore-high for timing. AP is NOT added to Spent To Date"),
    ("AP / Procore Spent Ratio", "DIVIDE ( [AP Job Cost], [Spent To Date] )", '"0.00"',
     "no workbook equivalent - [AP Job Cost] over [Spent To Date]. AP history starts 2025-03-11; "
     "AP is NOT added to Spent To Date"),
    ("ERP-only Vendor Cost",
     "CALCULATE ( SUM ( fct_ApInvoice[LineTotal] ), fct_ApInvoice[IsErpOnlyVendor] = TRUE (),\n"
     "\t\t\tNOT ISBLANK ( fct_ApInvoice[ProjectKey] ), REMOVEFILTERS ( dim_Date ) )",
     '"$#,0"', "no workbook equivalent - AP job cost at vendors with no Procore commitment or direct cost on "
     "the project: cost Spent To Date cannot contain. AP history starts 2025-03-11; NOT added to Spent To Date"),



    # ---- Pipeline liveness --------------------------------------------------
    #
    # ALERTING, for a platform that has no credentialed connector to send email or post to
    # Teams. The DQ gate writes one row per completed run; if any stage fails the gate
    # never runs, no row is written, and this number climbs. Absence of a heartbeat is the
    # signal - which is exactly the failure mode that went unnoticed for a month, when the
    # nightly pipeline failed every night while reporting itself as enabled.
    ("Last Checked Run", "MAX ( meta_PipelineRun[RunAt] )", '"yyyy-mm-dd hh:nn"',
     "nothing - when the last PUBLISHED run passed the DQ gate, not when gold was last built"),
    # UTCNOW, the same clock [Pipeline Status] uses, so the two cards cannot disagree.
    ("Hours Since Last Checked Run",
     "VAR Last = MAX ( meta_PipelineRun[RunAt] )\n"
     "\t\t\tRETURN IF ( ISBLANK ( Last ), BLANK (), DATEDIFF ( Last, UTCNOW (), HOUR ) )",
     '"#,0"',
     "nothing - hours since the last PUBLISHED validated run: automatic update is off, so the model only moves when cd_50_publish_models frames a run that passed the DQ gate. A blocked gate is NOT visible here (the model keeps the last good run); the alert is the signal"),
    # Text, not a colour. A stale pipeline has to be readable in greyscale and by the 8% of
    # men who are colour-blind - the same rule the theme applies to every RAG status.
    ("Pipeline Status",
     PIPELINE_STATUS_DAX,
     None, "nothing - status of the last PUBLISHED validated run, as text so it survives greyscale. A blocked gate never publishes, so BLOCKED is not expected in-model; the alert is the signal"),
    ("Blocking Violations Last Run",
     # BLANK with no checked run - a zero there reads as a clean run.
     "VAR Last = MAX ( meta_PipelineRun[RunAt] )\n"
     "\t\t\tRETURN IF ( ISBLANK ( Last ), BLANK (), COALESCE ( CALCULATE ( SUM ( meta_PipelineRun[Blocking] ),\n"
     "\t\t\tmeta_PipelineRun[RunAt] = Last ), 0 ) )",
     '"#,0"', "derived"),
    # ---- Vendor <-> cost code (Phase 0 item 3) ------------------------------
    # ACTUAL only. bridge_VendorCostCode holds actual and committed as separate
    # rows, and an unfiltered SUM over Amount blends the two - counting the same
    # work once when it was committed and again when it was paid.
    ("Vendor Spend",
     'CALCULATE ( SUM ( bridge_VendorCostCode[Amount] ), '
     'bridge_VendorCostCode[AmountType] = "Actual" )', '"$#,0"',
     "no workbook equivalent - vendor spend could not be sliced by cost code"),
    ("Vendor Committed",
     'CALCULATE ( SUM ( bridge_VendorCostCode[Amount] ), '
     'bridge_VendorCostCode[AmountType] = "Committed" )', '"$#,0"',
     "FINANCIALS!D61 - committed by vendor and cost code, which the workbook cannot slice"),
    ("Cost Codes Per Vendor",
     "COALESCE ( DISTINCTCOUNT ( bridge_VendorCostCode[CostCodeKey] ), 0 )", '"#,0"',
     "derived"),
    ("Vendors Per Cost Code",
     "COALESCE ( DISTINCTCOUNT ( bridge_VendorCostCode[VendorKey] ), 0 )", '"#,0"',
     "derived"),

    # ---- Insurance (D8) -----------------------------------------------------
    #
    # COVERAGE and CURRENCY are counted separately on purpose. A vendor with no
    # certificate and a vendor with a lapsed one both fail a single "compliant" flag, and
    # they need completely different follow-up.
    #
    # PROJECT SCOPE. fct_VendorInsurance hangs off dim_Vendor only, so a project selection
    # never reached it: "Vendors On Project" and "Vendors Without Insurance" followed the
    # project while "Vendors With Insurance" and every certificate count stayed company-wide,
    # and With + Without did not add up to On Project. With a project selected these now
    # count only that project's vendors (TREATAS over the bridge). The month slicer still
    # does not apply - certificates have no reporting month - and the page says so.
    ("Certificates On File", _project_vendors("COUNTROWS ( fct_VendorInsurance )"), '"#,0"',
     "D8"),
    ("Vendors With Insurance",
     _project_vendors("DISTINCTCOUNT ( fct_VendorInsurance[VendorKey] )"), '"#,0"', "D8"),
    ("Expired Certificates",
     _project_vendors('CALCULATE ( COUNTROWS ( fct_VendorInsurance ), '
                      'fct_VendorInsurance[ExpiryStatus] = "Expired" )'), '"#,0"', "D8"),
    ("Certificates Expiring Soon",
     _project_vendors('CALCULATE ( COUNTROWS ( fct_VendorInsurance ), '
                      'fct_VendorInsurance[ExpiryStatus] = "Expiring within 30 days" )'), '"#,0"',
     "D8 - the renewals to chase this month"),
    # Explains an all-expired page: the newest certificate in Procore, not a count.
    ("Latest Certificate Expiration", "MAX ( fct_VendorInsurance[ExpirationDate] )", '"yyyy-mm-dd"',
     "D8 - latest certificate expiration on file"),
    # The gap the vendor list is really for: vendors on a project with NO certificate at
    # all. Counted from the bridge rather than the insurance table, because a vendor with
    # no record does not appear in the insurance table to be counted.
    # EXCEPT over the two key lists, not RELATEDTABLE. There is no relationship from
    # bridge_ProjectVendor to fct_VendorInsurance - both hang off dim_Vendor - so
    # RELATEDTABLE has no path and the measure fails at RENDER while deploying perfectly
    # cleanly. Set difference needs no relationship and states the question directly:
    # which vendors on a project appear nowhere in the certificate list.
    ("Vendors Without Insurance",
     "VAR Insured = VALUES ( fct_VendorInsurance[VendorKey] )\n"
     "\t\t\tRETURN COALESCE ( COUNTROWS ( EXCEPT (\n"
     "\t\t\tVALUES ( bridge_ProjectVendor[VendorKey] ), Insured ) ), 0 )",
     '"#,0"', "D8 - a vendor with no certificate never appears in the insurance table"),
    # ---- Progress billing ---------------------------------------------------
    #
    # RETAINAGE. The workbook has no figure for this at all, and neither does Sage - its
    # invoice header is zero across all 940 rows. It lives in progress billing.
    #
    # Every measure below over a `ToDate` column or RetainageHeld filters to
    # IsLatestPeriod, because those columns are RUNNING BALANCES restated each period.
    # Without the filter, retainage held reads $9.0M against a true $823K. The filter is
    # written out in full on each measure rather than hidden behind a helper: it is the
    # correctness argument, and it has to be visible to whoever reads the measure next.
    ("Retainage Held Owner",
     'CALCULATE ( SUM ( fct_Billing[RetainageHeld] ), fct_Billing[IsLatestPeriod] = TRUE (), REMOVEFILTERS ( dim_Date ), '
     'fct_Billing[BillingType] = "Owner" )',
     '"$#,0"', "no workbook equivalent - Sage holds no header retainage"),
    ("Retainage Held Sub",
     'CALCULATE ( SUM ( fct_Billing[RetainageHeld] ), fct_Billing[IsLatestApprovedPeriod] = TRUE (), REMOVEFILTERS ( dim_Date ), '
     'fct_Billing[BillingType] = "Subcontractor" )',
     # Approved only: an UNDER_REVIEW or PENDING_OWNER_APPROVAL pay app is not yet money
     # Affect holds. Each commitment contributes the balance on its latest APPROVED /
     # APPROVED_AS_NOTED pay app (IsLatestApprovedPeriod), so a later unapproved pay app
     # carries the last approved balance forward instead of zeroing the contract.
     '"$#,0"', "no workbook equivalent - latest approved subcontractor pay app per commitment"),
    # Owner retainage is money owed TO Affect, sub retainage is money Affect holds FROM
    # others. Netting them is the cash question a GC actually asks at month end.
    ("Net Retainage Position", "[Retainage Held Owner] - [Retainage Held Sub]", '"$#,0"',
     "derived - Owner-held minus sub-held; negative = Affect holds more than it is owed"),

    # Billed from the billing side, as opposed to [Total Billed] which comes from Sage
    # invoices. Two independent paths to the same figure is the point: they are sourced
    # from different systems, and a gap between them is a reconciliation finding rather
    # than a rounding difference.
    ("Owner Billed To Date",
     'CALCULATE ( SUM ( fct_Billing[CompletedToDate] ), fct_Billing[IsLatestPeriod] = TRUE (), REMOVEFILTERS ( dim_Date ), '
     'fct_Billing[BillingType] = "Owner" )',
     '"$#,0"', "FINANCIALS!C10, sourced from Procore instead of Sage"),
    ("Owner Contract Sum",
     'CALCULATE ( SUM ( fct_Billing[ContractSumToDate] ), fct_Billing[IsLatestPeriod] = TRUE (), REMOVEFILTERS ( dim_Date ), '
     'fct_Billing[BillingType] = "Owner" )',
     '"$#,0"', "FINANCIALS!C4, cross-check on [Current Contract]"),
    ("Balance To Finish",
     'CALCULATE ( SUM ( fct_Billing[BalanceToFinish] ), fct_Billing[IsLatestPeriod] = TRUE (), REMOVEFILTERS ( dim_Date ), '
     'fct_Billing[BillingType] = "Owner" )',
     '"$#,0"', "derived - contract sum less completed, including retainage"),
    # The sum-safe column. This is a period movement, so it sums across periods and is the
    # right measure for a trend chart - the cumulative ones are not.
    ("Billed This Period",
     'CALCULATE ( SUM ( fct_Billing[CurrentPaymentDue] ), fct_Billing[BillingType] = "Owner", '
     "fct_Billing[StatusLabel] <> \"DRAFT\" )",
     '"$#,0"', "derived - owner billed net of retainage (payment due, Procore); safe to sum, unlike the cumulative columns"),
    ("Billing Periods", "COALESCE ( COUNTROWS ( fct_Billing ), 0 )", '"#,0"', "derived"),
    ("Draft Billings",
     'COALESCE ( CALCULATE ( COUNTROWS ( fct_Billing ), '
     'fct_Billing[StatusLabel] = "DRAFT" ), 0 )',
     '"#,0"', "derived - what is sitting unissued at month end"),

    # ---- Direct costs -------------------------------------------------------
    #
    # Discrete transactions, so these sum across any grouping with no latest-period guard.
    ("Direct Costs", "SUM ( fct_DirectCost[GrandTotal] )", '"$#,0"',
     "no workbook equivalent - self-performed cost was never captured"),
    ("Self Performed Labour",
     'CALCULATE ( SUM ( fct_DirectCost[GrandTotal] ), fct_DirectCost[CostType] = "payroll" )',
     '"$#,0"', "no workbook equivalent"),
    ("Unapproved Direct Costs",
     "CALCULATE ( SUM ( fct_DirectCost[GrandTotal] ), fct_DirectCost[IsApproved] = FALSE () )",
     '"$#,0"', "derived - cost committed but not yet approved"),

    # ---- Vendors ------------------------------------------------------------
    ("Vendors On Project",
     "COALESCE ( DISTINCTCOUNT ( bridge_ProjectVendor[VendorKey] ), 0 )", '"#,0"',
     "D8 - the vendor list, assembled by hand from Procore today"),
    # A vendor invoiced in Procore but never written back to Sage is a reconciliation gap
    # that nothing today would surface.
    ("Vendors Missing From ERP",
     "COALESCE ( CALCULATE ( DISTINCTCOUNT ( bridge_ProjectVendor[VendorKey] ), "
     "bridge_ProjectVendor[IsMissingFromErp] = TRUE () ), 0 )",
     '"#,0"', "derived"),
    ("Total Billed", "SUM ( fct_Invoice[Amount] )", '"$#,0"', "FINANCIALS!C10"),
    ("Total Paid", "SUM ( fct_Invoice[AmountPaid] )", '"$#,0"',
     "FINANCIALS!C12 - paid on invoices SENT in the period, not cash received in it"),
    # Cash by the day it arrived. PaidDate is when receipts first fully covered the invoice
    # (22_fct_invoice.sql), so a partially paid invoice is not counted until it settles.
    ("Cash Received",
     "CALCULATE ( SUM ( fct_Invoice[AmountPaid] ), NOT ISBLANK ( fct_Invoice[PaidDate] ),\n"
     "USERELATIONSHIP ( fct_Invoice[PaidDate], dim_Date[Date] ) )",
     '"$#,0"', "no workbook equivalent - invoices fully paid in the period, by paid date"),
    ("AR Outstanding", "SUM ( fct_Invoice[Balance] )", '"$#,0"', "FINANCIALS!F57"),
    # BILLED TO DATE as of the end of the selected period, against the contract as of that
    # same point. It used to be [Total Billed] / [Current Contract], which with a month
    # selected divided ONE month's invoices by the whole contract - not the workbook's
    # billed-to-date %. Invoices with no matched project are excluded: they carry no
    # contract, so counting them in the numerator overstated the portfolio figure.
    ("Total Billed %",
     "DIVIDE ( CALCULATE ( SUM ( fct_Invoice[Amount] ), fct_Invoice[HasUnmatchedProject] <> TRUE (),\n"
     "\t\t\tFILTER ( ALL ( dim_Date ), dim_Date[Date] <= MAX ( dim_Date[Date] ) ) ),\n"
     "\t\t\t[Current Contract] )", '"0.0%"',
     "DASHBOARD!AT15 - billed to date at period end over contract; was a TEXT string"),
    # DIVIDE, not "/", so a new project with no prior month returns blank instead of
    # #DIV/0! - the workbook's failure at DASHBOARD!AI48.
    ("Total Billed MoM %",
     "VAR Prior = CALCULATE ( [Total Billed], DATEADD ( dim_Date[Date], -1, MONTH ) )\n"
     "\t\t\tRETURN DIVIDE ( [Total Billed] - Prior, Prior )",
     '"0.0%"', "replaces the hand-keyed LAST PERIOD column"),
    ("Open Submittals",
     'CALCULATE ( COUNTROWS ( fct_RfiSubmittal ), fct_RfiSubmittal[IsOpen] = TRUE, fct_RfiSubmittal[ItemType] = "Submittal" )',
     '"#,0"', "SUBMITTALS & RFI!D"),
    ("Open Submittals Past Due",
     'CALCULATE ( COUNTROWS ( fct_RfiSubmittal ), fct_RfiSubmittal[IsPastDue] = TRUE, fct_RfiSubmittal[ItemType] = "Submittal" )',
     '"#,0"', "derived - the workbook has no equivalent"),
    # Open items only - DaysOpen is blank on closed/draft rows, and the filter says so.
    ("Avg Days Open",
     "CALCULATE ( AVERAGE ( fct_RfiSubmittal[DaysOpen] ), fct_RfiSubmittal[IsOpen] = TRUE )",
     '"#,0.0"', "QUALITY!D39 - typed by hand"),
    ("Draft Submittals",
     'CALCULATE ( COUNTROWS ( fct_RfiSubmittal ), fct_RfiSubmittal[IsDraft] = TRUE, fct_RfiSubmittal[ItemType] = "Submittal" )',
     '"#,0"', "derived - drafts are not yet submitted, so excluded from Open Submittals"),
    # 0 only where the project has Outbuild data at all; BLANK where it has none, so "no
    # schedule" does not read as "no milestones due".
    ("Critical Milestones",
     "VAR N = COUNTROWS ( fct_Milestone )\n"
     "RETURN IF ( ISBLANK ( N ) && NOT ISBLANK ( CALCULATE ( COUNTROWS ( fct_Milestone ), REMOVEFILTERS ( dim_Date ) ) ), 0, N )",
     '"#,0"', "SCHEDULE!Table5"),
    ("Overdue Milestones",
     "CALCULATE ( COUNTROWS ( fct_Milestone ), fct_Milestone[IsOverdue] = TRUE )",
     '"#,0"', "derived"),
    # Named for what it counts. Higher is WORSE; "Schedule Performance %" read the other way.
    ("Milestones Overdue %",
     "DIVIDE ( [Overdue Milestones], [Critical Milestones] )", '"0.0%"',
     "DASHBOARD!L19 (Schedule Performance) - a FRACTION, which the scorecard compared against 5/9/10 (defect #1a)"),
    ("Avg Milestone Progress", "AVERAGE ( fct_Milestone[PercentComplete] )", '"0.0%"',
     "derived"),
    # Data-quality measures. These drive the hidden diagnostics page - surfacing bad data
    # rather than letting it flow silently into a leadership rollup, which is exactly how
    # the workbook's defects survived.
    # Quality detail. `Observations` and `Avg Observation Days Open` are NOT here - they
    # already exist in scorecard.py and were repointed at this same fact. Defining them in
    # both places is what the TMDL merge rejects, and rightly: the model would have had a
    # scorecard reading zero from the manual table while a page read 850 from the fact.
    ("Punchlist Items",
     "COALESCE ( CALCULATE ( COUNTROWS ( fct_QualityItem ), "
     "fct_QualityItem[ItemType] = \"PunchItem\" ), 0 )",
     '"#,0"', "QUALITY!Table18 - typed by hand today"),
    ("Open Quality Items",
     "COALESCE ( CALCULATE ( COUNTROWS ( fct_QualityItem ), "
     "fct_QualityItem[IsOpen] = TRUE ), 0 )",
     '"#,0"', "observations and punch items still outstanding"),
    ("Quality Items Past Due",
     "COALESCE ( CALCULATE ( COUNTROWS ( fct_QualityItem ), "
     "fct_QualityItem[IsPastDue] = TRUE ), 0 )",
     '"#,0"', "open AND past their due date"),
    # Over past-due items only - averaging across everything would dilute the number with
    # items that are not late at all.
    ("Avg Days Past Due",
     "AVERAGEX ( FILTER ( fct_QualityItem, fct_QualityItem[IsPastDue] = TRUE ), "
     "fct_QualityItem[DaysPastDue] )",
     '"0.0"', "QUALITY!D38:E38 - hand-computed today"),
    # Cross-source coverage. These count integration GAPS, not data-entry errors, and each
    # one has a financial consequence: a project missing from Sage contributes zero revenue
    # to every measure on every other page without erroring.
    ("Projects Fully Mapped",
     "COALESCE ( CALCULATE ( COUNTROWS ( dim_ProjectCrosswalk ), dim_ProjectCrosswalk[SystemCount] = 3 ), 0 )",
     '"#,0"', "present in Procore AND Sage AND Outbuild"),
    ("Projects In Coverage", "COUNTROWS ( dim_ProjectCrosswalk )", '"#,0"',
     "all projects in the selected coverage category, including incomplete mappings"),
    ("Projects Missing From Sage",
     "COALESCE ( CALCULATE ( COUNTROWS ( dim_ProjectCrosswalk ), dim_ProjectCrosswalk[IsInSage] = FALSE ), 0 )",
     '"#,0"', "these read as ZERO revenue everywhere - the most dangerous gap"),
    ("Projects Missing From Outbuild",
     "COALESCE ( CALCULATE ( COUNTROWS ( dim_ProjectCrosswalk ), dim_ProjectCrosswalk[IsInOutbuild] = FALSE ), 0 )",
     '"#,0"', "no milestones - Outbuild is the only milestone source that exists"),
    ("Source Coverage %",
     "DIVIDE ( [Projects Fully Mapped], COUNTROWS ( dim_ProjectCrosswalk ) )",
     '"0.0%"', "share of projects present in all three systems"),
    ("Vendors Missing From Sage",
     "COALESCE ( CALCULATE ( COUNTROWS ( dim_VendorCrosswalk ), dim_VendorCrosswalk[IsInSage] = FALSE ), 0 )",
     '"#,0"', "mostly expected - a vendor invited to bid is not a vendor who was paid"),
    ("DQ Projects Without Crosswalk",
     'CALCULATE ( COUNTROWS ( dim_Project ), dim_Project[IsInCrosswalk] = FALSE, dim_Project[ProjectKey] <> "UNMATCHED" )',
     '"#,0"', "diagnostics - cannot join to Sage until fixed"),
    ("DQ Cost Codes Not In Source",
     "CALCULATE ( COUNTROWS ( dim_CostCode ), dim_CostCode[IsInSource] = FALSE )",
     '"#,0"', "diagnostics"),
    ("DQ Milestones With Inverted Dates",
     "CALCULATE ( COUNTROWS ( fct_Milestone ), fct_Milestone[HasDateInversion] = TRUE )",
     '"#,0"', "diagnostics - Excel defect #6, never flagged in the workbook"),
    ("DQ Unmatched Invoices",
     "CALCULATE ( COUNTROWS ( fct_Invoice ), REMOVEFILTERS ( dim_Project ), fct_Invoice[HasUnmatchedProject] = TRUE )",
     '"#,0"', "diagnostics - unmatched AR across all projects; retains the selected month"),
    # BILLED, not AR: it sums invoice Amount, not the outstanding Balance.
    ("Unmatched Billed Amount - All Projects",
     "CALCULATE ( SUM ( fct_Invoice[Amount] ), REMOVEFILTERS ( dim_Project ), fct_Invoice[HasUnmatchedProject] = TRUE )",
     '"$#,0"', "unattributed billed amount across all projects; retains the selected month"),
    # The gap register. Gaps with no project (rejected source rows, expired certificates,
    # empty registers) have a blank ProjectKey, so selecting a project hides them - clear
    # the project slicer to see the whole register.
    ("Data Gaps", "COALESCE ( COUNTROWS ( dq_DataGap ), 0 )", '"#,0"',
     "nothing - rejects, unmatched AR, unmapped trades, coverage and certificate gaps in one register"),
    ("Data Gap Amount", "SUM ( dq_DataGap[Amount] )", '"$#,0"',
     "money carried by data gaps - today only unmatched AR invoices carry an amount"),

    # ---- Trend and portfolio ------------------------------------------------
    #
    # dim_Date is 7,670 contiguous days, marked, and DATEADD over it is asserted in
    # validate_model.py - and until now the report used it for exactly one chart. These are
    # the measures that make it earn its place: the question is never "what is the number",
    # it is "which way is it moving".
    ("Billed Cumulative",
     # The S-curve. Uses the SUM-SAFE period movement accumulated over time, NOT the
     # running-balance column - summing a restated balance double-counts every period it
     # was restated in, and slopes upward whether or not anything was billed.
     "CALCULATE ( [Billed This Period], "
     "FILTER ( ALL ( dim_Date ), dim_Date[Date] <= MAX ( dim_Date[Date] ) ) )",
     '"$#,0"', "no workbook equivalent - a single snapshot cannot draw a curve"),
    ("Billed Cumulative % Of Contract",
     "DIVIDE ( [Billed Cumulative], [Current Contract] )",
     '"0.0%"', "the S-curve against the contract line"),
    # Portfolio counts. Every page today is one project behind a slicer; leadership was
    # never given a number that spans the jobs.
    # Projects with a financial period in context - not every row of dim_Project, which
    # ignored the month slicer and counted projects that have never reported anything.
    # UNMATCHED is the unassigned-AR member, not a project.
    ("Projects Reporting",
     'CALCULATE ( DISTINCTCOUNTNOBLANK ( fct_FinancialPeriod[ProjectKey] ), fct_FinancialPeriod[ProjectKey] <> "UNMATCHED" )', '"#,0"',
     "portfolio scope - projects with financial-period rows in the current filters"),
    ("Projects At Risk",
     # Below 0.60 on the measured-only score, so a project is not flagged merely for being
     # under-instrumented - that is what [Scorecard Coverage %] is for.
     "COUNTROWS ( FILTER ( dim_Project, dim_Project[ProjectKey] <> \"UNMATCHED\" "
     "&& NOT ISBLANK ( [Project Scorecard (Measured Only)] ) "
     "&& [Project Scorecard (Measured Only)] < 0.6 ) )",
     '"#,0"', "no workbook equivalent - one workbook per project cannot rank them"),

    # ---- Schedule geometry --------------------------------------------------
    #
    # Power BI has no native Gantt. A stacked bar draws one: an invisible bar to the
    # milestone's start, then a visible bar for its duration. Both are day counts from the
    # earliest start in the current filter, so the axis reads as a timeline.
    #
    # NOTE: fct_Milestone carries CurrentStart/CurrentFinish only. There is no baseline and
    # no actual, so this shows the schedule AS IT STANDS - it cannot show drift against a
    # baseline. That needs baseline dates Outbuild is not supplying today.
    ("Milestone Offset Days",
     "VAR StartDate = SELECTEDVALUE ( fct_Milestone[CurrentStart] )\n"
     "VAR FinishDate = SELECTEDVALUE ( fct_Milestone[CurrentFinish] )\n"
     "VAR Origin = MINX ( FILTER ( ALLSELECTED ( fct_Milestone ), "
     "NOT ISBLANK ( fct_Milestone[CurrentStart] ) && NOT ISBLANK ( fct_Milestone[CurrentFinish] ) "
     "&& fct_Milestone[CurrentFinish] >= fct_Milestone[CurrentStart] ), fct_Milestone[CurrentStart] )\n"
     "RETURN IF ( COUNTROWS ( fct_Milestone ) = 1 && NOT ISBLANK ( StartDate ) "
     "&& NOT ISBLANK ( FinishDate ) && FinishDate >= StartDate && NOT ISBLANK ( Origin ), "
     "DATEDIFF ( Origin, StartDate, DAY ), BLANK () )",
     '"#,0"', "Gantt geometry - the transparent leading bar"),
    ("Milestone Duration Days",
     "VAR StartDate = SELECTEDVALUE ( fct_Milestone[CurrentStart] )\n"
     "VAR FinishDate = SELECTEDVALUE ( fct_Milestone[CurrentFinish] )\n"
     "RETURN IF ( COUNTROWS ( fct_Milestone ) = 1 && NOT ISBLANK ( StartDate ) "
     "&& NOT ISBLANK ( FinishDate ) && FinishDate >= StartDate, "
     "DATEDIFF ( StartDate, FinishDate, DAY ), BLANK () )",
     '"#,0"', "Gantt geometry - the visible bar"),

    # ---- Report context -----------------------------------------------------
    #
    # A page exported to PDF has to state what it is a snapshot OF. The workbook could not:
    # DASHBOARD used TODAY(), so a saved file silently re-reported itself every time it was
    # opened (defect #5). These two put the answer on the page instead.
    #
    # Last Refresh reads a real timestamp stamped into the anchor table when gold is built,
    # not NOW() - NOW() is when the report was VIEWED, which is the same lie in a new place.
    ("Last Refresh", "MAX ( _Measures[_built_at] )", '"yyyy-mm-dd hh:nn"',
     "no workbook equivalent - the Excel could not say when its numbers were true"),
    # Follows the slicer. With no month selected it says so: the calendar spans 2015-2035,
    # and "January 2015 - December 2035" on a printed page implied data out to 2035.
    ("Report Month Label", REPORT_MONTH_LABEL_DAX,
     None, "DASHBOARD!AU4 - the month anchor, now driven by the slicer"),
] + SNAPSHOT_MEASURES + scorecard.measures()


# Field-list folders. Forward-filled: a measure inherits the folder of the last section
# opened above it, so inserting a measure into a section needs no change here. The section
# names mirror the comment headings the MEASURES list is already organised by.
FOLDER_STARTS = [
    ("Original Contract", "01 Contract & Change"),
    ("Budget", "02 Budget & Cost"),
    ("Retainage Held Owner", "03 Billing & Retainage"),
    ("Direct Costs", "04 Direct Costs & Vendors"),
    ("Total Billed", "05 Cash & AR"),
    ("Open Submittals", "06 Submittals & RFIs"),
    ("Critical Milestones", "07 Schedule"),
    ("Punchlist Items", "08 Quality"),
    ("Projects Fully Mapped", "09 Source Coverage"),
    ("DQ Projects Without Crosswalk", "10 Data Quality"),
    ("Billed Cumulative", "05 Cash & AR"),
    ("Projects Reporting", "13 Portfolio"),
    ("Milestone Offset Days", "07 Schedule"),
    # These three start the groups merged in from the pipeline/vendor/insurance work. The
    # fill is positional, so without them all 13 of those measures land in whatever folder
    # the measure above them happens to be in - silently, and wrongly.
    ("Last Checked Run", "14 Pipeline liveness"),
    ("Vendor Spend", "04 Direct Costs & Vendors"),
    ("Certificates On File", "15 Insurance"),
    ("Avg Days To Payment", "11 Scorecard drivers"),
    ("Score - Accounts Receivable", "12 Scorecard"),
    ("Last Refresh", "00 Report context"),
    ("Open Submittals (Month End)", "16 Month-end snapshots"),
]


def folder_for(name: str, _cache: dict = {}) -> str:
    """Which display folder a measure belongs in, by forward-fill over FOLDER_STARTS."""
    if not _cache:
        starts = dict(FOLDER_STARTS)
        current = "00 Report context"
        for measure_name, *_ in MEASURES:
            current = starts.get(measure_name, current)
            _cache[measure_name] = current
    return _cache[name]


def introspect(lakehouse_id: str | None = None) -> dict[str, list[tuple[str, str]]]:
    """Column names and types for each model table, read from FABRIC.

    Authoritative on purpose. Inferring types from the offline DuckDB build is unsound:
    DuckDB reads DECIMAL from a VALUES literal and widens SUM(DOUBLE) to DECIMAL, where
    Spark keeps DOUBLE. A TMDL type that does not match the real column makes DirectLake
    drop the entire table - and it fails silently, surfacing only as
    "Failed to resolve name 'fct_FinancialPeriod'" from a DAX query, with nothing visibly
    wrong in the pipeline.

    cd_30_build_gold publishes the real Spark schema to Files/_diag/gold_schema.json on
    every run, so this always reflects the tables as they actually are.
    """
    import deploy_gold as dg

    raw = dg.fetch_diagnostics(lakehouse_id or ds.lakehouse()["id"], "gold_schema.json")
    if not raw:
        raise RuntimeError(
            "gold_schema.json not found in the lakehouse. Run deploy_gold.py --apply first "
            "- it publishes the schema this generator reads."
        )

    schema: dict[str, list[tuple[str, str]]] = {}
    unmapped = []
    for table in MODEL_TABLES:
        cols = raw.get(table)
        if not cols:
            raise RuntimeError(f"{table} missing from the published Fabric schema")
        resolved = []
        for name, dtype in cols:
            base = dtype.split("(")[0].upper()
            if base not in TYPE_MAP:
                unmapped.append(f"{table}.{name}: {dtype}")
            resolved.append((name, TYPE_MAP.get(base, "string")))
        schema[table] = resolved
    if unmapped:
        raise RuntimeError("unmapped column types (add to TYPE_MAP):\n  " + "\n  ".join(unmapped))
    return schema


# Month labels sort by their number, not alphabetically ("Apr 2024, Aug 2024, Dec 2024").
# Without this the S-curve zig-zags and the month slicer lists 250 months out of order.
SORT_BY = {("dim_Date", "MonthYear"): "MonthYearSort", ("dim_Date", "MonthName"): "Month"}

# Numeric columns that must never be added up in a totals row: keys, ordinals, day counts,
# fractions and band thresholds. Default Sum put "Total 18,402" days under registers and
# added milestone percentages together.
NO_SUM = re.compile(r"(Key|Tier|Sort|Year|Quarter|Month|Day|Offset|Number|PercentComplete|Weight|Score|MinValue|MaxValue)$|Days")
PERCENT_COLUMNS = re.compile(r"^(PercentComplete|Weight)$")


def table_tmdl(name: str, columns: list[tuple[str, str]]) -> str:
    lines = [f"table {name}", ""]
    present = {col for col, _ in columns}
    for col, dtype in columns:
        quoted = f"'{col}'" if not col.isidentifier() else col
        source_completion = name == "fct_ProcoreInspection" and col == "SourcePercentComplete"
        if source_completion:
            lines.append("\t/// Raw source completion value; unit and scale require confirmation. Unknown remains blank. Do not sum across inspections.")
        lines += [
            f"\tcolumn {quoted}",
            f"\t\tdataType: {dtype}",
            "\t\tsummarizeBy: none" if source_completion or dtype in ("string", "boolean", "dateTime")
            or NO_SUM.search(col) else "\t\tsummarizeBy: sum",
            f"\t\tsourceColumn: {col}",
        ]
        if dtype == "dateTime":
            lines.append('\t\tformatString: yyyy-mm-dd')
        elif source_completion:
            lines.append('\t\tformatString: 0.##')
        elif dtype in ("double", "decimal") and PERCENT_COLUMNS.match(col):
            lines.append('\t\tformatString: 0%')
        if SORT_BY.get((name, col)) in present:
            lines.append(f"\t\tsortByColumn: {SORT_BY[(name, col)]}")
        lines.append("")
    lines += [
        f"\tpartition {name} = entity",
        "\t\tmode: directLake",
        "\t\tsource",
        # Spark LOWERCASES table names when it writes them, so the Delta folder is
        # `fct_rfisubmittal` even though the SQL says fct_RfiSubmittal. entityName binds to
        # the PHYSICAL table and must match that; the model-facing table name stays
        # PascalCase for the field list. A mismatch surfaces only at reframe, as
        # "We cannot access the source Delta table" - the definition itself looks fine.
        f"\t\t\tentityName: {name.lower()}",
        "\t\t\tschemaName: dbo",
        "\t\t\texpressionSource: 'DirectLake - CD_Gold_Lakehouse'",
        "",
    ]
    return "\n".join(lines)


def measures_tmdl() -> str:
    """Measures live in their own table so they sort to the top of the field list."""
    lines = ["table _Measures", ""]
    for measure_name, expression, fmt, origin in MEASURES:
        # TMDL: the /// description PRECEDES the object it documents. Placing it after the
        # properties is a parse error ("Unexpected line type"), not a style preference.
        lines.append(f"\t/// Replaces {origin}")
        if "\n" in expression:
            # Multi-line DAX: TMDL requires the `=` to end the line, with EVERY expression
            # line below it and indented deeper. Leaving the first line beside the `=` and
            # continuing underneath is a parse error - the parser reads the continuation as
            # a new property rather than as part of the expression.
            lines.append(f"\tmeasure '{measure_name}' =")
            for expr_line in expression.split("\n"):
                lines.append(f"\t\t\t{expr_line.strip()}")
        else:
            lines.append(f"\tmeasure '{measure_name}' = {expression}")
        if fmt:
            lines.append(f"\t\tformatString: {fmt}")
        # 75 measures in one flat list is a wall. Folders are the only grouping the field
        # list offers, and they cost one line each.
        lines.append(f'\t\tdisplayFolder: {folder_for(measure_name)}')
        lines.append("")
    # Direct Lake over a real one-row table, NOT a calculated table. Calculated tables are
    # unsupported in Direct Lake and do not fail loudly: the model deploys, reports
    # success, and silently loads no tables at all - every DAX query then returns
    # "Failed to resolve name 'dim_Date'". See sql/gold/07_measures_anchor.sql.
    lines += [
        "\tcolumn _placeholder",
        "\t\tisHidden",
        "\t\tdataType: string",
        "\t\tsummarizeBy: none",
        "\t\tsourceColumn: _placeholder",
        "",
        # Stamped when gold is built, so [Last Refresh] reports when the DATA became true
        # rather than when someone opened the report.
        "\tcolumn _built_at",
        "\t\tisHidden",
        "\t\tdataType: dateTime",
        "\t\tformatString: yyyy-mm-dd hh:nn:ss",
        "\t\tsummarizeBy: none",
        "\t\tsourceColumn: _built_at",
        "",
        "\tpartition _Measures = entity",
        "\t\tmode: directLake",
        "\t\tsource",
        "\t\t\tentityName: measures_anchor",
        "\t\t\tschemaName: dbo",
        "\t\t\texpressionSource: 'DirectLake - CD_Gold_Lakehouse'",
        "",
    ]
    return "\n".join(lines)


def model_tmdl(schema: dict) -> str:
    refs = "\n".join(f"ref table {t}" for t in ["_Measures", *MODEL_TABLES])
    return (
        "model Model\n"
        "\tculture: en-US\n"
        "\tdefaultPowerBIDataSourceVersion: powerBI_V3\n"
        "\tsourceQueryCulture: en-US\n"
        "\tdiscourageImplicitMeasures\n"
        "\n"
        "annotation PBI_QueryOrder = [\"DirectLake - CD_Gold_Lakehouse\"]\n"
        "\n"
        f"{refs}\n"
    )


def relationships_tmdl() -> str:
    out = []
    for i, (fact, fcol, dim, dcol) in enumerate(RELATIONSHIPS):
        out += [
            f"relationship rel_{i:02d}_{fact}_{dim}_{fcol}",
            f"\tfromColumn: {fact}.{fcol}",
            f"\ttoColumn: {dim}.{dcol}",
            "",
        ]
    # Only where both tables are in this model: deploy_model_qc reuses this generator.
    for fact, fcol, dim, dcol in INACTIVE_RELATIONSHIPS:
        if fact in MODEL_TABLES and dim in MODEL_TABLES:
            out += [
                f"relationship rel_inactive_{fact}_{dim}_{fcol}",
                "\tisActive: false",
                f"\tfromColumn: {fact}.{fcol}",
                f"\ttoColumn: {dim}.{dcol}",
                "",
            ]
    return "\n".join(out)


def expressions_tmdl(lakehouse_id: str) -> str:
    url = f"https://onelake.dfs.fabric.microsoft.com/{dp.WORKSPACE_ID}/{lakehouse_id}"
    return (
        "expression 'DirectLake - CD_Gold_Lakehouse' =\n"
        "\t\tlet\n"
        f'\t\t    Source = AzureStorage.DataLake("{url}", [HierarchicalNavigation=true])\n'
        "\t\tin\n"
        "\t\t    Source\n"
    )


def write_files(lakehouse_id: str, output_dir: Path | None = None,
                model_name: str | None = None) -> dict[str, str]:
    """Build every TMDL part. Also written to disk so the model is reviewable in a diff."""
    schema = introspect(lakehouse_id)

    files = {
        ".platform": json.dumps({
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/"
                       "platformProperties/2.0.0/schema.json",
            "metadata": {"type": "SemanticModel", "displayName": model_name or MODEL_NAME},
            "config": {"version": "2.0", "logicalId": "00000000-0000-0000-0000-000000000000"},
        }, indent=2),
        "definition.pbism": json.dumps({
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/"
                       "semanticModel/definitionProperties/1.0.0/schema.json",
            "version": "4.2", "settings": {},
        }, indent=2),
        "definition/database.tmdl": "database\n\tcompatibilityLevel: 1604\n",
        "definition/model.tmdl": model_tmdl(schema),
        "definition/expressions.tmdl": expressions_tmdl(lakehouse_id),
        "definition/relationships.tmdl": relationships_tmdl(),
        "definition/tables/_Measures.tmdl": measures_tmdl(),
    }
    for table, cols in schema.items():
        files[f"definition/tables/{table}.tmdl"] = table_tmdl(table, cols)

    for rel, content in files.items():
        path = (output_dir or MODEL_DIR) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        # newline="" prevents Python translating \n to \r\n on Windows. TMDL is
        # whitespace-significant and the payload is uploaded verbatim, so the file on disk
        # and the bytes Fabric parses must be identical.
        path.write_text(content, encoding="utf-8", newline="")
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--recreate", action="store_true",
                        help="delete and recreate - needed for partition-type changes")
    args = parser.parse_args()

    lh = ds.lakehouse()
    files = write_files(lh["id"])
    tables = [f for f in files if f.startswith("definition/tables/")]
    print(f"generated {len(files)} TMDL file(s): {len(tables)} tables, "
          f"{len(MEASURES)} measures, {len(RELATIONSHIPS)} relationships")
    print(f"  written to {MODEL_DIR.relative_to(CHARLEY_DEV)}")

    if not args.apply:
        print("\nDRY RUN - written to disk only. Re-run with --apply to deploy.")
        return 0

    tok = dp.token()
    definition = {
        "parts": [
            {"path": rel,
             "payload": base64.b64encode(content.encode()).decode(),
             "payloadType": "InlineBase64"}
            for rel, content in files.items() if rel != ".platform"
        ]
    }

    existing = ds.find_item(tok, MODEL_NAME, "SemanticModel")

    # Some model changes cannot be applied in place - switching a partition between
    # calculated and Direct Lake is rejected with "Changing the partition type ... is not
    # allowed". Recreating is safe here because the model holds no data of its own: it is
    # a view over CD_Gold_Lakehouse, and every definition lives in this repo.
    if existing and args.recreate:
        assert existing.get("folderId") == dp.FOLDER_ID, "refusing: model is not in charley-dev"
        dp.call("DELETE", f"/workspaces/{dp.WORKSPACE_ID}/items/{existing['id']}", tok)
        print(f"  deleted {MODEL_NAME} for recreation")
        existing = None

    if existing:
        status, _, headers = dp.call(
            "POST", f"/workspaces/{dp.WORKSPACE_ID}/items/{existing['id']}/updateDefinition",
            tok, {"definition": definition},
        )
        if status == 202:
            dp.wait_for_operation(headers, tok)
        print(f"  updated {MODEL_NAME}")
    else:
        # Fabric holds a deleted display name for some minutes, returning a retriable 409.
        import time as _time
        for attempt in range(12):
            try:
                status, _, headers = dp.call(
                    "POST", f"/workspaces/{dp.WORKSPACE_ID}/items", tok,
                    {"displayName": MODEL_NAME, "type": "SemanticModel",
                     "folderId": dp.FOLDER_ID, "definition": definition},
                )
                if status == 202:
                    dp.wait_for_operation(headers, tok)
                break
            except dp.FabricError as exc:
                if "NotAvailableYet" not in str(exc) or attempt == 11:
                    raise
                print(f"name still held, retry {attempt + 1} ...", end=" ", flush=True)
                _time.sleep(20)
        print(f"  created {MODEL_NAME}")

    item = ds.find_item(tok, MODEL_NAME, "SemanticModel")
    print(f"  semantic model id: {item['id']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except dp.FabricError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
