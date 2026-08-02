-- gold: man_* - the ~40% of the Monthly Progress Report that exists nowhere but the
-- spreadsheet.
--
-- From analysis/excel-tracker/field-inventory.md:348 - wins, the entire risk register,
-- recovery-plan narratives, the client survey, cost-management flags, the profitability
-- judgement. No amount of Procore or Sage integration produces these.
--
-- Created here as EMPTY, TYPED tables rather than left absent. Three reasons:
--   1. The semantic model can bind to them today, so the report and the scorecard are
--      complete in shape even before a single row is entered.
--   2. An empty table with the right schema is a contract. Whatever the input mechanism
--      turns out to be - SharePoint list, Excel drop, Dataverse - it fills these columns.
--   3. Measures over an empty table return BLANK, which renders as an empty tile. A
--      MISSING table breaks the whole model. Blank is a visible gap; broken is not.
--
-- WE HAVE NOT INVENTED ANY DATA. Seeding these with plausible values would put numbers in
-- front of leadership that nobody entered, and they would be indistinguishable from real
-- ones. `cd_40_load_manual` fills them from Files/manual/*.csv when those exist.
--
-- Affect has not yet decided where the manual data lives (dashboard.md, open blocker).
-- The CSV drop is deliberately the lowest-friction thing that works today and can be
-- replaced without touching the model - see _docs/manual-input.md.

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
