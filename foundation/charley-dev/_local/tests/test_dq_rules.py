"""Mutation regressions for the conservation, key, vocabulary and band rules in expectations.py.

Each rule must pass on the shipped fixtures and FAIL once the fixture is corrupted in the
way the rule exists to catch. A rule that never fails is decoration.

Run:  python test_dq_rules.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from seedrunner import CHARLEY_DEV, build  # noqa: E402

sys.path.insert(0, str(CHARLEY_DEV / "02-transformation" / "dq"))
import expectations  # noqa: E402

RULES = {e.name: e for e in expectations.build_suite().expectations}


def failing(con, name: str) -> int:
    return len(con.execute(RULES[name].failing_sql.replace("`", '"')).fetchall())


def mutated(con, name: str, *sql: str) -> int:
    """Failing-row count after the mutation, rolled back afterwards."""
    con.execute("BEGIN")
    try:
        for s in sql:
            con.execute(s)
        return failing(con, name)
    finally:
        con.execute("ROLLBACK")


def check_fails(con, name: str, *sql: str, clean: bool = True) -> None:
    before = failing(con, name)
    if clean:
        assert before == 0, f"{name}: fails on clean fixtures ({before})"
    after = mutated(con, name, *sql)
    assert after > before, f"{name}: did not fire on {sql}"


def main() -> int:
    con = build()
    checks = 0

    # Conservation: altered amount, dropped row, fanned-out row, extra source row.
    for gold, view, src_cols, gold_cols, keep in expectations.CONSERVATION:
        name = f"{gold} conserves {view} rows and amounts exactly"
        assert RULES[name].severity == expectations.SEVERITY_ERROR
        # Corrupt EACH compared column, not just the last: a column missing from the rule
        # would pass silently.
        types = dict(con.execute("SELECT column_name, data_type FROM information_schema.columns "
                                 "WHERE table_name = ?", [gold]).fetchall())
        for col in gold_cols.split(", "):
            corrupt = {"BOOLEAN": f"NOT COALESCE({col}, FALSE)", "VARCHAR": f"COALESCE({col}, '') || 'x'"
                       }.get(types[col], f"COALESCE({col}, 0) + 1")
            check_fails(con, name, f"UPDATE {gold} SET {col} = {corrupt} WHERE rowid = 0")
            checks += 1
        check_fails(con, name, f"DELETE FROM {gold} WHERE rowid = 0")
        check_fails(con, name, f"INSERT INTO {gold} SELECT * FROM {gold} LIMIT 1")
        snap = f"CREATE TEMP TABLE {view}_snap AS SELECT * FROM {view}"
        check_fails(con, name, snap,
                    f"CREATE OR REPLACE VIEW {view} AS SELECT * FROM {view}_snap "
                    f"UNION ALL SELECT * FROM {view}_snap LIMIT 1")
        checks += 4
        if keep:
            # A no-project source row is NOT a conservation failure (gold drops it by
            # design) but IS counted by the warning.
            drop = f"{view} rows dropped from {gold} for having no project"
            assert RULES[drop].severity == expectations.SEVERITY_WARN
            orphan = (snap, f"CREATE OR REPLACE VIEW {view} AS SELECT * FROM {view}_snap UNION ALL "
                            f"(SELECT * REPLACE (CAST(NULL AS VARCHAR) AS project_id) FROM {view}_snap LIMIT 1)")
            check_fails(con, drop, *orphan)
            assert mutated(con, name, *orphan) == 0, f"{name}: fired on a row gold drops by design"
            checks += 2

    check_fails(con, "unattributed Outbuild critical activities dropped from fct_Milestone",
                "CREATE TEMP TABLE ob_snap AS SELECT * FROM sv_outbuild_activities",
                "CREATE OR REPLACE VIEW sv_outbuild_activities AS SELECT * FROM ob_snap UNION ALL "
                "(SELECT * REPLACE (CAST(NULL AS VARCHAR) AS project_id, TRUE AS is_critical) FROM ob_snap LIMIT 1)")
    checks += 1

    # Keys: a duplicated row must fire every uniqueness rule added for these tables.
    unique = [e for e in RULES.values() if e.name.endswith(".unique") and (e.table.startswith("man_")
              or e.table in {"fct_ChangeOrder", "fct_Milestone", "fct_FinancialPeriod", "fct_DirectCost"})]
    for rule in unique:
        check_fails(con, rule.name, f"INSERT INTO {rule.table} SELECT * FROM {rule.table} LIMIT 1")
        checks += 1
    assert len(unique) >= 4 + 17, [r.name for r in unique]

    # Vendor references: WARN, and they fire on an unknown vendor. The bridge fixture
    # already names a vendor outside the directory (V3), so it must merely grow.
    for table in ("fct_VendorInsurance", "bridge_VendorCostCode"):
        name = f"{table}.VendorKey.fk_dim_Vendor"
        assert RULES[name].severity == expectations.SEVERITY_WARN
        check_fails(con, name, f"UPDATE {table} SET VendorKey = 'NOT_A_VENDOR'", clean=False)
        checks += 1

    # QC vocabulary: an unknown code fires, and so does a real code from ANOTHER list.
    status = [e for e in RULES.values() if e.name.endswith(".fk_dim_QcStatus")]
    assert len(status) == 17, len(status)
    for rule in status:
        column = rule.name.split(".")[1]
        check_fails(con, rule.name, f"UPDATE {rule.table} SET {column} = 'NOT_A_CODE'")
        checks += 1
    check_fails(con, "fct_QcNcr.StatusCode.fk_dim_QcStatus", "UPDATE fct_QcNcr SET StatusCode = 'CORRECTED'")
    checks += 1

    # Score bands: gap, overlap, bounded top band, empty band, text row with bounds.
    band = "dim_ScorecardBand numeric bands tile with no gap or overlap"
    for sql in ("UPDATE dim_ScorecardBand SET MinValue = 50 WHERE CategoryKey = 1 AND Score = 2",
                "UPDATE dim_ScorecardBand SET MaxValue = 50 WHERE CategoryKey = 1 AND Score = 3",
                "UPDATE dim_ScorecardBand SET MaxValue = 999 WHERE CategoryKey = 1 AND Score = 0",
                "UPDATE dim_ScorecardBand SET MaxValue = 45 WHERE CategoryKey = 1 AND Score = 2",
                "UPDATE dim_ScorecardBand SET MinValue = NULL WHERE CategoryKey = 3 AND Score = 2",
                "UPDATE dim_ScorecardBand SET MinValue = 1 WHERE CategoryKey = 2 AND Score = 3"):
        check_fails(con, band, sql)
        checks += 1

    # AR receipts. Conservation is ERROR (our aggregation); the rest are source facts, WARN.
    conserve = "fct_Invoice.PaymentsReceived conserves sv_ar_payments"
    assert RULES[conserve].severity == expectations.SEVERITY_ERROR
    for sql in ("UPDATE fct_Invoice SET PaymentsReceived = PaymentsReceived + 1 WHERE InvoiceKey = 'INV1'",
                "UPDATE fct_Invoice SET PaymentsReceived = NULL WHERE InvoiceKey = 'INV1'",
                "UPDATE fct_Invoice SET PaymentsReceived = 5 WHERE InvoiceKey = 'INV3'",
                "DELETE FROM fct_Invoice WHERE InvoiceKey = 'INV1'"):
        check_fails(con, conserve, sql)
        checks += 1
    snap = "CREATE TEMP TABLE pmt_snap AS SELECT * FROM sv_ar_payments"
    check_fails(con, conserve, snap, "CREATE OR REPLACE VIEW sv_ar_payments AS SELECT * FROM pmt_snap "
                                     "UNION ALL SELECT * FROM pmt_snap WHERE payment_uid = 'PMT1'")
    orphan = (snap, "CREATE OR REPLACE VIEW sv_ar_payments AS SELECT * FROM pmt_snap UNION ALL "
                    "SELECT 'PMTX', 'NO-SUCH-INVOICE', NULL, DATE '2025-06-01', 10.0")
    check_fails(con, "sv_ar_payments rows with no AR invoice", *orphan)
    assert mutated(con, conserve, *orphan) == 0, "conservation fired on a receipt with no invoice"
    checks += 2
    recon = "fct_Invoice receipts reconcile to AmountPaid"
    check_fails(con, recon, "UPDATE fct_Invoice SET AmountPaid = AmountPaid + 1 WHERE InvoiceKey = 'INV1'")
    check_fails(con, "fct_Invoice.PaidDate is not before SentDate",
                "UPDATE fct_Invoice SET PaidDate = SentDate - INTERVAL 1 DAY WHERE InvoiceKey = 'INV1'")
    for name in (recon, "fct_Invoice.PaidDate is not before SentDate", "sv_ar_payments rows with no AR invoice"):
        assert RULES[name].severity == expectations.SEVERITY_WARN, name
    checks += 3

    # Owned crosswalks: a key pointing nowhere or at two entities blocks; a gap warns.
    xw = "CREATE TEMP TABLE xw_snap AS SELECT * FROM sv_project_crosswalk"
    check_fails(con, "sv_project_crosswalk Sage job maps to only one project", xw,
                "CREATE OR REPLACE VIEW sv_project_crosswalk AS SELECT * FROM xw_snap "
                "UNION ALL SELECT 'P2', 'S100', 'Depot B'")
    # The shared fixture's P3/S300 row is deliberately in neither source, so not clean.
    check_fails(con, "sv_project_crosswalk rows exist in Procore and Sage", xw,
                "CREATE OR REPLACE VIEW sv_project_crosswalk AS SELECT * FROM xw_snap "
                "UNION ALL SELECT 'P1', 'S404', 'Typo'", clean=False)
    check_fails(con, "Sage jobs with AR/AP but no crosswalk mapping", xw,
                "CREATE OR REPLACE VIEW sv_project_crosswalk AS SELECT * FROM xw_snap WHERE sage_project_id <> 'S100'",
                clean=False)
    vn = "CREATE TEMP TABLE vn_snap AS SELECT * FROM sv_vendors"
    check_fails(con, "Sage AP invoices with no job",
                "CREATE TEMP TABLE ap_snap AS SELECT * FROM sv_ap_invoices",
                "CREATE OR REPLACE VIEW sv_ap_invoices AS SELECT * REPLACE (CAST(NULL AS VARCHAR) AS sage_project_id) FROM ap_snap",
                clean=False)  # the shared fixture's AP3 has no job by design
    check_fails(con, "sv_vendors Sage vendor id exists in actpay", vn,
                "CREATE OR REPLACE VIEW sv_vendors AS SELECT * REPLACE ('SV404' AS sage_vendor_id) FROM vn_snap")
    check_fails(con, "sv_vendors Sage vendor maps to only one Procore vendor", vn,
                "CREATE OR REPLACE VIEW sv_vendors AS SELECT * REPLACE (COALESCE(sage_vendor_id, 'SV1') AS sage_vendor_id) FROM vn_snap")
    check_fails(con, "ERP-synced vendors without origin_code", vn,
                "CREATE OR REPLACE VIEW sv_vendors AS SELECT * REPLACE (CAST(NULL AS VARCHAR) AS sage_vendor_id) FROM vn_snap")
    for name, sev in (("sv_project_crosswalk Sage job maps to only one project", "error"),
                      ("sv_project_crosswalk rows exist in Procore and Sage", "warn"),
                      ("Sage jobs with AR/AP but no crosswalk mapping", "warn"),
                      ("sv_vendors Sage vendor id exists in actpay", "warn"),
                      ("Sage AP invoices with no job", "warn"),
                      ("sv_vendors Sage vendor maps to only one Procore vendor", "error"),
                      ("ERP-synced vendors without origin_code", "warn")):
        assert RULES[name].severity == sev, name
    checks += 7
    # Submittal date rules: the pre-2026-09-14 mapping (responded submittals open, and an
    # intake date before creation as the "response") must trip both.
    for fact, where in (("fct_RfiSubmittal", "ItemKey = 'SB2'"), ("fct_QcSubmittal", "SubmittalKey = 'SB2'")):
        name = f"{fact}: no responded submittal is counted open"
        assert RULES[name].severity == expectations.SEVERITY_ERROR
        check_fails(con, name, f"UPDATE {fact} SET IsOpen = TRUE WHERE {where}")
        checks += 1
    early = "submittal responded before it was created"
    assert RULES[early].severity == expectations.SEVERITY_WARN
    check_fails(con, early, "UPDATE fct_RfiSubmittal SET RespondedDate = CreatedDate - INTERVAL 3 DAY "
                            "WHERE ItemKey = 'SB2'")
    # An RFI answered "early" is not this rule's business.
    assert mutated(con, early, "UPDATE fct_RfiSubmittal SET RespondedDate = CreatedDate - INTERVAL 3 DAY "
                               "WHERE ItemType = 'RFI'") == 0
    checks += 2

    con.close()
    print(f"test_dq_rules: {checks} mutation checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
