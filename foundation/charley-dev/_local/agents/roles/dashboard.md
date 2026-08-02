# Role: Dashboard

You own the semantic model (TMDL) and the report (PBIR), plus the scripts that build and
verify them: `_local/deploy_model.py`, `_local/deploy_report.py`, `_local/scorecard.py`,
`_local/validate_model.py`.

## State

`Affect Project Report` is live: 26 tables, 52 measures, 31 relationships, Direct Lake over
`CD_Gold_Lakehouse`, reframed and queryable. `Monthly Progress Report` renders six pages.
`[Scorecard Coverage %]` reads 35% — the ceiling until manual inputs and field-ops facts land.

## Traps already paid for — every one of these failed silently

- **`Current` is a reserved word in DAX.** `VAR Current` does not parse; the service
  substitutes SYNTAXERROR and *every* measure in the model breaks at once. The variable is
  now named `Forecast`.
- **Direct Lake does not support calculated tables.** A model using one deploys
  "successfully", loads zero tables, and every query returns "Failed to resolve name". The
  fix was a physical one-row `measures_anchor` table for measures to hang off.
- **`CREATE TABLE (cols)` with no rows writes no data files**, so Direct Lake cannot bind and
  refresh fails with "source tables either do not exist or access was denied". Write an empty
  DataFrame with `overwriteSchema`.
- **`entityName` must be lowercase** — Spark lowercases on write.
- **A model is not queryable until reframed.** `deploy_model.py` calls the Power BI refresh
  API; skipping it leaves a model that looks deployed and answers nothing.
- **TMDL is whitespace- and order-sensitive**: `///` descriptions precede the object,
  multi-line DAX goes entirely below the `=`, files must be LF.
- **PBIR is strict**: `byConnection` accepts only `connectionString`; `report.json` rejects
  `useNewFilterPaneExperience`.
- Partition type cannot change in place — `deploy_model.py --recreate` exists for that.

## Verification

`validate_model.py` runs live DAX checks. The reconciliation gate is nine measures at
`2025-05-01` for the sample project (`[Current Contract]` = 9,116,960.48, `[Total Billed]` =
2,997,804.23, `[Avg Days To Payment]` = 8.82, and six more). Those are asserted, not eyeballed.

## The scorecard rule

`[Project Scorecard]` deliberately does **not** reproduce the workbook's 0.59. Two band
errors cancel: a schedule band that always scores 3 and a completion-variance band that
always scores 0. Show corrected and as-reported side by side with the arithmetic visible.
Affect decides when to switch the number they report to leadership — not us, and never
silently.

## Depth work, in priority order

1. RAG status as **icon + label**, never colour alone. `powerbi/theme.json` already encodes
   the rule; this goes to leadership and 8% of men are colour-blind.
2. Drill-through portfolio → project → line item. The workbook has one row per project and no
   way down; this is the single biggest thing it cannot do.
3. Tooltip pages on KPI cards, showing a number's components without leaving the page.
4. The scorecard side-by-side above.
5. `HasOutOfRangeDate` / `IsInCrosswalk` surfaced as visual-level warnings so the known
   orphans stay visible instead of quietly rolling up.
6. Bookmarks for period / project / trade; a field-parameter measure switcher on the trend
   chart; `[Scorecard Coverage %]` shown on the scorecard page.
