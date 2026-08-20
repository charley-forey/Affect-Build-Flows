# SharePoint lists — build sheet

Hand this to whoever has SharePoint admin on Affect's tenant. It is the complete spec for
the lists that replace the spreadsheet's manual half.

**How many lists.** **Eighteen in total: 17 data lists — one per `man_*` table, 140 columns
between them — plus `CD Projects`, a lookup list that holds no report data and exists only
so `ProjectKey` cannot be mistyped.** Both counts you may have seen elsewhere are the same
thing: "18 lists" counts `CD Projects`, "17 lists, 140 columns" does not. This is the
sentence to quote.

The 17 are the 9 original registers for the Monthly Progress Report plus the 8 PQP intake
registers added 2026-08-19 ([`pqp-solution.md`](pqp-solution.md)).

**Site:** `AffectProjectReporting_main` — created 2026-08-19 and now bound in
`_local/make_sharepoint.py`. The `_main` suffix is not a typo: a first attempt came out
half-provisioned (no lists at all, not even the default Documents library) and was deleted,
and it still reserves the unsuffixed URL from the site recycle bin. The site now bound is the
working one. **The 18 lists on it have not been created yet** — that run is outstanding.
**Naming:** every list is prefixed `CD ` so it is obvious which lists the report depends on.

---

## The script is the spec — this document is the review copy

**Both defects this section used to warn about are fixed at the source, 2026-08-19.**

`01-ingestion/Manual/provision-sharepoint.ps1` is **generated** by
`_local/make_sharepoint.py` from the `man_*` gold DDL (`40_man_tables.sql` and
`41_man_qc_tables.sql`), and so are `CD_Manual_Ingest`'s `mashup.pq`, its
`queryMetadata.json`, and `deploy_manual.LISTS` (the CSV path). One function, `list_name()`,
decides every list name; one function, `bronze_table()`, decides every bronze table name.
`test_sharepoint.py` asserts all four writers agree, and `make_sharepoint.py --check` fails
on a stale artefact.

| Was | Now |
|---|---|
| **List names disagreed** — the PS1 created `CD PriorityItems`, `CD SafetyMonthly`, `CD QualityMonthly`, `CD DailyLogCompliance`; `mashup.pq` read the spaced forms. Four of nine queries would have navigated to a list that does not exist, returned nothing, and rendered as blank tiles indistinguishable from "nobody filled this in" | One generator. The spaced forms (`CD Priority Items`, …) are what both write |
| **Column specs disagreed** on `man_Flags`, `man_Milestones`, `man_Survey`, `man_DailyLogCompliance`, framed as four open questions for Affect | Not questions. The gold DDL and the model TMDL had agreed all along; the *input* side had drifted from both and was corrected to match. The tables below now carry the live spec |

**If you are creating the lists today, run the script.** The tables below are the
human-readable review copy of what it creates, and they are kept in step with it by hand —
where they differ, the script wins.

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
| `StatusCode` | Choice | yes | `NOT_STARTED`, `PLANNED`, `IN_PROGRESS`, `COMPLETE` |

Spreadsheet cap: 8. **No cap here.**

## 3. `CD Priority Items`

| Column | Type | Required | Choices / notes |
|---|---|---|---|
| `ItemNumber` | Number (integer) | yes | |
| `ScheduleItem` | Single line of text | yes | |
| `StatusCode` | Choice | yes | `ON_TRACK`, `BEHIND`, `AT_RISK` |
| `CriticalDelays` | Multiple lines of text | no | |
| `RecoveryPlan` | Multiple lines of text | no | |
| `ForecastImpact` | Multiple lines of text | no | |
| `Notes` | Multiple lines of text | no | |

## 4. `CD Flags`

One row per project-month.

| Column | Type | Required | Choices / notes |
|---|---|---|---|
| `ProfitabilityCode` | Choice | yes | `Within Range`, `Out of Range, but has a plan`, `Margin fade but no plan` — these are `dim_ScorecardBand[MatchValue]` for category 2, and they are **labels, not codes**. Seeding `IN_RANGE` here would look right and match nothing |
| `ContingencyRemaining` | Number | no | |
| `BaselineApproved` | Yes/No | no | |
| `BaselineRevision` | Single line of text | no | e.g. `Rev#3` |
| `MonthEndClosedOut` | Yes/No | no | |
| `ForecastingInLine` | Yes/No | no | |
| `ResourcesUpdated` | Yes/No | no | |

> **Codes, not labels.** `HIGH`, not `🔴 High`. The emoji is applied by the report from
> `dim_Status`; storing it in the data means the report cannot restyle without a data
> migration.

## 5. `CD Survey`

One row **per question**, six questions per project-month.

| Column | Type | Required | Choices / notes |
|---|---|---|---|
| `QuestionNumber` | Number (integer) | yes | 1–6 |
| `QuestionText` | Single line of text | no | **Worth filling in** — see below |
| `Score` | Number (integer) | yes | |
| `SurveyedParty` | Single line of text | no | Who answered. The survey is attributed, not anonymous |

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
(850 and 1,469 rows) and both now land in gold as `fct_QcNcr` and `fct_QcPunch`. Doing so also fixes workbook defect #2, where the quality tab reads
*safety* orientations.

