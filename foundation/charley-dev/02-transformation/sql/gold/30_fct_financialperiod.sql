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
change_orders AS (
    SELECT ProjectKey, MonthStart,
           CAST(SUM(Amount) AS DOUBLE)                                          AS ChangeOrderValue,
           CAST(SUM(CASE WHEN IsPending THEN Amount ELSE 0 END) AS DOUBLE)      AS PendingChangeOrders,
           CAST(MAX(CASE WHEN IsPending THEN DaysOpen END) AS BIGINT)           AS AgeOfOldestUnapprovedCO,
           COUNT(*)                                             AS ChangeOrderCount
    FROM fct_ChangeOrder GROUP BY ProjectKey, MonthStart
)
SELECT
    m.ProjectKey,
    m.MonthStart,
    p.OriginalContractAmount                          AS OriginalContract,
    -- Current contract = original + approved change orders, which is what
    -- FINANCIALS!C4 holds and what every "% of contract" tile divides by.
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
