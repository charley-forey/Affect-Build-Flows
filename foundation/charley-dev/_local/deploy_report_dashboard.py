"""Generate and deploy the AFFECT Weekly Dashboard report over the Affect Project Report model.

    python deploy_report_dashboard.py            # dry run - write PBIR to disk only
    python deploy_report_dashboard.py --apply    # create/update the report in Fabric

The three pages of "AFFECT Weekly Dashboard Layout 10-21-26.pptx", built to the deck's own
geometry - the deck is 17 x 11 in, so at 80 px to the inch every page is 1360 x 880 and a
shape at (x in, y in) sits at (80x, 80y) px:

  1. Executive Dashboard       the company: revenue, margin, backlog, cash, safety, execution
  2. Project Portfolio | Status every active project: phase, the four pillars, team, grade
  3. Project Overview           one project; reached by drill-through or its project picker

plus Grade Detail, the drill-through behind a grade - the "Detail Scorecard" the deck's
slide 2 asks for: every Scorecard.xlsx measure, its reading, band, score and weight.

The deck's TBD callouts are honoured, not papered over. A tile whose data does not exist yet
(revenue plan, EBITDA, the commercial pipeline, executive decisions, field productivity)
says what it is waiting for - it never shows an invented number. Every value on these pages
is a dashboard.py measure; nothing is computed here.
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deploy_report as dr  # noqa: E402
import deploy_report_scorecard as rs  # noqa: E402
import dashboard as dash  # noqa: E402

CHARLEY_DEV = Path(__file__).resolve().parents[1]
REPORT_NAME = "AFFECT Weekly Dashboard"
REPORT_DIR = CHARLEY_DEV / "05-reports" / "AFFECT Weekly Dashboard.Report"
W, H = 1360, 880
PX = 80  # per deck inch

NAVY, TEAL, GREEN, AMBER, RED, SLATE = dash.NAVY, dash.TEAL, dash.GREEN, dash.AMBER, dash.RED, dash.SLATE
PAGE_BG, CARD_BG, LINE, PALE = "#EEF1F5", "#FFFFFF", "#DDE4EB", "#E7EDF2"
measure, column, lit, oid, _ON, _OFF, _num = dr.measure, dr.column, dr.lit, dr.oid, dr._ON, dr._OFF, dr._num

dr.CARD_TEXT_SAMPLES.update({
    "Report Week Label": "Last week  Oct 12 - Oct 18, 2026",
    "Week Header": "CONSTRUCTION OPERATIONS  |  LAST WEEK  OCT 12 - OCT 18, 2026",
    "Gross Margin Subline": "-9.1 pts vs 12.5% target",
    "At Risk Breakdown": "Schedule (4)  -  Budget (2)",
    "Financial Exceptions": "Cash negative: -$28,758  -  $17,166 of AR over 60 days",
    "Executive Focus": "EXECUTIVE FOCUS:  OAC Meeting  -  Safety Inspections  -  Quality Inspections",
})


def _color(c: str) -> dict:
    return {"solid": {"color": lit(c)}}


def _mref(name: str) -> dict:
    return {"expr": {"Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": name}}}


def boxed(v: dict, fill: str | None = CARD_BG, radius: int = 0, border: str | None = None,
          shadow: bool = False, header: bool = False, pad: int = 4) -> dict:
    """Container fill, rounded border and no visual header - the deck's white cards."""
    c = v["visual"].setdefault("visualContainerObjects", {})
    c["background"] = [{"properties": {"show": _ON if fill else _OFF,
                                       **({"color": _color(fill), "transparency": _num(0)} if fill else {})}}]
    c["border"] = [{"properties": {"show": _ON if (border or radius) else _OFF,
                                   "color": _color(border or fill or CARD_BG), "radius": _num(radius)}}]
    c["dropShadow"] = [{"properties": {"show": _ON if shadow else _OFF}}]
    c["visualHeader"] = [{"properties": {"show": _ON if header else _OFF}}]
    c["padding"] = [{"properties": {"top": _num(pad), "bottom": _num(pad), "left": _num(pad * 1.5),
                                    "right": _num(pad * 1.5)}}]
    return v


def z(v: dict, level: int) -> dict:
    v["position"]["z"] = level
    return v


def text(p: str, key: str, value: str, x, y, w, h, size: float = 9, color: str = SLATE,
         bold: bool = True, fill: str | None = None, radius: int = 0, align: str = "left") -> dict:
    """A textbox with the deck's type: Arial, caps labels in slate, headings in navy."""
    if value.strip():
        # A line needs ~1.33 em plus the textbox's own inner margin, or the service draws a
        # scrollbar beside the label (seen live at 20px for 9pt).
        # Grow upward: the label's bottom edge sits on whatever it captions.
        need = round(size * 4 / 3 * 1.33) + 8
        if need > h:
            y, h = max(0, y - (need - h)), need
    v = {
        "$schema": f"{dr.SCHEMA}/visualContainer/1.0.0/schema.json",
        "name": oid(p, key),
        "position": {"x": x, "y": y, "z": 2000, "width": w, "height": h},
        "visual": {
            "visualType": "textbox",
            "objects": {"general": [{"properties": {"paragraphs": [{
                "horizontalTextAlignment": align,
                "textRuns": [{"value": value, "textStyle": {
                    "fontFamily": "Arial", "fontSize": f"{size}pt", "color": color,
                    "fontWeight": "bold" if bold else "normal"}}]}]}}]},
            "visualContainerObjects": {"general": [{"properties": {"altText": lit(value.strip() or "Decoration")}}]},
        },
    }
    # No padding: a 20px label with the container's default padding scrolled (seen live).
    return boxed(v, fill=fill, radius=radius, pad=0)


def panel(p: str, key: str, x, y, w, h, fill: str = CARD_BG, radius: int = 12) -> dict:
    """A card behind a group of visuals. A blank textbox, so it costs no query."""
    return z(text(p, key, " ", x, y, w, h, fill=fill, radius=radius), 0)


def kpi_value(p: str, key: str, name: str, x, y, w, h, size: int = 20, color: str = NAVY,
              precision: int | None = None, units: int | None = None, align: str = "left") -> dict:
    """A bare value: no title, no category label, deck navy, on the panel behind it."""
    v = dr.visual(p, key, "card", x, y, w, h, {"Values": [measure(name)]},
                  alt=f"Card. {name}.")
    v["visual"]["visualContainerObjects"].pop("title", None)
    labels = {"fontSize": _num(size), "color": _color(color), "fontFamily": lit("Arial")}
    if precision is not None:
        labels["labelPrecision"] = _num(precision)
    if units is not None:
        labels["labelDisplayUnits"] = _num(units)
    v["visual"]["objects"] = {
        "labels": [{"properties": labels}],
        "categoryLabels": [{"properties": {"show": _OFF}}],
        "wordWrap": [{"properties": {"show": _ON}}],
    }
    c = boxed(v, fill=None)["visual"]["visualContainerObjects"]
    c["title"] = [{"properties": {"show": _OFF}}]
    return z(v, 3000)