## 8. `CD Milestones`

Per project × milestone. **No `MonthStart`** — a milestone is not monthly.

| Column | Type | Required | Notes |
|---|---|---|---|
| `ActivityKey` | Single line of text | no | Ties the milestone to a schedule activity |
| `MilestoneName` | Single line of text | yes | |
| `ContractStart` | Date | no | Off the signed contract — exists in no system |
| `ContractFinish` | Date | no | |
| `BaselineStart` | Date | no | |
| `BaselineFinish` | Date | no | |
| `IsSubstantialCompletion` | Yes/No | no | |

**A milestone is a span, not a date.** That is what completion variance measures against.

## 9. `CD Daily Log Compliance`

| Column | Type | Required |
|---|---|---|
| `LogsExpected` | Number (integer) | yes |
| `LogsMissedSameDay` | Number (integer) | yes |

**Compliance is "submitted the same day", not "submitted at all".** The column counts the
misses, so a healthy month is a low number.

---

## 10–17. The PQP registers

Added 2026-08-19 for the Project Quality Plan. Same rules as everything above — `ProjectKey`
is a lookup, coded fields are choice columns, versioning on. Column-for-column detail is in
the generated script; the summary here is for review.

| List | Columns beyond `ProjectKey` |
|---|---|
| `CD QC DFOW` | `DfowRef`, `DfowDescription`, `TradeKey`, `RiskTier`, `ControlMeasure`, `OwnerRole`, `StatusCode`, `Notes` |
| `CD QC ITP` | `ItpRef`, `TradeKey`, `Activity`, `InspectionType`, `AcceptanceCriteria`, `HoldPointType`, `Responsible`, `PlannedDate`, `ActualDate`, `ResultCode`, `StatusCode`, `Notes` |
| `CD QC Gate` | `GateKey`, `GateType`, `StatusCode`, `Responsible`, `TargetDate`, `SubmittedDate`, `CompletedDate`, `EvidenceLink`, `BlockerNote` |
| `CD QC Special Inspection` | `InspectionRef`, `Category`, `Agency`, `InspectorName`, `RequiredCode`, `PerformedCode`, `ScheduledDate`, `PerformedDate`, `ReportReceivedDate`, `StatusCode`, `Notes` |
| `CD QC Commissioning` | `SystemRef`, `SystemName`, `TradeKey`, `Responsible`, `PlannedDate`, `ActualDate`, `StatusCode`, `Notes` |
| `CD QC Inspector Sign In` | `SignInRef`, `VisitDate`, `InspectorName`, `AgencyCode`, `Purpose`, `AreaInspected`, `OutcomeCode`, `FollowUpRequired`, `Notes` |
| `CD QC Checklist Result` | `TradeKey`, `ItemKey`, `StageCode`, `ResultCode`, `InspectedDate`, `InspectedBy`, `Notes` |
| `CD QC DOH Result` | `ItemKey`, `ResponsibilityCode`, `StatusCode`, `VerifiedDate`, `VerifiedBy`, `EvidenceLink`, `Notes` |

**None of the choice values here were retyped.** `StatusCode`, `ResultCode`, `StageCode`,
`AgencyCode`, `OutcomeCode`, `RequiredCode`, `PerformedCode` and `ResponsibilityCode` are all
read out of `02-transformation/seed/qc_status_vocab.csv` — the workbook's own dropdown
vocabulary — which is the same file that builds `dim_QcStatus`. So what somebody can **pick**
and what the model can **resolve** come from one file by construction. Retyping 143 codes into
a PowerShell script is how you get a status that no measure matches and no error anywhere.

`TradeKey` and `ItemKey` draw their choices from the `qc_seed_*` CSVs for the same reason —
they have to match `qc_seed_Trade` / `qc_seed_ChecklistItem` exactly or the result joins to
nothing.

**One cost, stated rather than hidden.** `CD QC Gate` is one list covering all three gate
paths (Path to TCO, Path to Fire Alarm, Statutory Inspections), so its `StatusCode` offers
the **union** of the three vocabularies — 15 codes where the three separately hold 6, 7 and
9. The alternative was three lists differing only in a dropdown, which is what the workbook
had. `test_sharepoint.py` asserts this deliberately, so it reads as a decision rather than a
bug.

---

## Permissions

| List | Edit | Read |
|---|---|---|
| `CD Projects` | Admin only | Everyone |
| `CD Safety Monthly` | Safety lead + PMs | Everyone |
| `CD Survey` | Client-facing lead | Leadership |
| The eight `CD QC *` lists | The Q-Team + PMs | Everyone |
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

Send back the **site URL** and the list names exactly as SharePoint shows them — 17 data
lists plus `CD Projects`. The exact strings matter: `CD_Manual_Ingest.Dataflow` navigates by
list title, and the fixed defect above is precisely what happens when the string is close but
not identical.

The site URL is the last placeholder: `SITE` in `mashup.pq` is still
`https://REPLACE-ME.sharepoint.com/…`, and the mashup is generated, so binding it is
replacing one constant.
