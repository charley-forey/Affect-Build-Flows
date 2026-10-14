"""The nine scorecard category measures, plus their drivers and the weighted total.

analysis/excel-tracker/README.md:174 calls this "the most valuable thing here and it is
partly broken ... Rebuilding it correctly in DAX is the highest-leverage single piece of
the build". It is a genuine, agreed, weighted definition of project health - and three of
its nine categories currently measure nothing.

THE DESIGN RULE: no threshold is written in DAX. Every score is a LOOKUP against
dim_ScorecardBand, and every weight a lookup against dim_ScorecardWeight. Affect retunes
the scorecard by editing two seed tables, not by finding a developer. It is also what
makes defects #1a-#1c fixable once, in data, rather than in nine nested IF chains.

BLANK, NEVER ZERO. A category with no data returns BLANK, not 0. Scoring a missing input
as zero is exactly how the workbook's Completion Variance silently cost every project 15%
of its score. [Scorecard Coverage %] then reports how much of the weight is genuinely
being measured - the honest headline number, given that ~40% of the report's inputs still
live only in a spreadsheet.
"""

from __future__ import annotations

# Category keys match dim_ScorecardWeight / dim_ScorecardBand.
AR, PROFIT, CASH, CO, SAFETY, SCHEDULE, COMPLETION, OBSERVATIONS, DAILY = range(1, 10)


def numeric_band(category: int, driver: str) -> str:
    """Resolve a numeric driver to its 3/2/0 score by looking up the band table.

    Half-open intervals: MinValue inclusive, MaxValue exclusive, NULL unbounded - which is
    why the seeded bands tile the number line with no gap and no overlap.

    ALL() is required: dim_ScorecardBand has no relationship to anything, but a slicer on
    another table would still narrow it through the filter context and silently drop the
    matching band.
    """
    return (
        f"VAR V = [{driver}]\n"
        "RETURN\n"
        "IF (\n"
        "    ISBLANK ( V ),\n"
        "    BLANK (),\n"
        "    MAXX (\n"
        "        FILTER (\n"
        "            ALL ( dim_ScorecardBand ),\n"
        f"            dim_ScorecardBand[CategoryKey] = {category}\n"
        "                && ( ISBLANK ( dim_ScorecardBand[MinValue] ) || V >= dim_ScorecardBand[MinValue] )\n"
        "                && ( ISBLANK ( dim_ScorecardBand[MaxValue] ) || V < dim_ScorecardBand[MaxValue] )\n"
        "        ),\n"
        "        dim_ScorecardBand[Score]\n"
        "    )\n"
        ")"
    )


def text_band(category: int, driver: str) -> str:
    """Resolve a text driver by exact match against MatchValue.

    The workbook does the same thing with nested IFs against DROPDOWN cells, where a single
    changed character silently zeroes a 12%-weighted category. Here an unmatched value
    returns BLANK rather than 0, so it shows up as missing instead of as a bad score.
    """
    return (
        f"VAR V = [{driver}]\n"
        "RETURN\n"
        "IF (\n"
        "    ISBLANK ( V ),\n"
        "    BLANK (),\n"
        "    MAXX (\n"
        "        FILTER (\n"
        "            ALL ( dim_ScorecardBand ),\n"
        f"            dim_ScorecardBand[CategoryKey] = {category}\n"
        "                && dim_ScorecardBand[MatchValue] = V\n"
        "        ),\n"
        "        dim_ScorecardBand[Score]\n"
        "    )\n"
        ")"
    )


# The nine categories, in dim_ScorecardWeight order.
CATEGORY_MEASURES = [
    (AR, "Score - Accounts Receivable"),
    (PROFIT, "Score - Profitability"),
    (CASH, "Score - Cash Position"),
    (CO, "Score - Change Orders"),
    (SAFETY, "Score - Safety Incidents"),
    (SCHEDULE, "Score - Schedule Performance"),
    (COMPLETION, "Score - Completion Variance"),
    (OBSERVATIONS, "Score - Observations"),
    (DAILY, "Score - Daily Reports"),
]

# A project below target on this many categories is flagged, whatever its weighted rank.
ATTENTION_CATEGORIES = 2

# Pillars shown as side-by-side columns on the Portfolio table. Names match
# dim_ScorecardWeight[Pillar]; a pillar the workshop adds gets a line here.
PILLARS = ["Financial", "Schedule", "Safety & Quality", "Reporting"]

