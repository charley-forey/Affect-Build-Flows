"""Shared helpers for every charley-dev notebook.

Pure Python at import time. Spark is imported *inside* the functions that need it, so
this module can be imported by the local test harness on a machine with no Spark and no
Fabric. That is what makes the logic testable offline.

The important function here is `merge_delta`. The existing workspace notebooks do:

    spark.sql("DROP TABLE IF EXISTS procore_projects_raw")
    df.write.format("delta").mode("append").saveAsTable("procore_projects_raw")

which destroys the table on every run, loses all history, and leaves a window where a
concurrent reader sees nothing. `merge_delta` is idempotent instead: re-running a load
is a no-op, which is what makes incremental refresh and retry-after-failure safe.

Self-check: python fabric_common.py
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Iterable

# Audit columns stamped onto every bronze and silver row. See naming-standards.md.
AUDIT_COLUMNS = ("_ingested_at", "_source_endpoint", "_batch_id", "_row_hash")


# --------------------------------------------------------------------------
# Secrets
# --------------------------------------------------------------------------


def get_secret(name: str, vault_env: str = "PROCORE_KEYVAULT_URL") -> str:
    """Key Vault inside Fabric, environment variable locally.

    Same contract as foundation/01-ingestion/Procore_APICalls/procore_auth.ipynb, so
    there is one way to obtain a credential across the whole workspace and no second
    place for one to hide. The Jul 23 warehouse review flagged hard-coded credentials in
    a notebook cell as the first thing to fix.
    """
    try:
        import notebookutils  # type: ignore[import-not-found]

        vault = os.environ.get(vault_env)
        if vault:
            return notebookutils.credentials.getSecret(vault, name)
    except ImportError:
        pass  # not running inside Fabric

    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Secret {name!r} not found. Set {vault_env} to the Key Vault URL inside "
            f"Fabric, or export {name} locally. See charley-dev/README.md."
        )
    return value


# --------------------------------------------------------------------------
# Run identity and audit columns
# --------------------------------------------------------------------------


def new_batch_id() -> str:
    """One id per pipeline run, stamped on every row that run writes.

    Makes "which run produced this number?" answerable, and makes a bad run reversible:
    delete where _batch_id = x.
    """
    return f"{utc_now():%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:8]}"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def row_hash(payload: Any) -> str:
    """Stable hash of a source record, used for change detection.

    sort_keys makes it independent of JSON key ordering - without that, a source that
    reorders its keys would look like every row changed.
    """
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def audit_columns(source_endpoint: str, batch_id: str, payload: Any = None) -> dict[str, Any]:
    """The four audit values for one row."""
    return {
        "_ingested_at": utc_now(),
        "_source_endpoint": source_endpoint,
        "_batch_id": batch_id,
        "_row_hash": row_hash(payload) if payload is not None else None,
    }


# --------------------------------------------------------------------------
# Delta writes
# --------------------------------------------------------------------------


def merge_sql(table: str, source_view: str, key_columns: Iterable[str], columns: Iterable[str]) -> str:
    """Build the MERGE statement used by merge_delta.

    Split out from the Spark call so it can be asserted in a test without a cluster -
    the join predicate is the part that is easy to get wrong and expensive to get wrong.
    """
    keys = list(key_columns)
    cols = list(columns)
    if not keys:
        raise ValueError("merge requires at least one key column")
    if not cols:
        raise ValueError("merge requires at least one column")

    on = " AND ".join(f"t.`{k}` = s.`{k}`" for k in keys)
    updates = ", ".join(f"t.`{c}` = s.`{c}`" for c in cols if c not in keys)
    insert_cols = ", ".join(f"`{c}`" for c in cols)
    insert_vals = ", ".join(f"s.`{c}`" for c in cols)

    # UPDATE clause is omitted when every column is a key - "matched" then means the row
    # is byte-identical and there is nothing to write.
    matched = f"WHEN MATCHED THEN UPDATE SET {updates}\n" if updates else ""
    return (
        f"MERGE INTO {table} AS t\n"
        f"USING {source_view} AS s\n"
        f"ON {on}\n"
        f"{matched}"
        f"WHEN NOT MATCHED THEN INSERT ({insert_cols}) VALUES ({insert_vals})"
    )


def merge_delta(spark: Any, df: Any, table: str, key_columns: Iterable[str]) -> int:
    """Idempotent upsert of `df` into Delta `table` on `key_columns`.

    Creates the table on first run. Returns the row count written.

    Why this and not overwrite: re-running a load must be safe. Incremental pulls
    deliberately overlap by an hour (clock skew is real), so the same row arrives twice
    and must not duplicate.
    """
    keys = list(key_columns)
    if not spark.catalog.tableExists(table):
        df.write.format("delta").saveAsTable(table)
        return df.count()

    view = f"_src_{uuid.uuid4().hex[:8]}"
    df.createOrReplaceTempView(view)
    try:
        spark.sql(merge_sql(table, view, keys, df.columns))
    finally:
        spark.catalog.dropTempView(view)
    return df.count()


# --------------------------------------------------------------------------
# Run log
# --------------------------------------------------------------------------

RUN_LOG_TABLE = "cd_meta_run_log"


def log_run(
    spark: Any,
    batch_id: str,
    step: str,
    table: str,
    row_count: int,
    status: str = "ok",
    message: str = "",
) -> None:
    """Append one row to the run log.

    Deliberately append-only and deliberately never raises: a logging failure must not
    take down a pipeline that otherwise succeeded.
    """
    try:
        row = [(batch_id, step, table, int(row_count), status, message, utc_now())]
        schema = "batch_id string, step string, table_name string, row_count long, status string, message string, logged_at timestamp"
        spark.createDataFrame(row, schema).write.format("delta").mode("append").saveAsTable(RUN_LOG_TABLE)
    except Exception as exc:  # noqa: BLE001 - logging must never be fatal
        print(f"[warn] run log write failed: {exc}")


# --------------------------------------------------------------------------
# Self-check
# --------------------------------------------------------------------------


def _selftest() -> None:
    # row_hash is order-independent, so a source reordering keys is not a false change.
    assert row_hash({"a": 1, "b": 2}) == row_hash({"b": 2, "a": 1})
    assert row_hash({"a": 1}) != row_hash({"a": 2})

    # batch ids are unique per call
    assert new_batch_id() != new_batch_id()

    audit = audit_columns("rfis", "batch-1", {"id": 7})
    assert set(audit) == set(AUDIT_COLUMNS)
    assert audit["_source_endpoint"] == "rfis"
    assert audit["_row_hash"] is not None
    assert audit_columns("rfis", "batch-1")["_row_hash"] is None

    # The merge predicate joins on every key, and never updates a key column.
    sql = merge_sql("t_target", "v_src", ["id", "project_id"], ["id", "project_id", "subject"])
    assert "t.`id` = s.`id` AND t.`project_id` = s.`project_id`" in sql
    assert "t.`subject` = s.`subject`" in sql
    assert "t.`id` = s.`id`," not in sql, "key columns must not appear in the UPDATE SET"
    assert "WHEN NOT MATCHED THEN INSERT" in sql

    # All-key merge has nothing to update, so the UPDATE clause is omitted entirely.
    assert "WHEN MATCHED" not in merge_sql("t", "v", ["id"], ["id"])

    for bad in (([], ["a"]), (["a"], [])):
        try:
            merge_sql("t", "v", *bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"merge_sql should reject {bad}")

    print("fabric_common: all checks passed")


if __name__ == "__main__":
    _selftest()
