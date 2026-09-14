-- gold: fct_ApInvoice - Sage AP at LINE grain, the ERP side of the cost reconciliation.
--
-- WHAT IT IS FOR. Procore [Spent To Date] is invoiced-to-date on commitments plus direct
-- costs. It cannot see a vendor bill keyed straight into Sage. Measured 2026-09-14
-- (scratchpad ap-cost-reconciliation.json): $3.57M of job-coded AP on the 15 mapped jobs sits
-- at vendors with no Procore commitment or direct cost on that project. This fact makes that
-- visible; it is NEVER added into Spent To Date (the $7.5M of AP at vendors Procore does
-- carry would then be counted twice).
--
-- WHAT IT CANNOT DO. AP lines carry a GL account only - no cost code - so reconciliation is
-- per project (and vendor), never per cost code. AP history starts 2025-03-11, so jobs that
-- ran before then (23-006, 24-011) read Procore-high for timing, not missing cost. Sage holds
-- no retainage (hold amount 0 everywhere) while Procore requisitions are gross.
--
-- IsJobCost = a Sage job AND GL account 50000-50999. VERIFIED, NOT ASSUMED, against the live
-- line distribution on 2026-09-14 (read-only SQL endpoint; no GL master is ingested):
--   job-coded lines   50001 $945,703.21 | 50004 $10,228,680.28 | 50005 $107,715.03 |
--                     50400 $14,656.58  -> $11,296,755.10, all inside 50000-50999
--                     60010/60070/61100/62000/65100 $16,512.10 -> overhead GLs, outside
--   no-job lines      carry 1xxxx/2xxxx/3xxxx balance-sheet and 6xxxx/7xxxx overhead as well
--                     as 5xxxx; without a job they are not job cost whatever the account.
-- A job-coded line outside the range is kept (conservation) but is not job cost.
--
-- ProjectKey via sv_project_crosswalk (NULL when the job is unmapped - those jobs are listed
-- under 'Sage job without Procore project' in dq_DataGap). VendorKey via the Procore vendor
-- whose origin_code is the Sage vendor id; 'UNASSIGNED' when no Procore vendor carries it.
-- Both lookups collapse to one id or none, so an ambiguous key can never fan out a line (the
-- DQ gate blocks those keys separately).
--
-- CD-ONLY (sv_ap_*, sv_commitments exist only in 01_source_views_cd.sql).

CREATE OR REPLACE TABLE fct_ApInvoice AS
WITH job AS (
    SELECT x.sage_project_id, MAX(p.ProjectKey) AS ProjectKey
    FROM sv_project_crosswalk x
    JOIN dim_Project p ON p.ProjectKey = x.procore_project_id
    WHERE x.sage_project_id IS NOT NULL
    GROUP BY x.sage_project_id
    HAVING COUNT(DISTINCT x.procore_project_id) = 1
),
vendor AS (
    SELECT sage_vendor_id, MAX(procore_vendor_id) AS VendorKey
    FROM sv_vendors
    WHERE sage_vendor_id IS NOT NULL AND procore_vendor_id IS NOT NULL
    GROUP BY sage_vendor_id
    HAVING COUNT(DISTINCT procore_vendor_id) = 1
),
-- A Procore commitment or direct cost for the vendor on the project, of any amount. This is
-- the definition that reproduces the measured $3,570,774.67 ERP-only job cost.
procore_cost AS (
    SELECT DISTINCT project_id, vendor_id FROM sv_commitments WHERE vendor_id IS NOT NULL
    UNION
    SELECT DISTINCT project_id, vendor_id FROM sv_direct_costs WHERE vendor_id IS NOT NULL
),
lines AS (
    SELECT
        l.*,
        j.ProjectKey,
        v.VendorKey,
        COALESCE(l.sage_project_id IS NOT NULL
                 AND TRY_CAST(l.ledger_account AS INT) BETWEEN 50000 AND 50999, FALSE) AS IsJobCost
    FROM sv_ap_lines l
    LEFT JOIN job    j ON j.sage_project_id = l.sage_project_id
    LEFT JOIN vendor v ON v.sage_vendor_id  = l.sage_vendor_id
)
SELECT
    CAST(l.line_uid AS STRING)                      AS ApLineKey,
    l.invoice_uid                                   AS InvoiceKey,
    h.invoice_id                                    AS InvoiceID,
    h.invoice_number                                AS InvoiceNumber,
    l.ProjectKey                                    AS ProjectKey,
    l.sage_project_id                               AS SageJobId,
    COALESCE(l.VendorKey, 'UNASSIGNED')             AS VendorKey,
    l.sage_vendor_id                                AS SageVendorId,
    l.ledger_account                                AS LedgerAccount,
    l.IsJobCost                                     AS IsJobCost,
    -- Job cost on a mapped project at a vendor Procore holds no cost for there.
    -- A LEFT JOIN rather than a select-list NOT EXISTS (not portable across Spark
    -- versions); procore_cost is DISTINCT (UNION), so the join cannot fan a line out.
    (l.IsJobCost AND l.ProjectKey IS NOT NULL AND c.project_id IS NULL)
                                                    AS IsErpOnlyVendor,
    l.line_total                                    AS LineTotal,
    -- Header money repeats on every line of the invoice: never SUM these across lines.
    h.invoice_total                                 AS InvoiceTotal,
    h.amount_paid                                   AS AmountPaid,
    h.invoice_balance                               AS InvoiceBalance,
    h.invoice_date                                  AS InvoiceDate,
    CASE WHEN h.invoice_date IS NULL
              OR h.invoice_date < DATE '2015-01-01'
              OR h.invoice_date > DATE '2035-12-31' THEN NULL
         ELSE make_date(year(h.invoice_date), month(h.invoice_date), 1) END AS MonthStart,
    h.status_code                                   AS StatusCode
FROM lines l
LEFT JOIN sv_ap_invoices h ON h.invoice_uid = l.invoice_uid
LEFT JOIN procore_cost   c ON c.project_id = l.ProjectKey AND c.vendor_id = l.VendorKey;
