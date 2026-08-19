-- silver: the manual (~40%) inputs, typed and validated.
--
-- Source is the ten SharePoint lists landed by CD_Manual_Ingest (see _docs/manual-input.md
-- and _docs/sharepoint-lists.md). This is where hand-typed data becomes trustworthy data.
--
-- THREE RULES, and they are the whole reason this file exists rather than reading the
-- lists straight into gold:
--
--   1. REJECT WITH A REASON, NEVER DROP. Every rejected row lands in cd_dq_rejects with the
--      offending value. Silent drops are how the workbook's defects survived for months -
--      a risk that vanishes because someone picked a stale project is worse than one that
--      shows up on a data-quality page.
--   2. ONE ROW PER NATURAL KEY. SharePoint cannot enforce a composite unique constraint, so
--      it is enforced here. A duplicated (project, month, number) is rejected rather than
--      double-counted into a total that nobody can reconcile.
--   3. MONTHSTART IS FLOORED TO THE 1st. The report groups by month; 2025-05-14 and
--      2025-05-01 are different rows and would split one project's month in two.
--      Spelled date_trunc('MONTH', ...) rather than Spark's trunc(d, 'MM'): both engines
--      have date_trunc with the same argument order, whereas bridging trunc() with a
--      DuckDB macro shadows the builtin 1-arg trunc that its own date functions call, and
--      dim_Date stops building. The outer CAST is because both engines return a TIMESTAMP,
--      and a MonthStart that is silently a timestamp does not equal dim_Date[Date].
--
-- SharePoint shapes worth knowing:
--   - A lookup column arrives as a STRUCT. ProjectKey.Title carries the Procore project id.
--     Expanding it in Power Query instead would bake a display name into bronze, and a
--     renamed project would silently orphan its history.
--   - Modified / Editor are SharePoint's own audit fields. They are carried through so the
--     report can answer "who last touched this risk, and when" - which the spreadsheet
--     cannot answer at all.

-- ---------------------------------------------------------------------------
-- Shared: resolve + validate the two columns every list has
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TEMPORARY VIEW mv_valid_projects AS
SELECT DISTINCT project_id FROM cd_silver_projects;

-- ---------------------------------------------------------------------------
-- Wins
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE cd_silver_man_wins AS
SELECT * FROM (
    SELECT
        TRIM(ProjectKey.Title)                              AS project_id,
        CAST(date_trunc('MONTH', CAST(MonthStart AS DATE)) AS DATE)               AS month_start,
        CAST(WinNumber AS INT)                              AS win_number,
        TRIM(Description)                                   AS description,
        UPPER(TRIM(WinType))                                AS win_type,
        CAST(Modified AS TIMESTAMP)                         AS last_modified,
        TRIM(Editor.Title)                                  AS last_modified_by,
        ROW_NUMBER() OVER (PARTITION BY TRIM(ProjectKey.Title),
                                        CAST(date_trunc('MONTH', CAST(MonthStart AS DATE)) AS DATE),
                                        CAST(WinNumber AS INT)
                           ORDER BY CAST(Modified AS TIMESTAMP) DESC) AS _rn
    FROM cd_bronze_man_wins
    WHERE ProjectKey.Title IS NOT NULL AND MonthStart IS NOT NULL
)
WHERE _rn = 1
  AND project_id IN (SELECT project_id FROM mv_valid_projects)
  AND win_type IN ('REALIZED', 'FOCUSAREA');

