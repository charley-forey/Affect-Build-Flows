"""delta-rs bronze writes match the Spark path on the same inputs.

The oracle is the Spark path's own code: fabric_common.prepare_merge run over DuckDB relations,
then fabric_common.merge_sql executed by DuckDB (translated only in dialect: backticks, <=>, and
DuckDB's unqualified UPDATE SET target). The candidate is deltars.merge_rows into a real local
Delta table. Both see identical batches; their tables must hold identical rows after every one.

    python foundation/charley-dev/_local/tests/test_deltars.py
"""
import re
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "00-platform" / "lib"))

import duckdb
from deltalake import DeltaTable

import deltars
import fabric_common
import procore_scope
import watermark

KEYS = ["_key", "_project_id"]
COLUMNS = deltars._schemas()["bronze"].names
T0 = datetime(2026, 9, 14, 6, 0, tzinfo=timezone.utc)


class Frame:
    """The DataFrame surface prepare_merge uses, over a DuckDB relation."""
    def __init__(self, relation):
        self.relation, self.columns = relation, relation.columns
    def dropDuplicates(self):
        return Frame(self.relation.distinct())
    def groupBy(self, *keys):
        cols = ", ".join(keys)
        return SimpleNamespace(count=lambda: Frame(self.relation.aggregate(f"{cols}, count(*) AS count", cols)))
    def filter(self, predicate):
        return Frame(self.relation.filter(predicate))
    def limit(self, n):
        return Frame(self.relation.limit(n))
    def count(self):
        return self.relation.aggregate("count(*)").fetchone()[0]


def row(key, project, payload, batch="b1", at=T0):
    return {"_key": key, "_project_id": project, "_source_endpoint": "ep", "_ingested_at": at,
            "payload": payload, "_batch_id": batch, "_row_hash": fabric_common.row_hash(payload)}


