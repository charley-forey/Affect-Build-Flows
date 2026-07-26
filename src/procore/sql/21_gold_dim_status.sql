-- gold: dim_Status - one conformed status dimension, keyed by a stable Code.
--
-- The 32 seeded rows are verbatim from analysis/excel-tracker/dropdowns-and-status.md:238-269
-- (hex values sampled from the workbook's actual font colours, so Power BI matches what
-- Affect already recognises).
--
-- NOTE: that seed has NO RFI or Submittal domain - the workbook's SUBMITTALS & RFI tab is
-- just trade x count, it never carries a status. But powerbi/semantic-model.md gives
-- fct_RfiSubmittal a StatusKey, so those two domains are built here from Procore's OWN
-- vocabulary (the rfis/filter_options/status endpoint, which is why it is in
-- config/endpoints.yml). Keys start at 90/100 to stay clear of the seeded block.
--
-- Join on Code, never on Label. Sort by SortOrder, colour by HexColor, display Label.

CREATE OR REPLACE TEMPORARY VIEW _status_seed AS
SELECT * FROM (VALUES
    (1,  'RiskImpact',     'HIGH',          'High',                        'Red',     1, '#DB1918'),
    (2,  'RiskImpact',     'MEDIUM',        'Medium',                      'Amber',   2, '#FFD800'),
    (3,  'RiskImpact',     'LOW',           'Low',                         'Neutral', 3, '#A6A6A6'),
    (10, 'RiskStatus',     'NOT_STARTED',   'Not Started',                 'Red',     1, '#DB1918'),
    (11, 'RiskStatus',     'PLANNED',       'Planned',                     'Amber',   2, '#FFD800'),
    (12, 'RiskStatus',     'IN_PROGRESS',   'In Progress',                 'Amber',   3, '#FFD800'),
    (13, 'RiskStatus',     'COMPLETE',      'Complete',                    'Green',   4, '#01AF00'),
    (20, 'ScheduleStatus', 'ON_TRACK',      'On Track',                    'Green',   1, '#01AF00'),
    (21, 'ScheduleStatus', 'BEHIND',        'Behind',                      'Amber',   2, '#FFD800'),
    (22, 'ScheduleStatus', 'AT_RISK',       'At Risk',                     'Red',     3, '#DB1918'),
    (30, 'SafetyStatus',   'COMPLETED',     'Completed',                   'Green',   1, '#01AF00'),
    (31, 'SafetyStatus',   'POSITIVE',      'Positive',                    'Green',   2, '#01AF00'),
    (32, 'SafetyStatus',   'SCHEDULED',     'Scheduled',                   'Amber',   3, '#FFD800'),
    (33, 'SafetyStatus',   'PLANNED',       'Planned',                     'Amber',   4, '#FFD800'),
    (34, 'SafetyStatus',   'HIGH_RISK',     'High Risk',                   'Red',     5, '#DB1918'),
    (35, 'SafetyStatus',   'DELAYED',       'Delayed',                     'Red',     6, '#DB1918'),
    (40, 'QualityStatus',  'OPEN',          'Open',                        'Red',     1, '#DB1918'),
    (41, 'QualityStatus',  'PASSED',        'Passed',                      'Green',   2, '#01AF00'),
    (42, 'QualityStatus',  'SCHEDULED',     'Scheduled',                   'Amber',   3, '#FFD800'),
    (43, 'QualityStatus',  'REJECTED',      'Rejected',                    'Red',     4, '#DB1918'),
    (44, 'QualityStatus',  'NCR',           'NCR',                         'Red',     5, '#DB1918'),
    (50, 'BudgetStatus',   'ON_TRACK',      'On Track',                    'Green',   1, '#01AF00'),
    (51, 'BudgetStatus',   'WATCH',         'Watch',                       'Amber',   2, '#FFD800'),
    (52, 'BudgetStatus',   'OVER_BUDGET',   'Over Budget',                 'Red',     3, '#DB1918'),
    (60, 'CashPosition',   'GOOD',          'Good (>= 100%)',              'Green',   1, '#01AF00'),
    (61, 'CashPosition',   'WATCH',         'Watch (50-99%)',              'Amber',   2, '#FFD800'),
    (62, 'CashPosition',   'BAD',           'Bad (< 50%)',                 'Red',     3, '#DB1918'),
    (70, 'Profitability',  'IN_RANGE',      'Within Range',                'Green',   1, '#01AF00'),
    (71, 'Profitability',  'OUT_WITH_PLAN', 'Out of Range, but has a plan','Amber',   2, '#FFD800'),
    (72, 'Profitability',  'MARGIN_FADE',   'Margin fade but no plan',     'Red',     3, '#DB1918'),
    (80, 'YesNo',          'Y',             'Yes',                         'Green',   1, '#01AF00'),
    (81, 'YesNo',          'N',             'No',                          'Red',     2, '#DB1918')
) AS t(StatusKey, Domain, Code, Label, RAG, SortOrder, HexColor);

