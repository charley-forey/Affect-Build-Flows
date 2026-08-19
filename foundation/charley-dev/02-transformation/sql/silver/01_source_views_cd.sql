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

CREATE OR REPLACE TEMPORARY VIEW sv_incidents AS
SELECT project_id, incident_id, title, status_label, is_recordable, event_date
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_incidents`;

CREATE OR REPLACE TEMPORARY VIEW sv_manpower_daily AS
SELECT project_id, log_date, total_hours, total_workers
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_manpower_daily`;


-- ---------------------------------------------------------------------------
-- PROGRESS BILLING, DIRECT COSTS, VENDOR BRIDGE
-- ---------------------------------------------------------------------------
--
-- Live from our own Procore ingestion as of 2026-08-02: 607 billing periods (134 owner,
-- 473 sub), 418 direct costs, 393 project-vendor pairs. None of it exists in the existing
-- warehouse, and retainage exists nowhere else at all.

CREATE OR REPLACE TEMPORARY VIEW sv_billing AS
SELECT billing_type, project_id, billing_id, invoice_number, period_number, status_label,
       vendor_id, counterparty_name, contract_id, contract_name, contract_type,
       billing_date, period_start, period_end, payment_date, percent_complete,
       original_contract_sum, net_change_by_change_orders, contract_sum_to_date,
       completed_to_date, previous_certificates, retainage_amount, retainage_percent,
       stored_retainage_amount, total_retainage, earned_less_retainage,
       current_payment_due, balance_to_finish
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_billing`;

CREATE OR REPLACE TEMPORARY VIEW sv_direct_costs AS
SELECT project_id, direct_cost_id, description, cost_type, status_label,
       vendor_id, vendor_name, employee_name, cost_date, amount, grand_total
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_direct_costs`;

CREATE OR REPLACE TEMPORARY VIEW sv_project_vendors AS
SELECT project_id, vendor_id, vendor_name, trade_name, city, state_code, business_phone,
       email_address, is_prequalified, is_active, is_union_member, license_number,
       labor_union, synced_to_erp
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_project_vendors`;


-- ---------------------------------------------------------------------------
-- VENDOR <-> COST CODE, AND INSURANCE
-- ---------------------------------------------------------------------------
--
-- Phase 0 items 3 and 4. Live as of 2026-08-02: 509 direct cost line items (all with a
-- cost code) and 105 insurance certificates across 23 vendors.

CREATE OR REPLACE TEMPORARY VIEW sv_direct_cost_lines AS
SELECT project_id, line_item_id, direct_cost_id, holder_type, cost_code_id, cost_code,
       cost_code_name, description, line_item_type, amount, total_amount,
       quantity, unit_cost, unit_of_measure
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_direct_cost_lines`;

CREATE OR REPLACE TEMPORARY VIEW sv_vendor_insurance AS
SELECT insurance_id, vendor_id, insurance_type, provider, policy_number, status_label,
       effective_date, expiration_date, coverage_limit_raw, is_exempt, info_received,
       additional_insured, notes
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_vendor_insurance`;


-- Commitments: 189 subcontracts + 109 purchase orders, 431 line items, all cost-coded.
CREATE OR REPLACE TEMPORARY VIEW sv_commitments AS
SELECT commitment_type, project_id, commitment_id, commitment_number, title, status_label,
       vendor_id, vendor_name, grand_total, total_payments, total_requisitioned, is_executed
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_commitments`;

CREATE OR REPLACE TEMPORARY VIEW sv_commitment_lines AS
SELECT project_id, line_item_id, commitment_id, holder_type, source_endpoint, cost_code_id,
       cost_code, cost_code_name, description, line_item_type, amount, total_amount,
       quantity, unit_cost
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_commitment_lines`;


-- ---------------------------------------------------------------------------
-- MANUAL INPUT - the ~40% that exists in no system of record
-- ---------------------------------------------------------------------------
--
-- These are the views that were MISSING, and their absence is why gold's nine man_* tables
-- were permanently empty: 40_man_tables.sql had nothing to select from, so it declared the
-- schema and stopped. The whole manual chain - CSV template, cd_06_land_manual, the silver
-- parsers, the reject log, the semantic model bindings - ran end to end and delivered
-- nothing, with no error anywhere to say so.
--
-- CD-ONLY. There is no counterpart in 00_source_views.sql, because the existing warehouse
-- holds none of this: the manual data was invented as part of THIS build and lives only in
-- cd_bronze_man_* / cd_silver_man_*. deploy_gold.py --source existing therefore skips the
-- gold files that read these (see GOLD_CD_ONLY there) rather than being handed empty views
-- that pretend a source exists.

CREATE OR REPLACE TEMPORARY VIEW sv_man_wins AS
SELECT project_id, month_start, win_number, description, win_type
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_man_wins`;

CREATE OR REPLACE TEMPORARY VIEW sv_man_risks AS
SELECT project_id, month_start, risk_number, description, impact_code, mitigation,
       owner_role, status_code
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_man_risks`;

CREATE OR REPLACE TEMPORARY VIEW sv_man_priority_items AS
SELECT project_id, month_start, item_number, schedule_item, status_code, critical_delays,
       recovery_plan, forecast_impact, notes
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_man_priority_items`;

