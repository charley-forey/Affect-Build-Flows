"""Offline release checks: generated code and fail-closed quality evidence."""
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import textwrap
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "00-platform" / "lib"))

import dq
import deploy_dq
import deploy_gold
import deploy_model
import deploy_landing
import deploy_manual
import deploy_seeds
import deploy_silver
import deploy_pipeline
import deploy_publish
import set_autosync  # noqa: F401 - import is the check
import deploy_ingestion
import make_notebooks
import duckdb
import fabric_common
import validate_sage_spark
import validate_gold_candidate
import validate_model
import validate_candidate_model
from audit_solution import bindings


def test_run_notebook_terminal_status():
    """deploy_dq (and every deploy script) exits 1 only when run_notebook raises FabricError."""
    dp = deploy_seeds.dp
    for final in ("Cancelled", "Deduped", "Failed", "Completed"):
        replies = [(202, {}, {"Location": "job"}), (200, {"status": final}, {})]
        with patch.object(dp, "call", side_effect=lambda *a, **k: replies.pop(0)):
            try:
                assert deploy_seeds.run_notebook("t", "nb") == final == "Completed"
            except dp.FabricError as exc:
                assert final != "Completed" and final in str(exc), exc
    print("  run_notebook: Cancelled, Deduped and Failed all raise")


def test_deployment_lookup():
    dp = deploy_seeds.dp
    base = dp.API + f"/workspaces/{dp.WORKSPACE_ID}/items"
    next_page = base + "?continuationToken=next"
    target = dict(id="owned", displayName="Target", type="Notebook", folderId=dp.FOLDER_ID)
    first = dict(id="unrelated", displayName="Other", type="Notebook")
    pages = [(200, {"value": [first], "continuationUri": next_page}, {}),
             (200, {"value": [target]}, {})]
    with patch.object(dp, "call", side_effect=pages) as read:
        assert deploy_seeds.find_item("test", "Target", "Notebook") == target
        assert [c.args[1] for c in read.call_args_list] == [base, next_page]
    with patch.object(dp, "call", side_effect=[
            (200, {"value": [], "continuationToken": "a+b="}, {}),
            (200, {"value": [target]}, {})]) as read:
        assert dp.list_items("test") == [target]
        assert read.call_args_list[1].args[1].endswith("continuationToken=a%2Bb%3D")
    for continuation in (base, "https://example.com/items", base.replace(dp.WORKSPACE_ID, "other-workspace")):
        with patch.object(dp, "call", return_value=(200, {"value": [], "continuationUri": continuation}, {})) as read:
            try:
                dp.list_items("test")
            except dp.FabricError:
                pass
            else:
                raise AssertionError("unsafe or repeating continuation accepted")
            assert read.call_count == 1
    for rows in ([dict(target, folderId="elsewhere")], [target, dict(target, id="duplicate-name")]):
        with patch.object(dp, "list_items", return_value=rows):
            try:
                deploy_seeds.find_item("test", "Target", "Notebook")
            except dp.FabricError:
                pass
            else:
                raise AssertionError("unsafe deployment lookup accepted")
    for body in ({}, {"value": None}, {"value": [{}]}, {"value": [target, target]}):
        with patch.object(dp, "call", return_value=(200, body, {})):
            try:
                dp.list_items("test")
            except dp.FabricError:
                pass
            else:
                raise AssertionError("incomplete or ambiguous collection accepted")


def test_notebooks():
    notebooks = {
        "dq": deploy_dq.build_notebook(),
        "gold": deploy_gold.build_notebook(deploy_gold.SOURCES["cd"]),
        "landing": deploy_landing.build_notebook(None),
        "manual": deploy_manual.build_notebook(),
        "seeds": deploy_seeds.build_notebook(),
        "silver": deploy_silver.build_notebook(),
        "extraction": make_notebooks.notebook(make_notebooks.EXTRACT_PROCORE),
        "outbuild extraction": make_notebooks.notebook(make_notebooks.EXTRACT_OUTBUILD),
        "sage candidate": validate_sage_spark.build("offline-test"),
        "gold candidate": validate_gold_candidate.build("offline-test", {"id": "validation-only", "defaultSchema": "dbo"}),
        "silver candidate": validate_gold_candidate.build_silver("offline-test", {"id": "validation-only", "defaultSchema": "dbo"}),
        "full candidate": validate_gold_candidate.build_full("offline-test", {"id": "validation-only", "defaultSchema": "dbo"}),
        "publish models": deploy_publish.build_notebook(),
    }
    count = 0
    for name, nb in notebooks.items():
        for i, cell in enumerate(nb["cells"]):
            if cell["cell_type"] == "code":
                compile("".join(cell["source"]), f"{name}:cell{i}", "exec")
                count += 1
    print(f"  {count} generated Python cells compile across {len(notebooks)} notebooks")
    source = "\n".join("".join(c["source"]) for c in notebooks["extraction"]["cells"])
    assert "session = rl.RateLimitedSession(requests.Session())" in source
    assert any(remote == "Files/lib/ratelimit.py" and local.exists()
               for local, remote in deploy_ingestion.UPLOADS)
    candidate = "\n".join("".join(c["source"]) for c in notebooks["sage candidate"]["cells"])
    assert "CREATE OR REPLACE TABLE" not in candidate
    assert "CREATE OR REPLACE TEMPORARY VIEW" in candidate
    assert notebooks["gold candidate"]["metadata"]["dependencies"]["lakehouse"]["default_lakehouse"] == "validation-only"
    assert notebooks["silver candidate"]["metadata"]["dependencies"]["lakehouse"]["default_lakehouse"] == "validation-only"
    assert notebooks["silver candidate"]["cells"][:-1] == notebooks["silver"]["cells"]
    full = notebooks["full candidate"]
    assert full["metadata"]["dependencies"]["lakehouse"]["default_lakehouse"] == "validation-only"
    assert full["cells"][:len(notebooks["silver candidate"]["cells"])] == notebooks["silver candidate"]["cells"]
    full_source = "\n".join("".join(c["source"]) for c in full["cells"])
    assert deploy_gold.CD_SILVER_ABFSS not in full_source
    assert "validation-only/Tables/dbo/cd_silver_budgets" in full_source
    assert 'dq.REJECTS_TABLE = "cd_validation_gold_rejects"' in full_source
    publish = "\n".join("".join(c["source"]) for c in notebooks["publish models"]["cells"])
    assert 'getToken("pbi")' in publish and "publish_run.json" in publish
    assert deploy_publish.MODEL_NAMES == ["Affect Project Report", "Project Quality Plan"]
    # Direct Lake on OneLake has no DirectQuery fallback. On SQL endpoints it does, and a
    # fallback query reads post-frame gold - bypassing the publish barrier.
    expressions = deploy_model.expressions_tmdl("x")
    assert "AzureStorage.DataLake" in expressions and "Sql.Database" not in expressions


def test_candidate_preserves_evaluation_on_write_failure():
    import json
    from datetime import datetime, timezone
    source = "".join(validate_gold_candidate.build_full("failure-test", {"id": "validation-only"})["cells"][-1]["source"])
    source = source[source.index("run_id = "):]
    result = dq.Result(dq.Expectation("checked", "table", "SELECT 1"), 0)
    def fail(*args):
        raise OSError("storage unavailable")
    with tempfile.TemporaryDirectory() as temp:
        source = source.replace("/lakehouse/default/Files/_diag", temp.replace("\\", "/"))
        scope = dict(expectations=SimpleNamespace(build_suite=lambda: SimpleNamespace(run=lambda *a, **k: [result])),
                     dq=SimpleNamespace(_persist_results=fail), spark=None, datetime=datetime,
                     timezone=timezone, json=json, os=__import__("os"))
        try:
            exec(compile(source, "candidate-persistence", "exec"), scope)
        except OSError:
            pass
        else:
            raise AssertionError("candidate persistence failure was ignored")
        evidence = json.loads((Path(temp) / "full_candidate_failure-test.json").read_text())
        assert evidence["checks"][0]["passed"] and evidence["run_id"] == "failure-test"


def test_validation_target_isolation():
    import json
    live = json.loads((validate_gold_candidate.HERE / "fabric_ids.json").read_text())
    for target_id, folder in ((live["CD_Gold_Lakehouse"]["id"], deploy_dq.dp.FOLDER_ID),
                              ("validation", "outside-charley-dev")):
        with patch.object(validate_gold_candidate.ds, "find_item", return_value={"id": target_id, "folderId": folder}):
            try:
                validate_gold_candidate.lakehouse("unused")
            except RuntimeError:
                pass
            else:
                raise AssertionError("validation accepted an unsafe lakehouse target")
    with tempfile.TemporaryDirectory() as temp:
        with patch.object(deploy_model, "introspect", return_value={"fct_BudgetLine": [("BudgetLineID", "string")]}) as read_schema:
            files = deploy_model.write_files("validation-only", Path(temp), "Validation model")
        read_schema.assert_called_once_with("validation-only")
        assert "validation-only" in files["definition/expressions.tmdl"]
        assert json.loads(files[".platform"])["metadata"]["displayName"] == "Validation model"
        for relative, content in files.items():
            assert (Path(temp) / relative).read_text() == content


def test_model_counts_from_build():
    tables = ("dim_Project", "dim_Vendor", "dim_CostCode", "fct_BudgetLine", "fct_ChangeOrder",
              "fct_Invoice", "fct_RfiSubmittal", "fct_Milestone", "fct_FinancialPeriod",
              "fct_Billing", "fct_DirectCost", "bridge_ProjectVendor")
    counts = {name: i + 10 for i, name in enumerate(tables)}
    counts["fct_BudgetLine"] = 404
    gold = [{"step": "verification", "ok": True, "counts": counts, "findings": []}]
    seeds = {"counts": {"dim_Date": 7670}, "expected": {"dim_Date": 7670}, "findings": []}
    with patch.object(deploy_gold, "fetch_diagnostics", side_effect=[gold, seeds]) as fetch:
        actual = validate_model.expected_counts("candidate")
        assert actual["[BudgetLines]"] == 404 and actual["[Dates]"] == 7670
        assert all(call.args[0] == "candidate" for call in fetch.call_args_list)
    for bad_gold, bad_seeds in ((None, seeds), ([{"step": "verification", "ok": False}], seeds),
                               (gold, None), (gold, dict(seeds, findings=["missing seed"]))):
        with patch.object(deploy_gold, "fetch_diagnostics", side_effect=[bad_gold, bad_seeds]):
            try:
                validate_model.expected_counts("candidate")
            except RuntimeError:
                pass
            else:
                raise AssertionError("invalid build evidence was accepted as expected model counts")


