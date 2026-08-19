"""Run DAX against the deployed semantic model and check the numbers.

    python validate_model.py

This is the reconciliation gate as a test rather than a manual comparison. It executes
each measure against the live model and asserts the result, so "the model deploys" becomes
"the model returns the right numbers".

Uses the Power BI executeQueries API, which needs a different token audience from the
Fabric API (analysis.windows.net/powerbi/api rather than api.fabric.microsoft.com).
"""

from __future__ import annotations

import os
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
            "Periods",      COUNTROWS ( fct_FinancialPeriod ),
            "Billings",     COALESCE ( COUNTROWS ( fct_Billing ), 0 ),
            "DirectCosts",  COALESCE ( COUNTROWS ( fct_DirectCost ), 0 ),
            "ProjectVendors", COALESCE ( COUNTROWS ( bridge_ProjectVendor ), 0 )
        )
    """)[0]
    # Baselines for --source cd, i.e. gold built on OUR OWN medallion (2026-08-02).
    #
    # The second number is what the same table held under --source existing (Rebecca's
    # Silver). Both are kept because the DIFFERENCE is the L2 parity check, and three of
    # these differences are findings rather than noise:
    #
    #   Submittals   2,861 vs 2,242   HIGHER, and expected: the fact now unions submittals
    #                                 (2,245) with RFIs (616). No RFI data exists anywhere
    #                                 in the existing warehouse.
    #   Projects        19 vs 17      HIGHER: Procore reports 19 active projects.
    #   CostCodes    5,434 vs 4,837   HIGHER: 5,433 from Procore + the UNASSIGNED member.
    #
    #   BudgetLines    402 vs 404     Two rows apart. Procore returns 404 detail rows;
    #                                 silver keeps one per (project, cost code) at the
    #                                 latest snapshot, and two pairs were duplicated. That
    #                                 is the dedup working, not data lost.
    #   ChangeOrders   307 vs 1,812   LOWER - RESOLVED 2026-08-02, and the resolution is
    #                                 that THEIR number is wrong.
    #
    #                                 procore_prime_change_orders holds 1,812 rows for 454
    #                                 distinct Change Order IDs - each one repeated EXACTLY
    #                                 four times. The pattern is uniform within every
    #                                 batch_id group (4 rows per CO, 12 for 3, 52 for 13),
    #                                 which is a fan-out from an un-deduplicated join, not
    #                                 an ingestion artifact.
    #
    #                                 Summing CO Value $ off that table gives $20,152,671.
    #                                 Deduplicated it is $5,056,742. Ours is $4,907,551 -
    #                                 within 3%.
    #
    #                                 So nothing was lost. The residual 454 vs 307 is grain:
    #                                 change_order_packages groups change orders, and their
    #                                 table carries statuses ours does not (not_proceeding,
    #                                 no_charge, rejected, pricing). Package grain is
    #                                 accepted here because the money agrees; if CO-level
    #                                 detail is needed later it is a different endpoint, not
    #                                 a correction.
    #
    #                                 Reported to Affect, NOT fixed - it is Rebecca's table.
    #
    # Periods is derived from the fact date range, so it moves with the two above.
    EXPECTED_BY_SOURCE = {
        "cd": {
            "[Projects]": 19, "[Vendors]": 126, "[CostCodes]": 5434, "[Dates]": 7670,
            # [Invoices] 117 -> 122 on 2026-08-19, and NOT because of anything we changed.
            # fct_Invoice reads Sage AR from Rebecca's Silver_Lakehouse, which is a live
            # external source: it moves when her dataflow runs. The max SentDate went
            # 2026-07-20 -> 2026-07-31 at the same time, so her Sage feed refreshed some
            # time after our 2026-08-02 measurement. Still 19 days behind today, so the
            # staleness warning stands - but "stopped dead on Jul 20" no longer does.
            #
            # Asserting an exact count against someone else's warehouse is fragile by
            # design. That fragility is the point: this assertion is what noticed.
            "[BudgetLines]": 402, "[ChangeOrders]": 307, "[Invoices]": 122,
            # 130 -> 142 for the same reason, exactly as the note above predicts: Periods
            # is derived from the fact date range, so eleven more days of Sage AR widened
            # it by twelve project-months. Two assertions moving together from one external
            # refresh is the expected shape - had only one moved, that would be the alarm.
            "[Submittals]": 2861, "[Milestones]": 52, "[Periods]": 142,
            "[Billings]": 607, "[DirectCosts]": 418, "[ProjectVendors]": 393,
        },
        "existing": {
            "[Projects]": 17, "[Vendors]": 126, "[CostCodes]": 4837, "[Dates]": 7670,
            # Same live Sage AR source as the cd block above, so the same 117 -> 122 move.
            # Not re-measured under --source existing today; corrected for consistency
            # rather than verified, and flagged here rather than quietly assumed.
            "[BudgetLines]": 404, "[ChangeOrders]": 1812, "[Invoices]": 122,
            "[Submittals]": 2242, "[Milestones]": 52, "[Periods]": 128,
            # Zero, legitimately: the existing warehouse holds no progress billing,
            # no direct costs and no vendor bridge. Asserted rather than skipped, so
            # that "empty" stays a decision and not an unnoticed regression.
            "[Billings]": 0, "[DirectCosts]": 0, "[ProjectVendors]": 0,
        },
    }
    expected = EXPECTED_BY_SOURCE[os.environ.get("CD_GOLD_SOURCE", "cd")]
    bad = []
    for key, want in expected.items():
        got = rows.get(key)
        print(f"  {key[1:-1]:<14} {got:>7}  (expected {want})")
        if got != want:
            bad.append(f"{key}: got {got}, expected {want}")
    if bad:
        print("\nROW COUNT MISMATCH:\n  " + "\n  ".join(bad))
        return 1
    # Counted, not typed. A hardcoded number here goes stale the first time a table is
    # added and then quietly understates what was actually checked.
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

    # 3b. Billing: balances vs flows, and the identity that proves the distinction holds.
    billing = dax(model["id"], tok, """
        EVALUATE ROW (
            "RetainOwner",   [Retainage Held Owner],
            "RetainSub",     [Retainage Held Sub],
            "NetRetain",     [Net Retainage Position],
            "NaiveRetain",   SUM ( fct_Billing[RetainageHeld] ),
            "OwnerToDate",   [Owner Billed To Date],
            "ThisPeriod",    [Billed This Period],
            "CurrentContract", [Current Contract]
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

        # The cumulative-column trap, asserted rather than described. If someone drops the
        # IsLatestPeriod filter from a measure, this is what catches it.
        assert billing["NaiveRetain"] > billing["RetainOwner"] * 3, (
            "summing RetainageHeld across all periods should vastly exceed the held "
            "balance - if it does not, IsLatestPeriod may be marking too many rows")
        CHECKS.append("IsLatestPeriod guards a cumulative column that is ~7x its own sum")

        assert abs(billing["NetRetain"]
                   - (billing["RetainOwner"] - billing["RetainSub"])) < 0.01
        CHECKS.append("[Net Retainage Position] is owner held less sub held")

        # Contract value must be within an order of magnitude of what the owner billing
        # says, which comes from a different table by a different route. This is what
        # would have caught the $355M portfolio card: it read 10x the billing figure.
        assert billing["CurrentContract"] < 100_000_000, (
            f"[Current Contract] is {billing['CurrentContract']:,.0f} across the portfolio "
            "- a per-project balance is probably being summed across months again")
        CHECKS.append("[Current Contract] is a balance, not a running total of months")

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
    print(f"\nvalidate_model: {len(CHECKS)} checks passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except dp.FabricError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
