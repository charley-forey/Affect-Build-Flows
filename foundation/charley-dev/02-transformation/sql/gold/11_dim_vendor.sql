-- gold: dim_Vendor - Procore vendors with their Sage counterpart.
--
-- VendorKey is the Procore vendor id, for the same reason as dim_Project: stable, already
-- on the facts, and debuggable.
--
-- The Jul 23 warehouse review identified vendor linkage as the core modelling problem:
-- "some tables have cost-code ID, some don't; some have vendor ID, some don't". This
-- dimension is the anchor for resolving that - the bridging happens on the fact side.
--
-- VendorKey 'UNASSIGNED' exists so a fact with no vendor still appears. Dropping such rows
-- from an inner join is how a total silently stops reconciling.

CREATE OR REPLACE TABLE dim_Vendor AS
SELECT
    'UNASSIGNED' AS VendorKey,
    'Unassigned' AS VendorName,
    CAST(NULL AS STRING) AS SageVendorId,
    FALSE AS HasSageMatch

UNION ALL

SELECT
    procore_vendor_id AS VendorKey,
    -- TRIM everywhere on the way in: source text carries trailing whitespace, and
    -- "Metals  " never equals "Metals" in a join (Excel defect #9, same class of bug).
    TRIM(vendor_name) AS VendorName,
    sage_vendor_id    AS SageVendorId,
    CASE WHEN sage_vendor_id IS NULL OR sage_vendor_id = '' THEN FALSE ELSE TRUE END AS HasSageMatch
FROM sv_vendors
WHERE procore_vendor_id IS NOT NULL;
