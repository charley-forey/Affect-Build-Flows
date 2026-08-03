# D3 — Sage 100 Ingestion Pipeline

**Status:** 🔵 **Built & deployed — blocked on one permission grant** | **Phase:** 1 — Foundation | **Billing:** ~2 hrs in Phase 0; silver transforms to follow | **Target:** Unblocks same day the grant lands

> **`CD_Sage_Ingest` is live in the `charley-dev` folder**, wired to the on-prem gateway Affect already uses, writing to `CD_Bronze`. It pulls 8 tables — including `arivln` and `apivln`, the AR/AP **line** tables the existing dataflow explicitly discards, which is where cost codes and the real retainage live. (Header `retain` is **$0 across all 940 invoices**; a header-sourced report shows zero retainage silently.)
>
> **The one remaining ask:** grant `cforey-c@affect-group.com` **"Can use"** on connection `nc-affect-1\sage100con;Affect Group`. The identity currently cannot see any gateway in the tenant, so the first run failed in 5 seconds before reaching Sage. No subscription, no vault, no code change. Detail: [`_docs/sage-ingestion.md`](../foundation/charley-dev/_docs/sage-ingestion.md).

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
- [ ] Inventory available tables/views and row volumes (D1 output)
- [ ] Confirm connectivity path (gateway vs other) from Fabric to the SQL Server
- [ ] Design landing schema + load strategy (incremental vs full vs snapshot per table)
- [ ] Build and test pipeline
- [ ] Schedule + alerting
- [ ] Repoint/plan migration of existing Power BI live queries to Lakehouse data
- [ ] Document for Rebecca (pattern reusable for future sources)

## Acceptance criteria
- Required Sage tables land in the Lakehouse on schedule
- Power BI no longer depends on live SQL queries for the core reports
- Job/cost data reconciles with Sage source (spot-check totals)

## Files & resources
- (add: schema inventory, pipeline link, mapping doc)

## Log
| Date | Note |
|---|---|
| | |
