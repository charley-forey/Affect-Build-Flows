# D2 — Procore ETL Validation & Hardening

**Status:** 🟢 **Complete** (2026-08-02) | **Phase:** 1 — Foundation | **Billing:** 6 hrs in Phase 0 | **Target:** ✅ Met

> **Delivered, and rebuilt rather than patched.** 36 endpoints live against Affect's production tenant, driven by one shared extractor and a YAML registry — adding an endpoint is a config entry, not a new notebook. Incremental (`updated_at` watermark, upsert on natural key), quota-aware, credentials via a secret helper. 12 offline test suites run the production Spark SQL through DuckDB with no Fabric and no network. **One limitation:** extraction runs locally and lands files pending an Azure subscription for Key Vault — the nightly pipeline merges what was last landed and does not call the API. Detail: [`_docs/procore-ingestion.md`](../foundation/charley-dev/_docs/procore-ingestion.md).

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
- [`src/procore/`](../src/procore/) — the reference pipeline (extractor, endpoint registry, SQL, notebooks, tests)
- [`src/README.md`](../src/README.md) — layer rules, how to run it, how to get it into Fabric
- [`powerbi/AffectProjectReport.pbip`](../powerbi/AffectProjectReport.pbip) — semantic model over the gold output
- (add: link to Rebecca's script location in Fabric, run log location, handoff doc)

## Log
| Date | Note |
|---|---|
| 2026-07-23 | Walked the Procore ingestion with Rebecca (`meeting-notes/2026-07-23-warehouse-review.md`). Concrete findings to address here: (1) **credentials hard-coded in a notebook cell** → move to env vars / Key Vault; (2) notebooks **full-reload the table each run** → incremental refresh; (3) notebooks **loop every project** regardless of status → filter to active + set a deliberate cadence (rate limits); (4) coverage is **financial-only** (commitments, change orders, pay apps) → add RFIs, submittals, and others per the endpoint inventory; (5) **transformations may drop ID columns** (vendor/cost-code) the model needs → verify at silver. |
| 2026-07-26 | Built a **runnable reference pipeline** for the RFI/submittal slice — `src/procore/`. Deliberately structured as **one config-driven extractor** rather than one notebook per entity, because the five findings above are one bug duplicated per notebook: auth, pagination and load strategy copy-pasted N times means every fix is applied N times. Addressed: (1) credentials via `get_secret()` — Key Vault in Fabric, env vars locally, one function; (2) Delta **merge** on natural key + `updated_at` watermark — re-running does not double rows, asserted by `test_rerun_is_idempotent`; (3) `iter_active_projects()` filters to active; (4) new endpoint = a YAML entry in `config/endpoints.yml`; (5) bronze stores the **unparsed payload**, so it structurally cannot drop the vendor/cost-code IDs the model needs. Transform logic is version-controlled `.sql` (not dataflows) with a `data_quality_log` that flags rather than drops. 34 tests pass; pipeline runs end to end on fixtures producing `fct_RfiSubmittal`. **Not yet run against a real tenant** — Procore field names come from documented shapes, not a live response. Two values stay undefined by the client and are marked in the SQL for a one-line change: "critical" (open question #5) and the trade mapping. |
