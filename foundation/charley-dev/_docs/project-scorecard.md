# Project Scorecard report

This report comes out of the 2026-10-09 call and Cal Egan's follow-up of 2026-10-13. It is one scorecard-first report for the SharePoint hub, with a single main page that you click down from. It sits beside the Monthly Progress Report and the Project Quality Plan, which do not change. It uses the same **Affect Project Report** model, the same nightly pipeline and the same scorecard.

The target is 11/18 for the portfolio and project levels. The executive (financial) report comes after that, as a separate report with its own audience.

## The hierarchy: one main page, then click down

```
Portfolio Scorecard   (the main page: every project on one table)
  └─ right-click a project ▸ Drill through ▸
       Project Health        (one project, six section tiles on one screen)
         ├─ Schedule  "Details >"  ▸ Schedule & Data Entry
         ├─ Financial "Details >"  ▸ Change Orders
         ├─ Quality   "Details >"  ▸ Open Quality Items
         └─ Data entry "Details >" ▸ Schedule & Data Entry
```

Only the Portfolio is in the page tabs. Every other page is a drill-through page: it opens already filtered to the project you came from, and has a **< Back** button. Every section page is also in the right-click menu on the Portfolio table, so the buttons are shortcuts, never the only way in.

| Page | What it shows |
|---|---|
| **Portfolio Scorecard** | **All projects on one table**, one row each: rank, ranked score, one column per pillar (Financial, Schedule, Safety & Quality, Reporting), share measured, bonus rating, *Needs attention*, and the data-entry check. A **Rank by pillar** slicer re-ranks in place. Also shows the number of projects reporting and at risk, and the "coming soon" list. |
| Project Health | One project. Tiles: health score and bonus rating (with how the score is built), schedule, financial, safety, quality, and data entry & challenges. |
| Schedule & Data Entry | Scheduled finish, last daily log, days since the last log, daily reports missed, the data-entry check, critical-path milestones, and missed daily reports by month. |
| Change Orders | Pending change orders, oldest first. |
| Open Quality Items | Open observations and punch items, oldest first. |

The canvas is 1280×720, the footprint the call agreed fits a full-width SharePoint page.

## Is the data actually being entered?

This answers Cal's 2026-10-13 question. A score is only as good as its inputs, so every project now carries a **data-entry check**. It is shown as text, on the Portfolio table and on Project Health, and is blank when nothing is wrong:

| Check | Rule | Effect |
|---|---|---|
| **Schedule ended - site still active** | The last critical-path finish in Outbuild has passed, but Procore daily logs are still being filed after it **or** punch items are still open | **Schedule Performance scores 0** until the schedule is updated. Without this, a schedule that "ran out" reads as every milestone done and scores 3/3. |
| No daily log for *N* days | The schedule says the job is live, but the last Procore daily log is more than 7 days old | Flag only |
| No daily logs in Procore | The schedule says the job is live, but there are no logs at all | Flag only |
| No schedule in Outbuild | Daily logs filed in the last 30 days, but there is no schedule | Flag only |

**Daily Reports is now scored from Procore**, instead of the hand-typed list (which is still empty). A Procore manpower entry only exists inside a filed daily log. So a weekday with no entry, between the month's first and last log, counts as a daily report missed. A site that stops logging altogether is caught by the "No daily log" check instead.

Limits, stated:
- Public holidays count as weekdays.
- "Missed" means not filed at all, not "filed late". Same-day filing needs the daily-log timestamps, which the 30-day `/daily_logs` extract does not give us yet.

The thresholds (7 days, 30 days) live in `_local/scorecard.py`.

## Checked against the Performance Bonus & Incentive Policy

The policy's project bucket is 25% of each bonus. A project is rated on a five-tier scale, and the tier sets the multiplier. The scorecard now produces that rating.

| Rating | Multiplier | Score needed (**proposed**) |
|---|---|---|
| Outstanding | 150% | 0.90 or more |
| Exceeds Expectations | 115% | 0.75 to 0.89 |
| Meets Expectations | 100% | 0.60 to 0.74 (0.60 is the existing at-risk line) |
| Needs Improvement | 50% | 0.40 to 0.59 |
| Unacceptable | 0% | below 0.40 |

