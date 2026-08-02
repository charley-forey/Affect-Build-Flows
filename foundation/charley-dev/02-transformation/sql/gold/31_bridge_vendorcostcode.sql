-- gold: bridge_VendorCostCode - what each vendor is spent with, and committed to, per cost
-- code.
--
-- PHASE 0 ITEM 3, the linkage the engagement was scoped to resolve: "resolve the vendor
-- <-> cost-code linkage (invoice as the bridge) so the model slices by both".
--
-- It exists in no single Procore object. Both halves have the same shape:
--
--   DIRECT COSTS   header carries the vendor, line items carry the cost code
--   COMMITMENTS    header carries the vendor, line items carry the cost code
--
-- so both are joined on the line's `holder`, which is the header that owns it.
--
-- ===========================================================================
-- COMMITTED IS NOT SPENT. THE TWO ARE NEVER ADDED TOGETHER.
-- ===========================================================================
--
-- A direct cost line is money that has gone out. A commitment line is money that has been
-- promised. They are both "vendor money against a cost code", which is what makes it
-- tempting to sum them into one number - and that number would be nonsense: it counts the
-- same work once when it was committed and again when it was paid, and it flatters every
-- vendor total by roughly the amount of work in progress.
--
-- So AmountType is part of the GRAIN, not a label bolted on afterwards. A row is either
-- actual or committed, never a blend, and [Vendor Spend] and [Vendor Committed] each
-- filter to one of them. Anyone who writes SUM(Amount) without a filter gets a number that
-- is obviously too big rather than one that is quietly wrong.
--
-- GRAIN: (project, vendor, cost code, amount type). Line items are rolled up - the
-- question this answers is "what have we spent with this vendor on this code", not "what
-- was on line 3"; fct_DirectCost still holds the transactions.

CREATE OR REPLACE TABLE bridge_VendorCostCode AS
WITH direct_lines AS (
    SELECT
        l.project_id,
        d.vendor_id,
        d.vendor_name,
        l.cost_code_id,
        l.cost_code,
        l.cost_code_name,
        'Actual'                            AS amount_type,
        'Direct cost'                       AS source_label,
        l.direct_cost_id                    AS parent_id,
        COALESCE(l.total_amount, l.amount)  AS line_amount
    FROM sv_direct_cost_lines l
    -- Only lines whose holder really is a direct cost. Procore reuses `holder` across
    -- object types, and a Commitment::Item joined on id alone would be attributed to
    -- whichever direct cost happened to share that id.
    JOIN sv_direct_costs d ON d.direct_cost_id = l.direct_cost_id
    WHERE l.holder_type = 'DirectCost::Item'
      AND l.cost_code_id IS NOT NULL
      AND d.vendor_id IS NOT NULL
),
commitment_lines AS (
    SELECT
        c.project_id,
        c.vendor_id,
        c.vendor_name,
        l.cost_code_id,
        l.cost_code,
        l.cost_code_name,
        'Committed'                         AS amount_type,
        c.commitment_type                   AS source_label,
        l.commitment_id                     AS parent_id,
        COALESCE(l.total_amount, l.amount)  AS line_amount
    FROM sv_commitment_lines l
    JOIN sv_commitments c ON c.commitment_id = l.commitment_id
    WHERE l.cost_code_id IS NOT NULL
      AND c.vendor_id IS NOT NULL
      -- The holder_type must match the endpoint the line came from. A work order id and a
      -- purchase order id are different id spaces that can collide, so joining without
      -- this can attach a subcontract line to an unrelated purchase order.
      AND ((l.holder_type = 'WorkOrderContract'     AND c.commitment_type = 'Subcontract')
        OR (l.holder_type = 'PurchaseOrderContract' AND c.commitment_type = 'Purchase Order'))
),
combined AS (
    SELECT * FROM direct_lines
    UNION ALL
    SELECT * FROM commitment_lines
)
SELECT
    CONCAT_WS('|', project_id, vendor_id, cost_code_id, amount_type) AS VendorCostCodeKey,
    project_id                       AS ProjectKey,
    vendor_id                        AS VendorKey,
    MAX(vendor_name)                 AS VendorName,
    cost_code_id                     AS CostCodeKey,
    MAX(cost_code)                   AS CostCode,
    MAX(cost_code_name)              AS CostCodeName,
    amount_type                      AS AmountType,
    -- Direct cost / Subcontract / Purchase Order, kept beside AmountType so the report can
    -- separate subcontract from supply without re-deriving it.
    MAX(source_label)                AS SourceLabel,
    SUM(line_amount)                 AS Amount,
    COUNT(*)                         AS LineItemCount,
    COUNT(DISTINCT parent_id)        AS ParentCount,
    (amount_type = 'Actual')         AS IsActual
FROM combined
GROUP BY project_id, vendor_id, cost_code_id, amount_type;
