"""Write _docs/trade-mapping-worklist.csv - the trade mapping decisions, for offline review.

    python export_trade_worklist.py            # write the CSV
    python export_trade_worklist.py --check    # fail if the committed CSV is stale

No Fabric. Input is _docs/trade-label-evidence.json, the per-label counts captured by a
read-only query against silver. The label counts are expanded back into rows and run
through the REAL 46_dq_trademappingcandidate.sql in DuckDB, so the CSV and the gold table
cannot disagree about a status or a proposal. Labels and counts only - no names, no ids.
"""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from seedrunner import CHARLEY_DEV, build, split_statements  # noqa: E402

EVIDENCE = CHARLEY_DEV / "_docs" / "trade-label-evidence.json"
OUT = CHARLEY_DEV / "_docs" / "trade-mapping-worklist.csv"
SQL = CHARLEY_DEV / "02-transformation" / "sql" / "gold" / "46_dq_trademappingcandidate.sql"
COLUMNS = ("RawTrade", "MappingStatus", "AffectedRecords", "ObservationCount", "PunchCount",
           "InspectionCount", "ProjectCount", "FirstSeen", "LastSeen", "CurrentTradeKey",
           "ProposedTradeKeys", "ProposalSource", "ProposalReason", "IsDecisionNeeded")


def worklist(labels: list[dict]) -> list[tuple]:
    con = build()
    rows = {"sv_qc_ncr": [], "sv_qc_punch": [], "sv_qc_inspection": []}
    for lab in labels:
        n = lab["obs"] + lab["punch"] + lab["insp"]
        # One row per record; projects cycle so COUNT(DISTINCT) reproduces, and the first
        # record carries first_seen so MIN/MAX reproduce.
        kinds = ["sv_qc_ncr"] * lab["obs"] + ["sv_qc_punch"] * lab["punch"] + ["sv_qc_inspection"] * lab["insp"]
        for i, view in enumerate(kinds):
            seen = lab["first_seen"] if i == 0 else lab["last_seen"]
            rows[view].append((f"P{i % lab['projects']}", lab["label"], seen))
        assert n >= lab["projects"]
    for view, data in rows.items():
        date_col = "inspection_date" if view == "sv_qc_inspection" else "created_date"
        con.execute(f"CREATE OR REPLACE TABLE _{view} (project_id VARCHAR, trade VARCHAR, {date_col} DATE)")
        if data:
            con.executemany(f"INSERT INTO _{view} VALUES (?, ?, ?)", data)
        con.execute(f"CREATE OR REPLACE VIEW {view} AS SELECT * FROM _{view}")
    for statement in split_statements(SQL.read_text(encoding="utf-8")):
        con.execute(statement)
    return con.execute(f"SELECT {', '.join(COLUMNS)} FROM dq_TradeMappingCandidate "
                       "ORDER BY IsDecisionNeeded DESC, AffectedRecords DESC, RawTrade").fetchall()


def render(rows: list[tuple]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(COLUMNS)
    w.writerows(rows)
    return buf.getvalue()


def main() -> int:
    text = render(worklist(json.loads(EVIDENCE.read_text(encoding="utf-8"))["labels"]))
    if "--check" in sys.argv:
        if OUT.read_text(encoding="utf-8") != text:
            print(f"STALE: {OUT.name} - re-run without --check")
            return 1
        print(f"{OUT.name} up to date")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(CHARLEY_DEV)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
