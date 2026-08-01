-- gold: fct_Milestone - critical-path schedule, from Outbuild.
--
-- Outbuild is the ONLY real source for this. Procore's OAS has no milestone path at all
-- (powerbi/source-mapping.md:87), and SCHEDULE!Table5 in the workbook is typed by hand for
-- every project every month.
--
-- Only critical-path activities are kept. Outbuild carries the full schedule (1,196
-- activities), but SCHEDULE!Table5 is explicitly the critical-path milestone list, capped
-- at 10 rows plus a protected "Contractural Substaintial Completion [DO NOT DELETE THIS
-- LINE]" terminator. is_critical is Outbuild's own flag, so this is its judgement rather
-- than ours.
--
-- CONTRACT DATES ARE NOT HERE. SCHEDULE!D:E are contract start/finish, which exist in
-- neither Procore nor Outbuild - they come off the signed contract. They stay manual
-- (man_Milestones) and join on ActivityKey. Baseline dates are likewise absent: Outbuild
-- exposes current dates, and whether baselines are maintained there at all is unconfirmed.
-- So StartVariance/FinishVariance cannot yet be computed, and are NOT faked with
-- current-vs-current, which would produce a confident zero.
--
-- HasDateInversion is Excel defect #6 caught at load time: two milestone rows in the
-- sample workbook have a start later than their finish, and nothing ever flagged it.

CREATE OR REPLACE TABLE fct_Milestone AS
SELECT
    project_id                    AS ProjectKey,
    activity_id                   AS ActivityKey,
    TRIM(activity_name)           AS MilestoneName,
    activity_type                 AS ActivityType,
    TRIM(status)                  AS StatusLabel,
    start_date                    AS CurrentStart,
    end_date                      AS CurrentFinish,
    CASE WHEN start_date IS NULL THEN NULL
         ELSE make_date(year(start_date), month(start_date), 1) END AS MonthStart,
    duration                      AS DurationDays,
    -- Outbuild reports progress 0-1; kept as a fraction so it formats as a percentage in
    -- the report rather than being multiplied twice.
    progress                      AS PercentComplete,
    is_critical                   AS IsCritical,
    CASE WHEN end_date IS NOT NULL AND end_date < CURRENT_DATE AND COALESCE(progress, 0) < 1
         THEN TRUE ELSE FALSE END AS IsOverdue,
    CASE WHEN start_date IS NOT NULL AND end_date IS NOT NULL AND start_date > end_date
         THEN TRUE ELSE FALSE END AS HasDateInversion
FROM sv_outbuild_activities
WHERE project_id IS NOT NULL
  AND is_critical = TRUE;
