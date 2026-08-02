-- silver: progress billing, direct costs, and the project-vendor bridge.
--
-- These three feeds landed in bronze and were parsed by nothing. Data that is extracted and
-- never read costs capacity and creates the impression of coverage, which is worse than not
-- having pulled it.
--
-- THE HEADLINE: RETAINAGE IS HERE.
--
-- fct_Invoice says, correctly, that retainage is absent from Sage: `retain` on the invoice
-- header is ZERO across all 940 invoices (verified in db0d11e), so it is not held at header
-- level for this company. That left three candidates - `arivln`, `actrec.retain`, or
-- progress billing - and the first two need the on-prem gateway Affect has not bound yet.
--
-- It is progress billing, and it is already in our bronze. Verified against Affect's
-- tenant 2026-08-02, read back through the model:
--
--     owner retainage held    $830,725.87
--     sub retainage held      $486,030.04
--     net position            $344,695.83   owed to Affect, less what Affect holds
--
-- Those are CURRENT balances, taken from the latest issued billing per contract. The
-- retainage columns are restated in full every period, so adding them up across 607 rows
-- gives $9,046,211.75 - a figure that looks like a plausible retainage number and is
-- nearly seven times the real one. See gold/27_fct_billing.sql.
--
-- So retainage does not need the Sage gateway at all. That closes open question #4 and
-- removes it from the blocker list.
--
-- ONE TABLE, NOT TWO. Requisitions (money we owe subs) and payment applications (money the
-- owner owes us) are different directions of the same transaction, and Procore gives them
-- the IDENTICAL 21-field AIA G702 block - `summary` on one, `g702` on the other, same keys.
-- Unioning them means one fact, one set of measures and one page section, sliced by
-- direction, instead of two of everything that then have to be kept in step.
--
-- FIELD NAMES ARE FROM THE LIVE PAYLOAD. Confirmed by reading the landed JSONL, not the
-- docs - the last time these were assumed, every budget money column parsed to NULL and
-- produced a model that looked healthy and reported nothing.

