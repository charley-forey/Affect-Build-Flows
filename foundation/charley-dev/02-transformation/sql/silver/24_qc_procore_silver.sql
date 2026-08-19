-- silver: the PQP subject area's PROCORE-sourced half.
--
-- Procore is the client's MANDATORY system of record for quality - their own QA/QC
-- workbook says so in as many words. So NCRs, punch items and submittals are read from the
-- API and are NOT SharePoint lists. That distinction is the single most important decision
-- in this subject area: a hand-maintained NCR log next to a Procore NCR log is two answers
-- to "how many are open", and the workbook already demonstrates which one wins (neither).
--
-- WHAT THIS FILE DOES THAT 20_fieldops_silver.sql DOES NOT.
--
-- 20_ already parses observations, punch items and submittals out of the raw payload, and
-- re-parsing the same JSON here would be two parsers to keep in step. This reads the
-- ALREADY-TYPED cd_silver_* tables (10_ and 20_ run first) and adds the one thing the
-- generic field-ops shape cannot carry: the QA/QC WORKBOOK'S OWN VOCABULARY.
--
-- The workbook scores quality against fixed code lists - NCR status, punch category,
-- submittal disposition - and Procore's status text is configurable per company. Mapping
-- one to the other is a real transform with a real failure mode, and it belongs in silver
-- where it can be inspected, not in a DAX SWITCH nobody can diff.
--
-- AN UNMAPPED STATUS BECOMES NULL, NOT A GUESS. The raw label is kept alongside in
-- source_status, and the DQ suite has an expectation that every *_code resolves to
-- dim_QcStatus - so an unmapped value hands you the rows rather than quietly bucketing
-- them into whatever the ELSE branch said. Naming-standards.md rule 2, applied where both
-- sides of the comparison exist.

-- ---------------------------------------------------------------------------
-- NCRs - Procore observations, read through the QA/QC lens
-- ---------------------------------------------------------------------------
-- NOT filtered to quality-typed observations. The workbook's NCR log and Procore's
-- observation list are the same population viewed differently, and filtering here would
-- make "open NCRs" disagree with "open observations" by an amount nobody could reconcile.
-- ItemClassCode carries the workbook's COR/NCR/WIP split so the filter can be applied in
-- the model, reversibly, by whoever needs it.

CREATE OR REPLACE TABLE cd_silver_qc_ncr AS
SELECT
    project_id,
    observation_id                                          AS ncr_id,
    observation_number                                      AS ncr_number,
    title,
    description,
    observation_type,
    category,
    trade,
    assignee_name,
    priority,
    status_label                                            AS source_status,
    -- -> dim_QcStatus Domain='NCRLOG_5'
    CASE UPPER(COALESCE(status_label, ''))
         WHEN 'INITIATED'        THEN 'OPEN'
         WHEN 'OPEN'             THEN 'OPEN'
         WHEN 'NOT_ACCEPTED'     THEN 'IN_PROGRESS'
         WHEN 'READY_FOR_REVIEW' THEN 'AWAITING_A_E'
         WHEN 'CLOSED'           THEN 'CLOSED'
    END                                                     AS status_code,
    -- -> dim_QcStatus Domain='NCRLOG_3'. Procore has no such field, so it is derived from
    -- the observation type the site team already picks. NULL where the type says nothing
    -- about it, which is most of them today - visible rather than defaulted to 'NCR'.
    CASE
        WHEN UPPER(COALESCE(observation_type, '')) LIKE '%NON-CONFORM%' THEN 'NCR'
        WHEN UPPER(COALESCE(observation_type, '')) LIKE '%NCR%'         THEN 'NCR'
        WHEN UPPER(COALESCE(observation_type, '')) LIKE '%CORRECT%'     THEN 'COR'
        WHEN UPPER(COALESCE(observation_type, '')) LIKE '%WORK IN PROGRESS%' THEN 'WIP'
    END                                                     AS item_class_code,
    created_date,
    due_date,
    closed_date,
    _ingested_at, _batch_id
FROM cd_silver_observations
WHERE project_id IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Punch & RCL log - Procore punch items
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE cd_silver_qc_punch AS
SELECT
    project_id,
    punch_item_id                                           AS punch_id,
    punch_item_number                                       AS punch_number,
    title,
    punch_item_type,
    trade,
    manager_name,
    cost_code_id,
    priority,
    status_label                                            AS source_status,
    -- -> dim_QcStatus Domain='PUNCHRCLLOG_5'
    CASE UPPER(COALESCE(status_label, ''))
         WHEN 'INITIATED'          THEN 'OPEN'
         WHEN 'OPEN'               THEN 'OPEN'
         WHEN 'IN_PROGRESS'        THEN 'IN_PROGRESS'
         WHEN 'WORK_REQUIRED'      THEN 'IN_PROGRESS'
         WHEN 'WORK_NOT_ACCEPTED'  THEN 'IN_PROGRESS'
         WHEN 'READY_FOR_REVIEW'   THEN 'CORRECTED'
         WHEN 'CLOSED'             THEN 'CLOSED'
    END                                                     AS status_code,
    -- -> dim_QcStatus Domain='PUNCHRCLLOG_3'. The workbook separates a punch item from
    -- work-to-complete and day-2 work because they are billed and chased differently.
    CASE
        WHEN UPPER(COALESCE(punch_item_type, '')) LIKE '%DAY 2%'   THEN 'DAY_2_WORK'
        WHEN UPPER(COALESCE(punch_item_type, '')) LIKE '%DAY-2%'   THEN 'DAY_2_WORK'
        WHEN UPPER(COALESCE(punch_item_type, '')) LIKE '%WORK TO COMPLETE%' THEN 'WORK_TO_COMPLETE_WTC'
        WHEN UPPER(COALESCE(punch_item_type, '')) LIKE '%WTC%'     THEN 'WORK_TO_COMPLETE_WTC'
        WHEN punch_item_type IS NOT NULL                           THEN 'PUNCH_ITEM'
    END                                                     AS item_class_code,
    created_date,
    due_date,
    closed_date,
    _ingested_at, _batch_id
