-- silver: Sage 100 Contractor AR/AP, including the line detail nobody had ever queried.
--
-- Bronze here is NOT the Procore payload shape. There is no `payload` JSON column to pick
-- apart: CD_Sage_Ingest lands real typed SQL Server columns, so these transforms rename and
-- constrain rather than parse. Anything reading `get_json_object` in this file would be a
-- copy-paste from the Procore parsers and would fail immediately.
--
-- THE JOIN KEY IS `_idref`, NOT `invrec`.
--
-- resources/sage-100-contractor/schema implies the line tables hang off their header by
-- `invrec`. Measured against the live data on 2026-08-25, that join orphans EVERY row:
--
--     arivln.invrec -> acrinv.recnum      258 of 258 orphaned
--     apivln.invrec -> acpinv.recnum      901 of 901 orphaned
--     arivln._idref -> acrinv._idnum        0 orphaned
--     apivln._idref -> acpinv._idnum        0 orphaned
--
-- `_idnum`/`_idref` look like internal plumbing, which is presumably how the documented
-- answer came to be wrong. They are the foreign key. Getting this wrong does not error - it
-- silently produces zero rows, which is the failure mode this whole engagement exists to
-- remove.
--
-- RETAINAGE IS NOT HERE, AND THAT IS THE ANSWER, NOT A GAP.
--
-- Sage holds no retainage anywhere: acrinv.retain 0 of 940, arivln.hldamt 0 of 258,
-- apivln.hldamt 0 of 901, actrec.retain 0 of 27. The real retainage figures come from
-- Procore progress billing and are already in fct_Billing - see 21_financial_silver.sql,
-- which carries $830,725.87 owner and $486,030.04 sub. The line tables were the last
-- unchecked candidate; they are now checked. `hold_amount` is carried through anyway so a
-- future non-zero value shows up rather than being assumed away.
--
--
-- `invamt` IS ZERO ON EVERY INVOICE. THE TOTAL IS amtpad + invbal.
--
-- Measured 2026-08-25: acrinv.invamt = 0 on all 148 rows, acpinv.invamt = 0 on all 871.
-- The obvious column for "invoice total" is simply not populated by this company. Taking
-- it at face value would have put $0 on every invoice in fct_Invoice - with total
-- confidence, no error, and a report that looks finished.
--
-- Paid + outstanding is the total, and it cross-checks EXACTLY against the line tables,
-- which are an independent source:
--
--     AR   amtpad 18,713,981.77 + invbal 6,899,677.89 = 25,613,659.66 = SUM(arivln.extprc)
--     AP   amtpad 11,103,345.67 + invbal 4,406,036.11 = 15,509,381.78 = SUM(apivln.extttl)
--
-- Two independent derivations agreeing to the cent is what makes this a fact rather than a
-- guess. NULLIF keeps `invamt` authoritative if Sage ever starts populating it.
--
-- THE TWO LINE TABLES DO NOT SHARE A SHAPE. AP codes to `actnum`/`subact` (GL account), AR
-- to `cstcde` (cost code), and AP's line total is `extttl` where AR's is `extprc`. They are
-- deliberately NOT unioned: one table with half its columns null per direction reads as a
-- data problem forever after.

-- ---------------------------------------------------------------------------
-- Jobs. `jobnum` on an invoice is a foreign key to actrec.recnum, not a readable
-- job code - which is why dim_projects_procoreXsage is a real crosswalk rather than
-- a convenience lookup. Verified: 0 of 148 AR invoices orphan on this key.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE cd_silver_sage_jobs AS
SELECT
    CAST(recnum AS STRING)              AS sage_project_id,
    TRIM(jobnme)                        AS job_name,
    TRIM(shtnme)                        AS job_short_name,
    CAST(clnnum AS STRING)              AS client_id,
    TRIM(ctynme)                        AS city,
    TRIM(state_)                        AS state,
    CAST(status AS INT)                 AS status_code,
    CAST(strdte AS DATE)                AS start_date,
    CAST(cmpdte AS DATE)                AS completion_date,
    CAST(ctcdte AS DATE)                AS contract_date,
    CAST(begbal AS DOUBLE)              AS beginning_balance,
    CAST(endbal AS DOUBLE)              AS ending_balance,
    CAST(upddte AS TIMESTAMP)           AS updated_at
FROM cd_bronze_sage_actrec
WHERE recnum IS NOT NULL;

