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

import csv
from datetime import date, datetime, timedelta
from pathlib import Path

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
    "Meeting Met Standard", "Data Notice", "Priority Status", "On Track Caption", "Monitor Caption", "Attention Caption", "Work Progress Shown", "Tracking Finish Shown", "Forecast Finish Shown",
    # dim_DashMetric row measures: BLANK outside a row; their inputs are the checked
    # "Metric Score - <name>" measures.
    "Metric Score", "Metric Driver", "Metric Reading", "Metric Band", "Metric State",
    "Metric Weight In Grade", "Is Top Risk", "Risk Severity", "Risk Severity Colour", "Risk Severity Ink",
    # Schedule-activity and inspection row flags.
    "Near Term Flag", "Critical Near Term Flag", "Activity Next Step", "Behind Schedule Flag",
    "Days Behind Baseline", "Recent Win Flag", "Inspection In Week Flag",
    # Drill-down text over checked measures (Oct 30 call).
    "Close Status Text", "Revenue YTD Subline", "In Margin Tile", "On Budget Row", "On Schedule Row",
    "Open AR Shown", "Health Header", "Detail Header", "Check Colour", "Check Ink",
    # Outbuild milestone wording: the seed_PhaseMilestone patterns are not in the model.
    "Phase Source",
    # Drill-down row readings and filters: BLANK without one invoice, AP invoice, cost code,
    # inspection, observation or check row in context.
    "Invoice In YTD Flag", "Open AR Flag", "Invoice Treatment", "Invoice Age Days", "Invoice Age Band",
    "Open AR Job Flag", "Line Treatment", "Open AP Flag", "AP Age Days", "Open AP Active Flag",
    "Inspection In Week Any Flag", "Inspection In Week Active Flag", "Inspection Counted",
    "Observation In View Flag", "Observation Active Flag", "Check Result", "Cash Row Flag", "Unmatched Job Flag",
    # Project Overview, shown working: row readings (BLANK without one activity / milestone / cost
    # code); their totals are tied to the Overview tiles live by validate_drilldowns.py.
    "Progress Row Flag", "Budget Line Flag", "Manual Baseline Note", "Activity Duration", "Activity % Complete",
    "Activity Share Of Progress", "Milestone Baseline Finish", "Milestone Forecast Finish", "Milestone Days Late",
    "Line Cost To Complete",
    *{f"{p} {suffix}" for _, p in dashboard.PILLARS for suffix in ("Cell", "Colour", "Ink")},
}


# seed_PhaseMilestone (priority, pattern, marks): config, not in the model.
with open(Path(__file__).resolve().parent.parent / "02-transformation" / "seed" / "dashboard_phase_milestone.csv",
          encoding="utf-8") as _f:
    PHASE_MILESTONES = sorted((int(r["priority"]), r["pattern"].lower(), r["marks"]) for r in csv.DictReader(_f))


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


