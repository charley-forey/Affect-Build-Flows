"""Generate and deploy the DirectLake semantic model for the Project Quality Plan (PQP).

    python deploy_model_qc.py            # dry run - write TMDL to disk only
    python deploy_model_qc.py --apply    # create/update the model in Fabric
    python deploy_model_qc.py --apply --recreate

This is Model B. Model A (`Affect Project Report`, the Monthly Progress Report) is portfolio
finance for leadership; this one is per-project quality for the Q-Team. They are separate
models over the SAME `CD_Gold_Lakehouse`, which is the point:

  - `dim_Project` and `dim_Date` are CONFORMED, not copied. One definition, two models. A
    second lakehouse would have duplicated them and they would have drifted.
  - Model A is live and audited. Adding 19 tables to it to serve a different audience would
    have put that at risk for no gain. Rollback here is deleting one item.

EVERYTHING is reused from deploy_model.py - the TMDL emission, the Fabric introspection, the
Direct Lake traps, the upload and retry logic. This module supplies three lists and a name.
Overriding the globals works because every generator function reads them at call time; the
alternative was an 800-line copy that would rot the day the other one changed.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deploy_model as dm  # noqa: E402

CHARLEY_DEV = Path(__file__).resolve().parents[1]

dm.MODEL_NAME = "Project Quality Plan"
dm.MODEL_DIR = CHARLEY_DEV / "04-semantic_models" / "Project Quality Plan.SemanticModel"

# The two conformed dimensions come first so they sort to the top of the field list, then
# the seeds (the template library), then what actually happened on a project.
dm.MODEL_TABLES = [
    # Conformed with Model A - same physical tables, one definition.
    "dim_Date", "dim_Project",
    # The template library, versioned in the repo and identical on every project.
    "qc_seed_Trade", "qc_seed_ChecklistItem", "qc_seed_Gate", "qc_seed_DohItem",
    "dim_QcStatus",
    # Read from Procore, which the client's own workbook names as the mandatory system of
    # record for quality. These carry real data today.
    "fct_QcNcr", "fct_QcPunch", "fct_QcSubmittal",
    # The registers Procore does not hold. Typed and empty until the SharePoint lists exist;
    # bound now so the model is complete in shape before a single row is entered.
    "man_QcDfow", "man_QcItp", "man_QcGate", "man_QcSpecialInspection",
    "man_QcCommissioning", "man_QcInspectorSignIn", "man_QcChecklistResult",
    "man_QcDohResult",
    # The pipeline heartbeat - how the report answers "are these numbers from last night?".
    "meta_PipelineRun",
]

# fact.column -> dimension.column, single direction. Note TradeKey resolves to
# qc_seed_Trade, NOT dim_Trade: the PQP uses the workbook's controlled trade vocabulary
# (EXCAVATION, WATERPROOFING, ...), which is a different key space from the existing
# dim_Trade. Relating them would have silently produced a blank unknown-member row.
dm.RELATIONSHIPS = [
    ("fct_QcNcr", "ProjectKey", "dim_Project", "ProjectKey"),
    ("fct_QcNcr", "MonthStart", "dim_Date", "Date"),
    ("fct_QcNcr", "TradeKey", "qc_seed_Trade", "TradeKey"),
    ("fct_QcPunch", "ProjectKey", "dim_Project", "ProjectKey"),
    ("fct_QcPunch", "MonthStart", "dim_Date", "Date"),
    ("fct_QcPunch", "TradeKey", "qc_seed_Trade", "TradeKey"),
    ("fct_QcSubmittal", "ProjectKey", "dim_Project", "ProjectKey"),
    ("fct_QcSubmittal", "MonthStart", "dim_Date", "Date"),

    ("qc_seed_ChecklistItem", "TradeKey", "qc_seed_Trade", "TradeKey"),

    ("man_QcDfow", "ProjectKey", "dim_Project", "ProjectKey"),
    ("man_QcDfow", "TradeKey", "qc_seed_Trade", "TradeKey"),
    ("man_QcItp", "ProjectKey", "dim_Project", "ProjectKey"),
    ("man_QcItp", "TradeKey", "qc_seed_Trade", "TradeKey"),
    ("man_QcGate", "ProjectKey", "dim_Project", "ProjectKey"),
    ("man_QcGate", "GateKey", "qc_seed_Gate", "GateKey"),
    ("man_QcSpecialInspection", "ProjectKey", "dim_Project", "ProjectKey"),
    ("man_QcCommissioning", "ProjectKey", "dim_Project", "ProjectKey"),
    ("man_QcCommissioning", "TradeKey", "qc_seed_Trade", "TradeKey"),
    ("man_QcInspectorSignIn", "ProjectKey", "dim_Project", "ProjectKey"),
    ("man_QcChecklistResult", "ProjectKey", "dim_Project", "ProjectKey"),
    ("man_QcChecklistResult", "ItemKey", "qc_seed_ChecklistItem", "ItemKey"),
    ("man_QcDohResult", "ProjectKey", "dim_Project", "ProjectKey"),
    ("man_QcDohResult", "ItemKey", "qc_seed_DohItem", "ItemKey"),
]

# `origin` names the workbook cell each measure replaces, and is emitted as a /// comment so
# the lineage back to the client's spreadsheet survives in the model itself.
# TMDL format strings are QUOTED. Emitting `formatString: #,0` bare parses inconsistently,
# and a bare `yyyy-mm-dd hh:nn:ss` with spaces in it is worse. Matches deploy_model.py.
COUNT = '"#,0"'
DAYS = '"#,0.0"'
PCT = '"0.0%"'

dm.MEASURES = [
    ("Last Refresh", "MAX('_Measures'[_built_at])", '"yyyy-mm-dd hh:nn:ss"',
     "nothing - the workbook could not say when it was last true"),
    # The four below are what chrome() renders in the footer on every page. Model A has
    # them; the shared page furniture needs them here too or every page loses its header.
    ("Report Month Label",
     'VAR L = MIN ( dim_Date[MonthStart] )\n'
     'VAR H = MAX ( dim_Date[MonthStart] )\n'
     'RETURN IF ( L = H, FORMAT ( L, "MMMM YYYY" ), '
     'FORMAT ( L, "MMMM YYYY" ) & " - " & FORMAT ( H, "MMMM YYYY" ) )', "",
     "the workbook used TODAY(), so a saved copy silently re-dated itself"),
    ("Last Checked Run", "MAX ( meta_PipelineRun[RunAt] )", '"yyyy-mm-dd hh:nn"',
     "no workbook equivalent - a spreadsheet cannot say when it was last correct"),
    ("Hours Since Last Checked Run",
     "VAR Last = MAX ( meta_PipelineRun[RunAt] )\n"
     "RETURN IF ( ISBLANK ( Last ), BLANK (), DATEDIFF ( Last, NOW (), HOUR ) )",
     COUNT, "derived"),
    ("Pipeline Status",
     "VAR Hrs = [Hours Since Last Checked Run]\n"
     'RETURN SWITCH ( TRUE (), ISBLANK ( Hrs ), "Never completed a checked run", '
     'Hrs <= 30, "Current", Hrs <= 72, "Late - no run in over a day", '
     '"STALE - these numbers may be weeks old" )', "",
     "nothing - text not colour, so it survives greyscale and colour-blindness"),
    ("Projects With Quality Data",
     "CALCULATE(DISTINCTCOUNT(fct_QcNcr[ProjectKey]), ALL(dim_Project))", COUNT,
     "nothing - the workbook is one project per file"),

    # --- NCR / Observations -------------------------------------------------------
    ("Total NCRs", "COUNTROWS(fct_QcNcr)", COUNT, "NCR Log!B4 (Total Raised)"),
    ("Open NCRs", "CALCULATE(COUNTROWS(fct_QcNcr), fct_QcNcr[IsOpen] = TRUE())", COUNT,
     "NCR Log!D4 (Open)"),
    ("Closed NCRs", "CALCULATE(COUNTROWS(fct_QcNcr), fct_QcNcr[IsOpen] = FALSE())", COUNT,
     "NCR Log!F4 (Closed)"),
    ("NCRs Past Due", "CALCULATE(COUNTROWS(fct_QcNcr), fct_QcNcr[IsPastDue] = TRUE())", COUNT,
     "NCR Log!H4 (Overdue)"),
    ("Avg Days To Close NCR",
     "AVERAGEX(FILTER(fct_QcNcr, fct_QcNcr[IsOpen] = FALSE()), fct_QcNcr[DaysOpen])", DAYS,
     "NCR Log!K4 (Avg Days to Close)"),
    ("NCR Closure Rate",
     "DIVIDE([Closed NCRs], [Total NCRs])", PCT, "NCR Log - not computed in the workbook"),

    # --- Punch & Rolling Completion ----------------------------------------------
    ("Total Punch Items", "COUNTROWS(fct_QcPunch)", COUNT, "Punch & RCL Log!B4 (Total Items)"),
    ("Open Punch Items", "CALCULATE(COUNTROWS(fct_QcPunch), fct_QcPunch[IsOpen] = TRUE())",
     COUNT, "Punch & RCL Log!D4 (Open)"),
    ("Punch Items Aged Over 7 Days",
     "CALCULATE(COUNTROWS(fct_QcPunch), fct_QcPunch[IsOpen] = TRUE(), fct_QcPunch[DaysOpen] > 7)",
     COUNT, "Punch & RCL Log!L4 (Aged > 7 Days)"),
    ("Punch Closure Rate",
     "DIVIDE(CALCULATE(COUNTROWS(fct_QcPunch), fct_QcPunch[IsOpen] = FALSE()), [Total Punch Items])",
     PCT, "Punch & RCL Log!N4 (% Closed)"),
    ("Avg Days Punch Open",
     "AVERAGEX(FILTER(fct_QcPunch, fct_QcPunch[IsOpen] = TRUE()), fct_QcPunch[DaysOpen])", DAYS,
     "Punch & RCL Log!N column (Days Open)"),

    # --- Submittals & mock-ups ----------------------------------------------------
    ("Total Submittals", "COUNTROWS(fct_QcSubmittal)", COUNT,
     "Submittals & Mockups!B4 (Total)"),
    ("Open Submittals",
     "CALCULATE(COUNTROWS(fct_QcSubmittal), fct_QcSubmittal[IsOpen] = TRUE())", COUNT,
     "Submittals & Mockups!I4 (Outstanding)"),
    ("Overdue Submittals",
     "CALCULATE(COUNTROWS(fct_QcSubmittal), fct_QcSubmittal[IsOverdue] = TRUE())", COUNT,
     "Submittals & Mockups - not computed in the workbook"),
    ("Avg Submittal Turnaround",
     "AVERAGEX(FILTER(fct_QcSubmittal, NOT ISBLANK(fct_QcSubmittal[TurnaroundDays])), "
     "fct_QcSubmittal[TurnaroundDays])", DAYS,
     "Submittals & Mockups - not computed in the workbook"),
    ("Mock-Ups Registered",
     "CALCULATE(COUNTROWS(fct_QcSubmittal), fct_QcSubmittal[IsMockup] = TRUE())", COUNT,
     "Project Identifiers!B15 (8 project mock-ups)"),

    # --- Statutory gates (TCO / Fire Alarm / Statutory, one table) ----------------
    ("Gates Defined", "COUNTROWS(qc_seed_Gate)", COUNT,
     "Path to TCO!E4 + Path to Fire Alarm + Statutory Inspections"),
    ("Gates Recorded", "COUNTROWS(man_QcGate)", COUNT, "Path to TCO!A9:A71"),
    ("Gates Complete",
     "CALCULATE(COUNTROWS(man_QcGate), man_QcGate[StatusCode] = \"COMPLETE\")", COUNT,
     "Path to TCO!G4 (Complete)"),
    ("Gate Readiness", "DIVIDE([Gates Complete], [Gates Defined])", PCT,
     "Path to TCO!K4 (TCO Readiness)"),

    # --- Trade QC checklists ------------------------------------------------------
    ("Checklist Items Defined", "COUNTROWS(qc_seed_ChecklistItem)", COUNT,
     "DASHBOARD!D59 (TOTAL - ALL TRADE CHECKLISTS)"),
    ("Checklist Items Recorded", "COUNTROWS(man_QcChecklistResult)", COUNT,
     "the 26 trade checklist tabs, column G"),
    ("Checklist Items Passed",
     "CALCULATE(COUNTROWS(man_QcChecklistResult), man_QcChecklistResult[ResultCode] = \"PASS\")",
     COUNT, "DASHBOARD!E59 (Pass)"),
    ("Checklist Items Failed",
     "CALCULATE(COUNTROWS(man_QcChecklistResult), man_QcChecklistResult[ResultCode] = \"FAIL\")",
     COUNT, "DASHBOARD!F59 (Fail)"),
    ("Checklist Completion",
     "DIVIDE([Checklist Items Passed], [Checklist Items Defined])", PCT,
     "DASHBOARD!G59 (% Complete)"),

    # --- DFOW risk, ITP, inspections ----------------------------------------------
    ("DFOWs Registered", "COUNTROWS(man_QcDfow)", COUNT, "DFOW Risk Register!A5:A36"),
    ("Tier 3 And 4 DFOWs",
     "CALCULATE(COUNTROWS(man_QcDfow), man_QcDfow[RiskTier] >= 3)", COUNT,
     "DASHBOARD!B29 (Tier 3 & 4 DFOWs)"),
    ("ITP Tests Defined", "COUNTROWS(man_QcItp)", COUNT, "DASHBOARD!B10 (ITP total)"),
    ("ITP Tests Passed",
     "CALCULATE(COUNTROWS(man_QcItp), man_QcItp[ResultCode] = \"PASS\")", COUNT,
     "DASHBOARD!C10 (ITP Pass)"),
    ("Special Inspections Logged", "COUNTROWS(man_QcSpecialInspection)", COUNT,
     "Special Inspections!B4 (Total Events)"),
    ("Inspector Visits Logged", "COUNTROWS(man_QcInspectorSignIn)", COUNT,
     "DASHBOARD!B28 (Inspector sign-in entries)"),
    ("Systems Accepted",
     "CALCULATE(COUNTROWS(man_QcCommissioning), man_QcCommissioning[StatusCode] = \"ACCEPTED\")",
     COUNT, "DASHBOARD!C11 (Commissioning accepted)"),
    ("DOH Items Verified",
     "CALCULATE(COUNTROWS(man_QcDohResult), man_QcDohResult[StatusCode] = \"VERIFIED\")", COUNT,
     "DOH Checklist!D4 (Verified)"),

    # --- Data quality -------------------------------------------------------------
    ("DQ NCRs With Unmapped Trade",
     "CALCULATE(COUNTROWS(fct_QcNcr), fct_QcNcr[HasUnmappedTrade] = TRUE())", COUNT,
     "nothing - Excel drops unmatched rows from a lookup silently"),
    ("DQ Punch With Unmapped Trade",
     "CALCULATE(COUNTROWS(fct_QcPunch), fct_QcPunch[HasUnmappedTrade] = TRUE())", COUNT,
     "nothing - Excel drops unmatched rows from a lookup silently"),
    ("DQ Registers Awaiting Input",
     "IF([Gates Recorded] + [Checklist Items Recorded] + [DFOWs Registered] = 0, "
     "\"No manual quality data entered yet\", \"\")", "",
     "nothing - an empty tab and a complete tab look identical in Excel"),
]

# Forward-filled positionally over MEASURES, so each entry names the FIRST measure of a group.
dm.FOLDER_STARTS = [
    ("Last Refresh", "00 Report context"),
    ("Total NCRs", "01 Non-conformance"),
    ("Total Punch Items", "02 Punch & completion"),
    ("Total Submittals", "03 Submittals & mock-ups"),
    ("Gates Defined", "04 Statutory gates"),
    ("Checklist Items Defined", "05 Trade checklists"),
    ("DFOWs Registered", "06 DFOW, ITP & inspections"),
    ("DQ NCRs With Unmapped Trade", "07 Data quality"),
]


if __name__ == "__main__":
    try:
        raise SystemExit(dm.main())
    except dm.dp.FabricError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
