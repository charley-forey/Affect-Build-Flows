-- silver: the PQP (Project Quality Plan) hand-entered inputs, typed and validated.
--
-- Source is the eight SharePoint lists / CSV templates that carry the QA/QC workbook's
-- per-project answers. Exactly the same three rules as 30_manual_silver.sql, and for
-- exactly the same reasons:
--
--   1. REJECT WITH A REASON, NEVER DROP. -> cd_dq_rejects_qc at the bottom.
--   2. ONE ROW PER NATURAL KEY. SharePoint cannot enforce a composite unique constraint,
--      so it is enforced here. A duplicated checklist answer is not a harmless repeat: it
--      double-counts into "% of items passed", which is a number on a client-facing page.
--   3. COLUMN NAMES COME FROM sql/gold/41_man_qc_tables.sql. That DDL is the single source
--      of truth for the SharePoint columns, the CSV templates and the semantic model; this
--      file lower-cases them and does nothing else clever. When those three drift, the
--      manual pipeline silently stops arriving - which is the failure 40_man_tables.sql
--      spent a year in.
--
-- WHAT IS *NOT* VALIDATED HERE, and deliberately. Status codes are not checked against
-- dim_QcStatus, and TradeKey / ItemKey / GateKey are not checked against qc_seed_*. Those
-- live in GOLD, and silver reading gold would invert the layering for no gain: the DQ
-- suite (02-transformation/dq/expectations.py) checks every one of them where both sides
-- are in scope, and a violation there names the row rather than swallowing it.
--
-- FILE PREFIX. 31, not 30. deploy_silver.py globs the silver folder and skips only the
-- 00/01 source-view files, so 31 IS deployed - which is what we want, because
-- cd_06_land_manual creates every cd_bronze_man_qc_* table (empty and correctly typed)
-- before this notebook runs. Run order is the dependency, not the filter.

-- ---------------------------------------------------------------------------
-- Shared: the project allow-list, same view 30_manual_silver.sql builds
-- ---------------------------------------------------------------------------
-- Re-declared rather than assumed: the two files run in the same session today, but a
-- temporary view is not a dependency anyone can see, and 31 must not break the day 30 is
-- split out or reordered.

CREATE OR REPLACE TEMPORARY VIEW qcv_valid_projects AS
SELECT DISTINCT project_id FROM cd_silver_projects;

-- ---------------------------------------------------------------------------
-- Definable Features of Work risk register
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TEMPORARY VIEW qcv_dfow AS
SELECT *,
       MAX(_version) OVER (PARTITION BY _reject_reason, project_id, dfow_ref) AS _versions,
       ROW_NUMBER() OVER (PARTITION BY _reject_reason, project_id, dfow_ref, _version
                          ORDER BY last_modified DESC) AS _copy
FROM (
    SELECT *,
           DENSE_RANK() OVER (PARTITION BY _reject_reason, project_id, dfow_ref
                              ORDER BY dfow_description, trade_key, risk_tier, control_measure, owner_role, status_code, notes) AS _version
    FROM (
        SELECT
            TRIM(b.ProjectKey.Title)                             AS project_id,
            UPPER(TRIM(b.DfowRef))                               AS dfow_ref,
            TRIM(b.DfowDescription)                              AS dfow_description,
            UPPER(TRIM(b.TradeKey))                              AS trade_key,
            CAST(b.RiskTier AS INT)                              AS risk_tier,
            TRIM(b.ControlMeasure)                               AS control_measure,
            TRIM(b.OwnerRole)                                    AS owner_role,
            UPPER(TRIM(b.StatusCode))                            AS status_code,
            TRIM(b.Notes)                                        AS notes,
            CAST(b.Modified AS TIMESTAMP)                        AS last_modified,
            TRIM(b.Editor.Title)                                 AS last_modified_by,
            CASE
                WHEN b.ProjectKey.Title IS NULL
                     THEN 'missing ProjectKey'
                WHEN b.DfowRef IS NULL
                     THEN 'missing DfowRef'
                WHEN v.project_id IS NULL AND UPPER(TRIM(b.ProjectKey.Title)) = 'ALL'
                     THEN 'ALL is only valid on CD Project Access'
                WHEN v.project_id IS NULL
                     THEN 'unknown project - is CD Projects stale?'
            END AS _reject_reason
        FROM cd_bronze_man_qc_dfow b
        LEFT JOIN qcv_valid_projects v ON v.project_id = TRIM(b.ProjectKey.Title)
    )
);

