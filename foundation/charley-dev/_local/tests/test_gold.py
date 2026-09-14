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


def rebuild_with(con, view_sql: str, gold_file: str, query: str):
    """Swap one silver view, rebuild one gold file, read the result, roll it all back."""
    import seedrunner
    con.execute("BEGIN")
    try:
        con.execute(view_sql)
        gold_sql = (seedrunner.CHARLEY_DEV / "02-transformation/sql/gold" / gold_file).read_text()
        for sql in seedrunner.split_statements(gold_sql):
            con.execute(sql)
        return q(con, query)
    finally:
        con.execute("ROLLBACK")


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
    # Two real projects plus the UNMATCHED member unmatched AR points at.
    assert one(con, "SELECT COUNT(*) FROM dim_Project") == 3
    assert one(con, "SELECT COUNT(DISTINCT ProjectKey) FROM dim_Project") == 3
    assert q(con, "SELECT ProjectName, SageJobNumber FROM dim_Project WHERE ProjectKey='UNMATCHED'")         == [("Unassigned project (no Procore match)", None)]
    check("dim_Project carries an UNMATCHED member, so unmatched AR is labelled, not (Blank)")
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

    # THE SAGE JOIN. sv_projects.sage_project_id is a hardcoded NULL in production
    # (01_source_views_cd.sql:43), so SageJobNumber has to come from sv_project_crosswalk.
    # When it came from sv_projects instead, every AR invoice resolved to UNMATCHED - no
    # error, no row-count change, $23.7M of receivables attached to no project.
    assert one(con, "SELECT SageJobNumber FROM dim_Project WHERE ProjectKey='P1'") == "S100"
    check("dim_Project[SageJobNumber] resolves through the crosswalk, not sv_projects")

    # IsInCrosswalk was derived from the same wrong source, so it read TRUE for every
    # project and the flag meant to catch this could never fire.
    assert one(con, "SELECT IsInCrosswalk FROM dim_Project WHERE ProjectKey='P1'") is True
    assert one(con, "SELECT IsInCrosswalk FROM dim_Project WHERE ProjectKey='P2'") is False
    check("dim_Project[IsInCrosswalk] is FALSE for a project with no Sage mapping")


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

    rows = rebuild_with(con, """CREATE OR REPLACE VIEW sv_cost_codes AS SELECT * FROM (VALUES
        ('CC1', '03-100', 'Concrete'), ('D1', '1-1000', 'General Requirements'),
        ('D2', 'AB-100', 'Not numeric'), ('D3', '123-4', 'Three digits')
        ) AS t(cost_code_id, cost_code, cost_code_name)""", "12_dim_costcode.sql",
        "SELECT CostCodeKey, Division FROM dim_CostCode WHERE CostCodeKey IN ('CC1','D1','D2','D3') ORDER BY 1")
    assert rows == [("CC1", "03"), ("D1", "01"), ("D2", None), ("D3", None)], rows
    check("dim_CostCode[Division] zero-pads '1' to '01' so one division is not split in two")


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
    assert one(con, "SELECT COUNT(*) FROM fct_ChangeOrder") == 5
    assert one(con, "SELECT IsPending FROM fct_ChangeOrder WHERE ChangeOrderKey='CO5'") is False
    # Approved is settled; Pending AND Draft are both still outstanding.
    assert one(con, "SELECT IsPending FROM fct_ChangeOrder WHERE ChangeOrderKey='CO1'") is False
    assert one(con, "SELECT COUNT(*) FROM fct_ChangeOrder WHERE IsPending") == 2
    check("fct_ChangeOrder[IsPending] treats Draft as outstanding, not just 'Pending'")

    # FINANCIALS!C5 addends, recoverable as rows instead of lost inside a formula.
    pending = one(con, "SELECT ROUND(SUM(Amount), 2) FROM fct_ChangeOrder WHERE IsPending")
    assert float(pending) == 14708.46, pending
    check("pending CO total is recoverable from rows (14,708.46)")

    rows = rebuild_with(con, """CREATE OR REPLACE VIEW sv_prime_change_orders AS SELECT * FROM (VALUES
        ('P1','CO9','C1', DATE '2025-05-02', 0.0, '9', 'Void')
        ) AS t(project_id, change_order_id, contract_id, created_date, amount, co_number, status)""",
        "21_fct_changeorder.sql", "SELECT IsPending FROM fct_ChangeOrder WHERE ChangeOrderKey='CO9'")
    assert rows == [(False,)], rows
    check("a void change order is not pending")


