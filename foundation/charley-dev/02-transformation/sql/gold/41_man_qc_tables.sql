-- gold: man_Qc* - the PQP (Project Quality Plan) tables that are HAND-ENTERED per project.
--
-- Same contract as 40_man_tables.sql, same chain, same generators: this DDL is the single
-- source of truth for the SharePoint columns AND for the semantic model, the silver parser
-- lower-cases these names, and the INSERT at the bottom is the silver -> gold link.
--
-- WHAT IS HERE AND WHAT IS DELIBERATELY NOT.
--
-- The client's 44-sheet QA/QC workbook covers three kinds of thing:
--
--   1. TEMPLATES - the 26 trade checklists, the three gate paths, the DOH checklist. Those
--      are the same on every project, so they are SEEDS (08_qc_seeds.sql), not manual
--      input. Nobody retypes 625 checklist items per project; they record an ANSWER
--      against each one, which is what man_QcChecklistResult holds.
--
--   2. THINGS PROCORE ALREADY OWNS - NCRs, punch items, submittals. Procore is the
--      client's MANDATORY system of record for quality; their own workbook says so. So
--      those are facts from the API (33_fct_qc.sql), not lists to type into. There is no
--      man_QcNcr and there must not be: a second place to record an NCR is a second answer
--      to "how many are open".
--
--   3. WHAT NO SYSTEM HOLDS - the DFOW risk register, the ITP, gate progress, special
--      inspections, commissioning, the inspector sign-in log. Those are these eight tables.
--
-- EVERY TABLE CARRIES ProjectKey. The templates do not; the results do. That is the whole
-- shape of the collapse - one template, N projects - and it is why adding a project is a
-- row rather than a copy of a workbook.
--
-- Status columns hold CODES from dim_QcStatus, not labels. The SharePoint choice lists are
-- generated from the same vocabulary (_local/make_sharepoint.py reads seed/qc_status_vocab
-- .csv), so what someone can pick and what the model can resolve cannot diverge.

-- ---------------------------------------------------------------------------
-- Definable Features of Work - the risk register that drives inspection frequency
-- ---------------------------------------------------------------------------
-- DFOW Risk Register!B5:P36. RiskTier is the workbook's 1-3, carried as entered rather
-- than recomputed: it is a judgement, and qc_seed_Trade holds the DEFAULT tier for a trade
-- so a project overriding it is visible as a difference.

CREATE OR REPLACE TABLE man_QcDfow (
    ProjectKey      STRING,
    DfowRef         STRING,        -- 'D-07' etc, joins qc_seed_Trade[DfowRef]
    DfowDescription STRING,
    TradeKey        STRING,        -- -> qc_seed_Trade[TradeKey]
    RiskTier        INT,           -- 1 low .. 4 (life-safety / water ingress)
    ControlMeasure  STRING,
    OwnerRole       STRING,
    StatusCode      STRING,        -- -> dim_QcStatus Domain='DFOWRISKREGISTER_4'
    Notes           STRING
);

-- ---------------------------------------------------------------------------
-- Inspection & Test Plan
-- ---------------------------------------------------------------------------
-- ITP!B5:N35. ResultCode and StatusCode are two different questions the workbook keeps in
-- two columns: did the test pass, and where is the activity up to. Collapsing them loses
-- "passed, but the re-test is still scheduled".

CREATE OR REPLACE TABLE man_QcItp (
    ProjectKey         STRING,
    ItpRef             STRING,
    TradeKey           STRING,     -- -> qc_seed_Trade[TradeKey]
    Activity           STRING,
    InspectionType     STRING,
    AcceptanceCriteria STRING,
    HoldPointType      STRING,     -- Hold / Witness / Review / Surveillance
    Responsible        STRING,
    PlannedDate        DATE,
    ActualDate         DATE,
    ResultCode         STRING,     -- -> dim_QcStatus Domain='ITP_4'
    StatusCode         STRING,     -- -> dim_QcStatus Domain='ITP_6'
    Notes              STRING
);

-- ---------------------------------------------------------------------------
-- Gate progress - ONE table for all three paths
-- ---------------------------------------------------------------------------
-- Path to TCO (46 steps), Path to Fire Alarm (23) and Statutory Inspections (24) are the
-- same shape, so the template collapsed into qc_seed_Gate discriminated by GateType and
-- the RESULT collapses the same way. GateType is carried on the row as well as being
-- derivable from the seed: the report slices by it constantly, and a slicer that needs a
-- join to exist is a slicer that breaks when the join does.
--
-- TargetDate / SubmittedDate / CompletedDate are a progression, not three independent
-- dates. The DQ suite checks TargetDate <= CompletedDate rather than assuming it.

