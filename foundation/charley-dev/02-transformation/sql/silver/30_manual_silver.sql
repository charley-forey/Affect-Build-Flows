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
--      double-counted into a total that nobody can reconcile. EXACT duplicates (same
--      business values, e.g. one CSV landed twice) collapse to one row; CONFLICTING
--      versions of one key are ALL rejected, never resolved by picking the latest - the
--      latest edit is not evidence of the right value.
--
-- THE SHAPE, per list: a staging view (mv_<list>) types every bronze row and gives it at
-- most one _reject_reason, _versions (distinct business versions of its natural key) and
-- _copy (exact-duplicate ordinal). The silver table is the rows with no reason, one
-- version and _copy = 1; cd_dq_rejects_manual is the rows with a reason or >1 version.
-- So bronze rows = silver rows + rejected rows + collapsed exact copies, by construction.
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

CREATE OR REPLACE TEMPORARY VIEW mv_wins AS
SELECT *,
       MAX(_version) OVER (PARTITION BY _reject_reason, project_id, month_start, win_number) AS _versions,
       ROW_NUMBER() OVER (PARTITION BY _reject_reason, project_id, month_start, win_number, _version
                          ORDER BY last_modified DESC) AS _copy
FROM (
    SELECT *,
           DENSE_RANK() OVER (PARTITION BY _reject_reason, project_id, month_start, win_number
                              ORDER BY description, win_type) AS _version
    FROM (
        SELECT
            TRIM(b.ProjectKey.Title)                             AS project_id,
            CAST(date_trunc('MONTH', CAST(b.MonthStart AS DATE)) AS DATE) AS month_start,
            CAST(b.WinNumber AS INT)                             AS win_number,
            TRIM(b.Description)                                  AS description,
            UPPER(TRIM(b.WinType))                               AS win_type,
            CAST(b.Modified AS TIMESTAMP)                        AS last_modified,
            TRIM(b.Editor.Title)                                 AS last_modified_by,
            CASE
                WHEN b.ProjectKey.Title IS NULL OR b.MonthStart IS NULL
                     THEN 'missing ProjectKey or MonthStart'
                WHEN v.project_id IS NULL
                     THEN 'unknown project - is CD Projects stale?'
                WHEN UPPER(TRIM(COALESCE(b.WinType, ''))) NOT IN ('REALIZED', 'FOCUSAREA')
                     THEN CONCAT('invalid WinType: ', COALESCE(b.WinType, '(blank)'))
            END AS _reject_reason
        FROM cd_bronze_man_wins b
        LEFT JOIN mv_valid_projects v ON v.project_id = TRIM(b.ProjectKey.Title)
    )
);

CREATE OR REPLACE TABLE cd_silver_man_wins AS
SELECT project_id, month_start, win_number, description, win_type,
       last_modified, last_modified_by
FROM mv_wins
WHERE _reject_reason IS NULL AND _versions = 1 AND _copy = 1;

-- ---------------------------------------------------------------------------
-- Risks
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TEMPORARY VIEW mv_risks AS
SELECT *,
       MAX(_version) OVER (PARTITION BY _reject_reason, project_id, month_start, risk_number) AS _versions,
       ROW_NUMBER() OVER (PARTITION BY _reject_reason, project_id, month_start, risk_number, _version
                          ORDER BY last_modified DESC) AS _copy
FROM (
    SELECT *,
           DENSE_RANK() OVER (PARTITION BY _reject_reason, project_id, month_start, risk_number
                              ORDER BY description, impact_code, mitigation, owner_role, status_code) AS _version
    FROM (
        SELECT
            TRIM(b.ProjectKey.Title)                             AS project_id,
            CAST(date_trunc('MONTH', CAST(b.MonthStart AS DATE)) AS DATE) AS month_start,
            CAST(b.RiskNumber AS INT)                            AS risk_number,
            TRIM(b.Description)                                  AS description,
            UPPER(TRIM(b.ImpactCode))                            AS impact_code,
            TRIM(b.Mitigation)                                   AS mitigation,
            TRIM(b.OwnerRole)                                    AS owner_role,
            UPPER(TRIM(b.StatusCode))                            AS status_code,
            CAST(b.Modified AS TIMESTAMP)                        AS last_modified,
            TRIM(b.Editor.Title)                                 AS last_modified_by,
            CASE
                WHEN b.ProjectKey.Title IS NULL OR b.MonthStart IS NULL
                     THEN 'missing ProjectKey or MonthStart'
                WHEN v.project_id IS NULL
                     THEN 'unknown project - is CD Projects stale?'
                WHEN UPPER(TRIM(COALESCE(b.ImpactCode, ''))) NOT IN ('HIGH', 'MEDIUM', 'LOW')
                     THEN CONCAT('invalid ImpactCode: ', COALESCE(b.ImpactCode, '(blank)'))
            END AS _reject_reason
        FROM cd_bronze_man_risks b
        LEFT JOIN mv_valid_projects v ON v.project_id = TRIM(b.ProjectKey.Title)
    )
);

