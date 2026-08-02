-- silver: commitments and their line items - the subcontract half of the bridge.
--
-- A commitment is money Affect has agreed to pay somebody: a work order contract is a
-- subcontract, a purchase order contract is a supply order. Procore keeps them as two
-- endpoints with the same shape, and they union here for the same reason requisitions and
-- payment applications do - one table, one set of measures, sliced by type.
--
-- Live as of 2026-08-02: 189 work orders + 109 purchase orders, 256 + 175 line items, and
-- EVERY line item carries a cost code.
--
-- THE POINT OF THIS FILE. The commitment HEADER carries the vendor; the LINE ITEMS carry
-- the cost code. Same split as direct costs, so the same join completes the other half of
-- bridge_VendorCostCode - the subcontract spend that direct costs cannot see.
--
-- COMMITTED IS NOT SPENT, and this distinction must survive into gold. A direct cost line
-- is money that has gone out. A commitment line is money that has been promised. Adding
-- them together produces a number that is neither, and it would flatter the vendor totals
-- by counting the same work twice - once when it was committed and again when it was paid.

CREATE OR REPLACE TABLE cd_silver_commitments AS
WITH work_orders AS (
    SELECT
        'Subcontract'                                            AS commitment_type,
        CAST(_project_id                             AS STRING)  AS project_id,
        CAST(get_json_object(payload, '$.id')        AS STRING)  AS commitment_id,
        payload, _ingested_at, _batch_id
    FROM cd_bronze_procore_work_order_contracts
    WHERE get_json_object(payload, '$.id') IS NOT NULL
),
purchase_orders AS (
    SELECT
        'Purchase Order'                                         AS commitment_type,
        CAST(_project_id                             AS STRING)  AS project_id,
        CAST(get_json_object(payload, '$.id')        AS STRING)  AS commitment_id,
        payload, _ingested_at, _batch_id
    FROM cd_bronze_procore_purchase_order_contracts
    WHERE get_json_object(payload, '$.id') IS NOT NULL
)
SELECT
    commitment_type, project_id, commitment_id,
    TRIM(get_json_object(payload, '$.number'))                   AS commitment_number,
    TRIM(get_json_object(payload, '$.title'))                    AS title,
    UPPER(TRIM(get_json_object(payload, '$.status')))            AS status_label,
    -- vendor.company is the NAME on this endpoint, not a nested company object - Procore
    -- reuses the word for both across its API, which is exactly the kind of thing that
    -- silently yields NULL when assumed rather than read.
    CAST(get_json_object(payload, '$.vendor.id')     AS STRING)  AS vendor_id,
    TRIM(get_json_object(payload, '$.vendor.company'))           AS vendor_name,
    CAST(get_json_object(payload, '$.grand_total')   AS DOUBLE)  AS grand_total,
    CAST(get_json_object(payload, '$.total_payments') AS DOUBLE) AS total_payments,
    CAST(get_json_object(payload, '$.total_requisitions_amount') AS DOUBLE)
                                                                 AS total_requisitioned,
    CAST(get_json_object(payload, '$.executed')      AS BOOLEAN) AS is_executed,
    _ingested_at, _batch_id
FROM (SELECT * FROM work_orders UNION ALL SELECT * FROM purchase_orders);

-- ---------------------------------------------------------------------------
-- Commitment line items - cost code per line
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE cd_silver_commitment_lines AS
WITH wo_lines AS (
    SELECT 'WorkOrderContract' AS expected_holder, payload, _project_id,
           _ingested_at, _batch_id
    FROM cd_bronze_procore_work_order_contract_line_items
    WHERE get_json_object(payload, '$.id') IS NOT NULL
),
po_lines AS (
    SELECT 'PurchaseOrderContract' AS expected_holder, payload, _project_id,
           _ingested_at, _batch_id
    FROM cd_bronze_procore_purchase_order_contract_line_items
    WHERE get_json_object(payload, '$.id') IS NOT NULL
)
SELECT
    CAST(_project_id                                       AS STRING) AS project_id,
    CAST(get_json_object(payload, '$.id')                  AS STRING) AS line_item_id,
    -- holder.id is the commitment. holder_type says which endpoint it came from, and it
    -- is kept rather than assumed: a work order id and a purchase order id are separate
    -- id spaces, so joining on the id alone could match the wrong contract entirely.
    CAST(get_json_object(payload, '$.holder.id')           AS STRING) AS commitment_id,
    TRIM(get_json_object(payload, '$.holder.holder_type'))            AS holder_type,
    expected_holder                                                   AS source_endpoint,
    CAST(get_json_object(payload, '$.cost_code.id')        AS STRING) AS cost_code_id,
    -- full_code, not name. `name` is "03-100 - CONCRETE" with the description glued on,
    -- and reading a code out of that is the defect that left 5,429 of 5,433 cost codes
    -- without a CSI division.
    TRIM(get_json_object(payload, '$.cost_code.full_code'))           AS cost_code,
    TRIM(get_json_object(payload, '$.cost_code.name'))                AS cost_code_name,
    TRIM(get_json_object(payload, '$.description'))                   AS description,
    TRIM(get_json_object(payload, '$.line_item_type.name'))           AS line_item_type,
    CAST(get_json_object(payload, '$.amount')              AS DOUBLE) AS amount,
    CAST(get_json_object(payload, '$.total_amount')        AS DOUBLE) AS total_amount,
    CAST(get_json_object(payload, '$.quantity')            AS DOUBLE) AS quantity,
    CAST(get_json_object(payload, '$.unit_cost')           AS DOUBLE) AS unit_cost,
    _ingested_at, _batch_id
FROM (SELECT * FROM wo_lines UNION ALL SELECT * FROM po_lines);
