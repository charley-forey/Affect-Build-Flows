-- silver: bronze RFI + submittal payloads -> one typed, trimmed, validated table.
--
-- Written in Spark SQL (the production dialect). run_local.py registers DuckDB macros
-- for get_json_object/datediff so the exact same file runs locally.
--
-- Two rules from resources/microsoft-fabric/README.md:85-89 and
-- analysis/excel-tracker/dropdowns-and-status.md:296-299:
--   1. TRIM() every text value on the way in. 12 of the 29 trades carry trailing
--      whitespace, and "Metals  " never equals "Metals" in a join.
--   2. Reject loudly - a bad row goes to data_quality_log with a reason, it does not
--      silently disappear. That is how a $200,000,000 buyout against a $9.1M contract
--      reached a leadership report unchallenged.
--
-- FIELD NAMES: taken from Procore's documented RFI (v1.0) and Submittal (v1.1) shapes.
-- Confirm against the sandbox before trusting - see src/README.md "Confirming field names".

CREATE OR REPLACE TEMPORARY VIEW _rfi_submittal_parsed AS
SELECT
    b._source_endpoint                                        AS SourceEndpoint,
    CASE b._source_endpoint WHEN 'rfis' THEN 'RFI'
                            WHEN 'submittals' THEN 'Submittal' END
                                                              AS ItemType,
    CAST(b._project_id AS INT)                                AS ProcoreProjectId,
    CAST(b._key AS BIGINT)                                    AS ProcoreItemId,
    TRIM(get_json_object(b.payload, '$.number'))              AS ItemNumber,
    -- RFIs call it subject, submittals call it title.
    TRIM(COALESCE(get_json_object(b.payload, '$.subject'),
                  get_json_object(b.payload, '$.title')))     AS Subject,
    -- RFI status is a bare string; submittal status is an object.
    TRIM(COALESCE(get_json_object(b.payload, '$.status.name'),
                  get_json_object(b.payload, '$.status')))    AS StatusLabel,
    TRIM(COALESCE(get_json_object(b.payload, '$.priority.name'),
                  get_json_object(b.payload, '$.priority')))  AS PriorityLabel,
    -- Neither object carries an Affect trade. RFIs carry a cost code, submittals a spec
    -- section. Kept here so the gold layer can attempt a match and log what fails.
    TRIM(get_json_object(b.payload, '$.cost_code.name'))      AS CostCodeName,
    TRIM(get_json_object(b.payload, '$.specification_section.description'))
                                                              AS SpecSection,
    -- Substring the ISO-8601 date out rather than parsing the timestamp: identical
    -- behaviour in Spark and DuckDB, and the grain we need is the day.
    CAST(SUBSTR(get_json_object(b.payload, '$.created_at'), 1, 10) AS DATE) AS CreatedDate,
    CAST(SUBSTR(get_json_object(b.payload, '$.due_date'),   1, 10) AS DATE) AS DueDate,
    CAST(SUBSTR(COALESCE(get_json_object(b.payload, '$.closed_at'),
                         get_json_object(b.payload, '$.completed_at')), 1, 10) AS DATE)
                                                              AS ClosedDate,
    b._ingested_at                                            AS IngestedAt
FROM bronze_rfi_submittal_union b;

-- The data-quality log. Severity 'reject' = kept out of silver; 'warn' = let through but
-- flagged (the gold layer appends to this too). Surfaces on the report's hidden Data
-- Quality page rather than disappearing.
CREATE OR REPLACE TABLE data_quality_log AS
SELECT
    'silver_rfi_submittal' AS TableName,
    ProcoreItemId,
    ProcoreProjectId,
    ItemType,
    CASE
        WHEN ProcoreProjectId IS NULL       THEN 'missing_project_id'
        WHEN ProcoreItemId    IS NULL       THEN 'missing_item_id'
        WHEN ItemNumber IS NULL OR ItemNumber = '' THEN 'missing_item_number'
        WHEN CreatedDate IS NULL            THEN 'missing_created_date'
        WHEN ClosedDate IS NOT NULL AND ClosedDate < CreatedDate
                                            THEN 'closed_before_created'
    END AS Issue,
    'reject' AS Severity,
    IngestedAt
FROM _rfi_submittal_parsed
WHERE ProcoreProjectId IS NULL
   OR ProcoreItemId IS NULL
   OR ItemNumber IS NULL OR ItemNumber = ''
   OR CreatedDate IS NULL
   OR (ClosedDate IS NOT NULL AND ClosedDate < CreatedDate);

CREATE OR REPLACE TABLE silver_rfi_submittal AS
SELECT *
FROM _rfi_submittal_parsed
WHERE ProcoreProjectId IS NOT NULL
  AND ProcoreItemId IS NOT NULL
  AND ItemNumber IS NOT NULL AND ItemNumber <> ''
  AND CreatedDate IS NOT NULL
  AND (ClosedDate IS NULL OR ClosedDate >= CreatedDate);
