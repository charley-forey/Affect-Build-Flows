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
-- (man_Milestones) and join on ActivityKey.
--
-- BASELINES ARE OUTBUILD'S, AND ARE MAINTAINED (checked live 2026-10-16). This file used to
-- say they were absent; they are on every activity, and on the current schedules they
-- differ from the current dates on most rows (Embankment Phase III: 137 of 137 baselined,
-- 132 finishes moved; PCNA 49/49, 42 moved; 360Lex 220 of 266 baselined) - so they are
-- real baselines, not copies of the current dates. FinishVarianceDays = CurrentFinish -
-- BaselineFinish, NULL when there is no baseline (never a fake zero). Completion Variance
-- reads BaselineFinish, preferring a hand-typed man_Milestones baseline when one exists.
--
-- ONLY THE CURRENT SCHEDULE. An Outbuild project carries several schedules - drafts,
-- copies, superseded versions - and exactly one has is_current_schedule. Until 2026-10-16
-- this kept every schedule's critical activities: Sauna Lounge has 6 schedules (current
-- 103755 "Contract Schedule"; SU01/SU02/SU03/RECOVERY drafts), so its milestones were
-- counted several times over; 360Lex mixed its current "8th & 20th Floor" with "Main
-- Schedule - Copy" and "15th & 17th Floor"; Embankment Phase III mixed "August Update" with
-- its superseded predecessor. Schedule Performance (% overdue) and the "schedule ended -
-- site still active" check were being computed over schedules nobody works to any more.
-- `= TRUE` is strict: an activity whose schedule identity is unknown is not counted.
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
         THEN TRUE ELSE FALSE END AS HasDateInversion,
    baseline_start_date           AS BaselineStart,
    baseline_end_date             AS BaselineFinish,
    -- Positive = finishing later than baselined. NULL when either date is missing.
    CASE WHEN end_date IS NOT NULL AND baseline_end_date IS NOT NULL
         THEN datediff(end_date, baseline_end_date) END AS FinishVarianceDays
FROM sv_outbuild_activities
WHERE project_id IS NOT NULL
  AND is_critical = TRUE
  AND is_current_schedule = TRUE;
