# D3 — Sage 100 Ingestion Pipeline

**Status:** 🟢 **Live end to end** | **Phase:** 1 — Foundation | **Billing:** ~2 hrs in Phase 0 + ~2 hrs on 2026-08-25 | **Target:** ✅ Met

> **LIVE as of 2026-08-25.** `CD_Sage_Ingest` completed at 09:25 UTC — the first successful run since it was built on Aug 2 — and all 8 tables land in `CD_Bronze_Lakehouse`: **4,027 rows**, including `arivln` and `apivln`, the AR/AP **line tables the existing dataflow strips the pointer columns for and which no one at Affect had ever queried**. A new silver layer (`26_sage_silver.sql`, 5 tables) feeds gold, and `fct_Invoice` moved **122 → 148 rows** and **$23.70M → $25.61M**, with the latest invoice going Jul 31 → **Aug 31**. Detail: [`_docs/sage-ingestion.md`](../foundation/charley-dev/_docs/sage-ingestion.md).

## Objective
Sage 100 Contractor data lands in the Fabric Lakehouse on a schedule, replacing the current live SQL queries from Power BI, so accounting data joins the warehouse alongside Procore.

## Scope
**In:** Ingestion pipeline from the read-only SQL Server connection into Lakehouse raw tables; scheduling; history/snapshots where needed (e.g., AR/AP aging over time); documentation.
**Out:** Curated modeling (D4), dashboard (D5).

## Key data
Confirm in D1, likely: jobs, job cost detail/summary, cost codes & cost types, AP invoices, AR invoices/receivables, vendors, payroll summaries, GL as needed. Job number ↔ Procore project mapping is critical.

## Integration approach
Sage 100 SQL Server (read-only; likely on-prem → **on-premises data gateway** or mirrored/pipeline copy into Fabric) → Lakehouse raw tables. Incremental where change-detection columns exist; snapshot tables for balances that need history. Scheduled via Fabric Data Pipeline.

## Tasks
- [x] Inventory available tables/views and row volumes (D1 output)
- [x] Confirm connectivity path — on-premises data gateway, the same one `Build_Sage_Test` already uses
- [x] Design landing schema + load strategy — land raw, shape in `sql/silver/`, so every transform is diffable and testable offline
- [x] Build the dataflow — 8 queries, `DefaultDestination` → `CD_Bronze_Lakehouse`
- [x] Deploy it — live in the `charley-dev` folder; the definition reads back from Fabric exactly as committed
- [x] ~~Grant *Can use* on the gateway connection~~ — **withdrawn 2026-08-25 as a mis-diagnosis.** Rebecca and IT already held it; the dataflow ran as an account that did not. The real fault was the Lakehouse destination being routed through the on-premises gateway
- [x] **Run it** — completed 09:25 UTC 2026-08-25, all 8 tables, 4,027 rows
- [x] **Silver transform** — `26_sage_silver.sql`, five typed tables, 62 offline checks
- [x] **Point `sv_ar_invoices` at `cd_silver_*`** — `fct_Invoice` 122 → **148 rows / $25.61M**
- [x] **Settle open question 4 (retainage)** — Sage holds none anywhere; the real figures come from Procore progress billing and were already in `fct_Billing`
- [x] **Schedule** — `Ingest Sage` runs in `CD_Master_Pipeline`, parallel to Procore extraction, ahead of Bronze To Silver
- [ ] Alerting — the DQ gate fails the run, but nothing emails a person yet (shared gap with every other subject area)
- [ ] Repoint `fct_BudgetLine`'s invoiced column onto `apivln` — the actual-cost-by-account prize, and a real change to a live report
- [ ] Document for Rebecca (pattern reusable for future sources)

## Acceptance criteria
- [x] Required Sage tables land in the Lakehouse on schedule — 8 of 8, nightly
- [x] Power BI no longer depends on live SQL queries for the core reports — `sv_ar_invoices` reads our own silver, not Rebecca's `Revenue_AllTime`
- [x] Job/cost data reconciles with the Sage source — **AR $25,613,659.66 and AP $15,509,381.78 tie to the cent** between two independent derivations (header paid + outstanding, and the sum of the line detail). `jobnum → actrec.recnum` orphans 0 of 148

## Files & resources
- [`sage-ingestion.md`](../foundation/charley-dev/_docs/sage-ingestion.md) — the dataflow, why `arivln`/`apivln` matter, and what is left
- `foundation/charley-dev/01-ingestion/Sage/CD_Sage_Ingest.Dataflow` — the committed definition

## Log
| Date | Note |
|---|---|
| 2026-08-02 | Established that Sage is **not** blocked on Key Vault or on an Azure subscription. Sage 100 is on-premises; the credential lives in the gateway connection's configuration, not in any notebook (recorded as F3 in `security-findings.md`). Conflating the two asks had been costing the one that could have been done weeks earlier. |
| 2026-08-03 | **Deployed.** First run failed in 5 seconds — `GET /v1/gateways` and `GET /v1/connections` both return empty for our identity, and `GET /v1/gateways/1e798beb-…` returns 404. The gateway demonstrably exists (`Build_Sage_Test` uses it); this identity cannot see it. Leaving the failed dataflow deployed is deliberate: it is correct, inert until run, and it turns the remaining work into one grant plus one refresh. |
| 2026-08-11 | Rebecca raising the gateway grant with IT support, alongside the Key Vault ask. |
| 2026-08-19 | Still blocked on the same single grant. Verified live that the dataflow **is** deployed and present in the `charley-dev` folder — documentation that said "defined in the repo, not deployed" was stale and has been corrected. |
| 2026-08-25 | **LIVE.** Ran at 09:25 UTC, 3m55s, all 8 tables, **4,027 rows**. Three findings the run itself produced. (1) **The blocker was ours.** Rebecca and IT already held *Can use* on the datasource — a Dataflow Gen2 runs as its OWNER, and we had deployed it owned by an account with no gateway rights, then reported the failure as a grant Affect was withholding. (2) **The real fault was the destination, not the source.** `gatewayObjectId` sits at the dataflow level and Power Query applies it to *every* connection, so Fabric was asking a server in Affect's office to authenticate to OneLake. Fixed by re-adding the data destination with the gateway set to `(none)` — a dropdown that only appears when the destination is added from scratch. (3) **`invamt` is zero on all 1,019 invoices.** The obvious "invoice total" column is not populated by this company; the total is paid + outstanding, which reconciles **to the cent** against the line tables on both AR and AP. Trusting it would have published $0 billed with total confidence. Also found the documented join key `invrec` orphans **every** line row — the real key is `_idref`. |
| 2026-08-19 (evening) | **Now the only access grant left on the engagement.** The Outbuild token arrived and the Key Vault ask was withdrawn as having named the wrong vault, so this is the last one. Separately: the handoff document's database name `ABMI` is **wrong** and was not changed — `Affect Group`, which `CD_Sage_Ingest` already queries, resolves to 15 of the 16 real projects and $22.5M of AR. |