def spark_merge(con, rows, scopes=(), deleted_at=None):
    """merge_delta's logic, executed by DuckDB."""
    con.execute("CREATE OR REPLACE TABLE src (_key VARCHAR, _project_id BIGINT, _source_endpoint VARCHAR, "
                "_ingested_at TIMESTAMPTZ, payload VARCHAR, _batch_id VARCHAR, _row_hash VARCHAR, "
                "_source_deleted_at TIMESTAMPTZ)")
    con.executemany("INSERT INTO src VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [[r.get(c) for c in COLUMNS] for r in rows])
    fabric_common.prepare_merge(Frame(con.table("src")), KEYS)
    if not con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name = 'tgt'").fetchone()[0]:
        con.execute("CREATE TABLE tgt AS SELECT DISTINCT * FROM src")
        return
    sql = fabric_common.merge_sql("tgt", "src", KEYS, COLUMNS, scopes, deleted_at)
    sql = re.sub(r"t\.(\"[^\"]+\") = ", r"\1 = ", sql.replace("`", '"').replace("<=>", "IS NOT DISTINCT FROM"))
    con.execute(sql)


def rows_of(relation_rows):
    return sorted((tuple(r[c] for c in COLUMNS) for r in relation_rows), key=repr)


def test_merge_equivalence():
    con = duckdb.connect()
    con.execute("SET TimeZone = 'UTC'")
    later = T0 + timedelta(days=1)
    batches = [
        # first write creates the table: exact duplicate collapses, company (NULL) and project keys
        [row("1", None, "a"), row("1", None, "a"), row("2", 7, "b"), row("2", 8, "b")],
        # update NULL-project key (null-safe join), insert new key, untouched 2/8
        [row("1", None, "a2", "b2", later), row("3", None, "c", "b2", later), row("2", 7, "b", "b2", later)],
        # re-running the same batch is a no-op
        [row("1", None, "a2", "b2", later), row("3", None, "c", "b2", later), row("2", 7, "b", "b2", later)],
    ]
    with tempfile.TemporaryDirectory() as tmp:
        uri = str(Path(tmp) / "cd_bronze_procore_test")
        for batch in batches:
            spark_merge(con, batch)
            written = deltars.merge_rows(uri, batch, KEYS)
            assert written == len({tuple(r.get(c) for c in COLUMNS) for r in batch})
            expected = rows_of(dict(zip(COLUMNS, r)) for r in con.execute("SELECT * FROM tgt").fetchall())
            actual = rows_of(DeltaTable(uri).to_pyarrow_table().to_pylist())
            assert actual == expected, (actual, expected)
        assert len(actual) == 4
        assert DeltaTable(uri).schema().to_arrow().field("_ingested_at").type.tz == "UTC"

        # A conflicting batch is refused by both paths, and delta-rs writes nothing.
        version = DeltaTable(uri).version()
        conflict = [row("9", None, "x"), row("9", None, "y")]
        for write in (lambda: spark_merge(con, conflict), lambda: deltars.merge_rows(uri, conflict, KEYS)):
            try:
                write()
            except ValueError as exc:
                assert "conflicting records" in str(exc)
            else:
                raise AssertionError("conflicting keys permitted a write")
        assert DeltaTable(uri).version() == version
        # Also on first write: no table is created.
        fresh = str(Path(tmp) / "never_created")
        try:
            deltars.merge_rows(fresh, conflict, KEYS)
        except ValueError:
            pass
        assert not DeltaTable.is_deltatable(fresh)
    con.close()
    print("  delta-rs merge == Spark merge_sql on inserts, updates, NULL keys, duplicates, replays; conflicts refused")


def test_watermark_and_run_log():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).as_posix()
        assert deltars.read_watermark(root, "t", "ep") is None, "first run is a full pull"
        deltars.write_watermark(root, "t", "ep", T0, "b1")
        deltars.write_watermark(root, "t", "other", T0 - timedelta(days=9), "b1")
        deltars.write_watermark(root, "t", "ep", T0 + timedelta(hours=5), "b2")
        assert deltars.read_watermark(root, "t", "ep") == T0 + timedelta(hours=5)
        assert deltars.read_watermark(root, "t", "other") == T0 - timedelta(days=9)
        assert watermark.apply_overlap(deltars.read_watermark(root, "t", "ep")) == T0 + timedelta(hours=4)
        # One row per (table, endpoint): the watermark table is merged, not appended.
        assert DeltaTable(f"{root}/{deltars.WATERMARK_TABLE}").to_pyarrow_table().num_rows == 2

        deltars.log_run(root, "b1", "extract_procore", "t", 3)
        deltars.log_run(root, "b2", "extract_procore", "t", 5)
        logged = DeltaTable(f"{root}/{deltars.RUN_LOG_TABLE}").to_pyarrow_table().to_pylist()
        assert [r["row_count"] for r in sorted(logged, key=lambda r: r["batch_id"])] == [3, 5]
        # Logging never raises, even when the write cannot happen.
        deltars.log_run(root, "b3", "extract_procore", "t", "not a number")
    print("  delta-rs watermark: None first, newest per endpoint, overlap applied, merged; run log appends, never raises")


def audit(mode, *scopes):
    """The endpoint audit the extraction cell writes: (project_id, status, received_rows)."""
    return {"mode": mode, "scopes": [{"project_id": p, "status": s, "received_rows": n} for p, s, n in scopes]}


