# AFFECT Weekly Dashboard

Built 2026-10-25 from the Oct 21 working session, Chris's deck *AFFECT Weekly Dashboard Layout
10-21-26.pptx*, *Scorecard.xlsx* (the v1 project score) and his Cash Position formula (Oct 22).

One Power BI report, **AFFECT Weekly Dashboard**, over the existing *Affect Project Report*
model. Its pages are the deck's three slides, at the deck's own 17 x 11 in geometry, plus the
drill-through behind a grade:

| Page | Deck | Purpose |
|---|---|---|
| Executive Dashboard | slide 1 | The company: revenue, margin, backlog, cash, safety, execution, priority projects |
| Project Portfolio \| Status | slide 2 | Every active project: phase, Safety / Quality / Schedule / Budget, team, grade |
| Project Overview | slide 3 | One project: contract, schedule, financials, top risks, next three weeks, wins |
| Grade Detail (drill-through) | slide 2 callout | Every Scorecard.xlsx measure: reading, band, score, share of the grade |
| Detail \| Revenue, Receivables, Margin & Budget, Contracts & COs, Cash Position, Schedule, Safety & Quality | Oct 30 call | The rows behind each Executive number, with totals that tie to the tile |
| Project Payments | Oct 30 call | One project: owner billed, received and owed; each subcontractor committed, billed, paid, still to pay |
| Data Health | Oct 30 call | Nine input checks on every active project: is the source kept up? |

