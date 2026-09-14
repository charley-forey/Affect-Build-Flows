# Deletion and source-scope handling

Validation plan stages: **Source scope** and **Bronze**. Written 2026-09-14, offline: nothing
here was measured against Fabric or a live tenant. Evidence is the code, the Procore OAS
(`resources/procore/combined_OAS.json`, main checkout), and the extraction manifests in
`_docs/procore-*-manifest.json`.

## The problem

1. **Deletes never arrive.** Bronze loads MERGE on `(_key, _project_id)`. A record deleted or
   recycled at source is simply not returned again, so its last bronze copy stays and keeps
   counting in silver, gold and the report.
2. **Scope freezes silently.** `iter_active_projects` pulls `filters[by_status]=Active`. When a
   project goes inactive it drops out of every project-scoped call; its facts stop updating
   but still count in portfolio totals, and nothing says so.

## Findings by source

### Procore

**How Procore signals deletion.** There is no change feed. The `/sync` paths in the OAS are
bulk *write* (PATCH) endpoints, not delta reads. What exists:

| Signal | Where (OAS) | Use |
|---|---|---|
| Record absent from a list call | every list endpoint | the only signal common to all endpoints |
| `recycle_bin` list endpoints | `rfis/recycle_bin`, `submittals/recycle_bin`, `punch_items/recycle_bin`, `recycle_bin/observations/items`, `recycle_bin/incidents` (+ injuries, near misses), `recycle_bin/checklist/lists` | proves "deleted" rather than "not returned"; items there can be restored |
| `filters[include_deleted]` | `potential_change_orders`, `change_order_packages` (prime_change_orders), `work_order_contracts`, `purchase_order_contracts`, v2.0 `commitment_contracts` (also `filters[deleted_at]`) | lets an **incremental** pull see deletions: the record comes back with `deleted_at` set |
| `deleted_at` in the response schema | prime_contracts, change_order_packages, potential_change_orders, direct_costs, observations, punch_items, incidents, cost_codes, WO/PO contracts, rfis (also `deleted`) | only populated when the call asks for deleted records |

The recycle bins carry no permanent-delete signal (a purged record just disappears from the
bin too), so "absent from a complete list" remains the primary rule and the bins are a
refinement.

**Is a full key set available each run?** Per endpoint, from `endpoints.yml` and the repair
manifest (`procore-repair-manifest.json`: 20 projects, 29 endpoints `complete/full`):

| Endpoint class | Endpoints | Full key set per run? |
|---|---|---|
| Full pull, project scope | project_vendors, cost_codes, requisitions, work_order_contracts, purchase_order_contracts, commitment_contracts, budget, budget_views, prime_change_orders, direct_costs, rfis, rfi_statuses, rfi_priorities, submittals, observations, punch_items, inspection_logs, checklist_lists, incident_injuries, incident_near_misses | **Yes**, per project, when that scope ends `complete` |
| Full pull, company scope | vendors, company_insurances, change_order_statuses, observation_types | **Yes** (one scope, `_project_id` NULL) |
| Full pull, parent scope | work_order_contract_line_items, purchase_order_contract_line_items, payment_applications, budget_detail_rows, checklist_list_items | **Yes per project** when every parent scope of that project is complete. A deleted parent's children are then correctly absent too |
| Parent discovery on an incremental endpoint | prime_contracts (always pulled full because it is a parent) | **Yes** |
| Incremental (`filters[updated_at]`) | projects, prime_contract_line_items, direct_cost_line_items, potential_change_orders, incidents, incident_severity_levels | **No** - only changed records. Deletions need `filters[include_deleted]` or a periodic full pull |
| Date-windowed | manpower_daily_totals, manpower_logs (365 d), daily_log_headers (30 d) | **No** - a record leaving the window is not a deletion |

No endpoint offers a cheap id-only list; full pulls already return every key, and they are
what the nightly run already pays for. Note the OAS lists `filters[updated_at]` on rfis and
submittals, which `endpoints.yml` still treats as unconfirmed - worth a live check, but
moving them to incremental would take them out of tombstoning (see recommendation 4).

### Outbuild

Every endpoint is a company-wide full pull (`extract_outbuild_local.extract`, manifest
`mode: full`), merged on `_merge_key`. Full key set: **yes**, one scope (the whole table) per
endpoint. **Implemented 2026-09-14** for the consumed endpoints, `projects` and `activities`:

- `extract()` passes `tombstone=True` to the notebook's `write` only when the endpoint is
  `consumed`, its pull finished (every page, no exception) and returned **at least one row**.
  Skipped (`scope:`) and failed endpoints never reach `write`; an empty answer is not
  trusted. The decision is recorded per endpoint as `tombstone` in the manifest.
- `pull()` now **raises** past `MAX_PAGES` instead of returning the pages it had: a truncated
  list would otherwise tombstone everything after page 200.
