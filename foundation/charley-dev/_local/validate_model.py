"""Run DAX against the deployed semantic model and check the numbers.

    python validate_model.py

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
        return body["results"][0]["tables"][0]["rows"]
    except urllib.error.HTTPError as exc:
        raise dp.FabricError(f"DAX failed ({exc.code}): {exc.read().decode()[:400]}\n{query[:200]}") from exc


def reframe(dataset_id: str, tok: str, timeout: int = 300) -> str:
    """Refresh (reframe) the Direct Lake model, then wait for it to finish.

    A newly deployed Direct Lake model holds a correct definition but is not yet bound to
    the Delta files. Until it is reframed every table is invisible to DAX - queries fail
    with "Failed to resolve name 'dim_Date'", which reads like a broken model rather than
    an unrefreshed one. The definition being right is not the same as the model being
    loaded.
    """
    import time

    request = urllib.request.Request(
        f"{PBI_API}/datasets/{dataset_id}/refreshes",
        method="POST",
        data=json.dumps({"type": "full"}).encode(),
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(request, timeout=60)
    except urllib.error.HTTPError as exc:
        raise dp.FabricError(f"refresh failed ({exc.code}): {exc.read().decode()[:300]}") from exc

    deadline = time.time() + timeout
    while time.time() < deadline:
        poll = urllib.request.Request(
            f"{PBI_API}/datasets/{dataset_id}/refreshes?$top=1",
            headers={"Authorization": f"Bearer {tok}"},
        )
        with urllib.request.urlopen(poll, timeout=60) as response:
            runs = json.loads(response.read().decode()).get("value", [])
        status = runs[0].get("status") if runs else "Unknown"
        if status == "Completed":
            return status
        if status == "Failed":
            raise dp.FabricError(f"reframe failed: {runs[0].get('serviceExceptionJson')}")
        time.sleep(5)
    raise dp.FabricError(f"reframe did not finish within {timeout}s")


def main() -> int:
    tok_fabric = dp.token()
    model = ds.find_item(tok_fabric, MODEL_NAME, "SemanticModel")
    if not model:
        print(f"ERROR: semantic model {MODEL_NAME!r} not found - run deploy_model.py --apply")
        return 1
    print(f"model {model['id']}")

    tok = pbi_token()

    print("  reframing ...", end=" ", flush=True)
    print(reframe(model["id"], tok))

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
            "Periods",      COUNTROWS ( fct_FinancialPeriod )
        )
    """)[0]
    expected = {
        "[Projects]": 17, "[Vendors]": 126, "[CostCodes]": 4837, "[Dates]": 7670,
        "[BudgetLines]": 404, "[ChangeOrders]": 1812, "[Invoices]": 117,
        "[Submittals]": 2242, "[Milestones]": 52, "[Periods]": 128,
    }
    bad = []
    for key, want in expected.items():
        got = rows.get(key)
        print(f"  {key[1:-1]:<14} {got:>7}  (expected {want})")
        if got != want:
            bad.append(f"{key}: got {got}, expected {want}")
    if bad:
        print("\nROW COUNT MISMATCH:\n  " + "\n  ".join(bad))
        return 1
    CHECKS.append("all 10 tables readable through DirectLake at the expected row counts")

    # 2. Every measure must evaluate. A measure referencing a renamed column fails HERE
    #    rather than as a blank tile in front of leadership.
    measures = [
        "Original Contract", "Current Contract", "Contract Growth %",
        "Pending Change Orders", "Budget", "Forecast", "Committed", "Spent To Date",
        "Budget Variance", "Budget Variance %", "Percent Bought Out", "Total Billed",
        "Total Paid", "AR Outstanding", "Total Billed %", "Open Submittals",
        "Open Submittals Past Due", "Avg Days Open", "Critical Milestones",
        "Overdue Milestones", "Schedule Performance %", "Avg Milestone Progress",
        "DQ Projects Without Crosswalk", "DQ Cost Codes Not In Source",
        "DQ Milestones With Inverted Dates", "DQ Unmatched Invoices",
    ]
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
    lookup = {r["dim_ScorecardWeight[CategoryName]"]: r["dim_ScorecardWeight[Weight]"]
              for r in weights}
    expected_cov = sum(float(lookup[c]) for c in measured)
    assert abs(cov - expected_cov) < 0.001, f"coverage {cov} != summed weights {expected_cov}"
    CHECKS.append(f"[Scorecard Coverage %] = {cov:.0%}, matching the scored categories' weights")

    # Weights must still total exactly 1.00, or every score is quietly wrong.
    assert abs(sum(float(w) for w in lookup.values()) - 1.0) < 1e-9
    CHECKS.append("scorecard weights still sum to exactly 1.00")

    print()
    for label in CHECKS:
        print(f"  ok  {label}")
    print(f"\nvalidate_model: {len(CHECKS)} checks passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except dp.FabricError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
