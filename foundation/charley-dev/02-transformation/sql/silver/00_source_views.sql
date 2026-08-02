-- silver: source views - the ONLY place source naming is dealt with.
--
-- Every downstream gold file reads `sv_*` and nothing else. That buys two things:
--
-- 1. PORTABILITY. Source columns are named "Project ID", "CO Value $", "%_OVER/UNDER".
--    Quoting those differs by engine - Spark wants backticks, DuckDB wants double quotes -
--    so any gold file touching them directly could only ever run on one engine. Renaming
--    here to clean snake_case means every gold file is quote-free and runs unchanged on
--    both, which is what makes the offline suite verify the real production SQL.
--
-- 2. A SINGLE SWITCH. Today these views read the EXISTING Silver_Lakehouse read-only, so
--    the gold layer can be built and validated against real data now, before Procore
--    credentials land. When cd_01_extract_procore has populated CD_Bronze and
--    cd_10_bronze_to_silver has populated CD_Silver, only this file changes - every gold
--    file keeps working untouched.
--
-- SPARK-SPECIFIC. Backticks and the abfss path are Spark/Fabric syntax. The offline suite
-- creates the same `sv_*` views from fixtures instead, so the gold SQL is exercised
-- identically without needing this file.
--
-- READ-ONLY. These are views over another lakehouse's Delta files. Nothing here writes,
-- and nothing in charley-dev ever writes outside CD_*.

-- {SILVER_ABFSS} is substituted by deploy_gold.py from _local/fabric_ids.json.

CREATE OR REPLACE TEMPORARY VIEW sv_projects AS
SELECT
    CAST(`Project ID`      AS STRING) AS project_id,
    CAST(`Project Name`    AS STRING) AS project_name,
    CAST(`Sage Project ID` AS STRING) AS sage_project_id,
    CAST(origin_code       AS STRING) AS origin_code
FROM delta.`{SILVER_ABFSS}/dim_projects_procoreXsage`;

CREATE OR REPLACE TEMPORARY VIEW sv_vendors AS
SELECT
    CAST(`Procore Vendor ID` AS STRING) AS procore_vendor_id,
    CAST(`Sage Vendor ID`    AS STRING) AS sage_vendor_id,
    CAST(`Vendor Name`       AS STRING) AS vendor_name
FROM delta.`{SILVER_ABFSS}/dim_procore_project_vendor`;

CREATE OR REPLACE TEMPORARY VIEW sv_cost_codes AS
SELECT
    -- The existing warehouse holds no separate full_code, so the name doubles as it.
    CAST(`Cost Code _Name_` AS STRING) AS cost_code,
    CAST(`Cost Code ID`     AS STRING) AS cost_code_id,
    CAST(`Cost Code _Name_` AS STRING) AS cost_code_name
FROM delta.`{SILVER_ABFSS}/dim_procore_cost_codes`;

CREATE OR REPLACE TEMPORARY VIEW sv_budgets AS
SELECT
    CAST(`Project ID`   AS STRING) AS project_id,
    CAST(`Cost Code ID` AS STRING) AS cost_code_id,
    CAST(cost_code      AS STRING) AS cost_code,
    CAST(category       AS STRING) AS category,
    CAST(snapshot_date  AS DATE)   AS snapshot_date,
    CAST(original_budget_amount                     AS DOUBLE) AS original_budget,
    CAST(budget_modifications                       AS DOUBLE) AS budget_modifications,
    CAST(`UPDATED_PRIME_CONTRACT_BUDGET_D_A+B+C`    AS DOUBLE) AS updated_budget,
    CAST(`PROJECTED_PRIME_CONTRACT_BUDGET_F_D+E`    AS DOUBLE) AS forecast_budget,
    CAST(`TOTAL_COMMITTED_TO_DATE_K_G+H+I+J`        AS DOUBLE) AS committed_to_date,
    CAST(DIRECT_COSTS_J                             AS DOUBLE) AS direct_costs,
    CAST(INVOICED_TO_DATE_P                         AS DOUBLE) AS invoiced_to_date,
    CAST(`COST_TO_COMPLETE_Q_K-P`                   AS DOUBLE) AS cost_to_complete
FROM delta.`{SILVER_ABFSS}/procore_budgets_silver`;

CREATE OR REPLACE TEMPORARY VIEW sv_prime_change_orders AS
SELECT
    CAST(`Project ID`      AS STRING) AS project_id,
    CAST(`Change Order ID` AS STRING) AS change_order_id,
    CAST(`Contract ID`     AS STRING) AS contract_id,
    CAST(`Date Created`    AS DATE)   AS created_date,
    CAST(`CO Value $`      AS DOUBLE) AS amount,
    CAST(number            AS STRING) AS co_number,
    CAST(status            AS STRING) AS status
