"""Generate and deploy the Monthly Progress Report (PBIR) over the semantic model.

    python deploy_report.py            # dry run - write PBIR to disk only
    python deploy_report.py --apply    # create/update the report in Fabric

Four pages, following powerbi/report-spec.md:
  1. Overview        - the one-page replacement for the DASHBOARD tab
  2. Financial       - contract, budget, change orders, billing
  3. Schedule & Quality
  4. Data Quality    - hidden; surfaces bad data instead of letting it flow into a rollup

Colours come from analysis/excel-tracker/dropdowns-and-status.md, sampled from the
workbook's own font colours (#DB1918 red, #FFD800 amber, #01AF00 green) so the report
matches what Affect already recognises.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deploy as dp  # noqa: E402
import deploy_seeds as ds  # noqa: E402

HERE = Path(__file__).resolve().parent
CHARLEY_DEV = HERE.parent
REPORT_DIR = CHARLEY_DEV / "05-reports" / "Monthly Progress Report.Report"

REPORT_NAME = "Monthly Progress Report"
MODEL_NAME = "Affect Project Report"

GREEN, AMBER, RED, INK, MUTED = "#01AF00", "#FFD800", "#DB1918", "#252423", "#605E5C"

SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"


def oid(*parts: str) -> str:
    """Deterministic 20-hex id, so redeploying does not churn every visual's identity."""
    return hashlib.sha1("|".join(parts).encode()).hexdigest()[:20]


def measure(name: str) -> dict:
    return {
        "field": {"Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}},
                              "Property": name}},
        "queryRef": f"_Measures.{name}",
        "nativeQueryRef": name,
    }


def column(table: str, col: str) -> dict:
    return {
        "field": {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": col}},
        "queryRef": f"{table}.{col}",
        "nativeQueryRef": col,
    }


def visual(page: str, key: str, vtype: str, x, y, w, h, projections: dict,
           title: str | None = None) -> dict:
    v = {
        "$schema": f"{SCHEMA}/visualContainer/1.0.0/schema.json",
        "name": oid(page, key),
        "position": {"x": x, "y": y, "z": 0, "width": w, "height": h},
        "visual": {
            "visualType": vtype,
            "query": {"queryState": {
                role: {"projections": items} for role, items in projections.items()
            }},
            "drillFilterOtherVisuals": True,
        },
    }
    if title:
        v["visual"]["visualContainerObjects"] = {
            "title": [{"properties": {
                "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{INK}'"}}}}},
                "fontSize": {"expr": {"Literal": {"Value": "12D"}}},
            }}]
        }
    return v


def textbox(page: str, key: str, text: str, x, y, w, h, size: int = 20,
            color: str = INK) -> dict:
    return {
        "$schema": f"{SCHEMA}/visualContainer/1.0.0/schema.json",
        "name": oid(page, key),
        "position": {"x": x, "y": y, "z": 0, "width": w, "height": h},
        "visual": {
            "visualType": "textbox",
            "objects": {"general": [{"properties": {"paragraphs": [{
                "textRuns": [{"value": text, "textStyle": {
                    "fontSize": f"{size}pt", "color": color, "fontWeight": "bold"}}]
            }]}}]},
        },
    }


def card(page: str, key: str, name: str, x, y, w=180, h=110) -> dict:
    return visual(page, key, "card", x, y, w, h, {"Values": [measure(name)]}, title=name)


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------


