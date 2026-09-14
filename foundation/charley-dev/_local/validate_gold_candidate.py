"""Build the existing gold release and DQ suite in a separate validation lakehouse."""
import json
from pathlib import Path

import deploy as dp
import deploy_seeds as ds
import deploy_gold as dg
import deploy_silver
import deploy_dq
from make_notebooks import cell, notebook

HERE = Path(__file__).resolve().parent
LAKEHOUSE_NAME = "CD_Validation_Lakehouse"


def build_silver(run_id, target):
    nb = deploy_silver.build_notebook()
    nb["cells"].append(cell(f'''
from datetime import datetime, timezone
evidence = {{"run_id": {run_id!r}, "completed_at": datetime.now(timezone.utc).isoformat(),
             "validation_lakehouse_id": {target['id']!r},
             "scope": "candidate silver writes from existing bronze; upstream completeness not certified",
             "results": results}}
with open("/lakehouse/default/Files/_diag/silver_candidate_{run_id}.json", "x", encoding="utf-8") as fh:
    json.dump(evidence, fh, indent=2)
'''))
    nb = ds.attach(nb, target, dp.WORKSPACE_ID)
    nb["metadata"]["dependencies"]["lakehouse"]["default_lakehouse_name"] = LAKEHOUSE_NAME
    return nb


def lakehouse(token):
    item = ds.find_item(token, LAKEHOUSE_NAME, "Lakehouse")
    if not item:
        dp.assert_folder(token)
        dp.create(LAKEHOUSE_NAME, "Lakehouse", token)
        item = ds.find_item(token, LAKEHOUSE_NAME, "Lakehouse")
    if not item or item.get("folderId") != dp.FOLDER_ID:
        raise RuntimeError("validation lakehouse must be inside charley-dev")
    live = json.loads((HERE / "fabric_ids.json").read_text())
    if item["id"] in {v.get("id") for v in live.values()}:
        raise RuntimeError("validation may not target a published lakehouse")
    _, detail, _ = dp.call("GET", f"/workspaces/{dp.WORKSPACE_ID}/lakehouses/{item['id']}", token)
    if detail.get("properties", {}).get("defaultSchema") != "dbo":
        raise RuntimeError("validation lakehouse requires dbo schema")
    return {"id": item["id"], "defaultSchema": "dbo"}


def build_full(run_id, target):
    return build(run_id, target, full=True)


def build(run_id, target, full=False):
    source = (f"abfss://{dp.WORKSPACE_ID}@onelake.dfs.fabric.microsoft.com/{target['id']}/Tables/dbo"
              if full else dg.CD_SILVER_ABFSS)
    cells = build_silver(run_id, target)["cells"] if full else []
    cells += [*ds.build_notebook()["cells"], cell('''
candidate_seed_counts = dict(actual)
'''), *dg.build_notebook(dg.SOURCES["cd"], silver_abfss=source)["cells"], cell('''
candidate_gold_evidence = json.loads(json.dumps(results))
''')]
    scope = ("candidate silver and gold from existing bronze" if full else "candidate gold from published silver")
    prefix = "full" if full else "gold"
    lib = HERE / "../00-platform/lib/dq.py"
    suite = HERE / "../02-transformation/dq/expectations.py"
    cells.append(cell(f'''
import types, sys, json, os
from datetime import datetime, timezone
dq = types.ModuleType("dq")
sys.modules["dq"] = dq
exec({lib.read_text()!r}, dq.__dict__)
dq.REJECTS_TABLE = "cd_validation_gold_rejects"
expectations = types.ModuleType("candidate_expectations")
expectations.__file__ = "/validation/02-transformation/dq/expectations.py"
exec({suite.read_text()!r}, expectations.__dict__)
run_id = {run_id!r}
results = expectations.build_suite().run(spark, run_id, persist=False)
evidence = {{"run_id": run_id, "completed_at": datetime.now(timezone.utc).isoformat(),
             "validation_lakehouse_id": {target['id']!r},
             "scope": {scope!r} + "; upstream freshness not certified",
             "checks": [{{"name": r.expectation.name, "severity": r.expectation.severity,
                         "failing_rows": r.failing_rows, "passed": r.passed,
                         "blocking": r.blocking}} for r in results]}}
os.makedirs("/lakehouse/default/Files/_diag", exist_ok=True)
with open(f"/lakehouse/default/Files/_diag/{prefix}_evaluation_{{run_id}}.json", "x", encoding="utf-8") as fh:
    json.dump(evidence, fh, indent=2)
dq._persist_results(spark, results, run_id)
for result in results:
    if result.failing_rows > 0:
        dq._persist_rejects(spark, result.expectation, spark.sql(result.expectation.failing_sql), run_id)
dq.persist_heartbeat(spark, results, run_id, "/lakehouse/default/Files/_diag")
dq.assert_no_blocking(results)
# Exercise the production snapshot SQL and both validation phases in isolation.
# Candidate certification is stricter than publication: missing history fails here.
snapshot_date = datetime.now(timezone.utc).date().isoformat()
snapshot_stage, snapshot_swap = {deploy_dq.snapshot_phases()!r}
evidence["snapshot_checks"] = {{}}
evidence["snapshot_date"] = snapshot_date
for statements, table in ((snapshot_stage, "v_DailySnapshotStage"),
                          (snapshot_swap, "fct_DailySnapshot")):
    for statement in statements:
        spark.sql(statement.replace("{{SNAPSHOT_DATE}}", snapshot_date).replace("{{RUN_ID}}", run_id))
    snapshot_results = expectations.snapshot_suite(snapshot_date, table).run(spark, run_id, persist=False)
    dq.assert_no_blocking(snapshot_results)
    evidence["snapshot_checks"][table] = [{{"name": r.expectation.name, "severity": r.expectation.severity,
        "failing_rows": r.failing_rows, "passed": r.passed, "blocking": r.blocking}} for r in snapshot_results]
dq.publish_schema(spark, "/lakehouse/default/Files/_diag", "fct_DailySnapshot")
count_evidence = {{"run_id": run_id, "validation_lakehouse_id": {target['id']!r},
                  "gold": candidate_gold_evidence, "seeds": candidate_seed_counts,
                  "snapshots": {{"fct_DailySnapshot": spark.table("fct_DailySnapshot").count()}},
                  "heartbeat": {{"meta_PipelineRun": spark.table("meta_PipelineRun").count()}}}}
with open(f"/lakehouse/default/Files/_diag/candidate_counts_{{run_id}}.json", "x", encoding="utf-8") as fh:
    json.dump(count_evidence, fh, indent=2)
evidence["completed_at"] = datetime.now(timezone.utc).isoformat()
with open(f"/lakehouse/default/Files/_diag/{prefix}_candidate_{{run_id}}.json", "x", encoding="utf-8") as fh:
    json.dump(evidence, fh, indent=2)

'''))
    nb = ds.attach(notebook(cells), target, dp.WORKSPACE_ID)
    nb["metadata"]["dependencies"]["lakehouse"]["default_lakehouse_name"] = LAKEHOUSE_NAME
    return nb