-- ---------------------------------------------------------------------------
-- Progress billing - the AIA G702, both directions
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE cd_silver_billing AS
WITH requisitions AS (
    SELECT
        'Subcontractor'                                                     AS billing_type,
        CAST(_project_id                                        AS STRING)  AS project_id,
        CAST(get_json_object(payload, '$.id')                   AS STRING)  AS billing_id,
        TRIM(get_json_object(payload, '$.invoice_number'))                  AS invoice_number,
        CAST(get_json_object(payload, '$.number')               AS INT)     AS period_number,
        UPPER(TRIM(get_json_object(payload, '$.status')))                   AS status_label,
        -- Sub side: the counterparty is the vendor, and the contract is the commitment.
        CAST(get_json_object(payload, '$.vendor_id')            AS STRING)  AS vendor_id,
        TRIM(get_json_object(payload, '$.vendor_name'))                     AS counterparty_name,
        CAST(get_json_object(payload, '$.commitment_id')        AS STRING)  AS contract_id,
        TRIM(get_json_object(payload, '$.contract_name'))                   AS contract_name,
        TRIM(get_json_object(payload, '$.commitment_type'))                 AS contract_type,
        CAST(get_json_object(payload, '$.billing_date')         AS DATE)    AS billing_date,
        CAST(get_json_object(payload, '$.requisition_start')    AS DATE)    AS period_start,
        CAST(get_json_object(payload, '$.requisition_end')      AS DATE)    AS period_end,
        CAST(get_json_object(payload, '$.payment_date')         AS DATE)    AS payment_date,
        -- "9.28%" WITH the sign on this endpoint and "25.07" WITHOUT it on the other. An
        -- uncleaned CAST of the first returns NULL - silently, on a column that reads as a
        -- perfectly reasonable zero percent complete. Stripped on both sides so neither
        -- endpoint's formatting can decide whether the number exists.
        CAST(replace(TRIM(get_json_object(payload, '$.percent_complete')), '%', '')
                                                                AS DOUBLE)  AS percent_complete,
        -- The G702 block, lifted whole. Procore hangs the identical 21 keys off `summary`
        -- here and off `g702` on the other endpoint, so pulling the sub-object out is what
        -- lets the union share one set of field paths below.
        --
        -- Extracted as an object rather than by building paths like concat(prefix, key):
        -- Spark's get_json_object wants a constant path, and a per-row one is at best slow
        -- and at worst rejected outright.
        get_json_object(payload, '$.summary')                               AS g702,
        _ingested_at, _batch_id
    FROM cd_bronze_procore_requisitions
    WHERE get_json_object(payload, '$.id') IS NOT NULL
),
payment_apps AS (
    SELECT
        'Owner'                                                             AS billing_type,
        CAST(_project_id                                        AS STRING)  AS project_id,
        CAST(get_json_object(payload, '$.id')                   AS STRING)  AS billing_id,
        TRIM(get_json_object(payload, '$.invoice_number'))                  AS invoice_number,
        CAST(get_json_object(payload, '$.number')               AS INT)     AS period_number,
        UPPER(TRIM(get_json_object(payload, '$.status')))                   AS status_label,
        -- Owner side: no vendor. The counterparty is the client, and the contract is the
        -- prime contract.
        CAST(NULL                                               AS STRING)  AS vendor_id,
        TRIM(get_json_object(payload, '$.formatted_contract_company'))      AS counterparty_name,
        CAST(get_json_object(payload, '$.contract.id')          AS STRING)  AS contract_id,
        TRIM(get_json_object(payload, '$.contract.title'))                  AS contract_name,
        TRIM(get_json_object(payload, '$.contract.type'))                   AS contract_type,
        CAST(get_json_object(payload, '$.billing_date')         AS DATE)    AS billing_date,
        CAST(get_json_object(payload, '$.period_start')         AS DATE)    AS period_start,
        CAST(get_json_object(payload, '$.period_end')           AS DATE)    AS period_end,
        CAST(NULL                                               AS DATE)    AS payment_date,
        CAST(replace(TRIM(get_json_object(payload, '$.percent_complete')), '%', '')
                                                                AS DOUBLE)  AS percent_complete,
        get_json_object(payload, '$.g702')                                  AS g702,
        _ingested_at, _batch_id
    FROM cd_bronze_procore_payment_applications
    WHERE get_json_object(payload, '$.id') IS NOT NULL
),
combined AS (
    SELECT * FROM requisitions
    UNION ALL
    SELECT * FROM payment_apps
)
SELECT
    billing_type, project_id, billing_id, invoice_number, period_number, status_label,
    vendor_id, counterparty_name, contract_id, contract_name, contract_type,
    billing_date, period_start, period_end, payment_date, percent_complete,

    -- The G702 block. Same 21 keys on both endpoints, so it is read once here against the
    -- sub-object each branch lifted out - constant paths, one definition per field.
    CAST(get_json_object(g702, '$.original_contract_sum')
                                                    AS DOUBLE) AS original_contract_sum,
    CAST(get_json_object(g702, '$.net_change_by_change_orders')
                                                    AS DOUBLE) AS net_change_by_change_orders,
    CAST(get_json_object(g702, '$.contract_sum_to_date')
                                                    AS DOUBLE) AS contract_sum_to_date,
    CAST(get_json_object(g702, '$.total_completed_and_stored_to_date')
                                                    AS DOUBLE) AS completed_to_date,
    -- Retainage. The whole reason this table exists.
    CAST(get_json_object(g702, '$.completed_work_retainage_amount')
                                                    AS DOUBLE) AS retainage_amount,
    CAST(get_json_object(g702, '$.completed_work_retainage_percent')
                                                    AS DOUBLE) AS retainage_percent,
    CAST(get_json_object(g702, '$.stored_materials_retainage_amount')
                                                    AS DOUBLE) AS stored_retainage_amount,
    CAST(get_json_object(g702, '$.total_retainage')
                                                    AS DOUBLE) AS total_retainage,
    CAST(get_json_object(g702, '$.total_earned_less_retainage')
                                                    AS DOUBLE) AS earned_less_retainage,
    CAST(get_json_object(g702, '$.less_previous_certificates_for_payment')
                                                    AS DOUBLE) AS previous_certificates,
    CAST(get_json_object(g702, '$.current_payment_due')
                                                    AS DOUBLE) AS current_payment_due,
    CAST(get_json_object(g702, '$.balance_to_finish_including_retainage')
                                                    AS DOUBLE) AS balance_to_finish,
    _ingested_at, _batch_id
FROM combined;

