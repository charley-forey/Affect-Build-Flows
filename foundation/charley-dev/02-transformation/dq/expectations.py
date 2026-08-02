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
