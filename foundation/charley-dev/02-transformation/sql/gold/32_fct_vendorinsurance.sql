-- gold: fct_VendorInsurance - certificates of insurance, per vendor.
--
-- The other half of D8, "vendor list with insurance and contract info". The vendor list
-- shipped without it because nothing in the model carried insurance.
--
-- WHAT THE DATA SAYS, as of 2026-08-02. This belongs at the top of the file rather than
-- discovered later by whoever reads a card:
--
--     105 certificates on file, and ALL 105 are past expiry.
--     The most recent expiration date is 2025-04-01 - sixteen months ago.
--     Every record carries Procore's own status of `non_compliant`.
--     Only 23 of 251 vendors have any certificate at all.
--
-- This is NOT evidence that Affect's subcontractors are uninsured. The likelier reading is
-- that the Procore insurance module was populated once and then abandoned, with current
-- certificates living in email or a shared drive. But "we stopped tracking it here" and
-- "our subs are uninsured" have very different consequences for a general contractor, and
-- nothing in the current reporting tells the two apart - or raises the question at all.
--
-- So the columns keep two things separate that a single "compliant" flag would merge:
--
--   COVERAGE   does a certificate exist for this vendor at all?
--   CURRENCY   is that certificate in date?
--
-- A vendor with no record and a vendor with a lapsed record both read as "not compliant",
-- and they call for completely different actions - chase the certificate, or chase the
-- renewal. Merging them is how a compliance report becomes a list nobody acts on.

CREATE OR REPLACE TABLE fct_VendorInsurance AS
SELECT
    insurance_id                     AS InsuranceKey,
    vendor_id                        AS VendorKey,
    insurance_type                   AS InsuranceType,
    provider                         AS Provider,
    policy_number                    AS PolicyNumber,
    status_label                     AS StatusLabel,
    effective_date                   AS EffectiveDate,
    expiration_date                  AS ExpirationDate,
    coverage_limit_raw               AS CoverageLimitRaw,
    is_exempt                        AS IsExempt,
    info_received                    AS InfoReceived,
    additional_insured               AS AdditionalInsured,

    -- Evaluated against the LOAD date and stored, not recomputed against TODAY() in DAX.
    -- Same reasoning as fct_ChangeOrder[DaysOpen]: a monthly report has to say what was
    -- true when it was produced, and a measure that silently re-evaluates is why the
    -- workbook's saved files disagree with each other (defect #5).
    CASE WHEN expiration_date IS NULL THEN NULL
         ELSE expiration_date < CURRENT_DATE END          AS IsExpired,
    CASE WHEN expiration_date IS NULL THEN NULL
         ELSE datediff(expiration_date, CURRENT_DATE) END AS DaysUntilExpiry,
    -- The actionable window. Expiring inside 30 days is a renewal to chase this month;
    -- already expired is a different conversation.
    CASE WHEN expiration_date IS NULL THEN 'No expiry recorded'
         WHEN expiration_date <  CURRENT_DATE THEN 'Expired'
         WHEN expiration_date <= date_add(CURRENT_DATE, 30) THEN 'Expiring within 30 days'
         WHEN expiration_date <= date_add(CURRENT_DATE, 90) THEN 'Expiring within 90 days'
         ELSE 'Current' END                               AS ExpiryStatus,
    -- Exempt is a legitimate state - an owner-supplied vendor, or one that never comes on
    -- site. Kept distinct from "expired" so it is not chased as a lapse.
    CASE WHEN COALESCE(is_exempt, FALSE) THEN 'Exempt'
         WHEN expiration_date IS NULL THEN 'Unknown'
         WHEN expiration_date < CURRENT_DATE THEN 'Lapsed'
         ELSE 'In date' END                               AS ComplianceState,

    CASE WHEN expiration_date IS NULL THEN NULL
         ELSE make_date(year(expiration_date), month(expiration_date), 1) END AS MonthStart,
    CASE WHEN expiration_date IS NOT NULL
              AND (expiration_date < DATE '2015-01-01'
                   OR expiration_date > DATE '2035-12-31')
         THEN TRUE ELSE FALSE END                         AS HasOutOfRangeDate
FROM sv_vendor_insurance
WHERE vendor_id IS NOT NULL;
