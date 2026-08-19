# D5 — Power BI Project Dashboard (Excel Replacement)

**Status:** 🟢 **Deployed and live** — coverage gated on source data | **Phase:** 2 — Project Intelligence | **Billing:** ~5 hrs in Phase 0 | **Target:** Delivered; parallel run and leadership iteration outstanding

> **The Excel replacement exists and is running in Fabric.** `Monthly Progress Report` — **12 pages, 180 visuals, 99 measures** on a Direct Lake semantic model of **37 tables, 99 measures, 45 relationships** — with drill-through, 3 bookmarks, synced project and month slicers on every page, alt text on all 180 visuals, tab order in reading order, and the validated theme applied. Refreshes nightly. **It has already paid for itself:** a $4.85M understatement of portfolio contract value was found here and fixed (Current Contract $30.25M → $35.10M, growth 0.00% → 16.03%). PDF and page screenshots: [`resources/power-bi/monthly-progress-report/`](../resources/power-bi/monthly-progress-report/).
>
> **It goes beyond the workbook** rather than reproducing it: a Portfolio page (leadership had no cross-project view — the Excel is one workbook per job), a billing S-curve, a schedule timeline, budget as a matrix rolling up by division instead of a flat table over 4,837 cost codes, and a Vendor Insurance page.
>
> **What it still cannot show is other people's turnaround, not build effort.** **Scorecard coverage is 59%** — the canonical figure is maintained in [`build-status.md`](../foundation/charley-dev/_docs/build-status.md). Four of nine categories return BLANK, never zero, because scoring a missing input as zero is exactly how the workbook silently cost every project 15% of its score: Accounts Receivable (Sage), Profitability (manual judgement by design), Completion Variance (Outbuild), Daily Reports (SharePoint). **Quote `Project Scorecard (Measured Only)` = 0.44**, or absent data reads as poor performance. Full picture: [`_docs/dashboard-assessment.md`](../foundation/charley-dev/_docs/dashboard-assessment.md).

## Objective
Replace the manually-maintained Excel project tracker with a Power BI report fed from the curated Lakehouse model — real-time visibility into budget, cost, schedule, and risk across all projects, reusable per project with no manual data entry.

## Scope
**In:** Semantic model on the curated tables; six report pages (overview + schedule, financial, safety & quality, scorecard detail, hidden data quality); the eight sections of the Excel tracker; refresh configuration; rollout to leadership.
**Out:** Schedule data from Outbuild (pending — the Procore API has no `milestone` endpoint, so this may become in-scope), automations (D6/D7).

The Excel tracker has been fully extracted — its eight dashboard sections, 17 tables, 15 pick-lists, and complete formula set are documented in [`analysis/excel-tracker/`](../analysis/excel-tracker/). Scope below is the real thing, not a placeholder.

### The eight sections to reproduce
| Section | Source tab | Notes |
|---|---|---|
| Wins / Focus Areas | `WINS` | Manual; 4+4 cap removed |
| Schedule | `SCHEDULE` | Milestone matrix, completion variance, missed starts, % complete, manpower, priority items |
| Risks | `RISKS` | Manual register; **actually sorted by severity** for the first time |
| Safety | `SAFETY` | Hours, incidents, orientations, violations, activity log |
| Quality | `QUALITY` | Observations, punchlist, aging, offenders, issue log |
| Financial | `FINANCIALS` | Contract waterfall, COs, budget, aging, buyout, cost-mgmt flags |
| Critical Submittals & RFIs | `SUBMITTALS & RFI` | The workbook's only chart — and the cleanest automation win |
| Scorecard | `SCORECARD CALC` | 9 weighted categories + client satisfaction |

## Key data
The scorecard is the highest-value artifact: nine categories, weights summing to exactly 1.00, covering AR, profitability, cash position, change orders, safety, schedule performance, completion variance, observations, and daily reports.

