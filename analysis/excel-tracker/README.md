# Excel Project Tracker — Assessment

Full teardown of `YY-000 PROJECT NAME_InternalReport_YYMMDD.xlsx` — the Monthly Progress
Report template Affect Group uses today and the artifact the Power BI dashboard replaces.

Received from Rebecca Buckley, Jul 22 2026. Extracted and verified Jul 22 2026.

## Documents in this folder

| File | What it answers |
|---|---|
| `README.md` (this file) | What the workbook is, who owns what, how the monthly cycle works |
| `field-inventory.md` | Every field — where it lives, whether it's typed in or calculated, and which system should own it |
| `calculations.md` | Every formula decoded to plain English, with its DAX equivalent |
| `dashboard-map.md` | Cell-by-cell map of the DASHBOARD tab back to its source cells |
| `dropdowns-and-status.md` | All 15 pick-lists verbatim + the proposed `dim_Status` table |
| `defects-and-questions.md` | 14 verified defects + the open questions for Affect |

Downstream: [`../../powerbi/`](../../powerbi/) turns this assessment into a build kit.

## What it is

A single-project, single-month status report. One workbook per project per reporting
cycle, saved with a versioned filename (`YY-000 PROJECT NAME_InternalReport_YYMMDD`).
It is filled in by hand, then printed/shared as the monthly progress report.

**11 sheets. No macros, no Power Query, no external workbook links.** All logic is
plain cell formulas. Total file size 138 KB.

| Sheet | Role | Size |
|---|---|---|
| `INSTRUCTIONS` | Usage rules + responsibility matrix | B2:J29 |
| `DASHBOARD` | Read-only presentation canvas | A1:BA94 (53 cols × 94 rows) |
| `WINS` | Wins realized + focus areas for next month | B1:C12 |
| `SCHEDULE` | Critical-path milestones, manpower, priority items | B2:P43 |
| `RISKS` | Risk register | B2:G10 |
| `SAFETY` | Monthly safety metrics, violations, activity log | B2:X41 |
| `QUALITY` | Monthly quality metrics, offenders, issue log | B2:J57 |
| `SUBMITTALS & RFI` | Open critical counts by trade | B2:D13 |
| `FINANCIALS` | Contract, COs, billing, budget, aging, buyout, flags | B2:K73 |
| `SCORECARD CALC` | 9-category weighted health score + client survey | A2:I47 |
| `DROPDOWN` | 15 pick-lists backing every data validation | B2:Q40 |

`DASHBOARD` contains almost no logic of its own — it is a grid of cross-sheet
references arranged visually. It has **exactly one native chart** (a clustered bar for
Submittals & RFIs). Everything else is text, numbers, and conditional formatting.

## Who owns what

From `INSTRUCTIONS!B20:D29`:

| Section | Responsibility | Contributor |
|---|---|---|
| Dashboard | Read Only. Ask Administrator | — |
| Wins | PM | Superintendent & Foremen |
| Schedule | PM | Superintendent & Foremen |
| Risks | PM | Superintendent & Foremen |
| Safety | PM | Superintendent & Foremen |
| Quality | PM | Superintendent & Foremen |
| Submittals & RFIs | PM | Superintendent & Foremen |
| Financial | QS/Estimator | PM & Project Accountant |
| Scorecard Calc | PM & Marketing | PM & Marketing |

> Rebecca noted she is only familiar with the financial inputs — Cathal may need to
> walk the operational tabs.

## How the monthly cycle works

1. PM and QS fill the blue-text cells across the input tabs for the reporting month.
2. `SCHEDULE!E21:K21` is a **manual paste-special** of last month's values so the
   month-to-month delta row (`E22:K22`) can compute. Instruction on the sheet:
   *"Manually Input last months values. If first month reporting enter same value as this month."*
3. `FINANCIALS` column `D` (`LAST PERIOD`) is likewise re-keyed by hand each month.
4. `DASHBOARD!AU4` is set to the **first day of the reporting month**.
5. Everything on `DASHBOARD` recalculates; the file is saved under a new dated name.

Rules from `INSTRUCTIONS`:

- Do not rename, move, or delete tabs.
- Only input data in cells with **blue text**.
- Use the drop-downs where provided.
- `MM/DD/YYYY` for all dates; consistent spelling for trade and status names.
- *"Date needs to be first of the month to pull data."*
- Do not remove rows with formulas; add new rows at the bottom of tables.
- Dashboard is read-only.

## The two conventions you must know

### 1. Blue text `#2334D4` = manual input

~700 cells. This is the only marker distinguishing input from calculation — there is
no cell locking or sheet protection enforcing it.

| Sheet | Input ranges |
|---|---|
| `WINS` | `C3:C12` |
| `SCHEDULE` | `D5:K14`, `C25:D30`, `D35:H39`, `E21:L21`, `N4:N14` |
| `RISKS` | `C3:G10` |
| `SAFETY` | `C3:F33`, `J3:L25`, `B37:G41` |
| `QUALITY` | `C3:E34`, `B48:I57` |
| `SUBMITTALS & RFI` | `C3:D13` |
| `FINANCIALS` | `C3:D15`, `C19:E20`, `C25:E55`, `J25:J55`, `D60:D61`, `E65:E67` |
| `SCORECARD CALC` | `E28`, `C34`, `C36:C41` |

