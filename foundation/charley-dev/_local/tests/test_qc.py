"""Assertions over the PQP (Project Quality Plan) subject area.

Same engine and the same rules as test_gold.py: seedrunner builds an in-memory DuckDB from
the REAL production .sql - the seeds, the source-view fixtures and every gold file - so
what is checked here is the SQL that ships, not a re-implementation of it.

What this suite is actually for, in order of how expensive the failure would be:

  1. THE SILVER -> GOLD LINK EXISTS. Every man_* table, old and new, is reachable from its
     sv_* source. That link was absent for the nine original manual tables, so the whole
     manual pipeline ran green and delivered nothing. Eight more tables were about to be
     added on the same path.
  2. THE TWO COLLAPSES HOLD. 625 checklist items across 26 trades in one table; 93 gates
     across three paths in one table, split 46/23/24. If either drifts, the workbook has
     quietly grown a table back.
  3. NOTHING IS ORPHANED. A result whose ProjectKey or TradeKey does not resolve does not
     error - it silently vanishes from every filtered visual.

Run:  python test_qc.py
"""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from seedrunner import CHARLEY_DEV, build  # noqa: E402

SEED_DIR = CHARLEY_DEV / "02-transformation" / "seed"

CHECKS: list[str] = []


def check(label: str) -> None:
    CHECKS.append(label)


def one(con, sql: str):
    row = con.execute(sql).fetchone()
    return row[0] if row else None


def q(con, sql: str):
    return con.execute(sql).fetchall()


# --------------------------------------------------------------------------
# The seeds - the templates every project shares
# --------------------------------------------------------------------------