def test_heartbeat_schema_publication():
    import json
    captured = []
    class Writer:
        def format(self, value):
            assert value == "delta"
            return self
        def mode(self, value):
            assert value == "append"
            return self
        def saveAsTable(self, value):
            assert value == "meta_PipelineRun"
    class Spark:
        def createDataFrame(self, rows, schema):
            captured.append(rows[0])
            assert "RunAt TIMESTAMP" in schema
            return SimpleNamespace(write=Writer())
        def table(self, name):
            assert name == "meta_PipelineRun"
            return SimpleNamespace(count=lambda: 3, schema=SimpleNamespace(fields=[
                SimpleNamespace(name="RunId", dataType=SimpleNamespace(simpleString=lambda: "string"))]))
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "gold_schema.json"
        path.write_text(json.dumps({"existing": [["ID", "string"]]}))
        results = [dq.Result(dq.Expectation("broken", "t", "SELECT 1", severity="warn"), -1)]
        dq.persist_heartbeat(Spark(), results, "candidate-run", temp)
        assert captured[0][0] == "candidate-run" and captured[0][3:] == ("blocked", 1, 1, 1)
        assert json.loads(path.read_text()) == {"existing": [["ID", "string"]], "meta_PipelineRun": [["RunId", "string"]]}
        assert json.loads((Path(temp) / "heartbeat_run.json").read_text()) == {
            "run_id": "candidate-run", "counts": {"meta_PipelineRun": 3}}


def test_candidate_model_gate():
    import copy
    sys.path.insert(0, str(validate_candidate_model.DOCS.parent / "02-transformation/dq"))
    from expectations import build_suite
    handle = dict(location="https://example.invalid/jobs/job", run_id="run", lakehouse_id="candidate")
    job = dict(status="Completed", id="job")
    evidence = dict(run_id="run", validation_lakehouse_id="candidate", checks=[
        dict(name=e.name, severity=e.severity, failing_rows=0, passed=True, blocking=False)
        for e in build_suite().expectations])
    validate_candidate_model.require_passing_run(handle, job, evidence)
    wrong_check = copy.deepcopy(evidence)
    wrong_check["checks"][0].update(failing_rows=1, passed=False)
    for observed_job, observed_evidence in (
        (dict(job, status="InProgress"), evidence), (dict(job, id="other"), evidence),
        (job, dict(evidence, run_id="old")), (job, dict(evidence, validation_lakehouse_id="published")),
        (job, dict(evidence, checks=[])), (job, wrong_check)):
        try:
            validate_candidate_model.require_passing_run(handle, observed_job, observed_evidence)
        except RuntimeError:
            pass
        else:
            raise AssertionError("candidate model accepted incomplete or inconsistent build evidence")


def test_unknown_checks_block():
    warning = dq.Expectation("warning", "t", "SELECT * FROM missing", severity="warn")
    good = dq.Expectation("good", "t", "SELECT 1")
    class Spark:
        def sql(self, sql):
            if "missing" in sql:
                raise RuntimeError("missing source")
            return SimpleNamespace(count=lambda: 0)
    results = dq.Suite([warning, good]).run(Spark(), "test", persist=False)
    assert len(results) == 2 and results[1].passed
    assert results[0].blocking and not results[0].passed
    try:
        dq.assert_no_blocking(results)
    except RuntimeError:
        pass
    else:
        raise AssertionError("an unexecuted warning check permitted publication")
    dq.assert_no_blocking([dq.Result(warning, 2), dq.Result(good, 0)])


def test_conflicting_merge_keys_block():
    # Execute the guard's relational operations on real rows, including nullable
    # company-scope keys. Verify that neither creation nor update can write a conflict.
    class Frame:
        def __init__(self, relation):
            self.relation = relation
            self.columns = relation.columns
        def dropDuplicates(self):
            return Frame(self.relation.distinct())
        def groupBy(self, *keys):
            columns = ", ".join(keys)
            return SimpleNamespace(count=lambda: Frame(self.relation.aggregate(
                columns + ", count(*) AS count", columns)))
        def filter(self, predicate):
            return Frame(self.relation.filter(predicate))
        def limit(self, n):
            return Frame(self.relation.limit(n))
        def count(self):
            return self.relation.aggregate("count(*)").fetchone()[0]
    con = duckdb.connect()
    def frame(values):
        return Frame(con.sql(f"SELECT * FROM (VALUES {values}) AS t(id, project_id, payload)"))
    duplicate = frame("(1, NULL, 'a'), (1, NULL, 'a'), (2, 'p', 'b')")
    assert fabric_common.prepare_merge(duplicate, ["id", "project_id"]).count() == 2
    conflict = frame("(1, NULL, 'a'), (1, NULL, 'b')")
    for exists in (False, True):
        spark = SimpleNamespace(catalog=SimpleNamespace(tableExists=lambda table: exists))
        try:
            fabric_common.merge_delta(spark, conflict, "target", ["id", "project_id"])
        except ValueError as exc:
            assert "conflicting records" in str(exc)
        else:
            raise AssertionError("conflicting keys permitted a write")
    landing = "\n".join("".join(c["source"]) for c in deploy_landing.build_notebook(None)["cells"])
    assert 'prepare_merge(df.select(*cols), ["_merge_key"])' in landing
    con.close()


def test_landing_missing_files():
    import json
    import os
    cells = ["".join(c["source"]) for c in deploy_landing.build_notebook(None)["cells"]]
    loop = next(c for c in cells if "results, landed" in c)
    finish = next(c for c in cells if "landing_run.json" in c)
    with tempfile.TemporaryDirectory() as temp:
        (Path(temp) / "b1").mkdir()
        (Path(temp) / "b1" / "cd_bronze_outbuild_tasks.jsonl").write_text("")
        manifest = {"endpoints": [
            {"endpoint": "tasks", "table": "cd_bronze_outbuild_tasks", "rows": 0},
            {"endpoint": "activities", "table": "cd_bronze_outbuild_activities", "rows": 5}],
            "failures": [{"endpoint": "activities", "error": "HTTPError: 500"}]}
        def spark_unused(*a, **k):
            raise AssertionError("spark touched for a file that is not there")
        for recorded in (True, False):
            if not recorded:
                manifest["failures"] = []
            scope = dict(manifest=manifest, batch="b1", LANDING=temp, DIAG=temp, os=os, json=json,
                         print=lambda *a, **k: None, spark=SimpleNamespace(read=SimpleNamespace(json=spark_unused)))
            exec(compile(loop, "landing:loop", "exec"), scope)
            missing = scope["results"][1]
            if recorded:
                assert missing == {"table": "cd_bronze_outbuild_activities", "ok": True, "landed": False,
                                   "note": "not landed - failed at extract time",
                                   "extract_error": "HTTPError: 500"}
            else:
                assert not missing["ok"] and "missing" in missing["error"]
                try:
                    exec(compile(finish, "landing:finish", "exec"), scope)
                except AssertionError as exc:
                    assert "failed to land" in str(exc)
                else:
                    raise AssertionError("an unexpected missing landing file did not fail")


def test_silver_input_failure_blocks():
    import json
    nb = deploy_silver.build_notebook()
    source = "".join(nb["cells"][1]["source"])
    # Substitute only the filesystem diagnostic location; execute the deployed logic.
    with tempfile.TemporaryDirectory() as temp:
        source = source.replace('DIAG = "/lakehouse/default/Files/_diag"', f"DIAG = {temp!r}")
        attempted = []
        def sql(statement):
            attempted.append(statement)
            if deploy_silver.BRONZE_TABLES[0] in statement:
                raise PermissionError("source access denied")
        scope = dict(spark=SimpleNamespace(sql=sql, udf=SimpleNamespace(register=lambda *a: None)),
                     print=lambda *a: None)
        try:
            exec(compile(source, "silver:inputs", "exec"), scope)
        except RuntimeError as exc:
            assert "transformation blocked" in str(exc)
        else:
            raise AssertionError("unreadable bronze was accepted")
        assert len(attempted) == len(deploy_silver.BRONZE_TABLES)
        assert not any("WHERE 1=0" in statement for statement in attempted)
        evidence = json.loads((Path(temp) / "silver_run.json").read_text())
        assert len(evidence) == 1 and not evidence[0]["ok"]
        assert "PermissionError" in evidence[0]["error"]

    finish = "".join(nb["cells"][-1]["source"])
    with tempfile.TemporaryDirectory() as temp:
        def sql(statement):
            if deploy_silver.SILVER_TABLES[0] in statement:
                raise OSError("count read failed")
            return SimpleNamespace(collect=lambda: [{"n": 1}])
        scope = dict(spark=SimpleNamespace(sql=sql), results=[], json=json, DIAG=temp,
                     print=lambda *a: None)
        try:
            exec(compile(finish, "silver:verification", "exec"), scope)
        except AssertionError:
            pass
        else:
            raise AssertionError("unreadable silver count was marked verified")
        evidence = json.loads((Path(temp) / "silver_run.json").read_text())
        assert not evidence[-1]["ok"]
        assert evidence[-1]["counts"][deploy_silver.SILVER_TABLES[0]] is None


def test_audit_validation_scope():
    import audit_solution as audit
    for status, expected in (
        ("Gold checks passed; source completeness unverified", True),
        ("Gold checked with warnings; source completeness unverified", True),
        ("Unvalidated - data built after last check", False),
        (None, False),
    ):
        with patch.object(deploy_seeds, "find_item", return_value={"id": "candidate"}), \
                patch.object(validate_model, "dax", side_effect=lambda model, token, query:
                             [{"[Status]": status}] if '"Status"' in query else []):
            result = audit.live_check({"model": "PQP", "measures": [], "tables": []}, "test", "test")
        assert result["gold_checks_recent"] is expected
        assert "validation_current" not in result


