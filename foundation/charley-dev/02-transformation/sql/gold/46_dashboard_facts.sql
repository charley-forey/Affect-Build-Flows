-- gold: the Weekly Dashboard's facts (2026-10-21 call, AFFECT Weekly Dashboard Layout deck,
-- Scorecard.xlsx). Six tables, each the record behind one or more scorecard measures:
--
--   fct_Inspection        Safety / Quality inspections, classified from the template name
--   fct_Meeting           OAC and trade partner meetings, with the agenda and minutes checks
--   fct_ProjectTeam       PM, APM, Superintendent, Assistant Superintendent, Project Executive
--   fct_ScheduleActivity  every activity on the CURRENT Outbuild schedule (fct_Milestone keeps
--                         only the critical path): near-term milestones, recent wins
--   fct_LookaheadTask     the 3-week look-ahead tasks under those activities
--   dim_ReportWeek        the reporting weeks the dashboard's week slicer offers
--
-- Nothing is scored here. The scores are DAX over these rows and the dim_Dash* seeds, so
-- retuning a band never needs a rebuild.

-- ---------------------------------------------------------------------------
-- fct_Inspection
-- ---------------------------------------------------------------------------
--
-- Procore's inspection_type is NULL on every inspection on this tenant (checked
-- 2026-10-25), so SAFETY vs QUALITY comes from the template and inspection names: the
-- highest-priority seed_InspectionCategory pattern the lower-cased names contain. A template
-- no pattern matches is 'Unclassified' - counted by neither pillar, and listed on the
-- dashboard so a new template gets a pattern instead of silently scoring nothing.
--
-- PERFORMED, not merely scheduled. Procore dates an inspection when it is created and
-- several sit OPEN with future dates. One counts once it is closed or has at least one item
-- answered (conforming, deficient, not applicable or neutral) - "not inspected" is not an
-- answer. The reporting-week window is applied in DAX.
CREATE OR REPLACE TABLE fct_Inspection AS
WITH matched AS (
    SELECT i.InspectionKey, c.Category,
           ROW_NUMBER() OVER (PARTITION BY i.InspectionKey ORDER BY c.Priority) AS rn
    FROM fct_ProcoreInspection i
    JOIN seed_InspectionCategory c
      ON LOWER(CONCAT(COALESCE(i.SourceTemplateName, ''), ' ', COALESCE(i.InspectionName, '')))
         LIKE CONCAT('%', c.Pattern, '%')
)
SELECT
    i.ProjectKey,
    i.InspectionKey,
    i.InspectionNumber,
    i.InspectionName,
    i.SourceTemplateName                         AS TemplateName,
    COALESCE(m.Category, 'Unclassified')         AS Category,
    i.SourceStatus                               AS StatusLabel,
    i.InspectionDate,
    i.DueDate,
    i.SourceItemCount                            AS ItemCount,
    i.DeficientItemCount,
    CASE WHEN UPPER(COALESCE(i.SourceStatus, '')) = 'CLOSED'
              OR COALESCE(i.ConformingItemCount, 0) + COALESCE(i.DeficientItemCount, 0)
                 + COALESCE(i.NotApplicableItemCount, 0) + COALESCE(i.NeutralItemCount, 0) > 0
         THEN TRUE ELSE FALSE END                AS IsPerformed
FROM fct_ProcoreInspection i
LEFT JOIN matched m
       ON m.InspectionKey = i.InspectionKey AND m.rn = 1
WHERE i.ProjectKey IS NOT NULL;

