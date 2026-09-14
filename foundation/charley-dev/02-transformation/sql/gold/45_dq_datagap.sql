-- gold: dq_DataGap - one row per known data gap, from every place a gap is recorded.
--
-- THE PROBLEM THIS SOLVES. The platform already detects most of its gaps - silver writes
-- three reject ledgers, fct_Invoice flags unmatched AR, the QC facts flag unmapped trades,
-- the crosswalk flags missing systems, insurance flags expiry - but each lives in its own
-- table with its own shape, and the reject ledgers reached no report at all. So "what is
-- wrong with the data, and how much money does it touch" had no single answer.
--
-- A PLAIN UNION ALL, deliberately. One arm per gap source, each mapped onto the same nine
-- columns. Adding a gap source is adding an arm; there is no rule engine to learn.
--
--   GapCategory   what kind of gap - the report groups by this
--   SourceSystem  where the fix has to happen (Procore, Sage, Outbuild, SharePoint)
--   EntityType    the table the gap was found in
--   EntityKey     the row's own identifier there, where it has one
--   ProjectKey    NULL unless the key resolves to dim_Project, so the relationship never
--                 produces a blank unknown member; the raw project id is kept in Detail
--   Reason        plain language
--   Amount        money at stake, only where the gap carries a real amount
--   Detail        enough to find the row at source
--   RunBatchId    the ingestion batch, where the source records one
--
-- CD-ONLY: reads the silver reject ledgers and the PQP facts, so deploy_gold.py lists it in
-- GOLD_CD_ONLY. Prefixed 45 so it runs after every table it reads (33_fct_qc, 41_man_qc).

CREATE OR REPLACE TABLE dq_DataGap AS

-- ---- Silver reject ledgers --------------------------------------------------------------

SELECT
    'Rejected source row'                                   AS GapCategory,
    CASE WHEN r.target_table LIKE 'cd_silver_sage%' THEN 'Sage'
         WHEN r.target_table LIKE '%outbuild%'      THEN 'Outbuild'
         ELSE 'Procore' END                                 AS SourceSystem,
    r.target_table                                          AS EntityType,
    COALESCE(get_json_object(r.payload, '$.id'),
             get_json_object(r.payload, '$._idnum'))        AS EntityKey,
    CAST(NULL AS STRING)                                    AS ProjectKey,
    r.reason                                                AS Reason,
    CAST(NULL AS DOUBLE)                                    AS Amount,
    -- Identifiers only, never the payload: Procore payloads carry user emails, and this
    -- table reaches both models. The record id finds the row at source.
    concat_ws('; ',
              CONCAT('record ', COALESCE(get_json_object(r.payload, '$.id'),
                                         get_json_object(r.payload, '$._idnum'), '(no id)')),
              CONCAT('table ', r.target_table),
              CONCAT('reason ', r.reason),
              CONCAT('batch ', r._batch_id))                AS Detail,
    r._batch_id                                             AS RunBatchId
FROM sv_dq_rejects r

UNION ALL
SELECT 'Rejected manual entry', 'SharePoint', r.target_table, r.item_ref, p.ProjectKey,
       r.reason, CAST(NULL AS DOUBLE),
       concat_ws('; ', CONCAT('project ', r.project_id),
                 CONCAT('month ', CAST(r.month_start AS STRING)),
                 CONCAT('item ', r.item_ref)),
       CAST(NULL AS STRING)
FROM sv_dq_rejects_manual r
LEFT JOIN dim_Project p ON p.ProjectKey = r.project_id

UNION ALL
SELECT 'Rejected quality entry', 'SharePoint', r.target_table, r.item_ref, p.ProjectKey,
       r.reason, CAST(NULL AS DOUBLE),
       concat_ws('; ', CONCAT('project ', r.project_id), CONCAT('item ', r.item_ref)),
       CAST(NULL AS STRING)
FROM sv_dq_rejects_qc r
LEFT JOIN dim_Project p ON p.ProjectKey = r.project_id

-- ---- Gaps flagged in gold ---------------------------------------------------------------

UNION ALL
-- The one category with money on it: billed revenue attached to no project.
SELECT 'Unmatched AR invoice', 'Sage', 'fct_Invoice', i.InvoiceKey, CAST(NULL AS STRING),
       CONCAT('Sage job ', COALESCE(i.SageJobNumber, '(blank)'),
              ' does not resolve to a Procore project'),
       i.Amount,
       concat_ws('; ', CONCAT('invoice ', i.InvoiceNumber),
                 CONCAT('sent ', CAST(i.SentDate AS STRING))),
       CAST(NULL AS STRING)
