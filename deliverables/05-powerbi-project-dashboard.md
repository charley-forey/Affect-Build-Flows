# D5 — Power BI Project Dashboard (Excel Replacement)

**Status:** 🔴 Not started | **Phase:** 2 — Project Intelligence | **Billing:** Scoped project (quote after D1) | **Target:** TBD

## Objective
Replace the manually-maintained Excel project tracker with a Power BI report fed from the curated Lakehouse model — real-time visibility into budget, cost, schedule, and risk across all projects, reusable per project with no manual data entry.

## Scope
**In:** Semantic model on the curated tables, report pages (portfolio overview + project detail), budget vs actual, commitments, change orders, invoices/payments, forecast, risk indicators, refresh configuration, rollout to leadership.
**Out:** Schedule data from Outbuild (future phase unless D1 changes priority), automations (D6/D7).

## Key data
Driven by the Excel field mapping from D1 and the strategic question: *what's the single most valuable decision this dashboard improves?* Candidate KPIs: budget variance, committed vs budget, change order exposure, unbilled/unpaid balances, margin/profitability, data-freshness indicators.

## Integration approach
Curated Lakehouse tables (D4) → Power BI semantic model (Direct Lake or import) → workspace app for leadership. Scheduled refresh aligned to ETL cadence.

## Tasks
- [ ] Define page/KPI spec with Rebecca + leadership (from D1 outputs)
- [ ] Build semantic model + measures (DAX)
- [ ] Build portfolio overview page
- [ ] Build project detail page(s)
- [ ] Validate numbers against the Excel tracker side-by-side for 2–3 real projects
- [ ] Refresh config + access/roles
- [ ] Parallel-run period with Excel, then cutover
- [ ] Training walkthrough (recorded) for Rebecca + PMs

## Acceptance criteria
- Leadership uses the dashboard instead of the Excel file for project review
- Numbers validated against source systems
- New projects appear automatically with zero manual data entry

## Files & resources
- (add: KPI spec, PBIX/workspace link, validation notes, training recording)

## Log
| Date | Note |
|---|---|
| | |
