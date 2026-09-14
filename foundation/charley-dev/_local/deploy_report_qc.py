"""Generate and deploy the Project Quality Plan report over the PQP semantic model.

    python deploy_report_qc.py            # dry run - write PBIR to disk only
    python deploy_report_qc.py --apply    # create/update the report in Fabric

Model B's report. It replaces the client's 44-sheet QA/QC workbook the same way the Monthly
Progress Report replaced the Excel tracker: the registers become tables, the DASHBOARD tab
becomes a roll-up page, and the numbers are computed rather than typed.

Everything is reused from deploy_report.py - the visual helpers, alt text, tab order, the
synced slicers and footer, the id stability that stops a redeploy churning every visual.
This module supplies page functions and a name.

WHAT IS DELIBERATELY NOT HERE: a "quality by trade" headline. 459 of 850 NCRs still resolve
to no trade, because Procore's trade vocabulary and the workbook's controlled keys are
different vocabularies ("HVAC" vs HVAC_DUCTWORK, "Sprinkler" vs FIRE_SPRINKLER). Charting
by trade today would silently describe 46% of the data. The count is on the Data Quality
page instead, where it is the finding rather than the footnote.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deploy_report as dr  # noqa: E402

CHARLEY_DEV = Path(__file__).resolve().parents[1]

dr.REPORT_NAME = "Project Quality Plan"
dr.REPORT_DIR = CHARLEY_DEV / "05-reports" / "Project Quality Plan.Report"
dr.MODEL_NAME = "Project Quality Plan"

textbox, card, visual, chrome = dr.textbox, dr.card, dr.visual, dr.chrome
measure, column = dr.measure, dr.column
MUTED = dr.MUTED

# Rows below the shared 60-104 subtitle band. Tables and charts run to FULL_BOTTOM, just
# above the footer, so no page leaves its lower third empty.
ROW1, ROW2 = 140, 260
FULL_BOTTOM = 656


def page_portfolio() -> tuple[str, list[dict]]:
    """The DASHBOARD tab, computed. One row per register, across every project."""
    p = "qcportfolio"
    return p, [
        textbox(p, "title", "Quality Portfolio", 20, 16, 600, 44),
        textbox(p, "note",
                "The workbook's DASHBOARD tab, rebuilt. Every figure is computed from the "
                "registers rather than typed beside them - four of the workbook's own "
                "roll-ups counted completions over a shorter row range than totals, so "
                "their % Complete could never reach 100%. Open and overdue counts are as of today; a month selection groups them by creation month.",
                20, 56, 1160, 44, size=10, color=MUTED),

        textbox(p, "h_ncr", "Non-conformance", 20, 106, 400, 32, size=13),
        card(p, "k_ncr_open", "Open Observations", 20, ROW1, 270, 100),
        card(p, "k_ncr_due", "Observations Past Due", 306, ROW1, 270, 100),
        card(p, "k_ncr_days", "Avg Observation Closure Days", 592, ROW1, 270, 100),
        card(p, "k_ncr_rate", "Observation Closure Rate", 878, ROW1, 270, 100),

        textbox(p, "h_punch", "Punch & submittals", 20, 244, 400, 32, size=13),
        card(p, "k_punch_open", "Open Punch Items", 20, 280, 270, 100),
        card(p, "k_punch_aged", "Punch Items Aged Over 7 Days", 306, 280, 270, 100),
        card(p, "k_sub_open", "Open Submittals", 592, 280, 270, 100),
        card(p, "k_sub_late", "Overdue Submittals", 878, 280, 270, 100),

        visual(p, "by_project", "barChart", 20, 392, 560, FULL_BOTTOM - 392,
               {"Category": [column("dim_Project", "ProjectName")],
                "Y": [measure("Open Observations")]},
               title="Open Observations by project"),
        visual(p, "reg_state", "tableEx", 600, 392, 584, FULL_BOTTOM - 392,
               {"Values": [column("dim_Project", "ProjectName"),
                           measure("Total Observations"), measure("Open Punch Items"),
                           measure("Open Submittals")]},
               title="Register state by project"),
    ]


def page_ncr() -> tuple[str, list[dict]]:
    p = "qcncr"
    return p, [
        textbox(p, "title", "Procore Observations", 20, 16, 600, 44),
        textbox(p, "note",
                "Includes all retrieved Procore observations, not only confirmed NCRs. "
                "NCR classification requires review. The monthly chart groups currently "
                "open records by creation month; it is not historical month-end backlog.",
                20, 56, 1160, 44, size=10, color=MUTED),
        card(p, "k_total", "Total Observations", 20, ROW1, 220, 100),
        card(p, "k_open", "Open Observations", 256, ROW1, 220, 100),
        card(p, "k_closed", "Closed Observations", 492, ROW1, 220, 100),
        card(p, "k_due", "Observations Past Due", 728, ROW1, 220, 100),
        card(p, "k_days", "Avg Observation Closure Days", 964, ROW1, 220, 100),
        visual(p, "by_month", "columnChart", 20, ROW2, 560, FULL_BOTTOM - ROW2,
               {"Category": [column("dim_Date", "MonthYear")],
                "Y": [measure("Open Observations")]},
               title="Open Observations by month"),
        # Longest open first. NcrNumber is text in gold (Procore's observation number) and
        # sorts 1, 10, 11, 2 - there is no numeric column to sort it by without a model
        # change, so the default sort is the one a reader acts on instead.
        dr.sort_desc(visual(p, "list", "tableEx", 600, ROW2, 584, FULL_BOTTOM - ROW2,
               {"Values": [column("fct_QcNcr", "NcrNumber"),
                           column("fct_QcNcr", "Title"),
                           column("fct_QcNcr", "StatusCode"),
                           column("fct_QcNcr", "DaysOpen")]},
               title="Observation register - longest open first"), column("fct_QcNcr", "DaysOpen")),
    ]


def page_punch() -> tuple[str, list[dict]]:
    p = "qcpunch"
    return p, [
        textbox(p, "title", "Punch & Completion", 20, 16, 600, 44),
        textbox(p, "note",
                "Punch is not quality control - it confirms readiness. Zero Punch is the "
                "stated objective. Items beyond 5 days escalate to the trade PM, beyond 7 "
                "to the trade executive, which is why ageing is a headline here. Open and overdue counts are as of today; a month selection groups them by creation month.",
                20, 56, 1160, 44, size=10, color=MUTED),
        card(p, "k_total", "Total Punch Items", 20, ROW1, 270, 100),
        card(p, "k_open", "Open Punch Items", 306, ROW1, 270, 100),
        card(p, "k_aged", "Punch Items Aged Over 7 Days", 592, ROW1, 270, 100),
        card(p, "k_rate", "Punch Closure Rate", 878, ROW1, 270, 100),
        visual(p, "by_project", "barChart", 20, ROW2, 560, FULL_BOTTOM - ROW2,
               {"Category": [column("dim_Project", "ProjectName")],
                "Y": [measure("Open Punch Items")]},
               title="Open punch items by project"),
        # PunchNumber is text in gold, like NcrNumber - sorted by age instead.
        dr.sort_desc(visual(p, "list", "tableEx", 600, ROW2, 584, FULL_BOTTOM - ROW2,
               {"Values": [column("fct_QcPunch", "PunchNumber"),
                           column("fct_QcPunch", "Title"),
                           column("fct_QcPunch", "StatusCode"),
                           column("fct_QcPunch", "DaysOpen")]},
               title="Punch register - longest open first"), column("fct_QcPunch", "DaysOpen")),
    ]


def page_submittals() -> tuple[str, list[dict]]:
    p = "qcsubmittals"
    return p, [
        textbox(p, "title", "Submittals & Mock-Ups", 20, 16, 600, 44),
        textbox(p, "note",
                "Possible mock-ups are inferred from subject text containing MOCK. "
                "Matches can be wrong or incomplete; this is not a confirmed mock-up register. "
                "Overdue submittals need review for procurement impact. Turnaround averages closed "
                "submittals only. Open and overdue counts are as of today; a month selection groups them by creation month.",
                20, 56, 1160, 44, size=10, color=MUTED),
        card(p, "k_total", "Total Submittals", 20, ROW1, 270, 100),
        card(p, "k_open", "Open Submittals", 306, ROW1, 270, 100),
        card(p, "k_late", "Overdue Submittals", 592, ROW1, 270, 100),
        card(p, "k_turn", "Avg Submittal Turnaround Days", 878, ROW1, 270, 100),
        card(p, "k_mock", "Possible Mock-Ups", 20, ROW2, 270, 100),
        visual(p, "list", "tableEx", 306, ROW2, 878, FULL_BOTTOM - ROW2,
               {"Values": [column("fct_QcSubmittal", "SubmittalNumber"),
                           column("fct_QcSubmittal", "Subject"),
                           column("fct_QcSubmittal", "StatusCode"),
                           column("fct_QcSubmittal", "TurnaroundDays")]},
               title="Submittal register"),
    ]


def page_native_inspections() -> tuple[str, list[dict]]:
    p = "qcinspections"
    return p, [
        textbox(p, "title", "Procore Inspections", 20, 16, 600, 44),
        textbox(p, "note",
                "Native inspections are not mapped to manual checklist templates. Closed does not "
                "mean every item was inspected. Blanks are unknown. Month filters use inspection "
                "date and exclude undated records; clear the month filter to include them.",
                20, 56, 1160, 44, size=10, color=MUTED),
        card(p, "total", "Native Inspections", 20, ROW1, 270, 100),
        visual(p, "register", "tableEx", 20, ROW2, 1164, FULL_BOTTOM - ROW2,
               {"Values": [column("fct_ProcoreInspection", c) for c in
                           ("ProjectKey", "InspectionKey", "InspectionName", "SourceTemplateName",
                            "InspectionDate", "DueDate", "SourceStatus", "SourceItemCount",
                            "ConformingItemCount", "DeficientItemCount", "NotInspectedItemCount")]},
               title="Native inspection register — source counts"),
    ]


def page_native_inspection_items() -> tuple[str, list[dict]]:
    p = "qcinspectionitems"
    return p, [
        textbox(p, "title", "Inspection Items", 20, 16, 600, 44),
        textbox(p, "note",
                "Original Procore responses include multiple-choice, text and signatures. "
                "No Response is a source label, not a failed check. Project and month filters "
                "follow the parent inspection; undated inspections require clearing the month filter.",
                20, 56, 1160, 44, size=10, color=MUTED),
        card(p, "total", "Native Inspection Items", 20, ROW1, 270, 100),
        visual(p, "items", "tableEx", 20, ROW2, 1164, FULL_BOTTOM - ROW2,
               {"Values": [column("fct_ProcoreInspectionItem", c) for c in
                           ("ProjectKey", "InspectionKey", "ItemKey", "ItemName",
                            "ResponseCategory", "ResponseType", "SourceStatus", "SourceResponse")]},
               title="Inspection item responses — unchanged source labels"),
    ]


def page_gates() -> tuple[str, list[dict]]:
    """Path to TCO, Path to Fire Alarm and Statutory Inspections - one table, one page.

    Three tabs in the workbook because Excel has no other way to group them. Here they are
    one register with a GateType, which is what makes a single readiness number possible.
    """
    p = "qcgates"
    return p, [
        textbox(p, "title", "Statutory Gates", 20, 16, 600, 44),
        textbox(p, "note",
                "93 template gates: 46 TCO, 23 fire alarm, 24 statutory. Select one project "
                "for recorded completion against this template. Missing input or invalid counts "
                "leave the percentage blank. Applicability and readiness are not certified.",
                20, 56, 1160, 44, size=10, color=MUTED),
        card(p, "k_def", "Gates Defined", 20, ROW1, 270, 100),
        card(p, "k_rec", "Gates Recorded", 306, ROW1, 270, 100),
        card(p, "k_done", "Gates Complete", 592, ROW1, 270, 100),
        card(p, "k_ready", "Gate Template Completion", 878, ROW1, 270, 100),
        visual(p, "by_type", "columnChart", 20, ROW2, 480, FULL_BOTTOM - ROW2,
               {"Category": [column("qc_seed_Gate", "GateType")],
                "Y": [measure("Gates Defined")]},
               title="Gates by pathway"),
        visual(p, "list", "tableEx", 520, ROW2, 664, FULL_BOTTOM - ROW2,
               {"Values": [column("qc_seed_Gate", "GateType"),
                           column("qc_seed_Gate", "Step"),
                           column("qc_seed_Gate", "Gate"),
                           column("qc_seed_Gate", "Authority")]},
               title="Gate register"),
    ]


def page_checklists() -> tuple[str, list[dict]]:
    p = "qcchecklists"
    return p, [
        textbox(p, "title", "Trade Checklists & DFOW", 20, 16, 600, 44),
        textbox(p, "note",
                "26 trade templates define 625 items. Counts use the manual registers; Procore "
                "inspection results are not linked to these templates. Completion requires one "
                "project and valid input; missing input stays blank. Applicability is unverified.",
                20, 56, 1160, 44, size=10, color=MUTED),
        card(p, "k_def", "Checklist Items Defined", 20, ROW1, 270, 100),
        card(p, "k_rec", "Checklist Items Recorded", 306, ROW1, 270, 100),
        card(p, "k_pass", "Checklist Items Passed", 592, ROW1, 270, 100),
        card(p, "k_fail", "Checklist Items Failed", 878, ROW1, 270, 100),
        card(p, "k_dfow", "DFOWs Registered", 20, ROW2, 270, 100),
        card(p, "k_tier", "Tier 3 And 4 DFOWs", 306, ROW2, 270, 100),
        card(p, "k_itp", "ITP Tests Defined", 592, ROW2, 270, 100),
        card(p, "k_si", "Special Inspections Logged", 878, ROW2, 270, 100),
        visual(p, "by_trade", "barChart", 20, 372, 560, FULL_BOTTOM - 372,
               {"Category": [column("qc_seed_Trade", "TradeName")],
                "Y": [measure("Checklist Items Defined")]},
               title="Checklist items per trade"),
        visual(p, "trades", "tableEx", 600, 372, 584, FULL_BOTTOM - 372,
               {"Values": [column("qc_seed_Trade", "TradeName"),
                           column("qc_seed_Trade", "CsiCode"),
                           column("qc_seed_Trade", "DfowRef"),
                           column("qc_seed_Trade", "RiskTier")]},
               title="Trades, CSI code and risk tier"),
    ]


def page_data_quality() -> tuple[str, list[dict]]:
    """Visible coverage limitations for the numbers on the other pages."""
    p = "qcdq"
    return p, [
        textbox(p, "title", "Data Quality", 20, 16, 600, 44),
        textbox(p, "note",
                "Coverage reflects rows available under the current filters. Empty registers "
                "are unverified inputs; populated registers are not proof of complete "
                "submissions. Confirm source intake and project applicability.",
                20, 56, 1160, 44, size=10, color=MUTED),

        # Three short bands, then the two tables at a height that shows the gap register
        # rather than three rows of it. The trade note was shortened to fit its band.
        textbox(p, "h_trade", "Trade resolution", 20, 106, 400, 32, size=13),
        textbox(p, "n_trade",
                "Procore trade names (\"HVAC\", \"Sprinkler\") differ from the workbook's "
                "controlled keys (HVAC_DUCTWORK, FIRE_SPRINKLER). Unmatched rows are flagged, "
                "never dropped. Resolving them needs Affect to confirm the mapping; guessing "
                "would attach a defect to the wrong trade.",
                20, ROW1, 560, 84, size=10, color=MUTED),
        card(p, "k_ncr_un", "DQ Observations With Unmapped Trade", 600, ROW1, 280, 84),
        card(p, "k_punch_un", "DQ Punch With Unmapped Trade", 896, ROW1, 280, 84),

        textbox(p, "h_manual", "Manual registers", 20, 228, 400, 32, size=13),
        card(p, "k_await", "DQ Registers Awaiting Input", 20, 264, 560, 80),
        card(p, "k_gates_rec", "Gates Recorded", 600, 264, 280, 80),
        card(p, "k_check_rec", "Checklist Items Recorded", 896, 264, 280, 80),

        textbox(p, "h_pipe", "Pipeline", 20, 352, 400, 32, size=13),
        card(p, "k_status", "Pipeline Status", 20, 388, 560, 72),
        card(p, "k_hours", "Hours Since Last Checked Run", 600, 388, 280, 72),
        card(p, "k_last", "Last Checked Run", 896, 388, 280, 72),

        visual(p, "unmapped", "tableEx", 20, 470, 568, 190,
               {"Values": [column("fct_QcNcr", "TradeLabel"), column("fct_QcNcr", "HasUnmappedTrade"),
                           measure("Total Observations")]},
               title="Procore trade labels seen on observations"),
        visual(p, "data_gaps", "tableEx", 604, 470, 580, 190,
               {"Values": [column("dq_DataGap", "GapCategory"),
                           measure("Data Gaps"), measure("Data Gap Amount")]},
               title="Data gap register by category",
               alt="Table. Count of known data gaps and the money they carry, by gap "
                   "category. Gaps not tied to a project are hidden while a project is "
                   "selected."),
    ]


dr.PAGES = [
    ("Quality Portfolio", page_portfolio, False),
    ("Observations", page_ncr, False),
    ("Punch & Completion", page_punch, False),
    ("Submittals & Mock-Ups", page_submittals, False),
    ("Procore Inspections", page_native_inspections, False),
    ("Inspection Items", page_native_inspection_items, False),
    ("Statutory Gates", page_gates, False),
    ("Trade Checklists & DFOW", page_checklists, False),
    ("Data Quality", page_data_quality, False),
    ("KPI Definitions", dr.page_definitions, True),   # hidden; header button target
]


if __name__ == "__main__":
    try:
        raise SystemExit(dr.main())
    except dr.dp.FabricError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