-- ---------------------------------------------------------------------------
-- Direct costs - payroll and expenses charged straight to the job
-- ---------------------------------------------------------------------------
--
-- 418 rows: 313 expense, 99 payroll, 6 invoice. This is the only place self-performed
-- labour cost appears anywhere in the platform - it is not in a commitment, not in a
-- requisition, and not in the budget's committed column. Cost-to-date without it
-- understates every job that Affect's own crews work on.

CREATE OR REPLACE TABLE cd_silver_direct_costs AS
SELECT
    CAST(_project_id                                        AS STRING) AS project_id,
    CAST(get_json_object(payload, '$.id')                   AS STRING) AS direct_cost_id,
    TRIM(get_json_object(payload, '$.description'))                    AS description,
    -- payroll | expense | invoice. Payroll is the interesting one: it is the self-performed
    -- labour that no other feed carries.
    LOWER(TRIM(get_json_object(payload, '$.direct_cost_type')))        AS cost_type,
    UPPER(TRIM(get_json_object(payload, '$.status')))                  AS status_label,
    CAST(get_json_object(payload, '$.vendor_id')            AS STRING) AS vendor_id,
    TRIM(get_json_object(payload, '$.vendor_name'))                    AS vendor_name,
    TRIM(get_json_object(payload, '$.employee.name'))                  AS employee_name,
    CAST(get_json_object(payload, '$.direct_cost_date')     AS DATE)   AS cost_date,
    -- `amount` is the line total and `grand_total` includes tax and freight. Both kept:
    -- grand_total is what hits the job, amount is what reconciles to the source document.
    CAST(get_json_object(payload, '$.amount')               AS DOUBLE) AS amount,
    CAST(get_json_object(payload, '$.grand_total')          AS DOUBLE) AS grand_total,
    _ingested_at, _batch_id
FROM cd_bronze_procore_direct_costs
WHERE get_json_object(payload, '$.id') IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Project-vendor bridge - who is working on what, with the prequal detail
-- ---------------------------------------------------------------------------
--
-- The grain is (project, vendor): 393 pairs over 251 distinct vendors.
--
-- The payload also carries a `project_ids` ARRAY, and exploding it would look like the more
-- complete answer. It is not. That array lists every project the vendor is attached to in
-- Procore INCLUDING ones our extraction could not read - two projects return 403 - so
-- exploding it manufactures pairs pointing at projects that are not in dim_Project, which
-- arrive as orphans. `_project_id` is stamped by the extractor from the path it actually
-- called, so it describes what we genuinely observed. Narrower and true beats wider and
-- partly invented.

CREATE OR REPLACE TABLE cd_silver_project_vendors AS
SELECT
    CAST(_project_id                                        AS STRING) AS project_id,
    CAST(get_json_object(payload, '$.id')                   AS STRING) AS vendor_id,
    TRIM(get_json_object(payload, '$.name'))                           AS vendor_name,
    TRIM(get_json_object(payload, '$.trade_name'))                     AS trade_name,
    TRIM(get_json_object(payload, '$.city'))                           AS city,
    TRIM(get_json_object(payload, '$.state_code'))                     AS state_code,
    TRIM(get_json_object(payload, '$.business_phone'))                 AS business_phone,
    TRIM(get_json_object(payload, '$.email_address'))                  AS email_address,
    -- The compliance columns. Affect's D8 deliverable is a vendor and insurance list, and
    -- these are the fields Procore holds for it. Insurance certificates themselves are a
    -- separate endpoint we do not have permission for yet - noted so nobody reads this
    -- table as a complete compliance record.
    CAST(get_json_object(payload, '$.prequalified')         AS BOOLEAN) AS is_prequalified,
    CAST(get_json_object(payload, '$.is_active')            AS BOOLEAN) AS is_active,
    CAST(get_json_object(payload, '$.union_member')         AS BOOLEAN) AS is_union_member,
    NULLIF(TRIM(get_json_object(payload, '$.license_number')), '')      AS license_number,
    NULLIF(TRIM(get_json_object(payload, '$.labor_union')), '')         AS labor_union,
    -- Written back to the ERP. A vendor invoiced through Procore but never synced to Sage
    -- is a reconciliation gap worth being able to see.
    CAST(get_json_object(payload, '$.synced_to_erp')        AS BOOLEAN) AS synced_to_erp,
    _ingested_at, _batch_id
FROM cd_bronze_procore_project_vendors
WHERE get_json_object(payload, '$.id') IS NOT NULL
  AND _project_id IS NOT NULL;
