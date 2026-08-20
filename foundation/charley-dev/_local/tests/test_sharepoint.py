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
    for path, builder in ms.ARTEFACTS:
        assert path.exists(), f"{path.name} has never been generated"
        assert path.read_text(encoding="utf-8") == builder(), (
            f"{path.name} is stale - re-run make_sharepoint.py. A column or table was "
            f"added to the man_* DDL without regenerating it."
        )
    check(f"all {len(ms.ARTEFACTS)} generated artefacts match the man_* DDL")


def test_list_names_agree_across_writers() -> None:
    """THE ROOT CAUSE THIS FILE NOW GUARDS.

    The PS1 created "CD PriorityItems" and the dataflow read "CD Priority Items". Neither
    errors: SharePoint returns nothing for a list that does not exist under that name, so
    the dataflow would have landed an empty table and the report a blank tile. Both are
    generated from ms.list_name() now, and this asserts they still are.
    """
    script = ms.OUT.read_text(encoding="utf-8")
    mashup = ms.OUT_PQ.read_text(encoding="utf-8")
    meta = ms.OUT_META.read_text(encoding="utf-8")

    for table in ms.tables():
        name, bronze = ms.list_name(table), ms.bronze_table(table)
        assert f'Ensure-List "{name}"' in script, f"{name} is never created by the PS1"
        assert f'[Title = "{name}"]' in mashup, f"{name} is never read by the dataflow"
        assert f"shared {bronze} =" in mashup, f"{bronze} is not a dataflow query"
        assert f'"queryName": "{bronze}"' in meta, f"{bronze} is missing from the metadata"
    check("every list name is identical in the PS1, the dataflow and its metadata")

    # THE OTHER WAY THIS DATAFLOW SHIPS BROKEN, and it did until 2026-08-19.
    #
    # The header declares its output destination by REFERENCE - QueryName =
    # "DefaultDestination" - and every query carries BindToDefaultDestination = true. If
    # nothing in the file actually defines that query, the mashup still parses, still
    # deploys, and fails at RUN with an unresolved reference. All 18 queries, every time.
    # It went unnoticed because this dataflow has never been deployed; CD_Sage_Ingest,
    # the only one that has, carries the line and a comment saying exactly this.
    assert 'QueryName = "DefaultDestination"' in mashup
    assert "shared DefaultDestination =" in mashup, (
        "mashup.pq binds every query to DefaultDestination but never defines it - "
        "the dataflow will deploy and then fail at run"
    )
    assert "Lakehouse.Contents" in mashup, "DefaultDestination does not point at a lakehouse"
    workspace_id, bronze_id = ms.fabric_ids()
    assert workspace_id in mashup and bronze_id in mashup, (
        "the destination does not match fabric_ids.json - it must land in CD_Bronze"
    )
    check("the dataflow defines the destination it binds every query to")

    # Two sites, and only the Job Register reads the second one. The reporting lists and
    # the BUILD site are different tenanted sites; crossing them wires the register to a
    # site that does not have it and returns nothing, silently.
    assert f'shared {ms.JOB_REGISTER_QUERY} =' in mashup
    assert "SITE_BUILD = " in mashup
    register_block = mashup.split(f"shared {ms.JOB_REGISTER_QUERY} =")[1]
    assert "SharePoint.Tables(SITE_BUILD" in register_block, (
        "the Job Register must read SITE_BUILD, not the reporting site"
    )
    assert f'Ensure-List "{ms.JOB_REGISTER_LIST}"' not in script, (
        "the Job Register is created by power-automate/provision-sharepoint-build.ps1 on "
        "the BUILD site - this script must not create a second one on the reporting site"
    )
    check("the Job Register reads the BUILD site, and is not duplicated onto the other one")

    # The CSV loader is the fourth writer into the same bronze contract.
    import deploy_manual as dm

    assert set(dm.LISTS) == {ms.csv_name(t) for t in ms.tables()}, (
        "deploy_manual.LISTS has drifted from the man_* DDL - it must be derived from it"
    )
    for table, cols in ms.tables().items():
        assert [c for c, _ in cols] == [c for c, _ in dm.LISTS[ms.csv_name(table)]], (
            f"{table}: the CSV loader collects different columns from the gold DDL"
        )
    check("the CSV loader collects exactly the columns the man_* tables declare")


def test_every_column_is_provisioned() -> None:
    script = ms.OUT.read_text(encoding="utf-8")
    defs = ms.tables()
    # 9 monthly-report lists + 8 PQP lists.
    assert len(defs) == 17, f"{len(defs)} man_ tables parsed, expected 17"

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


def test_pqp_choices_come_from_the_seed_vocabulary() -> None:
    """The PQP choice lists are read out of seed/qc_status_vocab.csv, which also builds
    dim_QcStatus. One file, so what a person can PICK and what the model can RESOLVE cannot
    diverge - and nobody retypes 143 codes into a PowerShell script."""
    script = ms.OUT.read_text(encoding="utf-8")

    for (table, column), domains in ms.VOCAB_COLUMNS.items():
        values = ms.vocab_choices(table, column)
        assert values, f"{table}.{column} resolved no codes from {domains}"
        block = script.split(f'$list = Ensure-List "{ms.list_name(table)}"', 1)[1]                       .split("Ensure-List", 1)[0]
        joined = ",".join(f'"{v}"' for v in values)
        assert f'-InternalName "{column}" -Type Choice -Choices {joined}' in block, (
            f"{table}.{column} is not a choice column over {domains}"
        )
    check(f"all {len(ms.VOCAB_COLUMNS)} PQP choice columns come from qc_status_vocab.csv")

    # TradeKey must offer exactly the 26 trades the seed holds, or a result joins to
    # nothing - and a checklist answer that joins to nothing is an answer nobody counts.
    trades = ms.vocab_choices("man_QcChecklistResult", "TradeKey")
    assert len(trades) == 26, f"{len(trades)} trades offered, expected 26"
    assert "EXCAVATION" in trades and "CONCRETE_FORMWORK" in trades
    check("TradeKey offers exactly the 26 seeded trades")

    # The gate collapse's visible cost: one result table for three paths means one choice
    # column offering the union of the three vocabularies.
    gates = ms.vocab_choices("man_QcGate", "StatusCode")
    assert {"SUBMITTED", "FAILED_RE_TEST", "RE_INSPECT"} <= set(gates), gates
    check("the gate list offers all three paths' statuses, which is the collapse's cost")


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
    test_list_names_agree_across_writers()
    test_every_column_is_provisioned()
    test_project_key_is_a_lookup_everywhere()
    test_choice_values_match_the_dimensions()
    test_pqp_choices_come_from_the_seed_vocabulary()
    test_versioning_is_on()
    test_script_parses_as_powershell()
    for c in CHECKS:
        print(f"  ok  {c}")
    print(f"\ntest_sharepoint: {len(CHECKS)} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