# Data-entry checks (Cal Egan, 2026-10-13: "ensuring the data is actually inputted").
# A project whose schedule says it should be on site but has no daily log for this many
# calendar days is flagged.
DAILY_LOG_GRACE_DAYS = 7

# Performance Bonus & Incentive Policy (FY2026): the project score feeds the rating tier,
# and the tier sets the multiplier. The policy names the tiers and multipliers but not the
# score cut-offs, so these minimums are PROPOSED - 0.60 is the existing at-risk line.
# ponytail: constants until the workshop confirms them; then a seed table like the bands.
RATING_TIERS = [  # (minimum score, rating, multiplier %)
    (0.90, "Outstanding", 150),
    (0.75, "Exceeds Expectations", 115),
    (0.60, "Meets Expectations", 100),
    (0.40, "Needs Improvement", 50),
    (0.00, "Unacceptable", 0),
]
# Policy: "A project will be rated as Needs Improvement if either Safety or Quality is
# subpar." Subpar = below target (under 3) on Safety Incidents or Observations.
GATE_CATEGORIES = ("Score - Safety Incidents", "Score - Observations")
GATE_RATING = "Needs Improvement"

_SWITCH = "\n".join(
    f"            {key}, [{name}],"
    for key, name in CATEGORY_MEASURES
)


