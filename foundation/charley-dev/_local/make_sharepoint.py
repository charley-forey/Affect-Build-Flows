"""Generate everything that has to agree about the manual-input lists.

    python make_sharepoint.py            # write the PS1, the dataflow and its metadata
    python make_sharepoint.py --check    # fail if any committed artefact is stale

ONE SOURCE, THREE ARTEFACTS, AND A FOURTH CONSUMER.

The `man_*` DDL in sql/gold/40_man_tables.sql and 41_man_qc_tables.sql is the single source
of truth. From it this generates:

    01-ingestion/Manual/provision-sharepoint.ps1                 the lists and columns
    01-ingestion/Manual/CD_Manual_Ingest.Dataflow/mashup.pq      SharePoint -> bronze
    01-ingestion/Manual/CD_Manual_Ingest.Dataflow/queryMetadata.json

and `_local/deploy_manual.py` imports `tables()` and `bronze_table()` from here for the CSV
loader, so the fourth writer agrees too.

WHY, SPECIFICALLY. The PS1 used to create lists called "CD PriorityItems" while the
dataflow read "CD Priority Items", and deploy_manual.py kept its own hand-written column
lists that had drifted from gold on four tables. None of that errors: SharePoint returns no
row for a list that does not exist under that name, a column that does not match simply
stops arriving, and the report renders a blank tile indistinguishable from "nobody has
filled this in yet". Three files that must agree and no mechanism forcing them to is not a
convention, it is a scheduled outage.

What this does NOT do is create the lists -- it has no credentials and they live in
Affect's tenant. The PS1 is handed to whoever has SharePoint admin, who runs it once.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHARLEY_DEV = HERE.parent
# Both manual DDL files. 40_ is the monthly report's ~40%; 41_ is the PQP subject area.
MAN_SQL = (
    CHARLEY_DEV / "02-transformation" / "sql" / "gold" / "40_man_tables.sql",
    CHARLEY_DEV / "02-transformation" / "sql" / "gold" / "41_man_qc_tables.sql",
)
SEED_DIR = CHARLEY_DEV / "02-transformation" / "seed"
MANUAL_DIR = CHARLEY_DEV / "01-ingestion" / "Manual"
OUT = MANUAL_DIR / "provision-sharepoint.ps1"
OUT_PQ = MANUAL_DIR / "CD_Manual_Ingest.Dataflow" / "mashup.pq"
OUT_META = MANUAL_DIR / "CD_Manual_Ingest.Dataflow" / "queryMetadata.json"

SITE_TITLE = "Affect Project Reporting"
LOOKUP_LIST = "CD Projects"
SITE_URL = "https://REPLACE-ME.sharepoint.com/sites/AffectProjectReporting"

# Choice columns, with the values read out of dim_Status / dim_ScorecardBand on
# 2026-08-02. A choice column is what stops somebody typing "🔴 High" where HIGH is
# expected -- the same reason ProjectKey is a lookup rather than free text.
#
# ProfitabilityCode is the exception worth noticing: it matches dim_ScorecardBand
# [MatchValue] for category 2, and those are the LABELS, not the codes. Seeding it with
# IN_RANGE / OUT_WITH_PLAN would look right and match nothing.
CHOICES = {
    "ImpactCode": ["HIGH", "MEDIUM", "LOW"],
    "StatusCode": {
        "man_Risks": ["NOT_STARTED", "PLANNED", "IN_PROGRESS", "COMPLETE"],
        "man_PriorityItems": ["ON_TRACK", "BEHIND", "AT_RISK"],
    },
    "ProfitabilityCode": [
        "Within Range",
        "Out of Range, but has a plan",
        "Margin fade but no plan",
    ],
}

# The PQP choice columns, read out of seed/qc_status_vocab.csv rather than retyped. That
# CSV is the workbook's own dropdown vocabulary and it also builds dim_QcStatus
# (08_qc_seeds.sql), so what somebody can PICK and what the model can RESOLVE come from one
# file by construction. Retyping 143 codes into a PowerShell script is how you get a status
# that no measure matches and no error anywhere.
#
# (table, column) -> the vocab domain(s) that column draws from.
VOCAB_COLUMNS: dict[tuple[str, str], tuple[str, ...]] = {
    ("man_QcDfow", "StatusCode"): ("DFOWRISKREGISTER_4",),
    ("man_QcItp", "ResultCode"): ("ITP_4",),
    ("man_QcItp", "StatusCode"): ("ITP_6",),
    # THE COST OF THE GATE COLLAPSE, stated rather than hidden: one result table for three
    # paths means one choice column, so it offers the union of the three paths' vocabularies
    # (12 distinct codes rather than 6/7/5). The alternative is three lists that differ only
    # in a dropdown, which is what the workbook had and what the collapse removed.
    ("man_QcGate", "StatusCode"): ("PATHTOTCO_6", "PATHTOFIREALARM_7",
                                   "STATUTORYINSPECTIONS_5"),
    ("man_QcSpecialInspection", "RequiredCode"): ("SPECIALINSPECTIONS_3",),
    ("man_QcSpecialInspection", "PerformedCode"): ("SPECIALINSPECTIONS_2",),
    ("man_QcSpecialInspection", "StatusCode"): ("SPECIALINSPECTIONS_5",),
    ("man_QcCommissioning", "StatusCode"): ("COMMISSIONING_6",),
    ("man_QcInspectorSignIn", "AgencyCode"): ("INSPECTORSIGNIN_11",),
    ("man_QcInspectorSignIn", "OutcomeCode"): ("INSPECTORSIGNIN_5",),
    # The four-stage inspection cycle and the pass/fail result are held on the Excavation
    # sheet, but they are the SAME two dropdowns on all 26 trade sheets - which is the
    # evidence for the checklist collapse, not an artefact of it.
    ("man_QcChecklistResult", "StageCode"): ("EXCAVATION_4",),
    ("man_QcChecklistResult", "ResultCode"): ("EXCAVATION_3",),
    ("man_QcDohResult", "ResponsibilityCode"): ("DOHCHECKLIST_4",),
    ("man_QcDohResult", "StatusCode"): ("DOHCHECKLIST_6",),
}

# Columns whose choices come from a seed CSV's own key column rather than the status
# vocabulary. TradeKey has to match qc_seed_Trade exactly or the result joins to nothing.
SEED_COLUMNS: dict[str, tuple[str, str]] = {
    "TradeKey": ("qc_trades.csv", "TradeKey"),
    "GateType": ("qc_gate_template.csv", "GateType"),
}

# Columns that hold prose. SharePoint's single-line text truncates at 255 characters
# without saying so, and a mitigation plan is exactly the kind of field that runs long.
MULTILINE = {
    "Description", "Mitigation", "CriticalDelays", "RecoveryPlan", "ForecastImpact",
    "Notes", "QuestionText", "BaselineRevision", "ScheduleItem",
    # PQP prose. AcceptanceCriteria and ControlMeasure are the two that run longest -
    # a truncated acceptance criterion is an inspection nobody can repeat.
    "DfowDescription", "ControlMeasure", "AcceptanceCriteria", "Activity", "BlockerNote",
    "AreaInspected", "Purpose", "EvidenceLink",
}


def _csv_rows(name: str) -> list[dict[str, str]]:
    with (SEED_DIR / name).open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _distinct(rows: list[dict[str, str]], column: str) -> list[str]:
    """Distinct values in first-seen order - the workbook's own SortOrder, not alphabetical."""
    out: list[str] = []
    for row in rows:
        value = (row[column] or "").strip()
        if value and value not in out:
            out.append(value)
    return out


