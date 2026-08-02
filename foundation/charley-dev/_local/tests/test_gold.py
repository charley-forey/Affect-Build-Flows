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
    assert one(con, "SELECT COUNT(*) FROM fct_ChangeOrder") == 3
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
    row = q(
        con,
        "SELECT ROUND(OriginalContract,2), ROUND(CurrentContract,2), "
        "ROUND(PendingChangeOrders,2), ROUND(PercentBoughtOut,4) "
        "FROM fct_FinancialPeriod WHERE ProjectKey='P1'",
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

def main() -> int:
    con = build()
    for fn in (
        test_dim_project, test_dim_vendor, test_dim_costcode,
        test_fct_budgetline, test_fct_changeorder, test_fct_invoice,
        test_fct_rfisubmittal, test_fct_milestone, test_fct_financialperiod,
        test_referential_integrity, test_crosswalks, test_fct_qualityitem):
        fn(con)
    for label in CHECKS:
        print(f"  ok  {label}")
    print(f"\ntest_gold: {len(CHECKS)} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
