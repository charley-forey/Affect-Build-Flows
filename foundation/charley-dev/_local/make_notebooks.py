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
"""
    ),
    cell(
        """
from datetime import timezone

# Records kept per endpoint so parent-scoped endpoints can read their parents' ids.
fetched: dict[str, list[dict]] = {}
summary = []

for ep in ordered:
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
    params = px.watermark_params(ep, since) if ep.incremental else {}
    if ep.scope == "company":
        params = {**params, "company_id": settings.company_id}

    records, rows = [], []
    ingested_at = fc.utc_now()
    for path, project_id in ps.expand_paths(ep, settings.company_id, project_ids, parent_ids):
        for record in px.iter_records(session, settings.base_url, path, headers, params=params):
            records.append(record)
            rows.append({
                **px.to_bronze_row(record, ep, project_id, ingested_at),
                "_batch_id": batch_id,
                "_row_hash": fc.row_hash(record),
            })

    fetched[ep.name] = records

    if rows:
        df = spark.createDataFrame(rows)
        # MERGE on the natural key, not DROP + append: re-running is a no-op, so the
        # deliberate one-hour watermark overlap cannot duplicate rows.
        fc.merge_delta(spark, df, ep.bronze_table, ["_key"])

        high = wm.high_water(records, "updated_at")
        if ep.incremental and high:
            wm.write_watermark(spark, ep.bronze_table, ep.name, high, batch_id)

    fc.log_run(spark, batch_id, "extract_procore", ep.bronze_table, len(rows))
    summary.append((ep.name, len(rows), "incremental" if since else "full"))
    print(f"  {ep.name:<32} {len(rows):>7} rows  ({summary[-1][2]})")
"""
    ),
    cell(
        """
total = sum(n for _, n, _ in summary)
empty = [name for name, n, mode in summary if n == 0 and mode != "skipped"]

print(f"\\nbatch {batch_id}: {total} rows across {len(summary)} endpoints")
if empty:
    # Worth surfacing rather than burying: on a full reload an empty result usually means
    # a permission gap or a tool Affect does not use, not genuinely zero records.
    print(f"returned nothing: {', '.join(empty)}")
"""
    ),
]


NOTEBOOKS = {
    "01-ingestion/Procore/cd_01_extract_procore.ipynb": EXTRACT_PROCORE,
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
