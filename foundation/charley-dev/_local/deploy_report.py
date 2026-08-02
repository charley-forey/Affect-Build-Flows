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
                "This page is how the Excel's defects would have been caught.  Status is "
                "always shown as TEXT, never colour alone - around 8% of men have some "
                "colour-vision deficiency, and this report goes to leadership.",
                20, 56, 1100, 44, size=10, color=MUTED),
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
        # THE TRUST PARAGRAPH. Affect reports 0.59 to leadership today and this model does
        # not reproduce it. Shipping a different number with no explanation is how a new
        # system gets labelled wrong; showing the arithmetic is how it gets adopted.
        #
        # It is TEXT, not a measure, because the workbook's number cannot be recomputed
        # from correct bands - the defects are wrong band SCORES multiplied by category
        # weights, so the error varies per project and only happens to cancel on this one.
        # A measure claiming to reproduce it would have to be arithmetic that is always
        # zero, which reads as confirmation the two agree.
        textbox(p, "correction",
                "WHY THIS DIFFERS FROM THE 0.59 IN THE WORKBOOK.  Two scoring bands are "
                "wrong there: Schedule Performance uses 5/10 where the data is a fraction "
                "(0.05/0.10), so it always scored 3; Completion Variance never matched any "
                "band, so it always scored 0. On the sample project those two errors cancel "
                "exactly - which is why nobody noticed. On a project where they do not "
                "cancel, the workbook's score is wrong by the difference.  The bands here "
                "are corrected (dim_ScorecardBand). Affect decides when to switch the "
                "number reported to leadership.",
                20, 664, 1240, 78, size=10, color=MUTED),

        visual(p, "bands", "tableEx", 660, 260, 600, 390,
               {"Values": [column("dim_ScorecardBand", "CategoryKey"),
                           column("dim_ScorecardBand", "Score"),
                           column("dim_ScorecardBand", "BandLabel")]},
               title="Scoring bands - corrected (defects #1a-#1c)"),
    ]



def page_source_coverage() -> tuple[str, list[dict]]:
    """Which projects actually exist in all three systems - and which silently do not.

    This is the page that would have caught the platform's most dangerous failure mode. A
    project present in Procore but missing from Sage contributes ZERO revenue to every
    financial measure without erroring: no blank, no warning, just a project that appears
    never to have billed. Across Affect's 19 projects that is 4 of them today.

    It is visible (not hidden like Data Quality) because these are not data-entry typos to
    be cleaned up quietly - they are integration gaps someone has to act on, and the
    financial numbers on every other page are wrong until they are.
    """
    p = "sourcecoverage"
    return p, [
        textbox(p, "title", "Source Coverage", 20, 16, 700, 44),
        textbox(p, "note",
                "A project missing from Sage reads as ZERO revenue everywhere - it does not "
                "error, it just looks like a project that never billed. Every project below "
                "appears exactly once; the status says what is missing.",
                20, 56, 1100, 44, size=10, color=MUTED),

        # Counts first, so the shape of the problem is legible before the detail.
        card(p, "cov_full", "Projects Fully Mapped", 20, 116, 260, 120),
        card(p, "cov_nosage", "Projects Missing From Sage", 296, 116, 260, 120),
        card(p, "cov_nooutbuild", "Projects Missing From Outbuild", 572, 116, 260, 120),
        card(p, "cov_pct", "Source Coverage %", 848, 116, 260, 120),

        visual(p, "cov_status", "columnChart", 20, 252, 540, 300,
               {"Category": [column("dim_ProjectCrosswalk", "CoverageStatus")],
                "Y": [measure("Projects Fully Mapped")]},
               title="Projects by coverage status"),

        # The list is the actionable artifact: it names the projects to go fix.
        visual(p, "cov_detail", "tableEx", 580, 252, 700, 300,
               {"Values": [column("dim_ProjectCrosswalk", "ProjectName"),
                           column("dim_ProjectCrosswalk", "CoverageStatus"),
                           column("dim_ProjectCrosswalk", "SageProjectId"),
                           column("dim_ProjectCrosswalk", "OutbuildProjectId")]},
               title="Every project, and what it is missing"),

        textbox(p, "vendornote",
                "Vendors below are expected to be mostly unmatched - a vendor invited to bid "
                "is not a vendor who was paid. What matters is a vendor WITH commitments and "
                "no Sage id.",
                20, 566, 1100, 30, size=10, color=MUTED),
        visual(p, "vendor_cov", "tableEx", 20, 600, 620, 260,
               {"Values": [column("dim_VendorCrosswalk", "VendorName"),
                           column("dim_VendorCrosswalk", "IsInSage"),
                           column("dim_VendorCrosswalk", "HasNameMismatch")]},
               title="Vendor mapping - Procore to Sage"),
        visual(p, "costcode_cov", "tableEx", 660, 600, 620, 260,
               {"Values": [column("dim_CostCodeCrosswalk", "DivisionCode"),
                           column("dim_CostCodeCrosswalk", "CostCode"),
                           column("dim_CostCodeCrosswalk", "HasUnparseableCode")]},
               title="Cost codes - CSI division parse"),
    ]



