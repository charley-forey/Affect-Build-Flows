# Project Scorecard report

This report comes out of the 2026-10-09 call. It gives one scorecard-first report for the SharePoint hub: rank every project, re-rank by one pillar, open one project on a single screen, and drill into the records. It sits beside the Monthly Progress Report and the Project Quality Plan, which do not change. It uses the same **Affect Project Report** model, the same nightly pipeline and the same scorecard.

The target is 11/18 for the portfolio and project levels. The executive (financial) report comes after that, as a separate report with its own audience.

## Pages

| Page | What it shows |
|---|---|
| Portfolio Scorecard | Projects ranked by `Pillar Score`, with rank, coverage, categories below target and a *Needs attention* flag. A **Rank by pillar** slicer re-ranks in place. Also: a project × category heatmap, the at-risk count, and the "coming soon" list. |
| Project Health | One project on one screen, picked with the synced Project slicer. It has six tiles: health score (with how it is built), schedule, financial (including change orders open / over 30 days / average age), safety, quality, and challenges. |
| Change Orders | Drill-through (right-click a project). Pending change orders, oldest first. |
| Open Quality Items | Drill-through. Open observations and punch items, oldest first. |

The canvas is 1280×720, the footprint the call agreed fits a full-width SharePoint page.

## How the ranking works

- `Pillar Score` is `Project Scorecard (Measured Only)` computed over the categories left after the pillar slicer. With no pillar selected the two are the same number.
- `Project Rank` is a dense rank of that score. A project with nothing measured gets no rank, rather than ranking last.
- `Needs Attention` fires when 2 or more categories score below 3, whatever the rank. This is the "mediocre on several things" signal. The threshold is `ATTENTION_CATEGORIES` in `_local/scorecard.py`.
- Each category's pillar is in `sql/gold/05_dim_scorecardweight.sql`, next to its weight. The workshop's decisions are edits to that data, not code changes.

## Rollout (respect the F2 budget: one Spark-heavy run a day)

1. `python _local/run_tests.py`. All suites are offline.
2. `python _local/deploy_seeds.py --apply --no-run` uploads the seed SQL that adds `Pillar`. Let the **nightly pipeline** rebuild it. Do not start a manual Spark run.
3. The next morning, check that `gold_schema.json` lists `dim_ScorecardWeight.Pillar`. Then run `deploy_model.py --apply` and `deploy_report_scorecard.py --apply`. **Order matters.** A model that references `Pillar` before gold has the column breaks every report on the model.
4. Run `validate_model.py` and `reconcile_live.py`. Then check the rank in DAX: with no pillar filter, `Pillar Score` equals `Project Scorecard (Measured Only)` for every project.
5. Do a browser check: change the pillar and confirm the order changes; right-click a project to open Change Orders and come back; pick a project and confirm Project Health fills.

## SharePoint

- Add the **Power BI** web part to the communications-site page and paste the report link with the Portfolio Scorecard page. Turn the navigation pane off and keep the filter pane on.
- Viewers need access to the report, through the workspace or a Power BI app audience. The capacity is below F64, so **every viewer needs a Power BI Pro licence.** Flag this to the new IT provider before rollout.
- Data entry stays on each project team site: the `CD Risks` list, shown as "Biggest challenges on site". The hub page links to it.

## Not scored yet, and what unblocks each

| Metric | Unblocked by |
|---|---|
| Completion variance | Gold reading the Outbuild baselines already parsed in `silver/25_outbuild_silver.sql`, instead of `man_Milestones` |
| Daily reports | A silver/gold parser for `cd_bronze_procore_daily_log_headers`, then repointing `Daily Reports Missed` at it |
| Profitability | Affect's gross-margin bands (in range / out of range) |
| Client satisfaction | Integrating the Forms survey |
| Meeting agendas (24h ahead), 3-week look-ahead | A Procore meetings endpoint; Outbuild weekly commitments into silver |
| Insurance compliance | Importing the carrier's weekly verification report, then cross-referencing it against commitments |

## Needed from Affect

- The list of projects to include. This becomes a seed scope flag, filtered at report level only.
- The Sage-only jobs to exclude.
- Confirmed pillars and weights.
- Margin bands.
- The bonus metric sheet, to reconcile against the scorecard categories.