def tile(p: str, key: str, label: str, value: str, sub: str | None, x, y, w, h, accent: str = TEAL,
         size: int = 22, sub_color: str = GREEN, precision: int | None = None, units: int | None = None,
         pending: str | None = None) -> list[dict]:
    """The deck's KPI tile: white card, coloured bar on the left, caps label, big value,
    one line under it. `pending` replaces the value with what the tile is waiting for."""
    out = [panel(p, f"{key}_bg", x, y, w, h, radius=8),
           z(text(p, f"{key}_bar", " ", x, y, 6, h, fill=accent), 1),
           text(p, f"{key}_lbl", label, x + 16, y + 10, w - 24, 20, size=9)]
    if pending:
        out.append(text(p, f"{key}_pending", pending, x + 16, y + 36, w - 24, h - 44, size=9,
                        color=SLATE, bold=False))
        return out
    out.append(kpi_value(p, f"{key}_val", value, x + 10, y + 32, w - 18, 40, size=size,
                         precision=precision, units=units))
    if sub:
        out.append(kpi_value(p, f"{key}_sub", sub, x + 10, y + h - 30, w - 18, 26, size=8, color=sub_color))
    return out


def header(p: str, title: str, sub_measure: str, right_measure: str, slicer: bool = True) -> list[dict]:
    """Navy band, teal rule, white title; the week (and, where useful, the project) pickers."""
    out = [z(text(p, "hdr_band", " ", 0, 0, W, 81, fill=NAVY), 0),
           z(text(p, "hdr_rule", " ", 0, 81, W, 3, fill=TEAL), 1),
           text(p, "title", title, 36, 4, 760, 43, size=20, color="#FFFFFF"),
           kpi_value(p, "hdr_sub", sub_measure, 30, 50, 760, 26, size=9, color="#C7D7E7"),
           kpi_value(p, "hdr_right", right_measure, 800, 52, 540, 26, size=8, color="#C7D7E7")]
    if slicer:
        out.append(week_slicer(p, 1100, 8, 236, 44))
    return out


def week_slicer(p: str, x, y, w, h) -> dict:
    """Single week, default 'Last week'. Nothing picked also means last week (the measures
    default to it), so a cleared slicer never silently means "every week"."""
    s = dr.visual(p, "slicer_week", "slicer", x, y, w, h,
                  {"Values": [column("dim_ReportWeek", "WeekLabel")]},
                  title="Reporting week", tab=1, sync="week", title_size=9,
                  alt="Slicer. Picks the reporting week; last week by default.")
    s["visual"]["objects"] = {
        "data": [{"properties": {"mode": lit("Dropdown")}}],
        "selection": [{"properties": {"singleSelect": _ON, "strictSingleSelect": _ON}}],
        "header": [{"properties": {"show": _OFF}}],
        "general": [{"properties": {"filter": {"filter": {
            "Version": 2,
            "From": [{"Name": "w", "Entity": "dim_ReportWeek", "Type": 0}],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "w"}}, "Property": "WeekLabel"}}],
                "Values": [[{"Literal": {"Value": "'Last week'"}}]]}}}]}}}}],
    }
    # A white box on the navy band: the dropdown's own text is dark (seen live).
    return boxed(s, fill=CARD_BG, radius=6)


def bar(p: str, key: str, name: str, x, y, w, h, color: str) -> list[dict]:
    """A progress bar on a 0-100% axis over a pale track - the deck's execution bars."""
    # One category row to draw against: a bar chart with no category renders only its
    # placeholder icon (seen live). dim_DashSetting is disconnected, so the one row picked
    # by the filter below changes no number.
    v = dr.visual(p, key, "barChart", x, y, w, h,
                  {"Category": [column("dim_DashSetting", "SettingKey")], "Y": [measure(name)]},
                  alt=f"Bar. {name} on a 0 to 100 percent scale.")
    v["filterConfig"] = {"filters": [{
        "name": oid(v["name"], "one-row"), "type": "Categorical",
        "field": {"Column": {"Expression": {"SourceRef": {"Entity": "dim_DashSetting"}}, "Property": "SettingKey"}},
        "filter": {"Version": 2, "From": [{"Name": "s", "Entity": "dim_DashSetting", "Type": 0}],
                   "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {
                       "Source": "s"}}, "Property": "SettingKey"}}], "Values": [[{"Literal": {"Value": "'min_coverage'"}}]]}}}]},
        "howCreated": "User"}]}
    v["visual"]["visualContainerObjects"].pop("title", None)
    v["visual"]["objects"] = {
        # Hidden axes still draw their titles, which leave a 20px chart no plot area (seen live).
        "valueAxis": [{"properties": {"show": _OFF, "showAxisTitle": _OFF, "start": _num(0),
                                      "end": {"expr": {"Literal": {"Value": "1D"}}}}}],
        "categoryAxis": [{"properties": {"show": _OFF, "showAxisTitle": _OFF, "innerPadding": _num(0)}}],
        "dataPoint": [{"properties": {"fill": _color(color)}}],
        "labels": [{"properties": {"show": _OFF}}],
        "legend": [{"properties": {"show": _OFF}}],
        "plotArea": [{"properties": {"transparency": _num(100)}}],
        # A 20px chart is below the responsive cut-off, which swaps the bar for an icon (seen live).
        "general": [{"properties": {"responsive": _OFF}}],
    }
    c = boxed(v, fill=None)["visual"]["visualContainerObjects"]
    c["title"] = [{"properties": {"show": _OFF}}]
    c["padding"] = [{"properties": {"top": _num(0), "bottom": _num(0), "left": _num(0), "right": _num(0)}}]
    return [z(text(p, f"{key}_track", " ", x, y + 3, w, h - 6, fill=PALE, radius=3), 1000), z(v, 3000)]