def vocab_choices(table: str, column: str) -> list[str] | None:
    """Choice values for a PQP column, or None if it is not one."""
    domains = VOCAB_COLUMNS.get((table, column))
    if domains:
        rows = [r for r in _csv_rows("qc_status_vocab.csv") if r["Domain"] in domains]
        return _distinct(rows, "Code")
    seed = SEED_COLUMNS.get(column)
    if seed and table.startswith("man_Qc"):
        return _distinct(_csv_rows(seed[0]), seed[1])
    return None

SQL_TO_PNP = {
    "STRING": "Text",
    "INT": "Number",
    "DOUBLE": "Number",
    "BOOLEAN": "Boolean",
    "DATE": "DateTime",
}


def tables() -> dict[str, list[tuple[str, str]]]:
    """man_* table name -> [(column, sql type)], parsed from the gold DDL."""
    out: dict[str, list[tuple[str, str]]] = {}
    for path in MAN_SQL:
        sql = path.read_text(encoding="utf-8")
        # Strip line comments first so a `-- STRING` in prose cannot look like a column.
        sql = "\n".join(line.split("--", 1)[0] for line in sql.splitlines())
        for name, body in re.findall(
            r"CREATE OR REPLACE TABLE\s+(man_\w+)\s*\((.*?)\)\s*;", sql, re.S | re.I
        ):
            cols = []
            for line in body.split(","):
                parts = line.split()
                if len(parts) >= 2 and parts[1].upper() in SQL_TO_PNP:
                    cols.append((parts[0], parts[1].upper()))
            out[name] = cols
    return out


