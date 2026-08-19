# Manual input — the ~40%

Roughly 40% of the Monthly Progress Report exists nowhere but the spreadsheet: wins, the
entire risk register, recovery-plan narratives, the client survey, cost-management flags,
the profitability judgement. No amount of Procore or Sage integration produces these
(`analysis/excel-tracker/field-inventory.md:348`).

The nine `man_*` tables are live in `CD_Gold_Lakehouse` and bound to the semantic model.
**They are empty**, and deliberately so — seeding them with plausible values would put
numbers in front of leadership that nobody entered, indistinguishable from real ones.

## How to put data in, today

Drop a CSV in the lakehouse at `Files/_manual/<list>.csv` and re-run **`cd_06_land_manual`**.
Templates with a worked example row are regenerated at `Files/_manual/_templates/` on every
run. The header row must match the column names exactly; the file is read against the
table's declared schema, not inferred, so a typo fails loudly instead of silently creating
a string column.

> **Two stale paths, now corrected in code.** `02-transformation/sql/gold/40_man_tables.sql`
> used to name `cd_40_load_manual` and `Files/manual/*.csv` as the loader and its input.
> Neither ever existed — the notebook is `cd_06_land_manual` and the directory is
> `Files/_manual/`. The header comment has since been rewritten to describe the real chain.
> Recorded here because the wrong names sat in the DDL for weeks and anyone reading an older
> checkout will still find them.

This is deliberately the lowest-friction thing that works **for one person loading a file**.
It is not the answer for a team, which is what the next section is.

---

## The real answer: SharePoint lists

A CSV in a lakehouse has no concurrency, no permissions, no edit history and no way for a
second person to contribute. Here is the design that does.

### Why SharePoint and not the alternatives

| Option | Multi-user | Edit history | Permissions | Mobile | Cost |
|---|---|---|---|---|---|
| **SharePoint list** | yes | per field, with who + when | per list and per item | native app | already owned |
| Excel in Teams | co-authoring | file versions, not fields | per file | yes | already owned |
| Power Apps + Dataverse | yes | yes | yes | yes | **premium licence per user** |
| Power BI write-back | yes | build it yourself | via RLS | no | Fabric capacity |
| CSV in the lakehouse | **no** | no | no | no | — |

SharePoint wins on the thing that decides adoption: **Affect already has it, already
administers it, and already knows it.** A solution needing a new licence or a new admin
story is one that quietly does not get used.

Power Apps stays available as an upgrade — a richer entry form writing to these same lists
changes nothing downstream.

### One list per table, columns identical

**Ten lists in total: nine data lists, one per `man_*` table, 61 columns between them, plus
`CD Projects` — a lookup list holding no report data.** Named `CD Wins`, `CD Risks`, …
matching the nine `man_*` tables column for column. The 1:1 mapping is the point: a column
added in SharePoint is a column in the report, with no translation layer to keep in sync.