CREATE OR REPLACE TABLE cd_silver_man_qc_dfow AS
SELECT project_id, dfow_ref, dfow_description, trade_key, risk_tier, control_measure, owner_role, status_code, notes,
       last_modified, last_modified_by
FROM qcv_dfow
WHERE _reject_reason IS NULL AND _versions = 1 AND _copy = 1;

-- ---------------------------------------------------------------------------
-- Inspection & Test Plan
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TEMPORARY VIEW qcv_itp AS
SELECT *,
       MAX(_version) OVER (PARTITION BY _reject_reason, project_id, itp_ref) AS _versions,
       ROW_NUMBER() OVER (PARTITION BY _reject_reason, project_id, itp_ref, _version
                          ORDER BY last_modified DESC) AS _copy
FROM (
    SELECT *,
           DENSE_RANK() OVER (PARTITION BY _reject_reason, project_id, itp_ref
                              ORDER BY trade_key, activity, inspection_type, acceptance_criteria, hold_point_type, responsible, planned_date, actual_date, result_code, status_code, notes) AS _version
    FROM (
        SELECT
            TRIM(b.ProjectKey.Title)                             AS project_id,
            UPPER(TRIM(b.ItpRef))                                AS itp_ref,
            UPPER(TRIM(b.TradeKey))                              AS trade_key,
            TRIM(b.Activity)                                     AS activity,
            TRIM(b.InspectionType)                               AS inspection_type,
            TRIM(b.AcceptanceCriteria)                           AS acceptance_criteria,
            TRIM(b.HoldPointType)                                AS hold_point_type,
            TRIM(b.Responsible)                                  AS responsible,
            CAST(b.PlannedDate AS DATE)                          AS planned_date,
            CAST(b.ActualDate AS DATE)                           AS actual_date,
            UPPER(TRIM(b.ResultCode))                            AS result_code,
            UPPER(TRIM(b.StatusCode))                            AS status_code,
            TRIM(b.Notes)                                        AS notes,
            CAST(b.Modified AS TIMESTAMP)                        AS last_modified,
            TRIM(b.Editor.Title)                                 AS last_modified_by,
            CASE
                WHEN b.ProjectKey.Title IS NULL
                     THEN 'missing ProjectKey'
                WHEN b.ItpRef IS NULL
                     THEN 'missing ItpRef'
                WHEN v.project_id IS NULL AND UPPER(TRIM(b.ProjectKey.Title)) = 'ALL'
                     THEN 'ALL is only valid on CD Project Access'
                WHEN v.project_id IS NULL
                     THEN 'unknown project - is CD Projects stale?'
            END AS _reject_reason
        FROM cd_bronze_man_qc_itp b
        LEFT JOIN qcv_valid_projects v ON v.project_id = TRIM(b.ProjectKey.Title)
    )
);

CREATE OR REPLACE TABLE cd_silver_man_qc_itp AS
SELECT project_id, itp_ref, trade_key, activity, inspection_type, acceptance_criteria, hold_point_type, responsible, planned_date, actual_date, result_code, status_code, notes,
       last_modified, last_modified_by
FROM qcv_itp
WHERE _reject_reason IS NULL AND _versions = 1 AND _copy = 1;

-- ---------------------------------------------------------------------------
-- Gates - TCO, fire alarm and statutory in ONE table
-- ---------------------------------------------------------------------------
-- GateKey is globally unique across the three paths (TCO-A1, FA-01, STAT-01), so the
-- natural key is (project, gate) and GateType is an attribute rather than part of the key.
-- Uppercased because a gate typed as 'tco-a1' must not become a second gate.
--
-- The gate collapse's one new failure mode: three sheets became one table, so a row that
-- does not declare which path it is on cannot be routed at all. Loud, not dropped.

