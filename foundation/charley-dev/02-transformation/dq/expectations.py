"""The data-quality suite: what must be true about gold before anyone reads a number.

Built with `00-platform/lib/dq.py`, which already has the right shape - expectations return
the rows that VIOLATE the rule, so a failure hands you the offending records rather than a
boolean you then have to go investigate.

TWO SEVERITIES, AND THE DIFFERENCE MATTERS:

  ERROR  stops the pipeline. The model is not refreshed and the report keeps yesterday's
         numbers. Reserved for things that make a number WRONG rather than incomplete -
         a duplicate key double-counts a total, a fact with no matching dimension row
         silently drops out of every filtered visual.

  WARN   records and continues. For things that are true of the real data and would be
         dishonest to hide, but are not defects: a project genuinely missing from Sage,
         a cost code Procore has and the master list does not.

The instinct to make everything an ERROR is wrong here. A pipeline that blocks on a real
business condition gets muted within a week, and then the blocking checks stop working too.

WHY A STALE REPORT BEATS A WRONG ONE. Blocking looks drastic - leadership opens the report
and the numbers are yesterday's. But the alternative is that they open it and the numbers
are today's and wrong, with nothing on the page saying so. The workbook's defects survived
for months precisely because nothing ever refused to publish.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "00-platform" / "lib"))

from dq import (  # noqa: E402
    SEVERITY_ERROR,
    SEVERITY_WARN,
    Expectation,
    Suite,
    date_order,
    not_null,
    referential,
    unique_key,
)


def build_suite() -> Suite:
    suite = Suite()

    # ---------------------------------------------------------------- keys
    #
    # A duplicate dimension key is the most expensive defect in a star schema: it fans out
    # every fact joined to it, so totals inflate silently and nothing errors.
    suite.add(
        unique_key("dim_Project", ["ProjectKey"]),
        unique_key("dim_Vendor", ["VendorKey"]),
        unique_key("dim_CostCode", ["CostCodeKey"]),
        unique_key("dim_Date", ["Date"]),
        unique_key("dim_ProjectCrosswalk", ["ProjectKey"]),
        unique_key("dim_VendorCrosswalk", ["VendorKey"]),
        unique_key("dim_CostCodeCrosswalk", ["CostCodeKey"]),
        # RFIs and submittals are numbered independently in Procore, so the key is the pair.
        unique_key("fct_RfiSubmittal", ["ItemType", "ItemKey"]),
        not_null("dim_Project", "ProjectKey"),
        not_null("fct_BudgetLine", "ProjectKey"),
        not_null("fct_ChangeOrder", "ProjectKey"),
    )

    # ---------------------------------------------------- referential integrity
    #
    # A fact row whose dimension key does not exist disappears from every visual that
    # filters by that dimension - it does not error, the totals just quietly disagree
    # between an unfiltered and a filtered view. Gold builds the dimensions by UNIONing in
    # observed keys precisely so this holds; these checks prove it still does.
    suite.add(
        referential("fct_BudgetLine", "ProjectKey", "dim_Project", "ProjectKey"),
        referential("fct_BudgetLine", "CostCodeKey", "dim_CostCode", "CostCodeKey"),
        referential("fct_ChangeOrder", "ProjectKey", "dim_Project", "ProjectKey"),
        referential("fct_RfiSubmittal", "ProjectKey", "dim_Project", "ProjectKey"),
        referential("fct_Milestone", "ProjectKey", "dim_Project", "ProjectKey"),
    )

    # ------------------------------------------------- the Sage join is alive
    #
    # A project genuinely missing from Sage is a WARN and always has been. EVERY project
    # missing from Sage is a different animal: it means the join itself is dead, not that
    # the data is incomplete. That is what happened when dim_Project took SageJobNumber
    # from sv_projects (a hardcoded NULL under --source cd) instead of from
    # sv_project_crosswalk - all 122 AR invoices resolved to UNMATCHED, $23.7M attached to
    # no project, and nothing errored because a LEFT JOIN keeps the row count identical.
    #
    # ERROR, not WARN: it makes every project-filtered financial number wrong rather than
    # incomplete. The check is structural - it fires only when NOT ONE project maps, which
    # real data gaps cannot produce while the crosswalk holds anything at all.
    suite.add(Expectation(
        name="dim_Project.SageJobNumber resolves for at least one project",
        table="dim_Project",
        failing_sql=(
            "SELECT * FROM dim_Project "
            "WHERE NOT EXISTS (SELECT 1 FROM dim_Project WHERE SageJobNumber IS NOT NULL)"
        ),
        severity=SEVERITY_ERROR,
        description="no project maps to Sage - the crosswalk join is broken, not sparse",
    ))

    # ------------------------------------------------------------ dates
    #
    # MonthStart is the dim_Date join. A value outside the calendar matches nothing, and a
    # measure over it returns BLANK - which on a card is indistinguishable from "zero".
    for fact in ("fct_BudgetLine", "fct_ChangeOrder", "fct_Invoice",
                 "fct_RfiSubmittal", "fct_Milestone", "fct_FinancialPeriod"):
        suite.add(Expectation(
            name=f"{fact}.MonthStart resolves to dim_Date",
            table=fact,
            failing_sql=(
                f"SELECT f.* FROM {fact} f "
                f"LEFT JOIN dim_Date d ON f.MonthStart = d.Date "
                f"WHERE f.MonthStart IS NOT NULL AND d.Date IS NULL"
            ),
            severity=SEVERITY_ERROR,
            description="a MonthStart outside dim_Date makes every measure over it blank",
        ))

    # Sentinel dates. Procore submittals carry values before 1582-10-15 as placeholders for
    # "unknown"; silver floors anything before 1990 to NULL. If one reaches gold the floor
    # has been bypassed, and a 400-year-old date will anchor any min/max it touches.
    for fact, col in (("fct_RfiSubmittal", "CreatedDate"),
                      ("fct_RfiSubmittal", "DueDate"),
                      ("fct_Milestone", "CurrentStart"),
                      ("fct_Milestone", "CurrentFinish"),
                      ("fct_Invoice", "SentDate")):
        suite.add(Expectation(
            name=f"{fact}.{col} has no sentinel dates",
            table=fact,
            failing_sql=f"SELECT * FROM {fact} WHERE {col} < DATE '1990-01-01'",
            severity=SEVERITY_ERROR,
            description="pre-1990 dates are 'unknown' placeholders, not real dates",
        ))

    suite.add(
        # A milestone finishing before it starts is workbook defect #6, which the
        # spreadsheet never flagged. WARN, not ERROR: it is real data entered by a human,
        # and the right response is to go fix the schedule, not to stop publishing.
        date_order("fct_Milestone", "CurrentStart", "CurrentFinish", severity=SEVERITY_WARN),
    )

    # -------------------------------------------------- cross-source coverage
    #
    # All WARN. These are integration gaps, not pipeline defects - blocking on them would
    # mean the report never publishes until Affect finishes their Sage and Outbuild
    # onboarding, which is not our call to force. But they must be counted out loud,
    # because a project missing from Sage reads as zero revenue with no other signal.
    suite.add(
        Expectation(
            name="every project is in Sage",
            table="dim_ProjectCrosswalk",
            failing_sql="SELECT * FROM dim_ProjectCrosswalk WHERE NOT IsInSage",
            severity=SEVERITY_WARN,
            description="a project missing from Sage reads as ZERO revenue everywhere",
        ),
        Expectation(
            name="every project is in Outbuild",
            table="dim_ProjectCrosswalk",
            failing_sql="SELECT * FROM dim_ProjectCrosswalk WHERE NOT IsInOutbuild",
            severity=SEVERITY_WARN,
            description="no Outbuild project means no milestones - the only source there is",
        ),
        Expectation(
            name="no project maps to two ids on the far side",
            table="dim_ProjectCrosswalk",
            failing_sql=("SELECT * FROM dim_ProjectCrosswalk "
                         "WHERE HasAmbiguousSageMatch OR HasAmbiguousOutbuildMatch"),
            # ERROR: an ambiguous mapping means the crosswalk silently PICKED one, and every
            # financial number for that project depends on which. That is wrong, not just
            # incomplete.
            severity=SEVERITY_ERROR,
            description="an ambiguous mapping was resolved by picking one - unsafe",
        ),
        Expectation(
            name="cost codes parse to a CSI division",
            table="dim_CostCodeCrosswalk",
            failing_sql="SELECT * FROM dim_CostCodeCrosswalk WHERE HasUnparseableCode",
            severity=SEVERITY_WARN,
            description="unparseable codes cannot roll up by division",
        ),
    )

    # ------------------------------------------------------------ money
    #
    # A negative contract or budget is not a rounding artefact - it means a sign convention
    # was misread somewhere upstream, and every derived percentage inherits it.
    suite.add(
        Expectation(
            name="no negative original budgets",
            table="fct_BudgetLine",
            failing_sql="SELECT * FROM fct_BudgetLine WHERE OriginalBudget < 0",
            severity=SEVERITY_WARN,
            description="a negative budget usually means a sign convention was misread",
        ),
        Expectation(
            name="cumulative billing never exceeds the current contract",
            table="fct_FinancialPeriod",
            # CUMULATIVE billing, not one period's. The first version compared
            # BilledThisPeriod to CurrentContract and fired on all 19 projects - it was
            # comparing a month against a contract total, which is meaningless. A check
            # that always fires is worse than no check: it trains people to ignore the page.
            failing_sql=(
                "SELECT * FROM ("
                "  SELECT ProjectKey, MAX(CurrentContract) AS contract, "
                "         SUM(BilledThisPeriod) AS billed "
                "  FROM fct_FinancialPeriod GROUP BY ProjectKey"
                ") WHERE contract > 0 AND billed > contract * 1.01"),
            # 1% tolerance: approved change orders can land a period after the billing that
            # anticipated them, which is normal. Beyond that it is a real reconciliation gap.
            # contract > 0 excludes projects with no contract yet - absent, not over-billed.
            severity=SEVERITY_WARN,
            description="cumulative billing above contract by >1% is a reconciliation gap",
        ),
    )

    # ------------------------------------------------------- progress billing
    #
    # fct_Billing carries RUNNING BALANCES restated every period alongside one sum-safe
    # period movement. Almost every way of getting this wrong produces a plausible number
    # rather than an error, so the invariants are checked rather than trusted.
    suite.add(
        unique_key("fct_Billing", ["BillingKey"]),
        not_null("fct_Billing", "ProjectKey"),
        unique_key("bridge_ProjectVendor", ["ProjectKey", "VendorKey"]),
        not_null("fct_DirectCost", "ProjectKey"),
        referential("fct_Billing", "ProjectKey", "dim_Project", "ProjectKey"),
        referential("fct_DirectCost", "ProjectKey", "dim_Project", "ProjectKey"),
        referential("bridge_ProjectVendor", "ProjectKey", "dim_Project", "ProjectKey"),
    )

    suite.add(
        # EXACTLY ONE latest period per contract per direction. Two would double every
        # retainage balance; zero would drop a contract out of the totals entirely. Both
        # read as an ordinary number on a card.
        Expectation(
            name="one latest billing period per contract",
            table="fct_Billing",
            failing_sql=(
                "SELECT * FROM ("
                "  SELECT BillingType, ContractId, SUM(CASE WHEN IsLatestPeriod THEN 1 ELSE 0 END) AS n"
                "  FROM fct_Billing GROUP BY BillingType, ContractId"
                # A contract billed only in draft legitimately has no latest period, so
                # zero is allowed and only two-or-more is a defect.
                ") WHERE n > 1"),
            severity=SEVERITY_ERROR,
            description="a duplicate latest period double-counts that contract's retainage",
        ),
        # THE IDENTITY. Completed-to-date at the latest period, less the sum of every
        # period's payment due, must equal the retainage withheld - because retainage is
        # exactly the part of completed work not paid out. It is checked here per contract
        # rather than only in aggregate, where offsetting errors could cancel.
        Expectation(
            name="billing balances reconcile to the sum of period movements",
            table="fct_Billing",
            failing_sql=(
                "SELECT * FROM ("
                "  SELECT ContractId,"
                "         MAX(CASE WHEN IsLatestPeriod THEN CompletedToDate END) AS completed,"
                "         MAX(CASE WHEN IsLatestPeriod THEN RetainageHeld END)   AS retained,"
                "         SUM(CASE WHEN StatusLabel <> 'DRAFT' THEN CurrentPaymentDue ELSE 0 END) AS paid"
                "  FROM fct_Billing WHERE BillingType = 'Owner' GROUP BY ContractId"
                ") WHERE completed IS NOT NULL"
                "  AND ABS(completed - retained - paid) > GREATEST(1.0, completed * 0.01)"),
            # WARN, not ERROR: a contract can be re-billed or credited in ways that break
            # the identity legitimately, and blocking the whole pipeline for one contract
            # would stop every other number reaching the report.
            severity=SEVERITY_WARN,
            description="cumulative and period-movement billing disagree by more than 1%",
        ),
        # Retainage above 20% is not a normal contract term; it usually means a percent was
        # read as a fraction or an amount landed in a percent column.
        Expectation(
            name="retainage percent is plausible",
            table="fct_Billing",
            failing_sql=("SELECT * FROM fct_Billing "
                         "WHERE RetainagePercent IS NOT NULL AND RetainagePercent > 20"),
            severity=SEVERITY_WARN,
            description="retainage above 20% suggests a percent/fraction mix-up",
        ),
        # This one was written as a blocking ERROR on the assumption that negative
        # retainage meant an inverted sign. It fired on 3 rows, and the rows were right:
        # Procore records a retainage RELEASE as a negative on the period. On
        # PO-24-011-012 the retainage is -489.94 and the payment due is +489.94 - exactly
        # offsetting, which is the release being paid out.
        #
        # So it is a WARN reporting a real event, not an error. Kept rather than deleted:
        # a release is money leaving the balance, month-end should see it, and a *large*
        # one appearing unexpectedly is worth a second look.
        Expectation(
            name="retainage released rather than withheld",
            table="fct_Billing",
            failing_sql=("SELECT * FROM fct_Billing "
                         "WHERE IsLatestPeriod AND RetainageHeld < 0"),
            severity=SEVERITY_WARN,
            description="negative retainage is a release being paid out, not a defect",
        ),
        # GrandTotal includes tax and freight, so it should never be BELOW the line amount.
        Expectation(
            name="direct cost grand total is at least the line amount",
            table="fct_DirectCost",
            failing_sql=("SELECT * FROM fct_DirectCost "
                         "WHERE Amount IS NOT NULL AND GrandTotal IS NOT NULL "
                         "AND GrandTotal < Amount - 0.01"),
            severity=SEVERITY_WARN,
            description="grand total below the line amount means the two are transposed",
        ),
    )

    # -------------------------------------------- vendor <-> cost code, insurance
    suite.add(
        unique_key("bridge_VendorCostCode", ["VendorCostCodeKey"]),
        unique_key("fct_VendorInsurance", ["InsuranceKey"]),
        not_null("bridge_VendorCostCode", "VendorKey"),
        not_null("bridge_VendorCostCode", "CostCodeKey"),
        not_null("fct_VendorInsurance", "VendorKey"),
        referential("bridge_VendorCostCode", "ProjectKey", "dim_Project", "ProjectKey"),
        referential("bridge_VendorCostCode", "CostCodeKey", "dim_CostCode", "CostCodeKey"),
    )

    suite.add(
        # The bridge INNER JOINs lines to their headers, because a line with no vendor
        # cannot be attributed and would otherwise become a silent "unallocated" bucket
        # that every vendor-filtered view drops without saying so. That is the right
        # choice, but it means dropped lines have to be counted SOMEWHERE - this is it.
        # Without this check, the bridge could silently cover a fraction of spend and
        # still look complete.
        # This suite runs against GOLD, so it cannot see the silver line items directly -
        # it checks the consequence instead. If the bridge covers only a sliver of direct
        # cost spend, most lines failed to join and the bridge is materially incomplete
        # while still looking populated.
        Expectation(
            name="the vendor bridge covers most direct cost spend",
            table="bridge_VendorCostCode",
            failing_sql=(
                "SELECT * FROM ("
                "  SELECT (SELECT COALESCE(SUM(Amount), 0) FROM bridge_VendorCostCode"
                "          WHERE AmountType = 'Actual') AS bridge,"
                "         (SELECT COALESCE(SUM(GrandTotal), 0) FROM fct_DirectCost) AS direct"
                ") WHERE direct > 0 AND bridge < direct * 0.5"),
            severity=SEVERITY_WARN,
            description="bridge covers under half of direct spend - lines are not joining",
        ),
        # Spend on the bridge must not exceed what fct_DirectCost says was spent. If it
        # does, lines have been double-counted - the classic fan-out when a join key is
        # not as unique as assumed.
        # ACTUAL only. The committed half is legitimately far larger than direct cost
        # spend - $25.5M committed against $1.5M spent - so comparing the unfiltered total
        # would fire on every run and teach everyone to ignore it.
        Expectation(
            name="bridge actual spend does not exceed direct cost spend",
            table="bridge_VendorCostCode",
            failing_sql=(
                "SELECT * FROM ("
                "  SELECT (SELECT COALESCE(SUM(Amount), 0) FROM bridge_VendorCostCode"
                "          WHERE AmountType = 'Actual') AS bridge,"
                "         (SELECT COALESCE(SUM(GrandTotal), 0) FROM fct_DirectCost) AS direct"
                ") WHERE bridge > direct * 1.01"),
            severity=SEVERITY_ERROR,
            description="bridge spend above direct cost spend means lines fanned out",
        ),
        # A negative committed line is a credit against a subcontract - real, but rare
        # enough to be worth a look, and indistinguishable from an inverted sign without
        # one. Per row, not in aggregate, where a credit and an error cancel.
        Expectation(
            name="committed lines are not negative",
            table="bridge_VendorCostCode",
            failing_sql=("SELECT * FROM bridge_VendorCostCode "
                         "WHERE AmountType = 'Committed' AND Amount < 0"),
            severity=SEVERITY_WARN,
            description="a negative committed line is a credit, or an inverted sign",
        ),
        # COVERAGE, reported as a number rather than assumed. Live this fires on ~228 of
        # 251 vendors, and that IS the finding: the vendor list was never checkable before.
        Expectation(
            name="vendors on a project have a certificate on file",
            table="bridge_ProjectVendor",
            failing_sql=(
                "SELECT v.* FROM bridge_ProjectVendor v "
                "LEFT JOIN fct_VendorInsurance i ON i.VendorKey = v.VendorKey "
                "WHERE i.VendorKey IS NULL"),
            severity=SEVERITY_WARN,
            description="a vendor with no certificate on file cannot be shown as compliant",
        ),
        # CURRENCY, counted apart from coverage. Live, all 105 certificates are lapsed and
        # the newest expired 2025-04-01 - which most likely means the Procore insurance
        # module was abandoned rather than that the subs are uninsured. WARN either way:
        # this is Affect's data to correct, and blocking the report would not help them.
        Expectation(
            name="certificates on file are in date",
            table="fct_VendorInsurance",
            failing_sql=("SELECT * FROM fct_VendorInsurance "
                         "WHERE ExpiryStatus = 'Expired' AND NOT COALESCE(IsExempt, FALSE)"),
            severity=SEVERITY_WARN,
            description="an expired certificate is not coverage - chase the renewal",
        ),
        # A certificate that ends before it starts is a data-entry error, and it makes any
        # validity window computed from the pair meaningless.
        date_order("fct_VendorInsurance", "EffectiveDate", "ExpirationDate",
                   severity=SEVERITY_WARN),
    )

    # ------------------------------------------------------------- freshness
    #
    # Until Key Vault exists, extraction runs locally and lands files, and the nightly
    # pipeline reprocesses whatever is there. That design is sound but it has one silent
    # failure mode: if nobody runs the extractor, every stage still succeeds, the DQ gate
    # still passes, the model still refreshes, and the report shows last quarter's numbers
    # with today's date on the page. Nothing anywhere would say so.
    #
    # These are the checks that say so. WARN rather than ERROR deliberately - stale data is
    # still the best available data, and blocking the pipeline would replace a slightly old
    # report with no report at all.
    suite.add(
        Expectation(
            name="billing data is not stale",
            table="fct_Billing",
            failing_sql=(
                "SELECT * FROM ("
                "  SELECT MAX(PeriodEnd) AS newest FROM fct_Billing"
                # 75 days, not 30: billing is monthly and a period can legitimately close
                # six weeks before anyone looks at it. Past 75 days a month has been missed.
                ") WHERE newest IS NULL OR datediff(CURRENT_DATE, newest) > 75"),
            severity=SEVERITY_WARN,
            description="no billing period closed in 75 days - has the extract been run?",
        ),
        Expectation(
            name="direct cost data is not stale",
            table="fct_DirectCost",
            failing_sql=(
                "SELECT * FROM ("
                "  SELECT MAX(CostDate) AS newest FROM fct_DirectCost"
                # Payroll and expenses post continuously, so this one should be recent.
                ") WHERE newest IS NULL OR datediff(CURRENT_DATE, newest) > 45"),
            severity=SEVERITY_WARN,
            description="no direct cost posted in 45 days - has the extract been run?",
        ),
        Expectation(
            name="field operations data is not stale",
            table="fct_QualityItem",
            failing_sql=(
                "SELECT * FROM ("
                "  SELECT MAX(CreatedDate) AS newest FROM fct_QualityItem"
                ") WHERE newest IS NULL OR datediff(CURRENT_DATE, newest) > 45"),
            severity=SEVERITY_WARN,
            description="no observation or punch item raised in 45 days on any project",
        ),
    )

    # ------------------------------------------------- PQP (Project Quality Plan)
    #
    # The QA/QC subject area has one property the rest of the model does not: its
    # dimensions are TEMPLATES the client hands us, and its facts are ANSWERS against them.
    # An answer whose template key does not resolve is not a rounding error - it is a
    # checklist item nobody can see was failed, sitting in a table that still looks
    # populated. So the referential checks here are ERROR, not WARN.

    # The seeds. A duplicate key in a template fans out every answer joined to it, so
    # "62 of 625 items failed" becomes "124 of 1250" with nothing saying so.
    suite.add(
        unique_key("qc_seed_Trade", ["TradeKey"]),
        unique_key("qc_seed_ChecklistItem", ["ItemKey"]),
        unique_key("qc_seed_Gate", ["GateKey"]),
        unique_key("qc_seed_DohItem", ["ItemKey"]),
        unique_key("dim_QcStatus", ["Domain", "Code"]),
        not_null("qc_seed_ChecklistItem", "TradeKey"),
        not_null("qc_seed_Gate", "GateType"),
    )

    # THE TWO COLLAPSES, checked as counts rather than trusted.
    #
    # 26 trade sheets became one table and three gate paths became one table. Both are
    # right, and both are the kind of change that silently loses rows: a trade whose sheet
    # was skipped, a gate path re-extracted with a different filter. A count is the cheapest
    # possible detector and the workbook's own numbers are the expected values.
    suite.add(
        Expectation(
            name="the checklist template still holds all 625 items",
            table="qc_seed_ChecklistItem",
            failing_sql=("SELECT * FROM (SELECT COUNT(*) AS n, COUNT(DISTINCT TradeKey) AS t "
                         "FROM qc_seed_ChecklistItem) WHERE n <> 625 OR t <> 26"),
            severity=SEVERITY_ERROR,
            description="26 trade sheets collapsed into one table - 625 items across 26 trades",
        ),
        Expectation(
            name="the gate template still holds all three paths",
            table="qc_seed_Gate",
            failing_sql=(
                "SELECT * FROM ("
                "  SELECT SUM(CASE WHEN GateType = 'TCO' THEN 1 ELSE 0 END) AS tco,"
                "         SUM(CASE WHEN GateType = 'FIRE_ALARM' THEN 1 ELSE 0 END) AS fire,"
                "         SUM(CASE WHEN GateType = 'STATUTORY' THEN 1 ELSE 0 END) AS stat"
                "  FROM qc_seed_Gate"
                ") WHERE tco <> 46 OR fire <> 23 OR stat <> 24"),
            severity=SEVERITY_ERROR,
            description="Path to TCO / Fire Alarm / Statutory collapsed to one table: 46/23/24",
        ),
        Expectation(
            name="the DOH checklist still holds all 101 requirements",
            table="qc_seed_DohItem",
            failing_sql="SELECT * FROM (SELECT COUNT(*) AS n FROM qc_seed_DohItem) WHERE n <> 101",
            severity=SEVERITY_ERROR,
            description="a missing DOH requirement is one nobody is tracking against",
        ),
    )

    # Referential integrity. ProjectKey on every manual table, old and new - this is the
    # link that did not exist at all until the man_* tables were wired to silver, so it is
    # checked on all seventeen rather than only on the eight new ones.
    for table in ("man_Wins", "man_Risks", "man_PriorityItems", "man_Flags", "man_Survey",
                  "man_SafetyMonthly", "man_QualityMonthly", "man_Milestones",
                  "man_DailyLogCompliance", "man_QcDfow", "man_QcItp", "man_QcGate",
                  "man_QcSpecialInspection", "man_QcCommissioning",
                  "man_QcInspectorSignIn", "man_QcChecklistResult", "man_QcDohResult"):
        suite.add(referential(table, "ProjectKey", "dim_Project", "ProjectKey"))

    # ------------------------------------------------------------------ dim_Job
    # THE POWER AUTOMATE FLOWS' ONE REAL PRODUCTION RISK, made visible.
    #
    # The two job flows issue sequential numbers by reading max(JobSeq), adding one and
    # writing it back. That is safe only because both triggers carry
    # `runtimeConfiguration.concurrency.runs = 1`. It is a SETTING, not code - the Power
    # Automate designer exposes it under trigger -> Settings -> Concurrency Control, and
    # anyone editing the flow can switch it off without touching a definition file.
    #
    # When it is off, two overlapping runs both read 24, both compute 25, and two different
    # projects are called 26-025. Nothing throws. No copy job fails. The flows report
    # success. It surfaces weeks later when somebody opens the wrong folder and both trees
    # already hold real documents - by which point neither can simply be deleted.
    #
    # power-automate/test_flows.py asserts the setting is present, so removing it shows up
    # in a diff. This is the half that catches it when it is switched off in the LIVE flow,
    # where no diff exists. Blocking, because the numbers are already wrong by then and a
    # stale report beats a report that confidently double-counts a job.
    # Spelled out rather than built with unique_key()/not_null(), because both need to
    # ignore rows that have not been issued a number YET. A person adds a row with just a
    # project name and leaves everything else blank; the flow fills in JobNumber a minute
    # later. Those rows are the normal state of a healthy register, and a check that fires
    # on them is a check that gets muted inside a week - taking the real one with it.
    #
    # unique_key() would also group the NULLs together and report several pending jobs as a
    # collision, which is the same wrong answer arrived at twice.
    suite.add(
        Expectation(
            name="dim_Job.JobNumber.unique",
            table="dim_Job",
            failing_sql=(
                "SELECT JobNumber, COUNT(*) AS n FROM dim_Job "
                "WHERE JobNumber IS NOT NULL AND TRIM(JobNumber) <> '' "
                "GROUP BY JobNumber HAVING COUNT(*) > 1"
            ),
            severity=SEVERITY_ERROR,
            description=("two jobs issued the same number - trigger concurrency is off on "
                         "the Power Automate flows"),
        ),
        # The other half: a row that reached Estimating or Bidding WITHOUT a number is a
        # flow that half-ran. Warning, not blocking - the numbers already in the report are
        # not wrong, one job is just missing from them, and silver has already written the
        # row to the reject log with the reason so it is visible on the DQ page.
        Expectation(
            name="dim_Job.JobNumber.issued_past_requested",
            table="dim_Job",
            failing_sql=(
                "SELECT * FROM dim_Job "
                "WHERE Stage IN ('ESTIMATING', 'BIDDING') "
                "AND (JobNumber IS NULL OR TRIM(JobNumber) = '')"
            ),
            severity=SEVERITY_WARN,
            description="a job past Requested with no number - the flow did not finish",
        ),
    )

    # TradeKey is the controlled key people get wrong - "Concrete Formwork" instead of
    # CONCRETE_FORMWORK. The SharePoint choice column is generated from qc_seed_Trade to
    # make that impossible; these prove it stayed impossible.
    for table in ("man_QcDfow", "man_QcItp", "man_QcCommissioning", "man_QcChecklistResult"):
        suite.add(referential(table, "TradeKey", "qc_seed_Trade", "TradeKey"))

    suite.add(
        referential("man_QcChecklistResult", "ItemKey", "qc_seed_ChecklistItem", "ItemKey"),
        referential("man_QcGate", "GateKey", "qc_seed_Gate", "GateKey"),
        referential("man_QcDohResult", "ItemKey", "qc_seed_DohItem", "ItemKey"),
    )

    # DATE ORDER, and only where it is an INVARIANT.
    #
    # The obvious set here is every plan-vs-actual pair - target vs submitted, planned vs
    # actual, scheduled vs performed. Those are NOT invariants: submitting a filing before
    # its target date, or running an inspection early, is the healthy case, and a check
    # that fires on the healthy case trains everyone to ignore the data-quality page - the
    # same mistake the billing check made before it was scoped to cumulative totals.
    #
    # What IS an invariant is a thing that cannot logically precede its cause: a gate
    # cannot complete before it was submitted, and a report cannot arrive before the
    # inspection that produced it. WARN, because these are dates a human typed and the
    # right response is to go fix the row, not to stop publishing the rest of the page.
    suite.add(
        date_order("man_QcGate", "SubmittedDate", "CompletedDate", severity=SEVERITY_WARN),
        date_order("man_QcSpecialInspection", "PerformedDate", "ReportReceivedDate",
                   severity=SEVERITY_WARN),
    )

    # The plan-vs-actual question asked the way it is actually meant: not "are these dates
    # in order" but "did this gate miss the date it was targeted for". A real management
    # signal with a real action behind it, and it does not fire on a gate delivered early.
    suite.add(Expectation(
        name="gates completed after their target date",
        table="man_QcGate",
        failing_sql=("SELECT * FROM man_QcGate WHERE TargetDate IS NOT NULL "
                     "AND CompletedDate IS NOT NULL AND CompletedDate > TargetDate"),
        severity=SEVERITY_WARN,
        description="a TCO or fire alarm gate closed late - the critical path moved",
    ))

    suite.add(
        # A gate result filed under a different path from its own template means the
        # collapse has mis-routed a row, and every "% of TCO steps complete" is wrong by it.
        Expectation(
            name="gate results agree with their template's path",
            table="man_QcGate",
            failing_sql=("SELECT g.* FROM man_QcGate g "
                         "JOIN qc_seed_Gate s ON s.GateKey = g.GateKey "
                         "WHERE s.GateType <> g.GateType"),
            severity=SEVERITY_ERROR,
            description="a gate result filed under the wrong path skews both paths' progress",
        ),
        # Procore's status vocabulary is configurable per company, so the mapping onto the
        # workbook's codes is a guess that can go stale. An unmapped status is not a
        # pipeline failure - the row is still there with its source text - but it drops out
        # of every status slicer, so it has to be counted out loud.
        Expectation(
            name="Procore QC statuses map to the workbook's vocabulary",
            table="fct_QcSubmittal",
            failing_sql=("SELECT * FROM fct_QcSubmittal "
                         "WHERE SourceStatus IS NOT NULL AND StatusCode IS NULL"),
            severity=SEVERITY_WARN,
            description="an unmapped Procore status drops the row out of every status slicer",
        ),
        # Same argument for trade. Procore's trade is free text and gold resolves it by
        # exact match only, refusing to guess - so the unmapped count is the signal for
        # whether an alias table is worth building.
        Expectation(
            name="Procore trades resolve to a seeded trade",
            table="fct_QcNcr",
            failing_sql="SELECT * FROM fct_QcNcr WHERE HasUnmappedTrade",
            severity=SEVERITY_WARN,
            description="an unmapped trade cannot roll up by trade - alias it or fix Procore",
        ),
        # ERROR, not warn, and the distinction is the point. An unmapped trade is a fact
        # about Procore's vocabulary; an alias pointing at a TradeKey that does not exist
        # is a typo in a CSV we control. It would resolve to NULL and read as "unmapped",
        # so the alias would look like it was never written rather than like it was
        # written wrong - the failure mode this whole engagement keeps meeting.
        referential("qc_seed_TradeAlias", "TradeKey", "qc_seed_Trade", "TradeKey",
                    severity=SEVERITY_ERROR),
    )

    # ------------------------------------------------------ scorecard integrity
    #
    # ERROR, because this is the number leadership reads. The workbook's scorecard was
    # broken for months precisely because nothing checked its arithmetic.
    suite.add(Expectation(
        name="scorecard weights sum to 1.00",
        table="dim_ScorecardWeight",
        failing_sql=("SELECT * FROM (SELECT ROUND(SUM(Weight), 4) AS total "
                     "FROM dim_ScorecardWeight) WHERE total <> 1.0"),
        severity=SEVERITY_ERROR,
        description="weights that do not sum to 1.00 make every score meaningless",
    ))

    return suite


def summarise(results) -> str:
    """One line per failure, blocking first. Written for a notebook log, not a dashboard."""
    blocking = [r for r in results if r.blocking]
    warnings = [r for r in results if not r.passed and not r.blocking]
    broken = [r for r in results if r.failing_rows < 0]

    lines = [f"{len(results)} expectation(s): "
             f"{sum(1 for r in results if r.passed)} passed, "
             f"{len(blocking)} BLOCKING, {len(warnings)} warning(s), "
             f"{len(broken)} could not run"]
    for r in blocking:
        lines.append(f"  BLOCKING  {r.expectation.name}: {r.failing_rows} row(s)")
    for r in warnings:
        lines.append(f"  warn      {r.expectation.name}: {r.failing_rows} row(s)")
    for r in broken:
        lines.append(f"  BROKEN    {r.expectation.name} - the check itself failed to run")
    return "\n".join(lines)


def _selftest() -> None:
    """The suite is configuration, so what is worth asserting is its SHAPE - that the
    severities are assigned deliberately rather than left at the default."""
    suite = build_suite()
    names = [e.name for e in suite.expectations]

    assert len(suite.expectations) >= 30, f"only {len(suite.expectations)} expectations"
    assert len(names) == len(set(names)), "duplicate expectation names"

    errors = [e for e in suite.expectations if e.severity == SEVERITY_ERROR]
    warns = [e for e in suite.expectations if e.severity == SEVERITY_WARN]
    assert errors and warns, "both severities must be used - see the module docstring"

    # Coverage gaps must NEVER block. Blocking on a real business condition is how a
    # pipeline gets muted, and then the blocking checks stop working too.
    for e in suite.expectations:
        if "is in Sage" in e.name or "is in Outbuild" in e.name:
            assert e.severity == SEVERITY_WARN, f"{e.name} must not block the pipeline"

    # An ambiguous mapping MUST block: the crosswalk silently picked one id, and every
    # financial number for that project depends on which.
    amb = next(e for e in suite.expectations if "two ids" in e.name)
    assert amb.severity == SEVERITY_ERROR

    # Every expectation must describe why it exists, or nobody knows what to do when it
    # fires at 6am.
    missing = [e.name for e in suite.expectations if not e.description]
    assert not missing, f"no description: {missing}"

    print(f"  ok  {len(suite.expectations)} expectations, names unique")
    print(f"  ok  {len(errors)} blocking / {len(warns)} warning - both used deliberately")
    print(f"  ok  coverage gaps warn, they never block the pipeline")
    print(f"  ok  an ambiguous crosswalk mapping DOES block")
    print(f"  ok  every expectation carries a description")
    print(f"\ndq suite: 5 checks passed")


if __name__ == "__main__":
    _selftest()