-- ---------------------------------------------------------------------------
-- fct_Meeting
-- ---------------------------------------------------------------------------
--
-- The standard (Scorecard.xlsx, Field Ops): agenda sent at least 24 hours before the
-- meeting, minutes sent within 24 hours after. What Procore's meeting list can verify:
--
--   MinutesOnTime   TRUE when the minutes were distributed on the meeting day or the day
--                   after; FALSE when they went out later, or a past meeting has none;
--                   NULL for a meeting still to come.
--   AgendaOnTime    TRUE when the agenda was distributed by the day before; FALSE when it
--                   went out on the day or later, or a past meeting was never sent at all;
--                   NULL when the minutes were sent afterwards - Procore's list keeps only
--                   the LAST send, so that agenda's time is gone (the per-meeting
--                   change_history endpoint has it, and is the planned upgrade).
--
-- DATES, NOT HOURS. The list carries the meeting date but not its start time, so "24 hours"
-- is read as "by the day before" and "within a day after". The start time is on the meeting
-- detail endpoint, which costs a request per meeting.
--
-- ONE MEETING PER TYPE PER DAY. A follow-up copied in Procore keeps its source's date until
-- someone edits it (11 Essex has four OAC meetings dated 2025-11-06, created over five
-- weeks). Only the earliest-created counts; the rest are IsDuplicateDate.
--
-- Classified by series title (seed_MeetingCategory): OAC, Trade Partner, or Other.
CREATE OR REPLACE TABLE fct_Meeting AS
WITH cat AS (
    SELECT m.meeting_id, c.Category,
           ROW_NUMBER() OVER (PARTITION BY m.meeting_id ORDER BY c.Priority) AS rn
    FROM sv_meetings m
    JOIN seed_MeetingCategory c
      ON LOWER(COALESCE(m.series_title, m.title, '')) LIKE CONCAT('%', c.Pattern, '%')
),
typed AS (
    SELECT m.*, COALESCE(c.Category, 'Other') AS meeting_type
    FROM sv_meetings m
    LEFT JOIN cat c ON c.meeting_id = m.meeting_id AND c.rn = 1
    WHERE m.project_id IS NOT NULL AND m.meeting_date IS NOT NULL
),
ranked AS (
    SELECT t.*,
           ROW_NUMBER() OVER (PARTITION BY t.project_id, t.meeting_type, t.meeting_date
                              ORDER BY t.created_at, t.meeting_id) AS date_rank,
           CASE WHEN t.last_distributed_event = 'minutes'
                    THEN t.distributed_date <= date_add(t.meeting_date, 1)
                WHEN t.meeting_date < CURRENT_DATE THEN FALSE END AS minutes_on_time,
           CASE WHEN t.last_distributed_event = 'agenda'
                    THEN t.distributed_date <= date_add(t.meeting_date, -1)
                WHEN t.last_distributed_event IS NULL AND t.meeting_date < CURRENT_DATE
                    THEN FALSE END AS agenda_on_time
    FROM typed t
)
SELECT
    project_id                                   AS ProjectKey,
    meeting_id                                   AS MeetingKey,
    series_title                                 AS SeriesTitle,
    title                                        AS Title,
    meeting_type                                 AS MeetingType,
    meeting_date                                 AS MeetingDate,
    meeting_mode                                 AS MeetingMode,
    COALESCE(occurred, FALSE)                    AS HasOccurred,
    last_distributed_event                       AS LastDistributedEvent,
    distributed_date                             AS DistributedDate,
    date_rank > 1                                AS IsDuplicateDate,
    minutes_on_time                              AS MinutesOnTime,
    agenda_on_time                               AS AgendaOnTime,
    -- A held meeting that met the standard as far as Procore can show: minutes on time,
    -- and the agenda on time or unverifiable (never a guessed FALSE).
    CASE WHEN date_rank = 1 AND meeting_date < CURRENT_DATE
              AND COALESCE(minutes_on_time, FALSE) AND COALESCE(agenda_on_time, TRUE)
         THEN TRUE ELSE FALSE END                AS IsCompliant,
    CASE WHEN agenda_on_time IS NULL AND last_distributed_event = 'minutes'
             THEN 'Not verifiable - minutes sent since'
         WHEN agenda_on_time THEN 'On time'
         WHEN agenda_on_time = FALSE AND last_distributed_event IS NULL THEN 'Never sent'
         WHEN agenda_on_time = FALSE THEN 'Late'
         ELSE 'Not yet due' END                  AS AgendaStatus,
    CASE WHEN minutes_on_time THEN 'On time'
         WHEN minutes_on_time = FALSE AND last_distributed_event = 'minutes' THEN 'Late'
         WHEN minutes_on_time = FALSE THEN 'Not sent'
         ELSE 'Not yet due' END                  AS MinutesStatus
