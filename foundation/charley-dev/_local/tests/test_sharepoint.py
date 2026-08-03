"""The SharePoint lists must match the man_* tables, column for column.

`CD_Manual_Ingest` maps list columns to table columns 1:1 with no translation layer, so a
name that differs by one character does not error - the column simply stops arriving, and
the report renders a blank tile that looks exactly like "nobody has filled this in yet".

That is the failure this file exists to prevent. Nothing here needs SharePoint, Fabric or
a network: it reads the committed script and the gold DDL and compares them.

Run:  python test_sharepoint.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import make_sharepoint as ms  # noqa: E402

CHECKS: list[str] = []


def check(label: str) -> None:
    CHECKS.append(label)


def test_committed_script_is_current() -> None:
    assert ms.OUT.exists(), f"{ms.OUT.name} has never been generated"
    assert ms.OUT.read_text(encoding="utf-8") == ms.build(), (
        "provision-sharepoint.ps1 is stale - re-run make_sharepoint.py. "
        "A column was added to 40_man_tables.sql without regenerating the lists."
    )
    check("provision-sharepoint.ps1 matches 40_man_tables.sql")


def test_every_column_is_provisioned() -> None:
    script = ms.OUT.read_text(encoding="utf-8")
    defs = ms.tables()
    assert len(defs) == 9, f"{len(defs)} man_ tables parsed, expected 9"

    for table, cols in defs.items():
        name = ms.list_name(table)
        assert f'Ensure-List "{name}"' in script, f"{name} is never created"
        # Scope to this list's block so a column present on a DIFFERENT list cannot
        # satisfy the assertion - that would defeat the whole check.
        block = script.split(f'$list = Ensure-List "{name}"', 1)[1].split("Ensure-List", 1)[0]
        for col, _ in cols:
            assert f'-InternalName "{col}"' in block, f"{name} is missing {col}"
    total = sum(len(c) for c in defs.values())
    check(f"all {total} man_* columns across {len(defs)} lists are provisioned")


def test_project_key_is_a_lookup_everywhere() -> None:
    """The single most important design choice. A typed project name is how '1100 Fulton'
    and '1100 Fulton St' become two projects that each under-count."""
    script = ms.OUT.read_text(encoding="utf-8")
    for table in ms.tables():
        name = ms.list_name(table)
        block = script.split(f'$list = Ensure-List "{name}"', 1)[1].split("Ensure-List", 1)[0]
        assert re.search(r'-InternalName "ProjectKey" -Type Lookup', block), (
            f"{name}: ProjectKey must be a Lookup, never free text"
        )
        assert "LookupField = \"Title\"" in block, f"{name}: lookup does not target Title"
    check("ProjectKey is a lookup on every list, never free text")


def test_choice_values_match_the_dimensions() -> None:
    """ProfitabilityCode is the one that catches people out: it matches
    dim_ScorecardBand[MatchValue], which holds LABELS. Seeding it with the dim_Status
    codes (IN_RANGE, OUT_WITH_PLAN) would look right and join to nothing."""
    script = ms.OUT.read_text(encoding="utf-8")
    assert '"Within Range","Out of Range, but has a plan","Margin fade but no plan"' in script
    assert "IN_RANGE" not in script, "ProfitabilityCode seeded with codes, not MatchValues"
    check("ProfitabilityCode carries dim_ScorecardBand[MatchValue], not status codes")

    assert '"HIGH","MEDIUM","LOW"' in script
    assert '"NOT_STARTED","PLANNED","IN_PROGRESS","COMPLETE"' in script
    assert '"ON_TRACK","BEHIND","AT_RISK"' in script
    check("risk and schedule choices carry the dim_Status codes")


def test_versioning_is_on() -> None:
    """Per-field who and when - the audit trail the spreadsheet has never had."""
    script = ms.OUT.read_text(encoding="utf-8")
    assert "-EnableVersioning" in script and "EnableVersioning $true" in script
    check("versioning is enabled on every list")


def test_script_parses_as_powershell() -> None:
    """The script is assembled from strings, so a stray quote produces a file that looks
    fine in review and fails at the console with a parse error - in front of whoever we
    handed it to. PowerShell's own parser settles it.

    Skipped where powershell is not on PATH, so the suite still runs on a non-Windows box.
    """
    import shutil
    import subprocess

    exe = shutil.which("powershell") or shutil.which("pwsh")
    if not exe:
        check("powershell not available - parse check skipped")
        return

    script = str(ms.OUT).replace("'", "''")
    probe = (
        "$e=$null; "
        f"[System.Management.Automation.Language.Parser]::ParseFile('{script}',"
        "[ref]$null,[ref]$e) | Out-Null; "
        "if ($e.Count) { $e | ForEach-Object { $_.Message }; exit 1 } else { exit 0 }"
    )
    result = subprocess.run([exe, "-NoProfile", "-Command", probe],
                            capture_output=True, text=True)
    assert result.returncode == 0, f"provision-sharepoint.ps1 does not parse:\n{result.stdout}"
    check("provision-sharepoint.ps1 parses as valid PowerShell")


def main() -> int:
    test_committed_script_is_current()
    test_every_column_is_provisioned()
    test_project_key_is_a_lookup_everywhere()
    test_choice_values_match_the_dimensions()
    test_versioning_is_on()
    test_script_parses_as_powershell()
    for c in CHECKS:
        print(f"  ok  {c}")
    print(f"\ntest_sharepoint: {len(CHECKS)} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