FROM fct_Invoice i
WHERE i.HasUnmatchedProject

UNION ALL
SELECT 'Unmapped trade', 'Procore', 'fct_QcNcr', n.NcrKey, p.ProjectKey,
       CONCAT('Procore trade "', n.TradeLabel, '" has no workbook TradeKey'),
       CAST(NULL AS DOUBLE), CONCAT('observation ', n.NcrNumber), CAST(NULL AS STRING)
FROM fct_QcNcr n
LEFT JOIN dim_Project p ON p.ProjectKey = n.ProjectKey
WHERE n.HasUnmappedTrade

UNION ALL
SELECT 'Unmapped trade', 'Procore', 'fct_QcPunch', u.PunchKey, p.ProjectKey,
       CONCAT('Procore trade "', u.TradeLabel, '" has no workbook TradeKey'),
       CAST(NULL AS DOUBLE), CONCAT('punch item ', u.PunchNumber), CAST(NULL AS STRING)
FROM fct_QcPunch u
LEFT JOIN dim_Project p ON p.ProjectKey = u.ProjectKey
WHERE u.HasUnmappedTrade

UNION ALL
SELECT 'Project missing from Sage', 'Sage', 'dim_ProjectCrosswalk', x.ProjectKey, x.ProjectKey,
       CASE WHEN x.HasAmbiguousSageMatch
            THEN 'Maps to more than one Sage job - no revenue attached until resolved'
            ELSE 'No Sage job in the Procore-Sage crosswalk - reads as zero revenue' END,
       CAST(NULL AS DOUBLE), x.ProjectName, CAST(NULL AS STRING)
FROM dim_ProjectCrosswalk x
WHERE NOT x.IsInSage

UNION ALL
-- The other side of the crosswalk: a Sage job carrying money that maps to no Procore project.
-- One row per job AND direction (AR, AP). AMOUNT IS NULL ON PURPOSE: the AR money is already
-- itemised per invoice under 'Unmatched AR invoice', so putting it here too would make
-- SUM(Amount) - the Data Gap Amount measure - count it twice. The figure is in Reason.
-- Nothing is excluded (the office overhead job included): which jobs are legitimately
-- outside Procore is Affect's call, not a filter in this file. Invoices with NO job at all
-- cannot belong to a job-level row; they are the next arm.
SELECT 'Sage job without Procore project', 'Sage', g.src, g.sage_project_id, CAST(NULL AS STRING),
       CONCAT('Sage job ', g.sage_project_id, ' has ', CAST(g.n AS STRING), ' ', g.kind,
              ' invoice(s) totalling ', CAST(CAST(g.amount AS DECIMAL(18,2)) AS STRING),
              ' and no Procore project in the crosswalk'),
       CAST(NULL AS DOUBLE),
       concat_ws('; ', CONCAT('job ', COALESCE(j.job_name, '(not in sv_sage_jobs)')),
                 'see dq_CrosswalkCandidate for proposed matches'),
       CAST(NULL AS STRING)
FROM (
    SELECT 'sv_ar_invoices' AS src, 'AR' AS kind, sage_project_id,
           COUNT(*) AS n, CAST(SUM(invoice_total) AS DOUBLE) AS amount
    FROM sv_ar_invoices GROUP BY sage_project_id
    UNION ALL
    SELECT 'sv_ap_invoices', 'AP', sage_project_id,
           COUNT(*), CAST(SUM(invoice_total) AS DOUBLE)
    FROM sv_ap_invoices GROUP BY sage_project_id
) g
LEFT JOIN sv_sage_jobs j ON j.sage_project_id = g.sage_project_id
WHERE g.sage_project_id IS NOT NULL
  AND g.sage_project_id NOT IN (SELECT sage_project_id FROM sv_project_crosswalk
                                WHERE sage_project_id IS NOT NULL)

UNION ALL
-- AP booked to no Sage job at all (overhead, stock, suppliers). No crosswalk can attach it
-- to a project, so it is counted, not valued: Amount NULL for the same double-count reason,
-- the invoice total in Detail. Measured 2026-09-13: 303 invoices, $4,205,597.50.
SELECT 'AP invoice with no Sage job', 'Sage', 'sv_ap_invoices', a.invoice_id, CAST(NULL AS STRING),
       'Sage AP invoice carries no job - it cannot reach any project',
       CAST(NULL AS DOUBLE),
       concat_ws('; ', CONCAT('invoice ', a.invoice_number),
                 CONCAT('vendor ', a.sage_vendor_id),
                 CONCAT('total ', CAST(CAST(a.invoice_total AS DECIMAL(18,2)) AS STRING))),
       CAST(NULL AS STRING)
