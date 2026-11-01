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
AMBER_TEXT = dash.AMBER_TEXT
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
              precision: int | None = None, units: int | None = None, align: str = "left",
              alt: str | None = None) -> dict:
    """A bare value: no title, no category label, deck navy, on the panel behind it."""
    v = dr.visual(p, key, "card", x, y, w, h, {"Values": [measure(name)]},
                  alt=alt or f"Card. {name}.")
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
         pending: str | None = None, link: tuple[str, str] | None = None) -> list[dict]:
    """The deck's KPI tile: white card, coloured bar on the left, caps label, big value,
    one line under it. `pending` replaces the value with what the tile is waiting for;
    `link` (page, what) adds the "Data >" button that opens the rows behind the value."""
    out = [panel(p, f"{key}_bg", x, y, w, h, radius=8),
           z(text(p, f"{key}_bar", " ", x, y, 6, h, fill=accent), 1),
           text(p, f"{key}_lbl", label, x + 16, y + 10, w - 24 - (52 if link else 0), 20, size=9)]
    if link and len(link) > 2:
        # One project's page: drill through, so the target opens on the same project.
        out.append(button(p, f"{key}_data", "Data >", x + w - 54, y + 8, 46, 20, "Drillthrough", link[0]))
    elif link:
        out.append(nav(p, f"{key}_data", "Data >", x + w - 54, y + 8, 46, 20, link[0], link[1]))
    if pending:
        out.append(text(p, f"{key}_pending", pending, x + 16, y + 36, w - 24, h - 44, size=9,
                        color=SLATE, bold=False))
        return out
    # Alt text names the tile, not just the measure (audit): "Card. Revenue Ytd: the value (...)."
    name = label.title()
    out.append(kpi_value(p, f"{key}_val", value, x + 10, y + 32, w - 18, 40, size=size,
                         precision=precision, units=units, alt=f"Card. {name}: the value ({value})."))
    if sub:
        out.append(kpi_value(p, f"{key}_sub", sub, x + 10, y + h - 30, w - 18, 26, size=8, color=sub_color,
                             alt=f"Card. {name}: the line under the value ({sub})."))
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
    # Track #D3DCE5, not PALE: PALE is 1.18:1 on the white card, so the 100% end vanished (audit).
    return [z(text(p, f"{key}_track", " ", x, y + 3, w, h - 6, fill="#D3DCE5", radius=3), 1000), z(v, 3000)]


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


def nav(p: str, key: str, label: str, x, y, w, h, target: str, what: str) -> dict:
    """A link to a detail page (Oct 30 call: every number opens the rows it is made from)."""
    b = button(p, key, label, x, y, w, h, "Back")
    c = b["visual"]["visualContainerObjects"]
    c["visualLink"] = [{"properties": {"show": _ON, "type": rs._text("PageNavigation"),
                                       "navigationSection": rs._text(target)}}]
    c["general"] = [{"properties": {"altText": lit(f"Button. Opens {what}.")}}]
    b["visual"]["objects"]["text"][1]["properties"]["fontSize"] = _num(8)
    return b


def where(v: dict, table: str, col: str, value: str) -> dict:
    """A visual filter on a column: value is a DAX literal ('Owner', true)."""
    v.setdefault("filterConfig", {"filters": []})["filters"].append({
        "name": oid(v["name"], "where", table, col), "type": "Categorical",
        "field": {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": col}},
        "filter": {"Version": 2, "From": [{"Name": "t", "Entity": table, "Type": 0}],
                   "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {
                       "Source": "t"}}, "Property": col}}], "Values": [[{"Literal": {"Value": value}}]]}}}]},
        "howCreated": "User"})
    return v


def proof(p: str, key: str, x, y, w, h, fields: list, alt: str, title: str | None = None,
          pills: dict | None = None, sort: tuple[dict, str] | None = None, wide: dict | None = None,
          flag: str | None = None, totals: bool = True) -> dict:
    """The rows behind a number, WITH the totals row - the total is what ties to the tile.
    Export data on the visual's menu gives the same rows to Excel."""
    v = dr.visual(p, key, "tableEx", x, y, w, h, {"Values": fields}, title=title, alt=alt, title_size=10)
    v = z(styled_table(v, pills), 3000)
    v["visual"]["objects"]["total"] = [{"properties": {"totals": _ON if totals else _OFF, "fontColor": _color(NAVY),
                                                       "backColor": _color("#E7EDF2")}}]
    if sort:
        v["visual"]["query"]["sortDefinition"] = {"sort": [{"field": sort[0]["field"], "direction": sort[1]}],
                                                  "isDefaultSort": True}
    # Measure columns hold money and totals: twice a label column, or a total wraps (seen live).
    weights = {f["field"]["Measure"]["Property"]: 2 for f in fields if "Measure" in f["field"]}
    rs.widen(v, {**weights, **(wide or {})})
    return flagged(v, flag) if flag else v


def detail_header(p: str, title: str, right: str = "Detail Header", project_picker: bool = True) -> list[dict]:
    """Navy band as the deck pages, with Back, a way home, the week and (optionally) projects."""
    out = [z(text(p, "hdr_band", " ", 0, 0, W, 81, fill=NAVY), 0),
           z(text(p, "hdr_rule", " ", 0, 81, W, 3, fill=TEAL), 1),
           text(p, "title", title, 36, 4, 800, 43, size=18, color="#FFFFFF"),
           kpi_value(p, "hdr_sub", "Week Header", 30, 50, 560, 26, size=9, color="#C7D7E7"),
           kpi_value(p, "hdr_right", right, 600, 52, 440, 26, size=8, color="#C7D7E7"),
           week_slicer(p, 1100, 8, 236, 44),
           button(p, "back", "< Back", 1150, 56, 84, 22, "Back"),
           nav(p, "home", "Executive >", 1240, 56, 96, 22, "dsexec", "the Executive Dashboard")]
    if project_picker:
        pick = rs.exclude_blank_name(dr.exclude_unmatched(dr.visual(
            p, "slicer_project", "slicer", 860, 8, 230, 44, {"Values": [column("dim_Project", "ProjectName")]},
            title="Projects (all active if none picked)", tab=2, title_size=8,
            alt="Slicer. Narrows the tables on this page to the projects picked; none picked shows every active project.")))
        pick["visual"]["objects"] = {"data": [{"properties": {"mode": lit("Dropdown")}}],
                                     "selection": [{"properties": {"singleSelect": _OFF}}],
                                     "header": [{"properties": {"show": _OFF}}]}
        out.append(boxed(pick, fill=CARD_BG, radius=6))
    return out


def strip(p: str, cards: list[tuple[str, str, str | None]], y: int = 96, h: int = 84) -> list[dict]:
    """The dashboard's own figure(s) at the top of a detail page: the number the rows below add to."""
    n = len(cards)
    gap = 12
    w = (W - 72 - gap * (n - 1)) // n
    out = []
    for i, (label_, m, note) in enumerate(cards):
        x = 36 + i * (w + gap)
        out += [panel(p, f"s{i}_bg", x, y, w, h, radius=8),
                z(text(p, f"s{i}_bar", " ", x, y, 6, h, fill=TEAL), 1),
                text(p, f"s{i}_l", label_, x + 16, y + 8, w - 24, 20, size=8.5),
                kpi_value(p, f"s{i}_v", m, x + 10, y + 29, w - 18, 28, size=15, units=1,
                          alt=f"Card. {label_.title()}: the value ({m}).")]
        if note:
            out.append(text(p, f"s{i}_n", note, x + 16, y + h - 22, w - 24, 18, size=7, color=SLATE, bold=False))
    return out


def how(p: str, words: str, y: int = 188, h: int = 40) -> list[dict]:
    """How the number is calculated, in words, on a pale band."""
    return [z(text(p, "how_bg", " ", 36, y, W - 72, h, fill="#E7EDF2", radius=8), 1000),
            text(p, "how", words, 48, y + 4, W - 96, h - 8, size=8, color=NAVY, bold=False)]


m_ = measure
c_ = column
sa = rs.shown_as


def invoice_fields(age: bool = False) -> list:
    out = [sa(c_("fct_Invoice", "SageJobNumber"), "Job"), sa(c_("fct_Invoice", "SageJobName"), "Sage job"),
           sa(c_("dim_Project", "ProjectName"), "Procore project"), sa(c_("fct_Invoice", "InvoiceID"), "Sage rec"),
           sa(c_("fct_Invoice", "InvoiceNumber"), "Invoice"), sa(c_("fct_Invoice", "SentDate"), "Date"),
           sa(c_("fct_Invoice", "SageStatus"), "Sage status")]
    if age:
        out += [sa(m_("Invoice Age Days"), "Days"), sa(m_("Invoice Age Band"), "Age")]
    return out + [sa(m_("Invoice Amount"), "Counted"), sa(m_("Invoice Voided"), "Voided"),
                  sa(m_("Invoice Paid"), "Paid"), sa(m_("Invoice Balance"), "Owed"),
                  sa(m_("Invoice Treatment"), "Treatment")]


