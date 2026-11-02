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
-- PERFORMED = CLOSED (Oct 30 call). An inspection is "not really done until it is distributed
-- or the status is closed": one created and half filled in showed up as performed on the
-- dashboard. Items answered on an OPEN inspection now read IsInProgress - listed on the
-- drill-down, never counted. The reporting-week window is applied in the score.
--
-- PASS RATE (Oct 30 call, the next layer of the safety score): conforming items over
-- conforming + deficient - "60 passes and 27 fails". N/A and neutral items are left out of
-- both sides. Collected and shown; not in the grade until Affect agrees how to weight it.
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
    i.ConformingItemCount                        AS PassItemCount,
    i.NotApplicableItemCount                     AS NaItemCount,
    CASE WHEN COALESCE(i.ConformingItemCount, 0) + COALESCE(i.DeficientItemCount, 0) > 0
         THEN CAST(COALESCE(i.ConformingItemCount, 0) AS DOUBLE)
              / (COALESCE(i.ConformingItemCount, 0) + COALESCE(i.DeficientItemCount, 0)) END AS PassRate,
    UPPER(COALESCE(i.SourceStatus, '')) = 'CLOSED' AS IsPerformed,
    UPPER(COALESCE(i.SourceStatus, '')) <> 'CLOSED'
        AND COALESCE(i.ConformingItemCount, 0) + COALESCE(i.DeficientItemCount, 0)
            + COALESCE(i.NotApplicableItemCount, 0) + COALESCE(i.NeutralItemCount, 0) > 0 AS IsInProgress,
    -- Why the row does or does not count, in words, for the drill-down.
    CASE WHEN COALESCE(m.Category, 'Unclassified') = 'Unclassified'
             THEN 'Not counted - template matches no safety / quality pattern'
         WHEN UPPER(COALESCE(i.SourceStatus, '')) = 'CLOSED' THEN 'Counted - closed'
         WHEN COALESCE(i.ConformingItemCount, 0) + COALESCE(i.DeficientItemCount, 0)
              + COALESCE(i.NotApplicableItemCount, 0) + COALESCE(i.NeutralItemCount, 0) > 0
             THEN 'Not counted - started, not closed'
         ELSE 'Not counted - created, not started' END AS CountedReason
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
                -- Due by the end of the day after: not late until that day has passed.
                WHEN date_add(t.meeting_date, 1) < CURRENT_DATE THEN FALSE END AS minutes_on_time,
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
         ELSE CONCAT('Week of ', date_format(date_add(this_monday, -7 * WeeksAgo), 'MM/dd/yy')) END AS WeekLabel,
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
--   Phase               Cal's Oct 30 notes: from the Outbuild schedule - 95% of its tasks
--                       complete = Closeout (phase_closeout_tasks); else the construction-start
--                       milestone reached = Construction, not yet = Precon (seed_PhaseMilestone);
--                       no schedule = billed %. PhaseSource says which, in words.
--   DashboardStatus     Archived once 100% paid. With rollout_only = 1 (Oct 30 call) only the
--                       projects in seed_DashProject are Active; the rest are Archived, with
--                       StatusReason. With 0: Active = Procore activity in 60 days.
-- Sage voids never reach these sums: fct_Invoice zeroes them, AP readers drop IsVoid.
CREATE OR REPLACE TABLE fct_ProjectPosition AS
WITH settings AS (
    SELECT MAX(CASE WHEN SettingKey = 'phase_precon_below' THEN Value END)  AS precon_below,
           MAX(CASE WHEN SettingKey = 'phase_closeout_from' THEN Value END) AS closeout_from,
           MAX(CASE WHEN SettingKey = 'phase_closeout_tasks' THEN Value END) AS closeout_tasks,
           MAX(CASE WHEN SettingKey = 'archive_paid_from' THEN Value END)   AS archive_from,
           MAX(CASE WHEN SettingKey = 'active_within_days' THEN Value END)  AS active_days,
           MAX(CASE WHEN SettingKey = 'ar_aged_days' THEN Value END)        AS aged_days,
           COALESCE(MAX(CASE WHEN SettingKey = 'rollout_only' THEN Value END), 0) AS rollout_only
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
    SELECT ProjectKey, SUM(CompletedToDate) AS billed, SUM(RetainageHeld) AS retainage,
           SUM(EarnedLessRetainageToDate) AS earned_net, COUNT(*) AS contracts
    FROM fct_Billing WHERE IsLatestPeriod = TRUE AND BillingType = 'Owner' GROUP BY ProjectKey
),
sub AS (
    SELECT ProjectKey, SUM(RetainageHeld) AS retainage
    FROM fct_Billing WHERE IsLatestApprovedPeriod = TRUE AND BillingType = 'Subcontractor' GROUP BY ProjectKey
),
ar AS (
    SELECT i.ProjectKey, SUM(i.Amount) AS billed, SUM(i.Balance) AS unpaid, SUM(i.AmountPaid) AS paid,
           SUM(CASE WHEN i.IsVoid THEN 0 ELSE 1 END) AS invoices,
           SUM(CASE WHEN i.Balance > 0 AND i.SentDate IS NOT NULL THEN i.Balance END) AS owed,
           SUM(CASE WHEN i.Balance > 0 AND i.SentDate IS NOT NULL
                    THEN i.Balance * datediff(CURRENT_DATE, i.SentDate) END) AS owed_days,
           SUM(CASE WHEN i.Balance > 0 AND datediff(CURRENT_DATE, i.SentDate) > s.aged_days THEN i.Balance END) AS over60,
           SUM(i.VoidedAmount) AS voided, SUM(CASE WHEN i.IsVoid THEN 1 ELSE 0 END) AS voids
    FROM fct_Invoice i CROSS JOIN settings s
    WHERE COALESCE(i.HasUnmatchedProject, FALSE) = FALSE GROUP BY i.ProjectKey
),
ap AS (
    SELECT ProjectKey, SUM(LineTotal * InvoiceBalance / InvoiceTotal) AS unpaid
    FROM fct_ApInvoice
    WHERE IsJobCost = TRUE AND NOT IsVoid AND ProjectKey IS NOT NULL AND COALESCE(InvoiceTotal, 0) <> 0
    GROUP BY ProjectKey
),
budget AS (
    SELECT b.ProjectKey, SUM(b.BudgetAmount) AS revenue, SUM(b.SpentToDate) AS spent,
           SUM(CASE WHEN COALESCE(x.NewDivisionCode, '') <> '50' THEN b.ForecastAmount END) AS cost,
           SUM(CASE WHEN COALESCE(x.NewDivisionCode, '') = '50' THEN b.ForecastAmount END) AS fee
    FROM fct_BudgetLine b LEFT JOIN dim_CostCodeCrosswalk x ON x.CostCodeKey = b.CostCodeKey
    GROUP BY b.ProjectKey
),
activity AS (
    -- The latest sign of a working project in any Procore tool. A daily log alone missed
    -- City Harvest, which logs nothing but holds weekly OAC meetings.
    SELECT ProjectKey, MAX(d) AS last_activity FROM (
        SELECT ProjectKey, LastLogDate AS d FROM fct_SafetyMonthly
        -- Held OAC / trade partner meetings only: a template or test series is not a working job.
        UNION ALL SELECT ProjectKey, MeetingDate FROM fct_Meeting
                  WHERE MeetingDate <= CURRENT_DATE AND HasOccurred AND MeetingType IN ('OAC', 'Trade Partner')
        UNION ALL SELECT ProjectKey, InspectionDate FROM fct_Inspection WHERE InspectionDate <= CURRENT_DATE
        UNION ALL SELECT ProjectKey, CreatedDate FROM fct_RfiSubmittal
        UNION ALL SELECT ProjectKey, CreatedDate FROM fct_QualityItem
    ) a GROUP BY ProjectKey
),
-- Phase milestones: each Outbuild milestone classified by the first seed pattern it contains.
ms AS (
    SELECT a.ProjectKey, a.ActivityName, a.FinishDate, c.Marks, c.Priority,
           COALESCE(a.PercentComplete, 0) >= 1 OR a.FinishDate <= CURRENT_DATE AS reached,
           ROW_NUMBER() OVER (PARTITION BY a.ProjectKey, a.ActivityKey ORDER BY c.Priority) AS rn
    FROM fct_ScheduleActivity a
    JOIN seed_PhaseMilestone c ON LOWER(a.ActivityName) LIKE CONCAT('%', c.Pattern, '%')
    WHERE a.IsMilestone AND a.FinishDate IS NOT NULL
),
tasks AS (
    -- The schedule's tasks: every activity but the summary bars and the milestones.
    SELECT ProjectKey, COUNT(*) AS n, SUM(CASE WHEN IsComplete THEN 1 ELSE 0 END) AS done
    FROM fct_ScheduleActivity WHERE NOT IsSummary AND NOT IsMilestone GROUP BY ProjectKey
),
start AS (
    -- The construction-start milestone, of the best-named kind (lowest priority): any of them
    -- reached = construction (the latest reached is named); none reached = the next one due.
    -- City Harvest's schedule re-dates its work-start trigger rather than closing it.
    SELECT ProjectKey, ActivityName, FinishDate, reached FROM (
        SELECT b.*, ROW_NUMBER() OVER (PARTITION BY ProjectKey
                                       ORDER BY CASE WHEN reached THEN 0 ELSE 1 END,
                                                CASE WHEN reached THEN datediff(CURRENT_DATE, FinishDate) END,
                                                FinishDate, ActivityName) AS k
        FROM (SELECT ms.*, MIN(Priority) OVER (PARTITION BY ProjectKey) AS best
              FROM ms WHERE rn = 1 AND Marks = 'Construction') b
        WHERE Priority = best) x WHERE k = 1
),
base AS (
    SELECT p.ProjectKey,
           cur.cur AS CurrentContract, orig.orig AS OriginalContract,
           CASE WHEN owner.billed IS NOT NULL AND owner.billed <> 0 THEN owner.billed ELSE ar.billed END AS BilledToDateGross,
           CASE WHEN owner.billed IS NOT NULL AND owner.billed <> 0 THEN 'Procore owner pay apps (gross of retainage)'
                WHEN ar.billed IS NOT NULL THEN 'Sage AR invoices (no Procore pay app)' END AS BillingSource,
           owner.earned_net AS ProcoreEarnedLessRetainage, owner.contracts AS PrimeContractCount,
           ar.billed AS SageInvoicedToDate,
           COALESCE(owner.retainage, 0) AS RetainageReceivable,
           COALESCE(ar.unpaid, 0) AS UnpaidReceivables,
           ar.paid AS PaidToDate,
           budget.spent AS CostsIncurred,
           COALESCE(ap.unpaid, 0) AS UnpaidPayables,
           COALESCE(sub.retainage, 0) AS RetainagePayable,
           budget.revenue AS ProjectedRevenue, budget.cost AS ProjectedCost, budget.fee AS ProjectedFee,
           ar.owed AS ArOwedBalance, ar.owed_days AS ArOwedBalanceDays, COALESCE(ar.invoices, 0) AS InvoiceCount,
           COALESCE(ar.over60, 0) AS ArOver60, COALESCE(ar.voided, 0) AS VoidedInvoiceAmount,
           COALESCE(ar.voids, 0) AS VoidedInvoiceCount,
           activity.last_activity AS LastActivityDate,
           tasks.n AS task_n, tasks.done AS task_done,
           start.ActivityName AS start_name, start.FinishDate AS start_date, start.reached AS start_reached,
           dp.ProcoreProjectId IS NOT NULL AS IsRolloutProject
    FROM projects p
    LEFT JOIN cur ON cur.ProjectKey = p.ProjectKey
    LEFT JOIN orig ON orig.ProjectKey = p.ProjectKey
    LEFT JOIN owner ON owner.ProjectKey = p.ProjectKey
    LEFT JOIN sub ON sub.ProjectKey = p.ProjectKey
    LEFT JOIN ar ON ar.ProjectKey = p.ProjectKey
    LEFT JOIN ap ON ap.ProjectKey = p.ProjectKey
    LEFT JOIN budget ON budget.ProjectKey = p.ProjectKey
    LEFT JOIN activity ON activity.ProjectKey = p.ProjectKey
    LEFT JOIN tasks ON tasks.ProjectKey = p.ProjectKey
    LEFT JOIN start ON start.ProjectKey = p.ProjectKey
    LEFT JOIN seed_DashProject dp ON dp.ProcoreProjectId = p.ProjectKey
),
cash AS (
    SELECT b.*,
           CASE WHEN BilledToDateGross IS NOT NULL
                THEN BilledToDateGross - RetainageReceivable - UnpaidReceivables END AS CashCollected,
           CASE WHEN CostsIncurred IS NOT NULL
                THEN CostsIncurred - UnpaidPayables - RetainagePayable END AS CashPaidOut,
           CASE WHEN COALESCE(CurrentContract, 0) <> 0 THEN BilledToDateGross / CurrentContract END AS BilledPct
    FROM base b
),
phased AS (
    SELECT c.*,
           CASE WHEN c.task_done >= s.closeout_tasks * c.task_n THEN 'Closeout'
                WHEN c.start_name IS NOT NULL THEN CASE WHEN c.start_reached THEN 'Construction' ELSE 'Precon' END
                WHEN c.task_n > 0 THEN 'Construction'
                WHEN c.BilledPct IS NULL THEN NULL
                WHEN c.BilledPct < s.precon_below THEN 'Precon'
                WHEN c.BilledPct > s.closeout_from THEN 'Closeout'
                ELSE 'Construction' END AS Phase,
           CASE WHEN c.task_done >= s.closeout_tasks * c.task_n
                    THEN CONCAT('Outbuild: ', CAST(c.task_done AS STRING), ' of ', CAST(c.task_n AS STRING),
                                ' tasks complete (', CAST(CAST(ROUND(100 * s.closeout_tasks, 0) AS INT) AS STRING), '% = closeout)')
                WHEN c.start_name IS NOT NULL
                    THEN CONCAT('Outbuild: "', c.start_name, '" ',
                                CASE WHEN c.start_reached THEN 'reached ' ELSE 'due ' END,
                                date_format(c.start_date, 'MM/dd/yy'), '; ',
                                CAST(COALESCE(c.task_done, 0) AS STRING), ' of ', CAST(COALESCE(c.task_n, 0) AS STRING), ' tasks complete')
                WHEN c.task_n > 0
                    THEN CONCAT('Outbuild: no construction-start milestone; ', CAST(c.task_done AS STRING), ' of ',
                                CAST(c.task_n AS STRING), ' tasks complete')
                WHEN c.BilledPct IS NULL THEN 'No contract or billing, and no Outbuild phase milestone'
                ELSE CONCAT('Billed ', CAST(ROUND(100 * c.BilledPct, 1) AS STRING),
                            '% of contract (no Outbuild phase milestone)') END AS PhaseSource,
           s.archive_from, s.active_days, s.rollout_only
    FROM cash c CROSS JOIN settings s
)
SELECT ProjectKey, CurrentContract, OriginalContract, BilledToDateGross, BillingSource, ProcoreEarnedLessRetainage,
       PrimeContractCount, SageInvoicedToDate, RetainageReceivable, UnpaidReceivables, PaidToDate, CostsIncurred,
       UnpaidPayables, RetainagePayable, ProjectedRevenue, ProjectedCost, ProjectedFee, ArOwedBalance,
       ArOwedBalanceDays, InvoiceCount, ArOver60, VoidedInvoiceAmount, VoidedInvoiceCount, LastActivityDate,
       IsRolloutProject, CashCollected, CashPaidOut, BilledPct, Phase, PhaseSource,
       CASE WHEN COALESCE(CurrentContract, 0) <> 0 AND CashCollected / CurrentContract >= archive_from THEN 'Archived'
            WHEN rollout_only = 1 AND IsRolloutProject THEN 'Active'
            WHEN rollout_only = 1 THEN 'Archived'
            WHEN LastActivityDate IS NOT NULL AND datediff(CURRENT_DATE, LastActivityDate) <= active_days THEN 'Active'
            ELSE 'Inactive' END AS DashboardStatus,
       CASE WHEN COALESCE(CurrentContract, 0) <> 0 AND CashCollected / CurrentContract >= archive_from
                THEN '100% paid'
            WHEN rollout_only = 1 AND IsRolloutProject THEN 'In the Nov 19 rollout (Oct 30 call)'
            WHEN rollout_only = 1 THEN 'Not in the Nov 19 rollout (Oct 30 call)'
            WHEN LastActivityDate IS NOT NULL AND datediff(CURRENT_DATE, LastActivityDate) <= active_days
                THEN 'Procore activity in the last 60 days'
            ELSE 'No Procore activity in the last 60 days' END AS StatusReason
