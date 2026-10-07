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
CROSSWALK_OUT = CHARLEY_DEV / "02-transformation" / "sql" / "gold" / "09_seed_projectcrosswalk.sql"

# The Procore <-> Sage project crosswalk. Not a QC seed, but the same mechanism: a reviewed
# CSV inlined as VALUES, built by cd_20_seed_gold, --check'd by test_qc.py. CSV headers are
# snake_case for the people editing it; the gold columns follow gold naming.
CROSSWALK = ("project_crosswalk.csv", "seed_ProjectCrosswalk",
             {"procore_project_id": "STRING", "sage_job_number": "STRING",
              "relationship": "STRING", "source": "STRING"},
             ("procore_project_id", "sage_job_number"))
CROSSWALK_NAMES = ("ProcoreProjectId", "SageJobNumber", "Relationship", "Source")
# Procore projects kept out of every report (test projects). Applied at the sv_* views by
# deploy_gold.source_view_code, so it reaches every gold table at once.
EXCLUSION = ("project_exclusion.csv", "seed_ProjectExclusion",
             {"procore_project_id": "STRING", "project_name": "STRING", "reason": "STRING"},
             ("procore_project_id",))
EXCLUSION_NAMES = ("ProcoreProjectId", "ProjectName", "Reason")

# The client's old Sage -> new cost-code mapping. Same mechanism again; the CSVs are written
# by import_cost_code_map.py from the client's workbook, never edited by hand.
# The map's de-dup key is the whole PAIR, not the old code: an old code mapped to two
# different new codes must survive into gold, where the DQ suite reports it and
# dim_CostCodeCrosswalk refuses to pick one. De-duplicating on the old code here would
# silently pick the first.
COSTCODE_OUT = CHARLEY_DEV / "02-transformation" / "sql" / "gold" / "09_seed_costcode.sql"
COSTCODE_NEW = ("cost_code_new.csv", "seed_CostCodeNew",
                {"new_cost_code": "STRING", "description": "STRING",
                 "division_code": "STRING", "division_name": "STRING"},
                ("new_cost_code",))
COSTCODE_NEW_NAMES = ("NewCostCode", "Description", "DivisionCode", "DivisionName")
COSTCODE_MAP = ("cost_code_map.csv", "seed_CostCodeMap",
                {"old_cost_code": "STRING", "new_cost_code": "STRING",
                 "old_description": "STRING"},
                ("old_cost_code", "new_cost_code"))
COSTCODE_MAP_NAMES = ("OldCostCode", "NewCostCode", "OldDescription")
# Pre-2026 Procore CSI code -> new code (the client's 'Legacy to New' answers). Same pair key.
COSTCODE_LEGACY = ("cost_code_legacy_map.csv", "seed_CostCodeLegacyMap",
                   {"legacy_cost_code": "STRING", "new_cost_code": "STRING",
                    "legacy_description": "STRING"},
                   ("legacy_cost_code", "new_cost_code"))