def styled_table(v: dict, pills: dict[str, tuple[str, str]] | None = None, header_fill: str = NAVY) -> dict:
    """Deck table: navy header, white body, and PILL cells - field-value conditional
    formatting, the fill and the text colour each from a measure, so the colour and the
    number printed in the cell always come from the same score."""
    vis = v["visual"]
    objects = vis.setdefault("objects", {})
    objects["columnHeaders"][0]["properties"].update(
        {"backColor": _color(header_fill), "fontColor": _color("#FFFFFF"), "fontFamily": lit("Arial")})
    objects["grid"] = [{"properties": {"gridHorizontal": _ON, "gridHorizontalColor": _color(LINE),
                                       "gridVertical": _OFF, "rowPadding": _num(6)}}]
    for cell, (fill, ink) in (pills or {}).items():
        ref = f"_Measures.{cell}"
        sel = {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": ref}
        props = {"backColor": {"solid": {"color": _mref(fill)}}}
        # Text colour from a measure, or fixed white when ink is None.
        props["fontColor"] = {"solid": {"color": _mref(ink)}} if ink else _color("#FFFFFF")
        objects["values"].append({"properties": props, "selector": sel})
        objects.setdefault("columnFormatting", []).append(
            {"properties": {"alignment": lit("Center")}, "selector": {"metadata": ref}})
    return boxed(v, fill=CARD_BG, header=True)


def table(p: str, key: str, x, y, w, h, fields: list, title: str | None = None, alt: str | None = None,
          pills: dict | None = None) -> dict:
    v = dr.no_totals(dr.visual(p, key, "tableEx", x, y, w, h, {"Values": fields}, title=title, alt=alt,
                               title_size=10))
    return z(styled_table(v, pills), 3000)


def flagged(v: dict, flag: str) -> dict:
    """Rows only where a "Yes" flag measure says so (Near Term Flag, Active Flag, ...)."""
    return rs.measure_filter(v, flag, "Yes")


def footer(p: str, note: str) -> list[dict]:
    return [text(p, "footer", note, 36, 852, W - 72, 22, size=7.5, color=SLATE, bold=False)]


def button(p: str, key: str, label: str, x, y, w, h, action: str, target: str | None = None) -> dict:
    b = rs.button(p, key, label, x, y, w, h, action, target)
    b["position"]["z"] = 4000
    return b


# --------------------------------------------------------------------------- pages

def page_executive() -> tuple[str, list[dict]]:
    """Deck slide 1. The company in one screen; every tile Active projects only."""
    p = "dsexec"
    y0, th = 102, 110
    xs = [37, 254, 470, 686, 903, 1119]
    tw = 204
    out = [*header(p, "EXECUTIVE DASHBOARD", "Week Header", "Data As Of Header")]
    out += tile(p, "k_rev", "REVENUE YTD", "Revenue YTD", None, xs[0], y0, tw, th, accent=GREEN,
                precision=1, units=1000000)
    out.append(text(p, "k_rev_note", "Sage AR invoiced, net of retainage  -  plan not set yet", xs[0] + 16,
                    y0 + th - 28, tw - 24, 24, size=7, color=SLATE, bold=False))
    out += tile(p, "k_gm", "GROSS MARGIN", "Portfolio Gross Margin %", "Gross Margin Subline", xs[1], y0, tw, th,
                accent=GREEN, precision=1, sub_color=AMBER)
    out += tile(p, "k_backlog", "BACKLOG", "Backlog", "Backlog Subline", xs[2], y0, tw, th, accent=TEAL,
                precision=1, units=1000000, sub_color=GREEN)
    out += tile(p, "k_active", "ACTIVE PROJECTS", "Active Projects", "Attention Subline", xs[3], y0, tw, th,
                accent=AMBER, sub_color=AMBER)
    out += tile(p, "k_cash", "CASH POSITION", "Portfolio Cash Position", "Cash Subline", xs[4], y0, tw, th,
                accent=GREEN, precision=1, units=1000000)
    out += tile(p, "k_safety", "SAFETY  •  INSPECTIONS", "Portfolio Safety Score", "Safety Subline",
                xs[5], y0, tw, th, accent=GREEN, sub_color=SLATE)

    # Financial performance (deck 0.46-6.61 in)
    fx, fy, fw, fh = 37, 230, 492, 381
    out += [panel(p, "fin_bg", fx, fy, fw, fh),
            text(p, "fin_h", "FINANCIAL PERFORMANCE", fx + 18, fy + 12, fw - 36, 26, size=12, color=NAVY),
            z(text(p, "fin_rule", " ", fx + 18, fy + 42, fw - 36, 1, fill=LINE), 1),
            text(p, "fin_sub", "REVENUE  •  ACTUAL BY MONTH  (PLAN: AWAITING DATA ENTRY)", fx + 18, fy + 50,
                 fw - 36, 22, size=8.5)]
    chart = dr.visual(p, "fin_chart", "clusteredColumnChart", fx + 12, fy + 74, fw - 24, 220,
                      {"Category": [column("dim_Date", "MonthYear")], "Y": [measure("Revenue Last 6 Months")]},
                      alt="Column chart. Revenue invoiced in Sage by month, the last six months.")
    chart["visual"]["visualContainerObjects"]["title"] = [{"properties": {"show": _OFF}}]
    chart["visual"]["objects"] = {"dataPoint": [{"properties": {"fill": _color(TEAL)}}],
                                  "labels": [{"properties": {"show": _ON, "labelDisplayUnits": _num(1000000),
                                                             "labelPrecision": _num(1), "fontSize": _num(8)}}],
                                  "valueAxis": [{"properties": {"show": _ON, "labelDisplayUnits": _num(1000000),
                                                                "showAxisTitle": _OFF}}],
                                  "categoryAxis": [{"properties": {"show": _ON, "fontSize": _num(8),
                                                                   "showAxisTitle": _OFF}}],
                                  "legend": [{"properties": {"show": _OFF}}]}
    out.append(z(boxed(chart, fill=None), 3000))
    out += [z(text(p, "fin_rule2", " ", fx + 18, fy + 306, fw - 36, 1, fill=LINE), 1),
            text(p, "fin_ebitda", "EBITDA", fx + 18, fy + 318, 80, 22, size=9),
            text(p, "fin_ebitda_v", "Needs Sage general ledger (overheads) - not yet ingested", fx + 18, fy + 342,
                 220, 34, size=8, color=SLATE, bold=False),
            text(p, "fin_ar", "AR > 60 DAYS", fx + 270, fy + 318, 110, 22, size=9),
            kpi_value(p, "fin_ar_v", "AR Over 60 Days", fx + 262, fy + 342, 200, 34, size=18, color=AMBER,
                      precision=1, units=1000000)]

    # Project execution (deck 6.79-12.06 in)
    ex, ey, ew, eh = 543, 230, 422, 381
    out += [panel(p, "exe_bg", ex, ey, ew, eh),
            text(p, "exe_h", "PROJECT EXECUTION", ex + 18, ey + 12, ew - 36, 26, size=12, color=NAVY),
            z(text(p, "exe_rule", " ", ex + 18, ey + 42, ew - 36, 1, fill=LINE), 1)]
    rows = [("ON SCHEDULE", "On Schedule Text", "On Schedule Ratio", GREEN, "forecast finish on or before baseline"),
            ("ON BUDGET", "On Budget Text", "On Budget Ratio", TEAL, "forecast final cost within budget"),
            ("SUBCONTRACTOR COVERAGE", "Portfolio Subcontractor Coverage", "Portfolio Subcontractor Coverage",
             "#235A89", "committed / buyable budget"),
            ("CHANGE ORDERS APPROVED", "Change Orders Approved %", "Change Orders Approved %", AMBER,
             "approved / approved + pending value")]
    for i, (lbl, val, ratio, color, hint) in enumerate(rows):
        ry = ey + 48 + i * 64
        out += [text(p, f"exe_{i}_l", lbl, ex + 18, ry, 250, 24, size=9),
                kpi_value(p, f"exe_{i}_v", val, ex + ew - 128, ry - 6, 112, 28, size=11, color=NAVY),
                *bar(p, f"exe_{i}_bar", ratio, ex + 18, ry + 24, ew - 36, 20, color),
                text(p, f"exe_{i}_hint", hint, ex + 18, ry + 44, ew - 176, 20, size=6.5, color=SLATE, bold=False)]
    out += [z(text(p, "exe_rule2", " ", ex + 18, ey + 308, ew - 36, 1, fill=LINE), 1),
            text(p, "exe_fp", "FIELD PRODUCTIVITY", ex + 18, ey + 312, 170, 24, size=9),
            text(p, "exe_fp_v", "Calculation criteria needed", ex + 190, ey + 312, 214, 22, size=8,
                 color=SLATE, bold=False),
            text(p, "exe_risk", "PROJECTS AT RISK", ex + 18, ey + 348, 136, 24, size=9),
            kpi_value(p, "exe_risk_v", "Projects At Risk (Grade)", ex + 160, ey + 340, 60, 38, size=20, color=RED),
            kpi_value(p, "exe_risk_why", "At Risk Breakdown", ex + 224, ey + 342, ew - 242, 36, size=8, color=SLATE)]

    # Commercial & pipeline (deck 12.24-16.54 in) - TBD: Need Data Entry Capability.
    cx, cy, cw, ch = 979, 230, 344, 381
    out += [panel(p, "com_bg", cx, cy, cw, ch),
            text(p, "com_h", "COMMERCIAL & PIPELINE", cx + 18, cy + 12, cw - 36, 26, size=12, color=NAVY),
            z(text(p, "com_rule", " ", cx + 18, cy + 42, cw - 36, 1, fill=LINE), 1),
            text(p, "com_pending",
                 "Awaiting data entry. The CRM is being replaced, so there is no system to read the "
                 "pipeline from yet. A short SharePoint list - weighted pipeline, value at proposal, "
                 "shortlisted and negotiation, and the bid hit rate against its 35% target - will "
                 "feed this panel; until then it stays empty rather than showing sample numbers.",
                 cx + 18, cy + 56, cw - 36, 170, size=9, color=SLATE, bold=False, fill="#F6F8FA", radius=8),
            text(p, "com_fields", "WEIGHTED PIPELINE  •  PIPELINE BY STAGE  •  BID HIT RATE",
                 cx + 18, cy + 240, cw - 36, 34, size=8)]

    # Priority projects (deck 0.46-10.9 in) - "Top 3 based on calc from Page 2, lowest first".
    px_, py, pw, ph = 37, 626, 834, 214
    out += [panel(p, "pri_bg", px_, py, pw, ph),
            text(p, "pri_h", "PRIORITY PROJECTS  •  EXCEPTION VIEW", px_ + 18, py + 10, 420, 26, size=12, color=NAVY),
            text(p, "pri_note", "The three lowest grades on the Portfolio page", px_ + 440, py + 14, 376, 20, size=8,
                 color=SLATE, bold=False, align="right")]
    pri = table(p, "pri_tbl", px_ + 12, py + 40, pw - 24, ph - 50,
                [rs.shown_as(column("dim_Project", "ProjectName"), "Project"),
                 rs.shown_as(measure("Current Contract"), "Contract"),
                 rs.shown_as(measure("Billed % Of Contract"), "% Complete (billed)"),
                 rs.shown_as(measure("Projected Gross Margin %"), "Margin"),
                 rs.shown_as(measure("Grade Cell"), "Grade"),
                 rs.shown_as(measure("Grade Status"), "Status")],
                alt="Table. The three active projects with the lowest grades: contract, share billed, projected "
                    "margin, grade and status. Right-click a project to open it.",
                pills={"Grade Cell": ("Grade Colour", "Grade Ink")})
    # Top 3 by [Priority Score] (100 less the grade, active scored projects only): one grade
    # per project. A per-row RANKX over every project's grade ran out of memory (seen live).
    pri = dr.top_n(pri, "dim_Project", "ProjectName", "Priority Score", 3)
    pri["visual"]["query"]["sortDefinition"] = {"sort": [{"field": measure("Priority Score")["field"],
                                                          "direction": "Descending"}], "isDefaultSort": True}
    out.append(pri)

    # Executive decisions / watchlist (deck 11.2-16.6 in) - TBD: Need Data Entry Capability.
    wx, wy, ww, wh = 885, 626, 438, 214
    out += [panel(p, "wl_bg", wx, wy, ww, wh),
            text(p, "wl_h", "EXECUTIVE DECISIONS / WATCHLIST", wx + 18, wy + 10, ww - 36, 26, size=12, color=NAVY),
            text(p, "wl_pending",
                 "Awaiting data entry: leadership's three focus items for the month (the decision, and "
                 "the project or issue behind it). A SharePoint list will feed this panel, alongside the "
                 "projects leadership wants always shown under Priority Projects.",
                 wx + 18, wy + 42, ww - 36, 90, size=8.5, color=SLATE, bold=False, fill="#F6F8FA", radius=8),
            z(text(p, "wl_dq_bg", " ", wx + 18, wy + 140, ww - 36, 64, fill="#FFF0CF", radius=8), 1000),
            kpi_value(p, "wl_dq", "Data Notice", wx + 26, wy + 144, ww - 52, 56, size=8, color="#986319")]
    out += footer(p, "Executive review  •  Active projects only (Procore activity in the last 60 days, not yet "
                     "100% paid)  •  Margin: Procore budget forecast, CM fee excluded  •  Cash position: "
                     "billings - retainage receivable - unpaid AR - (costs - unpaid AP - retainage payable)  •  "
                     "Safety: inspections performed in the week, 5 = 80%")
    return p, out


def page_portfolio() -> tuple[str, list[dict]]:
    """Deck slide 2. The four pillars and the grade, one row per active project."""
    p = "dsportfolio"
    out = [*header(p, "PROJECT PORTFOLIO  |  STATUS", "Week Header", "Portfolio Header")]
    tiles = [("PROJECTS", "Active Projects", "In portfolio", TEAL),
             ("ON TRACK", "Projects On Track", "Grade 90 and over", GREEN),
             ("NEEDS ATTENTION", "Projects Needing Attention", "Grade under 75", RED),
             ("MONITOR", "Projects Monitor", "Grade 75-89", AMBER),
             ("UNSCORED", "Projects Unscored", "Awaiting data", SLATE)]
    for i, (lbl, m, sub, color) in enumerate(tiles):
        x = 36 + i * 262
        out += [panel(p, f"k{i}_bg", x, 100, 246, 84, radius=8),
                z(text(p, f"k{i}_bar", " ", x, 100, 6, 84, fill=color), 1),
                text(p, f"k{i}_l", lbl, x + 18, 108, 210, 20, size=9),
                kpi_value(p, f"k{i}_v", m, x + 12, 128, 90, 50, size=24, color=NAVY),
                text(p, f"k{i}_s", sub, x + 104, 148, 136, 20, size=8, color=SLATE, bold=False)]
    out += [panel(p, "tbl_bg", 36, 198, 1288, 450),
            text(p, "tbl_h", "ACTIVE PROJECTS  •  PERFORMANCE & ACCOUNTABILITY", 56, 208, 760, 28, size=13, color=NAVY),
            text(p, "tbl_note", "Right-click a project and choose Drill through to open it or its grade detail",
                 820, 212, 484, 20, size=8, color=SLATE, bold=False, align="right")]
    grid = table(p, "portfolio", 48, 240, 1264, 396,
                 [rs.shown_as(column("dim_Project", "ProjectName"), "Project"),
                  rs.shown_as(measure("Phase Label"), "Current phase"),
                  rs.shown_as(measure("Safety Cell"), "Safety"),
                  rs.shown_as(measure("Quality Cell"), "Quality"),
                  rs.shown_as(measure("Schedule Cell"), "Schedule"),
                  rs.shown_as(measure("Budget Cell"), "Budget"),
                  rs.shown_as(measure("Team Initials"), "Team"),
                  rs.shown_as(measure("Grade Cell"), "Grade"),
                  rs.shown_as(measure("Measures Below Target"), "Below target")],
                 alt="Table. Every active project: current phase, the Safety, Quality, Schedule and Budget pillars "
                     "(the headline reading and the pillar score, coloured by the score), the team's initials "
                     "from Procore, the weighted grade out of 100 and how many measures are below target. "
                     "Filtered to active projects; clear the Active Flag filter in the Filters pane to see all. "
                     "Right-click a project to drill through to its overview or grade detail.",
                 pills={"Safety Cell": ("Safety Colour", "Safety Ink"),
                        "Quality Cell": ("Quality Colour", "Quality Ink"),
                        "Schedule Cell": ("Schedule Colour", "Schedule Ink"),
                        "Budget Cell": ("Budget Colour", "Budget Ink"),
                        "Grade Cell": ("Grade Colour", "Grade Ink")})
    rs.widen(grid, {"ProjectName": 4, "Phase Label": 2, "Schedule Cell": 3, "Budget Cell": 3, "Safety Cell": 2,
                    "Quality Cell": 2, "Team Initials": 1})
    # Stack-ranked, worst grade first (Oct 21 call); unscored projects sort last.
    grid["visual"]["query"]["sortDefinition"] = {"sort": [{"field": measure("Priority Score")["field"],
                                                           "direction": "Descending"}], "isDefaultSort": True}
    out.append(flagged(grid, "Active Flag"))
    out += [panel(p, "off_bg", 36, 660, 1288, 172),
            text(p, "off_h", "NOT ON THE ACTIVE LIST", 56, 668, 560, 24, size=10, color=NAVY),
            text(p, "off_note", "Inactive = no Procore activity in 60 days; Archived = 100% paid. Still graded, not counted.",
                 640, 670, 664, 20, size=8, color=SLATE, bold=False, align="right")]
    off = table(p, "inactive", 48, 694, 1264, 132,
                [rs.shown_as(column("dim_Project", "ProjectName"), "Project"),
                 rs.shown_as(measure("Status Note"), "Status"),
                 rs.shown_as(measure("Last Project Activity"), "Last Procore activity"),
                 rs.shown_as(measure("Phase Label"), "Phase"),
                 rs.shown_as(measure("AR Outstanding"), "AR outstanding"),
                 rs.shown_as(measure("Grade Cell"), "Grade")],
                alt="Table. Projects that are inactive or archived, with the last Procore activity, phase, AR still "
                    "owed and grade.",
                pills={"Grade Cell": ("Grade Colour", "Grade Ink")})
    rs.widen(off, {"ProjectName": 3, "Status Note": 3, "Phase Label": 1})
    out.append(flagged(off, "Not Active Flag"))
    out += footer(p, "GRADE   90+ On track   •   75-89 Monitor   •   under 75 Needs attention   •   "
                     "— No data      Cells: headline reading  ·  pillar score (the colour)      Schedule: days "
                     "ahead (+) / behind (-) baseline   Budget: projected gross margin   Safety / Quality: inspections "
                     "performed in the week      Weights: Schedule 50  Budget 30  Safety 15  Quality 5")
    return p, out


def page_project() -> tuple[str, list[dict]]:
    """Deck slide 3. One project; drill-through target, or pick it in the header."""
    p = "dsproject"
    out = [z(text(p, "hdr_band", " ", 0, 0, W, 81, fill=NAVY), 0),
           z(text(p, "hdr_rule", " ", 0, 81, W, 3, fill=TEAL), 1),
           text(p, "title", "PROJECT OVERVIEW  |", 36, 4, 300, 43, size=20, color="#FFFFFF"),
           kpi_value(p, "hdr_proj", "Project Title", 340, 8, 500, 38, size=20, color="#FFFFFF"),
           kpi_value(p, "hdr_sub", "Week Header", 30, 50, 600, 26, size=9, color="#C7D7E7"),
           kpi_value(p, "hdr_team", "Project Team", 640, 52, 450, 26, size=8, color="#C7D7E7"),
           week_slicer(p, 1100, 8, 236, 44)]
    pick = rs.exclude_blank_name(dr.exclude_unmatched(dr.visual(p, "slicer_project", "slicer", 860, 8, 230, 44,
                                          {"Values": [column("dim_Project", "ProjectName")]},
                                          title="Project", tab=2, title_size=9,
                                          alt="Slicer. Picks the project this page shows.")))
    pick["visual"]["objects"] = {"data": [{"properties": {"mode": lit("Dropdown")}}],
                                 "selection": [{"properties": {"singleSelect": _ON, "strictSingleSelect": _ON}}],
                                 "header": [{"properties": {"show": _OFF}}]}
    out.append(boxed(pick, fill=CARD_BG, radius=6))
    out.append(button(p, "go_grade", "Grade detail >", 1226, 92, 110, 24, "Drillthrough", "dsgrade"))
    out.append(button(p, "back", "< Back", 1140, 92, 80, 24, "Back"))

    # KPI row (deck 1.34-2.0 in)
    xs, tw, y0, th = [37, 306, 575, 844, 1113], 246, 120, 104
    out += tile(p, "k_contract", "CURRENT CONTRACT", "Current Contract", "Contract Change Text", xs[0], y0, tw, th,
                accent=TEAL, precision=2, units=1000000, sub_color=SLATE)
    out += tile(p, "k_complete", "PROJECT COMPLETE", "Work Progress Shown", None, xs[1], y0, tw, th, accent=AMBER)
    out.append(text(p, "k_complete_s", "Outbuild work progress (duration-weighted)", xs[1] + 16, y0 + th - 28,
                    tw - 24, 22, size=8, color=SLATE, bold=False))
    out += tile(p, "k_sched", "SCHEDULE", "Schedule Headline", "Schedule Subline", xs[2], y0, tw, th, accent=AMBER,
                size=20, sub_color=SLATE)
    out += tile(p, "k_grade", "PROJECT SCORECARD", "Grade Text", "Grade Subline", xs[3], y0, tw, th, accent=AMBER,
                size=20, sub_color=SLATE)
    out += tile(p, "k_billed", "BILLED TO DATE", "Billed To Date (Gross)", "Billed Subline", xs[4], y0, tw, th,
                accent=GREEN, precision=2, units=1000000, sub_color=SLATE)

    # Row 2 (deck 2.61-4.95 in): schedule & delivery, project financials, delivery & financial health
    r2, h2 = 234, 290
    sx, sw = 37, 466
    out += [panel(p, "sd_bg", sx, r2, sw, h2),
            z(text(p, "sd_bar", " ", sx, r2, 6, h2, fill=TEAL), 1),
            text(p, "sd_h", "SCHEDULE & DELIVERY", sx + 20, r2 + 12, sw - 40, 26, size=12, color=NAVY),
            text(p, "sd_tl", "TRACKING FINISH (BASELINE)", sx + 20, r2 + 46, 240, 20, size=9),
            kpi_value(p, "sd_tv", "Tracking Finish Shown", sx + 270, r2 + 40, 180, 30, size=13, color=NAVY),
            text(p, "sd_fl", "FORECAST FINISH", sx + 20, r2 + 80, 240, 20, size=9),
            kpi_value(p, "sd_fv", "Forecast Finish Shown", sx + 270, r2 + 74, 180, 30, size=13, color=AMBER)]
    behind = table(p, "sd_behind", sx + 14, r2 + 112, sw - 28, h2 - 122,
                   [rs.shown_as(column("fct_ScheduleActivity", "ActivityName"), "Behind baseline - schedule pressure"),
                    rs.shown_as(measure("Days Behind Baseline"), "Days behind"),
                    rs.shown_as(column("fct_ScheduleActivity", "FinishDate"), "Forecast finish")],
                   alt="Table. Open Outbuild activities finishing later than their baseline, most days behind first.")
    dr.sort_desc(behind, measure("Days Behind Baseline"))
    rs.widen(behind, {"ActivityName": 4})
    out.append(flagged(behind, "Behind Schedule Flag"))

    fx, fw = 517, 390
    out += [panel(p, "pf_bg", fx, r2, fw, h2),
            z(text(p, "pf_bar", " ", fx, r2, 6, h2, fill=TEAL), 1),
            text(p, "pf_h", "PROJECT FINANCIALS", fx + 20, r2 + 12, fw - 40, 26, size=12, color=NAVY)]
    for i, (lbl, m) in enumerate([("ORIGINAL CONTRACT", "Original Contract"), ("CURRENT CONTRACT", "Current Contract"),
                                  ("PENDING CHANGE ORDERS", "Pending Change Orders"),
                                  ("BILLED TO DATE", "Billed To Date (Gross)"), ("PAID TO DATE", "Paid To Date"),
                                  ("REMAINING CONTRACT BALANCE", "Remaining Contract Balance")]):
        ry = r2 + 48 + i * 40
        out += [text(p, f"pf_{i}_l", lbl, fx + 20, ry + 6, 200, 20, size=9),
                kpi_value(p, f"pf_{i}_v", m, fx + 230, ry, 150, 30, size=12, color=NAVY, precision=0, units=1)]

    hx, hw = 921, 402
    out += [panel(p, "hf_bg", hx, r2, hw, h2),
            z(text(p, "hf_bar", " ", hx, r2, 6, h2, fill=TEAL), 1),
            text(p, "hf_h", "DELIVERY & FINANCIAL HEALTH", hx + 20, r2 + 12, hw - 40, 26, size=12, color=NAVY),
            text(p, "hf_bl", "BILLING PROGRESS", hx + 20, r2 + 48, 200, 20, size=9),
            kpi_value(p, "hf_bv", "Billed % Of Contract", hx + hw - 120, r2 + 40, 104, 30, size=14, color=GREEN,
                      precision=1),
            *bar(p, "hf_bbar", "Billed % Of Contract", hx + 20, r2 + 70, hw - 40, 26, GREEN),
            text(p, "hf_rl", "RISK BOUGHT OUT", hx + 20, r2 + 104, 200, 20, size=9),
            kpi_value(p, "hf_rv", "Subcontractor Coverage %", hx + hw - 120, r2 + 96, 104, 30, size=14, color=GREEN),
            text(p, "hf_cl", "COST TO COMPLETE", hx + 20, r2 + 140, 200, 20, size=9),
            kpi_value(p, "hf_cv", "Cost To Complete", hx + hw - 150, r2 + 132, 134, 30, size=14, color=NAVY,
                      precision=2, units=1000000),
            text(p, "hf_pl", "CASH POSITION", hx + 20, r2 + 176, 200, 20, size=9),
            kpi_value(p, "hf_pv", "Cash Position", hx + hw - 150, r2 + 168, 134, 30, size=14, color=NAVY,
                      precision=2, units=1000000),
            z(text(p, "hf_ex_bg", " ", hx + 20, r2 + 210, hw - 40, 74, fill="#FFF0CF", radius=8), 1000),
            kpi_value(p, "hf_ex", "Financial Exceptions", hx + 28, r2 + 214, hw - 56, 66, size=9, color="#986319")]

    # Row 3 (deck 6.2-10.0 in): top risks, near-term milestones + critical path, safety/quality/wins
    r3, h3 = 536, 252
    tx, tw3 = 37, 560
    out += [panel(p, "tr_bg", tx, r3, tw3, h3),
            z(text(p, "tr_bar", " ", tx, r3, 6, h3, fill=RED), 1),
            text(p, "tr_h", "TOP RISKS", tx + 20, r3 + 10, 260, 26, size=12, color=NAVY),
            text(p, "tr_note", "Scorecard measures below 80%, weakest first", tx + 300, r3 + 14, tw3 - 316, 20,
                 size=8, color=SLATE, bold=False, align="right")]
    risks = z(styled_table(dr.no_totals(dr.visual(p, "tr_tbl", "tableEx", tx + 14, r3 + 40, tw3 - 28, h3 - 50,
              {"Values": [rs.shown_as(measure("Risk Severity"), "Level"),
                          rs.shown_as(column("dim_DashMetric", "Metric"), "Risk"),
                          rs.shown_as(measure("Metric Reading"), "What the data shows")]},
              alt="Table. The scorecard measures scoring below 80 percent for this project: HIGH below 50 "
                  "percent, MED otherwise, and the reading behind each.")),
              pills={"Risk Severity": ("Risk Severity Colour", "Risk Severity Ink")}, header_fill="#F6F8FA"), 3000)
    risks["visual"]["objects"]["columnHeaders"][0]["properties"]["fontColor"] = _color(SLATE)
    risks["visual"]["query"]["sortDefinition"] = {"sort": [{"field": measure("Metric Score")["field"],
                                                            "direction": "Ascending"}], "isDefaultSort": True}
    rs.widen(risks, {"Metric Reading": 4, "Metric": 2})
    out.append(flagged(risks, "Is Top Risk"))

    mx, mw = 611, 352
    out += [panel(p, "ms_bg", mx, r3, mw, h3),
            z(text(p, "ms_bar", " ", mx, r3, 6, h3, fill=GREEN), 1),
            text(p, "ms_h", "NEAR-TERM MILESTONES  [NEXT 3 WEEKS]", mx + 20, r3 + 10, mw - 34, 24, size=11, color=NAVY)]
    near = table(p, "ms_near", mx + 14, r3 + 36, mw - 28, 94,
                 [rs.shown_as(column("fct_ScheduleActivity", "ActivityName"), "Activity"),
                  rs.shown_as(measure("Activity Next Step"), "Next")],
                 alt="Table. Outbuild activities starting or finishing in the next three weeks.")
    rs.widen(near, {"ActivityName": 3, "Activity Next Step": 2})
    out.append(flagged(near, "Near Term Flag"))
    out.append(text(p, "ms_cp", "CRITICAL PATH  [NEXT 3 WEEKS]", mx + 20, r3 + 138, mw - 34, 20, size=10, color=NAVY))
    crit = table(p, "ms_crit", mx + 14, r3 + 158, mw - 28, 86,
                 [rs.shown_as(column("fct_ScheduleActivity", "ActivityName"), "Activity"),
                  rs.shown_as(measure("Activity Next Step"), "Next")],
                 alt="Table. Critical-path Outbuild activities starting or finishing in the next three weeks.")
    rs.widen(crit, {"ActivityName": 3, "Activity Next Step": 2})
    out.append(flagged(crit, "Critical Near Term Flag"))

    qx, qw = 977, 346
    out += [panel(p, "sq_bg", qx, r3, qw, h3),
            z(text(p, "sq_bar", " ", qx, r3, 6, h3, fill=TEAL), 1),
            text(p, "sq_h", "SAFETY, QUALITY & WINS", qx + 20, r3 + 10, qw - 34, 24, size=11, color=NAVY)]
    for i, (lbl, cat) in enumerate([("SAFETY", "Safety"), ("QUALITY", "Quality")]):
        ly = r3 + 36 + i * 72
        t = table(p, f"sq_{cat.lower()}", qx + 14, ly, qw - 28, 66,
                  [rs.shown_as(column("fct_Inspection", "InspectionName"), f"{lbl} inspections this week"),
                   rs.shown_as(column("fct_Inspection", "InspectionDate"), "Date")],
                  alt=f"Table. {cat} inspections performed in the reporting week.")
        t.setdefault("filterConfig", {"filters": []})["filters"].append({
            "name": oid(t["name"], "category", cat), "type": "Categorical",
            "field": {"Column": {"Expression": {"SourceRef": {"Entity": "fct_Inspection"}}, "Property": "Category"}},
            "filter": {"Version": 2, "From": [{"Name": "i", "Entity": "fct_Inspection", "Type": 0}],
                       "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {
                           "Source": "i"}}, "Property": "Category"}}], "Values": [[{"Literal": {"Value": f"'{cat}'"}}]]}}}]},
            "howCreated": "User"})
        rs.widen(t, {"InspectionName": 4})
        out.append(flagged(t, "Inspection In Week Flag"))
    wins = table(p, "sq_wins", qx + 14, r3 + 180, qw - 28, 64,
                 [rs.shown_as(column("fct_ScheduleActivity", "ActivityName"), "Recent wins - completed this week")],
                 alt="Table. Outbuild activities completed in the reporting week.")
    out.append(flagged(wins, "Recent Win Flag"))

    out += [z(text(p, "focus_bg", " ", 37, 798, 1286, 40, fill="#E7EDF2", radius=8), 1000),
            kpi_value(p, "focus", "Executive Focus", 52, 802, 1260, 32, size=10, color=NAVY)]
    out += footer(p, "Financials as of the last refresh; inspections, meetings and wins for the reporting week  "
                     "•  Milestones and critical path: Outbuild current schedule  •  Top risks: Scorecard.xlsx "
                     "measures below 80% (HIGH below 50%)  •  Grade detail: the button, top right")
    return p, out


