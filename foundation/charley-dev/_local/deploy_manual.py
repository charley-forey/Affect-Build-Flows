"""Land the manual-input lists from CSV, so data entry does not wait on SharePoint.

    python deploy_manual.py            # dry run
    python deploy_manual.py --apply    # deploy cd_06_land_manual and run it

WHY THIS EXISTS. About 40% of the monthly report lives in nobody's system - wins, risks,
priority items, the client survey, contract milestone dates. The design for it is a set of
SharePoint lists (`_docs/sharepoint-lists.md`), and it is a good design: versioned,
multi-user, permissioned, with an audit trail.

It is also blocked on a SharePoint administrator, and has been. Meanwhile the thing that
actually takes time is not the plumbing - it is people sitting down and typing a month of
history they have only ever kept in a spreadsheet. Blocking THAT on an admin ticket is the
expensive way round.

So this is the same destination by a road nobody has to unlock: fill a CSV, drop it in
OneLake, and it lands in exactly the bronze tables the SharePoint dataflow would have
written - same table names, same column shapes, same downstream parsers. When the lists are
provisioned, the dataflow takes over and nothing downstream changes. Neither path is
"temporary"; they are two writers into one contract.

    Files/_manual/_templates/<list>.csv     generated here - the blank to fill in
    Files/_manual/<list>.csv                what somebody uploads
    cd_bronze_man_<list>                     what this writes

A MISSING CSV IS NOT AN ERROR. Every list that has no file is created as an empty table
with the right schema, so silver and gold run to completion from day one and the report
shows honest blanks rather than failing. Partially-entered data is the normal state here
for months, and a pipeline that only works once every list is complete would never run.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deploy as dp  # noqa: E402
import deploy_seeds as ds  # noqa: E402
import make_sharepoint as ms  # noqa: E402
from make_notebooks import cell, notebook  # noqa: E402

HERE = Path(__file__).resolve().parent
CHARLEY_DEV = HERE.parent

NOTEBOOK_NAME = "cd_06_land_manual"

# THE LIST SPEC IS NOT WRITTEN HERE ANY MORE. It is derived from the man_* DDL in
# sql/gold/40_man_tables.sql and 41_man_qc_tables.sql, via make_sharepoint - the same
# source the provisioning script and the dataflow are generated from.
#
# It used to be a hand-kept dict, and it had drifted from gold on four of the nine tables:
# man_Flags collected CostMgmtFlag / ScheduleFlag that gold has never had while missing the
# three attestations it does, man_Milestones collected four single dates where gold wants
# two spans, man_Survey never collected SurveyedParty, and man_DailyLogCompliance collected
# LogsSubmitted where the scorecard scores LogsMissedSameDay. None of that errored. It
# simply meant the CSV a person filled in could not fill the table the report reads.
#
# Types are what the CSV is CAST to. Anything unparseable becomes NULL and is caught by the
# reject rules in 30/31_*_silver.sql rather than failing the load - a typo in one cell of
# one row must not stop the other sixteen lists.
SQL_TO_SPARK = {"STRING": "string", "INT": "int", "DOUBLE": "double",
                "DATE": "date", "BOOLEAN": "boolean"}

LISTS: dict[str, list[tuple[str, str]]] = {
    ms.csv_name(table): [(col, SQL_TO_SPARK[sql_type]) for col, sql_type in cols]
    for table, cols in ms.tables().items()
}

# One example row per list, written into the template. A blank template gets filled in
# wrongly - the format of MonthStart and the allowed values of a code column are exactly
# what somebody guesses at, and guessing produces rows that reject silently.
EXAMPLES: dict[str, list[str]] = {
    "wins": ["26-001", "2026-07-01", "1", "Topped out two weeks early", "Realized"],
    "risks": ["26-001", "2026-07-01", "1", "Curtain wall lead time",
              "HIGH", "Expedite fabrication; weekly vendor call", "PM", "IN_PROGRESS"],
    "priority_items": ["26-001", "2026-07-01", "1", "Level 3 slab pour", "AT_RISK",
                       "Concrete delivery delayed 3 days", "Saturday pour",
                       "No impact to substantial completion", ""],
    "flags": ["26-001", "2026-07-01", "Within Range", "125000.0", "TRUE", "Rev 3",
              "TRUE", "TRUE", "FALSE"],
    "survey": ["26-001", "2026-07-01", "1",
               "How satisfied are you with communication?", "4", "ANONYMOUS"],
    "safety_monthly": ["26-001", "2026-07-01", "12500.0", "0", "18", "310.5"],
    "quality_monthly": ["26-001", "2026-07-01", "42", "17", "3.5", "9.2"],
    "milestones": ["26-001", "A1042", "Substantial Completion", "2027-03-01",
                   "2027-03-31", "2027-03-01", "2027-03-31", "TRUE"],
    "daily_log_compliance": ["26-001", "2026-07-01", "22", "3"],

    # PQP. Every code below is a real value from seed/qc_status_vocab.csv, and every key a
    # real value from seed/qc_trades.csv or qc_gate_template.csv - because the example row
    # is what people copy, and an example carrying a plausible-but-wrong code teaches the
    # wrong vocabulary on day one.
    "qc_dfow": ["26-001", "D-07", "Cast-in-place concrete frame", "CONCRETE_FORMWORK",
                "3", "Pre-pour checklist and third-party survey", "Superintendent",
                "IN_PROGRESS", ""],
    "qc_itp": ["26-001", "ITP-014", "CONCRETE_FORMWORK", "Slab on grade pour",
               "Compressive strength test", "28-day break >= 4000 psi", "Hold",
               "QA Manager", "2026-07-14", "2026-07-14", "PASS", "COMPLETE", ""],
    "qc_gate": ["26-001", "TCO-A2", "TCO", "SUBMITTED", "I. Aguire (PM)", "2026-09-01",
                "2026-08-20", "", "", "Awaiting DOB NOW acceptance"],
    "qc_special_inspection": ["26-001", "SI-006", "Structural steel welding", "SIA",
                              "R. Patel", "YES", "YES", "2026-07-02", "2026-07-02",
                              "2026-07-09", "CLOSED", ""],
    "qc_commissioning": ["26-001", "CX-003", "Smoke purge fans", "HVAC", "MEP Manager",
                         "2026-10-01", "", "NOT_STARTED", ""],
    "qc_inspector_sign_in": ["26-001", "SI-2026-041", "2026-07-16", "T. Nguyen",
                             "NYC_DOB", "Facade progress inspection", "Levels 4-6",
                             "OBSERVATION_ONLY", "FALSE", ""],
    "qc_checklist_result": ["26-001", "EXCAVATION", "EXCAVATION-001",
                            "1_PREPARATORY", "PASS", "2026-07-08", "J. Alvarez", ""],
    "qc_doh_result": ["26-001", "H-01", "OWNER_DOH_CONSULTANT", "VERIFIED", "2026-07-20",
                      "QA Manager", "", ""],
}


def build_notebook() -> dict:
    spec = {name: cols for name, cols in LISTS.items()}
    examples = EXAMPLES

    cells = [
        cell(f'''
"""Land the manual-input CSVs into cd_bronze_man_*.

