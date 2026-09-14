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


# The vault the platform actually uses: resource group Affect_Data, subscription
# 73932b34-3bb6-4a94-bd4b-4b7623d4f7d6. Not a secret - it is a URL - and defaulting it
# here removes the failure this code shipped with: PROCORE_KEYVAULT_URL was read in five
# places and set in none, so the Key Vault branch never executed at all.
KEYVAULT_URL = "https://affectkeyvault.vault.azure.net/"

# Key Vault secret names cannot contain underscores, so the environment-variable name is
# not the secret name. Every secret in AffectKeyVault was created by hand in the portal by
# the Affect reporting lead, in PascalCase rather than the mechanical kebab-case this used to assume, so each
# one is mapped explicitly. Mapped, not renamed: something we cannot see may already read
# them under these names, and renaming a secret to satisfy a convention breaks that caller
# silently. Verified against `az keyvault secret list` on 2026-08-24.
SECRET_NAMES = {
    "OUTBUILD_API_TOKEN": "OutbuildToken",
    "PROCORE_CLIENT_ID": "ProcoreClientID",
    "PROCORE_CLIENT_SECRET": "ProcoreClientSecret",
    "PROCORE_COMPANY_ID": "ProcoreCompanyID",
}


def kv_secret_name(name: str) -> str:
    """Environment-variable name -> Key Vault secret name."""
    return SECRET_NAMES.get(name, name.replace("_", "-").lower())


