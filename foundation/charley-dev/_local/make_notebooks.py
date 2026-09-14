"""Generate the Fabric .ipynb notebooks from the source below.

Notebooks are generated rather than hand-edited because hand-editing JSON is how you get
a notebook that will not open, and because the interesting content is the Python - which
belongs under review as Python, not as escaped strings inside a JSON blob.

Run:  python make_notebooks.py
"""

from __future__ import annotations

import json
from pathlib import Path

CHARLEY_DEV = Path(__file__).resolve().parent.parent


def cell(source: str, kind: str = "code") -> dict:
    lines = source.strip("\n").splitlines(keepends=True)
    base = {"cell_type": kind, "metadata": {}, "source": lines}
    if kind == "code":
        base |= {"execution_count": None, "outputs": []}
    return base


def notebook(cells: list[dict]) -> dict:
    """A Fabric-compatible notebook. No outputs are ever stored.

    The Fabric export in foundation/ had to be scrubbed because saved cell outputs held
    18 live Procore access tokens. Generating with empty outputs means that class of leak
    cannot happen here in the first place.
    """
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Synapse PySpark", "name": "synapse_pyspark"},
            "language_info": {"name": "python"},
            "microsoft": {"language": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


# ==========================================================================
# 01-ingestion/Procore/cd_01_extract_procore.ipynb
# ==========================================================================

EXTRACT_PROCORE = [
    cell(
        """
# cd_01_extract_procore

Pulls every endpoint in `config/endpoints.yml` into **CD_Bronze_Lakehouse**.

This notebook holds no endpoint logic. Auth, pagination, the v2.0 header rule, 429 retry
and watermarking live in `procore_extract.py`; parent-scope expansion lives in
`procore_scope.py`. Adding an endpoint is a YAML entry, not a change here.

**Attach this notebook to `CD_Bronze_Lakehouse` as its default lakehouse before running.**

Prerequisites:
- `Files/lib/` holds `fabric_common.py`, `procore_scope.py`, `procore_extract.py`
- `Files/config/endpoints.yml`
- Key Vault holds `PROCORE_CLIENT_ID`, `PROCORE_CLIENT_SECRET`, `PROCORE_COMPANY_ID`,
  and `PROCORE_KEYVAULT_URL` is set on the environment
""",
        "markdown",
    ),
    cell(
        """
import sys, os

# The shared library ships as Files/ in the lakehouse rather than being pasted into the
# notebook. One copy, one place to fix a bug.
sys.path.insert(0, "/lakehouse/default/Files/lib")

import requests

import fabric_common as fc
import procore_scope as ps
import procore_extract as px
import watermark as wm
import ratelimit as rl

CONFIG = "/lakehouse/default/Files/config/endpoints.yml"

batch_id = fc.new_batch_id()
print(f"batch {batch_id}")
"""
    ),
    cell(
        """
# Registry is validated on load: duplicate names, duplicate destination tables, a parent
# pointing at an endpoint that does not exist, or a parent cycle all raise here rather
# than surfacing hours later as an empty table.
endpoints = ps.load_registry(CONFIG)
ordered = ps.resolution_order(endpoints)   # parents before their children

print(f"{len(ordered)} endpoints")
for scope in ("company", "project", "parent"):
    names = [e.name for e in ordered if e.scope == scope]
    print(f"  {scope:<8} {len(names):>2}  {', '.join(names[:6])}{' ...' if len(names) > 6 else ''}")
"""
    ),
    cell(
        """
# Capture WHY this fails. The Fabric jobs API reports "statement execution failures" with
# no cell detail, so without this a missing credential and a genuine bug look identical.
import os, traceback, json as _json

DIAG = "/lakehouse/default/Files/_diag"
os.makedirs(DIAG, exist_ok=True)

def fail(stage, exc):
    detail = {"stage": stage, "error": f"{type(exc).__name__}: {exc}"[:1500],
              "trace": traceback.format_exc()[-1500:],
              "secrets_present": {k: bool(os.environ.get(k)) for k in
                                  ("PROCORE_CLIENT_ID", "PROCORE_CLIENT_SECRET",
                                   "PROCORE_COMPANY_ID", "PROCORE_KEYVAULT_URL",
                                   "PROCORE_BASE_URL")}}
    with open(f"{DIAG}/ingest_run.json", "w", encoding="utf-8") as fh:
        _json.dump(detail, fh, indent=1)
    print(f"FAILED at {stage}: {type(exc).__name__}: {str(exc)[:400]}")
    raise

try:
    settings = px.load_settings()
except Exception as exc:
    fail("load_settings (credentials)", exc)

session = rl.RateLimitedSession(requests.Session())
try:
    token = px.fetch_token(settings, session)
except Exception as exc:
    fail("fetch_token (Procore OAuth)", exc)
print("authenticated")

# Active projects only. The existing notebooks loop EVERY project on every run; most are
# closed, and Procore's rate limits are high but real. Jul 23 warehouse review.
try:
    projects = list(px.iter_active_projects(session, settings, token))
except Exception as exc:
    fail("enumerate active projects", exc)
project_ids = [p["id"] for p in projects if p.get("id") is not None]
print(f"{len(project_ids)} active projects")
"""
    ),
    cell(
        """
from datetime import timezone

# Records kept per endpoint so parent-scoped endpoints can read their parents' ids.
fetched: dict[str, list[dict]] = {}
summary = []

failures = []
endpoint_audit = []
parent_endpoints = {e.parent.endpoint for e in ordered if e.parent}

for ep in ordered:
  audit = {"endpoint": ep.name, "table": ep.bronze_table, "status": "started",
           "received_rows": 0, "normalized_rows": 0, "written_rows": 0, "scopes": [],
           "duplicate_rows_removed": None, "watermark_advanced": False}
  endpoint_audit.append(audit)
  try:
    parent_ids = None
    parent_incomplete = parent_excluded = False
    if ep.parent:
        if any(name == ep.parent.endpoint for name, _ in failures):
            raise RuntimeError(f"parent endpoint {ep.parent.endpoint} failed; child coverage unknown")
        parent_incomplete = any(a["endpoint"] == ep.parent.endpoint and
                                a["status"] == "incomplete_scope" for a in endpoint_audit)
        audit["parent_scope_incomplete"] = parent_incomplete
        # A declared parent exclusion does not block the child, but children of the
        # excluded project were never listed: advancing the child watermark would skip
        # their older records once the tool is enabled. Hold it, as for an incomplete parent.
        parent_excluded = any(a["endpoint"] == ep.parent.endpoint and a.get("excluded_declared_scopes")
                              for a in endpoint_audit)
        audit["parent_scope_excluded"] = parent_excluded
        parent_ids = ps.collect_parent_ids(fetched.get(ep.parent.endpoint, []), ep.parent)
        if not parent_ids:
            # Not an error: a company with no prime contracts has no line items either.
            print(f"  {ep.name:<32} skipped - parent '{ep.parent.endpoint}' returned nothing")
            summary.append((ep.name, 0, "skipped"))
            audit["status"] = "incomplete_scope" if parent_incomplete else "no_parent_records"
            continue

    # A changed child need not change its parent. Discover the complete current
    # parent population, or unchanged contracts lose their new lines/applications.
    # Child endpoints can still use their own supported incremental filters.
    full_parent_discovery = ep.name in parent_endpoints
    since = wm.read_since(spark, ep.bronze_table, ep.name) if ep.incremental and not full_parent_discovery else None
    audit["full_parent_discovery"] = full_parent_discovery
    audit["mode"] = "incremental" if since else "full"
    audit["since"] = str(since) if since else None

    headers = px.build_headers(token, settings.company_id, ep)
    # Shared with extract_procore_local.py. Company scoping, the incremental watermark and
    # the declared date window are all decided in one function, so this notebook cannot
    # quietly ship without one of them again.
    params = px.build_params(ep, settings.company_id, since if ep.incremental else None)

    records, rows = [], []
    ingested_at = fc.utc_now()
    raw_directory = f"{DIAG}/ingestion/{batch_id}"
    os.makedirs(raw_directory, exist_ok=True)
    audit["raw_archive"] = f"{raw_directory}/{ep.name}.jsonl"
    audit["archived_rows"] = 0
    audit["raw_archive_complete"] = False
    # Exclusive creation prevents replay from overwriting an earlier source capture.
    # Closing the archive must succeed before any bronze merge or watermark write.
    with open(audit["raw_archive"], "x", encoding="utf-8") as raw_archive:
        skipped = excluded = 0
        for path, project_id in ps.expand_paths(ep, settings.company_id, project_ids, parent_ids):
            scope_audit = {"path": path, "project_id": project_id,
                           "status": "started", "received_rows": 0}
            audit["scopes"].append(scope_audit)
            try:
                for record in px.iter_records(session, settings.base_url, path, headers,
                                              params=params):
                    # Preserve the decoded source record before normalization or merging.
                    scope_audit["received_rows"] += 1
                    audit["received_rows"] += 1
                    raw_archive.write(_json.dumps({"path": path, "project_id": project_id,
                                                  "record": record}, default=str) + "\\n")
                    audit["archived_rows"] += 1
                    # The project this was fetched under, for the child endpoints that need it.
                    for normalized in ps.normalize_records(ep, record, path):
                        normalized = px.stamp_project(normalized, project_id)
                        records.append(normalized)
                        rows.append({
                            **px.to_bronze_row(normalized, ep, project_id, ingested_at),
                            "_batch_id": batch_id,
                            "_row_hash": fc.row_hash(normalized),
                        })
                        audit["normalized_rows"] += 1
                scope_audit["status"] = "complete"
                # Declarations never expire on their own. Say so when one is stale; don't fail.
                if ps.declared_unavailable(ep, project_id):
                    scope_audit["note"] = "declared_exclusion_now_available"
                    audit.setdefault("warnings", []).append(
                        {"warning": "declared_exclusion_now_available", "project_id": project_id})
                    print(f"      WARNING project {project_id}: declared exclusion now returns data - remove it from endpoints.yml")
            except Exception as exc:                                    # noqa: BLE001
                # The legacy helper recognizes HTTP 403/404, not proof of a disabled
                # tool. Preserve the scope gap; finish other pulls, then block the run.
                scope_audit["error_type"] = type(exc).__name__
                scope_audit["http_status"] = getattr(getattr(exc, "response", None), "status_code", None)
                scope_audit["status"] = "failed"
                if not px.is_tool_not_enabled(exc) or scope_audit["received_rows"]:
                    raise
                # A declared (endpoint, project) exclusion carries its reason into the
                # manifest and does not block. Anything undeclared is still a coverage gap.
                reason = ps.declared_unavailable(ep, project_id)
                if reason:
                    scope_audit["status"] = "excluded_declared"
                    scope_audit["exclusion_reason"] = reason
                    excluded += 1
                    continue
                scope_audit["status"] = f"unavailable_{scope_audit['http_status']}"
                skipped += 1
        if excluded:
            audit["excluded_declared_scopes"] = excluded
            print(f"      ({excluded} scope(s) excluded by declaration in endpoints.yml)")
        if skipped:
            print(f"      ({skipped} scope(s) unavailable - permission, endpoint or tool configuration requires review)")

    audit["raw_archive_complete"] = True

    if rows:
        df = spark.createDataFrame(rows, px.bronze_schema())
        # MERGE on the natural key, not DROP + append: re-running is a no-op, so the
        # deliberate one-hour watermark overlap cannot duplicate rows.
        audit["written_rows"] = fc.merge_delta(spark, df, ep.bronze_table, px.bronze_merge_keys(ep))
        audit["duplicate_rows_removed"] = len(rows) - audit["written_rows"]
        if audit["duplicate_rows_removed"] < 0:
            raise RuntimeError("merge reported more input rows than were received")

        high = wm.high_water(records, "updated_at")
        # A global watermark must not move past a scope that was not read.
        # Declared exclusions also hold it back, or the project would miss history once enabled.
        if ep.incremental and high and not skipped and not excluded and not parent_incomplete and not parent_excluded:
            wm.write_watermark(spark, ep.bronze_table, ep.name, high, batch_id)
            audit["watermark_advanced"] = True

    else:
        audit["duplicate_rows_removed"] = 0

    fetched[ep.name] = records
    audit["status"] = "incomplete_scope" if skipped or parent_incomplete else "complete"
    fc.log_run(spark, batch_id, "extract_procore", ep.bronze_table, len(rows))
    summary.append((ep.name, len(rows), "incremental" if since else "full"))
    print(f"  {ep.name:<32} {len(rows):>7} rows  ({summary[-1][2]})")

  except Exception as exc:                                          # noqa: BLE001
    audit["status"] = "failed"
    audit["error_type"] = type(exc).__name__
    # One endpoint's contract being wrong must not cost the other 43. commitment_contracts
    # is the live example: a REST v2.0 path that 400s on page/per_page, because v2.0 pages
    # by cursor. That is a real defect, it is named in the summary below, and it still
    # fails the run - but only after everything that could land has landed.
    #
    # 403/404 is recorded one level in as an unavailable scope, not an empty source. Everything
    # else arrives here.
    failures.append((ep.name, f"{type(exc).__name__}: {exc}"[:300]))
    summary.append((ep.name, 0, "failed"))
    print(f"  {ep.name:<32} FAILED  {type(exc).__name__}: {str(exc)[:160]}")
  finally:
    # Retain finished endpoint evidence even if a later endpoint or the session fails.
    # Failure to persist this checkpoint stops extraction; no unauditable success.
    os.makedirs(f"{DIAG}/ingestion/{batch_id}", exist_ok=True)
    with open(f"{DIAG}/ingestion/{batch_id}/{ep.name}.audit.json", "x", encoding="utf-8") as fh:
        _json.dump({"batch": batch_id, **audit}, fh, indent=1, default=str)
"""
    ),
    cell(
        """
total = sum(n for _, n, _ in summary)
evidence = {"batch": batch_id, "source_scope": "active_projects",
            "written_rows_semantics": "Distinct input rows in a successful upsert; not inserted/updated totals",
            "normalized_rows_semantics": "Rows after expanding source groups; equals written_rows plus duplicate_rows_removed after a successful merge",
            "project_ids": project_ids, "endpoints": endpoint_audit,
            "status": "failed" if failures else (
                "incomplete_scope" if any(a["status"] == "incomplete_scope" for a in endpoint_audit)
                else "complete")}
# Keep batch-addressable evidence as well as the latest-run diagnostic. An evidence
# write failure must fail the notebook, rather than leave an unauditable success.
os.makedirs(f"{DIAG}/ingestion", exist_ok=True)
for destination, mode in ((f"{DIAG}/ingestion/{batch_id}.json", "x"), (f"{DIAG}/ingest_run.json", "w")):
    with open(destination, mode, encoding="utf-8") as fh:
        _json.dump(evidence, fh, indent=1, default=str)
empty = [name for name, n, mode in summary
         if n == 0 and mode not in ("skipped", "failed")]

print(f"\\nbatch {batch_id}: {total} rows across {len(summary)} endpoints")
if empty:
    # Worth surfacing rather than burying: on a full reload an empty result usually means
    # a permission gap or a tool Affect does not use, not genuinely zero records.
    print(f"returned nothing: {', '.join(empty)}")

if failures:
    print(f"\\n{len(failures)} endpoint(s) FAILED:")
    for name, detail in failures:
        print(f"  {name:<32} {detail}")
    # Raise only now. Everything that could land has landed and been merged, so the rerun
    # after a fix is incremental rather than a full re-pull - and the pipeline still goes
    # red, which is the point. Silently succeeding on 43 of 44 is how one endpoint stays
    # broken for a month.
    raise RuntimeError(
        f"{len(failures)} of {len(summary)} endpoints failed: "
        + ", ".join(name for name, _ in failures)
    )

incomplete = [a["endpoint"] for a in endpoint_audit if a["status"] == "incomplete_scope"]
if incomplete:
    raise RuntimeError("source scope coverage is incomplete; review permissions or explicitly justified exclusions: "
                       + ", ".join(incomplete))
"""
    ),
]


# ==========================================================================
# 01-ingestion/Outbuild/cd_02_extract_outbuild.ipynb
# ==========================================================================

EXTRACT_OUTBUILD = [
    cell(
        """
# cd_02_extract_outbuild

Pulls every Outbuild endpoint in `Files/config/outbuild_endpoints.yml` into
**CD_Bronze_Lakehouse**. Outbuild is the ONLY milestone source (fct_Milestone, Schedule page).

No endpoint logic here: requests, paging, transient-5xx retry, the bronze row shape, raw
archive, manifest and the failure policy live in `extract_outbuild_local.py` (`extract()`).
Every endpoint is a full pull, so there are no watermarks.

Failure policy: an endpoint that still fails after retries fails this notebook only if it is
`consumed: true` (read by silver: projects, activities). Any other failure is a warning in
`Files/_diag/ingestion/<batch>.json`.

Generated by `_local/make_notebooks.py`; deployed by `_local/deploy_outbuild.py`.
""",
        "markdown",
    ),
    cell(
        """
import sys
sys.path.insert(0, "/lakehouse/default/Files/lib")

from pyspark.sql import functions as F

import fabric_common as fc
import extract_outbuild_local as ob

CONFIG = "/lakehouse/default/Files/config/outbuild_endpoints.yml"
DIAG = "/lakehouse/default/Files/_diag"
# The contract cd_05_land_to_bronze writes; the existing tables were created by it.
COLUMNS = ["_key", "_project_id", "payload", "_ingested_at", "_batch_id",
           "_row_hash", "_source_endpoint", "_merge_key"]

batch_id = fc.new_batch_id()
endpoints = ob.load_registry(CONFIG)
# Fails closed inside Fabric: a missing secret raises here, before any request.
token = fc.get_secret("OUTBUILD_API_TOKEN")
print(f"batch {batch_id}: {len(endpoints)} endpoints")
"""
    ),
    cell(
        """
def write(table, rows):
    df = spark.createDataFrame([[r[c] for c in COLUMNS] for r in rows],
                               ", ".join(f"`{c}` string" for c in COLUMNS))
    df = fc.prepare_merge(df.withColumn("_ingested_at", F.to_timestamp("_ingested_at")),
                          ["_merge_key"])
    if not spark.catalog.tableExists(table):
        df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(table)
    else:
        df.createOrReplaceTempView("_outbuild_staged")
        spark.sql(fc.merge_sql(table, "_outbuild_staged", ["_merge_key"], COLUMNS))
    n = df.count()
    fc.log_run(spark, batch_id, "extract_outbuild", table, n)
    return n

manifest = ob.extract(endpoints, token, batch_id, DIAG, write)

for a in manifest["endpoints"]:
    detail = a.get("error") or a.get("note") or ""
    print(f"  {a['endpoint']:<28} {a['status']:<9} {a['written_rows']:>7} rows  {detail[:160]}")
print(f"\\n{manifest['total_rows']} rows, status {manifest['status']}")
if manifest["warnings"]:
    print(f"WARNING - unconsumed endpoint(s) failed, not blocking: {', '.join(manifest['warnings'])}")
if manifest["blocking_failures"]:
    raise RuntimeError("consumed Outbuild endpoint(s) failed: "
                       + ", ".join(manifest["blocking_failures"])
                       + f" - see Files/_diag/ingestion/{batch_id}.json")
"""
    ),
]


NOTEBOOKS = {
    "01-ingestion/Procore/cd_01_extract_procore.ipynb": EXTRACT_PROCORE,
    "01-ingestion/Outbuild/cd_02_extract_outbuild.ipynb": EXTRACT_OUTBUILD,
}


def main() -> int:
    for rel, cells in NOTEBOOKS.items():
        path = CHARLEY_DEV / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(notebook(cells), indent=1) + "\n", encoding="utf-8")

        # A notebook that will not parse is worse than no notebook.
        reloaded = json.loads(path.read_text(encoding="utf-8"))
        assert reloaded["nbformat"] == 4
        assert all(c["cell_type"] in ("code", "markdown") for c in reloaded["cells"])
        assert not any(c.get("outputs") for c in reloaded["cells"]), "outputs must never be stored"
        print(f"  wrote {rel}  ({len(cells)} cells)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
