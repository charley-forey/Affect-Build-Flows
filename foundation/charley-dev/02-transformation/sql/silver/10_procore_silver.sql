-- silver: cd_bronze_procore_* -> cd_silver_*
--
-- Bronze holds the raw Procore payload as an unparsed JSON string. That is deliberate:
-- bronze cannot drop a column it never parsed, so a transform bug is a re-run rather than
-- a re-extract. This is where it gets parsed, typed and trimmed.
--
-- THE COLUMN NAMES HERE ARE A CONTRACT. They must match what sql/silver/00_source_views.sql
-- exposes as sv_*, because every gold file reads sv_* and nothing else. Get this right and
-- switching gold from Rebecca's Silver_Lakehouse to our own CD_Silver is a one-file change
-- with no gold file, measure or visual touched. That is the whole reason the naming was
-- isolated in one place.
--
-- RULES, from src/README.md and 00-platform/naming-standards.md:
--   TRIM every text value. Untrimmed source text never matches in a join - twelve of the
--   workbook's trade values carry trailing whitespace today (defect #9).
--   Reject loudly, never drop silently. A row missing its natural key goes to
--   cd_dq_rejects with a reason; it does not disappear.
--   Sentinel dates are floored to NULL. Procore and the existing warehouse both carry
--   placeholder dates - see the 1582 sentinels found in the submittals data.
--
-- Audit columns carry through so any silver row traces back to the run that produced it.

-- ---------------------------------------------------------------------------
-- Reference / dimensions
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE cd_silver_projects AS
SELECT
    CAST(get_json_object(payload, '$.id')            AS STRING) AS project_id,
    TRIM(get_json_object(payload, '$.name'))                    AS project_name,
    TRIM(get_json_object(payload, '$.project_number'))          AS project_number,
    TRIM(get_json_object(payload, '$.display_name'))            AS display_name,
    TRIM(get_json_object(payload, '$.status_name'))             AS status,
    CAST(get_json_object(payload, '$.active')        AS BOOLEAN) AS is_active,
    _ingested_at, _batch_id
FROM cd_bronze_procore_projects
WHERE get_json_object(payload, '$.id') IS NOT NULL;

CREATE OR REPLACE TABLE cd_silver_vendors AS
SELECT
    CAST(get_json_object(payload, '$.id')      AS STRING) AS procore_vendor_id,
    TRIM(get_json_object(payload, '$.name'))              AS vendor_name,
    TRIM(get_json_object(payload, '$.abbreviated_name'))  AS vendor_abbreviation,
    -- Procore's ERP sync writes the Sage vendor id (actpay.recnum) into origin_code.
    -- Measured 2026-09-13: 933 of 1,117 vendors carry one, all 933 resolve in actpay, none
    -- shared by two vendors, and all 125 of the legacy crosswalk's pairs agree. NULL means
    -- never synced to Sage. Blank is NULL, so it can never look like a match.
    NULLIF(TRIM(get_json_object(payload, '$.origin_code')), '') AS sage_vendor_id,
    CAST(get_json_object(payload, '$.is_active') AS BOOLEAN) AS is_active,
    _ingested_at, _batch_id
FROM cd_bronze_procore_vendors
WHERE get_json_object(payload, '$.id') IS NOT NULL;

CREATE OR REPLACE TABLE cd_silver_cost_codes AS
SELECT
    CAST(get_json_object(payload, '$.id')         AS STRING) AS cost_code_id,
    TRIM(get_json_object(payload, '$.full_code'))            AS cost_code,
    TRIM(get_json_object(payload, '$.name'))                 AS cost_code_name,
    CAST(get_json_object(payload, '$.parent.id')  AS STRING) AS parent_cost_code_id,
    _ingested_at, _batch_id