# Initialisms the PascalCase splitter must not break apart. Without these you get lists
# called "CD Qc Doh Result", which is what a machine writes and not what anyone would type.
ACRONYMS = {"Qc": "QC", "Itp": "ITP", "Doh": "DOH", "Dfow": "DFOW"}


def list_name(table: str) -> str:
    """man_PriorityItems -> 'CD Priority Items', man_QcDohResult -> 'CD QC DOH Result'.

    The CD prefix marks the lists the report depends on, so nobody deletes one during a
    tidy-up. The SPACES matter: this function is now the only thing that decides a list's
    name, and the PS1, the dataflow and the CSV loader all read it. Before, the PS1 spelled
    it "CD PriorityItems" and the dataflow read "CD Priority Items" - a latent break that
    would have surfaced as an empty list the day somebody bound the dataflow.
    """
    words = re.findall(r"[A-Z][a-z0-9]*|[A-Z]+(?![a-z])", table[len("man_"):])
    return "CD " + " ".join(ACRONYMS.get(w, w) for w in words)


def bronze_table(table: str) -> str:
    """man_QcSpecialInspection -> 'cd_bronze_man_qc_special_inspection'.

    The destination both writers land in - the dataflow query name and the CSV loader's
    table name - and therefore what 30/31_*_silver.sql read.
    """
    words = re.findall(r"[A-Z][a-z0-9]*|[A-Z]+(?![a-z])", table[len("man_"):])
    return "cd_bronze_man_" + "_".join(w.lower() for w in words)


def csv_name(table: str) -> str:
    """man_QcGate -> 'qc_gate'. The CSV template's filename, and the loader's key."""
    return bronze_table(table)[len("cd_bronze_man_"):]


def field_xml(table: str, col: str, sql_type: str) -> str:
    if col == "ProjectKey":
        return (
            f'    Add-PnPField -List $list -DisplayName "ProjectKey" -InternalName "ProjectKey" '
            f'-Type Lookup -AddToDefaultView -ErrorAction Stop | Out-Null\n'
            f'    Set-PnPField -List $list -Identity "ProjectKey" -Values @{{ '
            f'LookupList = $projectsList.Id.ToString(); LookupField = "Title"; Required = $true }}\n'
        )

    values = vocab_choices(table, col)
    if values is None and col in CHOICES:
        spec = CHOICES[col]
        values = spec[table] if isinstance(spec, dict) else spec
    if values:
        joined = ",".join(f'"{v}"' for v in values)
        return (
            f'    Add-PnPField -List $list -DisplayName "{col}" -InternalName "{col}" '
            f'-Type Choice -Choices {joined} -AddToDefaultView | Out-Null\n'
        )

    pnp = SQL_TO_PNP[sql_type]
    extra = ""
    if col == "MonthStart":
        # Always the 1st. The pipeline floors it anyway, but a correction nobody sees is
        # worse than a default that makes the mistake unlikely in the first place.
        extra = (
            f'\n    Set-PnPField -List $list -Identity "MonthStart" -Values @{{ '
            f'Required = $true; Description = "Always the FIRST of the reporting month, '
            f'e.g. 2026-08-01." }}'
        )
    if col in MULTILINE:
        pnp = "Note"
    return (
        f'    Add-PnPField -List $list -DisplayName "{col}" -InternalName "{col}" '
        f'-Type {pnp} -AddToDefaultView | Out-Null{extra}\n'
    )


