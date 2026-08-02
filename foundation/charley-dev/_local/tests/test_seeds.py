"""Assertions over the gold seed tables.

Every check here corresponds to something the Excel workbook got wrong, or something the
DAX will silently depend on. A seed is the cheapest thing in the pipeline to get wrong and
the most expensive to notice - a mistyped weight shifts every project's health score and
nothing anywhere errors.

No framework. Run it:
    python test_seeds.py
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


def q(con, sql: str):
    return con.execute(sql).fetchall()


def one(con, sql: str):
    return con.execute(sql).fetchone()[0]


# --------------------------------------------------------------------------
# dim_Date - replaces the AU4 INDEX/MATCH mechanic (defects #4, #5)
# --------------------------------------------------------------------------


def test_dim_date(con) -> None:
    # 2015-01-01 .. 2035-12-31 inclusive. Widened from 2023-2030 after the first run
    # against real data put change orders and submittals outside the calendar.
    assert one(con, "SELECT COUNT(*) FROM dim_Date") == 7670
    assert one(con, "SELECT MIN(Date) FROM dim_Date") == date(2015, 1, 1)
    assert one(con, "SELECT MAX(Date) FROM dim_Date") == date(2035, 12, 31)
    check("dim_Date spans 2015-01-01..2035-12-31 (7670 days)")

    # A date key must be unique or every measure over it double-counts.
    assert one(con, "SELECT COUNT(DISTINCT Date) FROM dim_Date") == 7670
    check("dim_Date[Date] is unique")

    # Contiguous: no gaps. A missing day is exactly the silent #N/A the Excel suffers.
    gaps = one(
        con,
        "SELECT COUNT(*) FROM ("
        "  SELECT Date, LAG(Date) OVER (ORDER BY Date) AS prev FROM dim_Date"
        ") WHERE prev IS NOT NULL AND Date <> prev + INTERVAL 1 DAY",
    )
    assert gaps == 0, f"{gaps} gaps in the calendar"
    check("dim_Date is contiguous - no missing days")

    # MonthStart must be the 1st, and every monthly fact joins on it.
    assert one(con, "SELECT COUNT(*) FROM dim_Date WHERE day(MonthStart) <> 1") == 0
    assert one(
        con, "SELECT COUNT(*) FROM dim_Date WHERE month(MonthStart) <> Month OR year(MonthStart) <> Year"
    ) == 0
    check("dim_Date[MonthStart] is the 1st of the row's own month")

    # 21 years x 12 months of distinct month starts, one month-end flag each.
    assert one(con, "SELECT COUNT(DISTINCT MonthStart) FROM dim_Date") == 252
    assert one(con, "SELECT COUNT(*) FROM dim_Date WHERE IsMonthEnd") == 252
    check("dim_Date has 252 months, each with exactly one IsMonthEnd")

    # Leap day present, and Feb 2024 flagged on the 29th not the 28th.
    assert one(con, "SELECT COUNT(*) FROM dim_Date WHERE Date = DATE '2024-02-29'") == 1
    assert one(
        con, "SELECT COUNT(*) FROM dim_Date WHERE Date = DATE '2024-02-29' AND IsMonthEnd"
    ) == 1
    check("dim_Date handles the 2024 leap day")

    # MonthOffset 0 = current month. This is what makes relative filtering possible.
    today = date.today()
    current = one(con, f"SELECT COUNT(*) FROM dim_Date WHERE MonthOffset = 0 AND Year = {today.year} AND Month = {today.month}")
    assert current > 0, "MonthOffset=0 does not land on the current month"
    assert one(con, "SELECT COUNT(DISTINCT MonthStart) FROM dim_Date WHERE MonthOffset = 0") == 1
    check("dim_Date[MonthOffset] = 0 is exactly the current month")

    # MonthYearSort must order chronologically - the reason it exists is that sorting
    # 'Apr 2026' alphabetically puts April first.
    assert one(
        con,
        "SELECT COUNT(*) FROM ("
        "  SELECT MonthYearSort, MonthStart,"
        "         LAG(MonthYearSort) OVER (ORDER BY MonthStart) AS prev"
        "  FROM (SELECT DISTINCT MonthYearSort, MonthStart FROM dim_Date)"
        ") WHERE prev IS NOT NULL AND MonthYearSort <= prev",
    ) == 0
    check("dim_Date[MonthYearSort] orders chronologically")


# --------------------------------------------------------------------------
# dim_Trade - defect #9 (trailing whitespace) and the duplicate Metals
# --------------------------------------------------------------------------


def test_dim_trade(con) -> None:
    # 29 cells in DROPDOWN!M4:M32, but Metals appears twice -> 28 distinct + Unassigned.
    assert one(con, "SELECT COUNT(*) FROM dim_Trade") == 29
    assert one(con, "SELECT COUNT(*) FROM dim_Trade WHERE TradeKey = 0") == 1
    check("dim_Trade has 28 real trades + Unassigned")

    dupes = q(con, "SELECT TradeName FROM dim_Trade GROUP BY TradeName HAVING COUNT(*) > 1")
    assert not dupes, f"duplicate trades: {dupes}"
    check("dim_Trade has no duplicate names (Metals appeared twice in the workbook)")

    # The whole point of defect #9: "Metals  " never equals "Metals" in a join.
    untrimmed = q(con, "SELECT TradeName FROM dim_Trade WHERE TradeName <> TRIM(TradeName)")
    assert not untrimmed, f"untrimmed trade names: {untrimmed}"
    check("dim_Trade names carry no leading/trailing whitespace")

    assert one(con, "SELECT COUNT(DISTINCT TradeKey) FROM dim_Trade") == 29
    check("dim_Trade[TradeKey] is unique")


# --------------------------------------------------------------------------
# dim_Status
# --------------------------------------------------------------------------


def test_dim_status(con) -> None:
    assert one(con, "SELECT COUNT(*) FROM dim_Status") == 32
    check("dim_Status seeds all 32 rows from dropdowns-and-status.md")

    assert one(con, "SELECT COUNT(DISTINCT StatusKey) FROM dim_Status") == 32
    check("dim_Status[StatusKey] is unique")

    # Code is what facts join on; it must be unique within its domain.
    dupes = q(con, "SELECT Domain, Code FROM dim_Status GROUP BY Domain, Code HAVING COUNT(*) > 1")
    assert not dupes, f"duplicate (Domain, Code): {dupes}"
    check("dim_Status (Domain, Code) is unique - safe to join on")

    # RAG drives colour everywhere; an unexpected value silently renders as no colour.
    bad = q(con, "SELECT DISTINCT RAG FROM dim_Status WHERE RAG NOT IN ('Red','Amber','Green','Neutral')")
    assert not bad, f"unexpected RAG values: {bad}"
    check("dim_Status[RAG] is one of Red/Amber/Green/Neutral")

    # Hex colours must be real hex or conditional formatting breaks at render time.
    bad_hex = q(
        con,
        "SELECT DISTINCT HexColor FROM dim_Status "
        "WHERE HexColor IS NOT NULL AND NOT regexp_matches(HexColor, '^#[0-9A-Fa-f]{6}$')",
    )
    assert not bad_hex, f"malformed hex colours: {bad_hex}"
    check("dim_Status[HexColor] values are well-formed hex")


# --------------------------------------------------------------------------
# dim_Owner / dim_ActivityCategory
# --------------------------------------------------------------------------


def test_dim_owner(con) -> None:
    assert one(con, "SELECT COUNT(*) FROM dim_Owner") == 10  # 9 roles + Unassigned
    assert one(con, "SELECT COUNT(DISTINCT RoleName) FROM dim_Owner") == 10
    check("dim_Owner has the 9 DROPDOWN!C roles + Unassigned, all distinct")

    # Seniority order must be a strict sequence, or "sort by SortOrder" is ambiguous.
    assert one(con, "SELECT COUNT(DISTINCT SortOrder) FROM dim_Owner WHERE OwnerKey <> 0") == 9
    assert one(con, "SELECT RoleName FROM dim_Owner WHERE OwnerKey <> 0 ORDER BY SortOrder LIMIT 1") == "Principal"
    check("dim_Owner[SortOrder] is a strict seniority sequence")


def test_dim_activity_category(con) -> None:
    assert one(con, "SELECT COUNT(*) FROM dim_ActivityCategory") == 28  # 16 + 11 + Unassigned
    assert one(con, "SELECT COUNT(*) FROM dim_ActivityCategory WHERE Domain = 'Safety'") == 16
    assert one(con, "SELECT COUNT(*) FROM dim_ActivityCategory WHERE Domain = 'Quality'") == 11
    check("dim_ActivityCategory splits 16 safety + 11 quality + Unassigned")

    dupes = q(con, "SELECT FullLabel FROM dim_ActivityCategory GROUP BY FullLabel HAVING COUNT(*) > 1")
    assert not dupes, f"duplicate categories: {dupes}"
    check("dim_ActivityCategory[FullLabel] is unique")

    # The split is the whole point: a flat picklist becomes a filterable hierarchy.
    assert one(con, "SELECT COUNT(*) FROM dim_ActivityCategory WHERE CategoryType = 'Toolbox Talk'") == 2
    assert one(con, "SELECT COUNT(*) FROM dim_ActivityCategory WHERE CategoryType = 'Notable Visitor'") == 5
    check("dim_ActivityCategory Type/Qualifier split produces a real hierarchy")

    # FullLabel must reconstruct from its parts, or the split silently lost information.
    mismatched = q(
        con,
        "SELECT FullLabel FROM dim_ActivityCategory "
        "WHERE CategoryQualifier IS NOT NULL "
        "AND FullLabel <> CategoryType || ' – ' || CategoryQualifier",
    )
    assert not mismatched, f"FullLabel does not reconstruct from its parts: {mismatched}"
    check("dim_ActivityCategory[FullLabel] round-trips from Type + Qualifier")


# --------------------------------------------------------------------------
# The scorecard - the highest-leverage thing in the build
# --------------------------------------------------------------------------


def test_scorecard_weights(con) -> None:
    assert one(con, "SELECT COUNT(*) FROM dim_ScorecardWeight") == 9
    check("dim_ScorecardWeight has all 9 categories")

    # The workbook's weights sum to exactly 1.00. If ours do not, every score is wrong
    # by a factor nobody would spot.
    # CAST to DOUBLE throughout: DuckDB infers DECIMAL from the literals, and
    # Decimal('0.15') != 0.15 in Python, which would fail for the wrong reason.
    total = one(con, "SELECT ROUND(CAST(SUM(Weight) AS DOUBLE), 6) FROM dim_ScorecardWeight WHERE EffectiveTo IS NULL")
    assert total == 1.0, f"weights sum to {total}, not 1.00"
    check("dim_ScorecardWeight sums to exactly 1.00")

    # Spot-check the two heaviest against SCORECARD CALC!F4:F30.
    assert one(con, "SELECT CAST(Weight AS DOUBLE) FROM dim_ScorecardWeight WHERE CategoryName = 'Schedule Performance'") == 0.15
    assert one(con, "SELECT CAST(Weight AS DOUBLE) FROM dim_ScorecardWeight WHERE CategoryName = 'Safety Incidents'") == 0.14
    check("dim_ScorecardWeight matches the workbook's stated weights")


def test_scorecard_bands(con) -> None:
    # 9 categories x 3 score levels.
    assert one(con, "SELECT COUNT(*) FROM dim_ScorecardBand") == 27
    check("dim_ScorecardBand has 3 bands for each of 9 categories")

    # Scores are 3/2/0 - the bottom band is ZERO, not one, so a failing category
    # contributes nothing rather than partial credit.
    bad = q(con, "SELECT DISTINCT Score FROM dim_ScorecardBand WHERE Score NOT IN (0, 2, 3)")
    assert not bad, f"unexpected score values: {bad}"
    assert one(con, "SELECT COUNT(*) FROM (SELECT CategoryKey FROM dim_ScorecardBand GROUP BY CategoryKey HAVING COUNT(DISTINCT Score) <> 3)") == 0
    check("dim_ScorecardBand scores are exactly {3, 2, 0} per category")

    # Every band category must exist in the weight table, or it scores into a void.
    orphans = q(
        con,
        "SELECT DISTINCT b.CategoryKey FROM dim_ScorecardBand b "
        "LEFT JOIN dim_ScorecardWeight w ON b.CategoryKey = w.CategoryKey "
        "WHERE w.CategoryKey IS NULL",
    )
    assert not orphans, f"bands with no matching weight: {orphans}"
    check("every dim_ScorecardBand category resolves to a weight")

    # --- defect #1a: Schedule Performance must use FRACTIONS, not integers ---
    # The workbook compared a 0.4 fraction against 5/9/10, so it always scored 3/3.
    bounds = q(
        con,
        "SELECT Score, MinValue, MaxValue FROM dim_ScorecardBand WHERE CategoryKey = 6 ORDER BY Score",
    )
    maxima = [b[2] for b in bounds if b[2] is not None]
    assert max(maxima) <= 1.0, f"Schedule Performance bands look like integers, not fractions: {bounds}"
    assert one(con, "SELECT MaxValue FROM dim_ScorecardBand WHERE CategoryKey = 6 AND Score = 3") == 0.05
    check("defect #1a fixed: Schedule Performance bands are fractions (0.05 / 0.10)")

    # --- defect #1b: Completion Variance - finishing ON baseline is the BEST outcome ---
    # The workbook's "0 days" string made it score 0. Zero must now fall in the 3-point band.
    band_for_zero = q(
        con,
        "SELECT Score FROM dim_ScorecardBand WHERE CategoryKey = 7 "
        "AND (MinValue IS NULL OR 0 >= MinValue) AND (MaxValue IS NULL OR 0 < MaxValue)",
    )
    assert [r[0] for r in band_for_zero] == [3], f"0 days variance should score 3, got {band_for_zero}"
    check("defect #1b fixed: 0 days completion variance scores 3, not 0")

    # --- the tiling property: bands must cover the number line with no gap, no overlap ---
    # This is what makes a score deterministic. The workbook's own bands have holes
    # (Observations skips 5, Daily Reports skips 2); ours must not.
    numeric_categories = [
        r[0] for r in q(con, "SELECT DISTINCT CategoryKey FROM dim_ScorecardBand WHERE MatchValue IS NULL")
    ]
    for cat in numeric_categories:
        rows = q(
            con,
            "SELECT MinValue, MaxValue FROM dim_ScorecardBand "
            f"WHERE CategoryKey = {cat} ORDER BY COALESCE(MinValue, -1e18)",
        )
        assert rows[0][0] is None or rows[0][0] <= 0, f"category {cat} lower bound leaves a hole: {rows}"
        assert rows[-1][1] is None, f"category {cat} is not open-ended at the top: {rows}"
        for (_, upper), (lower, _) in zip(rows, rows[1:]):
            assert upper == lower, f"category {cat} bands do not tile: {upper} -> {lower} in {rows}"
    check(f"all {len(numeric_categories)} numeric band sets tile with no gap or overlap")

    # Text-valued categories match the workbook's dropdown strings exactly - the scorecard
    # resolves them by string equality, so a single character change zeroes the category.
    profit = {r[0] for r in q(con, "SELECT MatchValue FROM dim_ScorecardBand WHERE CategoryKey = 2")}
    assert profit == {"Within Range", "Out of Range, but has a plan", "Margin fade but no plan"}, profit
    check("Profitability bands match DROPDOWN!Q verbatim")


def main() -> int:
    con = build()
    for fn in (
        test_dim_date, test_dim_trade, test_dim_status, test_dim_owner,
        test_dim_activity_category, test_scorecard_weights, test_scorecard_bands,
    ):
        fn(con)
    for label in CHECKS:
        print(f"  ok  {label}")
    print(f"\ntest_seeds: {len(CHECKS)} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
