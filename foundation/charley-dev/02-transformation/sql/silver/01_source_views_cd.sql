-- silver: THE SWITCH. Same sv_* contract, sourced from OUR OWN CD_Silver.
--
-- 00_source_views.sql reads Rebecca's existing Silver_Lakehouse read-only, which is how
-- the gold model was validated against real data before Procore credentials landed.
-- This file is its replacement: identical view names, identical column names, different
-- source.
--
-- Swapping them is the entire migration. deploy_gold.py picks the file via --source.
-- No gold file, no measure, no report visual changes - which is exactly why source naming
-- was isolated in one place rather than spread across nine gold files.
--
--     python deploy_gold.py --source existing --apply    (00_source_views.sql, the default)
--     python deploy_gold.py --source cd --apply          (this file)
--
-- IN USE as of 2026-08-02: cd_silver_* is populated from Affect's production Procore tenant
-- (see _docs/procore-ingestion.md).
--
-- TWO PLACEHOLDERS, because the switch is per-view rather than all-or-nothing:
--
--   {CD_SILVER_ABFSS}  our own CD_Silver_Lakehouse - the tables Procore now feeds.
--   {SILVER_ABFSS}     the EXISTING Silver lakehouse, read-only, for the sources Procore
--                      does not hold yet.
--
-- Both are substituted by deploy_gold.py from _local/fabric_ids.json. Views read through
-- abfss rather than by bare name because gold's notebook runs with CD_Gold_Lakehouse as its
-- default catalog - an unqualified cd_silver_projects does not resolve from there.
--
-- Three views still read the existing warehouse, each for a reason that is not laziness:
--
--   sv_ar_invoices          Sage AR. Procore does not hold it and CD_Sage_Ingest is blocked
--                           on the on-prem gateway.
--   sv_outbuild_activities  Outbuild. The only source of milestone data anywhere - Procore's
--                           OAS has no milestone endpoint - and its ingestion is not built.
--   sv_vendors              carries sage_vendor_id, which Procore does not put on the vendor
--                           record; it comes from the existing crosswalk.
--
-- Pointing a view at the old source is a smaller problem than pointing it at an empty new
-- one: fct_Invoice keeps its 117 rows through the switch instead of going to zero.

CREATE OR REPLACE TEMPORARY VIEW sv_projects AS
SELECT project_id, project_name,
       -- The Sage id is not on the Procore project record; it comes from the crosswalk.
       CAST(NULL AS STRING) AS sage_project_id,
       'PROCORE' AS origin_code
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_projects`;

-- Vendors stay on the existing crosswalk, and this one is easy to get wrong: Procore's
-- vendor record has no Sage vendor id, so cd_silver_vendors sets sage_vendor_id to NULL
-- (10_procore_silver.sql:46). Sourcing this view from our own silver would look like a
-- clean switch and would silently break every vendor-to-Sage join in gold - the mapping
-- only exists in dim_procore_project_vendor.
--
-- Our 1,098 Procore vendors are already landed and typed in cd_silver_vendors; they take
-- over here the moment we own the Sage side of the mapping.
CREATE OR REPLACE TEMPORARY VIEW sv_vendors AS
SELECT
    CAST(`Procore Vendor ID` AS STRING) AS procore_vendor_id,
    CAST(`Sage Vendor ID`    AS STRING) AS sage_vendor_id,
    CAST(`Vendor Name`       AS STRING) AS vendor_name
FROM delta.`{SILVER_ABFSS}/dim_procore_project_vendor`;

CREATE OR REPLACE TEMPORARY VIEW sv_cost_codes AS
SELECT cost_code_id, cost_code, cost_code_name
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_cost_codes`;

CREATE OR REPLACE TEMPORARY VIEW sv_prime_contracts AS
SELECT prime_contract_id, project_id, contract_value, retainage_pct,
       start_date, estimated_completion_date, status
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_prime_contracts`;

CREATE OR REPLACE TEMPORARY VIEW sv_prime_change_orders AS
SELECT project_id, change_order_id, contract_id, created_date, amount, co_number, status
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_prime_change_orders`;

CREATE OR REPLACE TEMPORARY VIEW sv_budgets AS
SELECT project_id, cost_code_id, cost_code, category, snapshot_date,
       original_budget, budget_modifications, updated_budget, forecast_budget,
       committed_to_date, direct_costs, invoiced_to_date, cost_to_complete
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_budgets`;

-- AR stays with Sage: this is the one source Procore does not hold, and CD_Sage_Ingest is
-- blocked on the on-prem gateway. So this view keeps reading the EXISTING Silver lakehouse
-- read-only, exactly as 00_source_views.sql does.
--
-- Switching source is per-view, not all-or-nothing, and that is deliberate: Procore
-- overtakes the existing warehouse endpoint by endpoint, and a view still pointing at the
-- old source is a smaller problem than a view pointing at an empty new one. fct_Invoice
-- keeps its 117 rows through the switch rather than going to zero.
-- Copied verbatim from 00_source_views.sql, including the casts. Retyping it from memory
-- got the column names wrong; the two must stay identical anyway, because gold reads the
-- same sv_ar_invoices either way.
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

-- Submittals AND RFIs. The RFI arm is new - no RFI data exists anywhere in the warehouse
-- today, so this union is the half of the workbook's only chart that has never been
-- automated. fct_RfiSubmittal reads sv_submittals; the union happens here so gold does not
-- need to know there are two sources.
CREATE OR REPLACE TEMPORARY VIEW sv_submittals AS
SELECT project_id, item_id, item_number, subject, status_label, cost_code_id,
       created_date, due_date, responded_date
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_submittals`;

CREATE OR REPLACE TEMPORARY VIEW sv_rfis AS
SELECT project_id, item_id, item_number, subject, status_label, priority, cost_code_id,
       created_date, due_date, responded_date
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_rfis`;

-- Outbuild is the ONLY source of milestone data anywhere in the estate - Procore's
-- OAS has no milestone endpoint - and CD_Outbuild ingestion is not built yet. So this
-- view keeps reading the existing Silver lakehouse read-only, verbatim from
-- 00_source_views.sql. Omitting it entirely is what would break fct_Milestone: gold
-- reads sv_outbuild_activities unconditionally, so a missing view is a hard failure,
-- not an empty fact.
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
-- FIELD OPERATIONS - the quality and safety halves of the scorecard
-- ---------------------------------------------------------------------------
--
-- Live from our own Procore ingestion as of 2026-08-02: 850 observations, 1,469 punch
-- items, 3 incidents. None of this exists in the existing warehouse.

CREATE OR REPLACE TEMPORARY VIEW sv_observations AS
SELECT project_id, observation_id, observation_number, title, observation_type,
       status_label, priority, trade, assignee_name, created_date, due_date, closed_date
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_observations`;

CREATE OR REPLACE TEMPORARY VIEW sv_punch_items AS
SELECT project_id, punch_item_id, punch_item_number, title, punch_item_type,
       status_label, priority, trade, manager_name, cost_code_id,
       created_date, due_date, closed_date
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_punch_items`;
