"""fct_ScoreHistory capture: the cd_40_dq_checks cell run on the fixture gold through DuckDB.

Checks the saved rows equal last week's fct_ProjectScore, a same-week rerun replaces rather
than duplicates, a project gone from the rerun is dropped from that week only, and a failure
is recorded and alerted without raising.
"""
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import deploy_dq
import seedrunner


class DuckSpark:
    def __init__(self, con):
        self.con = con

    def sql(self, query):
        query = query.replace(") USING DELTA", ")").replace("CREATE OR REPLACE TEMP VIEW", "CREATE OR REPLACE VIEW")
        rel = self.con.execute(query)
        rows = rel.fetchall() if rel.description else []
        return SimpleNamespace(first=lambda: rows[0] if rows else None, count=lambda: len(rows))


def cell_source() -> str:
    return next(s for s in ("".join(c["source"]) for c in deploy_dq.build_notebook()["cells"])
                if "WEEKLY GRADE HISTORY" in s)


def run(con, batch_id, notify=None):
    alerts = []
    with tempfile.TemporaryDirectory() as diag:
        (Path(diag) / "heartbeat_run.json").write_text(json.dumps({"run_id": batch_id}))
        scope = dict(spark=DuckSpark(con), batch_id=batch_id, DIAG=diag, json=json, os=__import__("os"),
                     dq=SimpleNamespace(publish_schema=lambda *a: None),
                     fc=SimpleNamespace(notify=notify or (lambda *a, **k: alerts.append(a) or True)))
        exec(compile(cell_source(), "dq:score-history", "exec"), scope)
        record = json.loads((Path(diag) / "score_history_run.json").read_text())
        assert json.loads((Path(diag) / "heartbeat_run.json").read_text())["score_history_status"] == record["status"]
    return record, alerts


def saved(con):
    return con.execute("SELECT ProjectKey, Grade, RunId FROM fct_ScoreHistory ORDER BY ProjectKey").fetchall()


def test_score_history():
    con = seedrunner.build()
    expected = con.execute("SELECT ProjectKey, Grade FROM fct_ProjectScore WHERE WeeksAgo = 1 ORDER BY ProjectKey").fetchall()
    assert expected, "fixture has no last-week scores"
    week = str(con.execute("SELECT WeekStart FROM dim_ReportWeek WHERE WeeksAgo = 1").fetchone()[0])

    record, alerts = run(con, "r1")
    assert record["status"] == "ok" and record["week_start"] == week and record["rows"] == len(expected), record
    assert not alerts
    assert [(k, g) for k, g, _ in saved(con)] == expected and {r for _, _, r in saved(con)} == {"r1"}

    # An earlier week is history: a rerun for this week must leave it alone.
    con.execute("INSERT INTO fct_ScoreHistory SELECT DATE '2000-01-03', 'old', NULL, NULL, NULL, NULL, "
                "NULL, 42, NULL, NULL, 'r0', CURRENT_TIMESTAMP")
    dropped = expected[0][0]
    con.execute(f"DELETE FROM fct_ProjectScore WHERE WeeksAgo = 1 AND ProjectKey = '{dropped}'")
    record, _ = run(con, "r2")
    assert record["status"] == "ok" and record["rows"] == len(expected) - 1, record
    rows = saved(con)
    assert ("old", 42, "r0") in rows and dropped not in {k for k, _, _ in rows}
    assert {r for k, _, r in rows if k != "old"} == {"r2"}, "same-week rerun must replace, not add"

    # A failure (no report week) is recorded and alerted, and never raises into the gate.
    con.execute("DELETE FROM dim_ReportWeek")
    before = saved(con)
    record, alerts = run(con, "r3")
    assert record["status"] == "failed" and "WeeksAgo = 1" in record["error"] and alerts and "GRADE HISTORY FAILED" in alerts[0][0]
    assert saved(con) == before


if __name__ == "__main__":
    test_score_history()
    print("score history capture checks passed (DuckDB; Fabric execution remains separate)")
