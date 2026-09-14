"""The KPI catalog: what every headline figure on both reports means, in one place.

    python kpi_catalog.py     # self-check

A reader looking at a card needs five answers the number cannot give: what it counts, which
period it describes, where it comes from, what it leaves out, and how current that source is.
Those answers were scattered across measure comments, page notes and _docs. This is now the
single source of truth, and three things are generated from it:

  - the measure `description` in TMDL (deploy_model.measures_tmdl), so the field-list hover
    says it;
  - gold `seed_KpiCatalog` (make_qc_seeds.py -> sql/gold/02_seed_kpicatalog.sql), bound to
    the hidden "KPI Definitions" page in both reports;
  - the source names on that page, which read against gold `meta_SourceFreshness` (written by
    the DQ gate, dq.persist_source_freshness) for "how current is it".

tests/test_kpi_catalog.py fails when a card or chart binds a measure with no entry here.

Keyed by SEMANTIC MODEL name, because the same measure name can mean different things in the
two models: [Open Submittals] reads fct_RfiSubmittal in one and fct_QcSubmittal in the other.
"""

from __future__ import annotations

MONTHLY_MODEL = "Affect Project Report"
PQP_MODEL = "Project Quality Plan"

# The systems meta_SourceFreshness reports on. A catalog source outside this set (a seed, the
# pipeline itself, SharePoint) has no extraction freshness row of its own.
PROCORE, SAGE, OUTBUILD = "Procore", "Sage", "Outbuild"
SHAREPOINT = "SharePoint manual registers"
PIPELINE = "Pipeline DQ gate"
TEMPLATE = "QA/QC workbook template (repo seed)"
FRESHNESS_SOURCES = (PROCORE, SAGE, OUTBUILD)

# ---- period semantics, worded once --------------------------------------------------------
PERIOD_END = ("As of period end: each project's latest value on or before the end of the selected "
              "months; the current position when no month is selected")
LAST_SNAPSHOT = "As of the last Procore budget load; the month slicer does not change it"
TODAY_CREATED = ("As of today (last load); a month selection groups items by creation month - "
                 "not a month-end backlog")
IN_PERIOD = "Created or dated in the selected months; all history when no month is selected"
LATEST_BILLING = "Current: latest billing per contract, whatever month is selected"
NOT_MONTH = "As of the last load; not month-filtered"
MONTH_END = ("As saved at the last nightly capture in the period; months before history starts "
             "are blank, not zero")
LAST_RUN = "As of the last published validated pipeline run"
REGISTER = "Current register contents in the current filters"
FILTERS = "Rows in the current project and month filters"

SNAPSHOT_CAVEAT = ("SnapshotDate is the UTC date of the DQ batch that saved it, so sources are as of "
                   "the previous night")


def K(definition: str, formula: str, period: str, sources: tuple[str, ...],
      exclusions: str = "", gap: str = "", caveats: str = "") -> dict:
    return dict(definition=definition, formula=formula, period=period, sources=sources,
                exclusions=exclusions, gap=gap, caveats=caveats)


# Identical in both models: the footer, pipeline liveness and the gap register.
SHARED = {
    "Report Month Label": K(
        "The months the page is filtered to.",
        "First and last selected dim_Date month; 'All months' when no month is selected",
        "The current month selection", (PIPELINE,)),
    "Last Refresh": K(
        "When gold was last built and verified.",
        "MAX of measures_anchor[_built_at], stamped only after gold verification passes",
        "Gold build time, UTC", (PIPELINE,),
        caveats="Build time, not validation time or source extraction time - see Pipeline Status "
                "and the source freshness table"),
    "Pipeline Status": K(
        "Status of the last published validated pipeline run, in words.",
        "Latest meta_PipelineRun row: blocked, stale (>72 h), late (>30 h), warnings or passed",
        LAST_RUN, (PIPELINE,),
        caveats="Gold checks passing does not certify that every source extracted completely"),
    "Last Checked Run": K(
        "When the last published run passed the DQ gate.",
        "MAX of meta_PipelineRun[RunAt]", LAST_RUN, (PIPELINE,),
        caveats="Not when gold was last built (see Last Refresh)"),
    "Hours Since Last Checked Run": K(
        "Hours since the last published validated run.",
        "Hours between MAX meta_PipelineRun[RunAt] and now (UTC)", LAST_RUN, (PIPELINE,),
        caveats="A blocked gate never publishes, so a climbing number is the alert"),
    "Data Gaps": K(
        "Known data gaps: source rejects, unmatched AR, unmapped trades, coverage, certificate and "
        "empty-register gaps.",
        "COUNTROWS of dq_DataGap", "The gap register from the last build", (PROCORE, SAGE, OUTBUILD, SHAREPOINT),
        exclusions="Gaps with no project hide while a project is selected",
        caveats="Clear the project slicer to see the whole register"),
    "Data Gap Amount": K(
        "Money carried by data gaps.",
        "SUM of dq_DataGap[Amount]", "The gap register from the last build", (SAGE,),
        exclusions="Only unmatched AR invoices carry an amount; AP gaps are count-only",
        gap="Unmatched AR invoice"),
}