def page_revenue() -> tuple[str, list[dict]]:
    p = "dsrevenue"
    out = detail_header(p, "DETAIL  |  REVENUE", project_picker=False)
    out += strip(p, [("REVENUE YTD (ON THE DASHBOARD)", "Revenue YTD", "Jan 1 to the end of the week picked"),
                     ("CLOSED MONTHS ONLY", "Revenue YTD Closed", "To the last month closed in Sage"),
                     ("VOIDED IN SAGE - LEFT OUT", "Revenue YTD Voided", "Status 5 invoices, counted at $0"),
                     ("BOOKS CLOSED THROUGH", "Books Closed Through", "Update dashboard_setting when a month closes")])
    out += how(p, "Revenue YTD = the total of every Sage AR invoice dated from Jan 1 to the end of the week picked, on every "
                  "Sage job - matched to a Procore project or not (job with no project = 'Counted - Sage job with no Procore "
                  "project'). Voided invoices are listed and count $0. These are BILLINGS: revenue after the WIP (over / "
                  "under billing) adjustment needs the Sage general ledger, not yet ingested.")
    out.append(proof(p, "invoices", 36, 236, W - 72, 328, invoice_fields(),
                     "Table. Every Sage AR invoice dated this year to the end of the week picked, with what counted, what "
                     "was voided, paid and still owed. The total of Counted is Revenue YTD.",
                     title="SAGE AR INVOICES IN REVENUE YTD  -  the Counted total is the tile",
                     sort=(c_("fct_Invoice", "SentDate"), "Descending"),
                     wide={"SageJobName": 3, "ProjectName": 3, "Invoice Treatment": 3, "InvoiceNumber": 2},
                     flag="Invoice In YTD Flag"))
    months = proof(p, "months", 36, 576, 520, 266,
                   [sa(c_("dim_Date", "MonthYear"), "Month"), sa(m_("Invoices In Month"), "Invoices"),
                    sa(m_("Revenue In Month"), "Invoiced (counted)"), sa(m_("Voided In Month"), "Voided"),
                    sa(m_("Month Close State"), "Sage close")],
                   "Table. Revenue invoiced in Sage by month this year, voids, and whether the month is closed.",
                   title="BY MONTH  -  what was invoiced in each month", wide={"Month Close State": 2})
    out.append(months)
    out.append(proof(p, "jobs", 568, 576, 756, 266,
                     [sa(c_("fct_Invoice", "SageJobNumber"), "Job"), sa(c_("fct_Invoice", "SageJobName"), "Sage job"),
                      sa(m_("Revenue YTD"), "Revenue YTD"),
                      sa(m_("Revenue YTD Closed"), "Closed months"), sa(m_("Revenue YTD Voided"), "Voided")],
                     "Table. Revenue YTD by Sage job, with the closed-months figure and voids.",
                     title="BY SAGE JOB  -  including jobs with no Procore project",
                     sort=(m_("Revenue YTD"), "Descending"), wide={"SageJobName": 4}))
    return p, out


def page_ar() -> tuple[str, list[dict]]:
    p = "dsar"
    out = detail_header(p, "DETAIL  |  RECEIVABLES (AR)", project_picker=False)
    out += strip(p, [("OPEN AR - EVERY JOB", "AR Outstanding", "Sage balance still owed, voids at $0"),
                     ("AR > 60 DAYS (ON THE DASHBOARD)", "AR Over 60 Days", "Invoice dated over 60 days ago"),
                     ("ON NO PROCORE PROJECT", "Unattributed Open AR", "Sage jobs not in the crosswalk"),
                     ("VOIDED BALANCES LEFT OUT", "Voided AR Left Out", "Sage keeps a void's full balance")])
    out += how(p, "Open AR = the Sage balance on every AR invoice not yet paid in full. Ageing counts days from the invoice date "
                  "to the data date; AR > 60 DAYS adds the 61-90 and over-90 rows. A voided invoice keeps its whole amount as a "
                  "balance in Sage - those are left out here (they were in the AR the Oct 30 call questioned). Retainage held "
                  "is not in Sage AR; it sits on the Procore pay app.")
    out.append(proof(p, "open", 36, 236, W - 72, 380, invoice_fields(age=True),
                     "Table. Every Sage AR invoice with a balance still owed, oldest first, with its age band. The Owed "
                     "total is open AR.",
                     title="OPEN SAGE AR INVOICES  -  oldest first",
                     sort=(m_("Invoice Age Days"), "Descending"),
                     wide={"SageJobName": 3, "ProjectName": 3, "Invoice Treatment": 3}, flag="Open AR Flag"))
    out.append(proof(p, "jobs", 36, 628, W - 72, 214,
                     [sa(c_("fct_Invoice", "SageJobNumber"), "Job"), sa(c_("fct_Invoice", "SageJobName"), "Sage job"),
                      sa(c_("dim_Project", "ProjectName"), "Procore project"), sa(m_("Job Open AR"), "Open AR"),
                      sa(m_("AR Over 60 Days"), "Over 60 days")],
                     "Table. Open AR and AR over 60 days by Sage job.", title="BY SAGE JOB",
                     sort=(m_("Job Open AR"), "Descending"), wide={"SageJobName": 3, "ProjectName": 3},
                     flag="Open AR Job Flag"))
    return p, out


def page_margin() -> tuple[str, list[dict]]:
    p = "dsmargin"
    out = detail_header(p, "DETAIL  |  MARGIN, BUDGET & BUYOUT")
    out += strip(p, [("GROSS MARGIN (ON THE DASHBOARD)", "Portfolio Gross Margin %", "Active projects with a forecast"),
                     ("TARGET", "Gross Margin Target", "dashboard_setting"),
                     ("ON BUDGET", "On Budget Text", "Forecast cost within budget"),
                     ("SUBCONTRACTOR COVERAGE", "Portfolio Subcontractor Coverage", "Committed / buyable budget, $-weighted")])
    out += how(p, "Margin = (Procore revised budget - forecast final cost) / revised budget. Affect's budgets carry the CM fee "
                  "as a line (division 50), so the fee is margin, not cost, and is left out of cost. The portfolio figure "
                  "adds every active project's budget and cost first. Coverage = committed (subcontracts and POs) over the "
                  "budget of divisions 01-44, dollar for dollar - GCs, insurance, contingency, tax and fee are not bought out.")
    out.append(proof(p, "projects", 36, 236, W - 72, 250,
                     [sa(c_("dim_Project", "ProjectName"), "Project"), sa(m_("Projected Revenue"), "Revised budget"),
                      sa(m_("Projected Fee"), "CM fee (div 50)"), sa(m_("Projected Cost"), "Forecast cost ex fee"),
                      sa(m_("Projected Margin $"), "Margin $"), sa(m_("Projected Gross Margin %"), "Margin %"),
                      sa(m_("Margin vs Target"), "vs target"), sa(m_("Forecast Variance"), "Budget less forecast"),
                      sa(m_("On Budget Row"), "On budget"), sa(m_("Subcontract Budget"), "Buyable budget"),
                      sa(m_("Subcontract Committed"), "Committed"), sa(m_("Subcontractor Coverage %"), "Coverage"),
                      sa(m_("In Margin Tile"), "In the tile")],
                     "Table. Every active project's budget, forecast cost, CM fee, margin, budget variance and buyout "
                     "coverage. The totals are the portfolio figures.",
                     title="BY PROJECT  -  active projects", wide={"ProjectName": 3, "On Budget Row": 2, "In Margin Tile": 2},
                     flag="Active Flag"))
    out.append(proof(p, "lines", 36, 498, W - 72, 344,
                     [sa(c_("dim_Project", "ProjectName"), "Project"), sa(c_("dim_CostCode", "CostCode"), "Cost code"),
                      sa(c_("dim_CostCode", "Description"), "Description"),
                      sa(c_("dim_CostCodeCrosswalk", "NewDivisionName"), "Division (new master)"),
                      sa(m_("Line Budget"), "Budget"), sa(m_("Line Forecast"), "Forecast"),
                      sa(m_("Line Committed"), "Committed"), sa(m_("Line Coverage %"), "Coverage"),
                      sa(m_("Line Spent"), "Spent"), sa(m_("Line Treatment"), "How it counts")],
                     "Table. Procore budget lines by cost code for the active projects: budget, forecast, committed, "
                     "coverage, spent, and how each line counts in margin and coverage. Pick a project above to narrow it.",
                     title="BUDGET LINES  -  pick a project above to narrow",
                     wide={"ProjectName": 2, "Description": 3, "NewDivisionName": 2, "Line Treatment": 3},
                     flag="Active Flag"))
    return p, out


def prime_fields(project: bool = True) -> list:
    return ([sa(c_("dim_Project", "ProjectName"), "Project")] if project else []) + [
        sa(c_("fct_Billing", "ContractName"), "Prime contract"), sa(c_("fct_Billing", "PeriodNumber"), "Pay app"),
        sa(c_("fct_Billing", "BillingDate"), "Date"), sa(m_("Pay App Original Sum"), "Original"),
        sa(m_("Pay App CO Change"), "Change orders"), sa(m_("Pay App Contract Sum"), "Contract to date"),
        sa(m_("Pay App Completed"), "Billed (gross)"), sa(m_("Pay App Retainage"), "Retainage"),
        sa(m_("Pay App Balance To Finish"), "Left to bill")]


def latest_owner(v: dict) -> dict:
    return where(where(v, "fct_Billing", "BillingType", "'Owner'"), "fct_Billing", "IsLatestPeriod", "true")