CREATE OR REPLACE TABLE cd_silver_man_risks AS
SELECT project_id, month_start, risk_number, description, impact_code, mitigation, owner_role, status_code,
       last_modified, last_modified_by
FROM mv_risks
WHERE _reject_reason IS NULL AND _versions = 1 AND _copy = 1;

-- ---------------------------------------------------------------------------
-- Priority items
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TEMPORARY VIEW mv_priority_items AS
SELECT *,
       MAX(_version) OVER (PARTITION BY _reject_reason, project_id, month_start, item_number) AS _versions,
       ROW_NUMBER() OVER (PARTITION BY _reject_reason, project_id, month_start, item_number, _version
                          ORDER BY last_modified DESC) AS _copy
FROM (
    SELECT *,
           DENSE_RANK() OVER (PARTITION BY _reject_reason, project_id, month_start, item_number
                              ORDER BY schedule_item, status_code, critical_delays, recovery_plan, forecast_impact, notes) AS _version
    FROM (
        SELECT
            TRIM(b.ProjectKey.Title)                             AS project_id,
            CAST(date_trunc('MONTH', CAST(b.MonthStart AS DATE)) AS DATE) AS month_start,
            CAST(b.ItemNumber AS INT)                            AS item_number,
            TRIM(b.ScheduleItem)                                 AS schedule_item,
            UPPER(TRIM(b.StatusCode))                            AS status_code,
            TRIM(b.CriticalDelays)                               AS critical_delays,
            TRIM(b.RecoveryPlan)                                 AS recovery_plan,
            TRIM(b.ForecastImpact)                               AS forecast_impact,
            TRIM(b.Notes)                                        AS notes,
            CAST(b.Modified AS TIMESTAMP)                        AS last_modified,
            TRIM(b.Editor.Title)                                 AS last_modified_by,
            CASE
                WHEN b.ProjectKey.Title IS NULL OR b.MonthStart IS NULL
                     THEN 'missing ProjectKey or MonthStart'
                WHEN v.project_id IS NULL
                     THEN 'unknown project - is CD Projects stale?'
            END AS _reject_reason
        FROM cd_bronze_man_priority_items b
        LEFT JOIN mv_valid_projects v ON v.project_id = TRIM(b.ProjectKey.Title)
    )
);

CREATE OR REPLACE TABLE cd_silver_man_priority_items AS
SELECT project_id, month_start, item_number, schedule_item, status_code, critical_delays, recovery_plan, forecast_impact, notes,
       last_modified, last_modified_by
FROM mv_priority_items
WHERE _reject_reason IS NULL AND _versions = 1 AND _copy = 1;

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

CREATE OR REPLACE TEMPORARY VIEW mv_flags AS
SELECT *,
       MAX(_version) OVER (PARTITION BY _reject_reason, project_id, month_start) AS _versions,
       ROW_NUMBER() OVER (PARTITION BY _reject_reason, project_id, month_start, _version
                          ORDER BY last_modified DESC) AS _copy
