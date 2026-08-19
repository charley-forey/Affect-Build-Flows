# Semantic Model

> **Status — design intent, superseded by what shipped (2026-08-19).** This star schema was
> derived from the Excel field inventory in July 2026 and is the design record, not a
> description of the delivered model. Two semantic models are now live, defined in TMDL under
> `foundation/charley-dev/04-semantic_models/`: *Affect Project Report* (37 tables,
> 99 measures, 45 relationships) and a **second** model this document predates entirely,
> *Project Quality Plan* (19 tables plus `_Measures`, 42 measures, 23 relationships).
> The build diverged — more tables, more measures, `man_*` sourced from SharePoint lists —
> but the grain, key and star-discipline decisions below are what it was built from.
> For the delivered shape read the TMDL and `foundation/charley-dev/_docs/`.

Star schema for the Power BI dashboard replacing the Excel Monthly Progress Report.

Derived from [`../analysis/excel-tracker/field-inventory.md`](../analysis/excel-tracker/field-inventory.md).
Measures live in [`measures.dax`](measures.dax).

## Design principles

1. **One `dim_Date`, marked as a date table.** This single change eliminates the entire
   `INDEX/MATCH` + `AU4` mechanic and every defect that flows from it (mismatched month
   anchors, `#N/A` tiles, hand-pasted prior-month rows, `TODAY()` volatility).
2. **Star, not snowflake.** Facts join to dimensions directly. No dimension joins another.
3. **Everything numeric stays numeric.** No `TEXT(...) & " / " & TEXT(...)` tiles, no
   `"NA"` sentinels, no `"0 days"` strings. Formatting is a visual concern.
4. **Status is a dimension, not a string.** See
   [`../analysis/excel-tracker/dropdowns-and-status.md`](../analysis/excel-tracker/dropdowns-and-status.md).
5. **Multi-project from day one.** The Excel is one workbook per project. Every fact
   carries `ProjectKey` so leadership can see a portfolio, not just one job.

## Overview

```
                          ┌──────────────┐
                          │   dim_Date   │  (marked as date table)
                          └──────┬───────┘
                                 │ 1
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼ *                      ▼ *                      ▼ *
┌───────────────┐      ┌──────────────────┐     ┌──────────────────┐
│ fct_Milestone │      │ fct_SafetyMonthly│     │ fct_FinancialPeriod│
│ fct_Invoice   │      │ fct_QualityMonthly│    │ fct_BudgetLine    │
│ fct_ChangeOrder│     │ fct_QualityItem  │     │ fct_ManpowerDaily │
│ fct_Violation │      │ fct_RfiSubmittal │     │ fct_ActivityLog   │
└───────┬───────┘      └────────┬─────────┘     └────────┬─────────┘
        │ *                     │ *                      │ *
        └───────────────────────┼────────────────────────┘
                                │
        ┌───────────────┬───────┴───────┬───────────────┬──────────────┐
        ▼ 1             ▼ 1             ▼ 1             ▼ 1            ▼ 1
┌──────────────┐ ┌────────────┐ ┌────────────┐ ┌───────────┐ ┌──────────────┐
│ dim_Project  │ │ dim_Status │ │ dim_Trade  │ │ dim_Owner │ │ dim_CostCode │
└──────────────┘ └────────────┘ └────────────┘ └───────────┘ └──────────────┘

Manual/narrative (same dims, no additive measures):
  man_Wins · man_Risks · man_PriorityItems · man_Flags · man_Survey

Config:
  dim_ScorecardWeight · dim_ScorecardBand
```

---

## Dimensions

### `dim_Date`
**Grain:** one row per calendar day. **Mark as date table** on `[Date]`.

| Column | Type | Notes |
|---|---|---|
| `Date` | date | Key |
| `Year`, `Quarter`, `Month`, `MonthName`, `MonthYear` | | |
| `MonthStart` | date | First of month — the join key for all monthly facts |
| `MonthEnd` | date | |
| `MonthOffset` | int | 0 = current month; enables relative filtering |
| `IsMonthEnd` | bool | |

Generate to cover the longest project plus a forecast tail. The workbook allows 30–31
project months; span at least 2023-01-01 → 2030-12-31.

> **This table is the fix for defect #4** (three different month anchors) and **defect #5**
> (`TODAY()` volatility). Monthly facts store `MonthStart` and relate on it, so a month
> either exists in the calendar or it doesn't — there is no silent `#N/A`.

### `dim_Project`
**Grain:** one row per project.