- The notebook's `write` now goes through `fc.merge_delta` (Spark only - there is no
  delta-rs Outbuild path) with the scope `fc.WHOLE_TABLE` (predicate `TRUE`). merge_delta
  adds `_source_deleted_at` to the landing-created tables with `ALTER TABLE`, and the source
  carries the column as NULL, so a key read again clears its flag.
- Silver `25_outbuild_silver.sql` excludes tombstoned activities, and tombstoned projects
  from the schedule map (their surviving activities become unattributed, which is visible,
  rather than staying on a deleted project). `28_source_deletions_silver.sql` ledgers them as
  `deleted at source` (targets `cd_silver_outbuild_activities`, `outbuild_schedule_map`), so
  bronze activities with an id = silver + `deleted at source` rejects. `dq_DataGap` shows them
  under **Deleted at source** with source system `Outbuild`.
- Unconsumed endpoints (tasks, roadblocks, ...) never tombstone: nothing reads them.

### Sage 100 (CD_Sage_Ingest dataflow / CD_Sage_Copy)

`CD_Sage_Ingest.Dataflow/mashup.pq`: `DefaultOutputDestinationSettings ... UpdateMethod =
[Kind = "Replace"]`, and `deploy_sage_copy.py` copies with overwrite. Every run is a **full
replace** of the eight tables, so a row deleted in Sage disappears from bronze on the next
run. Nothing to tombstone. What remains is **voids**: Sage voids by status, not by delete.
`26_sage_silver.sql` carries `status_code` on AR/AP headers but does not exclude voided
invoices. See **Decision: Sage voided invoices** below.

### SharePoint registers (CD_Manual_Ingest dataflow)

Same `UpdateMethod = Replace` on every `cd_bronze_man_*` query: a deleted list item is gone on
the next refresh. The existing "Empty manual register" gap covers the failure where a list
refresh returns nothing. No tombstone needed.

## Recommendation (implemented for Procore)

1. **Tombstone, never delete.** Bronze gains `_source_deleted_at` (timestamp). When a key in
   bronze is absent from a **complete full-scope pull** of that (endpoint, project) scope,
   the merge sets `_source_deleted_at` to the batch's `_ingested_at`. The row and its last
   payload stay as evidence. A key that is read again is written with NULL, clearing it.
2. **Never tombstone from doubt** (`procore_scope.tombstone_scopes`):
   - incremental or date-windowed pulls: never;
   - a project scope that `failed`, is `unavailable_*` (undeclared 403/404) or
     `excluded_declared`: never;
   - a parent endpoint's project: only if every child scope of that project completed;
   - a scope that returned **zero rows**: never. This tenant has returned 200 with an empty
     list for wrong parameters (`prime_change_orders`, `manpower_logs`). Ceiling: a project
     whose last record is deleted keeps it until a recycle-bin read is added;
   - projects outside the run (inactive): no scope, so never.
   The chosen scopes are written to the manifest as `tombstone_scopes` per endpoint.
3. **Silver excludes and ledgers.** The parsers for prime change orders, submittals, RFIs,
   observations, punch items, direct costs, commitments and commitment lines filter
   `_source_deleted_at IS NULL`; `28_source_deletions_silver.sql` writes those rows to
   `cd_dq_rejects` with reason `deleted at source`, so bronze-with-id = silver + rejects.
   `dq_DataGap` lists them under **Deleted at source**; DQ WARN
   *Procore records deleted at source* counts them.
4. **Incremental endpoints: weekly full pull (implemented 2026-09-14).** See **Decision:
   weekly full pull** below. Date-windowed endpoints still never tombstone.
   `filters[include_deleted]=true` remains the sharper signal where the OAS offers it
   (potential_change_orders, WO/PO contracts, change_order_packages) - not built.
5. **Inactive projects: make staleness visible rather than widen scope.** A "recently inactive"
   scope (projects whose `active` flipped within N days) needs the status-change date, which
   the projects payload does not carry (`updated_at` moves for any edit), and each extra
   project costs ~35 calls against 600/hour. Instead:
   - `cd_silver_project_extraction.last_extracted_at` = newest `_ingested_at` on the
     project's rows in full-pull, project-scoped tables (a full pull re-merges every row it
     reads, so this advances nightly while the project is in scope and stops when it leaves);
     `is_active_in_procore` = the projects payload `active` flag;
   - `dim_Project` gains **IsActiveInProcore** and **LastExtractedAt** (NULL on the
     existing-warehouse source, and for projects never read by a full pull);
   - DQ WARN *projects with facts extracted within 2 days* lists projects with budget lines,
     change orders or RFIs/submittals whose `LastExtractedAt` is older than 2 days.
   The semantic model and report do not bind the two columns yet (release branch owns them).
   If a frozen inactive project should be re-read once, the manual lever is a one-off run
   with its id added to `project_ids`.