def page_project_detail() -> tuple[str, list[dict]]:
    """The drill-through target: everything about ONE project, reached by right-clicking it.

    This is the capability the workbook fundamentally lacks. It holds one row per project
    and no way down, so a number that looks wrong can only be checked by asking whoever
    typed it. Here, every aggregate on every page is right-click -> Drill through, and the
    underlying records are on screen.

    The page is REACHABLE ONLY BY DRILLING - it is not in the page order. Opening it cold
    would show every project at once, which is exactly the portfolio view the other pages
    already give better.
    """
    p = "projectdetail"
    return p, [
        textbox(p, "title", "Project Detail", 20, 16, 600, 44),
        textbox(p, "note",
                "Reached by right-clicking a project on any page and choosing Drill through. "
                "Every figure here is for the single project you came from.",
                20, 56, 1000, 30, size=10, color=MUTED),

        card(p, "pd_contract", "Current Contract", 20, 100, 240, 110),
        card(p, "pd_billed", "Total Billed", 276, 100, 240, 110),
        card(p, "pd_paid", "Total Paid", 532, 100, 240, 110),
        card(p, "pd_ar", "AR Outstanding", 788, 100, 240, 110),
        card(p, "pd_score", "Project Scorecard", 1044, 100, 216, 110),

        # Budget by cost code: the line-item grain the portfolio pages roll up.
        visual(p, "pd_budget", "tableEx", 20, 228, 620, 300,
               {"Values": [column("dim_CostCode", "CostCodeKey"),
                           column("dim_CostCode", "Division"),
                           measure("Budget"),
                           measure("Spent To Date"),
                           measure("Budget Variance")]},
               title="Budget by cost code"),

        visual(p, "pd_co", "tableEx", 660, 228, 600, 300,
               {"Values": [column("fct_ChangeOrder", "ChangeOrderNumber"),
                           column("fct_ChangeOrder", "Status"),
                           measure("Approved Change Orders")]},
               title="Change orders"),

        visual(p, "pd_items", "tableEx", 20, 544, 620, 260,
               {"Values": [column("fct_RfiSubmittal", "ItemType"),
                           column("fct_RfiSubmittal", "ItemNumber"),
                           column("fct_RfiSubmittal", "Subject"),
                           column("fct_RfiSubmittal", "StatusLabel")]},
               title="RFIs and submittals"),

        visual(p, "pd_milestones", "tableEx", 660, 544, 600, 260,
               {"Values": [column("fct_Milestone", "MilestoneName"),
                           column("fct_Milestone", "CurrentStart"),
                           column("fct_Milestone", "CurrentFinish"),
                           column("fct_Milestone", "IsOverdue")]},
               title="Milestones"),
    ]


