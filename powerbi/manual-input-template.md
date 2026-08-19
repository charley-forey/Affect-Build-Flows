# Manual Input Template

> **Status — superseded (2026-08-19).** This specifies a locked-down Excel input workbook on
> SharePoint, drafted July 2026. That workbook was never built. What shipped instead is
> **17 SharePoint lists / 140 columns**, generated from the gold DDL by
> `foundation/charley-dev/_local/make_sharepoint.py`, plus a CSV import path that works today.
> Current truth: `foundation/charley-dev/_docs/sharepoint-lists.md` and `_docs/manual-input.md`.
> The field-level specs below are still the source of the column design and the validation
> rules, which is why they are kept intact.

Spec for the input workbook that replaces the ~40% of the Monthly Progress Report that
exists nowhere but Excel.

## Why this exists

No amount of Procore or Sage integration produces wins, risk registers, recovery-plan
narratives, client-satisfaction scores, or process attestations. They are judgment and
commentary, and they are the part of the report leadership actually reads.

**Approach: a slim, locked-down Excel workbook on SharePoint that Fabric ingests on a
schedule.** Chosen over Power App / Dataverse forms and over pushing everything into
Procore custom fields because it has the lowest change-management cost — PMs keep working
in the tool they already use, and the first version can ship in days rather than weeks.

Reassess once it has been in use a few months. If data quality suffers or PMs want mobile
entry, Dataverse + a Power App is the natural next step and this schema ports directly.

## Design rules

1. **One workbook, all projects** — not one per project. `ProjectNumber` on every sheet.
2. **Real Excel Tables only.** They auto-expand, which means Power Query never has to
   guess where the data ends.
3. **Codes, not display strings.** `HIGH`, not `🔴 High`. Dropdowns show the friendly
   label and store the code via a lookup column.
4. **ISO dates** (`YYYY-MM-DD`). The current workbook's `MM/DD/YYYY` instruction is fine
   for humans and a hazard for locale-dependent parsing.
5. **No formulas.** Everything computed lives in the model. The current file's chained
   `EOMONTH` sequences and hand-pasted prior-month rows are exactly what to remove.
6. **No merged cells.** Anywhere.
7. **Sheet protection on**, with only the input columns unlocked. The current file relies
   on blue text as the only marker of what's editable — a convention with no enforcement.
8. **No caps.** Add rows freely; the model has no fixed 4-wins or 8-risks limit.
9. **`ReportMonth` on every row**, always the first of the month. One column instead of
   four inconsistent chained sequences.

## Workbook structure

`Affect_ProjectReport_Input.xlsx` — SharePoint, one file, one row per entry.

| Sheet | Table | Replaces | Grain |
|---|---|---|---|
| `Wins` | `tblWins` | `WINS!C3:C6` | project × month × win |
| `FocusAreas` | `tblFocusAreas` | `WINS!C9:C12` | project × month × focus area |
| `Risks` | `tblRisks` | `RISKS!Table37` | project × month × risk |
| `PriorityItems` | `tblPriorityItems` | `SCHEDULE!Table3714` | project × month × item |
| `MilestoneContractDates` | `tblContractDates` | `SCHEDULE!D:E` | project × milestone |
| `SafetyActivity` | `tblSafetyActivity` | `SAFETY!Table20` | project × activity |
| `Violations` | `tblViolations` | `SAFETY!Table15` | project × violation |
| `SafetyManual` | `tblSafetyManual` | `SAFETY!F` (orientations) | project × month |
| `Flags` | `tblFlags` | `SCHEDULE!G16:G17`, `FINANCIALS!C7`, `C9`, `E65:E67` | project × month |
| `Survey` | `tblSurvey` | `SCORECARD CALC!C34:C41` | project × month × question |
| `_Lists` | — | `DROPDOWN` | validation source, hidden |

---

## Sheet specs

### `Wins` / `FocusAreas`

