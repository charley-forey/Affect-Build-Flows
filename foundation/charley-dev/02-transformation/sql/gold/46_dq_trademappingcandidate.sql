-- gold: dq_TradeMappingCandidate - one row per raw Procore trade label, with a PROPOSED
-- TradeKey and whether Affect still has to decide it. Never applied.
--
-- The DQ warning "Procore trades resolve to a seeded trade" counts rows; this says which
-- labels they are, how many records each touches, and what a reviewer might map it to.
--
--   MappingStatus  MAPPED         resolves today (exact key or qc_seed_TradeAlias)
--                  AMBIGUOUS      could be more than one library trade - Affect picks
--                  NO_EQUIVALENT  no trade in the 26-sheet library - a scope decision
--                  UNMAPPED       nothing curated yet; any token match is shown
--
-- Proposals come from two places, in this order:
--   1. qc_seed_TradeSynonymProposal (seed/qc_trade_synonym_proposals.csv), curated by hand.
--   2. An exact whole-word token match between the label and a TradeKey ("Plumbing
--      Fixtures" contains PLUMBING). Evidence for a reviewer, not a similarity score.
--
-- NOTHING READS THIS BACK, and neither 25_fct_qualityitem.sql nor 33_fct_qc.sql reads the
-- proposal seed - test_qc.py asserts both. Approving a proposal is a reviewed edit to
-- seed/qc_trade_alias.csv; attaching a defect to the wrong trade is worse than to none.
--
-- CD-ONLY (reads sv_qc_*): listed in deploy_gold.GOLD_CD_ONLY.

CREATE OR REPLACE TABLE dq_TradeMappingCandidate AS
WITH src AS (
    -- project_id IS NOT NULL: the same rows 33_fct_qc.sql keeps.
    SELECT 'Observation' AS SourceType, project_id, TRIM(trade) AS label, created_date AS seen
    FROM sv_qc_ncr WHERE NULLIF(TRIM(trade), '') IS NOT NULL AND project_id IS NOT NULL
    UNION ALL
    SELECT 'Punch', project_id, TRIM(trade), created_date
    FROM sv_qc_punch WHERE NULLIF(TRIM(trade), '') IS NOT NULL AND project_id IS NOT NULL
    UNION ALL
    SELECT 'Inspection', project_id, TRIM(trade), inspection_date
    FROM sv_qc_inspection WHERE NULLIF(TRIM(trade), '') IS NOT NULL AND project_id IS NOT NULL
),
labels AS (
    -- Grouped case-insensitively, as the alias join matches and as Power BI groups text.
    SELECT UPPER(label)                                              AS LabelKey,
           MIN(label)                                                AS RawTrade,
           SUM(CASE WHEN SourceType = 'Observation' THEN 1 ELSE 0 END) AS ObservationCount,
           SUM(CASE WHEN SourceType = 'Punch' THEN 1 ELSE 0 END)       AS PunchCount,
           SUM(CASE WHEN SourceType = 'Inspection' THEN 1 ELSE 0 END)  AS InspectionCount,
           -- AFFECTED = records a mapping would change: observations and punch items only.
           -- fct_ProcoreInspection never resolves a trade, so inspections are counted in
           -- InspectionCount for context and kept out of AffectedRecords and ProjectCount.
           SUM(CASE WHEN SourceType <> 'Inspection' THEN 1 ELSE 0 END) AS AffectedRecords,
           COUNT(DISTINCT CASE WHEN SourceType <> 'Inspection' THEN project_id END) AS ProjectCount,
           MIN(seen)                                                 AS FirstSeen,
           MAX(seen)                                                 AS LastSeen
    FROM src
    GROUP BY UPPER(label)
),
norm AS (
    -- ponytail: punctuation folded with nested REPLACE because regexp_replace replaces
    -- all matches in Spark but only the first in DuckDB. Add a character here if a label
    -- with new punctuation fails to token-match.
    SELECT l.*,
           REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
               l.LabelKey, ' ', '_'), '/', '_'), '-', '_'), '&', '_'), ',', '_'), '(', '_'), ')', '_')
                                                                     AS NormKey
    FROM labels l
),
tokens AS (
    SELECT n.LabelKey, COUNT(*) AS Matches, MIN(t.TradeKey) AS K1, MAX(t.TradeKey) AS K2
    FROM norm n
    JOIN qc_seed_Trade t
      ON instr('_' || t.TradeKey || '_', '_' || n.NormKey || '_') > 0
      OR instr('_' || n.NormKey || '_', '_' || t.TradeKey || '_') > 0
    GROUP BY n.LabelKey
),
decided AS (
    SELECT n.*,
           -- The SAME resolution 33_fct_qc.sql applies, so MAPPED here means mapped there.
           COALESCE(t.TradeKey, x.TradeKey)                          AS CurrentTradeKey,
           CASE WHEN t.TradeKey IS NOT NULL THEN 'EXACT'
                WHEN x.TradeKey IS NOT NULL THEN 'ALIAS' END         AS MatchedBy,
           p.Kind, p.ProposedTradeKeys AS CuratedKeys, p.Reason AS CuratedReason,
           k.Matches, k.K1, k.K2
    FROM norm n
    LEFT JOIN qc_seed_Trade t ON t.TradeKey = REPLACE(n.LabelKey, ' ', '_')
    LEFT JOIN qc_seed_TradeAlias x ON UPPER(TRIM(x.ProcoreTrade)) = n.LabelKey
    LEFT JOIN qc_seed_TradeSynonymProposal p ON UPPER(TRIM(p.ProcoreTrade)) = n.LabelKey
    LEFT JOIN tokens k ON k.LabelKey = n.LabelKey
),
statused AS (
    SELECT d.*,
           CASE WHEN CurrentTradeKey IS NOT NULL THEN 'MAPPED'
                WHEN Kind = 'AMBIGUOUS' THEN 'AMBIGUOUS'
                WHEN Kind = 'NO_EQUIVALENT' THEN 'NO_EQUIVALENT'
                WHEN Kind IS NULL AND Matches > 1 THEN 'AMBIGUOUS'
                ELSE 'UNMAPPED' END                                  AS MappingStatus
    FROM decided d
)
SELECT
    RawTrade,
    MappingStatus,
    ObservationCount,
    PunchCount,
    InspectionCount,
    AffectedRecords,
    ProjectCount,
    FirstSeen,
    LastSeen,
    CurrentTradeKey,
    CASE WHEN MappingStatus = 'MAPPED' THEN CAST(NULL AS STRING)
         WHEN Kind IS NOT NULL THEN CuratedKeys
         WHEN Matches = 1 THEN K1
         WHEN Matches = 2 THEN K1 || '|' || K2
         WHEN Matches > 2 THEN K1 || '|' || K2 || '|+' || CAST(Matches - 2 AS STRING) || ' more'
    END                                                              AS ProposedTradeKeys,
    CASE WHEN MappingStatus = 'MAPPED' THEN CAST(NULL AS STRING)
         WHEN Kind IS NOT NULL THEN 'CURATED_PROPOSAL'
         WHEN Matches > 0 THEN 'EXACT_TOKEN_MATCH' END               AS ProposalSource,
    CASE WHEN MatchedBy = 'EXACT' THEN 'Resolved: label equals a library TradeKey'
         WHEN MatchedBy = 'ALIAS' THEN 'Resolved: approved alias in qc_trade_alias.csv'
         WHEN Kind IS NOT NULL THEN CuratedReason
         WHEN Matches > 0 THEN 'Label shares a whole word with ' || CAST(Matches AS STRING)
                               || ' library TradeKey(s)'
         ELSE 'No proposal: no token match and no curated synonym' END AS ProposalReason,
    MappingStatus <> 'MAPPED'                                        AS IsDecisionNeeded,
    MappingStatus = 'NO_EQUIVALENT'                                  AS IsNoLibraryEquivalent
FROM statused;