Generated by _local/deploy_manual.py - edit that, not this.
"""
import json
from pyspark.sql import functions as F
from pyspark.sql.types import (StructType, StructField, StringType, IntegerType,
                               DoubleType, DateType, BooleanType, TimestampType)

SPEC = {json.dumps(spec, indent=1)}
EXAMPLES = {json.dumps(examples, indent=1)}

MANUAL_DIR = "Files/_manual"
TEMPLATE_DIR = f"{{MANUAL_DIR}}/_templates"

TYPES = {{"string": StringType(), "int": IntegerType(), "double": DoubleType(),
          "date": DateType(), "boolean": BooleanType()}}
'''),

        cell('''
# ---------------------------------------------------------------- templates
#
# Written on every run, so the blank always matches what the loader will read. A template
# that has drifted from the loader is worse than none: somebody fills it in, it loads to
# nulls, and the report shows blanks with no error anywhere.
import os

local_templates = "/lakehouse/default/Files/_manual/_templates"
os.makedirs(local_templates, exist_ok=True)

for name, cols in SPEC.items():
    header = ",".join(c for c, _ in cols)
    example = ",".join(f'"{v}"' if ("," in v or " " in v) else v
                       for v in EXAMPLES.get(name, []))
    with open(f"{local_templates}/{name}.csv", "w", encoding="utf-8") as fh:
        fh.write(header + "\\n")
        if example:
            fh.write(example + "\\n")
print(f"templates written: {len(SPEC)} file(s) in Files/_manual/_templates/")
'''),

        cell('''
# ------------------------------------------------------------------- load
#
# ProjectKey and Editor are wrapped into {Title: ...}. SharePoint lookup and person columns
# arrive that shape, 30_manual_silver.sql reads ProjectKey.Title, and the whole design
# depends on both writers producing identical bronze - so the CSV path adapts to
# SharePoint's shape rather than the parsers being forked.
loaded = {}
for name, cols in SPEC.items():
    path = f"{MANUAL_DIR}/{name}.csv"
    schema = StructType([StructField(c, TYPES[t], True) for c, t in cols])
    try:
        exists = len(notebookutils.fs.ls(path)) > 0
    except Exception:
        exists = False

    if exists:
        df = (spark.read.option("header", True).option("mode", "PERMISSIVE")
              .schema(schema).csv(path))
        source = "csv"
    else:
        # Empty but correctly typed. Silver and gold then run to completion and the report
        # shows an honest blank - rather than the pipeline failing until every list is
        # populated, which would mean it never runs at all.
        df = spark.createDataFrame([], schema)
        source = "empty"

    out = (df
           .withColumn("ProjectKey", F.struct(F.col("ProjectKey").alias("Title")))
           # Modified/Editor are SharePoint's audit columns. On the CSV path there is no
           # per-row editor, so the load time and the file are recorded instead - which is
           # the truth: this row is only known to be as fresh as the upload.
           .withColumn("Modified", F.current_timestamp())
           .withColumn("Editor", F.struct(F.lit(f"csv:{name}.csv").alias("Title"))))

    out.write.format("delta").mode("overwrite") \\
       .option("overwriteSchema", "true").saveAsTable(f"cd_bronze_man_{name}")
    n = out.count()
    loaded[name] = {"rows": n, "source": source}
    print(f"  cd_bronze_man_{name:<24} {n:>5} row(s)  ({source})")
'''),

        cell('''
# ------------------------------------------------- the Job Register, declared only
#
# cd_bronze_man_job_register is written by CD_Manual_Ingest off the BUILD site, NOT from a
# CSV - the two Power Automate job flows own it and nobody types into it by hand. It is
# declared here anyway because 30_manual_silver.sql reads it, and until the dataflow is
# published the table does not exist: silver would fail on "table not found" and take the
# whole nightly pipeline with it, on a chain that is otherwise ready to run.
#
# CREATED ONLY IF ABSENT. Every other table above is written with mode("overwrite"), which
# is correct for them - the CSV is the whole truth each run. Doing that here would delete
# the register the dataflow just landed, every single night. That exact bug (a leftover
# overwrite that would have wiped gold the moment it started populating) has already been
# found once in this repo; this is the same shape and it is not repeated.
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType

JOB_REGISTER = "cd_bronze_man_job_register"

if spark.catalog.tableExists(JOB_REGISTER):
    print(f"  {JOB_REGISTER:<26} exists - left alone (the dataflow owns it)")
else:
    # The shape SharePoint.Tables returns. URL and person columns arrive as records, the
    # same way lookup columns do, which is why silver reads EstimatingFolderUrl.Url and
    # Editor.Title rather than the bare column.
    url = StructType([StructField("Url", StringType(), True)])
    schema = StructType([
        StructField("Id", IntegerType(), True),
        StructField("Title", StringType(), True),
        StructField("JobYear", IntegerType(), True),
        StructField("JobSeq", IntegerType(), True),
        StructField("JobNumber", StringType(), True),
        StructField("Stage", StringType(), True),
        StructField("EstimatingFolderUrl", url, True),
        StructField("ProjectFolderUrl", url, True),
        StructField("RequestedBy", StringType(), True),
        StructField("RequestedAt", TimestampType(), True),
        StructField("CompletedAt", TimestampType(), True),
        StructField("CopyJobStatus", StringType(), True),
        StructField("ErrorDetail", StringType(), True),
        StructField("Modified", TimestampType(), True),
        StructField("Editor", StructType([StructField("Title", StringType(), True)]), True),
    ])
    spark.createDataFrame([], schema).write.format("delta").saveAsTable(JOB_REGISTER)
    print(f"  {JOB_REGISTER:<26} declared empty - publish CD_Manual_Ingest to fill it")
'''),

        cell('''
total = sum(v["rows"] for v in loaded.values())
from_csv = [k for k, v in loaded.items() if v["source"] == "csv"]
print(f"\\n{total} manual row(s) across {len(loaded)} list(s); "
      f"{len(from_csv)} loaded from CSV, {len(loaded) - len(from_csv)} empty")

DIAG = "/lakehouse/default/Files/_diag"
import os
os.makedirs(DIAG, exist_ok=True)
with open(f"{DIAG}/manual_run.json", "w", encoding="utf-8") as fh:
    json.dump(loaded, fh, indent=1)

if total == 0:
    print("\\nNo manual data yet. This is EXPECTED until somebody fills a template:")
    print("  1. download Files/_manual/_templates/<list>.csv")
    print("  2. fill it in (one row per project per month)")
    print("  3. upload it to Files/_manual/<list>.csv")
    print("  4. re-run this notebook")
    print("\\nUntil then the scorecard's manual categories score BLANK, not zero -")
    print("which is the honest answer and what [Scorecard Coverage %] reports.")
'''),
    ]
    return notebook(cells)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    tok = dp.token()
    ids = json.loads((HERE / "fabric_ids.json").read_text())
    lh = {"id": ids["CD_Bronze_Lakehouse"]["id"]}
    print(f"bronze lakehouse {lh['id']}")
    print(f"{len(LISTS)} manual list(s): {', '.join(sorted(LISTS))}")

    nb = ds.attach(build_notebook(), lh, dp.WORKSPACE_ID)
    nb["metadata"]["dependencies"]["lakehouse"]["default_lakehouse_name"] = \
        "CD_Bronze_Lakehouse"

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
        print(f"  created {NOTEBOOK_NAME}")

    print("  running ... ", end="", flush=True)
    print(ds.run_notebook(tok, item_id))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