## Decision: weekly full pull on incremental Procore endpoints

**Decision.** The six watermarked endpoints carry `full_pull_weekday: Sunday` in
`endpoints.yml`: `projects`, `prime_contract_line_items`, `direct_cost_line_items`,
`potential_change_orders`, `incidents`, `incident_severity_levels`. On that day the extraction
cell ignores the watermark (`procore_scope.full_pull_due(ep, run_started)`), the audit reads
`mode: full` and `scheduled_full_pull: true`, and `tombstone_scopes` applies exactly as for
any full pull (complete, non-empty scopes only). The watermark still advances afterwards.
`prime_contracts` is not flagged: it is already pulled in full nightly as a parent.

- **Clock.** `run_started = fc.utc_now()` is read once per run and passed in, so every
  endpoint agrees and the schedule is testable with any datetime. The weekday is the UTC
  weekday; the 02:00 Eastern pipeline (`deploy_schedule.py`) runs at 06:00/07:00 UTC, the
  same day.
- **Refused at registry load**: the flag on a non-incremental endpoint, a misspelled weekday,
  and any date-windowed endpoint (`manpower_daily_totals`, `manpower_logs`,
  `daily_log_headers`). Those APIs require the window (200-empty or 400 without it, and
  daily_logs caps it at 30 days), so no full key set exists; tombstoning inside the window
  would need a payload-date predicate on both merge paths. Not built.
- **Ceiling.** A Sunday run that fails or does not run leaves those deletions unseen for
  another week (`ponytail:` note in `full_pull_due`).

**Quota cost** (600 requests/hour). Requests per scope are `ceil(rows / per_page)`, minimum
1; an upper bound is `scopes + floor(rows / per_page)`. The nightly incremental run already
spends one request per scope (the repair manifest shows 0-5 changed rows per endpoint), so
the Sunday cost is the extra pages only. Scopes come from `procore-repair-manifest.json`
(batch 20260910T081211, 20 active projects). That manifest holds incremental row counts for
these endpoints, so full row counts come from `procore-ingestion.md` (its full-run table and
the defect-9 table). All six use `per_page: 100`.

| Endpoint | Scopes | Full rows (source) | Nightly incremental | Sunday full, upper bound | Extra |
|---|---:|---|---:|---:|---:|
| projects | 1 (company) | 19 (procore-ingestion.md) | 1 | 1 | 0 |
| incident_severity_levels | 1 (company) | 5 (procore-ingestion.md; manifest 5) | 1 | 1 | 0 |
| incidents | 20 | 3 (procore-ingestion.md) | 20 | 20 | 0 |
| prime_contract_line_items | 21 (parent) | 317 (procore-ingestion.md, defect 9) | 21 | 24 | 3 |
| potential_change_orders | 20 | 1,050 (procore-ingestion.md) | 20 | 30 | 10 |
| direct_cost_line_items | 20 | **not measured**; 418 direct_costs headers, assumed <= 1,300 lines | 20 | <= 33 | <= 13 |
| **Total** | | | **83** | **<= 109** | **<= 26** |

About 26 extra requests once a week, under 5% of one hour's quota. The row counts date from
August; re-derive from the first Sunday manifest (`received_rows` per scope).

## Decision: Sage voided invoices

