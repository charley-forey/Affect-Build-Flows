-- gold: fct_RfiSubmittal - the item grain behind SUBMITTALS & RFI!Table22.
--
-- The workbook stores only a per-trade COUNT (11 trades x 2 numbers, typed by hand) and
-- feeds the file's single native chart. Storing the items themselves reproduces that chart
-- exactly and adds drill-through to the actual records for free.
--
-- BOTH ARMS LIVE as of 2026-08-02. Submittals came from the existing warehouse; RFIs are
-- new - 616 of them, and no RFI table exists anywhere in the estate, so the RFI half of the
-- workbook's only chart has never been automated by anyone.
--
-- The union is the whole mechanism: ItemType distinguishes the two, so the model, the
-- measures and the chart needed no change to gain the second arm.
--
-- sv_rfis only exists in 01_source_views_cd.sql, so under --source existing the RFI arm
-- resolves to nothing. That is handled below rather than by two versions of this file.
--
-- "IsCritical" is UNRESOLVED. The workbook says "Open Critical" and never defines critical
-- anywhere. Procore exposes an RFI priority filter, which is the likely intent - hence
-- rfi_priorities in the registry - but it is a guess until Affect confirms. Rather than
-- bake a guess into a column everyone will trust, IsCritical is left NULL and the flag is
-- named honestly. Open question #5.

CREATE OR REPLACE TABLE fct_RfiSubmittal AS
SELECT
    project_id                        AS ProjectKey,
    'Submittal'                       AS ItemType,
    item_id                           AS ItemKey,
    item_number                       AS ItemNumber,
    TRIM(subject)                     AS Subject,
    TRIM(status_label)                AS StatusLabel,
    COALESCE(cost_code_id, 'UNASSIGNED') AS CostCodeKey,
    created_date                      AS CreatedDate,
    due_date                          AS DueDate,
    responded_date                    AS RespondedDate,
    -- Only set when the date falls inside dim_Date. Two submittals came back dated outside
    -- the calendar on the first real run; an unmatched key makes measures silently blank.
    CASE WHEN created_date IS NULL
              OR created_date < DATE '2015-01-01'
              OR created_date > DATE '2035-12-31' THEN NULL
         ELSE make_date(year(created_date), month(created_date), 1) END AS MonthStart,
    CASE WHEN created_date IS NOT NULL
              AND (created_date < DATE '2015-01-01' OR created_date > DATE '2035-12-31')
         THEN TRUE ELSE FALSE END     AS HasOutOfRangeDate,
    -- OPEN = awaiting review: not closed AND not a draft. Closed is a response date
    -- (distributed_at/closed_at) OR Procore's fixed 'Closed' status category - 65 of 952
    -- closed submittals (valid-JSON subset) carry neither date, and they are not open. Drafts (467 of 1,722
    -- measured 2026-09-14) have not been submitted, so they are not "open submittals";
    -- they stay visible through IsDraft / [Draft Submittals] instead of being dropped.
    -- Before 2026-09-14 this was responded_date IS NULL over the wrong date column, which
    -- counted ~96% of submittals open, every Approved one included.
    NOT is_closed AND NOT is_draft    AS IsOpen,
    CAST(NULL AS BOOLEAN)             AS IsCritical,
    -- Age of items still awaiting review. No value for closed or draft items: a
    -- today-minus-created fallback on those is what polluted the average before.
    CASE WHEN NOT is_closed AND NOT is_draft AND created_date IS NOT NULL
         THEN datediff(CURRENT_DATE, created_date) END AS DaysOpen,
    -- Past due only counts while still open: a late-but-answered item is not outstanding.
    CASE WHEN NOT is_closed AND NOT is_draft AND due_date IS NOT NULL AND due_date < CURRENT_DATE
         THEN TRUE ELSE FALSE END     AS IsPastDue,
    is_draft AND NOT is_closed        AS IsDraft,
    -- Created -> responded, closed items only.
    CASE WHEN responded_date IS NOT NULL AND created_date IS NOT NULL
         THEN datediff(responded_date, created_date) END AS TurnaroundDays
FROM (
    SELECT *,
           COALESCE(responded_date IS NOT NULL
                    OR UPPER(TRIM(status_category)) = 'CLOSED', FALSE)            AS is_closed,
           COALESCE(UPPER(TRIM(COALESCE(status_category, status_label))) = 'DRAFT', FALSE) AS is_draft
    FROM sv_submittals
) s
WHERE project_id IS NOT NULL

UNION ALL

SELECT
    project_id                        AS ProjectKey,
    'RFI'                             AS ItemType,
    item_id                           AS ItemKey,
    item_number                       AS ItemNumber,
    TRIM(subject)                     AS Subject,
    TRIM(status_label)                AS StatusLabel,
    COALESCE(cost_code_id, 'UNASSIGNED') AS CostCodeKey,
    created_date                      AS CreatedDate,
    due_date                          AS DueDate,
    responded_date                    AS RespondedDate,
    -- Only set when the date falls inside dim_Date. Two submittals came back dated outside
    -- the calendar on the first real run; an unmatched key makes measures silently blank.
    CASE WHEN created_date IS NULL
              OR created_date < DATE '2015-01-01'
              OR created_date > DATE '2035-12-31' THEN NULL
         ELSE make_date(year(created_date), month(created_date), 1) END AS MonthStart,
    CASE WHEN created_date IS NOT NULL
              AND (created_date < DATE '2015-01-01' OR created_date > DATE '2035-12-31')
         THEN TRUE ELSE FALSE END     AS HasOutOfRangeDate,
    -- OPEN = awaiting a response: not responded, not in a closed status, not a draft - the
    -- submittal arm's rule. RFI status is Procore's fixed vocabulary (open, draft, closed,
    -- closed_draft, closed_with_revision). Until 2026-09-14 this was responded_date IS NULL
    -- alone, which counted the 16 live drafts open (47 shown, 31 real).
    NOT is_closed AND NOT is_draft    AS IsOpen,
    -- "Critical" is still UNMEASURED - no confirmed rule. Candidates put to Affect: open and
    -- >14 days past due, or open with schedule impact yes_*. Priority is blank on every RFI.
    CAST(NULL AS BOOLEAN)             AS IsCritical,
    CASE WHEN NOT is_closed AND NOT is_draft AND created_date IS NOT NULL
         THEN datediff(CURRENT_DATE, created_date) END AS DaysOpen,
    -- Past due only counts while still open: a late-but-answered item is not outstanding.
    CASE WHEN NOT is_closed AND NOT is_draft AND due_date IS NOT NULL AND due_date < CURRENT_DATE
         THEN TRUE ELSE FALSE END     AS IsPastDue,
    is_draft AND NOT is_closed        AS IsDraft,
    CASE WHEN responded_date IS NOT NULL AND created_date IS NOT NULL
         THEN datediff(responded_date, created_date) END AS TurnaroundDays
FROM (
    SELECT *,
           COALESCE(responded_date IS NOT NULL
                    OR LOWER(TRIM(status_label)) LIKE 'closed%', FALSE)          AS is_closed,
           COALESCE(LOWER(TRIM(status_label)) = 'draft', FALSE)                  AS is_draft
    FROM sv_rfis
) r
WHERE project_id IS NOT NULL;
