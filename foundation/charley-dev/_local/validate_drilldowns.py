"""Live tie-out of the Weekly Dashboard drill-downs (Oct 30 call: "prove the work").

    python validate_drilldowns.py

For every Executive number with a "Data >" page, evaluates in the deployed model the tile's
measure and the total its detail table shows - the same measure over the same rows the
visual keeps (its row-filter measure), as Power BI computes a totals row - and fails on any
difference. Read-only: DAX queries only, no Spark. Run after deploy_model / deploy_publish.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_model as vm  # noqa: E402
import deploy_report as dr  # noqa: E402

ACTIVE = 'FILTER ( VALUES ( dim_Project[ProjectKey] ), [Dashboard Status] = "Active" )'


def kept(keys: str, flag: str) -> str:
    """The rows a detail table keeps: its grouping keys where its row-filter measure is Yes."""
    return f'FILTER ( {keys}, [{flag}] = "Yes" )'


# (label, tile expression, detail-table total expression). The total is the measure at the
# table's total, filtered to the rows the visual keeps - not a SUMX, which a totals row is not.
TIES = [
    ("Revenue YTD = invoice table Counted total", "[Revenue YTD]",
     f"CALCULATE ( [Invoice Amount], {kept('VALUES ( fct_Invoice[InvoiceID] )', 'Invoice In YTD Flag')} )"),
    ("Revenue YTD = month table total", "[Revenue YTD]", "[Revenue In Month]"),
    ("Revenue YTD = sum of the months", "[Revenue YTD]",
     "SUMX ( VALUES ( dim_Date[MonthYear] ), [Revenue In Month] )"),
    ("Revenue YTD = by-job table total", "[Revenue YTD]", "CALCULATE ( [Revenue YTD], VALUES ( fct_Invoice[SageJobNumber] ) )"),
    ("Open AR = open invoice table Owed total", "[AR Outstanding]",
     f"CALCULATE ( [Invoice Balance], {kept('VALUES ( fct_Invoice[InvoiceID] )', 'Open AR Flag')} )"),
    ("AR > 60 days = by-job table total", "[AR Over 60 Days]",
     f"CALCULATE ( [AR Over 60 Days], {kept('VALUES ( fct_Invoice[SageJobNumber] )', 'Open AR Job Flag')} )"),
    ("Gross margin = project table total", "[Portfolio Gross Margin %]",
     f"CALCULATE ( VAR R = SUMX ( VALUES ( dim_Project[ProjectKey] ), IF ( NOT ISBLANK ( [Projected Cost] ), [Projected Revenue] ) ) "
     f"VAR C = [Projected Cost] RETURN DIVIDE ( R - C, R ), {ACTIVE} )"),
    ("Backlog = contracts table total", "[Backlog]", f"CALCULATE ( [Project Backlog], {ACTIVE} )"),
    ("Current contract (detail strip) = contracts table total", "[Active Contract Value]",
     f"CALCULATE ( [Position Contract], {ACTIVE} )"),
    ("Cash position = cash table total", "[Portfolio Cash Position]",
     f"SUMX ( {ACTIVE}, [Cash Position] )"),
    ("Unpaid payables = open AP table total", "[Active Unpaid Payables]",
     f"CALCULATE ( [AP Line Open], {kept('SUMMARIZE ( fct_ApInvoice, dim_Project[ProjectName], fct_ApInvoice[InvoiceKey] )', 'Open AP Active Flag')} )"),
    ("Change orders approved % = CO table totals", "[Change Orders Approved %]",
     f"CALCULATE ( DIVIDE ( [CO Approved Amount], [CO Approved Amount] + [CO Pending Amount] ), {ACTIVE} )"),
    ("Subcontractor coverage = project table totals", "[Portfolio Subcontractor Coverage]",
     f"CALCULATE ( DIVIDE ( [Subcontract Committed], [Subcontract Budget] ), {ACTIVE} )"),
    ("Checks warning = health table Warn rows", "[Checks Warning]",
     f'CALCULATE ( COUNTROWS ( fct_DashCheck ), fct_DashCheck[Result] = "Warn", {ACTIVE} )'),
    ("Open safety observations = per-project total", "[Active Open Safety Observations]",
     f"CALCULATE ( [Open Safety Observations], {ACTIVE} ) + 0"),
]


def main() -> int:
    tok = vm.pbi_token()
    model = dr.ds.find_item(dr.dp.token(), dr.MODEL_NAME, "SemanticModel")["id"]
    bad = 0
    for label, tile, total in TIES:
        q = f'EVALUATE ROW ( "tile", {tile}, "total", {total} )'
        try:
            row = vm.dax(model, tok, q)[0]
        except Exception as exc:  # noqa: BLE001 - a query error is a failure to report, not a crash
            print(f"  ERROR {label}: {str(exc)[:300]}")
            bad += 1
            continue
        a, b = row.get("[tile]"), row.get("[total]")
        same = (a is None and b is None) or (a is not None and b is not None and abs(float(a) - float(b)) < 0.005)
        bad += not same
        print(f"  {'ok  ' if same else 'DIFF'} {label}: tile {a!r}, table {b!r}")
    print(f"\n{len(TIES) - bad} of {len(TIES)} drill-downs tie out")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