def get_secret(name: str, vault_env: str = "AFFECT_KEYVAULT_URL") -> str:
    """Key Vault inside Fabric, environment variable locally.

    One way to obtain a credential across the whole workspace, so there is no second
    place for one to hide. The Jul 23 warehouse review flagged hard-coded credentials in
    a notebook cell as the first thing to fix.

    Inside Fabric this fails closed: if the vault lookup does not produce the secret it
    raises, rather than falling through to os.environ. The previous version fell through,
    so a half-configured vault quietly read the value from somewhere else and looked
    healthy right up until the unattended 02:00 run.
    """
    try:
        import notebookutils  # type: ignore[import-not-found]
    except ImportError:
        notebookutils = None  # not running inside Fabric

    if notebookutils is not None:
        vault = os.environ.get(vault_env) or KEYVAULT_URL
        return notebookutils.credentials.getSecret(vault, kv_secret_name(name))

    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Secret {name!r} not found. Export {name} locally, or run inside Fabric "
            f"where it is read from {KEYVAULT_URL} as {kv_secret_name(name)!r}. "
            f"See charley-dev/_docs/keyvault-runbook.md."
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

    # <=> not =. A nullable key column makes `=` return NULL rather than true, so no
    # source row ever matches and every run appends a fresh copy of the data with
    # nothing raising. Bronze hit exactly this: `_project_id` is NULL on all 8
    # company-scoped Procore endpoints. Identical to `=` when neither side is null,
    # so it is safe for every other caller and removes the trap for the next one.
    on = " AND ".join(f"t.`{k}` <=> s.`{k}`" for k in keys)
    updates = ", ".join(f"t.`{c}` = s.`{c}`" for c in cols if c not in keys)
    insert_cols = ", ".join(f"`{c}`" for c in cols)
    insert_vals = ", ".join(f"s.`{c}`" for c in cols)

    # UPDATE clause is omitted when every column is a key - "matched" then means the row
    # is byte-identical and there is nothing to write.
    matched = f"WHEN MATCHED THEN UPDATE SET {updates}\n" if updates else ""
    # DEDUPE THE SOURCE IN THE STATEMENT ITSELF, not at the call site.
    #
    # Delta refuses a MERGE where two source rows match the same target row - it cannot know
    # which should win - and raises DELTA_MULTIPLE_SOURCE_ROW_MATCHING_TARGET_ROW_IN_MERGE.
    # There are TWO merge paths here: merge_delta() below, and the landing notebook, which
    # builds its own DataFrame and calls this function directly. Fixing it in merge_delta on
    # 2026-08-25 therefore fixed exactly half of them, and the nightly run failed that
    # evening on four Outbuild tables that go through the other half.
    #
    # Putting it here covers every caller, including the next one somebody writes.
    #
    # It only ever fires on the SECOND run: with an empty target there is nothing to match,
    # so duplicates insert quietly and the bug waits. That is the worst schedule a defect can
    # keep, and it is why this belongs in the shared builder rather than in whichever call
    # site last got bitten.
    #
    # Rows sharing a natural key inside one batch are the same record fetched twice - an
    # incremental pull deliberately overlaps by an hour, and a paginated list can repeat a
    # row across page boundaries - so keeping one is correct, not lossy.
    partition = ", ".join(f"`{k}`" for k in keys)
    deduped = (
        f"(SELECT * FROM (SELECT *, ROW_NUMBER() OVER "
        f"(PARTITION BY {partition} ORDER BY 1) AS _dedupe_rn FROM {source_view}) "
        f"WHERE _dedupe_rn = 1)"
    )
    return (
        f"MERGE INTO {table} AS t\n"
        f"USING {deduped} AS s\n"
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

    # Delta refuses a MERGE where two source rows match the same target row, and it is
    # right to: it cannot know which one should win. So the source is made unique on the
    # key first, which is what the Delta docs tell you to do.
    #
    # This is not hypothetical tidiness. Bronze hits it two different ways: an incremental
    # pull deliberately overlaps by an hour, so the same record legitimately arrives twice
    # in one batch; and a paginated list can repeat a row across page boundaries while
    # records are being written underneath it. `checklist_lists` failed exactly here on
    # 2026-08-25 - and only once its target table was non-empty, because with nothing to
    # match, duplicates insert quietly instead of raising. A bug that appears on the SECOND
    # run and not the first is the worst kind to leave to production.
    #
    # Deduplicating rather than raising is safe because rows sharing a natural key inside
    # one batch are the same record fetched twice, not two different records.
    df = df.dropDuplicates(keys)

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
    # Key Vault forbids underscores, so the env-var name is never the secret name. Getting
    # this wrong is silent: the vault returns "not found" for a name that looks correct.
    # Every secret in AffectKeyVault was created by hand in the portal, so all four are
    # mapped, not renamed. These names are what `az keyvault secret list` returns; the
    # kebab-case fallback below is only for a secret nobody has created yet.
    assert kv_secret_name("PROCORE_CLIENT_ID") == "ProcoreClientID"
    assert kv_secret_name("PROCORE_CLIENT_SECRET") == "ProcoreClientSecret"
    assert kv_secret_name("PROCORE_COMPANY_ID") == "ProcoreCompanyID"
    assert kv_secret_name("OUTBUILD_API_TOKEN") == "OutbuildToken"
    assert "_" not in kv_secret_name("SOME_FUTURE_TOKEN")

    # Locally (no notebookutils) a missing secret raises rather than returning None, and
    # the message names the vault so the reader knows which one to look in.
    import os as _os
    _os.environ.pop("NO_SUCH_SECRET_XYZ", None)
    try:
        get_secret("NO_SUCH_SECRET_XYZ")
    except RuntimeError as exc:
        assert "no-such-secret-xyz" in str(exc), str(exc)
    else:
        raise AssertionError("get_secret must raise when the secret is absent")

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
    assert "t.`id` <=> s.`id` AND t.`project_id` <=> s.`project_id`" in sql
    assert "t.`subject` = s.`subject`" in sql
    assert "t.`id` = s.`id`," not in sql, "key columns must not appear in the UPDATE SET"
    assert "= s.`id`" not in sql.split("WHEN")[0], "join must be null-safe"
    assert "WHEN NOT MATCHED THEN INSERT" in sql

    # The source is deduplicated INSIDE the statement, so every caller gets it - not just
    # merge_delta. This bug landed twice: once in bronze, then again the same evening in the
    # landing notebook, which calls merge_sql directly. It only fires on the second run,
    # because an empty target has nothing to match.
    assert "ROW_NUMBER() OVER (PARTITION BY `id`, `project_id`" in sql
    assert "_dedupe_rn = 1" in sql
    assert "USING v_src AS s" not in sql, "source must be wrapped, not used raw"

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
