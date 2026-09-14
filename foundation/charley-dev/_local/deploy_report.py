"""Generate and deploy the Monthly Progress Report (PBIR) over the semantic model.

    python deploy_report.py            # dry run - write PBIR to disk only
    python deploy_report.py --apply    # create/update the report in Fabric

Eleven pages, following powerbi/report-spec.md:
   1. Portfolio       - every project at once; the view leadership never had
   2. Overview        - the one-page replacement for the DASHBOARD tab
   3. Financial       - contract, budget, change orders, the billing S-curve
   4. Schedule        - the milestone timeline
   5. Safety & Quality
   6. Billing & Retainage
   7. Direct Costs & Vendors
   8. Scorecard       - and the table showing how the score is built
   9. Source Coverage - which projects exist in all three systems
  10. Project Detail  - drill-through target
  11. Data Quality    - visible; surfaces bad data instead of letting it flow into a rollup

Every page carries the same two synced slicers and a footer naming the reporting period
and the gold build time.

Colours come from powerbi/theme.json, registered here as a custom theme. The workbook's
own font colours (#DB1918 / #FFD800 / #01AF00) were measured and two of the three fail
contrast, so the RAG steps are the corrected ones - see the constants below.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
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

# RAG steps, contrast-corrected. The workbook's own font colours were #01AF00 / #FFD800 /
# #DB1918; two of the three fail against a light surface and were re-stepped in
# powerbi/report-spec.md after measuring, not by eye:
#   green  #01AF00 -> 2.87:1, below the 3:1 floor
#   amber  #FFD800 -> 1.36:1, effectively invisible on white
# The amber is worth raising with Affect directly - it is a plausible reason "Watch" status
# gets overlooked in the spreadsheet today.
#
# Colour is never the only channel: every status in this report carries its text label too,
# because red/green cannot be made colourblind-safe as colour alone (measured deuteranopia
# separation is dE 7.1, below the dE 8 floor, and no re-stepping fixes the hue pair).
GREEN, AMBER, RED, INK, MUTED = "#1B7F3B", "#B26A00", "#C62828", "#252423", "#605E5C"

THEME_SRC = CHARLEY_DEV.parent.parent / "powerbi" / "theme.json"
THEME_NAME = "AffectGroupProjectReport"

SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"


# Card titles where the measure name alone misstates what a month selection does.
BILLED_PCT_TITLE = "Billed To Date % Of Contract (at period end)"
AR_TITLE = "AR Outstanding (current balance)"
CARD_TITLES = {
    "Total Billed": "Total Billed (selected period)",
    "Total Paid": "Total Paid (on invoices sent in period)",
    "Total Billed %": BILLED_PCT_TITLE,
    "AR Outstanding": AR_TITLE,
    "Percent Bought Out": "Percent Bought Out (last snapshot)",
    "Open Submittals": "Open Submittals (as of today)",
}


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


def lit(value: str) -> dict:
    """A string literal expression. Embedded quotes are doubled, not dropped.

    Several of the notes on these pages contain apostrophes ("the Excel's defects"). An
    unescaped one terminates the literal early and the property silently becomes garbage.
    """
    return {"expr": {"Literal": {"Value": "'" + value.replace("'", "''") + "'"}}}


# What a visual type is, in words, for the alt text sentence.
_SHAPE = {
    "card": "Card", "tableEx": "Table", "slicer": "Slicer", "barChart": "Stacked bar chart",
    "columnChart": "Column chart", "clusteredColumnChart": "Clustered column chart",
    "clusteredBarChart": "Clustered bar chart", "pivotTable": "Matrix",
    "lineChart": "Line chart", "multiRowCard": "Card",
}


def describe(vtype: str, title: str | None, projections: dict) -> str:
    """Alt text, generated from what the visual is actually bound to.

    Screen-reader users get the same information sighted readers get from the title and
    axes. Deriving it from the projections rather than hand-writing 101 strings means it
    cannot drift out of date when a field changes - a hand-written one silently would.
    """
    shape = _SHAPE.get(vtype, vtype)
    names = {role: [p.get("nativeQueryRef", "?") for p in items]
             for role, items in projections.items()}
    values = names.get("Values") or names.get("Y") or []
    category = names.get("Category") or [*names.get("Rows", []), *names.get("Columns", [])]
    if vtype == "slicer":
        return f"Slicer. Filters the report by {', '.join(values) or 'a field'}."
    parts = [f"{shape}. {title}." if title else f"{shape}."]
    if values:
        parts.append(f"Shows {', '.join(values)}")
        parts.append(f"by {', '.join(category)}." if category else "for the current selection.")
    return " ".join(parts)


# --------------------------------------------------------------------------
# Text fit
#
# Static geometry checks passed while the service clipped subtitles, card labels and table
# columns on nearly every page: a box that is on the canvas is not a box its words fit in.
# These estimate rendered size from character count and font size, so generation can size
# boxes and tests/test_report.py can fail a clipping regression offline.
#
# ponytail: average-glyph heuristic for Segoe UI, not font metrics. Wide glyphs (W, M, caps
# runs) render wider than estimated; measure with a real font if a string sits at the edge.
# --------------------------------------------------------------------------

PX = 4 / 3            # points -> CSS pixels
LINE = 1.33           # line height, in ems
TEXT_PAD = 8          # textbox vertical padding, total
BOX_PAD = 16          # visual container padding, total, each axis
TABLE_GUTTER = 24     # vertical scrollbar and outline a table must leave free
TABLE_FONT = 10       # table header and value font, pt (the theme's 9pt read as tiny at fit-to-page)
CARD_TITLE = 10       # card title font, pt
CARD_VALUE = 20       # numeric card callout, pt (the theme's 28pt pushed the label off the card)
CARD_TEXT_VALUE = 11  # text-valued card callout, pt, wrapped
SLICER_TITLE = 10

# Longest value a text measure can show, so a card is sized for its worst case rather
# than for whatever the data happened to say on the day it was checked. Pipeline Status
# is asserted against the DAX in the tests so this cannot drift from the model.
CARD_TEXT_SAMPLES = {
    "Pipeline Status": "Gold checked with warnings; source completeness unverified",
    "Snapshot History Note": "History starts 2026-01-31; earlier months are unavailable, not zero",
    "DQ Registers Awaiting Input": "8/8 registers empty in current filters; completeness unverified",
    "Last Checked Run": "2026-09-14 04:00",
    "Category Band": "Not measured",
}
NUMBER_SAMPLE = "$25,123,456"


def text_px(text: str, size: float, bold: bool = False) -> float:
    return len(text) * size * PX * (0.55 if bold else 0.52)


def line_px(size: float) -> float:
    return size * PX * LINE


def wrap_lines(text: str, size: float, width: float, bold: bool = False) -> int:
    """Lines a greedy word wrap needs. A single word wider than `width` still counts as one
    line - callers check the longest word separately, because a word cannot wrap."""
    lines, cur, space = 1, 0.0, size * PX * 0.28
    for word in text.split():
        wp = text_px(word, size, bold)
        if cur and cur + space + wp > width:
            lines, cur = lines + 1, wp
        else:
            cur += (space if cur else 0) + wp
    return lines


def longest_word_px(text: str, size: float, bold: bool = False) -> float:
    return max((text_px(w, size, bold) for w in text.split()), default=0.0)


def label(name: str) -> str:
    """ProjectKey -> Project Key. Table headers wrap at spaces only, so a camel-case column
    name is one unbreakable word that forces its column wide or clips."""
    out = ""
    for i, ch in enumerate(name):
        if i and ch.isupper() and (not name[i - 1].isupper()
                                   or (i + 1 < len(name) and name[i + 1].islower())):
            out += " "
        out += ch
    return out


def _num(value: float) -> dict:
    return {"expr": {"Literal": {"Value": f"{round(value)}D"}}}


_ON = {"expr": {"Literal": {"Value": "true"}}}
_OFF = {"expr": {"Literal": {"Value": "false"}}}
_WIDE = ("Name", "Title", "Subject", "Gate", "Label", "Response", "Category")


def column_need(header: str) -> float:
    """Minimum width: the longest header word, or a ten-character value, plus cell padding."""
    return math.ceil(max(longest_word_px(header, TABLE_FONT, bold=True),
                         text_px("2026-09-14", TABLE_FONT)) + 12)


def fit_table(v: dict) -> dict:
    """Readable headers, wrapped text, and explicit column widths that sum to the visual.

    The theme turns column auto-size off, and with no widths set Power BI falls back to a
    default per column - so a wide table ran off its right edge behind a scrollbar.
    """
    vis = v["visual"]
    state = vis["query"]["queryState"]
    fields = [p for role in ("Rows", "Values") for p in state.get(role, {}).get("projections", [])]
    for p in fields:
        if "Column" in p["field"]:
            p.setdefault("displayName", label(p["nativeQueryRef"]))
    size = _num(TABLE_FONT)
    objects = vis.setdefault("objects", {})
    objects["columnHeaders"] = [{"properties": {"fontSize": size, "wordWrap": _ON,
                                                "autoSizeColumnWidth": _OFF}}]
    objects["values"] = [{"properties": {"fontSize": size, "wordWrap": _ON}}]
    if vis["visualType"] == "pivotTable":
        objects["rowHeaders"] = [{"properties": {"fontSize": size, "wordWrap": _ON}}]
    # A matrix with a Columns role has one column per category value, not per field; its
    # widths cannot be known here, so only the fonts and wrapping apply.
    if "Columns" in state:
        return v
    # A matrix steps every Rows field into ONE row-header column, so they share a width.
    groups = table_columns(vis)
    names = [[p.get("displayName", p["nativeQueryRef"]) for p in g] for g in groups]
    needs = [max(column_need(n) for n in g) for g in names]
    weights = [3 if any(n.split()[-1] in _WIDE for n in g) else 1 for g in names]
    spare = max(v["position"]["width"] - TABLE_GUTTER - sum(needs), 0)
    objects["columnWidth"] = [
        {"properties": {"value": _num(math.floor(need + spare * wt / sum(weights)))},
         "selector": {"metadata": p["queryRef"]}}
        for g, need, wt in zip(groups, needs, weights) for p in g
    ]
    return v


def table_columns(vis: dict) -> list[list[dict]]:
    """Rendered columns of a table or matrix, each a list of the projections sharing it."""
    state = vis["query"]["queryState"]
    rows = state.get("Rows", {}).get("projections", [])
    values = state.get("Values", {}).get("projections", [])
    return ([rows] if rows else []) + [[p] for p in values]


def visual(page: str, key: str, vtype: str, x, y, w, h, projections: dict,
           title: str | None = None, tab: int | None = None,
           alt: str | None = None, sync: str | None = None,
           title_size: int = 12) -> dict:
    position = {"x": x, "y": y, "z": 0, "width": w, "height": h}
    if tab is not None:
        position["tabOrder"] = tab
    v = {
        "$schema": f"{SCHEMA}/visualContainer/1.0.0/schema.json",
        "name": oid(page, key),
        "position": position,
        "visual": {
            "visualType": vtype,
            "query": {"queryState": {
                role: {"projections": items} for role, items in projections.items()
            }},
            "drillFilterOtherVisuals": True,
        },
    }
    container: dict = {"general": [{"properties": {
        "altText": lit(alt or describe(vtype, title, projections)),
    }}]}
    if title:
        # Shown explicitly and allowed to wrap: two register tables rendered with no title
        # on canvas, and a long title on a narrow card truncated rather than wrapping.
        container["title"] = [{"properties": {
            "show": _ON,
            "text": lit(title),
            "fontColor": {"solid": {"color": lit(INK)}},
            "fontSize": _num(title_size),
            "titleWrap": _ON,
        }}]
    v["visual"]["visualContainerObjects"] = container
    # Slicers only. Keeps project and month selection together across every page, so a
    # reader who picks a job on Overview does not land on Financial showing all of them.
    if sync:
        v["visual"]["syncGroup"] = {"groupName": sync, "fieldChanges": False,
                                    "filterChanges": True}
    if vtype in ("tableEx", "pivotTable"):
        fit_table(v)
    return v


def textbox(page: str, key: str, text: str, x, y, w, h, size: int = 20,
            color: str = INK, tab: int | None = None) -> dict:
    # The header band is shared furniture, so its geometry is fixed once here: the title and
    # slicers share y 4-58, and the subtitle runs the full canvas width beneath both. It
    # used to stop at x=748 beside slicers that reached y=72, and wrapped out of its box.
    if key == "title":
        h = 44
    if y in (56, 58):
        x, y, w = 20, 60, 1240
    position = {"x": x, "y": y, "z": 0, "width": w, "height": h}
    if tab is not None:
        position["tabOrder"] = tab
    return {
        "$schema": f"{SCHEMA}/visualContainer/1.0.0/schema.json",
        "name": oid(page, key),
        "position": position,
        "visual": {
            "visualType": "textbox",
            "objects": {"general": [{"properties": {"paragraphs": [{
                "textRuns": [{"value": text, "textStyle": {
                    "fontSize": f"{size}pt", "color": color,
                    # Headings bold; explanatory notes regular, which also fits more per line.
                    "fontWeight": "bold" if size > 10 else "normal"}}]
            }]}}]},
            # Textboxes carry their own words, so the alt text IS the text. Repeating it
            # is what a screen reader needs; leaving it blank drops the sentence entirely.
            "visualContainerObjects": {"general": [{"properties": {"altText": lit(text)}}]},
        },
    }


def card(page: str, key: str, name: str, x, y, w=180, h=110, title: str | None = None) -> dict:
    """title overrides the measure name where the name alone would misstate the scope.

    The title carries the name, so the category label under the value is off: with both on,
    title + 28pt value + label did not fit a 100px card and the label was cut at the bottom.
    Text-valued measures get a smaller wrapped value instead of a truncated one.
    """
    v = visual(page, key, "card", x, y, w, h, {"Values": [measure(name)]},
               title=title or name, title_size=CARD_TITLE)
    text = name in CARD_TEXT_SAMPLES
    v["visual"]["objects"] = {
        "labels": [{"properties": {"fontSize": _num(CARD_TEXT_VALUE if text else CARD_VALUE)}}],
        "categoryLabels": [{"properties": {"show": _OFF}}],
        "wordWrap": [{"properties": {"show": _ON if text else _OFF}}],
    }
    return v


def top_n(v: dict, table: str, col: str, by: str, n: int) -> dict:
    """Visual-level Top N filter: the n values of table[col] ranked by measure `by`.

    For categories that run to hundreds of rows, where squeezing all of them into one chart
    left every bar a hairline. The title must say "top n" - a silent cut reads as the whole.
    """
    ref = {"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": col}}
    v["filterConfig"] = {"filters": [{
        "name": oid(v["name"], "topn", col),
        "field": {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": col}},
        "type": "TopN",
        "filter": {
            "Version": 2,
            "From": [
                {"Name": "subquery", "Type": 2, "Expression": {"Subquery": {"Query": {
                    "Version": 2,
                    "From": [{"Name": "d", "Entity": table, "Type": 0}],
                    "Select": [dict(ref, Name="field")],
                    "OrderBy": [{"Direction": 2, "Expression": {"Measure": {
                        "Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": by}}}],
                    "Top": n,
                }}}},
                {"Name": "d", "Entity": table, "Type": 0},
            ],
            "Where": [{"Condition": {"In": {
                "Expressions": [ref],
                "Table": {"SourceRef": {"Source": "subquery"}},
            }}}],
        },
        "howCreated": "User",
    }]}
    return v


def no_totals(v: dict) -> dict:
    """Turn off the default totals row. Day counts, ordinals and per-row scores summed in a
    totals row read as real figures ("Total 18,402" days) - there is no meaningful total."""
    off = {"expr": {"Literal": {"Value": "false"}}}
    objects = v["visual"].setdefault("objects", {})
    if v["visual"]["visualType"] == "pivotTable":
        objects["subTotals"] = [{"properties": {"rowSubtotals": off, "columnSubtotals": off}}]
    else:
        objects["total"] = [{"properties": {"totals": off}}]
    return v


def keep_true(v: dict, table: str, col: str) -> dict:
    """Visual-level filter: only rows where table[col] is TRUE."""
    v["filterConfig"] = {"filters": [{
        "name": oid(v["name"], table, col),
        "field": {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": col}},
        "type": "Categorical",
        "filter": {
            "Version": 2,
            "From": [{"Name": "t", "Entity": table, "Type": 0}],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": col}}],
                "Values": [[{"Literal": {"Value": "true"}}]],
            }}}],
        },
        "howCreated": "User",
    }]}
    return v


def sort_desc(v: dict, field: dict) -> dict:
    """Default sort, descending, by a column() or measure() projection."""
    v["visual"]["query"]["sortDefinition"] = {
        "sort": [{"field": field["field"], "direction": "Descending"}],
        "isDefaultSort": True,
    }
    return v


def chrome(page: str, slicers: bool = True) -> list[dict]:
    """Slicers and footer, identical on every page.

    Two things the report did not have. There was no month slicer ANYWHERE, so a report
    called "Monthly" could not be set to a month - it always showed all of time. And each
    page carried its own project slicer or none at all, so a selection did not survive a
    page change.

    The footer states the reporting period and when the data was built, so a page printed
    to PDF says what it is a snapshot of. The workbook could not: it used TODAY(), and a
    saved copy silently re-dated itself every time anyone opened it.
    """
    items = [
        # [Pipeline Status] is here rather than only on the Data Quality page. It
        # answers "are these numbers from last night or from three weeks ago", which is a
        # question about every page, not about the DQ page - and the failure it guards
        # against went unnoticed for a month, with the nightly pipeline failing every
        # night while reporting itself as enabled. Text, never colour alone.
        # Full width, one third per field: at 540 wide the status sentence truncated and
        # the label row under each value was cut off at the bottom.
        visual(page, "footer", "multiRowCard", 20, FOOTER_Y, 1240, 720 - FOOTER_Y - 2,
               {"Values": [measure("Report Month Label"), measure("Last Refresh"),
                           measure("Pipeline Status")]},
               tab=99,
               alt="Report footer. States the reporting period shown, the time the "
                   "underlying data was last built, and whether the last checked pipeline "
                   "run passed its gold checks."),
    ]
    items[0]["visual"]["objects"] = {
        "dataLabels": [{"properties": {"fontSize": _num(FOOTER_VALUE)}}],
        "categoryLabels": [{"properties": {"fontSize": _num(FOOTER_LABEL)}}],
    }
    # A drill-through page receives its project from the caller. Putting a project slicer
    # on it would let a reader change that selection out from under the filter they
    # arrived by, so the page would answer a different question than the one asked.
    if slicers:
        items = [
            visual(page, "slicer_project", "slicer", 768, 4, 240, 54,
                   {"Values": [column("dim_Project", "ProjectName")]},
                   title="Project", tab=1, sync="project", title_size=SLICER_TITLE),
            visual(page, "slicer_month", "slicer", 1020, 4, 240, 54,
                   {"Values": [column("dim_Date", "MonthYear")]},
                   title="Month", tab=2, sync="month", title_size=SLICER_TITLE),
        ] + items
        # Dropdown, and no field header under the title. A list slicer in a 58px box with
        # both a title and a header had room for one item, which was "(Blank)".
        for s in items[:2]:
            s["visual"]["objects"] = {
                "data": [{"properties": {"mode": {"expr": {"Literal": {"Value": "'Dropdown'"}}}}}],
                "header": [{"properties": {"show": _OFF}}],
            }
    return items


FOOTER_Y = 662     # everything else on a page ends at or above this line
FOOTER_VALUE = 9   # pt
FOOTER_LABEL = 8   # pt
SLICER_BOX = 28    # dropdown control height, px


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------


def page_portfolio() -> tuple[str, list[dict]]:
    """Every project at once - the view leadership never had.

    The Excel is one workbook per job, so a portfolio question ("which of our jobs is in
    trouble") could only be answered by opening them all and comparing by eye. Every page
    of this report until now inherited that shape: one project behind a slicer.

    The heatmap is the point. Nine categories across, one row per project, scored by the
    same SWITCH that drives the headline number - so the answer to "which job, and what
    about it" is one screen rather than seventeen files.

    Like every page it carries the synced project and month slicers, so a project chosen
    elsewhere narrows it too. The subtitle says so rather than claiming "all projects".
    """
    p = "portfolio"
    return p, [
        textbox(p, "title", "Portfolio", 20, 16, 700, 44),
        textbox(p, "sub",
                "Every project in the current slicers - clear the project slicer to compare them "
                "all. Scores use the Scorecard page's weights and bands; no data reads as blank, "
                "never zero. AR is today's balance on invoices in the selected period.",
                20, 58, 1240, 44, size=10, color=MUTED),

        card(p, "pf_projects", "Projects Reporting", 20, 112, 228, 96),
        card(p, "pf_contract", "Current Contract", 268, 112, 228, 96),
        card(p, "pf_billed", "Total Billed %", 516, 112, 228, 96, title=BILLED_PCT_TITLE),
        card(p, "pf_ar", "AR Outstanding", 764, 112, 228, 96, title=AR_TITLE),
        card(p, "pf_risk", "Projects At Risk", 1012, 112, 228, 96),

        # THE HEATMAP. A matrix rather than a chart because the cell values are ordinal
        # scores (0/2/3) against two categorical axes - there is no magnitude to compare
        # lengths of, and conditional formatting carries the reading.
        no_totals(visual(p, "pf_heatmap", "pivotTable", 20, 220, 720, 230,
               {"Rows": [column("dim_Project", "ProjectName")],
                "Columns": [column("dim_ScorecardWeight", "CategoryName")],
                "Values": [measure("Category Score")]},
               title="Scorecard by project and category (0-3, blank = not measured)",
               alt="Matrix. One row per project, one column per scorecard category, "
                   "showing each category score out of 3. Blank cells are categories with "
                   "no data rather than a score of zero.")),

        # Contract, billed and paid together per job: the gap between the bars IS the
        # exposure, and reading three separate cards never showed it.
        visual(p, "pf_money", "clusteredColumnChart", 760, 220, 500, 230,
               {"Category": [column("dim_Project", "ProjectName")],
                "Y": [measure("Current Contract"), measure("Total Billed"),
                      measure("Total Paid")]},
               title="Contract, billed and paid by project"),

        # Ranked, and tall enough for eight bars before scrolling: at 128px each of these
        # three showed two projects and hid the rest behind a scrollbar.
        sort_desc(visual(p, "pf_ar_rank", "barChart", 20, 462, 400, 194,
               {"Category": [column("dim_Project", "ProjectName")],
                "Y": [measure("AR Outstanding")]},
               title="AR outstanding (current balance), ranked"), measure("AR Outstanding")),

        # Coverage sits on the portfolio page too, because the honest reading of any
        # cross-project comparison is "and how much of each score is real".
        sort_desc(visual(p, "pf_coverage", "barChart", 436, 462, 400, 194,
               {"Category": [column("dim_Project", "ProjectName")],
                "Y": [measure("Scorecard Coverage %")]},
               title="Scorecard coverage by project"), measure("Scorecard Coverage %")),

        # Insurance exposure belongs at portfolio level, not only on the Insurance page:
        # "which jobs are running subs with no certificate on file" is a question about
        # all of them at once. [Vendors Without Insurance] is a set difference (EXCEPT)
        # over two key lists, NOT a RELATEDTABLE - there is no relationship from
        # bridge_ProjectVendor to fct_VendorInsurance, both hang off dim_Vendor, and a
        # RELATEDTABLE version would deploy perfectly cleanly and then fail at render.
        sort_desc(visual(p, "pf_uninsured", "barChart", 852, 462, 408, 194,
               {"Category": [column("dim_Project", "ProjectName")],
                "Y": [measure("Vendors Without Insurance")]},
               title="Vendors with no certificate on file, by project"),
            measure("Vendors Without Insurance")),
    ]


def page_overview() -> tuple[str, list[dict]]:
    """The one-page replacement, and the page that gets exported to PDF and circulated.

    The project slicer that used to sit at (20,80) has moved into the shared chrome with
    the new month slicer, which frees the whole left column - so the card grid is five
    across instead of four squeezed to the right.
    """
    p = "overview"
    # Five columns, 228 wide on a 248 pitch: 20 .. 1240. Two rows.
    xs = [20, 268, 516, 764, 1012]
    row1 = ["Current Contract", "Total Billed", "Total Billed %", "Total Paid",
            "AR Outstanding"]
    row2 = ["Contract Growth %", "Percent Bought Out", "Pending Change Orders",
            "Open Submittals", "Critical Milestones"]
    cards = [card(p, f"c_r1_{i}", name, xs[i], 90, w=228, title=CARD_TITLES.get(name))
             for i, name in enumerate(row1)]
    cards += [card(p, f"c_r2_{i}", name, xs[i], 216, w=228, title=CARD_TITLES.get(name))
              for i, name in enumerate(row2)]
    trend = visual(p, "billed_trend", "columnChart", 20, 346, 640, 296,
                   {"Category": [column("dim_Date", "MonthYear")],
                    "Y": [measure("Total Billed")]},
                   title="Billed by month")
    # CLUSTERED. barChart is the stacked variant, which drew budget + spend as one bar.
    budget = visual(p, "budget_by_code", "clusteredBarChart", 680, 346, 580, 296,
                    {"Category": [column("dim_CostCode", "Division")],
                     "Y": [measure("Budget"), measure("Spent To Date")]},
                    title="Budget vs spent by division (last budget snapshot)")
    return p, [
        textbox(p, "title", "Monthly Progress Report", 20, 16, 700, 44),
        textbox(p, "sub", "Replaces the Excel Monthly Progress Report. Budget figures are the last "
                "snapshot; open counts are as of today, grouped by creation month when a month is selected.",
                20, 58, 1240, 26, size=10, color=MUTED),
        *cards, trend, budget,
    ]


def page_financial() -> tuple[str, list[dict]]:
    p = "financial"
    return p, [
        textbox(p, "title", "Financial", 20, 16, 600, 44),
        card(p, "f_budget", "Budget", 20, 80, title="Budget (last snapshot)"),
        card(p, "f_forecast", "Forecast", 216, 80, title="Forecast (last snapshot)"),
        card(p, "f_committed", "Committed", 412, 80, title="Committed (last snapshot)"),
        card(p, "f_spent", "Spent To Date", 608, 80, title="Spent To Date (last snapshot)"),
        card(p, "f_ctc", "Cost To Complete", 804, 80, title="Cost To Complete (last snapshot)"),
        card(p, "f_var", "Budget Remaining", 1000, 80, title="Budget Remaining (last snapshot)"),
        # A matrix rather than a flat table: cost codes roll up by division, so a reader
        # starts at the level they care about and expands into the detail rather than
        # scrolling 4,837 rows looking for it.
        visual(p, "budget_table", "pivotTable", 20, 210, 780, 440,
               {"Rows": [column("dim_CostCode", "Division"),
                         column("dim_CostCode", "CostCode"),
                         column("fct_BudgetLine", "Category"),
                         column("fct_BudgetLine", "ProjectKey"),
                         column("fct_BudgetLine", "BudgetLineID")],
                "Values": [measure("Budget"), measure("Spent To Date"),
                           measure("Budget Remaining"), measure("Budget Remaining %"),
                           measure("Budget Status"), measure("Forecast"),
                           measure("Forecast Variance"), measure("Forecast Status")]},
               title="Budget by cost code (last snapshot) - expand for category and source line",
               alt="Matrix. Budget remaining is budget less spend to date and Budget Status describes that spend "
                   "comparison; Forecast Variance is budget less forecast and Forecast Status bands it the same way. Expand through division, cost code, category, project ID and source budget line ID."),
        visual(p, "co_by_status", "clusteredColumnChart", 820, 210, 440, 210,
               {"Category": [column("fct_ChangeOrder", "StatusLabel")],
                "Y": [measure("Change Order Amount")]},
               title="Change orders by status"),
        # THE S-CURVE. Cumulative billing against the contract line is the chart a GC reads
        # to answer "are we billing at the pace we said we would" - and it is the one thing
        # a single-month snapshot structurally cannot show, no matter how many tiles it has.
        #
        # Built on the period movement accumulated over time, NOT on the running-balance
        # column, which is restated each period and would double-count.
        visual(p, "s_curve", "lineChart", 820, 440, 440, 210,
               {"Category": [column("dim_Date", "MonthYear")],
                "Y": [measure("Billed Cumulative"), measure("Current Contract")]},
               title="Billing S-curve vs contract",
               alt="Line chart. Cumulative amount billed by month against the current "
                   "contract value, showing billing pace over the life of the job."),
    ]


def page_schedule_quality() -> tuple[str, list[dict]]:
    p = "schedule"
    items = [
        textbox(p, "title", "Schedule & Quality", 20, 16, 600, 44),
        # Open/overdue flags are as of TODAY; the month slicer groups by start or creation
        # month, so the titles say "today" rather than implying a month-end backlog.
        card(p, "s_crit", "Critical Milestones", 20, 80),
        card(p, "s_overdue", "Overdue Milestones", 216, 80, title="Overdue Milestones (as of today)"),
        card(p, "s_perf", "Milestones Overdue %", 412, 80, title="Milestones Overdue % (as of today)"),
        card(p, "s_prog", "Avg Milestone Progress", 608, 80),
        card(p, "s_open", "Open Submittals", 804, 80, title="Open Submittals (as of today)"),
        card(p, "s_pastdue", "Open Submittals Past Due", 1000, 80, title="Submittals Past Due (as of today)"),
        # THE TIMELINE. report-spec.md calls this the single biggest visual gain over the
        # Excel, which could not draw one at all. Power BI has no native Gantt, so this is
        # the standard stacked-bar construction: an invisible bar to the milestone's start,
        # then a visible bar for its duration, both measured in days from the earliest
        # start on screen.
        #
        # WHAT THIS CANNOT SHOW: drift against a baseline. fct_Milestone carries
        # CurrentStart/CurrentFinish only - there is no baseline and no actual anywhere in
        # gold, because Outbuild is not supplying them. A baseline-vs-current timeline is
        # the version Affect actually wants, and it needs that data first.
        visual(p, "gantt", "barChart", 20, 210, 740, 290,
               {"Category": [dict(column("fct_Milestone", c), active=True)
                             for c in ("ProjectKey", "ActivityKey", "MilestoneName")],
                "Y": [measure("Milestone Offset Days"),
                      measure("Milestone Duration Days")]},
               title="Current schedule - elapsed days from earliest valid start",
               alt="Stacked bar timeline. One bar per milestone, positioned by its start "
                   "date and sized by its duration in days, relative to the earliest "
                   "valid milestone start currently shown. Missing or inverted dates are "
                   "omitted from the bars and retained in the table. Baseline variance is unavailable."),
        no_totals(visual(p, "milestones", "tableEx", 20, 508, 740, 150,
               {"Values": [column("fct_Milestone", "ProjectKey"),
                           column("fct_Milestone", "ActivityKey"),
                           column("fct_Milestone", "MilestoneName"),
                           column("fct_Milestone", "CurrentStart"),
                           column("fct_Milestone", "CurrentFinish"),
                           column("fct_Milestone", "PercentComplete"),
                           column("fct_Milestone", "StatusLabel"),
                           column("fct_Milestone", "HasDateInversion")]},
               title="Critical path milestones (Outbuild)")),
        # The workbook's one native chart, rebuilt - and now drillable to the items.
        visual(p, "submittals_by_status", "barChart", 780, 210, 480, 250,
               {"Category": [column("fct_RfiSubmittal", "StatusLabel")],
                "Y": [measure("Open Submittals")]},
               title="Open submittals by status (as of today)"),
        # SAVED HISTORY, not current state regrouped. A backlog chart built from today's
        # facts rewrites every past month whenever an item closes; this one reads what the
        # nightly run saved at each month end. The note names where history starts, because
        # a month before it is unavailable - an empty point, never a zero.
        card(p, "snapshot_note", "Snapshot History Note", 780, 468, 480, 76),
        visual(p, "backlog_month_end", "lineChart", 780, 552, 480, 104,
               {"Category": [column("dim_Date", "MonthYear")],
                "Y": [measure("Open Submittals (Month End)"),
                      measure("Open Submittals Past Due (Month End)")]},
               title="Submittal backlog at month end (saved history)",
               alt="Line chart. Open and past-due submittals as saved at the last nightly "
                   "capture of each month. Months before history starts have no value, "
                   "not zero."),
    ]
    timeline = next(v["visual"] for v in items if v["name"] == oid(p, "gantt"))
    timeline["objects"] = {"dataPoint": [{
        "selector": {"metadata": "_Measures.Milestone Offset Days"},
        "properties": {"fillTransparency": {"expr": {"Literal": {"Value": "100D"}}}},
    }]}
    return p, items


def page_data_quality() -> tuple[str, list[dict]]:
    p = "dataquality"
    return p, [
        textbox(p, "title", "Data Quality", 20, 16, 600, 44),
        textbox(p, "note",
                "Unmatched invoice count and billed amount cover all projects for the selected month. "
                "Other visuals follow the project selection. Invoice identifiers link amounts to Sage. "
                "Checks passed does not establish complete source coverage.",
                20, 56, 1240, 44, size=10, color=MUTED),

        # FIRST band on the page, deliberately. Every other number here describes the data;
        # this one says whether the data arrived at all. A DQ page full of green checks on
        # three-week-old numbers is worse than no DQ page.
        textbox(p, "hb_h", "Pipeline", 20, 106, 300, 32, size=13),
        card(p, "dq_hb_status", "Pipeline Status", 20, 140, 300, 100),
        card(p, "dq_hb_hours", "Hours Since Last Checked Run", 336, 140, 260, 100),
        card(p, "dq_hb_last", "Last Checked Run", 612, 140, 260, 100),
        card(p, "dq_hb_block", "Blocking Violations Last Run", 888, 140, 260, 100),

        card(p, "dq_cross", "DQ Projects Without Crosswalk", 20, 248, 228, 100),
        card(p, "dq_codes", "DQ Cost Codes Not In Source", 268, 248, 228, 100),
        card(p, "dq_inv", "DQ Milestones With Inverted Dates", 516, 248, 228, 100),
        card(p, "dq_ar", "DQ Unmatched Invoices", 764, 248, 228, 100),
        card(p, "dq_ar_amount", "Unmatched Billed Amount - All Projects", 1012, 248, 248, 100),
        visual(p, "no_crosswalk", "tableEx", 20, 360, 360, 300,
               {"Values": [column("dim_Project", "ProjectKey"),
                           column("dim_Project", "ProjectName"),
                           column("dim_Project", "IsInCrosswalk"),
                           column("dim_Project", "HasPrimeContract")]},
               title="Projects - crosswalk and contract coverage"),
        visual(p, "unmatched_ar", "tableEx", 396, 360, 460, 300,
               {"Values": [column("fct_Invoice", "InvoiceID"),
                           column("fct_Invoice", "InvoiceNumber"),
                           column("fct_Invoice", "SageJobNumber"),
                           column("fct_Invoice", "HasUnmatchedProject"),
                           measure("Total Billed")]},
               title="AR invoice trace - selected project and month"),
        # The whole gap register, one row per category. Gaps with no project (rejected
        # source rows, expired certificates, empty registers) drop out when a project is
        # selected, which the alt text says so it is not read as "no gaps".
        visual(p, "data_gaps", "tableEx", 872, 360, 388, 300,
               {"Values": [column("dq_DataGap", "GapCategory"),
                           measure("Data Gaps"), measure("Data Gap Amount")]},
               title="Data gap register by category",
               alt="Table. Count of known data gaps and the money they carry, by gap "
                   "category. Gaps not tied to a project are hidden while a project is "
                   "selected."),
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
        # With no single project selected the drivers pool across the portfolio, so the
        # headline is a portfolio blend - the title says so.
        card(p, "sc_total", "Project Scorecard", 20, 110, 240, 130,
             title="Project Scorecard (portfolio blend unless one project is selected)"),
        card(p, "sc_cov", "Scorecard Coverage %", 276, 110, 240, 130),
        card(p, "sc_measured", "Project Scorecard (Measured Only)", 532, 110, 300, 130),
        card(p, "sc_client", "Client Satisfaction", 848, 110, 240, 130),
        # THE AUDIT TABLE. This replaces two disconnected tables - one listing weights, the
        # other listing raw band rows keyed by CategoryKey, an integer surrogate that was
        # being rendered to readers. Neither could be read against the other, so the score
        # was a number you either believed or did not.
        #
        # One row per category, showing the score, the band it landed in, the weight, and
        # what it contributed. The contribution column sums to [Project Scorecard] exactly,
        # because it is driven by the same SWITCH the headline measure uses. This is the
        # view in which the workbook's three dead bands would have been obvious.
        visual(p, "audit", "tableEx", 20, 260, 700, 300,
               {"Values": [column("dim_ScorecardWeight", "CategoryName"),
                           measure("Category Score"),
                           measure("Category Band"),
                           column("dim_ScorecardWeight", "Weight"),
                           measure("Category Weighted")]},
               title="How the score is built - category, score, band, weight, contribution",
               alt="Table. One row per scorecard category showing its score out of 3, the "
                   "band the driver fell into, the category weight, and the weighted "
                   "contribution to the total. Categories with no data read Not measured."),
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
                "The workbook's 0.59 is not a reliable comparison: its schedule bands used "
                "whole numbers instead of percentages, and its completion-variance band "
                "never matched. Those errors happened to cancel in the sample project. "
                "This report uses corrected bands. Review category scores and missing "
                "inputs before comparing results with earlier workbook reports.",
                # Ends at y=660, above the footer band, so it can run the full width
                # of the canvas. It previously ran to 742 on a 720-high page, and then to
                # x=940, which the widened footer would have covered.
                20, 568, 700, 92, size=10, color=MUTED),

        # The band table stays, as the reference behind the Band column - but keyed by the
        # category NAME rather than the surrogate integer the previous version showed.
        # The name is a column on the band table itself, not reached through a
        # relationship; see the note in deploy_model.RELATIONSHIPS for why.
        # Thresholds shown, so the band behind a score can be read, not just its label.
        no_totals(visual(p, "bands", "tableEx", 740, 260, 520, 390,
               {"Values": [column("dim_ScorecardBand", "CategoryName"),
                           column("dim_ScorecardBand", "Score"),
                           column("dim_ScorecardBand", "BandLabel"),
                           column("dim_ScorecardBand", "MinValue"),
                           column("dim_ScorecardBand", "MaxValue"),
                           column("dim_ScorecardBand", "MatchValue")]},
               title="Scoring bands - corrected (defects #1a-#1c)")),
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
                "Missing Sage coverage means project revenue is not verified. A blank or zero "
                "does not establish that nothing was billed. Review the source mappings below "
                "and the unmatched invoices on Data Quality.",
                20, 56, 1100, 44, size=10, color=MUTED),

        # Counts first, so the shape of the problem is legible before the detail.
        card(p, "cov_full", "Projects Fully Mapped", 20, 116, 260, 120),
        card(p, "cov_nosage", "Projects Missing From Sage", 296, 116, 260, 120),
        card(p, "cov_nooutbuild", "Projects Missing From Outbuild", 572, 116, 260, 120),
        card(p, "cov_pct", "Source Coverage %", 848, 116, 260, 120),

        visual(p, "cov_status", "columnChart", 20, 252, 540, 200,
               {"Category": [column("dim_ProjectCrosswalk", "CoverageStatus")],
                "Y": [measure("Projects In Coverage")]},
               title="Projects by coverage status"),

        # The list is the actionable artifact: it names the projects to go fix.
        visual(p, "cov_detail", "tableEx", 580, 252, 680, 200,
               {"Values": [column("dim_ProjectCrosswalk", "ProjectName"),
                           column("dim_ProjectCrosswalk", "CoverageStatus"),
                           column("dim_ProjectCrosswalk", "SageProjectId"),
                           column("dim_ProjectCrosswalk", "OutbuildProjectId")]},
               title="Every project, and what it is missing"),

        textbox(p, "vendornote",
                "An unmatched vendor may be outside the ERP scope or may need a mapping. "
                "Review commitments and payments before deciding; an absent Sage id alone "
                "does not establish the reason. Crosswalk tables are company-wide and ignore both slicers.",
                20, 456, 1240, 44, size=10, color=MUTED),
        visual(p, "vendor_cov", "tableEx", 20, 508, 620, 150,
               {"Values": [column("dim_VendorCrosswalk", "VendorName"),
                           column("dim_VendorCrosswalk", "IsInSage"),
                           column("dim_VendorCrosswalk", "HasNameMismatch")]},
               title="Vendor mapping - Procore to Sage"),
        visual(p, "costcode_cov", "tableEx", 660, 508, 600, 150,
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

        card(p, "pd_contract", "Current Contract", 20, 100, 195, 110),
        card(p, "pd_billed", "Total Billed", 229, 100, 195, 110),
        card(p, "pd_paid", "Total Paid", 438, 100, 195, 110),
        card(p, "pd_ar", "AR Outstanding", 647, 100, 195, 110, title=AR_TITLE),
        card(p, "pd_score", "Project Scorecard", 856, 100, 195, 110),
        # Coverage beside the score: a thinly instrumented project must not read as unhealthy.
        card(p, "pd_cov", "Scorecard Coverage %", 1065, 100, 195, 110),

        # Budget by cost code: the line-item grain the portfolio pages roll up.
        visual(p, "pd_budget", "tableEx", 20, 228, 620, 232,
               {"Values": [column("dim_CostCode", "CostCode"),
                           column("dim_CostCode", "Division"),
                           measure("Budget"),
                           measure("Spent To Date"),
                           measure("Budget Remaining")]},
               title="Budget by cost code"),

        visual(p, "pd_co", "tableEx", 660, 228, 600, 232,
               {"Values": [column("fct_ChangeOrder", "ChangeOrderNumber"),
                           # StatusLabel, not Status. The column has never been called
                           # Status in gold, so this visual has been broken since it was
                           # written - see test_report_refs below, which now catches it.
                           column("fct_ChangeOrder", "StatusLabel"),
                           # Amount for every CO. Approved-only left pending rows blank, and a
                           # table drops all-blank rows, so pending COs vanished.
                           measure("Change Order Amount"),
                           measure("Approved Change Orders")]},
               title="Change orders"),

        visual(p, "pd_items", "tableEx", 20, 474, 620, 182,
               {"Values": [column("fct_RfiSubmittal", "ItemType"),
                           column("fct_RfiSubmittal", "ItemNumber"),
                           column("fct_RfiSubmittal", "Subject"),
                           column("fct_RfiSubmittal", "StatusLabel")]},
               title="RFIs and submittals"),

        visual(p, "pd_milestones", "tableEx", 660, 474, 600, 182,
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


def page_safety_quality() -> tuple[str, list[dict]]:
    """SAFETY!Table1 and QUALITY!Table18 - both typed by hand every month today.

    Every number here now comes from Procore records rather than a person's memory of them,
    which also retires workbook defect #2: QUALITY!D5:D6 read SAFETY orientations, so the
    quality tab has been reporting a safety number. A count sourced from the observation
    records cannot make that mistake.
    """
    p = "safetyquality"
    return p, [
        textbox(p, "title", "Safety & Quality", 20, 16, 600, 44),
        textbox(p, "note",
                "Every figure is counted from Procore records - observations, punch items, "
                "incidents and manpower logs - rather than typed each month. Open and past-due "
                "counts are as of today; a month selection groups them by creation month.",
                20, 56, 1240, 44, size=10, color=MUTED),

        # SAFETY. Hours first: an incident count without hours cannot be compared between a
        # 12-person job and a 200-person one, which is the entire reason TRIR exists.
        textbox(p, "safety_h", "Safety", 20, 106, 300, 32, size=13),
        card(p, "sq_hours", "Hours Worked", 20, 140, 250, 110),
        card(p, "sq_rec", "Recordable Incidents", 286, 140, 250, 110),

        # QUALITY.
        textbox(p, "quality_h", "Quality", 560, 106, 300, 32, size=13),
        card(p, "sq_obs", "Observations", 560, 140, 230, 110),
        card(p, "sq_punch", "Punchlist Items", 806, 140, 230, 110),
        card(p, "sq_open", "Open Quality Items", 1052, 140, 208, 110),

        # Open and past due are the actionable pair - the second is a subset of the first,
        # and the gap between them is what a PM does something about this week.
        card(p, "sq_pastdue", "Quality Items Past Due", 20, 262, 250, 100),
        card(p, "sq_avgpast", "Avg Days Past Due", 286, 262, 250, 100),
        card(p, "sq_avgclose", "Avg Observation Days To Close", 552, 262, 250, 100),

        visual(p, "sq_by_type", "columnChart", 20, 382, 520, 274,
               {"Category": [column("fct_QualityItem", "ItemType")],
                "Y": [measure("Open Quality Items")]},
               title="Open items by type"),

        visual(p, "sq_by_trade", "barChart", 560, 382, 340, 274,
               {"Category": [column("fct_QualityItem", "Trade")],
                "Y": [measure("Open Quality Items")]},
               title="Open items by trade"),

        # The list a PM actually works from: what is late, and how late.
        # Filtered to past-due items and sorted latest first, which is what the title says.
        sort_desc(keep_true(no_totals(visual(p, "sq_overdue", "tableEx", 920, 382, 340, 274,
               {"Values": [column("fct_QualityItem", "Title"),
                           column("fct_QualityItem", "AssignedTo"),
                           column("fct_QualityItem", "DaysPastDue")]},
               title="Past due, by days late")), "fct_QualityItem", "IsPastDue"),
            column("fct_QualityItem", "DaysPastDue")),
    ]



def page_billing() -> tuple[str, list[dict]]:
    """Progress billing and retainage - neither of which exists in the workbook.

    Retainage has no cell anywhere in the spreadsheet and no column in Sage that carries
    it: the invoice header is zero across all 940 rows. It is held in Procore progress
    billing, and this is the first time Affect can see it.

    The layout puts the net position first because that is the one number a GC acts on -
    owner retainage is cash owed to Affect, sub retainage is cash Affect is holding, and
    only the difference tells you which way the money is flowing.
    """
    p = "billing"
    return p, [
        textbox(p, "title", "Billing & Retainage", 20, 16, 600, 44),
        textbox(p, "note",
                "Balances are CURRENT, from the latest issued billing per contract, whatever "
                "month is selected - not a total of every period. Owner billed (selected "
                "period) is the sum of payments due in the selected months; all months if none. "
                "Drafts are excluded and counted separately.",
                20, 56, 1240, 44, size=10, color=MUTED),

        # Retainage first. This is the new information on the page.
        textbox(p, "ret_h", "Retainage", 20, 106, 300, 32, size=13),
        card(p, "b_net", "Net Retainage Position", 20, 140, 260, 110,
             title="Net Retainage (owner-held minus sub-held; negative = Affect holds more)"),
        card(p, "b_ret_own", "Retainage Held Owner", 296, 140, 240, 110),
        card(p, "b_ret_sub", "Retainage Held Sub", 552, 140, 240, 110),

        textbox(p, "bill_h", "Owner billing", 820, 106, 300, 32, size=13),
        card(p, "b_contract", "Owner Contract Sum", 820, 140, 220, 110),
        card(p, "b_todate", "Owner Billed To Date", 1056, 140, 204, 110),

        card(p, "b_balance", "Balance To Finish", 20, 262, 260, 100),
        # Shown beside the cumulative figure deliberately: this is the only sum-safe money
        # column on the fact, and the gap between the two IS the retainage above. A reader
        # who spots that has understood the table.
        card(p, "b_period", "Billed This Period", 296, 262, 240, 100,
             title="Owner billed (net of retainage)"),
        card(p, "b_draft", "Draft Billings", 552, 262, 240, 100),

        # Billing over time uses the SUM-SAFE measure. A cumulative column on a trend chart
        # would slope upward regardless of activity, which looks like progress and is not.
        visual(p, "b_trend", "columnChart", 20, 382, 620, 274,
               {"Category": [column("dim_Date", "MonthStart")],
                "Y": [measure("Billed This Period")]},
               title="Billed by month (period movement, not cumulative)"),

        # CLUSTERED: owner and sub retainage flow in opposite directions; stacking summed them.
        visual(p, "b_by_project", "clusteredBarChart", 660, 382, 600, 274,
               {"Category": [column("dim_Project", "ProjectName")],
                "Y": [measure("Retainage Held Owner"),
                      measure("Retainage Held Sub")]},
               title="Retainage held by project"),
    ]


def page_costs_vendors() -> tuple[str, list[dict]]:
    """Direct costs and the vendor list - deliverable D8, plus the ERP reconciliation gap.

    Self-performed labour appears in no other feed: not in a commitment, not in a
    requisition, not in the budget's committed column. A cost-to-date built without it
    understates every job Affect's own crews work on, and understates it in the
    comfortable direction - the job looks more profitable than it is.
    """
    p = "costsvendors"
    return p, [
        textbox(p, "title", "Direct Costs & Vendors", 20, 16, 600, 44),
        textbox(p, "note",
                "Direct costs sum at any grouping. The vendor list is Procore prequalification, "
                "not current insurance. Vendor figures and the Sage AP table are not "
                "month-filtered. Sage AP starts 2025-03-11 and lags or leads Procore, so it "
                "checks Spent To Date and is never added to it.",
                20, 56, 1240, 44, size=10, color=MUTED),

        # Six across. The vendor/cost-code bridge added a sixth headline number to a row
        # that was already full, so the whole row narrows rather than the new one wrapping
        # to a band of its own.
        card(p, "c_direct", "Direct Costs", 20, 108, 195, 92),
        card(p, "c_labour", "Self Performed Labour", 229, 108, 195, 92),
        card(p, "c_unapproved", "Unapproved Direct Costs", 438, 108, 195, 92),
        card(p, "c_vendors", "Vendors On Project", 647, 108, 195, 92),
        # Half of Affect's vendors are not written back to Sage. That is a reconciliation
        # gap - cost exists in one system and not the other - and nothing surfaced it
        # before this card.
        card(p, "c_missing", "Vendors Missing From ERP", 856, 108, 195, 92),
        # Committed and actual are shown side by side and NEVER summed: committed is what
        # was promised, actual is what has gone out, and adding them counts the same work
        # twice. The gap between them is work in progress.
        card(p, "c_committed", "Vendor Committed", 1065, 108, 195, 92),

        visual(p, "c_by_type", "columnChart", 20, 208, 297, 130,
               {"Category": [column("fct_DirectCost", "CostCategory")],
                "Y": [measure("Direct Costs")]},
               title="Direct cost by category"),

        visual(p, "c_trend", "columnChart", 333, 208, 297, 130,
               {"Category": [column("dim_Date", "MonthStart")],
                "Y": [measure("Direct Costs")]},
               title="Direct cost by month"),

        # Spend by vendor AND cost code - the linkage that exists in no single Procore
        # object, and that nothing in the current reporting can slice.
        # Top 10 by commitment. Every cost code at once left each bar a hairline; the
        # title names the cut so it is not read as the whole list.
        sort_desc(top_n(visual(p, "c_topcodes", "clusteredBarChart", 646, 208, 614, 180,
               {"Category": [column("bridge_VendorCostCode", "CostCodeName")],
                "Y": [measure("Vendor Committed"), measure("Vendor Spend")]},
               title="Top 10 cost codes by committed: committed and actual"),
            "bridge_VendorCostCode", "CostCodeName", "Vendor Committed", 10),
            measure("Vendor Committed")),

        # pivotTable is the PBIR matrix type. No AmountType on columns: the two measures
        # already split it, and pivoting by it left half the cells structurally blank.
        visual(p, "c_matrix", "pivotTable", 20, 350, 610, 150,
               {"Rows": [column("bridge_VendorCostCode", "VendorName")],
                "Values": [measure("Vendor Committed"), measure("Vendor Spend")]},
               title="Vendor: committed vs actual",
               alt="Matrix. One row per vendor showing committed and actual amounts side by "
                   "side. Not month-filtered."),

        # The D8 deliverable itself: the list somebody assembles by hand today.
        # Was 300 tall at y=542, which ran 122px off the bottom of the canvas - invisible
        # in a PDF export and clipped in the service, neither of which reports an error.
        visual(p, "c_vendorlist", "tableEx", 646, 400, 614, 262,
               {"Values": [column("bridge_ProjectVendor", "VendorName"),
                           column("bridge_ProjectVendor", "TradeName"),
                           column("bridge_ProjectVendor", "City"),
                           column("bridge_ProjectVendor", "LicenseNumber"),
                           column("bridge_ProjectVendor", "IsPrequalified"),
                           column("bridge_ProjectVendor", "SyncedToErp")]},
               title="Vendor list - prequalification and ERP sync"),

        # Sage AP against Procore, per project. Ends on the footer line (FOOTER_Y 662).
        # Left column: two short column charts, the matrix, then this table; right column:
        # the cost-code bars (180px minimum) over the vendor list running to the footer.
        visual(p, "c_ap_recon", "tableEx", 20, 512, 610, 150,
               {"Values": [column("dim_Project", "ProjectName"),
                           measure("Spent To Date"), measure("AP Job Cost"),
                           measure("AP vs Procore Spent Variance"), measure("AP / Procore Spent Ratio"),
                           measure("ERP-only Vendor Cost")]},
               title="Spent To Date vs Sage AP job cost (AP from 2025-03-11; never added to Spent)",
               alt="Table. One row per project: Procore Spent To Date, Sage AP job cost, the variance "
                   "and ratio between them, and AP job cost at vendors with no Procore commitment or "
                   "direct cost on the project. Sage AP history starts 2025-03-11 and timing differs "
                   "between the systems; AP is a check and is not added to Spent To Date. Not "
                   "month-filtered."),
    ]


def page_insurance() -> tuple[str, list[dict]]:
    """D8's other half: certificates of insurance.

    THE PAGE LEADS WITH THE BAD NEWS ON PURPOSE. Live, every one of the 105 certificates
    in Procore is past its expiry date, the most recent lapsed 2025-04-01, and only 23 of
    251 vendors have a certificate on file at all.

    That is not proof the subcontractors are uninsured - far more likely the module was
    populated once and abandoned, with current certificates living in email. But a
    compliance page that renders that as a green tick is worse than no page, and the two
    readings have very different consequences for a general contractor.

    Coverage and currency are shown as separate numbers throughout, because "no
    certificate on file" and "certificate lapsed" need different follow-up: chase the
    document, or chase the renewal.
    """
    p = "insurance"
    return p, [
        textbox(p, "title", "Vendor Insurance", 20, 16, 600, 44),
        textbox(p, "note",
                "Sourced from Procore's insurance records. COVERAGE (is there a "
                "certificate at all) and CURRENCY (is it in date) are counted separately - "
                "a vendor with no record and a vendor with a lapsed record both fail a "
                "single compliance flag and need different follow-up. With a project selected, "
                "every figure covers that project's vendors; the month slicer does not apply.",
                20, 56, 1240, 46, size=10, color=MUTED),

        # Three coverage numbers on the left, three currency numbers on the right, one
        # band. i_soon sits with currency rather than in a row of its own - "expiring
        # soon" is a renewal question, not a coverage one.
        textbox(p, "cov_h", "Coverage", 20, 110, 400, 32, size=13),
        card(p, "i_vendors", "Vendors On Project", 20, 144, 195, 100),
        card(p, "i_insured", "Vendors With Insurance", 229, 144, 195, 100),
        card(p, "i_missing", "Vendors Without Insurance", 438, 144, 195, 100),

        textbox(p, "cur_h", "Currency", 647, 110, 400, 32, size=13),
        card(p, "i_certs", "Certificates On File", 647, 144, 195, 100),
        card(p, "i_expired", "Expired Certificates", 856, 144, 195, 100),
        card(p, "i_soon", "Certificates Expiring Soon", 1065, 144, 195, 100),
        # Why every certificate reads Expired: the newest one in Procore is already past.
        # Beside the charts; the header strip above belongs to the title and slicers.
        card(p, "i_latest", "Latest Certificate Expiration", 1065, 256, 195, 100,
             title="Latest certificate expiration"),

        visual(p, "i_by_status", "columnChart", 20, 256, 335, 196,
               {"Category": [column("fct_VendorInsurance", "ExpiryStatus")],
                "Y": [measure("Certificates On File")]},
               title="Certificates by expiry status"),

        visual(p, "i_by_type", "barChart", 369, 256, 335, 196,
               {"Category": [column("fct_VendorInsurance", "InsuranceCategory")],
                "Y": [measure("Certificates On File")]},
               title="Certificates by coverage type"),

        visual(p, "i_state", "columnChart", 718, 256, 335, 196,
               {"Category": [column("fct_VendorInsurance", "ComplianceState")],
                "Y": [measure("Certificates On File")]},
               title="Lapsed vs in date vs exempt"),

        # The working list: who to chase, for what, and how overdue.
        # Vendor NAME, not the surrogate key. [Certificates On File] scopes the rows to the
        # selected project's vendors, the same way the cards above are scoped.
        no_totals(visual(p, "i_list", "tableEx", 20, 464, 1240, 192,
               {"Values": [column("dim_Vendor", "VendorName"),
                           column("fct_VendorInsurance", "InsuranceType"),
                           column("fct_VendorInsurance", "Provider"),
                           column("fct_VendorInsurance", "PolicyNumber"),
                           column("fct_VendorInsurance", "ExpirationDate"),
                           column("fct_VendorInsurance", "ExpiryStatus"),
                           column("fct_VendorInsurance", "DaysUntilExpiry"),
                           measure("Certificates On File")]},
               title="Certificates - what to chase, and how overdue")),
    ]


PAGES = [
    # Portfolio first: leadership was named a primary audience and had no page at all.
    # Overview stays second because it is the per-project page that gets exported to PDF.
    ("Portfolio", page_portfolio, False),
    ("Overview", page_overview, False),
    ("Financial", page_financial, False),
    ("Schedule & Quality", page_schedule_quality, False),
    ("Safety & Quality", page_safety_quality, False),
    ("Billing & Retainage", page_billing, False),
    ("Direct Costs & Vendors", page_costs_vendors, False),
    ("Vendor Insurance", page_insurance, False),
    ("Scorecard", page_scorecard, False),
    ("Source Coverage", page_source_coverage, False),
    ("Project Detail", page_project_detail, True),    # drill-through target
    ("Data Quality", page_data_quality, False),
]


def assign_tab_order(visuals: list[dict]) -> list[dict]:
    """Give every visual on a page an explicit keyboard tab position, in reading order.

    Power BI falls back to z-order for any visual without one, so setting tabOrder on SOME
    visuals is worse than setting it on none: the reader tabs through the few that are
    ordered, then jumps around the rest. Assigning here rather than at each call site means
    a page cannot be added with the accessibility half-done.

    Anything that set its own tab (the slicers at 1-2, the footer at 99) keeps it; the rest
    are numbered top-to-bottom, left-to-right from 10.
    """
    auto = sorted((v for v in visuals if "tabOrder" not in v["position"]),
                  key=lambda v: (v["position"]["y"], v["position"]["x"]))
    for i, v in enumerate(auto, start=10):
        v["position"]["tabOrder"] = i
    return visuals


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
        # The theme. Until now the report ran bare Power BI defaults while a validated
        # theme sat unused in powerbi/theme.json - eight categorical slots checked for
        # colour-vision separation and contrast in both light and dark, plus the corrected
        # RAG steps. Registering it is one file and one reference, and it is the single
        # largest visual change in this pass.
        f"StaticResources/RegisteredResources/{THEME_NAME}.json":
            THEME_SRC.read_text(encoding="utf-8"),
        "definition/report.json": json.dumps({
            "$schema": f"{SCHEMA}/report/2.0.0/schema.json",
            "themeCollection": {
                "baseTheme": {"name": "CY24SU10", "reportVersionAtImport": "5.55",
                              "type": "SharedResources"},
                # Layered OVER the base theme, so anything the custom theme does not
                # specify still falls back to a supported Microsoft base rather than to
                # nothing.
                "customTheme": {"name": f"{THEME_NAME}.json", "reportVersionAtImport": "5.55",
                                "type": "RegisteredResources"},
            },
            "resourcePackages": [{
                "name": "RegisteredResources",
                "type": "RegisteredResources",
                "items": [{"name": f"{THEME_NAME}.json", "path": f"{THEME_NAME}.json",
                           "type": "CustomTheme"}],
            }],
            "settings": {
                "useStylableVisualContainerHeader": True,
                # Summarized only. The detail behind a visual is a lakehouse query, not a
                # spreadsheet to re-download and re-key - which is the habit this whole
                # report exists to retire.
                "exportDataMode": "AllowSummarized",
                "defaultDrillFilterOtherVisuals": True,
                "useEnhancedTooltips": True,
                "allowChangeFilterTypes": True,
            },
        }, indent=2),
    }

    page_names = []
    for display, builder, hidden in PAGES:
        pid, visuals = builder()
        visuals = assign_tab_order(visuals + chrome(pid, slicers=pid not in DRILLTHROUGH))
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
    bookmarks = [b for b in [
        ("bmOverview", "Monthly overview", "overview"),
        ("bmCoverage", "Where the data is missing", "sourcecoverage"),
        ("bmScorecard", "Scorecard and how it is scored", "scorecard"),
    ] if b[2] in page_names]
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