| Column | Type | Required | Notes |
|---|---|---|---|
| `ProjectNumber` | text | ✅ | Dropdown from `_Lists` |
| `ReportMonth` | date | ✅ | First of month |
| `Sequence` | int | ✅ | Display order |
| `Description` | text | ✅ | No length limit — the current header's *"TEXT NEEDS TO FIT IN THE COLUM WIDTH AND HEIGHT"* is a layout constraint that no longer applies |

### `Risks`

| Column | Type | Required | Notes |
|---|---|---|---|
| `ProjectNumber` | text | ✅ | |
| `ReportMonth` | date | ✅ | |
| `RiskNumber` | int | ✅ | Never displayed on the Excel dashboard; carried here so risks are trackable across months |
| `Description` | text | ✅ | |
| `ImpactCode` | text | ✅ | `HIGH` / `MEDIUM` / `LOW` |
| `MitigationStrategy` | text | | |
| `OwnerRole` | text | ✅ | From the 9-role list |
| `StatusCode` | text | ✅ | `NOT_STARTED` / `PLANNED` / `IN_PROGRESS` / `COMPLETE` |

Carrying `RiskNumber` across months turns the register into something with history — you
can finally answer "how long has this risk been open?"

### `PriorityItems`

| Column | Type | Required | Notes |
|---|---|---|---|
| `ProjectNumber`, `ReportMonth` | | ✅ | |
| `ScheduleItem` | text | ✅ | **The Excel captured this but never displayed it** — recovery plans appeared with no item attached |
| `StatusCode` | text | ✅ | `ON_TRACK` / `BEHIND` / `AT_RISK` |
| `CriticalDelays` | text | | |
| `RecoveryPlan` | text | | *"critical if you're off track — list actionable steps, not just 'monitoring'"* |
| `ForecastImpact` | text | | |
| `Notes` | text | | |

### `MilestoneContractDates`

Contract dates are not in Procore's schedule tool, so they stay manual. Baseline, current,
and actual dates come from Procore — **do not duplicate them here.**

| Column | Type | Required |
|---|---|---|
| `ProjectNumber` | text | ✅ |
| `MilestoneName` | text | ✅ |
| `MilestoneOrder` | int | ✅ |
| `IsSubstantialCompletion` | bool | ✅ |
| `ContractStart` | date | |
| `ContractFinish` | date | |

Leave blank rather than typing `"NA"`. Blank is a null; `"NA"` is a string that poisons the
column's data type (defect #7).

### `SafetyActivity`

| Column | Type | Required | Notes |
|---|---|---|---|
| `ProjectNumber`, `ActivityDate` | | ✅ | |
| `Timeframe` | text | ✅ | `Lookback` / `Lookahead` |
| `CategoryType` | text | ✅ | `Toolbox Talk`, `Safety Standdown`, `Notable Visitor`, `Safety Win`, `High-Risk Item`, `Weekend/OT Work` |
| `CategoryQualifier` | text | ✅ | `Completed`, `Scheduled`, `DOB`, `FDNY`, `OSHA`, `Client`, `Other` … |
| `Description` | text | ✅ | |
| `StatusCode` | text | ✅ | |
| `Notes` | text | | |
| `ResponsibleRole` | text | ✅ | |

Splitting the Excel's 16 flat category strings into type + qualifier makes them filterable
— "show me all FDNY visits" becomes possible.

### `Violations`

| Column | Type | Required | Notes |
|---|---|---|---|
| `ProjectNumber`, `ViolationNumber`, `ReportedDate` | | ✅ | |
| `Description` | text | ✅ | **Empty in every row of the current file** — worth asking whether it is used |
| `Value` | decimal | ✅ | `0` is valid and meaningful |
| `StatusCode` | text | ✅ | `OPEN` / `CLOSED` |
| `ClosedDate` | date | | |

