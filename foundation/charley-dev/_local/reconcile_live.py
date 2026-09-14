"""Read-only live reconciliation suite. Run it after every publish.

    python reconcile_live.py                                   # production
    python reconcile_live.py --model-id <id> --qc-model-id <id> --lakehouse <gold lakehouse>

Turns the one-off reconciliations of 2026-09-14 (unmatched AR, AP cost, submittal dates,
render anomalies, Sage receipts) into ten repeatable checks. Nothing is written to Fabric:
DAX goes through validate_model.dax (partial-response safe) and SQL through the lakehouse
SQL analytics endpoint with the same SqlClient + az token access as validate_sage_live.ps1.

Writes _docs/live-reconciliation/<UTC timestamp>.json - aggregates, job numbers and invoice
record numbers only, never names or emails - prints a table, and exits 1 when any
ERROR-severity check FAILs or any check could not run.

Status per check: PASS, WARN (worth a look, does not fail the run), FAIL (ERROR severity),
ERROR (the check itself could not run - fails closed).
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCS = HERE.parent / "_docs"
OUT_DIR = DOCS / "live-reconciliation"
SAGE_PAYMENTS_EVIDENCE = DOCS / "sage-payments-evidence.json"
BRONZE = "CD_Bronze_Lakehouse"
CENT = 0.005


def result(status: str, summary: str, **detail) -> dict:
    return {"status": status, "summary": summary, "detail": detail}


# ---- Pure comparisons (unit-tested offline in tests/test_reconcile_live.py) ---------------

def cmp_ar_conservation(layers: dict[str, dict]) -> dict:
    """1 [ERROR] Every layer carries the same rows, billed, paid and balance to the cent."""
    names = list(layers)
    base = layers[names[0]]
    diffs = []
    for name in names[1:]:
        for key in ("rows", "billed", "paid", "balance"):
            a, b = base.get(key), layers[name].get(key)
            if a is None or b is None or abs(float(a) - float(b)) >= CENT:
                diffs.append(f"{key}: {names[0]}={a} {name}={b}")
    if diffs:
        return result("FAIL", "; ".join(diffs), layers=layers)
    return result("PASS", f"{base['rows']} invoices, billed {base['billed']:,.2f} equal across "
                  + " = ".join(names), layers=layers)


def cmp_unmatched_ar(rows: list[dict], previous: dict | None) -> dict:
    """2 [WARN] Unmatched AR by job; new jobs/invoices against the previous run.

    rows: [{"job", "invoice_id", "amount"}]. previous: the prior run's check detail, or None
    (first run: everything is new).
    """
    by_job: dict[str, dict] = {}
    for r in rows:
        j = by_job.setdefault(str(r["job"]), {"invoices": 0, "amount": 0.0})
        j["invoices"] += 1
        j["amount"] = round(j["amount"] + float(r["amount"] or 0), 2)
    ids = sorted({str(r["invoice_id"]) for r in rows}, key=lambda s: (len(s), s))
    prev_jobs = set((previous or {}).get("by_job", {}))
    prev_ids = set((previous or {}).get("invoice_ids", []))
    new_jobs = sorted(set(by_job) - prev_jobs, key=lambda s: (len(s), s))
    new_ids = [i for i in ids if i not in prev_ids]
    total = round(sum(j["amount"] for j in by_job.values()), 2)
    detail = dict(by_job=by_job, invoice_ids=ids, total_invoices=len(ids), total_amount=total,
                  new_jobs=new_jobs, new_invoice_ids=new_ids, previous_run=previous is not None)
    status = "WARN" if new_jobs or new_ids else "PASS"
    summary = f"{len(ids)} invoices / {len(by_job)} jobs / {total:,.2f} unmatched"
    if status == "WARN":
        summary += f"; new since previous run: jobs {new_jobs or '-'}, invoices {new_ids or '-'}"
    return result(status, summary, **detail)


def cmp_ar_receipts(mismatches: list[dict], documented: dict[int, float], orphan_receipts: int) -> dict:
    """3 [ERROR] Receipts per invoice equal header paid, except documented opening balances.

    mismatches: invoices where SUM(acrpmt.amount) != acrinv.amtpad, as
    {"recnum", "paid", "receipts"}. documented: {recnum: amtpad} pre-history opening balances
    with no receipt rows. A documented exception still excused only while it is unchanged.
    Orphan receipts or a drifted documented exception FAIL; any other mismatch WARNs.
    """
    excused, drifted, new = [], [], []
    for m in mismatches:
        rec, paid, receipts = int(m["recnum"]), float(m["paid"] or 0), float(m["receipts"] or 0)
        row = dict(recnum=rec, paid=round(paid, 2), receipts=round(receipts, 2),
                   difference=round(paid - receipts, 2))
        if rec in documented:
            ok = abs(receipts) < CENT and abs(paid - documented[rec]) < CENT
            (excused if ok else drifted).append(row)
        else:
            new.append(row)
    detail = dict(excused_opening_balances=excused, drifted_documented=drifted,
                  new_mismatches=new, orphan_receipts=orphan_receipts,
                  documented_recnums=sorted(documented))
    if orphan_receipts or drifted:
        return result("FAIL", f"{orphan_receipts} orphan receipts; documented exceptions changed: "
                      f"{[d['recnum'] for d in drifted]}", **detail)
    if new:
        amount = round(sum(n["difference"] for n in new), 2)
        return result("WARN", f"{len(new)} new paid/receipt mismatches, {amount:,.2f}", **detail)
    return result("PASS", f"receipts match paid; {len(excused)} documented opening balances excused",
                  **detail)


def ap_tolerance(ap: float, spent: float) -> float:
    return max(25000.0, 0.10 * max(abs(ap), abs(spent)))


def cmp_ap_cost(projects: list[dict], erp_only: list[dict]) -> dict:
    """4 [WARN] AP job cost vs Procore Spent To Date per mapped project, max($25k, 10%);
    ERP-only vendor cost > $5k (job + Sage vendor id with no Procore cost on the project)."""
    over = []
    for p in projects:
        ap, spent = float(p.get("ap") or 0), float(p.get("spent") or 0)
        if abs(ap - spent) > ap_tolerance(ap, spent):
            over.append(dict(job=str(p["job"]), ap=round(ap, 2), spent=round(spent, 2),
                             variance=round(ap - spent, 2)))
    big = [dict(job=str(e["job"]), sage_vendor_id=str(e["vendor"]), ap=round(float(e["ap"]), 2))
           for e in erp_only if float(e["ap"] or 0) > 5000]
    erp_total = round(sum(e["ap"] for e in big), 2)
    detail = dict(projects_checked=len(projects), over_tolerance=over,
                  erp_only_vendor_rows=len(big), erp_only_amount=erp_total, erp_only=big)
    if over or big:
        return result("WARN", f"{len(over)}/{len(projects)} projects outside tolerance; "
                      f"{len(big)} ERP-only job/vendor rows {erp_total:,.2f}", **detail)
    return result("PASS", f"{len(projects)} mapped projects within tolerance", **detail)


def cmp_submittals(closed_counted_open: int, negative_turnaround: int, median_days) -> dict:
    """5 [ERROR] closed-but-open = 0. [WARN] responded < created, median outside 1..365."""
    detail = dict(closed_counted_open=closed_counted_open, responded_before_created=negative_turnaround,
                  median_turnaround_days=median_days)
    warns = []
    if negative_turnaround:
        warns.append(f"{negative_turnaround} responded before created")
    if median_days is None or not 1 <= float(median_days) <= 365:
        warns.append(f"median turnaround {median_days} outside 1..365")
    if closed_counted_open:
        return result("FAIL", "; ".join([f"{closed_counted_open} closed submittals counted open"] + warns),
                      **detail)
    if warns:
        return result("WARN", "; ".join(warns), **detail)
    return result("PASS", f"median turnaround {median_days} days", **detail)


def cmp_carry_forward(month: str, pairs: dict[str, tuple]) -> dict:
    """6 [ERROR] A balance measure filtered to the latest complete month equals the same
    measure unfiltered over periods up to that month. pairs: {measure: (month, as_of)}."""
    bad = {m: dict(month=v[0], as_of=v[1]) for m, v in pairs.items()
           if v[0] is None or v[1] is None or abs(float(v[0]) - float(v[1])) >= CENT}
    detail = dict(month=month, values={m: dict(month=v[0], as_of=v[1]) for m, v in pairs.items()})
    if bad:
        return result("FAIL", f"{month}: " + "; ".join(
            f"{m} month={v['month']} vs as-of={v['as_of']}" for m, v in bad.items()), **detail)
    return result("PASS", f"{month}: balances carry forward", **detail)


def cmp_insurance(max_expiration: date | None, today: date, expired: int, total: int) -> dict:
    """7 [WARN] Latest certificate expiry in the past, or at least half expired."""
    share = round(expired / total, 4) if total else None
    detail = dict(max_expiration=str(max_expiration), certificates=total, expired=expired,
                  expired_share=share)
    stale = max_expiration is None or max_expiration < today
    if stale or (share is not None and share >= 0.5):
        return result("WARN", f"latest expiry {max_expiration}; {expired}/{total} expired", **detail)
    return result("PASS", f"latest expiry {max_expiration}; {expired}/{total} expired", **detail)


def cmp_freshness(runs: dict[str, dict], now: datetime, max_age_hours: float = 30) -> dict:
    """8 [ERROR] Both models show the same latest RunId with Status ok. [WARN] RunAt > 30h old.
    runs: {model: {"run_id", "status", "run_at": aware datetime or None}}."""
    ids = {r.get("run_id") for r in runs.values()}
    bad_status = [m for m, r in runs.items() if r.get("status") != "ok"]
    detail = {m: dict(run_id=r.get("run_id"), status=r.get("status"),
                      run_at=r["run_at"].isoformat() if r.get("run_at") else None)
              for m, r in runs.items()}
    if len(ids) != 1 or None in ids or bad_status:
        return result("FAIL", f"run ids {sorted(map(str, ids))}; not ok: {bad_status}", models=detail)
    ages = [(now - r["run_at"]).total_seconds() / 3600 for r in runs.values() if r.get("run_at")]
    age = max(ages) if len(ages) == len(runs) else None
    stale = age is None or age > max_age_hours
    age = None if age is None else round(age, 1)
    if stale:
        return result("WARN", f"run {ids.pop()} is {age}h old (> {max_age_hours}h)", models=detail,
                      age_hours=age)
    return result("PASS", f"run {ids.pop()} ok, {age}h old", models=detail, age_hours=age)


DIVISION = re.compile(r"^[0-9]{2}$")


def cmp_division(counts: dict) -> dict:
    """9 [ERROR] Every non-blank dim_CostCode[Division] is two digits. Blank is the
    UNASSIGNED / unparseable member by design and is reported, not failed."""
    bad = {str(k): v for k, v in counts.items() if k not in (None, "") and not DIVISION.match(str(k))}
    blank = sum(v for k, v in counts.items() if k in (None, ""))
    detail = dict(nonconforming=bad, nonconforming_codes=sum(bad.values()), blank_codes=blank,
                  distinct_divisions=len(counts))
    if bad:
        return result("FAIL", f"{len(bad)} division values ({sum(bad.values())} codes) not 2-digit: "
                      f"{sorted(bad, key=lambda s: (len(s), s))[:12]}", **detail)
    return result("PASS", f"all divisions 2-digit ({blank} blank codes)", **detail)


def cmp_blank_members(orphans: dict[str, int], trade: dict[str, tuple[int, int]]) -> dict:
    """10 [WARN] Fact rows landing on the (Blank) project member; blank trade share.
    orphans: {table: rows}. trade: {table: (blank rows, total rows)}."""
    hit = {t: n for t, n in orphans.items() if n}
    shares = {t: dict(blank=b, total=n, share=round(b / n, 4) if n else None) for t, (b, n) in trade.items()}
    detail = dict(blank_project_rows=hit, tables_checked=sum(n is not None for n in orphans.values()),
                  tables_skipped=sorted(t for t, n in orphans.items() if n is None), trade=shares)
    blank_trades = {t: s for t, s in shares.items() if s["blank"]}
    if hit or blank_trades:
        return result("WARN", f"(Blank) project rows {hit or '-'}; blank trade share " + ", ".join(
            f"{t} {s['share']:.0%}" for t, s in blank_trades.items()), **detail)
    return result("PASS", "no (Blank) project or trade members", **detail)


def latest_complete_month(today: date) -> date:
    return (today.replace(day=1) - timedelta(days=1)).replace(day=1)


def previous_detail(check_id: str, model_id: str, out_dir: Path = OUT_DIR) -> dict | None:
    """The given check's detail from the newest earlier run against the same model."""
    for path in sorted(out_dir.glob("*.json"), reverse=True):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if doc.get("target", {}).get("model_id") != model_id:
            continue
        for c in doc.get("checks", []):
            if c.get("id") == check_id and c.get("status") != "ERROR":
                return c.get("detail")
    return None


