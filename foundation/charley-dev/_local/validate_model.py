"""Run DAX against the deployed semantic model and check the numbers.

    python validate_model.py                              # validate the current frame
    python validate_model.py --allow-production-reframe   # refresh production first

Without --allow-production-reframe it does NOT refresh: it validates the release the
production model currently shows (its last frame). Direct Lake automatic update is off, so
refreshing production IS publishing - that is cd_50_publish_models' job, after the DQ gate.
To validate a model you just deployed, use validate_candidate_model.py (reframes candidates
only) or run the pipeline / deploy_publish.py --apply --run first.

This is the reconciliation gate as a test rather than a manual comparison. It executes
each measure against the live model and asserts the result, so "the model deploys" becomes
"the model returns the right numbers".

Uses the Power BI executeQueries API, which needs a different token audience from the
Fabric API (analysis.windows.net/powerbi/api rather than api.fabric.microsoft.com).
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deploy as dp  # noqa: E402
import deploy_seeds as ds  # noqa: E402

MODEL_NAME = "Affect Project Report"
PBI_API = "https://api.powerbi.com/v1.0/myorg"

CHECKS: list[str] = []

# Reconcile model measures to the selected fact rows, without historical size thresholds.
# This checks semantic aggregation; it does not independently certify source balances.
BALANCE_QUERY = '''EVALUATE ROW(
    "Owner", [Retainage Held Owner],
    "ExpectedOwner", SUMX(FILTER(fct_Billing,
        fct_Billing[IsLatestPeriod] = TRUE() && fct_Billing[BillingType] = "Owner"), fct_Billing[RetainageHeld]),
    "Sub", [Retainage Held Sub],
    "ExpectedSub", SUMX(FILTER(fct_Billing,
        fct_Billing[IsLatestPeriod] = TRUE() && fct_Billing[BillingType] = "Subcontractor"), fct_Billing[RetainageHeld]),
    "Net", [Net Retainage Position],
    "ExpectedNet", [Retainage Held Owner] - [Retainage Held Sub],
    "Contract", [Current Contract],
    "ExpectedContract", SUMX(VALUES(fct_FinancialPeriod[ProjectKey]),
        VAR LastMonth = CALCULATE(MAX(fct_FinancialPeriod[MonthStart]),
            NOT ISBLANK(fct_FinancialPeriod[CurrentContract]))
        RETURN CALCULATE(SUM(fct_FinancialPeriod[CurrentContract]),
            fct_FinancialPeriod[MonthStart] = LastMonth))
)'''


def check_balance_values(row):
    from decimal import Decimal
    checks = []
    for name in ("Owner", "Sub", "Net", "Contract"):
        actual, expected = row.get(f"[{name}]"), row.get(f"[Expected{name}]")
        if actual is None or expected is None:
            raise AssertionError(f"{name}: balance evidence is missing; not verified")
        actual, expected = Decimal(str(actual)), Decimal(str(expected))
        if not actual.is_finite() or not expected.is_finite() or abs(actual - expected) >= Decimal("0.01"):
            raise AssertionError(f"{name}: model balance {actual} != fact balance {expected}")
        checks.append(f"{name} balance agrees with its fact aggregation within one cent")
    return checks


def check_spend_status(dataset_id, tok):
    import deploy_model as dm
    expression = next(m[1] for m in dm.MEASURES if m[0] == "Budget Status")
    cases = [("unknown", "BLANK()", None), ("zero_budget_gap", "0", "Spend within budget"),
             ("under_budget", "0.5", "Spend within budget"),
             ("small_overrun", "-0.03", "Spend over budget up to 5%"),
             ("boundary", "-0.05", "Spend over budget up to 5%"),
             ("larger_overrun", "-0.0501", "Spend over budget above 5%")]
    query = "EVALUATE ROW(" + ",".join(
        f'"{label}",' + expression.replace("[Budget Variance %]", value) for label, value, _ in cases) + ")"
    rows = dax(dataset_id, tok, query)
    if rows != [{f"[{label}]": expected for label, _, expected in cases}]:
        raise AssertionError("spend status did not preserve unknowns or the defined band boundaries")
    return dict(query=query, result=rows, scenarios=len(cases), passed=True)


def check_milestone_geometry(dataset_id, tok):
    import deploy_model as dm
    fixture = '''DEFINE TABLE __Milestones = UNION(
        ROW("ID","first","CurrentStart",DATE(2026,9,1),"CurrentFinish",DATE(2026,9,3)),
        ROW("ID","second","CurrentStart",DATE(2026,9,4),"CurrentFinish",DATE(2026,9,6)),
        ROW("ID","same_day","CurrentStart",DATE(2026,9,9),"CurrentFinish",DATE(2026,9,9)),
        ROW("ID","missing_start","CurrentStart",BLANK(),"CurrentFinish",DATE(2026,9,10)),
        ROW("ID","missing_finish","CurrentStart",DATE(2026,8,1),"CurrentFinish",BLANK()),
        ROW("ID","inverted","CurrentStart",DATE(2026,8,1),"CurrentFinish",DATE(2026,7,1))) '''
    cases = [("first", 0, 2), ("second", 3, 2), ("same_day", 8, 0),
             ("missing_start", None, None), ("missing_finish", None, None),
             ("inverted", None, None), ("absent", None, None), ("all", None, None)]
    checks = []
    for index, name in enumerate(("Milestone Offset Days", "Milestone Duration Days"), 1):
        expression = next(m[1] for m in dm.MEASURES if m[0] == name).replace("fct_Milestone", "__Milestones")
        query = fixture + f'EVALUATE SUMMARIZECOLUMNS(__Milestones[ID],"Actual",{expression},"Keep",1)'
        rows = dax(dataset_id, tok, query)
        actual = {row["__Milestones[ID]"]: row["[Actual]"] for row in rows}
        if actual != {case[0]: case[index] for case in cases[:-2]}:
            raise AssertionError(f"milestone geometry scenarios failed for {name}: {rows}")
        totals_query = fixture + ('EVALUATE ROW("all",' + expression + ',"absent",CALCULATE('
                                  + expression + ',FILTER(__Milestones,FALSE())))')
        totals = dax(dataset_id, tok, totals_query)
        if totals != [{"[all]": None, "[absent]": None}]:
            raise AssertionError(f"milestone geometry accepted multiple or missing records for {name}")
        checks.append(dict(measure=name, query=query, result=rows, totals_query=totals_query,
                           totals=totals, scenarios=len(cases), passed=True))
    return checks


# ---------------------------------------------------------------------------------------
# Independent measure checks. Raw fact columns are read through the model, the expected
# value is recomputed here in Python (never by calling the measure), and compared with the
# measure at portfolio, project, month and (monthly) scorecard-category grain. Filter
# propagation is re-derived from deploy_model.RELATIONSHIPS: one side filters many side.
# DAX semantics reproduced deliberately: SUM/COUNTROWS of nothing is BLANK, BLANK = FALSE,
# string equality ignores case, DIVIDE by blank/zero is BLANK.
# ---------------------------------------------------------------------------------------
from collections import namedtuple  # noqa: E402
from datetime import datetime, timedelta  # noqa: E402

Scope = namedtuple("Scope", "project month category")
PORTFOLIO = Scope(None, None, None)

RAW_COLUMNS = {
    "_Measures": ["_built_at"], "dim_Date": ["Date", "MonthStart"],
    "dim_Project": ["ProjectKey", "IsInCrosswalk"], "dim_CostCode": ["IsInSource"],
    "dim_ScorecardWeight": ["CategoryKey", "Weight"],
    "dim_ScorecardBand": ["CategoryKey", "MinValue", "MaxValue", "MatchValue", "Score", "BandLabel"],
    "fct_BudgetLine": ["BudgetAmount", "ForecastAmount", "CommittedAmount", "SpentToDate", "CostToComplete"],
    "fct_ChangeOrder": ["Amount", "IsPending"],
    "fct_Invoice": ["Amount", "AmountPaid", "Balance", "HasUnmatchedProject", "DaysToPayment"],
    "fct_RfiSubmittal": ["IsOpen", "IsPastDue", "ItemType", "DaysOpen"],
    "fct_Milestone": ["IsOverdue", "PercentComplete", "CurrentFinish", "HasDateInversion"],
    "fct_FinancialPeriod": ["OriginalContract", "CurrentContract", "PendingChangeOrders", "AgeOfOldestUnapprovedCO"],
    "fct_QualityItem": ["ItemType", "IsOpen", "IsPastDue", "DaysPastDue", "DaysOpen"],
    "fct_SafetyMonthly": ["RecordableIncidents", "HoursWorked"],
    "fct_Billing": ["RetainageHeld", "IsLatestPeriod", "BillingType", "CompletedToDate", "ContractSumToDate",
                    "BalanceToFinish", "CurrentPaymentDue", "StatusLabel"],
    "fct_DirectCost": ["GrandTotal", "CostType", "IsApproved"],
    "bridge_ProjectVendor": ["VendorKey", "IsMissingFromErp"],
    "bridge_VendorCostCode": ["VendorKey", "CostCodeKey", "Amount", "AmountType"],
    "fct_VendorInsurance": ["VendorKey", "ExpiryStatus"],
    "man_Flags": ["ProfitabilityCode"], "man_Survey": ["Score"], "man_Milestones": ["BaselineFinish"],
    "man_DailyLogCompliance": ["LogsMissedSameDay"],
    "dim_ProjectCrosswalk": ["SystemCount", "IsInSage", "IsInOutbuild"], "dim_VendorCrosswalk": ["IsInSage"],
    "meta_PipelineRun": ["RunAt", "Status", "Blocking", "Failing"], "dq_DataGap": ["Amount"],
    "qc_seed_Gate": [], "qc_seed_ChecklistItem": [], "qc_seed_Trade": [],
    "fct_QcNcr": ["IsOpen", "IsPastDue", "DaysOpen", "HasUnmappedTrade"],
    "fct_QcPunch": ["IsOpen", "DaysOpen", "HasUnmappedTrade"],
    "fct_QcSubmittal": ["IsOpen", "IsOverdue", "TurnaroundDays", "IsMockup"],
    "fct_ProcoreInspection": [], "fct_ProcoreInspectionItem": [],
    "man_QcDfow": ["RiskTier"], "man_QcItp": ["ResultCode"], "man_QcGate": ["StatusCode"],
    "man_QcSpecialInspection": [], "man_QcCommissioning": ["StatusCode"], "man_QcInspectorSignIn": [],
    "man_QcChecklistResult": ["ResultCode"], "man_QcDohResult": ["StatusCode"],
}
OWN_FILTER = {"dim_Project": ("ProjectKey", "project"), "dim_Date": ("MonthStart", "month"),
              "dim_ScorecardWeight": ("CategoryKey", "category")}
# Checked by a synthetic fixture instead (check_milestone_geometry): they need ALLSELECTED.
FIXTURE_ONLY = {"Milestone Offset Days", "Milestone Duration Days"}


def _ts(text):
    return None if text is None else datetime.fromisoformat(text)


def _eq(value, text):
    return isinstance(value, str) and value.casefold() == text.casefold()


def _sum(rows, column):
    values = [r[column] for r in rows if r[column] is not None]
    return sum(values) if values else None


def _avg(rows, column):
    values = [r[column] for r in rows if r[column] is not None]
    return sum(values) / len(values) if values else None


def _max(rows, column, key=None):
    values = [r[column] for r in rows if r[column] is not None]
    return max(values, key=key) if values else None


def _count(rows):
    return len(rows) or None


def _distinct(rows, column):
    return len({r[column] for r in rows}) or None


def _div(numerator, denominator):
    return None if numerator is None or not denominator else numerator / denominator


def _add(a, b, sign=1):
    return None if a is None and b is None else (a or 0) + sign * (b or 0)


def _zero(value):
    return 0 if value is None else value


def _hours(start, end):
    """DATEDIFF(..., HOUR) counts hour boundaries crossed, not elapsed hours."""
    floor = lambda t: t.replace(minute=0, second=0, microsecond=0)
    return int((floor(end) - floor(start)).total_seconds() // 3600)


class Recompute:
    def __init__(self, data, relationships):
        self.data, self.now, self.utcnow, self._cache = data, None, None, {}
        self.links = {}
        for fact, fcol, dim, dcol in relationships:
            if fact in data and dim in data:
                self.links.setdefault(fact, []).append((fcol, dim, dcol))

    def reached(self, table, s):
        own = OWN_FILTER.get(table)
        if own and getattr(s, own[1]) is not None:
            return True
        return any(self.reached(dim, s) for _, dim, _ in self.links.get(table, ()))

    def rows(self, table, s=PORTFOLIO):
        if (table, s) not in self._cache:
            out = self.data[table]
            own = OWN_FILTER.get(table)
            if own and getattr(s, own[1]) is not None:
                out = [r for r in out if r[own[0]] == getattr(s, own[1])]
            for fcol, dim, dcol in self.links.get(table, ()):
                if self.reached(dim, s):
                    keys = {r[dcol] for r in self.rows(dim, s)}
                    out = [r for r in out if r[fcol] in keys]
            self._cache[(table, s)] = out
        return self._cache[(table, s)]

    def latest(self, table, column, s):
        """SUMX(VALUES(ProjectKey), LASTNONBLANKVALUE(date, SUM(column)))."""
        months = {}
        for r in self.rows(table, s):
            months.setdefault(r["ProjectKey"], {}).setdefault(r["MonthStart"], []).append(r)
        values = []
        for by_month in months.values():
            nonblank = {m: _sum(rs, column) for m, rs in by_month.items()
                        if m is not None and _sum(rs, column) is not None}
            if nonblank:
                values.append(nonblank[max(nonblank)])
        return sum(values) if values else None

    def label(self, s):
        months = [_ts(r["MonthStart"]) for r in self.rows("dim_Date", s) if r["MonthStart"]]
        if not months:
            return ""
        low, high = min(months).strftime("%B %Y"), max(months).strftime("%B %Y")
        return low if low == high else f"{low} - {high}"

    def pipeline_status(self, s):
        runs = self.rows("meta_PipelineRun", s)
        last = _max(runs, "RunAt", key=_ts)
        if last is None:
            return "Unknown - no checked run"
        built = _max(self.rows("_Measures", s), "_built_at", key=_ts)
        latest = [r for r in self.data["meta_PipelineRun"] if r["RunAt"] == last]
        hours = _hours(_ts(last), _ts(self.utcnow))
        if built is not None and _ts(built) > _ts(last):
            return "Unvalidated - data built after last check"
        if any(not _eq(r["Status"], "ok") or (r["Blocking"] or 0) > 0 for r in latest):
            return "BLOCKED - validation failed"
        if hours < 0:
            return "Unknown - check timestamp is in the future"
        if hours > 72:
            return "STALE - no checked run in over 72 hours"
        if hours > 30:
            return "Late - no checked run in over 30 hours"
        if (_sum(latest, "Failing") or 0) > 0:
            return "Gold checked with warnings; source completeness unverified"
        return "Gold checks passed; source completeness unverified"


def _shared_expected():
    return {
        "Last Refresh": lambda c, s: _max(c.rows("_Measures", s), "_built_at", key=_ts),
        "Report Month Label": lambda c, s: c.label(s),
        "Last Checked Run": lambda c, s: _max(c.rows("meta_PipelineRun", s), "RunAt", key=_ts),
        "Hours Since Last Checked Run": lambda c, s: (
            None if (last := _max(c.rows("meta_PipelineRun", s), "RunAt", key=_ts)) is None
            else _hours(_ts(last), _ts(c.now))),
        "Pipeline Status": lambda c, s: c.pipeline_status(s),
        "Data Gaps": lambda c, s: len(c.rows("dq_DataGap", s)),
        "Data Gap Amount": lambda c, s: _sum(c.rows("dq_DataGap", s), "Amount"),
    }


def monthly_expected():
    R = lambda c, table, s, keep=lambda r: True: [r for r in c.rows(table, s) if keep(r)]
    true = lambda column: lambda r: r[column] is True
    false = lambda column: lambda r: not r[column]
    latest_owner = lambda r: r["IsLatestPeriod"] is True and _eq(r["BillingType"], "Owner")
    E = _shared_expected()

    def billed_cumulative(c, s):
        dates = [r["Date"] for r in c.rows("dim_Date", s) if r["Date"]]
        if not dates:
            return None
        end = max(_ts(d) for d in dates)
        valid = {r["Date"] for r in c.data["dim_Date"] if r["Date"] and _ts(r["Date"]) <= end}
        return _sum([r for r in c.rows("fct_Billing", s._replace(month=None))
                     if r["MonthStart"] in valid and _eq(r["BillingType"], "Owner")
                     and not _eq(r["StatusLabel"], "DRAFT")], "CurrentPaymentDue")

    def mom(c, s):
        if s.month is None:
            return NotImplemented  # DATEADD over a multi-month range is not a month-on-month figure
        start = _ts(s.month)
        prior = (start.replace(day=1) - timedelta(days=1)).replace(day=1).isoformat()
        prior_total = _sum(c.rows("fct_Invoice", s._replace(month=prior)), "Amount")
        return _div(_add(E["Total Billed"](c, s), prior_total, -1), prior_total)

    def band(c, key, value, match=False):
        if value is None:
            return None
        scores = [b["Score"] for b in c.data["dim_ScorecardBand"] if b["CategoryKey"] == key and (
            _eq(b["MatchValue"], value) if match else
            (b["MinValue"] is None or value >= b["MinValue"]) and (b["MaxValue"] is None or value < b["MaxValue"]))]
        scores = [x for x in scores if x is not None]
        return max(scores) if scores else None

    def scores(c, s):
        return {1: band(c, 1, E["Avg Days To Payment"](c, s)),
                2: band(c, 2, E["Profitability Code"](c, s), match=True),
                3: band(c, 3, E["Cash Position %"](c, s)),
                4: band(c, 4, E["Age Of Oldest Unapproved CO"](c, s)),
                5: band(c, 5, E["Recordable Incidents"](c, s)),
                6: band(c, 6, E["Schedule Performance %"](c, s)),
                7: band(c, 7, E["Completion Variance Days"](c, s)),
                8: band(c, 8, E["Avg Observation Days Open"](c, s)),
                9: band(c, 9, E["Daily Reports Missed"](c, s))}

    def scorecard(c, s, weighted=True):
        weights = c.data["dim_ScorecardWeight"]  # ALL(dim_ScorecardWeight)
        if not weights:
            return None
        found = scores(c, s)
        total = sum(0 if found.get(w["CategoryKey"]) is None
                    else (found[w["CategoryKey"]] * w["Weight"] if weighted else w["Weight"]) for w in weights)
        return total / 3 if weighted else total

    def selected_category(c, s):
        keys = {r["CategoryKey"] for r in c.rows("dim_ScorecardWeight", s)}
        return keys.pop() if len(keys) == 1 else None

    def category_score(c, s):
        key = selected_category(c, s)
        return None if key is None else scores(c, s).get(key)

    def category_band(c, s):
        score, key = category_score(c, s), selected_category(c, s)
        if score is None:
            return "Not measured"
        labels = [b["BandLabel"] for b in c.data["dim_ScorecardBand"]
                  if b["CategoryKey"] == key and b["Score"] == score and b["BandLabel"] is not None]
        return max(labels) if labels else None

    def projects_at_risk(c, s):
        count = 0
        for p in c.rows("dim_Project", s):
            if p["ProjectKey"] is None:
                continue
            value = E["Project Scorecard (Measured Only)"](c, s._replace(project=p["ProjectKey"]))
            count += value is not None and value < 0.6
        return count or None

    def vendors_without_insurance(c, s):
        insured = {r["VendorKey"] for r in c.rows("fct_VendorInsurance", s)}
        return len({r["VendorKey"] for r in c.rows("bridge_ProjectVendor", s)} - insured)

    def completion_variance(c, s):
        baseline = _max(c.rows("man_Milestones", s), "BaselineFinish", key=_ts)
        forecast = _max(c.rows("fct_Milestone", s), "CurrentFinish", key=_ts)
        return None if baseline is None or forecast is None else (_ts(forecast).date() - _ts(baseline).date()).days

    def budget_status(c, s):
        v = E["Budget Variance %"](c, s)
        return (None if v is None else "Spend within budget" if v >= 0
                else "Spend over budget up to 5%" if v >= -0.05 else "Spend over budget above 5%")

    def selected(rows, column):
        values = {r[column] for r in rows}
        return values.pop() if len(values) == 1 else None

    budget = lambda column: lambda c, s: _sum(c.rows("fct_BudgetLine", s), column)
    E.update({
        "Original Contract": lambda c, s: c.latest("fct_FinancialPeriod", "OriginalContract", s),
        "Current Contract": lambda c, s: c.latest("fct_FinancialPeriod", "CurrentContract", s),
        "Pending Change Orders": lambda c, s: c.latest("fct_FinancialPeriod", "PendingChangeOrders", s),
        "Contract Growth %": lambda c, s: _div(_add(E["Current Contract"](c, s), E["Original Contract"](c, s), -1),
                                              E["Original Contract"](c, s)),
        "Age Of Oldest Unapproved CO": lambda c, s: _max(c.rows("fct_FinancialPeriod", s), "AgeOfOldestUnapprovedCO"),
        "Approved Change Orders": lambda c, s: _sum(R(c, "fct_ChangeOrder", s, false("IsPending")), "Amount"),
        "Change Order Amount": lambda c, s: _sum(c.rows("fct_ChangeOrder", s), "Amount"),
        "Budget": budget("BudgetAmount"), "Forecast": budget("ForecastAmount"),
        "Committed": budget("CommittedAmount"), "Spent To Date": budget("SpentToDate"),
        "Cost To Complete": budget("CostToComplete"),
        "Budget Variance": lambda c, s: _add(E["Budget"](c, s), E["Spent To Date"](c, s), -1),
        "Budget Variance %": lambda c, s: _div(E["Budget Variance"](c, s), E["Budget"](c, s)),
        "Budget Status": budget_status,
        "Percent Bought Out": lambda c, s: _div(E["Committed"](c, s), E["Budget"](c, s)),
        "Blocking Violations Last Run": lambda c, s: _zero(_sum(
            [r for r in c.rows("meta_PipelineRun", s) if r["RunAt"] == E["Last Checked Run"](c, s)], "Blocking")),
        "Vendor Spend": lambda c, s: _sum(R(c, "bridge_VendorCostCode", s, lambda r: _eq(r["AmountType"], "Actual")), "Amount"),
        "Vendor Committed": lambda c, s: _sum(R(c, "bridge_VendorCostCode", s, lambda r: _eq(r["AmountType"], "Committed")), "Amount"),
        "Cost Codes Per Vendor": lambda c, s: _zero(_distinct(c.rows("bridge_VendorCostCode", s), "CostCodeKey")),
        "Vendors Per Cost Code": lambda c, s: _zero(_distinct(c.rows("bridge_VendorCostCode", s), "VendorKey")),
        "Certificates On File": lambda c, s: len(c.rows("fct_VendorInsurance", s)),
        "Vendors With Insurance": lambda c, s: _zero(_distinct(c.rows("fct_VendorInsurance", s), "VendorKey")),
        "Expired Certificates": lambda c, s: len(R(c, "fct_VendorInsurance", s, lambda r: _eq(r["ExpiryStatus"], "Expired"))),
        "Certificates Expiring Soon": lambda c, s: len(R(c, "fct_VendorInsurance", s,
                                                         lambda r: _eq(r["ExpiryStatus"], "Expiring within 30 days"))),
        "Vendors Without Insurance": vendors_without_insurance,
        "Retainage Held Owner": lambda c, s: _sum(R(c, "fct_Billing", s, lambda r: r["IsLatestPeriod"] is True
                                                     and _eq(r["BillingType"], "Owner")), "RetainageHeld"),
        "Retainage Held Sub": lambda c, s: _sum(R(c, "fct_Billing", s, lambda r: r["IsLatestPeriod"] is True
                                                   and _eq(r["BillingType"], "Subcontractor")), "RetainageHeld"),
        "Net Retainage Position": lambda c, s: _add(E["Retainage Held Owner"](c, s), E["Retainage Held Sub"](c, s), -1),
        "Owner Billed To Date": lambda c, s: _sum(R(c, "fct_Billing", s, latest_owner), "CompletedToDate"),
        "Owner Contract Sum": lambda c, s: _sum(R(c, "fct_Billing", s, latest_owner), "ContractSumToDate"),
        "Balance To Finish": lambda c, s: _sum(R(c, "fct_Billing", s, latest_owner), "BalanceToFinish"),
        "Billed This Period": lambda c, s: _sum(R(c, "fct_Billing", s, lambda r: _eq(r["BillingType"], "Owner")
                                                 and not _eq(r["StatusLabel"], "DRAFT")), "CurrentPaymentDue"),
        "Billing Periods": lambda c, s: len(c.rows("fct_Billing", s)),
        "Draft Billings": lambda c, s: len(R(c, "fct_Billing", s, lambda r: _eq(r["StatusLabel"], "DRAFT"))),
        "Direct Costs": lambda c, s: _sum(c.rows("fct_DirectCost", s), "GrandTotal"),
        "Self Performed Labour": lambda c, s: _sum(R(c, "fct_DirectCost", s, lambda r: _eq(r["CostType"], "payroll")), "GrandTotal"),
        "Unapproved Direct Costs": lambda c, s: _sum(R(c, "fct_DirectCost", s, false("IsApproved")), "GrandTotal"),
        "Vendors On Project": lambda c, s: _zero(_distinct(c.rows("bridge_ProjectVendor", s), "VendorKey")),
        "Vendors Missing From ERP": lambda c, s: _zero(_distinct(R(c, "bridge_ProjectVendor", s, true("IsMissingFromErp")), "VendorKey")),
        "Total Billed": lambda c, s: _sum(c.rows("fct_Invoice", s), "Amount"),
        "Total Paid": lambda c, s: _sum(c.rows("fct_Invoice", s), "AmountPaid"),
        "AR Outstanding": lambda c, s: _sum(c.rows("fct_Invoice", s), "Balance"),
        "Total Billed %": lambda c, s: _div(E["Total Billed"](c, s), E["Current Contract"](c, s)),
        "Total Billed MoM %": mom,
        "Open Submittals": lambda c, s: _count(R(c, "fct_RfiSubmittal", s, lambda r: r["IsOpen"] is True and _eq(r["ItemType"], "Submittal"))),
        "Open Submittals Past Due": lambda c, s: _count(R(c, "fct_RfiSubmittal", s, lambda r: r["IsPastDue"] is True and _eq(r["ItemType"], "Submittal"))),
        "Avg Days Open": lambda c, s: _avg(c.rows("fct_RfiSubmittal", s), "DaysOpen"),
        "Critical Milestones": lambda c, s: _count(c.rows("fct_Milestone", s)),
        "Overdue Milestones": lambda c, s: _count(R(c, "fct_Milestone", s, true("IsOverdue"))),
        "Schedule Performance %": lambda c, s: _div(E["Overdue Milestones"](c, s), E["Critical Milestones"](c, s)),
        "Avg Milestone Progress": lambda c, s: _avg(c.rows("fct_Milestone", s), "PercentComplete"),
        "Punchlist Items": lambda c, s: len(R(c, "fct_QualityItem", s, lambda r: _eq(r["ItemType"], "PunchItem"))),
        "Open Quality Items": lambda c, s: len(R(c, "fct_QualityItem", s, true("IsOpen"))),
        "Quality Items Past Due": lambda c, s: len(R(c, "fct_QualityItem", s, true("IsPastDue"))),
        "Avg Days Past Due": lambda c, s: _avg(R(c, "fct_QualityItem", s, true("IsPastDue")), "DaysPastDue"),
        "Projects Fully Mapped": lambda c, s: len(R(c, "dim_ProjectCrosswalk", s, lambda r: r["SystemCount"] == 3)),
        "Projects In Coverage": lambda c, s: _count(c.rows("dim_ProjectCrosswalk", s)),
        "Projects Missing From Sage": lambda c, s: len(R(c, "dim_ProjectCrosswalk", s, false("IsInSage"))),
        "Projects Missing From Outbuild": lambda c, s: len(R(c, "dim_ProjectCrosswalk", s, false("IsInOutbuild"))),
        "Source Coverage %": lambda c, s: _div(E["Projects Fully Mapped"](c, s), _count(c.rows("dim_ProjectCrosswalk", s))),
        "Vendors Missing From Sage": lambda c, s: len(R(c, "dim_VendorCrosswalk", s, false("IsInSage"))),
        "DQ Projects Without Crosswalk": lambda c, s: _count(R(c, "dim_Project", s, false("IsInCrosswalk"))),
        "DQ Cost Codes Not In Source": lambda c, s: _count(R(c, "dim_CostCode", s, false("IsInSource"))),
        "DQ Milestones With Inverted Dates": lambda c, s: _count(R(c, "fct_Milestone", s, true("HasDateInversion"))),
        "DQ Unmatched Invoices": lambda c, s: _count(R(c, "fct_Invoice", s._replace(project=None), true("HasUnmatchedProject"))),
        "Unmatched AR Amount - All Projects": lambda c, s: _sum(R(c, "fct_Invoice", s._replace(project=None),
                                                                 true("HasUnmatchedProject")), "Amount"),
        "Billed Cumulative": billed_cumulative,
        "Billed Cumulative % Of Contract": lambda c, s: _div(billed_cumulative(c, s), E["Current Contract"](c, s)),
        "Projects Reporting": lambda c, s: _count(c.rows("dim_Project", s)),
        "Projects At Risk": projects_at_risk,
        "Avg Days To Payment": lambda c, s: _avg(c.rows("fct_Invoice", s), "DaysToPayment"),
        "Cash Position %": lambda c, s: _div(_add(E["Total Paid"](c, s), E["AR Outstanding"](c, s)), E["Cost To Complete"](c, s)),
        "Profitability Code": lambda c, s: selected(c.rows("man_Flags", s), "ProfitabilityCode"),
        "Recordable Incidents": lambda c, s: _zero(_sum(c.rows("fct_SafetyMonthly", s), "RecordableIncidents")),
        "Hours Worked": lambda c, s: _zero(_sum(c.rows("fct_SafetyMonthly", s), "HoursWorked")),
        "Observations": lambda c, s: len(R(c, "fct_QualityItem", s, lambda r: _eq(r["ItemType"], "Observation"))),
        "Avg Observation Days Open": lambda c, s: _avg(R(c, "fct_QualityItem", s, false("IsOpen")), "DaysOpen"),
        "Daily Reports Missed": lambda c, s: _sum(c.rows("man_DailyLogCompliance", s), "LogsMissedSameDay"),
        "Completion Variance Days": completion_variance,
        "Client Satisfaction": lambda c, s: _div(_sum(c.rows("man_Survey", s), "Score"),
                                                 _count(c.rows("man_Survey", s)) and 5 * len(c.rows("man_Survey", s))),
        "Project Scorecard": scorecard,
        "Scorecard Coverage %": lambda c, s: scorecard(c, s, weighted=False),
        "Project Scorecard (Measured Only)": lambda c, s: _div(scorecard(c, s), scorecard(c, s, weighted=False)),
        "Category Score": category_score,
        "Category Weighted": lambda c, s: (None if (score := category_score(c, s)) is None
                                           else score * selected(c.rows("dim_ScorecardWeight", s), "Weight") / 3),
        "Category Band": category_band,
    })
    for number, name in enumerate(("Accounts Receivable", "Profitability", "Cash Position", "Change Orders",
                                   "Safety Incidents", "Schedule Performance", "Completion Variance",
                                   "Observations", "Daily Reports"), 1):
        E[f"Score - {name}"] = lambda c, s, n=number: scores(c, s)[n]
    return E


def qc_expected():
    R = lambda c, table, s, keep: [r for r in c.rows(table, s) if keep(r)]
    true = lambda column: lambda r: r[column] is True
    false = lambda column: lambda r: not r[column]
    registers = ("man_QcDfow", "man_QcItp", "man_QcGate", "man_QcSpecialInspection", "man_QcCommissioning",
                 "man_QcInspectorSignIn", "man_QcChecklistResult", "man_QcDohResult")

    def completion(recorded_table, done, defined_table):
        def expected(c, s):
            recorded, defined = len(c.rows(recorded_table, s)), len(c.rows(defined_table, s))
            completed = len(R(c, recorded_table, s, done))
            if s.project is None or not (0 < recorded <= defined and completed <= recorded):
                return None
            return completed / defined
        return expected

    E = _shared_expected()
    count = lambda table, keep=lambda r: True: lambda c, s: _count(R(c, table, s, keep))
    E.update({
        "Projects With Quality Data": lambda c, s: _distinct(c.rows("fct_QcNcr", s._replace(project=None)), "ProjectKey"),
        "Total Observations": count("fct_QcNcr"),
        "Open Observations": count("fct_QcNcr", true("IsOpen")),
        "Closed Observations": count("fct_QcNcr", false("IsOpen")),
        "Observations Past Due": count("fct_QcNcr", true("IsPastDue")),
        "Avg Observation Closure Days": lambda c, s: _avg(R(c, "fct_QcNcr", s, false("IsOpen")), "DaysOpen"),
        "Observation Closure Rate": lambda c, s: _div(E["Closed Observations"](c, s), E["Total Observations"](c, s)),
        "Total Punch Items": count("fct_QcPunch"),
        "Open Punch Items": count("fct_QcPunch", true("IsOpen")),
        "Punch Items Aged Over 7 Days": count("fct_QcPunch", lambda r: r["IsOpen"] is True and (r["DaysOpen"] or 0) > 7),
        "Punch Closure Rate": lambda c, s: _div(E["Total Punch Items"](c, s) and _count(R(c, "fct_QcPunch", s, false("IsOpen"))),
                                                E["Total Punch Items"](c, s)),
        "Avg Days Punch Open": lambda c, s: _avg(R(c, "fct_QcPunch", s, true("IsOpen")), "DaysOpen"),
        "Total Submittals": count("fct_QcSubmittal"),
        "Open Submittals": count("fct_QcSubmittal", true("IsOpen")),
        "Overdue Submittals": count("fct_QcSubmittal", true("IsOverdue")),
        "Avg Submittal Turnaround": lambda c, s: _avg(c.rows("fct_QcSubmittal", s), "TurnaroundDays"),
        "Possible Mock-Ups": count("fct_QcSubmittal", true("IsMockup")),
        "Native Inspections": count("fct_ProcoreInspection"),
        "Native Inspection Items": count("fct_ProcoreInspectionItem"),
        "Gates Defined": count("qc_seed_Gate"), "Gates Recorded": count("man_QcGate"),
        "Gates Complete": count("man_QcGate", lambda r: _eq(r["StatusCode"], "COMPLETE")),
        "Gate Template Completion": completion("man_QcGate", lambda r: _eq(r["StatusCode"], "COMPLETE"), "qc_seed_Gate"),
        "Checklist Items Defined": count("qc_seed_ChecklistItem"),
        "Checklist Items Recorded": count("man_QcChecklistResult"),
        "Checklist Items Passed": count("man_QcChecklistResult", lambda r: _eq(r["ResultCode"], "PASS")),
        "Checklist Items Failed": count("man_QcChecklistResult", lambda r: _eq(r["ResultCode"], "FAIL")),
        "Checklist Template Completion": completion("man_QcChecklistResult", lambda r: _eq(r["ResultCode"], "PASS"),
                                                    "qc_seed_ChecklistItem"),
        "DFOWs Registered": count("man_QcDfow"),
        "Tier 3 And 4 DFOWs": count("man_QcDfow", lambda r: (r["RiskTier"] or 0) >= 3),
        "ITP Tests Defined": count("man_QcItp"),
        "ITP Tests Passed": count("man_QcItp", lambda r: _eq(r["ResultCode"], "PASS")),
        "Special Inspections Logged": count("man_QcSpecialInspection"),
        "Inspector Visits Logged": count("man_QcInspectorSignIn"),
        "Systems Accepted": count("man_QcCommissioning", lambda r: _eq(r["StatusCode"], "ACCEPTED")),
        "DOH Items Verified": count("man_QcDohResult", lambda r: _eq(r["StatusCode"], "VERIFIED")),
        "DQ Observations With Unmapped Trade": count("fct_QcNcr", true("HasUnmappedTrade")),
        "DQ Punch With Unmapped Trade": count("fct_QcPunch", true("HasUnmappedTrade")),
        "DQ Registers Awaiting Input": lambda c, s: (
            f"{sum(not c.rows(t, s) for t in registers)}/8 registers empty; completeness unverified"),
    })
    return E


def same_value(actual, expected) -> bool:
    """BLANK is never 0; numbers agree to a millionth (relative) or 1e-6 (absolute)."""
    import math
    if actual is None or expected is None:
        return actual is expected
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)) \
            and not isinstance(actual, bool) and not isinstance(expected, bool):
        return math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-6)
    return actual == expected


def compare_measure_observations(expected, data, relationships, observations, manual_inputs=None):
    """observations: [(grain, Scope, now, utcnow, {measure: value})]. Returns per-measure results."""
    recompute = Recompute(data, relationships)
    results = {}
    for grain, scope, now, utcnow, values in observations:
        recompute.now, recompute.utcnow = now, utcnow
        for measure, actual in values.items():
            result = results.setdefault(measure, dict(grains={}, mismatches=[]))
            want = expected[measure](recompute, scope)
            if want is NotImplemented:
                continue
            counts = result["grains"].setdefault(grain, 0)
            result["grains"][grain] = counts + 1
            if grain == "portfolio":
                result.update(measure_value=actual, independent_value=want)
            if not same_value(actual, want):
                result["mismatches"].append(dict(grain=grain, scope=scope._asdict(), measure=actual, independent=want))
    for measure, result in results.items():
        result["status"] = "FAIL" if result["mismatches"] or not result["grains"] else "PASS"
        empty = [t for t in (manual_inputs or {}).get(measure, []) if not data.get(t)]
        if empty and result.get("measure_value") is None and not result["mismatches"]:
            result["note"] = "unmeasured - no input (" + ", ".join(empty) + " empty)"
        result["mismatch_count"] = len(result["mismatches"])
        result["mismatches"] = result["mismatches"][:5]
    return results


def check_independent_measures(dataset_id, tok, kind):
    """Live wrapper: read raw columns and measure values, then compare. Returns evidence."""
    import re
    import deploy_model as dm
    expected = qc_expected() if kind == "qc" else monthly_expected()
    present = {r["[n]"] for r in dax(dataset_id, tok, 'EVALUATE SELECTCOLUMNS(INFO.VIEW.TABLES(),"n",[Name])')}
    tables = [t for t in ["_Measures", *dm.MODEL_TABLES] if t in RAW_COLUMNS and t in present]
    columns = {t: list(RAW_COLUMNS[t]) for t in tables}
    for fact, fcol, dim, dcol in dm.RELATIONSHIPS:
        if fact in columns and dim in columns:
            columns[fact].append(fcol)
            columns[dim].append(dcol)
    data = {}
    for table in tables:
        cols = sorted(set(columns[table])) or None
        query = (f"EVALUATE SELECTCOLUMNS('{table}'," + ",".join(f'"{c}",\'{table}\'[{c}]' for c in cols) + ")"
                 if cols else f"EVALUATE ROW(\"n\",COUNTROWS('{table}'))")
        rows = dax(dataset_id, tok, query)
        data[table] = ([{k.strip("[]"): v for k, v in r.items()} for r in rows] if cols
                       else [{}] * (rows[0]["[n]"] or 0))
    deployed = {r["[n]"] for r in dax(dataset_id, tok, 'EVALUATE SELECTCOLUMNS(INFO.VIEW.MEASURES(),"n",[Name])')}
    definitions = {m[0]: m[1] for m in dm.MEASURES}
    names = [m for m in definitions if m in deployed and m in expected and m not in FIXTURE_ONLY]
    grains = [("portfolio", None, None), ("project", "dim_Project[ProjectKey]", "project"),
              ("month", "dim_Date[MonthStart]", "month")]
    if kind != "qc":
        grains.append(("category", "dim_ScorecardWeight[CategoryKey]", "category"))
    observations, skipped_blank_project = [], 0
    for start in range(0, len(names), 20):
        chunk = names[start:start + 20]
        fields = '"__now",NOW(),"__utcnow",UTCNOW(),' + ",".join(f'"m{i}",[{m}]' for i, m in enumerate(chunk))
        for grain, column, field in grains:
            query = f"EVALUATE ROW({fields})" if column is None else f"EVALUATE ADDCOLUMNS(VALUES({column}),{fields})"
            for row in dax(dataset_id, tok, query):
                scope = PORTFOLIO if column is None else Scope(**{**PORTFOLIO._asdict(), field: row[column]})
                if column and row[column] is None:
                    skipped_blank_project += 1  # the unknown member stands for orphan keys, not a real project
                    continue
                observations.append((grain, scope, row["[__now]"], row["[__utcnow]"],
                                     {m: row[f"[m{i}]"] for i, m in enumerate(chunk)}))
    manual = {m: sorted(set(re.findall(r"\bman_\w+", definitions[m]))) for m in names}
    results = compare_measure_observations(expected, data, dm.RELATIONSHIPS, observations, manual)
    return dict(
        results=results,
        not_deployed=sorted(set(definitions) - deployed),
        tables_not_deployed=sorted(set(dm.MODEL_TABLES) - present),
        deployed_not_generated=sorted(deployed - set(definitions)),
        without_independent_check=sorted(set(definitions) - set(expected) - FIXTURE_ONLY),
        fixture_only=sorted(FIXTURE_ONLY & set(definitions)),
        blank_member_rows_skipped=skipped_blank_project,
        raw_row_counts={t: len(v) for t, v in data.items()},
        failed=sorted(m for m, r in results.items() if r["status"] == "FAIL"))


def pbi_token() -> str:
    result = subprocess.run(
        [dp.az_path(), "account", "get-access-token",
         "--resource", "https://analysis.windows.net/powerbi/api",
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise dp.FabricError(f"Power BI token failed: {result.stderr.strip()[:200]}")
    return result.stdout.strip()


def dax(dataset_id: str, tok: str, query: str) -> list[dict]:
    request = urllib.request.Request(
        f"{PBI_API}/datasets/{dataset_id}/executeQueries",
        method="POST",
        data=json.dumps({"queries": [{"query": query}],
                         "serializerSettings": {"includeNulls": True}}).encode(),
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode())
        # HTTP 200 can contain partial rows AND an error at any of these three levels.
        node = body
        for child in ("results", "tables", "rows"):
            if not isinstance(node, dict):
                raise dp.FabricError("DAX response has an invalid result structure")
            if node.get("error") is not None:
                raise dp.FabricError(f"DAX response reports an error: {json.dumps(node['error'])[:800]}")
            values = node.get(child)
            if not isinstance(values, list) or any(not isinstance(value, dict) for value in values):
                raise dp.FabricError(f"DAX response has invalid or missing {child}")
            if child == "rows":
                return values
            if len(values) != 1:
                raise dp.FabricError(f"DAX response must contain exactly one {child} entry")
            node = values[0]
    except urllib.error.HTTPError as exc:
        raise dp.FabricError(f"DAX failed ({exc.code}): {exc.read().decode()[:400]}\n{query[:200]}") from exc


def reframe(dataset_id: str, tok: str, timeout: int = 300) -> dict:
    """Refresh (reframe) the Direct Lake model, then wait for it to finish.

    A newly deployed Direct Lake model holds a correct definition but is not yet bound to
    the Delta files. Until it is reframed every table is invisible to DAX - queries fail
    with "Failed to resolve name 'dim_Date'", which reads like a broken model rather than
    an unrefreshed one. The definition being right is not the same as the model being
    loaded.
    """
    from urllib.parse import urlsplit

    request = urllib.request.Request(
        f"{PBI_API}/datasets/{dataset_id}/refreshes",
        method="POST",
        data=json.dumps({"type": "full"}).encode(),
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            location = response.headers.get("Location")
            request_id = (urlsplit(location).path.rstrip("/").split("/")[-1] if location
                          else response.headers.get("x-ms-request-id"))
    except urllib.error.HTTPError as exc:
        raise dp.FabricError(f"refresh failed ({exc.code}): {exc.read().decode()[:300]}") from exc

    if not request_id:
        raise dp.FabricError("refresh accepted without a tracking ID; inspect history before submitting another refresh")
    return wait_refresh(dataset_id, tok, request_id, timeout)


def wait_refresh(dataset_id: str, tok: str, request_id: str, timeout: int = 300) -> dict:
    """Observe one accepted request; safe to resume after an observation timeout."""
    import time
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        poll = urllib.request.Request(
            f"{PBI_API}/datasets/{dataset_id}/refreshes",
            headers={"Authorization": f"Bearer {tok}"},
        )
        with urllib.request.urlopen(poll, timeout=60) as response:
            runs = json.loads(response.read().decode()).get("value", [])
        matches = [run for run in runs if run.get("requestId") == request_id]
        if len(matches) > 1:
            raise dp.FabricError(f"ambiguous refresh history for request {request_id}")
        run = matches[0] if matches else {}
        status = run.get("status", "Unknown")
        if status == "Completed":
            return run
        if status in ("Failed", "Cancelled", "Disabled"):
            raise dp.FabricError(f"refresh {request_id} {status}: {run.get('serviceExceptionJson')}")
        time.sleep(5)
    raise dp.FabricError(f"refresh {request_id} not verified within {timeout}s; resume wait_refresh for this ID, do not resubmit")


def expected_counts(lakehouse_id: str) -> dict[str, int]:
    """Model-to-lakehouse reconciliation; these diagnostics are not a source completeness proof."""
    import deploy_gold as dg
    gold = dg.fetch_diagnostics(lakehouse_id, "gold_run.json")
    seeds = dg.fetch_diagnostics(lakehouse_id, "seed_run.json")
    if not gold or any(not step.get("ok") for step in gold):
        raise RuntimeError("gold build diagnostics are missing or report failure")
    verified = [step for step in gold if step.get("step") == "verification"]
    if len(verified) != 1 or verified[0].get("findings"):
        raise RuntimeError("gold verification is missing, ambiguous, or has findings")
    if not seeds or seeds.get("findings") or seeds.get("counts") != seeds.get("expected"):
        raise RuntimeError("seed verification is missing or inconsistent")
    counts = dict(verified[0]["counts"])
    counts["dim_Date"] = seeds["counts"]["dim_Date"]
    tables = dict(Projects="dim_Project", Vendors="dim_Vendor", CostCodes="dim_CostCode",
                  Dates="dim_Date", BudgetLines="fct_BudgetLine", ChangeOrders="fct_ChangeOrder",
                  Invoices="fct_Invoice", Submittals="fct_RfiSubmittal", Milestones="fct_Milestone",
                  Periods="fct_FinancialPeriod", Billings="fct_Billing", DirectCosts="fct_DirectCost",
                  ProjectVendors="bridge_ProjectVendor")
    result = {}
    for label, table in tables.items():
        value = counts.get(table)
        if type(value) is not int or value < 0:
            raise RuntimeError(f"invalid or absent build count for {table}: {value!r}")
        result[f"[{label}]"] = value
    return result


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    # With Direct Lake automatic update off, a refresh IS a publish: it shows readers whatever
    # gold holds now, gated or not. Publishing belongs to cd_50_publish_models; candidate
    # models are reframed by validate_candidate_model.py.
    parser.add_argument("--allow-production-reframe", action="store_true",
                        help="refresh the PRODUCTION model before validating (out-of-band publish)")
    args = parser.parse_args()
    tok_fabric = dp.token()
    model = ds.find_item(tok_fabric, MODEL_NAME, "SemanticModel")
    if not model:
        print(f"ERROR: semantic model {MODEL_NAME!r} not found - run deploy_model.py --apply")
        return 1
    print(f"model {model['id']}")

    tok = pbi_token()

    if args.allow_production_reframe:
        print("  reframing PRODUCTION ...", end=" ", flush=True)
        print(reframe(model["id"], tok))
    else:
        print("  not reframing production - validating the release it currently shows "
              "(--allow-production-reframe to override)")

    # 1. Row counts straight from the model. If DirectLake is not wired to the lakehouse,
    #    these come back zero or the query errors - either way we find out here rather
    #    than from a blank report.
    rows = dax(model["id"], tok, """
        EVALUATE
        ROW(
            "Projects",     COUNTROWS ( dim_Project ),
            "Vendors",      COUNTROWS ( dim_Vendor ),
            "CostCodes",    COUNTROWS ( dim_CostCode ),
            "Dates",        COUNTROWS ( dim_Date ),
            "BudgetLines",  COUNTROWS ( fct_BudgetLine ),
            "ChangeOrders", COUNTROWS ( fct_ChangeOrder ),
            "Invoices",     COUNTROWS ( fct_Invoice ),
            "Submittals",   COUNTROWS ( fct_RfiSubmittal ),
            "Milestones",   COUNTROWS ( fct_Milestone ),
            "Periods",      COUNTROWS ( fct_FinancialPeriod ),
            "Billings",     COALESCE ( COUNTROWS ( fct_Billing ), 0 ),
            "DirectCosts",  COALESCE ( COUNTROWS ( fct_DirectCost ), 0 ),
            "ProjectVendors", COALESCE ( COUNTROWS ( bridge_ProjectVendor ), 0 )
        )
    """)[0]
    # Compare with the actual source build diagnostics, not historical hardcoded totals.
    # This checks the model against its lakehouse; it does not certify upstream completeness.
    expected = expected_counts(ds.lakehouse()["id"])

    bad = []
    for key, want in expected.items():
        got = rows.get(key)
        print(f"  {key[1:-1]:<14} {got:>7}  (expected {want})")
        if got != want:
            bad.append(f"{key}: got {got}, expected {want}")
    if bad:
        print("\nROW COUNT MISMATCH:\n  " + "\n  ".join(bad))
        print("Model-to-build count differences remain unresolved; continuing independent checks.")
    # Counted, not typed. A hardcoded number here goes stale the first time a table is
    # added and then quietly understates what was actually checked.
    if not bad:
        CHECKS.append(f"all {len(expected)} tables readable through DirectLake "
                      "at the expected row counts")

    # 1b. EVERY table in the model must resolve, not just the ones with a row-count
    #     baseline. This exists because of a failure that cost an hour:
    #
    #     A brand-new gold table is written to the lakehouse, deploy_model generates its
    #     TMDL correctly, the model deploys with no error at all - and Direct Lake still
    #     cannot bind it, because the SQL endpoint has not yet discovered the new Delta
    #     table. The model then contains a table reference that resolves to nothing, and
    #     every measure over it deploys perfectly and fails only when a visual renders,
    #     with "the value cannot be determined". Nothing before this point says a word.
    #
    #     Checking COUNTROWS on all of them turns a render-time mystery into a deploy-time
    #     failure. It costs one cheap query per table.
    from deploy_model import MODEL_TABLES  # noqa: PLC0415

    unresolved = []
    for table in MODEL_TABLES:
        try:
            dax(model["id"], tok, f'EVALUATE ROW ( "n", COUNTROWS ( {table} ) )')
        except Exception as exc:  # noqa: BLE001 - the message is what matters
            unresolved.append(f"{table}: {str(exc)[:120]}")
    assert not unresolved, (
        f"{len(unresolved)} model table(s) do not resolve - Direct Lake has not bound "
        "them. New tables can need a minute for the SQL endpoint to discover them; "
        "re-run deploy_model.py --apply.\n  " + "\n  ".join(unresolved[:5]))
    CHECKS.append(f"all {len(MODEL_TABLES)} model tables resolve through DirectLake")

    # 2. Every measure must evaluate. A measure referencing a renamed column fails HERE
    #    rather than as a blank tile in front of leadership.
    from deploy_model import MEASURES
    measures = [m[0] for m in MEASURES]
    expr = ", ".join(f'"{m}", [{m}]' for m in measures)
    result = dax(model["id"], tok, f"EVALUATE ROW({expr})")[0]
    print()
    for m in measures:
        print(f"  [{m}] = {result.get(f'[{m}]')}")
    CHECKS.append(f"all {len(measures)} measures evaluate without error")

    # 3. Measures that must be internally consistent.
    consistency = dax(model["id"], tok, """
        EVALUATE
        ROW(
            "BudgetMinusSpent", [Budget] - [Spent To Date],
            "Variance",         [Budget Variance],
            "Billed",           [Total Billed],
            "Paid",             [Total Paid],
            "Outstanding",      [AR Outstanding]
        )
    """)[0]
    assert abs(consistency["[BudgetMinusSpent]"] - consistency["[Variance]"]) < 0.01
    CHECKS.append("[Budget Variance] equals Budget - Spent To Date")

    # Billed must equal paid plus what is still outstanding, or the AR numbers do not add up.
    billed = consistency["[Billed]"]
    reconciled = consistency["[Paid]"] + consistency["[Outstanding]"]
    assert abs(billed - reconciled) < 1.0, f"billed {billed} != paid+outstanding {reconciled}"
    CHECKS.append("[Total Billed] reconciles to [Total Paid] + [AR Outstanding]")

    # 3b. Billing: balances vs flows, and the identity that proves the distinction holds.
    billing = dax(model["id"], tok, """
        EVALUATE ROW (
            "RetainOwner",   [Retainage Held Owner],
            "OwnerToDate",   [Owner Billed To Date],
            "ThisPeriod",    [Billed This Period]
        )
    """)[0]
    billing = {k.split("[")[-1].rstrip("]"): v for k, v in billing.items()}

    if billing["OwnerToDate"]:
        # THE IDENTITY. Owner billing has two independently-computed paths through this
        # fact: a cumulative one (CompletedToDate at the latest period) and a sum-safe one
        # (CurrentPaymentDue added across every period). They are computed from different
        # columns by different aggregations, and the difference between them must be
        # exactly the retainage withheld - because retainage is precisely the part of
        # completed work that has not been paid out.
        #
        # If the latest-period ranking picked the wrong row, or a draft won it, or the
        # cumulative columns were summed by mistake, this stops holding. It is the single
        # strongest evidence that the grain is handled correctly, and it needs no external
        # source to check against.
        gap = billing["OwnerToDate"] - billing["ThisPeriod"]
        assert abs(gap - billing["RetainOwner"]) < 1.0, (
            f"completed-to-date less billed-this-period is {gap:,.2f}, "
            f"but retainage held is {billing['RetainOwner']:,.2f} - "
            "the two paths through fct_Billing disagree")
        CHECKS.append("cumulative and sum-safe billing differ by exactly the retainage held")

    CHECKS.extend(check_balance_values(dax(model["id"], tok, BALANCE_QUERY)[0]))

    # 4. Time intelligence must actually work - this is what dim_Date exists for. If it
    #    is not marked as a date table, DATEADD returns an error rather than a number.
    dax(model["id"], tok, """
        EVALUATE
        SUMMARIZECOLUMNS (
            dim_Date[Year],
            "Billed", [Total Billed],
            "MoM", [Total Billed MoM %]
        )
        ORDER BY dim_Date[Year]
    """)
    CHECKS.append("time intelligence works - DATEADD over dim_Date evaluates")

    # 5. The diagnostics are real findings, not decoration.
    dq = dax(model["id"], tok, """
        EVALUATE ROW(
            "NoCrosswalk", [DQ Projects Without Crosswalk],
            "NoSource",    [DQ Cost Codes Not In Source],
            "Inverted",    [DQ Milestones With Inverted Dates],
            "Unmatched",   [DQ Unmatched Invoices]
        )
    """)[0]
    print(f"\ndata-quality findings surfaced by the model:")
    print(f"  projects with no Sage crosswalk entry : {dq['[NoCrosswalk]']}")
    print(f"  cost codes not in master data        : {dq['[NoSource]']}")
    print(f"  milestones with inverted dates       : {dq['[Inverted]']}")
    print(f"  AR invoices with no matching project : {dq['[Unmatched]']}")
    CHECKS.append("data-quality measures return real counts")

    # 6. The scorecard. Every category must EVALUATE; a category with no data must be
    #    BLANK, never 0 - scoring a missing input as zero is exactly how the workbook's
    #    Completion Variance silently cost every project 15% of its score.
    categories = [
        "Accounts Receivable", "Profitability", "Cash Position", "Change Orders",
        "Safety Incidents", "Schedule Performance", "Completion Variance",
        "Observations", "Daily Reports",
    ]
    expr = ", ".join(f'"{c}", [Score - {c}]' for c in categories)
    scores = dax(model["id"], tok, f"EVALUATE ROW({expr})")[0]

    print("\nscorecard - score per category (BLANK = no data yet, NOT zero):")
    measured, missing = [], []
    for c in categories:
        v = scores.get(f"[{c}]")
        print(f"  {c:<24} {'-- no data' if v is None else v}")
        (missing if v is None else measured).append(c)
    CHECKS.append(f"all 9 scorecard categories evaluate ({len(measured)} scored, "
                  f"{len(missing)} awaiting data)")

    totals = dax(model["id"], tok, """
        EVALUATE ROW(
            "Scorecard", [Project Scorecard],
            "Coverage",  [Scorecard Coverage %],
            "Measured",  [Project Scorecard (Measured Only)]
        )
    """)[0]
    cov = totals["[Coverage]"]
    print(f"\n  [Project Scorecard]                 {totals['[Scorecard]']}")
    print(f"  [Scorecard Coverage %]              {cov:.0%} of the agreed weight")
    print(f"  [Project Scorecard (Measured Only)] {totals['[Measured]']}")

    # Coverage must equal the summed weight of exactly the categories that scored - that
    # is the whole claim the measure makes.
    weights = dax(model["id"], tok, """
        EVALUATE SUMMARIZECOLUMNS(
            dim_ScorecardWeight[CategoryName], dim_ScorecardWeight[Weight] )
    """)
    # SUMMARIZECOLUMNS can return an extra all-null row - DAX's blank row, not a row in
    # the table. Verified directly: COUNTROWS(dim_ScorecardWeight) is 9 and EVALUATE over
    # the table returns 9 clean rows. Dropping it here rather than letting float(None)
    # blow up, and pinning the count below so a genuinely missing category still fails.
    lookup = {r["dim_ScorecardWeight[CategoryName]"]: r["dim_ScorecardWeight[Weight]"]
              for r in weights
              if r["dim_ScorecardWeight[CategoryName]"] is not None
              and r["dim_ScorecardWeight[Weight]"] is not None}
    assert len(lookup) == 9, f"expected 9 scorecard categories, found {len(lookup)}"
    expected_cov = sum(float(lookup[c]) for c in measured)
    assert abs(cov - expected_cov) < 0.001, f"coverage {cov} != summed weights {expected_cov}"
    CHECKS.append(f"[Scorecard Coverage %] = {cov:.0%}, matching the scored categories' weights")

    # Weights must still total exactly 1.00, or every score is quietly wrong.
    assert abs(sum(float(w) for w in lookup.values()) - 1.0) < 1e-9
    CHECKS.append("scorecard weights still sum to exactly 1.00")

    # THE AUDIT TABLE'S CLAIM. The Scorecard page shows a contribution per category and
    # invites the reader to add them up. If that column does not sum to the headline
    # number, the page is worse than no page - it looks auditable and disagrees.
    #
    # Both come from the same SWITCH, so this asserts the per-category measures resolve
    # the same way inside a row context as they do inside the total's ALL() iteration.
    audit = dax(model["id"], tok, """
        EVALUATE
        ROW( "Summed", SUMX( ALL( dim_ScorecardWeight ), [Category Weighted] ) )
    """)[0]["[Summed]"]
    assert abs(float(audit) - float(totals["[Scorecard]"])) < 0.001, (
        f"audit table sums to {audit}, headline says {totals['[Scorecard]']}")
    CHECKS.append("[Category Weighted] sums to [Project Scorecard] - the audit table adds up")

    # Every category resolves a band label, including the unmeasured ones. A blank here
    # would render an empty cell that reads as "zero" rather than "no data".
    bands = dax(model["id"], tok, """
        EVALUATE SUMMARIZECOLUMNS(
            dim_ScorecardWeight[CategoryName], "Band", [Category Band] )
    """)
    blank_bands = [r["dim_ScorecardWeight[CategoryName]"] for r in bands if not r.get("[Band]")]
    assert not blank_bands, f"categories with no band label: {blank_bands}"
    CHECKS.append(f"all {len(bands)} categories resolve a band label, measured or not")

    # The S-curve. Cumulative at the end of time must equal the sum of the period movement
    # over all time - if it does not, the accumulation window is wrong and every point on
    # the curve is wrong with it.
    curve = dax(model["id"], tok, """
        EVALUATE
        ROW(
            "Cumulative", CALCULATE( [Billed Cumulative], ALL( dim_Date ) ),
            "Movement",   CALCULATE( [Billed This Period], ALL( dim_Date ) )
        )
    """)[0]
    assert abs(float(curve["[Cumulative]"] or 0) - float(curve["[Movement]"] or 0)) < 1.0, (
        f"S-curve endpoint {curve['[Cumulative]']} != total movement {curve['[Movement]']}")
    CHECKS.append("[Billed Cumulative] ends at the total of [Billed This Period]")

    print()
    for label in CHECKS:
        print(f"  ok  {label}")
    print(f"\nvalidate_model: {len(CHECKS)} checks passed; {len(bad)} unresolved model-to-build differences")
    return int(bool(bad))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except dp.FabricError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