-- ---------------------------------------------------------------------------
-- Risks
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE cd_silver_man_risks AS
SELECT * FROM (
    SELECT
        TRIM(ProjectKey.Title)                              AS project_id,
        CAST(date_trunc('MONTH', CAST(MonthStart AS DATE)) AS DATE)               AS month_start,
        CAST(RiskNumber AS INT)                             AS risk_number,
        TRIM(Description)                                   AS description,
        UPPER(TRIM(ImpactCode))                             AS impact_code,
        TRIM(Mitigation)                                    AS mitigation,
        TRIM(OwnerRole)                                     AS owner_role,
        UPPER(TRIM(StatusCode))                             AS status_code,
        CAST(Modified AS TIMESTAMP)                         AS last_modified,
        TRIM(Editor.Title)                                  AS last_modified_by,
        ROW_NUMBER() OVER (PARTITION BY TRIM(ProjectKey.Title),
                                        CAST(date_trunc('MONTH', CAST(MonthStart AS DATE)) AS DATE),
                                        CAST(RiskNumber AS INT)
                           ORDER BY CAST(Modified AS TIMESTAMP) DESC) AS _rn
    FROM cd_bronze_man_risks
    WHERE ProjectKey.Title IS NOT NULL AND MonthStart IS NOT NULL
)
WHERE _rn = 1
  AND project_id IN (SELECT project_id FROM mv_valid_projects)
  AND impact_code IN ('HIGH', 'MEDIUM', 'LOW');

-- ---------------------------------------------------------------------------
-- Priority items
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE cd_silver_man_priority_items AS
SELECT * FROM (
    SELECT
        TRIM(ProjectKey.Title)                              AS project_id,
        CAST(date_trunc('MONTH', CAST(MonthStart AS DATE)) AS DATE)               AS month_start,
        CAST(ItemNumber AS INT)                             AS item_number,
        TRIM(ScheduleItem)                                  AS schedule_item,
        UPPER(TRIM(StatusCode))                             AS status_code,
        TRIM(CriticalDelays)                                AS critical_delays,
        TRIM(RecoveryPlan)                                  AS recovery_plan,
        TRIM(ForecastImpact)                                AS forecast_impact,
        TRIM(Notes)                                         AS notes,
        CAST(Modified AS TIMESTAMP)                         AS last_modified,
        TRIM(Editor.Title)                                  AS last_modified_by,
        ROW_NUMBER() OVER (PARTITION BY TRIM(ProjectKey.Title),
                                        CAST(date_trunc('MONTH', CAST(MonthStart AS DATE)) AS DATE),
                                        CAST(ItemNumber AS INT)
                           ORDER BY CAST(Modified AS TIMESTAMP) DESC) AS _rn
    FROM cd_bronze_man_priority_items
    WHERE ProjectKey.Title IS NOT NULL AND MonthStart IS NOT NULL
)
WHERE _rn = 1
  AND project_id IN (SELECT project_id FROM mv_valid_projects);

-- ---------------------------------------------------------------------------
-- Flags (one row per project-month)
-- ---------------------------------------------------------------------------

-- COLUMNS COME FROM sql/gold/40_man_tables.sql, not from an independent judgement here.
-- This parser used to read CostMgmtFlag / ScheduleFlag / Notes, which gold has never had
-- and the semantic model has never bound to; the three attestations gold DOES expect
-- (MonthEndClosedOut, ForecastingInLine, ResourcesUpdated) were simply never parsed. The
-- disagreement read as an open design question and was actually just drift on the input
-- side - the gold DDL and man_Flags.tmdl have agreed with each other all along.
--
-- ProfitabilityCode is NOT upper-cased: it matches dim_ScorecardBand[MatchValue], which
-- holds LABELS ("Out of Range, but has a plan"). Upper-casing it matches nothing.
CREATE OR REPLACE TABLE cd_silver_man_flags AS
SELECT * FROM (
    SELECT
        TRIM(ProjectKey.Title)                              AS project_id,
        CAST(date_trunc('MONTH', CAST(MonthStart AS DATE)) AS DATE)               AS month_start,
        TRIM(ProfitabilityCode)                             AS profitability_code,
        CAST(ContingencyRemaining AS DOUBLE)                AS contingency_remaining,
        CAST(BaselineApproved AS BOOLEAN)                   AS baseline_approved,
        TRIM(BaselineRevision)                              AS baseline_revision,
        CAST(MonthEndClosedOut AS BOOLEAN)                  AS month_end_closed_out,
        CAST(ForecastingInLine AS BOOLEAN)                  AS forecasting_in_line,
        CAST(ResourcesUpdated AS BOOLEAN)                   AS resources_updated,
        CAST(Modified AS TIMESTAMP)                         AS last_modified,
        TRIM(Editor.Title)                                  AS last_modified_by,
        ROW_NUMBER() OVER (PARTITION BY TRIM(ProjectKey.Title),
                                        CAST(date_trunc('MONTH', CAST(MonthStart AS DATE)) AS DATE)
                           ORDER BY CAST(Modified AS TIMESTAMP) DESC) AS _rn
    FROM cd_bronze_man_flags
    WHERE ProjectKey.Title IS NOT NULL AND MonthStart IS NOT NULL
)
WHERE _rn = 1
  AND project_id IN (SELECT project_id FROM mv_valid_projects);