def page_contracts() -> tuple[str, list[dict]]:
    p = "dscontract"
    out = detail_header(p, "DETAIL  |  CONTRACTS, BACKLOG & CHANGE ORDERS")
    out += strip(p, [("ACTIVE PROJECTS", "Active Projects", "The Nov 19 rollout list"),
                     ("CURRENT CONTRACT", "Active Contract Value", "Active projects"),
                     ("BACKLOG (ON THE DASHBOARD)", "Backlog", "Contract not yet billed"),
                     ("CHANGE ORDERS APPROVED", "Change Orders Approved %", "Approved / approved + pending"),
                     ("PENDING CHANGE ORDERS", "Active Pending COs", "Procore prime COs not approved")])
    out += how(p, "Current contract = the latest month's Procore prime contract value, every prime contract on the project added "
                  "together (one Procore project can hold several - landlord / tenant splits). Billed to date = the latest "
                  "Procore owner pay app's completed and stored (gross of retainage), or Sage invoices where there is no pay "
                  "app. Backlog = current contract - billed to date. Change orders are Procore prime change orders.")
    out.append(proof(p, "projects", 36, 236, W - 72, 200,
                     [sa(c_("dim_Project", "ProjectName"), "Project"), sa(m_("Status Reason"), "Why active"),
                      sa(m_("Phase Label"), "Phase"), sa(m_("Phase Source"), "Phase read from"),
                      sa(m_("Original Contract"), "Original"), sa(m_("CO Approved Amount"), "Approved COs"),
                      sa(m_("CO Pending Amount"), "Pending COs"), sa(m_("Position Contract"), "Current contract"),
                      sa(m_("Billed To Date (Gross)"), "Billed to date"), sa(m_("Billing Source"), "Billed from"),
                      sa(m_("Billed % Of Contract"), "Billed %"), sa(m_("Project Backlog"), "Backlog")],
                     "Table. Every active project: why it is active, its phase and where the phase is read from, original "
                     "and current contract, change orders, billed to date and its source, and backlog. The Backlog total "
                     "is the tile.",
                     title="BY PROJECT  -  active projects",
                     wide={"ProjectName": 3, "Status Reason": 2, "Phase Source": 4, "Billing Source": 3},
                     flag="Active Flag"))
    out.append(latest_owner(proof(p, "prime", 36, 448, 700, 394, prime_fields(),
                                  "Table. Each Procore prime contract on the active projects, from its latest owner pay app: "
                                  "original sum, change orders, contract to date, billed, retainage and left to bill.",
                                  title="PRIME CONTRACTS  -  latest owner pay app on each", wide={"ProjectName": 2, "ContractName": 3},
                                  flag="Active Flag")))
    out.append(proof(p, "cos", 748, 448, 576, 394,
                     [sa(c_("dim_Project", "ProjectName"), "Project"), sa(c_("fct_ChangeOrder", "ChangeOrderNumber"), "CO"),
                      sa(c_("fct_ChangeOrder", "ChangeOrderTitle"), "Title"), sa(c_("fct_ChangeOrder", "StatusDisplay"), "Status"),
                      sa(c_("fct_ChangeOrder", "CreatedDate"), "Created"), sa(m_("CO Approved Amount"), "Approved"),
                      sa(m_("CO Pending Amount"), "Pending")],
                     "Table. Every Procore prime change order on the active projects, approved or pending.",
                     title="PRIME CHANGE ORDERS", wide={"ProjectName": 2, "ChangeOrderTitle": 3},
                     sort=(c_("fct_ChangeOrder", "CreatedDate"), "Descending"), flag="Active Flag"))
    return p, out


def page_cash() -> tuple[str, list[dict]]:
    p = "dscash"
    out = detail_header(p, "DETAIL  |  CASH POSITION")
    out += strip(p, [("CASH POSITION (ON THE DASHBOARD)", "Portfolio Cash Position", "Active projects"),
                     ("COLLECTED VS PAID", "Cash Subline", None),
                     ("UNPAID PAYABLES", "Active Unpaid Payables", "Sage AP still to pay, voids excluded")])
    out += how(p, "Cash position (Chris, Oct 22) = billings to date - retainage receivable - unpaid receivables, less (costs "
                  "incurred - unpaid payables - retainage payable). Billings: Procore owner pay apps (gross). Retainage: Procore "
                  "pay apps and requisitions. Unpaid AR and AP: Sage, voids excluded. Costs incurred: Procore job-to-date cost. A "
                  "project with no Procore budget has no cash position and is left out (Data Health: budget forecast).")
    out.append(proof(p, "projects", 36, 236, W - 72, 270,
                     [sa(c_("dim_Project", "ProjectName"), "Project"), sa(m_("Cash - Billings To Date"), "Billings to date"),
                      sa(m_("Cash - Retainage Receivable"), "- Retainage rec."), sa(m_("Cash - Unpaid Receivables"), "- Unpaid AR"),
                      sa(m_("Cash Collected"), "= Collected"), sa(m_("Cash - Costs Incurred"), "Costs incurred"),
                      sa(m_("Cash - Unpaid Payables"), "- Unpaid AP"), sa(m_("Cash - Retainage Payable"), "- Sub retainage"),
                      sa(m_("Cash Paid Out"), "= Paid out"), sa(m_("Cash Position"), "Cash position"),
                      sa(m_("Cash Collected / Paid"), "Collected / paid")],
                     "Table. Chris's cash position formula for every active project, step by step. The Cash position total "
                     "is the tile.", title="BY PROJECT  -  every step of the formula (projects with both halves)",
                     wide={"ProjectName": 3}, flag="Cash Row Flag"))
    out.append(proof(p, "ap", 36, 518, W - 72, 324,
                     [sa(c_("dim_Project", "ProjectName"), "Project"), sa(c_("dim_Vendor", "VendorName"), "Vendor"),
                      sa(c_("fct_ApInvoice", "InvoiceID"), "Sage rec"),
                      sa(c_("fct_ApInvoice", "InvoiceNumber"), "AP invoice"), sa(c_("fct_ApInvoice", "InvoiceDate"), "Date"),
                      sa(m_("AP Age Days"), "Days"), sa(m_("AP Line Amount"), "Job cost"), sa(m_("AP Line Open"), "Still to pay")],
                     "Table. Sage AP job-cost invoices still unpaid on the active projects: vendor, date, age and amount "
                     "still to pay. The total is Unpaid payables.",
                     title="UNPAID PAYABLES  -  Sage AP, oldest first", sort=(m_("AP Age Days"), "Descending"),
                     wide={"ProjectName": 2, "VendorName": 3}, flag="Open AP Active Flag"))
    return p, out


def page_schedule_detail() -> tuple[str, list[dict]]:
    p = "dsschedule"
    out = detail_header(p, "DETAIL  |  SCHEDULE")
    out += strip(p, [("ON SCHEDULE (ON THE DASHBOARD)", "On Schedule Text", "Forecast finish on or before baseline"),
                     ("PROJECTS AT RISK", "Projects At Risk (Grade)", "Grade 45 and below"),
                     ("NEEDING ATTENTION", "Projects Needing Attention", "Below the monitor cut-off")])
    out += how(p, "On schedule = Outbuild's current critical-path finish on or before the baseline (tracking) finish. The SCHEDULE "
                  "pillar on the Portfolio page is NOT only this: it averages seven measures - OAC and trade partner meetings, "
                  "the look-ahead, the monthly update, completion variance, submittals and RFIs - so a job 8 days ahead can "
                  "still read 54% if minutes or the look-ahead are missing. The second table shows each part.")
    out.append(proof(p, "finish", 36, 236, W - 72, 250,
                     [sa(c_("dim_Project", "ProjectName"), "Project"), sa(m_("Phase Label"), "Phase"),
                      sa(m_("Phase Source"), "Phase read from"), sa(m_("Tracking Finish"), "Baseline finish"),
                      sa(m_("Forecast Finish"), "Forecast finish"), sa(m_("Completion Variance Days"), "Days vs baseline"),
                      sa(m_("Completion Variance %"), "% of duration"), sa(m_("On Schedule Row"), "On schedule")],
                     "Table. Every active project's baseline and forecast finish from Outbuild, days early or late, and "
                     "whether it counts as on schedule.", title="FINISH VS BASELINE  -  Outbuild current schedule",
                     wide={"ProjectName": 3, "Phase Source": 4, "On Schedule Row": 2}, flag="Active Flag", totals=False))
    out.append(proof(p, "parts", 36, 498, W - 72, 344,
                     [sa(c_("dim_Project", "ProjectName"), "Project"), sa(m_("Schedule Pillar"), "Schedule pillar"),
                      *[sa(m_(dash.score_name(n)), n) for k, n, _ in dash.METRICS if 200 < k < 300]],
                     "Table. For every active project, the schedule pillar and the score of each of the seven measures it "
                     "averages. Grade Detail shows each reading.",
                     title="WHAT MAKES THE SCHEDULE PILLAR  -  equal-weighted average of the measures scored",
                     pills={"Schedule Pillar": ("Schedule Colour", "Schedule Ink")}, wide={"ProjectName": 3},
                     flag="Active Flag"))
    return p, out


