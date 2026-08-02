-- gold: dim_ScorecardWeight - the 9 category weights, as data rather than as DAX.
--
-- Verbatim from SCORECARD CALC!F4:F30 (analysis/excel-tracker/field-inventory.md:313-326).
-- They sum to exactly 1.00, and the workbook's own total (0.59) reconciles against them -
-- see calculations.md:508-519. This is a genuine, agreed definition of project health and
-- it is the single most valuable piece of business logic in the workbook.
--
-- Weights live in a table so Affect can retune them without a model change. The scorecard
-- is a management judgement about what matters; it should not require a developer.
--
-- EffectiveFrom / EffectiveTo preserve history. Without them, retuning a weight silently
-- rewrites last year's scores - a project that scored 0.72 in March would show a different
-- number the moment someone decided safety mattered more. EffectiveTo NULL = current.

CREATE OR REPLACE TABLE dim_ScorecardWeight AS
SELECT * FROM (VALUES
    (1, 'Accounts Receivable',   0.12, 1, DATE '2023-01-01', CAST(NULL AS DATE)),
    (2, 'Profitability',         0.12, 2, DATE '2023-01-01', CAST(NULL AS DATE)),
    (3, 'Cash Position',         0.12, 3, DATE '2023-01-01', CAST(NULL AS DATE)),
    (4, 'Change Orders',         0.08, 4, DATE '2023-01-01', CAST(NULL AS DATE)),
    (5, 'Safety Incidents',      0.14, 5, DATE '2023-01-01', CAST(NULL AS DATE)),
    (6, 'Schedule Performance',  0.15, 6, DATE '2023-01-01', CAST(NULL AS DATE)),
    (7, 'Completion Variance',   0.15, 7, DATE '2023-01-01', CAST(NULL AS DATE)),
    (8, 'Observations',          0.10, 8, DATE '2023-01-01', CAST(NULL AS DATE)),
    (9, 'Daily Reports',         0.02, 9, DATE '2023-01-01', CAST(NULL AS DATE))
) AS t(CategoryKey, CategoryName, Weight, SortOrder, EffectiveFrom, EffectiveTo);
