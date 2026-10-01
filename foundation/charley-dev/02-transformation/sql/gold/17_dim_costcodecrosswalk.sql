-- gold: dim_CostCodeCrosswalk - cost codes across Procore and Sage, with the division
-- rollup the report groups by and the client's old -> new cost-code mapping.
--
-- One row per Procore cost code id (CostCodeKey), so it can sit behind dim_CostCode in the
-- model (dim_CostCode -> dim_CostCodeCrosswalk, many-to-one, single direction) and group
-- fct_BudgetLine / bridge_VendorCostCode by the NEW code or division without fanning out.
-- Every lookup below joins a source that is unique on its key: seed_CostCodeNew is
-- de-duplicated by make_qc_seeds.py and the old map is grouped to one row per old code.
--
-- THREE CODE SCHEMES LIVE SIDE BY SIDE IN PROCORE (measured 2026-09-30):
--   NEW             the client's new list, e.g. 10111.000. Carries no money yet.
--   OLD_SAGE        the old Sage code, forced into Procore in Jan 2026 with a CSI division
--                   written in front: '1-1018.000', '1-1018', '9-92000', '15-230000'. All
--                   four 2026 projects are 100% on this scheme by dollars, and it maps.
--   LEGACY_PROCORE  Procore's own CSI codes before 2026 - '09-20-00', '23-000', '01-013'.
--                   No mapping covers them and none is invented here: the client's answer
--                   is that completed pre-2026 projects stay as they are.
-- Anything without even a division prefix is UNPARSEABLE (HasUnparseableCode, below).
--
-- THE SAGE SIDE. Sage holds cost codes on invoice LINE tables: AP lines carry only a GL
-- account, AR lines carry a bare old code ('1012.0000') or nothing at all, because AR is
-- billed at division/aggregate level on lump-sum jobs. So SageCostCode is the old Sage code
-- a Procore code denotes, found by normalising the Procore code - not by a join to Sage
-- transactions, which mostly have no code to join on.
--
-- THE DIVISION PARSE. Procore cost codes read "01-00-00 - GENERAL REQUIREMENTS"; the report
-- groups by CSI division ("01"), which is not a column anywhere - it is a substring nobody
-- had extracted. Parsing it once here means every visual groups the same way, rather than
-- each doing its own string surgery. NewDivisionCode is the client's division of the NEW
-- code, and is the one to roll up and include/exclude by (01 General Requirements and 45
-- General Conditions are separate divisions in the new list).

