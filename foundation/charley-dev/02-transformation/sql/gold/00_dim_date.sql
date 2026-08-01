-- gold: dim_Date - the contiguous calendar, marked as the date table in the model.
--
-- This single table is the fix for the workbook's most fragile mechanic. Every "this
-- period" tile on the DASHBOARD is:
--
--     INDEX(<metric column>, MATCH(AU4, <month column>, 0))
--
-- which requires AU4 to be exactly the 1st, that exact date to exist in every monthly
-- table's month column, and the prior month to exist too. Miss any one and the tile
-- shows #N/A - silently, in a report going to leadership. Three of the workbook's
-- monthly tables already start from different months (defect #4), and TODAY() in the
-- % complete formula makes a saved file show different numbers than when it was issued
-- (defect #5).
--
-- With a real date dimension, DATEADD/PREVIOUSMONTH replace INDEX/MATCH and a slicer
-- replaces AU4. A month either exists in the calendar or it does not; there is no
-- silent #N/A.
--
-- Range covers the longest project the workbook allows (30-31 months) plus a forecast
-- tail. powerbi/build-plan.md:56.
--
-- DIALECT: explode(sequence(...)) is Spark. run_local.py maps both to DuckDB with one
-- macro each. Everything else here uses functions both engines share natively
-- (make_date, last_day, quarter, year, month), so no other shim is needed.
--
-- MonthOffset is computed from year/month arithmetic rather than a months_between()
-- call because the two engines spell that differently. 0 = the current month, negative
-- = past. It is what makes "last 3 months" a filter instead of a hand-edited date.

-- RANGE WIDENED after the first run against real data: change orders, submittals and one
-- financial period fell OUTSIDE 2023-2030, so their MonthStart resolved to nothing and the
-- measures over them would have silently returned blank. Affect has ~14 years of history,
-- so the calendar now starts in 2015 and runs to 2035 for the forecast tail.
CREATE OR REPLACE TABLE dim_Date AS
WITH days AS (
    SELECT explode(sequence(DATE '2015-01-01', DATE '2035-12-31', INTERVAL 1 DAY)) AS Date
),
parts AS (
    SELECT
        CAST(Date AS DATE)                          AS Date,
        year(Date)                                  AS Year,
        quarter(Date)                               AS Quarter,
        month(Date)                                 AS Month,
        day(Date)                                   AS Day,
        make_date(year(Date), month(Date), 1)       AS MonthStart,
        last_day(Date)                              AS MonthEnd
    FROM days
)
SELECT
    Date,
    Year,
    Quarter,
    Month,
    Day,
    MonthStart,
    MonthEnd,
    CASE Month
        WHEN 1 THEN 'January'  WHEN 2 THEN 'February' WHEN 3  THEN 'March'
        WHEN 4 THEN 'April'    WHEN 5 THEN 'May'      WHEN 6  THEN 'June'
        WHEN 7 THEN 'July'     WHEN 8 THEN 'August'   WHEN 9  THEN 'September'
        WHEN 10 THEN 'October' WHEN 11 THEN 'November' WHEN 12 THEN 'December'
    END                                             AS MonthName,
    CASE Month
        WHEN 1 THEN 'Jan' WHEN 2 THEN 'Feb' WHEN 3  THEN 'Mar' WHEN 4  THEN 'Apr'
        WHEN 5 THEN 'May' WHEN 6 THEN 'Jun' WHEN 7  THEN 'Jul' WHEN 8  THEN 'Aug'
        WHEN 9 THEN 'Sep' WHEN 10 THEN 'Oct' WHEN 11 THEN 'Nov' WHEN 12 THEN 'Dec'
    END || ' ' || CAST(Year AS STRING)             AS MonthYear,
    -- Sorts MonthYear chronologically instead of alphabetically ('Apr 2026' first).
    (Year * 100) + Month                            AS MonthYearSort,
    (Year * 12 + Month)
        - (year(CURRENT_DATE) * 12 + month(CURRENT_DATE))
                                                    AS MonthOffset,
    CASE WHEN Date = last_day(Date) THEN TRUE ELSE FALSE END AS IsMonthEnd
FROM parts;
