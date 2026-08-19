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

CREATE OR REPLACE TABLE cd_silver_man_qc_dfow AS
SELECT * FROM (
    SELECT
        TRIM(ProjectKey.Title)                              AS project_id,
        UPPER(TRIM(DfowRef))                                AS dfow_ref,
        TRIM(DfowDescription)                               AS dfow_description,
        UPPER(TRIM(TradeKey))                               AS trade_key,
        CAST(RiskTier AS INT)                               AS risk_tier,
        TRIM(ControlMeasure)                                AS control_measure,
        TRIM(OwnerRole)                                     AS owner_role,
        UPPER(TRIM(StatusCode))                             AS status_code,
        TRIM(Notes)                                         AS notes,
        CAST(Modified AS TIMESTAMP)                         AS last_modified,
        TRIM(Editor.Title)                                  AS last_modified_by,
        ROW_NUMBER() OVER (PARTITION BY TRIM(ProjectKey.Title), UPPER(TRIM(DfowRef))
                           ORDER BY CAST(Modified AS TIMESTAMP) DESC) AS _rn
    FROM cd_bronze_man_qc_dfow
    WHERE ProjectKey.Title IS NOT NULL AND DfowRef IS NOT NULL
)
WHERE _rn = 1
  AND project_id IN (SELECT project_id FROM qcv_valid_projects);

-- ---------------------------------------------------------------------------
-- Inspection & Test Plan
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE cd_silver_man_qc_itp AS
SELECT * FROM (
    SELECT
        TRIM(ProjectKey.Title)                              AS project_id,
        UPPER(TRIM(ItpRef))                                 AS itp_ref,
        UPPER(TRIM(TradeKey))                               AS trade_key,
        TRIM(Activity)                                      AS activity,
        TRIM(InspectionType)                                AS inspection_type,
        TRIM(AcceptanceCriteria)                            AS acceptance_criteria,
        TRIM(HoldPointType)                                 AS hold_point_type,
        TRIM(Responsible)                                   AS responsible,
        CAST(PlannedDate AS DATE)                           AS planned_date,
        CAST(ActualDate AS DATE)                            AS actual_date,
        UPPER(TRIM(ResultCode))                             AS result_code,
        UPPER(TRIM(StatusCode))                             AS status_code,
        TRIM(Notes)                                         AS notes,
        CAST(Modified AS TIMESTAMP)                         AS last_modified,
        TRIM(Editor.Title)                                  AS last_modified_by,
        ROW_NUMBER() OVER (PARTITION BY TRIM(ProjectKey.Title), UPPER(TRIM(ItpRef))
                           ORDER BY CAST(Modified AS TIMESTAMP) DESC) AS _rn
    FROM cd_bronze_man_qc_itp
    WHERE ProjectKey.Title IS NOT NULL AND ItpRef IS NOT NULL
)
WHERE _rn = 1
  AND project_id IN (SELECT project_id FROM qcv_valid_projects);

-- ---------------------------------------------------------------------------
-- Gates - TCO, fire alarm and statutory in ONE table
-- ---------------------------------------------------------------------------
-- GateKey is globally unique across the three paths (TCO-A1, FA-01, STAT-01), so the
-- natural key is (project, gate) and GateType is an attribute rather than part of the key.
-- Uppercased because a gate typed as 'tco-a1' must not become a second gate.

CREATE OR REPLACE TABLE cd_silver_man_qc_gate AS
SELECT * FROM (
    SELECT
        TRIM(ProjectKey.Title)                              AS project_id,
        UPPER(TRIM(GateKey))                                AS gate_key,
        UPPER(TRIM(GateType))                               AS gate_type,
        UPPER(TRIM(StatusCode))                             AS status_code,
        TRIM(Responsible)                                   AS responsible,
        CAST(TargetDate AS DATE)                            AS target_date,
        CAST(SubmittedDate AS DATE)                         AS submitted_date,
        CAST(CompletedDate AS DATE)                         AS completed_date,
        TRIM(EvidenceLink)                                  AS evidence_link,
        TRIM(BlockerNote)                                   AS blocker_note,
        CAST(Modified AS TIMESTAMP)                         AS last_modified,
        TRIM(Editor.Title)                                  AS last_modified_by,
        ROW_NUMBER() OVER (PARTITION BY TRIM(ProjectKey.Title), UPPER(TRIM(GateKey))
                           ORDER BY CAST(Modified AS TIMESTAMP) DESC) AS _rn
    FROM cd_bronze_man_qc_gate
    WHERE ProjectKey.Title IS NOT NULL AND GateKey IS NOT NULL
)
WHERE _rn = 1
  AND project_id IN (SELECT project_id FROM qcv_valid_projects)
  AND gate_type IN ('TCO', 'FIRE_ALARM', 'STATUTORY');