CREATE OR REPLACE TABLE dim_CostCodeCrosswalk AS
WITH procore AS (
    SELECT
        cost_code_id,
        -- The CODE ("03-100"), not the name ("Concrete"). Parsing the name for a division
        -- is what made 5,429 of 5,433 codes look unparseable - a name has no division in it.
        TRIM(cost_code)      AS cost_code_raw,
        TRIM(cost_code_name) AS cost_code_name
    FROM sv_cost_codes
    WHERE cost_code_id IS NOT NULL
),
parsed AS (
    SELECT
        cost_code_id,
        cost_code_name,
        -- Everything before the first space-hyphen-space is the code; the rest is the name.
        -- Codes that do not follow the pattern keep the whole string as the code and get
        -- flagged, rather than being silently truncated into something that looks valid.
        -- Procore returns the code two ways depending on endpoint: "03-100" from
        -- /cost_codes, and "03-100 - CONCRETE" from a budget view. Handle both.
        CASE WHEN cost_code_raw LIKE '% - %'
             THEN TRIM(SUBSTRING(cost_code_raw, 1, INSTR(cost_code_raw, ' - ') - 1))
             ELSE cost_code_raw END  AS code_part,
        cost_code_name              AS name_part
    FROM procore
),
normalized AS (
    SELECT
        *,
        -- THE NORMALISER. Strip a leading 1-2 digit CSI division ('15-230000' -> '230000'),
        -- then, if what is left is digits with optional decimals, render it the way the
        -- client's lists write codes: integer part + '.' + decimals right-padded or cut to
        -- three. '1-1018' -> '1018.000', Sage AR's '1012.0000' -> '1012.000'.
        -- The integer part stays TEXT: '01-013' becomes '013.000' and cannot collide with
        -- an old code 13.000. A legacy three-part code ('09-20-00') is not digits after the
        -- strip and normalises to NULL. Character classes rather than \d so the pattern
        -- means the same in a Spark string literal and in DuckDB.
        CASE WHEN rlike_(regexp_replace(code_part, '^[0-9]{1,2}-', ''), '^[0-9]+([.][0-9]+)?$')
             THEN regexp_extract(regexp_replace(code_part, '^[0-9]{1,2}-', ''), '^([0-9]+)', 1)
                  || '.'
                  || SUBSTRING(RPAD(regexp_extract(regexp_replace(code_part, '^[0-9]{1,2}-', ''),
                                                   '[.]([0-9]+)$', 1), 3, '0'), 1, 3)
        END AS normalized_code,
        -- CSI division: the leading digits, ZERO-PADDED to two.
        --
        -- Affect writes divisions 1-9 without the leading zero - "1-1000 GENERAL REQUIREMENTS"
        -- is CSI Division 01, not an unparseable code. Requiring two digits marked all 807 of
        -- them unparseable (780 as `N-`, 27 as a bare `N`), so every Division 1-9 cost silently
        -- left the by-division rollup and surfaced as a data-quality problem rather than the
        -- parsing bug it was. Measured 2026-08-19: zero codes fail for any other reason.
        CASE WHEN rlike_(code_part, '^[0-9]{2}')
             THEN SUBSTRING(code_part, 1, 2)
             WHEN rlike_(code_part, '^[0-9]($|[^0-9])')
             THEN LPAD(SUBSTRING(code_part, 1, 1), 2, '0') END AS division_code
    FROM parsed
),
-- One row per old code. An old code the client mapped to two DIFFERENT new codes resolves
-- to no target rather than to whichever row came first - the DQ suite reports the
-- duplicate, and a guessed mapping would move dollars between divisions unseen.
old_map AS (
    SELECT OldCostCode,
           CASE WHEN COUNT(DISTINCT NewCostCode) = 1 THEN MAX(NewCostCode) END AS NewCostCode
    FROM seed_CostCodeMap
    GROUP BY OldCostCode
),
classified AS (
    SELECT
        n.*,
        CASE WHEN nat.NewCostCode IS NOT NULL THEN 'NEW'
             WHEN m.OldCostCode   IS NOT NULL THEN 'OLD_SAGE'
             WHEN n.division_code IS NOT NULL THEN 'LEGACY_PROCORE'
             ELSE 'UNPARSEABLE' END                   AS code_scheme,
        -- The client confirmed old and new numbering do not overlap; NEW wins if they ever do.
        COALESCE(nat.NewCostCode, m.NewCostCode)       AS new_cost_code,
        m.OldCostCode                                  AS old_cost_code
    FROM normalized n
    LEFT JOIN seed_CostCodeNew nat ON nat.NewCostCode = n.normalized_code
    LEFT JOIN old_map m           ON m.OldCostCode   = n.normalized_code
)
SELECT
    c.cost_code_id                                 AS CostCodeKey,
    c.cost_code_id                                 AS ProcoreCostCodeId,
    c.code_part                                    AS CostCode,
    COALESCE(c.name_part, c.cost_code_name)        AS CostCodeName,
    -- The Procore CSI prefix. This is what the budget page and every cost rollup grouped
    -- by before the new list existed; NewDivisionCode is the client's own division.
    c.division_code                                AS DivisionCode,

    -- The old Sage code this Procore code denotes, when it is one. 'OLD CC' in the client's
    -- workbook is the Sage cost-code export, so membership of seed_CostCodeMap is
    -- membership of Sage's list.
    c.old_cost_code                                AS SageCostCode,
    (c.old_cost_code IS NOT NULL)                  AS IsInSage,
    CASE WHEN c.old_cost_code IS NOT NULL THEN 'NORMALIZED_CODE' ELSE 'NONE' END
                                                   AS SageMatchMethod,

    TRUE                                           AS IsInProcore,
    -- A code that does not parse still appears - it just cannot be rolled up by division,
    -- and this flag is how that shows on the DQ page instead of quietly falling out of a
    -- subtotal.
    (c.division_code IS NULL)                      AS HasUnparseableCode,

    c.normalized_code                              AS NormalizedCode,
    c.code_scheme                                  AS CodeScheme,
    c.new_cost_code                                AS NewCostCode,
    t.Description                                  AS NewCostCodeName,
    t.DivisionCode                                 AS NewDivisionCode,
    t.DivisionName                                 AS NewDivisionName,
    -- NATIVE_NEW  already on the new list.
    -- MAPPED      an old Sage code with a target in the client's map.
    -- OLD_UNMAPPED an old Sage code the client has not mapped (v1: the two ALLOWANCES
    --             codes). Dollars here are a DQ warning: they cannot reach a new division.
    -- LEGACY_UNMAPPED pre-2026 Procore CSI codes, and anything unparseable. Expected, and
    --             left aside by agreement - reported, not mapped.
    CASE WHEN c.code_scheme = 'NEW' THEN 'NATIVE_NEW'
         WHEN c.code_scheme = 'OLD_SAGE' AND c.new_cost_code IS NOT NULL THEN 'MAPPED'
         WHEN c.code_scheme = 'OLD_SAGE' THEN 'OLD_UNMAPPED'
         ELSE 'LEGACY_UNMAPPED' END                AS MappingStatus
FROM classified c
LEFT JOIN seed_CostCodeNew t ON t.NewCostCode = c.new_cost_code;
