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
-- FULL OUTER JOIN, deliberately. A month can have hours and no incidents (the good case,
-- and the common one), or an incident recorded against a month with no logged hours (a
-- real data-entry state worth seeing). An inner join would silently drop both.

CREATE OR REPLACE TABLE fct_SafetyMonthly AS
WITH hours AS (
    SELECT
        project_id,
        make_date(year(log_date), month(log_date), 1) AS month_start,
        SUM(total_hours)   AS hours_worked,
        SUM(total_workers) AS worker_days,
        COUNT(*)           AS days_logged
    FROM sv_manpower_daily
    WHERE project_id IS NOT NULL
      AND log_date IS NOT NULL
      -- Outside dim_Date the month cannot join, and every measure over it returns BLANK -
      -- which on a card is indistinguishable from zero hours worked.
      AND log_date BETWEEN DATE '2015-01-01' AND DATE '2035-12-31'
    GROUP BY project_id, make_date(year(log_date), month(log_date), 1)
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
)
SELECT
    COALESCE(h.project_id, i.project_id)     AS ProjectKey,
    COALESCE(h.month_start, i.month_start)   AS MonthStart,
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
    -- Hours with no logged days means the join produced a month from the incident side
    -- only. Visible rather than silently zeroed.
    (h.project_id IS NULL)                   AS HasNoManpowerLog
FROM hours h
FULL OUTER JOIN incidents i
  ON i.project_id = h.project_id AND i.month_start = h.month_start;
