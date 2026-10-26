"""The Weekly Dashboard's measures: the v1 project scorecard (Scorecard.xlsx) and the three
deck pages (AFFECT Weekly Dashboard Layout 10-21-26.pptx).

THE SCORECARD. Seventeen measures in five departments (Scorecard.xlsx), rolled into the four
pillars the deck's Portfolio page shows - Schedule (Field Ops), Budget (Financial), Safety,
Quality - weighted 50 / 30 / 15 / 5 (the Oct 21 call), into a 0-100 grade.

Same design rules as scorecard.py, which this sits beside and does not change:

  NO THRESHOLD IN DAX. Every score is a lookup against dim_DashBand, every weight against
  dim_DashPillar, every target and cut-off against dim_DashSetting. Retuning is a CSV edit.

  BLANK, NEVER ZERO. A measure with no data, or one that does not apply at the project's
  phase (Scorecard.xlsx's Stage column), is BLANK and drops out of its pillar's average; a
  pillar with nothing measured drops out of the grade, and [Grade Coverage %] says how much
  of the weight is real. A project under the coverage minimum is Unscored, not failing.

  EQUAL WEIGHTS INSIDE A PILLAR. Scorecard.xlsx's Weighting column is empty and the call
  said "the five headings equally"; the pillar weights are the call's.

THE WEEK. dim_ReportWeek is the slicer ('Last week' by default). Window measures read it
explicitly; it filters no table. Current-state measures (open RFIs, the look-ahead, today's
balances) are what they are today whatever week is picked, and say so.
"""

from __future__ import annotations

# Metric keys (dim_DashMetric). Pillar keys: 1 Schedule, 2 Budget, 3 Safety, 4 Quality.
CASH, PROFIT, AGING = 101, 102, 103
OAC, TRADE, LOOKAHEAD, SCHED_UPDATE, COMPLETION, SUBMITTALS, RFIS = 201, 202, 203, 204, 205, 206, 207
SAFETY_INSP, QUALITY_INSP = 301, 401

PILLARS = [(1, "Schedule"), (2, "Budget"), (3, "Safety"), (4, "Quality")]

# Deck palette (slide XML), and text that reads on it. White on the deck's amber is 2:1,
# so amber pills carry navy text - colour is never the only channel either way.
NAVY, TEAL, GREEN, AMBER, RED, SLATE, MIST = ("#16283F", "#087F83", "#278367", "#E5A13B",
                                              "#BF534E", "#657589", "#DDE4EB")


def setting(key: str) -> str:
    return (f'CALCULATE ( MAX ( dim_DashSetting[Value] ), REMOVEFILTERS ( dim_DashSetting ), '
            f'dim_DashSetting[SettingKey] = "{key}" )')


def pillar_weight(key: int) -> str:
    return (f"CALCULATE ( MAX ( dim_DashPillar[Weight] ), REMOVEFILTERS ( dim_DashPillar ), "
            f"dim_DashPillar[PillarKey] = {key} )")


# (metric key, display name, driver measure). The driver is the number the band scores.
METRICS = [
    (CASH, "Cash Position", "Cash Collected / Paid"),
    (PROFIT, "Profitability", "Margin vs Target"),
    (AGING, "Aging Balance", "AR Weighted Age Days"),
    (OAC, "OAC Meeting", "OAC Weeks Missed"),
    (TRADE, "Trade Partner Meeting", "Trade Partner Weeks Missed"),
    (LOOKAHEAD, "3-Week Look-Ahead", "Days Since Look-Ahead Update"),
    (SCHED_UPDATE, "Monthly Schedule Update", "Days Since Schedule Update"),
    (COMPLETION, "Completion Variance", "Completion Variance %"),
    (SUBMITTALS, "Submittals", "Submittals Overdue"),
    (RFIS, "RFIs", "RFIs Outstanding"),
    (SAFETY_INSP, "Safety Inspections", "Safety Inspections (Week)"),
    (QUALITY_INSP, "Quality Inspections", "Quality Inspections (Week)"),
]


def score_name(name: str) -> str:
    return f"Metric Score - {name}"


def metric_score(key: int) -> str:
    """The metric's score for the selected week, from fct_MetricScore (47_dashboard_score.sql).
    Scoring runs at build time: as DAX, the Portfolio table's pills re-scored every pillar from
    twelve band lookups per project and ran out of F2 query memory (2026-10-25)."""
    return ("VAR W = [Report Weeks Ago]\n"
            "RETURN IF ( [Is Dashboard Project], CALCULATE ( MAX ( fct_MetricScore[Score] ),\n"
            f"    fct_MetricScore[MetricKey] = {key}, fct_MetricScore[WeeksAgo] = W ) )")


def project_score(column: str) -> str:
    """A fct_ProjectScore column (pillars, grade, coverage) for the selected week."""
    return ("VAR W = [Report Weeks Ago]\n"
            "RETURN IF ( [Is Dashboard Project], CALCULATE ( MAX ( fct_ProjectScore[" + column + "] ),\n"
            "    fct_ProjectScore[WeeksAgo] = W ) )")


def row_metric(column: str) -> str:
    """A fct_MetricScore column for the dim_DashMetric row in context (Grade Detail, Top Risks)."""
    return ("VAR K = SELECTEDVALUE ( dim_DashMetric[MetricKey] )\n"
            "VAR W = [Report Weeks Ago]\n"
            "RETURN IF ( [Is Dashboard Project] && NOT ISBLANK ( K ), CALCULATE ( MAX ( fct_MetricScore[" + column + "] ),\n"
            "    fct_MetricScore[MetricKey] = K, fct_MetricScore[WeeksAgo] = W ) )")


def colour_for(score: str, scale: str = "1") -> str:
    """Pill fill for a 0-1 (or 0-100, scale "100") score, on the grade's own cut-offs."""
    return (
        f"VAR S = {score}\n"
        f"RETURN SWITCH ( TRUE (), ISBLANK ( S ), \"{MIST}\",\n"
        f"    S >= {setting('grade_on_track_from')} / 100 * {scale}, \"{GREEN}\",\n"
        f"    S >= {setting('grade_monitor_from')} / 100 * {scale}, \"{AMBER}\",\n"
        f"    \"{RED}\" )"
    )


def ink_for(score: str, scale: str = "1") -> str:
    """Pill text: white on green and red, navy on amber and on the empty grey."""
    return (
        f"VAR S = {score}\n"
        f"RETURN IF ( NOT ISBLANK ( S ) && ( S >= {setting('grade_on_track_from')} / 100 * {scale}"
        f" || S < {setting('grade_monitor_from')} / 100 * {scale} ), \"#FFFFFF\", \"{NAVY}\" )"
    )


def meetings_missed(kind: str) -> str:
    """Weeks of the rolling four ending with the report week with no meeting of this kind
    that met the standard (fct_Meeting[IsCompliant]). Precon and construction only - the
    band gate applies that - so a missing series in either IS the miss."""
    return (
        "VAR E = [Report Week End]\n"
        "VAR Weeks = SELECTCOLUMNS ( GENERATESERIES ( 0, 3, 1 ), \"@k\", [Value] )\n"
        "VAR Held = COUNTROWS ( FILTER ( Weeks,\n"
        "    VAR Hi = E - 7 * [@k]\n"
        "    VAR Lo = Hi - 6\n"
        "    RETURN NOT ISEMPTY ( FILTER ( fct_Meeting,\n"
        f"        fct_Meeting[MeetingType] = \"{kind}\" && fct_Meeting[IsCompliant]\n"
        "            && fct_Meeting[MeetingDate] >= Lo && fct_Meeting[MeetingDate] <= Hi ) ) ) )\n"
        # This week is still running: it counts once a meeting is held, never as a miss.
        "VAR HeldNow = NOT ISEMPTY ( FILTER ( fct_Meeting,\n"
        f"        fct_Meeting[MeetingType] = \"{kind}\" && fct_Meeting[IsCompliant]\n"
        "            && fct_Meeting[MeetingDate] >= E - 6 && fct_Meeting[MeetingDate] <= E ) )\n"
        "VAR Open = IF ( [Report Weeks Ago] = 0 && NOT HeldNow, 1, 0 )\n"
        "RETURN IF ( [Is Dashboard Project], 4 - COALESCE ( Held, 0 ) - Open )"
    )


