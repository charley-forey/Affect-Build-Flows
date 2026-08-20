-- silver: Outbuild activities - the only source of milestone data anywhere in the estate.
--
-- Until 2026-08-20 there was no Outbuild silver at all. `sv_outbuild_activities` read
-- Rebecca's `Silver_Lakehouse/Outbuild_activities` directly, because our own ingestion did
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
-- multiplied twice" - and the offline fixture uses 0.5 / 0.2 / 0.0. Rebecca's silver had
-- already normalised it, so reading her table hid the difference.
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
-- `status`: there is no status field on an activity. Rebecca's table has a `Status` column
-- that is hers, not Outbuild's. It is NULL here rather than derived from progress, because
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
        TRIM(get_json_object(payload, '$.name'))              AS outbuild_project_name
    FROM cd_bronze_outbuild_projects
),
schedule_map AS (
    SELECT get_json_object(sched, '$.id') AS schedule_id,
           procore_project_id, outbuild_project_id, outbuild_project_name
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
    -- Baselines, landed but not yet consumed. See the header.
    CAST(get_json_object(a.payload, '$.baseline_start_date') AS DATE)   AS baseline_start_date,
    CAST(get_json_object(a.payload, '$.baseline_end_date')   AS DATE)   AS baseline_end_date,
    CAST(get_json_object(a.payload, '$.baseline_duration')   AS DOUBLE) AS baseline_duration,
    -- Kept so an unattributed activity can be named without a re-extract.
    CAST(m.outbuild_project_id                            AS STRING)  AS outbuild_project_id,
    m.outbuild_project_name                                           AS outbuild_project_name,
    CAST(get_json_object(a.payload, '$.schedule_id')      AS STRING)  AS schedule_id,
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
