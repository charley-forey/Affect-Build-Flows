"""End-to-end check of the SQL layer. Run: python src/procore/tests/test_pipeline.py

Executes the real .sql files against the fixtures in DuckDB and asserts the shape of the
result. The single most important assertion here is test_rerun_is_idempotent: running the
pipeline twice must not double the row counts. That is the proof for defect #2 (the
current ETL replaces the whole table every run), and it is the thing most likely to
regress silently.
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import duckdb  # noqa: E402

from run_local import (  # noqa: E402
    COMPAT_MACROS,
    bronze_from_fixtures,
    load_bronze,
    run_sql,
    table_names,
)


def build(con):
    load_bronze(con, bronze_from_fixtures())
    run_sql(con)
    return con


def fresh():
    tmp = tempfile.mkdtemp()
    con = duckdb.connect(str(Path(tmp) / "t.duckdb"))
    con.execute(COMPAT_MACROS)
    return con


def counts(con):
    return {name: con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            for name in table_names(con)}


def one(con, sql):
    return con.execute(sql).fetchone()[0]


# --------------------------------------------------------------------------


def test_rerun_is_idempotent():
    """THE defect-#2 proof. Two runs, identical counts, no doubling anywhere."""
    con = fresh()
    build(con)
    first = counts(con)
    build(con)
    second = counts(con)
    assert first == second, (
        "row counts changed on re-run - the merge is appending instead of replacing.\n"
        f"first={first}\nsecond={second}"
    )
    assert first["bronze_procore_rfis"] == 6, first


def test_silver_rejects_bad_rows_and_keeps_the_rest():
    con = build(fresh())
    assert one(con, "SELECT COUNT(*) FROM silver_rfi_submittal") == 8
    rejects = con.execute(
        "SELECT Issue FROM data_quality_log WHERE Severity = 'reject' ORDER BY Issue"
    ).fetchall()
    assert [r[0] for r in rejects] == ["closed_before_created", "missing_item_number"], rejects


def test_nothing_is_dropped_silently():
    """Every bronze row is either in silver or explained in the log."""
    con = build(fresh())
    bronze = one(con, "SELECT COUNT(*) FROM bronze_rfi_submittal_union")
    silver = one(con, "SELECT COUNT(*) FROM silver_rfi_submittal")
    rejected = one(con, "SELECT COUNT(*) FROM data_quality_log WHERE Severity = 'reject'")
    assert bronze == silver + rejected, f"{bronze} != {silver} + {rejected}"


def test_trailing_whitespace_is_trimmed():
    con = build(fresh())
    untrimmed = one(
        con,
        "SELECT COUNT(*) FROM silver_rfi_submittal "
        "WHERE StatusLabel <> TRIM(StatusLabel) OR ItemNumber <> TRIM(ItemNumber)",
    )
    assert untrimmed == 0, "text values reached silver untrimmed"


def test_dim_trade_is_deduplicated_with_an_unassigned_member():
    con = build(fresh())
    # 29 cells in DROPDOWN!M4:M32, `Metals` twice -> 28 distinct, + Unassigned.
    assert one(con, "SELECT COUNT(*) FROM dim_Trade") == 29
    assert one(con, "SELECT COUNT(DISTINCT TradeName) FROM dim_Trade") == 29
    assert one(con, "SELECT TradeName FROM dim_Trade WHERE TradeKey = 0") == "Unassigned"


def test_dim_status_keeps_the_seed_and_adds_procore_domains():
    con = build(fresh())
    assert one(con, "SELECT COUNT(*) FROM dim_Status") == 37, "32 seeded + 3 RFI + 2 submittal"
    assert one(con, "SELECT COUNT(*) FROM dim_Status WHERE Domain = 'RfiStatus'") == 3
    assert one(con, "SELECT COUNT(*) FROM dim_Status WHERE Domain = 'SubmittalStatus'") == 2
    # Codes are uppercase and underscored so joins never touch a display label.
    assert one(con, "SELECT COUNT(*) FROM dim_Status WHERE Code <> UPPER(Code)") == 0
    assert one(con, "SELECT IsOpen FROM dim_Status WHERE Domain='RfiStatus' AND Code='OPEN'")
    assert not one(con, "SELECT IsOpen FROM dim_Status WHERE Domain='RfiStatus' AND Code='CLOSED'")