def build() -> str:
    defs = tables()
    lines = [
        "# Provision the manual-input lists for the Monthly Progress Report.",
        "#",
        "# GENERATED by _local/make_sharepoint.py from sql/gold/40_man_tables.sql.",
        "# Do not edit by hand - the column names must stay identical to the man_* tables,",
        "# and CD_Manual_Ingest maps them 1:1 with no translation layer.",
        "#",
        "# ---------------------------------------------------------------------------",
        "# HOW TO RUN THIS  (about five minutes, once)",
        "#",
        "# 0. The SITE must already exist. Create it in SharePoint first if it does not:",
        "#    SharePoint -> Create site -> Team site -> name it 'Affect Project Reporting'.",
        "#    Note its URL; that is the -Url below.",
        "#",
        "# 1. Install the module:",
        "#",
        "#        Install-Module PnP.PowerShell -Scope CurrentUser -Force",
        "#",
        "# 2. Register an Entra app for sign-in. PnP.PowerShell 2.x REMOVED the built-in",
        "#    multi-tenant app, so `Connect-PnPOnline -Interactive` on its own now fails",
        "#    with 'ClientId is required'. This is the step people get stuck on. Run it",
        "#    ONCE per tenant - it prints a ClientId, keep that:",
        "#",
        "#        Register-PnPEntraIDAppForInteractiveLogin -ApplicationName 'PnP Rocks' "
        "-Tenant <tenant>.onmicrosoft.com -Interactive",
        "#",
        "#    It asks a tenant admin to consent. If you are not one, someone who is has to",
        "#    approve it - that is the only admin step in this whole file.",
        "#",
        "# 3. Connect and run. Run it from THIS folder, so it finds cd-projects.csv:",
        "#",
        "#        Connect-PnPOnline -Url https://<tenant>.sharepoint.com/sites/<site> "
        "-Interactive -ClientId <the id from step 2>",
        "#        ./provision-sharepoint.ps1",
        "#",
        "#    (Commands are on one line each on purpose - a copied backslash is not a",
        "#    PowerShell line continuation and fails with a confusing parse error.)",
        "#",
        "# 4. Nothing. CD Projects populates itself from cd-projects.csv, and the nine",
        "#    lists are ready to type into. Point CD_Manual_Ingest at the site when you",
        "#    want the rows flowing through to the report.",
        "# ---------------------------------------------------------------------------",
        "#",
        "# Idempotent: an existing list is left alone and its missing columns are added, so",
        "# re-running after a schema change is safe and is the intended way to apply one.",
        "",
        "$ErrorActionPreference = 'Stop'",
        "",
        "if (-not (Get-PnPContext)) { throw 'Connect-PnPOnline first.' }",
        "",
        "function Ensure-List($title) {",
        "    $existing = Get-PnPList -Identity $title -ErrorAction SilentlyContinue",
        "    if ($null -eq $existing) {",
        "        Write-Host \"creating $title\"",
        "        $existing = New-PnPList -Title $title -Template GenericList -EnableVersioning",
        "    } else {",
        "        Write-Host \"$title exists - adding any missing columns\"",
        "    }",
        "    # Versioning is what gives every field change a who and a when. The spreadsheet",
        "    # has never had that: a risk rating can change today with no record that it did.",
        "    Set-PnPList -Identity $title -EnableVersioning $true -MajorVersions 500",
        "    return $existing",
        "}",
        "",
        "# ---------------------------------------------------------------- lookup source",
        "# Built FIRST because every other list points at it. A free-text project name is",
        "# how '1100 Fulton' and '1100 Fulton St' become two projects in a report that then",
        "# under-counts both. A lookup column cannot be misspelled.",
        f'$projectsList = Ensure-List "{LOOKUP_LIST}"',
        f'Add-PnPField -List "{LOOKUP_LIST}" -DisplayName "ProjectName" -InternalName "ProjectName" '
        "-Type Text -AddToDefaultView -ErrorAction SilentlyContinue | Out-Null",
        f'Add-PnPField -List "{LOOKUP_LIST}" -DisplayName "IsActive" -InternalName "IsActive" '
        "-Type Boolean -AddToDefaultView -ErrorAction SilentlyContinue | Out-Null",
        "",
        "# Title holds the Procore project id, e.g. 562949955001573.",
        "#",
        "# Populated from cd-projects.csv sitting next to this script, exported from",
        "# dim_Project. Typing 19 project ids by hand is 19 chances to transpose a digit,",
        "# and a wrong id here does not error - it creates a lookup entry that no fact row",
        "# ever joins to, so the project silently reports zeros.",
        "$csv = Join-Path $PSScriptRoot 'cd-projects.csv'",
        "if (Test-Path $csv) {",
        "    $existing = (Get-PnPListItem -List \"" + LOOKUP_LIST + "\" -PageSize 500).FieldValues.Title",
        "    foreach ($row in Import-Csv $csv) {",
        "        if ($existing -contains $row.ProjectKey) { continue }",
        "        Add-PnPListItem -List \"" + LOOKUP_LIST + "\" -Values @{",
        "            Title = $row.ProjectKey; ProjectName = $row.ProjectName",
        "            IsActive = ($row.IsActive -eq 'TRUE')",
        "        } | Out-Null",
        "        Write-Host \"  + $($row.ProjectName)\"",
        "    }",
        "} else {",
        "    Write-Host \"cd-projects.csv not found - populate CD Projects by hand\"",
        "}",
        "",
    ]

    for table, cols in defs.items():
        name = list_name(table)
        lines += [
            "# " + "-" * 74,
            f"# {name}  ->  {table}",
            f'$list = Ensure-List "{name}"',
            "try {",
        ]
        for col, sql_type in cols:
            lines.append(field_xml(table, col, sql_type).rstrip("\n"))
        lines += [
            "} catch [System.Management.Automation.RuntimeException] {",
            "    # Add-PnPField throws if the column already exists. That is the idempotent",
            "    # path, not a failure - anything else rethrows.",
            "    if ($_.Exception.Message -notmatch 'already exists') { throw }",
            "}",
            "",
        ]

    lines += [
        "Write-Host ''",
        f"Write-Host 'Done. {len(defs)} lists plus {LOOKUP_LIST}.'",
        "Write-Host 'Next: populate CD Projects from dim_Project, then point'",
        "Write-Host 'CD_Manual_Ingest at this site and run it.'",
        "",
    ]
    return "\n".join(lines)


