"""Generate the PnP provisioning script for the manual-input SharePoint lists.

    python make_sharepoint.py            # write 01-ingestion/Manual/provision-sharepoint.ps1
    python make_sharepoint.py --check    # fail if the committed script is stale

The lists are GENERATED from `sql/gold/40_man_tables.sql` rather than written by hand,
because the SharePoint column names and the `man_*` column names have to be identical --
`CD_Manual_Ingest` maps them 1:1 with no translation layer. Hand-maintaining ~60 columns
in two places is how they drift, and the drift is silent: a renamed SharePoint column does
not error, it just stops arriving, and the report shows a blank tile that looks like
"nobody filled this in yet".

So the .sql is the single source of truth for both the table and the list, and
`test_sharepoint.py` asserts the committed script still matches it.

What this script does NOT do is create the lists itself -- it has no credentials and the
lists live in Affect's tenant. It is handed to whoever has SharePoint admin, who runs it
once. That is the only manual step.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHARLEY_DEV = HERE.parent
MAN_SQL = CHARLEY_DEV / "02-transformation" / "sql" / "gold" / "40_man_tables.sql"
OUT = CHARLEY_DEV / "01-ingestion" / "Manual" / "provision-sharepoint.ps1"

SITE_TITLE = "Affect Project Reporting"
LOOKUP_LIST = "CD Projects"

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

# Columns that hold prose. SharePoint's single-line text truncates at 255 characters
# without saying so, and a mitigation plan is exactly the kind of field that runs long.
MULTILINE = {
    "Description", "Mitigation", "CriticalDelays", "RecoveryPlan", "ForecastImpact",
    "Notes", "QuestionText", "BaselineRevision", "ScheduleItem",
}

SQL_TO_PNP = {
    "STRING": "Text",
    "INT": "Number",
    "DOUBLE": "Number",
    "BOOLEAN": "Boolean",
    "DATE": "DateTime",
}


def tables() -> dict[str, list[tuple[str, str]]]:
    """man_* table name -> [(column, sql type)], parsed from the gold DDL."""
    sql = MAN_SQL.read_text(encoding="utf-8")
    # Strip line comments first so a `-- STRING` in prose cannot look like a column.
    sql = "\n".join(line.split("--", 1)[0] for line in sql.splitlines())
    out: dict[str, list[tuple[str, str]]] = {}
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


def list_name(table: str) -> str:
    """man_PriorityItems -> 'CD PriorityItems'. The CD prefix marks the lists the report
    depends on, so nobody deletes one during a tidy-up."""
    return "CD " + table[len("man_"):]


def field_xml(table: str, col: str, sql_type: str) -> str:
    if col == "ProjectKey":
        return (
            f'    Add-PnPField -List $list -DisplayName "ProjectKey" -InternalName "ProjectKey" '
            f'-Type Lookup -AddToDefaultView -ErrorAction Stop | Out-Null\n'
            f'    Set-PnPField -List $list -Identity "ProjectKey" -Values @{{ '
            f'LookupList = $projectsList.Id.ToString(); LookupField = "Title"; Required = $true }}\n'
        )

    if col in CHOICES:
        spec = CHOICES[col]
        values = spec[table] if isinstance(spec, dict) else spec
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="fail if the committed script is out of date")
    args = parser.parse_args()

    generated = build()
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != generated:
            print(f"STALE: {OUT.name} does not match 40_man_tables.sql - re-run without --check")
            return 1
        print(f"{OUT.name} is up to date")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(generated, encoding="utf-8")
    defs = tables()
    total = sum(len(c) for c in defs.values())
    print(f"wrote {OUT.relative_to(CHARLEY_DEV)}")
    print(f"  {len(defs)} lists, {total} columns, from {MAN_SQL.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