def test_fct_invoice(con) -> None:
    assert one(con, "SELECT COUNT(*) FROM fct_Invoice") == 3

    # An AR row whose Sage job does not resolve must be KEPT and flagged. Dropping it is
    # how a billing total silently stops reconciling.
    assert one(con, "SELECT COUNT(*) FROM fct_Invoice WHERE HasUnmatchedProject") == 1
    assert one(con, "SELECT ProjectKey FROM fct_Invoice WHERE HasUnmatchedProject") == "UNMATCHED"
    check("fct_Invoice keeps unmatched AR rows, flagged rather than dropped")

    # The regression guard: if the Sage join dies, EVERY invoice reads UNMATCHED and the
    # count above still passes. This asserts the join actually resolves something.
    assert one(con, "SELECT COUNT(*) FROM fct_Invoice WHERE NOT HasUnmatchedProject") == 2
    check("fct_Invoice matches AR rows to projects - the Sage join is live")

    assert one(con, "SELECT COUNT(*) FROM fct_Invoice WHERE IsPaid") == 1
    assert one(con, "SELECT ROUND(SUM(Balance), 2) FROM fct_Invoice WHERE ProjectKey='P1'") == 300000.0
    check("fct_Invoice[IsPaid] and outstanding balance agree")

    # Paid date from receipts. INV1: 200k on 05-20, 300k on 06-10 -> paid 06-10, NOT the
    # first receipt and NOT the due date (06-04). INV2: same-day +300k/-300k nets to nothing.
    rows = q(con, "SELECT InvoiceKey, PaymentsReceived, FirstPaymentDate, LastPaymentDate, PaidDate, "
                  "DaysToPayment FROM fct_Invoice ORDER BY InvoiceKey")
    assert rows == [
        ("INV1", 500000.0, date(2025, 5, 20), date(2025, 6, 10), date(2025, 6, 10), 36),
        ("INV2", 0.0, date(2025, 6, 1), date(2025, 6, 1), None, None),
        ("INV3", None, None, None, None, None),
    ], rows
    check("fct_Invoice[PaidDate] is when receipts first covered the invoice; reversals and partials stay unpaid")

    import seedrunner
    gold_sql = (seedrunner.CHARLEY_DEV / "02-transformation/sql/gold/22_fct_invoice.sql").read_text()

    def rebuild(*receipts):
        con.execute("BEGIN")
        try:
            con.execute("CREATE OR REPLACE VIEW sv_ar_payments AS SELECT * FROM (VALUES "
                        + ", ".join(receipts) + ") AS t(payment_uid, invoice_uid, invoice_id, payment_date, amount)")
            for sql in seedrunner.split_statements(gold_sql):
                con.execute(sql)
            return q(con, "SELECT PaidDate, DaysToPayment FROM fct_Invoice WHERE InvoiceKey = 'INV1'")[0]
        finally:
            con.execute("ROLLBACK")

    # A LATER reversal reopens the invoice; a later re-payment sets PaidDate to that day.
    full = "('A','INV1','901',DATE '2025-05-20',500000.0)"
    back = "('B','INV1','901',DATE '2025-05-25',-500000.0)"
    again = "('C','INV1','901',DATE '2025-06-01',500000.0)"
    assert rebuild(full) == (date(2025, 5, 20), 15)
    assert rebuild(full, back) == (None, None)
    assert rebuild(full, back, again) == (date(2025, 6, 1), 27)
    # Short by more than a cent is not paid; within a cent is.
    assert rebuild("('A','INV1','901',DATE '2025-05-20',499999.98)") == (None, None)
    assert rebuild("('A','INV1','901',DATE '2025-05-20',499999.996)") == (date(2025, 5, 20), 15)
    check("fct_Invoice[PaidDate] reopens on a later reversal and ignores sub-cent rounding")