FROM (
    SELECT *,
           DENSE_RANK() OVER (PARTITION BY _reject_reason, project_id, month_start
                              ORDER BY profitability_code, contingency_remaining, baseline_approved, baseline_revision, month_end_closed_out, forecasting_in_line, resources_updated) AS _version
    FROM (
        SELECT
            TRIM(b.ProjectKey.Title)                             AS project_id,
            CAST(date_trunc('MONTH', CAST(b.MonthStart AS DATE)) AS DATE) AS month_start,
            TRIM(b.ProfitabilityCode)                            AS profitability_code,
            CAST(b.ContingencyRemaining AS DOUBLE)               AS contingency_remaining,
            CAST(b.BaselineApproved AS BOOLEAN)                  AS baseline_approved,
            TRIM(b.BaselineRevision)                             AS baseline_revision,
            CAST(b.MonthEndClosedOut AS BOOLEAN)                 AS month_end_closed_out,
            CAST(b.ForecastingInLine AS BOOLEAN)                 AS forecasting_in_line,
            CAST(b.ResourcesUpdated AS BOOLEAN)                  AS resources_updated,
            CAST(b.Modified AS TIMESTAMP)                        AS last_modified,
            TRIM(b.Editor.Title)                                 AS last_modified_by,
            CASE
                WHEN b.ProjectKey.Title IS NULL OR b.MonthStart IS NULL
                     THEN 'missing ProjectKey or MonthStart'
                WHEN v.project_id IS NULL
                     THEN 'unknown project - is CD Projects stale?'
            END AS _reject_reason
        FROM cd_bronze_man_flags b
        LEFT JOIN mv_valid_projects v ON v.project_id = TRIM(b.ProjectKey.Title)
    )
);

CREATE OR REPLACE TABLE cd_silver_man_flags AS
SELECT project_id, month_start, profitability_code, contingency_remaining, baseline_approved, baseline_revision, month_end_closed_out, forecasting_in_line, resources_updated,
       last_modified, last_modified_by
FROM mv_flags
WHERE _reject_reason IS NULL AND _versions = 1 AND _copy = 1;

-- ---------------------------------------------------------------------------
-- Survey (one row per question)
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TEMPORARY VIEW mv_survey AS
SELECT *,
       MAX(_version) OVER (PARTITION BY _reject_reason, project_id, month_start, question_number) AS _versions,
       ROW_NUMBER() OVER (PARTITION BY _reject_reason, project_id, month_start, question_number, _version
                          ORDER BY last_modified DESC) AS _copy
FROM (
    SELECT *,
           DENSE_RANK() OVER (PARTITION BY _reject_reason, project_id, month_start, question_number
                              ORDER BY question_text, score, surveyed_party) AS _version
    FROM (
        SELECT
            TRIM(b.ProjectKey.Title)                             AS project_id,
            CAST(date_trunc('MONTH', CAST(b.MonthStart AS DATE)) AS DATE) AS month_start,
            CAST(b.QuestionNumber AS INT)                        AS question_number,
            -- The workbook stores the six scores but NOT the question text, so nobody now
            -- knows what question 3 asked (open question 6). Capturing it here fixes that
            -- permanently, which is why it is carried even though no measure reads it yet.
            TRIM(b.QuestionText)                                 AS question_text,
            CAST(b.Score AS INT)                                 AS score,
            -- 'ANONYMOUS' in the workbook today (SCORECARD CALC!C34). Captured rather than
            -- assumed: an attributed survey and an anonymous one are different instruments,
            -- and gold has always had the column.
            TRIM(b.SurveyedParty)                                AS surveyed_party,
            CAST(b.Modified AS TIMESTAMP)                        AS last_modified,
            TRIM(b.Editor.Title)                                 AS last_modified_by,
            CASE
                WHEN b.ProjectKey.Title IS NULL OR b.MonthStart IS NULL
                     THEN 'missing ProjectKey or MonthStart'
                WHEN v.project_id IS NULL
                     THEN 'unknown project - is CD Projects stale?'
                WHEN b.Score IS NULL
                     THEN 'missing Score'
            END AS _reject_reason
        FROM cd_bronze_man_survey b
        LEFT JOIN mv_valid_projects v ON v.project_id = TRIM(b.ProjectKey.Title)
    )
);

CREATE OR REPLACE TABLE cd_silver_man_survey AS
SELECT project_id, month_start, question_number, question_text, score, surveyed_party,
       last_modified, last_modified_by
FROM mv_survey
WHERE _reject_reason IS NULL AND _versions = 1 AND _copy = 1;

-- ---------------------------------------------------------------------------
-- Safety and quality (BOTH TEMPORARY - retire when Procore feeds them)
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TEMPORARY VIEW mv_safety_monthly AS
SELECT *,
       MAX(_version) OVER (PARTITION BY _reject_reason, project_id, month_start) AS _versions,
       ROW_NUMBER() OVER (PARTITION BY _reject_reason, project_id, month_start, _version
                          ORDER BY last_modified DESC) AS _copy
