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

This is deliberately the lowest-friction thing that works. Affect has not decided where
the manual data will ultimately live (`dashboard.md`, open blocker) — SharePoint lists are
the proposal. When that lands it replaces the CSV read in one notebook cell. **No gold
file, no measure, and no report visual changes.**

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