FROM sv_ap_invoices a
WHERE a.sage_project_id IS NULL

UNION ALL
SELECT 'Project missing from Outbuild', 'Outbuild', 'dim_ProjectCrosswalk', x.ProjectKey, x.ProjectKey,
       CASE WHEN x.HasAmbiguousOutbuildMatch
            THEN 'Linked from more than one Outbuild project - no milestones until resolved'
            ELSE 'No Outbuild project carries this Procore id - no milestones' END,
       CAST(NULL AS DOUBLE), x.ProjectName, CAST(NULL AS STRING)
FROM dim_ProjectCrosswalk x
WHERE NOT x.IsInOutbuild

UNION ALL
-- Coverage, not currency: the vendor has no certificate at all. The lapsed case is below.
SELECT 'Vendor without certificate', 'Procore', 'bridge_ProjectVendor', b.VendorKey, p.ProjectKey,
       'Vendor on this project has no insurance certificate on file',
       CAST(NULL AS DOUBLE), b.VendorName, CAST(NULL AS STRING)
FROM bridge_ProjectVendor b
LEFT JOIN dim_Project p ON p.ProjectKey = b.ProjectKey
WHERE NOT EXISTS (SELECT 1 FROM fct_VendorInsurance c WHERE c.VendorKey = b.VendorKey)

UNION ALL
-- Exempt certificates are a legitimate state, not a lapse, so they are not listed.
SELECT 'Expired certificate', 'Procore', 'fct_VendorInsurance', c.InsuranceKey, CAST(NULL AS STRING),
       CONCAT('Certificate expired ', CAST(c.ExpirationDate AS STRING)),
       CAST(NULL AS DOUBLE),
       concat_ws('; ', CONCAT('vendor ', c.VendorKey), c.InsuranceType, c.PolicyNumber),
       CAST(NULL AS STRING)
FROM fct_VendorInsurance c
WHERE c.IsExpired AND NOT COALESCE(c.IsExempt, FALSE)

-- ---- Empty manual registers -------------------------------------------------------------
-- One row per register with zero rows. Empty is not "nothing to report": nobody can tell
-- a month with no risks from a month where nobody opened the list.