def test_fct_rfisubmittal(con) -> None:
    # BOTH arms, as of 2026-08-02. RFIs are the half of the workbook's only chart that has
    # never been automated anywhere - no RFI table exists in the existing warehouse - so
    # asserting the union is asserting the new capability, not just the row count.
    assert one(con, "SELECT COUNT(*) FROM fct_RfiSubmittal") == 7
    assert one(con, "SELECT COUNT(*) FROM fct_RfiSubmittal WHERE ItemType='Submittal'") == 5
    assert one(con, "SELECT COUNT(*) FROM fct_RfiSubmittal WHERE ItemType='RFI'") == 2
    check("fct_RfiSubmittal unions submittals AND RFIs, split by ItemType")

    # ItemKey is only unique WITHIN an arm - Procore numbers RFIs and submittals
    # independently, so the model keys on the pair.
    assert one(con, "SELECT COUNT(*) FROM (SELECT DISTINCT ItemType, ItemKey "
                    "FROM fct_RfiSubmittal)") == 7
    check("ItemType + ItemKey is unique across both arms")

    # The RFI arm must behave identically to the submittal arm - same derivations, not a
    # near-copy that drifts.
    assert one(con, "SELECT IsOpen FROM fct_RfiSubmittal WHERE ItemType='RFI' AND ItemKey='R1'") is True
    assert one(con, "SELECT IsOpen FROM fct_RfiSubmittal WHERE ItemType='RFI' AND ItemKey='R2'") is False
    check("the RFI arm derives IsOpen the same way the submittal arm does")

    # Open = awaiting review: no response, not in Procore's Closed category, not a draft.
    def sub(item):
        return con.execute("SELECT IsOpen, IsDraft, IsPastDue, DaysOpen IS NOT NULL, TurnaroundDays "
                           "FROM fct_RfiSubmittal WHERE ItemType='Submittal' AND ItemKey=?",
                           [item]).fetchone()
    assert sub("SB1") == (True, False, True, True, None)
    assert sub("SB2") == (False, False, False, False, 14)
    assert sub("SB4") == (False, True, False, False, None)
    assert sub("SB5") == (False, False, False, False, None)
    check("submittal IsOpen excludes responded, Closed-category and draft items")
    check("DaysOpen is set for open items only; TurnaroundDays for responded items only")
    assert one(con, "SELECT DaysOpen FROM fct_RfiSubmittal WHERE ItemType='RFI' AND ItemKey='R2'") is None
    assert one(con, "SELECT TurnaroundDays FROM fct_RfiSubmittal WHERE ItemType='RFI' AND ItemKey='R2'") == 9
    check("an answered RFI has a turnaround and no today-minus-created DaysOpen")

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

    rows = rebuild_with(con, """CREATE OR REPLACE VIEW sv_observations AS SELECT * FROM (VALUES
        ('P1','T1','1','a','Q','OPEN','High',NULL,'A', DATE '2025-05-01', NULL, NULL),
        ('P1','T2','2','b','Q','OPEN','High','Roofing','A', DATE '2025-05-01', NULL, NULL),
        ('P1','T3','3','c','Q','OPEN','High','Concrete Formwork','A', DATE '2025-05-01', NULL, NULL),
        ('P1','T4','4','d','Q','OPEN','High','HVAC','A', DATE '2025-05-01', NULL, NULL)
        ) AS t(project_id, observation_id, observation_number, title, observation_type,
               status_label, priority, trade, assignee_name, created_date, due_date, closed_date)""",
        "25_fct_qualityitem.sql",
        "SELECT ItemKey, Trade FROM fct_QualityItem WHERE ItemType='Observation' ORDER BY 1")
    assert rows == [("T1", "Unassigned trade"), ("T2", "Unmapped trade: Roofing"),
                    ("T3", "Concrete Formwork"), ("T4", "HVAC")], rows
    check("fct_QualityItem[Trade] says Unassigned or Unmapped instead of (Blank)")


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

    # Held sub retainage is the balance on each commitment's latest APPROVED pay app. SC7's
    # newest pay app is UNDER_REVIEW (and a DRAFT after it): the approved-as-noted balance
    # (6,000) carries forward rather than the contract reading 0 or the unapproved 9,000.
    # SC8 has never been approved, so it holds nothing.
    cols = ("billing_type, project_id, billing_id, invoice_number, period_number, status_label, "
            "vendor_id, counterparty_name, contract_id, contract_name, contract_type, billing_date, "
            "period_start, period_end, payment_date, percent_complete, original_contract_sum, "
            "net_change_by_change_orders, contract_sum_to_date, completed_to_date, previous_certificates, "
            "retainage_amount, retainage_percent, stored_retainage_amount, total_retainage, "
            "earned_less_retainage, current_payment_due, balance_to_finish")
    def pay_app(bid, n, status, contract, end, retainage):
        return (f"('Subcontractor','P1','{bid}','{n}',{n},'{status}','V1','Demar','{contract}','SC',"
                f"'WorkOrderContract',DATE '{end}',DATE '{end}',DATE '{end}',NULL,10.0,100.0,0.0,100.0,"
                f"10.0,0.0,{retainage},5.0,0.0,{retainage},0.0,0.0,90.0)")
    rows = rebuild_with(con, "CREATE OR REPLACE VIEW sv_billing AS SELECT * FROM (VALUES " + ",".join([
            pay_app("S1", 1, "APPROVED", "SC7", "2025-05-31", 4000.0),
            pay_app("S2", 2, "APPROVED_AS_NOTED", "SC7", "2025-06-30", 6000.0),
            pay_app("S3", 3, "UNDER_REVIEW", "SC7", "2025-07-31", 9000.0),
            pay_app("S4", 4, "DRAFT", "SC7", "2025-08-31", 9500.0),
            pay_app("S5", 1, "PENDING_OWNER_APPROVAL", "SC8", "2025-07-31", 700.0),
        ]) + f") AS t({cols})", "27_fct_billing.sql",
        "SELECT BillingKey, IsLatestPeriod, IsLatestApprovedPeriod FROM fct_Billing ORDER BY BillingKey")
    assert rows == [("S1", False, False), ("S2", False, True), ("S3", True, False),
                    ("S4", False, False), ("S5", True, False)], rows
    check("sub retainage carries the latest approved pay app forward past an unapproved one")


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

    types = ["Auto Mobile Liability", "AUTOMOBILE LIABILITY", "Commercial General Liability", "Commercial GL",
             "GL", "Workers' Compensation Insurance", "Workers Comp & Employers Liability", "Umbrella Liab Excess Liab",
             "Excess", "NYS DBL", "Disability", "CERTIFICATE OF LIABILITY INSURANCE", "Contractors Pollution Excess",
             "Equipment Floater"]
    values = ", ".join(f"('X{i}','V1','{v.replace(chr(39), chr(39) * 2)}','p','n','s', DATE '2024-01-01', DATE '2025-01-01',"
                       " 1.0, FALSE, TRUE, TRUE, NULL)" for i, v in enumerate(types))
    cols = [r[0] for r in q(con, "SELECT column_name FROM information_schema.columns "
                                 "WHERE table_name = 'sv_vendor_insurance' ORDER BY ordinal_position")]
    rows = rebuild_with(con, f"CREATE OR REPLACE VIEW sv_vendor_insurance AS SELECT * FROM (VALUES {values}) "
                             f"AS t({', '.join(cols)})", "32_fct_vendorinsurance.sql",
                        "SELECT InsuranceType, InsuranceCategory FROM fct_VendorInsurance")
    assert dict(rows) == {
        "Auto Mobile Liability": "Auto", "AUTOMOBILE LIABILITY": "Auto",
        "Commercial General Liability": "General Liability", "Commercial GL": "General Liability",
        "GL": "General Liability", "Workers' Compensation Insurance": "Workers Comp",
        "Workers Comp & Employers Liability": "Workers Comp", "Umbrella Liab Excess Liab": "Umbrella/Excess",
        "Excess": "Umbrella/Excess", "NYS DBL": "Disability", "Disability": "Disability",
        "CERTIFICATE OF LIABILITY INSURANCE": "Other", "Contractors Pollution Excess": "Other",
        "Equipment Floater": "Other"}, rows
    check("fct_VendorInsurance[InsuranceCategory] folds free-text types into six categories")

