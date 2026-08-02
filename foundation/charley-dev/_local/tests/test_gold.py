"""Assertions over the gold dimensions and facts.

The fixtures in seedrunner.SOURCE_FIXTURES are faithful to the sample project where the
real numbers are known, so two of these checks reproduce values straight from the
reconciliation gate in powerbi/build-plan.md:142-158.

Run:  python test_gold.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from seedrunner import build  # noqa: E402

CHECKS: list[str] = []


def check(label: str) -> None:
    CHECKS.append(label)


def one(con, sql: str):
    row = con.execute(sql).fetchone()
    return row[0] if row else None


def q(con, sql: str):
    return con.execute(sql).fetchall()


# --------------------------------------------------------------------------
# Dimensions
# --------------------------------------------------------------------------


def test_dim_project(con) -> None:
    assert one(con, "SELECT COUNT(*) FROM dim_Project") == 2
    assert one(con, "SELECT COUNT(DISTINCT ProjectKey) FROM dim_Project") == 2
    check("dim_Project[ProjectKey] is unique")

    # OriginalContract is FINANCIALS!C3 verbatim.
    assert one(con, "SELECT OriginalContractAmount FROM dim_Project WHERE ProjectKey='P1'") == 8800000.0
    check("dim_Project[OriginalContractAmount] = 8,800,000 (FINANCIALS!C3)")

    # A project with no prime contract is real (early stage) and must survive as a flag,
    # not be filtered away.
    assert one(con, "SELECT HasPrimeContract FROM dim_Project WHERE ProjectKey='P2'") is False
    assert one(con, "SELECT COUNT(*) FROM dim_Project WHERE ProjectKey='P2'") == 1
    check("dim_Project keeps contract-less projects, flagged not dropped")

    # ProjectNumber stays NULL until the YY-000 mapping is confirmed. A wrong join key is
    # worse than an absent one - it produces plausible numbers.
    assert one(con, "SELECT COUNT(*) FROM dim_Project WHERE ProjectNumber IS NOT NULL") == 0
    check("dim_Project[ProjectNumber] left NULL rather than guessed")


def test_dim_vendor(con) -> None:
    assert one(con, "SELECT COUNT(*) FROM dim_Vendor") == 3  # 2 + Unassigned
    assert one(con, "SELECT COUNT(*) FROM dim_Vendor WHERE VendorKey='UNASSIGNED'") == 1
    check("dim_Vendor carries an Unassigned member so facts never drop out of a join")

    # Source value is '  Acme Concrete  '. Untrimmed text never matches in a join.
    assert one(con, "SELECT VendorName FROM dim_Vendor WHERE VendorKey='V1'") == "Acme Concrete"
    check("dim_Vendor trims source whitespace")

    assert one(con, "SELECT HasSageMatch FROM dim_Vendor WHERE VendorKey='V1'") is True
    assert one(con, "SELECT HasSageMatch FROM dim_Vendor WHERE VendorKey='V2'") is False
    check("dim_Vendor[HasSageMatch] distinguishes matched from unmatched vendors")


def test_dim_costcode(con) -> None:
    assert one(con, "SELECT Division FROM dim_CostCode WHERE CostCodeKey='CC1'") == "03"
    # A code that does not parse gets NULL, not a silently wrong division.
    assert one(con, "SELECT Division FROM dim_CostCode WHERE CostCodeKey='CC2'") is None
    check("dim_CostCode[Division] parses '03-100' and NULLs what it cannot parse")


# --------------------------------------------------------------------------
# Facts
# --------------------------------------------------------------------------


def test_fct_budgetline(con) -> None:
    assert one(con, "SELECT COUNT(*) FROM fct_BudgetLine") == 2
    # MonthStart is the dim_Date join. It must be the 1st or the relationship silently
    # matches nothing.
    assert one(con, "SELECT COUNT(*) FROM fct_BudgetLine WHERE day(MonthStart) <> 1") == 0
    assert one(con, "SELECT DISTINCT MonthStart FROM fct_BudgetLine") == date(2025, 5, 1)
    check("fct_BudgetLine[MonthStart] normalises to the 1st for the dim_Date join")

    # 1,050,000 budget - 350,000 invoiced
    assert one(con, "SELECT BudgetVariance FROM fct_BudgetLine WHERE CostCodeKey='CC1'") == 700000.0
    check("fct_BudgetLine[BudgetVariance] = budget - spent, row level")


def test_fct_changeorder(con) -> None:
    assert one(con, "SELECT COUNT(*) FROM fct_ChangeOrder") == 4
    # Approved is settled; Pending AND Draft are both still outstanding.
    assert one(con, "SELECT IsPending FROM fct_ChangeOrder WHERE ChangeOrderKey='CO1'") is False
    assert one(con, "SELECT COUNT(*) FROM fct_ChangeOrder WHERE IsPending") == 2
    check("fct_ChangeOrder[IsPending] treats Draft as outstanding, not just 'Pending'")

    # FINANCIALS!C5 addends, recoverable as rows instead of lost inside a formula.
    pending = one(con, "SELECT ROUND(SUM(Amount), 2) FROM fct_ChangeOrder WHERE IsPending")
    assert float(pending) == 14708.46, pending
    check("pending CO total is recoverable from rows (14,708.46)")


def test_fct_invoice(con) -> None:
    assert one(con, "SELECT COUNT(*) FROM fct_Invoice") == 3

    # An AR row whose Sage job does not resolve must be KEPT and flagged. Dropping it is
    # how a billing total silently stops reconciling.
    assert one(con, "SELECT COUNT(*) FROM fct_Invoice WHERE HasUnmatchedProject") == 1
    assert one(con, "SELECT ProjectKey FROM fct_Invoice WHERE HasUnmatchedProject") == "UNMATCHED"
    check("fct_Invoice keeps unmatched AR rows, flagged rather than dropped")

    assert one(con, "SELECT COUNT(*) FROM fct_Invoice WHERE IsPaid") == 1
    assert one(con, "SELECT ROUND(SUM(Balance), 2) FROM fct_Invoice WHERE ProjectKey='P1'") == 300000.0
    check("fct_Invoice[IsPaid] and outstanding balance agree")


def test_fct_rfisubmittal(con) -> None:
    # BOTH arms, as of 2026-08-02. RFIs are the half of the workbook's only chart that has
    # never been automated anywhere - no RFI table exists in the existing warehouse - so
    # asserting the union is asserting the new capability, not just the row count.
    assert one(con, "SELECT COUNT(*) FROM fct_RfiSubmittal") == 5
    assert one(con, "SELECT COUNT(*) FROM fct_RfiSubmittal WHERE ItemType='Submittal'") == 3
    assert one(con, "SELECT COUNT(*) FROM fct_RfiSubmittal WHERE ItemType='RFI'") == 2
    check("fct_RfiSubmittal unions submittals AND RFIs, split by ItemType")

    # ItemKey is only unique WITHIN an arm - Procore numbers RFIs and submittals
    # independently, so the model keys on the pair.
    assert one(con, "SELECT COUNT(*) FROM (SELECT DISTINCT ItemType, ItemKey "
                    "FROM fct_RfiSubmittal)") == 5
    check("ItemType + ItemKey is unique across both arms")

    # The RFI arm must behave identically to the submittal arm - same derivations, not a
    # near-copy that drifts.
    assert one(con, "SELECT IsOpen FROM fct_RfiSubmittal WHERE ItemType='RFI' AND ItemKey='R1'") is True
    assert one(con, "SELECT IsOpen FROM fct_RfiSubmittal WHERE ItemType='RFI' AND ItemKey='R2'") is False
    check("the RFI arm derives IsOpen the same way the submittal arm does")

    # Open is derived from the data (no response yet), not from status text, which varies
    # by Procore configuration.
    assert one(con, "SELECT IsOpen FROM fct_RfiSubmittal WHERE ItemKey='SB1'") is True
    assert one(con, "SELECT IsOpen FROM fct_RfiSubmittal WHERE ItemKey='SB2'") is False
    check("fct_RfiSubmittal[IsOpen] derives from RespondedDate, not status text")

    # A responded item is not past due even if its due date has gone.
    assert one(con, "SELECT IsPastDue FROM fct_RfiSubmittal WHERE ItemKey='SB2'") is False
    assert one(con, "SELECT IsPastDue FROM fct_RfiSubmittal WHERE ItemKey='SB1'") is True
    check("fct_RfiSubmittal[IsPastDue] only counts items still open")

    assert one(con, "SELECT CostCodeKey FROM fct_RfiSubmittal WHERE ItemKey='SB3'") == "UNASSIGNED"
    check("fct_RfiSubmittal routes a missing cost code to UNASSIGNED")

    # IsCritical stays NULL: the workbook never defines "critical" (open question #5).
    assert one(con, "SELECT COUNT(*) FROM fct_RfiSubmittal WHERE IsCritical IS NOT NULL") == 0
    check("fct_RfiSubmittal[IsCritical] left NULL - 'critical' is undefined by the client")


def test_fct_milestone(con) -> None:
    # Outbuild holds the whole schedule; only the critical path is the milestone list.
    assert one(con, "SELECT COUNT(*) FROM fct_Milestone") == 2
    assert one(con, "SELECT COUNT(*) FROM fct_Milestone WHERE ActivityKey='A2'") == 0
    check("fct_Milestone keeps only critical-path activities")

    # Excel defect #6 caught at load time rather than shipped into a rollup.
    assert one(con, "SELECT HasDateInversion FROM fct_Milestone WHERE ActivityKey='A3'") is True
    assert one(con, "SELECT HasDateInversion FROM fct_Milestone WHERE ActivityKey='A1'") is False
    check("fct_Milestone[HasDateInversion] flags start > finish (defect #6)")

    # Progress is a 0-1 fraction so the report formats it once, not twice.
    assert one(con, "SELECT MAX(PercentComplete) FROM fct_Milestone") <= 1.0
    check("fct_Milestone[PercentComplete] stays a 0-1 fraction")


def test_fct_financialperiod(con) -> None:
    # Pinned to May: the gate is a single month's numbers from the workbook, and P1 now
    # spans two months so that the cumulative check below has something to bite on.
    row = q(
        con,
        "SELECT ROUND(OriginalContract,2), ROUND(CurrentContract,2), "
        "ROUND(PendingChangeOrders,2), ROUND(PercentBoughtOut,4) "
        "FROM fct_FinancialPeriod WHERE ProjectKey='P1' AND MonthStart = DATE '2025-05-01'",
    )
    assert len(row) == 1, row
    original, current, pending, bought_out = (float(v) for v in row[0])

    # === RECONCILIATION GATE (powerbi/build-plan.md:142-158) ===
    assert original == 8800000.0, original
    assert current == 9116960.48, current
    check("GATE: [Current Contract] = 9,116,960.48 - matches the workbook exactly")

    growth = (current - original) / original
    assert round(growth * 100, 2) == 3.60, growth
    check("GATE: [Contract Growth %] = 3.60% - matches the workbook exactly")

    # Only unapproved COs are pending; the approved one has already moved into the contract.
    assert pending == 14708.46, pending
    check("fct_FinancialPeriod[PendingChangeOrders] excludes the approved CO")

    # committed 1,380,000 / budget 1,550,000
    assert bought_out == 0.8903, bought_out
    check("fct_FinancialPeriod[PercentBoughtOut] = committed / budgeted")

    # === CHANGE ORDERS ACCUMULATE ===
    # The regression this file did not catch. CO4 is a 100,000 approved CO in June; June's
    # contract must be May's PLUS that, not June's activity alone. Until 2026-08-02 this
    # read 8,900,000 - May's 316,960.48 approved CO silently dropped out of the contract
    # the moment a later month existed, and the DAX reads the LAST month per project, so
    # the portfolio understated by $4.85M and Contract Growth showed 0.00%.
    june = q(
        con,
        "SELECT ROUND(CurrentContract,2), ROUND(PendingChangeOrders,2) "
        "FROM fct_FinancialPeriod WHERE ProjectKey='P1' AND MonthStart = DATE '2025-06-01'",
    )
    assert len(june) == 1, june
    june_current, june_pending = (float(v) for v in june[0])
    assert june_current == round(current + 100000.0, 2), (june_current, current)
    check("fct_FinancialPeriod[CurrentContract] carries prior months' approved COs forward")

    # Pending is a running total for the same reason: a CO still unapproved in June was
    # already unapproved in May, and must not drop off because June added no new ones.
    assert june_pending == pending, (june_pending, pending)
    check("fct_FinancialPeriod[PendingChangeOrders] accumulates rather than resetting")

    # A contract only shrinks when a change order was itself negative. Asserting plain
    # monotonicity would be wrong - production has five genuine credits, and the first
    # version of this check called all five a bug. So the invariant is that every decrease
    # is ACCOUNTED FOR by that month's approved COs, which still catches a roll-up that
    # resets while allowing a credit through.
    assert one(
        con,
        "SELECT COUNT(*) FROM ("
        "  SELECT f.ProjectKey, f.MonthStart,"
        "         f.CurrentContract - LAG(f.CurrentContract) OVER "
        "           (PARTITION BY f.ProjectKey ORDER BY f.MonthStart) AS d,"
        "         (SELECT COALESCE(SUM(c.Amount), 0) FROM fct_ChangeOrder c"
        "           WHERE c.ProjectKey = f.ProjectKey AND c.MonthStart = f.MonthStart"
        "             AND NOT c.IsPending) AS approved"
        "  FROM fct_FinancialPeriod f"
        ") WHERE d < -0.005 AND ABS(d - approved) > 0.005",
    ) == 0
    check("fct_FinancialPeriod[CurrentContract] only falls by that month's credit COs")

    # The unmatched AR row still produces a period row, so the money is visible somewhere
    # rather than silently vanishing from the portfolio total.
    assert one(con, "SELECT COUNT(*) FROM fct_FinancialPeriod WHERE ProjectKey='UNMATCHED'") == 1
    check("unmatched billing still surfaces as its own period row")


def test_referential_integrity(con) -> None:
    """Every fact key must resolve to its dimension, or the report drops rows silently."""
    for fact, column, dim, key in [
        ("fct_BudgetLine", "ProjectKey", "dim_Project", "ProjectKey"),
        ("fct_BudgetLine", "CostCodeKey", "dim_CostCode", "CostCodeKey"),
        ("fct_ChangeOrder", "ProjectKey", "dim_Project", "ProjectKey"),
        ("fct_RfiSubmittal", "ProjectKey", "dim_Project", "ProjectKey"),
        ("fct_RfiSubmittal", "CostCodeKey", "dim_CostCode", "CostCodeKey"),
        ("fct_Milestone", "ProjectKey", "dim_Project", "ProjectKey"),
    ]:
        orphans = one(
            con,
            f"SELECT COUNT(*) FROM {fact} f LEFT JOIN {dim} d ON f.{column} = d.{key} "
            f"WHERE f.{column} IS NOT NULL AND d.{key} IS NULL",
        )
        assert orphans == 0, f"{fact}.{column} has {orphans} orphan(s)"
    check("all 6 fact->dimension keys resolve (no orphans)")

    # Every fact MonthStart must exist in the calendar, or time intelligence silently
    # returns blank - the exact failure mode dim_Date was built to eliminate.
    for fact in ("fct_BudgetLine", "fct_ChangeOrder", "fct_Invoice", "fct_RfiSubmittal",
                 "fct_Milestone", "fct_FinancialPeriod"):
        missing = one(
            con,
            f"SELECT COUNT(*) FROM {fact} f LEFT JOIN dim_Date d ON f.MonthStart = d.Date "
            f"WHERE f.MonthStart IS NOT NULL AND d.Date IS NULL",
        )
        assert missing == 0, f"{fact}.MonthStart has {missing} date(s) outside dim_Date"
    check("every fact MonthStart resolves to dim_Date")



def test_crosswalks(con) -> None:
    """The crosswalk is what makes "integrated across three systems" a fact rather than a
    claim - and its job is to make GAPS visible, not to hide them behind an inner join."""

    # Every Procore project appears, including the one in no other system. An INNER JOIN
    # here is the failure mode: a project missing from Sage contributes zero revenue to
    # every financial measure WITHOUT erroring, so it reads as a project that never billed.
    assert one(con, "SELECT COUNT(*) FROM dim_ProjectCrosswalk") == 2
    assert one(con, "SELECT CoverageStatus FROM dim_ProjectCrosswalk WHERE ProjectKey='P2'")         == "Procore only - no financials, no schedule"
    assert one(con, "SELECT SystemCount FROM dim_ProjectCrosswalk WHERE ProjectKey='P2'") == 1
    check("dim_ProjectCrosswalk keeps unmatched projects and names the gap")

    assert one(con, "SELECT SystemCount FROM dim_ProjectCrosswalk WHERE ProjectKey='P1'") == 3
    assert one(con, "SELECT IsInSage FROM dim_ProjectCrosswalk WHERE ProjectKey='P1'") is True
    assert one(con, "SELECT IsInOutbuild FROM dim_ProjectCrosswalk WHERE ProjectKey='P1'") is True
    check("a project present in all three systems reports SystemCount 3")

    # The match METHOD is recorded, so a fuzzy match can never be mistaken for a certain one
    # once name-similarity fallbacks exist. Today everything is an exact key join.
    assert one(con, "SELECT SageMatchMethod FROM dim_ProjectCrosswalk WHERE ProjectKey='P1'")         == "CROSSWALK_TABLE"
    assert one(con, "SELECT OutbuildMatchMethod FROM dim_ProjectCrosswalk WHERE ProjectKey='P2'")         == "UNMATCHED"
    check("every match records HOW it was made, not just that it was")

    # A vendor with no Sage id is normal (invited to bid, never paid) and must not be
    # dropped; the name mismatch flag is the early warning that a mapping has drifted.
    assert one(con, "SELECT COUNT(*) FROM dim_VendorCrosswalk") == 2
    assert one(con, "SELECT IsInSage FROM dim_VendorCrosswalk WHERE VendorKey='V2'") is False
    assert one(con, "SELECT HasNameMismatch FROM dim_VendorCrosswalk WHERE VendorKey='V1'") is True
    check("dim_VendorCrosswalk keeps unmatched vendors and flags name drift")

    # The CSI division is a substring nobody had extracted; parsing it once here is what
    # lets every visual group the same way.
    assert one(con, "SELECT DivisionCode FROM dim_CostCodeCrosswalk WHERE CostCode='03-100'") == "03"
    # A code that does not parse still appears - flagged, not silently dropped from a subtotal.
    assert one(con, "SELECT HasUnparseableCode FROM dim_CostCodeCrosswalk "
                    "WHERE CostCodeName='General'") is True
    assert one(con, "SELECT SageMatchMethod FROM dim_CostCodeCrosswalk LIMIT 1") == "PENDING_SAGE_INGEST"
    check("dim_CostCodeCrosswalk parses the CSI division and flags codes that do not")


def test_fct_qualityitem(con) -> None:
    """Observations + punch items, the quality half of the scorecard.

    Neither exists anywhere in the existing warehouse, so this fact is entirely new
    capability - and it retires workbook defect #2, where QUALITY!D5:D6 read SAFETY
    orientations. Sourcing the counts from the item records makes that class of mistake
    impossible rather than merely corrected.
    """
    assert one(con, "SELECT COUNT(*) FROM fct_QualityItem") == 4
    assert one(con, "SELECT COUNT(*) FROM fct_QualityItem WHERE ItemType='Observation'") == 2
    assert one(con, "SELECT COUNT(*) FROM fct_QualityItem WHERE ItemType='PunchItem'") == 2
    check("fct_QualityItem unions observations and punch items, split by ItemType")

    # Open is derived from ClosedDate, not from status text - Procore's status vocabulary
    # is configurable per company, so a rule keyed to the word "closed" breaks on a rename.
    assert one(con, "SELECT IsOpen FROM fct_QualityItem WHERE ItemKey='OB1'") is True
    assert one(con, "SELECT IsOpen FROM fct_QualityItem WHERE ItemKey='PI2'") is False
    check("fct_QualityItem[IsOpen] derives from ClosedDate, not status text")

    # A late-but-closed item is not outstanding. Getting this wrong inflates every
    # past-due count with work that is already finished.
    assert one(con, "SELECT IsPastDue FROM fct_QualityItem WHERE ItemKey='OB2'") is False
    assert one(con, "SELECT IsPastDue FROM fct_QualityItem WHERE ItemKey='PI1'") is True
    check("IsPastDue counts only items still open")

    # A punch item with no cost code must survive - dropping it would quietly shrink
    # every quality count on projects that do not code their punch list.
    assert one(con, "SELECT COUNT(*) FROM fct_QualityItem WHERE CostCodeKey IS NULL") == 3
    check("items without a cost code are kept, not dropped")


def test_fct_safetymonthly(con) -> None:
    """Hours worked and incidents per project-month - SAFETY!Table1, typed by hand today.

    Hours matter as much as incidents: a count without them cannot be compared between a
    12-person job and a 200-person one, which is the whole reason TRIR exists.
    """
    # P1 has hours + incidents; P2 has an incident and no manpower log. A FULL OUTER JOIN
    # keeps both - an inner join would drop P2 entirely and understate the incident count.
    assert one(con, "SELECT COUNT(*) FROM fct_SafetyMonthly") == 2
    assert one(con, "SELECT HasNoManpowerLog FROM fct_SafetyMonthly WHERE ProjectKey='P2'") is True
    check("fct_SafetyMonthly keeps months with incidents but no logged hours")

    assert one(con, "SELECT HoursWorked FROM fct_SafetyMonthly WHERE ProjectKey='P1'") == 1000.0
    assert one(con, "SELECT IncidentCount FROM fct_SafetyMonthly WHERE ProjectKey='P1'") == 2
    assert one(con, "SELECT RecordableIncidents FROM fct_SafetyMonthly WHERE ProjectKey='P1'") == 1
    check("hours sum across days; recordables are distinguished from all incidents")

    # TRIR = recordables per 200,000 hours. 1 recordable / 1,000 hours = 200.
    assert one(con, "SELECT ROUND(TRIR, 1) FROM fct_SafetyMonthly WHERE ProjectKey='P1'") == 200.0
    check("TRIR uses the OSHA 200,000-hour base")

    # NULL, not zero, with no hours. A zero would read as a perfect safety record on a
    # project that simply logged nothing.
    assert one(con, "SELECT TRIR FROM fct_SafetyMonthly WHERE ProjectKey='P2'") is None
    check("TRIR is NULL when there are no hours, never a misleading zero")


def test_fct_billing(con) -> None:
    """Progress billing - and the cumulative-balance trap it exists to prevent.

    Every `ToDate` column plus RetainageHeld is a running balance restated in full on each
    period. On the real data, summing RetainageHeld across all 607 rows gives $9,046,211.75
    against a true $1,316,755.91 - a near-sevenfold overstatement that would look entirely
    plausible on a card and that nobody could check without the source.
    """
    # Drafts stay in the table. They are real pending work, and dropping a row to make a
    # flag behave is how you end up unable to answer "what is waiting to be billed?".
    assert one(con, "SELECT COUNT(*) FROM fct_Billing") == 6
    assert one(con, "SELECT COUNT(*) FROM fct_Billing WHERE IsLatestPeriod") == 2
    check("every billing period is kept; exactly one per contract carries the balance")

    # The trap, made a number. The naive sum multiplies one contract's retainage and adds
    # a draft and an orphan on top; the guarded sum is the money actually held.
    assert one(con, "SELECT SUM(RetainageHeld) FROM fct_Billing") == 179276.0
    assert one(con, "SELECT SUM(RetainageHeld) FROM fct_Billing WHERE IsLatestPeriod") == 34000.0
    check("summing a cumulative column overstates 5x here; IsLatestPeriod is the guard")

    # B2 and B3 share a period_end, as three real periods on contract ...513836 do.
    # Ordering on the date alone makes the winner arbitrary - and picks the wrong balance.
    assert one(con, "SELECT BillingKey FROM fct_Billing "
                    "WHERE IsLatestPeriod AND BillingType='Owner'") == "B3"
    check("a tied period_end breaks on period_number, not arbitrarily")

    # A draft has not been issued, so its retainage is not held by anyone. B4 has the
    # latest date on its contract and must still lose.
    assert one(con, "SELECT IsLatestPeriod FROM fct_Billing WHERE BillingKey='B4'") is False
    # B6 is the only billing on its contract and is a draft, so that contract has no
    # current balance at all rather than a speculative one.
    assert one(con, "SELECT IsLatestPeriod FROM fct_Billing WHERE BillingKey='B6'") is False
    check("a draft never wins the ranking, even when it is the only row")

    # Owner contract C1 and subcontract C1 are different id spaces that happen to collide.
    # Partitioning on contract alone would let one direction hide the other's balance.
    assert one(con, "SELECT COUNT(*) FROM fct_Billing "
                    "WHERE IsLatestPeriod AND ContractId='C1'") == 2
    check("billing direction partitions the ranking, so colliding ids cannot merge")

    # The independent cross-check: CurrentPaymentDue is the only period movement here, so
    # it sums, and it must reach the same place the cumulative column reports.
    assert one(con, "SELECT SUM(CurrentPaymentDue) FROM fct_Billing "
                    "WHERE BillingType='Owner' AND StatusLabel<>'DRAFT'") == 570000.0
    assert one(con, "SELECT CompletedToDate FROM fct_Billing WHERE BillingKey='B3'") == 600000.0
    check("the sum-safe column reconciles against the cumulative one")


def test_fct_directcost(con) -> None:
    """Direct costs - the only self-performed labour anywhere in the platform."""
    assert one(con, "SELECT COUNT(*) FROM fct_DirectCost") == 3
    assert one(con, "SELECT SUM(GrandTotal) FROM fct_DirectCost") == 14000.0
    check("direct costs are discrete transactions and sum across any grouping")

    assert one(con, "SELECT CostCategory FROM fct_DirectCost WHERE DirectCostKey='D1'") \
        == "Self-Performed Labour"
    check("payroll is labelled as the self-performed labour it is")

    # Unapproved spend stays visible. "What is sitting unapproved at month end?" is a real
    # question, and filtering it away in the fact makes it unanswerable.
    assert one(con, "SELECT COUNT(*) FROM fct_DirectCost WHERE NOT IsApproved") == 1
    check("unapproved cost is flagged, not filtered away")


def test_bridge_projectvendor(con) -> None:
    """The vendor and insurance list - deliverable D8, from data already landed."""
    assert one(con, "SELECT COUNT(*) FROM bridge_ProjectVendor") == 2
    check("the bridge pairs vendors to the projects they are actually on")

    # A vendor invoiced in Procore but never written back to Sage is a reconciliation gap
    # that nothing today would surface.
    assert one(con, "SELECT COUNT(*) FROM bridge_ProjectVendor WHERE IsMissingFromErp") == 1
    check("vendors missing from the ERP are visible rather than assumed clean")


def test_bridge_vendorcostcode(con) -> None:
    """Phase 0 item 3 - the vendor <-> cost-code linkage, "invoice as the bridge".

    It exists in no single Procore object: the direct cost header has the vendor and no
    cost code, the line items have the cost code and no vendor. The line's `holder` is
    what joins them.
    """
    # Direct: L1+L2 share (P1, V1, CC1) and roll up to one ACTUAL row; L4 is a different
    # cost code. L3 is excluded (its holder is a commitment, not a direct cost).
    # Commitments: CL1 gives V1/CC1 a COMMITTED row, CL2 gives V3/CC2 one. CL3 is excluded.
    assert one(con, "SELECT COUNT(*) FROM bridge_VendorCostCode") == 4
    check("lines roll up per project, vendor, cost code AND amount type")

    assert one(con, "SELECT Amount FROM bridge_VendorCostCode "
                    "WHERE VendorKey='V1' AND CostCodeKey='CC1' AND AmountType='Actual'") == 1600.0
    assert one(con, "SELECT LineItemCount FROM bridge_VendorCostCode "
                    "WHERE VendorKey='V1' AND CostCodeKey='CC1' AND AmountType='Actual'") == 2
    check("actual spend sums the lines, using the total that hit the job")

    # COMMITTED IS NOT SPENT. V1/CC1 has both, and they must stay two rows - summing them
    # counts the same work once when committed and again when paid.
    assert one(con, "SELECT Amount FROM bridge_VendorCostCode "
                    "WHERE VendorKey='V1' AND CostCodeKey='CC1' AND AmountType='Committed'") == 390000.0
    assert one(con, "SELECT COUNT(*) FROM bridge_VendorCostCode "
                    "WHERE VendorKey='V1' AND CostCodeKey='CC1'") == 2
    check("actual and committed are separate rows, never a blended total")

    # Procore reuses `holder` across object types and the id spaces can collide. L3 (a
    # Commitment::Item among direct cost lines) and CL3 (a WorkOrderContract line pointing
    # at a purchase order id) are both traps - neither may reach the bridge.
    assert one(con, "SELECT COUNT(*) FROM bridge_VendorCostCode WHERE Amount IN (9999.0, 7777.0)") == 0
    check("a mismatched holder type is never attributed to the wrong contract or vendor")

    # The bridge exists so dim_Vendor and dim_CostCode can filter each other - neither can
    # do that directly, since a vendor spans codes and a code spans vendors.
    assert one(con, "SELECT COUNT(DISTINCT VendorKey) FROM bridge_VendorCostCode") == 3
    check("the model can now slice spend by vendor AND cost code")


def test_fct_vendorinsurance(con) -> None:
    """D8 - the insurance half of the vendor list."""
    assert one(con, "SELECT COUNT(*) FROM fct_VendorInsurance") == 3
    check("every certificate on file is kept")

    # Lapsed, in date and exempt are three different states needing three different
    # actions. A single "compliant" boolean merges them and the report becomes a list
    # nobody works from.
    assert one(con, "SELECT ExpiryStatus FROM fct_VendorInsurance WHERE InsuranceKey='I1'") \
        == "Expired"
    assert one(con, "SELECT ExpiryStatus FROM fct_VendorInsurance WHERE InsuranceKey='I2'") \
        == "Current"
    assert one(con, "SELECT ComplianceState FROM fct_VendorInsurance WHERE InsuranceKey='I1'") \
        == "Lapsed"
    assert one(con, "SELECT ComplianceState FROM fct_VendorInsurance WHERE InsuranceKey='I3'") \
        == "Exempt"
    check("lapsed, in date and exempt stay distinguishable")

    assert one(con, "SELECT IsExpired FROM fct_VendorInsurance WHERE InsuranceKey='I1'") is True
    assert one(con, "SELECT IsExpired FROM fct_VendorInsurance WHERE InsuranceKey='I2'") is False
    check("expiry is evaluated at load time and stored, not recomputed per render")

def main() -> int:
    con = build()
    for fn in (
        test_dim_project, test_dim_vendor, test_dim_costcode,
        test_fct_budgetline, test_fct_changeorder, test_fct_invoice,
        test_fct_rfisubmittal, test_fct_milestone, test_fct_financialperiod,
        test_referential_integrity, test_crosswalks, test_fct_qualityitem, test_fct_safetymonthly, test_fct_billing, test_fct_directcost, test_bridge_projectvendor, test_bridge_vendorcostcode, test_fct_vendorinsurance):
        fn(con)
    for label in CHECKS:
        print(f"  ok  {label}")
    print(f"\ntest_gold: {len(CHECKS)} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