| Column | Type | Notes |
|---|---|---|
| `ProjectKey` | int | Surrogate |
| `ProjectNumber` | text | ⚠️ **The linchpin.** The `YY-000` from the filename convention |
| `ProcoreProjectId` | int | |
| `SageJobNumber` | text | |
| `ProjectName` | text | |
| `ClientName` | text | |
| `OriginalContractAmount` | decimal | |
| `ContractStart`, `ContractFinish` | date | From the contract, not the schedule |
| `Status` | text | Active / Complete / On Hold |

> **Open question #1 in `defects-and-questions.md`:** is `ProjectNumber` the same value in
> Procore and Sage, entered identically? Nothing in this model joins until that is settled.

### `dim_Status`
**Grain:** one row per status value per domain. Full seed data in
[`../analysis/excel-tracker/dropdowns-and-status.md`](../analysis/excel-tracker/dropdowns-and-status.md).

| Column | Type | Notes |
|---|---|---|
| `StatusKey` | int | Surrogate |
| `Domain` | text | `RiskImpact`, `RiskStatus`, `ScheduleStatus`, `SafetyStatus`, `QualityStatus`, `BudgetStatus`, `CashPosition`, `Profitability`, `YesNo` |
| `Code` | text | `HIGH`, `ON_TRACK`, … — join on this, never on the label |
| `Label` | text | Display |
| `Emoji` | text | Kept for export parity only |
| `RAG` | text | Red / Amber / Green / Neutral |
| `SortOrder` | int | **Sort `Label` by this** — makes "Ranked by Severity" actually rank |
| `HexColor` | text | Drives conditional formatting |

Role-playing: facts reference it multiple times (a quality item has both a status and a
category). Use **inactive relationships + `USERELATIONSHIP`**, or separate dimension
copies where the report needs both filtered simultaneously.

