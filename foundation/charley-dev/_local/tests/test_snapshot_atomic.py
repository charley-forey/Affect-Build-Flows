"""Execute actual swap SQL locally; DuckDB checks semantics, not Fabric runtime behavior."""
import sys
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import deploy_dq


def test_snapshot_atomic():
    _, swap = deploy_dq.snapshot_phases()
    assert len(swap) == 1 and swap[0].startswith("MERGE INTO"), "replacement must be one statement"
    sql = swap[0].replace("{SNAPSHOT_DATE}", "2026-09-14")
    con = duckdb.connect()
    try:
        con.execute("CREATE TABLE fct_DailySnapshot (SnapshotDate DATE, ProjectKey VARCHAR, "
                    "OpenSubmittals BIGINT CHECK (OpenSubmittals >= 0), RunId VARCHAR)")
        con.execute("CREATE TABLE v_DailySnapshotStage AS SELECT * FROM fct_DailySnapshot")
        con.execute("INSERT INTO fct_DailySnapshot VALUES "
                    "('2026-09-13','keep',7,'old'),('2026-09-14','same',1,'old'),"
                    "('2026-09-14','obsolete',2,'old'),('2026-09-14',NULL,3,'old')")
        con.execute("INSERT INTO v_DailySnapshotStage VALUES "
                    "('2026-09-14','same',4,'new'),('2026-09-14','added',5,'new'),"
                    "('2026-09-14',NULL,6,'new')")
        read = lambda: con.execute("SELECT CAST(SnapshotDate AS VARCHAR), ProjectKey, OpenSubmittals, RunId "
                                   "FROM fct_DailySnapshot ORDER BY SnapshotDate, ProjectKey NULLS LAST").fetchall()
        expected = [('2026-09-13', 'keep', 7, 'old'), ('2026-09-14', 'added', 5, 'new'),
                    ('2026-09-14', 'same', 4, 'new'), ('2026-09-14', None, 6, 'new')]
        con.execute(sql)
        assert read() == expected
        con.execute(sql)
        assert read() == expected, "same-date replay duplicated rows"
        con.execute("UPDATE v_DailySnapshotStage SET OpenSubmittals=-1 WHERE ProjectKey='same'")
        try:
            con.execute(sql)
        except duckdb.ConstraintException:
            pass
        else:
            raise AssertionError("invalid replacement accepted")
        assert read() == expected, "failed statement damaged previous capture"
        con.execute("DELETE FROM v_DailySnapshotStage")
        con.execute(sql)
        assert read() == expected[:1], "empty replacement must remove only the selected date"
    finally:
        con.close()


def test_snapshot_excludes_test_projects():
    """The live capture drops seed_ProjectExclusion keys and keeps a NULL (unmatched) key."""
    stage, _ = deploy_dq.snapshot_phases()
    con = duckdb.connect()
    try:
        for ddl in ("seed_ProjectExclusion (ProcoreProjectId VARCHAR)",
                    "dim_Project (ProjectKey VARCHAR)",
                    "fct_RfiSubmittal (ProjectKey VARCHAR, ItemType VARCHAR, IsOpen BOOLEAN, IsPastDue BOOLEAN)",
                    "fct_QualityItem (ProjectKey VARCHAR, ItemType VARCHAR, IsOpen BOOLEAN)",
                    "fct_Invoice (ProjectKey VARCHAR, Balance DOUBLE, Amount DOUBLE)",
                    "fct_BudgetLine (ProjectKey VARCHAR, BudgetAmount DOUBLE, SpentToDate DOUBLE, CommittedAmount DOUBLE)",
                    "fct_FinancialPeriod (ProjectKey VARCHAR, MonthStart DATE, CurrentContract DOUBLE, PendingChangeOrders DOUBLE)",
                    "fct_ChangeOrder (ProjectKey VARCHAR, IsPending BOOLEAN, StatusLabel VARCHAR, Amount DOUBLE)"):
            con.execute(f"CREATE TABLE {ddl}")
        con.execute("INSERT INTO seed_ProjectExclusion VALUES ('test')")
        con.execute("INSERT INTO dim_Project VALUES ('real'), ('test')")
        con.execute("INSERT INTO fct_RfiSubmittal VALUES ('real','RFI',TRUE,FALSE), ('test','RFI',TRUE,FALSE), "
                    "(NULL,'RFI',TRUE,FALSE)")
        live = next(s for s in stage if "v_DailySnapshotLive AS" in s)
        con.execute(live.replace("CREATE OR REPLACE TEMP VIEW", "CREATE OR REPLACE VIEW"))
        rows = con.execute("SELECT ProjectKey, OpenRfis FROM v_DailySnapshotLive ORDER BY ProjectKey NULLS LAST").fetchall()
        assert rows == [("real", 1), (None, 1)], rows
    finally:
        con.close()


if __name__ == "__main__":
    test_snapshot_atomic()
    test_snapshot_excludes_test_projects()
    print("atomic snapshot SQL checks passed (DuckDB; Fabric execution remains separate)")