MONTHLY = {
    **SHARED,
    # ---- contract, change orders -------------------------------------------------------
    "Current Contract": K(
        "Prime contract value including approved change orders.",
        "Per project, the last fct_FinancialPeriod[CurrentContract] on or before period end, summed "
        "across projects", PERIOD_END, (PROCORE,),
        exclusions="Pending change orders",
        caveats="A balance: months are never added together"),
    "Contract Growth %": K(
        "Growth of the current contract over the original contract.",
        "([Current Contract] - [Original Contract]) / [Original Contract]", PERIOD_END, (PROCORE,)),
    "Pending Change Orders": K(
        "Value of change orders not yet approved.",
        "Per project, the last fct_FinancialPeriod[PendingChangeOrders] on or before period end, "
        "summed", PERIOD_END, (PROCORE,), exclusions="Void change orders"),
    "Approved Change Orders": K(
        "Value of approved change orders.",
        "SUM of fct_ChangeOrder[Amount] where not pending and status is not void", IN_PERIOD, (PROCORE,),
        exclusions="Pending and void change orders"),
    "Change Order Amount": K(
        "Change-order value at change-order grain.",
        "SUM of fct_ChangeOrder[Amount]", IN_PERIOD, (PROCORE,),
        caveats="Includes pending and void rows unless filtered by status"),
    # ---- budget and cost -----------------------------------------------------------------
    "Budget": K(
        "Total project budget from Procore budget lines.",
        "SUM of fct_BudgetLine[BudgetAmount], month filter removed", LAST_SNAPSHOT, (PROCORE,),
        gap="Project with no Procore budget or zero Spent To Date while AP/requisitions exist"),
    "Forecast": K(
        "Forecast final cost.",
        "SUM of fct_BudgetLine[ForecastAmount], month filter removed", LAST_SNAPSHOT, (PROCORE,)),
    "Committed": K(
        "Value of commitments (subcontracts and purchase orders).",
        "SUM of fct_BudgetLine[CommittedAmount], month filter removed", LAST_SNAPSHOT, (PROCORE,)),
    "Spent To Date": K(
        "Cost to date recorded against the Procore budget.",
        "SUM of fct_BudgetLine[SpentToDate], month filter removed", LAST_SNAPSHOT, (PROCORE,),
        exclusions="Sage AP - a check on this figure, never added to it",
        gap="Cost reconciliation variance"),
    "Cost To Complete": K(
        "Remaining cost to finish the job.",
        "SUM of fct_BudgetLine[CostToComplete], month filter removed", LAST_SNAPSHOT, (PROCORE,)),
    "Budget Remaining": K(
        "Budget left to spend.",
        "[Budget] - [Spent To Date]", LAST_SNAPSHOT, (PROCORE,),
        caveats="Not a forecast variance - see Forecast Variance"),
    "Budget Remaining %": K(
        "Budget left to spend, as a share of budget.",
        "[Budget Remaining] / [Budget]", LAST_SNAPSHOT, (PROCORE,)),
    "Budget Status": K(
        "Spend to date banded against budget.",
        "Within budget when remaining >= 0; over up to 5%; over above 5%", LAST_SNAPSHOT, (PROCORE,),
        caveats="Describes spend so far, not a completion forecast"),
    "Forecast Variance": K(
        "Budget less forecast final cost.",
        "[Budget] - [Forecast]; negative means forecast over budget", LAST_SNAPSHOT, (PROCORE,)),
    "Forecast Status": K(
        "Forecast final cost banded against budget.",
        "Within budget when variance >= 0; over up to 5%; over above 5%", LAST_SNAPSHOT, (PROCORE,)),
    "Percent Bought Out": K(
        "Committed cost as a share of budget.",
        "[Committed] / [Budget]", LAST_SNAPSHOT, (PROCORE,)),
    # ---- Sage AP check ----------------------------------------------------------------------
    "AP Job Cost": K(
        "Sage AP job cost on jobs mapped to a Procore project.",
        "SUM of fct_ApInvoice[LineTotal] where GL 50000-50999 and the job maps to a project", NOT_MONTH, (SAGE,),
        exclusions="Unmapped Sage jobs; non-job-cost GL lines. Never added to Spent To Date",
        gap="Sage job without Procore project",
        caveats="Sage AP history starts 2025-03-11, so older jobs read Procore-high for timing"),
    "AP vs Procore Spent Variance": K(
        "Sage AP job cost minus Procore Spent To Date.",
        "[AP Job Cost] - [Spent To Date]; blank when either side is blank", NOT_MONTH, (SAGE, PROCORE),
        gap="Cost reconciliation variance",
        caveats="AP history starts 2025-03-11; timing differs between the systems"),
    "AP / Procore Spent Ratio": K(
        "Sage AP job cost over Procore Spent To Date.",
        "[AP Job Cost] / [Spent To Date]", NOT_MONTH, (SAGE, PROCORE),
        gap="Cost reconciliation variance", caveats="AP history starts 2025-03-11"),
    "ERP-only Vendor Cost": K(
        "AP job cost at vendors with no Procore commitment or direct cost on the project.",
        "SUM of fct_ApInvoice[LineTotal] where IsErpOnlyVendor, mapped jobs only", NOT_MONTH, (SAGE, PROCORE),
        gap="ERP-only vendor cost",
        caveats="Cost Spent To Date cannot contain; AP history starts 2025-03-11"),
    # ---- billing and retainage --------------------------------------------------------------
    "Retainage Held Owner": K(
        "Retainage the owner is holding from Affect.",
        "SUM of fct_Billing[RetainageHeld] on each owner contract's latest billing", LATEST_BILLING, (PROCORE,),
        caveats="Sage holds no retainage; Procore progress billing is the only source"),
    "Retainage Held Sub": K(
        "Retainage Affect is holding from subcontractors.",
        "SUM of fct_Billing[RetainageHeld] on each commitment's latest APPROVED pay app", LATEST_BILLING, (PROCORE,),
        exclusions="Unapproved pay apps (under review, pending owner approval)"),
    "Net Retainage Position": K(
        "Owner-held retainage minus sub-held retainage.",
        "[Retainage Held Owner] - [Retainage Held Sub]", LATEST_BILLING, (PROCORE,),
        caveats="Negative means Affect holds more than it is owed"),
    "Owner Contract Sum": K(
        "Contract sum to date on the latest owner billing.",
        "SUM of fct_Billing[ContractSumToDate], latest owner period", LATEST_BILLING, (PROCORE,),
        caveats="A cross-check on Current Contract"),
    "Owner Billed To Date": K(
        "Work completed to date on the latest owner billing.",
        "SUM of fct_Billing[CompletedToDate], latest owner period", LATEST_BILLING, (PROCORE,),
        caveats="Procore-side billed; compare with Total Billed from Sage"),
    "Balance To Finish": K(
        "Contract sum less work completed, including retainage.",
        "SUM of fct_Billing[BalanceToFinish], latest owner period", LATEST_BILLING, (PROCORE,)),
    "Billed This Period": K(
        "Owner billed net of retainage (payment due).",
        "SUM of fct_Billing[CurrentPaymentDue], owner billings", IN_PERIOD, (PROCORE,),
        exclusions="Draft billings"),
    "Billed Cumulative": K(
        "Owner billed net of retainage, accumulated to period end.",
        "Running total of [Billed This Period] up to the end of the selected period", PERIOD_END, (PROCORE,),
        exclusions="Draft billings"),
    "Draft Billings": K(
        "Billings still in draft.",
        "COUNT of fct_Billing rows with status DRAFT", IN_PERIOD, (PROCORE,)),
    # ---- cash and AR ---------------------------------------------------------------------------
    "Total Billed": K(
        "Amount invoiced to the owner in Sage AR.",
        "SUM of fct_Invoice[Amount]", "Invoices sent in the selected months; all when none selected", (SAGE,),
        gap="Unmatched AR invoice",
        caveats="Unmatched invoices count in portfolio totals but under no project"),
    "Total Billed %": K(
        "Billed to date as a share of the current contract.",
        "Invoices dated on or before period end / [Current Contract]", PERIOD_END, (SAGE, PROCORE),
        exclusions="Invoices with no matched Procore project", gap="Unmatched AR invoice"),
    "Total Paid": K(
        "Amount paid on invoices sent in the period.",
        "SUM of fct_Invoice[AmountPaid] by invoice month",
        "Invoices sent in the selected months - not cash received in them", (SAGE,),
        gap="Unmatched AR invoice",
        caveats="3 opening-balance invoices dated 2024-12-31 ($227,667.54) have no receipt rows"),
    "AR Outstanding": K(
        "Open receivable balance on Sage AR invoices.",
        "SUM of fct_Invoice[Balance]", "Today's balance on invoices sent in the selected months", (SAGE,),
        gap="Unmatched AR invoice",
        caveats="Unmatched invoices count in portfolio totals but under no project"),
    # ---- submittals, schedule --------------------------------------------------------------
    "Open Submittals": K(
        "Submittals currently open (submitted, awaiting a response).",
        "COUNT of fct_RfiSubmittal where IsOpen and ItemType = Submittal", TODAY_CREATED, (PROCORE,),
        exclusions="RFIs; draft submittals; closed submittals",
        caveats="For month-end history use Open Submittals (Month End)"),
    "Open Submittals Past Due": K(
        "Open submittals past their due date.",
        "COUNT of fct_RfiSubmittal where IsPastDue and ItemType = Submittal", TODAY_CREATED, (PROCORE,),
        exclusions="RFIs; drafts; closed submittals"),
    "Open Submittals (Month End)": K(
        "Open submittals as saved at the last nightly capture in the period.",
        "fct_DailySnapshot[OpenSubmittals] at the last SnapshotDate in context", MONTH_END, (PROCORE, PIPELINE),
        caveats=SNAPSHOT_CAVEAT),
    "Open Submittals Past Due (Month End)": K(
        "Past-due submittals as saved at the last nightly capture in the period.",
        "fct_DailySnapshot[SubmittalsPastDue] at the last SnapshotDate in context", MONTH_END, (PROCORE, PIPELINE),
        caveats=SNAPSHOT_CAVEAT),
    "Snapshot History Note": K(
        "Where saved month-end history begins.",
        "Earliest fct_DailySnapshot[SnapshotDate]", MONTH_END, (PIPELINE,),
        caveats="Months before history starts are unavailable, not zero"),
    "Critical Milestones": K(
        "Outbuild milestones in the current filters.",
        "COUNT of fct_Milestone; 0 only where the project has Outbuild data",
        "Grouped by milestone month when a month is selected", (OUTBUILD,),
        gap="Project missing from Outbuild",
        caveats="Blank means no Outbuild schedule, not no milestones"),
    "Overdue Milestones": K(
        "Milestones past their current finish and not complete.",
        "COUNT of fct_Milestone where IsOverdue", "Overdue as of today; grouped by milestone month", (OUTBUILD,),
        gap="Project missing from Outbuild"),
    "Milestones Overdue %": K(
        "Share of milestones that are overdue. Higher is worse.",
        "[Overdue Milestones] / [Critical Milestones]", "Overdue as of today; grouped by milestone month", (OUTBUILD,)),
    "Avg Milestone Progress": K(
        "Average percent complete across milestones.",
        "AVERAGE of fct_Milestone[PercentComplete]", "As of the last Outbuild load", (OUTBUILD,)),
    "Milestone Offset Days": K(
        "Timeline geometry: days from the earliest valid start on screen to this milestone's start.",
        "DATEDIFF from the earliest valid CurrentStart to this CurrentStart", "The current schedule", (OUTBUILD,),
        exclusions="Missing or inverted dates",
        caveats="No baseline is supplied, so drift against baseline cannot be shown"),
    "Milestone Duration Days": K(
        "Timeline geometry: days from this milestone's start to its finish.",
        "DATEDIFF of CurrentStart to CurrentFinish", "The current schedule", (OUTBUILD,),
        exclusions="Missing or inverted dates"),
    # ---- safety and quality --------------------------------------------------------------------
    "Hours Worked": K(
        "Manpower hours logged in Procore.",
        "SUM of fct_SafetyMonthly[HoursWorked]; blank when none logged", IN_PERIOD, (PROCORE,),
        caveats="The system of record for hours (Sage payroll, ADP or Procore timecards) is undecided"),
    "Recordable Incidents": K(
        "Recordable incidents from Procore incident records.",
        "SUM of fct_SafetyMonthly[RecordableIncidents]; blank when no hours and no incidents", IN_PERIOD, (PROCORE,),
        caveats="Procore shows 0 recordable incidents; confirm Procore is the safety system of record "
                "before reading 0 as incident-free"),
    "Observations": K(
        "Procore observations.",
        "COUNT of fct_QualityItem where ItemType = Observation", IN_PERIOD, (PROCORE,)),
    "Punchlist Items": K(
        "Procore punch items.",
        "COUNT of fct_QualityItem where ItemType = PunchItem", IN_PERIOD, (PROCORE,)),
    "Open Quality Items": K(
        "Observations and punch items still open.",
        "COUNT of fct_QualityItem where IsOpen", TODAY_CREATED, (PROCORE,)),
    "Quality Items Past Due": K(
        "Open observations and punch items past their due date.",
        "COUNT of fct_QualityItem where IsPastDue", TODAY_CREATED, (PROCORE,)),
    "Avg Days Past Due": K(
        "Average days late across past-due quality items.",
        "AVERAGE of DaysPastDue over past-due items only", TODAY_CREATED, (PROCORE,)),
    "Avg Observation Days To Close": K(
        "Average days an observation took to close.",
        "AVERAGE of fct_QualityItem[DaysOpen] over closed items", IN_PERIOD, (PROCORE,),
        exclusions="Open items"),
    # ---- direct costs and vendors ------------------------------------------------------------
    "Direct Costs": K(
        "Direct (self-performed and non-commitment) cost.",
        "SUM of fct_DirectCost[GrandTotal]", IN_PERIOD, (PROCORE,)),
    "Self Performed Labour": K(
        "Direct cost of Affect's own payroll.",
        "SUM of fct_DirectCost[GrandTotal] where CostType = payroll", IN_PERIOD, (PROCORE,)),
    "Unapproved Direct Costs": K(
        "Direct cost not yet approved.",
        "SUM of fct_DirectCost[GrandTotal] where not approved", IN_PERIOD, (PROCORE,)),
    "Vendors On Project": K(
        "Distinct vendors on the project's Procore vendor list.",
        "DISTINCTCOUNT of bridge_ProjectVendor[VendorKey]", NOT_MONTH, (PROCORE,)),
    "Vendors Missing From ERP": K(
        "Project vendors not synced to Sage.",
        "DISTINCTCOUNT of bridge_ProjectVendor[VendorKey] where IsMissingFromErp", NOT_MONTH, (PROCORE, SAGE)),
    "Vendor Committed": K(
        "Committed amount by vendor and cost code, from Procore subcontract and purchase order lines.",
        "SUM of bridge_VendorCostCode[Amount] where AmountType = Committed", NOT_MONTH, (PROCORE,),
        exclusions="VOID and DRAFT commitments",
        caveats="Never add to Vendor Spend - the same work would count twice. TERMINATED commitments "
                "count at full contract value (HasTerminatedCommitment, WARN DQ rule). Not the budget "
                "Committed column"),
    "Vendor Spend": K(
        "Actual spend by vendor and cost code.",
        "SUM of bridge_VendorCostCode[Amount] where AmountType = Actual", NOT_MONTH, (PROCORE,),
        exclusions="Committed amounts"),
    # ---- insurance -------------------------------------------------------------------------
    "Vendors With Insurance": K(
        "Vendors with at least one certificate on file in Procore.",
        "DISTINCTCOUNT of fct_VendorInsurance[VendorKey]; project vendors when a project is selected",
        NOT_MONTH, (PROCORE,),
        caveats="Every Procore certificate is expired (latest 2025-04-01); confirm where current "
                "certificates are kept"),
    "Vendors Without Insurance": K(
        "Vendors on the project with no certificate record in Procore.",
        "Project vendors EXCEPT vendors in fct_VendorInsurance", NOT_MONTH, (PROCORE,),
        gap="Vendor without certificate",
        caveats="No certificate in Procore does not prove the vendor is uninsured"),
    "Certificates On File": K(
        "Insurance certificates recorded in Procore.",
        "COUNTROWS of fct_VendorInsurance; project vendors when a project is selected", NOT_MONTH, (PROCORE,)),
    "Expired Certificates": K(
        "Certificates past their expiration date.",
        "COUNT of fct_VendorInsurance where ExpiryStatus = Expired", NOT_MONTH, (PROCORE,),
        gap="Expired certificate",
        caveats="Every Procore certificate is expired (latest 2025-04-01); the module may be unused"),
    "Certificates Expiring Soon": K(
        "Certificates expiring within 30 days.",
        "COUNT of fct_VendorInsurance where ExpiryStatus = Expiring within 30 days", NOT_MONTH, (PROCORE,)),
    "Latest Certificate Expiration": K(
        "The latest expiration date on any certificate on file.",
        "MAX of fct_VendorInsurance[ExpirationDate]", NOT_MONTH, (PROCORE,)),
    # ---- scorecard -------------------------------------------------------------------------
    "Project Scorecard": K(
        "Weighted 0-1 project health index across nine categories.",
        "SUM(category score x weight) / 3; blank when nothing is measured", FILTERS,
        (PROCORE, SAGE, OUTBUILD, SHAREPOINT),
        exclusions="Unmeasured categories contribute nothing",
        caveats="A portfolio blend unless one project is selected; read with Scorecard Coverage %; "
                "not comparable with the workbook's 0.59"),
    "Scorecard Coverage %": K(
        "Share of scorecard weight that is actually measured.",
        "SUM of weights whose category score is not blank", FILTERS, (PROCORE, SAGE, OUTBUILD, SHAREPOINT),
        gap="Empty manual register",
        caveats="Profitability, survey, daily-log and baseline inputs are manual registers that are empty today"),
    "Project Scorecard (Measured Only)": K(
        "Scorecard rescaled to the weight that is measured.",
        "[Project Scorecard] / [Scorecard Coverage %]", FILTERS, (PROCORE, SAGE, OUTBUILD, SHAREPOINT)),
    "Category Score": K(
        "Score 0-3 for one scorecard category.",
        "The category driver looked up against dim_ScorecardBand thresholds",
        "Follows the category driver's period", (PROCORE, SAGE, OUTBUILD, SHAREPOINT),
        exclusions="Categories with no data are blank, never zero"),
    "Category Band": K(
        "The band a category's driver fell into, in the band table's words.",
        "dim_ScorecardBand[BandLabel] for the category and score; Not measured when blank",
        "Follows the category driver's period", (PROCORE, SAGE, OUTBUILD, SHAREPOINT)),
    "Category Weighted": K(
        "What one category contributes to the 0-1 scorecard.",
        "Category score x weight / 3; these sum to Project Scorecard",
        "Follows the category driver's period", (PROCORE, SAGE, OUTBUILD, SHAREPOINT)),
    "Client Satisfaction": K(
        "Client survey score as a share of the maximum.",
        "SUM of man_Survey[Score] / (survey rows x 5)", REGISTER, (SHAREPOINT,),
        gap="Empty manual register", caveats="The survey register is empty until manual intake runs"),
    "Projects Reporting": K(
        "Projects with financial-period rows in the current filters.",
        "DISTINCTCOUNT of fct_FinancialPeriod[ProjectKey]", FILTERS, (PROCORE, SAGE),
        exclusions="The UNMATCHED (unassigned AR) member; projects that never reported"),
    "Projects At Risk": K(
        "Projects scoring below 0.60 on the measured-only scorecard.",
        "COUNT of projects where [Project Scorecard (Measured Only)] < 0.6", FILTERS,
        (PROCORE, SAGE, OUTBUILD, SHAREPOINT),
        exclusions="Projects with no measured category; UNMATCHED",
        caveats="A thinly measured project is not flagged - check coverage"),
    # ---- source coverage and data quality -------------------------------------------------
    "Projects Fully Mapped": K(
        "Projects present in Procore, Sage and Outbuild.",
        "COUNT of dim_ProjectCrosswalk where SystemCount = 3", NOT_MONTH, (PROCORE, SAGE, OUTBUILD)),
    "Projects In Coverage": K(
        "Projects in the selected coverage category.",
        "COUNTROWS of dim_ProjectCrosswalk", NOT_MONTH, (PROCORE, SAGE, OUTBUILD)),
    "Projects Missing From Sage": K(
        "Projects with no Sage job mapped.",
        "COUNT of dim_ProjectCrosswalk where not IsInSage", NOT_MONTH, (PROCORE, SAGE),
        gap="Project missing from Sage",
        caveats="These read as zero revenue on every page without erroring"),
    "Projects Missing From Outbuild": K(
        "Projects with no Outbuild schedule.",
        "COUNT of dim_ProjectCrosswalk where not IsInOutbuild", NOT_MONTH, (PROCORE, OUTBUILD),
        gap="Project missing from Outbuild", caveats="No milestones can appear for these projects"),
    "Source Coverage %": K(
        "Share of projects present in all three systems.",
        "[Projects Fully Mapped] / COUNTROWS(dim_ProjectCrosswalk)", NOT_MONTH, (PROCORE, SAGE, OUTBUILD)),
    "Blocking Violations Last Run": K(
        "Blocking DQ failures on the last checked run.",
        "SUM of meta_PipelineRun[Blocking] at the last RunAt; blank with no run", LAST_RUN, (PIPELINE,),
        caveats="Expected 0 in-model: a blocked run never publishes"),
    "DQ Projects Without Crosswalk": K(
        "Projects that cannot join to Sage.",
        "COUNT of dim_Project where not IsInCrosswalk", NOT_MONTH, (PROCORE, SAGE),
        exclusions="UNMATCHED", gap="Project missing from Sage"),
    "DQ Cost Codes Not In Source": K(
        "Cost codes in gold that the source cost-code list does not contain.",
        "COUNT of dim_CostCode where not IsInSource", NOT_MONTH, (PROCORE,)),
    "DQ Milestones With Inverted Dates": K(
        "Milestones whose finish is before their start.",
        "COUNT of fct_Milestone where HasDateInversion", "As of the last Outbuild load", (OUTBUILD,)),
    "DQ Unmatched Invoices": K(
        "AR invoices whose Sage job maps to no Procore project, across all projects.",
        "COUNT of fct_Invoice where HasUnmatchedProject, project filter removed",
        "Invoices sent in the selected months; ignores the project selection", (SAGE,),
        gap="Unmatched AR invoice"),
    "Unmatched Billed Amount - All Projects": K(
        "Billed amount on unmatched AR invoices, across all projects.",
        "SUM of fct_Invoice[Amount] where HasUnmatchedProject, project filter removed",
        "Invoices sent in the selected months; ignores the project selection", (SAGE,),
        gap="Unmatched AR invoice", caveats="Billed, not outstanding"),
}