**Safety & Quality gate.** The policy says: "A project will be rated as Needs Improvement if either Safety or Quality is subpar." Below target (under 3 of 3) on Safety Incidents or Observations caps the rating at Needs Improvement, whatever the score. Two points to confirm:
- The policy names the tiers but not the cut-offs, so the cut-offs above are a proposal for the workshop.
- "Subpar" is read here as "below target".

**How the policy's metrics map to the scorecard:**

| Policy metric | Scorecard today | Gap |
|---|---|---|
| Safety & Quality | Safety Incidents (Procore), Observations (Procore), plus the gate | none |
| Schedule: critical missed starts vs adjusted baseline; recovery plans | Schedule Performance (overdue critical milestones, Outbuild), Completion Variance | Baseline dates. Completion Variance stays blank until Outbuild baselines are read. Recovery plans are not tracked. |
| Reporting / OAC: monthly reports on time, OAC agenda 24h ahead, minutes in 24h | Daily Reports (Procore) | Meeting agendas and minutes need the Procore meetings endpoint |
| Financial: cash vs baseline cash plan, GP vs estimate, AR requisitions on time | AR days to payment, Cash Position, Change Orders, Profitability | Baseline cash plan: the WIP projection workbook (an S-curve by duration) is the template. GP needs margin bands. |
| Compliance: statutory sign-offs first time, zero NCRs | none | Procore NCRs are already in gold (`fct_QcNcr`). Needs a weight and a pillar. |
| Client / Vendor (10% in the policy): client NPS at substantial completion | Client Satisfaction measure exists; the list is empty | Import Megan's Forms responses |

Adding Compliance and Client/Vendor as scored pillars is a workshop decision: weights must still total 1.00. Once the weights are agreed, adding them is a data edit in `05_dim_scorecardweight.sql` plus a line in `scorecard.PILLARS`.

## How the ranking works

- **`Pillar Score`** is `Project Scorecard (Measured Only)` computed over the categories left after the pillar slicer. With no pillar selected, the two are the same number.
- **The pillar columns** each fix their pillar, so they do not move with the slicer.
- **`Project Rank`** is a dense rank of that score. A project with nothing measured gets no rank, rather than ranking last.
- **`Needs Attention`** fires when 2 or more categories score below 3, whatever the rank.
- **Each category's pillar** is in `sql/gold/05_dim_scorecardweight.sql`, next to its weight.

## Answers to the 2026-10-13 questions

**1. Sage-only jobs (Profoods, 260 Madison, the 360L common-space work).** Recommendation: every Sage job either maps to a Procore project or is explicitly a *Sage-only job*. These are the Sage jobs with billing but no Procore project:

| Sage job | Name | Billed | Suggested treatment |
|---|---|---|---|
| 29 | Profoods 10101 Foster Avenue | $45,075 (3 invoices) | Sage-only until it is set up in Procore |
| 23 | 260 Madison | $21,959 (4) | Sage-only |
| 25 | Ground Floor Remediation (Basement) | $47,859 (2) | Roll up to 360 Lexington if that is the "360L common space" |
| 26 | Ground Floor Demising Wall | $23,462 (3) | Roll up to 360 Lexington if that is the "360L common space" |
| 24 | 11 Essex Day Two | $52,994 (1) | Roll up to 11 Essex (job 1) |
| 4, 7, 8, 21 | 59 Maiden Lane, 247 E 117th, Wildflower, 1638 Park Ave | $477,912 (10) | Sage-only (older jobs) |

**Boys & Girls Club is already captured.** It is Sage job 18, mapped to its Procore project, with $247,312 billed.

A Sage-only job would show in financial and AR reporting under its own name, instead of "Unassigned". It would be left off the scorecard, which has nothing operational to score for it. A roll-up is one row in `seed/project_crosswalk.csv`. Built once Affect confirms the treatment of each job: it changes which totals reconcile where, so it is not guessed.

**2. Office job (Sage job 2).** It is company overhead (payroll transfers, insurance refunds, reimbursables), not project billing: 15 AR entries, $816,455.42. Recommendation: leave it out of project reporting and keep it for the executive (company) report, once Rebecca confirms. The line-by-line breakdown went to Affect directly, not into this public repo.