def page_safety_detail() -> tuple[str, list[dict]]:
    p = "dssafety"
    out = detail_header(p, "DETAIL  |  SAFETY & QUALITY")
    out += strip(p, [("SAFETY SCORE (ON THE DASHBOARD)", "Portfolio Safety Score", "Inspections in the week, 5 = 80%"),
                     ("INSPECTIONS COUNTED", "Safety Subline", None),
                     ("STARTED, NOT CLOSED", "Active Inspections Not Closed", "Not counted until closed"),
                     ("OPEN SAFETY OBSERVATIONS", "Active Open Safety Observations", "Procore observations")])
    out += how(p, "Scored today (left of the call's 'double barrel'): Procore inspections CLOSED in the week - 5 = 80%, 16% less "
                  "for each one short, 4% more for each extra. Collected beside it, NOT in the grade yet: inspection pass rate "
                  "(items passed / passed + failed), observations raised and closed, punch. 'Data score (proposed)' averages "
                  "pass rate and close rate - a placeholder to agree, as the call asked.")
    out.append(proof(p, "safety", 36, 236, W - 72, 150,
                     [sa(c_("dim_Project", "ProjectName"), "Project"), sa(m_("Safety Inspections (Week)"), "Closed (week)"),
                      sa(m_(dash.score_name("Safety Inspections")), "Score"), sa(m_("Safety Pass Rate (4 Weeks)"), "Pass rate 4 wk"),
                      sa(m_("Open Safety Observations"), "Open obs."), sa(m_("Safety Observations (Week)"), "Raised (week)"),
                      sa(m_("Safety Observation Close Rate"), "Closed 90 d"),
                      sa(m_("Safety Data Score (Proposed)"), "Data score (proposed)")],
                     "Table. Safety by active project: inspections closed in the week and their score, the pass rate, "
                     "safety observations open and raised, and the proposed data score.",
                     title="SAFETY  -  scored, and collected", wide={"ProjectName": 4}, flag="Active Flag"))
    out.append(proof(p, "quality", 36, 394, W - 72, 150,
                     [sa(c_("dim_Project", "ProjectName"), "Project"), sa(m_("Quality Inspections (Week)"), "Closed (week)"),
                      sa(m_(dash.score_name("Quality Inspections")), "Score"), sa(m_("Quality Pass Rate (4 Weeks)"), "Pass rate 4 wk"),
                      sa(m_("Open Quality Observations"), "Open items"), sa(m_("Open Punch Items"), "Open punch"),
                      sa(m_("Quality Item Close Rate"), "Closed 90 d"),
                      sa(m_("Quality Data Score (Proposed)"), "Data score (proposed)")],
                     "Table. Quality by active project: inspections closed in the week and their score, pass rate, open "
                     "corrective actions and punch, and the proposed data score.",
                     title="QUALITY  -  scored, and collected", wide={"ProjectName": 4}, flag="Active Flag"))
    out.append(proof(p, "insp", 36, 552, W - 72, 142,
                     [sa(c_("dim_Project", "ProjectName"), "Project"), sa(c_("fct_Inspection", "Category"), "Pillar"),
                      sa(c_("fct_Inspection", "InspectionKey"), "Procore id"),
                      sa(c_("fct_Inspection", "InspectionName"), "Inspection"), sa(c_("fct_Inspection", "TemplateName"), "Template"),
                      sa(c_("fct_Inspection", "InspectionDate"), "Date"), sa(c_("fct_Inspection", "StatusLabel"), "Status"),
                      sa(m_("Inspection Counted"), "Counted?"), sa(m_("Inspection Pass Items"), "Passed"),
                      sa(m_("Inspection Fail Items"), "Failed"), sa(m_("Inspection Pass Rate"), "Pass rate")],
                     "Table. Every Procore inspection dated in the week on the active projects, whether it counted and why, "
                     "and its passed and failed items.", title="INSPECTIONS DATED IN THE WEEK  -  counted or not, and why",
                     wide={"ProjectName": 2, "InspectionName": 3, "TemplateName": 3, "Inspection Counted": 3},
                     flag="Inspection In Week Active Flag"))
    out.append(proof(p, "obs", 36, 702, W - 72, 140,
                     [sa(c_("dim_Project", "ProjectName"), "Project"), sa(c_("fct_DashObservation", "Category"), "Pillar"),
                      sa(c_("fct_DashObservation", "ItemType"), "Type"), sa(c_("fct_DashObservation", "ItemNumber"), "#"), sa(c_("fct_DashObservation", "ProcoreCategory"), "Procore category"),
                      sa(c_("fct_DashObservation", "Title"), "Title"), sa(c_("fct_DashObservation", "StatusLabel"), "Status"),
                      sa(c_("fct_DashObservation", "CreatedDate"), "Raised"), sa(c_("fct_DashObservation", "DueDate"), "Due")],
                     "Table. Procore observations and punch items on the active projects raised in the week or still open.",
                     title="OBSERVATIONS & PUNCH  -  raised in the week, or still open",
                     wide={"ProjectName": 2, "ProcoreCategory": 2, "Title": 4}, sort=(c_("fct_DashObservation", "CreatedDate"), "Descending"),
                     flag="Observation Active Flag"))
    return p, out


def project_header(p: str, title: str) -> list[dict]:
    """A one-project page: drill-through target (from the Portfolio table or the Overview's
    buttons), or opened directly with its own project picker."""
    out = [z(text(p, "hdr_band", " ", 0, 0, W, 81, fill=NAVY), 0),
           z(text(p, "hdr_rule", " ", 0, 81, W, 3, fill=TEAL), 1),
           text(p, "title", title, 36, 4, 318, 43, size=20, color="#FFFFFF"),
           kpi_value(p, "hdr_proj", "Project Title", 358, 8, 482, 38, size=20, color="#FFFFFF"),
           kpi_value(p, "hdr_sub", "Week Header", 30, 50, 600, 26, size=9, color="#C7D7E7"),
           kpi_value(p, "hdr_right", "Detail Header", 640, 52, 400, 26, size=8, color="#C7D7E7"),
           week_slicer(p, 1100, 8, 236, 44),
           button(p, "back", "< Back", 1150, 56, 84, 22, "Back"),
           nav(p, "home", "Executive >", 1240, 56, 96, 22, "dsexec", "the Executive Dashboard")]
    pick = rs.exclude_blank_name(dr.exclude_unmatched(dr.visual(p, "slicer_project", "slicer", 860, 8, 230, 44,
                                 {"Values": [column("dim_Project", "ProjectName")]}, title="Project", tab=2, title_size=9,
                                 alt="Slicer. Picks the project this page shows.")))
    pick["visual"]["objects"] = {"data": [{"properties": {"mode": lit("Dropdown")}}],
                                 "selection": [{"properties": {"singleSelect": _ON, "strictSingleSelect": _ON}}],
                                 "header": [{"properties": {"show": _OFF}}]}
    out.append(boxed(pick, fill=CARD_BG, radius=6))
    return out


def page_portfolio_detail() -> tuple[str, list[dict]]:
    """The Portfolio page, shown working: every project's grade built from its pillars and measures,
    the counts in the tiles, and the team behind the TEAM column."""
    p = "dsportscore"
    out = detail_header(p, "DETAIL  |  PORTFOLIO GRADES")
    out += strip(p, [("ACTIVE PROJECTS", "Active Projects", None), ("ON TRACK", "Projects On Track", None),
                     ("MONITOR", "Projects Monitor", None), ("NEEDS ATTENTION", "Projects Needing Attention", None),
                     ("UNSCORED", "Projects Unscored", "Under half the weight measured")])
    out += how(p, "Grade = the four pillars weighted Schedule 50, Budget 30, Safety 15, Quality 5, over the weight actually "
                  "measured (a project with under half the weight measured is Unscored, not failing). Each pillar = the "
                  "equal-weighted average of its measures scored this week; the measure table below shows every reading, "
                  "score and band. The tiles count the projects by grade band in the first table.")
    out.append(proof(p, "grades", 36, 236, W - 72, 200,
                     [sa(c_("dim_Project", "ProjectName"), "Project"), sa(m_("Grade Status"), "Band"),
                      sa(m_("Grade Cell"), "Grade"), sa(m_("Grade Coverage %"), "Weight measured"),
                      sa(m_("Schedule Pillar"), "Schedule (50)"), sa(m_("Budget Pillar"), "Budget (30)"),
                      sa(m_("Safety Pillar"), "Safety (15)"), sa(m_("Quality Pillar"), "Quality (5)"),
                      sa(m_("Weakest Pillar"), "Costing most"), sa(m_("Measures Below Target"), "Below 80%"),
                      sa(m_("Phase Label"), "Phase"), sa(m_("Phase Source"), "Phase read from")],
                     "Table. Every active project: grade band, grade, share of weight measured, the four pillar scores, "
                     "the pillar costing the grade most, measures below 80%, and the phase with where it is read from.",
                     title="HOW EACH GRADE IS BUILT  -  pillars weighted 50 / 30 / 15 / 5",
                     pills={"Grade Cell": ("Grade Colour", "Grade Ink")},
                     wide={"ProjectName": 3, "Phase Source": 4, "Grade Status": 2}, flag="Active Flag", totals=False))
    measures = proof(p, "measures", 36, 448, 880, 394,
                     [sa(c_("dim_Project", "ProjectName"), "Project"), sa(c_("dim_DashMetric", "Pillar"), "Pillar"),
                      sa(c_("dim_DashMetric", "Metric"), "Measure"), sa(m_("Metric Reading"), "Reading"),
                      sa(m_("Metric Score"), "Score"), sa(m_("Metric State"), "Band, or why not scored"),
                      sa(m_("Metric Weight In Grade"), "Share of grade")],
                     "Table. Every scorecard measure for every active project: what the data shows, the score, the band "
                     "or why it is not scored, and its share of the grade. A project's rows add up to its grade.",
                     title="EVERY MEASURE, EVERY PROJECT",
                     pills={"Metric Score": ("Metric Colour", "Metric Ink")},
                     wide={"ProjectName": 2, "Metric": 2, "Metric Reading": 4, "Metric State": 3},
                     flag="Active Flag", totals=False)
    measures["visual"]["query"]["sortDefinition"] = {"sort": [
        {"field": c_("dim_Project", "ProjectName")["field"], "direction": "Ascending"},
        {"field": c_("dim_DashMetric", "PillarKey")["field"], "direction": "Ascending"}], "isDefaultSort": True}
    out.append(where(measures, "dim_DashMetric", "Status", "'Live'"))
    out.append(proof(p, "team", 928, 448, 396, 394,
                     [sa(c_("dim_Project", "ProjectName"), "Project"), sa(c_("fct_ProjectTeam", "RoleCode"), "Role"),
                      sa(c_("fct_ProjectTeam", "MemberName"), "Procore directory name")],
                     "Table. The Procore directory roles behind the TEAM column: PX, PM, APM, Superintendent and "
                     "Assistant Superintendent on each active project.",
                     title="TEAM  -  Procore directory roles", wide={"ProjectName": 2, "MemberName": 3},
                     flag="Active Flag", totals=False))
    return p, out