def inspections(category: str) -> str:
    return (
        "VAR E = [Report Window End]\n"
        "VAR S = [Report Week End] - 6\n"
        "RETURN IF ( [Is Dashboard Project], COALESCE ( CALCULATE ( COUNTROWS ( fct_Inspection ),\n"
        f"    fct_Inspection[Category] = \"{category}\", fct_Inspection[IsPerformed] = TRUE (),\n"
        "    fct_Inspection[InspectionDate] >= S, fct_Inspection[InspectionDate] <= E ), 0 ) )"
    )


def count_active(condition: str) -> str:
    """Active dashboard projects meeting a condition on their own measures. 0, not BLANK:
    "0 on track" is a real count, and a card would otherwise read "(Blank)"."""
    # [@g] in a condition is the project's grade, computed once per project.
    active = 'FILTER ( VALUES ( dim_Project[ProjectKey] ), [Dashboard Status] = "Active" )'
    if "[@g]" in condition:
        active = f'ADDCOLUMNS ( {active}, "@g", [Grade] )'
    return f"COALESCE ( COUNTROWS ( FILTER ( {active},\n    {condition} ) ), 0 )"


def over_active(expression: str) -> str:
    return ("SUMX ( FILTER ( VALUES ( dim_Project[ProjectKey] ), [Dashboard Status] = \"Active\" ),\n"
            f"    {expression} )")


def money_text(m: str) -> str:
    """$12.6M / $317K / $950 - the deck's own rounding for tile values."""
    return (f"VAR X = {m}\n"
            "RETURN IF ( ISBLANK ( X ), BLANK (), SWITCH ( TRUE (),\n"
            "    ABS ( X ) >= 1000000, FORMAT ( X / 1000000, \"$#,0.0\" ) & \"M\",\n"
            "    ABS ( X ) >= 1000, FORMAT ( X / 1000, \"$#,0\" ) & \"K\",\n"
            "    FORMAT ( X, \"$#,0\" ) ) )")


