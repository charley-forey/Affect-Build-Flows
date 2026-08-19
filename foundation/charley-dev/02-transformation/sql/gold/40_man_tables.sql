-- gold: man_* - the ~40% of the Monthly Progress Report that exists nowhere but the
-- spreadsheet.
--
-- From analysis/excel-tracker/field-inventory.md:348 - wins, the entire risk register,
-- recovery-plan narratives, the client survey, cost-management flags, the profitability
-- judgement. No amount of Procore or Sage integration produces these.
--
-- Declared as TYPED DDL and then FILLED FROM SILVER. Both halves matter:
--   1. The CREATE is the contract. It runs whether or not anybody has typed a row, so the
--      semantic model binds today and a measure over an empty table returns BLANK - a
--      visible gap. A MISSING table breaks the whole model; blank does not.
--   2. The INSERT is what makes the contract reachable. It used to be absent, and that was
--      not a stylistic gap: with nothing reading cd_silver_man_*, all nine tables were
--      permanently empty and the entire manual pipeline - CSV template, loader, silver
--      parser, reject log - terminated one join short of the report.
--
-- WE HAVE NOT INVENTED ANY DATA. Every row here came from a person typing it into a
-- SharePoint list or a CSV template; nothing is seeded with plausible values. With no
-- input the INSERTs move zero rows and the tables stay empty, exactly as before.
--
-- THE CHAIN, end to end:
--     Files/_manual/<list>.csv  ->  cd_06_land_manual  (_local/deploy_manual.py)
--       or the CD_Manual_Ingest dataflow over the SharePoint lists - two writers, one
--       contract, both producing the SAME cd_bronze_man_* shape
--     cd_bronze_man_*   ->  sql/silver/30_manual_silver.sql   (typed, deduped, rejects)
--     cd_silver_man_*   ->  sql/silver/01_source_views_cd.sql (sv_man_*)
--     sv_man_*          ->  THIS FILE
--
-- COLUMN NAMES ARE DECIDED HERE AND NOWHERE ELSE. This DDL is the single source of truth
-- for the SharePoint columns (_local/make_sharepoint.py generates the provisioning script,
-- the dataflow and the CSV templates from it) AND for the semantic model. The silver
-- parser reads these names out of bronze and lower-cases them; that is the only
-- transformation in the chain. Four tables used to disagree with silver on their columns -
-- man_Flags, man_Milestones, man_Survey, man_DailyLogCompliance - which is what made the
-- link look like a design question rather than a missing statement. It was never a design
-- question: the model and this DDL already agreed, and the input side had drifted.

-- ---------------------------------------------------------------------------
-- Narrative tables. WINS caps at 4+4 and RISKS at 8 in the workbook because the
-- DASHBOARD hard-references specific cells; a 5th win simply would not appear. There is
-- no cap here.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE man_Wins (
    ProjectKey    STRING,
    MonthStart    DATE,
    WinNumber     INT,
    Description   STRING,
    WinType       STRING          -- 'Realized' | 'FocusArea' (WINS rows 3-6 vs 9-12)
);

CREATE OR REPLACE TABLE man_Risks (
    ProjectKey    STRING,
    MonthStart    DATE,
    RiskNumber    INT,
    Description   STRING,
    ImpactCode    STRING,         -- -> dim_Status Domain='RiskImpact'  (HIGH/MEDIUM/LOW)
    Mitigation    STRING,
    OwnerRole     STRING,         -- -> dim_Owner[RoleName]
    StatusCode    STRING          -- -> dim_Status Domain='RiskStatus'
);

CREATE OR REPLACE TABLE man_PriorityItems (
    ProjectKey    STRING,
    MonthStart    DATE,
    ItemNumber    INT,
    ScheduleItem  STRING,
    StatusCode    STRING,         -- -> dim_Status Domain='ScheduleStatus'
    CriticalDelays STRING,
    RecoveryPlan  STRING,
    ForecastImpact STRING,
    Notes         STRING
);

-- ---------------------------------------------------------------------------
-- Judgements and attestations. FINANCIALS!C7 (profitability) and E65:E67.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE TABLE man_Flags (
    ProjectKey    STRING,
    MonthStart    DATE,
    ProfitabilityCode STRING,     -- matched to dim_ScorecardBand[MatchValue], category 2
    ContingencyRemaining DOUBLE,  -- FINANCIALS!C9, currently "N/A" in the workbook
    BaselineApproved BOOLEAN,     -- SCHEDULE!G16
    BaselineRevision STRING,      -- SCHEDULE!G17
    MonthEndClosedOut BOOLEAN,    -- FINANCIALS!E65
    ForecastingInLine BOOLEAN,    -- FINANCIALS!E66
    ResourcesUpdated  BOOLEAN     -- FINANCIALS!E67
);

-- SCORECARD CALC!C34:C41. The six QUESTIONS are not stored anywhere in the workbook -
-- only the scores (field-inventory.md:339). QuestionText exists so they are captured the
-- first time somebody writes them down. Open question #10.
CREATE OR REPLACE TABLE man_Survey (
    ProjectKey    STRING,
    MonthStart    DATE,
    QuestionNumber INT,
    QuestionText  STRING,
    Score         INT,            -- 1-5
    SurveyedParty STRING          -- C34, currently 'ANONYMOUS'
);

-- ---------------------------------------------------------------------------
-- Metrics that are manual ONLY because the source is not ingested yet. Each of these
-- has a real system of record identified; they move out of man_* as those land.
-- ---------------------------------------------------------------------------