CREATE OR REPLACE TEMPORARY VIEW sv_man_flags AS
SELECT project_id, month_start, profitability_code, contingency_remaining,
       baseline_approved, baseline_revision, month_end_closed_out, forecasting_in_line,
       resources_updated
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_man_flags`;

CREATE OR REPLACE TEMPORARY VIEW sv_man_survey AS
SELECT project_id, month_start, question_number, question_text, score, surveyed_party
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_man_survey`;

CREATE OR REPLACE TEMPORARY VIEW sv_man_safety_monthly AS
SELECT project_id, month_start, hours_worked, recordable_incidents, orientations, ot_hours
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_man_safety_monthly`;

CREATE OR REPLACE TEMPORARY VIEW sv_man_quality_monthly AS
SELECT project_id, month_start, observations, punchlist_items, avg_days_past_due,
       avg_days_to_close
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_man_quality_monthly`;

CREATE OR REPLACE TEMPORARY VIEW sv_man_milestones AS
SELECT project_id, activity_key, milestone_name, contract_start, contract_finish,
       baseline_start, baseline_finish, is_substantial_completion
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_man_milestones`;

CREATE OR REPLACE TEMPORARY VIEW sv_man_daily_log_compliance AS
SELECT project_id, month_start, logs_expected, logs_missed_same_day
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_man_daily_log_compliance`;


-- ---------------------------------------------------------------------------
-- PQP - the Project Quality Plan subject area
-- ---------------------------------------------------------------------------
--
-- Two halves, and which half a thing lands in is the design:
--
--   sv_qc_*      PROCORE. NCRs, punch items, submittals, inspections. Procore is the
--                client's mandatory system of record for quality, so these are read from
--                the API and never typed.
--   sv_man_qc_*  SHAREPOINT. The DFOW register, the ITP, gate progress, special
--                inspections, commissioning, the inspector sign-in log, and the per-project
--                answers against the checklist and DOH templates. No system holds these.
--
-- The TEMPLATES (26 trade checklists, 93 gates, 101 DOH items) are neither: they are seeds
-- in gold (08_qc_seeds.sql), identical on every project, so they never travel through
-- silver at all.

CREATE OR REPLACE TEMPORARY VIEW sv_qc_ncr AS
SELECT project_id, ncr_id, ncr_number, title, description, observation_type, category,
       trade, assignee_name, priority, source_status, status_code, item_class_code,
       created_date, due_date, closed_date
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_qc_ncr`;

CREATE OR REPLACE TEMPORARY VIEW sv_qc_punch AS
SELECT project_id, punch_id, punch_number, title, punch_item_type, trade, manager_name,
       cost_code_id, priority, source_status, status_code, item_class_code,
       created_date, due_date, closed_date
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_qc_punch`;

CREATE OR REPLACE TEMPORARY VIEW sv_qc_submittal AS
SELECT project_id, submittal_id, submittal_number, subject, cost_code_id, source_status,
       status_code, submittal_type_code, created_date, due_date, responded_date
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_qc_submittal`;

CREATE OR REPLACE TEMPORARY VIEW sv_qc_inspection AS
SELECT project_id, inspection_id, inspection_number, name, inspection_type, template_name,
       trade, inspector_name, source_status, inspection_date, due_date, percent_complete
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_qc_inspection`;

CREATE OR REPLACE TEMPORARY VIEW sv_man_qc_dfow AS
SELECT project_id, dfow_ref, dfow_description, trade_key, risk_tier, control_measure,
       owner_role, status_code, notes
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_man_qc_dfow`;

CREATE OR REPLACE TEMPORARY VIEW sv_man_qc_itp AS
SELECT project_id, itp_ref, trade_key, activity, inspection_type, acceptance_criteria,
       hold_point_type, responsible, planned_date, actual_date, result_code, status_code,
       notes
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_man_qc_itp`;

CREATE OR REPLACE TEMPORARY VIEW sv_man_qc_gate AS
SELECT project_id, gate_key, gate_type, status_code, responsible, target_date,
       submitted_date, completed_date, evidence_link, blocker_note
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_man_qc_gate`;

CREATE OR REPLACE TEMPORARY VIEW sv_man_qc_special_inspection AS
SELECT project_id, inspection_ref, category, agency, inspector_name, required_code,
       performed_code, scheduled_date, performed_date, report_received_date, status_code,
       notes
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_man_qc_special_inspection`;

CREATE OR REPLACE TEMPORARY VIEW sv_man_qc_commissioning AS
SELECT project_id, system_ref, system_name, trade_key, responsible, planned_date,
       actual_date, status_code, notes
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_man_qc_commissioning`;

CREATE OR REPLACE TEMPORARY VIEW sv_man_qc_inspector_sign_in AS
SELECT project_id, sign_in_ref, visit_date, inspector_name, agency_code, purpose,
       area_inspected, outcome_code, follow_up_required, notes
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_man_qc_inspector_sign_in`;

CREATE OR REPLACE TEMPORARY VIEW sv_man_qc_checklist_result AS
SELECT project_id, trade_key, item_key, stage_code, result_code, inspected_date,
       inspected_by, notes
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_man_qc_checklist_result`;

CREATE OR REPLACE TEMPORARY VIEW sv_man_qc_doh_result AS
SELECT project_id, item_key, responsibility_code, status_code, verified_date, verified_by,
       evidence_link, notes
FROM delta.`{CD_SILVER_ABFSS}/cd_silver_man_qc_doh_result`;
