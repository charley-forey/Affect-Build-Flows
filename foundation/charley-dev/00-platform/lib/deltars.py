"""Bronze writes without Spark: delta-rs (`deltalake`) ports of the Spark write path.

cd_01_extract_procore spends most of its ~80 minutes sleeping on Procore's 600 requests/hour
quota. On Spark that idle time holds a 4-8 CU session; on a Fabric Python notebook (2 vCores,
1 CU) it costs a fraction. The HTTP, archive and manifest logic never needed Spark - only the
four writes did, and they are ported here with the same semantics:

- merge_rows      = fabric_common.merge_delta   (prepare_merge + merge_sql)
- read_watermark  = watermark.read_watermark
- write_watermark = watermark.write_watermark
- log_run         = fabric_common.log_run

Semantics kept deliberately identical, because a bronze table written by either path must be
indistinguishable to silver:
- exact duplicate source rows collapse (SELECT DISTINCT *);
- two different rows sharing a merge key raise before anything is written;
- the join is null-safe (<=> in Spark, IS NOT DISTINCT FROM here) - company-scoped Procore
  endpoints carry a NULL _project_id;
- matched rows get every column from the source, unmatched rows are inserted;
- the table is created on first write.

pyarrow and deltalake are imported inside functions so the notebook generator and the test
harness can import this module on a machine without them.

Tests: _local/tests/test_deltars.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

WATERMARK_TABLE = "cd_meta_watermark"
RUN_LOG_TABLE = "cd_meta_run_log"


def _schemas() -> dict[str, Any]:
    """Arrow twins of px.bronze_schema() and watermark._SCHEMA / log_run's schema.

    timestamp[us, UTC] is what Delta calls `timestamp`, the type Spark wrote. int64 is `long`.
    """
    import pyarrow as pa

    ts = pa.timestamp("us", tz="UTC")
    return {
        "bronze": pa.schema([("_key", pa.string()), ("_project_id", pa.int64()),
                             ("_source_endpoint", pa.string()), ("_ingested_at", ts),
                             ("payload", pa.string()), ("_batch_id", pa.string()),
                             ("_row_hash", pa.string())]),
        "watermark": pa.schema([("table_name", pa.string()), ("endpoint", pa.string()),
                                ("watermark", ts), ("batch_id", pa.string()),
                                ("updated_at", ts)]),
        "run_log": pa.schema([("batch_id", pa.string()), ("step", pa.string()),
                              ("table_name", pa.string()), ("row_count", pa.int64()),
                              ("status", pa.string()), ("message", pa.string()),
                              ("logged_at", ts)]),
    }


def onelake_options() -> dict[str, str] | None:
    """Storage options for abfss://...onelake paths inside Fabric; None locally.

    A fresh token per write: the extract runs ~80 minutes, longer than one token lives.
    """
    try:
        import notebookutils  # type: ignore[import-not-found]
    except ImportError:
        return None
    return {"bearer_token": notebookutils.credentials.getToken("storage"),
            "use_fabric_endpoint": "true"}


def prepare_rows(rows: list[dict[str, Any]], columns: Iterable[str], key_columns: Iterable[str]) -> list[dict[str, Any]]:
    """fabric_common.prepare_merge for plain rows: drop exact repeats, refuse conflicts.

    Python's None == None, so the key check is null-safe exactly like Spark's groupBy.
    """
    cols, keys = list(columns), list(key_columns)
    if not keys or any(k not in cols for k in keys):
        raise ValueError("merge requires existing key columns")
    unique = list({tuple(r.get(c) for c in cols): r for r in rows}.values())
    seen = set()
    for r in unique:
        key = tuple(r.get(k) for k in keys)
        if key in seen:
            raise ValueError("conflicting records share a merge key; source batch must be resolved before writing")
        seen.add(key)
    return [{c: r.get(c) for c in cols} for r in unique]


def merge_rows(uri: str, rows: list[dict[str, Any]], key_columns: Iterable[str],
               schema: Any = None, storage_options: dict | None = None) -> int:
    """Idempotent upsert of `rows` into the Delta table at `uri`. Returns distinct rows written."""
    import pyarrow as pa
    from deltalake import DeltaTable, write_deltalake

    schema = schema if schema is not None else _schemas()["bronze"]
    keys = list(key_columns)
    unique = prepare_rows(rows, schema.names, keys)
    if not unique:
        return 0
    source = pa.Table.from_pylist(unique, schema)

    if not DeltaTable.is_deltatable(uri, storage_options=storage_options):
        write_deltalake(uri, source, mode="append", storage_options=storage_options)
        return len(unique)

    predicate = " AND ".join(f'(t."{k}" IS NOT DISTINCT FROM s."{k}")' for k in keys)
    (DeltaTable(uri, storage_options=storage_options)
        .merge(source, predicate, source_alias="s", target_alias="t")
        .when_matched_update_all()
        .when_not_matched_insert_all()
        .execute())
    return len(unique)


def read_watermark(root: str, table: str, endpoint: str, storage_options: dict | None = None) -> datetime | None:
    """Newest watermark for (table, endpoint) by updated_at, or None on first run."""
    from deltalake import DeltaTable

    uri = f"{root}/{WATERMARK_TABLE}"
    if not DeltaTable.is_deltatable(uri, storage_options=storage_options):
        return None
    rows = [r for r in DeltaTable(uri, storage_options=storage_options).to_pyarrow_table().to_pylist()
            if r["table_name"] == table and r["endpoint"] == endpoint]
    return max(rows, key=lambda r: r["updated_at"])["watermark"] if rows else None


def write_watermark(root: str, table: str, endpoint: str, value: datetime, batch_id: str,
                    storage_options: dict | None = None) -> None:
    """Record a new high-water mark. Call only after the load has succeeded."""
    row = {"table_name": table, "endpoint": endpoint, "watermark": value,
           "batch_id": batch_id, "updated_at": datetime.now(timezone.utc)}
    merge_rows(f"{root}/{WATERMARK_TABLE}", [row], ["table_name", "endpoint"],
               _schemas()["watermark"], storage_options)


def log_run(root: str, batch_id: str, step: str, table: str, row_count: int,
            status: str = "ok", message: str = "", storage_options: dict | None = None) -> None:
    """Append one run-log row. Never raises, like fabric_common.log_run."""
    try:
        import pyarrow as pa
        from deltalake import write_deltalake

        row = {"batch_id": batch_id, "step": step, "table_name": table, "row_count": int(row_count),
               "status": status, "message": message, "logged_at": datetime.now(timezone.utc)}
        write_deltalake(f"{root}/{RUN_LOG_TABLE}", pa.Table.from_pylist([row], _schemas()["run_log"]),
                        mode="append", storage_options=storage_options)
    except Exception as exc:  # noqa: BLE001 - logging must never be fatal
        print(f"[warn] run log write failed: {exc}")

