# D2 — Procore ETL Validation & Hardening

**Status:** 🟢 **Live against the production tenant** (2026-08-02) | **Phase:** 1 — Foundation | **Billing:** 6 hrs in Phase 0 | **Target:** ✅ Met

> **Delivered, and rebuilt rather than patched.** Ingesting Affect's **production** Procore tenant through a registry of **44 registered endpoints landing 40 bronze tables** — the other **2 are blocked by Procore 403s** (`punch_item_types`, `schedule`), which is a permissions gap, not a coverage gap — behind one shared extractor. Adding an endpoint is a YAML entry, not a new notebook. 15 typed silver tables; the last full row/reject count (14,791 rows, **0 rejects**) was measured 2026-08-02 and has not been re-read since the QC tables landed. Incremental where the API verifiably supports `filters[updated_at]`, upsert on the natural key, quota-aware, credentials via `get_secret()`. **14 offline suites**, all passing, run the production Spark SQL through DuckDB with no Fabric and no network.
>
> **Two live limitations, both external.** Extraction runs **locally** and lands files — `cd_01_extract_procore` is not in `CD_Master_Pipeline`, so the nightly run merges what was last landed and never calls the Procore API — pending the **rotation of the exposed Procore credential pair**. (The Key Vault ask that used to sit here was withdrawn on 2026-08-19 — it named the wrong vault; `AffectKeyVault` was readable and writable by our account all along.) And `punch_item_types` and `schedule` return **403**. Detail: [`_docs/procore-ingestion.md`](../foundation/charley-dev/_docs/procore-ingestion.md) and [`build-status.md`](../foundation/charley-dev/_docs/build-status.md).

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
- [x] Data quality checks on landed data — **107 expectations (83 blocking, 24 warning)**; the gate blocks rather than warns
- [x] Handoff doc — [`procore-ingestion.md`](../foundation/charley-dev/_docs/procore-ingestion.md)
- [ ] **Move extraction into Fabric** — blocked on rotating the exposed Procore credentials, not on Key Vault
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
| 2026-08-19 (evening) | **That Key Vault ask was wrong and is withdrawn.** It named vault `OneLake`; the vault Affect uses is `AffectKeyVault` (RG `Affect_Data`, subscription `73932b34-…`), where `cforey-c@affect-group.com` already held *Key Vault Administrator* inherited at resource-group scope. Two real defects were behind it: `get_secret` asked for `PROCORE_CLIENT_ID` while `setup_keyvault.py` wrote `procore-client-id` (Key Vault forbids underscores), and `get_secret` **failed open** to `os.environ` — a half-configured vault would have read a credential from an unaudited source and reported success. It now raises inside Fabric. The gate on moving extraction into Fabric is the **credential rotation**. |
| 2026-08-19 | **Sixth silent-failure defect, in the silver transform.** `20_fieldops_silver.sql` read `$.trade` as an **object** instead of `$.trade.name`, so the column held `{"id":…,"name":"Electrical",…}` rather than a trade name. It broke every QC trade join — **631 of 850 NCRs** resolved to no trade — **and it put raw JSON into `fct_QualityItem.Trade` on the live Monthly Progress Report**, where a person was looking at it. Fixed by taking `$.trade.name`; unmapped NCRs fell **631 → 459** and `fct_QualityItem.Trade` now reads e.g. `"Windows"`. The residual **459** was a real vocabulary difference rather than a bug, and has since been largely closed by `qc_seed_TradeAlias` — see the row below. |
| 2026-08-19 | **Three more silent defects, all in our own transforms, all verified fixed against the live workspace.** (1) **Submittal statuses — 223 → 0.** The silver `CASE` in `24_qc_procore_silver.sql` handled `'FOR RECORD ONLY'`, the workbook's wording; Procore actually sends `'For Record'`, and `'Not Reviewed'` was unhandled. **222 of 2,245 submittals** — a tenth of the register — matched no branch and fell out of every status slicer. A spelling mismatch, not a vocabulary problem. (2) **Trade vocabulary — 970 → 506 unmapped.** New seed table `qc_seed_TradeAlias` (16 rows, from `seed/qc_trade_alias.csv` via `_local/make_qc_seeds.py`), joined in `33_fct_qc.sql` on the **raw** Procore label as a fallback after the exact match. **464 rows recovered**: `fct_QcNcr` 459 → **215**, `fct_QcPunch` 511 → **291**. Only unambiguous pairs are mapped; `Drywall/Carpentry` (255), `Concrete Superstructure` (110) and `Concrete` (64) stay unmapped pending Affect, and a further set of Procore trades (Roofing, Glazing, Structural Steel, Low Voltage, …) has no equivalent in the 26-sheet library at all — a scope question, not a mapping gap. (3) **Cost-code CSI divisions — 807 → 0.** `17_dim_costcodecrosswalk.sql` required two leading digits; Affect writes divisions 1–9 without the leading zero, so `1-1000 GENERAL REQUIREMENTS` is Division **01**. All 807 were fixable (780 as `N-`, 27 as a bare digit) and **none was genuinely malformed** — 15% of the 5,433-code master had been silently absent from every by-division rollup. Same shape as the `$.trade` defect: a data-quality finding that was our code being wrong about the client's conventions. Plus a new ERROR-severity `referential` check on `qc_seed_TradeAlias.TradeKey`, so a typo'd alias cannot masquerade as an unmapped trade. |
| 2026-07-26 | Built a **runnable reference pipeline** for the RFI/submittal slice — `src/procore/`. Deliberately structured as **one config-driven extractor** rather than one notebook per entity, because the five findings above are one bug duplicated per notebook: auth, pagination and load strategy copy-pasted N times means every fix is applied N times. Addressed: (1) credentials via `get_secret()` — Key Vault in Fabric, env vars locally, one function; (2) Delta **merge** on natural key + `updated_at` watermark — re-running does not double rows, asserted by `test_rerun_is_idempotent`; (3) `iter_active_projects()` filters to active; (4) new endpoint = a YAML entry in `config/endpoints.yml`; (5) bronze stores the **unparsed payload**, so it structurally cannot drop the vendor/cost-code IDs the model needs. Transform logic is version-controlled `.sql` (not dataflows) with a `data_quality_log` that flags rather than drops. 34 tests pass; pipeline runs end to end on fixtures producing `fct_RfiSubmittal`. **Not yet run against a real tenant** — Procore field names come from documented shapes, not a live response. Two values stay undefined by the client and are marked in the SQL for a one-line change: "critical" (open question #5) and the trade mapping. |
