-- RFIs and submittals land in separate bronze tables (separate endpoints, separate API
-- versions) but become one fact. Union them once here so the silver file has a single
-- input and the same view name exists in Fabric and locally.

CREATE OR REPLACE TEMPORARY VIEW bronze_rfi_submittal_union AS
SELECT _key, _project_id, _source_endpoint, _ingested_at, payload
FROM bronze_procore_rfis
UNION ALL
SELECT _key, _project_id, _source_endpoint, _ingested_at, payload
FROM bronze_procore_submittals;
