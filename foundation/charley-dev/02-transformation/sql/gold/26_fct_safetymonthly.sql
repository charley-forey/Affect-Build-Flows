-- gold: fct_SafetyMonthly - hours worked and incidents, per project per month.
--
-- This is SAFETY!Table1, typed by hand every month. It is also the denominator of every
-- safety rate: an incident count without hours is a number nobody can compare between a
-- 12-person job and a 200-person one.
--
-- MONTHLY GRAIN, from DAILY source. Manpower logs are per vendor per day (911 project-days
-- after summing); incidents are events. Both roll to project-month because that is the
-- grain the scorecard and the report use, and because a monthly row is the thing a human
-- can check against a timesheet.
--
-- ONE ROW PER MONTH THAT HAS ANYTHING, deliberately (the union in `months`). A month can
-- have hours and no incidents (the good case, and the common one), an incident recorded
-- against a month with no logged hours (a real data-entry state worth seeing), or no log at
-- all inside the project's logging window (every expected day missed). An inner join would
-- silently drop the last two.

CREATE OR REPLACE TABLE fct_SafetyMonthly AS
WITH logs AS (
    SELECT project_id, log_date, total_hours, total_workers
    FROM sv_manpower_daily
    WHERE project_id IS NOT NULL
      AND log_date IS NOT NULL
      -- Outside dim_Date the month cannot join, and every measure over it returns BLANK -
      -- which on a card is indistinguishable from zero hours worked.
      AND log_date BETWEEN DATE '2015-01-01' AND DATE '2035-12-31'
),
hours AS (
    SELECT
        project_id,
        make_date(year(log_date), month(log_date), 1) AS month_start,
        SUM(total_hours)   AS hours_worked,
        SUM(total_workers) AS worker_days,
        COUNT(*)           AS days_logged,
        MIN(log_date)      AS first_log,
        MAX(log_date)      AS last_log
    FROM logs
    GROUP BY project_id, make_date(year(log_date), month(log_date), 1)
),
-- Daily-log discipline. A Procore manpower entry only exists inside a filed daily log, so
-- an expected day with none is a day with no daily report. Expected = every weekday that
-- is not a public holiday (seed_PublicHoliday), across the project's LOGGING WINDOW: its
-- first log ever to its last log (capped at today). Counted over the whole window, not
-- within each month's own first and last log - otherwise a site that logged Jan 2-10 and
-- then nothing until Feb 5 counted 0 missed in January. Months inside the window with no
-- log at all get a row. A site that stops logging altogether is caught by
-- [Days Since Daily Log] instead of being charged up to today.
-- Weekdays are anchored on Monday 2014-12-29 because Spark and DuckDB number dayofweek()
-- differently; (n % 7) < 5 is Monday-Friday in both.
log_window AS (
    SELECT project_id, MIN(log_date) AS first_log, LEAST(MAX(log_date), current_date) AS last_log
    FROM logs
    GROUP BY project_id
),
logged_days AS (
    SELECT DISTINCT project_id, log_date FROM logs
),
expected_days AS (
    SELECT w.project_id, d.Date AS day,
           make_date(year(d.Date), month(d.Date), 1) AS month_start
    FROM log_window w
    JOIN dim_Date d ON d.Date BETWEEN w.first_log AND w.last_log
    LEFT JOIN seed_PublicHoliday ph ON ph.HolidayDate = d.Date
    WHERE datediff(d.Date, DATE '2014-12-29') % 7 < 5
      AND ph.HolidayDate IS NULL
),
missed AS (
    SELECT e.project_id, e.month_start,
           SUM(CASE WHEN l.log_date IS NOT NULL THEN 1 ELSE 0 END) AS weekdays_logged,
           SUM(CASE WHEN l.log_date IS NULL THEN 1 ELSE 0 END)     AS days_missed
    FROM expected_days e
    LEFT JOIN logged_days l ON l.project_id = e.project_id AND l.log_date = e.day
    GROUP BY e.project_id, e.month_start
),
incidents AS (
    SELECT
        project_id,
        make_date(year(event_date), month(event_date), 1) AS month_start,
        COUNT(*)                                                    AS incident_count,
        SUM(CASE WHEN is_recordable THEN 1 ELSE 0 END)              AS recordable_count
    FROM sv_incidents
    WHERE project_id IS NOT NULL
      AND event_date IS NOT NULL
      AND event_date BETWEEN DATE '2015-01-01' AND DATE '2035-12-31'
    GROUP BY project_id, make_date(year(event_date), month(event_date), 1)
),
months AS (
    SELECT project_id, month_start FROM hours
    UNION SELECT project_id, month_start FROM missed
    UNION SELECT project_id, month_start FROM incidents
)
SELECT
    k.project_id                             AS ProjectKey,
    k.month_start                            AS MonthStart,
    COALESCE(h.hours_worked, 0)              AS HoursWorked,
    COALESCE(h.worker_days, 0)               AS WorkerDays,
    COALESCE(h.days_logged, 0)               AS DaysLogged,
    COALESCE(i.incident_count, 0)            AS IncidentCount,
    COALESCE(i.recordable_count, 0)          AS RecordableIncidents,
    -- TRIR, the OSHA standard: recordables per 200,000 hours, which is 100 workers at
    -- 40h/week for a year. Computed here rather than in DAX so the constant lives with the
    -- data and a reader can see what it is.
    --
    -- NULL, not zero, when there are no hours. A rate over zero hours is undefined, and a
    -- zero would read as a perfect safety record on a project that simply logged nothing.
    CASE WHEN COALESCE(h.hours_worked, 0) > 0
         THEN (COALESCE(i.recordable_count, 0) * 200000.0) / h.hours_worked
    END                                      AS TRIR,
    -- No manpower log this month: an incident-only month, or a month inside the logging
    -- window in which nothing was filed. Visible rather than silently zeroed.
    (h.project_id IS NULL)                   AS HasNoManpowerLog,
    h.first_log                              AS FirstLogDate,
    h.last_log                               AS LastLogDate,
    CAST(COALESCE(m.weekdays_logged, CASE WHEN h.project_id IS NOT NULL THEN 0 END) AS INT)
                                             AS WeekdaysLogged,
    -- NULL outside the logging window (an incident-only month): "not measured", not 0 missed.
    CAST(COALESCE(m.days_missed, CASE WHEN h.project_id IS NOT NULL THEN 0 END) AS INT)
                                             AS DailyLogsMissed
FROM months k
LEFT JOIN hours h     ON h.project_id = k.project_id AND h.month_start = k.month_start
LEFT JOIN missed m    ON m.project_id = k.project_id AND m.month_start = k.month_start
LEFT JOIN incidents i ON i.project_id = k.project_id AND i.month_start = k.month_start;
