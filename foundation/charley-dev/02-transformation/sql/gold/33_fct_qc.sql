-- gold: the PQP facts that come from PROCORE - fct_QcNcr, fct_QcPunch, fct_QcSubmittal.
--
-- THREE FACTS, NOT ONE, and that is a departure from fct_QualityItem (which unions
-- observations and punch items behind an ItemType). The reason is the workbook: its NCR
-- Log, Punch & RCL Log and Submittals & Mockups sheets each carry columns the others do
-- not - root cause and disposition on an NCR, a punch category on a punch item, a
-- submittal type and a responded date on a submittal. Unioning them would mean a table
-- two-thirds NULL and a measure set full of ItemType filters. fct_QualityItem stays for
-- the monthly report's counts; these three are the quality plan's working views.
--
-- WHY THESE ARE NOT MANUAL LISTS. Procore is the client's mandatory system of record for
-- quality; their own QA/QC workbook says so. A SharePoint NCR log next to a Procore NCR
-- log is two answers to "how many are open" and the workbook already shows which one wins:
-- neither, because nobody trusts either. So the workbook's NCR / punch / submittal sheets
-- become a VIEW OF PROCORE rather than a second place to type.
--
-- StatusCode is the WORKBOOK'S vocabulary, mapped in sql/silver/24_qc_procore_silver.sql
-- and resolvable against dim_QcStatus. SourceStatus keeps Procore's own text alongside, so
-- an unmapped value is visible as a row rather than absorbed into an ELSE branch.

-- ---------------------------------------------------------------------------
-- NCRs
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE fct_QcNcr AS
SELECT
    n.project_id                        AS ProjectKey,
    n.ncr_id                            AS NcrKey,
    n.ncr_number                        AS NcrNumber,
    n.title                             AS Title,
    n.description                       AS Description,
    n.observation_type                  AS ObservationType,
    n.category                          AS Category,
    n.trade                             AS TradeLabel,
    -- Procore's `trade` is free text and the workbook's TradeKey is a controlled key, so
    -- this resolves what it can and leaves the rest NULL next to a flag. A fuzzy match
    -- would attach an NCR to the wrong trade, which is worse than attaching it to none.
    --
    -- ponytail: exact match on the normalised label only. Upgrade path is a
    -- qc_seed_TradeAlias table the moment the unmapped count is worth the row - the flag
    -- below is what tells you when that is.
    t.TradeKey                          AS TradeKey,
    CASE WHEN n.trade IS NOT NULL AND t.TradeKey IS NULL THEN TRUE ELSE FALSE END
                                        AS HasUnmappedTrade,
    n.assignee_name                     AS AssignedTo,
    n.priority                          AS Priority,
    n.source_status                     AS SourceStatus,
    n.status_code                       AS StatusCode,
    n.item_class_code                   AS ItemClassCode,
    n.created_date                      AS CreatedDate,
    n.due_date                          AS DueDate,
    n.closed_date                       AS ClosedDate,
    CASE WHEN n.created_date IS NULL
              OR n.created_date < DATE '2015-01-01'
              OR n.created_date > DATE '2035-12-31' THEN NULL
         ELSE make_date(year(n.created_date), month(n.created_date), 1) END AS MonthStart,
    -- Open comes from the DATA, not from status text. Procore's status vocabulary is
    -- configurable per company, so a rule keyed to the word "closed" breaks the day
    -- somebody renames it.
    CASE WHEN n.closed_date IS NULL THEN TRUE ELSE FALSE END AS IsOpen,
    CASE WHEN n.closed_date IS NOT NULL AND n.created_date IS NOT NULL
              THEN datediff(n.closed_date, n.created_date)
         WHEN n.created_date IS NOT NULL
              THEN datediff(CURRENT_DATE, n.created_date)
    END                                 AS DaysOpen,
    CASE WHEN n.closed_date IS NULL AND n.due_date IS NOT NULL AND n.due_date < CURRENT_DATE
         THEN TRUE ELSE FALSE END       AS IsPastDue