-- ---------------------------------------------------------------------------
-- AR invoice headers. Money owed TO Affect.
--
-- Column contract is fixed by 01_source_views_cd.sql::sv_ar_invoices, because every gold
-- file reads sv_* and nothing else. Changing a name here without changing it there breaks
-- fct_Invoice silently.
--
-- NO `Invoice Balance <> 0` FILTER. The existing Build_Sage_Test dataflow applies one, so
-- its Revenue_AllTime output drops fully-paid invoices entirely. That is a reporting
-- decision baked into an extract, and it makes "total billed to date" unanswerable. Bronze
-- keeps everything; anything that wants open invoices only can filter on invoice_balance.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE cd_silver_sage_ar_invoices AS
SELECT
    h._idnum                            AS invoice_uid,
    CAST(h.recnum AS STRING)            AS invoice_id,
    TRIM(h.invnum)                      AS invoice_number,
    CAST(h.jobnum AS STRING)            AS sage_project_id,
    j.job_name                          AS job_name,
    CAST(h.invdte AS DATE)              AS invoice_date,
    CAST(h.duedte AS DATE)              AS due_date,
    TRIM(h.dscrpt)                      AS description,
    -- See the header note: invamt is 0 everywhere, so the total is paid + outstanding.
    CAST(COALESCE(NULLIF(h.invamt, 0),
                  h.amtpad + h.invbal) AS DOUBLE)
                                        AS invoice_total,
    CAST(h.amtpad AS DOUBLE)            AS amount_paid,
    CAST(h.invbal AS DOUBLE)            AS invoice_balance,
    CAST(h.hldamt AS DOUBLE)            AS hold_amount,
    CAST(h.status AS INT)               AS status_code,
    -- Revenue_AllTime carried a `Billing Period` column and gold reads it. Sage has no such
    -- field, so it is derived from the invoice date - the same grain the workbook reports at.
    DATE_FORMAT(CAST(h.invdte AS DATE), 'yyyy-MM')  AS billing_period,
    CAST(h.upddte AS TIMESTAMP)         AS updated_at
FROM cd_bronze_sage_acrinv h
LEFT JOIN cd_silver_sage_jobs j
       ON CAST(h.jobnum AS STRING) = j.sage_project_id
WHERE h.recnum IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Lines without a matching header remain visible with unresolved header fields.
-- The silver reconciliation gate blocks orphan lines; it must not erase them.
-- AR invoice lines. 258 rows, $25.6M. Only 25 carry a cost code, so revenue-by-cost-code
-- is NOT available from this source and must not be promised - the coverage is 10%.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE cd_silver_sage_ar_lines AS
SELECT
    l._idnum                            AS line_uid,
    l._idref                            AS invoice_uid,
    h.invoice_id                        AS invoice_id,
    h.sage_project_id                   AS sage_project_id,
    CAST(l.linnum AS INT)               AS line_number,
    TRIM(l.dscrpt)                      AS description,
    CAST(l.linqty AS DOUBLE)            AS quantity,
    CAST(l.linprc AS DOUBLE)            AS unit_price,
    CAST(l.extprc AS DOUBLE)            AS line_total,
    CAST(l.hldamt AS DOUBLE)            AS hold_amount,
    CAST(l.bllamt AS DOUBLE)            AS billed_amount,
    -- Cost code, where present. Cast through STRING so a numeric code keeps any leading
    -- zero convention the crosswalk expects - Affect writes CSI divisions 1-9 without one,
    -- which cost 807 codes their by-division rollup once already (see build-status.md).
    CASE WHEN l.cstcde IS NULL OR l.cstcde = 0 THEN NULL
         ELSE CAST(CAST(l.cstcde AS DECIMAL(18,4)) AS STRING) END  AS cost_code,
    CAST(l.lgract AS STRING)            AS ledger_account,
    CAST(l.upddte AS TIMESTAMP)         AS updated_at
FROM cd_bronze_sage_arivln l
LEFT JOIN cd_silver_sage_ar_invoices h
  ON l._idref = h.invoice_uid;

-- ---------------------------------------------------------------------------
-- AP invoice headers. Money Affect owes subs and suppliers.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE cd_silver_sage_ap_invoices AS
SELECT
    h._idnum                            AS invoice_uid,
    CAST(h.recnum AS STRING)            AS invoice_id,
    TRIM(h.invnum)                      AS invoice_number,
    CAST(h.vndnum AS STRING)            AS sage_vendor_id,
    CAST(h.jobnum AS STRING)            AS sage_project_id,
    j.job_name                          AS job_name,
    CAST(h.invdte AS DATE)              AS invoice_date,
    CAST(h.duedte AS DATE)              AS due_date,
    TRIM(h.dscrpt)                      AS description,
    -- See the header note: invamt is 0 everywhere, so the total is paid + outstanding.
    CAST(COALESCE(NULLIF(h.invamt, 0),
                  h.amtpad + h.invbal) AS DOUBLE)
                                        AS invoice_total,
    CAST(h.amtpad AS DOUBLE)            AS amount_paid,
    CAST(h.invbal AS DOUBLE)            AS invoice_balance,
    CAST(h.hldamt AS DOUBLE)            AS hold_amount,
    CAST(h.status AS INT)               AS status_code,
    DATE_FORMAT(CAST(h.invdte AS DATE), 'yyyy-MM')  AS billing_period,
    CAST(h.upddte AS TIMESTAMP)         AS updated_at