A `$0` open violation must be enterable and must count. The Excel's `COUNTIF(...,">1")`
made those invisible (defect #3).

### `SafetyManual`

| Column | Type | Required | Notes |
|---|---|---|---|
| `ProjectNumber`, `ReportMonth` | | ✅ | |
| `Orientations` | int | ✅ | No system of record today — open question #13 |
| `HoursWorked` | decimal | | **Only if not sourced from Sage/ADP.** Prefer the system |

### `Flags`

One row per project per month.

| Column | Type | Notes |
|---|---|---|
| `ProjectNumber`, `ReportMonth` | | |
| `BaselineApproved` | bool | |
| `BaselineRevision` | text | `Rev#1`… |
| `ProfitabilityCode` | text | `IN_RANGE` / `OUT_WITH_PLAN` / `MARGIN_FADE` |
| `ContingencyRemaining` | decimal | |
| `MonthEndClosedOut` | bool | |
| `ProcoreForecastingInLine` | bool | |
| `MonitoredResourcesUpdated` | bool | |
| `DailyReportsNotSameDay` | int | Interim, until derived from Procore daily logs |

**`CashPosition` is deliberately absent.** It is a dropdown in the current workbook, but
the formula is written out in `FINANCIALS!G8` and is fully computable from Sage — it
becomes a measure. See open question #7.

### `Survey`

| Column | Type | Required | Notes |
|---|---|---|---|
| `ProjectNumber`, `ReportMonth` | | ✅ | |
| `SurveyedParty` | text | ✅ | Currently `ANONYMOUS` |
| `QuestionNumber` | int | ✅ | |
| `QuestionText` | text | ✅ | ⚠️ **Not stored anywhere in the current workbook** — only the scores. Need the questionnaire from Affect (open question #10) |
| `Score` | int | ✅ | 1–5 |

### `_Lists` (hidden)

Every validation list, sourced from `DROPDOWN` and **cleaned**:

- Trades: 29 values, **trimmed** (12 currently carry trailing whitespace — defect #9)
- Statuses: code + label pairs per domain, deduplicated (`🟢  Passed` appears twice)
- Owner roles: the 9 values
- Project numbers: from `dim_Project`

Full seed data: [`../analysis/excel-tracker/dropdowns-and-status.md`](../analysis/excel-tracker/dropdowns-and-status.md).

---

## Ingestion into Fabric

**Storage.** SharePoint document library, versioning on. Versioning gives a free audit
trail — who changed what, when — which the current per-project file naming approximates
but does not guarantee.

**Pipeline.** Fabric Data Pipeline → SharePoint connector → Lakehouse `bronze` (raw) →
notebook transform → `silver` (typed, validated) → `gold` (`man_*` tables).

**Schedule.** Nightly. The business cadence is monthly, but nightly means a PM who updates
mid-month sees it reflected, which encourages keeping it current.

**Validation at the silver layer.** Fail loudly, never silently drop:

| Check | Action |
|---|---|
| `ProjectNumber` not in `dim_Project` | Reject row, log |
| `ReportMonth` is not the 1st | Reject row, log |
| Status code not in `dim_Status` | Reject row, log |
| Trade not in `dim_Trade` after `TRIM()` | Reject row, log |
| Required column blank | Reject row, log |
| Duplicate key | Keep latest by file version, log |

Rejected rows surface on the hidden Data Quality page (report-spec.md, page 6). **This is
the guardrail the Excel never had** — it is how a `$200,000,000` buyout figure against a
`$9.1M` contract reached a leadership report unchallenged.

**Transforms.**
- `TRIM()` every text field
- Strip leading emoji before matching codes
- Empty string → null
- `"NA"` / `"N/A"` / `"TBD"` → null

## Migrating the existing data

The sample workbook contains mostly demo data (`Kitchen Cabinet Design` ×5,
`Critical Path Item 1–9`, `Sub 1–5`, `$200M` buyout, `99999` hours). It is a template, not
a live project.

**Ask Affect for 2–3 completed real project reports.** Those are worth migrating, both to
seed history and to validate that the schema survives contact with real data. The template
alone will not surface the edge cases.

## Rollout

1. Build the workbook from this spec.
2. Walk one PM through it with a live project — watch where they hesitate. That is where
   the design is wrong, not where the PM is.
3. Run it in parallel with the current Excel for one cycle. Reconcile every number.
4. Cut over once they match.

Parallel-running one cycle is the step worth protecting. It is how you find out whether a
field means what the column header says it means.
