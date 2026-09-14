"""The data-quality suite: what must be true about gold before anyone reads a number.

Built with `00-platform/lib/dq.py`, which already has the right shape - expectations return
the rows that VIOLATE the rule, so a failure hands you the offending records rather than a
boolean you then have to go investigate.

TWO SEVERITIES, AND THE DIFFERENCE MATTERS:

  ERROR  stops Succeeded-dependent pipeline activities. Direct Lake publication isolation
         must be verified separately. Reserved for things that make a number WRONG -
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
        not_null("fct_BudgetLine", "BudgetLineID"),
        unique_key("fct_BudgetLine", ["ProjectKey", "BudgetLineID"]),
        not_null("fct_ChangeOrder", "ProjectKey"),
        not_null("fct_Invoice", "Amount"),
        not_null("fct_Invoice", "InvoiceKey"),
        unique_key("fct_Invoice", ["InvoiceKey"]),
        not_null("fct_Invoice", "AmountPaid"),
        not_null("fct_Invoice", "Balance"),
        Expectation(
            name="dim_Project.SageJobNumber maps to only one project",
            table="dim_Project",
            failing_sql=("SELECT SageJobNumber, COUNT(*) AS n FROM dim_Project "
                         "WHERE SageJobNumber IS NOT NULL GROUP BY SageJobNumber HAVING COUNT(*) > 1"),
            description="a Sage job assigned to multiple projects duplicates invoice amounts",
        ),
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

    # ------------------------------------------------- owned crosswalks (2026-09-13)
    #
    # sv_project_crosswalk is our committed seed and sv_vendors carries Procore's
    # origin_code; neither is Rebecca's warehouse any more, so their integrity is ours to
    # prove. A key shared by two entities BLOCKS - it attaches money to the wrong one. A key
    # that points nowhere WARNS: the usual cause is timing between systems (a job created in
    # Sage before silver refreshes, a vendor synced before actpay lands), and the join then
    # attaches nothing rather than the wrong thing. Unmapped jobs and unsynced vendors WARN.
    suite.add(
        Expectation(
            name="sv_project_crosswalk Sage job maps to only one project",
            table="sv_project_crosswalk",
            failing_sql=("SELECT sage_project_id, COUNT(DISTINCT procore_project_id) AS n "
                         "FROM sv_project_crosswalk WHERE sage_project_id IS NOT NULL "
                         "GROUP BY sage_project_id HAVING COUNT(DISTINCT procore_project_id) > 1"),
            severity=SEVERITY_ERROR,
            description="one Sage job on two projects duplicates its revenue and cost - fix seed/project_crosswalk.csv",
        ),
        Expectation(
            name="sv_project_crosswalk rows exist in Procore and Sage",
            table="sv_project_crosswalk",
            failing_sql=("SELECT x.* FROM sv_project_crosswalk x "
                         "WHERE x.procore_project_id NOT IN (SELECT project_id FROM sv_projects WHERE project_id IS NOT NULL) "
                         "OR x.sage_project_id NOT IN (SELECT sage_project_id FROM sv_sage_jobs WHERE sage_project_id IS NOT NULL)"),
            severity=SEVERITY_WARN,
            description="a seed row names a project or job the sources do not hold yet - source lag, a typo or a deleted record; check the CSV",
        ),
        Expectation(
            name="Sage jobs with AR/AP but no crosswalk mapping",
            table="sv_sage_jobs",
            failing_sql=("SELECT sage_project_id, COUNT(*) AS invoices FROM ("
                         "SELECT sage_project_id FROM sv_ar_invoices UNION ALL "
                         "SELECT sage_project_id FROM sv_ap_invoices) i "
                         "WHERE sage_project_id IS NOT NULL AND sage_project_id NOT IN "
                         "(SELECT sage_project_id FROM sv_project_crosswalk WHERE sage_project_id IS NOT NULL) "
                         "GROUP BY sage_project_id"),
            severity=SEVERITY_WARN,
            description="money on a Sage job no project owns - figures in dq_DataGap, proposals in dq_CrosswalkCandidate; Affect decides",
        ),
        Expectation(
            name="Sage AP invoices with no job",
            table="sv_ap_invoices",
            failing_sql="SELECT invoice_id, invoice_total FROM sv_ap_invoices WHERE sage_project_id IS NULL",
            severity=SEVERITY_WARN,
            description="AP booked to no Sage job cannot reach any project - listed in dq_DataGap; normal for overhead, worth reviewing",
        ),
        Expectation(
            name="sv_vendors Sage vendor id exists in actpay",
            table="sv_vendors",
            failing_sql=("SELECT v.* FROM sv_vendors v WHERE v.sage_vendor_id IS NOT NULL "
                         "AND v.sage_vendor_id NOT IN (SELECT sage_vendor_id FROM sv_sage_vendors "
                         "WHERE sage_vendor_id IS NOT NULL)"),
            severity=SEVERITY_WARN,
            description="a Procore origin_code that is not (yet) a Sage vendor - the join attaches no Sage name until actpay lands",
        ),
        Expectation(
            name="sv_vendors Sage vendor maps to only one Procore vendor",
            table="sv_vendors",
            failing_sql=("SELECT sage_vendor_id, COUNT(DISTINCT procore_vendor_id) AS n FROM sv_vendors "
                         "WHERE sage_vendor_id IS NOT NULL GROUP BY sage_vendor_id "
                         "HAVING COUNT(DISTINCT procore_vendor_id) > 1"),
            severity=SEVERITY_ERROR,
            description="one Sage vendor on two Procore vendors splits or duplicates its spend - merge in Procore",
        ),
        Expectation(
            name="ERP-synced vendors without origin_code",
            table="sv_vendors",
            failing_sql=("SELECT DISTINCT v.procore_vendor_id, v.vendor_name FROM sv_vendors v "
                         "JOIN sv_project_vendors pv ON pv.vendor_id = v.procore_vendor_id "
                         "WHERE pv.synced_to_erp AND v.sage_vendor_id IS NULL"),
            severity=SEVERITY_WARN,
            description="Procore says the vendor is synced to Sage but carries no Sage id - its spend cannot be joined",
        ),
    )

    # ------------------------------------------------------------ Sage AR
    #
    # fct_Invoice reads our own Sage ingestion as of 2026-08-25, not Rebecca's
    # Revenue_AllTime. These guard the three ways that source can go wrong QUIETLY - each
    # one produces a report that renders perfectly and is wrong.

    # THE $0 TRAP. acrinv.invamt is zero on all 148 live rows; the total is amtpad + invbal.
    # A transform that trusts invamt reports $0 billed with total confidence. Blocking,
    # because a zero revenue figure on a client-facing report is not a warning.
    suite.add(Expectation(
        name="fct_Invoice.Amount is not universally zero",
        table="fct_Invoice",
        failing_sql=(
            "SELECT * FROM fct_Invoice "
            "WHERE NOT EXISTS (SELECT 1 FROM fct_Invoice WHERE Amount <> 0)"
        ),
        severity=SEVERITY_ERROR,
        description="every invoice totals zero - invamt was trusted instead of paid+balance",
    ))

    # Paid + outstanding must equal the total. If the derivation above is ever replaced by
    # a raw column, this catches the drift on the next run rather than at quarter end.
    suite.add(Expectation(
        name="fct_Invoice.Amount reconciles to AmountPaid + Balance",
        table="fct_Invoice",
        failing_sql=(
            "SELECT * FROM fct_Invoice "
            "WHERE Amount IS NOT NULL AND AmountPaid IS NOT NULL AND Balance IS NOT NULL "
            "AND ABS(Amount - (AmountPaid + Balance)) > 0.01"
        ),
        severity=SEVERITY_ERROR,
        description="invoice total no longer equals paid plus outstanding",
    ))

    # The source must not go empty. Sage runs through an on-premises gateway, and the
    # failure mode when that breaks is an empty table rather than an error - which reads
    # downstream as "Affect billed nothing".
    suite.add(Expectation(
        name="fct_Invoice has rows",
        table="fct_Invoice",
        failing_sql=(
            "SELECT * FROM dim_Project "
            "WHERE NOT EXISTS (SELECT 1 FROM fct_Invoice)"
        ),
        severity=SEVERITY_ERROR,
        description="no AR invoices at all - the Sage gateway or dataflow has stopped",
    ))

    # Unmatched jobs are EXPECTED and must stay visible rather than blocking: Sage carries
    # jobs that were never opened in Procore. Warn so the number is watched, because a
    # sudden jump means the crosswalk broke rather than that Affect won work.
    suite.add(Expectation(
        name="fct_Invoice project match rate is not collapsing",
        table="fct_Invoice",
        failing_sql=(
            "SELECT * FROM fct_Invoice f "
            "WHERE NOT EXISTS (SELECT 1 FROM fct_Invoice WHERE HasUnmatchedProject = FALSE)"
        ),
        severity=SEVERITY_WARN,
        description="not one AR invoice resolves to a project - the crosswalk join broke",
    ))

    # AR receipts -> fct_Invoice payment columns (sv_ar_payments, 22_fct_invoice.sql).
    #
    # ERROR: every receipt on a known invoice reaches PaymentsReceived exactly. A mismatch
    # is our aggregation (a fan-out or dropped join), and PaidDate is built from the same sums.
    suite.add(Expectation(
        name="fct_Invoice.PaymentsReceived conserves sv_ar_payments",
        table="fct_Invoice",
        failing_sql=(
            "SELECT f.InvoiceKey, f.PaymentsReceived, s.amount FROM fct_Invoice f "
            "FULL OUTER JOIN (SELECT p.invoice_uid, SUM(p.amount) AS amount FROM sv_ar_payments p "
            "  WHERE p.invoice_uid IN (SELECT invoice_uid FROM sv_ar_invoices) GROUP BY p.invoice_uid) s "
            "ON s.invoice_uid = f.InvoiceKey "
            "WHERE (f.InvoiceKey IS NULL AND s.amount IS NOT NULL) "
            "   OR (s.invoice_uid IS NULL AND f.PaymentsReceived IS NOT NULL) "
            "   OR ABS(COALESCE(f.PaymentsReceived, 0) - COALESCE(s.amount, 0)) > 0.005"
        ),
        severity=SEVERITY_ERROR,
        description="receipt amounts on fct_Invoice no longer sum to the source receipts",
    ))
    # WARN: a receipt whose invoice is not in AR is money no invoice shows.
    suite.add(Expectation(
        name="sv_ar_payments rows with no AR invoice",
        table="fct_Invoice",
        failing_sql=("SELECT * FROM sv_ar_payments "
                     "WHERE invoice_uid NOT IN (SELECT invoice_uid FROM sv_ar_invoices)"),
        severity=SEVERITY_WARN,
        description="receipts that apply to no known AR invoice are absent from fct_Invoice",
    ))
    # WARN, with the amounts: receipts disagreeing with the header's amtpad is a SOURCE fact.
    # Live on 2026-09-13: 3 opening-balance invoices, $227,667.54 paid with no receipt rows,
    # so they carry no PaidDate (_docs/sage-payments-evidence.json).
    suite.add(Expectation(
        name="fct_Invoice receipts reconcile to AmountPaid",
        table="fct_Invoice",
        failing_sql=(
            "SELECT InvoiceKey, InvoiceID, SentDate, AmountPaid, PaymentsReceived, "
            "AmountPaid - COALESCE(PaymentsReceived, 0) AS Difference FROM fct_Invoice "
            "WHERE ABS(COALESCE(AmountPaid, 0) - COALESCE(PaymentsReceived, 0)) > 0.005"
        ),
        severity=SEVERITY_WARN,
        description="Sage receipts do not sum to the header's amount paid; PaidDate is unreliable there",
    ))
    suite.add(Expectation(
        name="fct_Invoice.PaidDate is not before SentDate",
        table="fct_Invoice",
        failing_sql="SELECT * FROM fct_Invoice WHERE PaidDate < SentDate",
        severity=SEVERITY_WARN,
        description="paid before invoiced - a receipt dated wrongly in Sage, and a negative day count",
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

    # Submittal dates. Until 2026-09-14 silver read the intake received_date as the response,
    # which put ~96% of submittals "open" (every Approved one included) and the turnaround
    # KPI at ~1 day. These rules make that class of mapping error loud.
    for fact, type_filter in (("fct_RfiSubmittal", "ItemType = 'Submittal' AND "),
                              ("fct_QcSubmittal", "")):
        suite.add(Expectation(
            # ERROR: a distributed or closed submittal counted open inflates Open and Past
            # Due and hides the real backlog.
            name=f"{fact}: no responded submittal is counted open",
            table=fact,
            failing_sql=f"SELECT * FROM {fact} WHERE {type_filter}IsOpen AND RespondedDate IS NOT NULL",
            severity=SEVERITY_ERROR,
            description="distributed/closed submittals must not count as open",
        ))
    suite.add(Expectation(
        # WARN: a negative turnaround means the response date is really an intake date or a
        # back-dated entry. Real data can do it; a large count means a wrong source field.
        name="submittal responded before it was created",
        table="fct_RfiSubmittal",
        failing_sql=("SELECT * FROM fct_RfiSubmittal WHERE ItemType = 'Submittal' "
                     "AND RespondedDate < CreatedDate"),
        severity=SEVERITY_WARN,
        description="negative submittal turnaround - check which date silver reads",
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

    # Native inspections are source records, not instances of the manual QC templates.
    suite.add(
        unique_key("fct_ProcoreInspection", ["ProjectKey", "InspectionKey"]),
        unique_key("fct_ProcoreInspection", ["InspectionLinkKey"]),
        not_null("fct_ProcoreInspection", "ProjectKey"),
        not_null("fct_ProcoreInspection", "InspectionKey"),
        referential("fct_ProcoreInspection", "ProjectKey", "dim_Project", "ProjectKey"),
    )
    inspection_source = ("SELECT project_id, inspection_id, inspection_number, name, template_id, "
                         "template_name, trade, inspector_name, inspectors_json, source_status, "
                         "inspection_date, due_date, item_count, conforming_item_count, "
                         "deficient_item_count, not_inspected_item_count, na_item_count, "
                         "neutral_item_count, percent_complete FROM sv_qc_inspection")
    inspection_gold = ("SELECT ProjectKey, InspectionKey, InspectionNumber, InspectionName, SourceTemplateId, "
                       "SourceTemplateName, SourceTrade, LegacyInspectorName, InspectorsJson, SourceStatus, "
                       "InspectionDate, DueDate, SourceItemCount, ConformingItemCount, DeficientItemCount, "
                       "NotInspectedItemCount, NotApplicableItemCount, NeutralItemCount, "
                       "SourcePercentComplete FROM fct_ProcoreInspection")
    suite.add(Expectation(
        name="native inspection source values are preserved",
        table="fct_ProcoreInspection",
        failing_sql=f"SELECT * FROM ({inspection_source} EXCEPT ALL {inspection_gold}) missing "
                    f"UNION ALL SELECT * FROM ({inspection_gold} EXCEPT ALL {inspection_source}) changed",
        description="both directions retain every source row, assignment, count and unknown value",
    ))
    suite.add(
        unique_key("fct_ProcoreInspectionItem", ["ProjectKey", "ItemKey"]),
        not_null("fct_ProcoreInspectionItem", "ProjectKey"),
        not_null("fct_ProcoreInspectionItem", "ItemKey"),
        not_null("fct_ProcoreInspectionItem", "InspectionKey"),
        referential("fct_ProcoreInspectionItem", "InspectionLinkKey", "fct_ProcoreInspection", "InspectionLinkKey"),
        Expectation(
            name="native inspection items link to the same project inspection",
            table="fct_ProcoreInspectionItem",
            failing_sql="SELECT i.* FROM fct_ProcoreInspectionItem i LEFT JOIN fct_ProcoreInspection p "
                        "ON i.ProjectKey=p.ProjectKey AND i.InspectionKey=p.InspectionKey "
                        "WHERE p.InspectionKey IS NULL",
            description="an item cannot borrow an inspection ID from a different project",
        ),
    )
    item_source = ("SELECT project_id,item_id,inspection_id,section_id,name,source_status,"
                   "source_response,response_category,response_type,response_json,item_response_json "
                   "FROM sv_qc_inspection_item")
    item_gold = ("SELECT ProjectKey,ItemKey,InspectionKey,SourceSectionId,ItemName,SourceStatus,"
                 "SourceResponse,ResponseCategory,ResponseType,ResponseJson,ItemResponseJson "
                 "FROM fct_ProcoreInspectionItem")
    suite.add(Expectation(
        name="native inspection item source values are preserved",
        table="fct_ProcoreInspectionItem",
        failing_sql=f"SELECT * FROM ({item_source} EXCEPT ALL {item_gold}) missing "
                    f"UNION ALL SELECT * FROM ({item_gold} EXCEPT ALL {item_source}) changed",
        description="all native item records and response types survive without reinterpretation",
    ))
    suite.add(Expectation(
        name="native inspection model link keys match source identity",
        table="fct_ProcoreInspectionItem",
        failing_sql="SELECT * FROM (SELECT ProjectKey, InspectionKey, InspectionLinkKey FROM fct_ProcoreInspection "
                    "UNION ALL SELECT ProjectKey, InspectionKey, InspectionLinkKey FROM fct_ProcoreInspectionItem) k "
                    "WHERE InspectionLinkKey IS NULL OR InspectionLinkKey <> "
                    "CONCAT(CAST(LENGTH(ProjectKey) AS STRING), ':', ProjectKey, InspectionKey)",
        description="model relationships must use the same unambiguous project/inspection identity as source joins",
    ))
    suite.add(Expectation(
        name="native inspection item totals match source headers",
        table="fct_ProcoreInspection",
        failing_sql="SELECT p.ProjectKey, p.InspectionKey, p.SourceItemCount, COALESCE(i.n, 0) AS RetrievedItemCount "
                    "FROM fct_ProcoreInspection p LEFT JOIN "
                    "(SELECT ProjectKey, InspectionKey, COUNT(*) AS n FROM fct_ProcoreInspectionItem "
                    "GROUP BY ProjectKey, InspectionKey) i "
                    "ON p.ProjectKey=i.ProjectKey AND p.InspectionKey=i.InspectionKey "
                    "WHERE p.SourceItemCount IS NOT NULL AND p.SourceItemCount <> COALESCE(i.n, 0)",
        description="a retrieved subset must not masquerade as the complete source inspection; unknown header counts remain unverified",
    ))

    _add_conservation_rules(suite)
    _add_key_and_vocabulary_rules(suite)
    return suite


# Silver source view -> gold fact, per money-bearing fact. Each tuple is:
#   (gold table, source view, source columns, gold columns, gold's own row filter)
# The filter is copied from the gold SQL's WHERE, so the comparison is "source minus what
# gold EXPLICITLY drops"; the dropped rows get their own WARN below so they stay visible.
#
# EXACT, NO TOLERANCE. Gold copies these values (or derives them with the same expression), so a DOUBLE that
# changed at all was changed by a transform. Row-level EXCEPT ALL in both directions
# catches a dropped row, a fanned-out duplicate and an altered amount - offsetting errors
# cannot cancel the way they can in a SUM comparison.
_BILLING_LATEST = ("(ROW_NUMBER() OVER (PARTITION BY billing_type, contract_id "
                   "ORDER BY (status_label = 'DRAFT') ASC, period_end DESC NULLS LAST, "
                   "period_number DESC, billing_id DESC) = 1 AND status_label <> 'DRAFT')")

CONSERVATION = (
    ("fct_ChangeOrder", "sv_prime_change_orders",           # 21_fct_changeorder.sql
     "project_id, change_order_id, amount, TRIM(status), "
     "CASE WHEN LOWER(TRIM(status)) IN ('approved', 'closed') THEN FALSE ELSE TRUE END",
     "ProjectKey, ChangeOrderKey, Amount, StatusLabel, IsPending",
     "project_id IS NOT NULL"),
    ("fct_BudgetLine", "sv_budgets",                        # 20_fct_budgetline.sql
     "project_id, budget_line_id, original_budget, budget_modifications, updated_budget, "
     "forecast_budget, committed_to_date, direct_costs, invoiced_to_date, cost_to_complete, "
     "updated_budget - invoiced_to_date",
     "ProjectKey, BudgetLineID, OriginalBudget, BudgetModifications, BudgetAmount, "
     "ForecastAmount, CommittedAmount, DirectCosts, SpentToDate, CostToComplete, BudgetVariance",
     "project_id IS NOT NULL"),
    # IsLatestPeriod/IsRetainageReleased are derived: the rule repeats 27_fct_billing.sql's
    # ranking (including its billing_id tie-break, so both evaluations agree).
    ("fct_Billing", "sv_billing",                           # 27_fct_billing.sql:66
     "project_id, billing_type, billing_id, status_label, percent_complete, current_payment_due, "
     "original_contract_sum, net_change_by_change_orders, contract_sum_to_date, completed_to_date, "
     "previous_certificates, retainage_amount, total_retainage, stored_retainage_amount, "
     "earned_less_retainage, balance_to_finish, retainage_percent, "
     f"{_BILLING_LATEST}, "
     f"({_BILLING_LATEST} AND COALESCE(retainage_amount, 0) = 0 AND COALESCE(percent_complete, 0) >= 100)",
     "ProjectKey, BillingType, BillingKey, StatusLabel, PercentComplete, CurrentPaymentDue, "
     "OriginalContractSum, NetChangeByChangeOrders, ContractSumToDate, CompletedToDate, "
     "PreviousCertificatesToDate, RetainageHeld, TotalRetainageHeld, StoredRetainageHeld, "
     "EarnedLessRetainageToDate, BalanceToFinish, RetainagePercent, IsLatestPeriod, IsRetainageReleased",
     "project_id IS NOT NULL"),
    ("fct_DirectCost", "sv_direct_costs",                   # 28_fct_directcost.sql
     "project_id, direct_cost_id, amount, grand_total, status_label, "
     "(UPPER(COALESCE(status_label, '')) = 'APPROVED')",
     "ProjectKey, DirectCostKey, Amount, GrandTotal, StatusLabel, IsApproved",
     "project_id IS NOT NULL"),
    # 22_fct_invoice.sql keeps every AR row (unmatched jobs become 'UNMATCHED'), so there
    # is no filter and no dropped-row warning: a missing invoice here is always a defect.
    ("fct_Invoice", "sv_ar_invoices",
     "invoice_uid, invoice_total, amount_paid, invoice_balance, "
     "CASE WHEN invoice_balance IS NULL THEN NULL WHEN invoice_balance = 0 THEN TRUE ELSE FALSE END",
     "InvoiceKey, Amount, AmountPaid, Balance, IsPaid",
     None),
)


def _add_conservation_rules(suite: Suite) -> None:
    for gold, view, src_cols, gold_cols, keep in CONSERVATION:
        src = f"SELECT {src_cols} FROM {view}" + (f" WHERE {keep}" if keep else "")
        dst = f"SELECT {gold_cols} FROM {gold}"
        suite.add(Expectation(
            name=f"{gold} conserves {view} rows and amounts exactly",
            table=gold,
            failing_sql=(f"SELECT 'missing_from_gold' AS side, * FROM ({src} EXCEPT ALL {dst}) m "
                         f"UNION ALL SELECT 'not_in_source' AS side, * FROM ({dst} EXCEPT ALL {src}) c"),
            severity=SEVERITY_ERROR,
            description=("every kept source row reaches gold once with identical amounts; "
                         "a drop, fan-out or altered value makes totals wrong (exact, no tolerance)"),
        ))
        if keep:
            # WARN: a row with no project is a source fact (Procore line not yet attributed),
            # not our defect - but it is money absent from every report total, so the rows
            # themselves (count and amounts) land in the rejects table rather than vanishing.
            suite.add(Expectation(
                name=f"{view} rows dropped from {gold} for having no project",
                table=gold,
                failing_sql=f"SELECT * FROM {view} WHERE NOT ({keep})",
                severity=SEVERITY_WARN,
                description="source money excluded from gold because it has no project",
            ))

    # 24_fct_milestone.sql:44 keeps critical activities only where the Outbuild project maps
    # to Procore. WARN: the unmapped Outbuild projects are an onboarding gap, not a defect.
    suite.add(Expectation(
        name="unattributed Outbuild critical activities dropped from fct_Milestone",
        table="fct_Milestone",
        failing_sql="SELECT * FROM sv_outbuild_activities WHERE is_critical = TRUE AND project_id IS NULL",
        severity=SEVERITY_WARN,
        description="a critical-path activity with no Procore project is absent from every schedule view",
    ))


def _add_key_and_vocabulary_rules(suite: Suite) -> None:
    # Keys. Procore ids are company-global, so change orders and direct costs key alone;
    # Outbuild activities are keyed within the project gold assigns them to.
    suite.add(
        unique_key("fct_ChangeOrder", ["ChangeOrderKey"]),
        unique_key("fct_Milestone", ["ProjectKey", "ActivityKey"]),
        unique_key("fct_FinancialPeriod", ["ProjectKey", "MonthStart"]),
        unique_key("fct_DirectCost", ["DirectCostKey"]),
    )
    # Manual natural keys, exactly the PARTITION BY each silver dedupe enforces
    # (30_manual_silver.sql, 31_qc_manual_silver.sql). A duplicate means that dedupe broke.
    for table, cols in (
        ("man_Wins", ["ProjectKey", "MonthStart", "WinNumber"]),
        ("man_Risks", ["ProjectKey", "MonthStart", "RiskNumber"]),
        ("man_PriorityItems", ["ProjectKey", "MonthStart", "ItemNumber"]),
        ("man_Flags", ["ProjectKey", "MonthStart"]),
        ("man_Survey", ["ProjectKey", "MonthStart", "QuestionNumber"]),
        ("man_SafetyMonthly", ["ProjectKey", "MonthStart"]),
        ("man_QualityMonthly", ["ProjectKey", "MonthStart"]),
        ("man_Milestones", ["ProjectKey", "MilestoneName"]),
        ("man_DailyLogCompliance", ["ProjectKey", "MonthStart"]),
        ("man_QcDfow", ["ProjectKey", "DfowRef"]),
        ("man_QcItp", ["ProjectKey", "ItpRef"]),
        ("man_QcGate", ["ProjectKey", "GateKey"]),
        ("man_QcSpecialInspection", ["ProjectKey", "InspectionRef"]),
        ("man_QcCommissioning", ["ProjectKey", "SystemRef"]),
        ("man_QcInspectorSignIn", ["ProjectKey", "SignInRef"]),
        ("man_QcChecklistResult", ["ProjectKey", "ItemKey"]),
        ("man_QcDohResult", ["ProjectKey", "ItemKey"]),
    ):
        suite.add(unique_key(table, cols))

    # Vendor keys. WARN: dim_Vendor is the Procore company vendor directory only
    # (11_dim_vendor.sql), not a union of observed keys, so a certificate or commitment
    # naming a vendor outside that extract is a source-scope fact rather than a transform
    # bug - and neither table relates to dim_Vendor in the model yet, so no visual drops it.
    suite.add(
        referential("fct_VendorInsurance", "VendorKey", "dim_Vendor", "VendorKey", severity=SEVERITY_WARN),
        referential("bridge_VendorCostCode", "VendorKey", "dim_Vendor", "VendorKey", severity=SEVERITY_WARN),
    )

    # QC codes -> dim_QcStatus, per domain (a code is only meaningful inside its list).
    # ERROR for both halves: Procore codes are emitted by OUR CASE mappings in
    # 24_qc_procore_silver.sql (unmapped source text is NULL, which is excluded), so an
    # unseeded code is a mapping typo; manual codes come from SharePoint choice columns
    # generated from the same qc_status_vocab.csv (make_sharepoint.py), so a miss means the
    # seed and the lists drifted. Either way the row silently leaves every status slicer.
    for table, column, domains in (
        ("fct_QcNcr", "StatusCode", ("NCRLOG_5",)),
        ("fct_QcPunch", "StatusCode", ("PUNCHRCLLOG_5",)),
        ("fct_QcSubmittal", "StatusCode", ("SUBMITTALSMOCKUPS_6",)),
        ("man_QcDfow", "StatusCode", ("DFOWRISKREGISTER_4",)),
        ("man_QcItp", "ResultCode", ("ITP_4",)),
        ("man_QcItp", "StatusCode", ("ITP_6",)),
        ("man_QcGate", "StatusCode", ("PATHTOTCO_6", "PATHTOFIREALARM_7", "STATUTORYINSPECTIONS_5")),
        ("man_QcSpecialInspection", "RequiredCode", ("SPECIALINSPECTIONS_3",)),
        ("man_QcSpecialInspection", "PerformedCode", ("SPECIALINSPECTIONS_2",)),
        ("man_QcSpecialInspection", "StatusCode", ("SPECIALINSPECTIONS_5",)),
        ("man_QcCommissioning", "StatusCode", ("COMMISSIONING_6",)),
        ("man_QcInspectorSignIn", "AgencyCode", ("INSPECTORSIGNIN_11",)),
        ("man_QcInspectorSignIn", "OutcomeCode", ("INSPECTORSIGNIN_5",)),
        ("man_QcChecklistResult", "StageCode", ("EXCAVATION_4",)),
        ("man_QcChecklistResult", "ResultCode", ("EXCAVATION_3",)),
        ("man_QcDohResult", "ResponsibilityCode", ("DOHCHECKLIST_4",)),
        ("man_QcDohResult", "StatusCode", ("DOHCHECKLIST_6",)),
    ):
        in_list = ", ".join(f"'{d}'" for d in domains)
        suite.add(Expectation(
            name=f"{table}.{column}.fk_dim_QcStatus",
            table=table,
            failing_sql=(f"SELECT t.* FROM {table} t WHERE t.{column} IS NOT NULL AND NOT EXISTS "
                         f"(SELECT 1 FROM dim_QcStatus s WHERE s.Domain IN ({in_list}) AND s.Code = t.{column})"),
            severity=SEVERITY_ERROR,
            description=f"{column} must be a code in dim_QcStatus[{in_list}]",
        ))

    # Numeric score bands must tile: ordered by MinValue (inclusive), each band starts where
    # the previous ends (MaxValue exclusive), bands are non-empty, only the lowest may be
    # unbounded below and the highest must be unbounded above. A first band with a finite
    # floor is allowed - incident counts cannot go below 0. Text-matched categories carry no
    # bounds. ERROR: we own this seed, and a gap scores a project as nothing.
    suite.add(Expectation(
        name="dim_ScorecardBand numeric bands tile with no gap or overlap",
        table="dim_ScorecardBand",
        failing_sql=(
            "SELECT CategoryKey, Score, MinValue, MaxValue, MatchValue FROM ("
            "  SELECT *, LAG(MaxValue) OVER (PARTITION BY CategoryKey ORDER BY MinValue NULLS FIRST, MaxValue) AS PrevMax,"
            "         ROW_NUMBER() OVER (PARTITION BY CategoryKey ORDER BY MinValue NULLS FIRST, MaxValue) AS rn,"
            "         COUNT(*) OVER (PARTITION BY CategoryKey) AS cnt"
            "  FROM dim_ScorecardBand WHERE MatchValue IS NULL) b "
            "WHERE (rn = cnt AND MaxValue IS NOT NULL) "
            "   OR (rn > 1 AND (MinValue IS NULL OR PrevMax IS NULL OR MinValue <> PrevMax)) "
            "   OR (MinValue IS NOT NULL AND MaxValue IS NOT NULL AND MinValue >= MaxValue) "
            "UNION ALL SELECT CategoryKey, Score, MinValue, MaxValue, MatchValue FROM dim_ScorecardBand "
            "WHERE MatchValue IS NOT NULL AND (MinValue IS NOT NULL OR MaxValue IS NOT NULL "
            "   OR CategoryKey IN (SELECT CategoryKey FROM dim_ScorecardBand WHERE MatchValue IS NULL))"),
        severity=SEVERITY_ERROR,
        description="a gap leaves a value unscored and an overlap scores it twice",
    ))


SNAPSHOT_TABLE = "fct_DailySnapshot"
SNAPSHOT_VALUES = ("ProjectKey, OpenSubmittals, SubmittalsPastDue, OpenRfis, OpenObservations, "
                   "OpenPunchItems, ArOutstanding, BilledToDate, BudgetAmount, SpentToDate, "
                   "CommittedAmount, CurrentContract, PendingChangeOrders, ApprovedChangeOrders")


def snapshot_suite(snapshot_date: str) -> Suite:
    """Checks run by cd_40_dq_checks straight AFTER capturing fct_DailySnapshot.

    Not part of build_suite: the table does not exist before the first passing run, and
    v_DailySnapshotLive is a temp view of the capture session, so these would read as
    "could not run" - which blocks - inside the main gate.
    """
    return Suite().add(
        unique_key(SNAPSHOT_TABLE, ["ProjectKey", "SnapshotDate"]),
        Expectation(
            name=f"{SNAPSHOT_TABLE} equals live facts at capture",
            table=SNAPSHOT_TABLE,
            # Both directions: a changed value, a missing project and an extra project each
            # leave a row on one side. EXCEPT compares NULLs as equal, which is what a
            # BLANK-preserving snapshot needs.
            failing_sql=(
                f"(SELECT {SNAPSHOT_VALUES} FROM v_DailySnapshotLive "
                f"EXCEPT SELECT {SNAPSHOT_VALUES} FROM {SNAPSHOT_TABLE} WHERE SnapshotDate = DATE '{snapshot_date}') "
                f"UNION ALL "
                f"(SELECT {SNAPSHOT_VALUES} FROM {SNAPSHOT_TABLE} WHERE SnapshotDate = DATE '{snapshot_date}' "
                f"EXCEPT SELECT {SNAPSHOT_VALUES} FROM v_DailySnapshotLive)"),
            description="the saved month-end history must be what the facts said when it was saved",
        ),
        Expectation(
            name=f"{SNAPSHOT_TABLE} rows come only from passing runs",
            table=SNAPSHOT_TABLE,
            failing_sql=(
                f"SELECT s.* FROM {SNAPSHOT_TABLE} s WHERE NOT EXISTS (SELECT 1 FROM meta_PipelineRun r "
                f"WHERE r.RunId = s.RunId AND r.Status = 'ok' AND r.Blocking = 0)"),
            description="a snapshot from a blocked run would freeze unvalidated numbers into history",
        ),
    )


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