FROM ranked;

-- ---------------------------------------------------------------------------
-- fct_ProjectTeam
-- ---------------------------------------------------------------------------
--
-- The deck's TEAM column: "Initials of: PM, APM, Super, Asst Super from Procore". Plus the
-- Project Executive - "only one throat to choke" - for the project page. Active directory
-- roles only, matched on Procore's role names exactly as they read on this tenant. Many
-- projects have only some of the four filled in (checked 2026-10-25); the dashboard shows
-- what Procore holds and never fills a gap.
CREATE OR REPLACE TABLE fct_ProjectTeam AS
SELECT
    project_id                                   AS ProjectKey,
    role_assignment_id                           AS RoleAssignmentKey,
    role_name                                    AS RoleName,
    CASE role_name WHEN 'Project Manager' THEN 'PM'
                   WHEN 'Assistant Project Manager' THEN 'APM'
                   WHEN 'Superintendent' THEN 'Super'
                   WHEN 'Assistant Superintendent' THEN 'Asst Super'
                   WHEN 'Project Executive' THEN 'PX' END AS RoleCode,
    CASE role_name WHEN 'Project Manager' THEN 1
                   WHEN 'Assistant Project Manager' THEN 2
                   WHEN 'Superintendent' THEN 3
                   WHEN 'Assistant Superintendent' THEN 4
                   WHEN 'Project Executive' THEN 5 END AS RoleOrder,
    member_name                                  AS MemberName
FROM sv_project_roles
WHERE project_id IS NOT NULL
  AND COALESCE(is_active, TRUE)
  AND role_name IN ('Project Manager', 'Assistant Project Manager', 'Superintendent',
                    'Assistant Superintendent', 'Project Executive');

-- ---------------------------------------------------------------------------
-- fct_ScheduleActivity
-- ---------------------------------------------------------------------------
--
-- Every activity on each project's CURRENT Outbuild schedule - not only the critical path
-- that fct_Milestone keeps - because the project page lists near-term milestones and recent
-- wins, most of which are not critical. 'project' rows are Outbuild's summary (WBS) bars:
-- kept, flagged IsSummary, and left out of the lists. UpdatedAt is a person's last edit,
-- the evidence for the "monthly schedule update" check.
CREATE OR REPLACE TABLE fct_ScheduleActivity AS
SELECT
    project_id                                   AS ProjectKey,
    activity_id                                  AS ActivityKey,
    TRIM(activity_name)                          AS ActivityName,
    activity_type                                AS ActivityType,
    COALESCE(activity_type = 'project', FALSE)   AS IsSummary,
    COALESCE(activity_type = 'milestone', FALSE) AS IsMilestone,
    start_date                                   AS StartDate,
    end_date                                     AS FinishDate,
    baseline_start_date                          AS BaselineStart,
    baseline_end_date                            AS BaselineFinish,
    progress                                     AS PercentComplete,
    -- Working days, Outbuild's own; weights the project's overall work progress.
    duration                                     AS DurationDays,
    COALESCE(is_critical, FALSE)                 AS IsCritical,
    COALESCE(progress, 0) >= 1                   AS IsComplete,
    CASE WHEN end_date IS NOT NULL AND baseline_end_date IS NOT NULL
         THEN datediff(end_date, baseline_end_date) END AS FinishVarianceDays,
    created_at                                   AS CreatedAt,
    updated_at                                   AS UpdatedAt
FROM sv_outbuild_activities
WHERE project_id IS NOT NULL
  AND is_current_schedule = TRUE;

