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

-- SECOND JOBS (2026-10-25). A Procore project that is already mapped can still have an
-- unmapped Sage job of the same name - Affect opens a new Sage job for a later phase or
-- change scope (seen live 2026-10-25: a second same-name job with open AR beside the
-- mapped one). Those are proposed too, under their own rule: the crosswalk holds
-- one Sage job per project, so accepting one is a design change, not just a seed row.

CREATE OR REPLACE TABLE dq_CrosswalkCandidate AS
WITH p AS (
    -- A join, not IN (subquery) in the SELECT list: Spark allows predicate subqueries only
    -- in filters.
    SELECT sp.project_id, sp.project_name, UPPER(TRIM(sp.project_name)) AS n,
           xw.procore_project_id IS NOT NULL AS is_mapped
    FROM sv_projects sp
    LEFT JOIN (SELECT DISTINCT procore_project_id FROM sv_project_crosswalk
               WHERE procore_project_id IS NOT NULL) xw ON xw.procore_project_id = sp.project_id
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
    CASE WHEN p.is_mapped THEN 'EXACT_NAME_SECOND_SAGE_JOB'
         WHEN p.n = UPPER(TRIM(j.job_name)) THEN 'EXACT_NAME_JOB_NAME'
         ELSE 'EXACT_NAME_SHORT_NAME' END          AS MatchRule,
    -- More than one candidate for either side means the name alone cannot decide.
    COUNT(*) OVER (PARTITION BY p.project_id) > 1
      OR COUNT(*) OVER (PARTITION BY j.sage_project_id) > 1
                                                   AS IsAmbiguous,
    'PROPOSED - review before adding to seed/project_crosswalk.csv' AS Status
FROM p
JOIN j ON p.n <> '' AND (p.n = UPPER(TRIM(j.job_name)) OR p.n = UPPER(TRIM(j.job_short_name)));
