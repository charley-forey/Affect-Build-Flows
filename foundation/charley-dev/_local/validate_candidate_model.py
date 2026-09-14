"""Generate/deploy an isolated semantic model after a verified candidate data build."""
import argparse
import base64
import hashlib
import json
from pathlib import Path

import deploy as dp
import deploy_seeds as ds
import deploy_gold as dg
import deploy_model as dm
import validate_gold_candidate as candidate

DOCS = Path(__file__).resolve().parent.parent / "_docs"


def compare_counts(actual, expected):
    if any(type(count) is not int or count < 0 for count in expected.values()):
        raise RuntimeError("build counts must be nonnegative integers")
    return [f"{table}: model={actual.get('[' + table + ']')}, build={count}"
            for table, count in expected.items()
            if table in dm.MODEL_TABLES and actual.get("[" + table + "]") != count]


def check_register_coverage(model_id, token):
    """Exercise the generated DAX with empty, partial and fully populated synthetic inputs."""
    import validate_model as vm
    tables = [t for t in dm.MODEL_TABLES if t.startswith("man_") and t != dm.ACCESS_TABLE]
    expression = next(m[1] for m in dm.MEASURES if m[0] == "DQ Registers Awaiting Input")
    tested = expression
    for table in tables:
        tested = tested.replace(f"COUNTROWS({table})", f'COUNTROWS(FILTER(__Input,[Register]="{table}"))')
    checks = []
    for count in (0, 1, len(tables)):
        fixture = ",".join('{"' + t + '"}' for t in tables[:count] or ["other"])
        query = ('DEFINE TABLE __Input = DATATABLE("Register",STRING,{' + fixture
                 + '}) EVALUATE ROW("Status",' + tested + ')')
        rows = vm.dax(model_id, token, query)
        expected = f"{len(tables) - count}/{len(tables)} registers empty; completeness unverified"
        if rows != [{"[Status]": expected}]:
            raise RuntimeError(f"manual-register coverage failed for {count} populated registers")
        checks.append(dict(populated_registers=count, query=query, result=rows, passed=True))
    return checks


def check_template_completion(model_id, token):
    """Test generated percentage expressions using synthetic counts and real project filters."""
    import validate_model as vm
    projects = "FILTER(ALL(dim_Project),NOT ISBLANK(dim_Project[ProjectKey]))"
    if vm.dax(model_id, token, f'EVALUATE ROW("n",COUNTROWS({projects}))')[0]["[n]"] < 2:
        raise RuntimeError("percentage scope test needs at least two real candidate projects")
    cases = [("no_project", 0, 5, 3, 10, None), ("multiple_projects", 2, 20, 20, 10, None),
             ("unknown_project", "blank", 5, 3, 10, None), ("no_input", 1, 0, None, 10, None),
             ("zero_completed", 1, 5, None, 10, 0), ("partial", 1, 5, 3, 10, 0.3),
             ("complete", 1, 10, 10, 10, 1), ("too_many_records", 1, 11, 3, 10, None),
             ("too_many_completions", 1, 5, 6, 10, None), ("no_template", 1, 5, 3, 0, None)]
    checks = []
    for name, inputs in [
        ("Gate Template Completion", ("Gates Recorded", "Gates Complete", "Gates Defined")),
        ("Checklist Template Completion", ("Checklist Items Recorded", "Checklist Items Passed", "Checklist Items Defined"))]:
        expression = next(m[1] for m in dm.MEASURES if m[0] == name)
        columns = []
        for label, scope, recorded, completed, defined, expected in cases:
            tested = expression
            for measure, value in zip(inputs, (recorded, completed, defined)):
                tested = tested.replace(f"[{measure}]", "BLANK()" if value is None else str(value))
            project_filter = ("FILTER(ALL(dim_Project),ISBLANK(dim_Project[ProjectKey]))" if scope == "blank"
                              else f"TOPN({scope},{projects},dim_Project[ProjectKey],ASC)")
            columns.append(f'"{label}",CALCULATE({tested},{project_filter})')
        query = "EVALUATE ROW(" + ",".join(columns) + ")"
        rows = vm.dax(model_id, token, query)
        expected = {f"[{case[0]}]": case[-1] for case in cases}
        if rows != [expected]:
            raise RuntimeError(f"template percentage scenarios failed for {name}: {rows}")
        checks.append(dict(measure=name, query=query, result=rows, scenarios=len(cases), passed=True))
    return checks