-- Procore's RFI status vocabulary, straight from its own filter_options endpoint.
CREATE OR REPLACE TEMPORARY VIEW _rfi_status_vocab AS
SELECT DISTINCT
    'RfiStatus' AS Domain,
    TRIM(COALESCE(get_json_object(payload, '$.value'),
                  get_json_object(payload, '$.name'))) AS RawValue,
    TRIM(COALESCE(get_json_object(payload, '$.label'),
                  get_json_object(payload, '$.name'),
                  get_json_object(payload, '$.value'))) AS Label
FROM bronze_procore_rfi_statuses
WHERE get_json_object(payload, '$.value') IS NOT NULL
   OR get_json_object(payload, '$.name')  IS NOT NULL;

-- Submittals have no filter_options endpoint in the cheatsheet, so their vocabulary is
-- the distinct set actually observed. A status Procore has but this project has never
-- used will not appear - it would then surface as an unmatched-status reject, which is
-- the intended loud failure rather than a silent drop.
CREATE OR REPLACE TEMPORARY VIEW _submittal_status_vocab AS
SELECT DISTINCT
    'SubmittalStatus' AS Domain,
    StatusLabel AS RawValue,
    StatusLabel AS Label
FROM silver_rfi_submittal
WHERE ItemType = 'Submittal' AND StatusLabel IS NOT NULL AND StatusLabel <> '';

CREATE OR REPLACE TABLE dim_Status AS
WITH procore_vocab AS (
    SELECT * FROM _rfi_status_vocab
    UNION ALL
    SELECT * FROM _submittal_status_vocab
),
keyed AS (
    SELECT
        Domain,
        UPPER(REPLACE(REPLACE(RawValue, ' ', '_'), '-', '_')) AS Code,
        Label,
        ROW_NUMBER() OVER (PARTITION BY Domain ORDER BY Label) AS rn
    FROM procore_vocab
)
SELECT StatusKey, Domain, Code, Label, RAG, SortOrder, HexColor, IsOpen FROM (
    SELECT
        StatusKey, Domain, Code, Label, RAG, SortOrder, HexColor,
        -- Seeded domains are not open/closed concepts; only the two Procore domains are.
        CAST(NULL AS BOOLEAN) AS IsOpen
    FROM _status_seed

    UNION ALL

    SELECT
        CASE Domain WHEN 'RfiStatus' THEN 90 ELSE 100 END + rn AS StatusKey,
        Domain,
        Code,
        Label,
        -- ponytail: open = red, closed = green. Refine if Affect wants a third state.
        CASE WHEN Code IN ('CLOSED','VOID','CANCELLED','CANCELED','REJECTED','APPROVED')
             THEN 'Green' ELSE 'Red' END AS RAG,
        rn AS SortOrder,
        CASE WHEN Code IN ('CLOSED','VOID','CANCELLED','CANCELED','REJECTED','APPROVED')
             THEN '#01AF00' ELSE '#DB1918' END AS HexColor,
        -- ponytail: "open" is everything Procore has not terminated. Confirm the exact
        -- terminal set with Affect - it drives every "Open Critical RFI" number on the
        -- report. One-line change when they answer.
        CAST(Code NOT IN ('CLOSED','VOID','CANCELLED','CANCELED','REJECTED','APPROVED')
             AS BOOLEAN) AS IsOpen
    FROM keyed
) u;