def test_seed_sql_is_current(con) -> None:
    """08_qc_seeds.sql is generated from the CSVs, so a CSV edited without regenerating
    would leave the pipeline running yesterday's workbook with today's file on disk."""
    result = subprocess.run(
        [sys.executable, str(CHARLEY_DEV / "_local" / "make_qc_seeds.py"), "--check"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    check("08_qc_seeds.sql matches seed/*.csv")


def test_checklist_collapse(con) -> None:
    """26 trade sheets with an identical schema became ONE table plus a TradeKey."""
    assert one(con, "SELECT COUNT(*) FROM qc_seed_ChecklistItem") == 625
    assert one(con, "SELECT COUNT(DISTINCT TradeKey) FROM qc_seed_ChecklistItem") == 26
    assert one(con, "SELECT COUNT(*) FROM qc_seed_Trade") == 26
    check("625 checklist items across 26 trades, in one table")

    # ItemKey is what a project's answer points at. A duplicate would let two answers
    # attach to the same question and both be counted.
    assert one(con, "SELECT COUNT(DISTINCT ItemKey) FROM qc_seed_ChecklistItem") == 625
    check("qc_seed_ChecklistItem[ItemKey] is unique across all 26 trades")

    # Every item belongs to a seeded trade. Without this the collapse would be a table with
    # a free-text discriminator, which is what it replaced.
    orphans = one(con, "SELECT COUNT(*) FROM qc_seed_ChecklistItem i "
                       "LEFT JOIN qc_seed_Trade t ON t.TradeKey = i.TradeKey "
                       "WHERE t.TradeKey IS NULL")
    assert orphans == 0, f"{orphans} checklist item(s) reference an unknown trade"
    check("every checklist item resolves to a seeded trade")

    # RiskTier drives inspection frequency, so an out-of-range value is not cosmetic.
    # 1..4, not 1..3: five trades in the workbook (waterproofing, electrical, plumbing,
    # fire sprinkler, fire alarm) carry tier 4 - the life-safety and water-ingress trades.
    # Taken from the data rather than from an assumption about what the scale "should" be.
    assert one(con, "SELECT COUNT(*) FROM qc_seed_Trade "
                    "WHERE RiskTier IS NULL OR RiskTier NOT BETWEEN 1 AND 4") == 0
    assert one(con, "SELECT COUNT(*) FROM qc_seed_Trade WHERE RiskTier = 4") == 5
    check("every trade carries a risk tier in 1..4, five of them the tier-4 life-safety trades")


def test_gate_collapse(con) -> None:
    """Path to TCO (46) + Path to Fire Alarm (23) + Statutory Inspections (24) = 93."""
    assert one(con, "SELECT COUNT(*) FROM qc_seed_Gate") == 93
    split = dict(q(con, "SELECT GateType, COUNT(*) FROM qc_seed_Gate GROUP BY GateType"))
    assert split == {"TCO": 46, "FIRE_ALARM": 23, "STATUTORY": 24}, split
    check("93 gates in one table, split 46 TCO / 23 fire alarm / 24 statutory")

    assert one(con, "SELECT COUNT(DISTINCT GateKey) FROM qc_seed_Gate") == 93
    check("qc_seed_Gate[GateKey] is unique across all three paths")

    # THE REASON THE COLLAPSE IS WORTH IT. LinkedTcoGate carries a statutory step back to
    # the TCO step it gates - a relationship the three separate sheets could only express by
    # being read side by side, and which nobody could query at all.
    #
    # It holds the TCO Step ('A1'), not the GateKey ('TCO-A1'), so the join is on Step. That
    # is the workbook's own spelling and it is left alone: rewriting the values to look like
    # keys would make the seed disagree with the sheet anyone checks it against.
    assert one(con, "SELECT COUNT(*) FROM qc_seed_Gate "
                    "WHERE LinkedTcoGate IS NOT NULL") == 21
    dangling = one(con, "SELECT COUNT(*) FROM qc_seed_Gate g LEFT JOIN qc_seed_Gate p "
                        "ON p.Step = g.LinkedTcoGate AND p.GateType = 'TCO' "
                        "WHERE g.LinkedTcoGate IS NOT NULL AND p.Step IS NULL")
    assert dangling == 0, f"{dangling} gate(s) link to a TCO step that does not exist"
    check("all 21 cross-path links resolve to a real TCO step")

    # The workbook writes an EM DASH for "none". Three statutory steps gate nothing and 29
    # gates have no prerequisite; both must be NULL, or every join over those columns
    # dangles against a one-character string and reads as a broken reference.
    assert one(con, "SELECT COUNT(*) FROM qc_seed_Gate "
                    "WHERE LinkedTcoGate = chr(8212) OR Prerequisite = chr(8212)") == 0
    assert one(con, "SELECT COUNT(*) FROM qc_seed_Gate WHERE Prerequisite IS NULL") == 29
    check("the workbook's em-dash placeholder becomes NULL, not a value")


def test_doh_and_status_seeds(con) -> None:
    assert one(con, "SELECT COUNT(*) FROM qc_seed_DohItem") == 101
    assert one(con, "SELECT COUNT(DISTINCT ItemKey) FROM qc_seed_DohItem") == 101
    check("101 DOH checklist items, uniquely keyed")

    # 143 rows in the CSV, 141 here. Two workbook dropdowns were extracted into one domain
    # each, so STATUTORYINSPECTIONS_5 carried N_A twice and SUBMITTALSMOCKUPS_6 carried
    # APPROVED twice. A choice column cannot offer the same value twice and a dimension
    # cannot have a duplicate key, so the first occurrence wins - counted here rather than
    # left as an unexplained discrepancy between the CSV and the table.
    raw = len(list(csv.DictReader(
        (SEED_DIR / "qc_status_vocab.csv").open(encoding="utf-8-sig"))))
    assert raw == 143, raw
    assert one(con, "SELECT COUNT(*) FROM dim_QcStatus") == 141
    assert one(con, "SELECT COUNT(*) FROM ("
                    "  SELECT Domain, Code FROM dim_QcStatus GROUP BY Domain, Code"
                    "  HAVING COUNT(*) > 1)") == 0
    check("dim_QcStatus de-duplicates 143 extracted rows to 141 unique (Domain, Code)")


# --------------------------------------------------------------------------
# THE FIX: man_* is reachable from silver
# --------------------------------------------------------------------------

MANUAL_TABLES = (
    "man_Wins", "man_Risks", "man_PriorityItems", "man_Flags", "man_Survey",
    "man_SafetyMonthly", "man_QualityMonthly", "man_Milestones", "man_DailyLogCompliance",
    "man_QcDfow", "man_QcItp", "man_QcGate", "man_QcSpecialInspection",
    "man_QcCommissioning", "man_QcInspectorSignIn", "man_QcChecklistResult",
    "man_QcDohResult",
)


def test_manual_tables_are_reachable(con) -> None:
    """Every man_* table has rows in it, from an sv_man_* source.

    This is the assertion that would have failed before any of this work: all nine original
    tables were declared and never populated, so the model bound to seventeen empty tables
    and the scorecard's manual categories scored BLANK forever. An empty man_* table is a
    legitimate STATE (nobody has typed anything yet) but it must not be the only state
    reachable, and that is what a fixture row proves.
    """
    empty = [t for t in MANUAL_TABLES if one(con, f"SELECT COUNT(*) FROM {t}") == 0]
    assert not empty, f"no silver -> gold link reaches: {empty}"
    check(f"all {len(MANUAL_TABLES)} man_* tables are populated from silver")

    # The four columns that had drifted. Each of these was unfillable before, because the
    # silver parser produced a different column and gold had nowhere to read from.
    assert one(con, "SELECT LogsMissedSameDay FROM man_DailyLogCompliance") == 3
    assert one(con, "SELECT SurveyedParty FROM man_Survey") == "ANONYMOUS"
    assert one(con, "SELECT ResourcesUpdated FROM man_Flags") is False
    assert one(con, "SELECT ActivityKey FROM man_Milestones") == "A1"
    check("the four drifted columns now arrive in gold with values")

    # The case flip at the silver -> gold boundary is the platform's own convention, and it
    # is load-bearing: the DAX reads man_Flags[ProfitabilityCode] by name.
    cols = [r[0] for r in q(con, "SELECT column_name FROM information_schema.columns "
                                 "WHERE table_name = 'man_QcGate'")]
    assert "ProjectKey" in cols and "project_id" not in cols
    check("gold man_Qc* columns are PascalCase, as the semantic model reads them")


def test_every_pqp_table_carries_a_project(con) -> None:
    """Every man_Qc* row is attributable to a project, and to a project that EXISTS."""
    for table in MANUAL_TABLES:
        nulls = one(con, f"SELECT COUNT(*) FROM {table} WHERE ProjectKey IS NULL")
        assert nulls == 0, f"{table}: {nulls} row(s) with no ProjectKey"
        orphans = one(con, f"SELECT COUNT(*) FROM {table} m "
                           f"LEFT JOIN dim_Project p ON p.ProjectKey = m.ProjectKey "
                           f"WHERE p.ProjectKey IS NULL")
        assert orphans == 0, f"{table}: {orphans} row(s) point at an unknown project"
    check(f"no orphaned ProjectKey across {len(MANUAL_TABLES)} manual tables")


def test_pqp_results_resolve_to_their_templates(con) -> None:
    """A result that does not join to its template is an answer to no question."""
    dangling = one(con, "SELECT COUNT(*) FROM man_QcChecklistResult r "
                        "LEFT JOIN qc_seed_ChecklistItem i ON i.ItemKey = r.ItemKey "
                        "WHERE i.ItemKey IS NULL")
    assert dangling == 0, f"{dangling} checklist answer(s) match no seeded item"

    dangling = one(con, "SELECT COUNT(*) FROM man_QcGate g "
                        "LEFT JOIN qc_seed_Gate s ON s.GateKey = g.GateKey "
                        "WHERE s.GateKey IS NULL")
    assert dangling == 0, f"{dangling} gate result(s) match no seeded gate"

    dangling = one(con, "SELECT COUNT(*) FROM man_QcDohResult d "
                        "LEFT JOIN qc_seed_DohItem s ON s.ItemKey = d.ItemKey "
                        "WHERE s.ItemKey IS NULL")
    assert dangling == 0, f"{dangling} DOH answer(s) match no seeded requirement"
    check("every checklist, gate and DOH result resolves to its seeded template")

    # TradeKey is a controlled key on four tables, and it is the one people get wrong -
    # 'Concrete Formwork' instead of CONCRETE_FORMWORK. The SharePoint choice column is
    # generated from the same seed to make that impossible; this proves it held.
    for table in ("man_QcDfow", "man_QcItp", "man_QcCommissioning", "man_QcChecklistResult"):
        orphans = one(con, f"SELECT COUNT(*) FROM {table} m "
                           f"LEFT JOIN qc_seed_Trade t ON t.TradeKey = m.TradeKey "
                           f"WHERE m.TradeKey IS NOT NULL AND t.TradeKey IS NULL")
        assert orphans == 0, f"{table}: {orphans} row(s) name a trade that is not seeded"
    check("no orphaned TradeKey on any PQP table")

    # The gate result's own discriminator has to agree with the template's, or the collapse
    # has produced a row filed under the wrong path.
    mismatched = one(con, "SELECT COUNT(*) FROM man_QcGate g "
                          "JOIN qc_seed_Gate s ON s.GateKey = g.GateKey "
                          "WHERE s.GateType <> g.GateType")
    assert mismatched == 0, f"{mismatched} gate result(s) disagree with the template's type"
    check("every gate result's GateType agrees with its template")


def test_pqp_keys_are_unique(con) -> None:
    """One row per project per thing. A duplicate does not error - it double-counts into
    '% of checklist items passed', which is a number on a client-facing page."""
    grain = {
        "man_QcDfow": "ProjectKey, DfowRef",
        "man_QcItp": "ProjectKey, ItpRef",
        "man_QcGate": "ProjectKey, GateKey",
        "man_QcSpecialInspection": "ProjectKey, InspectionRef",
        "man_QcCommissioning": "ProjectKey, SystemRef",
        "man_QcInspectorSignIn": "ProjectKey, SignInRef",
        "man_QcChecklistResult": "ProjectKey, ItemKey",
        "man_QcDohResult": "ProjectKey, ItemKey",
    }
    for table, cols in grain.items():
        dupes = one(con, f"SELECT COUNT(*) FROM (SELECT {cols} FROM {table} "
                         f"GROUP BY {cols} HAVING COUNT(*) > 1)")
        assert dupes == 0, f"{table}: {dupes} duplicate ({cols})"
    check(f"all {len(grain)} PQP result tables are unique on their natural key")


def test_status_codes_resolve(con) -> None:
    """A status the model cannot resolve renders as a blank slicer entry, which reads as
    'no data' rather than 'we do not know what this code means'."""
    coded = (
        ("man_QcDfow", "StatusCode", "DFOWRISKREGISTER_4"),
        ("man_QcItp", "ResultCode", "ITP_4"),
        ("man_QcItp", "StatusCode", "ITP_6"),
        ("man_QcSpecialInspection", "StatusCode", "SPECIALINSPECTIONS_5"),
        ("man_QcCommissioning", "StatusCode", "COMMISSIONING_6"),
        ("man_QcInspectorSignIn", "AgencyCode", "INSPECTORSIGNIN_11"),
        ("man_QcInspectorSignIn", "OutcomeCode", "INSPECTORSIGNIN_5"),
        ("man_QcChecklistResult", "StageCode", "EXCAVATION_4"),
        ("man_QcChecklistResult", "ResultCode", "EXCAVATION_3"),
        ("man_QcDohResult", "ResponsibilityCode", "DOHCHECKLIST_4"),
        ("man_QcDohResult", "StatusCode", "DOHCHECKLIST_6"),
    )
    for table, column, domain in coded:
        bad = one(con, f"SELECT COUNT(*) FROM {table} m LEFT JOIN dim_QcStatus s "
                       f"ON s.Domain = '{domain}' AND s.Code = m.{column} "
                       f"WHERE m.{column} IS NOT NULL AND s.Code IS NULL")
        assert bad == 0, f"{table}.{column}: {bad} value(s) not in dim_QcStatus[{domain}]"
    check(f"all {len(coded)} PQP code columns resolve to dim_QcStatus")

    # The gate table draws from three domains at once - that is the collapse's cost, and
    # it has to be checked as a union or every fire-alarm status reads as unresolvable.
    bad = one(con, "SELECT COUNT(*) FROM man_QcGate m LEFT JOIN ("
                   "  SELECT DISTINCT Code FROM dim_QcStatus WHERE Domain IN "
                   "  ('PATHTOTCO_6','PATHTOFIREALARM_7','STATUTORYINSPECTIONS_5')) s "
                   "ON s.Code = m.StatusCode "
                   "WHERE m.StatusCode IS NOT NULL AND s.Code IS NULL")
    assert bad == 0, f"{bad} gate status(es) are in none of the three path vocabularies"
    check("gate statuses resolve against the three paths' vocabularies unioned")


# --------------------------------------------------------------------------
# The Procore-sourced facts
# --------------------------------------------------------------------------


def test_procore_facts(con) -> None:
    """NCRs, punch items and submittals come from the API, not from a list."""
    assert one(con, "SELECT COUNT(*) FROM fct_QcNcr") == 3
    assert one(con, "SELECT COUNT(*) FROM fct_QcPunch") == 2
    assert one(con, "SELECT COUNT(*) FROM fct_QcSubmittal") == 3
    for table, key in (("fct_QcNcr", "NcrKey"), ("fct_QcPunch", "PunchKey"),
                       ("fct_QcSubmittal", "SubmittalKey")):
        n = one(con, f"SELECT COUNT(*) FROM {table}")
        assert one(con, f"SELECT COUNT(DISTINCT {key}) FROM {table}") == n
        assert one(con, f"SELECT COUNT(*) FROM {table} t LEFT JOIN dim_Project p "
                        f"ON p.ProjectKey = t.ProjectKey WHERE p.ProjectKey IS NULL") == 0
    check("the three Procore QC facts are uniquely keyed and fully attributed")

    # Trade resolution is exact-match only and leaves what it cannot resolve NULL next to a
    # flag. 'Concrete Formwork' resolves; 'Metals' is not one of the 26 and must NOT be
    # guessed into the nearest trade.
    assert one(con, "SELECT TradeKey FROM fct_QcNcr WHERE NcrKey='OB1'") == "CONCRETE_FORMWORK"
    assert one(con, "SELECT TradeKey FROM fct_QcNcr WHERE NcrKey='OB2'") is None
    assert one(con, "SELECT HasUnmappedTrade FROM fct_QcNcr WHERE NcrKey='OB2'") is True
    assert one(con, "SELECT HasUnmappedTrade FROM fct_QcNcr WHERE NcrKey='OB1'") is False
    # OB3 is the alias path, and it is the only thing that tests it. 'HVAC' does not
    # normalise to HVAC_DUCTWORK by any string rule - it resolves through
    # qc_seed_TradeAlias or not at all, so this assertion fails the moment that join
    # breaks. Live, the alias recovered 464 of 970 unmapped rows.
    assert one(con, "SELECT TradeKey FROM fct_QcNcr WHERE NcrKey='OB3'") == "HVAC_DUCTWORK"
    assert one(con, "SELECT HasUnmappedTrade FROM fct_QcNcr WHERE NcrKey='OB3'") is False
    # And the alias must not invent a trade that is not seeded - every TradeKey it emits
    # has to exist in qc_seed_Trade, or a CSV typo reads as "unmapped" instead of "wrong".
    assert one(con, "SELECT COUNT(*) FROM qc_seed_TradeAlias a "
                    "LEFT JOIN qc_seed_Trade t ON t.TradeKey = a.TradeKey "
                    "WHERE t.TradeKey IS NULL") == 0
    check("an unmatched Procore trade is flagged, never guessed into a seeded one")

    # Open comes from the DATA. Procore's status vocabulary is configurable per company, so
    # a rule keyed to the word "closed" breaks the day somebody renames it.
    assert one(con, "SELECT IsOpen FROM fct_QcNcr WHERE NcrKey='OB1'") is True
    assert one(con, "SELECT IsOpen FROM fct_QcNcr WHERE NcrKey='OB2'") is False
    assert one(con, "SELECT DaysOpen FROM fct_QcNcr WHERE NcrKey='OB2'") == 3
    check("IsOpen and DaysOpen derive from the dates, not from status text")

    # An unmapped Procore status stays NULL and keeps its source text, so the mapping can
    # be corrected from the data instead of the row being absorbed into an ELSE branch.
    assert one(con, "SELECT StatusCode FROM fct_QcSubmittal WHERE SubmittalKey='SB3'") is None
    assert one(con, "SELECT SourceStatus FROM fct_QcSubmittal "
                    "WHERE SubmittalKey='SB3'") == "Under Review"
    check("an unmapped Procore status is visible as NULL beside its source text")

    # A mockup is a submittal Procore has no field for, so it is derived - once, here.
    assert one(con, "SELECT IsMockup FROM fct_QcSubmittal WHERE SubmittalKey='SB2'") is True
    assert one(con, "SELECT IsMockup FROM fct_QcSubmittal WHERE SubmittalKey='SB1'") is False
    check("mockups are identifiable without a second place to record them")

    # MonthStart is the dim_Date join. A value outside the calendar matches nothing and
    # every measure over it returns BLANK, which on a card looks exactly like zero.
    for table in ("fct_QcNcr", "fct_QcPunch", "fct_QcSubmittal"):
        bad = one(con, f"SELECT COUNT(*) FROM {table} f LEFT JOIN dim_Date d "
                       f"ON f.MonthStart = d.Date "
                       f"WHERE f.MonthStart IS NOT NULL AND d.Date IS NULL")
        assert bad == 0, f"{table}: {bad} MonthStart value(s) outside dim_Date"
    check("every QC fact's MonthStart resolves to dim_Date")


def test_dim_job_links_the_flows_to_fabric(con) -> None:
    """The Power Automate job flows reach gold, and a duplicated job number is caught.

    Before this existed, power-automate/README.md described the Job Register as the dim_Job
    source while nothing anywhere read it: the flows created folders and issued numbers and
    not one row reached Fabric. This is the assertion that would have failed.
    """
    assert one(con, "SELECT COUNT(*) FROM dim_Job") > 0, \
        "no silver -> gold link reaches dim_Job"
    assert one(con, "SELECT ProjectName FROM dim_Job WHERE JobNumber = '26-001'") \
        == "Fulton Street Fit-Out"
    check("dim_Job is populated from the Job Register, so the job flows reach Fabric")

    # AND THE POINT OF BUILDING IT. The fixture holds two different jobs both issued
    # 26-002, which is what a race between two flow runs produces when somebody switches
    # trigger concurrency off in the Power Automate designer. Run the real expectation -
    # not a re-implementation of it - and require that it returns them.
    sys.path.insert(0, str(CHARLEY_DEV / "02-transformation" / "dq"))
    import expectations  # noqa: PLC0415

    suite = expectations.build_suite()
    dupe = next(e for e in suite.expectations if e.name == "dim_Job.JobNumber.unique")
    offenders = con.execute(dupe.failing_sql).fetchall()
    assert offenders, (
        "two jobs share a number and the expectation did not catch it - the guard on the "
        "flows' concurrency setting is not working"
    )
    assert offenders[0][0] == "26-002"
    assert dupe.severity == expectations.SEVERITY_ERROR, \
        "a duplicated job number must block, not warn"
    check("a duplicated job number fails the DQ gate, which is what guards flow concurrency")

    # The pending row - a job asked for but not yet numbered - must NOT trip anything.
    # It is the normal resting state of a healthy register, and a gate that fires on it
    # gets muted within a week, taking the real check above with it.
    pending = next(e for e in suite.expectations
                   if e.name == "dim_Job.JobNumber.issued_past_requested")
    assert not con.execute(pending.failing_sql).fetchall(), \
        "a job legitimately awaiting its number was flagged"
    check("a job still awaiting its number does not trip the gate")


def main() -> int:
    con = build()
    for fn in (test_seed_sql_is_current, test_checklist_collapse, test_gate_collapse,
               test_doh_and_status_seeds, test_manual_tables_are_reachable,
               test_dim_job_links_the_flows_to_fabric,
               test_every_pqp_table_carries_a_project,
               test_pqp_results_resolve_to_their_templates, test_pqp_keys_are_unique,
               test_status_codes_resolve, test_procore_facts):
        fn(con)
    for label in CHECKS:
        print(f"  ok  {label}")
    print(f"\ntest_qc: {len(CHECKS)} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