CREATE OR REPLACE TEMPORARY VIEW qcv_gate AS
SELECT *,
       MAX(_version) OVER (PARTITION BY _reject_reason, project_id, gate_key) AS _versions,
       ROW_NUMBER() OVER (PARTITION BY _reject_reason, project_id, gate_key, _version
                          ORDER BY last_modified DESC) AS _copy
FROM (
    SELECT *,
           DENSE_RANK() OVER (PARTITION BY _reject_reason, project_id, gate_key
                              ORDER BY gate_type, status_code, responsible, target_date, submitted_date, completed_date, evidence_link, blocker_note) AS _version
    FROM (
        SELECT
            TRIM(b.ProjectKey.Title)                             AS project_id,
            UPPER(TRIM(b.GateKey))                               AS gate_key,
            UPPER(TRIM(b.GateType))                              AS gate_type,
            UPPER(TRIM(b.StatusCode))                            AS status_code,
            TRIM(b.Responsible)                                  AS responsible,
            CAST(b.TargetDate AS DATE)                           AS target_date,
            CAST(b.SubmittedDate AS DATE)                        AS submitted_date,
            CAST(b.CompletedDate AS DATE)                        AS completed_date,
            TRIM(b.EvidenceLink)                                 AS evidence_link,
            TRIM(b.BlockerNote)                                  AS blocker_note,
            CAST(b.Modified AS TIMESTAMP)                        AS last_modified,
            TRIM(b.Editor.Title)                                 AS last_modified_by,
            CASE
                WHEN b.ProjectKey.Title IS NULL
                     THEN 'missing ProjectKey'
                WHEN b.GateKey IS NULL
                     THEN 'missing GateKey'
                WHEN v.project_id IS NULL AND UPPER(TRIM(b.ProjectKey.Title)) = 'ALL'
                     THEN 'ALL is only valid on CD Project Access'
                WHEN v.project_id IS NULL
                     THEN 'unknown project - is CD Projects stale?'
                WHEN UPPER(TRIM(COALESCE(b.GateType, ''))) NOT IN ('TCO', 'FIRE_ALARM', 'STATUTORY')
                     THEN CONCAT('invalid GateType: ', COALESCE(b.GateType, '(blank)'))
            END AS _reject_reason
        FROM cd_bronze_man_qc_gate b
        LEFT JOIN qcv_valid_projects v ON v.project_id = TRIM(b.ProjectKey.Title)
    )
);

CREATE OR REPLACE TABLE cd_silver_man_qc_gate AS
SELECT project_id, gate_key, gate_type, status_code, responsible, target_date, submitted_date, completed_date, evidence_link, blocker_note,
       last_modified, last_modified_by
FROM qcv_gate
WHERE _reject_reason IS NULL AND _versions = 1 AND _copy = 1;

-- ---------------------------------------------------------------------------
-- Special inspections
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TEMPORARY VIEW qcv_special_inspection AS
SELECT *,
       MAX(_version) OVER (PARTITION BY _reject_reason, project_id, inspection_ref) AS _versions,
       ROW_NUMBER() OVER (PARTITION BY _reject_reason, project_id, inspection_ref, _version
                          ORDER BY last_modified DESC) AS _copy
