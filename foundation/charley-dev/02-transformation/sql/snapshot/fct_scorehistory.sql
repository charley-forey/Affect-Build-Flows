-- snapshot: fct_ScoreHistory - each project's Weekly Dashboard grade for the last complete
-- week, saved per passing run, so "vs prior week" compares grades as they were shown.
--
-- WHY. fct_ProjectScore rescores 53 weeks every night from today's facts: a late inspection
-- or minutes upload rewrites an old week, and the Outbuild look-ahead and schedule update are
-- only measured for the latest two weeks (Outbuild keeps no history), so an older week is
-- graded on fewer measures. Week-on-week change from that table is partly an artefact.
--
-- WHO RUNS IT. cd_40_dq_checks, in its own cell after the daily snapshot - so only after the
-- gate passed. A failure is recorded and alerted; it never blocks publishing.
--
-- Grain: one row per project per saved week (WeekStart, ProjectKey).
--
-- ONE ROW-SET PER WEEK. Every night replaces the rows of last week ({WEEK_START}, the Monday
-- of dim_ReportWeek WeeksAgo = 1). The value kept is the last one captured before the week
-- rolled over: what the dashboard showed as "Last week" on its final day.

CREATE TABLE IF NOT EXISTS fct_ScoreHistory (
    WeekStart            DATE,
    ProjectKey           STRING,
    SchedulePillar       DOUBLE,
    BudgetPillar         DOUBLE,
    SafetyPillar         DOUBLE,
    QualityPillar        DOUBLE,
    GradeCoverage        DOUBLE,
    Grade                DOUBLE,
    MeasuresBelowTarget  INT,
    WeakestPillar        STRING,
    RunId                STRING,
    CapturedAt           TIMESTAMP
) USING DELTA;

CREATE OR REPLACE TEMP VIEW v_ScoreHistoryStage AS
SELECT DATE '{WEEK_START}' AS WeekStart, ProjectKey,
       CAST(SchedulePillar AS DOUBLE) AS SchedulePillar, CAST(BudgetPillar AS DOUBLE) AS BudgetPillar,
       CAST(SafetyPillar AS DOUBLE) AS SafetyPillar, CAST(QualityPillar AS DOUBLE) AS QualityPillar,
       CAST(GradeCoverage AS DOUBLE) AS GradeCoverage, CAST(Grade AS DOUBLE) AS Grade,
       CAST(MeasuresBelowTarget AS INT) AS MeasuresBelowTarget, WeakestPillar,
       '{RUN_ID}' AS RunId, CAST(CURRENT_TIMESTAMP AS TIMESTAMP) AS CapturedAt
FROM fct_ProjectScore
WHERE WeeksAgo = 1;

-- deploy_dq.score_history_phases splits the file on the next line.
-- ==== SWAP ====

-- One Delta transaction, as fct_DailySnapshot: the week's earlier capture is replaced, and
-- a project gone from this run's rows is removed from that week only.
MERGE INTO fct_ScoreHistory AS target
USING v_ScoreHistoryStage AS source
ON target.WeekStart = source.WeekStart AND target.ProjectKey IS NOT DISTINCT FROM source.ProjectKey
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
WHEN NOT MATCHED BY SOURCE AND target.WeekStart = DATE '{WEEK_START}' THEN DELETE;