def test_read_transport_retries():
    import ratelimit
    from requests.exceptions import ReadTimeout, ConnectionError as RequestConnectionError
    for failure in (ReadTimeout, RequestConnectionError):
        session = SimpleNamespace(get=Mock(
            side_effect=[failure("transient"), SimpleNamespace(status_code=200, headers={})]))
        waits = []
        wrapper = ratelimit.RateLimitedSession(session, sleep=waits.append)
        assert wrapper.get("/same-page", params={"page": 4}, timeout=60).status_code == 200
        assert waits == [1] and wrapper.requests_made == 2
        assert session.get.call_args_list[0] == session.get.call_args_list[1]
        session.get.side_effect = failure("persistent")
        waits.clear()
        before = wrapper.requests_made
        try:
            wrapper.get("/same-page")
        except failure:
            pass
        else:
            raise AssertionError("exhausted network reads passed")
        assert wrapper.requests_made - before == 3 and waits == [1, 2]
        session.post = Mock(side_effect=failure("post"))
        try:
            wrapper.post("/token")
        except failure:
            pass
        else:
            raise AssertionError("failed token exchange passed")
        assert session.post.call_count == 1


def test_checklist_group_normalization():
    import copy
    import procore_scope as ps
    endpoint = SimpleNamespace(name="checklist_lists")
    registry = ps.load_registry(str(Path(__file__).resolve().parents[2] / "01-ingestion/Procore/config/endpoints.yml"))
    items = next(e for e in registry if e.name == "checklist_list_items")
    assert items.scope == "parent" and items.parent.endpoint == "checklist_lists"
    assert list(ps.expand_paths(items, 1, [7, 8], [(101, 7), (102, 8)])) == [
        ("/rest/v1.0/projects/7/checklist/list_items?filters[list_id][]=101", 7),
        ("/rest/v1.0/projects/8/checklist/list_items?filters[list_id][]=102", 8)]
    try:
        ps.expand_paths(items, 1, [7], [101])
    except ValueError:
        pass
    else:
        raise AssertionError("inspection request guessed a missing project association")
    # Malformed/unavailable endpoints with no silver/gold consumer are out of the registry,
    # and the one consumed endpoint with a known gap declares it with a reason.
    names = {e.name for e in registry}
    assert not names & {"standard_cost_codes", "punch_item_types", "change_order_requests", "schedule"}
    prime = next(e for e in registry if e.name == "prime_contracts")
    assert "not enabled" in ps.declared_unavailable(prime, 562949955173068)
    assert ps.declared_unavailable(prime, 7) is None
    assert all(not e.unavailable_projects for e in registry if e.name != "prime_contracts")
    record = {"template_id": 10, "name": "Template", "response_set": {"pass": "yes"},
              "lists": [{"id": 101, "name": "First"}, {"id": 102, "name": "Second"}]}
    before = copy.deepcopy(record)
    normalized = ps.normalize_records(endpoint, record)
    assert record == before
    assert [r["id"] for r in normalized] == [101, 102]
    assert all(r["_source_group"] == {k: v for k, v in record.items() if k != "lists"} for r in normalized)
    parents = ps.collect_parent_ids([dict(r, project_id=7) for r in normalized], ps.ParentRef("checklist_lists"))
    assert parents == [(101, 7), (102, 7)]
    assert ps.normalize_records(endpoint, {"template_id": 10, "lists": []}) == []
    assert ps.normalize_records(endpoint, {"id": 101}) == [{"id": 101}]
    assert ps.normalize_records(SimpleNamespace(name="other"), record) == [record]
    child = SimpleNamespace(name="checklist_list_items")
    path = "/rest/v1.0/projects/7/checklist/list_items?filters[list_id][]=101"
    assert ps.normalize_records(child, {"id": 1, "list_id": 101}, path) == [{"id": 1, "list_id": 101}]
    for item, request in [({"list_id": 102}, path), ({}, path), ({"list_id": 101}, ""),
                          ({"list_id": 101}, path + "&filters[list_id][]=102")]:
        try:
            ps.normalize_records(child, item, request)
        except ValueError:
            pass
        else:
            raise AssertionError("unverified inspection parent association accepted")
    for malformed in ({"template_id": 10}, {"lists": None}, {"lists": [{}]}, {"lists": ["unexpected"]}):
        try:
            ps.normalize_records(endpoint, malformed)
        except ValueError:
            pass
        else:
            raise AssertionError("malformed inspection group accepted")


def test_extraction_scope_evidence():
    import json
    import os
    cells = ["".join(c["source"]) for c in make_notebooks.EXTRACT_PROCORE]
    extract = next(c for c in cells if "endpoint_audit = []" in c)
    finish = next(c for c in cells if "evidence = {" in c)
    class Disabled(Exception):
        def __init__(self, message, status):
            super().__init__(message)
            self.response = SimpleNamespace(status_code=status)
    parent = SimpleNamespace(name="parent", bronze_table="bronze_parent", parent=None, incremental=True, per_page=100)
    child = SimpleNamespace(name="child", bronze_table="bronze_child", per_page=100,
                            parent=SimpleNamespace(endpoint="parent"), incremental=True)
    for scenario in ("complete", "duplicates", "disabled", "declared", "declared_now_available", "partial_page", "merge_failure", "disabled_parent", "archive_failure", "checkpoint_failure"):
        written, watermarks = [], []
        def records(session, base, path, headers, params, per_page):
            # No changed parent since the watermark, but its child has new data.
            # Filtering parent discovery would hide the child entirely.
            if headers.get("endpoint") == "parent" and params.get("since"):
                return
            if path == "disabled":
                raise Disabled("tool absent", 403 if scenario == "disabled" else 404)
            yield {"id": 1, "updated_at": "2026-09-10"}
            if scenario == "duplicates":
                yield {"id": 1, "updated_at": "2026-09-10"}
            if scenario == "partial_page" and path == "good":
                raise Disabled("failure after page one", 404)
        def paths(ep, company, projects, parents):
            if scenario == "disabled_parent" and ep.name == "parent":
                return [("disabled", 7)]
            # "declared": the parent's project 8 gap is declared; the child has no gap.
            gap = scenario == "disabled" or (scenario == "declared" and ep.name == "parent")
            if scenario == "declared_now_available" and ep.name == "parent":
                return [("good", 7), ("good", 8)]
            return [("good", 7)] + ([("disabled", 8)] if gap else [])
        def merge(spark, rows, table, keys):
            if scenario == "merge_failure" and table == "bronze_parent":
                raise ValueError("conflicting key")
            written.append(table)
            return len({json.dumps(row, sort_keys=True) for row in rows})
        with tempfile.TemporaryDirectory() as temp:
            scope = dict(
                ordered=[parent, child], project_ids=[7, 8], batch_id="batch-test",
                DIAG=temp, os=os, _json=json, print=lambda *a, **k: None,
                settings=SimpleNamespace(company_id=1, base_url="unused"), session=None, token=None,
                spark=SimpleNamespace(createDataFrame=lambda rows, schema: rows),
                px=SimpleNamespace(build_headers=lambda token, company, ep: {"endpoint": ep.name},
                    build_params=lambda ep, company, since: {"since": since},
                    iter_records=records, stamp_project=lambda record, pid: dict(record, normalized_project=pid),
                    to_bronze_row=lambda record, *a: record, bronze_schema=lambda: None,
                    bronze_merge_keys=lambda ep: ["id"], is_tool_not_enabled=lambda exc: isinstance(exc, Disabled)),
                ps=SimpleNamespace(expand_paths=paths, collect_parent_ids=lambda records, parent: [r["id"] for r in records],
                                   declared_unavailable=lambda ep, pid: "tool not enabled" if (
                                       scenario in ("declared", "declared_now_available") and ep.name == "parent" and pid == 8) else None,
                                   normalize_records=lambda ep, record, path: [record]),
                fc=SimpleNamespace(utc_now=lambda: "now", row_hash=lambda r: "hash",
                                   merge_delta=merge, log_run=lambda *a: None),
                wm=SimpleNamespace(read_since=lambda *a: "previous-watermark", high_water=lambda *a: "high",
                                   write_watermark=lambda *a: watermarks.append(a)))
            if scenario in ("archive_failure", "checkpoint_failure"):
                def unavailable_archive(path, *args, **kwargs):
                    if str(path).endswith(".jsonl" if scenario == "archive_failure" else ".audit.json"):
                        raise OSError("archive storage unavailable")
                    return open(path, *args, **kwargs)
                scope["open"] = unavailable_archive
            if scenario == "checkpoint_failure":
                try:
                    exec(compile(extract, "extract:scopes", "exec"), scope)
                except OSError:
                    pass
                else:
                    raise AssertionError("checkpoint failure did not stop extraction")
                assert written == ["bronze_parent"]
                assert not (Path(temp) / "ingestion" / "batch-test.json").exists()
                continue
            exec(compile(extract, "extract:scopes", "exec"), scope)
            for audit in scope["endpoint_audit"]:
                checkpoint = Path(temp) / "ingestion" / "batch-test" / (audit["endpoint"] + ".audit.json")
                assert json.loads(checkpoint.read_text()) == {"batch": "batch-test", **audit}
            failed = scenario in ("partial_page", "merge_failure", "archive_failure")
            try:
                exec(compile(finish, "extract:evidence", "exec"), scope)
            except RuntimeError:
                assert scenario not in ("complete", "duplicates", "declared", "declared_now_available")
            else:
                assert scenario in ("complete", "duplicates", "declared", "declared_now_available")
            evidence = json.loads((Path(temp) / "ingestion" / "batch-test.json").read_text())
            assert evidence == json.loads((Path(temp) / "ingest_run.json").read_text())
            first, second = evidence["endpoints"]
            assert first["full_parent_discovery"] and first["since"] is None
            archive_path = Path(first["raw_archive"])
            if scenario != "archive_failure":
                archived = [json.loads(line) for line in archive_path.read_text().splitlines()]
                assert len(archived) == first["received_rows"] == first["archived_rows"]
                if archived:
                    assert archived[0] == {"path": "good", "project_id": 7,
                                           "record": {"id": 1, "updated_at": "2026-09-10"}}
            if failed:
                assert evidence["status"] == "failed" and not written and not watermarks
                assert first["received_rows"] == (0 if scenario == "archive_failure" else 1)
                assert first["written_rows"] == 0
                assert second["status"] == "failed" and not second["scopes"]
                assert "parent" not in scope["fetched"]
            elif scenario in ("disabled", "disabled_parent"):
                # An undeclared 403/404 still blocks, and records the real status code.
                assert evidence["status"] == "incomplete_scope" and not watermarks
                assert second["status"] == "incomplete_scope"
                code = 403 if scenario == "disabled" else 404
                assert any(s["status"] == f"unavailable_{code}" and s["http_status"] == code
                           for s in first["scopes"])
            elif scenario == "declared":
                # A declared exclusion passes the gate with its reason in the manifest, and
                # the child proceeds for the retrieved parent instead of inheriting a gap.
                assert evidence["status"] == "complete"
                assert first["status"] == "complete" and first["excluded_declared_scopes"] == 1
                gap = next(s for s in first["scopes"] if s["project_id"] == 8)
                assert gap == {"path": "disabled", "project_id": 8, "status": "excluded_declared",
                               "received_rows": 0, "error_type": "Disabled", "http_status": 404,
                               "exclusion_reason": "tool not enabled"}
                assert second["status"] == "complete" and not second["parent_scope_incomplete"]
                assert written == ["bronze_parent", "bronze_child"]
                # The excluded project was not read, so the parent watermark must not move -
                # nor the child's: its records under project 8 were never listed either.
                assert watermarks == [] and second["parent_scope_excluded"]
                assert not second["watermark_advanced"]
            elif scenario == "declared_now_available":
                # A stale declaration is surfaced, not failed, and no longer holds anything back.
                assert evidence["status"] == "complete" and "excluded_declared_scopes" not in first
                assert first["warnings"] == [{"warning": "declared_exclusion_now_available", "project_id": 8}]
                assert [s.get("note") for s in first["scopes"]] == [None, "declared_exclusion_now_available"]
                assert len(watermarks) == 2 and "warnings" not in second
            else:
                assert evidence["status"] == "complete" and len(watermarks) == 2
                assert written == ["bronze_parent", "bronze_child"]
                assert second["since"] == "previous-watermark"
                assert all(a["written_rows"] == 1 for a in evidence["endpoints"])
                for a in evidence["endpoints"]:
                    assert a["duplicate_rows_removed"] == (1 if scenario == "duplicates" else 0)
                    assert a["received_rows"] == a["archived_rows"] == a["written_rows"] + a["duplicate_rows_removed"]
                    assert a["normalized_rows"] == a["written_rows"] + a["duplicate_rows_removed"]
                before = archive_path.read_bytes()
                written.clear()
                watermarks.clear()
                checkpoint_path = Path(temp) / "ingestion" / "batch-test" / "parent.audit.json"
                checkpoint_before = checkpoint_path.read_bytes()
                try:
                    exec(compile(extract, "extract:replay", "exec"), scope)
                except FileExistsError:
                    pass
                else:
                    raise AssertionError("replay replaced the original endpoint checkpoint")
                assert scope["failures"] and not written and not watermarks
                assert archive_path.read_bytes() == before, "replay overwrote the source archive"
                assert checkpoint_path.read_bytes() == checkpoint_before
                manifest_path = Path(temp) / "ingestion" / "batch-test.json"
                manifest_before = manifest_path.read_bytes()
                try:
                    exec(compile(finish, "extract:replay-evidence", "exec"), scope)
                except FileExistsError:
                    pass
                else:
                    raise AssertionError("replay replaced the original manifest")
                assert manifest_path.read_bytes() == manifest_before


