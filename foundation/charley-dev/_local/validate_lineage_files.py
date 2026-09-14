"""Read production Delta files locally; record aggregate project and inspection lineage.

No Spark, SQL endpoint, model queries or remote writes. IDs remain only in memory.
"""
from __future__ import annotations
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import deploy
import deploy_ingestion
import seedrunner

HERE = Path(__file__).resolve().parent
SILVER = "8735633a-3f98-4d96-8666-abf57a1c0454"
GOLD = "812ec953-5517-447e-95aa-062f7cf89b28"


def key_summary(rows, columns):
    keys = [tuple(row[column] for column in columns) for row in rows]
    counts = Counter(keys)
    return {"rows": len(rows), "distinct_keys": len(counts),
            "null_key_rows": sum(any(value is None for value in key) for key in keys),
            "duplicate_excess_rows": sum(count - 1 for count in counts.values())}


def passed(record):
    dim = record["project_dimension"]
    return (not record["errors"] and record["stable_versions"]
            and not dim["null_key_rows"] and not dim["duplicate_excess_rows"]
            and not any(r["missing_dimension_project_ids"] for r in record["source_projects"])
            and all(c["passed"] and not any(c[side][field]
                    for side in ("source_keys", "target_keys")
                    for field in ("null_key_rows", "duplicate_excess_rows")) for c in record["checks"]))


