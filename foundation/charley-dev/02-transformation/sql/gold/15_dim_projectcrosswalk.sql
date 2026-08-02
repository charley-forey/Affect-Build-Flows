-- gold: dim_ProjectCrosswalk - one row per project, showing which systems it exists in.
--
-- THE PROCORE PROJECT ID IS THE HUB. Everything joins to it:
--
--        Sage  ──(dim_projects_procoreXsage)──►  PROCORE  ◄──(its own Procore Project ID)── Outbuild
--
-- That shape is not a preference, it is what the data allows. Sage's `jobnum` on an invoice
-- is a foreign key to actrec.recnum - an internal row id, not a readable job code
-- (resources/sage-100-contractor/schema/README.md) - so there is no natural key to join on
-- and the crosswalk table IS the join. Outbuild is easier: it already carries a Procore
-- project id on every activity, so it attaches to the hub directly.
--
-- WHY THIS TABLE EXISTS AT ALL. Without it, "which projects are missing from Sage?" is a
-- question nobody can answer, and a project present in Procore but absent from the
-- crosswalk silently contributes zero revenue to every financial measure - it does not
-- error, it just quietly reads as a project that has never billed. That is the single most
-- dangerous failure mode in this platform, so it gets its own dimension and its own page.
--
-- UNMATCHED ROWS ARE KEPT, NOT DROPPED. An INNER JOIN here would make the problem
-- invisible, which is exactly how the workbook's defects survived. Every Procore project
-- appears; the flags say what is missing.

CREATE OR REPLACE TABLE dim_ProjectCrosswalk AS
WITH procore AS (
    SELECT project_id, project_name FROM sv_projects
),
sage AS (
    -- One row per Procore project. The crosswalk should already be unique, but a duplicate
    -- would silently fan out every financial fact joined through it, so it is collapsed
    -- here rather than trusted.
    SELECT procore_project_id, MAX(sage_project_id) AS sage_project_id,
           COUNT(DISTINCT sage_project_id) AS sage_match_count
    FROM sv_project_crosswalk
    WHERE sage_project_id IS NOT NULL
    GROUP BY procore_project_id
),
outbuild AS (
    SELECT procore_project_id, MAX(outbuild_project_id) AS outbuild_project_id,
           COUNT(DISTINCT outbuild_project_id) AS outbuild_match_count
    FROM sv_outbuild_projects
    WHERE procore_project_id IS NOT NULL
    GROUP BY procore_project_id
)
SELECT
    p.project_id                                   AS ProjectKey,
    TRIM(p.project_name)                           AS ProjectName,
    p.project_id                                   AS ProcoreProjectId,
    s.sage_project_id                              AS SageProjectId,
    o.outbuild_project_id                          AS OutbuildProjectId,

    -- Presence flags. These drive the coverage page and the DQ expectations.
    TRUE                                           AS IsInProcore,
    (s.sage_project_id     IS NOT NULL)            AS IsInSage,
    (o.outbuild_project_id IS NOT NULL)            AS IsInOutbuild,

    -- How many of the three systems hold this project. 3 = fully integrated; 1 = Procore
    -- only, which means no financials and no schedule for it.
    CAST(1
         + CASE WHEN s.sage_project_id     IS NOT NULL THEN 1 ELSE 0 END
         + CASE WHEN o.outbuild_project_id IS NOT NULL THEN 1 ELSE 0 END
         AS INT)                                   AS SystemCount,

    -- HOW the match was made, never inferred later. Everything here is an exact key join -
    -- if a name-similarity fallback is ever added, it must land as a different value so a
    -- fuzzy match can never be mistaken for a certain one on a financial report.
    CASE WHEN s.sage_project_id IS NOT NULL THEN 'CROSSWALK_TABLE' ELSE 'UNMATCHED' END
                                                   AS SageMatchMethod,
    CASE WHEN o.outbuild_project_id IS NOT NULL THEN 'EMBEDDED_PROCORE_ID' ELSE 'UNMATCHED' END
                                                   AS OutbuildMatchMethod,

    -- A project mapping to more than one id on the far side is a data problem, not a
    -- richer mapping: the MAX() above silently picks one, and this flag is how anyone
    -- finds out that happened.
    COALESCE(s.sage_match_count, 0) > 1            AS HasAmbiguousSageMatch,
    COALESCE(o.outbuild_match_count, 0) > 1        AS HasAmbiguousOutbuildMatch,

    -- Plain-language, for the report. A status column beats three booleans in a visual.
    CASE
        WHEN s.sage_project_id IS NULL AND o.outbuild_project_id IS NULL
            THEN 'Procore only - no financials, no schedule'
        WHEN s.sage_project_id IS NULL  THEN 'Missing from Sage - reads as zero revenue'
        WHEN o.outbuild_project_id IS NULL THEN 'Missing from Outbuild - no milestones'
        ELSE 'Fully mapped'
    END                                            AS CoverageStatus
FROM procore p
LEFT JOIN sage     s ON s.procore_project_id = p.project_id
LEFT JOIN outbuild o ON o.procore_project_id = p.project_id;