def test_reject_evidence_is_complete():
    # A failure larger than the old 1,000-row cap must retain its full evidence.
    class Frame:
        def __init__(self, rows):
            self.rows = rows
        def limit(self, count):
            return Frame(self.rows[:count])
        def withColumn(self, *args):
            return self
        def selectExpr(self, *args):
            return self
        @property
        def write(self):
            return self
        def format(self, *args):
            return self
        def mode(self, *args):
            return self
        def saveAsTable(self, table):
            saved.extend(self.rows)
            assert table == dq.REJECTS_TABLE
    saved = []
    functions = SimpleNamespace(lit=lambda value: value)
    with patch.dict(sys.modules, {"pyspark": SimpleNamespace(),
                                 "pyspark.sql": SimpleNamespace(functions=functions)}):
        dq._persist_rejects(None, dq.not_null("source", "id"), Frame(list(range(1507))), "test")
    assert saved == list(range(1507))


def test_empty_freshness():
    con = duckdb.connect()
    con.execute("CREATE TABLE source (loaded_at TIMESTAMP)")
    sql = dq.freshness("source", "loaded_at", 24).failing_sql.replace("`", '"')
    sql = sql.replace("CURRENT_TIMESTAMP()", "CURRENT_TIMESTAMP")
    assert len(con.execute(sql).fetchall()) == 1
    con.execute("INSERT INTO source VALUES (NULL)")
    assert len(con.execute(sql).fetchall()) == 1
    con.execute("INSERT INTO source VALUES (CURRENT_TIMESTAMP - INTERVAL 25 HOURS)")
    assert len(con.execute(sql).fetchall()) == 1
    con.execute("INSERT INTO source VALUES (CURRENT_TIMESTAMP)")
    assert con.execute(sql).fetchall() == []
    con.close()


def test_evidence_write_failure():
    # Execute the generated evaluation cell, not a second implementation of the gate.
    source = "".join(deploy_dq.build_notebook()["cells"][2]["source"])
    passing = dq.Result(dq.not_null("t", "id"), 0)
    with tempfile.TemporaryDirectory() as temp:
        scope = dict(suite=SimpleNamespace(run=lambda *a, **k: [passing]),
                     spark=object(), batch_id="test", DIAG=temp, dq=dq,
                     summarise=lambda results: "one passed", __builtins__=__builtins__)
        import json
        scope["json"] = json
        with patch.object(dq, "_persist_results", side_effect=OSError("disk unavailable")):
            try:
                exec(compile(source, "dq:evaluate", "exec"), scope)
            except RuntimeError as exc:
                assert "pipeline blocked" in str(exc)
            else:
                raise AssertionError("missing audit evidence permitted publication")
        assert json.loads((Path(temp) / "dq_run.json").read_text())["batch"] == "test"


def test_outbuild_link_keys():
    import extract_outbuild_local
    extract_outbuild_local._selftest()


def test_outbuild_extract():
    """cd_02_extract_outbuild: retry, composite keys, raw archive, and the failure policy."""
    import hashlib
    import json
    import re
    import urllib.error
    import deploy_outbuild
    import extract_outbuild_local as ob

    # `consumed` must match what the SQL actually reads, or the policy guards the wrong tables.
    endpoints = ob.load_registry()
    sql = "\n".join(p.read_text(encoding="utf-8") for p in
                    (Path(__file__).resolve().parents[2] / "02-transformation" / "sql").rglob("*.sql"))
    read = set(re.findall(r"\bcd_bronze_outbuild_[a-z_]+", sql))
    assert {e["bronze_table"] for e in endpoints if e.get("consumed")} == read == {
        "cd_bronze_outbuild_projects", "cd_bronze_outbuild_activities"}, read
    assert any(remote == "Files/lib/extract_outbuild_local.py" and local.exists()
               for local, remote in deploy_outbuild.UPLOADS)
    source = "\n".join("".join(c["source"]) for c in make_notebooks.EXTRACT_OUTBUILD)
    assert 'fc.get_secret("OUTBUILD_API_TOKEN")' in source and "ob.extract(" in source

    # Transient 5xx retries with bounded backoff; a persistent one raises; 4xx never retries.
    class Response:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b'{"tasks": [{"id": 1}], "hasNextPage": false}'
    def http(code):
        return urllib.error.HTTPError("u", code, "x", {}, None)
    for outcomes, calls, ok in (([http(504), http(502), Response()], 3, True),
                                ([http(504)] * 4, 4, False),
                                ([http(401)], 1, False)):
        sleeps = []
        with patch.object(ob.urllib.request, "urlopen", side_effect=outcomes) as urlopen, \
             patch.object(ob.time, "sleep", sleeps.append):
            try:
                assert ob.fetch_page("/tasks", "t", 1) == ([{"id": 1}], False)
            except urllib.error.HTTPError:
                assert not ok
            else:
                assert ok
        assert urlopen.call_count == calls and sum(sleeps) <= 14, (calls, sleeps)

    reg = {e["name"]: e for e in endpoints}
    chosen = [reg[n] for n in ("projects", "activities", "tasks", "roadblock_tasks",
                               "schedule_impact_requests")]
    data = {"projects": [{"id": 5}], "activities": [{"id": 7, "projectId": 5}],
            "tasks": [{"id": 8}],
            "roadblock_tasks": [{"roadblock_id": 1, "task_id": 2, "project_id": 5},
                                {"roadblock_id": 1, "task_id": 3, "project_id": 5}]}
    for broken, status in ((None, "complete"), ("tasks", "complete_with_warnings"),
                           ("activities", "failed")):
        written = {}
        def pull(ep, tok):
            if ep["name"] == broken:
                raise http(504)
            return data[ep["name"]]
        def write(table, rows):
            written[table] = rows
            return len(rows)
        with tempfile.TemporaryDirectory() as temp, patch.object(ob, "pull", pull):
            manifest = ob.extract(chosen, "t", "b1", temp, write)
            assert json.loads((Path(temp) / "ingestion" / "b1.json").read_text()) == manifest
            assert json.loads((Path(temp) / "outbuild_run.json").read_text()) == manifest
            archive = Path(temp) / "ingestion" / "b1" / "roadblock_tasks.jsonl"
            assert [json.loads(l) for l in archive.read_text().splitlines()] == data["roadblock_tasks"]
            try:   # a replay of the same batch must not overwrite its evidence
                ob.extract(chosen, "t", "b1", temp, write)
            except FileExistsError:
                pass
            else:
                raise AssertionError("replay overwrote the batch manifest")
        by = {a["endpoint"]: a for a in manifest["endpoints"]}
        assert manifest["status"] == status and manifest["failure_policy"] == ob.FAILURE_POLICY
        assert manifest["blocking_failures"] == (["activities"] if broken == "activities" else [])
        assert manifest["warnings"] == (["tasks"] if broken == "tasks" else [])
        assert by["schedule_impact_requests"]["status"] == "skipped"
        if broken:
            assert by[broken]["status"] == "failed" and "504" in by[broken]["error"]
            assert by[broken]["written_rows"] == 0
        # The other endpoints still land; composite keys stay distinct per pair.
        link = written["cd_bronze_outbuild_roadblock_tasks"]
        assert [r["_merge_key"] for r in link] == ["1|2|5", "1|3|5"]
        assert set(link[0]) == set(deploy_landing.BRONZE_COLUMNS) | {"_merge_key"}
        assert written["cd_bronze_outbuild_projects"][0]["_merge_key"] == "5|"
        assert link[0]["_row_hash"] == hashlib.sha256(link[0]["payload"].encode()).hexdigest()


