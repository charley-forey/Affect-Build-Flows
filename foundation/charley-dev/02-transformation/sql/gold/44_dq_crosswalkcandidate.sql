-- gold: dq_CrosswalkCandidate - PROPOSED Procore project <-> Sage job pairs. Never applied.
--
-- The crosswalk (seed_ProjectCrosswalk) is human-curated because Sage holds no Procore
-- reference. This table lists the pairs a reviewer should look at: an UNMAPPED Procore
-- project whose name equals an UNMAPPED Sage job's name or short name, after UPPER(TRIM()).
-- Measured 2026-09-13 that rule reproduces 3 legacy pairs with 0 disagreements and
-- proposes one new one (25-034 -> job 28).
--
-- NOTHING READS THIS BACK. sv_project_crosswalk reads only the seed; accepting a candidate
-- is a reviewed edit to seed/project_crosswalk.csv. A name match is evidence, not a key -
-- attaching revenue to the wrong project is worse than attaching it to none.
--
-- CD-ONLY (reads sv_sage_jobs): listed in deploy_gold.GOLD_CD_ONLY.

CREATE OR REPLACE TABLE dq_CrosswalkCandidate AS
WITH p AS (
    SELECT project_id, project_name, UPPER(TRIM(project_name)) AS n
    FROM sv_projects
    WHERE project_id NOT IN (SELECT procore_project_id FROM sv_project_crosswalk
                             WHERE procore_project_id IS NOT NULL)
),
j AS (
    SELECT sage_project_id, job_name, job_short_name
    FROM sv_sage_jobs
    WHERE sage_project_id NOT IN (SELECT sage_project_id FROM sv_project_crosswalk
                                  WHERE sage_project_id IS NOT NULL)
)
SELECT
    p.project_id                                   AS ProcoreProjectId,
    p.project_name                                 AS ProjectName,
    j.sage_project_id                              AS SageJobNumber,
    j.job_name                                     AS SageJobName,
    CASE WHEN p.n = UPPER(TRIM(j.job_name)) THEN 'EXACT_NAME_JOB_NAME'
         ELSE 'EXACT_NAME_SHORT_NAME' END          AS MatchRule,
    -- More than one candidate for either side means the name alone cannot decide.
    COUNT(*) OVER (PARTITION BY p.project_id) > 1
      OR COUNT(*) OVER (PARTITION BY j.sage_project_id) > 1
                                                   AS IsAmbiguous,
    'PROPOSED - review before adding to seed/project_crosswalk.csv' AS Status
FROM p
JOIN j ON p.n <> '' AND (p.n = UPPER(TRIM(j.job_name)) OR p.n = UPPER(TRIM(j.job_short_name)));