def page_project_cost() -> tuple[str, list[dict]]:
    """Project Overview, shown working: contract, change orders, cost to complete, buyout."""
    p = "dsprojcost"
    out = project_header(p, "CONTRACT & COST  |")
    out += strip(p, [("ORIGINAL CONTRACT", "Original Contract", None), ("CURRENT CONTRACT", "Current Contract", None),
                     ("PENDING CHANGE ORDERS", "CO Pending Amount", "Procore prime COs not approved"),
                     ("REMAINING TO BILL", "Remaining Contract Balance", "Contract less billed (gross)"),
                     ("COST TO COMPLETE", "Cost To Complete", "Procore budget"),
                     ("RISK BOUGHT OUT", "Subcontractor Coverage %", "Committed / buyable budget")])
    out += how(p, "Current contract = the latest month's Procore prime contract value, every prime contract on the project added "
                  "together; the pay-app table shows each contract's own figure. Pending change orders = the change-order log "
                  "below, not yet approved. Cost to complete and risk bought out = the Procore budget lines below: committed "
                  "over the budget of divisions 01-44 (GCs, insurance, contingency, tax and fee are not bought out).")
    out.append(latest_owner(proof(p, "prime", 36, 236, 648, 210, prime_fields(project=False),
                                  "Table. The project's Procore prime contracts from their latest owner pay app.",
                                  title="PRIME CONTRACTS  -  latest owner pay app", wide={"ContractName": 3})))
    out.append(proof(p, "cos", 696, 236, 628, 210,
                     [sa(c_("fct_ChangeOrder", "ChangeOrderNumber"), "CO"), sa(c_("fct_ChangeOrder", "ChangeOrderTitle"), "Title"),
                      sa(c_("fct_ChangeOrder", "StatusDisplay"), "Status"), sa(c_("fct_ChangeOrder", "CreatedDate"), "Created"),
                      sa(m_("CO Approved Amount"), "Approved"), sa(m_("CO Pending Amount"), "Pending")],
                     "Table. Every Procore prime change order on the project; the Pending total is the card above.",
                     title="CHANGE ORDERS", wide={"ChangeOrderTitle": 4}, sort=(c_("fct_ChangeOrder", "CreatedDate"), "Descending")))
    out.append(proof(p, "lines", 36, 458, W - 72, 384,
                     [sa(c_("dim_CostCode", "CostCode"), "Cost code"), sa(c_("dim_CostCode", "Description"), "Description"),
                      sa(c_("dim_CostCodeCrosswalk", "NewDivisionName"), "Division (new master)"),
                      sa(m_("Line Budget"), "Budget"), sa(m_("Line Forecast"), "Forecast"), sa(m_("Line Committed"), "Committed"),
                      sa(m_("Line Coverage %"), "Coverage"), sa(m_("Line Spent"), "Spent"),
                      sa(m_("Line Cost To Complete"), "Cost to complete"), sa(m_("Line Treatment"), "How it counts")],
                     "Table. The project's Procore budget lines: budget, forecast, committed, coverage, spent and cost to "
                     "complete, and how each line counts. The totals are COST TO COMPLETE and RISK BOUGHT OUT.",
                     title="BUDGET LINES  -  the totals are the cards above",
                     wide={"Description": 3, "NewDivisionName": 2, "Line Treatment": 3}, flag="Budget Line Flag"))
    return p, out


def page_project_schedule() -> tuple[str, list[dict]]:
    """Project Overview, shown working: PROJECT COMPLETE and the finish dates."""
    p = "dsprojsched"
    out = project_header(p, "SCHEDULE & PROGRESS  |")
    out += strip(p, [("PROJECT COMPLETE", "Work Progress %", "Duration-weighted, Outbuild"),
                     ("TRACKING FINISH", "Tracking Finish", "Latest baseline finish"),
                     ("FORECAST FINISH", "Forecast Finish", "Latest current finish"),
                     ("DAYS VS BASELINE", "Completion Variance Days", "+ late, - early"),
                     ("BASELINE FROM", "Manual Baseline Note", None)])
    out += how(p, "Project complete = sum of (duration x % complete) over sum of duration, every real activity on the current "
                  "Outbuild schedule (summary bars and zero-duration milestones left out): the 'Share of progress' column adds "
                  "up to it. Tracking finish = the latest baseline finish on the critical path; forecast finish = the latest "
                  "current finish; days vs baseline = forecast less tracking (a hand-entered baseline overrides Outbuild's).")
    acts = proof(p, "acts", 36, 236, 796, 606,
                 [sa(c_("fct_ScheduleActivity", "ActivityName"), "Activity"), sa(c_("fct_ScheduleActivity", "StartDate"), "Start"),
                  sa(c_("fct_ScheduleActivity", "FinishDate"), "Finish"), sa(m_("Activity Duration"), "Days"),
                  sa(m_("Activity % Complete"), "% complete"), sa(m_("Activity Share Of Progress"), "Share of progress")],
                 "Table. Every activity PROJECT COMPLETE weighs: start, finish, duration, Outbuild % complete, and the "
                 "points of progress it contributes. The total is PROJECT COMPLETE.",
                 title="HOW PROJECT COMPLETE IS BUILT  -  the total is the card above",
                 wide={"ActivityName": 5}, sort=(m_("Activity Duration"), "Descending"), flag="Progress Row Flag")
    out.append(acts)
    out.append(proof(p, "ms", 844, 236, 480, 606,
                     [sa(c_("fct_Milestone", "MilestoneName"), "Critical-path activity"),
                      sa(m_("Milestone Baseline Finish"), "Baseline"), sa(m_("Milestone Forecast Finish"), "Forecast"),
                      sa(m_("Milestone Days Late"), "Days")],
                     "Table. The critical-path activities on the current Outbuild schedule with baseline and current finish; "
                     "the latest of each is TRACKING FINISH and FORECAST FINISH.",
                     title="CRITICAL PATH  -  latest dates first", wide={"MilestoneName": 4},
                     sort=(m_("Milestone Forecast Finish"), "Descending"), totals=False))
    return p, out


def page_payments() -> tuple[str, list[dict]]:
    """Oct 30 call: double-click Project Financials - have we been paid, has the sub been paid."""
    p = "dspayments"
    out = [z(text(p, "hdr_band", " ", 0, 0, W, 81, fill=NAVY), 0),
           z(text(p, "hdr_rule", " ", 0, 81, W, 3, fill=TEAL), 1),
           text(p, "title", "PROJECT PAYMENTS  |", 36, 4, 318, 43, size=20, color="#FFFFFF"),
           kpi_value(p, "hdr_proj", "Project Title", 358, 8, 482, 38, size=20, color="#FFFFFF"),
           kpi_value(p, "hdr_sub", "Week Header", 30, 50, 600, 26, size=9, color="#C7D7E7"),
           kpi_value(p, "hdr_right", "Detail Header", 640, 52, 400, 26, size=8, color="#C7D7E7"),
           week_slicer(p, 1100, 8, 236, 44),
           button(p, "back", "< Back", 1150, 56, 84, 22, "Back"),
           nav(p, "home", "Executive >", 1240, 56, 96, 22, "dsexec", "the Executive Dashboard")]
    pick = rs.exclude_blank_name(dr.exclude_unmatched(dr.visual(p, "slicer_project", "slicer", 860, 8, 230, 44,
                                 {"Values": [column("dim_Project", "ProjectName")]}, title="Project", tab=2, title_size=9,
                                 alt="Slicer. Picks the project this page shows.")))
    pick["visual"]["objects"] = {"data": [{"properties": {"mode": lit("Dropdown")}}],
                                 "selection": [{"properties": {"singleSelect": _ON, "strictSingleSelect": _ON}}],
                                 "header": [{"properties": {"show": _OFF}}]}
    out.append(boxed(pick, fill=CARD_BG, radius=6))
    out += strip(p, [("CONTRACT", "Position Contract", None), ("BILLED (GROSS)", "Billed To Date (Gross)", "Procore pay apps, before retainage"),
                     ("RECEIVED", "Paid To Date", "Sage receipts"), ("OWED TO AFFECT", "Cash - Unpaid Receivables", "Sage AR"),
                     ("LEFT TO BILL", "Remaining Contract Balance", None), ("OWED TO SUBS", "Sub AP Open", "Sage AP")])
    out += how(p, "Owner side: Procore prime contracts and their latest pay app; Sage invoices for what was received and is "
                  "still owed. Sub side: each subcontractor's latest approved Procore requisition (committed, billed, retainage) "
                  "beside Sage AP for the same vendor on the job (invoiced, paid, still to pay, age of the oldest unpaid). "
                  "Contract - received - owed = left to collect.")
    out.append(latest_owner(proof(p, "prime", 36, 236, 648, 230, prime_fields(project=False),
                                  "Table. The project's Procore prime contracts from their latest owner pay app.",
                                  title="PRIME CONTRACTS", wide={"ContractName": 3})))
    out.append(proof(p, "invoices", 696, 236, 628, 230,
                     [sa(c_("fct_Invoice", "InvoiceNumber"), "Invoice"), sa(c_("fct_Invoice", "InvoiceID"), "Sage rec"),
                      sa(c_("fct_Invoice", "SentDate"), "Date"), sa(c_("fct_Invoice", "SageStatus"), "Status"),
                      sa(m_("Invoice Amount"), "Invoiced"), sa(m_("Invoice Paid"), "Received"),
                      sa(m_("Invoice Balance"), "Owed"), sa(m_("Invoice Age Days"), "Days")],
                     "Table. The project's Sage AR invoices: invoiced, received and still owed, voids at zero.",
                     title="OWNER INVOICES (SAGE, NET OF RETAINAGE)", sort=(c_("fct_Invoice", "SentDate"), "Descending")))
    out.append(proof(p, "subs", 36, 478, W - 72, 364,
                     [sa(c_("fct_SubPayment", "SubName"), "Subcontractor"), sa(c_("fct_SubPayment", "ContractName"), "Commitment"),
                      sa(m_("Sub Committed"), "Committed"), sa(m_("Sub Requisitioned"), "Billed to date"),
                      sa(m_("Sub Retainage Held"), "Retainage"), sa(m_("Sub AP Invoiced"), "Sage AP"),
                      sa(m_("Sub Paid"), "Paid"), sa(m_("Sub AP Open"), "Still to pay"),
                      sa(m_("Sub Oldest Open Days"), "Oldest unpaid (days)"), sa(c_("fct_SubPayment", "OpenApAge"), "Age"),
                      sa(m_("Sub Left To Pay"), "Left on commitment"), sa(c_("fct_SubPayment", "Source"), "Source")],
                     "Table. Every subcontractor and supplier on the project: committed, billed, retainage, Sage AP invoiced, "
                     "paid and still to pay, the age of the oldest unpaid invoice, and what is left on the commitment.",
                     title="SUBCONTRACTORS  -  committed, billed, paid, still to pay",
                     sort=(m_("Sub AP Open"), "Descending"), wide={"SubName": 3, "ContractName": 3, "Source": 3}))
    out += footer(p, "Pick the project above, or right-click a project on the Portfolio page and drill through  •  Export any "
                     "table to Excel from its ... menu")
    return p, out


