"""Regenerate tests/observed_values.json from the lakehouse SQL endpoint. Read-only.

    python refresh_observed_values.py            # dry run: print every query, touch nothing
    python refresh_observed_values.py --apply    # run them and rewrite the catalogue

Run when capacity allows - it is a GROUP BY per field over silver (and bronze where silver
does not carry the raw value), nothing more. SELECT only, through the same SqlClient + az
token path reconcile_live.py uses. Nothing is written to Fabric.

Output is counts per distinct value, never names or ids. After --apply, run
`python run_tests.py`: any new value that the SQL does not map, or that no fixture carries,
fails test_observed_values and says what to do.

Silver columns are parsed in Spark, so they are complete. The few bronze JSON_VALUE reads
are cut at the endpoint's 8,000-character string limit on large payloads - their provenance
says so.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from reconcile_live import BRONZE, PS_SQL, READ_ONLY  # noqa: E402

CATALOGUE = HERE / "tests" / "observed_values.json"
SILVER = "CD_Silver_Lakehouse"
UNKNOWN = "unknown - capture next time capacity allows"

# field -> (database, table, value expression). Fields absent here keep their entry as is.
QUERIES = {
    "prime_change_order.status": (SILVER, "cd_silver_prime_change_orders", "status"),
    "potential_change_order.status": (BRONZE, "cd_bronze_procore_potential_change_orders", "JSON_VALUE(payload, '$.status')"),
    "submittal.status_name": (SILVER, "cd_silver_submittals", "status_label"),
    "submittal.status_category": (SILVER, "cd_silver_submittals", "status_category"),
    "rfi.status": (SILVER, "cd_silver_rfis", "status_label"),
    "billing.status_label": (SILVER, "cd_silver_billing", "status_label"),
    "commitment.status_label": (SILVER, "cd_silver_commitments", "status_label"),
    "commitment_line.holder_type": (SILVER, "cd_silver_commitment_lines", "holder_type"),
    "direct_cost_line.holder_type": (SILVER, "cd_silver_direct_cost_lines", "holder_type"),
    "direct_cost.cost_type": (SILVER, "cd_silver_direct_costs", "cost_type"),
    "direct_cost.status_label": (SILVER, "cd_silver_direct_costs", "status_label"),
    "observation.status_label": (SILVER, "cd_silver_observations", "status_label"),
    "observation.observation_type": (SILVER, "cd_silver_observations", "observation_type"),
    "observation.trade": (SILVER, "cd_silver_observations", "trade"),
    "punch_item.status_label": (SILVER, "cd_silver_punch_items", "status_label"),
    "punch_item.workflow_status": (SILVER, "cd_silver_punch_items", "workflow_status"),
    "punch_item.punch_item_type": (SILVER, "cd_silver_punch_items", "punch_item_type"),
    "punch_item.trade": (SILVER, "cd_silver_punch_items", "trade"),
    "vendor_insurance.insurance_type": (SILVER, "cd_silver_vendor_insurance", "insurance_type"),
    "vendor_insurance.status_label": (SILVER, "cd_silver_vendor_insurance", "status_label"),
    "manpower_log.status": (BRONZE, "cd_bronze_procore_manpower_logs", "JSON_VALUE(payload, '$.status')"),
    "manpower_log.trade": (BRONZE, "cd_bronze_procore_manpower_logs", "JSON_VALUE(payload, '$.trade.name')"),
    "outbuild_activity.activity_type": (SILVER, "cd_silver_outbuild_activities", "activity_type"),
    # Three Sage tables share the field; the table is kept in the value so they stay apart.
    "sage.status_code": (SILVER, None, None),
    # Bronze, not silver: silver drops the rejected rows, and the invalid values are the point.
    "manual.win_type": (BRONZE, "cd_bronze_man_wins", "WinType"),
    "manual.impact_code": (BRONZE, "cd_bronze_man_risks", "ImpactCode"),
    "manual.stage": (BRONZE, "cd_bronze_man_job_register", "Stage"),
    "manual.gate_type": (BRONZE, "cd_bronze_man_qc_gate", "GateType"),
}

SAGE_SQL = " UNION ALL ".join(
    f"SELECT CONCAT('{t}:', CAST(status_code AS VARCHAR(20))) AS v, COUNT_BIG(*) AS n "
    f"FROM {SILVER}.dbo.{t} GROUP BY status_code"
    for t in ("cd_silver_sage_jobs", "cd_silver_sage_ar_invoices", "cd_silver_sage_ap_invoices"))


def query_for(field: str) -> str:
    db, table, expr = QUERIES[field]
    if field == "sage.status_code":
        return SAGE_SQL
    return f"SELECT {expr} AS v, COUNT_BIG(*) AS n FROM {db}.dbo.{table} GROUP BY {expr}"


def run_sql(server: str, token: str, db: str, sql: str) -> list[dict]:
    assert READ_ONLY.match(sql), sql
    env = dict(os.environ, RL_SERVER=server, RL_DB=db, RL_TOKEN=token)
    run = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand",
         base64.b64encode(PS_SQL.encode("utf-16-le")).decode()],
        input=sql, capture_output=True, text=True, env=env, timeout=600)
    if run.returncode != 0:
        raise RuntimeError(run.stderr.strip()[:600])
    return json.loads(run.stdout or "[]")


def apply_rows(entry: dict, rows: list[dict], field: str, today: str) -> None:
    db, table, expr = QUERIES[field]
    values = {str(r["v"]): int(r["n"]) for r in rows if r["v"] is not None}
    entry["values"] = dict(sorted(values.items(), key=lambda kv: -kv[1]))
    entry["null_count"] = sum(int(r["n"]) for r in rows if r["v"] is None)
    entry["status"] = "observed" if rows else UNKNOWN
    note = " (JSON_VALUE: payloads over 8,000 chars read as NULL)" if expr and "JSON_VALUE" in expr else ""
    entry["provenance"] = [{"file": f"SQL endpoint {db}.dbo.{table or 'cd_silver_sage_*'} via "
                                    f"_local/refresh_observed_values.py{note}", "captured": today}]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="run the queries and rewrite the catalogue")
    ap.add_argument("--only", help="comma-separated field names")
    args = ap.parse_args()

    doc = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    fields = [f for f in QUERIES if not args.only or f in args.only.split(",")]
    missing = [f for f in fields if f not in doc["fields"]]
    if missing:
        raise SystemExit(f"not in the catalogue (add an entry first): {missing}")

    if not args.apply:
        for f in fields:
            print(f"-- {f}\n{query_for(f)};\n")
        print(f"dry run: {len(fields)} read-only queries, nothing executed. --apply to run them.")
        return 0

    import deploy as dp
    ids = json.loads((HERE / "fabric_ids.json").read_text())
    server = ids["CD_Gold_Lakehouse"]["sqlEndpoint"]
    tok = subprocess.run([dp.az_path(), "account", "get-access-token", "--resource",
                          "https://database.windows.net/", "--query", "accessToken", "-o", "tsv"],
                         capture_output=True, text=True)
    if tok.returncode != 0:
        raise SystemExit(f"database token failed: {tok.stderr.strip()[:200]}")
    today, failed = date.today().isoformat(), []
    for f in fields:
        try:
            rows = run_sql(server, tok.stdout.strip(), QUERIES[f][0], query_for(f))
        except Exception as exc:  # keep the old evidence rather than blanking a field
            failed.append(f)
            print(f"  {f}: FAILED, entry left unchanged ({str(exc)[:200]})")
            continue
        apply_rows(doc["fields"][f], rows, f, today)
        print(f"  {f}: {len(doc['fields'][f]['values'])} distinct")
    CATALOGUE.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {CATALOGUE} - now run run_tests.py")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