⚠️ **Three of the nine bands are defective in the Excel** — 42% of the total weight is currently disconnected from project reality (see [`defects-and-questions.md`](../analysis/excel-tracker/defects-and-questions.md) #1). The corrected logic is in [`measures.dax`](../powerbi/measures.dax). Present both numbers to Affect; do not silently change what they report.

## Integration approach
Curated Lakehouse tables (D4) → Power BI semantic model (Direct Lake or import) → workspace app for leadership. Scheduled refresh aligned to ETL cadence.

## Tasks
- [x] Extract and assess the Excel tracker (all 11 tabs, formulas, dropdowns, defects)
- [x] Write the semantic model, DAX library, report spec, and theme
- [x] Build semantic model + load `measures.dax` — 37 tables, 99 measures, 45 relationships, Direct Lake
- [x] Build page 1 — Overview (the one-page replacement)
- [x] Build pages 2–5 — Schedule, Financial, Safety & Quality, Scorecard detail
- [x] Build the Data Quality page (hidden)
- [x] Build beyond the spec — Portfolio, billing S-curve, schedule timeline, Vendor Insurance
- [x] **Reconciliation gate** — Current Contract 9,116,960.48 and Contract Growth 3.60% asserted offline, mutation-tested
- [x] Accessibility pass — alt text on all 180 visuals, tab order on every visual, text label beside every status colour, contrast-corrected RAG steps
- [x] Refresh config — pipeline 02:00, model 04:00 Eastern
- [ ] Confirm the page/KPI spec with Rebecca + leadership
- [ ] Access/roles — **row-level security before the Portfolio page is shared**; it is the first page showing every PM each other's jobs
- [ ] Reconciliation **page** in the report — the values are asserted in CI but are not visible to Affect
- [ ] Parallel-run one full monthly cycle with Excel, then cutover — needs 2–3 **real** completed project reports (the file received was a template with demo data)
- [ ] Training walkthrough (recorded) for Rebecca + PMs

## Acceptance criteria
- Leadership uses the dashboard instead of the Excel file for project review
- Every measure reconciles to the tracker's own values (P4 gate), with the three corrected scorecard bands explained and agreed rather than silently applied
- New projects appear automatically; only the genuinely manual ~40% requires entry
- Report exports cleanly to PDF in greyscale with every status readable

## Files & resources
- **[`powerbi/report-spec.md`](../powerbi/report-spec.md)** — page layouts, visuals, number formats, color rules, accessibility checklist
- **[`powerbi/measures.dax`](../powerbi/measures.dax)** — runnable DAX for every KPI, each traceable to the Excel cell it replaces
- **[`powerbi/theme.json`](../powerbi/theme.json)** — validated theme (*View → Themes → Browse* in Desktop)
- **[`powerbi/semantic-model.md`](../powerbi/semantic-model.md)** — the model it builds on
- **[`powerbi/build-plan.md`](../powerbi/build-plan.md)** — phases, estimates, the reconciliation gate
- **[`analysis/excel-tracker/dashboard-map.md`](../analysis/excel-tracker/dashboard-map.md)** — cell-by-cell map of what the current dashboard shows
- **[`resources/power-bi/monthly-progress-report/`](../resources/power-bi/monthly-progress-report/)** — the deployed report as a PDF plus a screenshot of each of the ten pages
- (add: PBIX/workspace link, validation notes, training recording)

## Log
| Date | Note |
|---|---|
| 2026-08-02 | **Deployed.** 12 pages, 180 visuals, 99 measures, all evaluated against live data. Two broken field references found on Project Detail that had failed no deploy, refresh or log — a visual bound to a name the model does not have is invisible to everything except a person looking at that page. `test_report.py` now resolves all 138 field references against the model offline. The validated theme had been sitting unused in the repo while the report ran bare Power BI defaults. |
| 2026-08-13 | Platform review with Rebecca. |
| 2026-08-19 | Unchanged and live; the PDF and the ten page screenshots are published under `resources/power-bi/monthly-progress-report/`. The PQP (Project Quality Plan) subject area is deployed to gold, but **no PQP semantic model or report exists yet** — when built it gets its own model, separate from this one. |