def page_overview() -> tuple[str, list[dict]]:
    p = "overview"
    slicer = visual(p, "slicer_project", "slicer", 20, 80, 260, 90,
                    {"Values": [column("dim_Project", "ProjectName")]}, title="Project")
    cards = [
        card(p, "c_contract", "Current Contract", 300, 80),
        card(p, "c_billed", "Total Billed", 496, 80),
        card(p, "c_billedpct", "Total Billed %", 692, 80),
        card(p, "c_paid", "Total Paid", 888, 80),
        card(p, "c_ar", "AR Outstanding", 1084, 80),
        card(p, "c_growth", "Contract Growth %", 300, 206),
        card(p, "c_bought", "Percent Bought Out", 496, 206),
        card(p, "c_pending", "Pending Change Orders", 692, 206),
        card(p, "c_open", "Open Submittals", 888, 206),
        card(p, "c_milestones", "Critical Milestones", 1084, 206),
    ]
    trend = visual(p, "billed_trend", "columnChart", 20, 340, 640, 300,
                   {"Category": [column("dim_Date", "MonthYear")],
                    "Y": [measure("Total Billed")]},
                   title="Billed by month")
    budget = visual(p, "budget_by_code", "barChart", 680, 340, 580, 300,
                    {"Category": [column("dim_CostCode", "Division")],
                     "Y": [measure("Budget"), measure("Spent To Date")]},
                    title="Budget vs spent by division")
    return p, [
        textbox(p, "title", "Monthly Progress Report", 20, 16, 700, 50),
        textbox(p, "sub", "Replaces the Excel Monthly Progress Report", 20, 56, 700, 24,
                size=10, color=MUTED),
        slicer, *cards, trend, budget,
    ]


def page_financial() -> tuple[str, list[dict]]:
    p = "financial"
    return p, [
        textbox(p, "title", "Financial", 20, 16, 600, 44),
        card(p, "f_budget", "Budget", 20, 80),
        card(p, "f_forecast", "Forecast", 216, 80),
        card(p, "f_committed", "Committed", 412, 80),
        card(p, "f_spent", "Spent To Date", 608, 80),
        card(p, "f_ctc", "Cost To Complete", 804, 80),
        card(p, "f_var", "Budget Variance", 1000, 80),
        visual(p, "budget_table", "tableEx", 20, 210, 780, 440,
               {"Values": [column("dim_CostCode", "CostCode"),
                           measure("Budget"), measure("Spent To Date"),
                           measure("Budget Variance"), measure("Budget Status")]},
               title="Budget by cost code"),
        visual(p, "co_by_status", "clusteredColumnChart", 820, 210, 440, 210,
               {"Category": [column("fct_ChangeOrder", "StatusLabel")],
                "Y": [measure("Pending Change Orders")]},
               title="Change orders by status"),
        visual(p, "billing_trend", "lineChart", 820, 440, 440, 210,
               {"Category": [column("dim_Date", "MonthYear")],
                "Y": [measure("Total Billed"), measure("Total Paid")]},
               title="Billed vs paid"),
    ]


def page_schedule_quality() -> tuple[str, list[dict]]:
    p = "schedule"
    return p, [
        textbox(p, "title", "Schedule & Quality", 20, 16, 600, 44),
        card(p, "s_crit", "Critical Milestones", 20, 80),
        card(p, "s_overdue", "Overdue Milestones", 216, 80),
        card(p, "s_perf", "Schedule Performance %", 412, 80),
        card(p, "s_prog", "Avg Milestone Progress", 608, 80),
        card(p, "s_open", "Open Submittals", 804, 80),
        card(p, "s_pastdue", "Open Submittals Past Due", 1000, 80),
        visual(p, "milestones", "tableEx", 20, 210, 740, 440,
               {"Values": [column("fct_Milestone", "MilestoneName"),
                           column("fct_Milestone", "CurrentStart"),
                           column("fct_Milestone", "CurrentFinish"),
                           column("fct_Milestone", "PercentComplete"),
                           column("fct_Milestone", "StatusLabel")]},
               title="Critical path milestones (Outbuild)"),
        # The workbook's one native chart, rebuilt - and now drillable to the items.
        visual(p, "submittals_by_status", "barChart", 780, 210, 480, 440,
               {"Category": [column("fct_RfiSubmittal", "StatusLabel")],
                "Y": [measure("Open Submittals")]},
               title="Open submittals by status"),
    ]