def check_model(record):
    """Evaluate every measure in three filter contexts; count agreement is a separate check."""
    from datetime import datetime, timezone
    import validate_model as vm
    evidence = dict(model_id=record["item_id"], source_run_id=record["source_run_id"],
                    captured_at=datetime.now(timezone.utc).isoformat(), queries={}, errors={})
    token = vm.pbi_token()
    path = DOCS / f"candidate-{record['kind']}-dax-evidence.json"
    try:
        evidence["refresh"] = vm.reframe(record["item_id"], token)
        queries = {"counts": "EVALUATE ROW(" + ",".join(
            f'"{t}",COALESCE(COUNTROWS({t}),0)' for t in dm.MODEL_TABLES) + ")"}
        if record["kind"] == "monthly":
            queries["balance_reconciliation"] = vm.BALANCE_QUERY
        for start in range(0, len(dm.MEASURES), 20):
            fields = ",".join(f'"{m[0]}",[{m[0]}]' for m in dm.MEASURES[start:start + 20])
            queries[f"measures_{start}"] = f"EVALUATE ROW({fields})"
            queries[f"project_measures_{start}"] = f"EVALUATE SUMMARIZECOLUMNS(dim_Project[ProjectKey],{fields})"
            queries[f"month_measures_{start}"] = f"EVALUATE SUMMARIZECOLUMNS(dim_Date[MonthStart],{fields})"
        for label, query in queries.items():
            try:
                evidence["queries"][label] = vm.dax(record["item_id"], token, query)
            except Exception as exc:
                evidence["errors"][label] = str(exc)
            path.write_text(json.dumps(evidence, indent=2))
        if record["kind"] == "monthly":
            evidence["balance_checks"] = vm.check_balance_values(evidence["queries"]["balance_reconciliation"][0])
            evidence["spend_status_checks"] = vm.check_spend_status(record["item_id"], token)
            evidence["milestone_geometry_checks"] = vm.check_milestone_geometry(record["item_id"], token)
        if record["kind"] == "qc":
            evidence["manual_coverage_checks"] = check_register_coverage(record["item_id"], token)
            evidence["template_completion_checks"] = check_template_completion(record["item_id"], token)
        independent = vm.check_independent_measures(record["item_id"], token, record["kind"])
        evidence["independent_measure_checks"] = independent
        gaps = {key: independent[key] for key in ("failed", "not_deployed", "without_independent_check") if independent[key]}
        if gaps:
            evidence["errors"]["independent_measures"] = json.dumps(gaps)
        counts = dg.fetch_diagnostics(record["lakehouse_id"], f"candidate_counts_{record['source_run_id']}.json")
        if (not counts or counts.get("run_id") != record["source_run_id"]
                or counts.get("validation_lakehouse_id") != record["lakehouse_id"]):
            raise RuntimeError("build count evidence is missing or belongs to another run or lakehouse")
        gold = counts.get("gold")
        if not gold or any(not step.get("ok") for step in gold):
            raise RuntimeError("build count evidence is missing or failed")
        verification = [step for step in gold if step.get("step") == "verification"]
        if len(verification) != 1 or verification[0].get("findings"):
            raise RuntimeError("gold count verification is missing or ambiguous")
        expected = {**verification[0]["counts"], **counts["seeds"], **counts["heartbeat"]}
        evidence["count_differences"] = compare_counts(evidence["queries"]["counts"][0], expected)
        evidence["count_compared_tables"] = [t for t in dm.MODEL_TABLES if t in expected]
        evidence["counts_without_build_comparison"] = [t for t in dm.MODEL_TABLES if t not in expected]
        evidence["scope"] = "Measure evaluation and build-count agreement; business meaning, source completeness and rendered visuals remain separate checks."
    except Exception as exc:
        evidence["errors"]["validation"] = str(exc)
    finally:
        path.write_text(json.dumps(evidence, indent=2))
    if evidence["errors"] or evidence.get("count_differences") or evidence.get("counts_without_build_comparison"):
        raise RuntimeError(f"candidate DAX validation failed; see {path}")
    print(f"{len(dm.MEASURES)} measures evaluated in portfolio/project/month contexts; "
          f"{len(evidence['count_compared_tables'])} table counts reconciled")


