-- gold: dim_CostCode.
--
-- Barely present in the Excel - only implicitly, via the GC/GR section (FINANCIALS!
-- Table11011, which has just two data rows and a column header reading "SPENT TO DATE2").
-- That section is the one place the workbook attempts budget-vs-actual, and it is
-- unfinished. Real cost-code coverage is what turns it into something usable.
--
-- LATE-ARRIVING CODES. The first run against real data found 69 budget lines carrying a
-- cost code id that is not in dim_procore_cost_codes. Same treatment as dim_Project: the
-- dimension unions in every code actually observed, so referential integrity holds by
-- construction and IsInSource records which codes have no master-data entry. Dropping
-- those 69 lines would understate the budget.
--
-- Division is the leading numeric segment of the cost code, which is how Affect's codes
-- are structured and what allows a rollup above line-item grain.

CREATE OR REPLACE TABLE dim_CostCode AS
WITH observed AS (
    SELECT DISTINCT cost_code_id FROM sv_budgets    WHERE cost_code_id IS NOT NULL
    UNION SELECT DISTINCT cost_code_id FROM sv_submittals WHERE cost_code_id IS NOT NULL
),
all_codes AS (
    SELECT cost_code_id FROM sv_cost_codes WHERE cost_code_id IS NOT NULL
    UNION
    SELECT cost_code_id FROM observed
)
SELECT
    'UNASSIGNED' AS CostCodeKey,
    'Unassigned' AS CostCode,
    'Unassigned' AS Description,
    CAST(NULL AS STRING) AS Division,
    TRUE AS IsInSource

UNION ALL

SELECT
    a.cost_code_id AS CostCodeKey,
    COALESCE(TRIM(s.cost_code_name), 'Code ' || a.cost_code_id) AS CostCode,
    COALESCE(TRIM(s.cost_code_name), 'Code ' || a.cost_code_id) AS Description,
    -- Leading numeric segment, e.g. "03-100 Concrete" -> "03". NULL when the code does not
    -- follow that shape, rather than a silently wrong division.
    CASE
        WHEN TRIM(s.cost_code_name) LIKE '%-%'
        THEN TRIM(SUBSTRING(TRIM(s.cost_code_name), 1, POSITION('-' IN TRIM(s.cost_code_name)) - 1))
    END AS Division,
    CASE WHEN s.cost_code_id IS NULL THEN FALSE ELSE TRUE END AS IsInSource
FROM all_codes a
LEFT JOIN sv_cost_codes s ON a.cost_code_id = s.cost_code_id;