def page_data_quality() -> tuple[str, list[dict]]:
    p = "dataquality"
    return p, [
        textbox(p, "title", "Data Quality", 20, 16, 600, 44),
        textbox(p, "note",
                "Surfacing bad data rather than letting it flow silently into a rollup. "
                "This page is how the Excel's defects would have been caught.",
                20, 56, 900, 30, size=10, color=MUTED),
        card(p, "dq_cross", "DQ Projects Without Crosswalk", 20, 110, 260, 130),
        card(p, "dq_codes", "DQ Cost Codes Not In Source", 296, 110, 260, 130),
        card(p, "dq_inv", "DQ Milestones With Inverted Dates", 572, 110, 260, 130),
        card(p, "dq_ar", "DQ Unmatched Invoices", 848, 110, 260, 130),
        visual(p, "no_crosswalk", "tableEx", 20, 260, 600, 390,
               {"Values": [column("dim_Project", "ProjectKey"),
                           column("dim_Project", "ProjectName"),
                           column("dim_Project", "IsInCrosswalk"),
                           column("dim_Project", "HasPrimeContract")]},
               title="Projects - crosswalk and contract coverage"),
        visual(p, "unmatched_ar", "tableEx", 640, 260, 620, 390,
               {"Values": [column("fct_Invoice", "SageJobNumber"),
                           column("fct_Invoice", "Description"),
                           measure("Total Billed")]},
               title="AR invoices by Sage job"),
    ]


def page_scorecard() -> tuple[str, list[dict]]:
    """The nine-category weighted health score.

    analysis/excel-tracker/README.md:174 calls the scorecard the most valuable thing in
    the workbook - and partly broken. Coverage sits beside the score deliberately: the
    Excel's 0.59 looked like a health score while 42% of its weight measured nothing, and
    because a missing category scored 0 rather than blank, that was invisible.
    """
    p = "scorecard"
    return p, [
        textbox(p, "title", "Project Scorecard", 20, 16, 600, 44),
        textbox(p, "note",
                "Weights and bands are data (dim_ScorecardWeight / dim_ScorecardBand) - "
                "retune them without a code change. A category with no data scores BLANK, "
                "never zero.",
                20, 56, 1000, 30, size=10, color=MUTED),
        card(p, "sc_total", "Project Scorecard", 20, 110, 240, 130),
        card(p, "sc_cov", "Scorecard Coverage %", 276, 110, 240, 130),
        card(p, "sc_measured", "Project Scorecard (Measured Only)", 532, 110, 300, 130),
        card(p, "sc_client", "Client Satisfaction", 848, 110, 240, 130),
        visual(p, "weights", "tableEx", 20, 260, 620, 390,
               {"Values": [column("dim_ScorecardWeight", "CategoryName"),
                           column("dim_ScorecardWeight", "Weight")]},
               title="Category weights (sum to 1.00)"),
        visual(p, "bands", "tableEx", 660, 260, 600, 390,
               {"Values": [column("dim_ScorecardBand", "CategoryKey"),
                           column("dim_ScorecardBand", "Score"),
                           column("dim_ScorecardBand", "BandLabel")]},
               title="Scoring bands - corrected (defects #1a-#1c)"),
    ]


PAGES = [
    ("Overview", page_overview, False),
    ("Financial", page_financial, False),
    ("Schedule & Quality", page_schedule_quality, False),
    ("Scorecard", page_scorecard, False),
    ("Data Quality", page_data_quality, True),   # hidden
]