GAP_CATEGORIES = {
    "Rejected source row", "Rejected manual entry", "Rejected quality entry",
    "Unmatched AR invoice", "Unmapped trade", "Project missing from Sage",
    "Project missing from Outbuild", "Vendor without certificate", "Expired certificate",
    "Empty manual register", "Sage job without Procore project", "AP invoice with no Sage job",
    "Cost reconciliation variance", "ERP-only vendor cost",
    "Project with no Procore budget or zero Spent To Date while AP/requisitions exist",
}


def test_dq_datagap(con) -> None:
    """One register of every known gap - every category must be reachable from fixtures."""
    from seedrunner import CHARLEY_DEV, split_statements
    gap_sql = split_statements((CHARLEY_DEV / "02-transformation" / "sql" / "gold"
                                / "45_dq_datagap.sql").read_text(encoding="utf-8"))
    con.execute("BEGIN")
    try:
        # The two categories the shared fixtures are healthy on: a project vendor with no
        # certificate, and a manual register nobody has typed into.
        con.execute("INSERT INTO bridge_ProjectVendor SELECT * REPLACE ('V9' AS VendorKey, "
                    "'Uninsured Co' AS VendorName) FROM bridge_ProjectVendor LIMIT 1")
        con.execute("DELETE FROM man_QcItp")
        # P2 has requisitions in Procore and no budget at all: the 25-012 pattern.
        con.execute("CREATE TEMP TABLE cm_gap AS SELECT * FROM sv_commitments")
        con.execute("CREATE OR REPLACE VIEW sv_commitments AS SELECT * FROM cm_gap UNION ALL "
                    "SELECT * REPLACE ('P2' AS project_id, 'SC9' AS commitment_id) FROM cm_gap WHERE commitment_id = 'SC1'")
        # Fact rows on a project gold has never heard of: ProjectKey must come out NULL.
        con.execute("INSERT INTO bridge_ProjectVendor SELECT * REPLACE ('V8' AS VendorKey, "
                    "'P404' AS ProjectKey) FROM bridge_ProjectVendor LIMIT 1")
        con.execute("INSERT INTO fct_QcNcr SELECT * REPLACE ('NCR404' AS NcrKey, 'P404' AS ProjectKey, "
                    "TRUE AS HasUnmappedTrade) FROM fct_QcNcr LIMIT 1")
        con.execute("INSERT INTO fct_QcPunch SELECT * REPLACE ('PUN404' AS PunchKey, 'P404' AS ProjectKey, "
                    "TRUE AS HasUnmappedTrade) FROM fct_QcPunch LIMIT 1")
        # Live Procore payloads carry user emails; none may reach the register.
        con.execute("""CREATE OR REPLACE VIEW sv_dq_rejects AS SELECT * FROM (VALUES
            ('cd_silver_submittals', 'missing id', '{"title":"No id","created_by":{"email":"a.person@example.com"}}', 'batch-1'),
            ('cd_silver_qc_ncr', 'missing project', '{"id":"OBX","assignee":{"login":"b.person@example.com"}}', 'batch-1'),
            ('cd_silver_sage_ar_invoice', 'missing job', '{"_idnum":"S77"}', 'batch-2')
        ) AS t(target_table, reason, payload, _batch_id)""")
        for sql in gap_sql:
            con.execute(sql)
        seen = {r[0] for r in q(con, "SELECT DISTINCT GapCategory FROM dq_DataGap")}
        assert seen == GAP_CATEGORIES, (seen ^ GAP_CATEGORIES)
        check(f"dq_DataGap surfaces all {len(GAP_CATEGORIES)} gap categories from fixtures")

        assert q(con, "SELECT EntityKey, ProjectKey FROM dq_DataGap WHERE EntityKey IN "
                      "('V8', 'NCR404', 'PUN404') ORDER BY EntityKey") ==             [("NCR404", None), ("PUN404", None), ("V8", None)]
        check("unmapped-trade and uninsured-vendor gaps on an unknown project get a NULL ProjectKey")

        details = [r[0] or "" for r in q(con, "SELECT Detail FROM dq_DataGap")]
        editors = [r[0] for r in q(con, "SELECT last_modified_by FROM sv_dq_rejects_manual "
                                         "UNION SELECT last_modified_by FROM sv_dq_rejects_qc")]
        assert not any("@" in d for d in details), details
        assert not any(e in d for d in details for e in editors), details
        assert q(con, "SELECT Detail FROM dq_DataGap WHERE EntityKey = 'S77'") ==             [("record S77; table cd_silver_sage_ar_invoice; reason missing job; batch batch-2",)]
        check("dq_DataGap[Detail] carries record ids, never payload emails or editor names")

        assert q(con, "SELECT EntityKey, ProjectKey FROM dq_DataGap "
                      "WHERE GapCategory = 'Vendor without certificate' AND EntityKey = 'V9'") == [("V9", "P1")]
        assert q(con, "SELECT EntityType FROM dq_DataGap "
                      "WHERE GapCategory = 'Empty manual register'") == [("man_QcItp",)]
        check("an uninsured project vendor and an empty register each produce exactly one gap")
    finally:
        con.execute("ROLLBACK")

    # Money only where the gap carries it: the orphan AR invoice's 1,000. The job-level and
    # no-job AP rows carry their figures in text, never in Amount - Data Gap Amount is
    # SUM(Amount), and valuing S999's AR again would count the same invoice twice.
    assert q(con, "SELECT EntityKey, Amount FROM dq_DataGap WHERE Amount IS NOT NULL") == [("INV3", 1000.0)]
    assert one(con, "SELECT SUM(Amount) FROM dq_DataGap") == one(
        con, "SELECT SUM(Amount) FROM fct_Invoice WHERE HasUnmatchedProject")
    check("Data Gap Amount equals unmatched AR only - no arm double-counts it")
    assert q(con, "SELECT EntityType, EntityKey, Reason FROM dq_DataGap "
                  "WHERE GapCategory = 'Sage job without Procore project' ORDER BY 1") == [
        ("sv_ap_invoices", "S999", "Sage job S999 has 1 AP invoice(s) totalling 2500.00 and no Procore project in the crosswalk"),
        ("sv_ar_invoices", "S999", "Sage job S999 has 1 AR invoice(s) totalling 1000.00 and no Procore project in the crosswalk")]
    assert q(con, "SELECT EntityKey, Detail FROM dq_DataGap WHERE GapCategory = 'AP invoice with no Sage job'") == [
        ("AP3", "invoice INV-79; vendor SV1; total 700.00")]
    check("unmapped Sage jobs (per direction) and job-less AP are listed with figures in text, not Amount")

    # Candidates are proposals: exact normalised name only, unmapped on both sides, and
    # nothing in the crosswalk reads them back.
    assert q(con, "SELECT ProcoreProjectId, SageJobNumber, MatchRule FROM dq_CrosswalkCandidate") == [
        ("P2", "S200", "EXACT_NAME_SHORT_NAME")]
    views = (CHARLEY_DEV / "02-transformation/sql/silver/01_source_views_cd.sql").read_text(encoding="utf-8")
    assert "dq_CrosswalkCandidate" not in views.split("CREATE OR REPLACE TEMPORARY VIEW sv_project_crosswalk")[1].split(";")[0]
    check("dq_CrosswalkCandidate proposes the exact-name match and is never auto-applied")

    # Every ProjectKey resolves, so the model relationship never shows a blank member. The
    # manual reject for P9 keeps its raw id in Detail instead.
    assert one(con, "SELECT COUNT(*) FROM dq_DataGap g LEFT JOIN dim_Project p "
                    "ON g.ProjectKey = p.ProjectKey WHERE g.ProjectKey IS NOT NULL "
                    "AND p.ProjectKey IS NULL") == 0
    assert one(con, "SELECT Detail FROM dq_DataGap WHERE GapCategory = 'Rejected manual entry'"
               ).startswith("project P9")
    check("dq_DataGap[ProjectKey] only holds keys dim_Project has; unknown ids stay readable in Detail")

    # Each reject ledger row appears once - the register is a view of the ledgers, not a sample.
    assert one(con, "SELECT COUNT(*) FROM dq_DataGap WHERE GapCategory LIKE 'Rejected%'") == \
        sum(one(con, f"SELECT COUNT(*) FROM {v}")
            for v in ("sv_dq_rejects", "sv_dq_rejects_manual", "sv_dq_rejects_qc"))
    assert one(con, "SELECT RunBatchId FROM dq_DataGap WHERE EntityKey = 'OBX'") == "batch-1"
    check("every reject ledger row reaches dq_DataGap exactly once, with its batch id")


