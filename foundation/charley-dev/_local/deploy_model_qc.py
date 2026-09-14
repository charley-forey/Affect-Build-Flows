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
    "fct_QcNcr", "fct_QcPunch", "fct_QcSubmittal", "fct_ProcoreInspection",
    "fct_ProcoreInspectionItem",
    # The registers Procore does not hold. Typed and empty until the SharePoint lists exist;
    # bound now so the model is complete in shape before a single row is entered.
    "man_QcDfow", "man_QcItp", "man_QcGate", "man_QcSpecialInspection",
    "man_QcCommissioning", "man_QcInspectorSignIn", "man_QcChecklistResult",
    "man_QcDohResult",
    # Every known data gap in one register - silver rejects included - for the DQ page.
    "dq_DataGap",
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
    ("fct_ProcoreInspection", "ProjectKey", "dim_Project", "ProjectKey"),
    ("fct_ProcoreInspection", "InspectionDate", "dim_Date", "Date"),
    ("fct_ProcoreInspectionItem", "InspectionLinkKey", "fct_ProcoreInspection", "InspectionLinkKey"),

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
    ("dq_DataGap", "ProjectKey", "dim_Project", "ProjectKey"),
]

# `origin` names the workbook cell each measure replaces, and is emitted as a /// comment so
# the lineage back to the client's spreadsheet survives in the model itself.
# TMDL format strings are QUOTED. Emitting `formatString: #,0` bare parses inconsistently,
# and a bare `yyyy-mm-dd hh:nn:ss` with spaces in it is worse. Matches deploy_model.py.
COUNT = '"#,0"'
DAYS = '"#,0.0"'
PCT = '"0.0%"'

