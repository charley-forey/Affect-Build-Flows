-- gold: dim_ScorecardBand - the 3/2/0 thresholds, as data.
--
-- This is where Excel defects #1a-#1c get fixed ONCE, in a table, instead of in nine
-- nested IF() chains scattered across SCORECARD CALC.
--
-- ============================================================================
-- READ THIS BEFORE SHOWING ANY SCORE TO AFFECT
-- ============================================================================
-- Three of the nine categories in the workbook are not measuring anything - together
-- 42% of the total weight (analysis/excel-tracker/calculations.md:521-524):
--
--   Schedule Performance (0.15) - DASHBOARD!L19 is a FRACTION (0.4 = 40% missed starts)
--       but SCORECARD CALC!E19 compares it to 5, 9 and 10 as if it were a percentage
--       number. 0.4 <= 5 is always TRUE, so this category ALWAYS awards full marks.
--   Completion Variance (0.15) - DASHBOARD!M16 returns the TEXT "0 days" when variance
--       is zero. In Excel text ranks above every number, so "0 days" <= 0 is FALSE and a
--       project finishing exactly on baseline scores ZERO on a 15%-weighted category.
--   Accounts Receivable (0.12) - reads an aging BALANCE against day-count bands.
--
-- The first two errors cancel for the sample project, which is exactly why nobody
-- noticed. With the corrected bands below the same inputs still total 0.59 for that
-- project - but for the right reasons, and they will diverge on the next project.
--
-- Show Affect BOTH numbers side by side with the arithmetic. Do not silently ship a
-- corrected number they have been reporting to leadership. powerbi/build-plan.md:160-174.
-- ============================================================================
--
-- BAND CONVENTION: MinValue is INCLUSIVE, MaxValue is EXCLUSIVE, NULL is unbounded.
-- Half-open intervals mean the bands tile the number line with no gap and no overlap -
-- which the workbook's own bands do not (see the two notes below). Text-valued
-- categories use MatchValue instead and leave both bounds NULL.
--
-- Corrected values per powerbi/semantic-model.md:411-423. Rows marked FIX differ from
-- the workbook.

