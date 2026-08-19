"""Generate sql/gold/08_qc_seeds.sql from the five PQP seed CSVs.

    python make_qc_seeds.py            # write 02-transformation/sql/gold/08_qc_seeds.sql
    python make_qc_seeds.py --check    # fail if the committed .sql is stale

WHY GENERATE INLINE VALUES RATHER THAN READ THE CSV.

`deploy_seeds.py` INLINES the seed SQL into the notebook precisely so there is no separate
upload step - the .sql files stay the single source of truth and regenerating picks up any
edit. A `read_csv` in the SQL would break that: the file would have to be uploaded to
OneLake first, and the offline DuckDB run and the Spark run would need different syntax for
it, which is exactly what `sv_*` isolation exists to avoid.

So the CSVs are the extraction record and this turns them into the same `VALUES` shape
every other seed already uses (see 04_dim_activitycategory.sql). `test_qc.py` runs
`--check`, so a CSV edited without regenerating fails the suite rather than drifting.

EVERY VALUE IS EMITTED AS A STRING LITERAL and cast in the SELECT. Spark infers a VALUES
column's type from the literals, so a column whose first row is NULL comes out NullType and
a later INT breaks the whole statement. Casting outside the VALUES makes the types explicit
and identical on both engines.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHARLEY_DEV = HERE.parent
SEED_DIR = CHARLEY_DEV / "02-transformation" / "seed"
OUT = CHARLEY_DEV / "02-transformation" / "sql" / "gold" / "08_qc_seeds.sql"

# csv file -> (table, {column: sql type}, natural key for de-duplication)
#
# The two structural collapses are visible right here, which is the point of the shape:
# 26 trade checklist sheets share ONE schema so they are ONE table discriminated by
# TradeKey, and Path to TCO / Path to Fire Alarm / Statutory Inspections share one shape
# so they are ONE table discriminated by GateType.
SEEDS: tuple[tuple[str, str, dict[str, str], tuple[str, ...]], ...] = (
    (
        "qc_trades.csv", "qc_seed_Trade",
        {"TradeKey": "STRING", "TradeName": "STRING", "SheetName": "STRING",
         "CsiCode": "STRING", "DfowRef": "STRING", "RiskTier": "INT", "SortOrder": "INT"},
        ("TradeKey",),
    ),
    (
        "qc_checklist_items.csv", "qc_seed_ChecklistItem",
        {"TradeKey": "STRING", "ItemNumber": "INT", "ItemText": "STRING",
         "ItemKey": "STRING"},
        ("ItemKey",),
    ),
    (
        "qc_gate_template.csv", "qc_seed_Gate",
        {"GateType": "STRING", "GateKey": "STRING", "Step": "STRING", "Section": "STRING",
         "Gate": "STRING", "Authority": "STRING", "Agency": "STRING",
         "Prerequisite": "STRING", "Responsible": "STRING", "EvidenceRequired": "STRING",
         "SortOrder": "INT", "LinkedTcoGate": "STRING"},
        ("GateKey",),
    ),
    (
        "qc_doh_items.csv", "qc_seed_DohItem",
        {"ItemKey": "STRING", "Section": "STRING", "Requirement": "STRING",
         "Responsibility": "STRING", "AffectInterface": "STRING",
         "EvidenceRequired": "STRING", "Reference": "STRING", "SortOrder": "INT"},
        ("ItemKey",),
    ),
    (
        # dim_, not qc_seed_: this is a conformed dimension the report slices by, the same
        # role dim_Status already plays. The other four are reference lists that only the
        # QC subject area reads.
        "qc_status_vocab.csv", "dim_QcStatus",
        {"Domain": "STRING", "Code": "STRING", "Label": "STRING", "SortOrder": "INT",
         "IsTerminal": "BOOLEAN", "UsedBy": "STRING"},
        ("Domain", "Code"),
    ),
)

# Two workbook dropdowns were extracted into one domain each, so the same code appears
# twice: STATUTORYINSPECTIONS_5 has N_A twice and SUBMITTALSMOCKUPS_6 has APPROVED twice.
# A SharePoint choice column cannot offer the same value twice and a dimension cannot have
# a duplicate key, so the first occurrence wins and the count drops 143 -> 141.
#
# ponytail: de-duplicated here rather than in the extractor, because the seed CSVs are
# INPUT and not ours to edit. Upgrade path: have extract_pqp_workbook.py name a domain
# after the COLUMN it came from rather than after its code count, and the two merged
# dropdowns separate on their own.
EXPECTED_ROWS = {
    "qc_seed_Trade": 26, "qc_seed_ChecklistItem": 625, "qc_seed_Gate": 93,
    "qc_seed_DohItem": 101, "dim_QcStatus": 141,
}


def rows(csv_name: str, key: tuple[str, ...]) -> list[dict[str, str]]:
    """Every row of a seed CSV, first-wins de-duplicated on its natural key."""
    with (SEED_DIR / csv_name).open(encoding="utf-8-sig", newline="") as fh:
        out, seen = [], set()
        for row in csv.DictReader(fh):
            ident = tuple(row[c] for c in key)
            if ident in seen:
                continue
            seen.add(ident)
            out.append(row)
    return out


# The workbook writes an EM DASH for "none" - in Prerequisite, and in LinkedTcoGate on the
# three statutory steps that gate nothing. Carrying it as a literal value makes every join
# over those columns dangle against a one-character string, which reads as a broken
# reference rather than as the absence it is. Empty and em dash both become NULL.
NULL_TOKENS = {"", "—"}


def literal(value: str) -> str:
    value = (value or "").strip()
    if value in NULL_TOKENS:
        return "NULL"
    return "'" + value.replace("'", "''") + "'"


def table_sql(csv_name: str, table: str, columns: dict[str, str],
              key: tuple[str, ...]) -> str:
    data = rows(csv_name, key)
    names = list(columns)
    select = ",\n       ".join(
        f"CAST(c{i} AS {sql_type}) AS {col}"
        for i, (col, sql_type) in enumerate(columns.items(), start=1)
    )
    values = ",\n    ".join(
        "(" + ", ".join(literal(row[c]) for c in names) + ")" for row in data
    )
    aliases = ", ".join(f"c{i}" for i in range(1, len(names) + 1))
    return (
        f"-- {table}: {len(data)} row(s) from seed/{csv_name}\n"
        f"CREATE OR REPLACE TABLE {table} AS\n"
        f"SELECT {select}\n"
        f"FROM (VALUES\n    {values}\n) AS t({aliases});\n"
    )


def build() -> str:
    parts = [
        "-- gold: the PQP (Project Quality Plan) reference seeds.",
        "--",
        "-- GENERATED by _local/make_qc_seeds.py from 02-transformation/seed/*.csv, which were",
        "-- extracted from the client's 44-sheet QA/QC workbook. Do not edit by hand - edit the",
        "-- CSV (or the extractor) and re-run. test_qc.py runs --check, so a stale file fails the",
        "-- suite rather than drifting quietly.",
        "--",
        "-- TWO STRUCTURAL COLLAPSES, both visible in the table list below:",
        "--",
        "--   1. The workbook has 26 trade checklist sheets with an IDENTICAL schema. They are",
        "--      ONE table, qc_seed_ChecklistItem, discriminated by TradeKey - 625 items across",
        "--      26 trades. Twenty-six near-identical tables would need twenty-six near-identical",
        "--      measures, and adding trade 27 would be a schema change instead of a row.",
        "--",
        "--   2. Path to TCO (46), Path to Fire Alarm (23) and Statutory Inspections (24) are the",
        "--      same shape - a numbered step with an authority, a prerequisite and a piece of",
        "--      evidence. They are ONE table, qc_seed_Gate, discriminated by GateType.",
        "--      LinkedTcoGate carries the fire-alarm/statutory step back to the TCO step it",
        "--      gates, which is the relationship the three separate sheets could only express",
        "--      by being read side by side.",
        "--",
        "-- These are TEMPLATES, not results. Nothing here is project-specific: a project's",
        "-- answers live in man_QcChecklistResult / man_QcGate / man_QcDohResult, which carry",
        "-- ProjectKey and join back to these on the item or gate key.",
        "",
    ]
    for csv_name, table, columns, key in SEEDS:
        parts.append(table_sql(csv_name, table, columns, key))
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="fail if the committed .sql is out of date")
    args = parser.parse_args()

    generated = build()
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != generated:
            print(f"STALE: {OUT.name} does not match seed/*.csv - re-run without --check")
            return 1
        print(f"{OUT.name} is up to date")
        return 0

    OUT.write_text(generated, encoding="utf-8")
    print(f"wrote {OUT.relative_to(CHARLEY_DEV)}")
    for csv_name, table, _, key in SEEDS:
        n = len(rows(csv_name, key))
        flag = "" if n == EXPECTED_ROWS[table] else f"   <-- EXPECTED {EXPECTED_ROWS[table]}"
        print(f"  {table:<24} {n:>4} rows{flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