-- SAFETY!Table1. HoursWorked: Sage payroll / ADP / Procore timecards - undecided (open
-- question #3). RecordableIncidents: Procore /incidents, in the registry, not yet run.
-- Orientations: genuinely manual, no system of record.
CREATE OR REPLACE TABLE man_SafetyMonthly (
    ProjectKey    STRING,
    MonthStart    DATE,
    HoursWorked   DOUBLE,
    RecordableIncidents INT,
    Orientations  INT,
    OtHours       DOUBLE          -- FINANCIALS!Table110
);

-- QUALITY!Table18. Both sides are Procore endpoints already in the registry
-- (/observations/items, /punch_items) - manual only until the ingestion runs.
-- Fixes defect #2 on arrival: QUALITY!D5:D6 currently read SAFETY orientations.
CREATE OR REPLACE TABLE man_QualityMonthly (
    ProjectKey    STRING,
    MonthStart    DATE,
    Observations  INT,
    PunchlistItems INT,
    AvgDaysPastDue DOUBLE,        -- QUALITY!D38:E38, typed by hand today
    AvgDaysToClose DOUBLE         -- QUALITY!D39:E39, typed by hand today
);

-- SCHEDULE!Table5 columns D:G. Contract dates come off the signed contract and exist in
-- neither Procore nor Outbuild. Baseline dates exist in Outbuild only if baselines are
-- maintained there, which is unconfirmed - so both stay manual and join to fct_Milestone
-- on ActivityKey. Without these, completion variance cannot be computed at all.
CREATE OR REPLACE TABLE man_Milestones (
    ProjectKey    STRING,
    ActivityKey   STRING,
    MilestoneName STRING,
    ContractStart DATE,
    ContractFinish DATE,
    BaselineStart DATE,
    BaselineFinish DATE,
    IsSubstantialCompletion BOOLEAN
);

-- SCORECARD CALC!E28 "Daily Reports". Derivable from Procore
-- /daily_log_headers once ingested; typed by hand today.
CREATE OR REPLACE TABLE man_DailyLogCompliance (
    ProjectKey    STRING,
    MonthStart    DATE,
    LogsExpected  INT,
    LogsMissedSameDay INT
);

-- ---------------------------------------------------------------------------
-- POPULATE. The silver -> gold link, and the only place the case flips.
-- ---------------------------------------------------------------------------
--
-- INSERT rather than CREATE TABLE AS, deliberately: the CREATE above is the schema
-- contract the semantic model binds to, and CTAS would let a silver column silently
-- redefine it. An INSERT with a column list fails loudly instead, which is the behaviour
-- worth having when the two sides are maintained by different generators.
--
-- No filtering here. Every rule - valid project, one row per natural key, MonthStart
-- floored to the 1st, rejects logged with a reason - is applied in
-- sql/silver/30_manual_silver.sql. Gold renames and nothing else, so there is exactly one
-- place to look when a row is missing.

INSERT INTO man_Wins (ProjectKey, MonthStart, WinNumber, Description, WinType)
SELECT project_id, month_start, win_number, description, win_type FROM sv_man_wins;

INSERT INTO man_Risks (ProjectKey, MonthStart, RiskNumber, Description, ImpactCode,
                       Mitigation, OwnerRole, StatusCode)
SELECT project_id, month_start, risk_number, description, impact_code,
       mitigation, owner_role, status_code FROM sv_man_risks;

INSERT INTO man_PriorityItems (ProjectKey, MonthStart, ItemNumber, ScheduleItem, StatusCode,
                               CriticalDelays, RecoveryPlan, ForecastImpact, Notes)
SELECT project_id, month_start, item_number, schedule_item, status_code,
       critical_delays, recovery_plan, forecast_impact, notes FROM sv_man_priority_items;

INSERT INTO man_Flags (ProjectKey, MonthStart, ProfitabilityCode, ContingencyRemaining,
                       BaselineApproved, BaselineRevision, MonthEndClosedOut,
                       ForecastingInLine, ResourcesUpdated)
SELECT project_id, month_start, profitability_code, contingency_remaining,
       baseline_approved, baseline_revision, month_end_closed_out,
       forecasting_in_line, resources_updated FROM sv_man_flags;

INSERT INTO man_Survey (ProjectKey, MonthStart, QuestionNumber, QuestionText, Score,
                        SurveyedParty)
SELECT project_id, month_start, question_number, question_text, score, surveyed_party
FROM sv_man_survey;

INSERT INTO man_SafetyMonthly (ProjectKey, MonthStart, HoursWorked, RecordableIncidents,
                               Orientations, OtHours)
SELECT project_id, month_start, hours_worked, recordable_incidents, orientations, ot_hours
FROM sv_man_safety_monthly;

INSERT INTO man_QualityMonthly (ProjectKey, MonthStart, Observations, PunchlistItems,
                                AvgDaysPastDue, AvgDaysToClose)
SELECT project_id, month_start, observations, punchlist_items, avg_days_past_due,
       avg_days_to_close FROM sv_man_quality_monthly;

INSERT INTO man_Milestones (ProjectKey, ActivityKey, MilestoneName, ContractStart,
                            ContractFinish, BaselineStart, BaselineFinish,
                            IsSubstantialCompletion)
SELECT project_id, activity_key, milestone_name, contract_start, contract_finish,
       baseline_start, baseline_finish, is_substantial_completion FROM sv_man_milestones;

INSERT INTO man_DailyLogCompliance (ProjectKey, MonthStart, LogsExpected, LogsMissedSameDay)
SELECT project_id, month_start, logs_expected, logs_missed_same_day
FROM sv_man_daily_log_compliance;
