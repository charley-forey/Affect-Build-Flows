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

## Verification

- Offline: `run_tests.py` (silver fixtures for the new sources, gold over fixtures, the report's
  layout / accessibility / bindings in `test_report_dashboard.py`).
- Live: `validate_model.py` recomputes every scoring and KPI measure independently in Python from
  raw model rows (`validate_dashboard.py`) and compares it with the deployed DAX at portfolio,
  project and month grain. Presentation measures (colours, cell text, row flags) are listed, not
  silently skipped. 2026-10-25: 91 of 91 dashboard measures match, after the move to gold scoring.
