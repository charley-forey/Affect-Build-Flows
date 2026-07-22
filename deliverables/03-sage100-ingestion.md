# D3 — Sage 100 Ingestion Pipeline

**Status:** 🔴 Not started | **Phase:** 1 — Foundation | **Billing:** TBD after D1 (likely scoped project) | **Target:** TBD

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