def test_pipeline():
    import json
    with tempfile.TemporaryDirectory() as tmp, patch.object(deploy_pipeline, "PIPELINE_DIR", Path(tmp)):
        ids = {nb: nb for _, nb, _ in deploy_pipeline.STAGES}
        files = deploy_pipeline.build(ids)
    activities = json.loads(files["pipeline-content.json"])["properties"]["activities"]
    by_name = {a["name"]: a for a in activities}
    assert len(by_name) == len(activities)
    visited = set()
    def ancestors(name):
        deps = {d["activity"] for d in by_name[name]["dependsOn"]}
        return deps.union(*(ancestors(d) for d in deps)) if deps else set()
    # Landing must finish before extraction starts: running alongside it starved the Spark
    # session pool, and landing after it could overwrite fresher bronze with a replay.
    assert {"Land To Bronze", "Land Manual Input"} <= ancestors("Extract Procore")
    # Outbuild: after landing (its live pull must win over a replayed landing batch), serial
    # with Procore rather than competing for a Spark session, and gating silver.
    assert {"Land To Bronze", "Land Manual Input"} <= ancestors("Extract Outbuild")
    assert "Extract Outbuild" in ancestors("Extract Procore")
    assert by_name["Extract Procore"]["policy"]["retry"] == 0, "a same-hour retry has no quota"
    assert by_name["Extract Procore"]["policy"]["timeout"] == "0.02:00:00"
    assert by_name["Land To Bronze"]["policy"]["timeout"] == "0.01:00:00"
    def visit(name, active):
        assert name in by_name, f"missing dependency {name}"
        assert name not in active, f"pipeline cycle at {name}"
        if name in visited:
            return
        for dep in by_name[name]["dependsOn"]:
            assert dep["dependencyConditions"] == ["Succeeded"]
            visit(dep["activity"], active | {name})
        visited.add(name)
    for name in by_name:
        visit(name, set())
    silver_deps = {d["activity"] for d in by_name["Bronze To Silver"]["dependsOn"]}
    assert {"Extract Procore", "Extract Outbuild", "Ingest Sage", "Land To Bronze", "Land Manual Input"} <= silver_deps
    assert by_name["Data Quality Gate"]["dependsOn"] == [
        {"activity": "Build Gold", "dependencyConditions": ["Succeeded"]}]
    # The only frame after autosync is off: strictly behind a passed gate, and not retried.
    assert by_name["Publish Models"]["dependsOn"] == [
        {"activity": "Data Quality Gate", "dependencyConditions": ["Succeeded"]}]
    assert by_name["Publish Models"]["typeProperties"]["notebookId"] == "cd_50_publish_models"
    assert by_name["Publish Models"]["policy"]["retry"] == 0


def test_publish_models():
    import json
    import os
    nb = deploy_publish.build_notebook()
    setup, publish = ("".join(c["source"]) for c in nb["cells"][1:])
    gate = "20260913T060000Z"

    def run(before, after=None, fail_refresh=None, names=None, settings_status=204):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "heartbeat_run.json").write_text(json.dumps({"run_id": gate}))
            scope = {}
            exec(compile(setup, "publish:setup", "exec"), scope)
            shown, calls = dict(before), []
            listing = [{"name": n, "id": n.lower()} for n in (names or deploy_publish.MODEL_NAMES)]
            def pbi(method, url, tok, body=None):
                calls.append((method, url, body))
                if url.endswith("/datasets"):
                    return 200, {"value": listing}
                if url.endswith("/capacities"):
                    return 200, {"@odata.context": "https://cluster/v1.0/myorg/$metadata#capacities"}
                if "/settings" in url:
                    return settings_status, {}
                return 200, {"model": {"id": 7}}
            def reframe(dataset_id, tok, timeout):
                calls.append(("REFRESH", dataset_id, None))
                if dataset_id == fail_refresh:
                    raise RuntimeError("refresh failed")
                shown[dataset_id] = (after or {}).get(dataset_id, {"run_id": gate, "status": "ok"})
                return {"status": "Completed", "requestId": dataset_id}
            def dax(dataset_id, tok, query):
                if isinstance(shown[dataset_id], Exception):
                    raise shown[dataset_id]
                return [{"[RunId]": shown[dataset_id]["run_id"], "[Status]": shown[dataset_id]["status"]}]
            sent = []
            scope.update(DIAG=tmp, pbi=pbi, reframe=reframe, dax=dax,
                         notebookutils=SimpleNamespace(credentials=SimpleNamespace(getToken=lambda aud: "t")))
            out = io.StringIO()
            # notify returns None: no webhook configured, so the notebook must warn loudly.
            with patch.object(fabric_common, "notify", side_effect=lambda subject, body: sent.append(body)), \
                    contextlib.redirect_stdout(out):
                try:
                    exec(compile(publish, "publish:run", "exec"), scope)
                    error = None
                except Exception as exc:
                    error = exc
            record = json.loads(Path(tmp, "publish_run.json").read_text())
            assert (error is not None) == ("NO ALERT WAS SENT" in out.getvalue()), out.getvalue()
        return error, record, calls, sent

    old = {"run_id": "20260912T060000Z", "status": "ok"}
    report, pqp = "affect project report", "project quality plan"
    error, record, calls, sent = run({report: old, pqp: RuntimeError("never framed")})
    assert error is None and record["ok"] and not sent, error
    posts = [c for c in calls if c[0] == "POST"]
    assert [c[2] for c in posts] == [{"directLakeAutoSync": False}] * 2
    # autosync is off on BOTH before the FIRST refresh, and refreshes are serial in order
    assert calls.index(posts[-1]) < calls.index(("REFRESH", report, None)) < calls.index(("REFRESH", pqp, None))

    error, record, calls, sent = run({report: old, pqp: old}, fail_refresh=pqp)
    assert error and not record["ok"] and ("REFRESH", pqp, None) in calls
    assert gate in sent[0] and "Affect Project Report" in sent[0] and "20260912T060000Z" in sent[0]

    error, record, _, sent = run({report: {"run_id": gate, "status": "ok"}, pqp: old})
    assert "AUTO-FRAMING" in str(error) and record["auto_framed"] == ["Affect Project Report"] and sent

    error, _, _, _ = run({report: old, pqp: old}, after={pqp: {"run_id": gate, "status": "blocked"}})
    assert "Project Quality Plan" in str(error)

    error, _, calls, _ = run({report: old, pqp: old}, names=deploy_publish.MODEL_NAMES + ["Project Quality Plan"])
    assert "exactly one" in str(error) and not any(c[0] in ("POST", "REFRESH") for c in calls)

    # Autosync cannot be disabled: both refreshes still run, the error is recorded, and the
    # activity fails at the end with an alert.
    error, record, calls, sent = run({report: old, pqp: old}, settings_status=500)
    assert "AUTOMATIC UPDATE NOT DISABLED" in str(error) and not record["ok"], error
    assert ("REFRESH", report, None) in calls and ("REFRESH", pqp, None) in calls
    assert all(m["autosync_disabled"] is False and "expected 204" in m["autosync_error"] for m in record["models"])
    assert all(m["after"] == {"run_id": gate, "status": "ok"} for m in record["models"]) and sent
    assert record["alert_sent"] is False
    print("  publish: autosync off first, serial refresh, auto-frame, split release and status all fail loudly")


def test_lineage_bindings():
    fields = [{"field": {"Column": {"Property": "Amount", "Expression": {"SourceRef": {"Entity": "fct_Invoice"}}}}},
              {"nested": {"Measure": {"Property": "Total Billed", "Expression": {"SourceRef": {"Entity": "_Measures"}}}}}]
    assert set(bindings(fields)) == {("fct_Invoice", "Amount", "Column"), ("_Measures", "Total Billed", "Measure")}


def test_missing_manual_csv_preserves_bronze():
    source = "".join(deploy_manual.build_notebook()["cells"][2]["source"])
    scope = dict(SPEC={"wins": []}, MANUAL_DIR="Files/_manual", TYPES={},
                 StructType=lambda fields: fields,
                 notebookutils=SimpleNamespace(fs=SimpleNamespace(exists=lambda path: False)),
                 spark=SimpleNamespace(catalog=SimpleNamespace(tableExists=lambda table: True),
                                       table=lambda table: SimpleNamespace(count=lambda: 7)))
    # Spark has no writer here: any attempt to overwrite an existing table fails the test.
    exec(compile(source, "manual:load", "exec"), scope)
    assert scope["loaded"]["wins"] == {"rows": 7, "source": "existing bronze preserved"}
    def unavailable(path):
        raise OSError("storage unavailable")
    scope["notebookutils"].fs.exists = unavailable
    try:
        exec(compile(source, "manual:load", "exec"), scope)
    except OSError:
        pass
    else:
        raise AssertionError("storage failure was treated as missing input")
    # A supplied but empty export is also not proof that all existing records were deleted.
    guard = source[source.index("    if exists and"):source.index("    out =")]
    for incoming, existing, blocked in (([], [1], True), ([], [], False), ([1], [1], False)):
        scope = dict(exists=True, table="cd_bronze_man_wins", df=SimpleNamespace(take=lambda n: incoming),
                     spark=SimpleNamespace(catalog=SimpleNamespace(tableExists=lambda table: True),
                                           table=lambda table: SimpleNamespace(take=lambda n: existing)))
        try:
            exec(compile(textwrap.dedent(guard), "manual:empty-snapshot", "exec"), scope)
        except ValueError as exc:
            assert blocked and "preserved" in str(exc)
        else:
            assert not blocked


