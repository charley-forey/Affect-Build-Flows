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
wins) use the week picked; balances (contract, AR, cost, cash) are as of the last refresh.

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
Construction; inspections in Construction; the rest at every phase. **Phase** is billed % of
contract: under 10% Precon, 10-95% Construction, over 95% Closeout (deck slide 2).

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
  performed - closed, or at least one item answered - not when it is merely scheduled.
- **Meetings**: the series title decides OAC / trade partner (`dashboard_meeting_category.csv`).
  Minutes on time = distributed in Procore on the meeting day or the next. Agenda on time =
  distributed by the day before. Procore's meeting list keeps only the **last** send, so once the
  minutes go out the agenda's time is no longer visible; those agendas read "not verifiable" and
  are not counted against the project. Upgrade: Procore's per-meeting change history records every
  send (verified 2026-10-25), at one request per meeting.
- **Active**: any Procore activity (daily log, meeting, inspection, RFI, submittal, observation) in
  the last 60 days, and not archived. **Archived** = 100% paid (collected / contract >= 99.5%),
  the call's trigger. Inactive and archived jobs are listed under the Portfolio table, not counted.
- **Team**: Procore Directory roles Project Manager, Assistant Project Manager, Superintendent,
  Assistant Superintendent, in that order; the company suffix Procore adds is dropped. Many jobs
  have only some of the four assigned - the column shows what Procore holds.

## What waits for data entry (the deck's TBD callouts)

Shown on the page as waiting, never with sample numbers: revenue and margin **plan**, EBITDA (needs
the Sage general ledger), the **commercial pipeline** and bid hit rate (CRM being replaced),
**executive decisions / watchlist**, and field productivity (calculation criteria). Each is a small
SharePoint list on the existing CD_Manual_Ingest path.

## Data added for this report

- Procore `meetings` and `project_roles` (endpoints.yml; landed 2026-10-25 with the production
  extraction cells, nightly from then on).
- Outbuild `tasks` now read by silver (the look-ahead); activities carry created / updated times.
- Gold `46_dashboard_facts.sql`: fct_Inspection, fct_Meeting, fct_ProjectTeam,
  fct_ScheduleActivity, fct_LookaheadTask, dim_ReportWeek, fct_ProjectPosition; `47_dashboard_score.sql`:
  fct_MetricScore, fct_ProjectScore. Seeds: dim_DashPillar, dim_DashMetric,
  dim_DashBand, dim_DashSetting, seed_InspectionCategory, seed_MeetingCategory.

## Where every number comes from

Source system → gold table the dashboard reads → what it feeds. Gold tables are rebuilt
nightly (02:00 ET); the model is reframed only after the data-quality gate passes.

| Source | Gold table | Feeds |
|---|---|---|
| Procore owner pay apps (prime contracts) | `fct_Billing` → `fct_ProjectPosition` | Billings to date, retainage receivable, billed %, phase, backlog |
| Procore requisitions | `fct_Billing` → `fct_ProjectPosition` | Retainage payable (sub retainage) |
| Procore budget (forecast, job-to-date cost) | `fct_BudgetLine` → `fct_ProjectPosition` | Costs incurred, projected cost and margin (CM fee, division 50, excluded), budget variance, on budget |
| Procore change orders / financial periods | `fct_FinancialPeriod`, `fct_ChangeOrder` | Original and current contract, pending change orders, change orders approved |
| Procore commitments | `fct_BudgetLine` | Subcontractor coverage, risk bought out |
| Sage AR invoices | `fct_Invoice` → `fct_ProjectPosition` | Unpaid receivables, paid to date, AR ageing, AR over 60 days, revenue YTD, unattributed AR |
| Sage AP invoices and lines | `fct_ApInvoice` → `fct_ProjectPosition` | Unpaid payables (job-cost lines, prorated by open balance) |
| Procore meetings (new 2026-10-25) | `fct_Meeting` | OAC and trade partner meeting scores, Grade Detail meeting list, activity |
| Procore inspections | `fct_Inspection` | Safety and quality inspection scores and lists, activity |
| Procore RFIs and submittals | `fct_RfiSubmittal` | Overdue submittals, outstanding RFIs, activity |
| Procore daily logs (manpower) | `fct_SafetyMonthly`, read daily by the score | Activity; daily logs (proposed measure) |
| Procore project directory roles (new) | `fct_ProjectTeam` | Team initials, project executive, team line |
| Outbuild activities (current schedule) | `fct_ScheduleActivity`, `fct_Milestone` | Work progress, completion variance, tracking / forecast finish, near-term milestones, critical path, behind-baseline list, wins, schedule update |
| Outbuild look-ahead tasks (new) | `fct_LookaheadTask` | 3-week look-ahead measure |
| Seeds (`dashboard_*.csv`) | `dim_DashPillar`, `dim_DashMetric`, `dim_DashBand`, `dim_DashSetting` | Weights, measures, bands, targets, cut-offs |
| All of the above | `fct_MetricScore`, `fct_ProjectScore` (`47_dashboard_score.sql`) | Every score, pillar, grade, below-target count and weakest pillar, per project and week |
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

## Open questions for Affect

1. **Gross margin definition** - revised budget less forecast cost, CM fee excluded, gives
   1-8% on active jobs against the 12.5% target. Which costs does Affect's gross profit count?
2. **Profitability bands** - proposed, not in Scorecard.xlsx.
3. **Grade cut-offs** - On track 90 (the deck shows 100), Monitor 75, at risk 45 and below.
4. **Sage jobs with no Procore project** - $1.0M of open AR, notably job 30 "360 Lexington
   15th floor fitout" beside the mapped job 27. Map it to the Procore project? Should
   Sage-only jobs appear financial-only (the call), and which are overhead (job 2 "Office")?
5. **Active** - we use Procore activity in 60 days, not yet 100% paid. Confirm.
6. **Daily logs in the grade** - the call wants them; v1 does not include them. Proposed
   bands: 0 missed 100%, 1-2 75%, 3+ 0%, under Schedule.
7. **Bi-weekly trade partner series** score as a miss every other week under the weekly rule.
8. **Agenda timing** - Procore's meeting list keeps only the last send, so a minuted meeting's
   agenda time is not verifiable. Upgrade: per-meeting change history (one request each).
9. **Reporting week** - default is last full week (read at Monday stand-ups, Tuesday exec).
   The call said "defaults to current": confirm.
10. **Data entry** - revenue plan, pipeline (5 numbers), executive watchlist and pinned
    priority projects, field productivity criteria: SharePoint lists, as agreed.
11. **Refresh cadence** - financials weekly (Sunday night), Procore project data daily.
12. **Week-over-week history** - balances and progress are as of each build; a nightly score
    snapshot would let a reader roll back weeks honestly. Recommended next.

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
