# D2 — Procore ETL Validation & Hardening

**Status:** 🔴 Not started | **Phase:** 1 — Foundation | **Billing:** Scoped from D1 review | **Target:** TBD

## Objective
Rebecca's existing Procore → Lakehouse ETL is reviewed, corrected where needed, and hardened into a reliable production pipeline with a known refresh cadence.

## Scope
**In:** Code review of existing script, endpoint coverage check, incremental refresh / history tracking, scheduling, error handling & alerting, data quality checks, documentation Rebecca can maintain.
**Out:** New source systems.

## Key data
- Procore endpoints: projects, budgets, budget line items, commitments, change orders, prime contracts, invoices/requisitions, vendors, cost codes (confirm actual list in D1)
- Landing tables in Lakehouse (raw) + any curated tables built from them

## Integration approach
Procore REST API (OAuth) → existing script (hosting method confirmed in D1: Fabric notebook / pipeline / Azure Function) → Fabric Lakehouse raw tables. Add: incremental pulls where supported, run logging, failure alerting, documented schedule.

## Tasks
- [ ] Review script line-by-line with Rebecca (knowledge transfer both ways)
- [ ] Verify endpoint coverage vs dashboard needs (from D1 Excel mapping)
- [ ] Assess full vs incremental refresh; add change/history tracking if needed
- [ ] Add error handling, run logging, alerting
- [ ] Confirm and document refresh schedule
- [ ] Data quality checks on landed data
- [ ] Handoff doc so Rebecca can maintain/extend the pattern

## Acceptance criteria
- ETL runs on schedule without manual intervention; failures alert someone
- All endpoints needed for D5 dashboard are landing correctly
- Rebecca can explain and modify the pipeline herself

## Files & resources
- (add: link to script location in Fabric/repo, run log location, handoff doc)

## Log
| Date | Note |
|---|---|
| 2026-07-23 | Walked the Procore ingestion with Rebecca (`meeting-notes/2026-07-23-warehouse-review.md`). Concrete findings to address here: (1) **credentials hard-coded in a notebook cell** → move to env vars / Key Vault; (2) notebooks **full-reload the table each run** → incremental refresh; (3) notebooks **loop every project** regardless of status → filter to active + set a deliberate cadence (rate limits); (4) coverage is **financial-only** (commitments, change orders, pay apps) → add RFIs, submittals, and others per the endpoint inventory; (5) **transformations may drop ID columns** (vendor/cost-code) the model needs → verify at silver. |
