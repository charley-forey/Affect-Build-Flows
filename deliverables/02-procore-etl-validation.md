# D2 — Procore ETL Validation & Hardening

**Status:** 🟢 **Live against the production tenant** (2026-08-02) | **Phase:** 1 — Foundation | **Billing:** 6 hrs in Phase 0 | **Target:** ✅ Met

> **Delivered, and rebuilt rather than patched.** Ingesting Affect's **production** Procore tenant through a registry of **44 registered endpoints landing 40 bronze tables** — the other **2 are blocked by Procore 403s** (`punch_item_types`, `schedule`), which is a permissions gap, not a coverage gap — behind one shared extractor. Adding an endpoint is a YAML entry, not a new notebook. 15 typed silver tables; the last full row/reject count (14,791 rows, **0 rejects**) was measured 2026-08-02 and has not been re-read since the QC tables landed. Incremental where the API verifiably supports `filters[updated_at]`, upsert on the natural key, quota-aware, credentials via `get_secret()`. **14 offline suites**, all passing, run the production Spark SQL through DuckDB with no Fabric and no network.
>
> **Two live limitations, both external.** Extraction runs **locally** and lands files — `cd_01_extract_procore` is not in `CD_Master_Pipeline`, so the nightly run merges what was last landed and never calls the Procore API — pending one Key Vault role assignment ("Key Vault Secrets Officer" on vault `OneLake`; the Azure subscription and the vault themselves now exist). And `punch_item_types` and `schedule` return **403**. Detail: [`_docs/procore-ingestion.md`](../foundation/charley-dev/_docs/procore-ingestion.md) and [`build-status.md`](../foundation/charley-dev/_docs/build-status.md).

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
- [x] Review script line-by-line with Rebecca (Jul 23 warehouse review)
- [x] Verify endpoint coverage vs dashboard needs — **44 registered, 40 landing bronze tables, 2 blocked by 403s**, generated inventory
- [x] Assess full vs incremental refresh — incremental where the API verifiably supports `filters[updated_at]`, MERGE on the natural key everywhere else
- [x] Add error handling, run logging — `meta_PipelineRun` heartbeat, diagnostics to `Files/_diag/`
- [x] Confirm and document refresh schedule — pipeline 02:00, model 04:00 Eastern
- [x] Data quality checks on landed data — **103 expectations (80 blocking, 23 warning)**; the gate blocks rather than warns
- [x] Handoff doc — [`procore-ingestion.md`](../foundation/charley-dev/_docs/procore-ingestion.md)
- [ ] **Move extraction into Fabric** — blocked on one Key Vault role assignment
- [ ] Resolve the two Procore 403s (`punch_item_types`, `schedule`) — Affect
- [ ] Failure alerting to a person (the gate fails the run; nothing emails yet)

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
| 2026-08-02 | **Deployed and running against the production tenant.** Bronze 40 tables; silver 15 tables, 14,791 rows, 0 rejects. Five silent-failure defects found and fixed on the way — a missing `Procore-Company-Id` header costing 28 endpoints, `manpower_logs` returning 200-with-zero-rows and costing 120,766 hours, `get_json_object` returning NULL on keys containing `(` or `=`, a company-level parent deduped to one project, and `percent_complete` formatted two different ways across endpoints. None raised an error. |
| 2026-08-19 | Registry re-counted and the framing corrected: **44 endpoints registered, 40 landing bronze tables, 2 blocked by Procore 403s**. The generated inventory had gone stale at 36 and is regenerated from `config/endpoints.yml`. Extraction still runs locally — the Azure subscription and a Key Vault now exist, so the remaining ask is one role assignment ("Key Vault Secrets Officer" on vault `OneLake`) rather than a purchasing decision. |
| 2026-08-19 | **Sixth silent-failure defect, in the silver transform.** `20_fieldops_silver.sql` read `$.trade` as an **object** instead of `$.trade.name`, so the column held `{"id":…,"name":"Electrical",…}` rather than a trade name. It broke every QC trade join — **631 of 850 NCRs** resolved to no trade — **and it put raw JSON into `fct_QualityItem.Trade` on the live Monthly Progress Report**, where a person was looking at it. Fixed by taking `$.trade.name`; unmapped NCRs fell **631 → 459** and `fct_QualityItem.Trade` now reads e.g. `"Windows"`. The residual **459** is a real vocabulary difference (Procore "HVAC"/"Sprinkler" vs workbook `HVAC_DUCTWORK`/`FIRE_SPRINKLER`) and is **deliberately not guessed** — a defect attributed to the wrong trade is worse than one attributed to none. Open question for Affect, surfaced on the PQP Data Quality page. |
| 2026-07-26 | Built a **runnable reference pipeline** for the RFI/submittal slice — `src/procore/`. Deliberately structured as **one config-driven extractor** rather than one notebook per entity, because the five findings above are one bug duplicated per notebook: auth, pagination and load strategy copy-pasted N times means every fix is applied N times. Addressed: (1) credentials via `get_secret()` — Key Vault in Fabric, env vars locally, one function; (2) Delta **merge** on natural key + `updated_at` watermark — re-running does not double rows, asserted by `test_rerun_is_idempotent`; (3) `iter_active_projects()` filters to active; (4) new endpoint = a YAML entry in `config/endpoints.yml`; (5) bronze stores the **unparsed payload**, so it structurally cannot drop the vendor/cost-code IDs the model needs. Transform logic is version-controlled `.sql` (not dataflows) with a `data_quality_log` that flags rather than drops. 34 tests pass; pipeline runs end to end on fixtures producing `fct_RfiSubmittal`. **Not yet run against a real tenant** — Procore field names come from documented shapes, not a live response. Two values stay undefined by the client and are marked in the SQL for a one-line change: "critical" (open question #5) and the trade mapping. |
