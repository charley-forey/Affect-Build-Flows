-- silver: the vendor <-> cost-code bridge, and vendor insurance.
--
-- These two close the two Phase 0 scope items that were still open:
--
--   item 3  "resolve the vendor <-> cost-code linkage (invoice as the bridge) so the model
--            slices by both"                                                      (4 hrs)
--   item 4  "vendor list with insurance and contract info"                        (3 hrs)
--
-- ---------------------------------------------------------------------------
-- Direct cost line items - the bridge itself
-- ---------------------------------------------------------------------------
--
-- The linkage does not exist in any single Procore object. The direct cost HEADER carries
-- vendor_id and no cost code; its LINE ITEMS carry cost_code and no vendor. Joining them
-- is the bridge, and `holder` is the join - it points back at the header that owns the
-- line.
--
-- This is the "invoice as the bridge" the engagement was scoped around, and it is the
-- honest version of it: a direct cost line is money actually spent with a named vendor
-- against a named cost code. A budget or a commitment would only say what was intended.
--
-- 509 of 509 lines carry a cost code, verified against the live payload 2026-08-02.

CREATE OR REPLACE TABLE cd_silver_direct_cost_lines AS
SELECT
    CAST(_project_id                                        AS STRING) AS project_id,
    CAST(get_json_object(payload, '$.id')                   AS STRING) AS line_item_id,
    -- holder.id is the direct cost this line belongs to. holder_type is carried so a
    -- future holder ("DirectCost::Item" today) cannot silently join to the wrong table.
    CAST(get_json_object(payload, '$.holder.id')            AS STRING) AS direct_cost_id,
    TRIM(get_json_object(payload, '$.holder.holder_type'))             AS holder_type,
    CAST(get_json_object(payload, '$.cost_code.id')         AS STRING) AS cost_code_id,
    -- full_code is the CSI code ("01-00-00"); name repeats it with the description
    -- attached ("01-00-00 - GENERAL REQUIREMENTS"). Taking full_code is the fix for the
    -- defect that left 5,429 of 5,433 divisions unparsed - that one exposed the name and
    -- then tried to read a code out of it.
    TRIM(get_json_object(payload, '$.cost_code.full_code'))            AS cost_code,
    TRIM(get_json_object(payload, '$.cost_code.name'))                 AS cost_code_name,
    TRIM(get_json_object(payload, '$.description'))                    AS description,
    TRIM(get_json_object(payload, '$.line_item_type.name'))            AS line_item_type,
    CAST(get_json_object(payload, '$.amount')               AS DOUBLE) AS amount,
    CAST(get_json_object(payload, '$.total_amount')         AS DOUBLE) AS total_amount,
    CAST(get_json_object(payload, '$.quantity')             AS DOUBLE) AS quantity,
    CAST(get_json_object(payload, '$.unit_cost')            AS DOUBLE) AS unit_cost,
    TRIM(get_json_object(payload, '$.uom'))                            AS unit_of_measure,
    _ingested_at, _batch_id
FROM cd_bronze_procore_direct_cost_line_items
WHERE get_json_object(payload, '$.id') IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Vendor insurance - the half of D8 that shipped missing
-- ---------------------------------------------------------------------------
--
-- The vendor list went out without insurance because nothing carried it. This does.
--
-- WHAT THE LIVE DATA SAYS, and it needs stating plainly rather than being rendered as a
-- tidy green column. As of 2026-08-02:
--
--   * 105 certificates, and ALL 105 are past their expiration date. The most recent
--     expiry is 2025-04-01 - sixteen months ago.
--   * Every one carries Procore's own status of `non_compliant`.
--   * Only 23 of 251 vendors have any certificate on file at all.
--
-- That does NOT prove Affect's subcontractors are uninsured. The likelier reading is that
-- the Procore insurance module stopped being maintained and certificates now live
-- somewhere else. But the two readings have very different consequences for a general
-- contractor, and nothing in the current reporting distinguishes them - or even raises the
-- question. So the columns below are built to make the distinction visible: coverage
-- (does a record exist at all) is kept separate from currency (is it in date).

CREATE OR REPLACE TABLE cd_silver_vendor_insurance AS
SELECT
    CAST(get_json_object(payload, '$.id')                   AS STRING) AS insurance_id,
    CAST(get_json_object(payload, '$.vendor_id')            AS STRING) AS vendor_id,
    -- Free text, and it shows: "Commercial General Liability ", "GL", "Umbrella Liability "
    -- and "Umbrella Liab Excess Liab" all appear. Trimmed but deliberately NOT bucketed -
    -- guessing that "Umbrella Liab Excess Liab" means the same as "Excess Liability" is
    -- the kind of tidying that turns a data-entry problem into a reporting one.
    TRIM(get_json_object(payload, '$.insurance_type'))                 AS insurance_type,
    TRIM(get_json_object(payload, '$.insurance_provider'))             AS provider,
    NULLIF(TRIM(get_json_object(payload, '$.policy_number')), '')      AS policy_number,
    UPPER(TRIM(get_json_object(payload, '$.status')))                  AS status_label,
    CAST(get_json_object(payload, '$.effective_date')       AS DATE)   AS effective_date,
    CAST(get_json_object(payload, '$.expiration_date')      AS DATE)   AS expiration_date,
    -- `limit` arrives as a string and reads "24.0" on the sample record, which is not a
    -- dollar limit at any plausible scale. Carried as-is rather than multiplied by a
    -- guessed factor: a wrong coverage limit on a compliance report is worse than none,
    -- and this is a question for Affect, not an inference for us.
    CAST(get_json_object(payload, '$.limit')                AS DOUBLE) AS coverage_limit_raw,
    CAST(get_json_object(payload, '$.exempt')               AS BOOLEAN) AS is_exempt,
    CAST(get_json_object(payload, '$.info_received')        AS BOOLEAN) AS info_received,
    CAST(get_json_object(payload, '$.additional_insured')   AS BOOLEAN) AS additional_insured,
    NULLIF(TRIM(get_json_object(payload, '$.notes')), '')              AS notes,
    _ingested_at, _batch_id
FROM cd_bronze_procore_company_insurances
WHERE get_json_object(payload, '$.id') IS NOT NULL
  AND get_json_object(payload, '$.vendor_id') IS NOT NULL;
