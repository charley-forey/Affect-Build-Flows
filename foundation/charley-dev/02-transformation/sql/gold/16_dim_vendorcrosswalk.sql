-- gold: dim_VendorCrosswalk - one row per vendor, Procore <-> Sage.
--
-- The same shape as dim_ProjectCrosswalk and for the same reason, one level down: a vendor
-- present in Procore commitments but absent from Sage contributes zero spend to every
-- payables measure, silently.
--
-- WHERE THE MAPPING COMES FROM. Procore's ERP sync writes the Sage vendor id (actpay.recnum)
-- into the vendor's origin_code; 10_procore_silver.sql carries it as sage_vendor_id. Until
-- 2026-09-13 this read the existing warehouse's dim_procore_project_vendor (125 pairs); the
-- origin_code key reproduces all 125 and adds 808 more. DQ blocks on an id not in actpay or
-- a Sage vendor shared by two Procore vendors.
--
-- UNMATCHED VENDORS ARE KEPT. Most of the 1,098 will never appear in Sage - a vendor
-- invited to bid is not a vendor who was paid - so "unmatched" here is normal, not an
-- error. What matters is that a vendor WITH commitments and NO Sage id is visible, because
-- that one is a real gap.

CREATE OR REPLACE TABLE dim_VendorCrosswalk AS
WITH mapped AS (
    -- The crosswalk is per project-vendor, so one vendor can appear many times. Collapse to
    -- one row per Procore vendor, and count the distinct Sage ids so an ambiguous mapping
    -- is visible rather than silently resolved by MAX().
    SELECT
        procore_vendor_id,
        MAX(sage_vendor_id)                   AS sage_vendor_id,
        COUNT(DISTINCT sage_vendor_id)        AS sage_match_count,
        MAX(vendor_name)                      AS vendor_name
    FROM sv_vendors
    WHERE procore_vendor_id IS NOT NULL
    GROUP BY procore_vendor_id
)
SELECT
    m.procore_vendor_id                            AS VendorKey,
    TRIM(COALESCE(m.vendor_name, s.sage_vendor_name)) AS VendorName,
    m.procore_vendor_id                            AS ProcoreVendorId,
    m.sage_vendor_id                               AS SageVendorId,
    TRIM(s.sage_vendor_name)                       AS SageVendorName,

    TRUE                                           AS IsInProcore,
    (m.sage_vendor_id IS NOT NULL)                 AS IsInSage,

    CASE WHEN m.sage_vendor_id IS NOT NULL THEN 'CROSSWALK_TABLE' ELSE 'UNMATCHED' END
                                                   AS SageMatchMethod,
    COALESCE(m.sage_match_count, 0) > 1            AS HasAmbiguousSageMatch,

    -- The names disagreeing is worth seeing even when the ids match: it usually means one
    -- system was renamed and the other was not, and it is the cheapest early warning that
    -- a mapping has drifted.
    (m.sage_vendor_id IS NOT NULL
     AND s.sage_vendor_name IS NOT NULL
     AND UPPER(TRIM(m.vendor_name)) <> UPPER(TRIM(s.sage_vendor_name)))
                                                   AS HasNameMismatch
FROM mapped m
LEFT JOIN sv_sage_vendors s ON s.sage_vendor_id = m.sage_vendor_id;