-- ---------------------------------------------------------------------------
-- fct_LookaheadTask
-- ---------------------------------------------------------------------------
--
-- The look-ahead tasks on each project's current schedule, attributed to the project
-- through their parent activity. "3WLA going out once per week" is read from UpdatedAt /
-- CreatedAt: Outbuild keeps no history, so only "when was it last worked" is knowable, and
-- the dashboard scores it for the current week only. Legitimately empty for a project that
-- plans no look-ahead in Outbuild.
CREATE OR REPLACE TABLE fct_LookaheadTask AS
SELECT
    a.project_id                                 AS ProjectKey,
    t.task_id                                    AS TaskKey,
    t.activity_id                                AS ActivityKey,
    t.task_name                                  AS TaskName,
    t.start_date                                 AS StartDate,
    t.end_date                                   AS FinishDate,
    t.progress                                   AS PercentComplete,
    t.status                                     AS StatusLabel,
    COALESCE(t.is_weekly_commitment, FALSE)      AS IsWeeklyCommitment,
    t.created_at                                 AS CreatedAt,
    t.updated_at                                 AS UpdatedAt
FROM sv_outbuild_tasks t
JOIN sv_outbuild_activities a
  ON a.activity_id = t.activity_id
WHERE a.project_id IS NOT NULL
  AND a.is_current_schedule = TRUE;

-- ---------------------------------------------------------------------------
-- dim_ReportWeek
-- ---------------------------------------------------------------------------
--
-- The week slicer: Monday-Sunday weeks back a year from the week of the build. Labels are
-- RELATIVE ('This week', 'Last week'), so a slicer saved on 'Last week' still means last
-- week after tomorrow's rebuild - the call's "selection box that defaults to current".
-- 'Last week' is the default because the dashboard is read at Monday's stand-ups and
-- Tuesday's executive meeting, when this week has barely started. AsOfDate is the build
-- date: a measure evaluating "this week" stops there, not at a Sunday still to come.
-- Disconnected from every fact, like dim_ScorecardWeight: measures read the selected
-- window explicitly, so picking a week never filters a table it should not.
CREATE OR REPLACE TABLE dim_ReportWeek AS
WITH w AS (
    SELECT explode(sequence(0, 52, 1)) AS WeeksAgo
),
anchored AS (
    -- INT: sequence() yields BIGINT, and date_add takes an INT day count on both engines.
    SELECT CAST(WeeksAgo AS INT) AS WeeksAgo, CAST(date_trunc('WEEK', CURRENT_DATE) AS DATE) AS this_monday
    FROM w
)
SELECT
    WeeksAgo,
    date_add(this_monday, -7 * WeeksAgo)                         AS WeekStart,
    date_add(this_monday, 6 - 7 * WeeksAgo)                      AS WeekEnd,
    CASE WHEN WeeksAgo = 0 THEN 'This week'
         WHEN WeeksAgo = 1 THEN 'Last week'
         ELSE CONCAT('Week of ', CAST(date_add(this_monday, -7 * WeeksAgo) AS STRING)) END AS WeekLabel,
    CAST(-WeeksAgo AS INT)                                       AS WeekSort,
    CURRENT_DATE                                                 AS AsOfDate
FROM anchored;