FROM (
    SELECT *,
           DENSE_RANK() OVER (PARTITION BY _reject_reason, project_id, inspection_ref
                              ORDER BY category, agency, inspector_name, required_code, performed_code, scheduled_date, performed_date, report_received_date, status_code, notes) AS _version
    FROM (
        SELECT
            TRIM(b.ProjectKey.Title)                             AS project_id,
            UPPER(TRIM(b.InspectionRef))                         AS inspection_ref,
            TRIM(b.Category)                                     AS category,
            TRIM(b.Agency)                                       AS agency,
            TRIM(b.InspectorName)                                AS inspector_name,
            UPPER(TRIM(b.RequiredCode))                          AS required_code,
            UPPER(TRIM(b.PerformedCode))                         AS performed_code,
            CAST(b.ScheduledDate AS DATE)                        AS scheduled_date,
            CAST(b.PerformedDate AS DATE)                        AS performed_date,
            CAST(b.ReportReceivedDate AS DATE)                   AS report_received_date,
            UPPER(TRIM(b.StatusCode))                            AS status_code,
            TRIM(b.Notes)                                        AS notes,
            CAST(b.Modified AS TIMESTAMP)                        AS last_modified,
            TRIM(b.Editor.Title)                                 AS last_modified_by,
            CASE
                WHEN b.ProjectKey.Title IS NULL
                     THEN 'missing ProjectKey'
                WHEN b.InspectionRef IS NULL
                     THEN 'missing InspectionRef'
                WHEN v.project_id IS NULL AND UPPER(TRIM(b.ProjectKey.Title)) = 'ALL'
                     THEN 'ALL is only valid on CD Project Access'
                WHEN v.project_id IS NULL
                     THEN 'unknown project - is CD Projects stale?'
            END AS _reject_reason
        FROM cd_bronze_man_qc_special_inspection b
        LEFT JOIN qcv_valid_projects v ON v.project_id = TRIM(b.ProjectKey.Title)
    )
);

CREATE OR REPLACE TABLE cd_silver_man_qc_special_inspection AS
SELECT project_id, inspection_ref, category, agency, inspector_name, required_code, performed_code, scheduled_date, performed_date, report_received_date, status_code, notes,
       last_modified, last_modified_by
FROM qcv_special_inspection
WHERE _reject_reason IS NULL AND _versions = 1 AND _copy = 1;

-- ---------------------------------------------------------------------------
-- Commissioning
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TEMPORARY VIEW qcv_commissioning AS
SELECT *,
       MAX(_version) OVER (PARTITION BY _reject_reason, project_id, system_ref) AS _versions,
       ROW_NUMBER() OVER (PARTITION BY _reject_reason, project_id, system_ref, _version
                          ORDER BY last_modified DESC) AS _copy
FROM (
    SELECT *,
           DENSE_RANK() OVER (PARTITION BY _reject_reason, project_id, system_ref
                              ORDER BY system_name, trade_key, responsible, planned_date, actual_date, status_code, notes) AS _version
    FROM (
        SELECT
            TRIM(b.ProjectKey.Title)                             AS project_id,
            UPPER(TRIM(b.SystemRef))                             AS system_ref,
            TRIM(b.SystemName)                                   AS system_name,
            UPPER(TRIM(b.TradeKey))                              AS trade_key,
            TRIM(b.Responsible)                                  AS responsible,
            CAST(b.PlannedDate AS DATE)                          AS planned_date,
            CAST(b.ActualDate AS DATE)                           AS actual_date,
            UPPER(TRIM(b.StatusCode))                            AS status_code,
            TRIM(b.Notes)                                        AS notes,
            CAST(b.Modified AS TIMESTAMP)                        AS last_modified,
            TRIM(b.Editor.Title)                                 AS last_modified_by,
            CASE
                WHEN b.ProjectKey.Title IS NULL
                     THEN 'missing ProjectKey'
                WHEN b.SystemRef IS NULL
                     THEN 'missing SystemRef'
                WHEN v.project_id IS NULL AND UPPER(TRIM(b.ProjectKey.Title)) = 'ALL'
                     THEN 'ALL is only valid on CD Project Access'
                WHEN v.project_id IS NULL
                     THEN 'unknown project - is CD Projects stale?'
            END AS _reject_reason
        FROM cd_bronze_man_qc_commissioning b
        LEFT JOIN qcv_valid_projects v ON v.project_id = TRIM(b.ProjectKey.Title)
    )
);

