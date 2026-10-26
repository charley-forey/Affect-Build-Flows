"""Assertions over the Weekly Dashboard gold: 46_dashboard_facts.sql and 47_dashboard_score.sql.

The scoring scenario replaces every table 47 reads with one synthetic week whose answer is
worked out by hand from Scorecard.xlsx (column H), so a changed band, weight or rule fails
here before it reaches the report. The position and meeting checks run on the shared fixtures.

Run:  python test_dashboard_gold.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import seedrunner  # noqa: E402
from seedrunner import build  # noqa: E402

CHECKS: list[str] = []
GOLD = seedrunner.CHARLEY_DEV / "02-transformation" / "sql" / "gold"


def check(label: str) -> None:
    CHECKS.append(label)


def q(con, sql: str):
    return con.execute(sql).fetchall()


def close(a, b, tol=1e-9) -> bool:
    return a is not None and b is not None and abs(float(a) - float(b)) <= tol


# One synthetic week, ending 2026-10-25. X is in Construction with every measure live; Y has
# no phase and only financials, so it must come out unscored rather than failing.
SCENARIO = [
    """CREATE OR REPLACE TABLE dim_ReportWeek AS SELECT * FROM (VALUES
        (0, DATE '2026-10-19', DATE '2026-10-25', DATE '2026-10-25'),
        (2, DATE '2026-10-05', DATE '2026-10-11', DATE '2026-10-25')
    ) AS t(WeeksAgo, WeekStart, WeekEnd, AsOfDate)""",
    # cash 95 / 100 = 0.95; margin (1000 - 880) / 1000 = 12.0% vs 12.5%; AR age 4500 / 100 = 45 days.
    """CREATE OR REPLACE TABLE fct_ProjectPosition AS SELECT * FROM (VALUES
        ('X', 95.0, 100.0, 1000.0, 880.0, 100.0, 4500.0, 2, 'Construction'),
        ('Y', 95.0, 100.0, 1000.0, 880.0, 100.0, 4500.0, 2, NULL)
    ) AS t(ProjectKey, CashCollected, CashPaidOut, ProjectedRevenue, ProjectedCost,
           ArOwedBalance, ArOwedBalanceDays, InvoiceCount, Phase)""",
    # OAC compliant in 3 of the 4 weeks (the 09-30 one was not compliant): misses 1.
    # Trade partner compliant in all 4: misses 0.
    """CREATE OR REPLACE TABLE fct_Meeting AS SELECT * FROM (VALUES
        ('X', 'OAC', DATE '2026-10-20', TRUE), ('X', 'OAC', DATE '2026-10-14', TRUE),
        ('X', 'OAC', DATE '2026-10-07', TRUE), ('X', 'OAC', DATE '2026-09-30', FALSE),
        ('X', 'Trade Partner', DATE '2026-10-21', TRUE), ('X', 'Trade Partner', DATE '2026-10-15', TRUE),
        ('X', 'Trade Partner', DATE '2026-10-08', TRUE), ('X', 'Trade Partner', DATE '2026-10-01', TRUE)
    ) AS t(ProjectKey, MeetingType, MeetingDate, IsCompliant)""",
    # Safety: 3 performed in the week (one not performed, one the week before). Quality: 7.
    """CREATE OR REPLACE TABLE fct_Inspection AS
        SELECT 'X' AS ProjectKey, 'Safety' AS Category, DATE '2026-10-20' + CAST(i AS INT) AS InspectionDate, TRUE AS IsPerformed
        FROM range(3) r(i)
        UNION ALL SELECT 'X', 'Safety', DATE '2026-10-23', FALSE
        UNION ALL SELECT 'X', 'Safety', DATE '2026-10-10', TRUE
        UNION ALL SELECT 'X', 'Quality', DATE '2026-10-19' + CAST(i % 7 AS INT), TRUE FROM range(7) r(i)""",
    # Schedule last edited 40 days before the as-of date; the look-ahead 3 days before.
    """CREATE OR REPLACE TABLE fct_ScheduleActivity AS
        SELECT 'X' AS ProjectKey, TIMESTAMP '2026-09-15 10:00:00' AS UpdatedAt""",
    """CREATE OR REPLACE TABLE fct_LookaheadTask AS
        SELECT 'X' AS ProjectKey, TIMESTAMP '2026-10-22 09:00:00' AS UpdatedAt, TIMESTAMP '2026-10-01 09:00:00' AS CreatedAt""",
    # Baseline 2026-01-01 to 2026-12-31 (364 days); forecast 31 days late.
    """CREATE OR REPLACE TABLE fct_Milestone AS
        SELECT 'X' AS ProjectKey, DATE '2026-01-01' AS BaselineStart, DATE '2026-12-31' AS BaselineFinish,
               DATE '2027-01-31' AS CurrentFinish""",
    """CREATE OR REPLACE TABLE man_Milestones AS
        SELECT 'X' AS ProjectKey, CAST(NULL AS DATE) AS BaselineFinish WHERE FALSE""",
    # 4 submittals all past due; 11 RFIs past due + 1 open 10 days with no due date = 12 out,
    # and 1 open 3 days with no due date, which is not yet outstanding.
    """CREATE OR REPLACE TABLE fct_RfiSubmittal AS
        SELECT 'X' AS ProjectKey, 'Submittal' AS ItemType, TRUE AS IsOpen, TRUE AS IsPastDue,
               DATE '2026-10-01' AS DueDate, 30 AS DaysOpen FROM range(4)
        UNION ALL SELECT 'X', 'RFI', TRUE, TRUE, DATE '2026-10-01', 30 FROM range(11)
        UNION ALL SELECT 'X', 'RFI', TRUE, FALSE, NULL, 10
        UNION ALL SELECT 'X', 'RFI', TRUE, FALSE, NULL, 3""",
]

# Expected scores, by hand from Scorecard.xlsx column H and dashboard_band.csv.
EXPECTED = {
    101: 0.75,               # 90-100%: cash position % less 20 points -> 95% - 20
    102: 0.75,               # up to 2.5 points below the 12.5% target (proposed band)
    103: 0.75,               # 30-60 days
    201: 0.75,               # misses 1
    202: 1.00,               # misses 0
    203: 1.00,               # look-ahead worked within 7 days
    204: 0.00,               # schedule not updated in the last month
    205: 1 - 31 / 364,       # 100% less the variance %
    206: 0.60,               # 3-5 overdue
    207: 0.00,               # >10 outstanding
    301: 0.80 - 2 * 0.16,    # 5 = 80%, 16% less for each one short
    401: 0.80 + 2 * 0.04,    # 4% more for each one over
}


def test_scoring(con) -> None:
    con.execute("BEGIN")
    try:
        for sql in SCENARIO:
            con.execute(sql)
        for sql in seedrunner.split_statements((GOLD / "47_dashboard_score.sql").read_text(encoding="utf-8")):
            con.execute(sql)

        got = dict(q(con, "SELECT MetricKey, Score FROM fct_MetricScore WHERE ProjectKey = 'X' AND WeeksAgo = 0"))
        wrong = {k: (got.get(k), v) for k, v in EXPECTED.items() if not close(got.get(k), v)}
        assert not wrong, wrong
        check("every live measure scores as Scorecard.xlsx says (linear cash, completion and inspection bands)")

        sched = sum(EXPECTED[k] for k in (201, 202, 203, 204, 205, 206, 207)) / 7
        budget = (EXPECTED[101] + EXPECTED[102] + EXPECTED[103]) / 3
        grade = 100 * (0.50 * sched + 0.30 * budget + 0.15 * EXPECTED[301] + 0.05 * EXPECTED[401])
        row = q(con, "SELECT SchedulePillar, BudgetPillar, SafetyPillar, QualityPillar, GradeCoverage, Grade, "
                     "MeasuresBelowTarget, WeakestPillar FROM fct_ProjectScore WHERE ProjectKey = 'X' AND WeeksAgo = 0")[0]
        assert all(close(a, b) for a, b in zip(row[:6], (sched, budget, EXPECTED[301], EXPECTED[401], 1.0, grade))), row
        check("pillars are equal-weighted averages; the grade weights them 50 / 30 / 15 / 5 (Oct 21 call)")
        assert row[6] == sum(1 for v in EXPECTED.values() if v < 0.8), row
        check("measures below target counts every score under 80%")
        # Schedule loses 50 x 39% = 19.5 points; safety, the lowest score (48%), loses 7.8.
        assert row[7] == "Schedule", row
        check("the weakest pillar is the one costing the grade most points, not the lowest score")

        y = q(con, "SELECT MetricKey, Applies, Score FROM fct_MetricScore WHERE ProjectKey = 'Y' AND WeeksAgo = 0 "
                   "AND MetricKey IN (201, 206, 301) ORDER BY 1")
        assert y == [(201, False, None), (206, True, None), (301, False, None)], y
        check("no phase: phase-gated measures do not apply; no submittals scores BLANK, not 100%")
        assert q(con, "SELECT GradeCoverage, Grade, MeasuresBelowTarget FROM fct_ProjectScore "
                      "WHERE ProjectKey = 'Y' AND WeeksAgo = 0") == [(0.3, None, None)]
        check("under half the weight measured is Unscored (grade BLANK), not a failing grade")

        old = dict(q(con, "SELECT MetricKey, Score FROM fct_MetricScore WHERE ProjectKey = 'X' AND WeeksAgo = 2 "
                          "AND MetricKey IN (203, 204, 301)"))
        assert old[203] is None and old[204] is None and close(old[301], 0.8 - 4 * 0.16), old
        check("earlier weeks: look-ahead and schedule update unmeasured (no Outbuild history); inspections by week")
    finally:
        con.execute("ROLLBACK")


def test_position(con) -> None:
    rows = q(con, "SELECT ProjectKey, BilledToDateGross, RetainageReceivable, UnpaidReceivables, CashCollected, "
                  "CostsIncurred, UnpaidPayables, RetainagePayable, CashPaidOut, OriginalContract, BilledPct, Phase "
                  "FROM fct_ProjectPosition WHERE BilledToDateGross IS NOT NULL")
    assert rows, "no fixture project has billings"
    for (k, billed, ret_r, unpaid_r, collected, cost, unpaid_p, ret_p, paid_out, original, pct, phase) in rows:
        assert close(collected, float(billed) - float(ret_r) - float(unpaid_r)), k
        assert close(paid_out, float(cost) - float(unpaid_p) - float(ret_p)), k
        assert phase == ("Precon" if pct < 0.10 else "Closeout" if pct > 0.95 else "Construction"), (k, pct, phase)
    check("Cash Position follows Chris's formula: billings - retainage - unpaid AR, less cost - unpaid AP - sub retainage")
    check("phase is billed % of contract: under 10% Precon, over 95% Closeout")
    assert q(con, "SELECT OriginalContract FROM fct_ProjectPosition WHERE ProjectKey = 'P1'") == [(8800000.0,)]
    check("the sample project's original contract is the workbook's 8,800,000 (deck slide 3)")
    assert q(con, "SELECT COUNT(*), COUNT(DISTINCT ProjectKey) FROM fct_ProjectPosition") == \
        q(con, "SELECT COUNT(*), COUNT(*) FROM dim_Project WHERE ProjectKey <> 'UNMATCHED'")
    check("one position row per real project, none for UNMATCHED")


def test_meetings(con) -> None:
    got = {r[0]: r[1:] for r in q(con, "SELECT MeetingKey, MeetingType, IsCompliant, MinutesStatus, AgendaStatus "
                                       "FROM fct_Meeting")}
    assert got["M1"] == ("OAC", True, "On time", "Not verifiable - minutes sent since"), got["M1"]
    assert got["M2"][1] is False, got["M2"]
    assert got["M3"] == ("Trade Partner", False, "Not sent", "Late"), got["M3"]
    assert got["M4"][0] == "Other", got["M4"]
    check("minutes sent the next day are on time; once sent, the agenda's time is not verifiable, not failed")
    check("a second meeting on the same date counts once; a template series is Other, never OAC")


def test_review_fixes(con) -> None:
    """Defects found in the 2026-10-25 review, each pinned so it cannot come back."""
    con.execute("BEGIN")
    try:
        # A held template meeting on a dead project, and OAC meetings 1 and 3 days ago with no minutes.
        con.execute("""CREATE OR REPLACE VIEW sv_meetings AS SELECT * FROM (VALUES
            ('P2', 'T1', 'Kick Start Agenda Template', 'Template', CURRENT_DATE - 1, 'minutes', TRUE,
             CAST(NULL AS VARCHAR), CAST(NULL AS DATE), TIMESTAMP '2025-05-01 12:00:00', 1),
            ('P1', 'Y1', 'Tower OAC Meeting', 'Tower OAC Meeting', CURRENT_DATE - 1, 'minutes', TRUE,
             CAST(NULL AS VARCHAR), CAST(NULL AS DATE), TIMESTAMP '2025-05-01 12:00:00', 1),
            ('P1', 'Y3', 'Tower OAC Meeting', 'Tower OAC Meeting', CURRENT_DATE - 3, 'minutes', TRUE,
             CAST(NULL AS VARCHAR), CAST(NULL AS DATE), TIMESTAMP '2025-05-01 12:00:00', 1)
        ) AS t(project_id, meeting_id, series_title, title, meeting_date, meeting_mode, occurred,
               last_distributed_event, distributed_date, created_at, position)""")
        for sql in seedrunner.split_statements((GOLD / "46_dashboard_facts.sql").read_text(encoding="utf-8")):
            con.execute(sql)
        status = dict(q(con, "SELECT MeetingKey, MinutesStatus FROM fct_Meeting WHERE ProjectKey = 'P1'"))
        assert status == {"Y1": "Not yet due", "Y3": "Not sent"}, status
        check("minutes are not late until the day after the meeting has passed")
        assert q(con, "SELECT LastActivityDate, DashboardStatus FROM fct_ProjectPosition WHERE ProjectKey = 'P2'") == \
            [(None, "Inactive")]
        check("a template meeting does not make a dead project Active")

        # Revenue with no forecast cost: margin unmeasured, never 100%.
        con.execute("UPDATE fct_ProjectPosition SET ProjectedRevenue = 1000, ProjectedCost = NULL WHERE ProjectKey = 'P1'")
        for sql in seedrunner.split_statements((GOLD / "47_dashboard_score.sql").read_text(encoding="utf-8")):
            con.execute(sql)
        assert q(con, "SELECT DISTINCT Driver, Score FROM fct_MetricScore WHERE ProjectKey = 'P1' AND MetricKey = 102") == \
            [(None, None)]
        check("a project with no forecast cost has no margin score (it used to score 100%)")
    finally:
        con.execute("ROLLBACK")


def main() -> int:
    con = build()
    for fn in (test_position, test_meetings, test_review_fixes, test_scoring):
        fn(con)
    for label in CHECKS:
        print(f"  ok  {label}")
    print(f"\ntest_dashboard_gold: {len(CHECKS)} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
