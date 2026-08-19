# D3 — Sage 100 Ingestion Pipeline

**Status:** 🔵 Built and deployed — blocked on one gateway permission grant | **Phase:** 1 — Foundation | **Billing:** Scoped from D1 review (per-solution block) | **Target:** Runs the day the grant lands

> **Built, committed and deployed.** `CD_Sage_Ingest` is live in the Fabric workspace `Build`, folder `charley-dev`, bound to gateway `1e798beb` and datasource `835e72c8`, writing to `CD_Bronze_Lakehouse`. Eight tables, including the two AR/AP **line** tables (`arivln`, `apivln`) whose pointing columns the existing dataflow explicitly removes — which is where retainage and cost codes live.
>
> **It is inert, not missing.** The first run failed in about five seconds, too fast to be a query: `cforey-c@affect-group.com` cannot see any gateway or connection in the tenant, so the dataflow asks to run through a gateway its runner has no rights on.
>
> **The ask is one line.** Whoever administers the on-premises data gateway grants `cforey-c@affect-group.com` the **"Can use"** permission on connection `nc-affect-1\sage100con;Affect Group`, in *Manage connections and gateways*. No subscription, no vault, no code change — Affect already uses this connection, so nothing new is built. The Sage database is managed by an outside consultant, so the ask may route through them. Detail: [`sage-ingestion.md`](../foundation/charley-dev/_docs/sage-ingestion.md).

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
- [ ] **Grant `cforey-c@affect-group.com` *Can use* on `nc-affect-1\sage100con;Affect Group`** — Affect / their Sage consultant
- [ ] Run it, then write `sql/silver/20_sage_silver.sql` to type and validate the eight tables
- [ ] Point `sv_ar_invoices` at `cd_silver_*` (it still reads the existing warehouse, which keeps `fct_Invoice` at 117 rows rather than zero while this is blocked)
- [ ] Settle open question 4 (retainage) with the line data in hand
- [ ] Schedule + alerting
- [ ] Repoint/plan migration of existing Power BI live queries to Lakehouse data
- [ ] Document for Rebecca (pattern reusable for future sources)

## Acceptance criteria
- Required Sage tables land in the Lakehouse on schedule
- Power BI no longer depends on live SQL queries for the core reports
- Job/cost data reconciles with Sage source (spot-check totals)

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
