"""Build, deploy and run the bronze -> silver transforms.

    python deploy_silver.py            # dry run
    python deploy_silver.py --apply    # create/update the notebook and run it

Writes cd_silver_* into CD_Silver_Lakehouse from the raw payloads in CD_Bronze.

Bronze is EMPTY until cd_01_extract_procore can authenticate, so this currently produces
empty silver tables. That is deliberate and useful: the pipeline shape is complete and
provably correct, and the moment credentials land the same notebook fills it. The SQL is
verified offline by _local/tests/test_silver.py (10 assertions) against real payload
shapes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deploy as dp  # noqa: E402
import deploy_seeds as ds  # noqa: E402
from make_notebooks import cell, notebook  # noqa: E402
from seedrunner import split_statements  # noqa: E402

HERE = Path(__file__).resolve().parent
CHARLEY_DEV = HERE.parent
SILVER_DIR = CHARLEY_DEV / "02-transformation" / "sql" / "silver"
# Every silver transform, in filename order. Prefixes carry meaning (naming-standards.md):
# 10_ is the Procore core, 20_ field operations. 00_/01_ are the gold SOURCE views and
# belong to deploy_gold, not here - globbing the whole folder would pull them in and fail
# on placeholders this notebook never substitutes.
#
# 30_manual_silver.sql WAS excluded, because it reads cd_bronze_man_*, which needed ten
# SharePoint lists that live in Affect's tenant. The note here said "add 30 the day the
# lists exist". They effectively do: `cd_06_land_manual` (deploy_manual.py) creates every
# cd_bronze_man_* table from CSV - empty and correctly typed when nobody has uploaded
# anything, with ProjectKey/Editor already wrapped in the {Title: ...} struct the parsers
# read. The empty-stub objection is answered by that notebook, not by this filter.
#
# Keeping 30 out was the ROOT CAUSE of the manual pipeline being permanently empty: with no
# cd_silver_man_*, the gold man_* tables had nothing to read and stayed placeholders. The
# run order (cd_06_land_manual before cd_10_bronze_to_silver) is what makes including it
# safe, and it is the order 06-orchestration already runs.
#
# Deny-list, not allow-list: adding a silver parser should mean adding one file, not
# also remembering to widen a filter in a deploy script. A forgotten widening fails
# silently - the table simply never builds and every measure over it reads as zero.
SILVER_FILES = sorted(p for p in SILVER_DIR.glob("*.sql")
                      if p.name[:2] not in ("00", "01"))

NOTEBOOK_NAME = "cd_10_bronze_to_silver"

# The bronze contract, exactly as procore_extract.to_bronze_row writes it. Declared here so
# silver builds before ingestion has ever run - otherwise every statement fails with
# "table not found", which looks like broken SQL rather than an empty pipeline.
def _scan(pattern: str) -> list[str]:
    """Every name matching `pattern` across the silver SQL, deduped and sorted."""
    found: set[str] = set()
    for path in SILVER_FILES:
        found.update(re.findall(pattern, path.read_text(encoding="utf-8")))
    return sorted(found)


# Read out of the SQL rather than listed by hand. A hand-kept list has to be edited in
# lockstep with the parsers, and forgetting is not a loud failure: the bronze view is never
# registered, the CREATE TABLE fails with TABLE_OR_VIEW_NOT_FOUND, and the only clue is a
# generic "session cancelled" from the jobs API. Adding a parser should mean adding one
# file and nothing else.
# Anchored on FROM/JOIN so it reads real usage, not prose. An unanchored scan also picks
# up the `cd_bronze_procore_*` written in a comment and tries to register a view for it.
BRONZE_TABLES = _scan(r"(?:FROM|JOIN)\s+(cd_bronze_\w+)")
# Same argument for what gets row-counted at the end. A silver table missing from a
# hand-kept verification list is simply never checked, which is the quietest way for a
# transform to be broken and look fine.
SILVER_TABLES = _scan(r"CREATE OR REPLACE TABLE\s+(cd_silver_\w+)")
BRONZE_SCHEMA = ("_key STRING, _project_id STRING, payload STRING, "
                 "_ingested_at TIMESTAMP, _batch_id STRING, _row_hash STRING")


# One splitter, shared with the offline runner - see seedrunner.split_statements. The
# local copy this replaces split on every `;`, including the ones inside string literals.
statements = split_statements


def silver_lakehouse() -> dict:
    ids = json.loads((HERE / "fabric_ids.json").read_text())
    lh = ids["CD_Silver_Lakehouse"]
    assert lh["defaultSchema"] == "dbo", "silver lakehouse is not schema-enabled"
    return lh


def build_notebook() -> dict:
    bronze_id = json.loads((HERE / "fabric_ids.json").read_text())["CD_Bronze_Lakehouse"]["id"]
    bronze_abfss = (f"abfss://{dp.WORKSPACE_ID}@onelake.dfs.fabric.microsoft.com/"
                    f"{bronze_id}/Tables/dbo")

    cells = [
        cell(
            f"""