FROM cd_silver_punch_items
WHERE project_id IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Submittals & mockups
-- ---------------------------------------------------------------------------
-- The workbook's Submittals & Mockups sheet tracks the SAME records Procore holds, plus a
-- mockup flag Procore has no field for. The flag is derived from the subject rather than
-- entered a second time: one place to look, and a mockup that is renamed reclassifies
-- itself instead of going stale.

CREATE OR REPLACE TABLE cd_silver_qc_submittal AS
SELECT
    project_id,
    item_id                                                 AS submittal_id,
    item_number                                             AS submittal_number,
    subject,
    cost_code_id,
    status_label                                            AS source_status,
    -- -> dim_QcStatus Domain='SUBMITTALSMOCKUPS_6'
    CASE UPPER(TRIM(COALESCE(status_label, '')))
         WHEN 'DRAFT'                THEN 'OPEN'
         WHEN 'OPEN'                 THEN 'OPEN'
         WHEN 'SUBMITTED'            THEN 'SUBMITTED'
         WHEN 'IN REVIEW'            THEN 'IN_REVIEW'
         WHEN 'PENDING'              THEN 'PENDING'
         WHEN 'APPROVED'             THEN 'APPROVED'
         WHEN 'APPROVED AS NOTED'    THEN 'APPROVED_AS_NOTED'
         WHEN 'REVISE AND RESUBMIT'  THEN 'REVISE_RESUBMIT'
         WHEN 'REJECTED'             THEN 'REJECTED'
         WHEN 'FOR RECORD ONLY'      THEN 'FOR_RECORD_ONLY'
         WHEN 'CLOSED'               THEN 'CLOSED'
    END                                                     AS status_code,
    -- -> dim_QcStatus Domain='SUBMITTALSMOCKUPS_9'
    CASE
        WHEN UPPER(COALESCE(subject, '')) LIKE '%MOCK%'          THEN 'MOCK_UP'
        WHEN UPPER(COALESCE(subject, '')) LIKE '%SHOP DRAWING%'  THEN 'SHOP_DRAWING'
        WHEN UPPER(COALESCE(subject, '')) LIKE '%SAMPLE%'        THEN 'SAMPLE'
        WHEN UPPER(COALESCE(subject, '')) LIKE '%O&M%'           THEN 'O_M_MANUAL'
        WHEN UPPER(COALESCE(subject, '')) LIKE '%WARRANT%'       THEN 'WARRANTY'
        WHEN UPPER(COALESCE(subject, '')) LIKE '%AS-BUILT%'      THEN 'AS_BUILT'
        WHEN UPPER(COALESCE(subject, '')) LIKE '%CERTIF%'        THEN 'CERTIFICATION'
        WHEN UPPER(COALESCE(subject, '')) LIKE '%TEST REPORT%'   THEN 'TEST_REPORT'
        WHEN UPPER(COALESCE(subject, '')) LIKE '%PRODUCT DATA%'  THEN 'PRODUCT_DATA'
    END                                                     AS submittal_type_code,
    created_date,
    due_date,
    responded_date,
    _ingested_at, _batch_id
FROM cd_silver_submittals
WHERE project_id IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Procore Inspections (checklist lists) - the ONE genuinely new payload
-- ---------------------------------------------------------------------------
-- /rest/v1.0/checklist/lists, added to endpoints.yml alongside this file. Parsed from raw
-- JSON because nothing upstream reads it yet.
--
-- This is the endpoint that could eventually retire man_QcChecklistResult: Procore
-- Inspections IS a per-project instance of a checklist template, which is exactly what the
-- 26 trade sheets are. It is landed now, and read now, so the comparison can be made
-- against real data rather than argued about - see _docs/pqp-solution.md.

CREATE OR REPLACE TABLE cd_silver_qc_inspection AS
SELECT
    CAST(_project_id                                        AS STRING)  AS project_id,
    CAST(get_json_object(payload, '$.id')                   AS STRING)  AS inspection_id,
    CAST(get_json_object(payload, '$.number')               AS STRING)  AS inspection_number,
    TRIM(get_json_object(payload, '$.name'))                            AS name,
    TRIM(get_json_object(payload, '$.inspection_type.name'))            AS inspection_type,
    TRIM(get_json_object(payload, '$.list_template.name'))              AS template_name,
    TRIM(get_json_object(payload, '$.trade.name'))                      AS trade,
    TRIM(get_json_object(payload, '$.inspector.name'))                  AS inspector_name,
    UPPER(TRIM(get_json_object(payload, '$.status')))                   AS source_status,
    CAST(get_json_object(payload, '$.inspection_date')      AS DATE)    AS inspection_date,
    CAST(get_json_object(payload, '$.due_date')             AS DATE)    AS due_date,
    CAST(get_json_object(payload, '$.percent_complete')     AS DOUBLE)  AS percent_complete,
    _ingested_at, _batch_id
FROM cd_bronze_procore_checklist_lists
WHERE get_json_object(payload, '$.id') IS NOT NULL;