FROM cd_bronze_procore_cost_codes
WHERE get_json_object(payload, '$.id') IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Financial
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE cd_silver_prime_contracts AS
SELECT
    CAST(get_json_object(payload, '$.id')          AS STRING) AS prime_contract_id,
    CAST(_project_id                               AS STRING) AS project_id,
    TRIM(get_json_object(payload, '$.number'))               AS contract_number,
    TRIM(get_json_object(payload, '$.title'))                AS title,
    CAST(get_json_object(payload, '$.grand_total') AS DOUBLE) AS contract_value,
    CAST(get_json_object(payload, '$.retainage_percent') AS DOUBLE) AS retainage_pct,
    CASE WHEN CAST(get_json_object(payload, '$.start_date') AS DATE) < DATE '1990-01-01'
         THEN NULL ELSE CAST(get_json_object(payload, '$.start_date') AS DATE) END
                                                              AS start_date,
    CASE WHEN CAST(get_json_object(payload, '$.estimated_completion_date') AS DATE) < DATE '1990-01-01'
         THEN NULL ELSE CAST(get_json_object(payload, '$.estimated_completion_date') AS DATE) END
                                                              AS estimated_completion_date,
    TRIM(get_json_object(payload, '$.status'))                AS status,
    _ingested_at, _batch_id
FROM cd_bronze_procore_prime_contracts
WHERE get_json_object(payload, '$.id') IS NOT NULL;

CREATE OR REPLACE TABLE cd_silver_prime_change_orders AS
SELECT
    CAST(get_json_object(payload, '$.id')            AS STRING) AS change_order_id,
    CAST(_project_id                                 AS STRING) AS project_id,
    CAST(get_json_object(payload, '$.contract_id')   AS STRING) AS contract_id,
    TRIM(get_json_object(payload, '$.number'))                  AS co_number,
    TRIM(get_json_object(payload, '$.title'))                   AS title,
    CAST(get_json_object(payload, '$.grand_total')   AS DOUBLE) AS amount,
    CASE WHEN CAST(get_json_object(payload, '$.created_at') AS DATE) < DATE '1990-01-01'
         THEN NULL ELSE CAST(get_json_object(payload, '$.created_at') AS DATE) END
                                                                AS created_date,
    TRIM(get_json_object(payload, '$.status'))                  AS status,
    _ingested_at, _batch_id
FROM cd_bronze_procore_prime_change_orders
WHERE get_json_object(payload, '$.id') IS NOT NULL;

-- Budget detail rows are the per-cost-code budget numbers. Procore's budget view exposes
-- these as generic columns, so the mapping to named amounts is confirmed against a live
-- tenant before this is trusted - see _docs/procore-ingestion.md.
-- The budget grid, from Affect's OWN budget view ("STANDARD BUDGET VIEW - CM").
--
-- THE COLUMN NAMES ARE THE CONFIGURED VIEW'S, NOT AN API SCHEMA. Procore returns a
-- different column set per budget view - "Procore Standard Forecast" carries two money
-- columns, this one carries sixteen under Affect's lettered scheme. The registry pins the
-- view by name (endpoints.yml -> budget_detail_rows.parent.where_value) so bronze holds one
-- consistent shape; this parser reads that shape.
--
-- The first version of this file was written against the EXISTING warehouse's already-shaped
-- procore_budgets_silver ($.revised_budget_amount, $.committed_costs, $.cost_code.id). None
-- of those exist in the raw payload, so every money column silently parsed to NULL and the
-- budget measures returned blank in a model that otherwise looked healthy. Reading the raw
-- payload means reading the raw names.
--
-- Keep distinct source lines, including separate cost categories on one cost code.
-- Exact duplicate projected records collapse; conflicting versions survive for DQ to block.
CREATE OR REPLACE TABLE cd_silver_budgets AS
SELECT DISTINCT
    CAST(_key AS STRING) AS budget_line_id,
    CAST(_project_id                                    AS STRING) AS project_id,
    -- Flat cost_code_id, not a nested object. cost_code is the readable "01-00-00 - NAME".
    CAST(get_json_object(payload, '$.cost_code_id')     AS STRING) AS cost_code_id,
    TRIM(get_json_object(payload, '$.cost_code'))                  AS cost_code,
    TRIM(get_json_object(payload, '$.category'))                   AS category,
    CAST(get_json_object(payload, '$.original_budget_amount') AS DOUBLE) AS original_budget,
    CAST(get_json_object(payload, '$.budget_modifications')   AS DOUBLE) AS budget_modifications,
    -- D = A+B+C: original + modifications + approved prime contract COs.
    CAST(json_field(payload, 'UPDATED PRIME CONTRACT BUDGET (D = A+B+C)') AS DOUBLE)
                                                                   AS updated_budget,
    -- F = D+E: updated budget plus PENDING prime contract COs. This is the forecast.
    CAST(json_field(payload, 'PROJECTED PRIME CONTRACT BUDGET (F=D+E)') AS DOUBLE)
                                                                   AS forecast_budget,
    -- K = G+H+I+J: commitments + commitment COs + other + direct costs.
    CAST(json_field(payload, 'TOTAL COMMITTED TO DATE (K=G+H+I+J)') AS DOUBLE)
                                                                   AS committed_to_date,
    CAST(json_field(payload, 'DIRECT COSTS (J)')     AS DOUBLE) AS direct_costs,
    CAST(json_field(payload, 'INVOICED TO DATE (P)') AS DOUBLE) AS invoiced_to_date,
    -- Q = K-P: committed but not yet invoiced.
    CAST(json_field(payload, 'COST TO COMPLETE (Q=K-P)') AS DOUBLE)
                                                                   AS cost_to_complete,
    CAST(_ingested_at AS DATE)                                     AS snapshot_date,
    _ingested_at, _batch_id
