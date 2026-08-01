-- gold: dim_Project - the spine every fact hangs off.
--
-- ⚠️ THE LINCHPIN UNKNOWN (dashboard.md:59, defects-and-questions.md:289):
-- whether the client's `YY-000` project number is the Procore project number, the Sage
-- job number, or a third thing entered by hand is still unconfirmed. Nothing joins
-- across systems without that answer.
--
-- For slice 1 this is deliberately sidestepped rather than guessed: ProjectKey = the
-- Procore project ID. That is stable, guaranteed unique, and sufficient for a
-- Procore-only fact table. SageJobNumber is left NULL - it is genuinely not available
-- from this source. When the shared key is confirmed, only this file changes.

CREATE OR REPLACE TABLE dim_Project AS
SELECT
    CAST(_key AS BIGINT)                                        AS ProjectKey,
    CAST(_key AS BIGINT)                                        AS ProcoreProjectId,
    TRIM(get_json_object(payload, '$.project_number'))          AS ProjectNumber,
    CAST(NULL AS STRING)                                        AS SageJobNumber,
    TRIM(get_json_object(payload, '$.name'))                    AS ProjectName,
    TRIM(get_json_object(payload, '$.customer.name'))           AS ClientName,
    CAST(SUBSTR(get_json_object(payload, '$.start_date'),      1, 10) AS DATE)
                                                                AS ContractStart,
    CAST(SUBSTR(get_json_object(payload, '$.completion_date'), 1, 10) AS DATE)
                                                                AS ContractFinish,
    -- Procore exposes both a boolean `active` and a `project_stage` object depending on
    -- version; prefer the stage label when present.
    TRIM(COALESCE(get_json_object(payload, '$.project_stage.name'),
                  get_json_object(payload, '$.active')))        AS Status
FROM bronze_procore_projects;
