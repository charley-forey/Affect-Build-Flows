"""Replay all production DQ rules on read-only Delta files in local memory; no fixtures."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import duckdb
from deltalake import DeltaTable
import deploy
import deploy_gold
import seedrunner
from validate_snapshot_files import GOLD, expectations


def plan(con, rules, sql):
    views = {}
    for statement in seedrunner.split_statements(sql):
        match = re.match(r"CREATE OR REPLACE TEMPORARY VIEW (\w+) AS", statement, re.I)
        if not match:
            raise RuntimeError("unexpected source-view statement")
        def replace(match):
            if not match[1].startswith("{CD_SILVER_ABFSS}/"):
                raise RuntimeError("unrecognized source lakehouse; refusing to substitute")
            name = match[1].rsplit("/", 1)[-1]
            return "input_" + name
        views[match[1]] = re.sub(r"delta\.`([^`]+)`", replace, statement).replace("`", '"')
    needed = set()
    def visit(name):
        if name in needed:
            return
        needed.add(name)
        if name in views:
            for dependency in con.get_table_names(re.sub(r"^CREATE OR REPLACE TEMPORARY VIEW \w+ AS\s*", "", views[name], flags=re.I)):
                visit(dependency)
    for rule in rules:
        for name in con.get_table_names(rule.failing_sql.replace("`", '"')):
            visit(name)
    return views, needed


def evaluate(con, rules):
    results = []
    for rule in rules:
        item = dict(name=rule.name, severity=rule.severity)
        try:
            count = con.execute("SELECT COUNT(*) FROM (" + rule.failing_sql.replace("`", '"') + ") failing").fetchone()[0]
            item.update(failing_rows=count, passed=count == 0,
                        blocking=count > 0 and rule.severity == "error")
        except Exception as exc:
            item.update(failing_rows=-1, passed=False, blocking=True, error_type=type(exc).__name__)
        results.append(item)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    con = duckdb.connect()
    for macro in seedrunner.MACROS:
        con.execute(macro)
    rules = expectations.build_suite().expectations
    source = deploy_gold.SOURCES["cd"].read_text()
    views, needed = plan(con, rules, source)
    token = subprocess.check_output([shutil.which("az") or "az", "account", "get-access-token",
        "--resource", "https://storage.azure.com/", "--query", "accessToken", "-o", "tsv"], text=True).strip()
    options = {"bearer_token": token, "use_fabric_endpoint": "true"}
    evidence = dict(started_at=datetime.now(timezone.utc).isoformat(), workspace_id=deploy.WORKSPACE_ID,
        gold_lakehouse_id=GOLD, tables={}, load_errors={}, view_errors={}, passed=False,
        source_views_sha256=hashlib.sha256(source.encode()).hexdigest(),
        suite_sha256=hashlib.sha256(Path(expectations.__file__).read_bytes()).hexdigest(),
        rule_sql_sha256=hashlib.sha256(json.dumps([(r.name, r.severity, r.failing_sql) for r in rules]).encode()).hexdigest(),
        duckdb_version=duckdb.__version__,
        compatibility_macros_sha256=hashlib.sha256(json.dumps(seedrunner.MACROS).encode()).hexdigest(),
        scope="All current main DQ rules replayed on actual production Delta files in local DuckDB. "
              "Uses current source-view SQL and compatibility macros, no synthetic fixtures. "
              "Stable table versions do not establish an atomic upstream batch. CURRENT_DATE uses replay day. Not Spark or report/model execution, source completeness, or proof of deployed code identity.")
    handles = {}
    for name in sorted(needed - views.keys()):
        if name.startswith("input_"):
            base, table = deploy_gold.CD_SILVER_ABFSS, name[len("input_"):]
        else:
            base = f"abfss://{deploy.WORKSPACE_ID}@onelake.dfs.fabric.microsoft.com/{GOLD}/Tables/dbo"
            table = name
        try:
            handle = handles[name] = DeltaTable(base + "/" + table.lower(), storage_options=options)
            arrow = handle.to_pyarrow_table()
            con.register(name, arrow)
            evidence["tables"][name] = dict(version_before=handle.version(), rows=arrow.num_rows,
                schema_sha256=hashlib.sha256(str(arrow.schema).encode()).hexdigest())
        except Exception as exc:
            evidence["load_errors"][name] = type(exc).__name__
        args.output.write_text(json.dumps(evidence, indent=2))
    for name, statement in views.items():
        if name in needed:
            try:
                con.execute(statement)
            except Exception as exc:
                evidence["view_errors"][name] = type(exc).__name__
    evidence["checks"] = evaluate(con, rules)
    for name, handle in handles.items():
        try:
            handle.update_incremental()
            evidence["tables"][name]["version_after"] = handle.version()
        except Exception as exc:
            evidence["load_errors"][name] = type(exc).__name__
    evidence["stable_versions"] = all(t.get("version_after") == t["version_before"] for t in evidence["tables"].values())
    evidence["summary"] = dict(total=len(rules), passed=sum(c["passed"] for c in evidence["checks"]),
        warnings=sum(not c["passed"] and not c["blocking"] for c in evidence["checks"]),
        blocking=sum(c["blocking"] for c in evidence["checks"]),
        errors=sum(c["failing_rows"] < 0 for c in evidence["checks"]))
    evidence["passed"] = (not evidence["summary"]["blocking"] and not evidence["load_errors"]
                           and not evidence["view_errors"] and evidence["stable_versions"])
    evidence["finished_at"] = datetime.now(timezone.utc).isoformat()
    args.output.write_text(json.dumps(evidence, indent=2))
    print(json.dumps(dict(gate_passed=evidence["passed"], **evidence["summary"])))
    if not evidence["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
