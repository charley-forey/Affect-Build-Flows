# Manual input — the ~40%

Roughly 40% of the Monthly Progress Report exists nowhere but the spreadsheet: wins, the
entire risk register, recovery-plan narratives, the client survey, cost-management flags,
the profitability judgement. No amount of Procore or Sage integration produces these
(`analysis/excel-tracker/field-inventory.md:348`).

There are now **17** `man_*` tables live in `CD_Gold_Lakehouse` and bound to a semantic
model: the 9 original registers for the Monthly Progress Report, plus 8 PQP intake registers
for the Project Quality Plan ([`pqp-solution.md`](pqp-solution.md)). **They are empty**, and
deliberately so — seeding them with plausible values would put numbers in front of leadership
that nobody entered, indistinguishable from real ones.

## How to put data in, today

Drop a CSV in the lakehouse at `Files/_manual/<list>.csv` and re-run **`cd_06_land_manual`**.
Templates with a worked example row are regenerated at `Files/_manual/_templates/` on every
run. The header row must match the column names exactly; the file is read against the
table's declared schema, not inferred, so a typo fails loudly instead of silently creating
a string column.

> **Two stale paths, corrected in code.** `02-transformation/sql/gold/40_man_tables.sql`
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

**Eighteen lists in total: 17 data lists, one per `man_*` table, 140 columns between them,
plus `CD Projects` — a lookup list holding no report data.** Named `CD Wins`, `CD Risks`, …
`CD QC Gate`, matching the 17 `man_*` tables column for column. The 1:1 mapping is the point:
a column added in SharePoint is a column in the report, with no translation layer to keep in
sync. It is enforced rather than intended — the list names and columns are **generated** from
the gold DDL, and `test_sharepoint.py` fails the build if any writer drifts.

