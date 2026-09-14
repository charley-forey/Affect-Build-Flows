"""Produce inspectable report lineage and optional read-only live validation evidence.

python audit_solution.py --live
No deployments, refreshes, credentials or individual source records are written.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import tempfile
from unittest.mock import patch

import deploy_model as dm
import deploy_report as dr

DOCS = Path(__file__).resolve().parents[1] / "_docs"


def bindings(value):
    if isinstance(value, dict):
        for kind in ("Column", "Measure"):
            field = value.get(kind)
            if isinstance(field, dict) and "Property" in field:
                entity = field.get("Expression", {}).get("SourceRef", {}).get("Entity")
                if entity:
                    yield entity, field["Property"], kind
        for child in value.values():
            yield from bindings(child)
    elif isinstance(value, list):
        for child in value:
            yield from bindings(child)


def inventory():
    with tempfile.TemporaryDirectory() as tmp, patch.object(dr, "REPORT_DIR", Path(tmp)):
        files = dr.build("00000000-0000-0000-0000-000000000000")
    pages = {}
    for path, content in files.items():
        if path.endswith("/page.json"):
            pages[path.split("/")[2]] = json.loads(content)["displayName"]
    refs = []
    for path, content in files.items():
        if path.endswith("visual.json"):
            for table, field, kind in sorted(set(bindings(json.loads(content)))):
                refs.append(dict(page=pages[path.split("/")[2]], visual=path.split("/")[4],
                                 table=table, field=field, kind=kind))
    return dict(model=dm.MODEL_NAME, report=dr.REPORT_NAME, pages=pages,
                tables=list(dm.MODEL_TABLES), relationships=list(dm.RELATIONSHIPS),
                measures=[dict(name=n, expression=e, format=f, origin=o)
                          for n, e, f, o in dm.MEASURES], visual_bindings=refs)


def live_check(model, fabric_token, pbi_token):
    import deploy_seeds as ds
    import validate_model as vm
    item = ds.find_item(fabric_token, model["model"], "SemanticModel")
    if not item:
        return {"error": "semantic model not found"}
    evidence = {"model_id": item["id"], "queries": {}, "errors": {}}
    def query(label, dax):
        try:
            evidence["queries"][label] = vm.dax(item["id"], pbi_token, dax)
        except Exception as exc:
            evidence["errors"][label] = str(exc)[:1500]
    for start in range(0, len(model["measures"]), 20):
        group = model["measures"][start:start + 20]
        fields = ", ".join(f'"{m["name"]}", [{m["name"]}]' for m in group)
        query(f"deployed_measures_{start}", f"EVALUATE ROW({fields})")
    fields = ", ".join(f'"{t}", COUNTROWS({t})' for t in model["tables"])
    query("table_counts", f"EVALUATE ROW({fields})")
    query("latest_checks", "EVALUATE TOPN(5, meta_PipelineRun, meta_PipelineRun[RunAt], DESC)")
    query("candidate_pipeline_status", f'EVALUATE ROW("Status", {dm.PIPELINE_STATUS_DAX})')
    if model["model"] == "Affect Project Report":
        query("financial_reconciliation", '''EVALUATE ROW(
            "InvoiceDifference", [Total Billed] - [Total Paid] - [AR Outstanding],
            "BudgetDifference", [Budget] - [Spent To Date] - [Budget Variance],
            "UnmatchedInvoiceAmount", CALCULATE(SUM(fct_Invoice[Amount]), fct_Invoice[HasUnmatchedProject] = TRUE()),
            "UnmatchedInvoices", [DQ Unmatched Invoices],
            "ActualOpenSubmittals", CALCULATE(COUNTROWS(fct_RfiSubmittal), fct_RfiSubmittal[ItemType] = "Submittal", fct_RfiSubmittal[IsOpen] = TRUE()),
            "ActualOpenRFIs", CALCULATE(COUNTROWS(fct_RfiSubmittal), fct_RfiSubmittal[ItemType] = "RFI", fct_RfiSubmittal[IsOpen] = TRUE()),
            "DisplayedOpenSubmittals", [Open Submittals])''')
        row = evidence["queries"].get("financial_reconciliation", [{}])[0]
        evidence["reconciliation"] = {
            key: {"difference": row.get(f"[{key}]"),
                  "passed": row.get(f"[{key}]") is not None and abs(row[f"[{key}]"]) < 0.01}
            for key in ("InvoiceDifference", "BudgetDifference")}
        evidence["submittal_definition_matches"] = (
            "[ActualOpenSubmittals]" in row and "[DisplayedOpenSubmittals]" in row
            and row["[ActualOpenSubmittals]"] == row["[DisplayedOpenSubmittals]"])
    evidence["gold_checks_recent"] = evidence["queries"].get("candidate_pipeline_status", [{}])[0].get("[Status]") in (
        "Gold checks passed; source completeness unverified", "Gold checked with warnings; source completeness unverified")
    return evidence


def main():
    models = [inventory()]
    import deploy_model_qc
    import deploy_report_qc
    models.append(inventory())
    timestamp = datetime.now(timezone.utc).isoformat()
    lineage = dict(generated_at=timestamp,
                   scope="Declared visual bindings, DAX, relationships and SQL producers; not proof of source completeness.",
                   models=models, sql_producers={})
    for path in sorted((DOCS.parent / "02-transformation" / "sql").rglob("*.sql")):
        for table in re.findall(r"CREATE (?:OR REPLACE )?(?:TEMPORARY VIEW|TABLE)(?: IF NOT EXISTS)?\s+(\w+)", path.read_text(), re.I):
            lineage["sql_producers"].setdefault(table, []).append(str(path.relative_to(DOCS.parent)))
    DOCS.mkdir(exist_ok=True)
    (DOCS / "report-lineage.json").write_text(json.dumps(lineage, indent=2), encoding="utf-8")
    print(f"Lineage: {len(models)} models, {sum(len(m['pages']) for m in models)} pages")
    if "--live" in sys.argv:
        import deploy as dp
        import validate_model as vm
        fabric_token, pbi_token = dp.token(), vm.pbi_token()
        evidence = dict(checked_at=timestamp,
                        scope="Read-only deployed aggregates and candidate status DAX; no deployment performed.",
                        certification="Not certified: source completeness, business definitions and rendered UI require separate proof.",
                        models={})
        for model in models:
            evidence["models"][model["model"]] = live_check(model, fabric_token, pbi_token)
            print(f"Checked {model['model']}", flush=True)
        (DOCS / "validation-evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        return int(any(m.get("errors") or m.get("error") or not m.get("gold_checks_recent") or
                       m.get("submittal_definition_matches") is False or
                       any(not r["passed"] for r in m.get("reconciliation", {}).values())
                       for m in evidence["models"].values()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