### `dim_Trade`
29 trades from `DROPDOWN!M`, **trimmed** (defect #9) and deduplicated.

| Column | Type | Notes |
|---|---|---|
| `TradeKey` | int | |
| `TradeName` | text | Trimmed |
| `CsiDivision` | text | Optional — the bridge to Procore cost codes. Open question #14 |
| `SortOrder` | int | Construction sequence, not alphabetical |

### `dim_Owner`
9 roles from `DROPDOWN!C`. Used for risk owner, safety responsible, quality responsible.

| Column | Type | Notes |
|---|---|---|
| `OwnerKey` | int | |
| `RoleName` | text | |
| `SortOrder` | int | Seniority — confirm the hierarchy with Affect |
| `PersonName` | text | Optional; the Excel tracks role only |

### `dim_CostCode`
Not in the Excel except implicitly (the GC/GR section). Needed for real budget analysis.

| Column | Type | Notes |
|---|---|---|
| `CostCodeKey` | int | |
| `CostCode` | text | |
| `Description` | text | |
| `CostType` | text | Labor / Material / Sub / Equipment / Other |
| `Division` | text | |
| `ProcoreCostCodeId` | int | |
| `SageCostCode` | text | ⚠️ Open question #2 — do these reconcile? |

### `dim_Vendor`
| Column | Type |
|---|---|
| `VendorKey` | int |
| `VendorName` | text |
| `ProcoreVendorId` | int |
| `SageVendorId` | text |

### `dim_ActivityCategory`
Lists `DROPDOWN!I` (16 safety) and `DROPDOWN!K` (11 quality), split on the en dash.

| Column | Type | Notes |
|---|---|---|
| `CategoryKey` | int | |
| `Domain` | text | `Safety` / `Quality` |
| `CategoryType` | text | `Toolbox Talk`, `Benchmark`, `Inspection`, `Notable Visitor` … |
| `CategoryQualifier` | text | `Completed`, `Scheduled`, `NCR`, `FDNY` … |
| `FullLabel` | text | Original string, for parity |

Splitting turns a flat 16-item picklist into a filterable hierarchy.

---

## Fact tables

### `fct_Milestone`
**Grain:** one row per project per milestone per reporting month.
**Source:** `SCHEDULE!Table5` (C3:M14) → Procore Schedule / Outbuild + manual contract dates.

| Column | Type | Notes |
|---|---|---|
| `ProjectKey`, `ReportMonth` | | `ReportMonth` → `dim_Date[MonthStart]` |
| `MilestoneName` | text | |
| `MilestoneOrder` | int | Preserves the workbook's row order |
| `IsSubstantialCompletion` | bool | The protected terminator row |
| `ContractStart/Finish` | date | Nullable — `"NA"` becomes null (defect #7) |
| `BaselineStart/Finish` | date | |
| `CurrentStart/Finish` | date | |
| `ActualStart/Finish` | date | |
| `StartVariance` | int | `DATEDIFF(BaselineStart, ActualStart, DAY)` |
| `FinishVariance` | int | `DATEDIFF(BaselineFinish, CurrentFinish, DAY)` |
| `HasDateInversion` | bool | **Data-quality flag for defect #6** — start > finish |

Storing a row per reporting month gives what the Excel structurally cannot: baseline drift
over time, and a defensible record of what was forecast when.

### `fct_SafetyMonthly`
**Grain:** one row per project per month. **Source:** `SAFETY!Table1`.

| Column | Type | Source |
|---|---|---|
| `ProjectKey`, `MonthStart` | | |
| `HoursWorked` | decimal | Sage payroll / ADP / Procore timecards — open question |
| `RecordableIncidents` | int | Procore `/rest/v1.0/projects/{project_id}/incidents` |
| `Orientations` | int | Manual — no system of record today |

### `fct_Violation`
**Grain:** one row per violation. **Source:** `SAFETY!Table15`.

| Column | Type | Notes |
|---|---|---|
| `ProjectKey`, `ReportedDate` | | |
| `ViolationNumber` | int | |
| `Description` | text | Empty in every row of the sample |
| `Value` | decimal | |
| `StatusKey` | int | → `dim_Status` (`Open` / `Closed`) |

Counting by `StatusKey` rather than by value is **the fix for defect #3**.

### `fct_QualityMonthly`
**Grain:** one row per project per month. **Source:** `QUALITY!Table18`.

| Column | Type | Source |
|---|---|---|
| `ProjectKey`, `MonthStart` | | |
| `Observations` | int | Procore `/rest/v1.0/observations/items` — **fixes defect #2** |
| `PunchlistItems` | int | Procore `/rest/v1.0/punch_items` |

### `fct_QualityItem`
**Grain:** one row per quality issue. **Source:** `QUALITY!Table16` + Procore.

Replaces the Excel's hand-typed averages (`QUALITY!Table17`) with computable ones.

| Column | Type | Notes |
|---|---|---|
| `ProjectKey`, `CreatedDate`, `DueDate`, `ClosedDate` | | |
| `ItemType` | text | `Observation` / `Punchlist` |
| `CategoryKey`, `StatusKey`, `TradeKey`, `VendorKey`, `OwnerKey` | int | |
| `Description`, `Outcome`, `ActionPlan` | text | |
| `Timeframe` | text | Lookback / Lookahead |
| `DaysPastDue` | int | Calculated |
| `DaysToClose` | int | Calculated |

"Main offenders" stops being a hand-typed list and becomes `TOPN` by open items per vendor.

### `fct_RfiSubmittal`
**Grain:** one row per RFI or submittal. **Source:** `SUBMITTALS & RFI!Table22` → Procore.

| Column | Type | Notes |
|---|---|---|
| `ProjectKey`, `TradeKey` | | |
| `ItemType` | text | `RFI` / `Submittal` |
| `ItemNumber`, `Subject` | text | |
| `IsCritical` | bool | ⚠️ Open question #5 — what defines critical? |
| `StatusKey` | int | |
| `CreatedDate`, `DueDate`, `RespondedDate` | date | |
| `DaysOpen` | int | |

The Excel stores only a per-trade **count**. Storing the items themselves gives the same
bar chart plus drill-through to the actual RFIs — free.

### `fct_FinancialPeriod`
**Grain:** one row per project per month. **Source:** `FINANCIALS!Table8`.

Note the Excel's `THIS PERIOD` / `LAST PERIOD` column pair collapses into rows over time —
the hand-keyed `LAST PERIOD` column disappears entirely.

| Column | Type | Source |
|---|---|---|
| `ProjectKey`, `MonthStart` | | |
| `OriginalContract`, `CurrentContract` | decimal | Procore prime contract / Sage |
| `PendingChangeOrders` | decimal | Procore |
| `AgeOfOldestUnapprovedCO` | int | Procore — derivable |
| `ContingencyRemaining` | decimal | Manual |
| `TotalBilled`, `BilledThisPeriod`, `TotalPaid` | decimal | Sage AR |
| `RemainingBalance`, `Retainage`, `CostToComplete` | decimal | Sage |
| `ArOutstanding` | decimal | Sage — needed for cash position |
| `AgingBalance` | decimal | Sage |
| `TradeCostsBudgeted`, `TradeCostsCommitted` | decimal | Procore commitments |
| `OtHours` | decimal | Sage payroll / ADP |
| `ProfitabilityStatusKey` | int | Manual judgment |
| `MonthEndClosedOut`, `ProcoreForecastingInLine`, `MonitoredResourcesUpdated` | bool | Manual attestations |

`CashPosition` is deliberately **absent** — it becomes a measure. See open question #7.

### `fct_Invoice`
**Grain:** one row per invoice. **Source:** `FINANCIALS!Table11012` → Sage AR.

| Column | Type |
|---|---|
| `ProjectKey`, `InvoiceNumber` | |
| `SentDate`, `PaidDate` | date |
| `Amount`, `AmountPaid`, `RetainageHeld` | decimal |
| `DaysToPayment` | int (calculated) |

### `fct_BudgetLine`
**Grain:** one row per project per cost code per month.
**Source:** `FINANCIALS!Table11011` — currently only 2 rows (defect #13); this is the
section to expand to full cost-code coverage.

| Column | Type | Source |
|---|---|---|
| `ProjectKey`, `CostCodeKey`, `MonthStart` | | |
| `BudgetAmount`, `ForecastAmount`, `SpentToDate`, `CommittedAmount` | decimal | Procore budget line items / Sage job cost |

`BudgetStatus` becomes a measure using the rule already written in `FINANCIALS!H18:J21` —
no more hand-picked dropdown.

### `fct_ChangeOrder`
**Grain:** one row per change order. Procore prime + commitment COs.

| Column | Type |
|---|---|
| `ProjectKey`, `ChangeOrderNumber`, `Type` | |
| `StatusKey`, `Amount` | |
| `CreatedDate`, `ApprovedDate`, `DaysOpen` | |

Turns "age of oldest unapproved CO" from a typed number into a measure.

### `fct_ManpowerDaily`
**Grain:** one row per project per vendor per day.
**Source:** `SCHEDULE!Table14` → Procore `/manpower_logs/daily_totals`.

| Column | Type |
|---|---|
| `ProjectKey`, `VendorKey`, `Date` |
| `WorkerCount`, `Hours` |

Daily grain gives the Excel's "avg daily over past 30 days" for free, over any window, and
removes the 5-subcontractor cap.

### `fct_ActivityLog`
**Grain:** one row per safety or quality activity. **Source:** `SAFETY!Table20` + `QUALITY!Table16`.

| Column | Type |
|---|---|
| `ProjectKey`, `ActivityDate`, `Domain` |
| `CategoryKey`, `StatusKey`, `OwnerKey` |
| `Timeframe`, `Description`, `Notes` |

### `fct_DailyLog`
**Grain:** one row per project per day.
**Source:** Procore `/rest/v1.0/projects/{project_id}/daily_log_headers`.

Not represented in the Excel — `SCORECARD CALC!E28` ("Daily Reports not complete and
distributed on same day") is typed in by hand. This table derives it.

| Column | Type | Notes |
|---|---|---|
| `ProjectKey`, `LogDate` | | |
| `IsComplete` | bool | |
| `CreatedAt`, `DistributedAt` | datetime | |
| `DistributedSameDay` | bool | ⚠️ Open question: how does Affect define "same day"? |

---

## Manual / narrative tables

Loaded from the input workbook — see [`manual-input-template.md`](manual-input-template.md).
These carry no additive measures; they are displayed as tables and cards.

| Table | Grain | Replaces | Cap removed |
|---|---|---|---|
| `man_Wins` | project × month × win | `WINS` | 4 → unlimited |
| `man_FocusAreas` | project × month × focus area | `WINS` rows 9–12 | 4 → unlimited |
| `man_Risks` | project × month × risk | `RISKS!Table37` | 8 → unlimited |
| `man_PriorityItems` | project × month × item | `SCHEDULE!Table3714` | 5 → unlimited |
| `man_Flags` | project × month | Cost-mgmt flags, baseline approval, profitability | — |
| `man_Survey` | project × month × question | `SCORECARD CALC!C36:C41` | 6 → unlimited |

`man_Risks` gains what the Excel lacks: `RiskNumber` (never displayed today), a real
`StatusKey`/`ImpactKey`, and a `SortOrder` so the "Ranked by Severity" header is honest.

`man_Survey` needs a `QuestionText` column — **the six questions are not stored anywhere in
the workbook** (open question #10).

---

## Configuration tables

### `dim_ScorecardWeight`
Weights as data, so Affect can retune without a model change.

| Category | Weight |
|---|---|
| Accounts Receivable | 0.12 |
| Profitability | 0.12 |
| Cash Position | 0.12 |
| Change Orders | 0.08 |
| Safety Incidents | 0.14 |
| Schedule Performance | 0.15 |
| Completion Variance | 0.15 |
| Observations | 0.10 |
| Daily Reports | 0.02 |
| **Total** | **1.00** |

| Column | Type |
|---|---|
| `CategoryKey`, `CategoryName`, `Weight`, `SortOrder`, `EffectiveFrom`, `EffectiveTo` |

`EffectiveFrom`/`To` preserve historical scores when weights change — otherwise retuning
silently rewrites last year's numbers.

### `dim_ScorecardBand`
The 3/2/0 thresholds as data. **This is where defects #1a–1c get fixed once**, in a table,
rather than in nine nested `IF`s.

| Column | Type | Notes |
|---|---|---|
| `CategoryKey` | int | |
| `Score` | int | 3, 2, or 0 |
| `MinValue`, `MaxValue` | decimal | Numeric bands |
| `MatchValue` | text | Text bands (profitability, cash position) |
| `BandLabel` | text | `< 45`, `46-60` … |

Corrected seed values (⚠️ marks a fix vs. the workbook):

| Category | 3 pts | 2 pts | 0 pts |
|---|---|---|---|
| Accounts Receivable | < 45 days | 45–60 | > 60 | ⚠️ driver → avg days to payment |
| Profitability | Within Range | Out of range, has plan | Margin fade, no plan |
| Cash Position | ≥ 100% | 50–99% | < 50% |
| Change Orders | ≤ 45 days | 46–60 | > 60 |
| Safety Incidents | 0 | 1 | ≥ 2 |
| Schedule Performance | < **0.05** | 0.05–0.09 | ≥ **0.10** | ⚠️ fraction not integer |
| Completion Variance | ≤ 0 days | 1–14 | ≥ 15 | ⚠️ numeric, no `"0 days"` text |
| Observations | < 5 days | 6–10 | ≥ 11 |
| Daily Reports | < 2 | 3–4 | ≥ 5 |

---

## Relationships

| From | To | Cardinality | Direction | Active |
|---|---|---|---|---|
| `fct_*[ProjectKey]` | `dim_Project[ProjectKey]` | \* : 1 | Single | ✅ |
| `fct_*[MonthStart]` / `[Date]` | `dim_Date[Date]` | \* : 1 | Single | ✅ |
| `fct_QualityItem[TradeKey]` | `dim_Trade[TradeKey]` | \* : 1 | Single | ✅ |
| `fct_RfiSubmittal[TradeKey]` | `dim_Trade[TradeKey]` | \* : 1 | Single | ✅ |
| `fct_*[StatusKey]` | `dim_Status[StatusKey]` | \* : 1 | Single | ✅ |
| `fct_QualityItem[CategoryKey]` | `dim_ActivityCategory[CategoryKey]` | \* : 1 | Single | ✅ |
| `fct_*[OwnerKey]` | `dim_Owner[OwnerKey]` | \* : 1 | Single | ✅ |
| `fct_BudgetLine[CostCodeKey]` | `dim_CostCode[CostCodeKey]` | \* : 1 | Single | ✅ |
| `fct_ManpowerDaily[VendorKey]` | `dim_Vendor[VendorKey]` | \* : 1 | Single | ✅ |
| `fct_Milestone[ActualFinish]` | `dim_Date[Date]` | \* : 1 | Single | ❌ inactive — `USERELATIONSHIP` |
| `fct_Invoice[PaidDate]` | `dim_Date[Date]` | \* : 1 | Single | ❌ inactive |

**No bidirectional filters.** They create ambiguity and hurt performance; use
`CROSSFILTER` in the specific measure if a case genuinely needs it.

## Notes on implementation

**Storage mode.** Import for everything. Total volume is small (one project produces ~30
monthly rows per fact). Direct Lake becomes worth considering only once the Lakehouse
tables are live and the portfolio has grown.

**Refresh.** Monthly is the current business cadence, but nightly costs nothing and means
the dashboard is never stale. Open question #15 — Affect may want live once they see it.

**Row-level security.** Not required initially (single tenant, internal). If PMs should
see only their own projects later, add an RLS role filtering `dim_Project` by a
`ProjectManagerEmail` column against `USERPRINCIPALNAME()`.

**Naming.** `fct_` / `dim_` / `man_` prefixes; PascalCase columns; measures in a dedicated
`_Measures` table so they sort to the top of the field list.

**Data-quality flags.** `HasDateInversion` on `fct_Milestone` is the pattern — surface
bad data on a hidden diagnostics page rather than letting it flow silently into a rollup,
which is exactly how defects #6 and #12 survived in the Excel.