> ⚠️ **The 1:1 mapping is currently broken in two places, and both are runtime breaks
> rather than errors.** Fixes are in progress in the ingestion code; the full write-up with
> the exact name and column tables is in
> [`sharepoint-lists.md`](sharepoint-lists.md#-two-known-defects--read-before-running-the-provisioning-script).
>
> 1. **List names disagree.** `provision-sharepoint.ps1` creates `CD PriorityItems`,
>    `CD SafetyMonthly`, `CD QualityMonthly`, `CD DailyLogCompliance`; `mashup.pq` reads
>    `CD Priority Items`, `CD Safety Monthly`, `CD Quality Monthly`,
>    `CD Daily Log Compliance`. Four of nine queries would navigate to a list that does not
>    exist, return nothing, and render as blank tiles — indistinguishable from "nobody has
>    filled this in".
> 2. **Column specs disagree** on `man_Flags`, `man_Milestones`, `man_Survey` and
>    `man_DailyLogCompliance`. The **gold DDL (`40_man_tables.sql`) and
>    `provision-sharepoint.ps1` are the authoritative pair** — the script is generated from
>    the DDL. `sharepoint-lists.md` and `_local/deploy_manual.py` carry the other spec.
>    These are the same four tables listed under *What is NOT built* below, and the
>    disagreement is not a typo — each one is a real question about what the scorecard
>    should measure.

### The single most important design choice

**`ProjectKey` is a SharePoint lookup column, not free text.** It points at a `CD Projects`
list synced from `dim_Project`.

A typed project name is exactly how "1100 Fulton" and "1100 Fulton St" become two projects
in a report that then quietly under-counts both. A lookup cannot be misspelled. The same
applies to every coded field — `ImpactCode`, `StatusCode`, `ProfitabilityCode` are **choice
columns** carrying the codes from `dim_Status`, so nobody types `🔴 High` where `HIGH` is
expected.

### Multiple people, editing all month

- **No submit step.** Rows are edited in place; each pipeline run reads current state.
- **Versioning on**, so every field change records who and when. That is an audit trail the
  spreadsheet has never had — today a risk rating can change with no record that it did.
- **Concurrent edits** are last-write-wins with a warning. At this grain (two people editing
  the same risk on the same project in the same minute) that is the right trade, and version
  history makes it recoverable.
- **Per-list permissions** — the safety lead does not need edit rights on client-satisfaction
  scores.

### Uniqueness is enforced by the pipeline, not the list

The natural key is `(ProjectKey, MonthStart, <item number>)`. SharePoint cannot enforce a
composite unique constraint, so **silver does**: a duplicate lands in `cd_dq_rejects` with a
reason and appears on the DQ page rather than being double-counted into a total. Same rule
as everywhere else here — **reject with a reason, never drop.**

### The path

```
SharePoint list ─► CD_Manual_Ingest.Dataflow ─► cd_bronze_man_* ─► cd_silver_man_* ─► man_*
```

The same medallion the Procore data runs through: same audit columns, same reject handling,
same `snapshot_date`. So "what did this project's risk register look like in May?" is
answerable the same way as "what was the budget in May?" — which the spreadsheet cannot
answer at all.

### Refresh cadence

**Hourly during business hours.** Manual data changes on a monthly rhythm with edits
throughout; hourly means someone updates a risk and sees it in the report a few minutes
later. It is a dataflow over a few hundred rows, so the cost is negligible and it removes
the "when will my change show up?" question.

### Deliberately not built

**No approval workflow** — nobody asked for one, and a review gate on an internal monthly
report is friction that gets routed around. If leadership later wants sign-off, a `Status`
choice column plus a report filter is a small change.

**No data entry inside Power BI.** Write-back exists in Fabric now, but it is the least
proven path, has no offline story, and puts typing inside a tool most of these users only
read.

### Who does what

Steps 2–6 below are ours. **Step 1 needs Affect** — the lists live in their tenant and
need SharePoint admin rights. `sharepoint-lists.md` is written to hand over directly.

1. Create the nine data lists plus `CD Projects` (ten in total). **This is now a script,
   not a build sheet** —
   `01-ingestion/Manual/provision-sharepoint.ps1`, generated from `40_man_tables.sql` by
   `_local/make_sharepoint.py`. Whoever has SharePoint admin runs:

   ```powershell
   Install-Module PnP.PowerShell -Scope CurrentUser
   Connect-PnPOnline -Url https://<tenant>.sharepoint.com/sites/<site> -Interactive
   ./provision-sharepoint.ps1
   ```

   9 lists, 61 columns, versioning on, `ProjectKey` a lookup everywhere. It is idempotent —
   an existing list keeps its data and gains any missing columns, so re-running after a
   schema change is how you apply one.

   The script is **generated**, not hand-written, because SharePoint column names and
   `man_*` column names have to be identical and `CD_Manual_Ingest` maps them 1:1 with no
   translation layer. A name differing by one character does not error: the column stops
   arriving and the report shows a blank tile indistinguishable from "nobody filled this
   in". `test_sharepoint.py` fails the build if the two drift.

   `sharepoint-lists.md` remains the human-readable spec for review.
2. `CD_Manual_Ingest.Dataflow` — one query per list into `cd_bronze_man_*`.
3. `sql/silver/30_manual_silver.sql` — type, validate, reject duplicates and unknown projects.
4. Point `40_man_tables.sql` at silver instead of the empty declarations.
5. DQ expectations: duplicate key, unknown project, month outside `dim_Date`.
6. Add the dataflow to `CD_Master_Pipeline`, upstream of silver.

Until step 1 happens, the CSV path above keeps working — and the switch from CSV to
SharePoint changes one notebook cell. **No gold file, no measure, no report visual.**

## The tables

Every one carries `ProjectKey` (the Procore project id) and, except `man_Milestones`,
`MonthStart` (first of the reporting month, `YYYY-MM-01`).

| Table | Grain | Replaces | Cap removed |
|---|---|---|---|
| `man_Wins` | project × month × win | `WINS` | 4+4 → unlimited |
| `man_Risks` | project × month × risk | `RISKS!Table37` | 8 → unlimited |
| `man_PriorityItems` | project × month × item | `SCHEDULE!Table3714` | 5 → unlimited |
| `man_Flags` | project × month | `FINANCIALS!C7`, `E65:E67`, `SCHEDULE!G16:G17` | — |
| `man_Survey` | project × month × question | `SCORECARD CALC!C34:C41` | 6 → unlimited |
| `man_SafetyMonthly` | project × month | `SAFETY!Table1` | — |
| `man_QualityMonthly` | project × month | `QUALITY!Table18` | — |
| `man_Milestones` | project × milestone | `SCHEDULE!Table5` cols D:G | 10 → unlimited |
| `man_DailyLogCompliance` | project × month | `SCORECARD CALC!E28` | — |

The workbook's caps exist because `DASHBOARD` hard-references specific cells — a 5th win
simply would not appear. Nothing here is capped.

### Codes, not display strings

`ImpactCode`, `StatusCode`, `ProfitabilityCode` take the **code**, not the emoji label.
`HIGH`, not `🔴 High`. Codes are in `dim_Status[Code]`; `ProfitabilityCode` must match
`dim_ScorecardBand[MatchValue]` for category 2 exactly:

```
Within Range
Out of Range, but has a plan
Margin fade but no plan
```

Exact-match is how the scorecard resolves it, so a single changed character means the
category scores nothing. That is inherited from the workbook, where the same fragility
silently zeroed a 12%-weighted category.

## Example

`Files/_manual/man_Flags.csv`

```csv
ProjectKey,MonthStart,ProfitabilityCode,ContingencyRemaining,BaselineApproved,BaselineRevision,MonthEndClosedOut,ForecastingInLine,ResourcesUpdated
12345,2025-05-01,Within Range,150000,true,Rev#3,true,true,false
```

`Files/_manual/man_Risks.csv`

```csv
ProjectKey,MonthStart,RiskNumber,Description,ImpactCode,Mitigation,OwnerRole,StatusCode
12345,2025-05-01,1,Curtain wall delivery slipping,HIGH,Expedite and pre-stage,Senior PM,IN_PROGRESS
```

## What this unblocks

**Scorecard coverage is 59%** — the canonical figure, its history and its provenance are in
[`build-status.md`](build-status.md#not-built-yet); do not restate it, link to it. (An
earlier edition of this page said 35%. That was the reading *before* field-ops data landed;
coverage went 35% → 45% → 59%.)

Four of nine categories return BLANK because their inputs do not exist yet: Accounts
Receivable, Profitability, Completion Variance and Daily Reports. Filling these tables is
most of what closes that gap. Six rows are listed below because two of them — Safety
Incidents and Observations — have since been covered by Procore field-ops ingestion rather
than by `man_*`, which is what moved coverage to 59%:

| Category | Weight | Needs |
|---|---|---|
| Profitability | 0.12 | `man_Flags.ProfitabilityCode` |
| Safety Incidents | 0.14 | `man_SafetyMonthly.RecordableIncidents` — or Procore ingestion |
| Completion Variance | 0.15 | `man_Milestones.BaselineFinish` |
| Observations | 0.10 | `man_QualityMonthly.AvgDaysToClose` — or Procore ingestion |
| Daily Reports | 0.02 | `man_DailyLogCompliance` — or Procore ingestion |
| Accounts Receivable | 0.12 | **blocked** — the Sage AR header has no payment date |

Filling the manual tables is **projected** to take coverage from 59% to 88%. That 88% is a
projection from the category weights, not a measurement — the measured figure stays 59%
until rows actually land. Accounts Receivable needs the Sage line tables (`arivln`) or
progress billing, not a manual entry — see [`build-status.md`](build-status.md).

Four of these six have a real system of record identified and move out of `man_*` when
that ingestion runs. They are manual because the pipe is not connected, not because the
data is inherently a judgement — only Profitability is genuinely that.

---

## Status, 2026-08-02 — and a correction

I previously described the manual-input pipework as "built and waiting on SharePoint". That
was not accurate, and the inaccuracy mattered, because it made the remaining work look like
an admin ticket when part of it is a decision only Affect can make.

### What is genuinely built and live

| Layer | State |
|---|---|
| CSV templates | **Live** — `Files/_manual/_templates/*.csv`, 9 lists, each with an example row |
| CSV → bronze loader | **Live** — `cd_06_land_manual`, run and succeeding |
| `cd_bronze_man_*` | **Live** — 9 tables, correctly typed, currently 0 rows |
| Silver parsers | Written (`30_manual_silver.sql`), with dedup and a reject log |
| Gold `man_*` tables | Exist, correctly typed, empty |
| Model + scorecard | Bound to all 9, measures written, categories score BLANK not zero |

**The SharePoint dependency is gone.** Data entry no longer waits on an administrator:
download a template, fill it in, upload it to `Files/_manual/<list>.csv`, re-run the
notebook. When the SharePoint lists are eventually provisioned the dataflow writes the same
bronze tables and nothing downstream changes — two writers, one contract.

That matters because the slow part was never the plumbing. It is people sitting down and
typing a month of history, and that can start now.

### What is NOT built, and needs an Affect decision first

**There is no silver → gold link for `man_*`.** `40_man_tables.sql` creates the gold tables
as empty typed placeholders; nothing populates them from `cd_silver_man_*`. Writing that
join is small. Agreeing what it should say is not, because the two specs disagree on four
tables — and each disagreement is a real question about what the scorecard should measure:

| Table | Gold expects | Silver produces | The question |
|---|---|---|---|
| `man_DailyLogCompliance` | `LogsMissedSameDay` | `LogsSubmitted` | Is compliance "submitted at all" or "submitted the same day"? These give different scores |
| `man_Milestones` | `ContractStart` + `ContractFinish`, `BaselineStart` + `BaselineFinish`, `ActivityKey` | single `ContractDate`, `BaselineDate`, `ForecastDate`, `ActualDate` | Are milestones a date or a span? Completion variance depends on which |
| `man_Flags` | `ContingencyRemaining`, `BaselineApproved`, `BaselineRevision`, `MonthEndClosedOut`, `ForecastingInLine`, `ResourcesUpdated` | `ProfitabilityCode`, `CostMgmtFlag`, `ScheduleFlag`, `Notes` | Which attestations are actually captured monthly? |
| `man_Survey` | `SurveyedParty` | *(not captured)* | Is the survey anonymous, or attributed? |

Guessing any of these produces a scorecard number that looks authoritative and measures
something nobody asked for — which is exactly the defect class this platform exists to
remove. So they are questions for the next client call, not decisions to take here.

**Until they are answered, `[Scorecard Coverage %]` stays at 59%** and the four unscored
categories return BLANK rather than zero. That is the honest reading, and it is visible on
the Scorecard page rather than buried.

### Status, 2026-08-19 — the join is written; the questions are still open

**The root cause named above has been addressed in code.** `40_man_tables.sql` no longer
stops at nine empty typed placeholders — it now `INSERT`s from `sv_man_*` over
`cd_silver_man_*`, so the chain runs end to end: CSV or SharePoint list →
`cd_bronze_man_*` → `cd_silver_man_*` → `man_*` → model. With no input the inserts move
zero rows and the tables stay empty, exactly as before, which is the correct behaviour —
the platform never invents a row.

**That does not close this page.** Two things are unchanged:

1. **The four column-spec questions above still need Affect.** A written join does not
   decide whether daily-log compliance means "submitted" or "submitted the same day", or
   whether a milestone is a date or a span. Until they are answered the two specs stay
   divergent and whichever one the join implements is a guess with a schema.
2. **Nobody has typed a row yet.** The slow part was never the plumbing. `[Scorecard
   Coverage %]` stays at **59%** and the four unscored categories return BLANK rather than
   zero until real data lands.

The remaining code defect is the SharePoint one: **the list names the provisioning script
creates do not match the names the dataflow reads** — see the top of this page. That one is
still open and is a runtime break rather than a question.
