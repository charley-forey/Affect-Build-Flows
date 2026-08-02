-- gold: bridge_VendorCostCode - which vendors are spent with against which cost codes.
--
-- PHASE 0 ITEM 3, the linkage the engagement was scoped to resolve: "resolve the vendor
-- <-> cost-code linkage (invoice as the bridge) so the model slices by both".
--
-- It exists in no single Procore object. The direct cost header carries the vendor and no
-- cost code; the line items carry the cost code and no vendor. This joins them on the
-- line's `holder`, which is the header that owns it.
--
-- GRAIN: one row per (project, vendor, cost code). Line items are rolled up, because the
-- question this answers is "what have we spent with this vendor on this code", not "what
-- was on line 3 of that invoice" - fct_DirectCost still holds the transactions.
--
-- WHY THIS IS A BRIDGE AND NOT A FACT. It has an additive measure on it (SpendAmount) and
-- could be read as a fact, but its job is to let dim_Vendor and dim_CostCode filter each
-- other, which neither can do directly - a vendor works across many codes and a code is
-- used by many vendors. Named `bridge_` so nobody points another fact at it.
--
-- WHAT IT DOES NOT COVER, stated because a partial bridge that looks total is worse than
-- an obviously partial one: this is DIRECT costs only. Subcontract spend flows through
-- commitments, whose line items also carry cost codes and are not yet extracted (that is a
-- per-contract nested pull, hundreds of calls against a 600/hour limit). So this answers
-- "what have we spent DIRECTLY with this vendor on this code" completely, and the
-- subcontract half is still to come. IsDirectCostOnly makes that explicit on every row
-- rather than in a footnote nobody reads.

CREATE OR REPLACE TABLE bridge_VendorCostCode AS
WITH lines AS (
    SELECT
        l.project_id,
        l.cost_code_id,
        l.cost_code,
        l.cost_code_name,
        l.direct_cost_id,
        -- total_amount includes tax and freight where the line carries them; amount is the
        -- bare line. Spend should be what actually hit the job.
        COALESCE(l.total_amount, l.amount) AS line_amount
    FROM sv_direct_cost_lines l
    -- Only lines whose holder really is a direct cost. Today every row says
    -- "DirectCost::Item", but Procore reuses `holder` across object types and a new one
    -- appearing would otherwise join silently to the wrong header.
    WHERE l.holder_type = 'DirectCost::Item'
      AND l.cost_code_id IS NOT NULL
)
SELECT
    CONCAT_WS('|', l.project_id, d.vendor_id, l.cost_code_id) AS VendorCostCodeKey,
    l.project_id                     AS ProjectKey,
    d.vendor_id                      AS VendorKey,
    d.vendor_name                    AS VendorName,
    l.cost_code_id                   AS CostCodeKey,
    l.cost_code                       AS CostCode,
    l.cost_code_name                 AS CostCodeName,
    SUM(l.line_amount)               AS SpendAmount,
    COUNT(*)                         AS LineItemCount,
    COUNT(DISTINCT l.direct_cost_id) AS DirectCostCount,
    TRUE                             AS IsDirectCostOnly
FROM lines l
-- INNER JOIN, deliberately. A line whose header we do not have cannot be attributed to a
-- vendor, and a bridge row with a NULL vendor would quietly become an "unallocated"
-- bucket that every vendor-filtered view excludes without saying so. Lines that fail to
-- join are counted by the DQ suite instead, where the number is visible.
JOIN sv_direct_costs d
  ON d.direct_cost_id = l.direct_cost_id
WHERE d.vendor_id IS NOT NULL
GROUP BY l.project_id, d.vendor_id, d.vendor_name,
         l.cost_code_id, l.cost_code, l.cost_code_name;