FROM (
    SELECT *,
           DENSE_RANK() OVER (PARTITION BY _reject_reason, project_id, month_start
                              ORDER BY hours_worked, recordable_incidents, orientations, ot_hours) AS _version
    FROM (
        SELECT
            TRIM(b.ProjectKey.Title)                             AS project_id,
            CAST(date_trunc('MONTH', CAST(b.MonthStart AS DATE)) AS DATE) AS month_start,
            CAST(b.HoursWorked AS DOUBLE)                        AS hours_worked,
            CAST(b.RecordableIncidents AS INT)                   AS recordable_incidents,
            CAST(b.Orientations AS INT)                          AS orientations,
            CAST(b.OtHours AS DOUBLE)                            AS ot_hours,
            CAST(b.Modified AS TIMESTAMP)                        AS last_modified,
            TRIM(b.Editor.Title)                                 AS last_modified_by,
            CASE
                WHEN b.ProjectKey.Title IS NULL OR b.MonthStart IS NULL
                     THEN 'missing ProjectKey or MonthStart'
                WHEN v.project_id IS NULL
                     THEN 'unknown project - is CD Projects stale?'
            END AS _reject_reason
        FROM cd_bronze_man_safety_monthly b
        LEFT JOIN mv_valid_projects v ON v.project_id = TRIM(b.ProjectKey.Title)
    )
);

CREATE OR REPLACE TABLE cd_silver_man_safety_monthly AS
SELECT project_id, month_start, hours_worked, recordable_incidents, orientations, ot_hours,
       last_modified, last_modified_by
FROM mv_safety_monthly
WHERE _reject_reason IS NULL AND _versions = 1 AND _copy = 1;

CREATE OR REPLACE TEMPORARY VIEW mv_quality_monthly AS
SELECT *,
       MAX(_version) OVER (PARTITION BY _reject_reason, project_id, month_start) AS _versions,
       ROW_NUMBER() OVER (PARTITION BY _reject_reason, project_id, month_start, _version
                          ORDER BY last_modified DESC) AS _copy
FROM (
    SELECT *,
           DENSE_RANK() OVER (PARTITION BY _reject_reason, project_id, month_start
                              ORDER BY observations, punchlist_items, avg_days_past_due, avg_days_to_close) AS _version
    FROM (
        SELECT
            TRIM(b.ProjectKey.Title)                             AS project_id,
            CAST(date_trunc('MONTH', CAST(b.MonthStart AS DATE)) AS DATE) AS month_start,
            CAST(b.Observations AS INT)                          AS observations,
            CAST(b.PunchlistItems AS INT)                        AS punchlist_items,
            CAST(b.AvgDaysPastDue AS DOUBLE)                     AS avg_days_past_due,
            CAST(b.AvgDaysToClose AS DOUBLE)                     AS avg_days_to_close,
            CAST(b.Modified AS TIMESTAMP)                        AS last_modified,
            TRIM(b.Editor.Title)                                 AS last_modified_by,
            CASE
                WHEN b.ProjectKey.Title IS NULL OR b.MonthStart IS NULL
                     THEN 'missing ProjectKey or MonthStart'
                WHEN v.project_id IS NULL
                     THEN 'unknown project - is CD Projects stale?'
            END AS _reject_reason
        FROM cd_bronze_man_quality_monthly b
        LEFT JOIN mv_valid_projects v ON v.project_id = TRIM(b.ProjectKey.Title)
    )
);

CREATE OR REPLACE TABLE cd_silver_man_quality_monthly AS
SELECT project_id, month_start, observations, punchlist_items, avg_days_past_due, avg_days_to_close,
       last_modified, last_modified_by
FROM mv_quality_monthly
WHERE _reject_reason IS NULL AND _versions = 1 AND _copy = 1;

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

CREATE OR REPLACE TEMPORARY VIEW mv_milestones AS
SELECT *,
       MAX(_version) OVER (PARTITION BY _reject_reason, project_id, milestone_name) AS _versions,
       ROW_NUMBER() OVER (PARTITION BY _reject_reason, project_id, milestone_name, _version
                          ORDER BY last_modified DESC) AS _copy