FROM sv_qc_ncr n
LEFT JOIN qc_seed_Trade t
       ON t.TradeKey = UPPER(REPLACE(TRIM(COALESCE(n.trade, '')), ' ', '_'))
WHERE n.project_id IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Punch & RCL log
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE fct_QcPunch AS
SELECT
    p.project_id                        AS ProjectKey,
    p.punch_id                          AS PunchKey,
    p.punch_number                      AS PunchNumber,
    p.title                             AS Title,
    p.punch_item_type                   AS PunchItemType,
    p.trade                             AS TradeLabel,
    t.TradeKey                          AS TradeKey,
    CASE WHEN p.trade IS NOT NULL AND t.TradeKey IS NULL THEN TRUE ELSE FALSE END
                                        AS HasUnmappedTrade,
    p.manager_name                      AS AssignedTo,
    p.cost_code_id                      AS CostCodeKey,
    p.priority                          AS Priority,
    p.source_status                     AS SourceStatus,
    p.status_code                       AS StatusCode,
    p.item_class_code                   AS ItemClassCode,
    p.created_date                      AS CreatedDate,
    p.due_date                          AS DueDate,
    p.closed_date                       AS ClosedDate,
    CASE WHEN p.created_date IS NULL
              OR p.created_date < DATE '2015-01-01'
              OR p.created_date > DATE '2035-12-31' THEN NULL
         ELSE make_date(year(p.created_date), month(p.created_date), 1) END AS MonthStart,
    CASE WHEN p.closed_date IS NULL THEN TRUE ELSE FALSE END AS IsOpen,
    CASE WHEN p.closed_date IS NOT NULL AND p.created_date IS NOT NULL
              THEN datediff(p.closed_date, p.created_date)
         WHEN p.created_date IS NOT NULL
              THEN datediff(CURRENT_DATE, p.created_date)
    END                                 AS DaysOpen,
    CASE WHEN p.closed_date IS NULL AND p.due_date IS NOT NULL AND p.due_date < CURRENT_DATE
         THEN TRUE ELSE FALSE END       AS IsPastDue
FROM sv_qc_punch p
LEFT JOIN qc_seed_Trade t
       ON t.TradeKey = UPPER(REPLACE(TRIM(COALESCE(p.trade, '')), ' ', '_'))
WHERE p.project_id IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Submittals & mockups
-- ---------------------------------------------------------------------------
-- IsOverdue is derived from responded_date rather than status, for the same reason IsOpen
-- is above. TurnaroundDays is the number the quality plan actually manages to: a submittal
-- approved in 40 days has held up procurement whatever its final status says.

CREATE OR REPLACE TABLE fct_QcSubmittal AS
SELECT
    project_id                          AS ProjectKey,
    submittal_id                        AS SubmittalKey,
    submittal_number                    AS SubmittalNumber,
    subject                             AS Subject,
    cost_code_id                        AS CostCodeKey,
    source_status                       AS SourceStatus,
    status_code                         AS StatusCode,
    submittal_type_code                 AS SubmittalTypeCode,
    CASE WHEN submittal_type_code = 'MOCK_UP' THEN TRUE ELSE FALSE END AS IsMockup,
    created_date                        AS CreatedDate,
    due_date                            AS DueDate,
    responded_date                      AS RespondedDate,
    CASE WHEN created_date IS NULL
              OR created_date < DATE '2015-01-01'
              OR created_date > DATE '2035-12-31' THEN NULL
         ELSE make_date(year(created_date), month(created_date), 1) END AS MonthStart,
    CASE WHEN responded_date IS NULL THEN TRUE ELSE FALSE END AS IsOpen,
    CASE WHEN responded_date IS NOT NULL AND created_date IS NOT NULL
              THEN datediff(responded_date, created_date)
         WHEN created_date IS NOT NULL
              THEN datediff(CURRENT_DATE, created_date)
    END                                 AS TurnaroundDays,
    CASE WHEN responded_date IS NULL AND due_date IS NOT NULL AND due_date < CURRENT_DATE
         THEN TRUE ELSE FALSE END       AS IsOverdue
FROM sv_qc_submittal
WHERE project_id IS NOT NULL;
