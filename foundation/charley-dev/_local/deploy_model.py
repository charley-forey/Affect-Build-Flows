"""Generate and deploy the DirectLake semantic model over CD_Gold_Lakehouse.

    python deploy_model.py            # dry run - write TMDL to disk only
    python deploy_model.py --apply    # create/update the model in Fabric

The TMDL is GENERATED from the schema cd_30_build_gold publishes to the lakehouse on
every run, so the model's columns and types cannot drift from the tables. Read from
FABRIC rather than from the offline build on purpose: DuckDB infers DECIMAL where Spark
has DOUBLE, and a declared type that does not match makes Direct Lake drop the table
silently.

DirectLake, matching the existing workspace models (`mode: directLake`,
`schemaName: dbo`) rather than import - so the report reads the lakehouse directly and
there is no refresh to schedule or fail.
"""

from __future__ import annotations

import argparse
import base64
import json
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
    # The ~40% that lives nowhere but the spreadsheet. Empty today; bound now so the model
    # and the scorecard are complete in shape before a single row is entered.
    "man_Wins", "man_Risks", "man_PriorityItems", "man_Flags", "man_Survey",
    "man_SafetyMonthly", "man_QualityMonthly", "man_Milestones", "man_DailyLogCompliance",
    # Cross-source coverage. These answer "is this project actually in Sage and Outbuild,
    # or is it silently reading as zero revenue?" - which nothing else in the model can.
    "dim_ProjectCrosswalk", "dim_VendorCrosswalk", "dim_CostCodeCrosswalk",
    # The pipeline heartbeat. Not project data - it is how the report answers
    # "are these numbers from last night, or from three weeks ago?".
    "meta_PipelineRun",
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
]