def page_grade() -> tuple[str, list[dict]]:
    """The 'Detail Scorecard' behind a grade: every measure, why it scored what it did."""
    p = "dsgrade"
    out = [z(text(p, "hdr_band", " ", 0, 0, W, 81, fill=NAVY), 0),
           z(text(p, "hdr_rule", " ", 0, 81, W, 3, fill=TEAL), 1),
           text(p, "title", "GRADE DETAIL  |", 36, 4, 240, 43, size=20, color="#FFFFFF"),
           kpi_value(p, "hdr_proj", "Project Title", 280, 8, 700, 38, size=20, color="#FFFFFF"),
           kpi_value(p, "hdr_sub", "Week Header", 30, 50, 700, 26, size=9, color="#C7D7E7"),
           button(p, "back", "< Back", 1240, 20, 84, 30, "Back")]
    cards = [("GRADE", "Grade", "Grade Colour"), ("SHARE MEASURED", "Grade Coverage %", None),
             ("SCHEDULE  50%", "Schedule Pillar", "Schedule Colour"), ("BUDGET  30%", "Budget Pillar", "Budget Colour"),
             ("SAFETY  15%", "Safety Pillar", "Safety Colour"), ("QUALITY  5%", "Quality Pillar", "Quality Colour")]
    for i, (lbl, m, _) in enumerate(cards):
        x = 36 + i * 216
        out += [panel(p, f"g{i}_bg", x, 98, 204, 80, radius=8),
                z(text(p, f"g{i}_bar", " ", x, 98, 6, 80, fill=TEAL if i < 2 else NAVY), 1),
                text(p, f"g{i}_l", lbl, x + 16, 104, 180, 20, size=9),
                kpi_value(p, f"g{i}_v", m, x + 10, 126, 186, 46, size=22, color=NAVY, precision=0)]
    out += [panel(p, "t_bg", 36, 192, 1288, 416),
            text(p, "t_h", "HOW THE GRADE IS BUILT  -  Scorecard.xlsx, in pillar order", 56, 200, 900, 26, size=12,
                 color=NAVY)]
    detail = z(styled_table(dr.no_totals(dr.visual(p, "detail", "tableEx", 48, 230, 1264, 370,
               {"Values": [rs.shown_as(column("dim_DashMetric", "Pillar"), "Pillar"),
                           rs.shown_as(column("dim_DashMetric", "Metric"), "Measure"),
                           rs.shown_as(column("dim_DashMetric", "Standard"), "Standard"),
                           rs.shown_as(column("dim_DashMetric", "Period"), "Period"),
                           rs.shown_as(measure("Metric Reading"), "Reading"),
                           rs.shown_as(measure("Metric Score"), "Score"),
                           rs.shown_as(measure("Metric State"), "Band, or why not scored"),
                           rs.shown_as(measure("Metric Weight In Grade"), "Share of grade")]},
               alt="Table. Every Scorecard.xlsx measure for this project: its standard and period, what the data "
                   "shows, the score, the band it fell in or why it is not scored, and the share of the grade it "
                   "carries.")), pills={"Metric Score": ("Metric Colour", "Metric Ink")}), 3000)
    detail["visual"]["query"]["sortDefinition"] = {"sort": [
        {"field": column("dim_DashMetric", "PillarKey")["field"], "direction": "Ascending"},
        {"field": column("dim_DashMetric", "SortOrder")["field"], "direction": "Ascending"}], "isDefaultSort": True}
    rs.widen(detail, {"Standard": 5, "Metric Reading": 4, "Metric State": 3, "Metric": 2})
    out.append(detail)

    out += [panel(p, "c_bg", 36, 620, 520, 220),
            text(p, "c_h", "CASH POSITION, STEP BY STEP", 56, 628, 480, 24, size=11, color=NAVY)]
    steps = [("Billings to date", "Cash - Billings To Date"), ("- Retainage receivable", "Cash - Retainage Receivable"),
             ("- Unpaid receivables", "Cash - Unpaid Receivables"), ("= Collected", "Cash Collected"),
             ("Costs incurred", "Cash - Costs Incurred"), ("- Unpaid payables", "Cash - Unpaid Payables"),
             ("- Retainage payable", "Cash - Retainage Payable"), ("= Paid out", "Cash Paid Out")]
    for i, (lbl, m) in enumerate(steps):
        col, row = divmod(i, 4)
        x, y = 56 + col * 250, 656 + row * 38
        bold = lbl.startswith("=")
        out += [text(p, f"c{i}_l", lbl, x, y + 6, 120, 20, size=8.5 if not bold else 9, color=SLATE if not bold else NAVY,
                     bold=bold),
                kpi_value(p, f"c{i}_v", m, x + 122, y, 120, 30, size=11, color=NAVY, precision=0, units=1)]
    out += [text(p, "c_pos", "CASH POSITION", 56, 812, 140, 20, size=9, color=NAVY),
            kpi_value(p, "c_pos_v", "Cash Position", 200, 804, 150, 32, size=13, color=NAVY, precision=0, units=1),
            kpi_value(p, "c_ratio", "Cash Collected / Paid", 360, 804, 180, 32, size=13, color=TEAL)]

    out += [panel(p, "m_bg", 570, 620, 754, 220),
            text(p, "m_h", "OAC & TRADE PARTNER MEETINGS  -  THE FOUR WEEKS SCORED", 590, 628, 714, 24, size=11,
                 color=NAVY)]
    meets = table(p, "meetings", 582, 654, 730, 180,
                  [rs.shown_as(column("fct_Meeting", "MeetingDate"), "Date"),
                   rs.shown_as(column("fct_Meeting", "MeetingType"), "Type"),
                   rs.shown_as(column("fct_Meeting", "SeriesTitle"), "Series"),
                   rs.shown_as(column("fct_Meeting", "AgendaStatus"), "Agenda (24h before)"),
                   rs.shown_as(column("fct_Meeting", "MinutesStatus"), "Minutes (24h after)"),
                   rs.shown_as(measure("Meeting Met Standard"), "Counted")],
                  alt="Table. The OAC and trade partner meetings in the four weeks the meeting measures score, with "
                      "whether the agenda and minutes went out on time in Procore.")
    dr.sort_desc(meets, column("fct_Meeting", "MeetingDate"))
    rs.widen(meets, {"SeriesTitle": 3, "AgendaStatus": 2, "MinutesStatus": 2})
    out.append(flagged(meets, "Meeting In Window Flag"))
    out += footer(p, "Scores 0-100%: Scorecard.xlsx bands (dim_DashBand)  •  Each pillar = equal-weighted average of "
                     "its measured measures  •  Grade = pillars weighted 50 / 30 / 15 / 5 over the weight measured  "
                     "•  Agenda 'not verifiable': Procore keeps only the last send once minutes go out")
    return p, out