CREATE OR REPLACE TABLE cd_silver_man_qc_commissioning AS
SELECT project_id, system_ref, system_name, trade_key, responsible, planned_date, actual_date, status_code, notes,
       last_modified, last_modified_by
FROM qcv_commissioning
WHERE _reject_reason IS NULL AND _versions = 1 AND _copy = 1;

-- ---------------------------------------------------------------------------
-- Inspector sign-in log
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TEMPORARY VIEW qcv_inspector_sign_in AS
SELECT *,
       MAX(_version) OVER (PARTITION BY _reject_reason, project_id, sign_in_ref) AS _versions,
       ROW_NUMBER() OVER (PARTITION BY _reject_reason, project_id, sign_in_ref, _version
                          ORDER BY last_modified DESC) AS _copy
FROM (
    SELECT *,
           DENSE_RANK() OVER (PARTITION BY _reject_reason, project_id, sign_in_ref
                              ORDER BY visit_date, inspector_name, agency_code, purpose, area_inspected, outcome_code, follow_up_required, notes) AS _version
    FROM (
        SELECT
            TRIM(b.ProjectKey.Title)                             AS project_id,
            UPPER(TRIM(b.SignInRef))                             AS sign_in_ref,
            CAST(b.VisitDate AS DATE)                            AS visit_date,
            TRIM(b.InspectorName)                                AS inspector_name,
            UPPER(TRIM(b.AgencyCode))                            AS agency_code,
            TRIM(b.Purpose)                                      AS purpose,
            TRIM(b.AreaInspected)                                AS area_inspected,
            UPPER(TRIM(b.OutcomeCode))                           AS outcome_code,
            CAST(b.FollowUpRequired AS BOOLEAN)                  AS follow_up_required,
            TRIM(b.Notes)                                        AS notes,
            CAST(b.Modified AS TIMESTAMP)                        AS last_modified,
            TRIM(b.Editor.Title)                                 AS last_modified_by,
            CASE
                WHEN b.ProjectKey.Title IS NULL
                     THEN 'missing ProjectKey'
                WHEN b.SignInRef IS NULL
                     THEN 'missing SignInRef'
                WHEN v.project_id IS NULL AND UPPER(TRIM(b.ProjectKey.Title)) = 'ALL'
                     THEN 'ALL is only valid on CD Project Access'
                WHEN v.project_id IS NULL
                     THEN 'unknown project - is CD Projects stale?'
            END AS _reject_reason
        FROM cd_bronze_man_qc_inspector_sign_in b
        LEFT JOIN qcv_valid_projects v ON v.project_id = TRIM(b.ProjectKey.Title)
    )
);

CREATE OR REPLACE TABLE cd_silver_man_qc_inspector_sign_in AS
SELECT project_id, sign_in_ref, visit_date, inspector_name, agency_code, purpose, area_inspected, outcome_code, follow_up_required, notes,
       last_modified, last_modified_by
FROM qcv_inspector_sign_in
WHERE _reject_reason IS NULL AND _versions = 1 AND _copy = 1;

-- ---------------------------------------------------------------------------
-- Trade checklist results - all 26 trades, one table
-- ---------------------------------------------------------------------------
-- ItemKey is 'EXCAVATION-001' shaped, so it already carries its trade and is unique across
-- all 625 items. TradeKey is carried anyway: it is what the report slices by, and deriving
-- it from a string prefix at query time is how a trade with a hyphen in its key stops
-- working.
--
-- A checklist answer with no item key answers nothing - there is no way to know which of
-- the 625 items it belongs to, so it cannot be counted and must not be silently ignored.

CREATE OR REPLACE TEMPORARY VIEW qcv_checklist_result AS
SELECT *,
       MAX(_version) OVER (PARTITION BY _reject_reason, project_id, item_key) AS _versions,
       ROW_NUMBER() OVER (PARTITION BY _reject_reason, project_id, item_key, _version
                          ORDER BY last_modified DESC) AS _copy