def require_passing_run(handle, job, evidence):
    if job.get("status") != "Completed" or job.get("id") != handle["location"].rstrip("/").split("/")[-1]:
        raise RuntimeError("candidate job has not completed successfully")
    if not evidence or evidence.get("run_id") != handle["run_id"] or evidence.get("validation_lakehouse_id") != handle["lakehouse_id"]:
        raise RuntimeError("candidate evaluation does not match the selected run and lakehouse")
    import sys
    sys.path.insert(0, str(DOCS.parent / "02-transformation/dq"))
    from expectations import build_suite
    expected = {e.name: e.severity for e in build_suite().expectations}
    checks = evidence.get("checks", [])
    if len(checks) != len(expected) or {c.get("name") for c in checks} != set(expected):
        raise RuntimeError("candidate quality-rule coverage does not match the current suite")
    for check in checks:
        rows = check.get("failing_rows")
        if (type(rows) is not int or rows < 0 or check.get("severity") != expected[check["name"]]
                or check.get("passed") is not (rows == 0) or check.get("blocking") is not False
                or (rows > 0 and expected[check["name"]] == "error")):
            raise RuntimeError("candidate quality evidence is inconsistent, blocking, or unexecuted")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qc", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true", help="refresh and validate the existing isolated candidate model")
    args = parser.parse_args()
    handle = json.loads((DOCS / "full-spark-job.json").read_text())
    token = dp.token()
    _, job, _ = dp.call("GET", handle["location"], token)
    evidence = dg.fetch_diagnostics(handle["lakehouse_id"], f"full_candidate_{handle['run_id']}.json")
    require_passing_run(handle, job, evidence)
    target = candidate.lakehouse(token)
    if target["id"] != handle["lakehouse_id"]:
        raise RuntimeError("candidate lakehouse changed since the validated run")
    if args.qc:
        import deploy_model_qc  # Supplies the QC definitions to the shared generator.
    kind = "qc" if args.qc else "monthly"
    name = "CD_Validation_PQP" if args.qc else "CD_Validation_Monthly"
    files = dm.write_files(target["id"], DOCS / "validation-models" / kind, name)
    definition = {"parts": [{"path": path, "payload": base64.b64encode(content.encode()).decode(),
                             "payloadType": "InlineBase64"}
                            for path, content in files.items() if path != ".platform"]}
    record = {"model_name": name, "kind": kind, "source_run_id": handle["run_id"],
              "lakehouse_id": target["id"], "definition_sha256": hashlib.sha256(json.dumps(definition).encode()).hexdigest(),
              "status": "generated only"}
    if args.check:
        previous = json.loads((DOCS / f"candidate-model-{kind}.json").read_text())
        item = ds.find_item(token, name, "SemanticModel")
        if (not item or item.get("folderId") != dp.FOLDER_ID or item["id"] != previous.get("item_id")
                or any(previous.get(key) != record[key] for key in ("source_run_id", "lakehouse_id", "definition_sha256"))):
            raise RuntimeError("candidate model does not match this build and definition")
        check_model(previous)
        return
    if args.apply:
        item = ds.find_item(token, name, "SemanticModel")
        if item and item.get("folderId") != dp.FOLDER_ID:
            raise RuntimeError("candidate model is outside charley-dev")
        path = (f"/workspaces/{dp.WORKSPACE_ID}/items/{item['id']}/updateDefinition" if item
                else f"/workspaces/{dp.WORKSPACE_ID}/items")
        body = {"definition": definition}
        if not item:
            body.update(displayName=name, type="SemanticModel", folderId=dp.FOLDER_ID)
        status, _, headers = dp.call("POST", path, token, body)
        if status == 202:
            dp.wait_for_operation(headers, token)
        item = ds.find_item(token, name, "SemanticModel")
        if not item or item.get("folderId") != dp.FOLDER_ID:
            raise RuntimeError("cannot verify candidate model after deployment")
        record.update(item_id=item["id"], status="deployed; DAX validation pending")
    (DOCS / f"candidate-model-{kind}.json").write_text(json.dumps(record, indent=2))
    print(name + ": " + record["status"])


if __name__ == "__main__":
    main()
