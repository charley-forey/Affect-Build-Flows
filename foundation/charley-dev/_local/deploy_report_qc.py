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

ROW1, ROW2 = 132, 250


def page_portfolio() -> tuple[str, list[dict]]:
    """The DASHBOARD tab, computed. One row per register, across every project."""
    p = "qcportfolio"
    return p, [
        textbox(p, "title", "Quality Portfolio", 20, 16, 600, 44),
        textbox(p, "note",
                "The workbook's DASHBOARD tab, rebuilt. Every figure is computed from the "
                "registers rather than typed beside them - four of the workbook's own "
                "roll-ups counted completions over a shorter row range than totals, so "
                "their % Complete could never reach 100%.",
                20, 56, 1160, 44, size=10, color=MUTED),

        textbox(p, "h_ncr", "Non-conformance", 20, 104, 400, 24, size=13),
        card(p, "k_ncr_open", "Open Observations", 20, ROW1, 270, 100),
        card(p, "k_ncr_due", "Observations Past Due", 306, ROW1, 270, 100),
        card(p, "k_ncr_days", "Avg Observation Closure Days", 592, ROW1, 270, 100),
        card(p, "k_ncr_rate", "Observation Closure Rate", 878, ROW1, 270, 100),

        textbox(p, "h_punch", "Punch & submittals", 20, 236, 400, 24, size=13),
        card(p, "k_punch_open", "Open Punch Items", 20, ROW2 + 20, 270, 100),
        card(p, "k_punch_aged", "Punch Items Aged Over 7 Days", 306, ROW2 + 20, 270, 100),
        card(p, "k_sub_open", "Open Submittals", 592, ROW2 + 20, 270, 100),
        card(p, "k_sub_late", "Overdue Submittals", 878, ROW2 + 20, 270, 100),

        visual(p, "by_project", "barChart", 20, 392, 560, 260,
               {"Category": [column("dim_Project", "ProjectName")],
                "Y": [measure("Open Observations")]},
               title="Open Observations by project"),
        visual(p, "reg_state", "tableEx", 600, 392, 560, 260,
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
                20, 56, 1160, 40, size=10, color=MUTED),
        card(p, "k_total", "Total Observations", 20, ROW1, 220, 100),
        card(p, "k_open", "Open Observations", 256, ROW1, 220, 100),
        card(p, "k_closed", "Closed Observations", 492, ROW1, 220, 100),
        card(p, "k_due", "Observations Past Due", 728, ROW1, 220, 100),
        card(p, "k_days", "Avg Observation Closure Days", 964, ROW1, 220, 100),
        visual(p, "by_month", "columnChart", 20, ROW2 + 10, 560, 280,
               {"Category": [column("dim_Date", "MonthYear")],
                "Y": [measure("Open Observations")]},
               title="Open Observations by month"),
        visual(p, "list", "tableEx", 600, ROW2 + 10, 584, 280,
               {"Values": [column("fct_QcNcr", "NcrNumber"),
                           column("fct_QcNcr", "Title"),
                           column("fct_QcNcr", "StatusCode"),
                           column("fct_QcNcr", "DaysOpen")]},
               title="Observation register"),
    ]


def page_punch() -> tuple[str, list[dict]]:
    p = "qcpunch"
    return p, [
        textbox(p, "title", "Punch & Completion", 20, 16, 600, 44),
        textbox(p, "note",
                "Punch is not quality control - it confirms readiness. Zero Punch is the "
                "stated objective. Items beyond 5 days escalate to the trade PM, beyond 7 "
                "to the trade executive, which is why ageing is a headline here.",
                20, 56, 1160, 40, size=10, color=MUTED),
        card(p, "k_total", "Total Punch Items", 20, ROW1, 270, 100),
        card(p, "k_open", "Open Punch Items", 306, ROW1, 270, 100),
        card(p, "k_aged", "Punch Items Aged Over 7 Days", 592, ROW1, 270, 100),
        card(p, "k_rate", "Punch Closure Rate", 878, ROW1, 270, 100),
        visual(p, "by_project", "barChart", 20, ROW2 + 10, 560, 280,
               {"Category": [column("dim_Project", "ProjectName")],
                "Y": [measure("Open Punch Items")]},
               title="Open punch items by project"),
        visual(p, "list", "tableEx", 600, ROW2 + 10, 584, 280,
               {"Values": [column("fct_QcPunch", "PunchNumber"),
                           column("fct_QcPunch", "Title"),
                           column("fct_QcPunch", "StatusCode"),
                           column("fct_QcPunch", "DaysOpen")]},
               title="Punch register"),
    ]