COSTCODE_LEGACY_NAMES = ("LegacyCostCode", "NewCostCode", "LegacyDescription")

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
        # Procore's trade list and the workbook's controlled keys are different
        # vocabularies. This maps ONLY the unambiguous pairs - "HVAC" is plainly
        # HVAC_DUCTWORK, "Sprinkler" is plainly FIRE_SPRINKLER. Three labels are
        # deliberately absent because they cannot be resolved without Affect:
        # "Drywall/Carpentry" (framing, board or millwork?), "Concrete Superstructure"
        # and "Concrete" (cast-in-place, formwork or slab on deck?). Attaching a defect
        # to the wrong trade is worse than attaching it to none, so they stay unmapped
        # and keep showing up on the DQ page until somebody who knows the breakdown says.
        # A further group - Roofing, Glazing, Windows, Structural Steel, Low Voltage,
        # Demolition, Housekeeping and others - has no equivalent trade in the 26-sheet
        # library at all. That is a finding, not a gap to paper over: Affect's Procore
        # trade list is broader than the SaunaLounge checklist library.
        "qc_trade_alias.csv", "qc_seed_TradeAlias",
        {"ProcoreTrade": "STRING", "TradeKey": "STRING", "Rationale": "STRING"},
        ("ProcoreTrade",),
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
    # Grows as Affect resolves the ambiguous labels. Bump it deliberately when it does -
    # the assertion is here so an alias cannot be added or lost without somebody noticing.
    "qc_seed_TradeAlias": 16,
    # The 15 legacy dim_projects_procoreXsage pairs, plus 25-034 -> job 28 and 26-056 -> job
    # 27 (confirmed 2026-10-05). Bump deliberately when Affect approves one.
    "seed_ProjectCrosswalk": 17,
    # The two Procore test projects numbered 1234.
    "seed_ProjectExclusion": 2,
    # Cost Code Mapping_OldvsNew_v1.xlsx. Bump deliberately when the client sends v2.
    "seed_CostCodeNew": 291, "seed_CostCodeMap": 318,
    # Legacy Procore Codes to New_v1_CE.xlsx. Bump deliberately when the client sends v2.
    "seed_CostCodeLegacyMap": 156,
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
              key: tuple[str, ...], out_names: tuple[str, ...] | None = None) -> str:
    data = rows(csv_name, key)
    names = list(columns)
    select = ",\n       ".join(
        f"CAST(c{i} AS {sql_type}) AS {out}"
        for i, (sql_type, out) in enumerate(zip(columns.values(), out_names or names), start=1)
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


def build_crosswalk() -> str:
    return "\n".join([
        "-- gold: seed_ProjectCrosswalk - the Procore project <-> Sage job mapping.",
        "--",
        "-- GENERATED by _local/make_qc_seeds.py from 02-transformation/seed/project_crosswalk.csv.",
        "-- Do not edit by hand. Sage actrec carries no Procore reference, so this cannot be",
        "-- derived; every row is a human decision. The first 15 are the legacy",
        "-- dim_projects_procoreXsage verbatim. gold dq_CrosswalkCandidate proposes new pairs; a",
        "-- proposal becomes a row here only through a reviewed CSV edit, never automatically.",
        "",
        table_sql(*CROSSWALK, out_names=CROSSWALK_NAMES),
        "-- seed_ProjectExclusion: Procore projects kept out of every report (test projects).",
        "-- deploy_gold.py filters every project-keyed sv_* view through it before gold builds.",
        table_sql(*EXCLUSION, out_names=EXCLUSION_NAMES),
    ])


def build_costcode() -> str:
    return "\n".join([
        "-- gold: seed_CostCodeNew / seed_CostCodeMap / seed_CostCodeLegacyMap - the client's new",
        "-- cost-code list, its old Sage code -> new code mapping, and its pre-2026 Procore code ->",
        "-- new code mapping.",
        "--",
        "-- GENERATED by _local/make_qc_seeds.py from 02-transformation/seed/cost_code_*.csv, which",
        "-- _local/import_cost_code_map.py writes from the client's mapping workbook. Do not edit by",
        "-- hand. A blank NewCostCode is an old code the client has not mapped yet (v1: the two",
        "-- ALLOWANCES codes), kept so it reads as unmapped rather than as unknown.",
        "-- dim_CostCodeCrosswalk reads all three.",
        "",
        table_sql(*COSTCODE_NEW, out_names=COSTCODE_NEW_NAMES),
        table_sql(*COSTCODE_MAP, out_names=COSTCODE_MAP_NAMES),
        table_sql(*COSTCODE_LEGACY, out_names=COSTCODE_LEGACY_NAMES),
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="fail if the committed .sql is out of date")
    args = parser.parse_args()

    outputs = {OUT: build(), CROSSWALK_OUT: build_crosswalk(), COSTCODE_OUT: build_costcode()}
    if args.check:
        stale = [p.name for p, text in outputs.items()
                 if (p.read_text(encoding="utf-8") if p.exists() else "") != text]
        if stale:
            print(f"STALE: {stale} do not match seed/*.csv - re-run without --check")
            return 1
        print(f"{', '.join(p.name for p in outputs)} up to date")
        return 0

    for path, text in outputs.items():
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path.relative_to(CHARLEY_DEV)}")
    for csv_name, table, _, key in (*SEEDS, CROSSWALK, EXCLUSION, COSTCODE_NEW, COSTCODE_MAP, COSTCODE_LEGACY):
        n = len(rows(csv_name, key))
        flag = "" if n == EXPECTED_ROWS[table] else f"   <-- EXPECTED {EXPECTED_ROWS[table]}"
        print(f"  {table:<24} {n:>4} rows{flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
