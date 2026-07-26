-- gold: fct_RfiSubmittal - one row per RFI or submittal.
--
-- Column names and types match powerbi/semantic-model.md exactly; powerbi/measures.dax
-- reads ItemType, IsCritical, StatusKey, DaysOpen and TradeKey, and matches ItemType
-- against the literal strings 'RFI' and 'Submittal', so those are not negotiable.
--
-- Two values here are undefined BY THE CLIENT, not by this pipeline. Both are isolated
-- to a single expression so confirming them is a one-line edit:
--   * IsCritical - the workbook never defines "critical" (open question #5).
--   * TradeKey   - RFIs carry a cost code, submittals a spec section; neither maps onto
--                  Affect's 29 trades (powerbi/source-mapping.md:143).

CREATE OR REPLACE TEMPORARY VIEW _fct_staged AS
SELECT
    p.ProjectKey,
    s.ItemType,
    s.ItemNumber,
    s.ProcoreItemId,
    s.Subject,
    st.StatusKey,
    st.IsOpen,
    -- ponytail: "critical" = Procore priority High/Urgent. The workbook never defines the
    -- word (open question #5) and this drives every number on the SUBMITTALS & RFI tab.
    -- Change this one CASE when Affect answers.
    CAST(UPPER(COALESCE(s.PriorityLabel, '')) IN ('HIGH', 'URGENT', 'CRITICAL') AS BOOLEAN)
                                                        AS IsCritical,
    -- ponytail: best-effort exact name match against the 29 trades. Procore does not
    -- carry Affect's trade vocabulary, so most rows will land on Unassigned (TradeKey 0)
    -- and get logged below. Upgrade path is a CSI-division bridge on dim_Trade
    -- (open question #14) once Affect decides.
    COALESCE(t.TradeKey, 0)                             AS TradeKey,
    datediff(COALESCE(s.ClosedDate, CURRENT_DATE), s.CreatedDate) AS DaysOpen,
    s.CreatedDate,
    s.DueDate,
    s.ClosedDate,
    s.ProcoreProjectId,
    s.IngestedAt
FROM silver_rfi_submittal s
LEFT JOIN dim_Project p
       ON p.ProcoreProjectId = s.ProcoreProjectId
LEFT JOIN dim_Status st
       ON st.Domain = CASE s.ItemType WHEN 'RFI' THEN 'RfiStatus' ELSE 'SubmittalStatus' END
      AND st.Code   = UPPER(REPLACE(REPLACE(s.StatusLabel, ' ', '_'), '-', '_'))
LEFT JOIN dim_Trade t
       ON LOWER(t.TradeName) = LOWER(COALESCE(s.CostCodeName, s.SpecSection))
      AND t.TradeKey <> 0;

-- Flag, do not drop. These rows still reach the report; the gaps are visible on the
-- Data Quality page instead of quietly shrinking a count.
INSERT INTO data_quality_log
SELECT 'fct_RfiSubmittal', ProcoreItemId, ProcoreProjectId, ItemType,
       'unmatched_trade', 'warn', IngestedAt
FROM _fct_staged WHERE TradeKey = 0;

INSERT INTO data_quality_log
SELECT 'fct_RfiSubmittal', ProcoreItemId, ProcoreProjectId, ItemType,
       'unmatched_status', 'warn', IngestedAt
FROM _fct_staged WHERE StatusKey IS NULL;

INSERT INTO data_quality_log
SELECT 'fct_RfiSubmittal', ProcoreItemId, ProcoreProjectId, ItemType,
       'unknown_project', 'warn', IngestedAt
FROM _fct_staged WHERE ProjectKey IS NULL;

CREATE OR REPLACE TABLE fct_RfiSubmittal AS
SELECT
    ProjectKey,
    TradeKey,
    StatusKey,
    ItemType,
    ItemNumber,
    Subject,
    IsCritical,
    IsOpen,
    DaysOpen,
    CreatedDate,
    DueDate,
    ClosedDate,
    ProcoreItemId,
    IngestedAt
FROM _fct_staged;
