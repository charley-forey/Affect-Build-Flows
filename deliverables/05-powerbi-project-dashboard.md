# D5 — Power BI Project Dashboard (Excel Replacement)

**Status:** 🔴 Not started | **Phase:** 2 — Project Intelligence | **Billing:** Scoped project (quote after D1) | **Target:** TBD

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
- [ ] Confirm the page/KPI spec with Rebecca + leadership
- [ ] Build semantic model + load `measures.dax`
- [ ] Build page 1 — Overview (the one-page replacement)
- [ ] Build pages 2–5 — Schedule, Financial, Safety & Quality, Scorecard detail
- [ ] Build page 6 — Data Quality (hidden)
- [ ] **Reconciliation gate** — validate against the tracker's cached values (table in [`build-plan.md`](../powerbi/build-plan.md) P4)
- [ ] Accessibility pass — icon+label on every status, greyscale print test
- [ ] Refresh config + access/roles
- [ ] Parallel-run one full monthly cycle with Excel, then cutover
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
- (add: PBIX/workspace link, validation notes, training recording)

## Log
| Date | Note |
|---|---|
| | |