dm.MEASURES = [
    ("Last Refresh", "MAX('_Measures'[_built_at])", '"yyyy-mm-dd hh:nn"',
     "nothing - the workbook could not say when it was last true"),
    # The four below are what chrome() renders in the footer on every page. Model A has
    # them; the shared page furniture needs them here too or every page loses its header.
    ("Report Month Label", dm.REPORT_MONTH_LABEL_DAX, "",
     "the workbook used TODAY(), so a saved copy silently re-dated itself"),
    ("Last Checked Run", "MAX ( meta_PipelineRun[RunAt] )", '"yyyy-mm-dd hh:nn"',
     "nothing - when the last PUBLISHED run passed the DQ gate, not when gold was last built"),
    ("Hours Since Last Checked Run",
     "VAR Last = MAX ( meta_PipelineRun[RunAt] )\n"
     "RETURN IF ( ISBLANK ( Last ), BLANK (), DATEDIFF ( Last, UTCNOW (), HOUR ) )",
     COUNT, "nothing - hours since the last PUBLISHED validated run: automatic update is off, so the model only moves when cd_50_publish_models frames a run that passed the DQ gate. A blocked gate is NOT visible here (the model keeps the last good run); the alert is the signal"),
    ("Pipeline Status",
     dm.PIPELINE_STATUS_DAX, "",
     "nothing - status of the last PUBLISHED validated run, as text so it survives greyscale. A blocked gate never publishes, so BLOCKED is not expected in-model; the alert is the signal"),
    ("Projects With Quality Data",
     "CALCULATE(DISTINCTCOUNT(fct_QcNcr[ProjectKey]), ALL(dim_Project))", COUNT,
     "nothing - the workbook is one project per file"),

    # --- NCR / Observations -------------------------------------------------------
    ("Total Observations", "COUNTROWS(fct_QcNcr)", COUNT, "NCR Log!B4 (Total Raised)"),
    ("Open Observations", "CALCULATE(COUNTROWS(fct_QcNcr), fct_QcNcr[IsOpen] = TRUE())", COUNT,
     "NCR Log!D4 (Open)"),
    ("Closed Observations", "CALCULATE(COUNTROWS(fct_QcNcr), fct_QcNcr[IsOpen] = FALSE())", COUNT,
     "NCR Log!F4 (Closed)"),
    ("Observations Past Due", "CALCULATE(COUNTROWS(fct_QcNcr), fct_QcNcr[IsPastDue] = TRUE())", COUNT,
     "NCR Log!H4 (Overdue)"),
    ("Avg Observation Closure Days",
     "AVERAGEX(FILTER(fct_QcNcr, fct_QcNcr[IsOpen] = FALSE()), fct_QcNcr[DaysOpen])", DAYS,
     "NCR Log!K4 (Avg Days to Close)"),
    ("Observation Closure Rate",
     "DIVIDE([Closed Observations], [Total Observations])", PCT, "NCR Log - not computed in the workbook"),

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
    # Closed submittals only. TurnaroundDays holds days-since-created for OPEN items, so the
    # old average blended completed response times with the age of pending ones.
    ("Avg Submittal Turnaround Days",
     "AVERAGEX(FILTER(fct_QcSubmittal, NOT fct_QcSubmittal[IsOpen] && NOT ISBLANK(fct_QcSubmittal[TurnaroundDays])), "
     "fct_QcSubmittal[TurnaroundDays])", DAYS,
     "Submittals & Mockups - not computed in the workbook; closed submittals only"),
    ("Possible Mock-Ups",
     "CALCULATE(COUNTROWS(fct_QcSubmittal), fct_QcSubmittal[IsMockup] = TRUE())", COUNT,
     "Inferred from submittal subject text containing MOCK; may include false matches and miss unnamed mock-ups. Not a confirmed register."),

    ("Native Inspections", "COUNTROWS(fct_ProcoreInspection)", COUNT,
     "Retrieved native Procore inspection records; month filters use inspection date. Not a certification of scope or completion."),
    ("Native Inspection Items", "COUNTROWS(fct_ProcoreInspectionItem)", COUNT,
     "Retrieved native items linked through the project/inspection key; source responses are not reclassified."),

    # --- Statutory gates (TCO / Fire Alarm / Statutory, one table) ----------------
    ("Gates Defined", "COUNTROWS(qc_seed_Gate)", COUNT,
     "Path to TCO!E4 + Path to Fire Alarm + Statutory Inspections"),
    ("Gates Recorded", "COUNTROWS(man_QcGate)", COUNT, "Path to TCO!A9:A71"),
    ("Gates Complete",
     "CALCULATE(COUNTROWS(man_QcGate), man_QcGate[StatusCode] = \"COMPLETE\")", COUNT,
     "Path to TCO!G4 (Complete)"),
    ("Gate Template Completion",
     "VAR Recorded = [Gates Recorded]\nVAR Completed = COALESCE([Gates Complete], 0)\n"
     "VAR Defined = [Gates Defined]\nRETURN IF(HASONEVALUE(dim_Project[ProjectKey]) "
     "&& NOT ISBLANK(SELECTEDVALUE(dim_Project[ProjectKey])) && Recorded > 0 "
     "&& Defined > 0 && Recorded <= Defined && Completed <= Recorded, DIVIDE(Completed, Defined))", PCT,
     "Recorded completion against the template for one project; applicability and readiness are not certified"),

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
    ("Checklist Template Completion",
     "VAR Recorded = [Checklist Items Recorded]\nVAR Completed = COALESCE([Checklist Items Passed], 0)\n"
     "VAR Defined = [Checklist Items Defined]\nRETURN IF(HASONEVALUE(dim_Project[ProjectKey]) "
     "&& NOT ISBLANK(SELECTEDVALUE(dim_Project[ProjectKey])) && Recorded > 0 "
     "&& Defined > 0 && Recorded <= Defined && Completed <= Recorded, DIVIDE(Completed, Defined))", PCT,
     "Recorded passes against the template for one project; applicability and submission completeness are unverified"),

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
    ("DQ Observations With Unmapped Trade",
     "CALCULATE(COUNTROWS(fct_QcNcr), fct_QcNcr[HasUnmappedTrade] = TRUE())", COUNT,
     "nothing - Excel drops unmatched rows from a lookup silently"),
    ("DQ Punch With Unmapped Trade",
     "CALCULATE(COUNTROWS(fct_QcPunch), fct_QcPunch[HasUnmappedTrade] = TRUE())", COUNT,
     "nothing - Excel drops unmatched rows from a lookup silently"),
    ("DQ Registers Awaiting Input",
     "VAR EmptyRegisters = " + " + ".join(
         f"IF(COUNTROWS({table}) = 0, 1, 0)" for table in dm.MODEL_TABLES if table.startswith("man_"))
     + '\nRETURN FORMAT(EmptyRegisters, "0") & "/' + str(sum(t.startswith("man_") for t in dm.MODEL_TABLES))
     + ' registers empty in current filters; completeness unverified"', "",
     "Observed row coverage in current filters; populated registers are not certified complete"),
    ("Data Gaps", "COALESCE(COUNTROWS(dq_DataGap), 0)", COUNT,
     "nothing - rejects, unmapped trades, coverage and certificate gaps in one register"),
    ("Data Gap Amount", "SUM(dq_DataGap[Amount])", '"$#,0"',
     "money carried by data gaps - today only unmatched AR invoices carry an amount"),
]

# Forward-filled positionally over MEASURES, so each entry names the FIRST measure of a group.
dm.FOLDER_STARTS = [
    ("Last Refresh", "00 Report context"),
    ("Total Observations", "01 Non-conformance"),
    ("Total Punch Items", "02 Punch & completion"),
    ("Total Submittals", "03 Submittals & mock-ups"),
    ("Gates Defined", "04 Statutory gates"),
    ("Checklist Items Defined", "05 Trade checklists"),
    ("DFOWs Registered", "06 DFOW, ITP & inspections"),
    ("DQ Observations With Unmapped Trade", "07 Data quality"),
]


if __name__ == "__main__":
    try:
        raise SystemExit(dm.main())
    except dm.dp.FabricError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