**Evidence (offline).**
- Sage 100 Contractor guides (`resources/sage-100-contractor/guides/`:
  `user-guide-2021-sql-v23.1.md` "About receivable invoice status" and "About payable invoice
  status"; `sage-100-contractor-and-your-business-2026.1.md`): AR (`acrinv`) and AP (`acpinv`)
  invoices share the status list **1-Open, 2-Review, 3-Dispute, 4-Paid, 5-Void**. 4 and 5 are
  assigned only by Sage ("If you void the record, Sage 100 Contractor automatically assigns
  status 5-Void"). `schema/OBSERVED-SCHEMA.md` confirms a `status` column on both tables but
  gives no value distribution.
- `_docs/sage-payments-evidence.json` (live aggregates, 2026-09-13): AR invoice **recnum 55
  has status 5**, receipts +200,000.00 and -200,000.00 on 2025-12-31, `amtpad` 0 and `invbal`
  200,000.00. It is a void, and silver's `invoice_total = amtpad + invbal` counts it as
  200,000 billed and 200,000 outstanding.
- No local evidence gives the full status distribution: `sage-reconciliation-evidence.json`
  and `sage-spark-evidence.json` hold rule outcomes only, the scratch
  `unmatched-ar-reconciliation.json` holds amounts by job with no status, and there is no
  `sage-*.json` in the scratchpad. Whether any AP invoice is status 5 is unknown.

**Decision.** A void is identifiable: `status_code = 5` on AR and AP. Inclusion logic is
**unchanged** - excluding voids changes billed revenue and the AR balance, which is Affect's
call, and a voided invoice still carrying `invbal` may be worth checking with their
bookkeeper first. Instead:
- `sv_ar_invoices` exposes `status_code` (NULL on the legacy warehouse source, which has no
  status), matching `sv_ap_invoices`;
- DQ WARN **voided Sage invoices included in totals** lists every AR/AP invoice with
  `status_code = 5` (ledger, ids, job, total, balance). Expected live: at least recnum 55.

If Affect confirms voids should not count, the change is one filter each in
`22_fct_invoice.sql` and `34_fct_apinvoice.sql`, plus the conservation rules that compare
them to silver.

## Implementation map

| Piece | File |
|---|---|
| MERGE with `WHEN NOT MATCHED BY SOURCE ... UPDATE SET _source_deleted_at`, legacy-table `ALTER TABLE ADD COLUMNS` | `00-platform/lib/fabric_common.py` (`merge_sql`, `merge_delta`, `tombstone_predicate`) |
| Same on delta-rs, schema evolved by an empty `schema_mode="merge"` append | `00-platform/lib/deltars.py` (`merge_rows`) |
| Scope eligibility from the endpoint audit | `00-platform/lib/procore_scope.py` (`tombstone_scopes`) |
| Bronze row and Spark schema carry the column | `src/procore/procore_extract.py` |
| Extraction cell passes scopes to both kernels' `write_bronze` | `_local/make_notebooks.py` |
| Silver exclusion, reject ledger, freshness | silver `10`, `20`, `21`, `23`, `24`, `28`; `01`/`00` `sv_projects` |
| Gold | `10_dim_project.sql`, `45_dq_datagap.sql` |
| DQ | `02-transformation/dq/expectations.py` |
| Outbuild tombstone decision, truncation guard | `_local/extract_outbuild_local.py` (`extract`, `pull`); `fabric_common.WHOLE_TABLE` |
| Outbuild notebook write via `merge_delta` | `_local/make_notebooks.py` (`EXTRACT_OUTBUILD`) |
| Outbuild silver exclusion and ledger | silver `25`, `28`; gold `45` (source system) |
| Weekly full pull | `endpoints.yml` (`full_pull_weekday`), `procore_scope.full_pull_due`, extraction cell in `make_notebooks.py` |
| Sage void WARN | `00`/`01` `sv_ar_invoices.status_code`, `dq/expectations.py` |
| Tests | `test_deltars.py` (both paths identical; complete / partial / excluded / empty / incremental / reappear / legacy schema; Outbuild through `extract()` + `merge_sql`: consumed / unconsumed / failed / empty / skipped / reappear), `test_validation.py` (manifest scopes and the weekly full pull from the real extraction cell; registry flags; Outbuild tombstone flag per endpoint), `procore_scope.py` self-check (schedule with an injected clock; registry refusals), `test_silver.py` (conservation incl. Outbuild), `test_gold.py`, `test_dq_rules.py` (void WARN fires on AR and AP) |

## Risks

- **Deploy order.** Silver reads `_source_deleted_at` on ten Procore bronze tables. Those
  tables gain the column on their first merge by the new extractor. Deploy the lib and
  ingestion notebook and let one extraction run finish **before** deploying silver, or
  silver fails with an unresolved column. Tables created by `cd_05_land_to_bronze` (local
  landing path) never gain it.
- **Deploy order, again.** Silver `25` and `28` read `_source_deleted_at` on the two consumed
  Outbuild bronze tables: run `cd_02_extract_outbuild` once with the new lib and notebook
  before deploying silver. `endpoints.yml` with `full_pull_weekday` needs the new
  `procore_scope.py` in `Files/lib` (the old dataclass rejects the unknown field): upload lib
  and config together, as `deploy_ingestion.py` does.
- **A pull that silently returns less.** Pagination truncation or a permission narrowing
  (e.g. private RFIs no longer visible to the service account) on a scope that still ends
  `complete` with rows will tombstone real records. They are recoverable (the next complete
  read clears them) and visible (DQ WARN count, dq_DataGap), not silent - but a spike in
  that WARN should be read as "check the pull" before "records were deleted".
- **delta-rs version.** `when_not_matched_by_source_update` and `schema_mode="merge"` are
  verified on deltalake 1.6.3 locally; the Fabric Python kernel's bundled version is not
  confirmed.
- **Spark MERGE `NOT MATCHED BY SOURCE`** needs Delta 2.3+ (Fabric runtime 1.2+). Verified
  only through the DuckDB oracle offline.
- **Freshness proxy.** `LastExtractedAt` is derived from bronze ingestion times, not from
  the manifest; a project with no rows in any full-pull table reads NULL.