FROM cd_bronze_sage_acpinv h
LEFT JOIN cd_silver_sage_jobs j
       ON CAST(h.jobnum AS STRING) = j.sage_project_id
WHERE h.recnum IS NOT NULL;

-- ---------------------------------------------------------------------------
-- AP invoice lines. THE POINT OF THE WHOLE EXERCISE.
--
-- 901 rows, $15.5M, and 901 of 901 carry a GL account. This is what makes
-- actual-cost-by-account real rather than Procore-only: the AP header carries a job number
-- but no account, so header-only AP data cannot be allocated to a budget line at all.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE cd_silver_sage_ap_lines AS
SELECT
    l._idnum                            AS line_uid,
    l._idref                            AS invoice_uid,
    h.invoice_id                        AS invoice_id,
    h.sage_project_id                   AS sage_project_id,
    h.sage_vendor_id                    AS sage_vendor_id,
    CAST(l.linnum AS INT)               AS line_number,
    TRIM(l.prtdsc)                      AS description,
    CAST(l.linqty AS DOUBLE)            AS quantity,
    CAST(l.linprc AS DOUBLE)            AS unit_price,
    CAST(l.extttl AS DOUBLE)            AS line_total,
    CAST(l.hldamt AS DOUBLE)            AS hold_amount,
    CAST(l.invamt AS DOUBLE)            AS invoiced_amount,
    -- GL account, not a CSI cost code. Named for what it is: calling it cost_code here
    -- would invite a join against dim_CostCode that cannot succeed.
    CAST(l.actnum AS STRING)            AS ledger_account,
    CAST(l.subact AS STRING)            AS sub_account,
    CAST(l.upddte AS TIMESTAMP)         AS updated_at
FROM cd_bronze_sage_apivln l
LEFT JOIN cd_silver_sage_ap_invoices h
  ON l._idref = h.invoice_uid;

-- ---------------------------------------------------------------------------
-- AR payments (cash receipts). WHERE THE PAID DATE LIVES.
--
-- The AR header carries amtpad but no date, so Avg Days To Payment was BLANK. acrpmt has
-- the date (`chkdte`) and the amount, one row per receipt applied to one invoice. Measured
-- 2026-09-13 (_docs/sage-payments-evidence.json):
--
--   * key: `_idref` -> acrinv._idnum, 0 of 86 orphaned. `recnum` on a payment is the
--     INVOICE's recnum (not a payment id) and agrees with _idref on all 86 rows; _idref is
--     used for the same reason as the line tables.
--   * reconciliation: per invoice, SUM(amount) = acrinv.amtpad on 82 of 85 paid invoices
--     to the cent. The 3 exceptions ($227,667.54) are invoices dated 2024-12-31 with no
--     receipts at all - opening balances that predate the payment history (first receipt
--     2025-01-07). Not a join failure.
--   * reversals are NEGATIVE ROWS, not a flag: one invoice has +200,000 and -200,000 on
--     the same day and amtpad 0. Every row is kept; gold nets them.
--   * dsctkn and aplcrd are 0 on all 86 rows. Carried so a non-zero value shows up.
--
-- Rows without `_idref` cannot reach an invoice and are recorded in 27_sage_rejects.sql.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE cd_silver_sage_ar_payments AS
SELECT
    p._idnum                            AS payment_uid,
    p._idref                            AS invoice_uid,
    h.invoice_id                        AS invoice_id,
    h.sage_project_id                   AS sage_project_id,
    TRIM(p.chknum)                      AS check_number,
    CAST(p.chkdte AS DATE)              AS payment_date,
    CAST(p.amount AS DOUBLE)            AS amount,
    CAST(p.dsctkn AS DOUBLE)            AS discount_taken,
    CAST(p.aplcrd AS DOUBLE)            AS applied_credit,
    TRIM(p.dscrpt)                      AS description,
    CAST(p.upddte AS TIMESTAMP)         AS updated_at
FROM cd_bronze_sage_acrpmt p
LEFT JOIN cd_silver_sage_ar_invoices h
  ON p._idref = h.invoice_uid
WHERE p._idref IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Vendor master (actpay). Replaces Rebecca's Dim_Sage_Vendors, which was actpay.recnum /
-- vndnme verbatim: measured 2026-09-13, 1,073 of 1,073 ids in actpay with 0 name
-- differences, and actpay carries 9 more. `recnum` is the id AP invoices carry in `vndnum`
-- and the id Procore writes into a vendor's `origin_code` when it syncs to Sage.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TABLE cd_silver_sage_vendors AS
SELECT
    CAST(recnum AS STRING)              AS sage_vendor_id,
    TRIM(vndnme)                        AS vendor_name,
    CAST(upddte AS TIMESTAMP)           AS updated_at
FROM cd_bronze_sage_actpay
WHERE recnum IS NOT NULL;
