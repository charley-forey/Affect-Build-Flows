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
            # The AR header carries the amount paid but NOT the payment DATE, so days-to-
            # payment cannot be computed from it (verified while building fct_Invoice).
            # Returning BLANK is deliberate: the alternative is substituting days-to-DUE,
            # which looks like an answer and is not one. The category scores BLANK and
            # [Scorecard Coverage %] reports the gap.
            "BLANK ()",
            '"#,0.0"',
            "FINANCIALS!F56 - blocked: Sage AR header has no payment date",
        ),
        (
            "Cash Position %",
            # FINANCIALS!C8 is a DROPDOWN in the workbook, but the note in G8 spells out
            # the arithmetic. Computing it removes one of the three subjective inputs.
            "DIVIDE ( [Total Paid] + [AR Outstanding], [Cost To Complete] )",
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
            "COALESCE ( SUM ( fct_SafetyMonthly[RecordableIncidents] ), 0 )",
            '"#,0"',
            "SAFETY!E - Procore /incidents, in the registry but not yet ingested",
        ),
        (
            "Hours Worked",
            # From the FACT now: 911 project-days of Procore manpower logs, summed. Was
            # man_SafetyMonthly, the hand-typed table that is still empty - so this
            # category scored BLANK and dragged [Scorecard Coverage %] down with it.
            "COALESCE ( SUM ( fct_SafetyMonthly[HoursWorked] ), 0 )",
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
            "Avg Observation Days Open",
            # Averaged over CLOSED items only. Mixing open and closed would blend "how long
            # has this been outstanding" with "how long did that take to close" - two
            # different questions with one misleading answer.
            "AVERAGEX ( FILTER ( fct_QualityItem, NOT fct_QualityItem[IsOpen] ), "
            "fct_QualityItem[DaysOpen] )",
            '"#,0.0"',
            "QUALITY!D39 - typed by hand today",
        ),
        (
            "Daily Reports Missed",
            "SUM ( man_DailyLogCompliance[LogsMissedSameDay] )",
            '"#,0"',
            "SCORECARD CALC!E28 - Procore /daily_log_headers derives this",
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
            numeric_band(SCHEDULE, "Schedule Performance %"),
            '"0"',
            "SCORECARD CALC!E19 - FIX: bands are fractions, so this stops always "
            "awarding 3/3 (defect #1a)",
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
            numeric_band(OBSERVATIONS, "Avg Observation Days Open"),
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
            ")",
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
            "VAR W = SELECTEDVALUE ( dim_ScorecardWeight[Weight] )\n"
            "RETURN IF ( ISBLANK ( S ), BLANK (), DIVIDE ( S * W, 3 ) )",
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
            "IF (\n"
            "    ISBLANK ( S ),\n"
            '    "Not measured",\n'
            "    CALCULATE (\n"
            "        MAX ( dim_ScorecardBand[BandLabel] ),\n"
            "        ALL ( dim_ScorecardBand ),\n"
            "        dim_ScorecardBand[CategoryKey] = K,\n"
            "        dim_ScorecardBand[Score] = S\n"
            "    )\n"
            ")",
            None,
            "derived - the band the driver fell in, in the seed table's own words",
        ),
    ]