def main():
    from deltalake import DeltaTable
    opts = {"bearer_token": deploy_ingestion.storage_token(), "use_fabric_endpoint": "true"}
    tables = {}
    record = {"started_at": datetime.now(timezone.utc).isoformat(),
              "method": "local Delta file reads; pinned individual table versions; no server query compute",
              "source_projects": [], "checks": [], "errors": []}

    def read(lakehouse, table, columns):
        key = (lakehouse, table.lower())
        if key not in tables:
            uri = f"abfss://{deploy.WORKSPACE_ID}@onelake.dfs.fabric.microsoft.com/{lakehouse}/Tables/dbo/{table.lower()}"
            print(f"Reading {table.lower()} metadata", flush=True)
            dt = DeltaTable(uri, storage_options=opts)
            tables[key] = (dt, dt.version())
        return tables[key][0].to_pyarrow_table(columns=columns).to_pylist()

    dim = read(GOLD, "dim_project", ["ProjectKey"])
    projects = {r["ProjectKey"] for r in dim}
    record["project_dimension"] = key_summary(dim, ["ProjectKey"])
    source_sql = (HERE.parent / "02-transformation/sql/silver/01_source_views_cd.sql").read_text()
    views = {}
    definitions = {}
    for sql in seedrunner.split_statements(source_sql):
        view = re.search(r"CREATE OR REPLACE TEMPORARY VIEW (sv_\w+) AS", sql)
        table = re.search(r"delta\.`\{CD_SILVER_ABFSS\}/(\w+)`", sql)
        if view and table:
            views[view[1]] = table[1]
            definitions[view[1]] = sql
    observed = next(s for s in seedrunner.split_statements(source_sql)
                    if s.startswith("CREATE OR REPLACE TEMPORARY VIEW sv_observed_projects AS"))
    for view in re.findall(r"FROM (sv_\w+)", observed):
        table = views[view]
        try:
            if view == "sv_outbuild_projects":
                # Execute the actual DISTINCT + non-null Outbuild-ID predicate and alias.
                import duckdb
                import pyarrow as pa
                rows = read(SILVER, table, ["project_id", "outbuild_project_id"])
                con = duckdb.connect()
                con.register("lineage_source", pa.Table.from_pylist(rows))
                con.execute(re.sub(r"delta\.`\{CD_SILVER_ABFSS\}/\w+`", "lineage_source", definitions[view]))
                rows = [{"project_id": r[0]} for r in con.execute("SELECT procore_project_id FROM sv_outbuild_projects").fetchall()]
                con.close()
            else:
                # The current remaining adapters project project_id without filters or joins.
                # Fail when that contract changes instead of silently skipping its semantics.
                assert not re.search(r"\b(DISTINCT|WHERE|JOIN|GROUP BY)\b", definitions[view], re.I), view
                rows = read(SILVER, table, ["project_id"])
            ids = {r["project_id"] for r in rows if r["project_id"] is not None}
            missing = ids - projects
            record["source_projects"].append({"view": view, "table": table, "rows": len(rows),
                "distinct_project_ids": len(ids), "null_project_rows": sum(r["project_id"] is None for r in rows),
                "missing_dimension_project_ids": len(missing),
                "rows_without_dimension_member": sum(r["project_id"] in missing for r in rows)})
        except Exception as exc:
            record["errors"].append({"table": table, "error_type": type(exc).__name__})
    for source, target, source_key, target_key in (
        ("cd_silver_qc_inspection", "fct_procoreinspection", ["project_id", "inspection_id"], ["ProjectKey", "InspectionKey"]),
        ("cd_silver_qc_inspection_item", "fct_procoreinspectionitem", ["project_id", "inspection_id", "item_id"], ["ProjectKey", "InspectionKey", "ItemKey"]),
    ):
        try:
            src = read(SILVER, source, source_key)
            dst = read(GOLD, target, target_key)
            a = Counter(tuple(r[k] for k in source_key) for r in src)
            b = Counter(tuple(r[k] for k in target_key) for r in dst)
            record["checks"].append({"source": source, "target": target,
                "source_keys": key_summary(src, source_key), "target_keys": key_summary(dst, target_key),
                "missing_rows": sum((a-b).values()), "extra_rows": sum((b-a).values()),
                "passed": a == b})
        except Exception as exc:
            record["errors"].append({"table": target, "error_type": type(exc).__name__})
    record["versions"] = []
    for (lakehouse, table), (dt, version) in tables.items():
        dt.update_incremental()
        record["versions"].append({"lakehouse": lakehouse, "table": table,
                                   "read_version": version, "end_version": dt.version()})
    record["stable_versions"] = all(v["read_version"] == v["end_version"] for v in record["versions"])
    record["completed_at"] = datetime.now(timezone.utc).isoformat()
    record["limitations"] = ["No upstream API population verification; source deletion scope unverified.",
        "Stable individual versions are not an atomic cross-table source snapshot.",
        "Project identity coverage does not establish business mapping correctness."]
    record["status"] = "PASS" if passed(record) else "FAIL"
    path = HERE.parent / "_docs/production-lineage-file-evidence.json"
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"errors": record["errors"], "stable_versions": record["stable_versions"],
                     "source_views": len(record["source_projects"]), "inspection_checks": record["checks"],
                     "missing_project_ids_by_source": sum(r["missing_dimension_project_ids"] for r in record["source_projects"])}))
    return int(not passed(record))


if __name__ == "__main__":
    assert key_summary([{"k": None}, {"k": "x"}, {"k": "x"}], ["k"]) == {
        "rows": 3, "distinct_keys": 2, "null_key_rows": 1, "duplicate_excess_rows": 1}
    clean = {"errors": [], "stable_versions": True,
             "project_dimension": {"null_key_rows": 0, "duplicate_excess_rows": 0},
             "source_projects": [{"missing_dimension_project_ids": 0}], "checks": []}
    assert passed(clean)
    clean["source_projects"][0]["missing_dimension_project_ids"] = 1
    assert not passed(clean)
    clean["source_projects"][0]["missing_dimension_project_ids"] = 0
    clean["project_dimension"]["null_key_rows"] = 1
    assert not passed(clean)
    clean["project_dimension"]["null_key_rows"] = 0
    clean["project_dimension"]["duplicate_excess_rows"] = 1
    assert not passed(clean)
    import sys
    if "--self-test" not in sys.argv:
        raise SystemExit(main())
    print("lineage summary self-test passed")
