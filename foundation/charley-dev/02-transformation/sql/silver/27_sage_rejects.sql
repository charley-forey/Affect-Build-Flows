-- ---------------------------------------------------------------------------
-- silver: rejects for 26_sage_silver.sql's three `recnum IS NOT NULL` filters
-- ---------------------------------------------------------------------------
-- A SEPARATE FILE, not an arm at the bottom of 26: validate_sage_spark.py replays 26 as
-- temporary views to validate Sage without writing anything, and refuses any statement
-- that is not a cd_silver_sage_* CREATE. Writing the shared reject ledger from 26 would
-- either break that isolation guard or have to weaken it.
--
-- A header with no recnum cannot be joined by anything (jobnum -> actrec.recnum, and
-- invoice_id is recnum), so it is excluded - and recorded. Sage bronze is typed columns, not
-- JSON, and carries no batch id; the payload is a minimal JSON object holding _idnum, the
-- one identifier that survives, so the row can still be found in bronze.
--
-- DELETE then INSERT for the same reason as 24_qc_procore_silver.sql.

DELETE FROM cd_dq_rejects
WHERE target_table IN ('cd_silver_sage_jobs', 'cd_silver_sage_ar_invoices', 'cd_silver_sage_ap_invoices');

INSERT INTO cd_dq_rejects
SELECT 'cd_silver_sage_jobs', 'missing recnum',
       CONCAT('{"_idnum":"', COALESCE(CAST(_idnum AS STRING), ''), '"}'), CAST(NULL AS STRING)
FROM cd_bronze_sage_actrec
WHERE recnum IS NULL
UNION ALL
SELECT 'cd_silver_sage_ar_invoices', 'missing recnum',
       CONCAT('{"_idnum":"', COALESCE(CAST(_idnum AS STRING), ''), '"}'), CAST(NULL AS STRING)
FROM cd_bronze_sage_acrinv
WHERE recnum IS NULL
UNION ALL
SELECT 'cd_silver_sage_ap_invoices', 'missing recnum',
       CONCAT('{"_idnum":"', COALESCE(CAST(_idnum AS STRING), ''), '"}'), CAST(NULL AS STRING)
FROM cd_bronze_sage_acpinv
WHERE recnum IS NULL;

-- AR payments with no _idref cannot be applied to any invoice (26_sage_silver.sql).
DELETE FROM cd_dq_rejects WHERE target_table = 'cd_silver_sage_ar_payments';

INSERT INTO cd_dq_rejects
SELECT 'cd_silver_sage_ar_payments', 'missing _idref',
       CONCAT('{"_idnum":"', COALESCE(CAST(_idnum AS STRING), ''), '"}'), CAST(NULL AS STRING)
FROM cd_bronze_sage_acrpmt
WHERE _idref IS NULL;