FROM delta.`{SILVER_ABFSS}/procore_prime_change_orders`;

CREATE OR REPLACE TEMPORARY VIEW sv_prime_contracts AS
SELECT
    CAST(`Prime Contract ID`           AS STRING) AS prime_contract_id,
    CAST(`Project ID`                  AS STRING) AS project_id,
    CAST(`Prime Contract Value`        AS DOUBLE) AS contract_value,
    CAST(`Retainage %`                 AS DOUBLE) AS retainage_pct,
    CAST(`Start Date`                  AS DATE)   AS start_date,
    CAST(`Estimated Completion Date`   AS DATE)   AS estimated_completion_date,
    CAST(Status                        AS STRING) AS status
FROM delta.`{SILVER_ABFSS}/procore_prime_contracts_silver`;

CREATE OR REPLACE TEMPORARY VIEW sv_ar_invoices AS
SELECT
    CAST(`Job Number`      AS STRING) AS sage_project_id,
    CAST(`Invoice Date`    AS DATE)   AS invoice_date,
    CAST(`Due Date`        AS DATE)   AS due_date,
    CAST(Description       AS STRING) AS description,
    CAST(`Invoice Total`   AS DOUBLE) AS invoice_total,
    CAST(`Amount Paid`     AS DOUBLE) AS amount_paid,
    CAST(`Invoice Balance` AS DOUBLE) AS invoice_balance,
    CAST(`Billing Period`  AS STRING) AS billing_period
FROM delta.`{SILVER_ABFSS}/Revenue_AllTime`;

