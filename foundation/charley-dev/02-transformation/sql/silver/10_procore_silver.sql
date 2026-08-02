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
    -- The Sage counterpart is not on the Procore vendor record; it is resolved in gold
    -- against the existing crosswalk. NULL here is correct, not missing data.
    CAST(NULL AS STRING)                                  AS sage_vendor_id,
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
-- Bracket notation is required: these names contain spaces, parentheses, apostrophes and
-- "=". get_json_object supports $['...'] for exactly this.
CREATE OR REPLACE TABLE cd_silver_budgets AS
WITH ranked AS (
SELECT
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
  -- REQUIRE THE CM VIEW'S SIGNATURE. Bronze is append-and-merge, so rows pulled before the
  -- registry pinned the view are still there - 76 of them, from "Procore Standard
  -- Forecast", which has none of these money columns. They merge in with NULL budgets and
  -- inflate the fact (480 rows where 404 are real) while dragging every budget measure
  -- toward zero.
  --
  -- Filtering on a signature column rather than cleaning bronze is deliberate: bronze is
  -- meant to be an append-only record of what the API returned, including supersededed
  -- shapes. Silver is where a shape is chosen. This also stays correct if a second view is
  -- ever added to the registry by mistake.
  AND json_field(payload, 'UPDATED PRIME CONTRACT BUDGET (D = A+B+C)') IS NOT NULL
)
-- ONE ROW PER PROJECT + COST CODE, LATEST SNAPSHOT WINS.
--
-- Bronze is append-and-merge and keeps every shape the API ever returned - including rows
-- pulled before the registry pinned the budget view. Those merge in under different row
-- ids and inflate the fact (480 rows where 404 are real), dragging every budget measure
-- toward zero without failing anything.
--
-- Deduping here rather than cleaning bronze is deliberate on both counts: bronze is meant
-- to be an append-only record of what the API said, and "one budget row per cost code, as
-- of the latest snapshot" is what this table means anyway. It is the correct semantic, not
-- a workaround that happens to fix a count.
SELECT project_id, cost_code_id, cost_code, category,
       original_budget, budget_modifications, updated_budget, forecast_budget,
       committed_to_date, direct_costs, invoiced_to_date, cost_to_complete,
       snapshot_date, _ingested_at, _batch_id
FROM (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY project_id, cost_code_id ORDER BY _ingested_at DESC
    ) AS _rn
    FROM ranked
)
WHERE _rn = 1;

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
    CAST(get_json_object(payload, '$.cost_code.id') AS STRING) AS cost_code_id,
    CASE WHEN CAST(get_json_object(payload, '$.created_at') AS DATE) < DATE '1990-01-01'
         THEN NULL ELSE CAST(get_json_object(payload, '$.created_at') AS DATE) END
                                                           AS created_date,
    CASE WHEN CAST(get_json_object(payload, '$.required_on_site_date') AS DATE) < DATE '1990-01-01'
         THEN NULL ELSE CAST(get_json_object(payload, '$.required_on_site_date') AS DATE) END
                                                           AS due_date,
    CASE WHEN CAST(get_json_object(payload, '$.received_date') AS DATE) < DATE '1990-01-01'
         THEN NULL ELSE CAST(get_json_object(payload, '$.received_date') AS DATE) END
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
SELECT 'cd_silver_submittals', 'missing id', payload, _batch_id
FROM cd_bronze_procore_submittals WHERE get_json_object(payload, '$.id') IS NULL
UNION ALL
SELECT 'cd_silver_rfis', 'missing id', payload, _batch_id
FROM cd_bronze_procore_rfis WHERE get_json_object(payload, '$.id') IS NULL;