-- ---------------------------------------------------------------------------
-- fct_ProjectPosition
-- ---------------------------------------------------------------------------
--
-- One row per project: where it stands as of this build - contract, billed, phase, the
-- Cash Position formula's six inputs, projected margin, AR ageing, last activity, status.
-- None of it moves with the report week, and every grade needs most of it, so it is worked
-- out ONCE here. As DAX measures the Portfolio table re-derived each project's contract
-- (a last-non-blank scan over 7,670 dates) and its billing several times per cell; the
-- service's query for that one table ran 26 seconds and then out of F2 memory (2026-10-25).
-- validate_dashboard recomputes every column from the raw facts and compares.
--
-- Definitions match the measures they replace:
--   CurrentContract / OriginalContract  the latest month with a value (fct_FinancialPeriod)
--   BilledToDateGross   Procore owner pay apps (gross of retainage), else Sage AR (net)
--   Phase               billed % of contract: < 10% Precon, > 95% Closeout (dim_DashSetting)
--   Cash...             Chris's formula; the Grade Detail page shows each step
--   ProjectedCost       forecast of every budget line except the FEE division (50)
--   ArOwed*             unpaid Sage AR, and its balance x days outstanding, for the weighted age
--   DashboardStatus     Archived once 100% paid; Active with Procore activity in 60 days
CREATE OR REPLACE TABLE fct_ProjectPosition AS
WITH settings AS (
    SELECT MAX(CASE WHEN SettingKey = 'phase_precon_below' THEN Value END)  AS precon_below,
           MAX(CASE WHEN SettingKey = 'phase_closeout_from' THEN Value END) AS closeout_from,
           MAX(CASE WHEN SettingKey = 'archive_paid_from' THEN Value END)   AS archive_from,
           MAX(CASE WHEN SettingKey = 'active_within_days' THEN Value END)  AS active_days
    FROM dim_DashSetting
),
projects AS (
    SELECT ProjectKey FROM dim_Project WHERE ProjectKey IS NOT NULL AND ProjectKey <> 'UNMATCHED'
),
contract_months AS (
    SELECT ProjectKey, MonthStart, SUM(CurrentContract) AS cur, SUM(OriginalContract) AS orig
    FROM fct_FinancialPeriod GROUP BY ProjectKey, MonthStart
),
cur AS (
    SELECT ProjectKey, cur FROM (
        SELECT ProjectKey, cur, ROW_NUMBER() OVER (PARTITION BY ProjectKey ORDER BY MonthStart DESC) AS rn
        FROM contract_months WHERE cur IS NOT NULL) x WHERE rn = 1
),
orig AS (
    SELECT ProjectKey, orig FROM (
        SELECT ProjectKey, orig, ROW_NUMBER() OVER (PARTITION BY ProjectKey ORDER BY MonthStart DESC) AS rn
        FROM contract_months WHERE orig IS NOT NULL) x WHERE rn = 1
),
owner AS (
    SELECT ProjectKey, SUM(CompletedToDate) AS billed, SUM(RetainageHeld) AS retainage
    FROM fct_Billing WHERE IsLatestPeriod = TRUE AND BillingType = 'Owner' GROUP BY ProjectKey
),
sub AS (
    SELECT ProjectKey, SUM(RetainageHeld) AS retainage
    FROM fct_Billing WHERE IsLatestApprovedPeriod = TRUE AND BillingType = 'Subcontractor' GROUP BY ProjectKey
),
ar AS (
    SELECT ProjectKey, SUM(Amount) AS billed, SUM(Balance) AS unpaid, SUM(AmountPaid) AS paid, COUNT(*) AS invoices,
           SUM(CASE WHEN Balance > 0 AND SentDate IS NOT NULL THEN Balance END) AS owed,
           SUM(CASE WHEN Balance > 0 AND SentDate IS NOT NULL
                    THEN Balance * datediff(CURRENT_DATE, SentDate) END) AS owed_days
    FROM fct_Invoice WHERE COALESCE(HasUnmatchedProject, FALSE) = FALSE GROUP BY ProjectKey
),
ap AS (
    SELECT ProjectKey, SUM(LineTotal * InvoiceBalance / InvoiceTotal) AS unpaid
    FROM fct_ApInvoice
    WHERE IsJobCost = TRUE AND ProjectKey IS NOT NULL AND COALESCE(InvoiceTotal, 0) <> 0
    GROUP BY ProjectKey
),
budget AS (
    SELECT b.ProjectKey, SUM(b.BudgetAmount) AS revenue, SUM(b.SpentToDate) AS spent,
           SUM(CASE WHEN COALESCE(x.NewDivisionCode, '') <> '50' THEN b.ForecastAmount END) AS cost
    FROM fct_BudgetLine b LEFT JOIN dim_CostCodeCrosswalk x ON x.CostCodeKey = b.CostCodeKey
    GROUP BY b.ProjectKey
),
activity AS (
    -- The latest sign of a working project in any Procore tool. A daily log alone missed
    -- City Harvest, which logs nothing but holds weekly OAC meetings.
    SELECT ProjectKey, MAX(d) AS last_activity FROM (
        SELECT ProjectKey, LastLogDate AS d FROM fct_SafetyMonthly
        UNION ALL SELECT ProjectKey, MeetingDate FROM fct_Meeting WHERE MeetingDate <= CURRENT_DATE
        UNION ALL SELECT ProjectKey, InspectionDate FROM fct_Inspection WHERE InspectionDate <= CURRENT_DATE
        UNION ALL SELECT ProjectKey, CreatedDate FROM fct_RfiSubmittal
        UNION ALL SELECT ProjectKey, CreatedDate FROM fct_QualityItem
    ) a GROUP BY ProjectKey
),
base AS (
    SELECT p.ProjectKey,
           cur.cur AS CurrentContract, orig.orig AS OriginalContract,
           CASE WHEN owner.billed IS NOT NULL AND owner.billed <> 0 THEN owner.billed ELSE ar.billed END AS BilledToDateGross,
           COALESCE(owner.retainage, 0) AS RetainageReceivable,
           COALESCE(ar.unpaid, 0) AS UnpaidReceivables,
           ar.paid AS PaidToDate,
           budget.spent AS CostsIncurred,
           COALESCE(ap.unpaid, 0) AS UnpaidPayables,
           COALESCE(sub.retainage, 0) AS RetainagePayable,
           budget.revenue AS ProjectedRevenue, budget.cost AS ProjectedCost,
           ar.owed AS ArOwedBalance, ar.owed_days AS ArOwedBalanceDays, COALESCE(ar.invoices, 0) AS InvoiceCount,
           activity.last_activity AS LastActivityDate
    FROM projects p
    LEFT JOIN cur ON cur.ProjectKey = p.ProjectKey
    LEFT JOIN orig ON orig.ProjectKey = p.ProjectKey
    LEFT JOIN owner ON owner.ProjectKey = p.ProjectKey
    LEFT JOIN sub ON sub.ProjectKey = p.ProjectKey
    LEFT JOIN ar ON ar.ProjectKey = p.ProjectKey
    LEFT JOIN ap ON ap.ProjectKey = p.ProjectKey
    LEFT JOIN budget ON budget.ProjectKey = p.ProjectKey
    LEFT JOIN activity ON activity.ProjectKey = p.ProjectKey
),
cash AS (
    SELECT b.*,
           CASE WHEN BilledToDateGross IS NOT NULL
                THEN BilledToDateGross - RetainageReceivable - UnpaidReceivables END AS CashCollected,
           CASE WHEN CostsIncurred IS NOT NULL
                THEN CostsIncurred - UnpaidPayables - RetainagePayable END AS CashPaidOut,
           CASE WHEN COALESCE(CurrentContract, 0) <> 0 THEN BilledToDateGross / CurrentContract END AS BilledPct
    FROM base b
)
SELECT c.*,
       CASE WHEN c.BilledPct IS NULL THEN NULL
            WHEN c.BilledPct < s.precon_below THEN 'Precon'
            WHEN c.BilledPct > s.closeout_from THEN 'Closeout'
            ELSE 'Construction' END AS Phase,
       CASE WHEN COALESCE(c.CurrentContract, 0) <> 0 AND c.CashCollected / c.CurrentContract >= s.archive_from THEN 'Archived'
            WHEN c.LastActivityDate IS NOT NULL AND datediff(CURRENT_DATE, c.LastActivityDate) <= s.active_days THEN 'Active'
            ELSE 'Inactive' END AS DashboardStatus
FROM cash c CROSS JOIN settings s;