FROM (
    SELECT *,
           DENSE_RANK() OVER (PARTITION BY _reject_reason, project_id, milestone_name
                              ORDER BY activity_key, contract_start, contract_finish, baseline_start, baseline_finish, is_substantial_completion) AS _version
    FROM (
        SELECT
            TRIM(b.ProjectKey.Title)                             AS project_id,
            TRIM(b.MilestoneName)                                AS milestone_name,
            TRIM(b.ActivityKey)                                  AS activity_key,
            CAST(b.ContractStart AS DATE)                        AS contract_start,
            CAST(b.ContractFinish AS DATE)                       AS contract_finish,
            CAST(b.BaselineStart AS DATE)                        AS baseline_start,
            CAST(b.BaselineFinish AS DATE)                       AS baseline_finish,
            CAST(b.IsSubstantialCompletion AS BOOLEAN)           AS is_substantial_completion,
            CAST(b.Modified AS TIMESTAMP)                        AS last_modified,
            TRIM(b.Editor.Title)                                 AS last_modified_by,
            CASE
                WHEN b.ProjectKey.Title IS NULL OR b.MilestoneName IS NULL
                     THEN 'missing ProjectKey or MilestoneName'
                WHEN v.project_id IS NULL
                     THEN 'unknown project - is CD Projects stale?'
            END AS _reject_reason
        FROM cd_bronze_man_milestones b
        LEFT JOIN mv_valid_projects v ON v.project_id = TRIM(b.ProjectKey.Title)
    )
);

CREATE OR REPLACE TABLE cd_silver_man_milestones AS
SELECT project_id, milestone_name, activity_key, contract_start, contract_finish, baseline_start, baseline_finish, is_substantial_completion,
       last_modified, last_modified_by
FROM mv_milestones
WHERE _reject_reason IS NULL AND _versions = 1 AND _copy = 1;

-- ---------------------------------------------------------------------------
-- Daily log compliance
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TEMPORARY VIEW mv_daily_log_compliance AS
SELECT *,
       MAX(_version) OVER (PARTITION BY _reject_reason, project_id, month_start) AS _versions,
       ROW_NUMBER() OVER (PARTITION BY _reject_reason, project_id, month_start, _version
                          ORDER BY last_modified DESC) AS _copy
FROM (
    SELECT *,
           DENSE_RANK() OVER (PARTITION BY _reject_reason, project_id, month_start
                              ORDER BY logs_expected, logs_missed_same_day) AS _version
    FROM (
        SELECT
            TRIM(b.ProjectKey.Title)                             AS project_id,
            CAST(date_trunc('MONTH', CAST(b.MonthStart AS DATE)) AS DATE) AS month_start,
            CAST(b.LogsExpected AS INT)                          AS logs_expected,
            -- MISSED SAME DAY, not submitted. SCORECARD CALC!E28 scores whether the log went
            -- in on the day of the work; a log typed up three days later is submitted and is
            -- still a miss. This parser used to read LogsSubmitted, which measures a different
            -- and easier thing - and gold, the model and the scorecard have always asked for
            -- the harder one.
            CAST(b.LogsMissedSameDay AS INT)                     AS logs_missed_same_day,
            CAST(b.Modified AS TIMESTAMP)                        AS last_modified,
            TRIM(b.Editor.Title)                                 AS last_modified_by,
            CASE
                WHEN b.ProjectKey.Title IS NULL OR b.MonthStart IS NULL
                     THEN 'missing ProjectKey or MonthStart'
                WHEN v.project_id IS NULL
                     THEN 'unknown project - is CD Projects stale?'
            END AS _reject_reason
        FROM cd_bronze_man_daily_log_compliance b
        LEFT JOIN mv_valid_projects v ON v.project_id = TRIM(b.ProjectKey.Title)
    )
);

CREATE OR REPLACE TABLE cd_silver_man_daily_log_compliance AS
SELECT project_id, month_start, logs_expected, logs_missed_same_day,
       last_modified, last_modified_by
FROM mv_daily_log_compliance
WHERE _reject_reason IS NULL AND _versions = 1 AND _copy = 1;