def _one(values):
    values = set(values)
    return next(iter(values)) if len(values) == 1 else None


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

    def by_project(fn):
        # dashboard.by_project: one project in context reads its own value (BLANK for
        # UNMATCHED); several - a totals row - the sum over the active projects.
        return lambda c, s: ((fn(c, s) if is_project(s) else None) if s.project is not None
                             else _sum(fn(c, ps) for ps in active(c, s)))

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
        # Oct 30 call: Outbuild milestones first. Each is classed by the best-priority
        # seed_PhaseMilestone pattern its name contains (the seed is not in the model: read
        # from the repo). Substantial completion reached = Closeout; of the best-named start
        # milestones, any reached = Construction, none = Precon. Else billed % of contract,
        # never Closeout while a substantial completion is still ahead.
        a, found = as_of(c), []
        for r in c.rows("fct_ScheduleActivity", s):
            name = (r["ActivityName"] or "").lower()
            hits = [p for p in PHASE_MILESTONES if p[1] in name]
            if r["IsMilestone"] is True and r["FinishDate"] and hits:
                prio, _, marks = min(hits)
                found.append((marks, prio, (r["PercentComplete"] or 0) >= 1 or _d(r["FinishDate"]) <= a))
        if any(m == "Closeout" and reached for m, _, reached in found):
            return "Closeout"
        starts = [(p, reached) for m, p, reached in found if m == "Construction"]
        if starts:
            best = min(p for p, _ in starts)
            return "Construction" if any(reached for p, reached in starts if p == best) else "Precon"
        b = D["Billed % Of Contract"](c, s)
        if b is None:
            return None
        if b < setting(c, "phase_precon_below"):
            return "Precon"
        ahead = any(m == "Closeout" and not reached for m, _, reached in found)
        return "Closeout" if b > setting(c, "phase_closeout_from") and not ahead else "Construction"

    # SELECTEDVALUE ( fct_ProjectPosition[Phase] ): one row per real project.
    D["Project Phase"] = lambda c, s: _one(phase(c, s._replace(project=k)) for k in projects(c, s) if k != "UNMATCHED")

    def last_activity(c, s):
        a = as_of(c)
        found = [
            max((_d(r["LastLogDate"]) for r in c.rows("fct_SafetyMonthly", nomonth(s)) if r["LastLogDate"]), default=None),
            max((_d(r["MeetingDate"]) for r in c.rows("fct_Meeting", s) if r["MeetingDate"] and _d(r["MeetingDate"]) <= a
                 and r["HasOccurred"] is True and r["MeetingType"] in ("OAC", "Trade Partner")), default=None),
            max((_d(r["InspectionDate"]) for r in c.rows("fct_Inspection", s)
                 if r["InspectionDate"] and _d(r["InspectionDate"]) <= a), default=None),
            max((_d(r["CreatedDate"]) for r in c.rows("fct_RfiSubmittal", nomonth(s)) if r["CreatedDate"]), default=None),
            max((_d(r["CreatedDate"]) for r in c.rows("fct_QualityItem", nomonth(s)) if r["CreatedDate"]), default=None),
        ]
        found = [f for f in found if f is not None]
        return max(found) if found else None

    D["Last Project Activity"] = lambda c, s: _iso(last_activity(c, s))

    def standing(c, s):
        # (status, reason), worded as fct_ProjectPosition words them. The rollout list
        # (seed_DashProject) is not in the model: IsRolloutProject is that list's membership,
        # read as an input like a seed, never a derived value.
        paid = _div(D["Cash Collected"](c, s), D["Position Contract"](c, s))
        if paid is not None and paid >= setting(c, "archive_paid_from"):
            return "Archived", "100% paid"
        if (setting(c, "rollout_only") or 0) == 1:
            if any(r["IsRolloutProject"] is True for r in c.rows("fct_ProjectPosition", nomonth(s))):
                return "Active", "In the Nov 19 rollout (Oct 30 call)"
            return "Archived", "Not in the Nov 19 rollout (Oct 30 call)"
        last = last_activity(c, s)
        if last is not None and (as_of(c) - last).days <= setting(c, "active_within_days"):
            return "Active", "Procore activity in the last 60 days"
        return "Inactive", "No Procore activity in the last 60 days"

    def status(c, s):
        return standing(c, s)[0] if is_project(s) else None

    def real(c, s):
        # The projects fct_ProjectPosition / fct_DashCheck hold a row for.
        return [s._replace(project=k) for k in projects(c, s) if k != "UNMATCHED"]

    D["Dashboard Status"] = status
    # SELECTEDVALUE: the one reason (source) every project in context shares, else BLANK.
    D["Status Reason"] = lambda c, s: _one(standing(c, ps)[1] for ps in real(c, s))

    def billing_source(c, s):
        p = E["Owner Billed To Date"](c, nomonth(s))
        if p is not None and p != 0:
            return "Procore owner pay apps (gross of retainage)"
        ar = _sum(r["Amount"] for r in c.rows("fct_Invoice", nomonth(s)) if r["HasUnmatchedProject"] is not True)
        return None if ar is None else "Sage AR invoices (no Procore pay app)"

    D["Billing Source"] = lambda c, s: _one(billing_source(c, ps) for ps in real(c, s))

    # ---- cash position ---------------------------------------------------------------
    D["Cash - Billings To Date"] = lambda c, s: D["Billed To Date (Gross)"](c, s)
    D["Cash - Retainage Receivable"] = lambda c, s: E["Retainage Held Owner"](c, s) or 0
    D["Cash - Unpaid Receivables"] = lambda c, s: _sum(
        r["Balance"] for r in c.rows("fct_Invoice", nomonth(s)) if r["HasUnmatchedProject"] is not True) or 0
    D["Cash - Costs Incurred"] = lambda c, s: E["Spent To Date"](c, s)
    D["Cash - Unpaid Payables"] = lambda c, s: _sum(
        r["LineTotal"] * r["InvoiceBalance"] / r["InvoiceTotal"] for r in c.rows("fct_ApInvoice", nomonth(s))
        if r["IsJobCost"] is True and r["IsVoid"] is not True and r["ProjectKey"] is not None and (r["InvoiceTotal"] or 0) != 0
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
    def position(c, s):
        return None if (i := collected(c, s)) is None or (o := paid_out(c, s)) is None else i - o

    # Several projects (a totals row): the sum of those that have both halves.
    D["Cash Position"] = lambda c, s: (position(c, s) if s.project is not None else
                                       _sum(position(c, s._replace(project=k)) for k in projects(c, s)))

    def ratio(c, s):
        i, o = collected(c, s), paid_out(c, s)
        if (o or 0) > 0:
            return _div(i, o)
        return 1 if i is not None and o is not None and i >= 0 else None

    D["Cash Collected / Paid"] = ratio

    # ---- profitability ---------------------------------------------------------------
    _divisions: dict = {}

    def division(c):
        # Built once per run: per budget line it made the live check quadratic (6,743 cost codes).
        if id(c) not in _divisions:
            _divisions[id(c)] = {x["CostCodeKey"]: x["NewDivisionCode"] for x in c.data["dim_CostCodeCrosswalk"]}
        return _divisions[id(c)]

    D["Projected Revenue"] = lambda c, s: E["Budget"](c, s)
    D["Projected Cost"] = lambda c, s: _sum(
        r["ForecastAmount"] for r in c.rows("fct_BudgetLine", nomonth(s))
        if not _eq(division(c).get(r["CostCodeKey"]), "50"))

    def gm(c, s):
        # Over several projects, revenue only from those with a forecast (the tile's formula).
        rev = _sum(D["Projected Revenue"](c, ps) for ps in (s._replace(project=k) for k in projects(c, s))
                   if D["Projected Cost"](c, ps) is not None)
        cost = D["Projected Cost"](c, s)
        return _div(rev - cost, rev) if (rev or 0) > 0 and cost is not None else None

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
            e, start = window_end(c), week_end(c) - timedelta(days=6)
            return sum(1 for r in c.rows("fct_Inspection", s)
                       if _eq(r["Category"], category) and r["IsPerformed"] is True and r["InspectionDate"]
                       and start <= _d(r["InspectionDate"]) <= e)
        return by_project(value)

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
        return round(den / total, 6) if den > 0 else None

    def grade(c, s):
        found = {k: pillar(c, s, k) for k, _ in dashboard.PILLARS}
        den = sum(weight(c, k) for k, v in found.items() if v is not None)
        total = sum(weight(c, k) for k, _ in dashboard.PILLARS)
        if den <= 0 or round(den / total, 6) < setting(c, "min_coverage"):
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
        found = [(-weight(c, k) * (1 - p), k, n) for k, n in dashboard.PILLARS
                 if (p := pillar(c, s, k)) is not None and p < 1]
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
    # Ordered by the full Procore name, shown without its " (Company)" suffix.
    D["Project Executive"] = lambda c, s: ", ".join(
        n.split(" (")[0] for n in sorted(r["MemberName"] for r in c.rows("fct_ProjectTeam", s)
                                          if _eq(r["RoleCode"], "PX"))) or None

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
    # Oct 30 call: to the end of the week picked (today for this week). Voids are 0 in Amount.
    def revenue_ytd(c, s, column="Amount", end=None):
        a = window_end(c)
        end = a if end is None else end
        return _sum(r[column] for r in c.data["fct_Invoice"]
                    if r["SentDate"] and date(a.year, 1, 1) <= _d(r["SentDate"]) <= end)

    def revenue_6(c, s):
        a = window_end(c)
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
        r = over(c, s, lambda c, ps: D["Projected Revenue"](c, ps) if D["Projected Cost"](c, ps) is not None else None)
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

    # Both halves straight from the change-order log (Oct 30 call). A void CO is neither:
    # IsPending is FALSE for it, and approved leaves its status out.
    D["CO Approved Amount"] = lambda c, s: _sum(
        r["Amount"] for r in c.rows("fct_ChangeOrder", nomonth(s))
        if r["IsPending"] is not True and not _eq(r["StatusLabel"], "void"))
    D["CO Pending Amount"] = lambda c, s: _sum(
        r["Amount"] for r in c.rows("fct_ChangeOrder", nomonth(s)) if r["IsPending"] is True)

    def co_approved(c, s):
        ap = over(c, s, D["CO Approved Amount"])
        pe = over(c, s, D["CO Pending Amount"])
        return _div(ap, (ap or 0) + (pe or 0))

    D["Change Orders Approved %"] = co_approved
    D["Priority Score"] = lambda c, s: (None if status(c, s) != "Active" or (g := grade(c, s)) is None else 100 - g)

    # ---- drill-downs (Oct 30 call): the rows behind each tile, and their totals --------------
    def books(c):
        v = setting(c, "sage_closed_through")
        return None if v is None or v <= 0 else date(int(v // 10000), int(v % 10000 // 100), int(v % 100))

    D["Books Closed Through"] = lambda c, s: _iso(books(c))
    # MIN ( A, BLANK ) is 0 in DAX: no month close recorded reads BLANK, not the full year.
    D["Revenue YTD Closed"] = lambda c, s: (
        None if books(c) is None else revenue_ytd(c, s, end=min(window_end(c), books(c))))
    D["Revenue YTD Voided"] = lambda c, s: revenue_ytd(c, s, "VoidedAmount")

    # The month table: HASONEVALUE ( MonthYear ) is one MonthStart in context; the totals row
    # (no single month) is the year to date, so the table ties to the tile.
    def month_dates(c, s):
        dates = [_d(r["Date"]) for r in c.rows("dim_Date", s) if r["Date"]]
        one = len({r["MonthStart"] for r in c.rows("dim_Date", s)}) == 1
        return one, dates

    def in_month(column):
        def value(c, s):
            a = window_end(c)
            one, dates = month_dates(c, s)
            if not one:
                return revenue_ytd(c, s, column)
            if not dates or max(dates).year != a.year or min(dates) > a:
                return None
            return _sum(r[column] for r in c.rows("fct_Invoice", s._replace(project=None))
                        if r["SentDate"] and _d(r["SentDate"]) <= a)
        return value

    D["Revenue In Month"], D["Voided In Month"] = in_month("Amount"), in_month("VoidedAmount")

    def invoices_in_month(c, s):
        a = window_end(c)
        one, dates = month_dates(c, s)
        if one and (not dates or max(dates).year != a.year or min(dates) > a):
            return None
        lo = min(dates) if one else date(a.year, 1, 1)
        hi = max(dates) if one and max(dates) < a else a
        return sum(1 for r in c.data["fct_Invoice"]
                   if r["SentDate"] and lo <= _d(r["SentDate"]) <= hi and r["IsVoid"] is not True) or None

    D["Invoices In Month"] = invoices_in_month

    def close_state(c, s):
        if invoices_in_month(c, s) is None and D["Voided In Month"](c, s) is None:
            return None
        _, dates = month_dates(c, s)
        closed = books(c)
        return "Closed in Sage" if closed is not None and _eomonth(max(dates), 0) <= closed else "Provisional - not closed"

    D["Month Close State"] = close_state

    # Invoice rows: plain sums in context (voids are 0 in Amount / Balance, kept in VoidedAmount).
    for _name, _col in (("Invoice Amount", "Amount"), ("Invoice Voided", "VoidedAmount"), ("Invoice Paid", "AmountPaid"),
                        ("Invoice Balance", "Balance"), ("Job Open AR", "Balance")):
        D[_name] = lambda c, s, col=_col: _sum(r[col] for r in c.rows("fct_Invoice", s))
    D["Voided AR Left Out"] = lambda c, s: _sum(r["VoidedAmount"] for r in c.data["fct_Invoice"])

    # Margin and budget lines.
    D["Projected Fee"] = lambda c, s: None if s.project == "UNMATCHED" else _sum(
        r["ForecastAmount"] for r in c.rows("fct_BudgetLine", nomonth(s)) if _eq(division(c).get(r["CostCodeKey"]), "50"))
    D["Projected Margin $"] = lambda c, s: _sum(
        (D["Projected Revenue"](c, ps) or 0) - k for ps in (s._replace(project=p) for p in projects(c, s))
        if (k := D["Projected Cost"](c, ps)) is not None)
    for _name, _col in (("Line Budget", "BudgetAmount"), ("Line Forecast", "ForecastAmount"),
                        ("Line Committed", "CommittedAmount"), ("Line Spent", "SpentToDate")):
        D[_name] = lambda c, s, col=_col: _sum(r[col] for r in c.rows("fct_BudgetLine", nomonth(s)))
    # Without one cost code in context (every grain here) it is the coverage card's own ratio.
    D["Line Coverage %"] = lambda c, s: D["Subcontractor Coverage %"](c, s)

    # Contracts and pay apps (the page filters to the latest owner pay app; the measure sums).
    D["Project Backlog"] = lambda c, s: _sum(
        max(0, (D["Position Contract"](c, ps) or 0) - (D["Billed To Date (Gross)"](c, ps) or 0))
        for ps in (s._replace(project=k) for k in projects(c, s)))
    for _name, _col in (("Pay App Contract Sum", "ContractSumToDate"), ("Pay App Original Sum", "OriginalContractSum"),
                        ("Pay App CO Change", "NetChangeByChangeOrders"), ("Pay App Completed", "CompletedToDate"),
                        ("Pay App Retainage", "RetainageHeld"), ("Pay App Balance To Finish", "BalanceToFinish")):
        D[_name] = lambda c, s, col=_col: _sum(r[col] for r in c.rows("fct_Billing", nomonth(s)))

    # Sage AP job-cost lines, voids out. A line's share of its invoice's paid / unpaid header.
    def share(r, column):
        if not r["InvoiceTotal"] or r["LineTotal"] is None or r[column] is None:
            return None
        return r["LineTotal"] * r[column] / r["InvoiceTotal"]

    def ap_lines(c, s):
        return [r for r in c.rows("fct_ApInvoice", nomonth(s)) if r["IsJobCost"] is True and r["IsVoid"] is not True]

    D["AP Line Amount"] = lambda c, s: _sum(r["LineTotal"] for r in ap_lines(c, s))
    D["AP Line Open"] = lambda c, s: _sum(share(r, "InvoiceBalance") for r in ap_lines(c, s))

    # Subcontractor payments: fct_SubPayment rebuilt from its sources - the latest approved
    # Procore requisitions, and Sage AP for the vendor on the job.
    def subs(c, s):
        out = {}
        for r in c.rows("fct_Billing", nomonth(s)):
            if _eq(r["BillingType"], "Subcontractor") and r["IsLatestApprovedPeriod"] is True and r["ProjectKey"] is not None:
                out.setdefault((r["ProjectKey"], r["VendorKey"]), ([], []))[0].append(r)
        for r in ap_lines(c, s):
            if r["ProjectKey"] is not None:
                out.setdefault((r["ProjectKey"], r["VendorKey"]), ([], []))[1].append(r)
        return list(out.values())

    def sub_sum(side, fn):
        return lambda c, s: _sum(fn(r) for g in subs(c, s) for r in g[side])

    D["Sub Committed"] = sub_sum(0, lambda r: r["ContractSumToDate"])
    D["Sub Requisitioned"] = sub_sum(0, lambda r: r["CompletedToDate"])
    D["Sub Retainage Held"] = sub_sum(0, lambda r: r["RetainageHeld"])
    D["Sub AP Invoiced"] = sub_sum(1, lambda r: r["LineTotal"])
    D["Sub Paid"] = sub_sum(1, lambda r: share(r, "AmountPaid"))
    D["Sub AP Open"] = sub_sum(1, lambda r: share(r, "InvoiceBalance"))

    def left_to_pay(c, s):
        # Per project and vendor: committed less AP paid, where there is a requisition.
        found = [(k, _sum(share(r, "AmountPaid") for r in ap)) for req, ap in subs(c, s)
                 if req and (k := _sum(r["ContractSumToDate"] for r in req)) is not None]
        return _sum(k - (p or 0) for k, p in found)

    D["Sub Left To Pay"] = left_to_pay
    D["Sub Oldest Open Days"] = lambda c, s: max(
        ((as_of(c) - _d(r["InvoiceDate"])).days for g in subs(c, s) for r in g[1]
         if (r["InvoiceBalance"] or 0) > 0 and r["InvoiceDate"]), default=None)

    # Inspections: performed = closed; pass rate is conforming over conforming + deficient.
    def pass_rate(rows):
        p, f = _sum(r["PassItemCount"] for r in rows), _sum(r["DeficientItemCount"] for r in rows)
        return _div(p, (p or 0) + (f or 0))

    D["Inspection Pass Rate"] = lambda c, s: pass_rate(c.rows("fct_Inspection", s))
    D["Inspection Pass Items"] = lambda c, s: _sum(r["PassItemCount"] for r in c.rows("fct_Inspection", s))
    D["Inspection Fail Items"] = lambda c, s: _sum(r["DeficientItemCount"] for r in c.rows("fct_Inspection", s))

    def in_week(c, d):
        return d is not None and week_end(c) - timedelta(days=6) <= _d(d) <= window_end(c)

    D["Inspections Not Closed (Week)"] = by_project(lambda c, s: sum(
        1 for r in c.rows("fct_Inspection", s) if r["IsPerformed"] is not True and in_week(c, r["InspectionDate"])))

    def pass_rate_4w(category):
        def value(c, s):
            e = window_end(c)
            return pass_rate([r for r in c.rows("fct_Inspection", s)
                              if _eq(r["Category"], category) and r["IsPerformed"] is True and r["InspectionDate"]
                              and e - timedelta(days=28) < _d(r["InspectionDate"]) <= e])
        return value

    D["Safety Pass Rate (4 Weeks)"], D["Quality Pass Rate (4 Weeks)"] = pass_rate_4w("Safety"), pass_rate_4w("Quality")

    # Observations and punch (fct_DashObservation: Category is the seed classification, an input).
    def observations(c, s, category):
        return [r for r in c.rows("fct_DashObservation", s) if _eq(r["Category"], category)]

    D["Open Safety Observations"] = by_project(
        lambda c, s: sum(1 for r in observations(c, s, "Safety") if r["IsOpen"] is True))
    D["Safety Observations (Week)"] = by_project(
        lambda c, s: sum(1 for r in observations(c, s, "Safety") if in_week(c, r["CreatedDate"])))
    D["Open Quality Observations"] = by_project(lambda c, s: sum(
        1 for r in observations(c, s, "Quality") if _eq(r["ItemType"], "Observation") and r["IsOpen"] is True))

    def close_rate(category):
        def value(c, s):
            e = window_end(c)
            raised = [r for r in observations(c, s, category)
                      if r["CreatedDate"] and e - timedelta(days=90) < _d(r["CreatedDate"]) <= e]
            # COUNTROWS of no closed rows is BLANK, and DIVIDE ( BLANK, n ) is BLANK, not 0.
            return _div(sum(1 for r in raised if r["IsOpen"] is not True) or None, len(raised))
        return value

    D["Safety Observation Close Rate"], D["Quality Item Close Rate"] = close_rate("Safety"), close_rate("Quality")

    def mean_of(*names):
        def value(c, s):
            found = [v for n in names if (v := D[n](c, s)) is not None]
            return sum(found) / len(found) if found else None
        return value

    D["Safety Data Score (Proposed)"] = mean_of("Safety Pass Rate (4 Weeks)", "Safety Observation Close Rate")
    D["Quality Data Score (Proposed)"] = mean_of("Quality Pass Rate (4 Weeks)", "Quality Item Close Rate")

    # Data Health: fct_DashCheck rebuilt, (Result, Amount) for each of one project's nine checks.
    _checks: dict = {}

    def checks(c, ps):
        # The nine checks are read by four measures in every context: worked out once per project.
        key = (id(c), ps)
        if key not in _checks:
            _checks[key] = _checks_for(c, ps)
        return _checks[key]

    def _checks_for(c, ps):
        a, ps = as_of(c), nomonth(ps)
        invoices = [r for r in c.rows("fct_Invoice", ps) if r["HasUnmatchedProject"] is not True]
        out = []
        # 1 Sage invoiced vs Procore earned less retainage, within the tie-out tolerance.
        p = _sum(r["EarnedLessRetainageToDate"] for r in c.rows("fct_Billing", ps)
                 if r["IsLatestPeriod"] is True and _eq(r["BillingType"], "Owner"))
        sg = _sum(r["Amount"] for r in invoices)
        tol = setting(c, "tieout_tolerance")
        tol = 0.01 if tol is None else tol
        out.append(("Info", None) if p is None or sg is None else
                   ("Pass" if abs(sg - p) <= tol * max(abs(p), 1) else "Warn", sg - p))
        # 2 voided invoices: shown, not a warning.
        voids = sum(1 for r in invoices if r["IsVoid"] is True)
        out.append(("Info" if voids else "Pass", _sum(r["VoidedAmount"] for r in invoices) or 0))
        # 3 live invoices with the same Sage job, amount and month as another: the extra copies.
        seen = {}
        for r in c.rows("fct_Invoice", ps):
            if r["IsVoid"] is not True and r["Amount"]:
                seen.setdefault((r["SageJobNumber"], r["MonthStart"], r["Amount"]), []).append(r["Amount"])
        extra = [v for copies in seen.values() for v in copies[1:]]
        out.append(("Warn" if extra else "Pass", _sum(extra)))
        # 4 AR over 90 days.
        old = [r for r in c.rows("fct_Invoice", ps)
               if (r["Balance"] or 0) > 0 and r["SentDate"] and (a - _d(r["SentDate"])).days > 90]
        out.append(("Warn" if old else "Pass", _sum(r["Balance"] for r in old)))
        # 5 look-ahead worked in the last 7 days (Info when the project has no Outbuild schedule).
        acts = c.rows("fct_ScheduleActivity", ps)
        stamps = [_ts(r[k]) for r in c.rows("fct_LookaheadTask", ps) for k in ("UpdatedAt", "CreatedAt") if r[k]]
        days = (a - max(stamps).date()).days if stamps else None
        out.append(("Info", None) if not acts else ("Warn", None) if days is None else
                   ("Warn" if days > 7 else "Pass", float(days)))
        # 6 activities past their finish and not marked complete; 7 inspections over a week old, not closed.
        stale = sum(1 for r in acts if r["IsSummary"] is False and r["IsComplete"] is False
                    and r["FinishDate"] and _d(r["FinishDate"]) < a)
        out.append(("Warn" if stale else "Pass", float(stale)))
        open_insp = sum(1 for r in c.rows("fct_Inspection", ps) if r["IsPerformed"] is False
                        and r["InspectionDate"] and _d(r["InspectionDate"]) < a - timedelta(days=7))
        out.append(("Warn" if open_insp else "Pass", float(open_insp)))
        # 8 PM and Superintendent in the Procore directory; 9 a budget forecast.
        roles = {r["RoleCode"] for r in c.rows("fct_ProjectTeam", ps)}
        out.append(("Pass" if {"PM", "Super"} <= roles else "Warn", None))
        cost = D["Projected Cost"](c, ps)
        out.append(("Warn" if cost is None else "Pass", cost))
        return out

    D["Check Amount"] = lambda c, s: _sum(v for ps in real(c, s) for _, v in checks(c, ps))
    D["Checks Warning"] = lambda c, s: sum(sum(1 for k, _ in checks(c, ps) if k == "Warn") for ps in active(c, s))
    D["Projects With Warnings"] = lambda c, s: count(c, s, lambda c, ps: any(k == "Warn" for k, _ in checks(c, ps)))
    D["Checks Passed"] = lambda c, s: sum(sum(1 for k, _ in checks(c, ps) if k == "Pass") for ps in active(c, s))

    # Active-project totals the detail pages tie to.
    D["Active Contract Value"] = lambda c, s: over(c, s, D["Position Contract"])
    D["Active Pending COs"] = lambda c, s: over(c, s, D["CO Pending Amount"])
    D["Active Unpaid Payables"] = lambda c, s: over(c, s, D["Cash - Unpaid Payables"])
    D["Active Inspections Not Closed"] = lambda c, s: over(c, s, D["Inspections Not Closed (Week)"]) or 0
    D["Active Open Safety Observations"] = lambda c, s: over(c, s, D["Open Safety Observations"]) or 0
    return D


RAW_COLUMNS = {
    "dim_DashPillar": ["PillarKey", "Weight"],
    "dim_DashMetric": ["MetricKey", "PillarKey", "Stages", "Status", "SortOrder", "Metric"],
    "dim_DashBand": ["MetricKey", "MinValue", "MaxValue", "ScoreAtMin", "ScoreAtMax", "BandLabel"],
    "dim_DashSetting": ["SettingKey", "Value"],
    "dim_ReportWeek": ["WeeksAgo", "WeekEnd", "AsOfDate"],
    "fct_Inspection": ["Category", "IsPerformed", "InspectionDate", "InspectionKey", "PassItemCount",
                       "DeficientItemCount"],
    # Category is the seed_ObservationCategory classification - an input, like fct_Inspection's.
    "fct_DashObservation": ["Category", "ItemType", "IsOpen", "CreatedDate"],
    "fct_Meeting": ["MeetingType", "IsCompliant", "MeetingDate", "HasOccurred"],
    "fct_ProjectTeam": ["RoleOrder", "RoleCode", "MemberName"],
    "fct_ScheduleActivity": ["ActivityName", "IsMilestone", "IsSummary", "IsCritical", "IsComplete", "DurationDays", "PercentComplete",
                             "UpdatedAt", "StartDate", "FinishDate", "FinishVarianceDays", "ActivityKey"],
    "fct_LookaheadTask": ["UpdatedAt", "CreatedAt"],
    # Read by the measures; every value is recomputed from the raw facts above, never from it.
    # IsRolloutProject is the one exception: seed_DashProject membership, an input (see standing).
    "fct_ProjectPosition": ["IsRolloutProject"], "fct_MetricScore": [], "fct_ProjectScore": [],
    "fct_SubPayment": [], "fct_DashCheck": [],
}
# Columns the dashboard reads on tables validate_model already loads.
EXTRA_COLUMNS = {
    "fct_ApInvoice": ["InvoiceBalance", "InvoiceTotal", "IsVoid", "AmountPaid", "InvoiceDate", "VendorKey"],
    "fct_Invoice": ["SageJobNumber", "IsVoid", "VoidedAmount"],
    "fct_Billing": ["OriginalContractSum", "NetChangeByChangeOrders", "EarnedLessRetainageToDate", "VendorKey"],
    "fct_Milestone": ["BaselineStart"],
    "fct_RfiSubmittal": ["DueDate", "CreatedDate"],
    "fct_QualityItem": ["CreatedDate"],
    "dim_CostCodeCrosswalk": ["NewDivisionCode"],
    "fct_BudgetLine": ["CostCodeKey"],
}
