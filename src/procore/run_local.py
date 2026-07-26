"""Run the whole Procore pipeline locally: bronze -> silver -> gold.

    python src/procore/run_local.py              # fixtures (no credentials needed)
    python src/procore/run_local.py --live       # hit the Procore sandbox
    python src/procore/run_local.py --capture    # hit the sandbox AND refresh fixtures

Why this exists: the .sql files are written in Spark SQL because Fabric is the production
target, but there is no Fabric access yet and no JDK on this machine. DuckDB runs the same
files unchanged given three compatibility macros (below), so the transformations are
actually executed rather than merely written.

What this verifies: SQL logic - joins, rejects, key resolution, row counts. What it does
NOT verify: Spark dialect edge cases. That gets checked in Fabric when access lands.

Output: .local/gold/*.parquet, which the Power BI project reads.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import duckdb  # noqa: E402

from procore_extract import (  # noqa: E402
    load_endpoints,
    load_settings,
    split_sql_statements,
)

HERE = Path(__file__).resolve().parent
SQL_DIR = HERE / "sql"
FIXTURE_DIR = HERE / "tests" / "fixtures"
OUT_DIR = HERE.parents[1] / ".local"

# Spark SQL functions DuckDB spells differently. Three lines is the entire dialect gap
# for this pipeline - keeping the .sql files in the production dialect is worth it.
COMPAT_MACROS = """
CREATE OR REPLACE MACRO get_json_object(j, p) AS json_extract_string(j, p);
CREATE OR REPLACE MACRO spark_datediff(e, s) AS date_diff('day', CAST(s AS DATE), CAST(e AS DATE));
"""

# DuckDB already has datediff(part, start, end); a 2-arg macro of the same name is a
# conflict, so the SQL is rewritten on the way in. This is the only textual rewrite.
DIALECT_REWRITES = [("datediff(", "spark_datediff(")]


def bronze_from_fixtures() -> dict[str, list[dict]]:
    """Load captured/sample API responses and wrap them as bronze rows."""
    from procore_extract import Endpoint, to_bronze_row

    endpoints = {e.name: e for e in load_endpoints(str(HERE / "config" / "endpoints.yml"))}
    ingested_at = datetime.now(timezone.utc)
    tables: dict[str, list[dict]] = {}

    for path in sorted(FIXTURE_DIR.glob("*.json")):
        fixture = json.loads(path.read_text(encoding="utf-8"))
        endpoint: Endpoint = endpoints[fixture["endpoint"]]
        rows = []
        for rec in fixture["records"]:
            # `_project_id` is fixture scaffolding, not part of the API payload.
            project_id = rec.pop("_project_id", None)
            rows.append(to_bronze_row(rec, endpoint, project_id, ingested_at))
        tables.setdefault(endpoint.bronze_table, []).extend(rows)
    return tables


def bronze_from_sandbox(capture: bool) -> dict[str, list[dict]]:
    """Pull live from the Procore sandbox using the same engine Fabric uses."""
    import requests

    from procore_extract import extract_endpoint, fetch_token, iter_active_projects

    settings = load_settings()
    session = requests.Session()
    token = fetch_token(settings, session)

    projects = list(iter_active_projects(session, settings, token))
    project_ids = [int(p["id"]) for p in projects]
    print(f"  {len(project_ids)} active project(s): {project_ids}")

    tables: dict[str, list[dict]] = {}
    for endpoint in load_endpoints(str(HERE / "config" / "endpoints.yml")):
        rows = extract_endpoint(session, settings, token, endpoint, project_ids)
        tables.setdefault(endpoint.bronze_table, []).extend(rows)
        print(f"  {endpoint.name:22s} {len(rows):5d} rows")
        if capture:
            FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
            (FIXTURE_DIR / f"{endpoint.name}.json").write_text(
                json.dumps(
                    {
                        "endpoint": endpoint.name,
                        "captured_at": datetime.now(timezone.utc).isoformat(),
                        "records": [json.loads(r["payload"]) for r in rows],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
    return tables


def load_bronze(con: duckdb.DuckDBPyConnection, tables: dict[str, list[dict]]) -> None:
    """Create bronze tables, MERGE-style: existing keys are replaced, not appended.

    This is the local stand-in for the Delta merge in Fabric, and it is what makes
    re-running the pipeline idempotent (defect #2). Running twice must not double rows.
    """
    for name, rows in tables.items():
        con.execute(
            f"""CREATE TABLE IF NOT EXISTS {name} (
                    _key VARCHAR, _project_id INTEGER, _source_endpoint VARCHAR,
                    _ingested_at TIMESTAMPTZ, payload VARCHAR)"""
        )
        if not rows:
            continue
        con.executemany(
            f"DELETE FROM {name} WHERE _key = ? AND (_project_id IS NOT DISTINCT FROM ?)",
            [(r["_key"], r["_project_id"]) for r in rows],
        )
        con.executemany(
            f"INSERT INTO {name} VALUES (?, ?, ?, ?, ?)",
            [
                (
                    r["_key"],
                    r["_project_id"],
                    r["_source_endpoint"],
                    r["_ingested_at"],
                    r["payload"],
                )
                for r in rows
            ],
        )


def run_sql(con: duckdb.DuckDBPyConnection) -> None:
    for path in sorted(SQL_DIR.glob("*.sql")):
        sql = path.read_text(encoding="utf-8")
        for old, new in DIALECT_REWRITES:
            sql = sql.replace(old, new)
        for statement in split_sql_statements(sql):
            try:
                con.execute(statement)
            except Exception as exc:
                raise RuntimeError(f"{path.name}: {exc}\n---\n{statement[:400]}") from exc
        print(f"  ran {path.name}")


def table_names(con: duckdb.DuckDBPyConnection) -> list[str]:
    """Real tables only - leading-underscore names are intermediate views."""
    return sorted(
        r[0] for r in con.execute("SHOW TABLES").fetchall() if not r[0].startswith("_")
    )


def report(con: duckdb.DuckDBPyConnection) -> None:
    print("\nRow counts")
    tables = table_names(con)
    for name in tables:
        count = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        print(f"  {name:34s} {count:6d}")

    if "data_quality_log" in tables:
        issues = con.execute(
            "SELECT Severity, Issue, COUNT(*) FROM data_quality_log "
            "GROUP BY 1, 2 ORDER BY 1, 3 DESC"
        ).fetchall()
        print("\nData quality" if issues else "\nData quality: clean")
        for severity, issue, count in issues:
            print(f"  {severity:7s} {issue:22s} {count:5d}")


def export(con: duckdb.DuckDBPyConnection) -> None:
    """Write the gold tables to parquet for the Power BI project to read."""
    gold = OUT_DIR / "gold"
    gold.mkdir(parents=True, exist_ok=True)
    for name in table_names(con):
        if name.startswith(("dim_", "fct_", "data_quality")):
            target = (gold / f"{name}.parquet").as_posix()
            con.execute(f"COPY {name} TO '{target}' (FORMAT PARQUET)")
    print(f"\nGold parquet -> {gold}")


ISSUE_EXPLANATIONS = {
    "unmatched_trade": "Procore carries a cost code / spec section, not Affect's trade list",
    "unmatched_status": "status value not in the Procore vocabulary we seeded",
    "unknown_project": "no matching project in dim_Project",
    "missing_item_number": "draft with no number assigned yet",
    "closed_before_created": "close date precedes the create date",
    "missing_project_id": "no project on the record",
    "missing_item_id": "no id on the record",
    "missing_created_date": "no create date on the record",
}


def write_preview(con: duckdb.DuckDBPyConnection, source: str) -> Path:
    """Render the gold tables to a standalone HTML page.

    Generated on every run rather than written once, so it can never drift from the
    data. This is what can be shown to Affect before anyone has a Power BI licence
    pointed at the Lakehouse.
    """
    rows = lambda sql: con.execute(sql).fetchall()  # noqa: E731

    by_trade = [
        {"trade": t, "rfis": r, "submittals": s}
        for t, r, s in rows(
            """SELECT t.TradeName,
                      SUM(CASE WHEN f.ItemType = 'RFI' THEN 1 ELSE 0 END),
                      SUM(CASE WHEN f.ItemType = 'Submittal' THEN 1 ELSE 0 END)
               FROM fct_RfiSubmittal f
               JOIN dim_Trade  t ON t.TradeKey  = f.TradeKey
               JOIN dim_Status s ON s.StatusKey = f.StatusKey
               WHERE f.IsCritical AND s.IsOpen
               GROUP BY 1 ORDER BY 2 + 3 DESC, 1"""
        )
    ]
    open_rfis, open_subs, crit_open, avg_days = rows(
        """SELECT SUM(CASE WHEN f.ItemType = 'RFI' AND s.IsOpen THEN 1 ELSE 0 END),
                  SUM(CASE WHEN f.ItemType = 'Submittal' AND s.IsOpen THEN 1 ELSE 0 END),
                  SUM(CASE WHEN f.IsCritical AND s.IsOpen THEN 1 ELSE 0 END),
                  ROUND(AVG(CASE WHEN f.ItemType = 'RFI' THEN f.DaysOpen END), 1)
           FROM fct_RfiSubmittal f
           JOIN dim_Status s ON s.StatusKey = f.StatusKey"""
    )[0]

    payload = {
        "source": source,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "projects": [
            {"number": n, "name": nm}
            for n, nm in rows("SELECT ProjectNumber, ProjectName FROM dim_Project ORDER BY 1")
        ],
        "tiles": [
            {"label": "Open critical items", "value": crit_open or 0},
            {"label": "Open RFIs", "value": open_rfis or 0},
            {"label": "Open submittals", "value": open_subs or 0},
            {"label": "Avg RFI days open", "value": avg_days or 0},
        ],
        "by_trade": by_trade,
        "items": [
            {
                "number": n, "type": t, "trade": tr, "status": st,
                "is_open": bool(o), "is_critical": bool(c), "days_open": d,
            }
            for n, t, tr, st, o, c, d in rows(
                """SELECT f.ItemNumber, f.ItemType, t.TradeName, s.Label, s.IsOpen,
                          f.IsCritical, f.DaysOpen
                   FROM fct_RfiSubmittal f
                   JOIN dim_Trade  t ON t.TradeKey  = f.TradeKey
                   JOIN dim_Status s ON s.StatusKey = f.StatusKey
                   ORDER BY f.ItemType, f.ItemNumber"""
            )
        ],
        "data_quality": [
            {
                "severity": sev, "issue": issue, "count": n,
                "why": ISSUE_EXPLANATIONS.get(issue, ""),
            }
            for sev, issue, n in rows(
                "SELECT Severity, Issue, COUNT(*) FROM data_quality_log "
                "GROUP BY 1, 2 ORDER BY 1, 3 DESC"
            )
        ],
    }

    template = (HERE / "preview" / "template.html").read_text(encoding="utf-8")
    out = OUT_DIR / "preview.html"
    out.write_text(
        template.replace("/*__DATA__*/ null", json.dumps(payload, indent=2)),
        encoding="utf-8",
    )
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="pull from the Procore sandbox")
    parser.add_argument("--capture", action="store_true", help="--live plus refresh fixtures")
    args = parser.parse_args()

    live = args.live or args.capture
    if live and not os.environ.get("PROCORE_CLIENT_ID"):
        print(
            "PROCORE_CLIENT_ID is not set. Copy src/procore/config/settings.example.env "
            "to .env at the repo root and fill it in, or drop --live to use fixtures."
        )
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    db_path = OUT_DIR / "pipeline.duckdb"
    con = duckdb.connect(str(db_path))
    con.execute(COMPAT_MACROS)

    print(f"Source: {'Procore sandbox' if live else 'fixtures'}")
    tables = bronze_from_sandbox(args.capture) if live else bronze_from_fixtures()
    load_bronze(con, tables)

    print("\nTransform")
    run_sql(con)
    report(con)
    export(con)
    print(f"Preview      -> {write_preview(con, 'Procore sandbox' if live else 'fixtures')}")

    con.close()
    print(f"\nDuckDB file: {db_path}  (delete it to start clean)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
