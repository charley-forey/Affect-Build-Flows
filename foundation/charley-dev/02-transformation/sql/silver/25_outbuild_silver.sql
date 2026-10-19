-- silver: Outbuild activities - the only source of milestone data anywhere in the estate.
--
-- Until 2026-08-20 there was no Outbuild silver at all. `sv_outbuild_activities` read
-- the Affect reporting lead's `Silver_Lakehouse/Outbuild_activities` directly, because our own ingestion did
-- not exist; the token arrived 2026-08-19 and 3,078 rows across 15 endpoints have been
-- landing since. This is the parser that lets fct_Milestone read our own bronze.
--
-- ---------------------------------------------------------------------------
-- AN ACTIVITY DOES NOT CARRY A PROJECT ID. THIS IS THE WHOLE DIFFICULTY.
-- ---------------------------------------------------------------------------
--
-- Outbuild's /activities payload has `schedule_id`, `gantt_id`, `company_id` and
-- `organization_id` - and no project. The route to a project is through /projects, whose
-- records embed their schedules:
--
--     activity.schedule_id  ->  project.schedules[].id  ->  project.procore_id
--
-- `procore_id` is the join key to everything else we hold, and Outbuild's own docs qualify
-- it: "only applicable if there is an active integration with Procore". Measured live on
-- 2026-08-20, only **3 of 15** Outbuild projects carry one. The other twelve are real
-- projects with real schedules that cannot be attributed to anything in Procore.
--
-- Those twelve are NOT dropped here. Their activities land with `project_id` NULL and
-- `outbuild_project_id` / `outbuild_project_name` populated, so "which projects are we
-- failing to attribute, and what are they called" is one query rather than a re-extract.
-- Gold's `WHERE project_id IS NOT NULL` is what excludes them from fct_Milestone, which is
-- the right place for that decision: silver types and joins, gold decides what counts.
--
-- The alternative - inner-joining here - would make the twelve vanish at the layer whose
-- entire job is to not lose rows silently, and the symptom would be a milestone count that
-- looks plausible and is a fifth of the schedule.
--
-- ---------------------------------------------------------------------------
-- PROGRESS IS 0-100 HERE AND 0-1 DOWNSTREAM
-- ---------------------------------------------------------------------------
--
-- Outbuild returns `progress` as a percentage: measured live, min 0.0, max 100.0.
-- 24_fct_milestone.sql documents its contract as a fraction - "Outbuild reports progress
-- 0-1; kept as a fraction so it formats as a percentage in the report rather than being
-- multiplied twice" - and the offline fixture uses 0.5 / 0.2 / 0.0. The Affect reporting lead's silver had
-- already normalised it, so reading their table hid the difference.
--
-- So it is divided by 100 exactly once, here. Getting this wrong is not a visible failure:
-- `Avg Milestone Progress` would read 5000%, and `IsOverdue` - which tests
-- `COALESCE(progress, 0) < 1` - would treat every activity past 1% as complete and report
-- **zero overdue milestones on a late job**. A confident, wrong, quiet answer.
--
-- ---------------------------------------------------------------------------
-- WHAT OUTBUILD DOES NOT HAVE
-- ---------------------------------------------------------------------------
--
-- `status`: there is no status field on an activity. The Affect reporting lead's table has a `Status` column
-- that is theirs, not Outbuild's. It is NULL here rather than derived from progress, because
-- "0% means Not Started" is a guess dressed as data. Nothing reads
-- fct_Milestone[StatusLabel] - no measure, no visual - so this costs nothing today, and
-- inventing it would cost the day somebody trusts it.
--
-- `baseline_start_date` / `baseline_end_date` / `baseline_duration` DO exist, and are kept.
-- 24_fct_milestone.sql says baselines are absent and "whether baselines are maintained
-- there at all is unconfirmed", so StartVariance/FinishVariance were left uncomputed rather
-- than faked as current-vs-current. They are present on every one of the 1,860 rows landed.
-- Whether they are MAINTAINED is still a question for Affect - a baseline copied from the
-- current schedule at import is not a baseline - so nothing is computed from them yet.
-- Landing them means that decision is a gold change, not another extract.
--
-- ANSWERED 2026-10-16, from the live tables: baselines ARE maintained. On the current
-- schedules most activities carry a baseline that differs from the current dates
-- (Embankment Phase III 137 of 137 baselined, 132 finishes moved; PCNA 49/49, 42 moved;
-- 360Lex 220 of 266). gold fct_Milestone now reads them (Completion Variance).
--
-- ---------------------------------------------------------------------------
-- A PROJECT HAS SEVERAL SCHEDULES; EXACTLY ONE IS CURRENT (added 2026-10-16)
-- ---------------------------------------------------------------------------
--
-- Each entry of the project's `schedules` array carries `is_current_schedule` and `name`.
-- The others are drafts, copies and superseded versions: Sauna Lounge has 6 (current
-- 103755 "Contract Schedule"; SU01/SU02/SU03/RECOVERY drafts), 360Lex has 3 (current 76258
-- "8th & 20th Floor"; "Main Schedule - Copy" and "15th & 17th Floor" not current). Silver
-- keeps every schedule's activities and labels them; gold decides to read only the
-- current one. `project_stage` / `archive_reason` come off the project record too
-- (PCNA and Evergreen Cemetery are 'archived').
--
-- The project id here is still Outbuild's own `procore_id`, NULL when there is no Procore
-- integration. The reviewed manual map (seed/outbuild_project_map.csv) is applied on top
-- of it in sv_outbuild_activities (01_source_views_cd.sql), where the seeds are readable -
-- silver records what Outbuild says, the source view adds what a person decided.