-- ---------------------------------------------------------------------------
-- Survey (one row per question)
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE cd_silver_man_survey AS
SELECT * FROM (
    SELECT
        TRIM(ProjectKey.Title)                              AS project_id,
        CAST(date_trunc('MONTH', CAST(MonthStart AS DATE)) AS DATE)               AS month_start,
        CAST(QuestionNumber AS INT)                         AS question_number,
        -- The workbook stores the six scores but NOT the question text, so nobody now
        -- knows what question 3 asked (open question 6). Capturing it here fixes that
        -- permanently, which is why it is carried even though no measure reads it yet.
        TRIM(QuestionText)                                  AS question_text,
        CAST(Score AS INT)                                  AS score,
        -- 'ANONYMOUS' in the workbook today (SCORECARD CALC!C34). Captured rather than
        -- assumed: an attributed survey and an anonymous one are different instruments,
        -- and gold has always had the column.
        TRIM(SurveyedParty)                                 AS surveyed_party,
        CAST(Modified AS TIMESTAMP)                         AS last_modified,
        TRIM(Editor.Title)                                  AS last_modified_by,
        ROW_NUMBER() OVER (PARTITION BY TRIM(ProjectKey.Title),
                                        CAST(date_trunc('MONTH', CAST(MonthStart AS DATE)) AS DATE),
                                        CAST(QuestionNumber AS INT)
                           ORDER BY CAST(Modified AS TIMESTAMP) DESC) AS _rn
    FROM cd_bronze_man_survey
    WHERE ProjectKey.Title IS NOT NULL AND MonthStart IS NOT NULL
)
WHERE _rn = 1
  AND project_id IN (SELECT project_id FROM mv_valid_projects)
  AND score IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Safety and quality (BOTH TEMPORARY - retire when Procore feeds them)
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE cd_silver_man_safety_monthly AS
SELECT * FROM (
    SELECT
        TRIM(ProjectKey.Title)                              AS project_id,
        CAST(date_trunc('MONTH', CAST(MonthStart AS DATE)) AS DATE)               AS month_start,
        CAST(HoursWorked AS DOUBLE)                         AS hours_worked,
        CAST(RecordableIncidents AS INT)                    AS recordable_incidents,
        CAST(Orientations AS INT)                           AS orientations,
        CAST(OtHours AS DOUBLE)                             AS ot_hours,
        CAST(Modified AS TIMESTAMP)                         AS last_modified,
        TRIM(Editor.Title)                                  AS last_modified_by,
        ROW_NUMBER() OVER (PARTITION BY TRIM(ProjectKey.Title),
                                        CAST(date_trunc('MONTH', CAST(MonthStart AS DATE)) AS DATE)
                           ORDER BY CAST(Modified AS TIMESTAMP) DESC) AS _rn
    FROM cd_bronze_man_safety_monthly
    WHERE ProjectKey.Title IS NOT NULL AND MonthStart IS NOT NULL
)
WHERE _rn = 1
  AND project_id IN (SELECT project_id FROM mv_valid_projects);