UNION ALL SELECT 'Empty manual register', 'SharePoint', 'man_Wins', 'man_Wins', CAST(NULL AS STRING), 'Register has zero rows - input completeness not established', CAST(NULL AS DOUBLE), CAST(NULL AS STRING), CAST(NULL AS STRING) FROM (SELECT COUNT(*) AS n FROM man_Wins) WHERE n = 0
UNION ALL SELECT 'Empty manual register', 'SharePoint', 'man_Risks', 'man_Risks', CAST(NULL AS STRING), 'Register has zero rows - input completeness not established', CAST(NULL AS DOUBLE), CAST(NULL AS STRING), CAST(NULL AS STRING) FROM (SELECT COUNT(*) AS n FROM man_Risks) WHERE n = 0
UNION ALL SELECT 'Empty manual register', 'SharePoint', 'man_PriorityItems', 'man_PriorityItems', CAST(NULL AS STRING), 'Register has zero rows - input completeness not established', CAST(NULL AS DOUBLE), CAST(NULL AS STRING), CAST(NULL AS STRING) FROM (SELECT COUNT(*) AS n FROM man_PriorityItems) WHERE n = 0
UNION ALL SELECT 'Empty manual register', 'SharePoint', 'man_Flags', 'man_Flags', CAST(NULL AS STRING), 'Register has zero rows - input completeness not established', CAST(NULL AS DOUBLE), CAST(NULL AS STRING), CAST(NULL AS STRING) FROM (SELECT COUNT(*) AS n FROM man_Flags) WHERE n = 0
UNION ALL SELECT 'Empty manual register', 'SharePoint', 'man_Survey', 'man_Survey', CAST(NULL AS STRING), 'Register has zero rows - input completeness not established', CAST(NULL AS DOUBLE), CAST(NULL AS STRING), CAST(NULL AS STRING) FROM (SELECT COUNT(*) AS n FROM man_Survey) WHERE n = 0
UNION ALL SELECT 'Empty manual register', 'SharePoint', 'man_SafetyMonthly', 'man_SafetyMonthly', CAST(NULL AS STRING), 'Register has zero rows - input completeness not established', CAST(NULL AS DOUBLE), CAST(NULL AS STRING), CAST(NULL AS STRING) FROM (SELECT COUNT(*) AS n FROM man_SafetyMonthly) WHERE n = 0
UNION ALL SELECT 'Empty manual register', 'SharePoint', 'man_QualityMonthly', 'man_QualityMonthly', CAST(NULL AS STRING), 'Register has zero rows - input completeness not established', CAST(NULL AS DOUBLE), CAST(NULL AS STRING), CAST(NULL AS STRING) FROM (SELECT COUNT(*) AS n FROM man_QualityMonthly) WHERE n = 0
UNION ALL SELECT 'Empty manual register', 'SharePoint', 'man_Milestones', 'man_Milestones', CAST(NULL AS STRING), 'Register has zero rows - input completeness not established', CAST(NULL AS DOUBLE), CAST(NULL AS STRING), CAST(NULL AS STRING) FROM (SELECT COUNT(*) AS n FROM man_Milestones) WHERE n = 0
UNION ALL SELECT 'Empty manual register', 'SharePoint', 'man_DailyLogCompliance', 'man_DailyLogCompliance', CAST(NULL AS STRING), 'Register has zero rows - input completeness not established', CAST(NULL AS DOUBLE), CAST(NULL AS STRING), CAST(NULL AS STRING) FROM (SELECT COUNT(*) AS n FROM man_DailyLogCompliance) WHERE n = 0
UNION ALL SELECT 'Empty manual register', 'SharePoint', 'man_QcDfow', 'man_QcDfow', CAST(NULL AS STRING), 'Register has zero rows - input completeness not established', CAST(NULL AS DOUBLE), CAST(NULL AS STRING), CAST(NULL AS STRING) FROM (SELECT COUNT(*) AS n FROM man_QcDfow) WHERE n = 0
UNION ALL SELECT 'Empty manual register', 'SharePoint', 'man_QcItp', 'man_QcItp', CAST(NULL AS STRING), 'Register has zero rows - input completeness not established', CAST(NULL AS DOUBLE), CAST(NULL AS STRING), CAST(NULL AS STRING) FROM (SELECT COUNT(*) AS n FROM man_QcItp) WHERE n = 0
UNION ALL SELECT 'Empty manual register', 'SharePoint', 'man_QcGate', 'man_QcGate', CAST(NULL AS STRING), 'Register has zero rows - input completeness not established', CAST(NULL AS DOUBLE), CAST(NULL AS STRING), CAST(NULL AS STRING) FROM (SELECT COUNT(*) AS n FROM man_QcGate) WHERE n = 0
UNION ALL SELECT 'Empty manual register', 'SharePoint', 'man_QcSpecialInspection', 'man_QcSpecialInspection', CAST(NULL AS STRING), 'Register has zero rows - input completeness not established', CAST(NULL AS DOUBLE), CAST(NULL AS STRING), CAST(NULL AS STRING) FROM (SELECT COUNT(*) AS n FROM man_QcSpecialInspection) WHERE n = 0
UNION ALL SELECT 'Empty manual register', 'SharePoint', 'man_QcCommissioning', 'man_QcCommissioning', CAST(NULL AS STRING), 'Register has zero rows - input completeness not established', CAST(NULL AS DOUBLE), CAST(NULL AS STRING), CAST(NULL AS STRING) FROM (SELECT COUNT(*) AS n FROM man_QcCommissioning) WHERE n = 0
UNION ALL SELECT 'Empty manual register', 'SharePoint', 'man_QcInspectorSignIn', 'man_QcInspectorSignIn', CAST(NULL AS STRING), 'Register has zero rows - input completeness not established', CAST(NULL AS DOUBLE), CAST(NULL AS STRING), CAST(NULL AS STRING) FROM (SELECT COUNT(*) AS n FROM man_QcInspectorSignIn) WHERE n = 0
UNION ALL SELECT 'Empty manual register', 'SharePoint', 'man_QcChecklistResult', 'man_QcChecklistResult', CAST(NULL AS STRING), 'Register has zero rows - input completeness not established', CAST(NULL AS DOUBLE), CAST(NULL AS STRING), CAST(NULL AS STRING) FROM (SELECT COUNT(*) AS n FROM man_QcChecklistResult) WHERE n = 0
UNION ALL SELECT 'Empty manual register', 'SharePoint', 'man_QcDohResult', 'man_QcDohResult', CAST(NULL AS STRING), 'Register has zero rows - input completeness not established', CAST(NULL AS DOUBLE), CAST(NULL AS STRING), CAST(NULL AS STRING) FROM (SELECT COUNT(*) AS n FROM man_QcDohResult) WHERE n = 0;
