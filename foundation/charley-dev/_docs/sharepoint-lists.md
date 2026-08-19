# SharePoint lists — build sheet

Hand this to whoever has SharePoint admin on Affect's tenant. It is the complete spec for
the lists that replace the spreadsheet's manual half.

**How many lists.** **Ten in total: nine data lists — one per `man_*` table, 61 columns
between them — plus `CD Projects`, a lookup list that holds no report data and exists only
so `ProjectKey` cannot be mistyped.** Both counts you may have seen elsewhere are the same
thing: "ten lists" counts `CD Projects`, "9 lists, 61 columns" does not. This is the
sentence to quote.

**Site:** one SharePoint site, suggested name `Affect Project Reporting`.
**Naming:** every list is prefixed `CD ` so it is obvious which lists the report depends on.

---

## ⚠️ Two known defects — read before running the provisioning script

Both are in code, both are being fixed by separate work in progress, and neither is fixed
by editing this document. They are recorded here because this is the page somebody reads
immediately before creating the lists, and either one produces a report that looks filled
in and is empty.

### Defect 1 — the list names do not match what reads them (runtime break)

`01-ingestion/Manual/provision-sharepoint.ps1` creates lists whose names have **no spaces**
inside the noun. `01-ingestion/Manual/CD_Manual_Ingest.Dataflow/mashup.pq` navigates to
names **with** spaces. Four of the nine do not match:

| Created by `provision-sharepoint.ps1` | Read by `mashup.pq` | Match? |
|---|---|---|
| `CD Wins` | `CD Wins` | yes |
| `CD Risks` | `CD Risks` | yes |
| **`CD PriorityItems`** | **`CD Priority Items`** | **NO** |
| `CD Flags` | `CD Flags` | yes |
| `CD Survey` | `CD Survey` | yes |
| **`CD SafetyMonthly`** | **`CD Safety Monthly`** | **NO** |
| **`CD QualityMonthly`** | **`CD Quality Monthly`** | **NO** |
| `CD Milestones` | `CD Milestones` | yes |
| **`CD DailyLogCompliance`** | **`CD Daily Log Compliance`** | **NO** |

The headings in this document use the spaced form. **Treat neither as settled until the
code is reconciled** — a fix is in progress on the ingestion side.

Why it matters more than a typo: a SharePoint navigation to a list that does not exist does
not fail the way a missing table does. It produces an empty query, which produces an empty
bronze table, which produces a blank tile on the report — and a blank tile is
indistinguishable from "nobody filled this in yet". Priority items, safety, quality and
daily-log compliance would all read as un-entered forever, and the scorecard categories over
them would score BLANK rather than error.

### Defect 2 — two column specs disagree on four tables

There are two descriptions of what the `man_*` columns are, and they do not match:

| | Files |
|---|---|
| **Authoritative** | `02-transformation/sql/gold/40_man_tables.sql` and `01-ingestion/Manual/provision-sharepoint.ps1` — the script is *generated* from the DDL, so these two agree by construction |
| Not authoritative | this document and `_local/deploy_manual.py` (the CSV path), which agree with each other and with the silver parsers |

They disagree on four tables — the same four listed in
[`manual-input.md`](manual-input.md), where each disagreement is written up as the real
question it is:

| Table | Authoritative (gold DDL + PS1) | This document / CSV path |
|---|---|---|
| `man_Flags` | `ProfitabilityCode`, `ContingencyRemaining`, `BaselineApproved`, `BaselineRevision`, `MonthEndClosedOut`, `ForecastingInLine`, `ResourcesUpdated` | `ProfitabilityCode`, `CostMgmtFlag`, `ScheduleFlag`, `Notes` |
| `man_Milestones` | `ActivityKey`, `MilestoneName`, `ContractStart`, `ContractFinish`, `BaselineStart`, `BaselineFinish`, `IsSubstantialCompletion` | `MilestoneName`, `ContractDate`, `BaselineDate`, `ForecastDate`, `ActualDate` |
| `man_Survey` | adds `SurveyedParty` | no `SurveyedParty` |
| `man_DailyLogCompliance` | `LogsExpected`, `LogsMissedSameDay` | `LogsExpected`, `LogsSubmitted` |