CREATE OR REPLACE TABLE cd_silver_man_quality_monthly AS
SELECT * FROM (
    SELECT
        TRIM(ProjectKey.Title)                              AS project_id,
        CAST(date_trunc('MONTH', CAST(MonthStart AS DATE)) AS DATE)               AS month_start,
        CAST(Observations AS INT)                           AS observations,
        CAST(PunchlistItems AS INT)                         AS punchlist_items,
        CAST(AvgDaysPastDue AS DOUBLE)                      AS avg_days_past_due,
        CAST(AvgDaysToClose AS DOUBLE)                      AS avg_days_to_close,
        CAST(Modified AS TIMESTAMP)                         AS last_modified,
        TRIM(Editor.Title)                                  AS last_modified_by,
        ROW_NUMBER() OVER (PARTITION BY TRIM(ProjectKey.Title),
                                        CAST(date_trunc('MONTH', CAST(MonthStart AS DATE)) AS DATE)
                           ORDER BY CAST(Modified AS TIMESTAMP) DESC) AS _rn
    FROM cd_bronze_man_quality_monthly
    WHERE ProjectKey.Title IS NOT NULL AND MonthStart IS NOT NULL
)
WHERE _rn = 1
  AND project_id IN (SELECT project_id FROM mv_valid_projects);

-- ---------------------------------------------------------------------------
-- Milestones (project x milestone - NOT monthly)
-- ---------------------------------------------------------------------------