def page_health() -> tuple[str, list[dict]]:
    p = "dshealth"
    out = detail_header(p, "DATA HEALTH  |  IS THE SOURCE KEPT UP?", right="Health Header")
    out += strip(p, [("WARNINGS", "Checks Warning", "Across active projects"),
                     ("PROJECTS WITH A WARNING", "Projects With Warnings", None),
                     ("CHECKS PASSED", "Checks Passed", None),
                     ("AR ON NO PROCORE PROJECT", "Unattributed Open AR", "Map the Sage job in the crosswalk"),
                     ("SAGE CLOSED THROUGH", "Books Closed Through", None)])
    out += how(p, "Oct 30 call: validate the input, not only the output. Each build checks every active project - does Sage tie "
                  "out to Procore, are there voids or duplicate invoices, old AR, a look-ahead not updated, activities past their "
                  "finish and not marked complete, inspections left open, roles missing in Procore, no budget forecast. A warning "
                  "means the number on the dashboard is only as good as that entry.")
    out.append(proof(p, "checks", 36, 236, W - 72, 420,
                     [sa(c_("dim_Project", "ProjectName"), "Project"), sa(c_("fct_DashCheck", "CheckOrder"), "#"),
                      sa(c_("fct_DashCheck", "CheckName"), "Check"), sa(m_("Check Result"), "Result"),
                      sa(c_("fct_DashCheck", "Detail"), "What the data shows"), sa(m_("Check Amount"), "Number"),
                      sa(c_("fct_DashCheck", "Action"), "To fix")],
                     "Table. Every input check on every active project: the check, Pass, Warn or Info, what the data shows, "
                     "the number behind it and who fixes it.",
                     title="INPUT CHECKS  -  every active project, every build",
                     pills={"Check Result": ("Check Colour", "Check Ink")},
                     wide={"ProjectName": 2, "CheckName": 2, "Detail": 5, "Action": 4}, flag="Active Flag", totals=False))
    out.append(where(proof(p, "unmatched", 36, 668, W - 72, 174,
                           [sa(c_("fct_Invoice", "SageJobNumber"), "Sage job"), sa(c_("fct_Invoice", "SageJobName"), "Job name"),
                            sa(m_("Job Open AR"), "Open AR"), sa(m_("Revenue YTD"), "Revenue YTD")],
                           "Table. Sage jobs with AR but no Procore project in the crosswalk: open AR and revenue this year.",
                           title="SAGE JOBS WITH NO PROCORE PROJECT  -  in Revenue YTD, on no project page",
                           sort=(m_("Job Open AR"), "Descending"), wide={"SageJobName": 4}, flag="Unmatched Job Flag"),
                     "fct_Invoice", "HasUnmatchedProject", "true"))
    return p, out


# --------------------------------------------------------------------------- pages

