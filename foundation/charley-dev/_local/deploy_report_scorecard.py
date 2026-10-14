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
import scorecard  # noqa: E402

CHARLEY_DEV = Path(__file__).resolve().parents[1]

dr.REPORT_NAME = "Project Scorecard"
dr.REPORT_DIR = CHARLEY_DEV / "05-reports" / "Project Scorecard.Report"

textbox, card, visual = dr.textbox, dr.card, dr.visual
measure, column = dr.measure, dr.column
MUTED = dr.MUTED

# Text measures shown on cards, at their longest, so the card is sized for the worst case.
dr.CARD_TEXT_SAMPLES.update({
    "Input Check": "Schedule ended - site still active",
    "Performance Rating": "Exceeds Expectations",
})

COMING_SOON = (
    "Coming soon - not scored until the data can be verified: profitability (needs agreed "
    "margin bands), client satisfaction (the Microsoft Forms survey), statutory "
    "sign-offs and NCRs (Compliance), "
    "meeting agendas sent 24 hours ahead, 3-week look-ahead updates, and subcontractor "
    "insurance compliance from the carrier's verification report."
)


def _text(value: str) -> dict:
    return {"expr": {"Literal": {"Value": f"'{value}'"}}}


def button(page: str, key: str, text: str, x, y, w, h, action: str,
           target: str | None = None) -> dict:
    """A button that navigates: 'Back', or 'Drillthrough' to a section page.

    A drill-through button carries the project the page is already filtered to, so Project
    Health -> Schedule & Data Entry keeps the job without a slicer. Right-click drill-through
    on the Portfolio table reaches every section page too, so a button is a shortcut, never
    the only way in.
    """
    link = {"show": dr._ON, "type": _text(action)}
    if target:
        link["drillthroughSection"] = _text(target)
    return {
        "$schema": f"{dr.SCHEMA}/visualContainer/1.0.0/schema.json",
        "name": dr.oid(page, key),
        "position": {"x": x, "y": y, "z": 0, "width": w, "height": h},
        "visual": {
            "visualType": "actionButton",
            "objects": {
                "icon": [{"properties": {"show": dr._OFF}}],
                "text": [{"properties": {"show": dr._ON}},
                         {"properties": {"text": _text(text), "fontSize": dr._num(10)},
                          "selector": {"id": "default"}}],
            },
            "visualContainerObjects": {
                "visualLink": [{"properties": link}],
                "general": [{"properties": {"altText": dr.lit(
                    "Button. Opens the details behind this section for this project." if target
                    else "Button. Returns to the previous page.")}}],
            },
        },
    }


def back(page: str) -> dict:
    return button(page, "back", "< Back", 1140, 16, 120, 32, "Back")


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
    """Every project on one table, the page leadership opens first - and the top of the
    hierarchy: right-click a project to open its Project Health page or any section."""
    p = "psportfolio"
    rank = dr.exclude_unmatched(dr.no_totals(dr.sort_desc(
        visual(p, "ranking", "tableEx", 20, 108, 1240, 400,
               {"Values": [measure("Project Rank"),
                           column("dim_Project", "ProjectName"),
                           measure("Pillar Score"),
                           *[measure(f"{x} Score") for x in scorecard.PILLARS],
                           measure("Scorecard Coverage %"),
                           measure("Performance Rating"),
                           measure("Needs Attention"),
                           measure("Input Check")]},
               title="All projects - ranked score, each pillar (0-1), bonus rating and data-entry check",
               alt="Table. Every project ranked by its weighted health score for the selected "
                   "pillar, with one column per pillar, the share of the score that is measured, "
                   "the bonus-policy rating, a Needs attention flag, and any data-entry problem. "
                   "Right-click a project to drill through to its health page or a section."),
        measure("Pillar Score"))))
    return p, [
        textbox(p, "title", "Portfolio Scorecard", 20, 16, 480, 44),
        pillar_slicer(p),
        textbox(p, "note",
                "Right-click a project and choose Drill through to open it. Pick a pillar to "
                "re-rank by that part only. Blank means not measured, never zero. Rating "
                "cut-offs are proposed until the scorecard workshop confirms them.",
                20, 56, 1240, 44, size=10, color=MUTED),
        rank,
        card(p, "k_reporting", "Projects Reporting", 20, 520, 300, 84),
        card(p, "k_risk", "Projects At Risk", 332, 520, 300, 84,
             title="Projects at risk (score below 0.60)"),
        textbox(p, "coming", COMING_SOON, 644, 520, 616, 136, size=10, color=MUTED),
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
    # Short of the full width: the right 104px holds the tile's Details button.
    out = [textbox(p, f"{key}_h", heading, x, y, TILE_W - 104, 32, size=13)]
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
        p, "challenges", "tableEx", x, y, w, h,
        {"Values": [column("man_Risks", "Description"),
                    column("man_Risks", "Mitigation")]},
        title="Biggest challenges on site - from the team")

    def go(key: str, col: int, row: int, target: str) -> dict:
        return button(p, f"{key}_go", "Details >", COLS[col] + TILE_W - 100, ROWS[row], 100, 28,
                      "Drillthrough", target)

    return p, [
        textbox(p, "title", "Project Health", 20, 16, 480, 44),
        back(p),
        # A drill-through button enables only once a data point carrying the drill field is
        # selected (found live 2026-10-14: every Details button stayed grey, because nothing
        # on this page showed ProjectName). This one-row banner is that data point.
        dr.no_totals(visual(p, "banner", "pivotTable", 520, 2, 600, 64,
               {"Rows": [column("dim_Project", "ProjectName")],
                "Values": [measure("Performance Rating")]},
               alt="Matrix. The project this page is showing and its bonus rating. Select the "
                   "project name to enable the Details buttons, or right-click it to drill "
                   "through to a section.")),
        textbox(p, "note",
                "Select the project name above to enable Details, or right-click it and choose "
                "Drill through. Safety or quality below target caps the rating at Needs Improvement.",
                20, 70, 1240, 34, size=10, color=MUTED),
        *tile(p, "score", "Health score", 0, 0,
              [("Project Scorecard (Measured Only)", "Health score (0-1)"),
               ("Performance Rating", "Bonus rating")], audit),
        *tile(p, "schedule", "Schedule", 1, 0,
              [("Scheduled Finish", "Scheduled finish"),
               ("Milestones Overdue %", "Milestones overdue")], milestones),
        go("schedule", 1, 0, "psschedule"),
        *tile(p, "financial", "Financial", 2, 0,
              [("AR Outstanding", "AR outstanding"),
               ("Avg Days To Payment", "Avg days to payment"),
               ("Outstanding CO Count", "Change orders open"),
               ("COs Over 30 Days", "Open over 30 days"),
               ("Avg CO Days Open", "Avg CO days open"),
               ("Cash Position %", "Cash position")]),
        go("financial", 2, 0, "pschangeorders"),
        *tile(p, "safety", "Safety", 0, 1,
              [("Recordable Incidents", "Recordable incidents"),
               ("Hours Worked", "Hours worked")], safety),
        *tile(p, "quality", "Quality", 1, 1,
              [("Open Observations", "Open observations"),
               ("Open Punch Items", "Open punch items")], quality),
        go("quality", 1, 1, "psquality"),
        *tile(p, "challenge", "Data entry & challenges", 2, 1,
              [("Input Check", "Data-entry check"),
               ("Days Since Daily Log", "Days since daily log")], challenges),
        go("inputs", 2, 1, "psschedule"),
    ]


