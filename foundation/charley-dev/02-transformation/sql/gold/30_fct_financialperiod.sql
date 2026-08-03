-- gold: fct_FinancialPeriod - one row per project per month. The FINANCIALS tab.
--
-- This table is where the workbook's structure changes shape most. FINANCIALS!Table8 is
-- 13 metrics x two columns, THIS PERIOD and LAST PERIOD, where LAST PERIOD is re-keyed BY
-- HAND every month (analysis/excel-tracker/README.md:72). That column disappears entirely
-- here: prior period is the previous ROW, and DAX reads it with DATEADD.
--
-- Built by aggregating the other facts rather than by a separate extract, so a number in
-- this table can always be drilled to the rows that produced it. The workbook cannot do
-- that - FINANCIALS!C5 is literally "=65000+3158.46+11550+4620" with the components lost.
--
-- Deliberately NOT here:
--   CashPosition  - a measure, not a stored value. FINANCIALS!C8 is a dropdown, but the
--                   note in G8 spells out the formula: (Cash Collected + AR Outstanding)
--                   / Remaining Forecasted Cost. Computing it removes one of the three
--                   subjective inputs to the scorecard.
--   Retainage     - zero on every Sage invoice header (verified, commit db0d11e). Must
--                   come from arivln / actrec.retain / progress billing.
--   Profitability - a genuine human judgement, stays manual.

CREATE OR REPLACE TABLE fct_FinancialPeriod AS
WITH months AS (
    SELECT DISTINCT ProjectKey, MonthStart FROM fct_BudgetLine WHERE MonthStart IS NOT NULL
    UNION
    SELECT DISTINCT ProjectKey, MonthStart FROM fct_Invoice     WHERE MonthStart IS NOT NULL
    UNION
    SELECT DISTINCT ProjectKey, MonthStart FROM fct_ChangeOrder WHERE MonthStart IS NOT NULL
),
budget AS (
    SELECT ProjectKey, MonthStart,
           CAST(SUM(BudgetAmount) AS DOUBLE)     AS BudgetAmount,
           CAST(SUM(ForecastAmount) AS DOUBLE)   AS ForecastAmount,
           CAST(SUM(CommittedAmount) AS DOUBLE)  AS CommittedAmount,
           CAST(SUM(SpentToDate) AS DOUBLE)      AS SpentToDate,
           CAST(SUM(CostToComplete) AS DOUBLE)   AS CostToComplete
    FROM fct_BudgetLine GROUP BY ProjectKey, MonthStart
),
billing AS (
    SELECT ProjectKey, MonthStart,
           CAST(SUM(Amount) AS DOUBLE)      AS BilledThisPeriod,
           CAST(SUM(AmountPaid) AS DOUBLE)  AS PaidThisPeriod,
           CAST(SUM(Balance) AS DOUBLE)     AS ArOutstanding,
           COUNT(*)         AS InvoiceCount
    FROM fct_Invoice GROUP BY ProjectKey, MonthStart
),
co_monthly AS (
    SELECT ProjectKey, MonthStart,
           CAST(SUM(Amount) AS DOUBLE)                                          AS ChangeOrderValue,
           CAST(SUM(CASE WHEN IsPending THEN Amount ELSE 0 END) AS DOUBLE)      AS PendingChangeOrders,
           CAST(MAX(CASE WHEN IsPending THEN DaysOpen END) AS BIGINT)           AS AgeOfOldestUnapprovedCO,
           COUNT(*)                                             AS ChangeOrderCount
    FROM fct_ChangeOrder GROUP BY ProjectKey, MonthStart
),
-- Change orders ACCUMULATE. A CO approved in March is still in the contract in December,
-- so every column below is a running total to that month, not that month's activity.
--
-- This was per-month until 2026-08-02, and it silently understated the portfolio by
-- $4.85M. The DAX reads this table with LASTNONBLANKVALUE - the latest row per project -
-- so a per-month CurrentContract meant the dashboard showed only the FINAL month's change
-- orders and dropped every approved CO before it. Contract Growth read 0.00% against 307
-- change orders. The fixture that guarded this had one month of COs per project, where
-- per-month and cumulative are identical, so the gate passed on both.
--
-- Rolled over the `months` spine rather than over co_monthly, so a month with no change
-- order still carries the contract as it stood, instead of falling back to original.
change_orders AS (
    SELECT m.ProjectKey, m.MonthStart,
           CAST(SUM(COALESCE(c.ChangeOrderValue, 0)) OVER (
                PARTITION BY m.ProjectKey ORDER BY m.MonthStart
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS DOUBLE)    AS ChangeOrderValue,
           CAST(SUM(COALESCE(c.PendingChangeOrders, 0)) OVER (
                PARTITION BY m.ProjectKey ORDER BY m.MonthStart
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS DOUBLE)    AS PendingChangeOrders,
           CAST(MAX(c.AgeOfOldestUnapprovedCO) OVER (
                PARTITION BY m.ProjectKey ORDER BY m.MonthStart
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS BIGINT)    AS AgeOfOldestUnapprovedCO,
           CAST(SUM(COALESCE(c.ChangeOrderCount, 0)) OVER (
                PARTITION BY m.ProjectKey ORDER BY m.MonthStart
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS BIGINT)    AS ChangeOrderCount
    FROM months m
    LEFT JOIN co_monthly c ON m.ProjectKey = c.ProjectKey AND m.MonthStart = c.MonthStart
)
SELECT
    m.ProjectKey,
    m.MonthStart,
    p.OriginalContractAmount                          AS OriginalContract,
    -- Current contract = original + approved change orders TO DATE, which is what
    -- FINANCIALS!C4 holds and what every "% of contract" tile divides by. Both CO terms
    -- are running totals (see change_orders above), so this row is the contract as it
    -- stood that month - it never goes down unless a CO was itself negative.
    CAST(COALESCE(p.OriginalContractAmount, 0)
         + COALESCE(c.ChangeOrderValue, 0)
         - COALESCE(c.PendingChangeOrders, 0) AS DOUBLE) AS CurrentContract,
    c.PendingChangeOrders,
    c.AgeOfOldestUnapprovedCO,
    c.ChangeOrderCount,
    b.BudgetAmount,
    b.ForecastAmount,
    b.CommittedAmount,
    b.SpentToDate,
    b.CostToComplete,
    i.BilledThisPeriod,
    i.PaidThisPeriod,
    i.ArOutstanding,
    i.InvoiceCount,
    -- Buyout: committed / budgeted. FINANCIALS!D62 computes this from two hand-typed cells
    -- currently holding 200,000,000 and 190,000,001 against a $9.1M contract (defect #12).
    CASE WHEN COALESCE(b.BudgetAmount, 0) = 0 THEN NULL
         ELSE CAST(b.CommittedAmount / b.BudgetAmount AS DOUBLE) END AS PercentBoughtOut
FROM months m
LEFT JOIN dim_Project  p ON m.ProjectKey = p.ProjectKey
LEFT JOIN budget       b ON m.ProjectKey = b.ProjectKey AND m.MonthStart = b.MonthStart
LEFT JOIN billing      i ON m.ProjectKey = i.ProjectKey AND m.MonthStart = i.MonthStart
LEFT JOIN change_orders c ON m.ProjectKey = c.ProjectKey AND m.MonthStart = c.MonthStart;
