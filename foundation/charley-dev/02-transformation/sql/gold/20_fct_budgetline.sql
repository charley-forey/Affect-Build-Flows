-- gold: fct_BudgetLine - budget, forecast, committed and spent per project x cost code.
--
-- Replaces FINANCIALS!Table11011, which the workbook never finished: two data rows, a
-- header reading "SPENT TO DATE2", and a STATUS column hand-picked from a dropdown despite
-- the rule being written out in plain text two columns away (FINANCIALS!H18:J21).
--
-- That rule becomes a measure, not a typed value:
--     variance >= 0      -> On Track
--     -5% <= variance < 0 -> Watch
--     variance < -5%      -> Over Budget
-- It is left to DAX rather than baked in here so the thresholds stay tunable without a
-- pipeline run.
--
-- Grain: one row per project x cost code x snapshot_date. The snapshot column is what
-- gives budget drift over time - the Excel is a single-month artifact and structurally
-- cannot show it.

CREATE OR REPLACE TABLE fct_BudgetLine AS
SELECT
    project_id                          AS ProjectKey,
    COALESCE(cost_code_id, 'UNASSIGNED') AS CostCodeKey,
    snapshot_date                       AS SnapshotDate,
    -- MonthStart is the join to dim_Date. Monthly facts relate on the 1st, so a month
    -- either exists in the calendar or it does not - no silent #N/A.
    CASE WHEN snapshot_date IS NULL THEN NULL
         ELSE make_date(year(snapshot_date), month(snapshot_date), 1) END AS MonthStart,
    TRIM(cost_code)                     AS CostCode,
    TRIM(category)                      AS Category,
    original_budget                     AS OriginalBudget,
    budget_modifications                AS BudgetModifications,
    updated_budget                      AS BudgetAmount,
    forecast_budget                     AS ForecastAmount,
    committed_to_date                   AS CommittedAmount,
    direct_costs                        AS DirectCosts,
    invoiced_to_date                    AS SpentToDate,
    cost_to_complete                    AS CostToComplete,
    -- Stored rather than left to DAX because it is row-level arithmetic, not an aggregate:
    -- summing a per-row variance is meaningful, averaging a pre-aggregated one is not.
    updated_budget - invoiced_to_date   AS BudgetVariance
FROM sv_budgets
WHERE project_id IS NOT NULL;