def build(model_id: str) -> dict[str, str]:
    files: dict[str, str] = {
        ".platform": json.dumps({
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/"
                       "platformProperties/2.0.0/schema.json",
            "metadata": {"type": "Report", "displayName": REPORT_NAME},
            "config": {"version": "2.0", "logicalId": "00000000-0000-0000-0000-000000000000"},
        }, indent=2),
        # byConnection accepts connectionString and NOTHING else - the 2.0.0 schema rejects
        # additional properties outright. Shape copied from the existing workspace reports
        # (foundation/05-reports/*/definition.pbir), which are known to load.
        "definition.pbir": json.dumps({
            "$schema": f"{SCHEMA}Properties/2.0.0/schema.json",
            "version": "4.0",
            "datasetReference": {"byConnection": {
                "connectionString": (
                    "Data Source=powerbi://api.powerbi.com/v1.0/myorg/Build;"
                    f"initial catalog={MODEL_NAME};"
                    f"integrated security=ClaimsToken;semanticmodelid={model_id}"
                ),
            }},
        }, indent=2),
        "definition/version.json": json.dumps(
            {"$schema": f"{SCHEMA}/versionMetadata/1.0.0/schema.json", "version": "2.0.0"},
            indent=2),
        "definition/report.json": json.dumps({
            "$schema": f"{SCHEMA}/report/2.0.0/schema.json",
            "themeCollection": {"baseTheme": {"name": "CY24SU10", "reportVersionAtImport": "5.55",
                                              "type": "SharedResources"}},
        }, indent=2),
    }

    page_names = []
    for display, builder, hidden in PAGES:
        pid, visuals = builder()
        page_names.append(pid)
        page: dict = {
            "$schema": f"{SCHEMA}/page/2.0.0/schema.json",
            "name": pid,
            "displayName": display,
            "displayOption": "FitToPage",
            "height": 720,
            "width": 1280,
        }
        if hidden:
            page["visibility"] = "HiddenInViewMode"
        files[f"definition/pages/{pid}/page.json"] = json.dumps(page, indent=2)
        for v in visuals:
            files[f"definition/pages/{pid}/visuals/{v['name']}/visual.json"] = json.dumps(v, indent=2)

    files["definition/pages/pages.json"] = json.dumps({
        "$schema": f"{SCHEMA}/pagesMetadata/1.0.0/schema.json",
        "pageOrder": page_names,
        "activePageName": page_names[0],
    }, indent=2)

    for rel, content in files.items():
        path = REPORT_DIR / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="")
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--recreate", action="store_true")
    args = parser.parse_args()

    tok = dp.token()
    model = ds.find_item(tok, MODEL_NAME, "SemanticModel")
    if not model:
        print(f"ERROR: semantic model {MODEL_NAME!r} not found")
        return 1

    files = build(model["id"])
    visuals = [f for f in files if f.endswith("visual.json")]
    print(f"generated {len(files)} file(s): {len(PAGES)} pages, {len(visuals)} visuals")
    print(f"  bound to semantic model {model['id']}")

    if not args.apply:
        print("\nDRY RUN - written to disk only. Re-run with --apply.")
        return 0

    definition = {"parts": [
        {"path": rel, "payload": base64.b64encode(content.encode()).decode(),
         "payloadType": "InlineBase64"}
        for rel, content in files.items() if rel != ".platform"
    ]}

    existing = ds.find_item(tok, REPORT_NAME, "Report")
    if existing and args.recreate:
        assert existing.get("folderId") == dp.FOLDER_ID, "refusing: report is not in charley-dev"
        dp.call("DELETE", f"/workspaces/{dp.WORKSPACE_ID}/items/{existing['id']}", tok)
        print(f"  deleted {REPORT_NAME} for recreation")
        existing = None

    if existing:
        status, _, headers = dp.call(
            "POST", f"/workspaces/{dp.WORKSPACE_ID}/items/{existing['id']}/updateDefinition",
            tok, {"definition": definition},
        )
        if status == 202:
            dp.wait_for_operation(headers, tok)
        print(f"  updated {REPORT_NAME}")
    else:
        status, _, headers = dp.call(
            "POST", f"/workspaces/{dp.WORKSPACE_ID}/items", tok,
            {"displayName": REPORT_NAME, "type": "Report",
             "folderId": dp.FOLDER_ID, "definition": definition},
        )
        if status == 202:
            dp.wait_for_operation(headers, tok)
        print(f"  created {REPORT_NAME}")

    item = ds.find_item(tok, REPORT_NAME, "Report")
    print(f"  report id: {item['id']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except dp.FabricError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
