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
`mode: full`), merged on `_merge_key`. Full key set: **yes**, one scope per endpoint, when
the endpoint status is not failed. Deletions are currently kept like Procore's. Not
implemented here (the merge goes through `fc.merge_sql` directly with a string schema); the
same `tombstone_scopes` argument applies with a single company scope.

### Sage 100 (CD_Sage_Ingest dataflow / CD_Sage_Copy)

`CD_Sage_Ingest.Dataflow/mashup.pq`: `DefaultOutputDestinationSettings ... UpdateMethod =
[Kind = "Replace"]`, and `deploy_sage_copy.py` copies with overwrite. Every run is a **full
replace** of the eight tables, so a row deleted in Sage disappears from bronze on the next
run. Nothing to tombstone. What remains is **voids**: Sage voids by status, not by delete.
`26_sage_silver.sql` carries `status_code` on AR/AP headers but does not exclude voided
invoices; that is a business-rule decision (void = status 5 in Sage 100 Contractor, to be
confirmed against the tenant) and is out of scope for this change.

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
4. **Incremental endpoints (next step, not done).** Add `filters[include_deleted]=true` where
   the OAS supports it (potential_change_orders, WO/PO contracts, change_order_packages) and
   map a returned `deleted_at` to `_source_deleted_at`; or run those endpoints full once a
   week. Until then their deletions are invisible.
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
| Tests | `test_deltars.py` (both paths identical; complete / partial / excluded / empty / incremental / reappear / legacy schema), `test_validation.py` (manifest scopes from the real extraction cell), `test_silver.py` (conservation), `test_gold.py`, `test_dq_rules.py` |

## Risks

- **Deploy order.** Silver reads `_source_deleted_at` on ten Procore bronze tables. Those
  tables gain the column on their first merge by the new extractor. Deploy the lib and
  ingestion notebook and let one extraction run finish **before** deploying silver, or
  silver fails with an unresolved column. Tables created by `cd_05_land_to_bronze` (local
  landing path) never gain it.
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
