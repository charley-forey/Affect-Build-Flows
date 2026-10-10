"""Generate and deploy the Project Scorecard report over the Affect Project Report model.

    python deploy_report_scorecard.py            # dry run - write PBIR to disk only
    python deploy_report_scorecard.py --apply    # create/update the report in Fabric

The 2026-10-09 call: one scorecard-first report for the SharePoint hub, instead of a tab
per subject. Portfolio ranks every project on the agreed weighted score and re-ranks by a
single pillar from a slicer, without leaving the page. Project Health is the same footprint
for one project - every section on one screen. Two drill-through pages hold the records
behind the tiles that most need them (change orders over 30 days, open quality items).

Nothing new is computed here. The score is scorecard.py's, the tiles are model measures,
and the Monthly Progress Report and Project Quality Plan are untouched. Metrics the call
said we cannot yet verify are listed as "coming soon", never scored from manual input.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deploy_report as dr  # noqa: E402

CHARLEY_DEV = Path(__file__).resolve().parents[1]

dr.REPORT_NAME = "Project Scorecard"
dr.REPORT_DIR = CHARLEY_DEV / "05-reports" / "Project Scorecard.Report"

textbox, card, visual = dr.textbox, dr.card, dr.visual
measure, column = dr.measure, dr.column
MUTED = dr.MUTED

COMING_SOON = (
    "Coming soon - not scored until the data can be verified: profitability (needs agreed "
    "margin bands), daily reports (Procore daily logs being parsed), client satisfaction, "
    "meeting agendas sent 24 hours ahead, 3-week look-ahead updates, and subcontractor "
    "insurance compliance from the carrier's verification report."
)


def pillar_slicer(page: str) -> dict:
    """Re-rank in place: the call's "show me just schedule" without a new screen.

    Filters dim_ScorecardWeight only, so [Pillar Score] re-scores over the chosen
    categories. Nothing selected = every category = the overall score.
    """
    s = visual(page, "slicer_pillar", "slicer", 516, 4, 240, 54,
               {"Values": [column("dim_ScorecardWeight", "Pillar")]},
               title="Rank by pillar", tab=3, title_size=dr.SLICER_TITLE)
    s["visual"]["objects"] = {
        "data": [{"properties": {"mode": {"expr": {"Literal": {"Value": "'Dropdown'"}}}}}],
        "header": [{"properties": {"show": dr._OFF}}],
    }
    return s


def page_portfolio() -> tuple[str, list[dict]]:
    """Every project, stack-ranked. The page leadership opens first."""
    p = "psportfolio"
    rank = dr.exclude_unmatched(dr.no_totals(dr.sort_desc(
        visual(p, "ranking", "tableEx", 20, 108, 600, 548,
               {"Values": [measure("Project Rank"),
                           column("dim_Project", "ProjectName"),
                           measure("Pillar Score"),
                           measure("Scorecard Coverage %"),
                           measure("Categories Below Target"),
                           measure("Needs Attention")]},
               title="Projects ranked by health score (0-1, highest first)",
               alt="Table. Every project ranked by its weighted health score for the selected "
                   "pillar, with the share of the score that is measured, how many categories "
                   "are below target, and a Needs attention flag. Right-click a project to "
                   "drill through to its records."),
        measure("Pillar Score"))))
    return p, [
        textbox(p, "title", "Portfolio Scorecard", 20, 16, 480, 44),
        pillar_slicer(p),
        textbox(p, "note",
                "Pick a pillar to re-rank by that part of the score only. Needs attention means "
                "two or more categories below target, whatever the rank. Blank means not "
                "measured, never zero. Right-click a project to see its records.",
                20, 56, 1240, 44, size=10, color=MUTED),
        rank,
        card(p, "k_reporting", "Projects Reporting", 640, 108, 300, 84),
        card(p, "k_risk", "Projects At Risk", 960, 108, 300, 84,
             title="Projects at risk (score below 0.60)"),
        # What is pulling each project down: same SWITCH as the rank, one cell per category.
        dr.exclude_unmatched(dr.no_totals(visual(p, "heatmap", "pivotTable", 640, 204, 620, 312,
               {"Rows": [column("dim_Project", "ProjectName")],
                "Columns": [column("dim_ScorecardWeight", "CategoryName")],
                "Values": [measure("Category Score")]},
               title="Score by category (0-3, blank = not measured)",
               alt="Matrix. One row per project, one column per scorecard category, showing "
                   "each category score out of 3. Blank cells are not measured."))),
        textbox(p, "coming", COMING_SOON, 640, 528, 620, 128, size=10, color=MUTED),
    ]


# Project Health: six tiles, three across, two down. Each is a header, cards, then the
# records or trend behind them, so a reader sees every section without changing page.
COLS = (20, 440, 860)
TILE_W = 400
ROWS = (108, 388)
TILE_H = 272
CARD_W, CARD_H = 194, 76


def tile(p: str, key: str, heading: str, col: int, row: int,
         cards: list[tuple[str, str]], body=None) -> list[dict]:
    """A section tile: heading, up to two cards a row, then `body(x, y, w, h)` below."""
    x, y = COLS[col], ROWS[row]
    out = [textbox(p, f"{key}_h", heading, x, y, TILE_W, 32, size=13)]
    cy = y + 34
    for i in range(0, len(cards), 2):
        for j, (name, title) in enumerate(cards[i:i + 2]):
            out.append(card(p, f"{key}_{i + j}", name, x + j * (CARD_W + 12), cy,
                            CARD_W, CARD_H, title=title))
        cy += CARD_H + 4
    if body:
        out.append(body(x, cy, TILE_W, y + TILE_H - cy))
    return out


def page_project() -> tuple[str, list[dict]]:
    """One project, every section, one screen. Chosen with the synced project slicer."""
    p = "pshealth"
    milestones = lambda x, y, w, h: visual(  # noqa: E731
        p, "milestones", "tableEx", x, y, w, h,
        {"Values": [column("fct_Milestone", "MilestoneName"),
                    column("fct_Milestone", "CurrentFinish"),
                    column("fct_Milestone", "IsOverdue")]},
        title="Critical milestones")
    audit = lambda x, y, w, h: dr.no_totals(visual(  # noqa: E731
        p, "audit", "tableEx", x, y, w, h,
        {"Values": [column("dim_ScorecardWeight", "CategoryName"),
                    measure("Category Score"), measure("Category Band")]},
        title="How the score is built"))
    safety = lambda x, y, w, h: visual(  # noqa: E731
        p, "safety_trend", "columnChart", x, y, w, h,
        {"Category": [column("dim_Date", "MonthYear")],
         "Y": [measure("Recordable Incidents")]},
        title="Recordable incidents by month")
    quality = lambda x, y, w, h: dr.keep_true(dr.sort_desc(visual(  # noqa: E731
        p, "quality_open", "tableEx", x, y, w, h,
        {"Values": [column("fct_QualityItem", "ItemType"),
                    column("fct_QualityItem", "Title"),
                    column("fct_QualityItem", "DaysOpen")]},
        title="Open items, oldest first"), column("fct_QualityItem", "DaysOpen")),
        "fct_QualityItem", "IsOpen")
    challenges = lambda x, y, w, h: visual(  # noqa: E731
        p, "challenges", "tableEx", x, y + 40, w, h - 40,
        {"Values": [column("man_Risks", "Description"),
                    column("man_Risks", "Mitigation")]},
        title="Biggest challenges on site - from the team")

    return p, [
        textbox(p, "title", "Project Health", 20, 16, 480, 44),
        textbox(p, "note",
                "Pick one project in the Project slicer; with none picked, every figure blends "
                "the whole portfolio. Right-click the project in a table to drill through to "
                "its change orders or open quality items.",
                20, 56, 1240, 44, size=10, color=MUTED),
        *tile(p, "score", "Health score", 0, 0,
              [("Project Scorecard (Measured Only)", "Health score (0-1)"),
               ("Scorecard Coverage %", "Share measured")], audit),
        *tile(p, "schedule", "Schedule", 1, 0,
              [("Completion Variance Days", "Finish vs baseline, days"),
               ("Milestones Overdue %", "Milestones overdue")], milestones),
        *tile(p, "financial", "Financial", 2, 0,
              [("AR Outstanding", "AR outstanding"),
               ("Avg Days To Payment", "Avg days to payment"),
               ("Outstanding CO Count", "Change orders open"),
               ("COs Over 30 Days", "Open over 30 days"),
               ("Avg CO Days Open", "Avg CO days open"),
               ("Cash Position %", "Cash position")]),
        *tile(p, "safety", "Safety", 0, 1,
              [("Recordable Incidents", "Recordable incidents"),
               ("Hours Worked", "Hours worked")], safety),
        *tile(p, "quality", "Quality", 1, 1,
              [("Open Observations", "Open observations"),
               ("Open Punch Items", "Open punch items")], quality),
        *tile(p, "challenge", "Challenges & reporting", 2, 1, [], challenges),
        textbox(p, "challenge_note",
                "The one manual input. Daily reports: coming soon.",
                COLS[2], ROWS[1] + 34, TILE_W, 36, size=10, color=MUTED),
    ]


def page_change_orders() -> tuple[str, list[dict]]:
    """Drill-through: the change orders behind the tile, oldest first."""
    p = "pschangeorders"
    return p, [
        textbox(p, "title", "Change Orders", 20, 16, 600, 44),
        textbox(p, "note",
                "Pending change orders for the project you drilled from, oldest first. The "
                "average can hide one sitting out at 90 days; this list cannot.",
                20, 56, 1240, 44, size=10, color=MUTED),
        card(p, "k_open", "Outstanding CO Count", 20, 108, 296, 84, title="Change orders open"),
        card(p, "k_30", "COs Over 30 Days", 332, 108, 296, 84, title="Open over 30 days"),
        card(p, "k_avg", "Avg CO Days Open", 644, 108, 296, 84, title="Avg days open"),
        card(p, "k_amt", "Pending Change Orders", 956, 108, 304, 84, title="Pending value"),
        dr.keep_true(dr.sort_desc(visual(p, "list", "tableEx", 20, 204, 1240, 452,
               {"Values": [column("fct_ChangeOrder", "ChangeOrderNumber"),
                           column("fct_ChangeOrder", "StatusLabel"),
                           column("fct_ChangeOrder", "CreatedDate"),
                           column("fct_ChangeOrder", "DaysOpen"),
                           measure("Change Order Amount")]},
               title="Pending change orders - oldest first"),
            column("fct_ChangeOrder", "DaysOpen")), "fct_ChangeOrder", "IsPending"),
    ]


def page_quality() -> tuple[str, list[dict]]:
    """Drill-through: every open observation and punch item, oldest first."""
    p = "psquality"
    return p, [
        textbox(p, "title", "Open Quality Items", 20, 16, 600, 44),
        textbox(p, "note",
                "Open Procore observations and punch items for the project you drilled from, "
                "oldest first. Past due means open beyond its due date.",
                20, 56, 1240, 44, size=10, color=MUTED),
        card(p, "k_obs", "Open Observations", 20, 108, 296, 84, title="Open observations"),
        card(p, "k_punch", "Open Punch Items", 332, 108, 296, 84, title="Open punch items"),
        card(p, "k_due", "Quality Items Past Due", 644, 108, 296, 84, title="Past due"),
        card(p, "k_inc", "Recordable Incidents", 956, 108, 304, 84, title="Recordable incidents"),
        dr.keep_true(dr.sort_desc(visual(p, "list", "tableEx", 20, 204, 1240, 452,
               {"Values": [column("fct_QualityItem", "ItemType"),
                           column("fct_QualityItem", "ItemNumber"),
                           column("fct_QualityItem", "Title"),
                           column("fct_QualityItem", "Trade"),
                           column("fct_QualityItem", "AssignedTo"),
                           column("fct_QualityItem", "DueDate"),
                           column("fct_QualityItem", "DaysOpen")]},
               title="Open quality items - oldest first"),
            column("fct_QualityItem", "DaysOpen")), "fct_QualityItem", "IsOpen"),
    ]


dr.PAGES = [
    ("Portfolio Scorecard", page_portfolio, False),
    ("Project Health", page_project, False),
    ("Change Orders", page_change_orders, True),
    ("Open Quality Items", page_quality, True),
]
dr.DRILLTHROUGH = {
    "pschangeorders": ("dim_Project", "ProjectName"),
    "psquality": ("dim_Project", "ProjectName"),
}


if __name__ == "__main__":
    try:
        raise SystemExit(dr.main())
    except dr.dp.FabricError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
