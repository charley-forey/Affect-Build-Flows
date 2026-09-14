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


def spark_merge(con, rows):
    """merge_delta's logic, executed by DuckDB."""
    con.execute("CREATE OR REPLACE TABLE src (_key VARCHAR, _project_id BIGINT, _source_endpoint VARCHAR, "
                "_ingested_at TIMESTAMPTZ, payload VARCHAR, _batch_id VARCHAR, _row_hash VARCHAR)")
    con.executemany("INSERT INTO src VALUES (?, ?, ?, ?, ?, ?, ?)", [[r[c] for c in COLUMNS] for r in rows])
    fabric_common.prepare_merge(Frame(con.table("src")), KEYS)
    if not con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name = 'tgt'").fetchone()[0]:
        con.execute("CREATE TABLE tgt AS SELECT DISTINCT * FROM src")
        return
    sql = fabric_common.merge_sql("tgt", "src", KEYS, COLUMNS)
    sql = re.sub(r"t\.(\"[^\"]+\") = ", r"\1 = ", sql.replace("`", '"').replace("<=>", "IS NOT DISTINCT FROM"))
    con.execute(sql)


def rows_of(relation_rows):
    return sorted(tuple(r[c] for c in COLUMNS) for r in relation_rows)


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
            assert written == len({tuple(r[c] for c in COLUMNS) for r in batch})
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


if __name__ == "__main__":
    test_merge_equivalence()
    test_watermark_and_run_log()
