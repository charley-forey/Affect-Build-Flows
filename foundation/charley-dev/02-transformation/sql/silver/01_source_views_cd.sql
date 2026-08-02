-- silver: THE SWITCH. Same sv_* contract, sourced from OUR OWN CD_Silver.
--
-- 00_source_views.sql reads Rebecca's existing Silver_Lakehouse read-only, which is how
-- the gold model was validated against real data before Procore credentials landed.
-- This file is its replacement: identical view names, identical column names, different
-- source.
--
-- Swapping them is the entire migration. deploy_gold.py picks the file via SOURCE_VIEWS.
-- No gold file, no measure, no report visual changes - which is exactly why source naming
-- was isolated in one place rather than spread across nine gold files.
--
-- NOT YET IN USE. cd_silver_* is empty until cd_01_extract_procore can authenticate
-- (see _docs/procore-ingestion.md). Switching now would produce an empty model, so
-- deploy_gold still points at 00_source_views.sql. Flip it when bronze has data.
--
-- The columns are already clean here - cd_silver_* was written to this contract - so these
-- views are mostly pass-throughs. The two that are not:
--
--   sv_vendors      Procore does not carry a Sage vendor id on the vendor record. It comes
--                   from the existing dim_procore_project_vendor crosswalk, which stays a
--                   read of the current warehouse until we own that mapping.
--   sv_outbuild_activities  Outbuild is a separate source with its own ingestion, not yet
--                   built. Until then it keeps reading the existing Silver lakehouse -
--                   which is also the only place milestone data exists at all.

CREATE OR REPLACE TEMPORARY VIEW sv_projects AS
SELECT project_id, project_name,
       -- The Sage id is not on the Procore project record; it comes from the crosswalk.
       CAST(NULL AS STRING) AS sage_project_id,
       'PROCORE' AS origin_code
FROM cd_silver_projects;

CREATE OR REPLACE TEMPORARY VIEW sv_vendors AS
SELECT procore_vendor_id, sage_vendor_id, vendor_name
FROM cd_silver_vendors;

CREATE OR REPLACE TEMPORARY VIEW sv_cost_codes AS
SELECT cost_code_id, cost_code_name
FROM cd_silver_cost_codes;

CREATE OR REPLACE TEMPORARY VIEW sv_prime_contracts AS
SELECT prime_contract_id, project_id, contract_value, retainage_pct,
       start_date, estimated_completion_date, status
FROM cd_silver_prime_contracts;

CREATE OR REPLACE TEMPORARY VIEW sv_prime_change_orders AS
SELECT project_id, change_order_id, contract_id, created_date, amount, co_number, status
FROM cd_silver_prime_change_orders;

CREATE OR REPLACE TEMPORARY VIEW sv_budgets AS
SELECT project_id, cost_code_id, cost_code, category, snapshot_date,
       original_budget, budget_modifications, updated_budget, forecast_budget,
       committed_to_date, direct_costs, invoiced_to_date, cost_to_complete
FROM cd_silver_budgets;

-- AR stays with Sage: this is the one source Procore does not hold. It moves here when
-- CD_Sage_Ingest is built (blocked on the on-prem gateway).
CREATE OR REPLACE TEMPORARY VIEW sv_ar_invoices AS
SELECT sage_project_id, invoice_date, due_date, description,
       invoice_total, amount_paid, invoice_balance, billing_period
FROM cd_silver_ar_invoices;

-- Submittals AND RFIs. The RFI arm is new - no RFI data exists anywhere in the warehouse
-- today, so this union is the half of the workbook's only chart that has never been
-- automated. fct_RfiSubmittal reads sv_submittals; the union happens here so gold does not
-- need to know there are two sources.
CREATE OR REPLACE TEMPORARY VIEW sv_submittals AS
SELECT project_id, item_id, item_number, subject, status_label, cost_code_id,
       created_date, due_date, responded_date
FROM cd_silver_submittals;

CREATE OR REPLACE TEMPORARY VIEW sv_rfis AS
SELECT project_id, item_id, item_number, subject, status_label, priority, cost_code_id,
       created_date, due_date, responded_date
FROM cd_silver_rfis;
