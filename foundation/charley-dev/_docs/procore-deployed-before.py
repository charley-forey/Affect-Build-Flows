# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "fa946636-e143-417b-b598-5cbd31ed9990",
# META       "default_lakehouse_name": "CD_Bronze_Lakehouse",
# META       "default_lakehouse_workspace_id": "1f7caed6-f88a-4e52-bc83-9a498a165301"
# META     }
# META   }
# META }

# MARKDOWN ********************

# # cd_01_extract_procore
# 
# Pulls every endpoint in `config/endpoints.yml` into **CD_Bronze_Lakehouse**.
# 
# This notebook holds no endpoint logic. Auth, pagination, the v2.0 header rule, 429 retry
# and watermarking live in `procore_extract.py`; parent-scope expansion lives in
# `procore_scope.py`. Adding an endpoint is a YAML entry, not a change here.
# 
# **Attach this notebook to `CD_Bronze_Lakehouse` as its default lakehouse before running.**
# 
# Prerequisites:
# - `Files/lib/` holds `fabric_common.py`, `procore_scope.py`, `procore_extract.py`
# - `Files/config/endpoints.yml`
# - Key Vault holds `PROCORE_CLIENT_ID`, `PROCORE_CLIENT_SECRET`, `PROCORE_COMPANY_ID`,
#   and `PROCORE_KEYVAULT_URL` is set on the environment

# CELL ********************

import sys, os

# The shared library ships as Files/ in the lakehouse rather than being pasted into the
# notebook. One copy, one place to fix a bug.
sys.path.insert(0, "/lakehouse/default/Files/lib")

import requests

import fabric_common as fc
import procore_scope as ps
import procore_extract as px
import watermark as wm

CONFIG = "/lakehouse/default/Files/config/endpoints.yml"

batch_id = fc.new_batch_id()
print(f"batch {batch_id}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Registry is validated on load: duplicate names, duplicate destination tables, a parent
# pointing at an endpoint that does not exist, or a parent cycle all raise here rather
# than surfacing hours later as an empty table.
endpoints = ps.load_registry(CONFIG)
ordered = ps.resolution_order(endpoints)   # parents before their children

print(f"{len(ordered)} endpoints")
for scope in ("company", "project", "parent"):
    names = [e.name for e in ordered if e.scope == scope]
    print(f"  {scope:<8} {len(names):>2}  {', '.join(names[:6])}{' ...' if len(names) > 6 else ''}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

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

session = requests.Session()
try:
    token = px.fetch_token(settings, session)
except Exception as exc:
    fail("fetch_token (Procore OAuth)", exc)
print("authenticated")

# Active projects only. The existing notebooks loop EVERY project on every run; most are
# closed, and Procore's rate limits are high but real. Jul 23 warehouse review.
projects = list(px.iter_active_projects(session, settings, token))
project_ids = [p["id"] for p in projects if p.get("id") is not None]
print(f"{len(project_ids)} active projects")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from datetime import timezone

# Records kept per endpoint so parent-scoped endpoints can read their parents' ids.
fetched: dict[str, list[dict]] = {}
summary = []

failures = []

for ep in ordered:
  try:
    parent_ids = None
    if ep.parent:
        parent_ids = ps.collect_parent_ids(fetched.get(ep.parent.endpoint, []), ep.parent)
        if not parent_ids:
            # Not an error: a company with no prime contracts has no line items either.
            print(f"  {ep.name:<32} skipped - parent '{ep.parent.endpoint}' returned nothing")
            summary.append((ep.name, 0, "skipped"))
            continue

    # Watermark is read BEFORE the pull and written only after it succeeds.
    since = wm.read_since(spark, ep.bronze_table, ep.name) if ep.incremental else None

    headers = px.build_headers(token, settings.company_id, ep)
    # Shared with extract_procore_local.py. Company scoping, the incremental watermark and
    # the declared date window are all decided in one function, so this notebook cannot
    # quietly ship without one of them again.
    params = px.build_params(ep, settings.company_id, since if ep.incremental else None)

    records, rows = [], []
    ingested_at = fc.utc_now()
    skipped = 0
    for path, project_id in ps.expand_paths(ep, settings.company_id, project_ids, parent_ids):
        try:
            for record in px.iter_records(session, settings.base_url, path, headers,
                                          params=params):
                # The project this was fetched under, for the child endpoints that need it.
                record = px.stamp_project(record, project_id)
                records.append(record)
                rows.append({
                    **px.to_bronze_row(record, ep, project_id, ingested_at),
                    "_batch_id": batch_id,
                    "_row_hash": fc.row_hash(record),
                })
        except Exception as exc:                                    # noqa: BLE001
            # One scope without the tool enabled must not cost the other 43 endpoints.
            # px.is_tool_not_enabled owns the rule; anything else is real and re-raises.
            if not px.is_tool_not_enabled(exc):
                raise
            skipped += 1
    if skipped:
        print(f"      ({skipped} scope(s) skipped - tool not enabled)")

    fetched[ep.name] = records

    if rows:
        df = spark.createDataFrame(rows, px.bronze_schema())
        # MERGE on the natural key, not DROP + append: re-running is a no-op, so the
        # deliberate one-hour watermark overlap cannot duplicate rows.
        fc.merge_delta(spark, df, ep.bronze_table, px.bronze_merge_keys(ep))

        high = wm.high_water(records, "updated_at")
        if ep.incremental and high:
            wm.write_watermark(spark, ep.bronze_table, ep.name, high, batch_id)

    fc.log_run(spark, batch_id, "extract_procore", ep.bronze_table, len(rows))
    summary.append((ep.name, len(rows), "incremental" if since else "full"))
    print(f"  {ep.name:<32} {len(rows):>7} rows  ({summary[-1][2]})")

  except Exception as exc:                                          # noqa: BLE001
    # One endpoint's contract being wrong must not cost the other 43. commitment_contracts
    # is the live example: a REST v2.0 path that 400s on page/per_page, because v2.0 pages
    # by cursor. That is a real defect, it is named in the summary below, and it still
    # fails the run - but only after everything that could land has landed.
    #
    # 403/404 is handled one level in, as "tool not enabled" for a single scope. Everything
    # else arrives here.
    failures.append((ep.name, f"{type(exc).__name__}: {exc}"[:300]))
    summary.append((ep.name, 0, "failed"))
    print(f"  {ep.name:<32} FAILED  {type(exc).__name__}: {str(exc)[:160]}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

total = sum(n for _, n, _ in summary)
empty = [name for name, n, mode in summary
         if n == 0 and mode not in ("skipped", "failed")]

print(f"\nbatch {batch_id}: {total} rows across {len(summary)} endpoints")
if empty:
    # Worth surfacing rather than burying: on a full reload an empty result usually means
    # a permission gap or a tool Affect does not use, not genuinely zero records.
    print(f"returned nothing: {', '.join(empty)}")

if failures:
    print(f"\n{len(failures)} endpoint(s) FAILED:")
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

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