# ---- Live access (read-only) ---------------------------------------------------------------

# Same access path as validate_sage_live.ps1: System.Data.SqlClient + an az database token.
PS_SQL = r"""
$ErrorActionPreference = 'Stop'
$q = [Console]::In.ReadToEnd()
$c = [System.Data.SqlClient.SqlConnection]::new("Server=tcp:$env:RL_SERVER,1433;Initial Catalog=$env:RL_DB;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;")
$c.AccessToken = $env:RL_TOKEN
$c.Open()
try {
  $cmd = $c.CreateCommand(); $cmd.CommandText = $q; $cmd.CommandTimeout = 300
  $r = $cmd.ExecuteReader(); $rows = New-Object System.Collections.ArrayList
  while ($r.Read()) { $o = [ordered]@{}; for ($i = 0; $i -lt $r.FieldCount; $i++) {
    $o[$r.GetName($i)] = if ($r.IsDBNull($i)) { $null } else { $r.GetValue($i) } }; [void]$rows.Add($o) }
} finally { $c.Close() }
[Console]::Out.Write((ConvertTo-Json -InputObject @($rows) -Depth 3 -Compress))
"""

READ_ONLY = re.compile(r"^\s*(select|with)\b", re.I)


class Live:
    def __init__(self, args):
        import deploy as dp
        import validate_model as vm
        self.vm, self.dp = vm, dp
        ids = json.loads((HERE / "fabric_ids.json").read_text())
        self.server = ids["CD_Gold_Lakehouse"]["sqlEndpoint"]
        self.gold, self.silver = args.lakehouse, args.silver_lakehouse
        self.pbi = vm.pbi_token()
        if args.model_id and args.qc_model_id:
            self.models = {"Affect Project Report": args.model_id, "Project Quality Plan": args.qc_model_id}
        else:
            import deploy_publish
            self.models = dict(deploy_publish.resolve_models(self.pbi))
            if args.model_id:
                self.models["Affect Project Report"] = args.model_id
            if args.qc_model_id:
                self.models["Project Quality Plan"] = args.qc_model_id
        self.apr, self.qc = self.models["Affect Project Report"], self.models["Project Quality Plan"]
        tok = subprocess.run([dp.az_path(), "account", "get-access-token", "--resource",
                              "https://database.windows.net/", "--query", "accessToken", "-o", "tsv"],
                             capture_output=True, text=True)
        if tok.returncode != 0:
            raise dp.FabricError(f"database token failed: {tok.stderr.strip()[:200]}")
        self.sql_token = tok.stdout.strip()

    def dax(self, model_id: str, query: str) -> list[dict]:
        rows = self.vm.dax(model_id, self.pbi, query)
        # "[n]" and "table[col]" -> "n" / "col"
        return [{k.rsplit("[", 1)[-1].rstrip("]"): v for k, v in r.items()} for r in rows]

    def sql(self, query: str) -> list[dict]:
        if not READ_ONLY.match(query) or re.search(r"\b(insert|update|delete|merge|drop|create|alter|exec)\b", query, re.I):
            raise ValueError("reconcile_live runs SELECT/WITH only")
        env = dict(os.environ, RL_SERVER=self.server, RL_DB=self.gold, RL_TOKEN=self.sql_token)
        run = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand",
             base64.b64encode(PS_SQL.encode("utf-16-le")).decode()],
            input=query, capture_output=True, text=True, env=env, timeout=600)
        if run.returncode != 0:
            raise RuntimeError(f"SQL failed: {run.stderr.strip()[:600]}")
        return json.loads(run.stdout or "[]")

    # -- one gather per check; each returns the comparison result --

    def c1(self):
        agg = "COUNT(*) AS rows, SUM({b}) AS billed, SUM({p}) AS paid, SUM({bal}) AS balance"
        bronze = self.sql(f"SELECT {agg.format(b='COALESCE(NULLIF(invamt,0), amtpad+invbal)', p='amtpad', bal='invbal')} "
                          f"FROM {BRONZE}.dbo.cd_bronze_sage_acrinv")[0]
        silver = self.sql(f"SELECT {agg.format(b='invoice_total', p='amount_paid', bal='invoice_balance')} "
                          f"FROM {self.silver}.dbo.cd_silver_sage_ar_invoices")[0]
        model = self.dax(self.apr, 'EVALUATE ROW("rows", COUNTROWS(fct_Invoice), "billed", SUM(fct_Invoice[Amount]), '
                         '"paid", SUM(fct_Invoice[AmountPaid]), "balance", SUM(fct_Invoice[Balance]))')[0]
        rnd = lambda d: {k: (round(float(v), 2) if k != "rows" and v is not None else v) for k, v in d.items()}
        return cmp_ar_conservation({"bronze_acrinv": rnd(bronze), "silver_ar_invoices": rnd(silver),
                                    "model_fct_Invoice": rnd(model)})

    def c2(self):
        rows = self.dax(self.apr, 'EVALUATE SUMMARIZECOLUMNS(fct_Invoice[SageJobNumber], fct_Invoice[InvoiceID], '
                        'FILTER(ALL(fct_Invoice[HasUnmatchedProject]), fct_Invoice[HasUnmatchedProject] = TRUE()), '
                        '"amount", SUM(fct_Invoice[Amount]))')
        return cmp_unmatched_ar([dict(job=r["SageJobNumber"], invoice_id=r["InvoiceID"], amount=r["amount"]) for r in rows],
                                previous_detail("2", self.apr))

    def c3(self):
        documented = {int(d["invoice_recnum"]): float(d["amtpad"]) for d in json.loads(
            SAGE_PAYMENTS_EVIDENCE.read_text(encoding="utf-8"))["reconciliation_receipts_vs_acrinv_amtpad"]["mismatch_detail"]}
        mismatches = self.sql(f"""
WITH r AS (SELECT _idref, SUM(amount) AS receipts FROM {BRONZE}.dbo.cd_bronze_sage_acrpmt GROUP BY _idref)
SELECT i.recnum, i.amtpad AS paid, COALESCE(r.receipts, 0) AS receipts
FROM {BRONZE}.dbo.cd_bronze_sage_acrinv i LEFT JOIN r ON r._idref = i._idnum
WHERE ABS(COALESCE(i.amtpad, 0) - COALESCE(r.receipts, 0)) >= 0.005""")
        orphans = self.sql(f"""
SELECT COUNT(*) AS n FROM {BRONZE}.dbo.cd_bronze_sage_acrpmt p
LEFT JOIN {BRONZE}.dbo.cd_bronze_sage_acrinv i ON p._idref = i._idnum WHERE i._idnum IS NULL""")[0]["n"]
        return cmp_ar_receipts(mismatches, documented, orphans)

    def c4(self):
        s, g = self.silver, self.gold
        # Job cost = job-coded AP lines on GL 50000-50999 (ap-cost-reconciliation.json IsJobCost).
        jobcost = "sage_project_id IS NOT NULL AND TRY_CAST(ledger_account AS int) BETWEEN 50000 AND 50999"
        projects = self.sql(f"""
WITH ap AS (SELECT sage_project_id AS job, SUM(line_total) AS ap FROM {s}.dbo.cd_silver_sage_ap_lines
            WHERE {jobcost} GROUP BY sage_project_id),
b AS (SELECT ProjectKey, SpentToDate, SnapshotDate, MAX(SnapshotDate) OVER (PARTITION BY ProjectKey) AS latest
      FROM {g}.dbo.fct_budgetline),
spent AS (SELECT ProjectKey, SUM(SpentToDate) AS spent FROM b WHERE SnapshotDate = latest GROUP BY ProjectKey)
SELECT p.SageJobNumber AS job, ap.ap, sp.spent
FROM {g}.dbo.dim_project p LEFT JOIN ap ON ap.job = p.SageJobNumber LEFT JOIN spent sp ON sp.ProjectKey = p.ProjectKey
WHERE p.SageJobNumber IS NOT NULL""")
        # Vendor match as in the evidence: Sage vendor recnum = Procore vendor origin_code.
        erp_only = self.sql(f"""
WITH pv AS (SELECT DISTINCT JSON_VALUE(payload, '$.id') AS procore_vendor_id, JSON_VALUE(payload, '$.origin_code') AS origin_code
            FROM {BRONZE}.dbo.cd_bronze_procore_vendors WHERE ISJSON(payload) = 1),
pc AS (SELECT project_id, vendor_id, SUM(COALESCE(total_requisitioned, 0)) AS amt FROM {s}.dbo.cd_silver_commitments GROUP BY project_id, vendor_id
       UNION ALL SELECT ProjectKey, VendorKey, SUM(COALESCE(GrandTotal, 0)) FROM {g}.dbo.fct_directcost GROUP BY ProjectKey, VendorKey),
av AS (SELECT sage_project_id AS job, sage_vendor_id AS vendor, SUM(line_total) AS ap FROM {s}.dbo.cd_silver_sage_ap_lines
       WHERE {jobcost} GROUP BY sage_project_id, sage_vendor_id)
SELECT a.job, a.vendor, a.ap FROM av a JOIN {g}.dbo.dim_project p ON p.SageJobNumber = a.job
WHERE a.ap > 5000 AND NOT EXISTS (SELECT 1 FROM pv JOIN pc ON pc.vendor_id = pv.procore_vendor_id AND pc.project_id = p.ProjectKey
                                  WHERE pv.origin_code = a.vendor AND pc.amt > 0)""")
        return cmp_ap_cost(projects, erp_only)

    def c5(self):
        sub = 'fct_RfiSubmittal[ItemType] = "Submittal"'
        answered = f'{sub} && NOT ISBLANK(fct_RfiSubmittal[RespondedDate]) && NOT ISBLANK(fct_RfiSubmittal[CreatedDate])'
        # Procore submittal status categories: only Draft and Open are not closed.
        r = self.dax(self.apr, f'''EVALUATE ROW(
 "closed_open", COALESCE(CALCULATE(COUNTROWS(fct_RfiSubmittal), {sub}, fct_RfiSubmittal[IsOpen] = TRUE(),
                NOT fct_RfiSubmittal[StatusLabel] IN {{"Open", "Draft"}}), 0),
 "negative", COALESCE(COUNTROWS(FILTER(fct_RfiSubmittal, {answered} && fct_RfiSubmittal[RespondedDate] < fct_RfiSubmittal[CreatedDate])), 0),
 "median", MEDIANX(FILTER(fct_RfiSubmittal, {answered}), INT(fct_RfiSubmittal[RespondedDate] - fct_RfiSubmittal[CreatedDate])))''')[0]
        return cmp_submittals(r["closed_open"], r["negative"], r["median"])

    def c6(self):
        m = latest_complete_month(self.now.date())
        dm = f"DATE({m.year},{m.month},1)"
        month = f"dim_Date[Date] >= {dm}, dim_Date[Date] <= EOMONTH({dm}, 0)"
        asof = f"REMOVEFILTERS(dim_Date), fct_FinancialPeriod[MonthStart] <= {dm}"
        measures = ["Current Contract", "Pending Change Orders"]
        cols = ", ".join(f'"m{i}", CALCULATE([{n}], {month}), "a{i}", CALCULATE([{n}], {asof})'
                         for i, n in enumerate(measures))
        r = self.dax(self.apr, f"EVALUATE ROW({cols})")[0]
        return cmp_carry_forward(m.isoformat()[:7], {n: (r[f"m{i}"], r[f"a{i}"]) for i, n in enumerate(measures)})

    def c7(self):
        r = self.dax(self.apr, 'EVALUATE ROW("maxexp", MAX(fct_VendorInsurance[ExpirationDate]), '
                     '"n", COUNTROWS(fct_VendorInsurance), "expired", CALCULATE(COUNTROWS(fct_VendorInsurance), '
                     'fct_VendorInsurance[ExpiryStatus] = "Expired"))')[0]
        maxexp = date.fromisoformat(r["maxexp"][:10]) if r["maxexp"] else None
        return cmp_insurance(maxexp, self.now.date(), r["expired"] or 0, r["n"] or 0)

    def c8(self):
        q = ('EVALUATE VAR Last = MAX(meta_PipelineRun[RunAt]) RETURN ROW('
             '"RunId", CALCULATE(MAX(meta_PipelineRun[RunId]), meta_PipelineRun[RunAt] = Last), '
             '"Status", CALCULATE(MIN(meta_PipelineRun[Status]), meta_PipelineRun[RunAt] = Last), "RunAt", Last)')
        runs = {}
        for name, mid in self.models.items():
            r = self.dax(mid, q)[0]
            at = datetime.fromisoformat(r["RunAt"]).replace(tzinfo=timezone.utc) if r["RunAt"] else None
            runs[name] = dict(run_id=r["RunId"], status=r["Status"], run_at=at)  # RunAt is recorded in UTC
        return cmp_freshness(runs, self.now)

    def c9(self):
        rows = self.dax(self.apr, 'EVALUATE SUMMARIZECOLUMNS(dim_CostCode[Division], "n", COUNTROWS(dim_CostCode))')
        return cmp_division({r["Division"]: r["n"] for r in rows})

    def c10(self):
        import deploy_model as dm
        blank = "FILTER(ALL(dim_Project), ISBLANK(dim_Project[ProjectKey]))"
        apr_tables = sorted({f for f, _, d, _ in dm.RELATIONSHIPS if d == "dim_Project"})
        orphans = {}
        for model, tables in ((self.apr, apr_tables), (self.qc, ["fct_QcNcr", "fct_QcPunch", "fct_QcSubmittal"])):
            for t in tables:
                orphans[t] = self.dax(model, f'EVALUATE ROW("n", COALESCE(CALCULATE(COUNTROWS({t}), {blank}), 0))')[0]["n"]
        trade = {}
        r = self.dax(self.apr, 'EVALUATE ROW("b", COALESCE(CALCULATE(COUNTROWS(fct_QualityItem), '
                     'ISBLANK(fct_QualityItem[Trade]) || fct_QualityItem[Trade] = ""), 0), "n", COUNTROWS(fct_QualityItem))')[0]
        trade["fct_QualityItem.Trade"] = (r["b"], r["n"] or 0)
        for t in ("fct_QcPunch", "fct_QcNcr"):
            r = self.dax(self.qc, f'EVALUATE ROW("b", COALESCE(CALCULATE(COUNTROWS({t}), ISBLANK({t}[TradeKey])), 0), "n", COUNTROWS({t}))')[0]
            trade[f"{t}.TradeKey"] = (r["b"], r["n"] or 0)
        return cmp_blank_members(orphans, trade)