CREATE OR REPLACE TABLE cd_silver_outbuild_activities AS
WITH schedule_rows AS (
    -- `schedules` is a JSON array on the project record. Explode it to one row per
    -- schedule, carrying the project's ids down with it.
    --
    -- The generator is in the SELECT list rather than a LATERAL VIEW on purpose: LATERAL
    -- VIEW is Hive/Spark-only and the offline harness runs this same file through DuckDB,
    -- so it would have made the parser untestable. Spark and DuckDB both accept a single
    -- generator alongside other columns here. Same reason 30_manual_silver.sql spells
    -- month-flooring date_trunc rather than Spark's trunc().
    --
    -- FOUR of the fifteen projects have more than one schedule (max 4), so this cannot be
    -- reduced to `$.schedules[0].id`: measured 2026-08-20, first-schedule-only would drop
    -- 1,150 of 1,860 activities while looking perfectly healthy.
    SELECT
        explode(from_json(get_json_object(payload, '$.schedules'), 'array<string>')) AS sched,
        get_json_object(payload, '$.procore_id')              AS procore_project_id,
        get_json_object(payload, '$.id')                      AS outbuild_project_id,
        TRIM(get_json_object(payload, '$.name'))              AS outbuild_project_name,
        TRIM(get_json_object(payload, '$.stage'))             AS project_stage,
        TRIM(get_json_object(payload, '$.archive_reason'))    AS archive_reason
    FROM cd_bronze_outbuild_projects
),
schedule_map AS (
    SELECT get_json_object(sched, '$.id') AS schedule_id,
           TRIM(get_json_object(sched, '$.name'))                    AS schedule_name,
           CAST(get_json_object(sched, '$.is_current_schedule') AS BOOLEAN) AS is_current_schedule,
           procore_project_id, outbuild_project_id, outbuild_project_name,
           project_stage, archive_reason
    FROM schedule_rows
)
SELECT
    -- The PROCORE project id, which is what every other fact in the model joins on.
    -- NULL for the twelve Outbuild projects with no Procore integration - see the header.
    CAST(m.procore_project_id                             AS STRING)  AS project_id,
    CAST(get_json_object(a.payload, '$.id')               AS STRING)  AS activity_id,
    TRIM(get_json_object(a.payload, '$.name'))                        AS activity_name,
    -- ISO with a time component ("2025-12-23T17:00:00.000"); CAST to DATE truncates it.
    CAST(get_json_object(a.payload, '$.start_date')       AS DATE)    AS start_date,
    CAST(get_json_object(a.payload, '$.end_date')         AS DATE)    AS end_date,
    -- /100: Outbuild's 0-100 to the 0-1 fraction gold expects. See the header.
    CAST(get_json_object(a.payload, '$.progress')  AS DOUBLE) / 100.0 AS progress,
    CAST(get_json_object(a.payload, '$.duration')         AS DOUBLE)  AS duration,
    CAST(get_json_object(a.payload, '$.is_critical')      AS BOOLEAN) AS is_critical,
    -- Outbuild's published docs spell this `activiy_type` (their typo). The LIVE payload
    -- spells it correctly on all 1,860 rows - checked, because trusting the doc would have
    -- produced a silently all-NULL column.
    TRIM(get_json_object(a.payload, '$.activity_type'))               AS activity_type,
    CAST(NULL AS STRING)                                              AS status,
    -- Baselines: maintained in Outbuild (checked 2026-10-16), read by fct_Milestone.
    CAST(get_json_object(a.payload, '$.baseline_start_date') AS DATE)   AS baseline_start_date,
    CAST(get_json_object(a.payload, '$.baseline_end_date')   AS DATE)   AS baseline_end_date,
    CAST(get_json_object(a.payload, '$.baseline_duration')   AS DOUBLE) AS baseline_duration,
    -- Kept so an unattributed activity can be named without a re-extract.
    CAST(m.outbuild_project_id                            AS STRING)  AS outbuild_project_id,
    m.outbuild_project_name                                           AS outbuild_project_name,
    CAST(get_json_object(a.payload, '$.schedule_id')      AS STRING)  AS schedule_id,
    -- Which of the project's schedules this activity is on, and whether it is the current
    -- one. NULL only when the schedule is not in /projects (then project_id is NULL too).
    m.schedule_name                                                   AS schedule_name,
    m.is_current_schedule                                             AS is_current_schedule,
    m.project_stage                                                   AS project_stage,
    m.archive_reason                                                  AS archive_reason,
    a._ingested_at, a._batch_id
