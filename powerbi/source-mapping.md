# Source Mapping

> **Status — design intent, still broadly accurate (2026-08-19).** Field-by-field mapping
> drafted July 2026. Two things have moved since: the Procore registry now holds **44
> registered endpoints** and the gold layer publishes **53** table schemas, so the tables
> below are a subset rather than the full inventory; and the manual `man_*` rows arrive from
> SharePoint lists, not the Excel workbook described in `manual-input-template.md`.
> Live inventories: `foundation/charley-dev/_docs/endpoint-inventory.md` and
> `_docs/solution-guide.md`. The endpoint paths and the connector analysis below still hold.

Where every field in the Power BI model comes from.

Procore endpoints below were **verified against `resources/procore/combined_OAS.json`**
(Procore REST API v2.0 spec, 2,107 paths, retrieved Jul 22 2026). Nothing here is guessed.

## The connector question — read this first

Affect has purchased the **Procore ↔ Sage 100 Contractor connector** but has not rolled it
out on a project yet (Rebecca, Jul 22). Verified sync directions:

| Object | Direction |
|---|---|
| Jobs / Projects | ↔ bidirectional |
| Cost Codes | ↔ bidirectional |
| Budgets | ↔ bidirectional (one-way after initial setup) |
| Vendors | ↔ bidirectional |
| Commitments | Procore → Sage |
| Commitment Change Orders | Procore → Sage |
| Subcontractor Invoices | Procore → Sage |
| **Job Costs** | **Sage → Procore** |
| Sub Jobs / Phases | Sage → Procore |

**Implication for the build:** once live, job-cost actuals land *in Procore*. The Lakehouse
may not need a separate Sage job-cost pull at all — the Sage ingestion would narrow to
**AR invoices, cash receipts, retainage, and aging**, which the connector does not sync.

That is materially less work. It also creates a sequencing decision: build the Sage job-cost
pull now, or wait for the connector rollout? **Raise on the call** — see open question #4.

The `Redundant after connector?` column below flags every field affected.

---

## Legend

| Column | Meaning |
|---|---|
| **Model field** | Table and column from [`semantic-model.md`](semantic-model.md) |
| **Excel origin** | The cell or table it replaces |
| **Source** | Where the data comes from |
| **Endpoint / table** | Verified Procore path, or Sage area |
| **Redundant?** | Whether the connector makes a separate Sage pull unnecessary |

---

## 1. Project & reference data