def test_fct_apinvoice(con) -> None:
    """Sage AP at line grain: the ERP side of the Procore cost reconciliation."""
    rows = {r[0]: r[1:] for r in q(con, "SELECT ApLineKey, ProjectKey, VendorKey, IsJobCost, IsErpOnlyVendor, "
                                         "LineTotal FROM fct_ApInvoice")}
    assert rows == {
        "L1": ("P1", "V1", True, False, 7000.0),          # mapped job, vendor Procore carries on P1
        "L2": ("P1", "V1", False, False, 1000.0),         # overhead GL 60010: not job cost
        "L3": (None, "V1", True, False, 2500.0),          # unmapped job: no ProjectKey, never ERP-only
        "L4": (None, "V1", False, False, 700.0),          # no job at all
        "L5": ("P1", "UNASSIGNED", True, True, 6000.0),   # Sage vendor unknown to Procore
    }, rows
    check("fct_ApInvoice classifies mapped/unmapped jobs, GL outside 50000-50999 and ERP-only vendors")
    assert one(con, "SELECT SUM(LineTotal) FROM fct_ApInvoice") == one(con, "SELECT SUM(line_total) FROM sv_ap_lines")
    assert q(con, "SELECT DISTINCT InvoiceKey, InvoiceTotal, MonthStart FROM fct_ApInvoice WHERE ApLineKey IN ('L1','L2')") == [
        ("U1", 8000.0, date(2025, 5, 1))]
    check("fct_ApInvoice keeps every AP line once and carries its header on each line")

    # dq_DataGap thresholds, at the boundary. P1 AP job cost is 13,000 (L1 + L5).
    from seedrunner import CHARLEY_DEV, split_statements
    gap_sql = split_statements((CHARLEY_DEV / "02-transformation/sql/gold/45_dq_datagap.sql").read_text(encoding="utf-8"))

    def gaps(category, *mutations):
        con.execute("BEGIN")
        try:
            for m in mutations:
                con.execute(m)
            for sql in gap_sql:
                con.execute(sql)
            return q(con, f"SELECT EntityKey FROM dq_DataGap WHERE GapCategory = '{category}' ORDER BY 1")
        finally:
            con.execute("ROLLBACK")

    variance = "Cost reconciliation variance"
    spent = lambda v: f"UPDATE fct_BudgetLine SET SpentToDate = CASE BudgetLineID WHEN 'B1' THEN {v} ELSE 0 END"
    assert gaps(variance) == [("P1",)]                      # 13,000 vs 500,000
    assert gaps(variance, spent(38000.0)) == []              # |diff| exactly 25,000 = floor
    assert gaps(variance, spent(38000.1)) == [("P1",)]
    big = "UPDATE fct_ApInvoice SET LineTotal = 300000.0 WHERE ApLineKey = 'L1'"   # AP 306,000
    assert gaps(variance, big, spent(275400.0)) == []        # exactly 10% of the larger side
    assert gaps(variance, big, spent(275399.9)) == [("P1",)]
    check("cost reconciliation variance fires above max($25k, 10%) and not at exactly either boundary")

    nobudget = "Project with no Procore budget or zero Spent To Date while AP/requisitions exist"
    assert gaps(nobudget) == []
    assert gaps(nobudget, spent(0)) == [("P1",)]             # the variance arm then stays quiet
    assert gaps(variance, spent(0)) == []
    assert gaps(nobudget, "DELETE FROM fct_BudgetLine") == [("P1",)]
    check("no-budget / zero Spent To Date fires on AP or requisitions, and never double-lists as variance")

    erp = "ERP-only vendor cost"
    assert gaps(erp) == [("P1:SV2",)]
    assert gaps(erp, "UPDATE fct_ApInvoice SET LineTotal = 5000.0 WHERE ApLineKey = 'L5'") == []
    assert gaps(erp, "UPDATE fct_ApInvoice SET LineTotal = 5000.01 WHERE ApLineKey = 'L5'") == [("P1:SV2",)]
    check("ERP-only vendor cost lists a project-vendor above $5,000, not at exactly $5,000")
    assert one(con, "SELECT COUNT(*) FROM dq_DataGap WHERE EntityType IN ('fct_ApInvoice', 'fct_BudgetLine') "
                    "AND Amount IS NOT NULL") == 0
    check("cost reconciliation gaps carry no Amount - Data Gap Amount stays unmatched AR")


def main() -> int:
    con = build()
    for fn in (
        test_dim_project, test_dim_vendor, test_dim_costcode,
        test_fct_budgetline, test_fct_changeorder, test_fct_invoice,
        test_fct_rfisubmittal, test_fct_milestone, test_fct_financialperiod,
        test_referential_integrity, test_crosswalks, test_fct_qualityitem, test_fct_safetymonthly, test_fct_billing, test_fct_directcost, test_bridge_projectvendor, test_bridge_vendorcostcode, test_fct_vendorinsurance, test_fct_apinvoice, test_dq_datagap):
        fn(con)
    for label in CHECKS:
        print(f"  ok  {label}")
    print(f"\ntest_gold: {len(CHECKS)} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