FROM cd_bronze_outbuild_activities a
-- LEFT, not INNER: an activity whose schedule is not in /projects is a real gap and should
-- be visible as a NULL project, not absent. Measured 2026-08-20: 0 of 1,860 fail to match a
-- schedule, so this join currently loses nothing - which is worth knowing rather than
-- assuming, because it means the twelve unattributed projects are a Procore-integration
-- question and not a broken join.
LEFT JOIN schedule_map m
       ON get_json_object(a.payload, '$.schedule_id') = m.schedule_id
WHERE get_json_object(a.payload, '$.id') IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Rejects
-- ---------------------------------------------------------------------------
-- Two ways a row leaves this parser without a trace, both now recorded:
--
--   * an activity with no id (the WHERE above) - target cd_silver_outbuild_activities, so
--     bronze activities = silver activities + these rejects;
--   * an Outbuild project with no schedules. explode() of an empty or missing array yields
--     no row, so the project vanishes from the schedule map - and sv_outbuild_projects,
--     which is derived from the activities, never sees it either. Its target is the map,
--     not the activity table, because no activity row was lost.
--
-- DELETE then INSERT for the same reason as 24_qc_procore_silver.sql.

DELETE FROM cd_dq_rejects
WHERE target_table IN ('cd_silver_outbuild_activities', 'outbuild_schedule_map');

INSERT INTO cd_dq_rejects
SELECT 'cd_silver_outbuild_activities', 'missing id', payload, _batch_id
FROM cd_bronze_outbuild_activities
WHERE get_json_object(payload, '$.id') IS NULL
UNION ALL
SELECT 'outbuild_schedule_map',
       'Outbuild project has no schedules - none of its activities can be attributed',
       payload, _batch_id
FROM cd_bronze_outbuild_projects
WHERE get_json_object(payload, '$.schedules[0]') IS NULL;