FROM phased;

-- ---------------------------------------------------------------------------
-- fct_DashObservation
-- ---------------------------------------------------------------------------
--
-- Oct 30 call: keep the inspection count as the score, and beside it "capture all these safety
-- data points" - observations, notices, near misses, corrective actions, punch - so a grading
-- can be agreed from real data. Procore observations and punch items (fct_QualityItem),
-- classified Safety / Quality by category (seed_ObservationCategory); anything unmatched is
-- Quality, the tool's default use here. Read by the drill-down and the PROPOSED data scores.
-- Cal's Oct 30 notes list them as Procore shows them, "Safety - Near Miss": Procore's own
-- category decides first (safety = Safety; quality, commissioning, environmental, warranty,
-- work to complete = Quality), the seed patterns after. Incidents (OSHA recordable or not)
-- are Safety.
CREATE OR REPLACE TABLE fct_DashObservation AS
WITH matched AS (
    SELECT q.ProjectKey, q.ItemType, q.ItemKey, c.Category,
           ROW_NUMBER() OVER (PARTITION BY q.ProjectKey, q.ItemType, q.ItemKey ORDER BY c.Priority) AS rn
    FROM fct_QualityItem q
    JOIN seed_ObservationCategory c
      ON LOWER(CONCAT(COALESCE(q.ItemCategory, ''), ' ', COALESCE(q.Title, ''))) LIKE CONCAT('%', c.Pattern, '%')
)
SELECT q.ProjectKey,
       CONCAT(q.ItemType, ':', CAST(q.ItemKey AS STRING)) AS ObservationKey,
       q.ItemTypeLabel                         AS ItemType,
       q.ItemNumber, q.Title,
       CASE WHEN o.observation_category IS NOT NULL
            THEN CONCAT(initcap(REPLACE(o.observation_category, '_', ' ')), ' - ', COALESCE(q.ItemCategory, '(no type)'))
            ELSE COALESCE(q.ItemCategory, '(no category)') END AS ProcoreCategory,
       CASE WHEN LOWER(o.observation_category) = 'safety' THEN 'Safety'
            ELSE COALESCE(m.Category, 'Quality') END AS Category,
       q.StatusLabel, q.IsOpen, q.CreatedDate, q.DueDate, q.ClosedDate, q.DaysOpen, q.IsPastDue,
       q.AssignedTo
