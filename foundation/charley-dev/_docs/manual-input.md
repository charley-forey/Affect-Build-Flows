# Manual input — the ~40%

Roughly 40% of the Monthly Progress Report exists nowhere but the spreadsheet: wins, the
entire risk register, recovery-plan narratives, the client survey, cost-management flags,
the profitability judgement. No amount of Procore or Sage integration produces these
(`analysis/excel-tracker/field-inventory.md:348`).

The nine `man_*` tables are live in `CD_Gold_Lakehouse` and bound to the semantic model.
**They are empty**, and deliberately so — seeding them with plausible values would put
numbers in front of leadership that nobody entered, indistinguishable from real ones.

## How to put data in, today

Drop a CSV in the lakehouse at `Files/manual/<TableName>.csv` and re-run
`cd_30_build_gold`. The header row must match the column names below exactly; the file is
read against the table's declared schema, not inferred, so a typo fails loudly instead of
silently creating a string column.

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

Nine lists, named `CD Wins`, `CD Risks`, … matching the nine `man_*` tables column for
column. The 1:1 mapping is the point: a column added in SharePoint is a column in the
report, with no translation layer to keep in sync.

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

1. Create the nine lists per `sharepoint-lists.md`, plus `CD Projects` as the lookup source.
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

`Files/manual/man_Flags.csv`

```csv
ProjectKey,MonthStart,ProfitabilityCode,ContingencyRemaining,BaselineApproved,BaselineRevision,MonthEndClosedOut,ForecastingInLine,ResourcesUpdated
12345,2025-05-01,Within Range,150000,true,Rev#3,true,true,false
```

`Files/manual/man_Risks.csv`

```csv
ProjectKey,MonthStart,RiskNumber,Description,ImpactCode,Mitigation,OwnerRole,StatusCode
12345,2025-05-01,1,Curtain wall delivery slipping,HIGH,Expedite and pre-stage,Senior PM,IN_PROGRESS
```

## What this unblocks

The scorecard currently measures **35% of its own agreed weight** — `[Scorecard
Coverage %]` reports this live. Six of nine categories return BLANK because their inputs
do not exist yet. Filling these tables is most of what closes that gap:

| Category | Weight | Needs |
|---|---|---|
| Profitability | 0.12 | `man_Flags.ProfitabilityCode` |
| Safety Incidents | 0.14 | `man_SafetyMonthly.RecordableIncidents` — or Procore ingestion |
| Completion Variance | 0.15 | `man_Milestones.BaselineFinish` |
| Observations | 0.10 | `man_QualityMonthly.AvgDaysToClose` — or Procore ingestion |
| Daily Reports | 0.02 | `man_DailyLogCompliance` — or Procore ingestion |
| Accounts Receivable | 0.12 | **blocked** — the Sage AR header has no payment date |

Filling the manual tables takes coverage from 35% to 88%. Accounts Receivable needs the
Sage line tables (`arivln`) or progress billing, not a manual entry — see
`_docs/build-status.md`.

Four of these six have a real system of record identified and move out of `man_*` when
that ingestion runs. They are manual because the pipe is not connected, not because the
data is inherently a judgement — only Profitability is genuinely that.
