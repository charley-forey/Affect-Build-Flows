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
# Rebecca, in PascalCase rather than the mechanical kebab-case this used to assume, so each
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


def get_secret_optional(name: str) -> str | None:
    """get_secret, but None instead of raising when the secret does not exist.

    get_secret fails CLOSED on purpose: a credential that silently resolves from somewhere
    unexpected is worse than a loud failure. That rule is right for credentials and wrong
    for configuration, and an alert webhook is configuration - its absence means "nobody has
    set up alerting yet", not "something is misconfigured".

    Without this distinction the choice is between an alerting feature that cannot ship
    until someone creates a webhook, and a get_secret that no longer fails closed. Neither
    is acceptable, so the two cases get two functions.
    """
    try:
        return get_secret(name)
    except Exception:                                               # noqa: BLE001
        return None


def notify(subject: str, body: str, failing: int = 0) -> bool:
    """Post an alert to a Teams incoming webhook. Returns True if it was sent.

    WHY A WEBHOOK AND NOT EMAIL. A pipeline email activity, a Teams activity and
    notebookutils' mail all require an OAuth connection that has to be created interactively
    by a licensed user. An incoming webhook is a URL and nothing else, so this ships today,
    is version-controlled, and needs no grant from anyone.

    INERT UNTIL CONFIGURED, AND SAYS SO. With no `DQ_ALERT_WEBHOOK` secret this prints what
    it would have sent and returns False. That means the alerting path is exercised by every
    run from the day it lands - if the wiring is wrong, it is wrong loudly and immediately
    rather than on the first night it was actually needed.

    NEVER RAISES. Taking the pipeline down to protect the thing that watches the pipeline is
    backwards - the same rule the heartbeat already follows.
    """
    url = get_secret_optional("DQ_ALERT_WEBHOOK")
    if not url:
        print(f"[alert] NOT SENT - no DQ_ALERT_WEBHOOK secret in the vault.")
        print(f"[alert] would have sent: {subject}")
        print(f"[alert] {body[:500]}")
        print("[alert] To enable: create a Teams incoming webhook and store the URL as")
        print("[alert] 'DQ-ALERT-WEBHOOK' in AffectKeyVault. No code change needed.")
        return False

    import json as _json
    import urllib.request

    # Teams' legacy MessageCard, because it renders in both Teams and most webhook relays.
    # Adaptive Cards need a Workflows-style webhook and would narrow where this works.
    payload = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "themeColor": "C62828" if failing else "2E7D32",
        "summary": subject,
        "title": subject,
        "text": body,
    }
    try:
        request = urllib.request.Request(
            url, data=_json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=30) as response:
            print(f"[alert] sent ({response.status}): {subject}")
        return True
    except Exception as exc:                                        # noqa: BLE001
        print(f"[alert] FAILED to send ({type(exc).__name__}: {exc}) - run unaffected")
        return False


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
    # Collapse exact duplicate rows only. Conflicting keys must be checked before
    # a write; choosing an arbitrary payload would silently corrupt evidence.
    deduped = f"(SELECT DISTINCT * FROM {source_view})"
    return (
        f"MERGE INTO {table} AS t\n"
        f"USING {deduped} AS s\n"
        f"ON {on}\n"
        f"{matched}"
        f"WHEN NOT MATCHED THEN INSERT ({insert_cols}) VALUES ({insert_vals})"
    )


def prepare_merge(df: Any, key_columns: Iterable[str]) -> Any:
    """Accept exact repeats, but never guess between different rows with one key."""
    keys = list(key_columns)
    if not keys or any(key not in df.columns for key in keys):
        raise ValueError("merge requires existing key columns")
    unique = df.dropDuplicates()
    if unique.groupBy(*keys).count().filter("count > 1").limit(1).count():
        raise ValueError("conflicting records share a merge key; source batch must be resolved before writing")
    return unique


def merge_delta(spark: Any, df: Any, table: str, key_columns: Iterable[str]) -> int:
    """Idempotent upsert of `df` into Delta `table` on `key_columns`.

    Creates the table on first run. Returns the row count written.

    Why this and not overwrite: re-running a load must be safe. Incremental pulls
    deliberately overlap by an hour (clock skew is real), so the same row arrives twice
    and must not duplicate.
    """
    keys = list(key_columns)

    df = prepare_merge(df, keys)

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

    assert "SELECT DISTINCT * FROM v_src" in sql
    assert "ROW_NUMBER" not in sql, "conflicting records must never be chosen arbitrarily"

    # Alerting is inert without its secret, and must SAY so rather than failing silently.
    # An alert path that is never exercised until the night it matters is not an alert path.
    _os.environ.pop("DQ_ALERT_WEBHOOK", None)
    assert get_secret_optional("DQ_ALERT_WEBHOOK") is None, "optional secret must not raise"
    assert notify("test", "body", failing=1) is False, "unconfigured notify must return False"

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