# {NOTEBOOK_NAME}

Parses the raw Procore payloads in **CD_Bronze_Lakehouse** into typed, trimmed, validated
tables in **CD_Silver_Lakehouse**.

Generated by `_local/deploy_silver.py` - edit the `.sql`, not this notebook.

The column names silver produces are a CONTRACT: they must match what
`sql/silver/01_source_views_cd.sql` exposes as `sv_*`, because every gold file reads
`sv_*` and nothing else. That is what makes switching gold's source a one-file change.

Verified offline by `_local/tests/test_silver.py` - 10 assertions against real payload
shapes, including the sv_* column contract itself.
""",
            "markdown",
        ),
        cell(
            f'''
import json, os, traceback

DIAG = "/lakehouse/default/Files/_diag"
os.makedirs(DIAG, exist_ok=True)
results = []

def run_sql(label, sql):
    try:
        spark.sql(sql)
        results.append({{"step": label, "ok": True}})
    except Exception as exc:
        results.append({{"step": label, "ok": False,
                         "error": f"{{type(exc).__name__}}: {{exc}}"[:1500], "sql": sql[:500]}})
        print(f"  FAILED {{label}}: {{type(exc).__name__}}: {{str(exc)[:300]}}")

# Bronze lives in a DIFFERENT lakehouse, so it is registered as views rather than read
# through the default catalog. CREATE IF NOT EXISTS declares the contract so silver builds
# cleanly before ingestion has ever run - an empty table is a valid state, a missing one
# looks like broken SQL.
# json_field(payload, 'KEY') - look a JSON key up by NAME, not by path.
#
# get_json_object uses a simplified JSONPath that silently returns NULL for bracket keys
# containing '(', ')' or '='. Affect's budget view names its columns
# "UPDATED PRIME CONTRACT BUDGET (D = A+B+C)", so every money column parsed to NULL and
# cd_silver_budgets came out empty - which reads as "Procore has no budget data" rather
# than "the path syntax lost". A dict lookup has no grammar to trip over.
#
# ponytail: a Python UDF, so one interpreter call per row. It is used on ONE table
# (404 budget rows), where that is unmeasurable next to the dialect risk it removes.
# Reach for from_json(payload,'map<string,string>')['KEY'] if it ever spreads to a
# million-row table.
def _json_field(payload, key):
    if not payload:
        return None
    try:
        value = json.loads(payload).get(key)
    except Exception:
        return None
    return None if value is None else str(value)

spark.udf.register("json_field", _json_field, "string")

BRONZE = "{bronze_abfss}"
for t in {BRONZE_TABLES!r}:
    try:
        spark.sql(f"CREATE OR REPLACE TEMPORARY VIEW {{t}} AS "
                  f"SELECT * FROM delta.`{{BRONZE}}/{{t}}`")
    except Exception:
        # Not yet extracted. Declare the shape so the transforms are exercisable now.
        spark.sql(f"CREATE OR REPLACE TEMPORARY VIEW {{t}} AS "
                  f"SELECT * FROM (SELECT NULL AS _key, NULL AS _project_id, "
                  f"NULL AS payload, NULL AS _ingested_at, NULL AS _batch_id, "
                  f"NULL AS _row_hash) WHERE 1=0")
        print(f"  {{t}}: not extracted yet, declared empty")
'''
        ),
    ]

    # One cell per .sql file, labelled with its filename. Labels matter: the run diag
    # records the failing step, and 'silver:7' says far less than
    # '20_fieldops_silver.sql:2' when a statement fails at 6am.
    for path in SILVER_FILES:
        body = "\n".join(
            f"run_sql({json.dumps(path.name + ':' + str(i))}, {json.dumps(s)})\n"
            for i, s in enumerate(statements(path.read_text(encoding="utf-8")))
        )
        cells.append(cell(f"# --- {path.name} ---\n{body}"))

    cells.append(
        cell(
            # Concatenated rather than interpolated: the rest of this cell is full of
            # inner f-strings, and making the whole thing an f-string means escaping every
            # one of them.
            f"tables = {SILVER_TABLES!r}\n"
            """