def measures() -> list[tuple[str, str, str | None, str]]:
    """(name, dax, formatString, origin) tuples, ready for the TMDL generator."""
    return [
        # -- drivers -------------------------------------------------------------
        (
            "Avg Days To Payment",
            # Sent to PAID, per fct_Invoice[DaysToPayment]: PaidDate is the day Sage
            # receipts (acrpmt) first fully covered the invoice. AVERAGE skips blanks, so
            # only fully-paid invoices count, and it is BLANK when none are in context -
            # the category then scores BLANK. Due date is never substituted for paid date.
            "AVERAGE ( fct_Invoice[DaysToPayment] )",
            '"#,0.0"',
            "FINANCIALS!F56 - now from Sage AR receipts (acrpmt)",
        ),
        (
            "Cash Position %",
            # FINANCIALS!C8 is a DROPDOWN in the workbook, but the note in G8 spells out
            # the arithmetic. Computing it removes one of the three subjective inputs.
            # The fact, not [Cost To Complete]: that card ignores the month slicer, and a
            # month's invoices over the whole remaining cost would score every job at risk.
            "DIVIDE ( [Total Paid] + [AR Outstanding], SUM ( fct_BudgetLine[CostToComplete] ) )",
            '"0.0%"',
            "FINANCIALS!C8 - a human judgement the workbook could already have computed",
        ),
        (
            "Profitability Code",
            "SELECTEDVALUE ( man_Flags[ProfitabilityCode] )",
            None,
            "FINANCIALS!C7 - a genuine human judgement, stays manual",
        ),
        (
            "Recordable Incidents",
            # BLANK, NEVER ZERO: a project or month with no hours logged and no incident
            # recorded is unmeasured, not incident-free. Zero only once hours exist.
            "VAR I = SUM ( fct_SafetyMonthly[RecordableIncidents] )\n"
            "VAR H = SUM ( fct_SafetyMonthly[HoursWorked] )\n"
            "RETURN IF ( H > 0 || I > 0, COALESCE ( I, 0 ) )",
            '"#,0"',
            "SAFETY!E - Procore /incidents, in the registry but not yet ingested",
        ),
        (
            "Hours Worked",
            # From the FACT now: 911 project-days of Procore manpower logs, summed. Was
            # man_SafetyMonthly, the hand-typed table that is still empty - so this
            # category scored BLANK and dragged [Scorecard Coverage %] down with it.
            # BLANK when no hours were logged, rather than a confident 0.
            "VAR H = SUM ( fct_SafetyMonthly[HoursWorked] )\n"
            "RETURN IF ( H > 0, H )",
            '"#,0"',
            "SAFETY!D - Sage payroll / ADP / Procore timecards, undecided",
        ),
        (
            "Observations",
            # NOW FROM THE FACT, not the hand-typed table. This is defect #2 retired:
            # QUALITY!D5:D6 read SAFETY orientations onto the quality tab, and a count
            # sourced from the observation records cannot make that mistake.
            "COALESCE ( CALCULATE ( COUNTROWS ( fct_QualityItem ), "
            "fct_QualityItem[ItemType] = \"Observation\" ), 0 )",
            '"#,0"',
            "Procore /observations/items - was QUALITY!D, typed by hand",
        ),
        (
            "Avg Observation Days To Close",
            # Averaged over CLOSED items only, hence "to close" - not the age of open items. Mixing open and closed would blend "how long
            # has this been outstanding" with "how long did that take to close" - two
            # different questions with one misleading answer.
            "AVERAGEX ( FILTER ( fct_QualityItem, NOT fct_QualityItem[IsOpen] "
            '&& fct_QualityItem[ItemType] = "Observation" ), '
            "fct_QualityItem[DaysOpen] )",
            '"#,0.0"',
            "QUALITY!D39 - typed by hand today",
        ),
        (
            "Daily Reports Missed",
            # FROM PROCORE now, not the hand-typed man_DailyLogCompliance list (still empty).
            # Weekdays with no daily log between the month's first and last log - see
            # 26_fct_safetymonthly.sql. BLANK for a month with no logs at all: unmeasured.
            "SUM ( fct_SafetyMonthly[DailyLogsMissed] )",
            '"#,0"',
            "SCORECARD CALC!E28 - now Procore daily logs (manpower entries), not typed",
        ),
        (
            "Last Daily Log",
            # Whatever the month slicer says: "when did this site last file a log" is a
            # question about today.
            "CALCULATE ( MAX ( fct_SafetyMonthly[LastLogDate] ), REMOVEFILTERS ( dim_Date ) )",
            '"yyyy-mm-dd"',
            "no workbook equivalent - data-entry check",
        ),
        (
            "Days Since Daily Log",
            "VAR L = [Last Daily Log]\n"
            "RETURN IF ( NOT ISBLANK ( L ), DATEDIFF ( L, TODAY (), DAY ) )",
            '"#,0"',
            "no workbook equivalent - data-entry check",
        ),
        (
            "Scheduled Finish",
            # The last critical-path finish in Outbuild: when the schedule says the job ends.
            "CALCULATE ( MAX ( fct_Milestone[CurrentFinish] ), REMOVEFILTERS ( dim_Date ) )",
            '"yyyy-mm-dd"',
            "SCHEDULE!Table5 terminator row - from Outbuild",
        ),
        (
            "Schedule Ended Site Active",
            # Cal Egan, 2026-10-13: the schedule "runs out to completion but daily logs and
            # punchlist items are still being completed". The schedule has stopped being
            # true, so it must not keep scoring 3/3 on milestones it marked done.
            "VAR F = [Scheduled Finish]\n"
            "RETURN IF ( NOT ISBLANK ( F ) && F < TODAY (),\n"
            "    [Last Daily Log] > F\n"
            "        || CALCULATE ( [Open Punch Items], REMOVEFILTERS ( dim_Date ) ) > 0 )",
            None,
            "no workbook equivalent - the 2026-10-13 schedule-overrun rule",
        ),
        (
            "Input Check",
            # Text, never colour alone. BLANK when nothing is wrong, so a table of projects
            # reads as a to-do list.
            "VAR F = [Scheduled Finish]\n"
            "VAR D = [Days Since Daily Log]\n"
            "RETURN\n"
            "SWITCH (\n"
            "    TRUE (),\n"
            '    [Schedule Ended Site Active], "Schedule ended - site still active",\n'
            f"    NOT ISBLANK ( F ) && F >= TODAY () && ISBLANK ( D ), \"No daily logs in Procore\",\n"
            f"    NOT ISBLANK ( F ) && F >= TODAY () && D > {DAILY_LOG_GRACE_DAYS}, "
            '"No daily log for " & D & " days",\n'
            f"    ISBLANK ( F ) && NOT ISBLANK ( D ) && D <= 30, \"No schedule in Outbuild\"\n"
            ")",
            None,
            "no workbook equivalent - is the data actually being entered",
        ),
        (
            "Completion Variance Days",
            # Current forecast finish vs BASELINE finish. Baseline lives in man_Milestones
            # because Outbuild may not hold baselines at all - unconfirmed. Without it this
            # is BLANK rather than a confident zero from comparing current against current.
            # NOT `VAR Current` - "Current" is reserved in DAX and the measure fails to
            # parse. Analysis Services then replaces it with SYNTAXERROR, which breaks the
            # ENTIRE model script: every query, including ones touching none of this,
            # returns "Failed to resolve name 'SYNTAXERROR'". One bad measure takes down
            # all 52.
            "VAR Baseline = MAX ( man_Milestones[BaselineFinish] )\n"
            "VAR Forecast = MAX ( fct_Milestone[CurrentFinish] )\n"
            "RETURN IF ( ISBLANK ( Baseline ) || ISBLANK ( Forecast ), BLANK (), "
            "DATEDIFF ( Baseline, Forecast, DAY ) )",
            '"#,0"',
            "DASHBOARD!M16 - which returned the TEXT \"0 days\" (defect #1b)",
        ),
        (
            "Client Satisfaction",
            # COUNTROWS, not COUNT of answered: an unanswered question still counts toward
            # the denominator, matching COUNTA(B36:B41) in the workbook.
            "DIVIDE ( SUM ( man_Survey[Score] ), COUNTROWS ( man_Survey ) * 5 )",
            '"0.0%"',
            "SCORECARD CALC!C42",
        ),

        # -- the nine category scores -------------------------------------------
        (
            "Score - Accounts Receivable",
            numeric_band(AR, "Avg Days To Payment"),
            '"0"',
            "SCORECARD CALC!E13 - FIX: driver is days to payment, not an aging balance "
            "(defect #1c)",
        ),
        (
            "Score - Profitability",
            text_band(PROFIT, "Profitability Code"),
            '"0"',
            "SCORECARD CALC!E7",
        ),
        (
            "Score - Cash Position",
            numeric_band(CASH, "Cash Position %"),
            '"0"',
            "SCORECARD CALC!E10 - now computed rather than picked from a dropdown",
        ),
        (
            "Score - Change Orders",
            numeric_band(CO, "Age Of Oldest Unapproved CO"),
            '"0"',
            "SCORECARD CALC!E14",
        ),
        (
            "Score - Safety Incidents",
            numeric_band(SAFETY, "Recordable Incidents"),
            '"0"',
            "SCORECARD CALC!E16",
        ),
        (
            "Score - Schedule Performance",
            # Zero when the schedule has run out but the site is still working: every
            # milestone reads complete, so the band alone would award 3/3 (2026-10-13 rule).
            "IF ( [Schedule Ended Site Active], 0,\n"
            + numeric_band(SCHEDULE, "Milestones Overdue %") + " )",
            '"0"',
            "SCORECARD CALC!E19 - FIX: bands are fractions, so this stops always "
            "awarding 3/3 (defect #1a); 0 when the schedule ended but the site is active",
        ),
        (
            "Score - Completion Variance",
            numeric_band(COMPLETION, "Completion Variance Days"),
            '"0"',
            "SCORECARD CALC!E22 - FIX: numeric, so finishing on baseline scores 3 "
            "not 0 (defect #1b)",
        ),
        (
            "Score - Observations",
            numeric_band(OBSERVATIONS, "Avg Observation Days To Close"),
            '"0"',
            "SCORECARD CALC!E25",
        ),
        (
            "Score - Daily Reports",
            numeric_band(DAILY, "Daily Reports Missed"),
            '"0"',
            "SCORECARD CALC!E28",
        ),

        # -- the total ----------------------------------------------------------
        (
            "Project Scorecard",
            # Weights come from the table, not from DAX, so retuning is a data edit.
            # Divided by 3 because 3 is the maximum category score - this is the
            # workbook's own ((E*F)/3) normalisation to a 0-1 index.
            # BLANK when nothing is measured: 0.00 on an uninstrumented project reads as a
            # failing one. [Scorecard Coverage %] sits beside it on every page that shows it.
            "IF ( [Scorecard Coverage %] > 0,\n"
            "DIVIDE (\n"
            "    SUMX (\n"
            "        ALL ( dim_ScorecardWeight ),\n"
            "        VAR S =\n"
            "            SWITCH (\n"
            "                dim_ScorecardWeight[CategoryKey],\n"
            f"{_SWITCH}\n"
            "                BLANK ()\n"
            "            )\n"
            "        RETURN IF ( ISBLANK ( S ), 0, S * dim_ScorecardWeight[Weight] )\n"
            "    ),\n"
            "    3\n"
            ") )",
            '"0.00"',
            "SCORECARD CALC!G31",
        ),
        (
            "Scorecard Coverage %",
            # The honest headline. The workbook's 0.59 looks like a health score but 42% of
            # its weight was measuring nothing - and because a missing category scored 0
            # rather than blank, that was invisible. This makes it visible: what share of
            # the agreed weight is actually being measured right now.
            "SUMX (\n"
            "    ALL ( dim_ScorecardWeight ),\n"
            "    VAR S =\n"
            "        SWITCH (\n"
            "            dim_ScorecardWeight[CategoryKey],\n"
            f"{_SWITCH}\n"
            "            BLANK ()\n"
            "        )\n"
            "    RETURN IF ( ISBLANK ( S ), 0, dim_ScorecardWeight[Weight] )\n"
            ")",
            '"0.0%"',
            "no equivalent - the workbook could not tell you this",
        ),
        (
            "Project Scorecard (Measured Only)",
            # Rescaled to the weight actually available, so a partially-instrumented
            # project is comparable to a fully-instrumented one instead of just looking bad.
            "DIVIDE ( [Project Scorecard], [Scorecard Coverage %] )",
            '"0.00"',
            "derived - makes partial coverage comparable",
        ),

        # -- per-category, for the audit table and the portfolio heatmap ----------
        #
        # [Project Scorecard] iterates ALL(dim_ScorecardWeight) internally and returns one
        # number, which is correct for a tile and useless for showing the WORKING. These
        # three resolve one category at a time, so the same switch drives a table with a
        # row per category and a matrix with a row per project.
        #
        # Same _SWITCH as the total. Sharing it is the point: the audit table cannot
        # disagree with the headline score, because there is only one definition.
        (
            "Category Score",
            "VAR K = SELECTEDVALUE ( dim_ScorecardWeight[CategoryKey] )\n"
            "RETURN\n"
            "SWITCH (\n"
            "    K,\n"
            f"{_SWITCH}\n"
            "    BLANK ()\n"
            ")",
            '"0"',
            "SCORECARD CALC!E23:E31 - the per-category score, never displayed in the Excel",
        ),
        (
            "Category Weighted",
            # What this category actually contributes to the 0-1 headline. The column that
            # makes the score auditable: these sum to [Project Scorecard] exactly.
            "VAR S = [Category Score]\n"
            # In a totals row (no single category) it shows the headline, so the column
            # visibly adds up to [Project Scorecard] instead of ending in a blank.
            "VAR W = SELECTEDVALUE ( dim_ScorecardWeight[Weight] )\n"
            "RETURN IF ( NOT HASONEVALUE ( dim_ScorecardWeight[CategoryKey] ), [Project Scorecard],\n"
            "    IF ( ISBLANK ( S ), BLANK (), DIVIDE ( S * W, 3 ) ) )",
            '"0.000"',
            "SCORECARD CALC!G23:G31 - ((E*F)/3), the workbook's own normalisation",
        ),
        (
            "Category Band",
            # Which band the driver landed in, in the seed table's own words. Without this
            # a reader can see a category scored 0 but not why, which is how three dead
            # bands survived in the workbook for as long as they did.
            "VAR K = SELECTEDVALUE ( dim_ScorecardWeight[CategoryKey] )\n"
            "VAR S = [Category Score]\n"
            "RETURN\n"
            "IF ( NOT HASONEVALUE ( dim_ScorecardWeight[CategoryKey] ), BLANK (),\n"
            "IF (\n"
            "    ISBLANK ( S ),\n"
            '    "Not measured",\n'
            "    CALCULATE (\n"
            "        MAX ( dim_ScorecardBand[BandLabel] ),\n"
            "        ALL ( dim_ScorecardBand ),\n"
            "        dim_ScorecardBand[CategoryKey] = K,\n"
            "        dim_ScorecardBand[Score] = S\n"
            "    )\n"
            ") )",
            None,
            "derived - the band the driver fell in, in the seed table's own words",
        ),

        # -- the Project Scorecard report: rank, re-rank by pillar, flag ----------
        #
        # The 2026-10-09 ask: stack-rank every project, then "show me just schedule" without
        # leaving the page. A slicer on dim_ScorecardWeight[Pillar] narrows the categories,
        # and this score is computed over whatever categories survive the filter - so with
        # no pillar selected it IS [Project Scorecard (Measured Only)], the same SWITCH, and
        # cannot disagree with it. Rescaled to measured weight for the same reason.
        (
            "Pillar Score",
            "VAR T =\n"
            "    ADDCOLUMNS (\n"
            "        dim_ScorecardWeight,\n"
            '        "@S",\n'
            "        SWITCH (\n"
            "            dim_ScorecardWeight[CategoryKey],\n"
            f"{_SWITCH}\n"
            "            BLANK ()\n"
            "        )\n"
            "    )\n"
            "VAR Measured = SUMX ( FILTER ( T, NOT ISBLANK ( [@S] ) ), dim_ScorecardWeight[Weight] )\n"
            "RETURN IF ( Measured > 0, DIVIDE ( SUMX ( T, [@S] * dim_ScorecardWeight[Weight] ), 3 * Measured ) )",
            '"0.00"',
            "derived - [Project Scorecard (Measured Only)] over the selected pillars",
        ),
        (
            "Project Rank",
            # Dense, highest score first; BLANK for a project with nothing measured, so an
            # uninstrumented job is not ranked last as if it were failing.
            "IF ( ISBLANK ( [Pillar Score] ), BLANK (),\n"
            "RANKX ( ALLSELECTED ( dim_Project[ProjectName] ), [Pillar Score], , DESC, DENSE ) )",
            '"#,0"',
            "no workbook equivalent - one workbook per project cannot rank them",
        ),
        (
            "Categories Below Target",
            # Measured categories scoring under 3, across all nine whatever the pillar
            # slicer says: "mediocre on three things" is a whole-project signal.
            "SUMX (\n"
            "    ALL ( dim_ScorecardWeight ),\n"
            "    VAR S =\n"
            "        SWITCH (\n"
            "            dim_ScorecardWeight[CategoryKey],\n"
            f"{_SWITCH}\n"
            "            BLANK ()\n"
            "        )\n"
            "    RETURN IF ( NOT ISBLANK ( S ) && S < 3, 1, 0 )\n"
            ")",
            '"#,0"',
            "derived - the 2026-10-09 'mediocre on several metrics' signal",
        ),
        (
            "Needs Attention",
            # Text, never colour alone. A project can rank mid-pack on the weighted sum while
            # slipping on several categories at once; the call asked for that to stand out.
            # ponytail: threshold is a constant; move it to a seed row if Affect retunes it.
            f'IF ( [Categories Below Target] >= {ATTENTION_CATEGORIES}, "Needs attention" )',
            None,
            "derived - flags projects below target on several categories",
        ),

        # -- one column per pillar, for the all-projects comparison table ----------
        # CALCULATE replaces any pillar slicer, so each column always means its pillar.
        *[(f"{p} Score",
           f'CALCULATE ( [Pillar Score], dim_ScorecardWeight[Pillar] = "{p}" )',
           '"0.00"',
           f"derived - [Pillar Score] for the {p} pillar")
          for p in PILLARS],

        # -- the bonus policy: score -> rating tier -> multiplier ------------------
        (
            "Safety Quality Gate",
            # TRUE when Safety or Quality is below target. BLANK, not FALSE, when neither
            # is measured: an unmeasured project has not passed the gate.
            "VAR A = [" + GATE_CATEGORIES[0] + "]\n"
            "VAR B = [" + GATE_CATEGORIES[1] + "]\n"
            "RETURN IF ( NOT ISBLANK ( A ) || NOT ISBLANK ( B ),\n"
            "    ( NOT ISBLANK ( A ) && A < 3 ) || ( NOT ISBLANK ( B ) && B < 3 ) )",
            None,
            "Bonus policy p.2 - Needs Improvement if either Safety or Quality is subpar",
        ),
        (
            "Bonus Multiplier %",
            "VAR S = [Project Scorecard (Measured Only)]\n"
            "VAR M =\n"
            "    SWITCH ( TRUE (),\n"
            + "".join(f"        S >= {lo}, {mult},\n" for lo, _, mult in RATING_TIERS[:-1])
            + f"        {RATING_TIERS[-1][2]} )\n"
            f"VAR Cap = {next(m for _, r, m in RATING_TIERS if r == GATE_RATING)}\n"
            "RETURN IF ( NOT ISBLANK ( S ),\n"
            "    DIVIDE ( IF ( [Safety Quality Gate], MIN ( M, Cap ), M ), 100 ) )",
            '"0%"',
            "Bonus policy p.1 - performance score tier multiplier (cut-offs proposed)",
        ),
        (
            "Performance Rating",
            "VAR M = [Bonus Multiplier %] * 100\n"
            "RETURN IF ( NOT ISBLANK ( M ),\n"
            "    SWITCH ( TRUE (),\n"
            + "".join(f'        M >= {mult - 0.5}, "{rating}",\n' for _, rating, mult in RATING_TIERS[:-1])
            + f'        "{RATING_TIERS[-1][1]}" ) )',
            None,
            "Bonus policy p.1 - Outstanding / Exceeds / Meets / Needs Improvement / Unacceptable",
        ),
    ]