-- SENTINEL DATES. The submittals table carries dates before 1582-10-15, which made Spark
-- refuse the read outright:
--   [INCONSISTENT_BEHAVIOR_CROSS_VERSION.READ_ANCIENT_DATETIME] reading dates before
--   1582-10-15 ... from Parquet files can be ambiguous
--
-- Those are placeholders standing in for "unknown", not real dates. Two things are needed:
-- the notebook sets datetimeRebaseModeInRead=CORRECTED so the read succeeds at all, and
-- the floor below turns the placeholder into a real NULL.
--
-- 1990-01-01 is the floor: Affect has been trading ~14 years, so nothing legitimate
-- predates it, and a submittal dated 0001-01-01 flowing into a report as a genuine date
-- is far worse than a blank. This is the same class of problem as the workbook's "NA"
-- string sentinels in date columns (Excel defect #7) - a placeholder that types as data.
CREATE OR REPLACE TEMPORARY VIEW sv_submittals AS
SELECT
    CAST(`Project ID`       AS STRING) AS project_id,
    CAST(id                 AS STRING) AS item_id,
    CAST(number             AS STRING) AS item_number,
    CAST(Description        AS STRING) AS subject,
    CAST(`Submittal Status` AS STRING) AS status_label,
    CAST(`Cost Code ID`     AS STRING) AS cost_code_id,
    CASE WHEN CAST(`Created At` AS DATE) < DATE '1990-01-01' THEN NULL
         ELSE CAST(`Created At` AS DATE) END          AS created_date,
    CASE WHEN CAST(required_on_site_date AS DATE) < DATE '1990-01-01' THEN NULL
         ELSE CAST(required_on_site_date AS DATE) END AS due_date,
    CASE WHEN CAST(received_date AS DATE) < DATE '1990-01-01' THEN NULL
         ELSE CAST(received_date AS DATE) END         AS responded_date
FROM delta.`{SILVER_ABFSS}/procore_submittals_silver`;

-- Outbuild is the only real source of critical-path milestones: Procore's OAS has no
-- milestone endpoint at all (powerbi/source-mapping.md:87).
CREATE OR REPLACE TEMPORARY VIEW sv_outbuild_activities AS
SELECT
    CAST(`Procore Project ID` AS STRING)  AS project_id,
    CAST(id                   AS STRING)  AS activity_id,
    CAST(name                 AS STRING)  AS activity_name,
    CAST(start_date           AS DATE)    AS start_date,
    CAST(end_date             AS DATE)    AS end_date,
    CAST(progress             AS DOUBLE)  AS progress,
    CAST(duration             AS DOUBLE)  AS duration,
    CAST(is_critical          AS BOOLEAN) AS is_critical,
    CAST(activity_type        AS STRING)  AS activity_type,
    CAST(Status               AS STRING)  AS status
FROM delta.`{SILVER_ABFSS}/Outbuild_activities`;

-- sv_rfis: EMPTY BY CONSTRUCTION under this source. There is no RFI table anywhere in the
-- existing warehouse - RFIs arrived with our own Procore ingestion, and 01_source_views_cd
-- is where they are real (616 rows).
--
-- It is declared rather than omitted so gold/23_fct_rfisubmittal.sql can UNION both arms
-- unconditionally and stay source-agnostic. The alternative - two versions of that file, or
-- a conditional inside it - is how a fact table quietly diverges between sources.
--
-- WHERE 1=0 keeps the column types without reading anything.
CREATE OR REPLACE TEMPORARY VIEW sv_rfis AS
SELECT
    CAST(NULL AS STRING) AS project_id,
    CAST(NULL AS STRING) AS item_id,
    CAST(NULL AS STRING) AS item_number,
    CAST(NULL AS STRING) AS subject,
    CAST(NULL AS STRING) AS status_label,
    CAST(NULL AS STRING) AS priority,
    CAST(NULL AS STRING) AS cost_code_id,
    CAST(NULL AS DATE)   AS created_date,
    CAST(NULL AS DATE)   AS due_date,
    CAST(NULL AS DATE)   AS responded_date
WHERE 1=0;


-- ---------------------------------------------------------------------------
-- CROSSWALK SOURCES
-- ---------------------------------------------------------------------------
--
-- These three feed dim_ProjectCrosswalk / dim_VendorCrosswalk. All read the EXISTING
-- warehouse, under both --source settings, because neither Sage nor Outbuild ingestion can
-- run yet (gateway binding and OUTBUILD_API_TOKEN, both Affect's to grant). When they do,
-- only these views move - the crosswalk gold files and every measure stay as they are.

-- Procore project id <-> Sage project id. Per resources/sage-100-contractor/schema, Sage
-- `jobnum` on an invoice is a foreign key to actrec.recnum, NOT a readable job code - so
-- this table IS the join between the two systems, not a convenience lookup.
CREATE OR REPLACE TEMPORARY VIEW sv_project_crosswalk AS
SELECT
    CAST(`Project ID`      AS STRING) AS procore_project_id,
    CAST(`Sage Project ID` AS STRING) AS sage_project_id,
    CAST(`Project Name`    AS STRING) AS project_name
FROM delta.`{SILVER_ABFSS}/dim_projects_procoreXsage`;

-- Outbuild carries its OWN Procore project id, so it joins to the hub directly rather than
-- needing a third mapping. One row per Outbuild project.
CREATE OR REPLACE TEMPORARY VIEW sv_outbuild_projects AS
SELECT DISTINCT
    CAST(`Outbuild Project ID` AS STRING) AS outbuild_project_id,
    CAST(`Procore Project ID`  AS STRING) AS procore_project_id
FROM delta.`{SILVER_ABFSS}/Outbuild_activities`
WHERE `Outbuild Project ID` IS NOT NULL;

-- Sage's own vendor master, for names on the Sage side of the vendor crosswalk.
CREATE OR REPLACE TEMPORARY VIEW sv_sage_vendors AS
SELECT
    CAST(`Vendor ID`   AS STRING) AS sage_vendor_id,
    CAST(`Vendor Name` AS STRING) AS sage_vendor_name
FROM delta.`{SILVER_ABFSS}/Dim_Sage_Vendors`;


-- ---------------------------------------------------------------------------
-- FIELD OPERATIONS - EMPTY under this source
-- ---------------------------------------------------------------------------
--
-- No observation or punch-item data exists anywhere in the existing warehouse; it arrived
-- with our own Procore ingestion (850 and 1,469 rows). Declared with the right column types
-- rather than omitted, so gold/25_fct_qualityitem.sql runs unchanged under both sources -
-- a missing view is a hard failure, an empty one is an empty fact.

CREATE OR REPLACE TEMPORARY VIEW sv_observations AS
SELECT CAST(NULL AS STRING) AS project_id, CAST(NULL AS STRING) AS observation_id,
       CAST(NULL AS STRING) AS observation_number, CAST(NULL AS STRING) AS title,
       CAST(NULL AS STRING) AS observation_type, CAST(NULL AS STRING) AS status_label,
       CAST(NULL AS STRING) AS priority, CAST(NULL AS STRING) AS trade,
       CAST(NULL AS STRING) AS assignee_name, CAST(NULL AS DATE) AS created_date,
       CAST(NULL AS DATE) AS due_date, CAST(NULL AS DATE) AS closed_date
WHERE 1=0;

CREATE OR REPLACE TEMPORARY VIEW sv_punch_items AS
SELECT CAST(NULL AS STRING) AS project_id, CAST(NULL AS STRING) AS punch_item_id,
       CAST(NULL AS STRING) AS punch_item_number, CAST(NULL AS STRING) AS title,
       CAST(NULL AS STRING) AS punch_item_type, CAST(NULL AS STRING) AS status_label,
       CAST(NULL AS STRING) AS priority, CAST(NULL AS STRING) AS trade,
       CAST(NULL AS STRING) AS manager_name, CAST(NULL AS STRING) AS cost_code_id,
       CAST(NULL AS DATE) AS created_date, CAST(NULL AS DATE) AS due_date,
       CAST(NULL AS DATE) AS closed_date
WHERE 1=0;

-- Empty under this source: no incident or manpower data exists in the existing warehouse.
-- Declared with real types so gold/26 runs unchanged under both sources.
CREATE OR REPLACE TEMPORARY VIEW sv_incidents AS
SELECT CAST(NULL AS STRING) AS project_id, CAST(NULL AS STRING) AS incident_id,
       CAST(NULL AS STRING) AS title, CAST(NULL AS STRING) AS status_label,
       CAST(NULL AS BOOLEAN) AS is_recordable, CAST(NULL AS DATE) AS event_date
WHERE 1=0;

CREATE OR REPLACE TEMPORARY VIEW sv_manpower_daily AS
SELECT CAST(NULL AS STRING) AS project_id, CAST(NULL AS DATE) AS log_date,
       CAST(NULL AS DOUBLE) AS total_hours, CAST(NULL AS DOUBLE) AS total_workers
WHERE 1=0;


-- Empty under this source. The existing warehouse holds no progress billing, no direct
-- costs and no project-vendor bridge - which is also why retainage could not be reported
-- from it. Declared with real types so gold/27-29 run unchanged under both sources; a
-- missing view would fail the build, and a wrongly-typed one would fail later and further
-- from the cause.
CREATE OR REPLACE TEMPORARY VIEW sv_billing AS
SELECT CAST(NULL AS STRING) AS billing_type, CAST(NULL AS STRING) AS project_id,
       CAST(NULL AS STRING) AS billing_id, CAST(NULL AS STRING) AS invoice_number,
       CAST(NULL AS INT) AS period_number, CAST(NULL AS STRING) AS status_label,
       CAST(NULL AS STRING) AS vendor_id, CAST(NULL AS STRING) AS counterparty_name,
       CAST(NULL AS STRING) AS contract_id, CAST(NULL AS STRING) AS contract_name,
       CAST(NULL AS STRING) AS contract_type, CAST(NULL AS DATE) AS billing_date,
       CAST(NULL AS DATE) AS period_start, CAST(NULL AS DATE) AS period_end,
       CAST(NULL AS DATE) AS payment_date, CAST(NULL AS DOUBLE) AS percent_complete,
       CAST(NULL AS DOUBLE) AS original_contract_sum,
       CAST(NULL AS DOUBLE) AS net_change_by_change_orders,
       CAST(NULL AS DOUBLE) AS contract_sum_to_date, CAST(NULL AS DOUBLE) AS completed_to_date,
       CAST(NULL AS DOUBLE) AS previous_certificates, CAST(NULL AS DOUBLE) AS retainage_amount,
       CAST(NULL AS DOUBLE) AS retainage_percent,
       CAST(NULL AS DOUBLE) AS stored_retainage_amount,
       CAST(NULL AS DOUBLE) AS total_retainage, CAST(NULL AS DOUBLE) AS earned_less_retainage,
       CAST(NULL AS DOUBLE) AS current_payment_due, CAST(NULL AS DOUBLE) AS balance_to_finish
WHERE 1=0;

CREATE OR REPLACE TEMPORARY VIEW sv_direct_costs AS
SELECT CAST(NULL AS STRING) AS project_id, CAST(NULL AS STRING) AS direct_cost_id,
       CAST(NULL AS STRING) AS description, CAST(NULL AS STRING) AS cost_type,
       CAST(NULL AS STRING) AS status_label, CAST(NULL AS STRING) AS vendor_id,
       CAST(NULL AS STRING) AS vendor_name, CAST(NULL AS STRING) AS employee_name,
       CAST(NULL AS DATE) AS cost_date, CAST(NULL AS DOUBLE) AS amount,
       CAST(NULL AS DOUBLE) AS grand_total
WHERE 1=0;

CREATE OR REPLACE TEMPORARY VIEW sv_project_vendors AS
SELECT CAST(NULL AS STRING) AS project_id, CAST(NULL AS STRING) AS vendor_id,
       CAST(NULL AS STRING) AS vendor_name, CAST(NULL AS STRING) AS trade_name,
       CAST(NULL AS STRING) AS city, CAST(NULL AS STRING) AS state_code,
       CAST(NULL AS STRING) AS business_phone, CAST(NULL AS STRING) AS email_address,
       CAST(NULL AS BOOLEAN) AS is_prequalified, CAST(NULL AS BOOLEAN) AS is_active,
       CAST(NULL AS BOOLEAN) AS is_union_member, CAST(NULL AS STRING) AS license_number,
       CAST(NULL AS STRING) AS labor_union, CAST(NULL AS BOOLEAN) AS synced_to_erp
WHERE 1=0;


-- Empty under this source: the existing warehouse has neither direct cost line items nor
-- insurance. Typed so gold/31-32 run unchanged under both sources.
CREATE OR REPLACE TEMPORARY VIEW sv_direct_cost_lines AS
SELECT CAST(NULL AS STRING) AS project_id, CAST(NULL AS STRING) AS line_item_id,
       CAST(NULL AS STRING) AS direct_cost_id, CAST(NULL AS STRING) AS holder_type,
       CAST(NULL AS STRING) AS cost_code_id, CAST(NULL AS STRING) AS cost_code,
       CAST(NULL AS STRING) AS cost_code_name, CAST(NULL AS STRING) AS description,
       CAST(NULL AS STRING) AS line_item_type, CAST(NULL AS DOUBLE) AS amount,
       CAST(NULL AS DOUBLE) AS total_amount, CAST(NULL AS DOUBLE) AS quantity,
       CAST(NULL AS DOUBLE) AS unit_cost, CAST(NULL AS STRING) AS unit_of_measure
WHERE 1=0;

CREATE OR REPLACE TEMPORARY VIEW sv_vendor_insurance AS
SELECT CAST(NULL AS STRING) AS insurance_id, CAST(NULL AS STRING) AS vendor_id,
       CAST(NULL AS STRING) AS insurance_type, CAST(NULL AS STRING) AS provider,
       CAST(NULL AS STRING) AS policy_number, CAST(NULL AS STRING) AS status_label,
       CAST(NULL AS DATE) AS effective_date, CAST(NULL AS DATE) AS expiration_date,
       CAST(NULL AS DOUBLE) AS coverage_limit_raw, CAST(NULL AS BOOLEAN) AS is_exempt,
       CAST(NULL AS BOOLEAN) AS info_received, CAST(NULL AS BOOLEAN) AS additional_insured,
       CAST(NULL AS STRING) AS notes
WHERE 1=0;


-- Empty under this source: the existing warehouse has commitment headers but no line
-- items, so the vendor <-> cost-code join cannot be made from it at all.
CREATE OR REPLACE TEMPORARY VIEW sv_commitments AS
SELECT CAST(NULL AS STRING) AS commitment_type, CAST(NULL AS STRING) AS project_id,
       CAST(NULL AS STRING) AS commitment_id, CAST(NULL AS STRING) AS commitment_number,
       CAST(NULL AS STRING) AS title, CAST(NULL AS STRING) AS status_label,
       CAST(NULL AS STRING) AS vendor_id, CAST(NULL AS STRING) AS vendor_name,
       CAST(NULL AS DOUBLE) AS grand_total, CAST(NULL AS DOUBLE) AS total_payments,
       CAST(NULL AS DOUBLE) AS total_requisitioned, CAST(NULL AS BOOLEAN) AS is_executed
WHERE 1=0;

CREATE OR REPLACE TEMPORARY VIEW sv_commitment_lines AS
SELECT CAST(NULL AS STRING) AS project_id, CAST(NULL AS STRING) AS line_item_id,
       CAST(NULL AS STRING) AS commitment_id, CAST(NULL AS STRING) AS holder_type,
       CAST(NULL AS STRING) AS source_endpoint, CAST(NULL AS STRING) AS cost_code_id,
       CAST(NULL AS STRING) AS cost_code, CAST(NULL AS STRING) AS cost_code_name,
       CAST(NULL AS STRING) AS description, CAST(NULL AS STRING) AS line_item_type,
       CAST(NULL AS DOUBLE) AS amount, CAST(NULL AS DOUBLE) AS total_amount,
       CAST(NULL AS DOUBLE) AS quantity, CAST(NULL AS DOUBLE) AS unit_cost
WHERE 1=0;