# Measures. Each carries the workbook cell it replaces, so anyone reading the model can
# trace a number back to the spreadsheet it came from.
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
    ("Original Contract",
     "SUMX ( VALUES ( fct_FinancialPeriod[ProjectKey] ),\n"
     "\t\t\tCALCULATE ( LASTNONBLANKVALUE ( dim_Date[Date],\n"
     "\t\t\tSUM ( fct_FinancialPeriod[OriginalContract] ) ) ) )",
     '"$#,0"', "FINANCIALS!C3"),
    ("Current Contract",
     "SUMX ( VALUES ( fct_FinancialPeriod[ProjectKey] ),\n"
     "\t\t\tCALCULATE ( LASTNONBLANKVALUE ( dim_Date[Date],\n"
     "\t\t\tSUM ( fct_FinancialPeriod[CurrentContract] ) ) ) )",
     '"$#,0"', "FINANCIALS!C4"),
    ("Contract Growth %",
     "DIVIDE ( [Current Contract] - [Original Contract], [Original Contract] )",
     '"0.00%"', "DASHBOARD!AT11"),
    # Also a balance. What is pending in a month is a standing amount, not that month's
    # new change orders - adding twelve months of it counts the same open CO twelve times.
    ("Pending Change Orders",
     "SUMX ( VALUES ( fct_FinancialPeriod[ProjectKey] ),\n"
     "\t\t\tCALCULATE ( LASTNONBLANKVALUE ( dim_Date[Date],\n"
     "\t\t\tSUM ( fct_FinancialPeriod[PendingChangeOrders] ) ) ) )",
     '"$#,0"', "FINANCIALS!C5 - was =65000+3158.46+11550+4620 typed in a value cell"),
    ("Age Of Oldest Unapproved CO", "MAX ( fct_FinancialPeriod[AgeOfOldestUnapprovedCO] )",
     '"#,0"', "FINANCIALS!C6 - typed by hand"),
    # The Project Detail change-order table asked for this by name and it had never been
    # written, so the visual rendered as "there's something wrong with one or more fields".
    # Summed from the fact rather than derived as [Current Contract] - [Original Contract],
    # because the table shows it PER CHANGE ORDER - the contract measures are balances that
    # collapse to one value per project and would repeat that value down every row.
    ("Approved Change Orders",
     "CALCULATE ( SUM ( fct_ChangeOrder[Amount] ), NOT fct_ChangeOrder[IsPending] )",
     '"$#,0"', "derived - approved COs, the complement of [Pending Change Orders]"),
    ("Budget", "SUM ( fct_BudgetLine[BudgetAmount] )", '"$#,0"', "FINANCIALS!C19:C20"),
    ("Forecast", "SUM ( fct_BudgetLine[ForecastAmount] )", '"$#,0"', "FINANCIALS!D19:D20"),
    ("Committed", "SUM ( fct_BudgetLine[CommittedAmount] )", '"$#,0"', "FINANCIALS!D61"),
    ("Spent To Date", "SUM ( fct_BudgetLine[SpentToDate] )", '"$#,0"', "FINANCIALS!E19:E20"),
    ("Cost To Complete", "SUM ( fct_BudgetLine[CostToComplete] )", '"$#,0"', "FINANCIALS!C15"),
    ("Budget Variance", "[Budget] - [Spent To Date]", '"$#,0"', "derived"),
    ("Budget Variance %", "DIVIDE ( [Budget Variance], [Budget] )", '"0.0%"',
     "the rule written out in FINANCIALS!H18:J21 but hand-picked from a dropdown"),
    # The rule the workbook wrote down and then ignored. SWITCH(TRUE(),...) is the
    # idiomatic DAX for banded IFs - flat instead of nested.
    ("Budget Status",
     'VAR V = [Budget Variance %]\n'
     '\t\t\tRETURN SWITCH ( TRUE(), ISBLANK ( V ), BLANK (), V >= 0, "On Track", '
     'V >= -0.05, "Watch", "Over Budget" )',
     None, "FINANCIALS!F19:F20 - derivable, but typed by hand today"),
    ("Percent Bought Out", "DIVIDE ( [Committed], [Budget] )", '"0.0%"', "FINANCIALS!D62"),



    # ---- Pipeline liveness --------------------------------------------------
    #
    # ALERTING, for a platform that has no credentialed connector to send email or post to
    # Teams. The DQ gate writes one row per completed run; if any stage fails the gate
    # never runs, no row is written, and this number climbs. Absence of a heartbeat is the
    # signal - which is exactly the failure mode that went unnoticed for a month, when the
    # nightly pipeline failed every night while reporting itself as enabled.
    ("Last Checked Run", "MAX ( meta_PipelineRun[RunAt] )", '"yyyy-mm-dd hh:nn"',
     "no workbook equivalent - the spreadsheet cannot say when it was last correct"),
    ("Hours Since Last Checked Run",
     "VAR Last = MAX ( meta_PipelineRun[RunAt] )\n"
     "\t\t\tRETURN IF ( ISBLANK ( Last ), BLANK (), DATEDIFF ( Last, NOW (), HOUR ) )",
     '"#,0"', "derived"),
    # Text, not a colour. A stale pipeline has to be readable in greyscale and by the 8% of
    # men who are colour-blind - the same rule the theme applies to every RAG status.
    ("Pipeline Status",
     "VAR Hrs = [Hours Since Last Checked Run]\n"
     '\t\t\tRETURN SWITCH ( TRUE (), ISBLANK ( Hrs ), "Never completed a checked run", '
     'Hrs <= 30, "Current", Hrs <= 72, "Late - no run in over a day", '
     '"STALE - these numbers may be weeks old" )',
     None, "derived"),
    ("Blocking Violations Last Run",
     "VAR Last = MAX ( meta_PipelineRun[RunAt] )\n"
     "\t\t\tRETURN COALESCE ( CALCULATE ( SUM ( meta_PipelineRun[Blocking] ),\n"
     "\t\t\tmeta_PipelineRun[RunAt] = Last ), 0 )",
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
    ("Certificates On File", "COALESCE ( COUNTROWS ( fct_VendorInsurance ), 0 )", '"#,0"',
     "D8"),
    ("Vendors With Insurance",
     "COALESCE ( DISTINCTCOUNT ( fct_VendorInsurance[VendorKey] ), 0 )", '"#,0"', "D8"),
    ("Expired Certificates",
     'COALESCE ( CALCULATE ( COUNTROWS ( fct_VendorInsurance ), '
     'fct_VendorInsurance[ExpiryStatus] = "Expired" ), 0 )', '"#,0"', "D8"),
    ("Certificates Expiring Soon",
     'COALESCE ( CALCULATE ( COUNTROWS ( fct_VendorInsurance ), '
     'fct_VendorInsurance[ExpiryStatus] = "Expiring within 30 days" ), 0 )', '"#,0"',
     "D8 - the renewals to chase this month"),
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
     'CALCULATE ( SUM ( fct_Billing[RetainageHeld] ), fct_Billing[IsLatestPeriod] = TRUE (), '
     'fct_Billing[BillingType] = "Owner" )',
     '"$#,0"', "no workbook equivalent - Sage holds no header retainage"),
    ("Retainage Held Sub",
     'CALCULATE ( SUM ( fct_Billing[RetainageHeld] ), fct_Billing[IsLatestPeriod] = TRUE (), '
     'fct_Billing[BillingType] = "Subcontractor" )',
     '"$#,0"', "no workbook equivalent"),
    # Owner retainage is money owed TO Affect, sub retainage is money Affect holds FROM
    # others. Netting them is the cash question a GC actually asks at month end.
    ("Net Retainage Position", "[Retainage Held Owner] - [Retainage Held Sub]", '"$#,0"',
     "derived - what Affect is owed, less what Affect holds"),

    # Billed from the billing side, as opposed to [Total Billed] which comes from Sage
    # invoices. Two independent paths to the same figure is the point: they are sourced
    # from different systems, and a gap between them is a reconciliation finding rather
    # than a rounding difference.
    ("Owner Billed To Date",
     'CALCULATE ( SUM ( fct_Billing[CompletedToDate] ), fct_Billing[IsLatestPeriod] = TRUE (), '
     'fct_Billing[BillingType] = "Owner" )',
     '"$#,0"', "FINANCIALS!C10, sourced from Procore instead of Sage"),
    ("Owner Contract Sum",
     'CALCULATE ( SUM ( fct_Billing[ContractSumToDate] ), fct_Billing[IsLatestPeriod] = TRUE (), '
     'fct_Billing[BillingType] = "Owner" )',
     '"$#,0"', "FINANCIALS!C4, cross-check on [Current Contract]"),
    ("Balance To Finish",
     'CALCULATE ( SUM ( fct_Billing[BalanceToFinish] ), fct_Billing[IsLatestPeriod] = TRUE (), '
     'fct_Billing[BillingType] = "Owner" )',
     '"$#,0"', "derived - contract sum less completed, including retainage"),
    # The sum-safe column. This is a period movement, so it sums across periods and is the
    # right measure for a trend chart - the cumulative ones are not.
    ("Billed This Period",
     'CALCULATE ( SUM ( fct_Billing[CurrentPaymentDue] ), fct_Billing[BillingType] = "Owner", '
     "fct_Billing[StatusLabel] <> \"DRAFT\" )",
     '"$#,0"', "derived - safe to sum, unlike the cumulative columns"),
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
    ("Total Paid", "SUM ( fct_Invoice[AmountPaid] )", '"$#,0"', "FINANCIALS!C12"),
    ("AR Outstanding", "SUM ( fct_Invoice[Balance] )", '"$#,0"', "FINANCIALS!F57"),
    ("Total Billed %", "DIVIDE ( [Total Billed], [Current Contract] )", '"0.0%"',
     "DASHBOARD!AT15 - was a TEXT string, so it could never be charted"),
    # DIVIDE, not "/", so a new project with no prior month returns blank instead of
    # #DIV/0! - the workbook's failure at DASHBOARD!AI48.
    ("Total Billed MoM %",
     "VAR Prior = CALCULATE ( [Total Billed], DATEADD ( dim_Date[Date], -1, MONTH ) )\n"
     "\t\t\tRETURN DIVIDE ( [Total Billed] - Prior, Prior )",
     '"0.0%"', "replaces the hand-keyed LAST PERIOD column"),
    ("Open Submittals",
     "CALCULATE ( COUNTROWS ( fct_RfiSubmittal ), fct_RfiSubmittal[IsOpen] = TRUE )",
     '"#,0"', "SUBMITTALS & RFI!D"),
    ("Open Submittals Past Due",
     "CALCULATE ( COUNTROWS ( fct_RfiSubmittal ), fct_RfiSubmittal[IsPastDue] = TRUE )",
     '"#,0"', "derived - the workbook has no equivalent"),
    ("Avg Days Open", "AVERAGE ( fct_RfiSubmittal[DaysOpen] )", '"#,0.0"',
     "QUALITY!D39 - typed by hand"),
    ("Critical Milestones", "COUNTROWS ( fct_Milestone )", '"#,0"', "SCHEDULE!Table5"),
    ("Overdue Milestones",
     "CALCULATE ( COUNTROWS ( fct_Milestone ), fct_Milestone[IsOverdue] = TRUE )",
     '"#,0"', "derived"),
    ("Schedule Performance %",
     "DIVIDE ( [Overdue Milestones], [Critical Milestones] )", '"0.0%"',
     "DASHBOARD!L19 - a FRACTION, which the scorecard compared against 5/9/10 (defect #1a)"),
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
     "CALCULATE ( COUNTROWS ( dim_Project ), dim_Project[IsInCrosswalk] = FALSE )",
     '"#,0"', "diagnostics - cannot join to Sage until fixed"),
    ("DQ Cost Codes Not In Source",
     "CALCULATE ( COUNTROWS ( dim_CostCode ), dim_CostCode[IsInSource] = FALSE )",
     '"#,0"', "diagnostics"),
    ("DQ Milestones With Inverted Dates",
     "CALCULATE ( COUNTROWS ( fct_Milestone ), fct_Milestone[HasDateInversion] = TRUE )",
     '"#,0"', "diagnostics - Excel defect #6, never flagged in the workbook"),
    ("DQ Unmatched Invoices",
     "CALCULATE ( COUNTROWS ( fct_Invoice ), fct_Invoice[HasUnmatchedProject] = TRUE )",
     '"#,0"', "diagnostics - AR rows whose Sage job resolves to no project"),

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
    ("Projects Reporting", "COUNTROWS ( dim_Project )", '"#,0"', "portfolio scope"),
    ("Projects At Risk",
     # Below 0.60 on the measured-only score, so a project is not flagged merely for being
     # under-instrumented - that is what [Scorecard Coverage %] is for.
     "COUNTROWS ( FILTER ( dim_Project, "
     "NOT ISBLANK ( [Project Scorecard (Measured Only)] ) "
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
     "VAR Origin = CALCULATE ( MIN ( fct_Milestone[CurrentStart] ), ALLSELECTED ( fct_Milestone ) )\n"
     "RETURN DATEDIFF ( Origin, MIN ( fct_Milestone[CurrentStart] ), DAY )",
     '"#,0"', "Gantt geometry - the transparent leading bar"),
    ("Milestone Duration Days",
     "DATEDIFF ( MIN ( fct_Milestone[CurrentStart] ), MAX ( fct_Milestone[CurrentFinish] ), DAY )",
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
    # Follows the slicer. With no month selected it names the full span rather than
    # inventing a single month, because that IS what the reader is looking at.
    ("Report Month Label",
     'VAR L = MIN ( dim_Date[MonthStart] )\n'
     'VAR H = MAX ( dim_Date[MonthStart] )\n'
     'RETURN IF ( L = H, FORMAT ( L, "MMMM YYYY" ), '
     'FORMAT ( L, "MMMM YYYY" ) & " - " & FORMAT ( H, "MMMM YYYY" ) )',
     None, "DASHBOARD!AU4 - the month anchor, now driven by the slicer"),
] + scorecard.measures()


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


def introspect() -> dict[str, list[tuple[str, str]]]:
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

    raw = dg.fetch_diagnostics(ds.lakehouse()["id"], "gold_schema.json")
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


def table_tmdl(name: str, columns: list[tuple[str, str]]) -> str:
    lines = [f"table {name}", ""]
    for col, dtype in columns:
        quoted = f"'{col}'" if not col.isidentifier() else col
        lines += [
            f"\tcolumn {quoted}",
            f"\t\tdataType: {dtype}",
            "\t\tsummarizeBy: none" if dtype in ("string", "boolean", "dateTime")
            else "\t\tsummarizeBy: sum",
            f"\t\tsourceColumn: {col}",
        ]
        if dtype == "dateTime":
            lines.append('\t\tformatString: yyyy-mm-dd')
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


def write_files(lakehouse_id: str) -> dict[str, str]:
    """Build every TMDL part. Also written to disk so the model is reviewable in a diff."""
    schema = introspect()

    files = {
        ".platform": json.dumps({
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/"
                       "platformProperties/2.0.0/schema.json",
            "metadata": {"type": "SemanticModel", "displayName": MODEL_NAME},
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
        path = MODEL_DIR / rel
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