# WRITE THE DIAG BEFORE COUNTING ANYTHING.
#
# It used to be written after the count loop, and that loop raises uncaught when a table
# does not exist - which is exactly what happens when a CREATE above it failed. So the one
# artefact that says WHICH statement failed was skipped precisely when it was needed, and
# the only thing left was the jobs API's generic "System cancelled the Spark session due to
# statement execution failures". Two runs were spent rediscovering that.
#
# The per-statement results are complete by this point; the counts are a bonus. Write what
# is known first, then enrich.
with open(f"{DIAG}/silver_run.json", "w", encoding="utf-8") as fh:
    json.dump(results, fh, indent=1)

counts = {}
for t in tables:
    # A missing table is a FAILED CREATE upstream, already recorded in results. Catch it so
    # the loop reaches the tables after it, rather than hiding them behind the first gap.
    try:
        counts[t] = spark.sql(f"SELECT COUNT(*) AS n FROM {t}").collect()[0]["n"]
        print(f"  {t:<34} {counts[t]:>7} rows")
    except Exception as exc:
        counts[t] = None
        print(f"  {t:<34}   MISSING  ({type(exc).__name__})")

rejects = spark.sql("SELECT COUNT(*) AS n FROM cd_dq_rejects").collect()[0]["n"]
print(f"\\n  cd_dq_rejects {rejects} row(s) - rows that failed their key check")

results.append({"step": "verification", "ok": True, "counts": counts, "rejects": rejects})
with open(f"{DIAG}/silver_run.json", "w", encoding="utf-8") as fh:
    json.dump(results, fh, indent=1)

failed = [r for r in results if not r["ok"]]
if failed:
    raise AssertionError(
        f"{len(failed)} statement(s) failed:\\n  "
        + "\\n  ".join(f"{r['step']}: {r['error'][:200]}" for r in failed[:5]))

# Zero rows is EXPECTED until cd_01_extract_procore can authenticate, so this is not an
# error - but it must be visible, not mistaken for a working pipeline.
if sum(v for v in counts.values() if v is not None) == 0:
    print("\\nAll silver tables are empty - bronze has not been extracted yet.")
    print("See _docs/procore-ingestion.md: the ingestion needs Procore credentials.")
else:
    built = [v for v in counts.values() if v is not None]
    print(f"\\nsilver built: {sum(built)} rows across {len(built)} of {len(tables)} tables")
"""
        )
    )
    return notebook(cells)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    tok = dp.token()
    lh = silver_lakehouse()
    print(f"silver lakehouse {lh['id']}")
    for path in SILVER_FILES:
        print(f"  {path.name:<28} {len(statements(path.read_text(encoding='utf-8')))} statement(s)")

    nb = ds.attach(build_notebook(), lh, dp.WORKSPACE_ID)
    nb["metadata"]["dependencies"]["lakehouse"]["default_lakehouse_name"] = "CD_Silver_Lakehouse"

    existing = ds.find_item(tok, NOTEBOOK_NAME, "Notebook")
    print(f"would {'update' if existing else 'create'} {NOTEBOOK_NAME} "
          f"({len(nb['cells'])} cells) and run it")

    if not args.apply:
        print("\nDRY RUN - nothing written. Re-run with --apply.")
        return 0

    definition = {"format": "ipynb", "parts": [
        {"path": "notebook-content.ipynb", "payload": ds.payload(nb),
         "payloadType": "InlineBase64"}]}

    if existing:
        status, _, headers = dp.call(
            "POST", f"/workspaces/{dp.WORKSPACE_ID}/items/{existing['id']}/updateDefinition",
            tok, {"definition": definition})
        if status == 202:
            dp.wait_for_operation(headers, tok)
        item_id = existing["id"]
        print(f"  updated {NOTEBOOK_NAME}")
    else:
        status, _, headers = dp.call(
            "POST", f"/workspaces/{dp.WORKSPACE_ID}/items", tok,
            {"displayName": NOTEBOOK_NAME, "type": "Notebook",
             "folderId": dp.FOLDER_ID, "definition": definition})
        if status == 202:
            dp.wait_for_operation(headers, tok)
        item_id = ds.find_item(tok, NOTEBOOK_NAME, "Notebook")["id"]
        print(f"  created {NOTEBOOK_NAME} ({item_id})")

    print("  running ...", end=" ", flush=True)
    print(ds.run_notebook(tok, item_id))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except dp.FabricError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