def test_build_timestamp():
    from seedrunner import split_statements
    con = duckdb.connect()
    statements = split_statements((deploy_gold.GOLD_SQL / "07_measures_anchor.sql").read_text())
    for sql in statements:
        con.execute(sql)
    assert con.execute("SELECT _built_at FROM measures_anchor").fetchone()[0] is None
    con.execute("UPDATE measures_anchor SET _built_at = TIMESTAMP '2026-08-28 01:00:00'")
    for sql in statements:
        con.execute(sql)
    assert str(con.execute("SELECT _built_at FROM measures_anchor").fetchone()[0]) == "2026-08-28 01:00:00"
    con.close()
    source = "".join(deploy_gold.build_notebook(deploy_gold.SOURCES["cd"])["cells"][-1]["source"])
    source = source[source.rindex("\nif bad:"):]
    writes = []
    for bad in (["failed check"], []):
        try:
            exec(compile(source, "gold:stamp", "exec"),
                 dict(bad=bad, spark=SimpleNamespace(sql=writes.append), print=lambda *args: None))
        except AssertionError:
            assert bad and not writes
    assert writes == ["UPDATE measures_anchor SET _built_at = CURRENT_TIMESTAMP()"]


def test_candidate_dax_evidence():
    import json
    import validate_model as vm
    module = validate_candidate_model
    record = dict(item_id="isolated", source_run_id="run", kind="test", lakehouse_id="candidate")
    def diagnostic(lakehouse, filename):
        assert lakehouse == "candidate"
        assert filename == "candidate_counts_run.json"
        return dict(run_id="run", validation_lakehouse_id="candidate",
                    gold=[dict(step="verification", ok=True, counts={"dim_Project": 2}, findings=[])],
                    seeds={}, heartbeat={"meta_PipelineRun": 1})
    with tempfile.TemporaryDirectory() as tmp, patch.object(module, "DOCS", Path(tmp)), \
            patch.object(module.dm, "MODEL_TABLES", ["dim_Project"]), \
            patch.object(module.dm, "MEASURES", [("Example", "", "", "")]), \
            patch.object(vm, "pbi_token", return_value="test"), \
            patch.object(vm, "reframe", return_value="Completed"), \
            patch.object(vm, "check_independent_measures", return_value=dict(
                failed=[], not_deployed=[], without_independent_check=[])), \
            patch.object(module.dg, "fetch_diagnostics", side_effect=diagnostic):
        for fail in (False, True):
            def query(model, token, dax):
                assert model == "isolated"
                if fail and "MonthStart" in dax:
                    raise RuntimeError("month measure failed")
                return [{"[dim_Project]": 2}] if "COUNTROWS" in dax else [{"[Example]": None}]
            with patch.object(vm, "dax", side_effect=query):
                try:
                    module.check_model(record)
                    assert not fail
                except RuntimeError:
                    assert fail
            evidence = json.loads((Path(tmp) / "candidate-test-dax-evidence.json").read_text())
            assert bool(evidence["errors"]) == fail
            assert evidence["count_differences"] == []
            assert evidence["queries"]["measures_0"][0]["[Example]"] is None
        assert module.compare_counts({"[dim_Project]": 1}, {"dim_Project": 2})
        assert module.compare_counts({}, {"dim_Project": 2})
        for invalid in (-1, True, "2", 2.0):
            try:
                module.compare_counts({"[dim_Project]": 2}, {"dim_Project": invalid})
            except RuntimeError:
                pass
            else:
                raise AssertionError("invalid expected count accepted")
        fail = False
        with patch.object(module.dm, "MODEL_TABLES", ["dim_Project", "unverified_table"]), \
                patch.object(vm, "dax", side_effect=query):
            try:
                module.check_model(record)
            except RuntimeError:
                pass
            else:
                raise AssertionError("a table without independent count evidence passed")
        evidence = json.loads((Path(tmp) / "candidate-test-dax-evidence.json").read_text())
        assert evidence["counts_without_build_comparison"] == ["unverified_table"]
        for key in ("run_id", "validation_lakehouse_id"):
            stale = dict(diagnostic("candidate", "candidate_counts_run.json"), **{key: "other"})
            with patch.object(module.dg, "fetch_diagnostics", return_value=stale), \
                    patch.object(vm, "dax", side_effect=query):
                try:
                    module.check_model(record)
                except RuntimeError:
                    pass
                else:
                    raise AssertionError("counts from another build or lakehouse passed")
            evidence = json.loads((Path(tmp) / "candidate-test-dax-evidence.json").read_text())
            assert "another run" in evidence["errors"]["validation"]


def test_independent_measure_comparison():
    vm = validate_model
    relationships = [("fct", "ProjectKey", "dim_Project", "ProjectKey"), ("fct", "MonthStart", "dim_Date", "Date"),
                     ("child", "ParentKey", "fct", "Key"), ("man_Input", "ProjectKey", "dim_Project", "ProjectKey")]
    jan, feb = "2026-01-01T00:00:00", "2026-02-01T00:00:00"
    data = dict(
        dim_Project=[{"ProjectKey": "a"}, {"ProjectKey": "b"}],
        dim_Date=[{"Date": jan, "MonthStart": jan}, {"Date": feb, "MonthStart": feb}],
        fct=[{"Key": 1, "ProjectKey": "a", "MonthStart": jan, "Amount": 10.0, "IsOpen": True, "Kind": "Owner"},
             {"Key": 2, "ProjectKey": "a", "MonthStart": feb, "Amount": None, "IsOpen": None, "Kind": "owner"},
             {"Key": 3, "ProjectKey": "b", "MonthStart": feb, "Amount": 5.0, "IsOpen": False, "Kind": "Sub"}],
        child=[{"ParentKey": 1}, {"ParentKey": 3}, {"ParentKey": 99}],
        man_Input=[])
    count = lambda c, s: len(c.rows("fct", s)) or None
    closed = lambda c, s: len([r for r in c.rows("fct", s) if not r["IsOpen"]]) or None  # BLANK = FALSE
    expected = {
        "Amount": lambda c, s: vm._sum(c.rows("fct", s), "Amount"),
        "Rows": count, "Closed": closed,
        "Closure": lambda c, s: vm._div(closed(c, s), count(c, s)),
        "Owner": lambda c, s: len([r for r in c.rows("fct", s) if vm._eq(r["Kind"], "OWNER")]),
        "Children": lambda c, s: len(c.rows("child", s)),  # filtered through fct, orphans only unfiltered
        "Inputs": lambda c, s: len(c.rows("man_Input", s)) or None,
        "Hours": lambda c, s: vm._hours(vm._ts("2026-01-01T10:59:59"), vm._ts(c.now)),
        "MonthOnly": lambda c, s: NotImplemented if s.month is None else 1,
    }
    P, S = vm.PORTFOLIO, vm.Scope
    truth = {P: dict(Amount=15.0, Rows=3, Closed=2, Closure=2 / 3, Owner=2, Children=3, Inputs=None),
             S("a", None, None): dict(Amount=10.0, Rows=2, Closed=1, Closure=0.5, Owner=2, Children=1, Inputs=None),
             S(None, feb, None): dict(Amount=5.0, Rows=2, Closed=2, Closure=1.0, Owner=1, Children=1, Inputs=None),
             S("b", jan, None): dict(Amount=None, Rows=None, Closed=None, Closure=None, Owner=0, Children=0, Inputs=None)}
    def observe(overrides=None):
        rows = []
        for scope, values in truth.items():
            grain = "portfolio" if scope == P else "project" if scope.month is None else "month"
            values = dict(values, Hours=1, MonthOnly=1)
            values.update((overrides or {}).get(grain, {}))
            rows.append((grain, scope, "2026-01-01T11:00:00", "2026-01-01T11:00:00", values))
        return rows
    results = vm.compare_measure_observations(expected, data, relationships, observe(), {"Inputs": ["man_Input"]})
    assert all(r["status"] == "PASS" for r in results.values()), results
    assert results["Inputs"]["note"].startswith("unmeasured - no input")
    assert results["MonthOnly"]["grains"] == {"month": 2}
    for grain, override in (("portfolio", {"Inputs": 0}), ("project", {"Closure": 0}), ("month", {"Amount": 5.01}),
                            ("portfolio", {"Hours": 0}), ("month", {"Owner": None}), ("project", {"Children": 3})):
        bad = vm.compare_measure_observations(expected, data, relationships, observe({grain: override}))
        name = next(iter(override))
        assert bad[name]["status"] == "FAIL" and bad[name]["mismatches"][0]["grain"] == grain, (grain, override)
    assert vm.same_value(0.1 + 0.2, 0.3) and not vm.same_value(0, None) and not vm.same_value(None, 0)
    assert vm._div(0, 5) == 0 and vm._div(None, 5) is None and vm._div(5, 0) is None and vm._div(5, None) is None
    assert vm._hours(vm._ts("2026-01-01T10:59:59"), vm._ts("2026-01-01T11:00:00")) == 1
    assert vm._add(None, None) is None and vm._add(None, 2, -1) == -2
    # Wiring: failures, undeployed measures and unchecked measures become candidate validation errors.
    record = dict(item_id="isolated", source_run_id="run", kind="monthly", lakehouse_id="candidate")
    module = validate_candidate_model
    with tempfile.TemporaryDirectory() as tmp, patch.object(module, "DOCS", Path(tmp)), \
            patch.object(module.dm, "MEASURES", []), patch.object(vm, "pbi_token", return_value="t"), \
            patch.object(vm, "reframe", return_value="Completed"), patch.object(vm, "dax", return_value=[{}]), \
            patch.object(vm, "check_balance_values", return_value=[]), \
            patch.object(vm, "check_spend_status", return_value={}), \
            patch.object(vm, "check_milestone_geometry", return_value=[]), \
            patch.object(vm, "check_independent_measures", return_value=dict(
                failed=["Budget Status"], not_deployed=[], without_independent_check=[])), \
            patch.object(module.dg, "fetch_diagnostics", return_value=None):
        try:
            module.check_model(record)
        except RuntimeError:
            pass
        else:
            raise AssertionError("independent measure failure passed")
        import json
        evidence = json.loads((Path(tmp) / "candidate-monthly-dax-evidence.json").read_text())
        assert "Budget Status" in evidence["errors"]["independent_measures"]


