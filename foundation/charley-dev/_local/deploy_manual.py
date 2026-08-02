"""Land the manual-input lists from CSV, so data entry does not wait on SharePoint.

    python deploy_manual.py            # dry run
    python deploy_manual.py --apply    # deploy cd_06_land_manual and run it

WHY THIS EXISTS. About 40% of the monthly report lives in nobody's system - wins, risks,
priority items, the client survey, contract milestone dates. The design for it is ten
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
for months, and a pipeline that only works once all ten lists are complete would never run.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deploy as dp  # noqa: E402
import deploy_seeds as ds  # noqa: E402
from make_notebooks import cell, notebook  # noqa: E402

HERE = Path(__file__).resolve().parent
CHARLEY_DEV = HERE.parent

NOTEBOOK_NAME = "cd_06_land_manual"

# Column names are the SharePoint list column names from _docs/sharepoint-lists.md, because
# the whole point is that both writers produce the same bronze. `ProjectKey` and `Editor`
# arrive as plain text in a CSV and are wrapped into the {Title: ...} shape SharePoint
# lookup and person columns produce, since that is what 30_manual_silver.sql reads.
#
# Types are what the CSV is CAST to. Anything unparseable becomes NULL and is caught by the
# reject rules in 30_manual_silver.sql rather than failing the load - a typo in one cell of
# one row must not stop the other nine lists.
LISTS: dict[str, list[tuple[str, str]]] = {
    "wins": [
        ("ProjectKey", "string"), ("MonthStart", "date"), ("WinNumber", "int"),
        ("Description", "string"), ("WinType", "string"),
    ],
    "risks": [
        ("ProjectKey", "string"), ("MonthStart", "date"), ("RiskNumber", "int"),
        ("Description", "string"), ("ImpactCode", "string"), ("Mitigation", "string"),
        ("OwnerRole", "string"), ("StatusCode", "string"),
    ],
    "priority_items": [
        ("ProjectKey", "string"), ("MonthStart", "date"), ("ItemNumber", "int"),
        ("ScheduleItem", "string"), ("StatusCode", "string"), ("CriticalDelays", "string"),
        ("RecoveryPlan", "string"), ("ForecastImpact", "string"), ("Notes", "string"),
    ],
    "flags": [
        ("ProjectKey", "string"), ("MonthStart", "date"), ("ProfitabilityCode", "string"),
        ("CostMgmtFlag", "string"), ("ScheduleFlag", "string"), ("Notes", "string"),
    ],
    "survey": [
        ("ProjectKey", "string"), ("MonthStart", "date"), ("QuestionNumber", "int"),
        # The workbook stores the six SCORES and not the question TEXT, so nobody now knows
        # what was asked. This column is why the next survey will not have that problem.
        ("QuestionText", "string"), ("Score", "int"),
    ],
    "safety_monthly": [
        ("ProjectKey", "string"), ("MonthStart", "date"), ("HoursWorked", "double"),
        ("RecordableIncidents", "int"), ("Orientations", "int"), ("OtHours", "double"),
    ],
    "quality_monthly": [
        ("ProjectKey", "string"), ("MonthStart", "date"), ("Observations", "int"),
        ("PunchlistItems", "int"), ("AvgDaysPastDue", "double"),
        ("AvgDaysToClose", "double"),
    ],
    "milestones": [
        ("ProjectKey", "string"), ("MilestoneName", "string"), ("ContractDate", "date"),
        ("BaselineDate", "date"), ("ForecastDate", "date"), ("ActualDate", "date"),
    ],
    "daily_log_compliance": [
        ("ProjectKey", "string"), ("MonthStart", "date"), ("LogsExpected", "int"),
        ("LogsSubmitted", "int"),
    ],
}

# One example row per list, written into the template. A blank template gets filled in
# wrongly - the format of MonthStart and the allowed values of a code column are exactly
# what somebody guesses at, and guessing produces rows that reject silently.
EXAMPLES: dict[str, list[str]] = {
    "wins": ["26-001", "2026-07-01", "1", "Topped out two weeks early", "Realized"],
    "risks": ["26-001", "2026-07-01", "1", "Curtain wall lead time",
              "High", "Expedite fabrication; weekly vendor call", "PM", "Open"],
    "priority_items": ["26-001", "2026-07-01", "1", "Level 3 slab pour", "At Risk",
                       "Concrete delivery delayed 3 days", "Saturday pour",
                       "No impact to substantial completion", ""],
    "flags": ["26-001", "2026-07-01", "On Target", "Yes", "Yes", ""],
    "survey": ["26-001", "2026-07-01", "1",
               "How satisfied are you with communication?", "4"],
    "safety_monthly": ["26-001", "2026-07-01", "12500.0", "0", "18", "310.5"],
    "quality_monthly": ["26-001", "2026-07-01", "42", "17", "3.5", "9.2"],
    "milestones": ["26-001", "Substantial Completion", "2027-03-31", "2027-03-31",
                   "2027-04-14", ""],
    "daily_log_compliance": ["26-001", "2026-07-01", "22", "21"],
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
                               DoubleType, DateType, TimestampType)

SPEC = {json.dumps(spec, indent=1)}
EXAMPLES = {json.dumps(examples, indent=1)}

MANUAL_DIR = "Files/_manual"
TEMPLATE_DIR = f"{{MANUAL_DIR}}/_templates"

TYPES = {{"string": StringType(), "int": IntegerType(),
          "double": DoubleType(), "date": DateType()}}
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
        # shows an honest blank - rather than the pipeline failing until all ten lists are
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