FROM cd_bronze_procore_budget_detail_rows
WHERE _project_id IS NOT NULL
  AND json_field(payload, 'UPDATED PRIME CONTRACT BUDGET (D = A+B+C)') IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Project management
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE cd_silver_submittals AS
SELECT
    CAST(_project_id                            AS STRING) AS project_id,
    CAST(get_json_object(payload, '$.id')       AS STRING) AS item_id,
    TRIM(get_json_object(payload, '$.number'))             AS item_number,
    TRIM(get_json_object(payload, '$.title'))              AS subject,
    TRIM(get_json_object(payload, '$.status.name'))        AS status_label,
    -- Procore's fixed status CATEGORY behind the configurable name: Draft / Open / Closed
    -- (measured 2026-09-14: 'Approved as Noted', 'For Record', 'Rejected' ... are all
    -- Closed). Gold decides open-ness from this, not from the name.
    TRIM(get_json_object(payload, '$.status.status'))      AS status_category,
    CAST(get_json_object(payload, '$.cost_code.id') AS STRING) AS cost_code_id,
    CASE WHEN CAST(get_json_object(payload, '$.created_at') AS DATE) < DATE '1990-01-01'
         THEN NULL ELSE CAST(get_json_object(payload, '$.created_at') AS DATE) END
                                                           AS created_date,
    -- $.due_date is the submittal's review due date (78% populated). required_on_site_date
    -- is a delivery date set on ~1% and is only a fallback. Reading it alone left
    -- "past due" almost always empty.
    CASE WHEN CAST(COALESCE(get_json_object(payload, '$.due_date'),
                            get_json_object(payload, '$.required_on_site_date')) AS DATE)
              < DATE '1990-01-01'
         THEN NULL ELSE CAST(COALESCE(get_json_object(payload, '$.due_date'),
                                      get_json_object(payload, '$.required_on_site_date')) AS DATE) END
                                                           AS due_date,
    -- The response is when the reviewed package went back out (distributed_at), else when
    -- it was closed. NOT $.received_date: that is the day the GC received the package from
    -- the sub - an intake date, set on 4% and usually BEFORE created_at - which made the
    -- turnaround KPI ~1 day and left every Approved submittal "open". Fixed 2026-09-14.
    CASE WHEN CAST(COALESCE(get_json_object(payload, '$.distributed_at'),
                            get_json_object(payload, '$.closed_at')) AS DATE) < DATE '1990-01-01'
         THEN NULL ELSE CAST(COALESCE(get_json_object(payload, '$.distributed_at'),
                                      get_json_object(payload, '$.closed_at')) AS DATE) END
                                                           AS responded_date,
    _ingested_at, _batch_id