def test_measure_expectations_cover_generator():
    import subprocess
    code = ("{imp}import deploy_model as dm, validate_model as vm;"
            "missing={{m[0] for m in dm.MEASURES}}-set(vm.{fn}())-vm.FIXTURE_ONLY; assert not missing, missing;"
            "import re; used={{t for m in dm.MEASURES for t in re.findall(r'\\b(?:dim|fct|bridge|man|meta|dq|qc_seed)_\\w+', m[1])}};"
            "cols=used-set(vm.RAW_COLUMNS); assert not cols, cols")
    for imp, fn in (("", "monthly_expected"), ("import deploy_model_qc;", "qc_expected")):
        result = subprocess.run([sys.executable, "-c", code.format(imp=imp, fn=fn)],
                                cwd=str(Path(validate_model.__file__).parent), capture_output=True, text=True)
        assert result.returncode == 0, result.stderr[-800:]


def test_candidate_count_snapshot():
    import json
    from datetime import datetime, timezone
    nb = validate_gold_candidate.build_full("count-test", {"id": "validation-only"})
    source = "".join(nb["cells"][-1]["source"])
    source = source[source.index("run_id = "):]
    result = dq.Result(dq.Expectation("checked", "table", "SELECT 1"), 0)
    with tempfile.TemporaryDirectory() as temp:
        source = source.replace("/lakehouse/default/Files/_diag", temp.replace("\\", "/"))
        scope = dict(expectations=SimpleNamespace(build_suite=lambda: SimpleNamespace(run=lambda *a, **k: [result])),
                     dq=SimpleNamespace(_persist_results=lambda *a: None, persist_heartbeat=lambda *a: None,
                                        assert_no_blocking=dq.assert_no_blocking),
                     spark=SimpleNamespace(table=lambda name: SimpleNamespace(count=lambda: 3)),
                     datetime=datetime, timezone=timezone, json=json, os=__import__("os"),
                     candidate_seed_counts={"dim_Date": 10},
                     candidate_gold_evidence=[dict(step="verification", ok=True, counts={"dim_Project": 2})])
        exec(compile(source, "candidate-count-snapshot", "exec"), scope)
        path = Path(temp) / "candidate_counts_count-test.json"
        saved = json.loads(path.read_text())
        assert saved["run_id"] == "count-test" and saved["validation_lakehouse_id"] == "validation-only"
        assert saved["seeds"] == {"dim_Date": 10} and saved["heartbeat"] == {"meta_PipelineRun": 3}
        assert saved["gold"][0]["counts"] == {"dim_Project": 2}
        scope["candidate_seed_counts"]["dim_Date"] = 99
        assert json.loads(path.read_text())["seeds"]["dim_Date"] == 10


def test_gold_manual_count_conservation():
    source = "".join(deploy_gold.build_notebook(deploy_gold.SOURCES["cd"])["cells"][-1]["source"])
    source = source[source.index("tables ="):source.index("# Referential integrity")]
    for before, after in ((0, 0), (3, 3), (3, 2)):
        def sql(query):
            count = after if query.endswith("man_Wins") else 2
            return SimpleNamespace(collect=lambda: [{"n": count}])
        scope = dict(spark=SimpleNamespace(sql=sql), manual_tables=["man_Wins"],
                     loaded={"man_Wins": before}, print=lambda *args: None)
        exec(compile(source, "gold:manual-counts", "exec"), scope)
        assert scope["counts"]["man_Wins"] == after
        assert bool(scope["bad"]) == (before != after)
        if before != after:
            assert "materialisation changed row count" in scope["bad"][0]


def test_balance_reconciliation():
    values = {"Owner": 0, "Sub": -489.94, "Net": 489.94, "Contract": 250_000_000}
    row = {f"[{prefix}{key}]": value for key, value in values.items() for prefix in ("", "Expected")}
    assert len(validate_model.check_balance_values(row)) == 4
    for bad in (None, float("nan"), float("inf"), 750_000_000):
        try:
            validate_model.check_balance_values({**row, "[Contract]": bad})
        except AssertionError:
            pass
        else:
            raise AssertionError("missing, nonfinite or overstated contract passed")


def test_dax_response_errors():
    import copy
    import io
    import json
    vm = validate_model
    complete = {"results": [{"tables": [{"rows": [{"[value]": None}, {"[value]": 0}]}]}]}
    def run(body):
        def respond(request, timeout):
            assert json.loads(request.data)["serializerSettings"]["includeNulls"] is True
            return io.BytesIO(json.dumps(body).encode())
        with patch.object(vm.urllib.request, "urlopen", side_effect=respond):
            return vm.dax("candidate", "test", "EVALUATE ROW(\"value\", BLANK())")
    assert run(complete) == [{"[value]": None}, {"[value]": 0}]
    assert run({"results": [{"tables": [{"rows": []}]}]}) == []
    for level in range(3):
        partial = copy.deepcopy(complete)
        node = partial
        for key in ("results", "tables")[:level]:
            node = node[key][0]
        node["error"] = {"code": "LimitedData", "message": "More than allowed rows"}
        try:
            run(partial)
        except vm.dp.FabricError as exc:
            assert "LimitedData" in str(exc)
        else:
            raise AssertionError("partial HTTP-200 response accepted")
    for malformed in ({}, {"results": []}, {"results": complete["results"] * 2},
                      {"results": [{"tables": [{}]}]},
                      {"results": [{"tables": [{"rows": [None]}]}]}):
        try:
            run(malformed)
        except vm.dp.FabricError:
            pass
        else:
            raise AssertionError("malformed result accepted")


def test_refresh_request_identity():
    import io
    import json
    import time
    vm = validate_model
    class Response(io.BytesIO):
        headers = {"Location": vm.PBI_API + "/datasets/candidate/refreshes/ours"}
    observed = []
    histories = iter([
        [{"requestId": "old", "status": "Completed"}],
        [{"requestId": "unrelated", "status": "Completed"}, {"requestId": "ours", "status": "Unknown"}],
        [{"requestId": "unrelated", "status": "Completed"}, {"requestId": "ours", "status": "Completed"}],
    ])
    def request(req, timeout):
        observed.append(req.get_method())
        return Response(b"") if req.get_method() == "POST" else Response(json.dumps({"value": next(histories)}).encode())
    with patch.object(vm.urllib.request, "urlopen", side_effect=request), patch.object(time, "sleep"):
        result = vm.reframe("candidate", "test")
    assert result == {"requestId": "ours", "status": "Completed"}
    assert observed == ["POST", "GET", "GET", "GET"]
    for status in ("Failed", "Cancelled", "Disabled"):
        with patch.object(vm.urllib.request, "urlopen", return_value=Response(json.dumps({"value": [
                {"requestId": "other", "status": "Completed"}, {"requestId": "ours", "status": status}]}).encode())):
            try:
                vm.wait_refresh("candidate", "test", "ours")
            except vm.dp.FabricError as exc:
                assert "ours" in str(exc) and status in str(exc)
            else:
                raise AssertionError("unrelated completed refresh hid terminal failure")
    with patch.object(vm.urllib.request, "urlopen") as network:
        try:
            vm.wait_refresh("candidate", "test", "ours", timeout=0)
        except vm.dp.FabricError as exc:
            assert "do not resubmit" in str(exc)
        else:
            raise AssertionError("unobserved refresh passed")
        network.assert_not_called()