CREATE OR REPLACE TABLE man_QcGate (
    ProjectKey     STRING,
    GateKey        STRING,         -- -> qc_seed_Gate[GateKey]
    GateType       STRING,         -- TCO | FIRE_ALARM | STATUTORY
    StatusCode     STRING,         -- -> dim_QcStatus, the three path domains unioned
    Responsible    STRING,
    TargetDate     DATE,
    SubmittedDate  DATE,
    CompletedDate  DATE,
    EvidenceLink   STRING,
    BlockerNote    STRING
);

-- ---------------------------------------------------------------------------
-- Special inspections (NYC DOB TR1 regime)
-- ---------------------------------------------------------------------------
-- Special Inspections!B7:P45. RequiredCode and PerformedCode are separate because
-- "not required" and "required but not done" are the two states a single boolean merges,
-- and only one of them is a problem.

CREATE OR REPLACE TABLE man_QcSpecialInspection (
    ProjectKey          STRING,
    InspectionRef       STRING,
    Category            STRING,     -- the TR1 special inspection category
    Agency              STRING,
    InspectorName       STRING,
    RequiredCode        STRING,     -- -> dim_QcStatus Domain='SPECIALINSPECTIONS_3'
    PerformedCode       STRING,     -- -> dim_QcStatus Domain='SPECIALINSPECTIONS_2'
    ScheduledDate       DATE,
    PerformedDate       DATE,
    ReportReceivedDate  DATE,
    StatusCode          STRING,     -- -> dim_QcStatus Domain='SPECIALINSPECTIONS_5'
    Notes               STRING
);

-- ---------------------------------------------------------------------------
-- Commissioning
-- ---------------------------------------------------------------------------
-- Commissioning!B7:P50.

CREATE OR REPLACE TABLE man_QcCommissioning (
    ProjectKey   STRING,
    SystemRef    STRING,
    SystemName   STRING,
    TradeKey     STRING,            -- -> qc_seed_Trade[TradeKey]
    Responsible  STRING,
    PlannedDate  DATE,
    ActualDate   DATE,
    StatusCode   STRING,            -- -> dim_QcStatus Domain='COMMISSIONING_6'
    Notes        STRING
);

-- ---------------------------------------------------------------------------
-- Inspector sign-in log
-- ---------------------------------------------------------------------------
-- Inspector Sign-In!B5:L120. The one PQP sheet that is a pure event log: who from which
-- authority walked the site, when, and what came of it. There is no template to join to,
-- which is why it carries no seed key.

CREATE OR REPLACE TABLE man_QcInspectorSignIn (
    ProjectKey       STRING,
    SignInRef        STRING,
    VisitDate        DATE,
    InspectorName    STRING,
    AgencyCode       STRING,        -- -> dim_QcStatus Domain='INSPECTORSIGNIN_11'
    Purpose          STRING,
    AreaInspected    STRING,
    OutcomeCode      STRING,        -- -> dim_QcStatus Domain='INSPECTORSIGNIN_5'
    FollowUpRequired BOOLEAN,
    Notes            STRING
);

-- ---------------------------------------------------------------------------
-- Trade checklist results - ONE table for all 26 trades
-- ---------------------------------------------------------------------------
-- The 26 trade sheets share one schema, so the template is one seed table and the answers
-- are one result table. (ProjectKey, ItemKey) is the grain: 625 items x N projects.
--
-- StageCode is the workbook's four-stage inspection cycle (Preparatory / Work Readiness /
-- First Work Review / Follow-up), which sits on the SHEET in the workbook - one value for
-- all of a trade's items. Carried per row here because a project part-way through a trade
-- genuinely has items at different stages, and the sheet-level cell could not say so.

CREATE OR REPLACE TABLE man_QcChecklistResult (
    ProjectKey    STRING,
    TradeKey      STRING,          -- -> qc_seed_Trade[TradeKey]
    ItemKey       STRING,          -- -> qc_seed_ChecklistItem[ItemKey]
    StageCode     STRING,          -- -> dim_QcStatus Domain='EXCAVATION_4'
    ResultCode    STRING,          -- -> dim_QcStatus Domain='EXCAVATION_3'  (PASS/FAIL/N_A)
    InspectedDate DATE,
    InspectedBy   STRING,
    Notes         STRING
);