**3. Insurance.** The Procore certificate data is now disregarded. Recommended store: CRS's Monday compliance workbook (Jencap 3rd Party Contractor Verification Program).
1. A Power Automate flow saves the attachment to a SharePoint library.
2. The nightly dataflow loads the newest file.
3. Gold keeps one row per contractor per week, so there is history.
4. The report shows Not-OK-to-Work contractors who have an active Procore commitment or manpower on site (the real exposure), plus GL/WC expiring within 30 days and the deficiency text.

The 2026-10-05 file has 33 active contracts: 25 OK to work, 8 deficient. If the provider changes at the December renewal, only the column mapping changes.

**4. Manual lists.** PMs and Superintendents. The full table is in [`sharepoint-lists.md`](sharepoint-lists.md#who-owns-what-agreed-with-affect-2026-10-13). Safety, daily-log, quality and survey lists are retired in favour of Procore and Forms. `CD Risks` stays as the one manual input.

## Keeping it live and correct

Every layer has a check, and they run in this order:

1. **Offline, before anything ships:** `python _local/run_tests.py`.
   - 28 suites: SQL in DuckDB, DQ rule mutations, report geometry, text fit, alt text, and every field reference resolving against the model.
   - The weekday arithmetic behind Daily Reports Missed was also fuzzed against Python over 2,000 random ranges.
2. **Every night:** the pipeline gate.
   - 217 DQ rules; a blocking failure stops publish.
   - Every page's footer shows the last refresh and the pipeline status, so a stale report says so.
3. **After every deploy:**
   - `validate_model.py` recomputes every measure, the new ones included, independently in Python from the raw rows, and compares it per project, per month and per category.
   - `reconcile_live.py` checks AR conservation from bronze to the model.
4. **In use:** the data-entry check on the Portfolio table is the standing check that the inputs themselves are being filled in.

## Rollout (respect the F2 budget: one Spark-heavy run a day)

1. Run `python _local/run_tests.py`. All suites are offline.
2. Run `python _local/deploy_gold.py --apply --no-run` to upload the gold SQL (`fct_SafetyMonthly` daily-log columns) without starting Spark. Let the **nightly pipeline** rebuild it.
3. The next morning, check that `gold_schema.json` lists `fct_SafetyMonthly.DailyLogsMissed`. Then:
   ```
   python deploy_model.py --apply
   python deploy_report_scorecard.py --apply
   ```
   **Order matters.** A model that references columns gold does not have yet breaks every report on the model.
4. Run `validate_model.py` and `reconcile_live.py`. Then confirm in DAX that, with no pillar filter, `Pillar Score` equals `Project Scorecard (Measured Only)` for every project.
5. Do a browser check:
   - On the Portfolio, right-click a project and open Project Health.
   - Each Details button opens its section.
   - Back returns to the previous page.
   - Changing the pillar re-ranks the table.

## SharePoint

- Add the **Power BI** web part to the communications-site page and paste the report link with the Portfolio Scorecard page. Turn the navigation pane off and keep the filter pane on.
- Viewers need access to the report, through the workspace or a Power BI app audience. The capacity is below F64, so **every viewer needs a Power BI Pro licence.** Flag this to the new IT provider before rollout.
- Data entry stays on each project team site: the `CD Risks` list, shown as "Biggest challenges on site". The hub page links to it.

## Not scored yet, and what unblocks each

| Metric | Unblocked by |
|---|---|
| Completion variance | Gold reading the Outbuild baselines already parsed in `silver/25_outbuild_silver.sql`, instead of `man_Milestones` |
| Profitability | Affect's gross-margin bands (in range / out of range) |
| Client satisfaction | Importing Megan's Forms survey responses |
| Compliance (sign-offs, NCRs) | A weight and pillar for it; NCR data is already in gold |
| Meeting agendas (24h ahead), 3-week look-ahead | A Procore meetings endpoint; Outbuild weekly commitments into silver |
| Insurance compliance | Importing the CRS weekly report (see answer 3) |

## Needed from Affect

- **Rating cut-offs and the meaning of "subpar"** for the Safety & Quality gate.
- **Weights for Compliance and Client/Vendor**, if they become scored pillars.
- **Treatment of each Sage-only job** (table above), and Rebecca on the Office job.
- **Go-ahead on the CRS import**, and who receives the Monday email.
- The list of projects to include, and the margin bands.