FROM cd_bronze_procore_submittals
WHERE get_json_object(payload, '$.id') IS NOT NULL;

-- RFIs. No RFI data exists ANYWHERE in the warehouse today - this is the half of the
-- workbook's only chart that has never been automated. Shaped identically to submittals so
-- fct_RfiSubmittal unions the two without special-casing either.
--
-- IsCritical is still not resolved here: the workbook says "Open Critical" and never
-- defines critical. The priority field is carried through so the question can be answered
-- from data once Affect confirms what they mean (open question #5).
CREATE OR REPLACE TABLE cd_silver_rfis AS
SELECT
    CAST(_project_id                            AS STRING) AS project_id,
    CAST(get_json_object(payload, '$.id')       AS STRING) AS item_id,
    TRIM(get_json_object(payload, '$.number'))             AS item_number,
    TRIM(get_json_object(payload, '$.subject'))            AS subject,
    TRIM(get_json_object(payload, '$.status'))             AS status_label,
    TRIM(get_json_object(payload, '$.priority'))           AS priority,
    CAST(get_json_object(payload, '$.cost_code.id') AS STRING) AS cost_code_id,
    CASE WHEN CAST(get_json_object(payload, '$.created_at') AS DATE) < DATE '1990-01-01'
         THEN NULL ELSE CAST(get_json_object(payload, '$.created_at') AS DATE) END
                                                           AS created_date,
    CASE WHEN CAST(get_json_object(payload, '$.due_date') AS DATE) < DATE '1990-01-01'
         THEN NULL ELSE CAST(get_json_object(payload, '$.due_date') AS DATE) END
                                                           AS due_date,
    CASE WHEN CAST(get_json_object(payload, '$.time_resolved') AS DATE) < DATE '1990-01-01'
         THEN NULL ELSE CAST(get_json_object(payload, '$.time_resolved') AS DATE) END
                                                           AS responded_date,
    _ingested_at, _batch_id
FROM cd_bronze_procore_rfis
WHERE get_json_object(payload, '$.id') IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Rejects. A row that fails its key check is recorded, not discarded. Silent drops are
-- how the workbook's defects #2 and #6 survived for months.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE cd_dq_rejects AS
SELECT 'cd_silver_projects' AS target_table, 'missing id' AS reason, payload, _batch_id
FROM cd_bronze_procore_projects WHERE get_json_object(payload, '$.id') IS NULL
UNION ALL
SELECT 'cd_silver_vendors', 'missing id', payload, _batch_id
FROM cd_bronze_procore_vendors WHERE get_json_object(payload, '$.id') IS NULL
UNION ALL
SELECT 'cd_silver_cost_codes', 'missing id', payload, _batch_id
FROM cd_bronze_procore_cost_codes WHERE get_json_object(payload, '$.id') IS NULL
UNION ALL
SELECT 'cd_silver_prime_contracts', 'missing id', payload, _batch_id
FROM cd_bronze_procore_prime_contracts WHERE get_json_object(payload, '$.id') IS NULL
UNION ALL
SELECT 'cd_silver_prime_change_orders', 'missing id', payload, _batch_id
FROM cd_bronze_procore_prime_change_orders WHERE get_json_object(payload, '$.id') IS NULL
UNION ALL
SELECT 'cd_silver_submittals', 'missing id', payload, _batch_id
FROM cd_bronze_procore_submittals WHERE get_json_object(payload, '$.id') IS NULL
UNION ALL
SELECT 'cd_silver_rfis', 'missing id', payload, _batch_id
FROM cd_bronze_procore_rfis WHERE get_json_object(payload, '$.id') IS NULL
UNION ALL
SELECT 'cd_silver_budgets',
       CASE WHEN _project_id IS NULL
                 AND json_field(payload, 'UPDATED PRIME CONTRACT BUDGET (D = A+B+C)') IS NULL
            THEN 'missing project and CM budget signature'
            WHEN _project_id IS NULL THEN 'missing project'
            ELSE 'missing CM budget signature' END,
       payload, _batch_id
FROM cd_bronze_procore_budget_detail_rows
WHERE _project_id IS NULL
   OR json_field(payload, 'UPDATED PRIME CONTRACT BUDGET (D = A+B+C)') IS NULL
UNION ALL
SELECT 'cd_silver_observations', 'missing id (observations)', payload, _batch_id
FROM cd_bronze_procore_observations WHERE get_json_object(payload, '$.id') IS NULL
UNION ALL
SELECT 'cd_silver_punch_items', 'missing id (punch_items)', payload, _batch_id
FROM cd_bronze_procore_punch_items WHERE get_json_object(payload, '$.id') IS NULL
UNION ALL
SELECT 'cd_silver_incidents', 'missing id (incidents)', payload, _batch_id
FROM cd_bronze_procore_incidents WHERE get_json_object(payload, '$.id') IS NULL
UNION ALL
SELECT 'cd_silver_billing', 'missing id (requisitions)', payload, _batch_id
FROM cd_bronze_procore_requisitions WHERE get_json_object(payload, '$.id') IS NULL
UNION ALL
SELECT 'cd_silver_billing', 'missing id (payment_applications)', payload, _batch_id
FROM cd_bronze_procore_payment_applications WHERE get_json_object(payload, '$.id') IS NULL
UNION ALL
SELECT 'cd_silver_direct_costs', 'missing id (direct_costs)', payload, _batch_id
FROM cd_bronze_procore_direct_costs WHERE get_json_object(payload, '$.id') IS NULL
UNION ALL
SELECT 'cd_silver_direct_cost_lines', 'missing id (direct_cost_line_items)', payload, _batch_id
FROM cd_bronze_procore_direct_cost_line_items WHERE get_json_object(payload, '$.id') IS NULL
UNION ALL
SELECT 'cd_silver_qc_inspection', 'missing id (checklist_lists)', payload, _batch_id
FROM cd_bronze_procore_checklist_lists WHERE get_json_object(payload, '$.id') IS NULL
UNION ALL
SELECT 'cd_silver_commitments', 'missing id (work_order_contracts)', payload, _batch_id
FROM cd_bronze_procore_work_order_contracts WHERE get_json_object(payload, '$.id') IS NULL
UNION ALL
SELECT 'cd_silver_commitments', 'missing id (purchase_order_contracts)', payload, _batch_id
FROM cd_bronze_procore_purchase_order_contracts WHERE get_json_object(payload, '$.id') IS NULL
UNION ALL
SELECT 'cd_silver_commitment_lines', 'missing id (work_order_contract_line_items)', payload, _batch_id
FROM cd_bronze_procore_work_order_contract_line_items WHERE get_json_object(payload, '$.id') IS NULL
UNION ALL
SELECT 'cd_silver_commitment_lines', 'missing id (purchase_order_contract_line_items)', payload, _batch_id
FROM cd_bronze_procore_purchase_order_contract_line_items WHERE get_json_object(payload, '$.id') IS NULL
UNION ALL
SELECT 'cd_silver_manpower_daily', 'missing date', payload, _batch_id
FROM cd_bronze_procore_manpower_logs WHERE get_json_object(payload, '$.date') IS NULL
UNION ALL
SELECT 'cd_silver_project_vendors',
       CASE WHEN get_json_object(payload, '$.id') IS NULL AND _project_id IS NULL
            THEN 'missing id and project'
            WHEN get_json_object(payload, '$.id') IS NULL THEN 'missing id'
            ELSE 'missing project' END, payload, _batch_id
FROM cd_bronze_procore_project_vendors
WHERE get_json_object(payload, '$.id') IS NULL OR _project_id IS NULL
UNION ALL
SELECT 'cd_silver_vendor_insurance',
       CASE WHEN get_json_object(payload, '$.id') IS NULL AND get_json_object(payload, '$.vendor_id') IS NULL
            THEN 'missing id and vendor id'
            WHEN get_json_object(payload, '$.id') IS NULL THEN 'missing id'
            ELSE 'missing vendor id' END, payload, _batch_id
FROM cd_bronze_procore_company_insurances
WHERE get_json_object(payload, '$.id') IS NULL OR get_json_object(payload, '$.vendor_id') IS NULL;
