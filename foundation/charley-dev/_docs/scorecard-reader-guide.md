# Project Scorecard: a reader's guide

For Affect leadership, PMs and superintendents.

## 1. What it is for

The scorecard rates every project on one agreed, weighted measure of health, so projects can be compared and ranked. It also shows what is pulling a score down and whether the data behind it is being entered.

It is a Power BI report on the SharePoint hub. It refreshes every night from Procore, Sage and Outbuild.

## 2. Reading the Portfolio

The Portfolio is the main page. It has one row per active project, ranked best first.

| Column | What it means |
|---|---|
| Rank | Position by ranked score, 1 = best. Blank if there is not enough data to score. |
| Number, Project | Job number and name. |
| Ranked score | 0 to 1. The overall score, or one pillar's score if a pillar is picked. |
| Financial, Schedule, Safety & Quality, Reporting | The score for each pillar, 0 to 1. These do not change when you pick a pillar. |
| Coverage | The share of the total weight that is actually measured. |
| Bonus rating | The bonus-policy tier (section 4). "(capped by …)" means a Safety or Observations score below full marks lowered the rating, and names which one. |
| Main issue | The lowest-scoring category, e.g. "Observations 0/3 +1 more". "+1 more" counts the other categories below full marks. Blank = all on target. |
| Data-entry check | A data problem to fix (section 5). Blank = no problem. |
| Status | Active, Inactive or No daily logs. |

- **Active filter.** The main table shows Active projects only: a Procore daily log in the last 60 days. To include the rest, clear *Project Status* in the Filters pane.
- **Not active table.** Below the main table. It lists projects with no daily log in 60+ days (likely closed) or none at all, with the last log date.
- **Rank by pillar.** Pick a pillar to re-rank by that part of the score only. Clear it to go back to the overall score.
- **Month.** Limits the scores to the months picked; the default is all months. Last daily log, scheduled finish and completion variance always read as of today.

## 3. The nine categories

Each category scores 3, 2 or 0. The bands below are exactly as set in the scorecard tables.

| Category | Pillar | Weight | What is measured | Source | 3 points | 2 points | 0 points |
|---|---|---|---|---|---|---|---|
| Accounts Receivable | Financial | 12% | Average days from invoice sent to paid. An unpaid invoice counts at its age today. | Sage | under 45 days | 45 to under 61 | 61 or more |
| Profitability | Financial | 12% | Margin judgement, entered by hand | Manual entry | Within range | Out of range, has a plan | Margin fade, no plan |
| Cash Position | Financial | 12% | Billed to date (paid plus still owed) divided by cost to complete | Sage, Procore | 100% or more | 50% to 99% | under 50% |
| Change Orders | Financial | 8% | Age of the oldest pending change order | Procore | 45 days or less | 46 to 60 | over 60 |
| Safety Incidents | Safety & Quality | 14% | Recordable incidents in the last 12 months | Procore | 0 | 1 | 2 or more |
| Schedule Performance | Schedule | 15% | Share of critical-path milestones past their finish and not complete | Outbuild | under 5% | 5% to 9% | 10% or more |
| Completion Variance | Schedule | 15% | Forecast completion minus baseline completion, in days | Outbuild | 0 or ahead | 1 to 14 days late | 15 or more late |
| Observations | Safety & Quality | 10% | Average days open per observation. Closed ones count at their days to close, open ones at their age today. | Procore | under 6 days | 6 to 10 | 11 or more |
| Daily Reports | Reporting | 2% | Daily reports missed per month, on average | Procore | under 2 | 2 to 4 | 5 or more |

The weights add up to 100%.

Notes:
- **Profitability** is not scored yet. It needs Affect's margin bands.
- **Schedule Performance scores 0** when the schedule has ended but the site is still active (section 5).
- **Daily report missed** = a weekday, not a public holiday, with no Procore daily log. It is counted from the project's first log to its last.
- **Completion Variance** is blank when the schedule has no baseline.

## 4. How the score is built