-- ---------------------------------------------------------------------------
-- Job Register - the BUILD site, not the reporting site
-- ---------------------------------------------------------------------------
--
-- Written by the two Power Automate job flows (power-automate/), one row per job from the
-- moment somebody asks for it. This is the ONLY record of a job between "requested" and
-- "it became a Procore project", and many jobs never make that second step - so there is
-- no ProjectKey here and no join to dim_Project. Bidding on work you do not win still
-- happened, and a register that quietly dropped those rows would answer "how many jobs did
-- we estimate this year" with only the ones that were won.
--
-- DEDUPLICATED ON Id, NOT ON JobNumber, and that distinction is the entire point.
--
-- Two register rows sharing a JobNumber is not a duplicate row - it is TWO DIFFERENT JOBS
-- that were both issued 26-025, which is what happens the moment somebody turns off the
-- flows' `concurrency: runs: 1` in the Power Automate designer. Both flows read max(JobSeq),
-- both compute the same next number, and nothing anywhere errors. Deduplicating on
-- JobNumber here would discard one of the two real jobs and make the collision invisible -
-- the same silent-drop failure this file exists to prevent, applied to the one bug
-- power-automate/README.md calls "the single most likely production bug in the whole
-- solution".
--
-- So both rows survive to gold, and dq/expectations.py fails the nightly gate on the
-- duplicate. Id is SharePoint's own item identity, so this still collapses the same item
-- appearing twice, which is all a dedup should ever do.

CREATE OR REPLACE TABLE cd_silver_man_job_register AS
SELECT * FROM (
    SELECT
        CAST(Id AS INT)                                     AS register_id,
        TRIM(Title)                                         AS project_name,
        CAST(JobYear AS INT)                                AS job_year,
        CAST(JobSeq AS INT)                                 AS job_seq,
        UPPER(TRIM(JobNumber))                              AS job_number,
        -- The flows write 'Requested' / 'Estimating' / 'Bidding' / 'Failed'. Upper-cased to
        -- the same shape as every other code in this platform, so a measure over Stage
        -- reads like a measure over StatusCode rather than like a special case.
        UPPER(TRIM(Stage))                                  AS stage,
        -- A SharePoint URL column arrives as a record, the same way a lookup does. Taking
        -- .Url keeps the link and drops the display text, which is the folder name and is
        -- already carried by project_name.
        EstimatingFolderUrl.Url                             AS estimating_folder_url,
        ProjectFolderUrl.Url                                AS project_folder_url,
        TRIM(RequestedBy)                                   AS requested_by,
        CAST(RequestedAt AS TIMESTAMP)                      AS requested_at,
        CAST(CompletedAt AS TIMESTAMP)                      AS completed_at,
        TRIM(CopyJobStatus)                                 AS copy_job_status,
        TRIM(ErrorDetail)                                   AS error_detail,
        CAST(Modified AS TIMESTAMP)                         AS last_modified,
        TRIM(Editor.Title)                                  AS last_modified_by,
        ROW_NUMBER() OVER (PARTITION BY CAST(Id AS INT)
                           ORDER BY CAST(Modified AS TIMESTAMP) DESC) AS _rn
    FROM cd_bronze_man_job_register
    WHERE Id IS NOT NULL
)
WHERE _rn = 1;

-- ---------------------------------------------------------------------------
-- Rejects: every row the rules above excluded, WITH THE REASON
-- ---------------------------------------------------------------------------
--
-- This is the half that makes the rules safe to have. A row silently excluded is a risk
-- that disappeared from a leadership report; a row in here is a line on the DQ page with
-- the project, the month and what was wrong with it.

CREATE OR REPLACE TABLE cd_dq_rejects_manual AS
SELECT 'cd_silver_man_wins' AS target_table, project_id, month_start AS month_start,
       CONCAT('win #', CAST(win_number AS STRING)) AS item_ref,
       COALESCE(_reject_reason, 'conflicting duplicate - (project, month, win number) has more than one version; resolve in SharePoint') AS reason,
       last_modified, last_modified_by
FROM mv_wins
WHERE _reject_reason IS NOT NULL OR _versions > 1

UNION ALL
SELECT 'cd_silver_man_risks' AS target_table, project_id, month_start AS month_start,
       CONCAT('risk #', CAST(risk_number AS STRING)) AS item_ref,
       COALESCE(_reject_reason, 'conflicting duplicate - (project, month, risk number) has more than one version; resolve in SharePoint') AS reason,
       last_modified, last_modified_by
FROM mv_risks
WHERE _reject_reason IS NOT NULL OR _versions > 1