FROM fct_QualityItem q
LEFT JOIN matched m ON m.ProjectKey = q.ProjectKey AND m.ItemType = q.ItemType AND m.ItemKey = q.ItemKey AND m.rn = 1
LEFT JOIN sv_observations o ON q.ItemType = 'Observation' AND o.observation_id = q.ItemKey
WHERE q.ProjectKey IS NOT NULL
UNION ALL
SELECT project_id, CONCAT('Incident:', incident_id), 'Incident', CAST(NULL AS STRING), title,
       CASE WHEN is_recordable THEN 'Incident - OSHA recordable' ELSE 'Incident' END, 'Safety',
       status_label, UPPER(COALESCE(status_label, '')) <> 'CLOSED', event_date, CAST(NULL AS DATE),
       CAST(NULL AS DATE), datediff(CURRENT_DATE, event_date), FALSE, 'UNASSIGNED'
FROM sv_incidents
WHERE project_id IS NOT NULL;

-- ---------------------------------------------------------------------------
-- fct_SubPayment
-- ---------------------------------------------------------------------------
--
-- Oct 30 call: "have we been paid, has this subcontractor been paid" - asked all the time and
-- 30 minutes to answer. One row per project and subcontractor: what they are committed (their
-- latest approved Procore requisition's contract sum), what they have requisitioned and what is
-- held as retainage, then Sage AP for the same vendor on the job - invoiced, paid, still owed,
-- and how old the oldest unpaid invoice is. A vendor with Sage AP but no Procore requisition
-- is still listed (Requisitioned blank), so nothing paid goes unseen. Voids excluded.
CREATE OR REPLACE TABLE fct_SubPayment AS
WITH req AS (
    SELECT ProjectKey, VendorKey, MAX(CounterpartyName) AS SubName,
           MAX(ContractName) AS ContractName, COUNT(*) AS Commitments,
           SUM(ContractSumToDate) AS Committed, SUM(CompletedToDate) AS Requisitioned,
           SUM(RetainageHeld) AS RetainageHeld, SUM(BalanceToFinish) AS BalanceToFinish,
           MAX(BillingDate) AS LastRequisitionDate
    FROM fct_Billing
    WHERE BillingType = 'Subcontractor' AND IsLatestApprovedPeriod = TRUE AND ProjectKey IS NOT NULL
    GROUP BY ProjectKey, VendorKey
),
ap AS (
    SELECT ProjectKey, VendorKey,
           SUM(LineTotal) AS ApInvoiced,
           SUM(CASE WHEN COALESCE(InvoiceTotal, 0) <> 0 THEN LineTotal * AmountPaid / InvoiceTotal END) AS ApPaid,
           SUM(CASE WHEN COALESCE(InvoiceTotal, 0) <> 0 THEN LineTotal * InvoiceBalance / InvoiceTotal END) AS ApOpen,
           MAX(CASE WHEN InvoiceBalance > 0 THEN datediff(CURRENT_DATE, InvoiceDate) END) AS OldestOpenDays,
           COUNT(DISTINCT InvoiceKey) AS ApInvoices,
           COUNT(DISTINCT CASE WHEN InvoiceBalance > 0 THEN InvoiceKey END) AS ApOpenInvoices,
           MAX(InvoiceDate) AS LastApInvoiceDate
    FROM fct_ApInvoice
    WHERE IsJobCost = TRUE AND NOT IsVoid AND ProjectKey IS NOT NULL
    GROUP BY ProjectKey, VendorKey
),
com AS (
    -- Cal's Project Financials sheet, TOTAL COMMITTED COST: every approved Procore commitment
    -- (subcontract or purchase order), billed against or not. A requisition's contract sum is
    -- used where there is one, because it includes the approved commitment change orders that
    -- the commitment's own total does not.
    SELECT project_id AS ProjectKey, vendor_id AS VendorKey, MAX(vendor_name) AS VendorName,
           SUM(grand_total) AS Committed, COUNT(*) AS Commitments
    FROM sv_commitments
    WHERE project_id IS NOT NULL AND UPPER(status_label) IN ('APPROVED', 'COMPLETE', 'CLOSED')
    GROUP BY project_id, vendor_id
),
k AS (
    SELECT ProjectKey, VendorKey FROM req UNION SELECT ProjectKey, VendorKey FROM ap
    UNION SELECT ProjectKey, VendorKey FROM com
)
SELECT k.ProjectKey,
       CONCAT(k.ProjectKey, ':', COALESCE(k.VendorKey, '?'))     AS SubPaymentKey,
       k.VendorKey,
       CASE WHEN k.VendorKey = 'UNASSIGNED' THEN 'Sage vendors with no Procore match (combined)'
            ELSE COALESCE(r.SubName, v.VendorName, c.VendorName, k.VendorKey) END AS SubName,
       r.ContractName, r.Commitments, r.Committed, r.Requisitioned, r.RetainageHeld, r.BalanceToFinish,
       r.LastRequisitionDate,
       a.ApInvoiced, a.ApPaid, a.ApOpen, a.ApInvoices, COALESCE(a.ApOpenInvoices, 0) AS ApOpenInvoices,
       a.LastApInvoiceDate, a.OldestOpenDays,
       c.Committed AS CommitmentTotal,
       COALESCE(r.Committed, c.Committed)                       AS TotalCommitted,
       CASE WHEN a.OldestOpenDays IS NULL THEN 'Nothing owed'
            WHEN a.OldestOpenDays <= 30 THEN '0-30 days'
            WHEN a.OldestOpenDays <= 60 THEN '31-60 days'
            WHEN a.OldestOpenDays <= 90 THEN '61-90 days'
            ELSE 'Over 90 days' END                              AS OpenApAge,
       CASE WHEN r.Committed IS NOT NULL THEN r.Committed - COALESCE(a.ApPaid, 0) END AS LeftToPay,
       CASE WHEN r.ProjectKey IS NULL AND a.ProjectKey IS NULL THEN 'Procore commitment - nothing billed yet'
            WHEN r.ProjectKey IS NULL AND c.ProjectKey IS NULL THEN 'Sage AP only - no Procore commitment'
            WHEN r.ProjectKey IS NULL THEN 'Procore commitment and Sage AP - no requisition'
            WHEN a.ProjectKey IS NULL THEN 'Procore requisition - no Sage AP yet'
            ELSE 'Procore and Sage' END                          AS Source
FROM k
LEFT JOIN req r ON r.ProjectKey = k.ProjectKey AND COALESCE(r.VendorKey, '?') = COALESCE(k.VendorKey, '?')
LEFT JOIN ap a ON a.ProjectKey = k.ProjectKey AND COALESCE(a.VendorKey, '?') = COALESCE(k.VendorKey, '?')
LEFT JOIN com c ON c.ProjectKey = k.ProjectKey AND COALESCE(c.VendorKey, '?') = COALESCE(k.VendorKey, '?')
LEFT JOIN dim_Vendor v ON v.VendorKey = k.VendorKey;

-- ---------------------------------------------------------------------------
-- fct_DashCheck
-- ---------------------------------------------------------------------------
--
-- Oct 30 call: "less validation of the data, more validation of the input" - a check that runs
-- with every build and says, project by project, where the systems disagree or the source has
-- not been kept up, so "the data is wrong" becomes "this entry was not made". One row per
-- project and check: Pass / Warn, the number behind it, and what to do.
CREATE OR REPLACE TABLE fct_DashCheck AS
WITH s AS (
    SELECT COALESCE(MAX(CASE WHEN SettingKey = 'tieout_tolerance' THEN Value END), 0.01) AS tol,
           MAX(CASE WHEN SettingKey = 'sage_closed_through' THEN Value END) AS closed
    FROM dim_DashSetting
),
dash AS (
    SELECT p.ProjectKey, p.DashboardStatus, p.ProcoreEarnedLessRetainage, p.SageInvoicedToDate,
           p.VoidedInvoiceAmount, p.VoidedInvoiceCount, p.ProjectedCost, p.CurrentContract
    FROM fct_ProjectPosition p
),
dup AS (
    -- Two live invoices on one job for the same amount in the same month: a re-issue left beside
    -- its original. n and amt are the extra copies only, not the original.
    SELECT ProjectKey, SUM(c - 1) AS n, SUM((c - 1) * Amount) AS amt FROM (
        SELECT ProjectKey, SageJobNumber, MonthStart, Amount, COUNT(*) AS c
        FROM fct_Invoice WHERE NOT IsVoid AND Amount <> 0
        GROUP BY ProjectKey, SageJobNumber, MonthStart, Amount) x
    WHERE c > 1 GROUP BY ProjectKey
),
old_ar AS (
    SELECT ProjectKey, COUNT(*) AS n, SUM(Balance) AS amt FROM fct_Invoice
    WHERE Balance > 0 AND datediff(CURRENT_DATE, SentDate) > 90 GROUP BY ProjectKey
),
la AS (
    SELECT a.ProjectKey, t.last_worked
    FROM (SELECT DISTINCT ProjectKey FROM fct_ScheduleActivity) a
    LEFT JOIN (SELECT ProjectKey, greatest(MAX(UpdatedAt), MAX(CreatedAt)) AS last_worked
               FROM fct_LookaheadTask GROUP BY ProjectKey) t ON t.ProjectKey = a.ProjectKey
),
stale AS (
    -- Activities whose forecast finish has passed with progress not marked complete.
    SELECT ProjectKey, COUNT(*) AS n FROM fct_ScheduleActivity
    WHERE NOT IsSummary AND NOT IsComplete AND FinishDate < CURRENT_DATE GROUP BY ProjectKey
),
insp AS (
    SELECT ProjectKey, COUNT(*) AS n FROM fct_Inspection
    WHERE NOT IsPerformed AND InspectionDate < date_add(CURRENT_DATE, -7) GROUP BY ProjectKey
),
team AS (
    SELECT ProjectKey, MAX(CASE WHEN RoleCode = 'PM' THEN 1 ELSE 0 END) AS pm,
           MAX(CASE WHEN RoleCode = 'Super' THEN 1 ELSE 0 END) AS super
    FROM fct_ProjectTeam GROUP BY ProjectKey
),
checks AS (
    SELECT d.ProjectKey, 1 AS CheckOrder, 'Sage vs Procore billing' AS CheckName,
           CASE WHEN d.ProcoreEarnedLessRetainage IS NULL OR d.SageInvoicedToDate IS NULL THEN 'Info'
                WHEN ABS(d.SageInvoicedToDate - d.ProcoreEarnedLessRetainage)
                     <= s.tol * GREATEST(ABS(d.ProcoreEarnedLessRetainage), 1) THEN 'Pass' ELSE 'Warn' END AS Result,
           d.SageInvoicedToDate - d.ProcoreEarnedLessRetainage AS Amount,
           CASE WHEN d.ProcoreEarnedLessRetainage IS NULL THEN 'No Procore owner pay app to compare'
                WHEN d.SageInvoicedToDate IS NULL THEN 'No Sage AR invoice on this job'
                ELSE CONCAT('Sage invoiced ', CAST(CAST(ROUND(d.SageInvoicedToDate, 0) AS BIGINT) AS STRING), ' vs Procore earned less retainage ',
                            CAST(CAST(ROUND(d.ProcoreEarnedLessRetainage, 0) AS BIGINT) AS STRING)) END AS Detail,
           'Finance: Sage and Procore should tie out; post or void the difference' AS Action
    FROM dash d CROSS JOIN s
    UNION ALL
    SELECT d.ProjectKey, 2, 'Voided Sage invoices',
           CASE WHEN d.VoidedInvoiceCount > 0 THEN 'Info' ELSE 'Pass' END, d.VoidedInvoiceAmount,
           CONCAT(CAST(d.VoidedInvoiceCount AS STRING), ' void invoice(s) left out of revenue and AR'),
           'None - shown so the totals tie to Sage reports that exclude voids'
    FROM dash d
    UNION ALL
    SELECT d.ProjectKey, 3, 'Possible duplicate invoices',
           CASE WHEN COALESCE(u.n, 0) > 0 THEN 'Warn' ELSE 'Pass' END, u.amt,
           CONCAT(CAST(COALESCE(u.n, 0) AS STRING), ' extra live invoice(s) with the same job, amount and month as another'),
           'Finance: void the copy in Sage if it is a re-issue'
    FROM dash d LEFT JOIN dup u ON u.ProjectKey = d.ProjectKey
    UNION ALL
    SELECT d.ProjectKey, 4, 'AR over 90 days',
           CASE WHEN COALESCE(o.n, 0) > 0 THEN 'Warn' ELSE 'Pass' END, o.amt,
           CONCAT(CAST(COALESCE(o.n, 0) AS STRING), ' open invoice(s) older than 90 days'),
           'Finance: collect, or write off / void old AR that will not be paid'
    FROM dash d LEFT JOIN old_ar o ON o.ProjectKey = d.ProjectKey
    UNION ALL
    SELECT d.ProjectKey, 5, '3-week look-ahead updated',
           CASE WHEN l.ProjectKey IS NULL THEN 'Info'
                WHEN l.last_worked IS NULL OR datediff(CURRENT_DATE, CAST(l.last_worked AS DATE)) > 7 THEN 'Warn'
                ELSE 'Pass' END,
           CAST(datediff(CURRENT_DATE, CAST(l.last_worked AS DATE)) AS DOUBLE),
           CASE WHEN l.ProjectKey IS NULL THEN 'Project not linked to Outbuild'
                WHEN l.last_worked IS NULL THEN 'No look-ahead tasks in Outbuild'
                ELSE CONCAT('Last worked ', CAST(datediff(CURRENT_DATE, CAST(l.last_worked AS DATE)) AS STRING), ' days ago') END,
           'Field: update the Outbuild look-ahead every week'
    FROM dash d LEFT JOIN la l ON l.ProjectKey = d.ProjectKey
    UNION ALL
    SELECT d.ProjectKey, 6, 'Schedule progress kept up',
           CASE WHEN COALESCE(t.n, 0) > 0 THEN 'Warn' ELSE 'Pass' END, CAST(COALESCE(t.n, 0) AS DOUBLE),
           CONCAT(CAST(COALESCE(t.n, 0) AS STRING), ' activities past their finish date and not marked 100%'),
           'Field: mark progress in Outbuild, or re-forecast the finish'
    FROM dash d LEFT JOIN stale t ON t.ProjectKey = d.ProjectKey
    UNION ALL
    SELECT d.ProjectKey, 7, 'Inspections closed',
           CASE WHEN COALESCE(i.n, 0) > 0 THEN 'Warn' ELSE 'Pass' END, CAST(COALESCE(i.n, 0) AS DOUBLE),
           CONCAT(CAST(COALESCE(i.n, 0) AS STRING), ' inspection(s) dated over a week ago and still not closed - not counted'),
           'Field: finish and close the inspection in Procore'
    FROM dash d LEFT JOIN insp i ON i.ProjectKey = d.ProjectKey
    UNION ALL
    SELECT d.ProjectKey, 8, 'Team roles in Procore',
           CASE WHEN COALESCE(m.pm, 0) = 1 AND COALESCE(m.super, 0) = 1 THEN 'Pass' ELSE 'Warn' END, CAST(NULL AS DOUBLE),
           CASE WHEN COALESCE(m.pm, 0) = 1 AND COALESCE(m.super, 0) = 1 THEN 'PM and Superintendent set'
                ELSE CONCAT('Missing: ', concat_ws(', ', CASE WHEN COALESCE(m.pm, 0) = 0 THEN 'Project Manager' END,
                                                     CASE WHEN COALESCE(m.super, 0) = 0 THEN 'Superintendent' END)) END,
           'PM: set the roles in the Procore directory'
    FROM dash d LEFT JOIN team m ON m.ProjectKey = d.ProjectKey
    UNION ALL
    SELECT d.ProjectKey, 9, 'Budget forecast in Procore',
           CASE WHEN d.ProjectedCost IS NULL THEN 'Warn' ELSE 'Pass' END, d.ProjectedCost,
           CASE WHEN d.ProjectedCost IS NULL THEN 'No forecast to complete - margin and on-budget cannot be read'
                ELSE 'Forecast present' END,
           'PM / QS: keep the Procore budget forecast current'
    FROM dash d
)
SELECT c.ProjectKey, CONCAT(c.ProjectKey, ':', CAST(c.CheckOrder AS STRING)) AS CheckKey,
       c.CheckOrder, c.CheckName, c.Result, c.Amount, c.Detail, c.Action,
       CASE c.Result WHEN 'Warn' THEN 1 ELSE 0 END AS IsWarning
FROM checks c
JOIN fct_ProjectPosition p ON p.ProjectKey = c.ProjectKey;