def query_names() -> list[str]:
    """Every bronze table the dataflow writes: the projects lookup, then one per man_*."""
    return ["cd_bronze_man_projects"] + [bronze_table(t) for t in tables()]


def build_mashup() -> str:
    """The Power Query that lands the SharePoint lists into CD_Bronze_Lakehouse.

    GENERATED for one reason: the list TITLES it navigates to have to be the titles the PS1
    creates, and hand-maintaining that across two files is what produced "CD PriorityItems"
    in one and "CD Priority Items" in the other.
    """
    header = f'''[DefaultOutputDestinationSettings = [DestinationDefinition = [Kind = "Reference", QueryName = "DefaultDestination", IsNewTarget = true], UpdateMethod = [Kind = "Replace"], DestinationTypeSettings = [Kind = "Table"]], StagingDefinition = [Kind = "FastCopy"]]
section Section1;

// ============================================================================
// CD_Manual_Ingest - SharePoint lists -> CD_Bronze_Lakehouse
//
// GENERATED by _local/make_sharepoint.py from sql/gold/40_man_tables.sql and
// 41_man_qc_tables.sql. Do not edit by hand: the list titles here must match the ones
// provision-sharepoint.ps1 creates exactly, and they used to differ by a space.
//
// The ~40% of the monthly report that exists in no system of record - wins, the risk
// register, priority items, the client survey, contract milestone dates, safety hours -
// plus the PQP subject area: the DFOW register, the ITP, the TCO / fire-alarm / statutory
// gates, special inspections, commissioning, the inspector sign-in log, and the per-project
// answers against the 625-item checklist and the DOH checklist.
//
// SITE URL IS A PLACEHOLDER. The lists live in Affect's tenant and need SharePoint admin
// rights to create - see _docs/sharepoint-lists.md. Replace SITE below with the real URL
// and this dataflow is ready to bind.
//
// LANDED RAW, SHAPED IN SQL. No filtering, renaming or retyping happens here. Power Query
// steps are not diffable in review, not testable offline, and not re-runnable against data
// already pulled; sql/silver/30_manual_silver.sql and 31_qc_manual_silver.sql are all
// three. Same bronze rule the Procore and Sage sides follow - never drop a column at the
// boundary, so a transform bug is a re-run rather than asking people to retype a month of
// work.
//
// Expand=false on lookup columns keeps ProjectKey as the raw lookup record. Silver reads
// the id out of it; expanding here would bake a display name into bronze, and a renamed
// project would then silently orphan its history.
// ============================================================================

SITE = "{SITE_URL}";
'''
    parts = [header]
    # The lookup list first, then one query per man_* table.
    for query, title in [("cd_bronze_man_projects", LOOKUP_LIST)] + [
        (bronze_table(t), list_name(t)) for t in tables()
    ]:
        parts.append(f'''
[BindToDefaultDestination = true]
shared {query} = let
  Source = SharePoint.Tables(SITE, [Implementation = "2.0", ViewMode = "All"]),
  Navigation = Source{{[Title = "{title}"]}}[Items]
in
  Navigation;
''')
    return "".join(parts)