| Model field | Excel origin | Source | Endpoint / table |
|---|---|---|---|
| `dim_Project[ProcoreProjectId]` | filename `YY-000` | Procore | `/rest/v1.0/companies/{company_id}/projects` |
| `dim_Project[ProjectName]` | filename | Procore | ↑ |
| `dim_Project[SageJobNumber]` | — | Sage | Job master |
| `dim_Project[OriginalContractAmount]` | `FINANCIALS!C3` | Procore | `/rest/v1.0/prime_contracts` |
| `dim_Vendor[*]` | `QUALITY!E`, `SCHEDULE!C25:C30` | Procore | `/rest/v1.0/projects/{project_id}/vendors` |
| `dim_CostCode[*]` | implied by `FINANCIALS!Table11011` | Procore | `/rest/v1.0/cost_codes`, `/rest/v1.0/standard_cost_codes` |
| `dim_Trade[*]` | `DROPDOWN!M4:M32` | Static seed | Trim whitespace (defect #9) |
| `dim_Status[*]` | `DROPDOWN!B,D,E,J,L,N,O,P,Q` | Static seed | See `dropdowns-and-status.md` |
| `dim_Owner[*]` | `DROPDOWN!C4:C12` | Static seed | 9 roles |
| `dim_ActivityCategory[*]` | `DROPDOWN!I`, `DROPDOWN!K` | Static seed | Split on en dash |
| `dim_Date[*]` | `DASHBOARD!AU4` | Generated | Replaces the whole `INDEX/MATCH` mechanic |

> ⚠️ **`dim_Project[ProjectNumber]` is the linchpin.** Every join in the model depends on
> one identifier meaning the same thing in Procore, Sage, and the manual input file.
> Unresolved — open question #1.

---

## 2. Schedule

| Model field | Excel origin | Source | Endpoint / table | Redundant? |
|---|---|---|---|---|
| `fct_Milestone[MilestoneName]` | `SCHEDULE!C5:C14` | Procore | `/rest/v1.0/projects/{project_id}/schedule` | — |
| `fct_Milestone[ContractStart/Finish]` | `SCHEDULE!D:E` | **Manual** | Contract dates are not in Procore's schedule tool | — |
| `fct_Milestone[BaselineStart/Finish]` | `SCHEDULE!F:G` | Procore | Schedule baseline — **only if baselines are maintained there** | — |
| `fct_Milestone[CurrentStart/Finish]` | `SCHEDULE!H:I` | Procore | ↑ | — |
| `fct_Milestone[ActualStart/Finish]` | `SCHEDULE!J:K` | Procore | ↑ | — |
| `fct_Milestone[StartVariance]` | `SCHEDULE!L` | Derived | `DATEDIFF` | — |
| `fct_Milestone[FinishVariance]` | `SCHEDULE!M` | Derived | `DATEDIFF` | — |
| `fct_ManpowerDaily[WorkerCount]` | `SCHEDULE!Table14` | Procore | `/rest/v1.0/projects/{project_id}/manpower_logs/daily_totals` | — |
| `fct_ManpowerDaily[VendorKey]` | `SCHEDULE!C26:C30` | Procore | `/rest/v1.0/projects/{project_id}/manpower_logs/vendor_options` | — |
| `man_PriorityItems[*]` | `SCHEDULE!Table3714` | **Manual** | Pure narrative | — |
| `man_Flags[BaselineApproved]` | `SCHEDULE!G16` | **Manual** | | — |
| `man_Flags[BaselineRevision]` | `SCHEDULE!G17` | **Manual** | | — |

> **`/rest/v1.0/projects/{project_id}/schedule` returns schedule tasks, not milestones** —
> the OAS has no `milestone` path at all. Affect is also evaluating **Outbuild** for
> scheduling. Need to confirm on the call: does the critical-path milestone list live in
> Procore, in Outbuild, or only in this spreadsheet?

---

## 3. Safety

| Model field | Excel origin | Source | Endpoint / table |
|---|---|---|---|
| `fct_SafetyMonthly[HoursWorked]` | `SAFETY!D` | Sage / ADP | Payroll hours by job. Also `/rest/v1.0/projects/{project_id}/timecard_entries` if Procore Timesheets is used |
| `fct_SafetyMonthly[RecordableIncidents]` | `SAFETY!E` | Procore | `/rest/v1.0/projects/{project_id}/incidents` |
| `fct_SafetyMonthly[Orientations]` | `SAFETY!F` | **Manual** | No system of record — open question #13 |
| `fct_Violation[*]` | `SAFETY!Table15` | **Manual** | Description column is empty in every row |
| `fct_ActivityLog[*]` (safety) | `SAFETY!Table20` | **Manual** | Could move to Procore Daily Logs — open question #12 |

Supporting Procore reference endpoints, all verified:
`/rest/v1.0/companies/{company_id}/incidents/severity_levels` ·
`/rest/v1.0/companies/{company_id}/incidents/statuses` ·
`/rest/v1.0/projects/{project_id}/incidents/injuries` ·
`/rest/v1.0/projects/{project_id}/incidents/near_misses`

> "Recordable" is an OSHA classification. Procore's incident model separates injuries,
> near misses, property damage, and environmental — confirm which of these Affect counts.

---

## 4. Quality

| Model field | Excel origin | Source | Endpoint / table |
|---|---|---|---|
| `fct_QualityMonthly[Observations]` | `QUALITY!D` | Procore | `/rest/v1.0/observations/items` — **fixes defect #2** (currently reads Safety orientations) |
| `fct_QualityMonthly[PunchlistItems]` | `QUALITY!E` | Procore | `/rest/v1.0/punch_items` |
| `fct_QualityItem[DaysPastDue]` | `QUALITY!D38:E38` | Derived | Currently **typed by hand** |
| `fct_QualityItem[DaysToClose]` | `QUALITY!D39:E39` | Derived | Currently **typed by hand** |
| `fct_QualityItem[VendorKey]` "offenders" | `QUALITY!D40:E44` | Derived | `RANKX` by open items — currently typed by hand |
| `fct_QualityItem[*]` (issue log) | `QUALITY!Table16` | Procore + manual | Observations/inspections from Procore; `ACTION PLAN` and `RESPONSIBLE` are manual |
| `fct_ActivityLog[*]` (quality) | `QUALITY!Table16` | Procore | Benchmarks/mockups/commissioning may be Procore inspections |

Supporting: `/rest/v1.0/observations/types` · `/rest/v1.0/punch_item_types` ·
`/rest/v2.0/companies/{company_id}/projects/{project_id}/punch_list/trades` ·
`/rest/v1.0/projects/{project_id}/inspection_logs` · `/rest/v1.0/checklist/lists`

> This is the section with the biggest automation win. Four hand-typed aggregates
> (`avg days past due`, `avg days to close`, ×2 for observations and punchlist) plus a
> hand-ranked offender list all become measures over data Procore already holds.

---

## 5. RFIs & Submittals

| Model field | Excel origin | Source | Endpoint / table |
|---|---|---|---|
| `fct_RfiSubmittal[*]` (RFI) | `SUBMITTALS & RFI!C` | Procore | `/rest/v1.0/projects/{project_id}/rfis` |
| `fct_RfiSubmittal[*]` (Submittal) | `SUBMITTALS & RFI!D` | Procore | `/rest/v1.1/projects/{project_id}/submittals` |
| `fct_RfiSubmittal[TradeKey]` | `SUBMITTALS & RFI!B` | Procore | RFIs carry `cost_code_id`; submittals carry a spec section — mapping to Affect's 29 trades needs confirming |
| `fct_RfiSubmittal[IsCritical]` | implied by "Open Critical" | **TBD** | `/rest/v1.0/projects/{project_id}/rfis/filter_options/priority` — is priority the criterion? Open question #5 |

Supporting: `/rest/v1.0/projects/{project_id}/rfis/filter_options/status` ·
`/rest/v1.1/projects/{project_id}/submittals/{id}/workflow_data`

**Fully automatable — the cleanest single win in the workbook.** The Excel stores only a
per-trade count; pulling the items themselves gives the same chart plus drill-through.

---

## 6. Financial

| Model field | Excel origin | Source | Endpoint / table | Redundant? |
|---|---|---|---|---|
| `fct_FinancialPeriod[OriginalContract]` | `FINANCIALS!C3` | Procore | `/rest/v1.0/prime_contracts` | — |
| `[CurrentContract]` | `C4` | Procore | ↑ (`grand_total`) | — |
| `[PendingChangeOrders]` | `C5` | Procore | `/rest/v2.0/…/prime_change_orders` filtered pending | — |
| `[AgeOfOldestUnapprovedCO]` | `C6` | Derived | `/rest/v1.0/change_order_requests` + `/rest/v1.0/change_order/statuses` | — |
| `[ContingencyRemaining]` | `C9` | **Manual** | Currently `"N/A"` | — |
| `[TotalBilled]` | `C10` | Sage AR | Invoice history by job | ❌ not synced |
| `[BilledThisPeriod]` | `C11` | Sage AR | ↑ | ❌ |
| `[TotalPaid]` | `C12` | Sage AR | Cash receipts | ❌ |
| `[RemainingBalance]` | `C13` | Derived | `CurrentContract − TotalBilled` | — |
| `[Retainage]` | `C14` | Sage AR | Retainage held | ❌ |
| `[CostToComplete]` | `C15` | Procore | Budget forecast — or Sage job cost | ✅ after connector |
| `[ArOutstanding]` | — (needed for cash position) | Sage AR | Open AR by job | ❌ |
| `[AgingBalance]` | `F57` | Sage AR | AR aging | ❌ |
| `[TradeCostsBudgeted]` | `D60` | Procore | `/rest/v1.0/projects/{project_id}/budget` | — |
| `[TradeCostsCommitted]` | `D61` | Procore | `/rest/v2.0/…/commitment_contracts` | — |
| `[OtHours]` | `FINANCIALS!J` | Sage / ADP | Payroll | ❌ |
| `[ProfitabilityStatusKey]` | `C7` | **Manual** | Human judgment | — |
| `[MonthEndClosedOut]` etc. | `E65:E67` | **Manual** | Process attestations | — |
| `fct_Invoice[SentDate/PaidDate]` | `FINANCIALS!Table11012` | Sage AR | Invoice + cash receipt dates | ❌ |
| `fct_BudgetLine[BudgetAmount]` | `FINANCIALS!C19:C20` | Procore | `/rest/v1.0/projects/{project_id}/budget`, `/rest/v2.0/…/budget_line_items/{id}` | — |
| `[ForecastAmount]` | `D19:D20` | Procore | ↑ | — |
| `[SpentToDate]` | `E19:E20` | Procore or Sage | `/rest/v1.1/projects/{project_id}/direct_costs` | ✅ after connector |
| `[CommittedAmount]` | — | Procore | `/rest/v2.0/…/commitment_contracts/{id}/summary` | — |
| `fct_ChangeOrder[*]` | implied by `C5`,`C6` | Procore | `/rest/v1.0/potential_change_orders`, `/rest/v2.0/…/prime_change_orders`, `/rest/v2.0/…/commitment_change_orders` | — |

**Cash Position** (`FINANCIALS!C8`) is a dropdown in the Excel but the formula is written
out in the note at `G8`:
`(Cash Collected + AR Outstanding) ÷ Remaining Forecasted Cost`.
Fully computable from Sage — becomes a measure, not an input. Open question #7.

Also verified and relevant: `/rest/v1.0/prime_contracts/{prime_contract_id}/payment_applications`
and `/rest/v1.1/requisitions` — if Affect bills through Procore rather than Sage, billing
data may already be in Procore. **Worth asking.**

---

## 7. Scorecard

| Model field | Excel origin | Source |
|---|---|---|
| `dim_ScorecardWeight[Weight]` | `SCORECARD CALC!F4:F30` | Static config |
| `dim_ScorecardBand[*]` | `SCORECARD CALC!C4:D30` | Static config (⚠️ 3 bands corrected — defect #1) |
| `fct_DailyLog[DistributedSameDay]` | `SCORECARD CALC!E28` | Procore `/rest/v1.0/projects/{project_id}/daily_log_headers` |
| `man_Survey[Score]` | `SCORECARD CALC!C36:C41` | **Manual** |
| `man_Survey[QuestionText]` | — | **Manual — not stored anywhere in the workbook.** Open question #10 |

Every other scorecard input is a measure over data already mapped above.

---

## 8. Manual-only — the ~40%

No integration produces these. They need the input file described in
[`manual-input-template.md`](manual-input-template.md).

| Model table | Excel origin | Fields |
|---|---|---|
| `man_Wins` | `WINS!C3:C6` | Description |
| `man_FocusAreas` | `WINS!C9:C12` | Description |
| `man_Risks` | `RISKS!Table37` | Description, Impact, Mitigation, Owner, Status |
| `man_PriorityItems` | `SCHEDULE!Table3714` | Item, Status, Delays, Recovery plan, Forecast impact, Notes |
| `man_Flags` | `SCHEDULE!G16:G17`, `FINANCIALS!C7`, `E65:E67` | Baseline approved, Revision, Profitability, 3 cost-mgmt flags |
| `man_Survey` | `SCORECARD CALC!C34:C41` | Surveyed party, Q1–Q6 scores, question text |
| Contract dates | `SCHEDULE!D:E` | Per milestone |
| Contingency remaining | `FINANCIALS!C9` | |
| Safety orientations | `SAFETY!F` | Until a system of record exists |
| Safety activity log | `SAFETY!Table20` | Toolbox talks, standdowns, visitors |
| Violations | `SAFETY!Table15` | |

---

## Procore integration notes

**Auth.** OAuth 2.0. For unattended ETL use the **client credentials** grant with a
service account (Procore calls this a "Data Connector App" / installation-based auth).
Verify with Rebecca which grant her existing script uses — a user-based token will expire
and break the pipeline.

**Company header.** v2.0 endpoints require the `Procore-Company-Id` header. v1.0 endpoints
generally take `company_id` in the path or as a query parameter. Mixing the two is a common
source of 403s.

**Rate limits.** Procore throttles per hour per app. Honour `Retry-After` on `429`.
For a company of Affect's size this should not bind, but the ETL needs the retry anyway.

**Pagination.** `page` and `per_page` (max 1000 on most v1.0 endpoints). The `Total` and
`Link` response headers drive the loop.

**Incremental loading.** Most list endpoints accept `filters[updated_at]` with an ISO 8601
range. Use it — full refreshes will not scale as the project count grows.

**API version mixing is expected.** Affect will need v1.0, v1.1, and v2.0 in the same
pipeline (e.g. RFIs are v1.0, submittals v1.1, commitments v2.0). Not a mistake; it is how
Procore's API is versioned.

Endpoint reference: [`../resources/procore/endpoints-cheatsheet.md`](../resources/procore/endpoints-cheatsheet.md)

## Sage 100 Contractor integration notes

⚠️ **Affect runs Sage 100 *Contractor*, not Sage 100 ERP.** The documentation link
circulated on Jul 22 (`help-sage100.na.sage.com/2023/FLOR/`) is the File Layouts and Object
Reference for **Sage 100 ERP** — a different product with a different schema. Correct
references in [`../resources/sage-100-contractor/README.md`](../resources/sage-100-contractor/README.md).

**Current state.** Read-only SQL Server connection, queried **live from Power BI today** —
it bypasses the Lakehouse entirely. That works for one report and stops working the moment
there are several.

**Open items for the call:**
- Which tables/views does the read-only account actually expose?
- Where does the SQL Server live? On-prem means an **on-premises data gateway** is required
  for Fabric ingestion — a real dependency with lead time.
- Which queries does Power BI run against it today? Those are the starting point for the
  ingestion, and they encode knowledge nobody has written down.
- Sage 100 Contractor maintains **audit tables** for history — worth knowing whether they
  are available, since they would give change tracking for free.