The choice codes differ too: the script writes `NOT_STARTED`/`PLANNED`/`IN_PROGRESS`/
`COMPLETE` for `CD Risks.StatusCode` and `ON_TRACK`/`BEHIND`/`AT_RISK` for
`CD PriorityItems.StatusCode`, where the tables below say `OPEN`/`MONITORING`/`CLOSED` and
`ON_TRACK`/`AT_RISK`/`DELAYED`/`COMPLETE`.

**If you are creating the lists today, the script is what runs — take its columns and its
codes.** The tables below stay as the human-readable review copy and will be reconciled
when the four questions in `manual-input.md` are answered, because answering them is what
decides which spec is right.

Before creating any of them, turn on for each list: **Settings → Versioning settings →
Create a version each time you edit an item = Yes.** That is what gives every field change a
who and a when — the audit trail the spreadsheet has never had.

---

## 0. `CD Projects` — the lookup source (build this first)

Every other list points at this one. Its job is to make a project *unselectable-if-wrong*
rather than typeable-and-wrong.

| Column | Type | Notes |
|---|---|---|
| `Title` | Single line of text | The Procore project id, e.g. `562949955001573` |
| `ProjectName` | Single line of text | Display name, e.g. `1100 Fulton Street` |
| `IsActive` | Yes/No | Filter the lookup on this so closed projects stop appearing |

Populate it from `dim_Project` (19 active projects today). It can be refreshed by hand
monthly, or by a scheduled flow — either is fine at this size.

> **Why this list exists at all:** a free-text project name is how "1100 Fulton" and
> "1100 Fulton St" become two projects in a report that then under-counts both. A lookup
> column cannot be misspelled.

---

## Shared columns

Every list below has these two. They are the join to everything else.

| Column | Type | Required | Notes |
|---|---|---|---|
| `ProjectKey` | **Lookup** → `CD Projects` : `Title` | yes | Never free text |
| `MonthStart` | Date (no time) | yes | **Always the 1st of the month.** See the note below |

**`MonthStart` must be the first of the month.** The report groups by month, and
`2025-05-14` and `2025-05-01` are different rows. Set the column's default to the 1st and
say so in its description; the pipeline also floors it, so a mistake is corrected rather
than duplicated — but the correction is invisible, so it is better not to make it.

---

## 1. `CD Wins`

| Column | Type | Required | Choices / notes |
|---|---|---|---|
| `WinNumber` | Number (integer) | yes | 1, 2, 3… within the project-month |
| `Description` | Multiple lines of text (plain) | yes | |
| `WinType` | Choice | yes | `Realized`, `FocusArea` |

The spreadsheet caps this at 4 realized + 4 focus areas because the dashboard references
fixed cells. **There is no cap here.**

## 2. `CD Risks`

| Column | Type | Required | Choices / notes |
|---|---|---|---|
| `RiskNumber` | Number (integer) | yes | |
| `Description` | Multiple lines of text | yes | |
| `ImpactCode` | Choice | yes | `HIGH`, `MEDIUM`, `LOW` |
| `Mitigation` | Multiple lines of text | no | |
| `OwnerRole` | Choice | no | The 9 roles from `dim_Owner` (PM, Super, PE, …) |
| `StatusCode` | Choice | yes | `OPEN`, `MONITORING`, `CLOSED` |

Spreadsheet cap: 8. **No cap here.**

## 3. `CD Priority Items`

| Column | Type | Required | Choices / notes |
|---|---|---|---|
| `ItemNumber` | Number (integer) | yes | |
| `ScheduleItem` | Single line of text | yes | |
| `StatusCode` | Choice | yes | `ON_TRACK`, `AT_RISK`, `DELAYED`, `COMPLETE` |
| `CriticalDelays` | Multiple lines of text | no | |
| `RecoveryPlan` | Multiple lines of text | no | |
| `ForecastImpact` | Multiple lines of text | no | |
| `Notes` | Multiple lines of text | no | |