def page_submittals() -> tuple[str, list[dict]]:
    p = "qcsubmittals"
    return p, [
        textbox(p, "title", "Submittals & Mock-Ups", 20, 16, 600, 44),
        textbox(p, "note",
                "Possible mock-ups are inferred from subject text containing MOCK. "
                "Matches can be wrong or incomplete; this is not a confirmed mock-up register. "
                "Overdue submittals need review for procurement impact.",
                20, 56, 1160, 40, size=10, color=MUTED),
        card(p, "k_total", "Total Submittals", 20, ROW1, 270, 100),
        card(p, "k_open", "Open Submittals", 306, ROW1, 270, 100),
        card(p, "k_late", "Overdue Submittals", 592, ROW1, 270, 100),
        card(p, "k_turn", "Avg Submittal Turnaround", 878, ROW1, 270, 100),
        card(p, "k_mock", "Possible Mock-Ups", 20, ROW2 + 10, 270, 100),
        visual(p, "list", "tableEx", 306, ROW2 + 10, 878, 290,
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
        visual(p, "register", "tableEx", 20, ROW2 + 10, 1164, 360,
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
        visual(p, "items", "tableEx", 20, ROW2 + 10, 1164, 360,
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
        visual(p, "by_type", "columnChart", 20, ROW2 + 10, 480, 290,
               {"Category": [column("qc_seed_Gate", "GateType")],
                "Y": [measure("Gates Defined")]},
               title="Gates by pathway"),
        visual(p, "list", "tableEx", 520, ROW2 + 10, 664, 290,
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
                20, 56, 1160, 40, size=10, color=MUTED),
        card(p, "k_def", "Checklist Items Defined", 20, ROW1, 270, 100),
        card(p, "k_rec", "Checklist Items Recorded", 306, ROW1, 270, 100),
        card(p, "k_pass", "Checklist Items Passed", 592, ROW1, 270, 100),
        card(p, "k_fail", "Checklist Items Failed", 878, ROW1, 270, 100),
        card(p, "k_dfow", "DFOWs Registered", 20, ROW2 + 10, 270, 100),
        card(p, "k_tier", "Tier 3 And 4 DFOWs", 306, ROW2 + 10, 270, 100),
        card(p, "k_itp", "ITP Tests Defined", 592, ROW2 + 10, 270, 100),
        card(p, "k_si", "Special Inspections Logged", 878, ROW2 + 10, 270, 100),
        visual(p, "by_trade", "barChart", 20, 392, 560, 260,
               {"Category": [column("qc_seed_Trade", "TradeName")],
                "Y": [measure("Checklist Items Defined")]},
               title="Checklist items per trade"),
        visual(p, "trades", "tableEx", 600, 392, 584, 260,
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
                20, 56, 1160, 40, size=10, color=MUTED),

        textbox(p, "h_trade", "Trade resolution", 20, 104, 400, 24, size=13),
        textbox(p, "n_trade",
                "Procore's trade vocabulary and the workbook's controlled keys are "
                "different vocabularies - Procore says \"HVAC\" and \"Sprinkler\" where "
                "the workbook says HVAC_DUCTWORK and FIRE_SPRINKLER. Unmatched rows are "
                "flagged, never dropped: in the workbook they would vanish from a lookup "
                "silently. Resolving them needs Affect to confirm the mapping, because "
                "guessing whether \"Concrete Superstructure\" is CIP concrete or slab on "
                "deck would attach a defect to the wrong trade.",
                20, ROW1, 560, 120, size=10, color=MUTED),
        card(p, "k_ncr_un", "DQ Observations With Unmapped Trade", 600, ROW1, 280, 100),
        card(p, "k_punch_un", "DQ Punch With Unmapped Trade", 896, ROW1, 280, 100),

        textbox(p, "h_manual", "Manual registers", 20, 270, 400, 24, size=13),
        card(p, "k_await", "DQ Registers Awaiting Input", 20, 300, 560, 100),
        card(p, "k_gates_rec", "Gates Recorded", 600, 300, 280, 100),
        card(p, "k_check_rec", "Checklist Items Recorded", 896, 300, 280, 100),

        textbox(p, "h_pipe", "Pipeline", 20, 420, 400, 24, size=13),
        card(p, "k_status", "Pipeline Status", 20, 450, 560, 80),
        card(p, "k_hours", "Hours Since Last Checked Run", 600, 450, 280, 80),
        card(p, "k_last", "Last Checked Run", 896, 450, 280, 80),

        visual(p, "unmapped", "tableEx", 20, 544, 568, 110,
               {"Values": [column("fct_QcNcr", "TradeLabel"), measure("Total Observations")]},
               title="Procore trade labels seen on observations"),
        visual(p, "data_gaps", "tableEx", 604, 544, 572, 110,
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
]


if __name__ == "__main__":
    try:
        raise SystemExit(dr.main())
    except dr.dp.FabricError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