def test_tombstones():
    """Deletion flags, driven by the manifest's scope audit, identical on both merge paths."""
    ep = procore_scope.Endpoint("rfis", "/rest/v1.0/projects/{project_id}/rfis", "project", "1.0", "t")
    days = [T0 + timedelta(days=d) for d in range(6)]
    first = [row("1", 7, "a"), row("2", 7, "b"), row("3", 8, "c"), row("4", None, "d"), row("5", 9, "e")]
    steps = [
        # 0: initial load.
        (first, audit("full", (7, "complete", 2), (8, "complete", 1), (None, "complete", 1), (9, "complete", 1)),
         {}),
        # 1: complete full pull: key 2 gone from 7, key 4 gone from the company scope. Project
        # 8 failed after page one (partial) and 9 was a declared exclusion: neither tombstones.
        ([row("1", 7, "a", "b1", days[1]), row("x", 8, "partial", "b1", days[1])],
         audit("full", (7, "complete", 1), (8, "failed", 1), (9, "excluded_declared", 0), (None, "complete", 0)),
         {("2", 7): days[1]}),
        # 2: the same deletion does not re-stamp; an incremental pull tombstones nothing.
        ([row("1", 7, "a", "b2", days[2])], audit("incremental", (7, "complete", 1), (8, "complete", 1)),
         {("2", 7): days[1]}),
        # 3: key 2 reappears - its tombstone clears. Company scope now complete and non-empty.
        ([row("1", 7, "a", "b3", days[3]), row("2", 7, "b", "b3", days[3]), row("9", None, "z", "b3", days[3])],
         audit("full", (7, "complete", 2), (None, "complete", 1)),
         {("4", None): days[3]}),
    ]
    con = duckdb.connect()
    con.execute("SET TimeZone = 'UTC'")
    with tempfile.TemporaryDirectory() as tmp:
        uri = str(Path(tmp) / "cd_bronze_procore_rfis")
        # A bronze table from before the column existed: both paths must add it, not fail.
        legacy = [r for r in first]
        for i, (batch, manifest, expected_deleted) in enumerate(steps):
            scopes = procore_scope.tombstone_scopes(ep, manifest) if i else []
            at = batch[0]["_ingested_at"]
            if i == 0:
                old = deltars._schemas()["bronze"]
                deltars.merge_rows(uri, legacy, KEYS, schema=old.remove(old.get_field_index("_source_deleted_at")))
                spark_merge(con, legacy)
                continue
            spark_merge(con, batch, scopes, at)
            deltars.merge_rows(uri, batch, KEYS, tombstone_scopes=scopes, deleted_at=at)
            expected = rows_of(dict(zip(COLUMNS, r)) for r in con.execute(f"SELECT {', '.join(COLUMNS)} FROM tgt").fetchall())
            actual = rows_of(DeltaTable(uri).to_pyarrow_table().to_pylist())
            assert actual == expected, (i, actual, expected)
            deleted = {(r["_key"], r["_project_id"]): r["_source_deleted_at"]
                       for r in DeltaTable(uri).to_pyarrow_table().to_pylist() if r["_source_deleted_at"]}
            assert deleted == expected_deleted, (i, deleted)
        # No row is ever removed: the tombstone is a flag, the evidence stays.
        assert DeltaTable(uri).to_pyarrow_table().num_rows == 7
    con.close()
    print("  tombstones: complete scopes only; partial, excluded, empty and incremental never; "
          "stamped once; reappearing key clears; legacy table gains the column; both paths identical")


