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
