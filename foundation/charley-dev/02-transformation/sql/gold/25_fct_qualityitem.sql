-- gold: fct_QualityItem - observations and punch items at the item grain.
--
-- Same union pattern as fct_RfiSubmittal, and for the same reason: two Procore endpoints
-- that answer the same business question ("what is outstanding on this project, and how
-- long has it been outstanding"). ItemType keeps them separable; one fact keeps every
-- measure from being written twice.
--
-- WHAT THIS REPLACES. QUALITY!Table18 is typed by hand each month: an observation count, a
-- punch count, and two hand-computed averages. It also carries workbook defect #2 -
-- QUALITY!D5:D6 read SAFETY orientations, so the quality tab has been reporting a safety
-- number. Sourcing both counts from the item records makes that defect impossible rather
-- than merely fixed.
--
-- The workbook stores only the COUNTS. Storing the items means the same numbers reproduce
-- exactly, and drill-through to the actual records comes free - which is the thing the
-- spreadsheet fundamentally cannot do.

CREATE OR REPLACE TABLE fct_QualityItem AS
SELECT
    project_id                          AS ProjectKey,
    'Observation'                       AS ItemType,
    observation_id                      AS ItemKey,
    observation_number                  AS ItemNumber,
    title                               AS Title,
    observation_type                    AS ItemCategory,
    status_label                        AS StatusLabel,
    priority                            AS Priority,
    trade                               AS Trade,
    COALESCE(assignee_name, 'UNASSIGNED') AS AssignedTo,
    CAST(NULL AS STRING)                AS CostCodeKey,
    created_date                        AS CreatedDate,
    due_date                            AS DueDate,
    closed_date                         AS ClosedDate,
    -- Only set when the date falls inside dim_Date, so an out-of-range value cannot
    -- silently blank every measure that groups by month.
    CASE WHEN created_date IS NULL
              OR created_date < DATE '2015-01-01'
              OR created_date > DATE '2035-12-31' THEN NULL
         ELSE make_date(year(created_date), month(created_date), 1) END AS MonthStart,
    CASE WHEN created_date IS NOT NULL
              AND (created_date < DATE '2015-01-01' OR created_date > DATE '2035-12-31')
         THEN TRUE ELSE FALSE END       AS HasOutOfRangeDate,
    -- Open is derived from the DATA, not from status text. Procore's status vocabulary is
    -- configurable per company, so a rule keyed to the word "closed" breaks the day someone
    -- renames it.
    CASE WHEN closed_date IS NULL THEN TRUE ELSE FALSE END AS IsOpen,
    CASE WHEN closed_date IS NOT NULL AND created_date IS NOT NULL
              THEN datediff(closed_date, created_date)
         WHEN created_date IS NOT NULL
              THEN datediff(CURRENT_DATE, created_date)
    END                                 AS DaysOpen,
    -- Past due only counts while still open: a late-but-closed item is not outstanding.
    CASE WHEN closed_date IS NULL AND due_date IS NOT NULL AND due_date < CURRENT_DATE
         THEN TRUE ELSE FALSE END       AS IsPastDue,
    CASE WHEN closed_date IS NULL AND due_date IS NOT NULL AND due_date < CURRENT_DATE
         THEN datediff(CURRENT_DATE, due_date) END AS DaysPastDue
FROM sv_observations
WHERE project_id IS NOT NULL

UNION ALL

SELECT
    project_id                          AS ProjectKey,
    'PunchItem'                         AS ItemType,
    punch_item_id                       AS ItemKey,
    punch_item_number                   AS ItemNumber,
    title                               AS Title,
    punch_item_type                     AS ItemCategory,
    status_label                        AS StatusLabel,
    priority                            AS Priority,
    trade                               AS Trade,
    COALESCE(manager_name, 'UNASSIGNED') AS AssignedTo,
    cost_code_id                        AS CostCodeKey,
    created_date                        AS CreatedDate,
    due_date                            AS DueDate,
    closed_date                         AS ClosedDate,
    CASE WHEN created_date IS NULL
              OR created_date < DATE '2015-01-01'
              OR created_date > DATE '2035-12-31' THEN NULL
         ELSE make_date(year(created_date), month(created_date), 1) END AS MonthStart,
    CASE WHEN created_date IS NOT NULL
              AND (created_date < DATE '2015-01-01' OR created_date > DATE '2035-12-31')
         THEN TRUE ELSE FALSE END       AS HasOutOfRangeDate,
    CASE WHEN closed_date IS NULL THEN TRUE ELSE FALSE END AS IsOpen,
    CASE WHEN closed_date IS NOT NULL AND created_date IS NOT NULL
              THEN datediff(closed_date, created_date)
         WHEN created_date IS NOT NULL
              THEN datediff(CURRENT_DATE, created_date)
    END                                 AS DaysOpen,
    CASE WHEN closed_date IS NULL AND due_date IS NOT NULL AND due_date < CURRENT_DATE
         THEN TRUE ELSE FALSE END       AS IsPastDue,
    CASE WHEN closed_date IS NULL AND due_date IS NOT NULL AND due_date < CURRENT_DATE
         THEN datediff(CURRENT_DATE, due_date) END AS DaysPastDue
FROM sv_punch_items
WHERE project_id IS NOT NULL;