def measures() -> list[tuple[str, str, str | None, str]]:
    weights = {k: pillar_weight(k) for k, _ in PILLARS}
    out: list[tuple[str, str, str | None, str]] = [
        # ---- the reporting week ------------------------------------------------
        ("Report Week End",
         # No single week picked (or several) = last week, the stand-up default.
         "VAR Picked = IF ( HASONEVALUE ( dim_ReportWeek[WeekEnd] ), VALUES ( dim_ReportWeek[WeekEnd] ) )\n"
         "RETURN IF ( ISBLANK ( Picked ),\n"
         "    CALCULATE ( MAX ( dim_ReportWeek[WeekEnd] ), REMOVEFILTERS ( dim_ReportWeek ), dim_ReportWeek[WeeksAgo] = 1 ),\n"
         "    Picked )",
         '"yyyy-mm-dd"', "deck slide 3 - the time-window selection box, defaulting to current"),
        ("Data As Of",
         "CALCULATE ( MAX ( dim_ReportWeek[AsOfDate] ), REMOVEFILTERS ( dim_ReportWeek ) )",
         '"yyyy-mm-dd"', "the gold build date; today's balances are as of this day"),
        ("Report Window End",
         # This week stops today, not at a Sunday still to come.
         "MIN ( [Report Week End], [Data As Of] )", '"yyyy-mm-dd"', "derived"),
        ("Report Weeks Ago",
         "IF ( HASONEVALUE ( dim_ReportWeek[WeeksAgo] ), VALUES ( dim_ReportWeek[WeeksAgo] ), 1 )",
         '"0"', "derived"),
        ("Report Week Label",
         "VAR E = [Report Week End]\n"
         "VAR S = E - 6\n"
         "VAR W = [Report Weeks Ago]\n"
         "RETURN SWITCH ( W, 0, \"This week\", 1, \"Last week\", \"Week\" ) & \"  \"\n"
         "    & FORMAT ( S, \"mmm d\" ) & \" - \" & FORMAT ( E, \"mmm d, yyyy\" )",
         None, "deck header - the week the page reports"),

        # ---- which projects --------------------------------------------------
        ("Is Dashboard Project",
         'VAR K = SELECTEDVALUE ( dim_Project[ProjectKey] )\n'
         'RETURN NOT ISBLANK ( K ) && K <> "UNMATCHED"',
         None, "derived - one real project in context"),
        # ---- where each project stands: fct_ProjectPosition, worked out once per build ----
        # Contract, billing, cash inputs, margin, ageing and activity do not move with the
        # report week, and as DAX they were re-derived many times per grade - the Portfolio
        # table's query ran out of F2 memory (2026-10-25). validate_dashboard recomputes each
        # from the raw facts and compares.
        ("Position Contract", "SUM ( fct_ProjectPosition[CurrentContract] )", '"$#,0"',
         "the current contract as of the build - the latest month with a value"),
        ("Billed To Date (Gross)",
         # Procore owner pay apps first: they are GROSS of retainage. Sage AR invoices are NET
         # (SaunaLounge: Sage billed = Procore earned-less-retainage to the cent, 2026-10-25),
         # so Sage is used only where a project has no owner pay app - with no retainage to
         # take off, because none was added.
         "SUM ( fct_ProjectPosition[BilledToDateGross] )",
         '"$#,0"', "deck slide 3 BILLED TO DATE - Procore owner pay apps (gross), else Sage AR"),
        ("Billed % Of Contract",
         "DIVIDE ( [Billed To Date (Gross)], [Position Contract] )", '"0.0%"',
         "deck slide 3 BILLING PROGRESS; slide 2 'Determine phase based on Billed %'"),
        ("Project Phase",
         "VAR B = [Billed % Of Contract]\n"
         f"RETURN IF ( NOT ISBLANK ( B ), SWITCH ( TRUE (), B < {setting('phase_precon_below')}, \"Precon\",\n"
         f"    B > {setting('phase_closeout_from')}, \"Closeout\", \"Construction\" ) )",
         None, "deck slide 2: <10% Precon, 10-95% Construction, >95% Closeout"),
        ("Phase Label", 'COALESCE ( [Project Phase], "Not supplied" )', None,
         "deck slide 2 CURRENT PHASE"),
        ("Last Project Activity",
         # The latest sign of a working project in any Procore tool - a daily log alone
         # missed City Harvest, which logs nothing but holds weekly OAC meetings.
         "MAX ( fct_ProjectPosition[LastActivityDate] )",
         '"yyyy-mm-dd"', "derived - latest daily log, meeting, inspection, RFI/submittal or observation"),
        ("Dashboard Status",
         # Archived once 100% paid (the Oct 21 call). Inactive = no Procore activity in the
         # window (PROPOSED 60 days) - listed on the Portfolio page but not counted.
         "VAR K = SELECTEDVALUE ( dim_Project[ProjectKey] )\n"
         'RETURN IF ( NOT ISBLANK ( K ) && K <> "UNMATCHED", SELECTEDVALUE ( fct_ProjectPosition[DashboardStatus] ) )',
         None, "Oct 21 call: archived once 100% paid; Active = recent Procore activity (proposed 60 days)"),

        # ---- Budget: cash position (Chris's formula, 2026-10-22) -----------------
        ("Cash - Billings To Date", "[Billed To Date (Gross)]", '"$#,0"',
         "Cash Position formula: Billings to Date"),
        ("Cash - Retainage Receivable", "SUM ( fct_ProjectPosition[RetainageReceivable] )", '"$#,0"',
         "Cash Position formula: Retainage Receivable (Procore owner pay apps)"),
        ("Cash - Unpaid Receivables", "SUM ( fct_ProjectPosition[UnpaidReceivables] )", '"$#,0"',
         "Cash Position formula: Unpaid Receivables (billed, not collected - Sage AR)"),
        ("Cash - Costs Incurred", "SUM ( fct_ProjectPosition[CostsIncurred] )", '"$#,0"',
         "Cash Position formula: Costs Incurred (Procore job-to-date cost)"),
        # Sage AP balance on job-cost lines, each line's share of its invoice's balance.
        ("Cash - Unpaid Payables", "SUM ( fct_ProjectPosition[UnpaidPayables] )", '"$#,0"',
         "Cash Position formula: Unpaid Payables (Sage AP job cost)"),
        ("Cash - Retainage Payable", "SUM ( fct_ProjectPosition[RetainagePayable] )", '"$#,0"',
         "Cash Position formula: Retainage Payable to Subs (Procore requisitions)"),
        ("Cash Collected",
         "VAR B = [Cash - Billings To Date]\n"
         "RETURN IF ( NOT ISBLANK ( B ), B - [Cash - Retainage Receivable] - [Cash - Unpaid Receivables] )",
         '"$#,0"', "Cash Position formula, inflow half"),
        ("Cash Paid Out",
         "VAR C = [Cash - Costs Incurred]\n"
         "RETURN IF ( NOT ISBLANK ( C ), C - [Cash - Unpaid Payables] - [Cash - Retainage Payable] )",
         '"$#,0"', "Cash Position formula, outflow half"),
        ("Cash Position",
         "VAR I = [Cash Collected]\nVAR O = [Cash Paid Out]\n"
         "RETURN IF ( NOT ISBLANK ( I ) && NOT ISBLANK ( O ), I - O )",
         '"$#,0"', "Cash Position = Billings - Retainage Receivable - Unpaid Receivables - "
                   "(Costs Incurred - Unpaid Payables - Retainage Payable) - Chris, 2026-10-22"),
        ("Cash Collected / Paid",
         # The ratio Scorecard.xlsx bands (>= 100% / 90-100% / < 90%). Nothing paid out yet
         # but cash in hand is cash positive: 100%.
         "VAR I = [Cash Collected]\nVAR O = [Cash Paid Out]\n"
         "RETURN IF ( O > 0, DIVIDE ( I, O ), IF ( NOT ISBLANK ( I ) && NOT ISBLANK ( O ) && I >= 0, 1 ) )",
         '"0%"', "Scorecard.xlsx Cash Position % - collected over paid"),

        # ---- Budget: profitability ---------------------------------------------
        ("Projected Revenue", "SUM ( fct_ProjectPosition[ProjectedRevenue] )", '"$#,0"',
         "Procore revised budget, which carries the CM fee and so equals contract revenue"),
        # Every forecast line except the FEE division (new cost-code master, division 50):
        # Affect's budgets include the CM fee as a line, so budget = revenue and the fee is
        # the margin, not a cost.
        ("Projected Cost", "SUM ( fct_ProjectPosition[ProjectedCost] )", '"$#,0"',
         "Procore forecast final cost, CM fee excluded"),
        ("Projected Gross Margin %",
         # No forecast cost = no margin (R - BLANK would read as 100%).
         "VAR R = [Projected Revenue]\nVAR C = [Projected Cost]\nRETURN IF ( R > 0 && NOT ISBLANK ( C ), DIVIDE ( R - C, R ) )",
         '"0.0%"', "Scorecard.xlsx Profitability (Gross) - DEFINITION TO CONFIRM with Affect"),
        ("Gross Margin Target", setting("gross_margin_target"), '"0.0%"',
         "Oct 21 call: 12.5%, 13% from the end of Q1 - dim_DashSetting"),
        ("Margin vs Target",
         "VAR M = [Projected Gross Margin %]\nRETURN IF ( NOT ISBLANK ( M ), M - [Gross Margin Target] )",
         '"+0.0%;-0.0%;0.0%"', "derived - points above (+) or below (-) target"),

        # ---- Budget: aging ----------------------------------------------------
        ("AR Weighted Age Days",
         # Average age of what is still owed, weighted by the amount owed. 0 when every
         # invoice is paid; BLANK when the project has never billed in Sage.
         "VAR Bal = SUM ( fct_ProjectPosition[ArOwedBalance] )\n"
         "RETURN IF ( Bal > 0, DIVIDE ( SUM ( fct_ProjectPosition[ArOwedBalanceDays] ), Bal ),\n"
         "    IF ( SUM ( fct_ProjectPosition[InvoiceCount] ) > 0, 0 ) )",
         '"#,0"', "Scorecard.xlsx Aging Balance - days, balance-weighted"),
        ("AR Over 60 Days",
         "VAR AsOf = [Data As Of]\n"
         "RETURN COALESCE ( SUMX ( FILTER ( CALCULATETABLE ( fct_Invoice, REMOVEFILTERS ( dim_Date ) ),\n"
         f"    fct_Invoice[Balance] > 0 && DATEDIFF ( fct_Invoice[SentDate], AsOf, DAY ) > {setting('ar_aged_days')} ),\n"
         "    fct_Invoice[Balance] ), 0 )",
         '"$#,0"', "deck slide 1 AR > 60 DAYS - every invoice, matched to a project or not"),

        # ---- Schedule (Field Ops) ------------------------------------------------
        ("OAC Weeks Missed", meetings_missed("OAC"), '"0"',
         "Scorecard.xlsx OAC Meeting - misses, rolling 4 weeks"),
        ("Trade Partner Weeks Missed", meetings_missed("Trade Partner"), '"0"',
         "Scorecard.xlsx Trade Partner Meeting - misses, rolling 4 weeks"),
        ("Days Since Look-Ahead Update",
         # Current state only: Outbuild keeps no history, so a past week cannot be checked.
         # 999 = linked to Outbuild but no look-ahead tasks at all. BLANK = not linked.
         "VAR Linked = NOT ISEMPTY ( fct_ScheduleActivity )\n"
         "VAR L = MAXX ( { MAX ( fct_LookaheadTask[UpdatedAt] ), MAX ( fct_LookaheadTask[CreatedAt] ) }, [Value] )\n"
         "RETURN IF ( [Is Dashboard Project] && Linked && [Report Weeks Ago] <= 1,\n"
         "    IF ( ISBLANK ( L ), 999, DATEDIFF ( L, [Data As Of], DAY ) ) )",
         '"0"', "Scorecard.xlsx 3WLA going out once per week - days since the Outbuild look-ahead was worked"),
        ("Days Since Schedule Update",
         "VAR L = MAX ( fct_ScheduleActivity[UpdatedAt] )\n"
         "RETURN IF ( [Is Dashboard Project] && NOT ISBLANK ( L ) && [Report Weeks Ago] <= 1,\n"
         "    DATEDIFF ( L, [Data As Of], DAY ) )",
         '"0"', "Scorecard.xlsx Monthly schedule update - days since an activity was last edited"),
        ("Baseline Duration Days",
         "CALCULATE ( VAR S = MIN ( fct_Milestone[BaselineStart] ) VAR F = MAX ( fct_Milestone[BaselineFinish] )\n"
         "    RETURN IF ( NOT ISBLANK ( S ) && F > S, DATEDIFF ( S, F, DAY ) ), REMOVEFILTERS ( dim_Date ) )",
         '"#,0"', "derived - first baseline start to last baseline finish on the critical path"),
        ("Completion Variance %",
         "DIVIDE ( [Completion Variance Days], [Baseline Duration Days] )", '"0.0%"',
         "Scorecard.xlsx Completion variance - days late over the baseline duration"),
        ("Submittals Overdue",
         # BLANK for a project with no submittals at all: nothing to be late is not "on target".
         "VAR Any = CALCULATE ( COUNTROWS ( fct_RfiSubmittal ), REMOVEFILTERS ( dim_Date ), fct_RfiSubmittal[ItemType] = \"Submittal\" )\n"
         "RETURN IF ( [Is Dashboard Project] && Any > 0,\n"
         "    COALESCE ( CALCULATE ( [Open Submittals Past Due], REMOVEFILTERS ( dim_Date ) ), 0 ) )",
         '"#,0"', "Scorecard.xlsx Submittals - overdue count, today"),
        ("RFIs Outstanding",
         # Open past the due date; an RFI with no due date counts once it is a week old -
         # the call's "outstanding or unclosed RFIs past seven".
         "VAR Any = CALCULATE ( COUNTROWS ( fct_RfiSubmittal ), REMOVEFILTERS ( dim_Date ), fct_RfiSubmittal[ItemType] = \"RFI\" )\n"
         # The rows are taken with dates removed FIRST. A FILTER over the bare fact is a filter
         # argument, evaluated in the outer context before REMOVEFILTERS applies, so under a
         # month it counted only that month's RFIs (found by validate_dashboard, 2026-10-25).
         "RETURN IF ( [Is Dashboard Project] && Any > 0, COALESCE ( COUNTROWS (\n"
         "    FILTER ( CALCULATETABLE ( fct_RfiSubmittal, REMOVEFILTERS ( dim_Date ) ),\n"
         "        fct_RfiSubmittal[ItemType] = \"RFI\" && fct_RfiSubmittal[IsOpen]\n"
         "        && ( fct_RfiSubmittal[IsPastDue] || ( ISBLANK ( fct_RfiSubmittal[DueDate] ) && fct_RfiSubmittal[DaysOpen] > 7 ) ) ) ), 0 ) )",
         '"#,0"', "Scorecard.xlsx RFIs - outstanding count, today"),

        # ---- Safety / Quality --------------------------------------------------
        ("Safety Inspections (Week)", inspections("Safety"), '"#,0"',
         "Scorecard.xlsx Safety Inspections - performed in the report week"),
        ("Quality Inspections (Week)", inspections("Quality"), '"#,0"',
         "Scorecard.xlsx Quality Inspections - performed in the report week"),
        ("Unclassified Inspections",
         'COALESCE ( CALCULATE ( COUNTROWS ( fct_Inspection ), fct_Inspection[Category] = "Unclassified" ), 0 )',
         '"#,0"', "data check - templates no seed_InspectionCategory pattern matches"),
    ]

    # ---- one score per metric: looked up, scored at build time -------------------
    out += [(score_name(n), metric_score(k), '"0%"', f"Scorecard.xlsx {n} - fct_MetricScore (dim_DashBand)")
            for k, n, _ in METRICS]

    # ---- per-metric rows, for the grade-detail and top-risk tables ----------------
    out += [
        ("Metric Score", row_metric("Score"), '"0%"', "derived - the score of the dim_DashMetric row in context"),
        ("Metric Driver", row_metric("Driver"), '"0.00"', "derived - the number the row's band scores"),
        ("Metric Reading",
         # The driver in words, so a reader sees WHY a measure scored what it did.
         "VAR K = SELECTEDVALUE ( dim_DashMetric[MetricKey] )\n"
         "VAR V = [Metric Driver]\n"
         "RETURN IF ( NOT ISBLANK ( V ), SWITCH ( K,\n"
         f"    {CASH}, FORMAT ( V, \"0%\" ) & \" collected vs paid (\" & {money_text('[Cash Position]').replace(chr(10), ' ')} & \")\",\n"
         f"    {PROFIT}, FORMAT ( [Projected Gross Margin %], \"0.0%\" ) & \" projected margin, \" & FORMAT ( V * 100, \"+0.0;-0.0;0.0\" ) & \" pts vs target\",\n"
         f"    {AGING}, FORMAT ( V, \"0\" ) & \" days average age of unpaid AR\",\n"
         f"    {OAC}, ( 4 - V ) & \" of 4 weeks met the standard\",\n"
         f"    {TRADE}, ( 4 - V ) & \" of 4 weeks met the standard\",\n"
         f"    {LOOKAHEAD}, IF ( V >= 999, \"No look-ahead tasks in Outbuild\", \"Last worked \" & V & \" days ago\" ),\n"
         f"    {SCHED_UPDATE}, \"Last edited \" & V & \" days ago\",\n"
         f"    {COMPLETION}, FORMAT ( [Completion Variance Days], \"0;-0;0\" ) & \" days vs baseline (\" & FORMAT ( V, \"0%\" ) & \" of duration)\",\n"
         f"    {SUBMITTALS}, V & \" overdue\",\n"
         f"    {RFIS}, V & \" outstanding\",\n"
         f"    {SAFETY_INSP}, V & \" performed (target 5)\",\n"
         f"    {QUALITY_INSP}, V & \" performed (target 5)\" ) )",
         None, "derived - the driver, in words"),
        ("Metric Band", row_metric("BandLabel"), None, "derived - the Scorecard.xlsx band the reading fell in"),
        ("Metric State",
         # Why a row has no score - the honest version of a blank cell.
         "VAR St = SELECTEDVALUE ( dim_DashMetric[Status] )\n"
         "VAR Stg = SELECTEDVALUE ( dim_DashMetric[Stages] )\n"
         "VAR Ph = [Project Phase]\n"
         "RETURN SWITCH ( TRUE (),\n"
         "    St <> \"Live\", \"Coming soon\",\n"
         "    NOT ISBLANK ( [Metric Score] ), [Metric Band],\n"
         "    Stg <> \"All\" && ( ISBLANK ( Ph ) || NOT CONTAINSSTRING ( Stg, Ph ) ),\n"
         "        \"Not scored at \" & COALESCE ( Ph, \"unknown\" ) & \" phase\",\n"
         "    \"Not measured - no data\" )",
         None, "derived - band, or why the measure is not scored"),
        ("Metric Weight In Grade",
         # Equal shares of the pillar weight among the pillar's measured metrics.
         "VAR P = SELECTEDVALUE ( dim_DashMetric[PillarKey] )\n"
         "VAR W = [Report Weeks Ago]\n"
         "VAR N = CALCULATE ( COUNTROWS ( fct_MetricScore ), fct_MetricScore[PillarKey] = P,\n"
         "    fct_MetricScore[WeeksAgo] = W, NOT ISBLANK ( fct_MetricScore[Score] ) )\n"
         "VAR Wt = CALCULATE ( MAX ( dim_DashPillar[Weight] ), REMOVEFILTERS ( dim_DashPillar ), dim_DashPillar[PillarKey] = P )\n"
         "RETURN IF ( NOT ISBLANK ( [Metric Score] ) && NOT ISBLANK ( [Grade] ) && N > 0, DIVIDE ( DIVIDE ( Wt, N ), [Grade Coverage %] ) )",
         '"0.0%"', "derived - share of the grade this measure carries"),
        ("Is Top Risk",
         f"VAR S = [Metric Score]\nRETURN IF ( NOT ISBLANK ( S ) && S < {setting('risk_metric_below')}, \"Yes\" )",
         None, "Oct 21 call: a measure below 80% is a top risk"),
        ("Risk Severity",
         f"VAR S = [Metric Score]\nRETURN IF ( NOT ISBLANK ( S ) && S < {setting('risk_metric_below')},\n"
         f"    IF ( S < {setting('risk_high_below')}, \"HIGH\", \"MED\" ) )",
         None, "derived - HIGH below 50% (proposed), MED below 80%"),
        ("Risk Severity Colour",
         f'IF ( [Risk Severity] = "HIGH", "#F6DADA", IF ( [Risk Severity] = "MED", "#FFF0CF" ) )',
         None, "deck slide 3 pill fills"),
        ("Risk Severity Ink",
         f'IF ( [Risk Severity] = "HIGH", "{RED}", IF ( [Risk Severity] = "MED", "#986319" ) )',
         None, "deck slide 3 pill text"),
        ("Measures Below Target", project_score("MeasuresBelowTarget"), '"0"',
         "Oct 21 call: the grade, and how many things the project failed"),
        ("Executive Focus",
         "VAR W = [Report Weeks Ago]\n"
         "VAR T = ADDCOLUMNS ( ALL ( dim_DashMetric ), \"@S\", VAR K = dim_DashMetric[MetricKey]\n"
         "    RETURN CALCULATE ( MAX ( fct_MetricScore[Score] ), fct_MetricScore[MetricKey] = K, fct_MetricScore[WeeksAgo] = W ) )\n"
         f"VAR R = TOPN ( 3, FILTER ( T, NOT ISBLANK ( [@S] ) && [@S] < {setting('risk_metric_below')} ), [@S], ASC, dim_DashMetric[MetricKey], ASC )\n"
         "RETURN IF ( [Is Dashboard Project], \"EXECUTIVE FOCUS:  \" & IF ( ISEMPTY ( R ), \"Every measured standard is on target\",\n"
         "    CONCATENATEX ( R, dim_DashMetric[Metric], \"  \" & UNICHAR ( 8226 ) & \"  \", [@S], ASC ) ) )",
         None, "deck slide 3 EXECUTIVE FOCUS - the three weakest measures"),
    ]

    # ---- pillars and the grade: fct_ProjectScore -------------------------------------
    out += [(f"{name} Pillar", project_score(f"{name}Pillar"), '"0%"',
             f"Scorecard.xlsx {name} - equal-weighted average of its measured metrics (fct_ProjectScore)")
            for k, name in PILLARS]
    out += [
        ("Grade Coverage %", project_score("GradeCoverage"), '"0%"', "derived - share of the pillar weight that is measured"),
        ("Grade", project_score("Grade"), '"0"',
         "deck slide 2 GRADE - schedule 50, budget 30, safety 15, quality 5 (Oct 21 call); fct_ProjectScore"),
        ("Grade Status",
         "VAR G = [Grade]\n"
         "RETURN IF ( [Is Dashboard Project], SWITCH ( TRUE (), ISBLANK ( G ), \"Unscored\",\n"
         f"    G >= {setting('grade_on_track_from')}, \"On track\",\n"
         f"    G >= {setting('grade_monitor_from')}, \"Monitor\", \"Needs attention\" ) )",
         None, "deck slide 2: On track / Monitor / Needs attention / Unscored"),
        ("Grade Colour", colour_for("[Grade]", "100"), None, "deck slide 2 grade pill"),
        ("Grade Ink", ink_for("[Grade]", "100"), None, "deck slide 2 grade pill text"),
        ("Grade Cell",
         "VAR G = [Grade]\nRETURN IF ( [Is Dashboard Project], IF ( ISBLANK ( G ), UNICHAR ( 8212 ), FORMAT ( G, \"0\" ) ) )",
         None, "deck slide 2 GRADE cell"),
        ("Weakest Pillar", project_score("WeakestPillar"), None, "derived - the pillar costing the grade most"),
    ]
    # Pill cells for the Portfolio table: the headline reading and the pillar score, coloured
    # by that score - the colour always matches the number printed in the cell.
    cells = {
        "Schedule": "VAR D = [Completion Variance Days]\n"
                    "VAR H = IF ( NOT ISBLANK ( D ), FORMAT ( -D, \"+0;-0;0\" ) & \" days\" )",
        "Budget": "VAR M = [Margin vs Target]\n"
                  "VAR H = IF ( NOT ISBLANK ( M ), FORMAT ( [Projected Gross Margin %], \"0.0%\" ) & \" GM\" )",
        "Safety": "VAR H = IF ( [Project Phase] = \"Construction\", [Safety Inspections (Week)] & \" insp\" )",
        "Quality": "VAR H = IF ( [Project Phase] = \"Construction\", [Quality Inspections (Week)] & \" insp\" )",
    }
    for k, n in PILLARS:
        out += [
            (f"{n} Cell",
             cells[n] + f"\nVAR S = [{n} Pillar]\n"
             "RETURN IF ( [Is Dashboard Project], SWITCH ( TRUE (),\n"
             "    ISBLANK ( S ), COALESCE ( H, UNICHAR ( 8212 ) ),\n"
             "    ISBLANK ( H ), FORMAT ( S, \"0%\" ),\n"
             "    H & \"  \" & UNICHAR ( 183 ) & \"  \" & FORMAT ( S, \"0%\" ) ) )",
             None, f"deck slide 2 {n.upper()} cell - headline reading and pillar score"),
            (f"{n} Colour", colour_for(f"[{n} Pillar]"), None, f"deck slide 2 {n.upper()} pill"),
            (f"{n} Ink", ink_for(f"[{n} Pillar]"), None, f"deck slide 2 {n.upper()} pill text"),
        ]

    out += [
        # ---- team -------------------------------------------------------------
        ("Team Initials",
         # "Initials of: PM, APM, Super, Asst Super from Procore" - in that order.
         "VAR T = SUMMARIZE ( FILTER ( fct_ProjectTeam, fct_ProjectTeam[RoleOrder] <= 4 ),\n"
         "    fct_ProjectTeam[RoleOrder], fct_ProjectTeam[MemberName] )\n"
         "VAR I = ADDCOLUMNS ( T, \"@i\",\n"
         # Procore appends the company - "Jane Doe (Affect)" - so cut it before initials.
         "    VAR Raw = fct_ProjectTeam[MemberName]\n"
         "    VAR Cut = SEARCH ( \" (\", Raw, 1, 0 )\n"
         "    VAR N = TRIM ( IF ( Cut > 0, LEFT ( Raw, Cut - 1 ), Raw ) )\n"
         "    VAR Sp = LEN ( N ) - LEN ( SUBSTITUTE ( N, \" \", \"\" ) )\n"
         "    VAR LastWord = IF ( Sp = 0, \"\", MID ( N, FIND ( \"~\", SUBSTITUTE ( N, \" \", \"~\", Sp ) ) + 1, 1 ) )\n"
         "    RETURN UPPER ( LEFT ( N, 1 ) & LastWord ) )\n"
         "RETURN IF ( [Is Dashboard Project], COALESCE ( CONCATENATEX ( I, [@i], \" \" & UNICHAR ( 183 ) & \" \", fct_ProjectTeam[RoleOrder], ASC, fct_ProjectTeam[MemberName], ASC ), UNICHAR ( 8212 ) ) )",
         None, "deck slide 2 TEAM - initials of PM, APM, Super, Asst Super from Procore"),
        ("Project Executive",
         'CONCATENATEX ( FILTER ( fct_ProjectTeam, fct_ProjectTeam[RoleCode] = "PX" ), VAR Cut = SEARCH ( " (", fct_ProjectTeam[MemberName], 1, 0 ) RETURN IF ( Cut > 0, LEFT ( fct_ProjectTeam[MemberName], Cut - 1 ), fct_ProjectTeam[MemberName] ), ", ", fct_ProjectTeam[MemberName], ASC )',
         None, "Oct 21 call: the one accountable name"),
        ("Project Team",
         "VAR T = CONCATENATEX ( FILTER ( fct_ProjectTeam, fct_ProjectTeam[RoleOrder] <= 4 ),\n"
         "    fct_ProjectTeam[RoleCode] & \" \" & ( VAR Cut = SEARCH ( \" (\", fct_ProjectTeam[MemberName], 1, 0 ) RETURN IF ( Cut > 0, LEFT ( fct_ProjectTeam[MemberName], Cut - 1 ), fct_ProjectTeam[MemberName] ) ), \"   \", fct_ProjectTeam[RoleOrder], ASC, fct_ProjectTeam[MemberName], ASC )\n"
         # The project executive first - "only one throat to choke" (Oct 21 call).
         "VAR X = [Project Executive]\n"
         "VAR A = IF ( NOT ISBLANK ( X ), \"PX \" & X & IF ( NOT ISBLANK ( T ), \"   \" ) ) & T\n"
         "RETURN IF ( [Is Dashboard Project], IF ( A = \"\", \"No PX / PM / Super roles set in Procore\", A ) )",
         None, "deck slide 2 TEAM, in full"),
    ]
    out += [
        # ---- project page ------------------------------------------------------
        ("Contract Change Text",
         "VAR D = [Current Contract] - [Original Contract]\n"
         "VAR A = ABS ( D )\n"
         "VAR T = SWITCH ( TRUE (), A >= 1000000, FORMAT ( A / 1000000, \"$#,0.0\" ) & \"M\",\n"
         "    A >= 1000, FORMAT ( A / 1000, \"$#,0\" ) & \"K\", FORMAT ( A, \"$#,0\" ) )\n"
         "RETURN IF ( NOT ISBLANK ( [Original Contract] ), IF ( D >= 0, \"+\", \"-\" ) & T & \" vs original\" )",
         None, "deck slide 3 CURRENT CONTRACT sub-line"),
    ]
    out += [
        ("Work Progress %",
         # Duration-weighted Outbuild progress over the current schedule's real activities.
         "VAR T = FILTER ( fct_ScheduleActivity, NOT fct_ScheduleActivity[IsSummary] && fct_ScheduleActivity[DurationDays] > 0 )\n"
         "RETURN DIVIDE ( SUMX ( T, fct_ScheduleActivity[DurationDays] * COALESCE ( fct_ScheduleActivity[PercentComplete], 0 ) ),\n"
         "    SUMX ( T, fct_ScheduleActivity[DurationDays] ) )",
         '"0%"', "deck slide 3 PROJECT COMPLETE - Outbuild, duration-weighted"),
        ("Tracking Finish",
         "CALCULATE ( MAX ( fct_Milestone[BaselineFinish] ), REMOVEFILTERS ( dim_Date ) )",
         '"mmm d, yyyy"', "deck slide 3 TRACKING FINISH - the baseline finish"),
        ("Forecast Finish", "[Scheduled Finish]", '"mmm d, yyyy"',
         "deck slide 3 ACTUAL FINISH FORECAST - the current critical-path finish"),
        # Card text: a card prints BLANK as "(Blank)", so say what is missing instead.
        ("Work Progress Shown",
         'IF ( [Is Dashboard Project], VAR V = [Work Progress %] RETURN IF ( ISBLANK ( V ), "No schedule", FORMAT ( V, "0%" ) ) )',
         None, "card text for Work Progress %"),
        ("Tracking Finish Shown",
         'IF ( [Is Dashboard Project], VAR V = [Tracking Finish] RETURN IF ( ISBLANK ( V ), "No baseline", FORMAT ( V, "mmm d, yyyy" ) ) )',
         None, "card text for Tracking Finish"),
        ("Forecast Finish Shown",
         'IF ( [Is Dashboard Project], VAR V = [Forecast Finish] RETURN IF ( ISBLANK ( V ), "No forecast", FORMAT ( V, "mmm d, yyyy" ) ) )',
         None, "card text for Forecast Finish"),
        ("Schedule Headline",
         "VAR D = [Completion Variance Days]\n"
         "RETURN SWITCH ( TRUE (), ISBLANK ( D ), \"No baseline\",\n"
         "    D = 0, \"On baseline\", ABS ( D ) & IF ( ABS ( D ) = 1, \" DAY\", \" DAYS\" ) )",
         None, "deck slide 3 SCHEDULE tile"),
        ("Schedule Subline",
         "VAR D = [Completion Variance Days]\n"
         "RETURN SWITCH ( TRUE (), ISBLANK ( D ), \"Outbuild baseline needed\", D > 0, \"Past tracking finish\",\n"
         "    D < 0, \"Ahead of tracking finish\", \"Forecast = tracking finish\" )",
         None, "deck slide 3 SCHEDULE sub-line"),
        ("Schedule Tile Colour",
         f"VAR D = [Completion Variance Days]\nRETURN SWITCH ( TRUE (), ISBLANK ( D ), \"{MIST}\", D <= 0, \"{GREEN}\", D <= 7, \"{AMBER}\", \"{RED}\" )",
         None, "deck slide 3 tile accent"),
        ("Grade Text",
         'VAR G = [Grade]\nRETURN IF ( ISBLANK ( G ), "Unscored", FORMAT ( G / 100, "0%" ) )',
         None, "deck slide 3 PROJECT SCORECARD tile"),
        ("Grade Subline",
         'IF ( ISBLANK ( [Grade] ), "Under " & FORMAT ( ' + setting("min_coverage") + ', "0%" ) & " of the weight measured",\n'
         '    [Grade Status] & "  " & UNICHAR ( 183 ) & "  " & [Measures Below Target] & " below target" )',
         None, "deck slide 3 PROJECT SCORECARD sub-line"),
        ("Billing Ahead Of Work Pts",
         # Oct 21 call: "you've billed almost a third - are you really a third of the way done?"
         "VAR B = [Billed % Of Contract]\n"
         "VAR P = [Work Progress %]\n"
         "RETURN IF ( NOT ISBLANK ( B ) && NOT ISBLANK ( P ), ( B - P ) * 100 )",
         '"+0;-0;0"', "derived - billed % less Outbuild work progress %, in points"),
        ("Billed Subline",
         "VAR G = [Billing Ahead Of Work Pts]\n"
         'RETURN FORMAT ( [Billed % Of Contract], "0.0%" ) & " of contract" & SWITCH ( TRUE (),\n'
         '    ISBLANK ( G ), "",\n'
         '    G >= 1, "  " & UNICHAR ( 8226 ) & "  billed " & FORMAT ( G, "0" ) & " pts ahead of work",\n'
         '    G <= -1, "  " & UNICHAR ( 8226 ) & "  work " & FORMAT ( -G, "0" ) & " pts ahead of billing",\n'
         '    "  " & UNICHAR ( 8226 ) & "  in line with work" )', None,
         "deck slide 3 BILLED TO DATE sub-line, with the billing-vs-progress gap"),
        ("Paid To Date",
         "SUM ( fct_ProjectPosition[PaidToDate] )",
         '"$#,0"', "deck slide 3 PAID TO DATE - Sage receipts"),
        ("Remaining Contract Balance",
         "VAR C = [Position Contract]\nRETURN IF ( NOT ISBLANK ( C ), C - [Billed To Date (Gross)] )",
         '"$#,0"', "deck slide 3 REMAINING CONTRACT BALANCE"),
        ("Financial Exceptions",
         # deck slide 3 "Cash / forecasting exceptions require review" - said only when true.
         "VAR CP = [Cash Position]\n"
         "VAR Aged = CALCULATE ( [AR Over 60 Days], fct_Invoice[HasUnmatchedProject] <> TRUE () )\n"
         "VAR FV = [Forecast Variance]\n"
         "VAR L = FILTER ( {\n"
         "    ( 1, IF ( CP < 0, \"Cash negative: \" & FORMAT ( CP, \"$#,0\" ) ) ),\n"
         "    ( 2, IF ( Aged > 0, FORMAT ( Aged, \"$#,0\" ) & \" of AR over 60 days\" ) ),\n"
         "    ( 3, IF ( FV < 0, \"Forecast over budget by \" & FORMAT ( -FV, \"$#,0\" ) ) ),\n"
         "    ( 4, IF ( [Margin vs Target] < 0, \"Projected margin below target\" ) ) }, NOT ISBLANK ( [Value2] ) )\n"
         "RETURN IF ( [Is Dashboard Project], IF ( ISEMPTY ( L ), \"No cash or forecasting exceptions\",\n"
         "    CONCATENATEX ( L, [Value2], \"  \" & UNICHAR ( 8226 ) & \"  \", [Value1], ASC ) ) )",
         None, "deck slide 3 cash / forecasting exceptions"),
        ("Subcontract Budget",
         # Budget a subcontract can buy: every division before 45 (general conditions,
         # preconstruction, insurance, contingency, tax and fee are not bought out).
         "CALCULATE ( SUM ( fct_BudgetLine[BudgetAmount] ), REMOVEFILTERS ( dim_Date ),\n"
         "    FILTER ( ALL ( dim_CostCodeCrosswalk[NewDivisionCode] ), COALESCE ( dim_CostCodeCrosswalk[NewDivisionCode], \"00\" ) < \"45\" ) )",
         '"$#,0"', "derived - divisions 01-44 of the new cost-code master"),
        ("Subcontract Committed",
         "CALCULATE ( SUM ( fct_BudgetLine[CommittedAmount] ), REMOVEFILTERS ( dim_Date ),\n"
         "    FILTER ( ALL ( dim_CostCodeCrosswalk[NewDivisionCode] ), COALESCE ( dim_CostCodeCrosswalk[NewDivisionCode], \"00\" ) < \"45\" ) )",
         '"$#,0"', "derived"),
        ("Subcontractor Coverage %",
         "DIVIDE ( [Subcontract Committed], [Subcontract Budget] )", '"0%"',
         "deck slide 1 SUBCONTRACTOR COVERAGE / slide 3 RISK BOUGHT OUT - committed over buyable budget"),

        # ---- schedule lists (row flags for visual filters) ---------------------------
        ("Near Term Flag",
         # Starting or finishing in the next three weeks and not done - deck slide 3.
         "VAR A = [Data As Of]\n"
         f"VAR Z = A + {setting('lookahead_days')}\n"
         "VAR S = SELECTEDVALUE ( fct_ScheduleActivity[StartDate] )\n"
         "VAR F = SELECTEDVALUE ( fct_ScheduleActivity[FinishDate] )\n"
         "RETURN IF ( HASONEVALUE ( fct_ScheduleActivity[ActivityKey] )\n"
         "    && NOT SELECTEDVALUE ( fct_ScheduleActivity[IsSummary] ) && NOT SELECTEDVALUE ( fct_ScheduleActivity[IsComplete] )\n"
         "    && ( ( S >= A && S <= Z ) || ( F >= A && F <= Z ) ), \"Yes\" )",
         None, "deck slide 3 NEAR-TERM MILESTONES [Next 3 Weeks]"),
        ("Critical Near Term Flag",
         'IF ( [Near Term Flag] = "Yes" && SELECTEDVALUE ( fct_ScheduleActivity[IsCritical] ), "Yes" )',
         None, "deck slide 3 CRITICAL PATH [Next 3 Weeks]"),
        ("Activity Next Step",
         "VAR A = [Data As Of]\n"
         "VAR S = SELECTEDVALUE ( fct_ScheduleActivity[StartDate] )\n"
         "VAR F = SELECTEDVALUE ( fct_ScheduleActivity[FinishDate] )\n"
         "RETURN IF ( HASONEVALUE ( fct_ScheduleActivity[ActivityKey] ),\n"
         "    IF ( S > A, \"Starts \" & FORMAT ( S, \"mmm d\" ), \"Finish \" & FORMAT ( F, \"mmm d\" ) )\n"
         "    & IF ( SELECTEDVALUE ( fct_ScheduleActivity[FinishVarianceDays] ) > 0,\n"
         "        \"  \" & UNICHAR ( 183 ) & \"  \" & SELECTEDVALUE ( fct_ScheduleActivity[FinishVarianceDays] ) & \" days behind baseline\" ) )",
         None, "deck slide 3 milestone sub-line"),
        ("Behind Schedule Flag",
         # "Top three things behind on schedule" (Oct 21 call): open activities later than baseline.
         "IF ( HASONEVALUE ( fct_ScheduleActivity[ActivityKey] ) && NOT SELECTEDVALUE ( fct_ScheduleActivity[IsSummary] )\n"
         "    && NOT SELECTEDVALUE ( fct_ScheduleActivity[IsComplete] ) && SELECTEDVALUE ( fct_ScheduleActivity[FinishVarianceDays] ) > 0, \"Yes\" )",
         None, "deck slide 3 schedule pressure / critical path"),
        ("Days Behind Baseline", "MAX ( fct_ScheduleActivity[FinishVarianceDays] )", '"0"', "derived"),
        ("Recent Win Flag",
         "VAR E = [Report Window End]\nVAR S = [Report Week End] - 6\n"
         "VAR F = SELECTEDVALUE ( fct_ScheduleActivity[FinishDate] )\n"
         "RETURN IF ( HASONEVALUE ( fct_ScheduleActivity[ActivityKey] ) && SELECTEDVALUE ( fct_ScheduleActivity[IsComplete] )\n"
         "    && NOT SELECTEDVALUE ( fct_ScheduleActivity[IsSummary] ) && F >= S && F <= E, \"Yes\" )",
         None, "deck slide 3 RECENT WINS - completed in the report week"),
        ("Inspection In Week Flag",
         "VAR E = [Report Window End]\nVAR S = [Report Week End] - 6\n"
         "VAR D = SELECTEDVALUE ( fct_Inspection[InspectionDate] )\n"
         "RETURN IF ( HASONEVALUE ( fct_Inspection[InspectionKey] ) && SELECTEDVALUE ( fct_Inspection[IsPerformed] )\n"
         "    && D >= S && D <= E, \"Yes\" )",
         None, "deck slide 3 SAFETY / QUALITY lists - performed in the report week"),

        # ---- Executive page: the company --------------------------------------------
        ("Revenue YTD",
         "VAR A = [Data As Of]\n"
         "RETURN CALCULATE ( SUM ( fct_Invoice[Amount] ), REMOVEFILTERS ( dim_Date ), REMOVEFILTERS ( dim_Project ),\n"
         "    fct_Invoice[SentDate] >= DATE ( YEAR ( A ), 1, 1 ), fct_Invoice[SentDate] <= A )",
         '"$#,0"', "deck slide 1 REVENUE YTD - Sage AR invoiced this calendar year, every job"),
        ("Revenue Last 6 Months",
         # The deck's six-month chart. A month is in when it ends after the window opens.
         "VAR A = [Data As Of]\n"
         "VAR M = MAX ( dim_Date[Date] )\n"
         "RETURN IF ( M > EOMONTH ( A, -6 ) && MIN ( dim_Date[Date] ) <= A,\n"
         "    CALCULATE ( SUM ( fct_Invoice[Amount] ), REMOVEFILTERS ( dim_Project ) ) )",
         '"$#,0"', "deck slide 1 REVENUE - ACTUAL, by month"),
        ("Active Projects", count_active("TRUE ()"), '"#,0"', "deck slide 1 ACTIVE PROJECTS"),
        ("Projects On Track", count_active(f"[@g] >= {setting('grade_on_track_from')}"), '"#,0"',
         "deck slide 2 ON TRACK"),
        ("Projects Monitor",
         count_active(f"[@g] >= {setting('grade_monitor_from')} && [@g] < {setting('grade_on_track_from')}"),
         '"#,0"', "deck slide 2 MONITOR"),
        ("Projects Needing Attention",
         count_active(f"NOT ISBLANK ( [@g] ) && [@g] < {setting('grade_monitor_from')}"), '"#,0"',
         "deck slide 2 NEEDS ATTENTION / slide 1 'require attention'"),
        ("Projects Unscored", count_active("ISBLANK ( [@g] )"), '"#,0"', "deck slide 2 UNSCORED"),
        ("Projects At Risk (Grade)",
         count_active(f"NOT ISBLANK ( [@g] ) && [@g] <= {setting('grade_at_risk_max')}"), '"#,0"',
         "deck slide 1 PROJECTS AT RISK - grade 45 and below (Oct 21 call)"),
        ("At Risk Breakdown",
         "VAR G = ADDCOLUMNS ( FILTER ( VALUES ( dim_Project[ProjectKey] ), [Dashboard Status] = \"Active\" ), \"@g\", [Grade] )\n"
         f"VAR T = ADDCOLUMNS ( FILTER ( G, NOT ISBLANK ( [@g] ) && [@g] <= {setting('grade_at_risk_max')} ), \"@p\", [Weakest Pillar] )\n"
         "VAR N = GROUPBY ( T, [@p], \"@n\", COUNTX ( CURRENTGROUP (), 1 ) )\n"
         "RETURN IF ( ISEMPTY ( T ), \"None at or below grade \" & " + setting("grade_at_risk_max") + ",\n"
         "    CONCATENATEX ( N, [@p] & \" (\" & [@n] & \")\", \"  \" & UNICHAR ( 8226 ) & \"  \", [@n], DESC, [@p], ASC ) )",
         None, "deck slide 1 'Schedule (2) - Margin (1)' - weakest pillar of each at-risk project"),
        ("Attention Subline",
         '[Projects Needing Attention] & " require attention"', None, "deck slide 1 ACTIVE PROJECTS sub-line"),
        ("Portfolio Gross Margin %",
         # Revenue only from projects that have a forecast, so a job with none adds no margin.
         "VAR R = " + over_active("IF ( NOT ISBLANK ( [Projected Cost] ), [Projected Revenue] )") + "\n"
         "VAR C = " + over_active("[Projected Cost]") + "\n"
         "RETURN IF ( R > 0, DIVIDE ( R - C, R ) )",
         '"0.0%"', "deck slide 1 GROSS MARGIN - projected, active projects"),
        ("Gross Margin Subline",
         "VAR D = [Portfolio Gross Margin %] - [Gross Margin Target]\n"
         'RETURN FORMAT ( D * 100, "+0.0;-0.0;0.0" ) & " pts vs " & FORMAT ( [Gross Margin Target], "0.0%" ) & " target"',
         None, "deck slide 1 GROSS MARGIN sub-line"),
        ("Backlog",
         over_active("MAX ( 0, [Position Contract] - [Billed To Date (Gross)] )"), '"$#,0"',
         "deck slide 1 BACKLOG - contract not yet billed, active projects"),
        ("Backlog Subline",
         # Months of cover at the last three complete months' billing rate.
         "VAR A = [Data As Of]\n"
         "VAR S = EOMONTH ( A, -4 ) + 1\nVAR E = EOMONTH ( A, -1 )\n"
         "VAR Rate = DIVIDE ( CALCULATE ( SUM ( fct_Invoice[Amount] ), REMOVEFILTERS ( dim_Date ), REMOVEFILTERS ( dim_Project ),\n"
         "    fct_Invoice[SentDate] >= S, fct_Invoice[SentDate] <= E ), 3 )\n"
         'RETURN IF ( Rate > 0, FORMAT ( DIVIDE ( [Backlog], Rate ), "0.0" ) & " months cover" )',
         None, "deck slide 1 BACKLOG sub-line - at the last 3 months' billing rate"),
        ("Portfolio Cash Position", over_active("[Cash Position]"), '"$#,0"',
         "deck slide 1 CASH POSITION - Chris's formula, active projects"),
        ("Cash Subline",
         "VAR I = " + over_active("[Cash Collected]") + "\n"
         "VAR O = " + over_active("[Cash Paid Out]") + "\n"
         'RETURN IF ( O > 0, FORMAT ( DIVIDE ( I, O ), "0%" ) & " collected vs paid" )',
         None, "deck slide 1 CASH POSITION sub-line"),
        ("Portfolio Safety Score",
         "VAR T = ADDCOLUMNS ( FILTER ( VALUES ( dim_Project[ProjectKey] ), [Dashboard Status] = \"Active\" ), \"@s\", [Safety Pillar] )\n"
         "RETURN AVERAGEX ( FILTER ( T, NOT ISBLANK ( [@s] ) ), [@s] )",
         '"0%"', "deck slide 1 SAFETY tile - 'Calc based on # of inspections' callout"),
        ("Safety Subline",
         "VAR N = " + over_active("[Safety Inspections (Week)]") + "\n"
         "VAR P = COUNTROWS ( FILTER ( VALUES ( dim_Project[ProjectKey] ), [Dashboard Status] = \"Active\" && [Project Phase] = \"Construction\" ) )\n"
         'RETURN COALESCE ( N, 0 ) & " inspections across " & COALESCE ( P, 0 ) & " sites (5 each)"',
         None, "deck slide 1 SAFETY sub-line"),
        ("Projects On Schedule", count_active("NOT ISBLANK ( [Completion Variance Days] ) && [Completion Variance Days] <= 0"), '"#,0"',
         "deck slide 1 ON SCHEDULE - forecast finish on or before baseline"),
        ("Projects With Baseline", count_active("NOT ISBLANK ( [Completion Variance Days] )"), '"#,0"', "derived"),
        ("On Schedule Ratio", "DIVIDE ( [Projects On Schedule], [Projects With Baseline] )", '"0%"', "derived"),
        ("On Schedule Text", '[Projects On Schedule] & " / " & [Projects With Baseline]', None, "deck slide 1 '19 / 24'"),
        ("Projects On Budget", count_active("NOT ISBLANK ( [Forecast Variance] ) && [Forecast Variance] >= 0"), '"#,0"',
         "deck slide 1 ON BUDGET - forecast final cost within budget"),
        ("Projects With Budget", count_active("NOT ISBLANK ( [Forecast Variance] )"), '"#,0"', "derived"),
        ("On Budget Ratio", "DIVIDE ( [Projects On Budget], [Projects With Budget] )", '"0%"', "derived"),
        ("On Budget Text", '[Projects On Budget] & " / " & [Projects With Budget]', None, "deck slide 1 '20 / 24'"),
        ("Portfolio Subcontractor Coverage",
         "DIVIDE ( " + over_active("[Subcontract Committed]") + ", " + over_active("[Subcontract Budget]") + " )",
         '"0%"', "deck slide 1 SUBCONTRACTOR COVERAGE"),
        ("Change Orders Approved %",
         "VAR Ap = " + over_active("CALCULATE ( [Approved Change Orders], REMOVEFILTERS ( dim_Date ) )") + "\n"
         "VAR Pe = " + over_active("[Pending Change Orders]") + "\n"
         "RETURN DIVIDE ( Ap, Ap + Pe )",
         '"0%"', "deck slide 1 CHANGE ORDERS APPROVED - approved value over approved + pending"),
        ("Active Flag", 'IF ( [Dashboard Status] = "Active", "Yes" )', None,
         "derived - visual filter for active projects"),
        ("Not Active Flag", 'IF ( [Is Dashboard Project] && [Dashboard Status] <> "Active", "Yes" )', None,
         "derived - visual filter for the inactive / archived list"),
        ("Priority Score",
         # deck slide 1: "Top 3 based on calc from Page 2 for projects sorted lowest to highest".
         # 100 less the grade, so a Top 3 filter picks the LOWEST grades; BLANK for a project
         # that is not active or not scored, which the Top N leaves out.
         'IF ( [Dashboard Status] = "Active", VAR G = [Grade] RETURN IF ( NOT ISBLANK ( G ), 100 - G ) )',
         '"0.0"', "deck slide 1 PRIORITY PROJECTS - lowest grade first"),
        ("Project Title",
         'IF ( HASONEVALUE ( dim_Project[ProjectName] ), UPPER ( VALUES ( dim_Project[ProjectName] ) ), "SELECT A PROJECT" )',
         None, "deck slide 3 header"),
        ("Week Header",
         '"CONSTRUCTION OPERATIONS  |  " & UPPER ( [Report Week Label] )', None, "deck header sub-line"),
        # ---- data to resolve: AR the crosswalk cannot attach to a project ---------------------
        ("Unattributed Open AR",
         "CALCULATE ( SUM ( fct_Invoice[Balance] ), fct_Invoice[HasUnmatchedProject] = TRUE (), REMOVEFILTERS () )",
         '"$#,0"', "derived - open Sage AR on jobs with no Procore project (dq_DataGap 'Unmatched AR invoice')"),
        ("Unattributed AR Jobs",
         "CALCULATE ( DISTINCTCOUNT ( fct_Invoice[SageJobNumber] ), fct_Invoice[HasUnmatchedProject] = TRUE (),"
         "    fct_Invoice[Balance] > 0, REMOVEFILTERS () )",
         '"#,0"', "derived - Sage jobs carrying that AR"),
        ("Data Notice",
         f"VAR T = {money_text('[Unattributed Open AR]')}\n"
         "RETURN IF ( [Unattributed Open AR] > 0, \"DATA TO RESOLVE:  \" & T & \" of open AR is on \" & [Unattributed AR Jobs]\n"
         "    & \" Sage jobs with no Procore project, so no project here carries it. Map them in the crosswalk.\",\n"
         "    \"Every open AR invoice is matched to a project\" )",
         None, "derived - the crosswalk gap, in words"),
        ("Data As Of Header",
         '"DATA AS OF " & UPPER ( FORMAT ( [Data As Of], "mmm d, yyyy" ) ) & "  " & UNICHAR ( 8226 ) & "  " & [Pipeline Status]',
         None, "deck header - when the numbers were true"),
        ("Portfolio Header",
         '[Active Projects] & " ACTIVE PROJECTS  " & UNICHAR ( 8226 ) & "  " & UPPER ( [Report Week Label] )', None,
         "deck slide 2 header"),
        ("Metric Colour", colour_for("[Metric Score]"), None, "grade detail - score pill"),
        ("Metric Ink", ink_for("[Metric Score]"), None, "grade detail - score pill text"),
        ("Meeting In Window Flag",
         "VAR E = [Report Week End]\n"
         "VAR D = SELECTEDVALUE ( fct_Meeting[MeetingDate] )\n"
         "RETURN IF ( HASONEVALUE ( fct_Meeting[MeetingKey] ) && SELECTEDVALUE ( fct_Meeting[MeetingType] ) IN { \"OAC\", \"Trade Partner\" }\n"
         "    && D >= E - 27 && D <= E, \"Yes\" )",
         None, "grade detail - the meetings the rolling four weeks scored"),
        ("Meeting Met Standard",
         'IF ( HASONEVALUE ( fct_Meeting[MeetingKey] ), IF ( SELECTEDVALUE ( fct_Meeting[IsCompliant] ), "Yes",\n'
         '    IF ( SELECTEDVALUE ( fct_Meeting[IsDuplicateDate] ), "Duplicate of an earlier meeting", "No" ) ) )',
         None, "grade detail - did this meeting count"),
        ("Status Note",
         'VAR S = [Dashboard Status]\nRETURN IF ( S <> "Active", S & IF ( S = "Inactive", " - no Procore activity in " & '
         + setting("active_within_days") + ' & " days" ) )',
         None, "derived - why a project is off the active list"),
    ]
    return out


if __name__ == "__main__":
    ms = measures()
    names = [m[0] for m in ms]
    assert len(names) == len(set(names)), "duplicate measure names"
    # Every bracketed reference to a dashboard measure resolves within this module or the
    # model; the full check runs against the model in test_report.py.
    print(f"dashboard: {len(ms)} measures")
