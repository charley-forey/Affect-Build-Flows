-- gold: the Weekly Dashboard score, worked out at build time for every project and week.
--
--   fct_MetricScore   one row per project x report week x Scorecard.xlsx measure: the reading
--                     (driver), whether it applies at the project's phase, the score and band
--   fct_ProjectScore  one row per project x report week: the four pillars, the share of the
--                     weight measured, the grade, how many measures are below target, and
--                     the weakest pillar
--
-- WHY IN GOLD. As DAX, every pill on the Portfolio table re-scored its pillar from twelve band
-- lookups, four weeks of meetings and the week's inspections; the service's query for that one
-- table ran out of F2 memory however the measures were arranged (2026-10-25). The rules are
-- the same ones - dim_DashBand, dim_DashPillar, dim_DashSetting, dim_DashMetric - applied once
-- a night to ~900 rows, and the report looks up the week it shows. validate_dashboard still
-- recomputes every score in Python from the raw facts and compares. Retuning a band or weight
-- is a CSV edit that the next nightly build applies.
--
-- THE WEEK. One row per dim_ReportWeek week. Meetings (rolling four weeks) and inspections
-- (the week) are read for that week; balances are as of the build. The look-ahead and the
-- schedule update are current state only - Outbuild keeps no history - so they are scored for
-- this week and last week and left unmeasured for earlier weeks.