def page_executive() -> tuple[str, list[dict]]:
    """Deck slide 1. The company in one screen; every tile Active projects only."""
    p = "dsexec"
    y0, th = 102, 110
    xs = [37, 254, 470, 686, 903, 1119]
    tw = 204
    out = [*header(p, "EXECUTIVE DASHBOARD", "Week Header", "Data As Of Header")]
    # Every tile opens the rows it is made from (Oct 30 call: "prove the work").
    out += tile(p, "k_rev", "REVENUE YTD", "Revenue YTD", "Revenue YTD Subline", xs[0], y0, tw, th, accent=GREEN,
                precision=1, units=1000000, sub_color=SLATE, link=("dsrevenue", "the Sage invoices behind Revenue YTD"))
    out += tile(p, "k_gm", "GROSS MARGIN", "Portfolio Gross Margin %", "Gross Margin Subline", xs[1], y0, tw, th,
                accent=GREEN, precision=1, sub_color=AMBER_TEXT, link=("dsmargin", "the budget and forecast behind the margin"))
    out += tile(p, "k_backlog", "BACKLOG", "Backlog", "Backlog Subline", xs[2], y0, tw, th, accent=TEAL,
                precision=1, units=1000000, sub_color=GREEN, link=("dscontract", "the contracts and billing behind backlog"))
    out += tile(p, "k_active", "ACTIVE PROJECTS", "Active Projects", "Attention Subline", xs[3], y0, tw, th,
                accent=AMBER, sub_color=AMBER_TEXT, link=("dscontract", "the active project list and why each is active"))
    out += tile(p, "k_cash", "CASH POSITION", "Portfolio Cash Position", "Cash Subline", xs[4], y0, tw, th,
                accent=GREEN, precision=1, units=1000000, link=("dscash", "every step of the cash position formula"))
    out += tile(p, "k_safety", "SAFETY", "Portfolio Safety Score", "Safety Subline",
                xs[5], y0, tw, th, accent=GREEN, sub_color=SLATE, link=("dssafety", "the inspections and safety data"))

    # Financial performance (deck 0.46-6.61 in)
    fx, fy, fw, fh = 37, 230, 492, 381
    out += [panel(p, "fin_bg", fx, fy, fw, fh),
            text(p, "fin_h", "FINANCIAL PERFORMANCE", fx + 18, fy + 12, fw - 140, 26, size=12, color=NAVY),
            nav(p, "fin_data", "Revenue data >", fx + fw - 116, fy + 14, 98, 20, "dsrevenue", "revenue by month and by job"),
            z(text(p, "fin_rule", " ", fx + 18, fy + 42, fw - 36, 1, fill=LINE), 1),
            text(p, "fin_sub", "REVENUE  •  ACTUAL BY MONTH  (PLAN: AWAITING DATA ENTRY)", fx + 18, fy + 50,
                 fw - 36, 22, size=8.5)]
    chart = dr.visual(p, "fin_chart", "clusteredColumnChart", fx + 12, fy + 74, fw - 24, 198,
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
    # Oct 30 call: closed months are final; a month not yet closed in Sage carries a warning.
    out.append(kpi_value(p, "fin_close", "Close Status Text", fx + 10, fy + 274, fw - 20, 26, size=7, color=AMBER_TEXT,
                         alt="Card. The last month closed in Sage, and whether later months are provisional."))
    out += [z(text(p, "fin_rule2", " ", fx + 18, fy + 306, fw - 36, 1, fill=LINE), 1),
            # Oct 30 call: Affect books no depreciation, so this reads as net income.
            text(p, "fin_ebitda", "NET INCOME", fx + 18, fy + 318, 110, 22, size=9),
            text(p, "fin_ebitda_v", "Needs the Sage general ledger (overheads) - not yet ingested", fx + 18, fy + 342,
                 220, 34, size=8, color=SLATE, bold=False),
            text(p, "fin_ar", "AR > 60 DAYS", fx + 270, fy + 318, 110, 22, size=9),
            nav(p, "fin_ar_data", "Data >", fx + fw - 64, fy + 318, 46, 20, "dsar", "the open AR invoices by age"),
            kpi_value(p, "fin_ar_v", "AR Over 60 Days", fx + 262, fy + 342, 200, 34, size=18, color=AMBER_TEXT,
                      precision=1, units=1000000)]

    # Project execution (deck 6.79-12.06 in)
    ex, ey, ew, eh = 543, 230, 422, 381
    out += [panel(p, "exe_bg", ex, ey, ew, eh),
            text(p, "exe_h", "PROJECT EXECUTION", ex + 18, ey + 12, ew - 36, 26, size=12, color=NAVY),
            z(text(p, "exe_rule", " ", ex + 18, ey + 42, ew - 36, 1, fill=LINE), 1)]
    rows = [("ON SCHEDULE", "On Schedule Text", "On Schedule Ratio", GREEN, "forecast finish on or before baseline",
             "dsschedule", "baseline and forecast finish by project"),
            ("ON BUDGET", "On Budget Text", "On Budget Ratio", TEAL, "forecast final cost within budget",
             "dsmargin", "budget against forecast by project"),
            ("SUBCONTRACTOR COVERAGE", "Portfolio Subcontractor Coverage", "Portfolio Subcontractor Coverage",
             "#235A89", "committed / buyable budget", "dsmargin", "committed against budget by cost code"),
            ("CHANGE ORDERS APPROVED", "Change Orders Approved %", "Change Orders Approved %", AMBER,
             "approved / approved + pending value", "dscontract", "every prime change order")]
    for i, (lbl, val, ratio, color, hint, target, what) in enumerate(rows):
        ry = ey + 48 + i * 64
        out += [text(p, f"exe_{i}_l", lbl, ex + 18, ry, 210, 24, size=9),
                nav(p, f"exe_{i}_data", "Data >", ex + 232, ry + 2, 46, 20, target, what),
                kpi_value(p, f"exe_{i}_v", val, ex + ew - 128, ry - 6, 112, 28, size=11, color=NAVY),
                *bar(p, f"exe_{i}_bar", ratio, ex + 18, ry + 24, ew - 36, 20, color),
                text(p, f"exe_{i}_hint", hint, ex + 18, ry + 44, ew - 176, 20, size=6.5, color=SLATE, bold=False)]
    out += [z(text(p, "exe_rule2", " ", ex + 18, ey + 308, ew - 36, 1, fill=LINE), 1),
            text(p, "exe_fp", "FIELD PRODUCTIVITY", ex + 18, ey + 312, 170, 24, size=9),
            # Oct 30 call: rolling 3-week look-ahead plan against what was put in place - to build.
            text(p, "exe_fp_v", "Next: 3-week plan vs actual (Outbuild)", ex + 190, ey + 312, 214, 22, size=8,
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
                 rs.shown_as(measure("Priority Status"), "Status")],
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
            text(p, "wl_h", "EXECUTIVE DECISIONS / WATCHLIST", wx + 18, wy + 10, ww - 140, 26, size=12, color=NAVY),
            nav(p, "wl_health", "Data health >", wx + ww - 116, wy + 12, 98, 20, "dshealth", "the data health checks"),
            text(p, "wl_pending",
                 "Awaiting data entry: leadership's three focus items for the month (the decision, and "
                 "the project or issue behind it). A SharePoint list will feed this panel, alongside the "
                 "projects leadership wants always shown under Priority Projects.",
                 wx + 18, wy + 42, ww - 36, 90, size=8.5, color=SLATE, bold=False, fill="#F6F8FA", radius=8),
            z(text(p, "wl_dq_bg", " ", wx + 18, wy + 140, ww - 36, 64, fill="#FFF0CF", radius=8), 1000),
            kpi_value(p, "wl_dq", "Data Notice", wx + 26, wy + 144, ww - 52, 56, size=8, color="#7A4F12")]
    out += footer(p, "Active: the Nov 19 rollout projects  •  Revenue: Sage invoiced to the week picked, voids excluded  •  "
                     "Margin: Procore forecast, CM fee excluded  •  Safety: inspections closed in the week, 5 = 80%  •  "
                     "Data > opens the rows behind each number")
    return p, out


def page_portfolio() -> tuple[str, list[dict]]:
    """Deck slide 2. The four pillars and the grade, one row per active project."""
    p = "dsportfolio"
    out = [*header(p, "PROJECT PORTFOLIO  |  STATUS", "Week Header", "Portfolio Header")]
    tiles = [("PROJECTS", "Active Projects", "In portfolio", TEAL),
             ("ON TRACK", "Projects On Track", "=On Track Caption", GREEN),
             ("NEEDS ATTENTION", "Projects Needing Attention", "=Attention Caption", RED),
             ("MONITOR", "Projects Monitor", "=Monitor Caption", AMBER),
             ("UNSCORED", "Projects Unscored", "Awaiting data", SLATE)]
    for i, (lbl, m, sub, color) in enumerate(tiles):
        x = 36 + i * 262
        out += [panel(p, f"k{i}_bg", x, 100, 246, 84, radius=8),
                z(text(p, f"k{i}_bar", " ", x, 100, 6, 84, fill=color), 1),
                text(p, f"k{i}_l", lbl, x + 18, 108, 160, 20, size=9),
                nav(p, f"k{i}_data", "Data >", x + 192, 106, 46, 20, "dsportscore", "how every grade is built"),
                kpi_value(p, f"k{i}_v", m, x + 12, 128, 90, 50, size=24, color=NAVY),
                # "=Name" is a caption measure (reads the grade settings); anything else is fixed text.
                kpi_value(p, f"k{i}_s", sub[1:], x + 104, 146, 136, 24, size=8, color=SLATE) if sub.startswith("=")
                else text(p, f"k{i}_s", sub, x + 104, 148, 136, 20, size=8, color=SLATE, bold=False)]
    out += [panel(p, "tbl_bg", 36, 198, 1288, 370),
            text(p, "tbl_h", "ACTIVE PROJECTS  •  PERFORMANCE & ACCOUNTABILITY", 56, 208, 760, 28, size=13, color=NAVY),
            text(p, "tbl_note", "Right-click a project to drill through  •  How each grade is built:",
                 820, 212, 370, 20, size=8, color=SLATE, bold=False, align="right"),
            nav(p, "tbl_data", "Data >", 1200, 210, 100, 22, "dsportscore", "how every grade is built")]
    grid = table(p, "portfolio", 48, 240, 1264, 316,
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
    out += [panel(p, "off_bg", 36, 580, 1288, 266),
            text(p, "off_h", "NOT ON THE ACTIVE LIST", 56, 588, 560, 24, size=10, color=NAVY),
            text(p, "off_note", "Archived = 100% paid, or not in the Nov 19 rollout (Oct 30 call). Still graded, not counted.",
                 640, 590, 664, 20, size=8, color=SLATE, bold=False, align="right")]
    off = table(p, "inactive", 48, 614, 1264, 226,
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
    # Grade legend with the pill colours, as the deck's slide 2 strip; the band captions are
    # the same setting-driven measures as the tiles, so legend, tiles and pills agree.
    out.append(text(p, "lg_h", "GRADE", 36, 852, 48, 22, size=7.5, color=NAVY))
    for i, (key, colour, cap) in enumerate([("ok", dash.GREEN, "On Track Caption"), ("watch", AMBER, "Monitor Caption"),
                                           ("bad", RED, "Attention Caption"), ("none", dash.MIST, None)]):
        lx = 88 + i * 150
        out.append(z(text(p, f"lg_{key}_sw", " ", lx, 857, 12, 12, fill=colour, radius=2), 1000))
        out.append(kpi_value(p, f"lg_{key}", cap, lx + 16, 850, 130, 24, size=7.5, color=SLATE) if cap
                   else text(p, f"lg_{key}", "No data", lx + 16, 852, 130, 22, size=7.5, color=SLATE, bold=False))
    out.append(text(p, "footer", "Cells: reading · pillar score (colour)   •   Weights: Schedule 50  Budget 30  "
                    "Safety 15  Quality 5   •   Worst grade first", 692, 852, 632, 22, size=7.5, color=SLATE,
                    bold=False))
    return p, out


def page_project() -> tuple[str, list[dict]]:
    """Deck slide 3. One project; drill-through target, or pick it in the header."""
    p = "dsproject"
    out = [z(text(p, "hdr_band", " ", 0, 0, W, 81, fill=NAVY), 0),
           z(text(p, "hdr_rule", " ", 0, 81, W, 3, fill=TEAL), 1),
           text(p, "title", "PROJECT OVERVIEW  |", 36, 4, 318, 43, size=20, color="#FFFFFF"),
           kpi_value(p, "hdr_proj", "Project Title", 358, 8, 482, 38, size=20, color="#FFFFFF"),
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
    # In the header band (audit 2026-10-26): the 24px they took above the tiles goes to row 3.
    out.append(button(p, "go_grade", "Grade detail >", 1226, 56, 110, 22, "Drillthrough", "dsgrade"))
    out.append(button(p, "back", "< Back", 1140, 56, 80, 22, "Back"))

    # KPI row (deck 1.34-2.0 in)
    xs, tw, y0, th = [37, 306, 575, 844, 1113], 246, 96, 104
    # Every tile opens the rows behind it for this project (Oct 30 call).
    out += tile(p, "k_contract", "CURRENT CONTRACT", "Current Contract", "Contract Change Text", xs[0], y0, tw, th,
                accent=TEAL, precision=2, units=1000000, sub_color=SLATE, link=("dsprojcost", "contract", "drill"))
    out += tile(p, "k_complete", "PROJECT COMPLETE", "Work Progress Shown", None, xs[1], y0, tw, th, accent=AMBER,
                link=("dsprojsched", "progress", "drill"))
    out.append(text(p, "k_complete_s", "Outbuild work progress (duration-weighted)", xs[1] + 16, y0 + th - 28,
                    tw - 24, 22, size=8, color=SLATE, bold=False))
    out += tile(p, "k_sched", "SCHEDULE", "Schedule Headline", "Schedule Subline", xs[2], y0, tw, th, accent=AMBER,
                size=20, sub_color=SLATE, link=("dsprojsched", "schedule", "drill"))
    out += tile(p, "k_grade", "PROJECT SCORECARD", "Grade Text", "Grade Subline", xs[3], y0, tw, th, accent=AMBER,
                size=20, sub_color=SLATE, link=("dsgrade", "grade", "drill"))
    out += tile(p, "k_billed", "BILLED TO DATE", "Billed To Date (Gross)", "Billed Subline", xs[4], y0, tw, th,
                accent=GREEN, precision=2, units=1000000, sub_color=SLATE, link=("dspayments", "billing", "drill"))

    # Row 2 (deck 2.61-4.95 in): schedule & delivery, project financials, delivery & financial health
    r2, h2 = 210, 290
    sx, sw = 37, 466
    out += [panel(p, "sd_bg", sx, r2, sw, h2),
            z(text(p, "sd_bar", " ", sx, r2, 6, h2, fill=TEAL), 1),
            text(p, "sd_h", "SCHEDULE & DELIVERY", sx + 20, r2 + 12, sw - 160, 26, size=12, color=NAVY),
            button(p, "sd_work", "Schedule detail >", sx + sw - 136, r2 + 14, 120, 22, "Drillthrough", "dsprojsched"),
            text(p, "sd_tl", "TRACKING FINISH (BASELINE)", sx + 20, r2 + 46, 240, 20, size=9),
            kpi_value(p, "sd_tv", "Tracking Finish Shown", sx + 270, r2 + 40, 180, 30, size=13, color=NAVY),
            text(p, "sd_fl", "FORECAST FINISH", sx + 20, r2 + 80, 240, 20, size=9),
            kpi_value(p, "sd_fv", "Forecast Finish Shown", sx + 270, r2 + 74, 180, 30, size=13, color=AMBER_TEXT)]
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
            text(p, "pf_h", "PROJECT FINANCIALS", fx + 20, r2 + 12, fw - 140, 26, size=12, color=NAVY),
            # Oct 30 call: double-click the financials - have we been paid, has each sub been paid.
            button(p, "pf_pay", "Payments >", fx + fw - 112, r2 + 14, 96, 22, "Drillthrough", "dspayments")]
    for i, (lbl, m) in enumerate([("ORIGINAL CONTRACT", "Original Contract"), ("CURRENT CONTRACT", "Current Contract"),
                                  # The change-order log itself, so it ties to Payments / Contracts.
                                  ("PENDING CHANGE ORDERS", "CO Pending Amount"),
                                  ("BILLED TO DATE", "Billed To Date (Gross)"), ("PAID TO DATE", "Paid To Date"),
                                  ("REMAINING CONTRACT BALANCE", "Remaining Contract Balance")]):
        ry = r2 + 48 + i * 40
        out += [text(p, f"pf_{i}_l", lbl, fx + 20, ry + 6, 208, 20, size=9),
                kpi_value(p, f"pf_{i}_v", m, fx + 230, ry, 150, 30, size=12, color=NAVY, precision=0, units=1)]

    hx, hw = 921, 402
    out += [panel(p, "hf_bg", hx, r2, hw, h2),
            z(text(p, "hf_bar", " ", hx, r2, 6, h2, fill=TEAL), 1),
            text(p, "hf_h", "DELIVERY & FINANCIAL HEALTH", hx + 20, r2 + 12, hw - 150, 26, size=12, color=NAVY),
            button(p, "hf_work", "Cost detail >", hx + hw - 116, r2 + 14, 100, 22, "Drillthrough", "dsprojcost"),
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
            kpi_value(p, "hf_ex", "Financial Exceptions", hx + 28, r2 + 214, hw - 56, 66, size=9, color="#7A4F12")]

    # Row 3 (deck 6.2-10.0 in): top risks, near-term milestones + critical path, safety/quality/wins
    r3, h3 = 512, 276
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
            text(p, "ms_h", "NEAR-TERM MILESTONES  [NEXT 3 WEEKS]", mx + 20, r3 + 10, mw - 34, 24, size=10, color=NAVY)]
    near = table(p, "ms_near", mx + 14, r3 + 36, mw - 28, 106,
                 [rs.shown_as(column("fct_ScheduleActivity", "ActivityName"), "Activity"),
                  rs.shown_as(measure("Activity Next Step"), "Next")],
                 alt="Table. Outbuild activities starting or finishing in the next three weeks.")
    rs.widen(near, {"ActivityName": 3, "Activity Next Step": 2})
    out.append(flagged(near, "Near Term Flag"))
    out.append(text(p, "ms_cp", "CRITICAL PATH  [NEXT 3 WEEKS]", mx + 20, r3 + 150, mw - 34, 20, size=10, color=NAVY))
    crit = table(p, "ms_crit", mx + 14, r3 + 170, mw - 28, 98,
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
        ly = r3 + 36 + i * 80
        t = table(p, f"sq_{cat.lower()}", qx + 14, ly, qw - 28, 74,
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
    wins = table(p, "sq_wins", qx + 14, r3 + 196, qw - 28, 72,
                 [rs.shown_as(column("fct_ScheduleActivity", "ActivityName"), "Recent wins - completed this week")],
                 alt="Table. Outbuild activities completed in the reporting week.")
    out.append(flagged(wins, "Recent Win Flag"))

    out += [z(text(p, "focus_bg", " ", 37, 798, 1286, 40, fill="#E7EDF2", radius=8), 1000),
            kpi_value(p, "focus", "Executive Focus", 52, 802, 1260, 32, size=10, color=NAVY)]
    out += footer(p, "Financials as of the last refresh; inspections, meetings and wins for the week  •  Milestones: "
                     "Outbuild current schedule  •  Top risks: measures below 80% (HIGH below 50%)")
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
    out += footer(p, "Scores: Scorecard.xlsx bands  •  Pillar = average of its measured items  •  Grade = pillars "
                     "weighted 50 / 30 / 15 / 5  •  Agenda 'not verifiable': Procore keeps only the last send")
    return p, out


PAGES = [
    ("Executive Dashboard", page_executive, False),
    ("Project Portfolio | Status", page_portfolio, False),
    ("Project Overview", page_project, False),
    # Oct 30 call: the rows behind every number, each opened from its tile's "Data >".
    ("Detail | Revenue", page_revenue, False),
    ("Detail | Receivables", page_ar, False),
    ("Detail | Margin & Budget", page_margin, False),
    ("Detail | Contracts & COs", page_contracts, False),
    ("Detail | Cash Position", page_cash, False),
    ("Detail | Schedule", page_schedule_detail, False),
    ("Detail | Safety & Quality", page_safety_detail, False),
    ("Detail | Portfolio Grades", page_portfolio_detail, False),
    ("Project Payments", page_payments, False),
    # The Project Overview's numbers, shown working (drill through from a project).
    ("Project | Contract & Cost", page_project_cost, False),
    ("Project | Schedule & Progress", page_project_schedule, False),
    ("Data Health", page_health, False),
    ("Grade Detail", page_grade, True),
]
DRILLTHROUGH = {"dsproject": ("dim_Project", "ProjectName"), "dsgrade": ("dim_Project", "ProjectName"),
                "dspayments": ("dim_Project", "ProjectName"), "dsprojcost": ("dim_Project", "ProjectName"),
                "dsprojsched": ("dim_Project", "ProjectName")}
# Drill-through targets a reader also opens directly; they keep their own project picker.
OPEN_DIRECTLY = {"dsproject", "dspayments", "dsprojcost", "dsprojsched"}


def retab(files: dict[str, str]) -> None:
    """Keyboard / screen-reader order: rows top to bottom, left to right within a row, so a
    label comes before the value card sitting a few px above it; decorations last (audit
    2026-10-26: values were read before labels, and blank boxes were tab stops)."""
    by_page: dict[str, list[tuple[str, dict]]] = {}
    for rel in [r for r in files if r.endswith("/visual.json") and "/pages/" in r]:
        by_page.setdefault(rel.split("/pages/")[1].split("/")[0], []).append((rel, json.loads(files[rel])))
    for items in by_page.values():
        def is_decor(v):
            alt = v["visual"]["visualContainerObjects"]["general"][0]["properties"]["altText"]["expr"]["Literal"]["Value"]
            return alt == "'Decoration'"
        def rows_of(group):  # a new row starts more than 12 px below the current row's top
            rows, top = [], None
            for it in sorted(group, key=lambda it: it[1]["position"]["y"]):
                y = it[1]["position"]["y"]
                if top is None or y > top + 12:
                    rows.append([])
                    top = y
                rows[-1].append(it)
            return [it for row in rows for it in sorted(row, key=lambda it: it[1]["position"]["x"])]

        # Each visual belongs to the smallest panel (a large decoration) around its centre, so a
        # tile reads label, value, sub-line before the next tile; panels go in row order.
        p_ = lambda v: v["position"]  # noqa: E731
        panels = [v for _, v in items if is_decor(v) and p_(v)["width"] * p_(v)["height"] > 4000]
        groups: dict[str, list] = {}
        for it in (it for it in items if not is_decor(it[1])):
            pos = p_(it[1])
            cx, cy = pos["x"] + pos["width"] / 2, pos["y"] + pos["height"] / 2
            around = [q for q in panels if p_(q)["x"] <= cx <= p_(q)["x"] + p_(q)["width"]
                      and p_(q)["y"] <= cy <= p_(q)["y"] + p_(q)["height"]]
            key = min(around, key=lambda q: p_(q)["width"] * p_(q)["height"])["name"] if around else it[1]["name"]
            groups.setdefault(key, []).append(it)
        heads = [(min(g, key=lambda it: (p_(it[1])["y"], p_(it[1])["x"])), g) for g in groups.values()]
        ordered = [it for _, g in sorted(heads, key=lambda hg: (p_(hg[0][1])["y"] // 40, p_(hg[0][1])["x"]))
                   for it in rows_of(g)]
        ordered += [it for it in items if is_decor(it[1])]
        for n, (rel, v) in enumerate(ordered):
            v["position"]["tabOrder"] = n
            files[rel] = json.dumps(v, indent=2)
            (REPORT_DIR / rel).write_text(files[rel], encoding="utf-8", newline="")


def build(model_id: str) -> dict[str, str]:
    """deploy_report.build with this report's pages, then the deck's page size and colour."""
    dr.REPORT_NAME, dr.REPORT_DIR, dr.PAGES, dr.DRILLTHROUGH = REPORT_NAME, REPORT_DIR, PAGES, DRILLTHROUGH
    dr.chrome = lambda page, slicers=True: []  # every page draws its own header and footer
    files = dr.build(model_id)
    for rel in [r for r in files if r.endswith("/page.json") and "/pages/" in r]:
        page = json.loads(files[rel])
        # FitToPage: on a 16:9 room screen FitToWidth pushed ~160px below the fold (audit).
        page.update(width=W, height=H, displayOption="FitToPage")
        page["objects"] = {"background": [{"properties": {"color": _color(PAGE_BG), "transparency": _num(0)}}],
                           "outspace": [{"properties": {"color": _color(PAGE_BG), "transparency": _num(0)}}]}
        # A drill-through page that is also opened directly keeps its own project picker.
        if page["name"] in OPEN_DIRECTLY:
            page.pop("visibility", None)
        files[rel] = json.dumps(page, indent=2)
        (REPORT_DIR / rel).write_text(files[rel], encoding="utf-8", newline="")
    retab(files)
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
