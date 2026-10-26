"""Independent checks for the Weekly Dashboard measures (dashboard.py).

Same contract as validate_model.monthly_expected: each measure is RECOMPUTED here in Python
from the raw model columns - never by calling the measure - and validate_model compares it
with the deployed DAX at portfolio, project, month and category grain. DAX semantics are
reproduced on purpose: a SUM of nothing is BLANK, BLANK compares as 0, string equality
ignores case, DIVIDE by blank or zero is BLANK.

PRESENTATION measures are listed, with the reason, instead of checked: pill colours, cell
and tile text, and the row flags the project page's lists filter on. Every number they
print is itself a checked measure; what they add is formatting or a row-level test that
only exists inside a visual (checked in the browser).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import dashboard

# Pure presentation: text or colour built from checked measures, or row-level flags that
# need a visual's row context (a schedule activity, an inspection, a dim_DashMetric row).
PRESENTATION = {
    "Report Week Label", "Phase Label", "Grade Colour", "Grade Ink", "Grade Cell", "Grade Text",
    "Grade Subline", "Schedule Headline", "Schedule Subline", "Schedule Tile Colour",
    "Billed Subline", "Contract Change Text", "Financial Exceptions", "Attention Subline",
    "Gross Margin Subline", "Backlog Subline", "Cash Subline", "Safety Subline", "On Schedule Text",
    "On Budget Text", "At Risk Breakdown", "Status Note", "Active Flag", "Executive Focus",
    "Project Team", "Not Active Flag", "Project Title", "Week Header",
    "Data As Of Header", "Portfolio Header", "Metric Colour", "Metric Ink", "Meeting In Window Flag",
    "Meeting Met Standard", "Data Notice", "Work Progress Shown", "Tracking Finish Shown", "Forecast Finish Shown",
    # dim_DashMetric row measures: BLANK outside a row; their inputs are the checked
    # "Metric Score - <name>" measures.
    "Metric Score", "Metric Driver", "Metric Reading", "Metric Band", "Metric State",
    "Metric Weight In Grade", "Is Top Risk", "Risk Severity", "Risk Severity Colour", "Risk Severity Ink",
    # Schedule-activity and inspection row flags.
    "Near Term Flag", "Critical Near Term Flag", "Activity Next Step", "Behind Schedule Flag",
    "Days Behind Baseline", "Recent Win Flag", "Inspection In Week Flag",
    *{f"{p} {suffix}" for _, p in dashboard.PILLARS for suffix in ("Cell", "Colour", "Ink")},
}


def _ts(text):
    return None if text is None else datetime.fromisoformat(str(text).replace("Z", ""))


def _d(text):
    return None if text is None else _ts(text).date()


def _iso(d):
    return None if d is None else f"{d.isoformat()}T00:00:00"


def _eq(a, b):
    return isinstance(a, str) and a.casefold() == b.casefold()


def _sum(values):
    values = [v for v in values if v is not None]
    return sum(values) if values else None


def _div(n, d):
    return None if n is None or not d else n / d


def _eomonth(d: date, months: int) -> date:
    y, m = divmod(d.year * 12 + d.month - 1 + months + 1, 12)
    return date(y, m + 1, 1) - timedelta(days=1)


def expected(E: dict) -> dict:
    """Recomputations keyed by measure name; E is monthly_expected's own dict (for the
    existing measures the dashboard builds on, e.g. Current Contract, Spent To Date)."""
    D: dict = {}

    def setting(c, key):
        vals = [r["Value"] for r in c.data["dim_DashSetting"] if _eq(r["SettingKey"], key)]
        return max(vals) if vals else None

    def week_end(c):
        return max(_d(r["WeekEnd"]) for r in c.data["dim_ReportWeek"] if r["WeeksAgo"] == 1)

    def as_of(c):
        return max(_d(r["AsOfDate"]) for r in c.data["dim_ReportWeek"])

    def window_end(c):
        return min(week_end(c), as_of(c))

    def is_project(s):
        return s.project not in (None, "UNMATCHED")

    def projects(c, s):
        return [p["ProjectKey"] for p in c.rows("dim_Project", s) if p["ProjectKey"] is not None]

    def per_project(c, s, fn):
        return [fn(c, s._replace(project=k)) for k in projects(c, s)]

    nomonth = lambda s: s._replace(month=None)  # noqa: E731 - REMOVEFILTERS ( dim_Date )

    # ---- week, project, phase ------------------------------------------------------
    # Dates come back from the model as ISO datetimes; compare in that shape.
    D["Report Week End"] = lambda c, s: _iso(week_end(c))
    D["Data As Of"] = lambda c, s: _iso(as_of(c))
    D["Report Window End"] = lambda c, s: _iso(window_end(c))
    D["Report Weeks Ago"] = lambda c, s: 1
    D["Is Dashboard Project"] = lambda c, s: is_project(s)

    def billed_gross_one(c, s):
        p = E["Owner Billed To Date"](c, s)
        if p is not None and p != 0:
            return p
        return _sum(r["Amount"] for r in c.rows("fct_Invoice", nomonth(s)) if r["HasUnmatchedProject"] is not True)

    D["Billed To Date (Gross)"] = lambda c, s: _sum(per_project(c, s, billed_gross_one))
    # The contract as of the build (fct_ProjectPosition), not at the end of a selected month.
    D["Position Contract"] = lambda c, s: E["Current Contract"](c, nomonth(s))
    D["Billed % Of Contract"] = lambda c, s: _div(D["Billed To Date (Gross)"](c, s), D["Position Contract"](c, s))

    def phase(c, s):
        b = D["Billed % Of Contract"](c, s)
        if b is None:
            return None
        if b < setting(c, "phase_precon_below"):
            return "Precon"
        return "Closeout" if b > setting(c, "phase_closeout_from") else "Construction"

    D["Project Phase"] = phase

    def last_activity(c, s):
        a = as_of(c)
        found = [
            max((_d(r["LastLogDate"]) for r in c.rows("fct_SafetyMonthly", nomonth(s)) if r["LastLogDate"]), default=None),
            max((_d(r["MeetingDate"]) for r in c.rows("fct_Meeting", s) if r["MeetingDate"] and _d(r["MeetingDate"]) <= a), default=None),
            max((_d(r["InspectionDate"]) for r in c.rows("fct_Inspection", s)
                 if r["InspectionDate"] and _d(r["InspectionDate"]) <= a), default=None),
            max((_d(r["CreatedDate"]) for r in c.rows("fct_RfiSubmittal", nomonth(s)) if r["CreatedDate"]), default=None),
            max((_d(r["CreatedDate"]) for r in c.rows("fct_QualityItem", nomonth(s)) if r["CreatedDate"]), default=None),
        ]
        found = [f for f in found if f is not None]
        return max(found) if found else None

    D["Last Project Activity"] = lambda c, s: _iso(last_activity(c, s))

    def status(c, s):
        if not is_project(s):
            return None
        paid = _div(D["Cash Collected"](c, s), D["Position Contract"](c, s))
        if paid is not None and paid >= setting(c, "archive_paid_from"):
            return "Archived"
        last = last_activity(c, s)
        if last is not None and (as_of(c) - last).days <= setting(c, "active_within_days"):
            return "Active"
        return "Inactive"

    D["Dashboard Status"] = status

    # ---- cash position ---------------------------------------------------------------
    D["Cash - Billings To Date"] = lambda c, s: D["Billed To Date (Gross)"](c, s)
    D["Cash - Retainage Receivable"] = lambda c, s: E["Retainage Held Owner"](c, s) or 0
    D["Cash - Unpaid Receivables"] = lambda c, s: _sum(
        r["Balance"] for r in c.rows("fct_Invoice", nomonth(s)) if r["HasUnmatchedProject"] is not True) or 0
    D["Cash - Costs Incurred"] = lambda c, s: E["Spent To Date"](c, s)
    D["Cash - Unpaid Payables"] = lambda c, s: _sum(
        r["LineTotal"] * r["InvoiceBalance"] / r["InvoiceTotal"] for r in c.rows("fct_ApInvoice", nomonth(s))
        if r["IsJobCost"] is True and r["ProjectKey"] is not None and (r["InvoiceTotal"] or 0) != 0
        and r["LineTotal"] is not None and r["InvoiceBalance"] is not None) or 0
    D["Cash - Retainage Payable"] = lambda c, s: E["Retainage Held Sub"](c, s) or 0
    # fct_ProjectPosition has one row per real project: the UNMATCHED member reads BLANK.
    for _k in ("Cash - Retainage Receivable", "Cash - Unpaid Receivables", "Cash - Unpaid Payables",
               "Cash - Retainage Payable"):
        D[_k] = (lambda f: lambda c, s: None if s.project == "UNMATCHED" else f(c, s))(D[_k])

    def collected(c, s):
        b = D["Cash - Billings To Date"](c, s)
        return None if b is None else b - D["Cash - Retainage Receivable"](c, s) - D["Cash - Unpaid Receivables"](c, s)

    def paid_out(c, s):
        x = D["Cash - Costs Incurred"](c, s)
        return None if x is None else x - D["Cash - Unpaid Payables"](c, s) - D["Cash - Retainage Payable"](c, s)

    D["Cash Collected"], D["Cash Paid Out"] = collected, paid_out
    D["Cash Position"] = lambda c, s: (None if (i := collected(c, s)) is None or (o := paid_out(c, s)) is None
                                       else i - o)

    def ratio(c, s):
        i, o = collected(c, s), paid_out(c, s)
        if (o or 0) > 0:
            return _div(i, o)
        return 1 if i is not None and o is not None and i >= 0 else None

    D["Cash Collected / Paid"] = ratio

    # ---- profitability ---------------------------------------------------------------
    def division(c):
        return {x["CostCodeKey"]: x["NewDivisionCode"] for x in c.data["dim_CostCodeCrosswalk"]}

    D["Projected Revenue"] = lambda c, s: E["Budget"](c, s)
    D["Projected Cost"] = lambda c, s: _sum(
        r["ForecastAmount"] for r in c.rows("fct_BudgetLine", nomonth(s))
        if not _eq(division(c).get(r["CostCodeKey"]), "50"))

    def gm(c, s):
        rev = D["Projected Revenue"](c, s)
        return _div(rev - (D["Projected Cost"](c, s) or 0), rev) if (rev or 0) > 0 else None

    D["Projected Gross Margin %"] = gm
    D["Gross Margin Target"] = lambda c, s: setting(c, "gross_margin_target")
    D["Margin vs Target"] = lambda c, s: None if (m := gm(c, s)) is None else m - setting(c, "gross_margin_target")

    # ---- aging ------------------------------------------------------------------------
    def weighted_age(c, s):
        a = as_of(c)
        rows = c.rows("fct_Invoice", nomonth(s))
        owed = [r for r in rows if (r["Balance"] or 0) > 0 and r["HasUnmatchedProject"] is not True and r["SentDate"]]
        bal = _sum(r["Balance"] for r in owed)
        if (bal or 0) > 0:
            return sum(r["Balance"] * (a - _d(r["SentDate"])).days for r in owed) / bal
        return 0 if any(r["HasUnmatchedProject"] is not True for r in rows) else None

    D["AR Weighted Age Days"] = weighted_age
    D["AR Over 60 Days"] = lambda c, s: _sum(
        r["Balance"] for r in c.rows("fct_Invoice", nomonth(s))
        if (r["Balance"] or 0) > 0 and r["SentDate"] and (as_of(c) - _d(r["SentDate"])).days > setting(c, "ar_aged_days")) or 0

    # ---- schedule (field ops) --------------------------------------------------------------
    def missed(kind):
        def value(c, s):
            if not is_project(s):
                return None
            e = week_end(c)
            rows = [r for r in c.rows("fct_Meeting", s) if _eq(r["MeetingType"], kind) and r["IsCompliant"] is True]
            held = sum(any(e - timedelta(days=7 * k + 6) <= _d(r["MeetingDate"]) <= e - timedelta(days=7 * k)
                           for r in rows) for k in range(4))
            return 4 - held
        return value

    D["OAC Weeks Missed"] = missed("OAC")
    D["Trade Partner Weeks Missed"] = missed("Trade Partner")

    def lookahead(c, s):
        if not is_project(s) or not c.rows("fct_ScheduleActivity", s):
            return None
        stamps = [_ts(r[k]) for r in c.rows("fct_LookaheadTask", s) for k in ("UpdatedAt", "CreatedAt") if r[k]]
        return 999 if not stamps else (as_of(c) - max(stamps).date()).days

    def schedule_update(c, s):
        stamps = [_ts(r["UpdatedAt"]) for r in c.rows("fct_ScheduleActivity", s) if r["UpdatedAt"]]
        return (as_of(c) - max(stamps).date()).days if is_project(s) and stamps else None

    D["Days Since Look-Ahead Update"], D["Days Since Schedule Update"] = lookahead, schedule_update

    def baseline_days(c, s):
        rows = c.rows("fct_Milestone", nomonth(s))
        starts = [_d(r["BaselineStart"]) for r in rows if r["BaselineStart"]]
        ends = [_d(r["BaselineFinish"]) for r in rows if r["BaselineFinish"]]
        if not starts or not ends or max(ends) <= min(starts):
            return None
        return (max(ends) - min(starts)).days

    D["Baseline Duration Days"] = baseline_days
    D["Completion Variance %"] = lambda c, s: _div(E["Completion Variance Days"](c, s), baseline_days(c, s))
    def has(c, s, kind):
        return any(_eq(r["ItemType"], kind) for r in c.rows("fct_RfiSubmittal", nomonth(s)))

    D["Submittals Overdue"] = lambda c, s: ((E["Open Submittals Past Due"](c, nomonth(s)) or 0)
                                            if is_project(s) and has(c, s, "Submittal") else None)
    D["RFIs Outstanding"] = lambda c, s: (sum(
        1 for r in c.rows("fct_RfiSubmittal", nomonth(s))
        if _eq(r["ItemType"], "RFI") and r["IsOpen"] is True
        and (r["IsPastDue"] is True or (r["DueDate"] is None and (r["DaysOpen"] or 0) > 7)))
        if is_project(s) and has(c, s, "RFI") else None)

    def inspections(category):
        def value(c, s):
            if not is_project(s):
                return None
            e, start = window_end(c), week_end(c) - timedelta(days=6)
            return sum(1 for r in c.rows("fct_Inspection", s)
                       if _eq(r["Category"], category) and r["IsPerformed"] is True and r["InspectionDate"]
                       and start <= _d(r["InspectionDate"]) <= e)
        return value

    D["Safety Inspections (Week)"] = inspections("Safety")
    D["Quality Inspections (Week)"] = inspections("Quality")
    D["Unclassified Inspections"] = lambda c, s: sum(1 for r in c.rows("fct_Inspection", s)
                                                     if _eq(r["Category"], "Unclassified"))

    # ---- scores ---------------------------------------------------------------------------
    def metric(c, key):
        return next(r for r in c.data["dim_DashMetric"] if r["MetricKey"] == key)

    # Scores, pillars and the grade are per project (fct_MetricScore / fct_ProjectScore):
    # BLANK without exactly one real project in context.
    def band(c, s, key, driver):
        if not is_project(s):
            return None
        v = D[driver](c, s)
        m = metric(c, key)
        ph = phase(c, s)
        applies = _eq(m["Stages"], "All") or (ph is not None and ph.casefold() in (m["Stages"] or "").casefold())
        if not _eq(m["Status"], "Live") or not applies or v is None:
            return None
        hits = [b for b in c.data["dim_DashBand"] if b["MetricKey"] == key
                and (b["MinValue"] is None or v >= b["MinValue"]) and (b["MaxValue"] is None or v < b["MaxValue"])]
        if not hits:
            return None
        lo, hi = max((b["MinValue"] for b in hits if b["MinValue"] is not None), default=None), \
            max((b["MaxValue"] for b in hits if b["MaxValue"] is not None), default=None)
        s0, s1 = max(b["ScoreAtMin"] for b in hits), max(b["ScoreAtMax"] for b in hits)
        if s0 == s1 or lo is None or hi is None:
            return s0
        return s0 + (s1 - s0) * (v - lo) / (hi - lo)

    for key, name, driver in dashboard.METRICS:
        D[dashboard.score_name(name)] = lambda c, s, k=key, d=driver: band(c, s, k, d)

    def pillar(c, s, key):
        if not is_project(s):
            return None
        found = [D[dashboard.score_name(n)](c, s) for k, n, _ in dashboard.METRICS if metric(c, k)["PillarKey"] == key]
        found = [f for f in found if f is not None]
        return sum(found) / len(found) if found else None

    for key, name in dashboard.PILLARS:
        D[f"{name} Pillar"] = lambda c, s, k=key: pillar(c, s, k)

    def weight(c, key):
        return next(r["Weight"] for r in c.data["dim_DashPillar"] if r["PillarKey"] == key)

    def coverage(c, s):
        den = sum(weight(c, k) for k, _ in dashboard.PILLARS if pillar(c, s, k) is not None)
        total = sum(weight(c, k) for k, _ in dashboard.PILLARS)
        return den / total if den > 0 else None

    def grade(c, s):
        found = {k: pillar(c, s, k) for k, _ in dashboard.PILLARS}
        den = sum(weight(c, k) for k, v in found.items() if v is not None)
        total = sum(weight(c, k) for k, _ in dashboard.PILLARS)
        if den <= 0 or den / total < setting(c, "min_coverage"):
            return None
        return 100 * sum(v * weight(c, k) for k, v in found.items() if v is not None) / den

    D["Grade Coverage %"], D["Grade"] = coverage, grade

    def grade_status(c, s):
        if not is_project(s):
            return None
        g = grade(c, s)
        if g is None:
            return "Unscored"
        if g >= setting(c, "grade_on_track_from"):
            return "On track"
        return "Monitor" if g >= setting(c, "grade_monitor_from") else "Needs attention"

    D["Grade Status"] = grade_status
    D["Measures Below Target"] = lambda c, s: (None if grade(c, s) is None else sum(
        1 for _, n, _ in dashboard.METRICS
        if (v := D[dashboard.score_name(n)](c, s)) is not None and v < setting(c, "risk_metric_below")))

    def weakest(c, s):
        # Points lost to the grade: weight x (1 - pillar); ties to the lower pillar key.
        found = [(-weight(c, k) * (1 - p), k, n) for k, n in dashboard.PILLARS if (p := pillar(c, s, k)) is not None]
        return min(found)[2] if found else None

    D["Weakest Pillar"] = weakest

    # ---- team, project page ----------------------------------------------------------------
    def initials(name):
        name = name or ""
        name = name[:name.find(" (")] if " (" in name else name
        words = " ".join(name.split()).split(" ")
        return (words[0][:1] + (words[-1][:1] if len(words) > 1 else "")).upper()

    def team(c, s):
        if not is_project(s):
            return None
        rows = sorted({(r["RoleOrder"], r["MemberName"]) for r in c.rows("fct_ProjectTeam", s)
                       if (r["RoleOrder"] or 0) <= 4})
        return " · ".join(initials(n) for _, n in rows) or "—"

    D["Team Initials"] = team
    D["Project Executive"] = lambda c, s: ", ".join(sorted(
        r["MemberName"] for r in c.rows("fct_ProjectTeam", s) if _eq(r["RoleCode"], "PX"))) or None

    def work_progress(c, s):
        rows = [r for r in c.rows("fct_ScheduleActivity", s) if not r["IsSummary"] and (r["DurationDays"] or 0) > 0]
        return _div(sum(r["DurationDays"] * (r["PercentComplete"] or 0) for r in rows),
                    sum(r["DurationDays"] for r in rows)) if rows else None

    D["Work Progress %"] = work_progress
    D["Billing Ahead Of Work Pts"] = lambda c, s: (
        None if (b := D["Billed % Of Contract"](c, s)) is None or (w := work_progress(c, s)) is None else (b - w) * 100)
    D["Tracking Finish"] = lambda c, s: max((r["BaselineFinish"] for r in c.rows("fct_Milestone", nomonth(s))
                                             if r["BaselineFinish"]), key=_ts, default=None)
    D["Forecast Finish"] = lambda c, s: E["Scheduled Finish"](c, s)
    D["Paid To Date"] = lambda c, s: _sum(r["AmountPaid"] for r in c.rows("fct_Invoice", nomonth(s))
                                          if r["HasUnmatchedProject"] is not True)
    D["Remaining Contract Balance"] = lambda c, s: (
        None if (k := D["Position Contract"](c, s)) is None else k - (D["Billed To Date (Gross)"](c, s) or 0))

    def subcontract(column):
        def value(c, s):
            div = division(c)
            return _sum(r[column] for r in c.rows("fct_BudgetLine", nomonth(s))
                        if (div.get(r["CostCodeKey"]) or "00") < "45")
        return value

    D["Subcontract Budget"], D["Subcontract Committed"] = subcontract("BudgetAmount"), subcontract("CommittedAmount")
    D["Subcontractor Coverage %"] = lambda c, s: _div(D["Subcontract Committed"](c, s), D["Subcontract Budget"](c, s))

    # ---- executive page ---------------------------------------------------------------
    def revenue_ytd(c, s):
        a = as_of(c)
        return _sum(r["Amount"] for r in c.data["fct_Invoice"]
                    if r["SentDate"] and date(a.year, 1, 1) <= _d(r["SentDate"]) <= a)

    def revenue_6(c, s):
        a = as_of(c)
        dates = [_d(r["Date"]) for r in c.rows("dim_Date", s) if r["Date"]]
        if not dates or not (max(dates) > _eomonth(a, -6) and min(dates) <= a):
            return None
        return _sum(r["Amount"] for r in c.rows("fct_Invoice", s._replace(project=None)))

    D["Revenue YTD"], D["Revenue Last 6 Months"] = revenue_ytd, revenue_6
    D["Unattributed Open AR"] = lambda c, s: _sum(
        r["Balance"] for r in c.data["fct_Invoice"] if r["HasUnmatchedProject"] is True)
    D["Unattributed AR Jobs"] = lambda c, s: len(
        {r["SageJobNumber"] for r in c.data["fct_Invoice"] if r["HasUnmatchedProject"] is True and (r["Balance"] or 0) > 0}) or None

    def active(c, s):
        return [s._replace(project=k) for k in projects(c, s) if status(c, s._replace(project=k)) == "Active"]

    def count(c, s, cond):
        return sum(1 for ps in active(c, s) if cond(c, ps))

    on, mon, risk = "grade_on_track_from", "grade_monitor_from", "grade_at_risk_max"
    D["Active Projects"] = lambda c, s: count(c, s, lambda c, ps: True)
    D["Projects On Track"] = lambda c, s: count(c, s, lambda c, ps: (grade(c, ps) or 0) >= setting(c, on))
    D["Projects Monitor"] = lambda c, s: count(c, s, lambda c, ps: setting(c, mon) <= (grade(c, ps) or 0) < setting(c, on))
    D["Projects Needing Attention"] = lambda c, s: count(
        c, s, lambda c, ps: grade(c, ps) is not None and grade(c, ps) < setting(c, mon))
    D["Projects Unscored"] = lambda c, s: count(c, s, lambda c, ps: grade(c, ps) is None)
    D["Projects At Risk (Grade)"] = lambda c, s: count(
        c, s, lambda c, ps: grade(c, ps) is not None and grade(c, ps) <= setting(c, risk))

    def over(c, s, fn):
        return _sum(fn(c, ps) for ps in active(c, s))

    def portfolio_gm(c, s):
        r = over(c, s, D["Projected Revenue"])
        return _div(r - (over(c, s, D["Projected Cost"]) or 0), r) if (r or 0) > 0 else None

    D["Portfolio Gross Margin %"] = portfolio_gm
    D["Backlog"] = lambda c, s: over(c, s, lambda c, ps: max(0, (D["Position Contract"](c, ps) or 0)
                                                           - (D["Billed To Date (Gross)"](c, ps) or 0)))
    D["Portfolio Cash Position"] = lambda c, s: over(c, s, D["Cash Position"])
    D["Portfolio Safety Score"] = lambda c, s: (
        (lambda v: sum(v) / len(v) if v else None)([x for ps in active(c, s) if (x := D["Safety Pillar"](c, ps)) is not None]))
    D["Projects On Schedule"] = lambda c, s: count(
        c, s, lambda c, ps: (v := E["Completion Variance Days"](c, ps)) is not None and v <= 0)
    D["Projects With Baseline"] = lambda c, s: count(c, s, lambda c, ps: E["Completion Variance Days"](c, ps) is not None)
    D["On Schedule Ratio"] = lambda c, s: _div(D["Projects On Schedule"](c, s), D["Projects With Baseline"](c, s))
    D["Projects On Budget"] = lambda c, s: count(
        c, s, lambda c, ps: (v := E["Forecast Variance"](c, ps)) is not None and v >= 0)
    D["Projects With Budget"] = lambda c, s: count(c, s, lambda c, ps: E["Forecast Variance"](c, ps) is not None)
    D["On Budget Ratio"] = lambda c, s: _div(D["Projects On Budget"](c, s), D["Projects With Budget"](c, s))
    D["Portfolio Subcontractor Coverage"] = lambda c, s: _div(over(c, s, D["Subcontract Committed"]),
                                                               over(c, s, D["Subcontract Budget"]))

    def co_approved(c, s):
        ap = over(c, s, lambda c, ps: E["Approved Change Orders"](c, nomonth(ps)))
        pe = over(c, s, E["Pending Change Orders"])
        return _div(ap, (ap or 0) + (pe or 0))

    D["Change Orders Approved %"] = co_approved
    D["Priority Score"] = lambda c, s: (None if status(c, s) != "Active" or (g := grade(c, s)) is None else 100 - g)
    return D


RAW_COLUMNS = {
    "dim_DashPillar": ["PillarKey", "Weight"],
    "dim_DashMetric": ["MetricKey", "PillarKey", "Stages", "Status", "SortOrder", "Metric"],
    "dim_DashBand": ["MetricKey", "MinValue", "MaxValue", "ScoreAtMin", "ScoreAtMax", "BandLabel"],
    "dim_DashSetting": ["SettingKey", "Value"],
    "dim_ReportWeek": ["WeeksAgo", "WeekEnd", "AsOfDate"],
    "fct_Inspection": ["Category", "IsPerformed", "InspectionDate", "InspectionKey"],
    "fct_Meeting": ["MeetingType", "IsCompliant", "MeetingDate"],
    "fct_ProjectTeam": ["RoleOrder", "RoleCode", "MemberName"],
    "fct_ScheduleActivity": ["IsSummary", "IsCritical", "IsComplete", "DurationDays", "PercentComplete",
                             "UpdatedAt", "StartDate", "FinishDate", "FinishVarianceDays", "ActivityKey"],
    "fct_LookaheadTask": ["UpdatedAt", "CreatedAt"],
    # Read by the measures; every value is recomputed from the raw facts above, never from it.
    "fct_ProjectPosition": [], "fct_MetricScore": [], "fct_ProjectScore": [],
}
# Columns the dashboard reads on tables validate_model already loads.
EXTRA_COLUMNS = {
    "fct_ApInvoice": ["InvoiceBalance", "InvoiceTotal"],
    "fct_Invoice": ["SageJobNumber"],
    "fct_Milestone": ["BaselineStart"],
    "fct_RfiSubmittal": ["DueDate", "CreatedDate"],
    "fct_QualityItem": ["CreatedDate"],
    "dim_CostCodeCrosswalk": ["NewDivisionCode"],
    "fct_BudgetLine": ["CostCodeKey"],
}
