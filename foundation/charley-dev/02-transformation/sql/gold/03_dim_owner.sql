-- gold: dim_Owner - the 9 roles from DROPDOWN!C4:C12.
--
-- Verbatim from analysis/excel-tracker/dropdowns-and-status.md:55-65. The workbook reuses
-- this one list in three places (risk owner, safety responsible, quality responsible), so
-- it is already a shared dimension in everything but name.
--
-- The workbook tracks ROLE, not person. PersonName is left here as a nullable column
-- because powerbi/semantic-model.md:131 anticipates Affect wanting named individuals
-- later; nothing depends on it today.
--
-- OwnerKey 0 = Unassigned, so a row with no owner still appears rather than dropping out
-- of an inner join.
--
-- SortOrder is SENIORITY, not alphabetical, taken from the hierarchy proposed in
-- dropdowns-and-status.md:280-282. That document explicitly says "Confirm the hierarchy
-- with Affect" - it is our reading of their org, not their statement of it. Open question
-- for the next call; changing it is a one-line edit here and nothing downstream cares.

CREATE OR REPLACE TABLE dim_Owner AS
SELECT * FROM (VALUES
    (0, 'Unassigned',           999, CAST(NULL AS VARCHAR)),
    (1, 'Principal',              1, CAST(NULL AS VARCHAR)),
    (2, 'PX',                     2, CAST(NULL AS VARCHAR)),
    (3, 'Senior PM',              3, CAST(NULL AS VARCHAR)),
    (4, 'Dir. of Construction',   4, CAST(NULL AS VARCHAR)),
    (5, 'PM',                     5, CAST(NULL AS VARCHAR)),
    (6, 'Asst. PM',               6, CAST(NULL AS VARCHAR)),
    (7, 'Super',                  7, CAST(NULL AS VARCHAR)),
    (8, 'Asst. Super',            8, CAST(NULL AS VARCHAR)),
    (9, 'Scheduler',              9, CAST(NULL AS VARCHAR))
) AS t(OwnerKey, RoleName, SortOrder, PersonName);
