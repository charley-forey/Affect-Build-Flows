-- gold: bridge_ProjectVendor - which vendors are on which projects, with prequal detail.
--
-- 393 (project, vendor) pairs over 251 distinct vendors.
--
-- This is deliverable D8, the vendor and insurance list, and it is the quick win because
-- the data was already landed. Today that list is assembled by hand from Procore's UI
-- whenever somebody asks for it.
--
-- A BRIDGE, NOT A FACT. It has no measure and no date - it exists so dim_Vendor can be
-- filtered by project, which a direct relationship cannot do when a vendor works on five
-- jobs. Named `bridge_` rather than `dim_` so nobody points a fact at it by mistake.
--
-- WHAT THIS IS NOT: an insurance compliance record. Procore holds certificates on a
-- separate endpoint we do not have permission to read. IsPrequalified and LicenseNumber
-- are what Procore has, and a vendor can be prequalified with expired insurance. Anyone
-- reading this as "cleared to work" is reading more into it than it says.

CREATE OR REPLACE TABLE bridge_ProjectVendor AS
SELECT
    project_id                       AS ProjectKey,
    vendor_id                        AS VendorKey,
    vendor_name                      AS VendorName,
    trade_name                       AS TradeName,
    city                             AS City,
    state_code                       AS StateCode,
    business_phone                   AS BusinessPhone,
    email_address                    AS EmailAddress,
    license_number                   AS LicenseNumber,
    labor_union                      AS LaborUnion,
    is_prequalified                  AS IsPrequalified,
    is_active                        AS IsActive,
    is_union_member                  AS IsUnionMember,
    -- A vendor invoiced through Procore but never written back to Sage is a reconciliation
    -- gap: the cost exists in one system and not the other, and nothing today would show
    -- it. Surfaced rather than assumed clean.
    synced_to_erp                    AS SyncedToErp,
    (COALESCE(synced_to_erp, FALSE) = FALSE) AS IsMissingFromErp
FROM sv_project_vendors
WHERE project_id IS NOT NULL
  AND vendor_id IS NOT NULL;
