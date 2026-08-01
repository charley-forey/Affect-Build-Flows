# Fabric notebook source

# MARKDOWN ********************

# ## Procore -> bronze
#
# One notebook for every Procore endpoint. The endpoints live in `config/endpoints.yml`;
# adding one is a YAML entry, not a new notebook.
#
# This replaces the per-entity notebook pattern deliberately. Auth, pagination, retry,
# the v2.0 header rule and the watermark are implemented once in `procore_extract.py`,
# so a fix lands in one place instead of N.
#
# **Setup (once):** upload `procore_extract.py`, `config/endpoints.yml` and the `sql/`
# folder to the Lakehouse under `Files/procore/`, and set `PROCORE_KEYVAULT_URL` plus the
# three secrets in Key Vault. Nothing goes in a notebook cell.

# CELL ********************

import sys

CODE_PATH = "/lakehouse/default/Files/procore"
if CODE_PATH not in sys.path:
    sys.path.append(CODE_PATH)

import requests
from delta.tables import DeltaTable

from procore_extract import (
    extract_endpoint,
    fetch_token,
    iter_active_projects,
    load_endpoints,
    load_settings,
)

# CELL ********************

settings = load_settings()
endpoints = load_endpoints(f"{CODE_PATH}/config/endpoints.yml")
session = requests.Session()
token = fetch_token(settings, session)

print(f"{len(endpoints)} endpoints registered")

# CELL ********************

# Only active projects. The previous pattern looped every project on every run, which is
# heavy against a per-app hourly rate limit and mostly re-pulls closed jobs.
projects = list(iter_active_projects(session, settings, token))
project_ids = [int(p["id"]) for p in projects]
print(f"{len(project_ids)} active projects: {project_ids}")

# CELL ********************


def last_ingested_at(table: str):
    """Watermark for the incremental pull. None on first run => full pull."""
    if not spark.catalog.tableExists(table):  # noqa: F821
        return None
    row = spark.sql(f"SELECT MAX(_ingested_at) AS m FROM {table}").collect()[0]  # noqa: F821
    return row["m"]


def merge_bronze(rows: list[dict], table: str) -> int:
    """MERGE on the natural key rather than overwriting the table.

    This is the fix for the full-reload defect. It also makes the run idempotent, which
    is what lets the watermark overlap by an hour without duplicating anything.
    """
    if not rows:
        return 0

    source = spark.createDataFrame(rows)  # noqa: F821
    if not spark.catalog.tableExists(table):  # noqa: F821
        source.write.format("delta").saveAsTable(table)
        return source.count()

    (
        DeltaTable.forName(spark, table)  # noqa: F821
        .alias("t")
        .merge(
            source.alias("s"),
            "t._key = s._key AND t._project_id <=> s._project_id",
        )
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
    return source.count()


# CELL ********************

for endpoint in endpoints:
    rows = extract_endpoint(
        session,
        settings,
        token,
        endpoint,
        project_ids,
        last_ingested=last_ingested_at(endpoint.bronze_table),
    )
    written = merge_bronze(rows, endpoint.bronze_table)
    print(f"{endpoint.name:24s} -> {endpoint.bronze_table:34s} {written:6d} rows")

# MARKDOWN ********************

# Bronze holds the **unparsed** payload plus `_ingested_at` / `_source_endpoint`.
# Keeping it raw means a transform bug is a re-run, not a re-extract - and it is the
# structural fix for transformations dropping the vendor / cost-code IDs the semantic
# model needs. Bronze cannot drop a column it never parsed.