OBSERVATION_CAVEAT = "All retrieved Procore observations, not only confirmed NCRs"
TEMPLATE_PERIOD = "Template definition; no period"

PQP = {
    **SHARED,
    "Total Observations": K(
        "Procore observations raised.",
        "COUNTROWS of fct_QcNcr", IN_PERIOD, (PROCORE,), gap="Unmapped trade", caveats=OBSERVATION_CAVEAT),
    "Open Observations": K(
        "Procore observations still open.",
        "COUNT of fct_QcNcr where IsOpen", TODAY_CREATED, (PROCORE,), gap="Unmapped trade",
        caveats=OBSERVATION_CAVEAT),
    "Closed Observations": K(
        "Procore observations closed.",
        "COUNT of fct_QcNcr where not IsOpen", IN_PERIOD, (PROCORE,), caveats=OBSERVATION_CAVEAT),
    "Observations Past Due": K(
        "Open observations past their due date.",
        "COUNT of fct_QcNcr where IsPastDue", TODAY_CREATED, (PROCORE,), caveats=OBSERVATION_CAVEAT),
    "Avg Observation Closure Days": K(
        "Average days a closed observation was open.",
        "AVERAGE of fct_QcNcr[DaysOpen] over closed observations", IN_PERIOD, (PROCORE,),
        exclusions="Open observations"),
    "Observation Closure Rate": K(
        "Share of observations closed.",
        "[Closed Observations] / [Total Observations]", IN_PERIOD, (PROCORE,)),
    "Total Punch Items": K(
        "Procore punch items raised.", "COUNTROWS of fct_QcPunch", IN_PERIOD, (PROCORE,), gap="Unmapped trade"),
    "Open Punch Items": K(
        "Punch items still open.", "COUNT of fct_QcPunch where IsOpen", TODAY_CREATED, (PROCORE,),
        gap="Unmapped trade"),
    "Punch Items Aged Over 7 Days": K(
        "Open punch items open more than 7 days (the trade-executive escalation line).",
        "COUNT of fct_QcPunch where IsOpen and DaysOpen > 7", TODAY_CREATED, (PROCORE,)),
    "Punch Closure Rate": K(
        "Share of punch items closed.",
        "Closed punch items / [Total Punch Items]", IN_PERIOD, (PROCORE,)),
    "Total Submittals": K(
        "Procore submittals.", "COUNTROWS of fct_QcSubmittal", IN_PERIOD, (PROCORE,)),
    "Open Submittals": K(
        "Submittals open for review.",
        "COUNT of fct_QcSubmittal where IsOpen", TODAY_CREATED, (PROCORE,),
        exclusions="Drafts (not yet submitted); closed submittals"),
    "Overdue Submittals": K(
        "Submittals past their due date.",
        "COUNT of fct_QcSubmittal where IsOverdue", TODAY_CREATED, (PROCORE,),
        caveats="Review for procurement impact"),
    "Avg Submittal Turnaround Days": K(
        "Average days from creation to distribution or close.",
        "AVERAGE of fct_QcSubmittal[TurnaroundDays] over closed submittals", IN_PERIOD, (PROCORE,),
        exclusions="Open and draft submittals",
        caveats="Right-skewed: live 2026-09-14 mean about 68 days against a median of about 32"),
    "Possible Mock-Ups": K(
        "Submittals whose subject text contains MOCK.",
        "COUNT of fct_QcSubmittal where IsMockup", IN_PERIOD, (PROCORE,),
        caveats="Inferred from text; may include false matches and miss unnamed mock-ups. Not a confirmed register"),
    "Native Inspections": K(
        "Native Procore inspection records retrieved.",
        "COUNTROWS of fct_ProcoreInspection", "Month filters use inspection date", (PROCORE,),
        exclusions="Undated inspections while a month is selected",
        caveats="Not mapped to the manual checklist templates; closed does not mean every item was inspected"),
    "Native Inspection Items": K(
        "Items on native Procore inspections.",
        "COUNTROWS of fct_ProcoreInspectionItem", "Follows the parent inspection's date", (PROCORE,),
        caveats="No Response is a source label, not a failed check"),
    "Gates Defined": K(
        "Statutory gates in the template: 46 TCO, 23 fire alarm, 24 statutory.",
        "COUNTROWS of qc_seed_Gate", TEMPLATE_PERIOD, (TEMPLATE,)),
    "Gates Recorded": K(
        "Gates with a recorded status on a project.",
        "COUNTROWS of man_QcGate", REGISTER, (SHAREPOINT,), gap="Empty manual register",
        caveats="Empty until SharePoint manual intake runs; empty is not complete"),
    "Gates Complete": K(
        "Gates recorded as COMPLETE.",
        "COUNT of man_QcGate where StatusCode = COMPLETE", REGISTER, (SHAREPOINT,), gap="Empty manual register"),
    "Gate Template Completion": K(
        "Recorded completion against the gate template for one project.",
        "[Gates Complete] / [Gates Defined]; blank unless one project with valid recorded counts",
        REGISTER, (SHAREPOINT, TEMPLATE), gap="Empty manual register",
        caveats="Applicability and readiness are not certified"),
    "Checklist Items Defined": K(
        "Checklist items in the 26 trade templates (625).",
        "COUNTROWS of qc_seed_ChecklistItem", TEMPLATE_PERIOD, (TEMPLATE,)),
    "Checklist Items Recorded": K(
        "Checklist items with a recorded result.",
        "COUNTROWS of man_QcChecklistResult", REGISTER, (SHAREPOINT,), gap="Empty manual register",
        caveats="Procore inspection results are not linked to these templates"),
    "Checklist Items Passed": K(
        "Checklist items recorded PASS.",
        "COUNT of man_QcChecklistResult where ResultCode = PASS", REGISTER, (SHAREPOINT,),
        gap="Empty manual register"),
    "Checklist Items Failed": K(
        "Checklist items recorded FAIL.",
        "COUNT of man_QcChecklistResult where ResultCode = FAIL", REGISTER, (SHAREPOINT,),
        gap="Empty manual register"),
    "DFOWs Registered": K(
        "Definable features of work on the DFOW risk register.",
        "COUNTROWS of man_QcDfow", REGISTER, (SHAREPOINT,), gap="Empty manual register"),
    "Tier 3 And 4 DFOWs": K(
        "High-risk definable features of work.",
        "COUNT of man_QcDfow where RiskTier >= 3", REGISTER, (SHAREPOINT,), gap="Empty manual register"),
    "ITP Tests Defined": K(
        "Inspection and test plan entries.",
        "COUNTROWS of man_QcItp", REGISTER, (SHAREPOINT,), gap="Empty manual register"),
    "Special Inspections Logged": K(
        "Special inspection events logged.",
        "COUNTROWS of man_QcSpecialInspection", REGISTER, (SHAREPOINT,), gap="Empty manual register"),
    "DQ Observations With Unmapped Trade": K(
        "Observations whose Procore trade has no workbook trade key.",
        "COUNT of fct_QcNcr where HasUnmappedTrade", IN_PERIOD, (PROCORE,), gap="Unmapped trade",
        caveats="Needs Affect to confirm the trade mapping; guessing would misattribute defects"),
    "DQ Punch With Unmapped Trade": K(
        "Punch items whose Procore trade has no workbook trade key.",
        "COUNT of fct_QcPunch where HasUnmappedTrade", IN_PERIOD, (PROCORE,), gap="Unmapped trade"),
    "DQ Registers Awaiting Input": K(
        "How many manual quality registers have no rows in the current filters.",
        "Count of empty man_Qc* registers, as text", REGISTER, (SHAREPOINT,), gap="Empty manual register",
        caveats="Populated registers are not certified complete"),
}

