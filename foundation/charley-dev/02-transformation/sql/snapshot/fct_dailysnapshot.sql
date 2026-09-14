-- snapshot: fct_DailySnapshot - point-in-time balances and backlogs, appended per passing run.
--
-- WHY THIS EXISTS. Every other gold fact is CURRENT STATE. Grouping current state by
-- creation month is not a month-end figure: a submittal created in March and closed in
-- June stops counting as "open in March" the day it closes, so every past month's backlog
-- and balance is silently rewritten. Only a value SAVED at the time is reproducible.
--
-- WHO RUNS IT. cd_40_dq_checks, in the cell after dq.assert_no_blocking - so a failed gate
-- raises before this file is reached and no row from a failed run is ever written. It is
-- not a gold build file (no 1-4 prefix) because gold runs BEFORE the gate.
--
-- STAGE, VALIDATE, THEN SWAP. The notebook runs everything above the SWAP marker, checks
-- v_DailySnapshotStage with expectations.snapshot_suite, and only then runs the swap. A
-- failed validation leaves an earlier capture of the same date untouched.
--
-- {SNAPSHOT_DATE} is the UTC date of the DQ batch. The nightly run starts 02:00 New York
-- (06:00-07:00 UTC), so a capture dated D is the build that ran overnight into D: sources
-- as of the previous night, not the close of business on D.
--
-- ONE ROW-SET PER DATE. Re-running on the same {SNAPSHOT_DATE} replaces that date's rows.
-- There is no backfill: months before the first capture are absent, and the model shows
-- them as BLANK (unavailable), never zero.
--
-- SAME LOGIC AS THE MEASURES. Each column restates the deploy_model.py measure named
-- beside it, per ProjectKey. validate_model.monthly_expected recomputes those measures
-- independently, and the offline suite asserts these columns equal that recomputation.
-- COUNTs are SUM(CASE ... THEN 1 END) so "no rows" stays NULL, exactly as COUNTROWS of
-- nothing is BLANK in DAX. Money is ROUNDed to cents here, once, so the stored value and
-- the reconciliation's recomputation cannot differ by floating-point noise.

CREATE TABLE IF NOT EXISTS fct_DailySnapshot (
    SnapshotDate          DATE,
    ProjectKey            STRING,
    OpenSubmittals        BIGINT,
    SubmittalsPastDue     BIGINT,
    OpenRfis              BIGINT,
    OpenObservations      BIGINT,
    OpenPunchItems        BIGINT,
    ArOutstanding         DOUBLE,
    BilledToDate          DOUBLE,
    BudgetAmount          DOUBLE,
    SpentToDate           DOUBLE,
    CommittedAmount       DOUBLE,
    CurrentContract       DOUBLE,
    PendingChangeOrders   DOUBLE,
    ApprovedChangeOrders  DOUBLE,
    RunId                 STRING,
    CapturedAt            TIMESTAMP
) USING DELTA;