`DASHBOARD` uses colored text purely for section theming (red for Schedule, orange for
Safety, purple for Quality, blue for Financial) — **not** to mark inputs.

### 2. `DASHBOARD!AU4` is the reporting-month anchor

Currently `2025-05-01`. A threaded comment sits on the cell:

> *"Date needs to be first of the month to pull data."*

Every "this period" tile on the dashboard is:

```
INDEX(<metric column>, MATCH(AU4, <month column>, 0))
```

and every month-to-month delta re-matches against `EDATE(AU4,-1)`.

**This is the most fragile mechanic in the file.** It requires that (a) `AU4` is
exactly the 1st, (b) every monthly table's month column contains that exact date, and
(c) the prior month also exists. Miss any one and the tile shows `#N/A` — silently, in
the middle of a report going to leadership. Three of the monthly tables in this file
already use different starting months (see `defects-and-questions.md` #7).

**In Power BI this disappears entirely.** A proper `dim_Date` marked as a date table
plus `DATEADD`/`PREVIOUSMONTH` replaces the whole `INDEX/MATCH` scheme, and a slicer
replaces `AU4`.

## Excel Tables (17)

Tables matter because their structured references (`Table5[[#This Row],[ACTUAL START]]`)
appear throughout the formulas, and because they define the real grain of each dataset.

| Sheet | Table | Range | Columns |
|---|---|---|---|
| `WINS` | `Table3` | B2:C6 | WIN #, DESCRIPTION |
| `WINS` | `Table35` | B8:C12 | WIN #, DESCRIPTION |
| `SCHEDULE` | `Table5` | C3:M14 | TASK, CONTRACT START/FINISH, BASELINE START/FINISH, CURRENT START/FINISH, ACTUAL START/FINISH, START VARIANCE, FINISH VARIANCE |
| `SCHEDULE` | `Table14` | C25:D30 | Company Name, Avg Daily over past 30 days |
| `SCHEDULE` | `Table3714` | C34:H39 | SCHEDULE ITEM, STATUS SUMMARY, CRITICAL DELAYS / VARIANCES, RECOVERY PLAN, FORECAST IMPACT, NOTES / ACTION ITEMS |
| `RISKS` | `Table37` | B2:G10 | RISK #, RISK DESCRIPTION, IMPACT, MITIGATION STRATEGY, OWNER, STATUS |
| `SAFETY` | `Table1` | B2:F34 | MONTH #, MONTH, HOURS WORKED, RECORDABLE INCIDENTS, ORIENTATIONS |
| `SAFETY` | `Table15` | H2:L27 | VLN #, VLN Description, VLN Value, Status, VLN Value / Status |
| `SAFETY` | `Table20` | B36:G41 | TIMEFRAME, CATEGORY, DESCRIPTION/ACTIVITY, STATUS, NOTES/OUTCOME/ACTION, RESPONSIBLE |
| `QUALITY` | `Table18` | B2:E35 | MONTH #, MONTH, OBSERVATIONS, PUNCHLIST ITEM |
| `QUALITY` | `Table17` | C37:E44 | Column1, OBSERVATIONS, PUNCHLIST |
| `QUALITY` | `Table16` | B47:I57 | TIMEFRAME, CATEGORY, DESCRIPTION, TRADE, STATUS, OUTCOME / COMMENTS, RESPONSIBLE, ACTION PLAN |
| `SUBMITTALS & RFI` | `Table22` | B2:D13 | Trade, Open Critical RFIs, Open Critical Submittals |
| `FINANCIALS` | `Table8` | B2:E15 | DESCRIPTION, THIS PERIOD, LAST PERIOD, & DIF |
| `FINANCIALS` | `Table11011` | B18:F21 | MONTH, BUDGET, FORECAST, SPENT TO DATE2, STATUS |
| `FINANCIALS` | `Table11012` | B24:F56 | MONTH #, MONTH, INVOICE SENT, INVOICE PAID, DELTA |
| `FINANCIALS` | `Table110` | H24:J56 | MONTH #, MONTH, OT HOURS WORKED THIS PERIOD |

## What this tells us about the Power BI build

Three findings shape everything downstream:

1. **~40% of the report exists nowhere but this file.** Wins, the entire risk register,
   recovery-plan narratives, client-satisfaction survey, cost-management flags,
   profitability judgment. No amount of Procore/Sage integration produces these. They
   need a home — see [`../../powerbi/manual-input-template.md`](../../powerbi/manual-input-template.md).

2. **The report has no history.** It is a single-month snapshot, and `TODAY()` appears
   in the % complete formula — so reopening a saved file shows different numbers than
   it did when issued. Power BI with a real date dimension gains trend analysis the
   Excel structurally cannot provide.

3. **The scorecard is the most valuable thing here and it is partly broken.** It is a
   genuine, weighted, agreed-upon definition of project health across 9 categories —
   exactly the kind of business logic worth preserving. Three of the nine bands
   currently misfire (see `defects-and-questions.md`). Rebuilding it correctly in DAX
   is the highest-leverage single piece of the build.