-- ---------------------------------------------------------------------------
-- DOH checklist results
-- ---------------------------------------------------------------------------
-- DOH Checklist!B8:F120. ResponsibilityCode is on the RESULT rather than the seed because
-- who owns a requirement is a per-project commercial split (Affect Build vs the owner's
-- separate trades vs a shared vendor), and getting it wrong is how a pool sits unfinished
-- with both sides believing the other had it.

CREATE OR REPLACE TABLE man_QcDohResult (
    ProjectKey         STRING,
    ItemKey            STRING,     -- -> qc_seed_DohItem[ItemKey]
    ResponsibilityCode STRING,     -- -> dim_QcStatus Domain='DOHCHECKLIST_4'
    StatusCode         STRING,     -- -> dim_QcStatus Domain='DOHCHECKLIST_6'
    VerifiedDate       DATE,
    VerifiedBy         STRING,
    EvidenceLink       STRING,
    Notes              STRING
);

-- ---------------------------------------------------------------------------
-- POPULATE from silver. Same rule as 40_man_tables.sql: gold renames, nothing else.
-- ---------------------------------------------------------------------------

INSERT INTO man_QcDfow (ProjectKey, DfowRef, DfowDescription, TradeKey, RiskTier,
                        ControlMeasure, OwnerRole, StatusCode, Notes)
SELECT project_id, dfow_ref, dfow_description, trade_key, risk_tier,
       control_measure, owner_role, status_code, notes FROM sv_man_qc_dfow;

INSERT INTO man_QcItp (ProjectKey, ItpRef, TradeKey, Activity, InspectionType,
                       AcceptanceCriteria, HoldPointType, Responsible, PlannedDate,
                       ActualDate, ResultCode, StatusCode, Notes)
SELECT project_id, itp_ref, trade_key, activity, inspection_type, acceptance_criteria,
       hold_point_type, responsible, planned_date, actual_date, result_code, status_code,
       notes FROM sv_man_qc_itp;

INSERT INTO man_QcGate (ProjectKey, GateKey, GateType, StatusCode, Responsible, TargetDate,
                        SubmittedDate, CompletedDate, EvidenceLink, BlockerNote)
SELECT project_id, gate_key, gate_type, status_code, responsible, target_date,
       submitted_date, completed_date, evidence_link, blocker_note FROM sv_man_qc_gate;

INSERT INTO man_QcSpecialInspection (ProjectKey, InspectionRef, Category, Agency,
                                     InspectorName, RequiredCode, PerformedCode,
                                     ScheduledDate, PerformedDate, ReportReceivedDate,
                                     StatusCode, Notes)
SELECT project_id, inspection_ref, category, agency, inspector_name, required_code,
       performed_code, scheduled_date, performed_date, report_received_date, status_code,
       notes FROM sv_man_qc_special_inspection;

INSERT INTO man_QcCommissioning (ProjectKey, SystemRef, SystemName, TradeKey, Responsible,
                                 PlannedDate, ActualDate, StatusCode, Notes)
SELECT project_id, system_ref, system_name, trade_key, responsible, planned_date,
       actual_date, status_code, notes FROM sv_man_qc_commissioning;

INSERT INTO man_QcInspectorSignIn (ProjectKey, SignInRef, VisitDate, InspectorName,
                                   AgencyCode, Purpose, AreaInspected, OutcomeCode,
                                   FollowUpRequired, Notes)
SELECT project_id, sign_in_ref, visit_date, inspector_name, agency_code, purpose,
       area_inspected, outcome_code, follow_up_required, notes
FROM sv_man_qc_inspector_sign_in;

INSERT INTO man_QcChecklistResult (ProjectKey, TradeKey, ItemKey, StageCode, ResultCode,
                                   InspectedDate, InspectedBy, Notes)
SELECT project_id, trade_key, item_key, stage_code, result_code, inspected_date,
       inspected_by, notes FROM sv_man_qc_checklist_result;

INSERT INTO man_QcDohResult (ProjectKey, ItemKey, ResponsibilityCode, StatusCode,
                             VerifiedDate, VerifiedBy, EvidenceLink, Notes)
SELECT project_id, item_key, responsibility_code, status_code, verified_date, verified_by,
       evidence_link, notes FROM sv_man_qc_doh_result;