def page_schedule() -> tuple[str, list[dict]]:
    """Drill-through: is the schedule still true, and is the site filing its daily logs?"""
    p = "psschedule"
    return p, [
        textbox(p, "title", "Schedule & Data Entry", 20, 16, 600, 44),
        back(p),
        textbox(p, "note",
                "A schedule that has run out while the site is still logging or closing punch "
                "items scores 0 on Schedule Performance until it is updated. Daily reports "
                "missed = weekdays with no Procore daily log between the month's first and last log.",
                20, 56, 1240, 44, size=10, color=MUTED),
        card(p, "k_finish", "Scheduled Finish", 20, 108, 240, 84, title="Scheduled finish"),
        card(p, "k_last", "Last Daily Log", 272, 108, 240, 84, title="Last daily log"),
        card(p, "k_since", "Days Since Daily Log", 524, 108, 240, 84, title="Days since daily log"),
        card(p, "k_missed", "Daily Reports Missed", 776, 108, 240, 84, title="Daily reports missed"),
        card(p, "k_check", "Input Check", 1028, 108, 232, 84, title="Data-entry check"),
        dr.sort_desc(visual(p, "list", "tableEx", 20, 204, 760, 452,
               {"Values": [column("fct_Milestone", "MilestoneName"),
                           column("fct_Milestone", "CurrentStart"),
                           column("fct_Milestone", "CurrentFinish"),
                           column("fct_Milestone", "PercentComplete"),
                           column("fct_Milestone", "IsOverdue")]},
               title="Critical-path milestones from Outbuild - latest finish first"),
            column("fct_Milestone", "CurrentFinish")),
        visual(p, "missed", "columnChart", 800, 204, 460, 452,
               {"Category": [column("dim_Date", "MonthYear")],
                "Y": [measure("Daily Reports Missed")]},
               title="Daily reports missed by month"),
    ]


def page_change_orders() -> tuple[str, list[dict]]:
    """Drill-through: the change orders behind the tile, oldest first."""
    p = "pschangeorders"
    return p, [
        textbox(p, "title", "Change Orders", 20, 16, 600, 44),
        back(p),
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
        back(p),
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
    ("Project Health", page_project, True),
    ("Schedule & Data Entry", page_schedule, True),
    ("Change Orders", page_change_orders, True),
    ("Open Quality Items", page_quality, True),
]
dr.DRILLTHROUGH = {
    "pshealth": ("dim_Project", "ProjectName"),
    "psschedule": ("dim_Project", "ProjectName"),
    "pschangeorders": ("dim_Project", "ProjectName"),
    "psquality": ("dim_Project", "ProjectName"),
}


if __name__ == "__main__":
    try:
        raise SystemExit(dr.main())
    except dr.dp.FabricError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
