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
    -- Resolved 2026-08-19. Exact match first, then qc_seed_TradeAlias for the labels
    -- Procore spells differently ("HVAC" -> HVAC_DUCTWORK, "Sprinkler" -> FIRE_SPRINKLER).
    -- The alias table carries ONLY unambiguous pairs. "Drywall/Carpentry", "Concrete
    -- Superstructure" and "Concrete" are deliberately absent - they need Affect to say
    -- which trade they mean - and a further group (Roofing, Glazing, Structural Steel,
    -- Low Voltage, ...) has no equivalent in the 26-sheet library at all. Both keep
    -- surfacing through the flag below rather than being guessed into a wrong trade.
    COALESCE(t.TradeKey, x.TradeKey)    AS TradeKey,
    CASE WHEN n.trade IS NOT NULL AND COALESCE(t.TradeKey, x.TradeKey) IS NULL
         THEN TRUE ELSE FALSE END       AS HasUnmappedTrade,
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
-- Joined on the RAW label, not the normalised key: an alias exists precisely
-- because the label does not normalise to a key.
LEFT JOIN qc_seed_TradeAlias x
       ON UPPER(TRIM(x.ProcoreTrade)) = UPPER(TRIM(COALESCE(n.trade, '')))
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
    COALESCE(t.TradeKey, x.TradeKey)    AS TradeKey,
    CASE WHEN p.trade IS NOT NULL AND COALESCE(t.TradeKey, x.TradeKey) IS NULL
         THEN TRUE ELSE FALSE END       AS HasUnmappedTrade,
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
-- Joined on the RAW label, not the normalised key: an alias exists precisely
-- because the label does not normalise to a key.
LEFT JOIN qc_seed_TradeAlias x
       ON UPPER(TRIM(x.ProcoreTrade)) = UPPER(TRIM(COALESCE(p.trade, '')))
WHERE p.project_id IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Submittals & mockups
-- ---------------------------------------------------------------------------
-- IsOpen/IsOverdue use the response date plus Procore's fixed status category, never the
-- configurable status name. TurnaroundDays is the number the quality plan actually manages to: a submittal
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
    -- Same open/closed/draft rule as fct_RfiSubmittal (see 23_fct_rfisubmittal.sql).
    NOT is_closed AND NOT is_draft      AS IsOpen,
    -- Created -> responded, closed items only. The old today-minus-created fallback put
    -- the age of open items into the turnaround average.
    CASE WHEN responded_date IS NOT NULL AND created_date IS NOT NULL
              THEN datediff(responded_date, created_date)
    END                                 AS TurnaroundDays,
    CASE WHEN NOT is_closed AND NOT is_draft AND due_date IS NOT NULL AND due_date < CURRENT_DATE
         THEN TRUE ELSE FALSE END       AS IsOverdue,
    is_draft AND NOT is_closed          AS IsDraft,
    CASE WHEN NOT is_closed AND NOT is_draft AND created_date IS NOT NULL
         THEN datediff(CURRENT_DATE, created_date) END AS DaysOpen
FROM (
    SELECT *,
           COALESCE(responded_date IS NOT NULL
                    OR UPPER(TRIM(status_category)) = 'CLOSED', FALSE)             AS is_closed,
           COALESCE(UPPER(TRIM(COALESCE(status_category, source_status))) = 'DRAFT', FALSE) AS is_draft
    FROM sv_qc_submittal
) s
WHERE project_id IS NOT NULL;

-- Native inspections retain their own identity; no equivalence to manual templates is assumed.
CREATE OR REPLACE TABLE fct_ProcoreInspection AS
SELECT project_id AS ProjectKey,
       inspection_id AS InspectionKey,
       CONCAT(CAST(LENGTH(project_id) AS STRING), ':', project_id, inspection_id) AS InspectionLinkKey,
       inspection_number AS InspectionNumber,
       name AS InspectionName,
       template_id AS SourceTemplateId,
       template_name AS SourceTemplateName,
       trade AS SourceTrade,
       inspector_name AS LegacyInspectorName,
       inspectors_json AS InspectorsJson,
       source_status AS SourceStatus,
       inspection_date AS InspectionDate,
       due_date AS DueDate,
       item_count AS SourceItemCount,
       conforming_item_count AS ConformingItemCount,
       deficient_item_count AS DeficientItemCount,
       not_inspected_item_count AS NotInspectedItemCount,
       na_item_count AS NotApplicableItemCount,
       neutral_item_count AS NeutralItemCount,
       percent_complete AS SourcePercentComplete
FROM sv_qc_inspection;

CREATE OR REPLACE TABLE fct_ProcoreInspectionItem AS
SELECT project_id AS ProjectKey, item_id AS ItemKey, inspection_id AS InspectionKey,
       CONCAT(CAST(LENGTH(project_id) AS STRING), ':', project_id, inspection_id) AS InspectionLinkKey,
       section_id AS SourceSectionId, name AS ItemName, source_status AS SourceStatus,
       source_response AS SourceResponse, response_category AS ResponseCategory,
       response_type AS ResponseType, response_json AS ResponseJson,
       item_response_json AS ItemResponseJson
FROM sv_qc_inspection_item;
