-- silver: records deleted at source (Procore and Outbuild), and when each Procore project was
-- last extracted.
--
-- DELETED AT SOURCE. Bronze never deletes. When a key present in bronze is absent from a
-- COMPLETE full pull of its (endpoint, project) scope, the extractor sets
-- `_source_deleted_at` on the row instead (fabric_common.merge_sql / deltars.merge_rows,
-- eligibility in procore_scope.tombstone_scopes). The parsers in 10/20/21/23/24 exclude
-- those rows; this file records them in cd_dq_rejects with the reason 'deleted at source',
-- so for every table below:
--     bronze rows with an id = silver rows + 'deleted at source' rejects
-- (rows without an id stay 'missing id' rejects, deleted or not). dq_DataGap lists them
-- under 'Deleted at source'. See _docs/deletion-and-scope-handling.md.
--
-- DELETE then INSERT, as 24 and 27 do: cd_dq_rejects is created by 10_procore_silver.sql.

DELETE FROM cd_dq_rejects WHERE reason = 'deleted at source';

INSERT INTO cd_dq_rejects
SELECT 'cd_silver_prime_change_orders', 'deleted at source', payload, _batch_id
FROM cd_bronze_procore_prime_change_orders
WHERE get_json_object(payload, '$.id') IS NOT NULL AND _source_deleted_at IS NOT NULL
UNION ALL
SELECT 'cd_silver_submittals', 'deleted at source', payload, _batch_id
FROM cd_bronze_procore_submittals
WHERE get_json_object(payload, '$.id') IS NOT NULL AND _source_deleted_at IS NOT NULL
UNION ALL
SELECT 'cd_silver_rfis', 'deleted at source', payload, _batch_id
FROM cd_bronze_procore_rfis
WHERE get_json_object(payload, '$.id') IS NOT NULL AND _source_deleted_at IS NOT NULL
UNION ALL
SELECT 'cd_silver_observations', 'deleted at source', payload, _batch_id
FROM cd_bronze_procore_observations
WHERE get_json_object(payload, '$.id') IS NOT NULL AND _source_deleted_at IS NOT NULL
UNION ALL
SELECT 'cd_silver_punch_items', 'deleted at source', payload, _batch_id
FROM cd_bronze_procore_punch_items
WHERE get_json_object(payload, '$.id') IS NOT NULL AND _source_deleted_at IS NOT NULL
UNION ALL
SELECT 'cd_silver_direct_costs', 'deleted at source', payload, _batch_id
FROM cd_bronze_procore_direct_costs
WHERE get_json_object(payload, '$.id') IS NOT NULL AND _source_deleted_at IS NOT NULL
UNION ALL
SELECT 'cd_silver_commitments', 'deleted at source', payload, _batch_id
FROM cd_bronze_procore_work_order_contracts
WHERE get_json_object(payload, '$.id') IS NOT NULL AND _source_deleted_at IS NOT NULL
UNION ALL
SELECT 'cd_silver_commitments', 'deleted at source', payload, _batch_id
FROM cd_bronze_procore_purchase_order_contracts
WHERE get_json_object(payload, '$.id') IS NOT NULL AND _source_deleted_at IS NOT NULL
UNION ALL
SELECT 'cd_silver_commitment_lines', 'deleted at source', payload, _batch_id
FROM cd_bronze_procore_work_order_contract_line_items
WHERE get_json_object(payload, '$.id') IS NOT NULL AND _source_deleted_at IS NOT NULL
UNION ALL
SELECT 'cd_silver_commitment_lines', 'deleted at source', payload, _batch_id
FROM cd_bronze_procore_purchase_order_contract_line_items
WHERE get_json_object(payload, '$.id') IS NOT NULL AND _source_deleted_at IS NOT NULL
-- Outbuild (cd_02_extract_outbuild tombstones projects and activities; 25 excludes them).
-- An activity without an id stays a 'missing id' reject, as for Procore above.
UNION ALL
SELECT 'cd_silver_outbuild_activities', 'deleted at source', payload, _batch_id
FROM cd_bronze_outbuild_activities
WHERE get_json_object(payload, '$.id') IS NOT NULL AND _source_deleted_at IS NOT NULL
UNION ALL
SELECT 'outbuild_schedule_map', 'deleted at source', payload, _batch_id
FROM cd_bronze_outbuild_projects
WHERE _source_deleted_at IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Project extraction freshness
-- ---------------------------------------------------------------------------
-- Extraction covers ACTIVE projects only. A project that goes inactive stops being read,
-- and its facts freeze while still counting in portfolio totals. This makes that visible.
--
-- last_extracted_at = the newest _ingested_at on the project's rows in FULL-PULL,
-- project-scoped endpoints. A full pull re-merges every row it reads, so these advance on
-- every run that reads the project and stop the night it leaves scope. Incremental and
-- windowed endpoints are left out: their rows only move when the record changes.
-- is_active_in_procore is Procore's own flag from the projects payload.
CREATE OR REPLACE TABLE cd_silver_project_extraction AS
SELECT p.project_id, p.is_active AS is_active_in_procore, e.last_extracted_at
FROM cd_silver_projects p
LEFT JOIN (
    SELECT CAST(_project_id AS STRING) AS project_id, MAX(_ingested_at) AS last_extracted_at
    FROM (
        SELECT _project_id, _ingested_at FROM cd_bronze_procore_cost_codes
        UNION ALL SELECT _project_id, _ingested_at FROM cd_bronze_procore_project_vendors
        UNION ALL SELECT _project_id, _ingested_at FROM cd_bronze_procore_submittals
        UNION ALL SELECT _project_id, _ingested_at FROM cd_bronze_procore_rfis
        UNION ALL SELECT _project_id, _ingested_at FROM cd_bronze_procore_observations
        UNION ALL SELECT _project_id, _ingested_at FROM cd_bronze_procore_punch_items
        UNION ALL SELECT _project_id, _ingested_at FROM cd_bronze_procore_direct_costs
        UNION ALL SELECT _project_id, _ingested_at FROM cd_bronze_procore_prime_change_orders
    ) r
    WHERE _project_id IS NOT NULL
    GROUP BY CAST(_project_id AS STRING)
) e ON e.project_id = p.project_id;