CREATE OR REPLACE TABLE fct_MetricScore AS
WITH weeks AS (
    SELECT WeeksAgo, WeekEnd, AsOfDate, least(WeekEnd, AsOfDate) AS WindowEnd,
           date_add(WeekEnd, -6) AS WeekStart
    FROM dim_ReportWeek
),
settings AS (
    SELECT MAX(CASE WHEN SettingKey = 'gross_margin_target' THEN Value END) AS gm_target
    FROM dim_DashSetting
),
pos AS (
    SELECT p.*,
           CASE WHEN CashPaidOut > 0 THEN CashCollected / CashPaidOut
                WHEN CashCollected IS NOT NULL AND CashPaidOut IS NOT NULL AND CashCollected >= 0 THEN 1 END AS cash_ratio,
           -- No forecast cost means no projected margin, not a 100% one.
           CASE WHEN ProjectedRevenue > 0 AND ProjectedCost IS NOT NULL
                THEN (ProjectedRevenue - ProjectedCost) / ProjectedRevenue END AS gm,
           CASE WHEN ArOwedBalance > 0 THEN ArOwedBalanceDays / ArOwedBalance
                WHEN InvoiceCount > 0 THEN 0 END AS ar_age
    FROM fct_ProjectPosition p
),
pw AS (
    SELECT pos.*, w.WeeksAgo, w.WeekEnd, w.WeekStart, w.WindowEnd, w.AsOfDate
    FROM pos CROSS JOIN weeks w
),
-- Meetings: weeks of the four ending with the report week that held a compliant meeting.
meeting_weeks AS (
    SELECT pw.ProjectKey, pw.WeeksAgo, m.MeetingType, COUNT(DISTINCT k.k) AS held,
           MAX(CASE WHEN k.k = 0 THEN 1 ELSE 0 END) AS held_now
    FROM pw
    CROSS JOIN (VALUES (0), (1), (2), (3)) AS k(k)
    JOIN fct_Meeting m
      ON m.ProjectKey = pw.ProjectKey AND m.IsCompliant = TRUE
     AND m.MeetingDate >= date_add(pw.WeekEnd, -7 * k.k - 6) AND m.MeetingDate <= date_add(pw.WeekEnd, -7 * k.k)
    GROUP BY pw.ProjectKey, pw.WeeksAgo, m.MeetingType
),
inspections AS (
    SELECT pw.ProjectKey, pw.WeeksAgo, i.Category, COUNT(*) AS n
    FROM pw JOIN fct_Inspection i
      ON i.ProjectKey = pw.ProjectKey AND i.IsPerformed = TRUE
     AND i.InspectionDate >= pw.WeekStart AND i.InspectionDate <= pw.WindowEnd
    GROUP BY pw.ProjectKey, pw.WeeksAgo, i.Category
),
schedule AS (
    SELECT ProjectKey, MAX(UpdatedAt) AS last_edit FROM fct_ScheduleActivity GROUP BY ProjectKey
),
lookahead AS (
    SELECT ProjectKey, greatest(MAX(UpdatedAt), MAX(CreatedAt)) AS last_worked FROM fct_LookaheadTask GROUP BY ProjectKey
),
completion AS (
    SELECT m.ProjectKey,
           datediff(MAX(m.CurrentFinish), COALESCE(MAX(mm.BaselineFinish), MAX(m.BaselineFinish))) AS cv_days,
           CASE WHEN MAX(m.BaselineFinish) > MIN(m.BaselineStart)
                THEN datediff(MAX(m.BaselineFinish), MIN(m.BaselineStart)) END AS baseline_days
    FROM fct_Milestone m
    LEFT JOIN (SELECT ProjectKey, MAX(BaselineFinish) AS BaselineFinish FROM man_Milestones GROUP BY ProjectKey) mm
           ON mm.ProjectKey = m.ProjectKey
    GROUP BY m.ProjectKey
),
-- Daily logs (proposed, status 'Proposed' in dim_DashMetric, so read but not scored): weekdays
-- in the week, public holidays excepted, with no Procore daily log. This week stops at
-- yesterday - today's log may not be filed yet. Same weekday anchor as fct_SafetyMonthly.
daily AS (
    SELECT pw.ProjectKey, pw.WeeksAgo, SUM(CASE WHEN l.log_date IS NULL THEN 1 ELSE 0 END) AS missed
    FROM pw
    JOIN dim_Date d ON d.Date >= pw.WeekStart AND d.Date <= least(pw.WeekEnd, date_add(pw.AsOfDate, -1))
    LEFT JOIN seed_PublicHoliday ph ON ph.HolidayDate = d.Date
    LEFT JOIN (SELECT DISTINCT project_id, log_date FROM sv_manpower_daily WHERE project_id IS NOT NULL) l
           ON l.project_id = pw.ProjectKey AND l.log_date = d.Date
    WHERE datediff(d.Date, DATE '2014-12-29') % 7 < 5 AND ph.HolidayDate IS NULL
    GROUP BY pw.ProjectKey, pw.WeeksAgo
),
items AS (
    SELECT ProjectKey,
           SUM(CASE WHEN ItemType = 'Submittal' THEN 1 ELSE 0 END) AS submittals,
           SUM(CASE WHEN ItemType = 'Submittal' AND IsPastDue = TRUE THEN 1 ELSE 0 END) AS submittals_overdue,
           SUM(CASE WHEN ItemType = 'RFI' THEN 1 ELSE 0 END) AS rfis,
           SUM(CASE WHEN ItemType = 'RFI' AND IsOpen = TRUE
                     AND (IsPastDue = TRUE OR (DueDate IS NULL AND COALESCE(DaysOpen, 0) > 7)) THEN 1 ELSE 0 END) AS rfis_out
    FROM fct_RfiSubmittal GROUP BY ProjectKey
),
drivers AS (
    -- One driver per metric: the number its band scores (dashboard.py METRICS).
    SELECT pw.ProjectKey, pw.WeeksAgo, pw.Phase, m.MetricKey,
        CASE m.MetricKey
        WHEN 101 THEN pw.cash_ratio
        WHEN 102 THEN pw.gm - st.gm_target
        WHEN 103 THEN pw.ar_age
        -- This week is still running: it counts once a meeting is held, never as a miss.
        WHEN 201 THEN CAST(4 - COALESCE(oac.held, 0)
                           - CASE WHEN pw.WeeksAgo = 0 AND COALESCE(oac.held_now, 0) = 0 THEN 1 ELSE 0 END AS DOUBLE)
        WHEN 202 THEN CAST(4 - COALESCE(tp.held, 0)
                           - CASE WHEN pw.WeeksAgo = 0 AND COALESCE(tp.held_now, 0) = 0 THEN 1 ELSE 0 END AS DOUBLE)
        WHEN 203 THEN CASE WHEN s.ProjectKey IS NOT NULL AND pw.WeeksAgo <= 1
                           THEN CAST(COALESCE(datediff(pw.AsOfDate, CAST(l.last_worked AS DATE)), 999) AS DOUBLE) END
        WHEN 204 THEN CASE WHEN s.last_edit IS NOT NULL AND pw.WeeksAgo <= 1
                           THEN CAST(datediff(pw.AsOfDate, CAST(s.last_edit AS DATE)) AS DOUBLE) END
        WHEN 205 THEN CASE WHEN c.baseline_days > 0 THEN CAST(c.cv_days AS DOUBLE) / c.baseline_days END
        WHEN 206 THEN CASE WHEN it.submittals > 0 THEN CAST(it.submittals_overdue AS DOUBLE) END
        WHEN 207 THEN CASE WHEN it.rfis > 0 THEN CAST(it.rfis_out AS DOUBLE) END
        WHEN 208 THEN CAST(dl.missed AS DOUBLE)
        WHEN 301 THEN CAST(COALESCE(si.n, 0) AS DOUBLE)
        WHEN 401 THEN CAST(COALESCE(qi.n, 0) AS DOUBLE)
        END AS Driver
    FROM pw
    CROSS JOIN (VALUES (101), (102), (103), (201), (202), (203), (204), (205), (206), (207), (208), (301), (401)) AS m(MetricKey)
    CROSS JOIN settings st
    LEFT JOIN schedule s ON s.ProjectKey = pw.ProjectKey
    LEFT JOIN lookahead l ON l.ProjectKey = pw.ProjectKey
    LEFT JOIN completion c ON c.ProjectKey = pw.ProjectKey
    LEFT JOIN items it ON it.ProjectKey = pw.ProjectKey
    LEFT JOIN daily dl ON dl.ProjectKey = pw.ProjectKey AND dl.WeeksAgo = pw.WeeksAgo
    LEFT JOIN meeting_weeks oac ON oac.ProjectKey = pw.ProjectKey AND oac.WeeksAgo = pw.WeeksAgo AND oac.MeetingType = 'OAC'
    LEFT JOIN meeting_weeks tp ON tp.ProjectKey = pw.ProjectKey AND tp.WeeksAgo = pw.WeeksAgo AND tp.MeetingType = 'Trade Partner'
    LEFT JOIN inspections si ON si.ProjectKey = pw.ProjectKey AND si.WeeksAgo = pw.WeeksAgo AND si.Category = 'Safety'
    LEFT JOIN inspections qi ON qi.ProjectKey = pw.ProjectKey AND qi.WeeksAgo = pw.WeeksAgo AND qi.Category = 'Quality'
),
gated AS (
    SELECT d.*, dm.PillarKey,
           dm.Status = 'Live' AND (dm.Stages = 'All' OR (d.Phase IS NOT NULL AND dm.Stages LIKE CONCAT('%', d.Phase, '%')))
               AS Applies
    FROM drivers d JOIN dim_DashMetric dm ON dm.MetricKey = d.MetricKey
)
SELECT g.ProjectKey, g.WeeksAgo, g.MetricKey, g.PillarKey, g.Driver, g.Applies,
       CASE WHEN g.Applies AND g.Driver IS NOT NULL THEN
            CASE WHEN b.ScoreAtMin = b.ScoreAtMax OR b.MinValue IS NULL OR b.MaxValue IS NULL THEN b.ScoreAtMin
                 ELSE b.ScoreAtMin + (b.ScoreAtMax - b.ScoreAtMin) * (g.Driver - b.MinValue) / (b.MaxValue - b.MinValue) END
       END AS Score,
       CASE WHEN g.Applies AND g.Driver IS NOT NULL THEN b.BandLabel END AS BandLabel
