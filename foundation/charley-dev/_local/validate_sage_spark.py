"""Build an isolated Sage validation notebook; no persistent table writes.

--start creates/updates only cd_91_validate_sage in charley-dev and starts one job.
--status polls that saved job once and fetches its uniquely named diagnostic.
"""
import argparse
import hashlib
import json
import re
import uuid
from pathlib import Path

import deploy as dp
import deploy_seeds as ds
import deploy_gold as dg
from make_notebooks import cell, notebook
from sage_validation import checks
from seedrunner import split_statements

HERE = Path(__file__).resolve().parent
HANDLE = HERE / "../_docs/sage-spark-job.json"
NAME = "cd_91_validate_sage"


def build(run_id):
    ids = json.loads((HERE / "fabric_ids.json").read_text())
    sql = (HERE / "../02-transformation/sql/silver/26_sage_silver.sql").read_text()
    sources = sorted(set(re.findall(r"FROM (cd_bronze_sage_\w+)", sql)))
    transforms = []
    for statement in split_statements(sql):
        if not re.match(r"CREATE OR REPLACE TABLE cd_silver_sage_\w+ AS\s+SELECT", statement):
            raise ValueError("unexpected Sage statement; review isolation before running")
        transforms.append(statement.replace("CREATE OR REPLACE TABLE", "CREATE OR REPLACE TEMPORARY VIEW", 1))
    root = f"abfss://{dp.WORKSPACE_ID}@onelake.dfs.fabric.microsoft.com/{ids['CD_Bronze_Lakehouse']['id']}/Tables/dbo"
    setup = f'''
import json, os
from datetime import datetime, timezone
run_id = {run_id!r}
evidence = {{"run_id": run_id, "started_at": datetime.now(timezone.utc).isoformat(),
             "source_sql_sha256": {hashlib.sha256(sql.encode()).hexdigest()!r},
             "mode": "candidate temporary views; published tables untouched", "checks": []}}
for name in {sources!r}:
    spark.sql(f"CREATE OR REPLACE TEMPORARY VIEW {{name}} AS SELECT * FROM delta.`{root}/{{name}}`")
'''
    transform = "\n".join(f"spark.sql({statement!r})" for statement in transforms)
    verify = f'''
for name, query in {checks()!r}.items():
    try:
        rows = [r.asDict(recursive=True) for r in spark.sql(query).collect()]
        evidence["checks"].append({{"name": name, "query": query, "rows": rows,
                                  "status": "violations" if rows else "passed"}})
    except Exception as exc:
        evidence["checks"].append({{"name": name, "query": query,
                                  "status": "error", "error": str(exc)}})
evidence["counts"] = {{name: spark.table(name).count() for name in {sources!r} +
    ["cd_silver_sage_jobs", "cd_silver_sage_ar_invoices", "cd_silver_sage_ar_lines",
     "cd_silver_sage_ap_invoices", "cd_silver_sage_ap_lines"]}}
evidence["completed_at"] = datetime.now(timezone.utc).isoformat()
os.makedirs("/lakehouse/default/Files/_diag", exist_ok=True)
with open(f"/lakehouse/default/Files/_diag/sage_candidate_{{run_id}}.json", "x", encoding="utf-8") as fh:
    json.dump(evidence, fh, indent=2, default=str)
assert all(c["status"] == "passed" for c in evidence["checks"]), "Sage candidate validation failed; see diagnostic"
print("Sage candidate: all reconciliation checks passed")
'''
    return ds.attach(notebook([cell(setup), cell(transform), cell(verify)]), ds.lakehouse(), dp.WORKSPACE_ID)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", action="store_true")
    parser.add_argument("--status", action="store_true")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--gold", action="store_true", help="validate full gold in a separate lakehouse")
    modes.add_argument("--silver", action="store_true", help="validate full silver in a separate lakehouse")
    modes.add_argument("--full", action="store_true", help="validate silver then gold in the isolated lakehouse")
    args = parser.parse_args()
    import validate_gold_candidate as gold
    mode = "full" if args.full else "silver" if args.silver else "gold" if args.gold else "sage"
    isolated = args.gold or args.silver or args.full
    builder = gold.build_full if args.full else gold.build_silver if args.silver else gold.build
    handle_path = HERE / f"../_docs/{mode}-spark-job.json"
    name = "cd_94_validate_full" if args.full else "cd_93_validate_silver" if args.silver else "cd_92_validate_gold" if args.gold else NAME
    prefix = f"{mode}_candidate"
    evidence_path = HERE / f"../_docs/{mode}-spark-evidence.json"
    if args.start and args.status:
        parser.error("choose start or status")
    if not args.start and not args.status:
        nb = builder("offline", {"id": "offline", "defaultSchema": "dbo"}) if isolated else build("offline")
        for c in nb["cells"]:
            if c["cell_type"] == "code":
                compile("".join(c["source"]), "candidate-validation", "exec")
        print(f"{len(nb['cells'])} candidate cells compile; gold mode writes only to its isolated validation lakehouse")
        return
    token = dp.token()
    if args.status:
        handle = json.loads(handle_path.read_text())
        _, job, _ = dp.call("GET", handle["location"], token)
        print(json.dumps(job, indent=2))
        handle["latest_job"] = job
        handle_path.write_text(json.dumps(handle, indent=2))
        if job.get("status") in ("Completed", "Failed", "Cancelled", "Deduped"):
            evidence = dg.fetch_diagnostics(handle.get("lakehouse_id", ds.lakehouse()["id"]), f"{prefix}_{handle['run_id']}.json")
            if evidence:
                evidence_path.write_text(json.dumps(evidence, indent=2))
                print("saved candidate evidence")
            if args.gold or args.full:
                for remote in ("seed_run.json", "gold_run.json", "gold_schema.json"):
                    diagnostic = dg.fetch_diagnostics(handle["lakehouse_id"], remote)
                    if diagnostic:
                        label = "full-candidate-" if args.full else "candidate-"
                        (HERE / "../_docs" / (label + remote)).write_text(json.dumps(diagnostic, indent=2))
            if args.silver or args.full:
                diagnostic = dg.fetch_diagnostics(handle["lakehouse_id"], "silver_run.json")
                if diagnostic:
                    label = "full-candidate-silver_run.json" if args.full else "candidate-silver_run.json"
                    (HERE / "../_docs" / label).write_text(json.dumps(diagnostic, indent=2))
        return
    prior_handles = [HERE / f"../_docs/{m}-spark-job.json" for m in ("silver", "gold", "full")] if isolated else [handle_path]
    for prior_handle in prior_handles:
        if not prior_handle.exists():
            continue
        previous = json.loads(prior_handle.read_text())
        _, job, _ = dp.call("GET", previous["location"], token)
        if job.get("status") not in ("Completed", "Failed", "Cancelled", "Deduped"):
            raise RuntimeError("prior validation job still active; use --status")
    target = gold.lakehouse(token) if isolated else ds.lakehouse()
    run_id = uuid.uuid4().hex
    candidate = builder(run_id, target) if isolated else build(run_id)
    definition = {"format": "ipynb", "parts": [{"path": "notebook-content.ipynb",
        "payload": ds.payload(candidate), "payloadType": "InlineBase64"}]}
    existing = ds.find_item(token, name, "Notebook")
    if existing:
        if existing.get("folderId") != dp.FOLDER_ID:
            raise RuntimeError("validation notebook is outside charley-dev")
        status, _, headers = dp.call("POST", f"/workspaces/{dp.WORKSPACE_ID}/items/{existing['id']}/updateDefinition", token, {"definition": definition})
    else:
        status, _, headers = dp.call("POST", f"/workspaces/{dp.WORKSPACE_ID}/items", token,
            {"displayName": name, "type": "Notebook", "folderId": dp.FOLDER_ID, "definition": definition})
    if status == 202:
        dp.wait_for_operation(headers, token)
    item = ds.find_item(token, name, "Notebook")
    if not item or item.get("folderId") != dp.FOLDER_ID:
        raise RuntimeError("cannot verify validation notebook folder")
    _, _, headers = dp.call("POST", f"/workspaces/{dp.WORKSPACE_ID}/items/{item['id']}/jobs/instances?jobType=RunNotebook", token, {})
    if not headers.get("Location"):
        raise RuntimeError("start response has no job handle; inspect Fabric before retrying")
    handle_path.write_text(json.dumps({"run_id": run_id, "item_id": item["id"], "lakehouse_id": target["id"],
        "definition_sha256": hashlib.sha256(json.dumps(candidate).encode()).hexdigest(),
        "location": headers["Location"]}, indent=2))
    print("validation job started; handle saved")


if __name__ == "__main__":
    main()