UNION ALL
SELECT 'cd_silver_man_priority_items' AS target_table, project_id, month_start AS month_start,
       CONCAT('priority item #', CAST(item_number AS STRING)) AS item_ref,
       COALESCE(_reject_reason, 'conflicting duplicate - (project, month, item number) has more than one version; resolve in SharePoint') AS reason,
       last_modified, last_modified_by
FROM mv_priority_items
WHERE _reject_reason IS NOT NULL OR _versions > 1

UNION ALL
SELECT 'cd_silver_man_flags' AS target_table, project_id, month_start AS month_start,
       'monthly flags' AS item_ref,
       COALESCE(_reject_reason, 'conflicting duplicate - (project, month) has more than one version; resolve in SharePoint') AS reason,
       last_modified, last_modified_by
FROM mv_flags
WHERE _reject_reason IS NOT NULL OR _versions > 1

UNION ALL
SELECT 'cd_silver_man_survey' AS target_table, project_id, month_start AS month_start,
       CONCAT('question #', CAST(question_number AS STRING)) AS item_ref,
       COALESCE(_reject_reason, 'conflicting duplicate - (project, month, question number) has more than one version; resolve in SharePoint') AS reason,
       last_modified, last_modified_by
FROM mv_survey
WHERE _reject_reason IS NOT NULL OR _versions > 1

UNION ALL
SELECT 'cd_silver_man_safety_monthly' AS target_table, project_id, month_start AS month_start,
       'monthly safety' AS item_ref,
       COALESCE(_reject_reason, 'conflicting duplicate - (project, month) has more than one version; resolve in SharePoint') AS reason,
       last_modified, last_modified_by
FROM mv_safety_monthly
WHERE _reject_reason IS NOT NULL OR _versions > 1

UNION ALL
SELECT 'cd_silver_man_quality_monthly' AS target_table, project_id, month_start AS month_start,
       'monthly quality' AS item_ref,
       COALESCE(_reject_reason, 'conflicting duplicate - (project, month) has more than one version; resolve in SharePoint') AS reason,
       last_modified, last_modified_by
FROM mv_quality_monthly
WHERE _reject_reason IS NOT NULL OR _versions > 1

UNION ALL
SELECT 'cd_silver_man_milestones' AS target_table, project_id, CAST(NULL AS DATE) AS month_start,
       CONCAT('milestone "', milestone_name, '"') AS item_ref,
       COALESCE(_reject_reason, 'conflicting duplicate - (project, milestone name) has more than one version; resolve in SharePoint') AS reason,
       last_modified, last_modified_by
FROM mv_milestones
WHERE _reject_reason IS NOT NULL OR _versions > 1

UNION ALL
SELECT 'cd_silver_man_daily_log_compliance' AS target_table, project_id, month_start AS month_start,
       'daily log compliance' AS item_ref,
       COALESCE(_reject_reason, 'conflicting duplicate - (project, month) has more than one version; resolve in SharePoint') AS reason,
       last_modified, last_modified_by
FROM mv_daily_log_compliance
WHERE _reject_reason IS NOT NULL OR _versions > 1

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
  AND CAST(MonthStart AS DATE) <> CAST(date_trunc('MONTH', CAST(MonthStart AS DATE)) AS DATE)

UNION ALL
-- The Job Register. No project and no month - a job predates both - so those two columns
-- are NULL here rather than invented. A register row that moved past Requested without
-- picking up a JobNumber is a flow that half-ran: EstimatingSetup writes Stage and
-- JobNumber in the same action, so one without the other means something failed between
-- issuing the number and recording it.
SELECT 'cd_silver_man_job_register', CAST(NULL AS STRING), CAST(NULL AS DATE),
       CONCAT('job "', COALESCE(TRIM(Title), '(unnamed)'), '"'),
       CONCAT('Stage is ', COALESCE(Stage, '(blank)'), ' but JobNumber is empty - ',
              'the flow did not finish. Check ErrorDetail on the row.'),
       CAST(Modified AS TIMESTAMP), TRIM(Editor.Title)
FROM cd_bronze_man_job_register
WHERE UPPER(TRIM(COALESCE(Stage, ''))) IN ('ESTIMATING', 'BIDDING')
  AND (JobNumber IS NULL OR TRIM(JobNumber) = '');