def build_query_metadata() -> str:
    """The dataflow's companion metadata: one entry per query.

    Query ids are uuid5 of the query name rather than random, so regenerating produces a
    byte-identical file and `--check` means something. They are internal to a dataflow that
    has never been bound (SITE is still a placeholder), so making them deterministic costs
    nothing and removes the only reason this file would have to be hand-edited.
    """
    ns = uuid.UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")  # RFC 4122 URL namespace
    entries = ",\n".join(
        f'''    "{q}": {{
      "queryId": "{uuid.uuid5(ns, 'CD_Manual_Ingest/' + q)}",
      "queryName": "{q}",
      "loadEnabled": true
    }}''' for q in query_names()
    )
    return f'''{{
  "formatVersion": "202502",
  "computeEngineSettings": {{
    "allowModernEvaluationEngine": true
  }},
  "name": "CD_Manual_Ingest",
  "queryGroups": [],
  "documentLocale": "en-US",
  "queriesMetadata": {{
{entries}
  }},
  "connections": []
}}
'''


ARTEFACTS = ((OUT, build), (OUT_PQ, build_mashup), (OUT_META, build_query_metadata))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="fail if any committed artefact is out of date")
    args = parser.parse_args()

    if args.check:
        stale = []
        for path, builder in ARTEFACTS:
            current = path.read_text(encoding="utf-8") if path.exists() else ""
            if current != builder():
                stale.append(path.name)
        if stale:
            print(f"STALE: {', '.join(stale)} does not match the man_* DDL - "
                  f"re-run make_sharepoint.py without --check")
            return 1
        print(f"{len(ARTEFACTS)} generated artefact(s) up to date")
        return 0

    defs = tables()
    for path, builder in ARTEFACTS:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(builder(), encoding="utf-8")
        print(f"wrote {path.relative_to(CHARLEY_DEV)}")
    total = sum(len(c) for c in defs.values())
    print(f"  {len(defs)} lists, {total} columns, from "
          f"{', '.join(p.name for p in MAN_SQL)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