def test_daily_snapshot():
    """fct_DailySnapshot: executes the generated gate + capture cells against DuckDB."""
    import json
    from datetime import date, datetime
    import seedrunner
    sys.path.insert(0, str(seedrunner.CHARLEY_DEV / "02-transformation" / "dq"))
    import expectations
    con = seedrunner.build()
    con.execute("CREATE TABLE meta_PipelineRun (RunId VARCHAR, RunAt TIMESTAMP, Stage VARCHAR, Status VARCHAR, "
                "Expectations BIGINT, Failing BIGINT, Blocking BIGINT)")

    class DuckSpark:
        corrupt = None  # SQL run straight after the capture INSERT, to fake a bad write
        def sql(self, query):
            rows = con.execute(query.replace("`", '"').replace(") USING DELTA", ")")).fetchall()
            if self.corrupt and query.lstrip().startswith("INSERT INTO fct_DailySnapshot"):
                con.execute(self.corrupt)
            return SimpleNamespace(count=lambda: len(rows))
        def table(self, name):
            return SimpleNamespace(schema=SimpleNamespace(fields=[
                SimpleNamespace(name=r[0], dataType=SimpleNamespace(simpleString=lambda t=r[1]: t.lower()))
                for r in con.execute(f'DESCRIBE "{name}"').fetchall()]))

    cells = deploy_dq.build_notebook()["cells"]
    gate_and_capture = "".join(cells[3]["source"]) + "\n" + "".join(cells[4]["source"])
    passing = [dq.Result(dq.not_null("t", "id"), 0)]
    blocked = [dq.Result(dq.not_null("t", "id"), 3)]
    spark = DuckSpark()

    def run(batch_id, results=passing, meta_status=None):
        status = "blocked" if any(r.blocking for r in results) else "ok"
        con.execute("INSERT INTO meta_PipelineRun VALUES (?, CURRENT_TIMESTAMP, 'dq_gate', ?, 1, 0, ?)",
                    [batch_id, meta_status or status, int(status != "ok")])  # what the heartbeat cell writes
        alerts = []
        with tempfile.TemporaryDirectory() as diag:
            (Path(diag) / "gold_schema.json").write_text("{}")
            (Path(diag) / "heartbeat_run.json").write_text(json.dumps({"run_id": batch_id}))
            scope = dict(results=results, dq=dq, fc=SimpleNamespace(notify=lambda *a, **k: alerts.append(a)),
                         summarise=expectations.summarise, spark=spark, batch_id=batch_id, DIAG=diag,
                         __builtins__=__builtins__)
            with contextlib.redirect_stdout(io.StringIO()):
                exec(compile(gate_and_capture, "dq:gate+snapshot", "exec"), scope)
            record = json.loads((Path(diag) / "snapshot_run.json").read_text())
            assert json.loads((Path(diag) / "heartbeat_run.json").read_text())["snapshot_status"] == record["status"]
            if record["status"] == "ok":
                assert not alerts
                assert "SnapshotDate" in dict(json.loads((Path(diag) / "gold_schema.json").read_text())["fct_DailySnapshot"])
            else:
                assert alerts and "SNAPSHOT FAILED" in alerts[0][0] and record["alert_sent"] is False
        return record

    def snap(day, column="OpenSubmittals"):
        return con.execute(f"SELECT COUNT(*), SUM({column}), MIN(RunId) FROM fct_DailySnapshot "
                           f"WHERE SnapshotDate = DATE '{day}'").fetchone()
    run("20260115T230000Z")
    rows, jan15, _ = snap("2026-01-15")
    assert jan15 == 2 and rows == con.execute("SELECT COUNT(*) FROM v_DailySnapshotLive").fetchone()[0]
    # A submittal closes retroactively: current-state facts now say January had one open.
    con.execute("UPDATE fct_RfiSubmittal SET IsOpen = FALSE, IsPastDue = FALSE WHERE ItemType = 'Submittal' AND IsPastDue")

    # Idempotent re-run on one date: replaced, never duplicated.
    run("20260131T230000Z")
    run("20260131T231500Z")
    assert snap("2026-01-31") == (rows, 1, "20260131T231500Z"), snap("2026-01-31")
    run("20260210T230000Z")

    # Failed gate: raises before capture, appends nothing.
    try:
        run("20260220T230000Z", blocked)
    except RuntimeError:
        pass
    else:
        raise AssertionError("a blocked gate reached the snapshot capture")
    assert snap("2026-02-20")[0] == 0

    # Bad write: post-capture verification removes this run's rows, alerts and records the
    # failure - but does NOT fail the gate, which would block publishing validated gold.
    spark.corrupt = "UPDATE fct_DailySnapshot SET OpenRfis = COALESCE(OpenRfis, 0) + 1 WHERE SnapshotDate = DATE '2026-02-25'"
    record = run("20260225T230000Z")
    assert record["status"] == "failed" and "equals live facts" in record["error"], record
    spark.corrupt = None
    assert snap("2026-02-25")[0] == 0

    # Failed validation of a same-date re-run: staged rows are rejected BEFORE the delete,
    # so the earlier good capture of that date survives.
    good = con.execute("SELECT * FROM fct_DailySnapshot WHERE SnapshotDate = DATE '2026-02-10' ORDER BY ProjectKey").fetchall()
    record = run("20260210T231500Z", meta_status="blocked")
    assert record["status"] == "failed" and "staged snapshot failed validation" in record["error"], record
    assert con.execute("SELECT * FROM fct_DailySnapshot WHERE SnapshotDate = DATE '2026-02-10' ORDER BY ProjectKey").fetchall() == good

    # Money is stored to the cent, so float noise in the facts cannot fail the reconciliation.
    con.execute("BEGIN")
    try:
        con.execute("UPDATE fct_Invoice SET Balance = Balance + 0.001234, Amount = Amount + 1e-9")
        assert con.execute("SELECT COUNT(*) FROM v_DailySnapshotLive WHERE ArOutstanding <> ROUND(ArOutstanding, 2) "
                           "OR BilledToDate <> ROUND(BilledToDate, 2)").fetchone()[0] == 0
    finally:
        con.execute("ROLLBACK")

    # History is not rewritten by the closure.
    assert snap("2026-01-15")[:2] == (rows, 2)

    # Model: month end = last capture in the month; BLANK before history and after it.
    from decimal import Decimal
    # The shapes the live DAX reader returns: ISO datetimes and JSON floats.
    iso = lambda v: (datetime(v.year, v.month, v.day).isoformat() if isinstance(v, date)
                     else float(v) if isinstance(v, Decimal) else v)
    def load(table):
        cur = con.execute(f'SELECT * FROM "{table}"')
        names = [d[0] for d in cur.description]
        return [{n: iso(v) for n, v in zip(names, row)} for row in cur.fetchall()]
    live = ["dim_Date", "dim_Project", "fct_DailySnapshot", "fct_RfiSubmittal", "fct_QualityItem", "fct_Invoice",
            "fct_BudgetLine", "fct_FinancialPeriod", "fct_ChangeOrder"]
    c = validate_model.Recompute({t: load(t) for t in live}, deploy_model.RELATIONSHIPS)
    E = validate_model.monthly_expected()
    month = lambda m: validate_model.Scope(None, m, None)
    assert E["Open Submittals (Month End)"](c, month("2026-01-01T00:00:00")) == 1
    assert E["Open Submittals (Month End)"](c, month("2025-12-01T00:00:00")) is None
    assert E["Open Submittals (Month End)"](c, month("2026-03-01T00:00:00")) is None
    assert E["Open Submittals (Month End)"](c, validate_model.PORTFOLIO) == 1
    assert E["Snapshot History Note"](c, month("2026-03-01T00:00:00")) == \
        "History starts 2026-01-15; earlier months are unavailable, not zero"
    blank_dax = [m[1] for m in deploy_model.MEASURES if m[0].endswith("(Month End)")]
    assert len(blank_dax) == len(deploy_model.SNAPSHOT_KPIS) and not any("COALESCE" in d for d in blank_dax)

    # Same logic as the live measures: the latest capture equals each measure's independent
    # recomputation, per project and for the portfolio (UNMATCHED AR included).
    scopes = [validate_model.PORTFOLIO] + [validate_model.Scope(p["ProjectKey"], None, None) for p in c.data["dim_Project"]]
    for name, _, _ in deploy_model.SNAPSHOT_KPIS:
        if name in E:
            for s in scopes:
                assert validate_model.same_value(E[f"{name} (Month End)"](c, s), E[name](c, s)), (name, s)

    # A void CO is neither pending nor approved: the capture must not count it either.
    approved = "SELECT SUM(ApprovedChangeOrders) FROM v_DailySnapshotLive"
    before = con.execute(approved).fetchone()[0]
    con.execute("BEGIN")
    try:
        con.execute("INSERT INTO fct_ChangeOrder SELECT * REPLACE ('COVOID' AS ChangeOrderKey, 'Void' AS StatusLabel, "
                    "FALSE AS IsPending, 999.0 AS Amount) FROM fct_ChangeOrder LIMIT 1")
        assert con.execute(approved).fetchone()[0] == before, "void change order captured as approved"
    finally:
        con.execute("ROLLBACK")

    # DQ rule mutations on the latest capture.
    rules = {e.name: e for e in expectations.snapshot_suite("2026-02-10").expectations}
    def failing(name, *mutations):
        con.execute("BEGIN")
        try:
            for m in mutations:
                con.execute(m)
            return len(con.execute(rules[name].failing_sql.replace("`", '"')).fetchall())
        finally:
            con.execute("ROLLBACK")
    recon, unique = "fct_DailySnapshot equals live facts at capture", "fct_DailySnapshot.ProjectKey_SnapshotDate.unique"
    passing_runs = "fct_DailySnapshot rows come only from passing runs"
    historical = "fct_DailySnapshot historical rows from runs not recorded as passing"
    assert all(failing(n) == 0 for n in rules), {n: failing(n) for n in rules}
    for col in expectations.SNAPSHOT_VALUES.split(", ")[1:]:
        assert failing(recon, f"UPDATE fct_DailySnapshot SET {col} = COALESCE({col}, 0) + 1 "
                              "WHERE SnapshotDate = DATE '2026-02-10' AND ProjectKey = 'P1'"), col
    assert failing(recon, "DELETE FROM fct_DailySnapshot WHERE SnapshotDate = DATE '2026-02-10' AND ProjectKey = 'P2'")
    assert failing(recon, "UPDATE fct_QualityItem SET IsOpen = FALSE WHERE ItemType = 'PunchItem'")
    assert failing(unique, "INSERT INTO fct_DailySnapshot SELECT * FROM fct_DailySnapshot "
                           "WHERE SnapshotDate = DATE '2026-02-10' LIMIT 1")
    # This capture from a non-passing run blocks; an orphan in HISTORY only warns.
    assert failing(passing_runs, "UPDATE fct_DailySnapshot SET RunId = '20260220T230000Z' WHERE SnapshotDate = DATE '2026-02-10'")
    orphan = ("INSERT INTO fct_DailySnapshot SELECT * REPLACE ('20260220T230000Z' AS RunId, "
              "DATE '2026-02-20' AS SnapshotDate) FROM fct_DailySnapshot WHERE SnapshotDate = DATE '2026-02-10'")
    assert failing(passing_runs, orphan) == 0 and failing(historical, orphan)
    assert rules[historical].severity == dq.SEVERITY_WARN
    con.close()
    print("  daily snapshot: idempotent re-run, failed gate and bad write append nothing, month end, blank before start, rule mutations")


if __name__ == "__main__":
    test_daily_snapshot()
    test_deployment_lookup()
    test_notebooks()
    test_candidate_preserves_evaluation_on_write_failure()
    test_validation_target_isolation()
    test_model_counts_from_build()
    test_heartbeat_schema_publication()
    test_candidate_model_gate()
    test_candidate_dax_evidence()
    test_candidate_count_snapshot()
    test_independent_measure_comparison()
    test_measure_expectations_cover_generator()
    test_gold_manual_count_conservation()
    test_balance_reconciliation()
    test_dax_response_errors()
    test_refresh_request_identity()
    test_unknown_checks_block()
    test_reject_evidence_is_complete()
    test_conflicting_merge_keys_block()
    test_extraction_scope_evidence()
    test_checklist_group_normalization()
    test_read_transport_retries()
    test_audit_validation_scope()
    test_landing_missing_files()
    test_silver_input_failure_blocks()
    test_empty_freshness()
    test_evidence_write_failure()
    test_pipeline()
    test_publish_models()
    test_run_notebook_terminal_status()
    test_outbuild_extract()
    test_outbuild_link_keys()
    test_lineage_bindings()
    test_missing_manual_csv_preserves_bronze()
    test_build_timestamp()
    print("validation checks passed")
