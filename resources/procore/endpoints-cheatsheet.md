# Procore API — Endpoint Cheatsheet

The ~50 endpoints relevant to the Monthly Progress Report, extracted from the Procore
OpenAPI spec (`combined_OAS.json`, v2.0 spec, `x-created-at: 2026-07-23`, **2,111 paths**).

**Every path and summary below was read programmatically from the spec — nothing is
guessed.** Filter parameters listed are the ones present on that endpoint's `GET`.

Base URL: `https://api.procore.com` · Full spec: see [`README.md`](README.md) for how to
re-download (the 52 MB file is gitignored).

## Reading this table

- `{company_id}`, `{project_id}` are path parameters.
- `filters[updated_at]` accepts an ISO 8601 range — **this is what makes incremental
  loading possible**. Use it on every list endpoint that has it.
- `page` / `per_page` — max 1000 on most v1.0 list endpoints.
- v2.0 endpoints require the `Procore-Company-Id` **header**. v1.0 generally takes
  `company_id` in the path or query. Mixing the two is the most common cause of a 403.

---

## Projects & reference data

| Endpoint | Summary | Useful filters |
|---|---|---|
| `GET /rest/v1.0/companies` | List Companies | `page`, `per_page` |
| `GET /rest/v1.0/companies/{company_id}/projects` | List company's projects | — |
| `GET /rest/v1.0/projects` | List projects | `filters[by_status]`, `filters[name]`, `filters[created_at]`, `filters[updated_at]` |
| `GET /rest/v1.0/projects/{id}` | Show project | `view` |
| `GET /rest/v1.0/vendors` | List company vendors | — |
| `GET /rest/v1.0/projects/{project_id}/vendors` | List project vendors | `filters[search]`, `filters[trade_id][]`, `filters[standard_cost_code_id][]` |
| `GET /rest/v1.0/cost_codes` | List Cost Codes | `filters[id]`, `filters[origin_id]`, `view` |
| `GET /rest/v1.0/standard_cost_codes` | List Standard Cost Codes | `filters[origin_id]`, `view` |

→ `dim_Project`, `dim_Vendor`, `dim_CostCode`

> `filters[trade_id][]` on project vendors is worth investigating — it may give a
> Procore-native trade list to reconcile against Affect's 29-trade `DROPDOWN!M`.

---

## Schedule & manpower

| Endpoint | Summary | Useful filters |
|---|---|---|
| `GET /rest/v1.0/projects/{project_id}/schedule` | Get Schedule Metadata | — |
| `GET /rest/v1.1/projects/{project_id}/schedule/resources` | List Resources | `filters[query]` |
| `GET /rest/v1.0/projects/{project_id}/manpower_logs` | List Manpower Logs | `filters[vendor_id]`, `filters[location_id]`, `filters[status]` |
| `GET /rest/v1.0/projects/{project_id}/manpower_logs/daily_totals` | **Get total workers and man hours** | `filters[created_by_id]` |
| `GET /rest/v1.0/projects/{project_id}/daily_log_headers` | Get the Daily Log Header via date or id | — |
| `GET /rest/v1.1/projects/{project_id}/daily_logs/counts` | List Counts of Daily Logs | `filters[status]`, `filters[daily_log_segment_id]` |

→ `fct_Milestone`, `fct_ManpowerDaily`, `fct_DailyLog`

> ⚠️ **The spec contains no `milestone` path.** `/schedule` returns metadata and tasks, not
> a milestone list. Affect is also evaluating **Outbuild** for scheduling. Confirm where
> the critical-path milestone list actually lives before building `fct_Milestone`.

> `daily_totals` computes the workbook's "Avg Daily over past 30 days" directly — the
> `SCHEDULE!Table14` values are typed in by hand today.

---

## RFIs & Submittals

| Endpoint | Summary | Useful filters |
|---|---|---|
| `GET /rest/v1.0/projects/{project_id}/rfis` | List RFIs | `filters[status]`, `filters[assigned_id]`, `filters[created_at]`, `filters[id]` |
| `GET /rest/v1.0/projects/{project_id}/rfis/filter_options/status` | List available RFI status filter options | — |
| `GET /rest/v1.0/projects/{project_id}/rfis/filter_options/priority` | List available RFI Priority filter options | — |
| `GET /rest/v1.1/projects/{project_id}/submittals` | List Submittals on a project | `filters[ball_in_court_id]`, `filters[created_at]`, `filters[query]`, `filters[id]` |
| `GET /rest/v1.1/projects/{project_id}/submittals/{id}` | Show Submittal | — |