One report rather than three files, so a project on the Portfolio page drills straight into
its Overview and Grade Detail (the call's "select that project and see what goes to that
score"). Each page has its own URL for sharing.

Code: `_local/dashboard.py` (measures), `_local/deploy_report_dashboard.py` (report),
`02-transformation/sql/gold/46_dashboard_facts.sql` (facts), `47_dashboard_score.sql` (the score),
`02-transformation/seed/dashboard_*.csv`
(the scorecard's weights, bands and settings), `_local/validate_dashboard.py` (independent checks).

## The reporting week

A week slicer on every page: Monday to Sunday, **Last week** by default (read at Monday's stand-ups
and Tuesday's executive meeting). Labels are relative - *This week*, *Last week*, *Week of
2026-10-05* - so the default survives each night's rebuild. Weekly measures (inspections, meetings,
wins) use the week picked, and so does Revenue YTD (Jan 1 to the end of that week, from Oct 30);
balances (contract, AR, cost, cash) are as of the last refresh.

**Saved grades (`fct_ScoreHistory`, from 2026-10-27).** Older weeks in `fct_ProjectScore` are
rescored each night from today's facts, and the Outbuild look-ahead and schedule update exist only
for the latest two weeks, so a week-on-week change read from it is partly an artefact. After the
DQ gate passes, `cd_40_dq_checks` saves last week's grades and pillars
(`sql/snapshot/fct_scorehistory.sql`); each night replaces that week until it rolls over, so the
kept value is what the dashboard last showed as *Last week*. A "vs prior week" measure joins the
model once two weeks are saved. Tested by `tests/test_score_history.py`.

## The v1 score

Four pillars, weighted as agreed on the call (50 / 30 / 15 / 5), each the equal-weighted average
of its measured Scorecard.xlsx measures. The grade is 0-100 over the weight actually measured; a
project with under half the weight measured is **Unscored**, not failing.

| Pillar | Measure (Scorecard.xlsx) | Reads | Scoring (column H) |
|---|---|---|---|
| Schedule | OAC meeting | Procore meetings, OAC series, rolling 4 weeks | misses 0 = 100%, 1 = 75%, 2+ = 0 |
| Schedule | Trade partner meeting | Procore meetings, trade partner series | as above |
| Schedule | 3-week look-ahead | Outbuild look-ahead tasks, days since last worked | 7 days or less = 100%, else 0 |
| Schedule | Monthly schedule update | Outbuild activities, days since last edited | within a month = 100%, else 0 |
| Schedule | Completion variance | Outbuild forecast vs baseline finish, % of baseline duration | 100% less the variance % |
| Schedule | Submittals | Open submittals past due | 0 / 1-2 / 3-5 / 6-10 / >10 = 100 / 80 / 60 / 25 / 0% |
| Schedule | RFIs | Open RFIs past due (or a week old with no due date) | 0 / 1-3 / 4-5 / 6-10 / >10 = 100 / 80 / 60 / 25 / 0% |
| Budget | Cash position | Chris's formula, collected over paid | >= 100% = 100%; 90-100% = cash % less 20 pts; < 90% = 0 |
| Budget | Profitability (gross) | Projected margin vs the 12.5% target | **proposed** bands (not in the workbook) |
| Budget | Aging balance | Balance-weighted age of unpaid AR | 1-30 / 30-60 / 60-90 / >90 days = 100 / 75 / 50 / 0% |
| Safety | Safety inspections | Procore inspections performed in the week | 5 = 80%; -16% each one short; +4% each over, to 100% |
| Quality | Quality inspections | as above | as above |

Stage gating follows the workbook: meetings, the look-ahead and schedule updates score in Precon and
Construction; inspections in Construction; the rest at every phase. **Phase** (Oct 30 call) is read
from Outbuild milestones where the schedule names them (`seed/dashboard_phase_milestone.csv`):
a substantial-completion milestone reached = Closeout; a construction-start milestone ("work start",
"construction start", then "notice to proceed") reached = Construction, not yet reached = Precon.
With no such milestone it falls back to billed % of contract: under 10% Precon, 10-95%
Construction, over 95% Closeout (deck slide 2). `fct_ProjectPosition.PhaseSource` says which, in words.

Coming soon, listed on Grade Detail, never scored: safety observations, forms, quality observations,
punchlist, insurance (Risk).

Every threshold above is a row in `seed/dashboard_band.csv`, every weight in `dashboard_pillar.csv`,
every target and cut-off in `dashboard_setting.csv`. Retuning the score is a CSV edit and
`make_qc_seeds.py`; the next nightly build applies it.

The score is worked out in gold, not in DAX: `47_dashboard_score.sql` writes `fct_MetricScore` (one
row per project, week and measure: driver, band, score) and `fct_ProjectScore` (pillars, coverage,
grade, weakest pillar), and `fct_ProjectPosition` holds each project's contract, billing, cash and
status. Scored as measures, the Portfolio table ran out of F2 query memory; read from gold it
returns in about 2 seconds with the same grades.

## Definitions that needed a decision (made, and flagged)

- **Cash position** (Chris, Oct 22): billings to date - retainage receivable - unpaid receivables -
  (costs incurred - unpaid payables - retainage payable). Billings are Procore owner pay apps,
  which are **gross** of retainage; Sage AR invoices are net (SaunaLounge: Sage billed equals
  Procore earned-less-retainage to the cent), so Sage is used only for a job with no owner pay app.
  Retainage from Procore pay apps and requisitions (Sage holds none). Unpaid AR and AP from Sage.
  Costs incurred = Procore job-to-date cost. The Grade Detail page shows every step.
- **Gross margin**: Procore revised budget less forecast final cost, the CM fee (division 50 of
  the new cost-code master) excluded, because Affect's budgets carry the fee as a line and so equal
  revenue. On this basis active jobs project 1-8%; the 12.5% target suggests Affect's own gross
  profit counts more (general conditions, insurance). **Needs Affect's definition.**
- **Safety vs quality inspections**: Procore's inspection type is blank on every inspection, so
  the template name decides (`seed/dashboard_inspection_category.csv`). An inspection counts once
  its Procore status is **Closed** (Oct 30 call). One started but not closed reads "Not counted -
  started, not closed" on the drill-down (`fct_Inspection.CountedReason`).
- **Meetings**: the series title decides OAC / trade partner (`dashboard_meeting_category.csv`).
  Minutes on time = distributed in Procore on the meeting day or the next. Agenda on time =
  distributed by the day before. Procore's meeting list keeps only the **last** send, so once the
  minutes go out the agenda's time is no longer visible; those agendas read "not verifiable" and
  are not counted against the project. Upgrade: Procore's per-meeting change history records every
  send (verified 2026-10-25), at one request per meeting.
- **Active** (Oct 30 call): the five projects kept live for the Nov 19 rollout, listed in
  `seed/dashboard_project.csv`, while `rollout_only` = 1 in `dashboard_setting.csv`. Every other
  project is Archived. **Archived** also = 100% paid (collected / contract >= 99.5%), the Oct 21
  trigger. With `rollout_only` = 0 the old rule returns: any Procore activity (daily log, meeting,
  inspection, RFI, submittal, observation) in the last 60 days. `fct_ProjectPosition.StatusReason`
  says why. Inactive and archived jobs are listed under the Portfolio table, not counted.
- **Team**: Procore Directory roles Project Manager, Assistant Project Manager, Superintendent,
  Assistant Superintendent, in that order; the company suffix Procore adds is dropped. Many jobs
  have only some of the four assigned - the column shows what Procore holds.

## What waits for data entry (the deck's TBD callouts)

Shown on the page as waiting, never with sample numbers: revenue and margin **plan**, the
**commercial pipeline** and bid hit rate (CRM being replaced), and **executive decisions /
watchlist**. Each is a small SharePoint list on the existing CD_Manual_Ingest path.

Waiting for data, not entry: **net income** (was EBITDA; needs the Sage general ledger) and
**field productivity** (criteria agreed Oct 30, read from Outbuild, not built). See the Oct 30
section below.

## Data added for this report

- Procore `meetings` and `project_roles` (endpoints.yml; landed 2026-10-25 with the production
  extraction cells, nightly from then on).
- Outbuild `tasks` now read by silver (the look-ahead); activities carry created / updated times.
- Gold `46_dashboard_facts.sql`: fct_Inspection, fct_Meeting, fct_ProjectTeam,
  fct_ScheduleActivity, fct_LookaheadTask, dim_ReportWeek, fct_ProjectPosition; `47_dashboard_score.sql`:
  fct_MetricScore, fct_ProjectScore. Seeds: dim_DashPillar, dim_DashMetric,
  dim_DashBand, dim_DashSetting, seed_InspectionCategory, seed_MeetingCategory.
- Oct 30: Sage AR status and job name read by silver (`status_code`, `job_name`); gold
  fct_DashObservation, fct_SubPayment, fct_DashCheck; seeds seed_DashProject,
  seed_ObservationCategory, seed_PhaseMilestone.

## Where every number comes from

Source system → gold table the dashboard reads → what it feeds. Gold tables are rebuilt
nightly (02:00 ET); the model is reframed only after the data-quality gate passes.

| Source | Gold table | Feeds |
|---|---|---|
| Procore owner pay apps (prime contracts) | `fct_Billing` → `fct_ProjectPosition` | Billings to date, retainage receivable, billed %, phase, backlog |
| Procore requisitions | `fct_Billing` → `fct_ProjectPosition`, `fct_SubPayment` | Retainage payable (sub retainage); Project Payments sub side |
| Procore budget (forecast, job-to-date cost) | `fct_BudgetLine` → `fct_ProjectPosition` | Costs incurred, projected cost and margin (CM fee, division 50, excluded), budget variance, on budget |
| Procore change orders / financial periods | `fct_FinancialPeriod`, `fct_ChangeOrder` | Original and current contract, pending change orders, change orders approved |
| Procore commitments | `fct_BudgetLine` | Subcontractor coverage, risk bought out |
| Sage AR invoices (voids at $0) | `fct_Invoice` → `fct_ProjectPosition` | Unpaid receivables, paid to date, AR ageing, AR over 60 days, revenue YTD, unattributed AR |
| Sage AP invoices and lines (voids excluded) | `fct_ApInvoice` → `fct_ProjectPosition`, `fct_SubPayment` | Unpaid payables (job-cost lines, prorated by open balance); Project Payments |
| Procore observations and punch | `fct_QualityItem` → `fct_DashObservation` | Safety and quality data collected beside the score (not in the grade) |
| Procore meetings (new 2026-10-25) | `fct_Meeting` | OAC and trade partner meeting scores, Grade Detail meeting list, activity |
| Procore inspections | `fct_Inspection` | Safety and quality inspection scores and lists, activity |
| Procore RFIs and submittals | `fct_RfiSubmittal` | Overdue submittals, outstanding RFIs, activity |
| Procore daily logs (manpower) | `fct_SafetyMonthly`, read daily by the score | Activity; daily logs (proposed measure) |
| Procore project directory roles (new) | `fct_ProjectTeam` | Team initials, project executive, team line |
| Outbuild activities (current schedule) | `fct_ScheduleActivity`, `fct_Milestone` | Work progress, completion variance, tracking / forecast finish, near-term milestones, critical path, behind-baseline list, wins, schedule update |
| Outbuild look-ahead tasks (new) | `fct_LookaheadTask` | 3-week look-ahead measure |
| Seeds (`dashboard_*.csv`) | `dim_DashPillar`, `dim_DashMetric`, `dim_DashBand`, `dim_DashSetting` | Weights, measures, bands, targets, cut-offs |
| All of the above | `fct_MetricScore`, `fct_ProjectScore` (`47_dashboard_score.sql`) | Every score, pillar, grade, below-target count and weakest pillar, per project and week |
| All of the above | `fct_DashCheck` (`46_dashboard_facts.sql`) | Data Health: nine input checks per project |
| Calendar | `dim_ReportWeek` | Week picker (Monday-Sunday, 52 weeks back), "This week" / "Last week" labels |

## Review pass, 2026-10-25 / 26

An independent code review and a requirements trace (every call request, deck element and
Scorecard.xlsx row against the code) were run. Fixed, each with a pinned test in
`tests/test_dashboard_gold.py`:

- A project with no forecast cost scored 100% profitability; it is now unmeasured.
- A template meeting could make a dead project Active; only held OAC / trade partner meetings
  count as activity.
- Minutes were marked late the morning after the meeting; the day after is the allowance.
- AR age bands: exactly 30 days now reads "1-30 days" (whole-day edges).
- "This week" counted the unfinished week as a missed meeting.
- The weakest pillar is the one losing the grade most points (weight x shortfall), not the
  lowest score - a 0% quality pillar costs 5 points, a 40% schedule pillar 30.
- Coverage is rounded before the 50% gate; Executive Focus lists exactly three measures.

Added: open AR on Sage jobs with no Procore project is stated on the Executive page
(`Data Notice`); the crosswalk-candidate check now also proposes a same-name second Sage job
for a mapped project; Portfolio is stack-ranked worst grade first; the project executive
leads the team line; Project Overview shows billing against work progress; daily logs are
read as a **proposed** measure (shown on Grade Detail, not in the grade).

## Oct 30 call: the work behind every number

Affect reviewed the first build. They accepted the layout but did not yet trust the numbers.
Cal: "our biggest concern is, we throw something out there that is incorrect". They asked for a
drill-down behind every number, "like a general ledger", with totals and an Excel output, so
finance can tie each figure to its own reports. Commit `5b4e74d`. What changed, and why:

| Change | Said on the call | What the code does now |
|---|---|---|
| **Sage voids left out** | Revenue to the end of September read $17.7M against Affect's ~$15.8M billed. The AR "didn't seem correct" - maybe "old AR that hasn't been pulled off" | Sage 100 Contractor keeps a voided invoice (status 5) with its full amount as a balance. 55 AR voids ($5.46M) and 77 AP voids ($1.68M) were being counted. `22_fct_invoice.sql` zeroes AR voids (the row stays, with `VoidedAmount`); every AP reader drops `IsVoid` (`34_fct_apinvoice.sql`) |
| Revenue, Jan 1 - Sep 30 | "Up to the end of September ... like 15.8" | **$16,394,810** (was $17.73M). Months: Jul $1.99M, Aug $1.11M, Sep $1.49M. Cal compared Jul-Sep with Rebecca's spreadsheet and found them close. About $0.6M of gap remains (open question 3) |
| Open AR | "The AR as well ... didn't seem correct" | Open AR **$2.31M**; AR > 60 days **$300K**, voids excluded |
| Second Sage jobs | "There could also be some AR that is not assigned to a project" | Sage job 30 "360 Lexington 15th floor fitout" attached to 360 Lexington 15th as an **additional** job (its $242.6K open AR was unattributed); job 29 "Profoods 10101 Foster Avenue" mapped to Pro Foods. Both **PROPOSED** in `seed/project_crosswalk.csv` - confirm |
| Rollout list | Keep live for 11/19 only "360 15th floor, SaunaLounge, City Harvest, Pro Foods and 45 Renwick" | Only those five are Active (`seed/dashboard_project.csv`, `rollout_only` = 1); every other project is Archived from the dashboard |
| Phase from Outbuild | City Harvest is 20% billed (a mobilization deposit) but not started. "If the construction milestone date hasn't started, it's precon ... substantial completion, closeout" | Phase from Outbuild milestones; billed % only when the schedule names none (`seed/dashboard_phase_milestone.csv`) |
| Inspections count once closed | An inspection "just created ... wasn't fully filled out" showed up as done. "Not really done until it's distributed or the status is closed" | `fct_Inspection.IsPerformed` = status Closed. Started ones are listed as "Not counted - started, not closed" |
| Safety and quality "double barrel" | Keep the inspection count as the score; beside it, "capture all these safety data points" and set up a placeholder grading | Pass rate (the call's example: 60 passed, 27 failed), observations and punch are collected (`fct_DashObservation`, `seed/dashboard_observation_category.csv`). Proposed data scores are shown on Detail \| Safety & Quality, **not in the grade** |
| Revenue YTD follows the week picked | Moving the week to the end of September, "the numbers didn't change" | Revenue YTD = Sage invoiced from Jan 1 to the end of the week picked. Balances (AR, cost, cash) stay as of the last refresh, because Sage holds no history of them |
| Sage month close | "If month close, show data; if not, show previous with a warning". Close goal: the 10th-15th of the next month | Setting `sage_closed_through` (now 2026-09-30) in `dashboard_setting.csv`. The Executive page shows "Sage books closed through ..." and, past that date, "later months provisional (no WIP adjustment yet)". Detail \| Revenue shows the closed-months figure beside the YTD one. **Update the setting when a month closes** |
| EBITDA relabelled **Net income** | "We don't put depreciation ... it'd be like net income basically" | Label changed. Still empty: it needs the Sage general ledger, which is not yet ingested |
| Change-order tile | Pending change orders of "some 190 ... not sure where that was pulled from" | Both halves now read the Procore prime change-order log (`fct_ChangeOrder`: `CO Approved Amount`, `CO Pending Amount`). The pending half used to come from the financial-period balance, which could not be tied to rows |
| Project Payments | "Have we been paid, has this subcontractor been paid": asked all the time, and 30 minutes to answer | New page: owner contract, billed, received and owed; for each sub, committed, billed, retainage, Sage AP paid, still to pay and the age of the oldest unpaid invoice (`fct_SubPayment`) |
| Data Health | "Less validation of the data, more validation of the input": Sage and Procore tie-out, a look-ahead not kept up | Nine checks per project, each build (`fct_DashCheck`, below) |

These figures are billings, not recognised revenue. Cal: "while we may have billed 15.8 million,
if we over-bill 200 thousand, we can only recognize 15.6". The WIP adjustment is in the general
ledger, which is not ingested.

## Where each number is proved

Each Executive tile has a **Data >** link. The revenue panel has **Revenue data >** and the
watchlist has **Data health >**. The link opens a detail page whose top strip repeats the
dashboard figure, and the table total below equals that figure.

| Executive number | Detail page | Table whose total ties to it | Source rows |
|---|---|---|---|
| REVENUE YTD | Detail \| Revenue | Sage AR invoices in Revenue YTD, column *Counted* | Sage AR invoices dated Jan 1 to the week end, every job, voids at $0 (`fct_Invoice`) |
| Revenue by month (chart) | Detail \| Revenue | By month, *Invoiced (counted)* | Sage AR invoices by invoice month (`fct_Invoice`) |
| Closed-months revenue, close warning | Detail \| Revenue | Strip *Closed months only*; by month, *Sage close* | `sage_closed_through` in `dashboard_setting.csv` |
| AR > 60 DAYS | Detail \| Receivables | Open Sage AR invoices, *Owed* on the 61-90 and over-90 rows; by Sage job, *Over 60 days* | Sage AR invoices with a balance, dated over 60 days before the data date |
| Open AR, AR on no Procore project | Detail \| Receivables | Open Sage AR invoices, *Owed* | Sage AR balances, every job (`fct_Invoice`) |
| GROSS MARGIN | Detail \| Margin & Budget | By project, *Revised budget* and *Forecast cost ex fee* | Procore budget lines, CM fee (division 50) left out (`fct_BudgetLine` → `fct_ProjectPosition`) |
| ON BUDGET | Detail \| Margin & Budget | By project, *On budget* | Procore forecast final cost vs revised budget |
| SUBCONTRACTOR COVERAGE | Detail \| Margin & Budget | Budget lines, *Committed* over *Budget* (divisions 01-44) | Procore budget and commitments (`fct_BudgetLine`) |
| BACKLOG | Detail \| Contracts & COs | By project, *Backlog* | Procore prime contracts and the latest owner pay app; Sage invoices where there is no pay app (`fct_ProjectPosition`, `fct_Billing`) |
| ACTIVE PROJECTS | Detail \| Contracts & COs | By project: row count, *Why active* | `seed/dashboard_project.csv` |
| CHANGE ORDERS APPROVED | Detail \| Contracts & COs | Prime change orders, *Approved* and *Pending* | Procore prime change orders (`fct_ChangeOrder`) |
| CASH POSITION | Detail \| Cash Position | By project, *Cash position*; unpaid payables, *Still to pay* | Procore pay apps, requisitions and job-to-date cost; Sage AR and AP, voids excluded |
| SAFETY | Detail \| Safety & Quality | Safety by project, *Closed (week)* and *Score*; inspections dated in the week, *Counted?* | Procore inspections closed in the week (`fct_Inspection`) |
| ON SCHEDULE | Detail \| Schedule | Finish vs baseline, *On schedule* | Outbuild current schedule, forecast vs baseline finish (`fct_ScheduleActivity`) |
| PROJECTS AT RISK | Detail \| Schedule (strip), Project Portfolio \| Status | Grades 45 and below; Grade Detail shows every measure | `fct_ProjectScore` |
| Priority projects | Project Portfolio \| Status → Grade Detail | Grade Detail, share of the grade | `fct_MetricScore` |
| Data notice, warnings | Data Health | Input checks; Sage jobs with no Procore project | `fct_DashCheck`, `fct_Invoice` |
| Project financials (one project) | Project Payments | Owner invoices; subcontractors | `fct_Invoice`, `fct_Billing`, `fct_SubPayment` |

Page names are the display names in `PAGES` (`_local/deploy_report_dashboard.py`).

## How to check a number against your own reports

1. On the Executive page, click **Data >** on the tile.
2. The strip at the top shows the same figure as the tile. The table below adds up to it.
3. To work in Excel, hover over the table, click **...** at its top right, then **Export
   data**. Pick *Summarized data* and the file downloads.
4. Compare it with the Sage report for the same dates:
   - Revenue YTD or a month: the AR invoice list for the period, voids excluded.
   - Open AR and AR > 60 days: the AR aging as of the "balances as of" date in the page header.
   - Unpaid payables, or what a sub is owed: the AP aging for the job.
   - Contract, billed to date, retainage: the latest owner pay app in Procore.
5. Match the rows one by one on the *Sage rec* or invoice number. The *Treatment* column says
   how each row was counted.

What a mismatch usually means:

| You see | Usually means |
|---|---|
| An invoice on the dashboard that your report leaves out | It was voided or reversed, but the void was not posted in Sage |
| A job missing from a project | The invoice is on a Sage job that is not mapped to a Procore project. It still counts in Revenue YTD; see *Sage jobs with no Procore project* on Data Health |
| Last month differs from the interim financials | Sage has not closed the month yet, or the financials include the WIP (over / under billing) adjustment. The dashboard shows billings only |
| Contract, budget, schedule or inspection figures look wrong | Someone has not kept a Procore or Outbuild entry up to date. Check Data Health for that project |

If none of these explains it, send us the exported rows and the Sage report. Then the
difference is in our calculation, and we fix it.

## Data Health checks

`fct_DashCheck` (`46_dashboard_facts.sql`) holds one row per project and check, rebuilt each
night. The result is Pass, Warn, or Info (nothing to compare). The page shows active projects.

| # | Check | Warns when | Who fixes it |
|---|---|---|---|
| 1 | Sage vs Procore billing | Sage invoiced to date differs from Procore earned less retainage by more than 1% (`tieout_tolerance`) | Finance: post or void the difference |
| 2 | Voided Sage invoices | Never warns. Info: how many voids were left out of revenue and AR, and their total | Nobody. Shown so totals tie to Sage reports that exclude voids |
| 3 | Possible duplicate invoices | Two live invoices on one job for the same amount | Finance: void the copy in Sage if it is a re-issue |
| 4 | AR over 90 days | An open invoice is older than 90 days | Finance: collect, or write off / void |
| 5 | 3-week look-ahead updated | No Outbuild look-ahead work in the last 7 days | Field: update the look-ahead every week |
| 6 | Schedule progress kept up | Activities are past their finish date and not marked 100% | Field: mark progress in Outbuild, or re-forecast |
| 7 | Inspections closed | Inspections dated over a week ago are still not closed (and so not counted) | Field: finish and close them in Procore |
| 8 | Team roles in Procore | No Project Manager or no Superintendent in the Procore directory | PM: set the roles |
| 9 | Budget forecast in Procore | No forecast to complete, so margin and on-budget cannot be read | PM / QS: keep the forecast current |

A warning means the dashboard number is only as good as that entry. As Cal put it, the data is
not wrong because the report is wrong; it is wrong because the entry was not made.

## Open questions for Affect

Answered by the Oct 30 call and `5b4e74d`:
- **Active**: the five rollout projects.
- **Phase**: Outbuild milestones.
- **When an inspection counts**: once closed.
- **Refresh cadence**: weekly is fine; Procore twice a week.
- **Week-over-week history**: `fct_ScoreHistory`, saved since Oct 27.
- **Field productivity criteria**: agreed (question 8).

1. **Sage job 30 and job 29**: job 30 is attached to 360 Lexington 15th as an additional job,
   and job 29 to Pro Foods. Both are proposed. Confirm.
2. **Sage jobs 24, 25, 26** (11 Essex Day Two, 360 Lex ground floor remediation, 360 Lex
   demising wall): which Procore project does each belong to, or are they Sage-only? Which jobs
   are overhead (job 2 "Office")?
3. **The remaining gap**: Jan 1 - Sep 30 reads $16.39M against Affect's ~$15.8M, about $0.6M.
   Exporting Detail \| Revenue and comparing it with the Sage invoice list should show which
   invoices make up the gap.
4. **Gross margin definition**: revised budget less forecast cost, CM fee excluded, gives 1-8%
   on active jobs. Affect's interim financials show ~12.5% through September. Cal described the
   goal as 12-15%, total committed over contract value. Which costs does Affect's gross profit
   count? The interim financials would settle it.
5. **Profitability bands**: proposed, not in Scorecard.xlsx.
6. **Grade cut-offs**: On track 90 (the deck shows 100), Monitor 75, at risk 45 and below.
7. **Scoring safety and quality data**: the proposed data scores average the 4-week inspection
   pass rate and the 90-day observation close rate, equally weighted. This is a placeholder, as
   agreed on the call. Still open: weights, critical fails, near misses, incidents, safety wins.
8. **Field productivity**: agreed on the call: the rolling 3-week look-ahead is the plan,
   compared each week with what was actually put in place, rolled up as the job goes. Not built
   yet; the tile says "Next".
9. **Risk register**: Affect used the Procore correspondence tool as a risk register and wants
   the top risks from it. Not ingested yet.
10. **Schedule delay attribution**: a delay the owner caused (compensated) should read
    differently from one Affect caused. Outbuild fragnets may show which is which. Not built.
11. **Data health by email**: a weekly email of the checks (Power Automate). Not built.
12. **Daily logs in the grade**: the call wants them; v1 does not include them. Proposed
    bands: 0 missed 100%, 1-2 75%, 3+ 0%, under Schedule.
13. **Bi-weekly trade partner series** score as a miss every other week under the weekly rule.
14. **Agenda timing**: Procore's meeting list keeps only the last send, so a minuted meeting's
    agenda time is not verifiable. Upgrade: per-meeting change history (one request each).
15. **Reporting week**: the default is the last full week. The call kept the week picker
    weekly; for looking back by month there are the month tables on Detail \| Revenue. The
    Oct 21 call said "defaults to current": confirm.
16. **Data entry**: revenue plan, pipeline (5 numbers), executive watchlist and pinned priority
    projects: SharePoint lists, as agreed.
17. **Month close**: `sage_closed_through` is set by hand. Who updates it when a month closes,
    or can we read the Sage close date?

## Verification

- Offline: `run_tests.py` (silver fixtures for the new sources, gold over fixtures, the report's
  layout / accessibility / bindings in `test_report_dashboard.py`).
- Live: `validate_model.py` recomputes every scoring and KPI measure independently in Python from
  raw model rows (`validate_dashboard.py`) and compares it with the deployed DAX at portfolio,
  project and month grain. Presentation measures (colours, cell text, row flags) are listed, not
  silently skipped. 2026-10-25: 91 of 91 dashboard measures match, after the move to gold scoring.
- Scoring rules: `test_dashboard_gold.py` replaces every input of `47_dashboard_score.sql` with
  one synthetic week and checks each score against the value worked out by hand from
  Scorecard.xlsx, plus the grade, coverage gate, weakest pillar and Cash Position identities.
- Spark dialect: the dashboard SQL also passes analysis on a local Spark 3.5 (Fabric's runtime)
  over empty tables shaped like the fixture build - DuckDB alone can accept SQL Spark rejects.
- This validator re-implements our reading of the rules, so it proves the numbers are
  consistent with that reading; whether the reading is right is the open questions above.