## 4. `CD Flags`

One row per project-month.

| Column | Type | Required | Choices / notes |
|---|---|---|---|
| `ProfitabilityCode` | Choice | yes | `IMPROVED`, `MAINTAINED`, `DECLINED` — must match `dim_ScorecardBand` category 2 exactly |
| `CostMgmtFlag` | Choice | no | `GREEN`, `AMBER`, `RED` |
| `ScheduleFlag` | Choice | no | `GREEN`, `AMBER`, `RED` |
| `Notes` | Multiple lines of text | no | |

> **Codes, not labels.** `HIGH`, not `🔴 High`. The emoji is applied by the report from
> `dim_Status`; storing it in the data means the report cannot restyle without a data
> migration.

## 5. `CD Survey`

One row **per question**, six questions per project-month.

| Column | Type | Required | Choices / notes |
|---|---|---|---|
| `QuestionNumber` | Number (integer) | yes | 1–6 |
| `QuestionText` | Single line of text | no | **Worth filling in** — see below |
| `Score` | Number (0–1, 2 decimals) | yes | Or 1–5 if Affect prefers; say which and the pipeline scales |

The workbook stores the six scores but **not the question text** (open question 6). Nobody
now knows what question 3 asked. Capturing it here fixes that permanently.

## 6. `CD Safety Monthly` — temporary

| Column | Type | Required |
|---|---|---|
| `HoursWorked` | Number | yes |
| `RecordableIncidents` | Number (integer) | yes |
| `Orientations` | Number (integer) | no |
| `OtHours` | Number | no |

**Retire this list once Procore's `incidents` and `manpower_daily_totals` feed the model.**
Both are already in the registry.

## 7. `CD Quality Monthly` — temporary

| Column | Type | Required |
|---|---|---|
| `Observations` | Number (integer) | yes |
| `PunchlistItems` | Number (integer) | yes |
| `AvgDaysPastDue` | Number | no |
| `AvgDaysToClose` | Number | no |

**Retire once `observations` and `punch_items` feed the model** — both already extract
(850 and 1,469 rows). Doing so also fixes workbook defect #2, where the quality tab reads
*safety* orientations.

## 8. `CD Milestones`

Per project × milestone. **No `MonthStart`** — a milestone is not monthly.

| Column | Type | Required | Notes |
|---|---|---|---|
| `MilestoneName` | Single line of text | yes | |
| `ContractDate` | Date | no | Off the signed contract — exists in no system |
| `BaselineDate` | Date | no | |
| `ForecastDate` | Date | no | |
| `ActualDate` | Date | no | Blank until it happens |

## 9. `CD Daily Log Compliance`

| Column | Type | Required |
|---|---|---|
| `LogsExpected` | Number (integer) | yes |
| `LogsSubmitted` | Number (integer) | yes |

---

## Permissions

| List | Edit | Read |
|---|---|---|
| `CD Projects` | Admin only | Everyone |
| `CD Safety Monthly` | Safety lead + PMs | Everyone |
| `CD Survey` | Client-facing lead | Leadership |
| All others | PMs | Everyone |

## What the pipeline does with mistakes

It **rejects with a reason and shows you** — it never silently drops a row, and never
silently fixes one in a way you cannot see:

| Problem | What happens |
|---|---|
| Two rows with the same project + month + number | Both rejected to `cd_dq_rejects`, visible on the DQ page |
| `MonthStart` not the 1st | Floored to the 1st, and flagged |
| A project not in `dim_Project` | Rejected — usually means the lookup list is stale |
| A code not in `dim_Status` | Rejected with the offending value shown |

## Refresh

**Hourly during business hours.** Edit a risk, see it in the report a few minutes later.

## After the lists exist

Send back the **site URL and the ten list names exactly as SharePoint shows them** — nine
data lists plus `CD Projects`. The exact strings matter: `CD_Manual_Ingest.Dataflow`
navigates by list title, and defect 1 above is precisely what happens when the string is
close but not identical.