CATALOG: dict[str, dict[str, dict]] = {MONTHLY_MODEL: MONTHLY, PQP_MODEL: PQP}


def description(model: str, measure: str, origin: str) -> str:
    """One-line TMDL description: the catalog entry when there is one, and the workbook lineage.

    One line because a TMDL `///` block is line-oriented; the field-list hover wraps it anyway.
    """
    e = CATALOG.get(model, {}).get(measure)
    if not e:
        return f"Replaces {origin}"
    parts = [e["definition"], f"Formula: {e['formula']}.", f"Period: {e['period']}.",
             f"Source: {', '.join(e['sources'])}."]
    parts += [f"{label}: {e[key]}." for label, key in
              (("Excludes", "exclusions"), ("Data gap category", "gap"), ("Caveat", "caveats")) if e[key]]
    fresh = [s for s in e["sources"] if s in FRESHNESS_SOURCES]
    if fresh:
        parts.append(f"Freshness: meta_SourceFreshness for {', '.join(fresh)}.")
    parts.append(f"Replaces {origin}")
    return " ".join(parts).replace("\n", " ")


SEED_COLUMNS = ("ModelName", "KpiName", "Definition", "Formula", "Period", "Sources",
                "Exclusions", "GapCategory", "Caveats", "SortOrder")


def rows() -> list[dict[str, str]]:
    """seed_KpiCatalog rows, all strings (make_qc_seeds casts them)."""
    out = []
    for model, entries in CATALOG.items():
        for i, (name, e) in enumerate(sorted(entries.items()), start=1):
            out.append(dict(ModelName=model, KpiName=name, Definition=e["definition"],
                            Formula=e["formula"], Period=e["period"], Sources=", ".join(e["sources"]),
                            Exclusions=e["exclusions"], GapCategory=e["gap"], Caveats=e["caveats"],
                            SortOrder=str(i)))
    return out


if __name__ == "__main__":
    for model, entries in CATALOG.items():
        for name, e in entries.items():
            assert all(e[k] for k in ("definition", "formula", "period", "sources")), f"{model}/{name}"
            assert "\n" not in description(model, name, "x"), name
    assert "system of record" in MONTHLY["Recordable Incidents"]["caveats"]
    assert MONTHLY["Open Submittals"] is not PQP["Open Submittals"]
    assert description(MONTHLY_MODEL, "no such measure", "FINANCIALS!C3") == "Replaces FINANCIALS!C3"
    print(f"kpi catalog: {len(MONTHLY)} monthly + {len(PQP)} PQP entries")