# page id -> the (entity, column) it is drilled by. A page listed here becomes reachable
# only by right-clicking that field somewhere else in the report.
DRILLTHROUGH = {
    "projectdetail": ("dim_Project", "ProjectName"),
}

PAGES = [
    ("Overview", page_overview, False),
    ("Financial", page_financial, False),
    ("Schedule & Quality", page_schedule_quality, False),
    ("Scorecard", page_scorecard, False),
    ("Source Coverage", page_source_coverage, False),
    ("Project Detail", page_project_detail, True),    # drill-through target
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

        # DRILL-THROUGH BINDING. Two things make a page a drill-through target and both are
        # required: a pageBinding of type Drillthrough, and a filter on the field being
        # drilled by. Without the filter the page opens showing every project, which is the
        # portfolio view the other pages already do better.
        if pid in DRILLTHROUGH:
            entity, prop = DRILLTHROUGH[pid]
            page["pageBinding"] = {
                "name": f"{pid}_binding",
                "type": "Drillthrough",
                # The parameter IS the contract: it names the field the caller passes in.
                # Without it the import fails with "DrillThrough pods cannot contain null
                # parameters" - the filter alone only says what this page is restricted by,
                # not what it receives.
                "parameters": [{"name": prop}],
            }
            page["filterConfig"] = {
                "filters": [{
                    "name": f"{pid}_drill",
                    "field": {"Column": {
                        "Expression": {"SourceRef": {"Entity": entity}},
                        "Property": prop,
                    }},
                    "type": "Passthrough",
                }]
            }
        files[f"definition/pages/{pid}/page.json"] = json.dumps(page, indent=2)
        for v in visuals:
            files[f"definition/pages/{pid}/visuals/{v['name']}/visual.json"] = json.dumps(v, indent=2)

    visible_order = [n for n in page_names if n not in DRILLTHROUGH]
    files["definition/pages/pages.json"] = json.dumps({
        "$schema": f"{SCHEMA}/pagesMetadata/1.0.0/schema.json",
        # Drill-through targets are deliberately absent: a page in the order appears in the
        # tab strip, and opening it cold shows every project - which reads as broken.
        "pageOrder": visible_order,
        "activePageName": visible_order[0],
    }, indent=2)

    # ------------------------------------------------------------- bookmarks
    #
    # The views people actually open the report to check. Each replaces four slicer changes
    # with one click, which is the difference between a report someone uses monthly and one
    # they rebuild in Excel because filtering it is a chore.
    #
    # Each captures the TARGET PAGE ONLY. A bookmark that also captured filter state would
    # freeze whatever project was selected when it was authored, and then silently show the
    # wrong project to everyone else.
    bookmarks = [
        ("bmOverview", "Portfolio overview", "overview"),
        ("bmCoverage", "Where the data is missing", "sourcecoverage"),
        ("bmScorecard", "Scorecard and how it is scored", "scorecard"),
    ]
    files["definition/bookmarks/bookmarks.json"] = json.dumps({
        "$schema": f"{SCHEMA}/bookmarksMetadata/1.0.0/schema.json",
        # Items carry the NAME only; the display name lives in the bookmark file itself.
        # The metadata file is an index, not a duplicate of the bookmark definitions.
        "items": [{"name": n} for n, _, _ in bookmarks],
    }, indent=2)
    for name, display, target in bookmarks:
        files[f"definition/bookmarks/{name}.bookmark.json"] = json.dumps({
            "$schema": f"{SCHEMA}/bookmark/1.0.0/schema.json",
            "name": name,
            "displayName": display,
            "explorationState": {
                "version": "1.0",
                "activeSection": target,
                # visualContainers is required by the schema, and empty is also what we
                # want: these bookmarks NAVIGATE, they do not restore visual state.
                # Capturing state would pin whatever project was selected when the bookmark
                # was authored and show it to everyone who clicks - a report quietly
                # answering a different question than the one asked.
                "sections": {target: {"visualContainers": {}}},
            },
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