PAGES = [
    ("Executive Dashboard", page_executive, False),
    ("Project Portfolio | Status", page_portfolio, False),
    ("Project Overview", page_project, False),
    ("Grade Detail", page_grade, True),
]
DRILLTHROUGH = {"dsproject": ("dim_Project", "ProjectName"), "dsgrade": ("dim_Project", "ProjectName")}


def build(model_id: str) -> dict[str, str]:
    """deploy_report.build with this report's pages, then the deck's page size and colour."""
    dr.REPORT_NAME, dr.REPORT_DIR, dr.PAGES, dr.DRILLTHROUGH = REPORT_NAME, REPORT_DIR, PAGES, DRILLTHROUGH
    dr.chrome = lambda page, slicers=True: []  # every page draws its own header and footer
    files = dr.build(model_id)
    for rel in [r for r in files if r.endswith("/page.json") and "/pages/" in r]:
        page = json.loads(files[rel])
        page.update(width=W, height=H, displayOption="FitToWidth")
        page["objects"] = {"background": [{"properties": {"color": _color(PAGE_BG), "transparency": _num(0)}}],
                           "outspace": [{"properties": {"color": _color(PAGE_BG), "transparency": _num(0)}}]}
        # A drill-through page that is also opened directly keeps its own project picker.
        if page["name"] == "dsproject":
            page.pop("visibility", None)
        files[rel] = json.dumps(page, indent=2)
        (REPORT_DIR / rel).write_text(files[rel], encoding="utf-8", newline="")
    files["definition/bookmarks/bookmarks.json"] = json.dumps(
        {"$schema": f"{dr.SCHEMA}/bookmarksMetadata/1.0.0/schema.json", "items": []}, indent=2)
    (REPORT_DIR / "definition/bookmarks/bookmarks.json").write_text(files["definition/bookmarks/bookmarks.json"],
                                                                     encoding="utf-8", newline="")
    return files


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    tok = dr.dp.token()
    model = dr.ds.find_item(tok, dr.MODEL_NAME, "SemanticModel")
    if not model:
        print(f"ERROR: semantic model {dr.MODEL_NAME!r} not found")
        return 1
    files = build(model["id"])
    print(f"generated {len(files)} file(s): {len(PAGES)} pages, "
          f"{sum(f.endswith('visual.json') for f in files)} visuals -> {REPORT_DIR.name}")
    if not args.apply:
        print("\nDRY RUN - written to disk only. Re-run with --apply.")
        return 0
    definition = {"parts": [{"path": rel, "payload": base64.b64encode(c.encode()).decode(),
                             "payloadType": "InlineBase64"} for rel, c in files.items() if rel != ".platform"]}
    existing = dr.ds.find_item(tok, REPORT_NAME, "Report")
    if existing:
        status, _, headers = dr.dp.call("POST", f"/workspaces/{dr.dp.WORKSPACE_ID}/items/{existing['id']}/updateDefinition",
                                        tok, {"definition": definition})
    else:
        status, _, headers = dr.dp.call("POST", f"/workspaces/{dr.dp.WORKSPACE_ID}/items", tok,
                                        {"displayName": REPORT_NAME, "type": "Report",
                                         "folderId": dr.dp.FOLDER_ID, "definition": definition})
    if status == 202:
        dr.dp.wait_for_operation(headers, tok)
    item = dr.ds.find_item(tok, REPORT_NAME, "Report")
    print(f"  {'updated' if existing else 'created'} {REPORT_NAME}: {item['id']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except dr.dp.FabricError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