FROM (
    SELECT *,
           DENSE_RANK() OVER (PARTITION BY _reject_reason, project_id, item_key
                              ORDER BY trade_key, stage_code, result_code, inspected_date, inspected_by, notes) AS _version
    FROM (
        SELECT
            TRIM(b.ProjectKey.Title)                             AS project_id,
            UPPER(TRIM(b.ItemKey))                               AS item_key,
            UPPER(TRIM(b.TradeKey))                              AS trade_key,
            UPPER(TRIM(b.StageCode))                             AS stage_code,
            UPPER(TRIM(b.ResultCode))                            AS result_code,
            CAST(b.InspectedDate AS DATE)                        AS inspected_date,
            TRIM(b.InspectedBy)                                  AS inspected_by,
            TRIM(b.Notes)                                        AS notes,
            CAST(b.Modified AS TIMESTAMP)                        AS last_modified,
            TRIM(b.Editor.Title)                                 AS last_modified_by,
            CASE
                WHEN b.ProjectKey.Title IS NULL
                     THEN 'missing ProjectKey'
                WHEN b.ItemKey IS NULL
                     THEN 'missing ItemKey - the answer cannot be attached to a checklist item'
                WHEN v.project_id IS NULL AND UPPER(TRIM(b.ProjectKey.Title)) = 'ALL'
                     THEN 'ALL is only valid on CD Project Access'
                WHEN v.project_id IS NULL
                     THEN 'unknown project - is CD Projects stale?'
            END AS _reject_reason
        FROM cd_bronze_man_qc_checklist_result b
        LEFT JOIN qcv_valid_projects v ON v.project_id = TRIM(b.ProjectKey.Title)
    )
);

CREATE OR REPLACE TABLE cd_silver_man_qc_checklist_result AS
SELECT project_id, item_key, trade_key, stage_code, result_code, inspected_date, inspected_by, notes,
       last_modified, last_modified_by
FROM qcv_checklist_result
WHERE _reject_reason IS NULL AND _versions = 1 AND _copy = 1;

-- ---------------------------------------------------------------------------
-- DOH checklist results
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TEMPORARY VIEW qcv_doh_result AS
SELECT *,
       MAX(_version) OVER (PARTITION BY _reject_reason, project_id, item_key) AS _versions,
       ROW_NUMBER() OVER (PARTITION BY _reject_reason, project_id, item_key, _version
                          ORDER BY last_modified DESC) AS _copy
FROM (
    SELECT *,
           DENSE_RANK() OVER (PARTITION BY _reject_reason, project_id, item_key
                              ORDER BY responsibility_code, status_code, verified_date, verified_by, evidence_link, notes) AS _version
    FROM (
        SELECT
            TRIM(b.ProjectKey.Title)                             AS project_id,
            UPPER(TRIM(b.ItemKey))                               AS item_key,
            UPPER(TRIM(b.ResponsibilityCode))                    AS responsibility_code,
            UPPER(TRIM(b.StatusCode))                            AS status_code,
            CAST(b.VerifiedDate AS DATE)                         AS verified_date,
            TRIM(b.VerifiedBy)                                   AS verified_by,
            TRIM(b.EvidenceLink)                                 AS evidence_link,
            TRIM(b.Notes)                                        AS notes,
            CAST(b.Modified AS TIMESTAMP)                        AS last_modified,
            TRIM(b.Editor.Title)                                 AS last_modified_by,
            CASE
                WHEN b.ProjectKey.Title IS NULL
                     THEN 'missing ProjectKey'
                WHEN b.ItemKey IS NULL
                     THEN 'missing ItemKey - the answer cannot be attached to a checklist item'
                WHEN v.project_id IS NULL AND UPPER(TRIM(b.ProjectKey.Title)) = 'ALL'
                     THEN 'ALL is only valid on CD Project Access'
                WHEN v.project_id IS NULL
                     THEN 'unknown project - is CD Projects stale?'
            END AS _reject_reason
        FROM cd_bronze_man_qc_doh_result b
        LEFT JOIN qcv_valid_projects v ON v.project_id = TRIM(b.ProjectKey.Title)
    )
);