-- ---------------------------------------------------------------------------
-- Special inspections
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE cd_silver_man_qc_special_inspection AS
SELECT * FROM (
    SELECT
        TRIM(ProjectKey.Title)                              AS project_id,
        UPPER(TRIM(InspectionRef))                          AS inspection_ref,
        TRIM(Category)                                      AS category,
        TRIM(Agency)                                        AS agency,
        TRIM(InspectorName)                                 AS inspector_name,
        UPPER(TRIM(RequiredCode))                           AS required_code,
        UPPER(TRIM(PerformedCode))                          AS performed_code,
        CAST(ScheduledDate AS DATE)                         AS scheduled_date,
        CAST(PerformedDate AS DATE)                         AS performed_date,
        CAST(ReportReceivedDate AS DATE)                    AS report_received_date,
        UPPER(TRIM(StatusCode))                             AS status_code,
        TRIM(Notes)                                         AS notes,
        CAST(Modified AS TIMESTAMP)                         AS last_modified,
        TRIM(Editor.Title)                                  AS last_modified_by,
        ROW_NUMBER() OVER (PARTITION BY TRIM(ProjectKey.Title), UPPER(TRIM(InspectionRef))
                           ORDER BY CAST(Modified AS TIMESTAMP) DESC) AS _rn
    FROM cd_bronze_man_qc_special_inspection
    WHERE ProjectKey.Title IS NOT NULL AND InspectionRef IS NOT NULL
)
WHERE _rn = 1
  AND project_id IN (SELECT project_id FROM qcv_valid_projects);

-- ---------------------------------------------------------------------------
-- Commissioning
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE cd_silver_man_qc_commissioning AS
SELECT * FROM (
    SELECT
        TRIM(ProjectKey.Title)                              AS project_id,
        UPPER(TRIM(SystemRef))                              AS system_ref,
        TRIM(SystemName)                                    AS system_name,
        UPPER(TRIM(TradeKey))                               AS trade_key,
        TRIM(Responsible)                                   AS responsible,
        CAST(PlannedDate AS DATE)                           AS planned_date,
        CAST(ActualDate AS DATE)                            AS actual_date,
        UPPER(TRIM(StatusCode))                             AS status_code,
        TRIM(Notes)                                         AS notes,
        CAST(Modified AS TIMESTAMP)                         AS last_modified,
        TRIM(Editor.Title)                                  AS last_modified_by,
        ROW_NUMBER() OVER (PARTITION BY TRIM(ProjectKey.Title), UPPER(TRIM(SystemRef))
                           ORDER BY CAST(Modified AS TIMESTAMP) DESC) AS _rn
    FROM cd_bronze_man_qc_commissioning
    WHERE ProjectKey.Title IS NOT NULL AND SystemRef IS NOT NULL
)
WHERE _rn = 1
  AND project_id IN (SELECT project_id FROM qcv_valid_projects);

-- ---------------------------------------------------------------------------
-- Inspector sign-in log
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE cd_silver_man_qc_inspector_sign_in AS
SELECT * FROM (
    SELECT
        TRIM(ProjectKey.Title)                              AS project_id,
        UPPER(TRIM(SignInRef))                              AS sign_in_ref,
        CAST(VisitDate AS DATE)                             AS visit_date,
        TRIM(InspectorName)                                 AS inspector_name,
        UPPER(TRIM(AgencyCode))                             AS agency_code,
        TRIM(Purpose)                                       AS purpose,
        TRIM(AreaInspected)                                 AS area_inspected,
        UPPER(TRIM(OutcomeCode))                            AS outcome_code,
        CAST(FollowUpRequired AS BOOLEAN)                   AS follow_up_required,
        TRIM(Notes)                                         AS notes,
        CAST(Modified AS TIMESTAMP)                         AS last_modified,
        TRIM(Editor.Title)                                  AS last_modified_by,
        ROW_NUMBER() OVER (PARTITION BY TRIM(ProjectKey.Title), UPPER(TRIM(SignInRef))
                           ORDER BY CAST(Modified AS TIMESTAMP) DESC) AS _rn
    FROM cd_bronze_man_qc_inspector_sign_in
    WHERE ProjectKey.Title IS NOT NULL AND SignInRef IS NOT NULL
)
WHERE _rn = 1
  AND project_id IN (SELECT project_id FROM qcv_valid_projects);

-- ---------------------------------------------------------------------------
-- Trade checklist results - all 26 trades, one table
-- ---------------------------------------------------------------------------
-- ItemKey is 'EXCAVATION-001' shaped, so it already carries its trade and is unique across
-- all 625 items. TradeKey is carried anyway: it is what the report slices by, and deriving
-- it from a string prefix at query time is how a trade with a hyphen in its key stops
-- working.

CREATE OR REPLACE TABLE cd_silver_man_qc_checklist_result AS
SELECT * FROM (
    SELECT
        TRIM(ProjectKey.Title)                              AS project_id,
        UPPER(TRIM(TradeKey))                               AS trade_key,
        UPPER(TRIM(ItemKey))                                AS item_key,
        UPPER(TRIM(StageCode))                              AS stage_code,
        UPPER(TRIM(ResultCode))                             AS result_code,
        CAST(InspectedDate AS DATE)                         AS inspected_date,
        TRIM(InspectedBy)                                   AS inspected_by,
        TRIM(Notes)                                         AS notes,
        CAST(Modified AS TIMESTAMP)                         AS last_modified,
        TRIM(Editor.Title)                                  AS last_modified_by,
        ROW_NUMBER() OVER (PARTITION BY TRIM(ProjectKey.Title), UPPER(TRIM(ItemKey))
                           ORDER BY CAST(Modified AS TIMESTAMP) DESC) AS _rn
    FROM cd_bronze_man_qc_checklist_result
    WHERE ProjectKey.Title IS NOT NULL AND ItemKey IS NOT NULL
)
WHERE _rn = 1
  AND project_id IN (SELECT project_id FROM qcv_valid_projects);