1. **Each category** gets 3, 2 or 0 points from its band.
2. **Blank never counts as zero.** A category with no data is left out. It does not count against the project.
3. **Weighted average.** The score is the weighted average of the measured categories only, divided by 3, so it runs from 0 to 1.
4. **The 50% rule.** A project is scored, ranked and rated only when at least 50% of the weight is measured. Below that, the rating reads **"Not enough data"** and there is no rank. A project with nothing measured shows blank.
5. **Rounding.** The score shows to 2 decimal places. The rating uses the rounded number, so 0.8995 shows 0.90 and rates Outstanding.

**Rating tiers (Performance Bonus & Incentive Policy).** The policy names the tiers and multipliers. The score cut-offs are **proposed, pending Affect**.

| Rating | Multiplier | Score (proposed) |
|---|---|---|
| Outstanding | 150% | 0.90 or more |
| Exceeds Expectations | 115% | 0.75 to 0.89 |
| Meets Expectations | 100% | 0.60 to 0.74 |
| Needs Improvement | 50% | 0.40 to 0.59 |
| Unacceptable | 0% | below 0.40 |

**The Safety & Quality gate.** The policy says a project is rated Needs Improvement if Safety or Quality is subpar. If Safety Incidents or Observations scores below 3, the rating is capped at Needs Improvement, whatever the score. The Bonus rating column then says "(capped by …)". "At risk" means rated Needs Improvement or Unacceptable, including projects capped by the gate.

## 5. Data-entry checks

The Data-entry check column shows one message, or nothing when all is well.

| Message | What it means | What to do |
|---|---|---|
| Schedule ended - site still active | The last critical-path finish in Outbuild has passed, but daily logs are still being filed after it, or punch items are still open. **Schedule Performance scores 0** until this is fixed. | Update the current Outbuild schedule to the real finish. |
| No daily log for *N* days | The schedule says the job is live, but the last Procore daily log is more than 7 days old. | File daily logs, or update the schedule if the job has stopped. |
| No daily logs in Procore | The schedule says the job is live, but there are no daily logs at all. | Start filing daily logs in Procore. |
| No schedule in Outbuild | Daily logs were filed in the last 30 days, but there is no schedule. | Set up the schedule in Outbuild, linked to the Procore project. |

**Top 5 things a PM or superintendent can do:**
1. **Close observations in Procore** once they are resolved. Open ones keep ageing and pull down Observations, which also triggers the gate.
2. **Void dead change orders in Procore.** A forgotten pending change order counts as the oldest, and scores 0 after 60 days.
3. **Set the trade on punch items and NCRs.** Items without a trade cannot be assigned or reported properly.
4. **Keep the current Outbuild schedule current and baselined.** Only the schedule marked current is read. Without a baseline, Completion Variance cannot be scored.
5. **File a Procore daily log every working day.** It drives Daily Reports, Active status and the data-entry checks.

## 6. Drilling down

1. On the **Portfolio**, right-click a project and choose **Drill through > Project Health**.
2. **Project Health** shows the score, rating and coverage, how each of the nine categories adds up, and tiles for Schedule, Financial, Safety & quality, and Data entry.
3. Select the project name at the top to enable **Details >**. Each opens a section page: Schedule & Data Entry, Change Orders or Open Quality Items.
4. **< Back** returns to the previous page.

## 7. Assumptions in force until Affect confirms

- **Observation target:** full marks need an average under 6 days open. This caps 9 of 10 rated projects through the gate.
- **Rating cut-offs:** the scores in section 4 are proposed.
- **"Subpar"** for the gate is read as below full marks (under 3 of 3).
- **Public holidays excused:** New Year's Day, Memorial Day, Independence Day, Labor Day, Thanksgiving and the day after, and Christmas (observed dates, 2023 to 2027).
- **Active** = a Procore daily log within the last 60 days.
- **Schedules:** only the current Outbuild schedule is read. Drafts, copies and superseded versions are ignored.
- **Outbuild links set by hand:** City Harvest (the Outbuild copy carrying job number 25-034) and 45 Renwick St (matched to Procore 25-013 by address). Neither has a Procore link in Outbuild itself.
- **Cost to date:** Procore's budget (cost to complete) is the cost source for Cash Position, not Sage.