def test_outbuild_tombstones():
    """Outbuild: extract() decides, the notebook's merge (merge_delta -> merge_sql with the
    WHOLE_TABLE scope) flags. One Spark path, so DuckDB runs merge_sql as the oracle does above."""
    import json
    from unittest.mock import patch

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import extract_outbuild_local as ob

    # The notebook cell's COLUMNS plus the tombstone column it adds.
    cols = ["_key", "_project_id", "payload", "_ingested_at", "_batch_id", "_row_hash",
            "_source_endpoint", "_merge_key", fabric_common.DELETED_AT]
    types = {"_ingested_at": "TIMESTAMPTZ", fabric_common.DELETED_AT: "TIMESTAMPTZ"}
    con = duckdb.connect()
    con.execute("SET TimeZone = 'UTC'")

    def write(table, rows, tombstone):
        con.execute("CREATE OR REPLACE TABLE src (" + ", ".join(f'"{c}" {types.get(c, "VARCHAR")}' for c in cols) + ")")
        con.executemany(f"INSERT INTO src VALUES ({', '.join('?' * len(cols))})",
                        [[r.get(c) for c in cols] for r in rows])
        fabric_common.prepare_merge(Frame(con.table("src")), ["_merge_key"])
        if not con.execute(f"SELECT count(*) FROM information_schema.tables WHERE table_name = '{table}'").fetchone()[0]:
            con.execute(f"CREATE TABLE {table} AS SELECT DISTINCT * FROM src")
            return len(rows)
        sql = fabric_common.merge_sql(table, "src", ["_merge_key"], cols,
                                      [fabric_common.WHOLE_TABLE] if tombstone else (),
                                      datetime.fromisoformat(rows[0]["_ingested_at"]))
        con.execute(re.sub(r"t\.(\"[^\"]+\") = ", r"\1 = ", sql.replace("`", '"').replace("<=>", "IS NOT DISTINCT FROM")))
        return len(rows)

    endpoints = [{"name": "activities", "path": "/activities", "bronze_table": "ob_activities", "consumed": True},
                 {"name": "tasks", "path": "/tasks", "bronze_table": "ob_tasks"},
                 {"name": "schedule_impact_requests", "path": "/s/{scheduleId}", "scope": "schedule",
                  "bronze_table": "ob_sir", "consumed": True}]
    recs = lambda *ids: [{"id": i} for i in ids]
    # (activities pull, tasks pull, expected tombstoned activity ids, expected tombstoned task ids)
    steps = [
        (recs(1, 2, 3), recs(10, 11), set(), set()),
        # 2 gone from a complete consumed pull: flagged. 11 gone from an unconsumed one: not.
        (recs(1, 3), recs(10), {"2"}, set()),
        # A failed pull never merges, so never tombstones; an empty answer is not trusted.
        (RuntimeError("504"), [], {"2"}, set()),
        ([], recs(10), {"2"}, set()),
        # 2 reappears and clears; 3 is now gone.
        (recs(1, 2), recs(10), {"3"}, set()),
    ]
    stamps = {}
    with tempfile.TemporaryDirectory() as tmp:
        for i, (activities, tasks, want_a, want_t) in enumerate(steps):
            def pull(ep, tok):
                got = {"activities": activities, "tasks": tasks}[ep["name"]]
                if isinstance(got, Exception):
                    raise got
                return got
            with patch.object(ob, "pull", pull):
                manifest = ob.extract(endpoints, "t", f"b{i}", tmp, write)
            by = {a["endpoint"]: a for a in manifest["endpoints"]}
            assert by["schedule_impact_requests"]["status"] == "skipped"
            assert by["activities"].get("tombstone", False) == bool(activities and not isinstance(activities, Exception)), (i, by)
            for table, want in (("ob_activities", want_a), ("ob_tasks", want_t)):
                flagged = dict(con.execute(f'SELECT _key, "{fabric_common.DELETED_AT}" FROM {table} '
                                           f'WHERE "{fabric_common.DELETED_AT}" IS NOT NULL').fetchall())
                assert set(flagged) == want, (i, table, flagged)
                for key, at in flagged.items():   # stamped once, never re-stamped
                    assert stamps.setdefault((table, key), at) == at
        assert json.loads((Path(tmp) / "outbuild_run.json").read_text())["batch"] == "b4"
    # Nothing is ever removed: the flag is the evidence.
    assert con.execute("SELECT count(*) FROM ob_activities").fetchone()[0] == 3
    assert con.execute("SELECT count(*) FROM ob_tasks").fetchone()[0] == 2
    con.close()
    print("  outbuild tombstones: consumed complete non-empty pulls only; failed, empty, skipped and "
          "unconsumed never; stamped once; reappearing key clears")


if __name__ == "__main__":
    test_merge_equivalence()
    test_tombstones()
    test_outbuild_tombstones()
    test_watermark_and_run_log()
