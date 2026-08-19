-- silver: field operations - observations, punch items, incidents.
--
-- These are the QUALITY and SAFETY halves of the scorecard. Until they land, six of nine
-- scorecard categories score BLANK and [Scorecard Coverage %] sits at 35% - which is honest
-- but not useful, because leadership sees a health score built on a third of the intended
-- weight.
--
-- All three also fix workbook defects on arrival:
--
--   Observations   QUALITY!D5:D6 currently reads SAFETY orientations (defect #2). The
--                  quality tab has been reporting a safety number for months.
--   Punch items    Counted by hand into QUALITY!Table18, capped at whatever fits the cells.
--   Incidents      SAFETY!Table1, typed monthly.
--
-- FIELD NAMES ARE FROM THE LIVE PAYLOAD, not the docs. Verified against Affect's tenant
-- 2026-08-02, because the last time these were assumed the money columns parsed to NULL
-- and produced a model that looked healthy and reported nothing.
--
-- Note `status` is lowercase on observations ("closed") and title case on punch items
-- ("Closed"). Both are UPPER()ed here so a downstream comparison cannot be defeated by
-- casing that varies per endpoint.

-- ---------------------------------------------------------------------------
-- Observations - the quality walk
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE cd_silver_observations AS
SELECT
    CAST(_project_id                                        AS STRING) AS project_id,
    CAST(get_json_object(payload, '$.id')                   AS STRING) AS observation_id,
    CAST(get_json_object(payload, '$.number')               AS STRING) AS observation_number,
    TRIM(get_json_object(payload, '$.name'))                           AS title,
    TRIM(get_json_object(payload, '$.description'))                    AS description,
    -- Nested one level: type.name is the observation type, category.name its grouping.
    TRIM(get_json_object(payload, '$.type.name'))                      AS observation_type,
    TRIM(get_json_object(payload, '$.category.name'))                  AS category,
    UPPER(TRIM(get_json_object(payload, '$.status')))                  AS status_label,
    TRIM(get_json_object(payload, '$.priority'))                       AS priority,
    -- $.trade is an OBJECT ({"id":..,"name":"Electrical",..}), not a string. Reading it
    -- whole put raw JSON in fct_QualityItem.Trade on the live report, and made every
    -- fct_Qc* trade join fail: 631 of 850 NCRs resolved to no trade. Take the name.
    TRIM(get_json_object(payload, '$.trade.name'))                     AS trade,
    TRIM(get_json_object(payload, '$.assignee.name'))                  AS assignee_name,
    CAST(get_json_object(payload, '$.created_at')           AS DATE)   AS created_date,
    CAST(get_json_object(payload, '$.due_date')             AS DATE)   AS due_date,
    CAST(get_json_object(payload, '$.closed_at')            AS DATE)   AS closed_date,
    _ingested_at, _batch_id
FROM cd_bronze_procore_observations
WHERE get_json_object(payload, '$.id') IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Punch items - the defect list
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE cd_silver_punch_items AS
SELECT
    CAST(_project_id                                        AS STRING) AS project_id,
    CAST(get_json_object(payload, '$.id')                   AS STRING) AS punch_item_id,
    CAST(get_json_object(payload, '$.position')             AS STRING) AS punch_item_number,
    TRIM(get_json_object(payload, '$.name'))                           AS title,
    TRIM(get_json_object(payload, '$.description'))                    AS description,
    TRIM(get_json_object(payload, '$.punch_item_type.name'))           AS punch_item_type,
    -- `status` is the display value, `workflow_status` the machine one. Both are kept:
    -- status is what a person recognises, workflow_status is what a rule should test.
    UPPER(TRIM(get_json_object(payload, '$.status')))                  AS status_label,
    UPPER(TRIM(get_json_object(payload, '$.workflow_status')))         AS workflow_status,
    TRIM(get_json_object(payload, '$.priority'))                       AS priority,
    -- $.trade is an OBJECT ({"id":..,"name":"Electrical",..}), not a string. Reading it
    -- whole put raw JSON in fct_QualityItem.Trade on the live report, and made every
    -- fct_Qc* trade join fail: 631 of 850 NCRs resolved to no trade. Take the name.
    TRIM(get_json_object(payload, '$.trade.name'))                     AS trade,
    CAST(get_json_object(payload, '$.cost_code.id')         AS STRING) AS cost_code_id,
    TRIM(get_json_object(payload, '$.punch_item_manager.name'))        AS manager_name,
    CAST(get_json_object(payload, '$.created_at')           AS DATE)   AS created_date,
    CAST(get_json_object(payload, '$.due_date')             AS DATE)   AS due_date,
    CAST(get_json_object(payload, '$.closed_at')            AS DATE)   AS closed_date,
    -- Procore computes overdue itself. Carried rather than recomputed: it reflects the
    -- project's own calendar and holidays, which we do not have.
    CAST(get_json_object(payload, '$.overdue')              AS BOOLEAN) AS is_overdue,
    _ingested_at, _batch_id
FROM cd_bronze_procore_punch_items
WHERE get_json_object(payload, '$.id') IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Incidents - safety
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE cd_silver_incidents AS
SELECT
    CAST(_project_id                                        AS STRING) AS project_id,
    CAST(get_json_object(payload, '$.id')                   AS STRING) AS incident_id,
    TRIM(get_json_object(payload, '$.title'))                          AS title,
    TRIM(get_json_object(payload, '$.description'))                    AS description,
    UPPER(TRIM(get_json_object(payload, '$.status')))                  AS status_label,
    -- Recordable is the OSHA distinction and the one the scorecard needs; a near miss is
    -- an incident but not a recordable one.
    CAST(get_json_object(payload, '$.recordable')           AS BOOLEAN) AS is_recordable,
    CAST(get_json_object(payload, '$.event_date')           AS DATE)   AS event_date,
    CAST(get_json_object(payload, '$.time_of_event')        AS STRING) AS event_time,
    CAST(get_json_object(payload, '$.created_at')           AS DATE)   AS created_date,
    _ingested_at, _batch_id
FROM cd_bronze_procore_incidents
WHERE get_json_object(payload, '$.id') IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Manpower - hours worked, the denominator of every safety rate
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE cd_silver_manpower_daily AS
SELECT
    project_id,
    log_date,
    SUM(man_hours)   AS total_hours,
    SUM(num_workers) AS total_workers,
    COUNT(*)         AS vendor_entries,
    MAX(_ingested_at) AS _ingested_at,
    MAX(_batch_id)    AS _batch_id
FROM (
    SELECT
        CAST(_project_id                                    AS STRING) AS project_id,
        CAST(get_json_object(payload, '$.date')             AS DATE)   AS log_date,
        -- man_hours arrives as a STRING ("24.0"). Cast explicitly: an uncast SUM over
        -- strings is the kind of thing that concatenates quietly rather than failing.
        CAST(get_json_object(payload, '$.man_hours')        AS DOUBLE) AS man_hours,
        CAST(get_json_object(payload, '$.num_workers')      AS DOUBLE) AS num_workers,
        _ingested_at, _batch_id
    FROM cd_bronze_procore_manpower_logs
    WHERE get_json_object(payload, '$.date') IS NOT NULL
)
-- One row PER VENDOR PER DAY in the source; the safety rate needs hours per project per
-- day, so it is summed here rather than left for every downstream measure to remember.
GROUP BY project_id, log_date;