CHECKS = [
    ("1", "ERROR", "AR conservation bronze=silver=model", "c1"),
    ("2", "WARN", "Unmatched AR by job", "c2"),
    ("3", "ERROR", "AR receipts vs paid", "c3"),
    ("4", "WARN", "AP job cost vs Procore spent", "c4"),
    ("5", "ERROR", "Submittal sanity", "c5"),
    ("6", "ERROR", "Balance measures carry forward", "c6"),
    ("7", "WARN", "Insurance expiry", "c7"),
    ("8", "ERROR", "Model freshness", "c8"),
    ("9", "ERROR", "Division format", "c9"),
    ("10", "WARN", "(Blank) members", "c10"),
]


def table(checks: list[dict]) -> str:
    lines = [f"{'#':>2}  {'SEV':5}  {'STATUS':6}  {'CHECK':36}  SUMMARY"]
    for c in checks:
        lines.append(f"{c['id']:>2}  {c['severity']:5}  {c['status']:6}  {c['name'][:36]:36}  {c['summary'][:150]}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model-id", help="Affect Project Report dataset id (default: production by name)")
    ap.add_argument("--qc-model-id", help="Project Quality Plan dataset id (default: production by name)")
    ap.add_argument("--lakehouse", default="CD_Gold_Lakehouse", help="gold lakehouse SQL database")
    ap.add_argument("--silver-lakehouse", default="CD_Silver_Lakehouse")
    ap.add_argument("--only", help="comma-separated check ids")
    args = ap.parse_args()

    sys.path.insert(0, str(HERE))
    live = Live(args)
    now = live.now = datetime.now(timezone.utc)
    wanted = set(args.only.split(",")) if args.only else None
    checks = []
    for cid, severity, name, method in CHECKS:
        if wanted and cid not in wanted:
            continue
        try:
            res = getattr(live, method)()
        except Exception as exc:  # fail closed: a check that cannot run is not a pass
            res = result("ERROR", f"check could not run: {str(exc)[:300]}")
        if severity == "WARN" and res["status"] == "FAIL":
            res["status"] = "WARN"
        checks.append(dict(id=cid, severity=severity, name=name, **res))
        print(f"  {cid:>2} {res['status']}", flush=True)

    doc = dict(run_at=now.isoformat(), target=dict(model_id=live.apr, qc_model_id=live.qc,
               gold_lakehouse=args.lakehouse, silver_lakehouse=args.silver_lakehouse,
               bronze_lakehouse=BRONZE), checks=checks,
               failed=[c["id"] for c in checks if c["status"] in ("FAIL", "ERROR")],
               warned=[c["id"] for c in checks if c["status"] == "WARN"])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{now.strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(doc, indent=1, default=str), encoding="utf-8")
    print("\n" + table(checks))
    print(f"\nwrote {out}")
    return 1 if doc["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