→ `fct_RfiSubmittal`

> **The cleanest automation win in the workbook.** `SUBMITTALS & RFI!Table22` is one small
> table feeding the only chart, and it is fully derivable from these four endpoints.
>
> ⚠️ `/rfis/filter_options/priority` is the likely definition of "Open **Critical** RFIs" —
> but the workbook never defines "critical". Confirm with Affect (open question #5).

---

## Quality

| Endpoint | Summary | Useful filters |
|---|---|---|
| `GET /rest/v1.0/observations/items` | List Observation Items | `filters[assignee_id]`, `filters[assignee_company_id]`, `filters[location_id]`, `filters[created_by_id]`, `filters[checklist_list_id]` |
| `GET /rest/v1.0/observations/types` | List Observation Types | `page`, `per_page` |
| `GET /rest/v1.0/projects/{project_id}/observations/items/statuses` | List Observation Item statuses with localized labels | — |
| `GET /rest/v1.0/punch_items` | List Punch Items | `filters[status]`, `filters[priority]`, `filters[punch_item_type_id]`, `filters[location_id]` |
| `GET /rest/v1.0/punch_item_types` | List punch item types | `sort`, `filters[name]` |
| `GET /rest/v2.0/companies/{company_id}/projects/{project_id}/punch_list/trades` | List Punch Item Trade Filter Options | `page`, `per_page` |
| `GET /rest/v1.0/projects/{project_id}/inspection_logs` | List Inspection Logs | `filters[location_id]`, `filters[daily_log_segment_id]` |
| `GET /rest/v1.0/checklist/lists` | List Checklists | `filters[inspection_type_id]`, `filters[inspector_id]`, `filters[list_template_id]` |

→ `fct_QualityItem`, `fct_QualityMonthly`, `fct_ActivityLog`

> Biggest hand-entry elimination: `QUALITY!D38:E39` (avg days past due / to close) and
> `D40:E44` (main offenders) are **all typed in by hand** today and are all computable from
> `observations/items` and `punch_items` timestamps.
>
> `checklist/lists` and `inspection_logs` likely cover the workbook's Benchmark, Mockup,
> and Commissioning categories — worth confirming how Affect records those.

---

## Safety

| Endpoint | Summary | Useful filters |
|---|---|---|
| `GET /rest/v1.0/projects/{project_id}/incidents` | List Incidents | `filters[event_date]`, `filters[created_at]`, `filters[updated_at]`, `filters[id]` |
| `GET /rest/v1.0/projects/{project_id}/incidents/{id}` | Show Incident | — |
| `GET /rest/v1.0/projects/{project_id}/incidents/injuries` | List Injuries | `filters[affected_company_id]`, `filters[affected_person_id]`, `filters[created_at]` |
| `GET /rest/v1.0/projects/{project_id}/incidents/near_misses` | List Near Misses | `filters[affected_company_id]`, `filters[created_at]` |
| `GET /rest/v1.0/companies/{company_id}/incidents/severity_levels` | List Incident Severity Levels | `filters[id]`, `filters[updated_at]` |
| `GET /rest/v1.0/companies/{company_id}/incidents/statuses` | Get Incident Statuses | — |

Also available: `/incidents/environmentals`, `/incidents/property_damages`,
`/incidents/witness_statements`, `/incidents/actions`.

→ `fct_SafetyMonthly[RecordableIncidents]`

> "Recordable" is an OSHA classification. Procore separates injuries, near misses, property
> damage, and environmental incidents — **confirm which of these Affect counts** as a
> recordable before wiring `SAFETY!E`.

> Toolbox talks, standdowns, and notable visitors (`SAFETY!Table20`) have **no obvious
> endpoint**. They may fit Procore Daily Logs, or stay manual. Open question #12.

---

## Financial — contracts & billing

| Endpoint | Summary | Useful filters |
|---|---|---|
| `GET /rest/v1.0/prime_contracts` | List all Prime Contracts | `filters[id]`, `filters[updated_at]` |
| `GET /rest/v1.0/prime_contracts/{prime_contract_id}/line_items` | List Prime Contract line items | `filters[cost_code_id]`, `filters[created_at]`, `filters[updated_at]` |
| `GET /rest/v1.0/prime_contracts/{prime_contract_id}/payment_applications` | **List Payment Applications (Owner Invoices)** | `filters[is_last]`, `filters[id]` |
| `GET /rest/v1.1/requisitions` | **List Requisitions (Subcontractor Invoices)** | `filters[commitment_id]`, `filters[period_id]`, `filters[status]` |
| `GET /rest/v1.0/work_order_contracts` | List work order contracts | `filters[status]`, `filters[created_at]`, `view` |

→ `fct_FinancialPeriod`, `fct_Invoice`

> ⚠️ **Worth asking on the call.** If Affect bills owners through Procore, then
> `payment_applications` already holds the billing data the workbook sources from Sage.
> That would materially shrink the Sage ingestion — possibly to just cash receipts,
> retainage, and AR aging.

---

## Financial — budget & commitments

| Endpoint | Summary | Useful filters |
|---|---|---|
| `GET /rest/v1.0/projects/{project_id}/budget` | Show Budget meta data | — |
| `GET /rest/v1.0/budget_views` | List Budget Views | `sort` |
| `GET /rest/v1.0/budget_views/{budget_view_id}/detail_rows` | List Budget View Detail Rows | — |
| `GET /rest/v1.0/budget_line_items/{id}` | Show Budget Line Item | — |
| `GET /rest/v2.0/companies/{company_id}/projects/{project_id}/budget_line_items/{id}` | (budget line item, v2.0) | — |
| `GET /rest/v1.0/commitments` | List Commitments | `page`, `per_page` |
| `GET /rest/v2.0/companies/{company_id}/projects/{project_id}/commitment_contracts` | List Commitment Contracts | `filters[type]`, `filters[accounting_method]`, `filters[include_deleted]`, `view` |
| `GET /rest/v1.1/projects/{project_id}/direct_costs` | List Direct Cost Items | `filters[invoice_number]`, `filters[origin_id]`, `filters[created_at]` |

→ `fct_BudgetLine`, `fct_FinancialPeriod[TradeCosts*]`

> `budget_views/{id}/detail_rows` is the richest budget source — it returns the same
> columns Procore shows on screen, including calculated ones. Prefer it over assembling
> line items by hand.

---

## Financial — change orders

| Endpoint | Summary | Useful filters |
|---|---|---|
| `GET /rest/v1.0/potential_change_orders` | List Potential Change Orders | `filters[contract_id]`, `filters[due_date]`, `filters[created_at]`, `filters[updated_at]` |
| `GET /rest/v1.0/change_order_requests` | List Change Order Requests | `filters[due_date]`, `filters[invoiced_date]`, `filters[paid_date]`, `filters[updated_at]` |
| `GET /rest/v1.0/change_order/statuses` | List Change Order Statuses | `page`, `per_page` |
| `GET /rest/v1.0/change_order_packages` | List Change Order Packages | — |
| `GET /rest/v2.0/companies/{company_id}/projects/{project_id}/prime_change_orders/{prime_change_order_id}/line_items` | List Prime Change Order Line Items | `view` |

→ `fct_ChangeOrder`

> `FINANCIALS!C6` ("Age of oldest unapproved CO") is typed in by hand. `created_at` plus
> an approval status from `change_order/statuses` derives it — and it feeds an 8%-weighted
> scorecard category, so it is worth getting right.

---

## Integration notes

### Auth
OAuth 2.0. For unattended ETL use the **client credentials** grant with a service account
(Procore's "Data Connector App" / installation-based auth).

**Confirm which grant Rebecca's existing script uses.** A user-based token expires and will
break the pipeline at the worst possible moment — this is the single most common failure
mode for Procore ETLs.

### Headers
```
Authorization: Bearer <token>
Procore-Company-Id: <company_id>     # REQUIRED on v2.0
```

### Rate limits
Per-app, per-hour. Honour `Retry-After` on `429` with exponential backoff. Affect's volume
should not bind, but the retry is not optional — a single throttled call without one fails
the whole nightly run.

### Pagination
```
?page=1&per_page=1000
```
Response headers `Total` and `Link` drive the loop. Do not assume a fixed page count.

### Incremental loading
```
?filters[updated_at]=2026-07-01T00:00:00Z...2026-07-31T23:59:59Z
```
Available on most list endpoints. **Use it.** Full refreshes work for one project and stop
working as the portfolio grows.

### Version mixing is normal
RFIs are v1.0, submittals v1.1, commitment contracts v2.0. A single pipeline will span all
three. That is how Procore versions its API, not a mistake to correct.

### Sandbox
Procore provides a developer sandbox. Build and test the ETL there before pointing at
production — especially anything that writes.
