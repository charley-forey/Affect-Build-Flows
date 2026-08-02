-- gold: dim_CostCodeCrosswalk - cost codes across Procore and Sage, with the division
-- rollup the report groups by.
--
-- THE SAGE SIDE IS NOT AVAILABLE YET, AND THAT IS THE POINT OF THE COLUMN.
--
-- Sage holds cost codes on the invoice LINE tables (apivln / arivln), not the header. The
-- existing Sage dataflow does not just omit those tables - it explicitly strips the columns
-- that point at them. CD_Sage_Ingest adds them and is built, but binding it needs the
-- on-prem gateway, which is Affect's to authorise (_docs/sage-ingestion.md).
--
-- So SageCostCode is declared and NULL rather than left out. Adding a column later means
-- touching the model, the measures and any visual that lists fields; declaring it now means
-- the Sage side arrives as data, not as a schema change. Everything downstream is already
-- written against the final shape.
--
-- THE DIVISION PARSE IS THE USEFUL PART TODAY. Procore cost codes read
-- "01-00-00 - GENERAL REQUIREMENTS"; the report groups by CSI division ("01"), which is not
-- a column anywhere - it is a substring nobody had extracted. Parsing it once here means
-- every visual groups the same way, rather than each doing its own string surgery.

CREATE OR REPLACE TABLE dim_CostCodeCrosswalk AS
WITH procore AS (
    SELECT
        cost_code_id,
        -- The CODE ("03-100"), not the name ("Concrete"). Parsing the name for a division
        -- is what made 5,429 of 5,433 codes look unparseable - a name has no division in it.
        TRIM(cost_code)      AS cost_code_raw,
        TRIM(cost_code_name) AS cost_code_name
    FROM sv_cost_codes
    WHERE cost_code_id IS NOT NULL
),
parsed AS (
    SELECT
        cost_code_id,
        cost_code_name,
        -- Everything before the first space-hyphen-space is the code; the rest is the name.
        -- Codes that do not follow the pattern keep the whole string as the code and get
        -- flagged, rather than being silently truncated into something that looks valid.
        -- Procore returns the code two ways depending on endpoint: "03-100" from
        -- /cost_codes, and "03-100 - CONCRETE" from a budget view. Handle both.
        CASE WHEN cost_code_raw LIKE '% - %'
             THEN TRIM(SUBSTRING(cost_code_raw, 1, INSTR(cost_code_raw, ' - ') - 1))
             ELSE cost_code_raw END  AS code_part,
        cost_code_name              AS name_part
    FROM procore
)
SELECT
    cost_code_id                                   AS CostCodeKey,
    cost_code_id                                   AS ProcoreCostCodeId,
    code_part                                      AS CostCode,
    COALESCE(name_part, cost_code_name)            AS CostCodeName,

    -- CSI division: the first two characters of the code. This is what the budget page and
    -- every cost rollup group by.
    CASE WHEN rlike_(code_part, '^[0-9]{2}')
         THEN SUBSTRING(code_part, 1, 2) END       AS DivisionCode,

    -- Blocked on the gateway. Declared so the model does not change shape when it arrives.
    CAST(NULL AS STRING)                           AS SageCostCode,
    FALSE                                          AS IsInSage,
    'PENDING_SAGE_INGEST'                          AS SageMatchMethod,

    TRUE                                           AS IsInProcore,
    -- A code that does not parse still appears - it just cannot be rolled up by division,
    -- and this flag is how that shows on the DQ page instead of quietly falling out of a
    -- subtotal.
    (code_part IS NULL OR NOT rlike_(code_part, '^[0-9]{2}')) AS HasUnparseableCode
FROM parsed;