FROM gated g
LEFT JOIN dim_DashBand b
       ON b.MetricKey = g.MetricKey
      AND (b.MinValue IS NULL OR g.Driver >= b.MinValue)
      AND (b.MaxValue IS NULL OR g.Driver < b.MaxValue);

-- The grade: pillars weighted by dim_DashPillar over the weight measured; under the coverage
-- minimum a project is unscored, not failing.
CREATE OR REPLACE TABLE fct_ProjectScore AS
WITH settings AS (
    SELECT MAX(CASE WHEN SettingKey = 'min_coverage' THEN Value END) AS min_coverage,
           MAX(CASE WHEN SettingKey = 'risk_metric_below' THEN Value END) AS risk_below
    FROM dim_DashSetting
),
pillars AS (
    SELECT s.ProjectKey, s.WeeksAgo, s.PillarKey, AVG(s.Score) AS PillarScore,
           SUM(CASE WHEN s.Score < st.risk_below THEN 1 ELSE 0 END) AS below
    FROM fct_MetricScore s CROSS JOIN settings st
    WHERE s.Score IS NOT NULL
    GROUP BY s.ProjectKey, s.WeeksAgo, s.PillarKey
),
frame AS (
    SELECT DISTINCT ProjectKey, WeeksAgo FROM fct_MetricScore
),
rolled AS (
    SELECT f.ProjectKey, f.WeeksAgo,
           MAX(CASE WHEN p.PillarKey = 1 THEN p.PillarScore END) AS SchedulePillar,
           MAX(CASE WHEN p.PillarKey = 2 THEN p.PillarScore END) AS BudgetPillar,
           MAX(CASE WHEN p.PillarKey = 3 THEN p.PillarScore END) AS SafetyPillar,
           MAX(CASE WHEN p.PillarKey = 4 THEN p.PillarScore END) AS QualityPillar,
           SUM(CASE WHEN p.PillarScore IS NOT NULL THEN w.Weight ELSE 0 END) AS measured_weight,
           SUM(CASE WHEN p.PillarScore IS NOT NULL THEN w.Weight * p.PillarScore ELSE 0 END) AS weighted,
           SUM(COALESCE(p.below, 0)) AS below
    FROM frame f
    LEFT JOIN pillars p ON p.ProjectKey = f.ProjectKey AND p.WeeksAgo = f.WeeksAgo
    LEFT JOIN dim_DashPillar w ON w.PillarKey = p.PillarKey
    GROUP BY f.ProjectKey, f.WeeksAgo
),
total AS (
    SELECT SUM(Weight) AS total_weight FROM dim_DashPillar WHERE PillarKey IN (1, 2, 3, 4)
),
weakest AS (
    -- The pillar costing the grade most: weight x points short of 100%. The lowest SCORE
    -- would name a 0% quality pillar (5 points lost) over a 40% schedule pillar (30 lost).
    SELECT ProjectKey, WeeksAgo, PillarKey FROM (
        SELECT p.ProjectKey, p.WeeksAgo, p.PillarKey,
               ROW_NUMBER() OVER (PARTITION BY p.ProjectKey, p.WeeksAgo
                                  ORDER BY w.Weight * (1 - p.PillarScore) DESC, p.PillarKey) AS rn
        FROM pillars p JOIN dim_DashPillar w ON w.PillarKey = p.PillarKey
        WHERE p.PillarKey IN (1, 2, 3, 4) AND p.PillarScore < 1) x WHERE rn = 1
)
SELECT r.ProjectKey, r.WeeksAgo, r.SchedulePillar, r.BudgetPillar, r.SafetyPillar, r.QualityPillar,
       -- ROUND: 0.30 + 0.15 + 0.05 is 0.49999999999999994 in floating point.
       CASE WHEN r.measured_weight > 0 THEN ROUND(r.measured_weight / t.total_weight, 6) END AS GradeCoverage,
       CASE WHEN r.measured_weight > 0 AND ROUND(r.measured_weight / t.total_weight, 6) >= st.min_coverage
            THEN 100 * r.weighted / r.measured_weight END AS Grade,
       CASE WHEN r.measured_weight > 0 AND ROUND(r.measured_weight / t.total_weight, 6) >= st.min_coverage
            THEN CAST(r.below AS INT) END AS MeasuresBelowTarget,
       dp.Pillar AS WeakestPillar
FROM rolled r
CROSS JOIN total t
CROSS JOIN settings st
LEFT JOIN weakest wk ON wk.ProjectKey = r.ProjectKey AND wk.WeeksAgo = r.WeeksAgo
LEFT JOIN dim_DashPillar dp ON dp.PillarKey = wk.PillarKey;