-- ---------------------------------------------------------------------------
-- DOH checklist results
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE cd_silver_man_qc_doh_result AS
SELECT * FROM (
    SELECT
        TRIM(ProjectKey.Title)                              AS project_id,
        UPPER(TRIM(ItemKey))                                AS item_key,
        UPPER(TRIM(ResponsibilityCode))                     AS responsibility_code,
        UPPER(TRIM(StatusCode))                             AS status_code,
        CAST(VerifiedDate AS DATE)                          AS verified_date,
        TRIM(VerifiedBy)                                    AS verified_by,
        TRIM(EvidenceLink)                                  AS evidence_link,
        TRIM(Notes)                                         AS notes,
        CAST(Modified AS TIMESTAMP)                         AS last_modified,
        TRIM(Editor.Title)                                  AS last_modified_by,
        ROW_NUMBER() OVER (PARTITION BY TRIM(ProjectKey.Title), UPPER(TRIM(ItemKey))
                           ORDER BY CAST(Modified AS TIMESTAMP) DESC) AS _rn
    FROM cd_bronze_man_qc_doh_result
    WHERE ProjectKey.Title IS NOT NULL AND ItemKey IS NOT NULL
)
WHERE _rn = 1
  AND project_id IN (SELECT project_id FROM qcv_valid_projects);

-- ---------------------------------------------------------------------------
-- Rejects: every row the rules above excluded, WITH THE REASON
-- ---------------------------------------------------------------------------
-- Its own table rather than an arm of cd_dq_rejects, matching cd_dq_rejects_manual: that
-- one is CREATE OR REPLACE'd by 10_procore_silver.sql, which runs first, so appending here
-- would either be overwritten or force 10 to know about 31.

CREATE OR REPLACE TABLE cd_dq_rejects_qc AS
SELECT 'cd_silver_man_qc_checklist_result' AS target_table,
       TRIM(ProjectKey.Title)              AS project_id,
       TRIM(ItemKey)                       AS item_ref,
       'unknown project - is CD Projects stale?' AS reason,
       CAST(Modified AS TIMESTAMP)         AS last_modified,
       TRIM(Editor.Title)                  AS last_modified_by
FROM cd_bronze_man_qc_checklist_result
WHERE ProjectKey.Title IS NOT NULL
  AND TRIM(ProjectKey.Title) NOT IN (SELECT project_id FROM qcv_valid_projects)

UNION ALL
SELECT 'cd_silver_man_qc_gate', TRIM(ProjectKey.Title), TRIM(GateKey),
       'unknown project - is CD Projects stale?',
       CAST(Modified AS TIMESTAMP), TRIM(Editor.Title)
FROM cd_bronze_man_qc_gate
WHERE ProjectKey.Title IS NOT NULL
  AND TRIM(ProjectKey.Title) NOT IN (SELECT project_id FROM qcv_valid_projects)

UNION ALL
-- The gate collapse's one new failure mode: three sheets became one table, so a row that
-- does not declare which path it is on cannot be routed at all. Loud, not dropped.
SELECT 'cd_silver_man_qc_gate', TRIM(ProjectKey.Title), TRIM(GateKey),
       CONCAT('invalid GateType: ', COALESCE(GateType, '(blank)')),
       CAST(Modified AS TIMESTAMP), TRIM(Editor.Title)
FROM cd_bronze_man_qc_gate
WHERE UPPER(TRIM(COALESCE(GateType, ''))) NOT IN ('TCO', 'FIRE_ALARM', 'STATUTORY')

UNION ALL
-- A checklist answer with no item key answers nothing - there is no way to know which of
-- the 625 items it belongs to, so it cannot be counted and must not be silently ignored.
SELECT 'cd_silver_man_qc_checklist_result', TRIM(ProjectKey.Title), NULL,
       'missing ItemKey - the answer cannot be attached to a checklist item',
       CAST(Modified AS TIMESTAMP), TRIM(Editor.Title)
FROM cd_bronze_man_qc_checklist_result
WHERE ItemKey IS NULL

UNION ALL
SELECT 'cd_silver_man_qc_doh_result', TRIM(ProjectKey.Title), TRIM(ItemKey),
       'unknown project - is CD Projects stale?',
       CAST(Modified AS TIMESTAMP), TRIM(Editor.Title)
FROM cd_bronze_man_qc_doh_result
WHERE ProjectKey.Title IS NOT NULL
  AND TRIM(ProjectKey.Title) NOT IN (SELECT project_id FROM qcv_valid_projects);