-- The live values. A TEMP view so the reconciliation rule in expectations.snapshot_suite
-- compares the written rows against exactly what was captured, in the same session.
-- Joins are IS NOT DISTINCT FROM: a NULL ProjectKey still counts in a portfolio total.
CREATE OR REPLACE TEMP VIEW v_DailySnapshotLive AS
WITH projects AS (
    SELECT ProjectKey FROM dim_Project
    UNION SELECT ProjectKey FROM fct_RfiSubmittal
    UNION SELECT ProjectKey FROM fct_QualityItem
    UNION SELECT ProjectKey FROM fct_Invoice
    UNION SELECT ProjectKey FROM fct_BudgetLine
    UNION SELECT ProjectKey FROM fct_FinancialPeriod
    UNION SELECT ProjectKey FROM fct_ChangeOrder
),
items AS (
    SELECT ProjectKey,
           -- [Open Submittals], [Open Submittals Past Due]
           CAST(SUM(CASE WHEN ItemType = 'Submittal' AND IsOpen THEN 1 END) AS BIGINT)    AS OpenSubmittals,
           CAST(SUM(CASE WHEN ItemType = 'Submittal' AND IsPastDue THEN 1 END) AS BIGINT) AS SubmittalsPastDue,
           CAST(SUM(CASE WHEN ItemType = 'RFI' AND IsOpen THEN 1 END) AS BIGINT)          AS OpenRfis
    FROM fct_RfiSubmittal GROUP BY ProjectKey
),
quality AS (
    SELECT ProjectKey,
           CAST(SUM(CASE WHEN ItemType = 'Observation' AND IsOpen THEN 1 END) AS BIGINT)  AS OpenObservations,
           CAST(SUM(CASE WHEN ItemType = 'PunchItem' AND IsOpen THEN 1 END) AS BIGINT)    AS OpenPunchItems
    FROM fct_QualityItem GROUP BY ProjectKey
),
ar AS (
    -- [AR Outstanding], [Total Billed]
    SELECT ProjectKey, ROUND(CAST(SUM(Balance) AS DOUBLE), 2) AS ArOutstanding,
           ROUND(CAST(SUM(Amount) AS DOUBLE), 2) AS BilledToDate
    FROM fct_Invoice GROUP BY ProjectKey
),
budget AS (
    -- [Budget], [Spent To Date], [Committed]
    SELECT ProjectKey, ROUND(CAST(SUM(BudgetAmount) AS DOUBLE), 2) AS BudgetAmount,
           ROUND(CAST(SUM(SpentToDate) AS DOUBLE), 2) AS SpentToDate,
           ROUND(CAST(SUM(CommittedAmount) AS DOUBLE), 2) AS CommittedAmount
    FROM fct_BudgetLine GROUP BY ProjectKey
),
-- [Current Contract], [Pending Change Orders]: LASTNONBLANKVALUE per project - the value
-- at the latest month where the column is populated, NOT a sum across months.
last_contract AS (
    SELECT ProjectKey, MAX(MonthStart) AS MonthStart FROM fct_FinancialPeriod
    WHERE CurrentContract IS NOT NULL AND MonthStart IS NOT NULL GROUP BY ProjectKey
),
last_pending AS (
    SELECT ProjectKey, MAX(MonthStart) AS MonthStart FROM fct_FinancialPeriod
    WHERE PendingChangeOrders IS NOT NULL AND MonthStart IS NOT NULL GROUP BY ProjectKey
),
contract AS (
    SELECT f.ProjectKey, ROUND(CAST(SUM(f.CurrentContract) AS DOUBLE), 2) AS CurrentContract
    FROM fct_FinancialPeriod f
    JOIN last_contract l ON f.ProjectKey IS NOT DISTINCT FROM l.ProjectKey AND f.MonthStart = l.MonthStart
    GROUP BY f.ProjectKey
),
pending AS (
    SELECT f.ProjectKey, ROUND(CAST(SUM(f.PendingChangeOrders) AS DOUBLE), 2) AS PendingChangeOrders
    FROM fct_FinancialPeriod f
    JOIN last_pending l ON f.ProjectKey IS NOT DISTINCT FROM l.ProjectKey AND f.MonthStart = l.MonthStart
    GROUP BY f.ProjectKey
),
approved AS (
    -- [Approved Change Orders]: StatusCategory = "Approved". Draft, Rejected, NoCharge, Void
    -- and Unknown are neither approved nor pending (21_fct_changeorder.sql). OpenRfis above
    -- and [Pending Change Orders] follow gold's IsOpen / IsPending, so drafts stay out.
    SELECT ProjectKey,
           ROUND(CAST(SUM(CASE WHEN StatusCategory = 'Approved'
                         THEN Amount END) AS DOUBLE), 2) AS ApprovedChangeOrders
    FROM fct_ChangeOrder GROUP BY ProjectKey
)
SELECT p.ProjectKey,
       i.OpenSubmittals, i.SubmittalsPastDue, i.OpenRfis,
       q.OpenObservations, q.OpenPunchItems,
       a.ArOutstanding, a.BilledToDate,
       b.BudgetAmount, b.SpentToDate, b.CommittedAmount,
       c.CurrentContract, pe.PendingChangeOrders, ap.ApprovedChangeOrders
FROM projects p
LEFT JOIN items    i  ON i.ProjectKey  IS NOT DISTINCT FROM p.ProjectKey
LEFT JOIN quality  q  ON q.ProjectKey  IS NOT DISTINCT FROM p.ProjectKey
LEFT JOIN ar       a  ON a.ProjectKey  IS NOT DISTINCT FROM p.ProjectKey
LEFT JOIN budget   b  ON b.ProjectKey  IS NOT DISTINCT FROM p.ProjectKey
LEFT JOIN contract c  ON c.ProjectKey  IS NOT DISTINCT FROM p.ProjectKey
LEFT JOIN pending  pe ON pe.ProjectKey IS NOT DISTINCT FROM p.ProjectKey
LEFT JOIN approved ap ON ap.ProjectKey IS NOT DISTINCT FROM p.ProjectKey;

-- The rows this run would write. Validated BEFORE anything is deleted.
CREATE OR REPLACE TEMP VIEW v_DailySnapshotStage AS
SELECT DATE '{SNAPSHOT_DATE}' AS SnapshotDate, ProjectKey,
       OpenSubmittals, SubmittalsPastDue, OpenRfis, OpenObservations, OpenPunchItems,
       ArOutstanding, BilledToDate, BudgetAmount, SpentToDate, CommittedAmount,
       CurrentContract, PendingChangeOrders, ApprovedChangeOrders,
       '{RUN_ID}' AS RunId, CAST(CURRENT_TIMESTAMP AS TIMESTAMP) AS CapturedAt
FROM v_DailySnapshotLive;

-- deploy_dq.snapshot_phases splits the file on the next line.
-- ==== SWAP ====

-- Idempotent re-run: replace this date, never duplicate it.
-- ponytail: DELETE + INSERT is two Delta commits, not one. A failure between them leaves
-- the date EMPTY (month-end falls back to the previous capture), never duplicated or
-- fabricated. Delta's INSERT ... REPLACE WHERE is atomic but DuckDB cannot run it offline.
DELETE FROM fct_DailySnapshot WHERE SnapshotDate = DATE '{SNAPSHOT_DATE}';

INSERT INTO fct_DailySnapshot
SELECT SnapshotDate, ProjectKey,
       OpenSubmittals, SubmittalsPastDue, OpenRfis, OpenObservations, OpenPunchItems,
       ArOutstanding, BilledToDate, BudgetAmount, SpentToDate, CommittedAmount,
       CurrentContract, PendingChangeOrders, ApprovedChangeOrders,
       RunId, CapturedAt
FROM v_DailySnapshotStage;