def test_fact_has_every_column_the_dax_reads():
    """powerbi/measures.dax reads these by name; a rename here blanks the report."""
    con = build(fresh())
    cols = {r[0] for r in con.execute("DESCRIBE fct_RfiSubmittal").fetchall()}
    required = {"ProjectKey", "TradeKey", "StatusKey", "ItemType", "ItemNumber",
                "IsCritical", "DaysOpen"}
    assert required <= cols, f"missing: {required - cols}"


def test_item_type_uses_the_exact_dax_literals():
    con = build(fresh())
    types = {r[0] for r in con.execute("SELECT DISTINCT ItemType FROM fct_RfiSubmittal").fetchall()}
    assert types == {"RFI", "Submittal"}, types


def test_every_fact_row_resolves_its_keys():
    con = build(fresh())
    assert one(con, "SELECT COUNT(*) FROM fct_RfiSubmittal WHERE ProjectKey IS NULL") == 0
    assert one(con, "SELECT COUNT(*) FROM fct_RfiSubmittal WHERE StatusKey IS NULL") == 0
    assert one(con, "SELECT COUNT(*) FROM fct_RfiSubmittal WHERE TradeKey IS NULL") == 0


def test_unmappable_trades_are_flagged_not_dropped():
    """The two spec-section-formatted values cannot match Affect's trade list."""
    con = build(fresh())
    warns = one(
        con, "SELECT COUNT(*) FROM data_quality_log WHERE Issue = 'unmatched_trade'"
    )
    assert warns == 2, warns
    unassigned = one(con, "SELECT COUNT(*) FROM fct_RfiSubmittal WHERE TradeKey = 0")
    assert unassigned == 2, "flagged rows must still reach the fact table"
    assert one(con, "SELECT COUNT(*) FROM fct_RfiSubmittal") == 8


def test_days_open_counts_from_created_to_closed():
    con = build(fresh())
    # RFI-003: created 2026-04-11, closed 2026-04-22.
    assert one(con, "SELECT DaysOpen FROM fct_RfiSubmittal WHERE ItemNumber = 'RFI-003'") == 11
    # An open item measures to today, so it only ever grows.
    assert one(
        con, "SELECT COUNT(*) FROM fct_RfiSubmittal WHERE ClosedDate IS NULL AND DaysOpen < 0"
    ) == 0


def test_is_critical_follows_the_priority_rule():
    con = build(fresh())
    critical = {
        r[0] for r in con.execute(
            "SELECT ItemNumber FROM fct_RfiSubmittal WHERE IsCritical"
        ).fetchall()
    }
    # High on RFI-001/003/010 and SUB-001, Urgent on SUB-010. Low/Medium excluded.
    assert critical == {"RFI-001", "RFI-003", "RFI-010", "SUB-001", "SUB-010"}, critical


def test_the_report_number_is_computable():
    """Open + critical, by trade - the one figure SUBMITTALS & RFI!Table22 actually needs."""
    con = build(fresh())
    rows = con.execute(
        """SELECT t.TradeName, COUNT(*)
           FROM fct_RfiSubmittal f
           JOIN dim_Trade  t ON t.TradeKey  = f.TradeKey
           JOIN dim_Status s ON s.StatusKey = f.StatusKey
           WHERE f.IsCritical AND s.IsOpen
           GROUP BY 1 ORDER BY 2 DESC, 1"""
    ).fetchall()
    assert dict(rows) == {"HVAC": 2, "Electrical": 1, "Plumbing": 1}, rows


# --------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    failed = []
    for name, fn in tests:
        try:
            fn()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001
            failed.append((name, exc))
            print(f"  FAIL {name}: {exc}")
    print(f"\n{len(tests) - len(failed)}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
