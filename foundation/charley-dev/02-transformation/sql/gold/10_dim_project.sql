-- gold: dim_Project - the spine every fact hangs off.
--
-- ProjectKey is the PROCORE PROJECT ID, not an invented surrogate. Procore ids are stable,
-- unique and already carried on every fact, so a surrogate would add a lookup hop and a
-- reconciliation burden for nothing. It also keeps the key debuggable: a wrong number in
-- the report can be pasted straight into Procore.
--
-- The Procore <-> Sage join is dim_projects_procoreXsage, which already exists in Silver
-- and is reused rather than rebuilt. Per resources/sage-100-contractor/schema/README.md,
-- Sage `jobnum` is a foreign key to actrec.recnum - NOT a readable job code - so this
-- crosswalk is the join. Do not attempt to match on job number text.
--
-- =====================================================================================
-- LATE-ARRIVING PROJECTS. The first run against real data found 6 budget lines, 4 change
-- orders, 9 submittals and 3 milestones referencing projects that are NOT in the
-- crosswalk - it holds 15 projects while Procore has 18, and some facts reference
-- projects in neither.
--
-- Those facts are real. Dropping them would understate budgets and change orders, and
-- that is precisely the silent-shortfall failure this build exists to remove. So the
-- dimension is the UNION of the crosswalk and every project id actually observed on a
-- fact source, with IsInCrosswalk recording the difference.
--
-- That makes referential integrity hold BY CONSTRUCTION rather than by hope, and turns
-- "which projects have no Sage mapping?" into a filter on the model instead of a
-- pipeline failure. IsInCrosswalk = FALSE is a real finding for Rebecca: those projects
-- cannot join to any Sage financial data until the crosswalk is extended.
-- =====================================================================================
--
-- STILL OPEN: whether the Excel's YY-000 ProjectNumber maps onto this crosswalk, or needs
-- a third mapping. ProjectNumber is therefore left NULL rather than guessed - a wrong join
-- key is worse than an absent one, because it silently produces plausible numbers.

CREATE OR REPLACE TABLE dim_Project AS
WITH observed AS (
    -- Every project id that appears on any fact source.
    SELECT DISTINCT project_id FROM sv_budgets              WHERE project_id IS NOT NULL
    UNION SELECT DISTINCT project_id FROM sv_prime_change_orders WHERE project_id IS NOT NULL
    UNION SELECT DISTINCT project_id FROM sv_submittals     WHERE project_id IS NOT NULL
    UNION SELECT DISTINCT project_id FROM sv_outbuild_activities WHERE project_id IS NOT NULL
    UNION SELECT DISTINCT project_id FROM sv_prime_contracts WHERE project_id IS NOT NULL
),
all_projects AS (
    SELECT project_id FROM sv_projects WHERE project_id IS NOT NULL
    UNION
    SELECT project_id FROM observed
),
crosswalk AS (
    -- THE SAGE ID COMES FROM HERE, NOT FROM sv_projects. sv_projects.sage_project_id is a
    -- hardcoded CAST(NULL AS STRING) (01_source_views_cd.sql:43) because the Procore
    -- project record simply does not carry a Sage id. Taking SageJobNumber from that view
    -- makes the fct_Invoice join match nothing and every AR row read as UNMATCHED - with
    -- no error, because it is a LEFT JOIN and the row count survives unchanged.
    --
    -- Collapsed to one row per project: a duplicate would fan out the project spine
    -- itself, which is the same guard 15_dim_projectcrosswalk.sql applies.
    SELECT procore_project_id, MAX(sage_project_id) AS sage_project_id
    FROM sv_project_crosswalk
    WHERE sage_project_id IS NOT NULL
    GROUP BY procore_project_id
),
contracts AS (
    -- A project can hold several prime contracts; sum them so OriginalContractAmount is
    -- the project's total rather than whichever row happened to sort first.
    SELECT
        project_id,
        -- Explicit DOUBLE: DuckDB widens SUM(DOUBLE) to DECIMAL while Spark keeps DOUBLE.
        -- The semantic model infers its types from the offline build, so a difference here
        -- makes the table fail to load in DirectLake - silently, as a missing table.
        CAST(SUM(contract_value) AS DOUBLE) AS contract_value,
        MAX(retainage_pct)             AS retainage_pct,
        MIN(start_date)                AS contract_start,
        MAX(estimated_completion_date) AS contract_finish
    FROM sv_prime_contracts
    GROUP BY project_id
)
SELECT
    a.project_id                                  AS ProjectKey,
    a.project_id                                  AS ProcoreProjectId,
    xw.sage_project_id                            AS SageJobNumber,
    CAST(NULL AS STRING)                          AS ProjectNumber,
    COALESCE(x.project_name, 'Project ' || a.project_id) AS ProjectName,
    x.origin_code                                 AS OriginCode,
    c.contract_value                              AS OriginalContractAmount,
    c.retainage_pct                               AS RetainagePercent,
    c.contract_start                              AS ContractStart,
    c.contract_finish                             AS ContractFinish,
    -- A project present but with no prime contract is real (early-stage), so this is a
    -- flag rather than a filter.
    CASE WHEN c.project_id IS NULL THEN FALSE ELSE TRUE END AS HasPrimeContract,
    -- FALSE means no Sage mapping exists: this project cannot join to any Sage financial
    -- data until the crosswalk is extended. Surfaced on the diagnostics page.
    CASE WHEN xw.procore_project_id IS NULL THEN FALSE ELSE TRUE END AS IsInCrosswalk
FROM all_projects a
LEFT JOIN sv_projects x  ON a.project_id = x.project_id
LEFT JOIN crosswalk   xw ON a.project_id = xw.procore_project_id
LEFT JOIN contracts   c  ON a.project_id = c.project_id;