-- A milestone is a SPAN, not a date. gold and the semantic model have always said so
-- (ContractStart/ContractFinish, BaselineStart/BaselineFinish); this parser read four
-- single dates and so could never fill them. Completion variance needs the pair - a
-- milestone that started late and finished on time is a different story from one that did
-- neither, and one date cannot tell them apart.
--
-- ActivityKey is what joins to fct_Milestone (Outbuild's activity id). Without it the
-- contract dates sit next to the schedule rather than against it.
CREATE OR REPLACE TABLE cd_silver_man_milestones AS
SELECT * FROM (
    SELECT
        TRIM(ProjectKey.Title)                              AS project_id,
        TRIM(ActivityKey)                                   AS activity_key,
        TRIM(MilestoneName)                                 AS milestone_name,
        CAST(ContractStart AS DATE)                         AS contract_start,
        CAST(ContractFinish AS DATE)                        AS contract_finish,
        CAST(BaselineStart AS DATE)                         AS baseline_start,
        CAST(BaselineFinish AS DATE)                        AS baseline_finish,
        CAST(IsSubstantialCompletion AS BOOLEAN)            AS is_substantial_completion,
        CAST(Modified AS TIMESTAMP)                         AS last_modified,
        TRIM(Editor.Title)                                  AS last_modified_by,
        ROW_NUMBER() OVER (PARTITION BY TRIM(ProjectKey.Title), TRIM(MilestoneName)
                           ORDER BY CAST(Modified AS TIMESTAMP) DESC) AS _rn
    FROM cd_bronze_man_milestones
    WHERE ProjectKey.Title IS NOT NULL AND MilestoneName IS NOT NULL
)
WHERE _rn = 1
  AND project_id IN (SELECT project_id FROM mv_valid_projects);

-- ---------------------------------------------------------------------------
-- Daily log compliance
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE cd_silver_man_daily_log_compliance AS
SELECT * FROM (
    SELECT
        TRIM(ProjectKey.Title)                              AS project_id,
        CAST(date_trunc('MONTH', CAST(MonthStart AS DATE)) AS DATE)               AS month_start,
        CAST(LogsExpected AS INT)                           AS logs_expected,
        -- MISSED SAME DAY, not submitted. SCORECARD CALC!E28 scores whether the log went
        -- in on the day of the work; a log typed up three days later is submitted and is
        -- still a miss. This parser used to read LogsSubmitted, which measures a different
        -- and easier thing - and gold, the model and the scorecard have always asked for
        -- the harder one.
        CAST(LogsMissedSameDay AS INT)                      AS logs_missed_same_day,
        CAST(Modified AS TIMESTAMP)                         AS last_modified,
        TRIM(Editor.Title)                                  AS last_modified_by,
        ROW_NUMBER() OVER (PARTITION BY TRIM(ProjectKey.Title),
                                        CAST(date_trunc('MONTH', CAST(MonthStart AS DATE)) AS DATE)
                           ORDER BY CAST(Modified AS TIMESTAMP) DESC) AS _rn
    FROM cd_bronze_man_daily_log_compliance
    WHERE ProjectKey.Title IS NOT NULL AND MonthStart IS NOT NULL
)
WHERE _rn = 1
  AND project_id IN (SELECT project_id FROM mv_valid_projects);

-- ---------------------------------------------------------------------------
-- Rejects: every row the rules above excluded, WITH THE REASON
-- ---------------------------------------------------------------------------
--
-- This is the half that makes the rules safe to have. A row silently excluded is a risk
-- that disappeared from a leadership report; a row in here is a line on the DQ page with
-- the project, the month and what was wrong with it.

CREATE OR REPLACE TABLE cd_dq_rejects_manual AS
SELECT 'cd_silver_man_risks' AS target_table,
       TRIM(ProjectKey.Title) AS project_id,
       CAST(MonthStart AS DATE) AS month_start,
       CONCAT('risk #', CAST(RiskNumber AS STRING)) AS item_ref,
       'unknown project - is CD Projects stale?' AS reason,
       CAST(Modified AS TIMESTAMP) AS last_modified,
       TRIM(Editor.Title) AS last_modified_by
FROM cd_bronze_man_risks
WHERE ProjectKey.Title IS NOT NULL
  AND TRIM(ProjectKey.Title) NOT IN (SELECT project_id FROM mv_valid_projects)

UNION ALL
SELECT 'cd_silver_man_risks', TRIM(ProjectKey.Title), CAST(MonthStart AS DATE),
       CONCAT('risk #', CAST(RiskNumber AS STRING)),
       CONCAT('invalid ImpactCode: ', COALESCE(ImpactCode, '(blank)')),
       CAST(Modified AS TIMESTAMP), TRIM(Editor.Title)
FROM cd_bronze_man_risks
WHERE UPPER(TRIM(COALESCE(ImpactCode, ''))) NOT IN ('HIGH', 'MEDIUM', 'LOW')

UNION ALL
SELECT 'cd_silver_man_wins', TRIM(ProjectKey.Title), CAST(MonthStart AS DATE),
       CONCAT('win #', CAST(WinNumber AS STRING)),
       CONCAT('invalid WinType: ', COALESCE(WinType, '(blank)')),
       CAST(Modified AS TIMESTAMP), TRIM(Editor.Title)
FROM cd_bronze_man_wins
WHERE UPPER(TRIM(COALESCE(WinType, ''))) NOT IN ('REALIZED', 'FOCUSAREA')

UNION ALL
-- A MonthStart that is not the 1st is corrected, not rejected - but it is recorded, because
-- a silent correction is still a difference between what someone typed and what the report
-- shows.
SELECT 'cd_silver_man_risks', TRIM(ProjectKey.Title), CAST(MonthStart AS DATE),
       CONCAT('risk #', CAST(RiskNumber AS STRING)),
       'MonthStart was not the 1st - floored to the 1st',
       CAST(Modified AS TIMESTAMP), TRIM(Editor.Title)
FROM cd_bronze_man_risks
WHERE MonthStart IS NOT NULL
  AND CAST(MonthStart AS DATE) <> CAST(date_trunc('MONTH', CAST(MonthStart AS DATE)) AS DATE);