CREATE OR REPLACE TABLE dim_ScorecardBand AS
SELECT * FROM (VALUES
    -- 1 Accounts Receivable - FIX: driver becomes avg days to payment, not aging balance
    (1, 3, CAST(NULL AS DOUBLE), CAST(45.0 AS DOUBLE), CAST(NULL AS VARCHAR), '< 45 days'),
    (1, 2, CAST(45.0 AS DOUBLE), CAST(61.0 AS DOUBLE), CAST(NULL AS VARCHAR), '45-60 days'),
    (1, 0, CAST(61.0 AS DOUBLE), CAST(NULL AS DOUBLE), CAST(NULL AS VARCHAR), '> 60 days'),

    -- 2 Profitability - text match, a human judgement the workbook stores as a dropdown
    (2, 3, CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE), 'Within Range',                 'Within Range'),
    (2, 2, CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE), 'Out of Range, but has a plan', 'Out of range, has plan'),
    (2, 0, CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE), 'Margin fade but no plan',      'Margin fade, no plan'),

    -- 3 Cash Position - stored as a fraction, so 100% = 1.0.
    -- FIX in the model rather than here: the workbook makes this a dropdown, but the
    -- note in FINANCIALS!G8 spells out the formula
    -- ((Cash Collected + AR Outstanding) / Remaining Forecasted Cost), so it becomes a
    -- measure and stops being one of the three subjective scorecard inputs.
    (3, 3, CAST(1.0 AS DOUBLE),  CAST(NULL AS DOUBLE), CAST(NULL AS VARCHAR), '>= 100%'),
    (3, 2, CAST(0.5 AS DOUBLE),  CAST(1.0 AS DOUBLE),  CAST(NULL AS VARCHAR), '50-99%'),
    (3, 0, CAST(NULL AS DOUBLE), CAST(0.5 AS DOUBLE),  CAST(NULL AS VARCHAR), '< 50%'),

    -- 4 Change Orders - age of oldest unapproved CO, in days
    (4, 3, CAST(NULL AS DOUBLE), CAST(46.0 AS DOUBLE), CAST(NULL AS VARCHAR), '<= 45 days'),
    (4, 2, CAST(46.0 AS DOUBLE), CAST(61.0 AS DOUBLE), CAST(NULL AS VARCHAR), '46-60 days'),
    (4, 0, CAST(61.0 AS DOUBLE), CAST(NULL AS DOUBLE), CAST(NULL AS VARCHAR), '> 60 days'),

    -- 5 Safety Incidents - recordable incidents in the period
    (5, 3, CAST(0.0 AS DOUBLE),  CAST(1.0 AS DOUBLE),  CAST(NULL AS VARCHAR), '0'),
    (5, 2, CAST(1.0 AS DOUBLE),  CAST(2.0 AS DOUBLE),  CAST(NULL AS VARCHAR), '1'),
    (5, 0, CAST(2.0 AS DOUBLE),  CAST(NULL AS DOUBLE), CAST(NULL AS VARCHAR), '>= 2'),

    -- 6 Schedule Performance - FIX: FRACTION not integer. This is defect #1a.
    -- The driver is [Critical Missed Starts %], which returns 0.4 for 40%. The workbook
    -- compared that to 5/9/10, so every project scored 3/3 forever.
    (6, 3, CAST(NULL AS DOUBLE), CAST(0.05 AS DOUBLE), CAST(NULL AS VARCHAR), '< 5%'),
    (6, 2, CAST(0.05 AS DOUBLE), CAST(0.10 AS DOUBLE), CAST(NULL AS VARCHAR), '5-9%'),
    (6, 0, CAST(0.10 AS DOUBLE), CAST(NULL AS DOUBLE), CAST(NULL AS VARCHAR), '>= 10%'),

    -- 7 Completion Variance - FIX: numeric days, no "0 days" string. This is defect #1b.
    -- Finishing on or ahead of baseline is the BEST outcome and now scores 3, not 0.
    (7, 3, CAST(NULL AS DOUBLE), CAST(1.0 AS DOUBLE),  CAST(NULL AS VARCHAR), '<= 0 days'),
    (7, 2, CAST(1.0 AS DOUBLE),  CAST(15.0 AS DOUBLE), CAST(NULL AS VARCHAR), '1-14 days'),
    (7, 0, CAST(15.0 AS DOUBLE), CAST(NULL AS DOUBLE), CAST(NULL AS VARCHAR), '>= 15 days'),

    -- 8 Observations - avg days open.
    -- NEW FINDING: the workbook's bands read "< 5", "6-10", ">= 11" - which leaves the
    -- value 5 unscored, and 10 < x < 11 unscored. Closed here at 6 and 11 so the bands
    -- tile without a hole. Worth confirming Affect intended "<= 5".
    (8, 3, CAST(NULL AS DOUBLE), CAST(6.0 AS DOUBLE),  CAST(NULL AS VARCHAR), '< 6 days'),
    (8, 2, CAST(6.0 AS DOUBLE),  CAST(11.0 AS DOUBLE), CAST(NULL AS VARCHAR), '6-10 days'),
    (8, 0, CAST(11.0 AS DOUBLE), CAST(NULL AS DOUBLE), CAST(NULL AS VARCHAR), '>= 11 days'),

    -- 9 Daily Reports - count not completed/distributed same day.
    -- NEW FINDING: same gap shape as Observations - "< 2", "3-4", ">= 5" leaves 2
    -- unscored. Closed at 2 and 5.
    (9, 3, CAST(NULL AS DOUBLE), CAST(2.0 AS DOUBLE),  CAST(NULL AS VARCHAR), '< 2'),
    (9, 2, CAST(2.0 AS DOUBLE),  CAST(5.0 AS DOUBLE),  CAST(NULL AS VARCHAR), '2-4'),
    (9, 0, CAST(5.0 AS DOUBLE),  CAST(NULL AS DOUBLE), CAST(NULL AS VARCHAR), '>= 5')
) AS t(CategoryKey, Score, MinValue, MaxValue, MatchValue, BandLabel);