> ✅ **Both of the defects this section used to warn about are fixed at the source, 2026-08-19.**
>
> 1. **List names used to disagree.** `provision-sharepoint.ps1` created `CD PriorityItems`
>    where `mashup.pq` read `CD Priority Items` — four of nine queries navigating to a list
>    that does not exist, returning nothing, and rendering as blank tiles indistinguishable
>    from "nobody has filled this in". `_local/make_sharepoint.py` now generates the PS1, the
>    mashup, `queryMetadata.json` and `deploy_manual.LISTS` from the `man_*` gold DDL, so
>    `list_name()` is the only place a list name is decided and `bronze_table()` the only
>    place a bronze table name is. `test_sharepoint.py` asserts all four writers agree, and
>    `make_sharepoint.py --check` fails on a stale artefact.
> 2. **The column specs no longer disagree, and it was never a design question.** The gold
>    DDL and the semantic model TMDL had agreed with each other all along; the *input* side
>    had drifted from both. The gold DDL is the contract the DAX reads by name, so the input
>    side was corrected to match it, and `deploy_manual.py` no longer keeps its own column
>    list — it derives it from the DDL. Full write-up in
>    [`pqp-solution.md`](pqp-solution.md#part-1--the-root-cause-that-had-to-be-fixed-first).

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

1. Create the 17 data lists plus `CD Projects` (18 in total). **This is now a script,
   not a build sheet** —
   `01-ingestion/Manual/provision-sharepoint.ps1`, generated from `40_man_tables.sql` and
   `41_man_qc_tables.sql` by `_local/make_sharepoint.py`. Whoever has SharePoint admin runs:

   ```powershell
   Install-Module PnP.PowerShell -Scope CurrentUser
   Connect-PnPOnline -Url https://<tenant>.sharepoint.com/sites/<site> -Interactive
   ./provision-sharepoint.ps1
   ```

   17 lists, 140 columns, versioning on, `ProjectKey` a lookup everywhere. It is idempotent —
   an existing list keeps its data and gains any missing columns, so re-running after a
   schema change is how you apply one.

   The script is **generated**, not hand-written, because SharePoint column names and
   `man_*` column names have to be identical and `CD_Manual_Ingest` maps them 1:1 with no
   translation layer. A name differing by one character does not error: the column stops
   arriving and the report shows a blank tile indistinguishable from "nobody filled this
   in". `test_sharepoint.py` fails the build if the two drift.

   `sharepoint-lists.md` remains the human-readable spec for review.
2. ~~`CD_Manual_Ingest.Dataflow` — one query per list into `cd_bronze_man_*`.~~ **Generated.**
   It cannot be *deployed* until the site exists, because `SITE` is still a `REPLACE-ME`
   placeholder — binding it is replacing one constant.
3. ~~`sql/silver/30_manual_silver.sql`~~ **Done**, plus `31_qc_manual_silver.sql`, and both
   are now actually deployed — `deploy_silver.py` used to skip prefix `30` entirely, so
   `cd_silver_man_*` was never built at all.
4. ~~Point `40_man_tables.sql` at silver instead of the empty declarations.~~ **Done** — gold
   now `INSERT`s from `sv_man_*`, and `01_source_views_cd.sql` defines all 17 `sv_man_*`
   views that had never existed.
5. ~~DQ expectations~~ **Done** — the gate is at 103 expectations (80 blocking, 23 warning).
6. **Still open:** add `cd_06_land_manual` (and later the dataflow) to `CD_Master_Pipeline`,
   ahead of `Bronze To Silver`. The nightly run currently rebuilds silver and gold without
   refreshing manual bronze first — harmless while every table is empty, a staleness bug the
   day somebody enters a row.

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

### The eight PQP registers

Added 2026-08-19 for the Project Quality Plan. Same contract, same medallion, same reject
handling; they feed **Model B** rather than the Monthly Progress Report. Design rationale
and the workbook sheets each replaces are in [`pqp-solution.md`](pqp-solution.md).

| Table | Grain |
|---|---|
| `man_QcDfow` | project × definable feature of work |
| `man_QcItp` | project × inspection & test plan line |
| `man_QcGate` | project × gate (against `qc_seed_Gate`, all three paths) |
| `man_QcSpecialInspection` | project × special inspection |
| `man_QcCommissioning` | project × commissioning item |
| `man_QcInspectorSignIn` | project × inspector visit |
| `man_QcChecklistResult` | project × checklist item (against `qc_seed_ChecklistItem`) |
| `man_QcDohResult` | project × DOH requirement (against `qc_seed_DohItem`) |

The `qc_seed_*` tables are the template library — what the workbook says should happen on
every project. These eight record what actually happened. Anything **Procore** already owns
— NCRs, punch items, submittals — is deliberately *not* a list here, because a SharePoint NCR
log next to a Procore NCR log is two answers to "how many are open".

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
| CSV templates | **Live** — `Files/_manual/_templates/*.csv`, **17** lists, each with an example row |
| CSV → bronze loader | **Live** — `cd_06_land_manual`, run and succeeding |
| `cd_bronze_man_*` | **Live** — **17** tables, correctly typed, currently 0 rows |
| Silver parsers | Written (`30_manual_silver.sql`, `31_qc_manual_silver.sql`), with dedup and a reject log — and, since 2026-08-19, actually deployed |
| Gold `man_*` tables | Exist, correctly typed, empty — and now populated **from silver** rather than declared and abandoned |
| Model + scorecard | Model A bound to the original 9; Model B bound to the 8 PQP registers. Categories score BLANK, not zero |

**The SharePoint dependency is gone.** Data entry no longer waits on an administrator:
download a template, fill it in, upload it to `Files/_manual/<list>.csv`, re-run the
notebook. When the SharePoint lists are eventually provisioned the dataflow writes the same
bronze tables and nothing downstream changes — two writers, one contract.

That matters because the slow part was never the plumbing. It is people sitting down and
typing a month of history, and that can start now.

### What was NOT built — resolved 2026-08-19

This section used to say **there is no silver → gold link for `man_*`**, and it was right:
`40_man_tables.sql` created empty typed placeholders and nothing populated them from
`cd_silver_man_*`. Nine gold tables, bound to the semantic model, permanently empty, with
the CSV templates, the loader notebook, the silver parsers and the reject log all running
green and delivering nothing — because the last statement in the chain did not exist.

**It is fixed.** Gold now `INSERT`s from `sv_man_*` over `cd_silver_man_*`, so the chain runs
end to end: CSV or SharePoint list → `cd_bronze_man_*` → `cd_silver_man_*` → `man_*` → model.
With no input the inserts move zero rows and the tables stay empty, which is correct — the
platform never invents a row. `test_qc.py` asserts all 17 `man_*` tables are reachable from
silver, which is the assertion that would have failed before any of this.

It was four root causes, not one: no `sv_man_*` source views existed; `deploy_silver.py`
skipped prefix `30` so `cd_silver_man_*` was never built; four tables' input columns had
drifted; and a leftover `mode("overwrite")` cell in `deploy_gold.py` would have wiped every
row the moment gold started populating. Full write-up in
[`pqp-solution.md`](pqp-solution.md#part-1--the-root-cause-that-had-to-be-fixed-first).

### The four "open questions" were not questions

This page previously listed four tables — `man_DailyLogCompliance`, `man_Milestones`,
`man_Flags`, `man_Survey` — where the gold DDL and the silver parsers disagreed, and framed
each as a decision only Affect could take.

That framing was wrong, and it is worth recording why. **The gold DDL and the semantic model
TMDL had agreed with each other all along.** It was the *input* side — the silver parsers and
the CSV loader — that had drifted away from both. There was nothing to decide: the gold DDL
is the contract the DAX reads by name, so the input side was corrected to match it, and
`deploy_manual.py` no longer keeps its own column list at all — it derives it from the DDL.

So the live spec is, unambiguously: `man_DailyLogCompliance.LogsMissedSameDay`;
`man_Milestones` as **spans** (`ContractStart`/`ContractFinish`,
`BaselineStart`/`BaselineFinish`) plus `ActivityKey` and `IsSubstantialCompletion`;
`man_Flags` carrying the six attestations; and `man_Survey.SurveyedParty` captured.

### What is genuinely left

1. **Nobody has typed a row yet.** The slow part was never the plumbing. `[Scorecard
   Coverage %]` stays at **59%** and the four unscored categories return BLANK rather than
   zero until real data lands.
2. **The SharePoint site does not exist**, so `provision-sharepoint.ps1` has not been run and
   `CD_Manual_Ingest` cannot be bound. That gates the *team* mechanism, not data entry — the
   CSV path works today and needs nobody.
3. **`cd_06_land_manual` is not in `CD_Master_Pipeline`.** Harmless while every table is
   empty; a staleness bug the day somebody enters a row.