CREATE OR REPLACE TABLE cd_silver_man_qc_doh_result AS
SELECT project_id, item_key, responsibility_code, status_code, verified_date, verified_by, evidence_link, notes,
       last_modified, last_modified_by
FROM qcv_doh_result
WHERE _reject_reason IS NULL AND _versions = 1 AND _copy = 1;

-- ---------------------------------------------------------------------------
-- Rejects: every row the rules above excluded, WITH THE REASON
-- ---------------------------------------------------------------------------
-- Its own table rather than an arm of cd_dq_rejects, matching cd_dq_rejects_manual: that
-- one is CREATE OR REPLACE'd by 10_procore_silver.sql, which runs first, so appending here
-- would either be overwritten or force 10 to know about 31.

CREATE OR REPLACE TABLE cd_dq_rejects_qc AS
SELECT 'cd_silver_man_qc_dfow' AS target_table, project_id, dfow_ref AS item_ref,
       COALESCE(_reject_reason, 'conflicting duplicate - (project, DfowRef) has more than one version; resolve in SharePoint') AS reason,
       last_modified, last_modified_by
FROM qcv_dfow
WHERE _reject_reason IS NOT NULL OR _versions > 1

UNION ALL
SELECT 'cd_silver_man_qc_itp' AS target_table, project_id, itp_ref AS item_ref,
       COALESCE(_reject_reason, 'conflicting duplicate - (project, ItpRef) has more than one version; resolve in SharePoint') AS reason,
       last_modified, last_modified_by
FROM qcv_itp
WHERE _reject_reason IS NOT NULL OR _versions > 1

UNION ALL
SELECT 'cd_silver_man_qc_gate' AS target_table, project_id, gate_key AS item_ref,
       COALESCE(_reject_reason, 'conflicting duplicate - (project, GateKey) has more than one version; resolve in SharePoint') AS reason,
       last_modified, last_modified_by
FROM qcv_gate
WHERE _reject_reason IS NOT NULL OR _versions > 1

UNION ALL
SELECT 'cd_silver_man_qc_special_inspection' AS target_table, project_id, inspection_ref AS item_ref,
       COALESCE(_reject_reason, 'conflicting duplicate - (project, InspectionRef) has more than one version; resolve in SharePoint') AS reason,
       last_modified, last_modified_by
FROM qcv_special_inspection
WHERE _reject_reason IS NOT NULL OR _versions > 1

UNION ALL
SELECT 'cd_silver_man_qc_commissioning' AS target_table, project_id, system_ref AS item_ref,
       COALESCE(_reject_reason, 'conflicting duplicate - (project, SystemRef) has more than one version; resolve in SharePoint') AS reason,
       last_modified, last_modified_by
FROM qcv_commissioning
WHERE _reject_reason IS NOT NULL OR _versions > 1

UNION ALL
SELECT 'cd_silver_man_qc_inspector_sign_in' AS target_table, project_id, sign_in_ref AS item_ref,
       COALESCE(_reject_reason, 'conflicting duplicate - (project, SignInRef) has more than one version; resolve in SharePoint') AS reason,
       last_modified, last_modified_by
FROM qcv_inspector_sign_in
WHERE _reject_reason IS NOT NULL OR _versions > 1

UNION ALL
SELECT 'cd_silver_man_qc_checklist_result' AS target_table, project_id, item_key AS item_ref,
       COALESCE(_reject_reason, 'conflicting duplicate - (project, ItemKey) has more than one version; resolve in SharePoint') AS reason,
       last_modified, last_modified_by
FROM qcv_checklist_result
WHERE _reject_reason IS NOT NULL OR _versions > 1

UNION ALL
SELECT 'cd_silver_man_qc_doh_result' AS target_table, project_id, item_key AS item_ref,
       COALESCE(_reject_reason, 'conflicting duplicate - (project, ItemKey) has more than one version; resolve in SharePoint') AS reason,
       last_modified, last_modified_by
FROM qcv_doh_result
WHERE _reject_reason IS NOT NULL OR _versions > 1;
