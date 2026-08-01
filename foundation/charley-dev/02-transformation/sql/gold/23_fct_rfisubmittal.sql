-- gold: fct_RfiSubmittal - the item grain behind SUBMITTALS & RFI!Table22.
--
-- The workbook stores only a per-trade COUNT (11 trades x 2 numbers, typed by hand) and
-- feeds the file's single native chart. Storing the items themselves reproduces that chart
-- exactly and adds drill-through to the actual records for free.
--
-- CURRENTLY SUBMITTALS ONLY. RFIs are in config/endpoints.yml but have never been
-- ingested - there is no RFI table anywhere in the existing warehouse. The union below is
-- shaped so the RFI arm slots in with no change to the model, the measures, or the chart:
-- ItemType already distinguishes them.
--
-- "IsCritical" is UNRESOLVED. The workbook says "Open Critical" and never defines critical
-- anywhere. Procore exposes an RFI priority filter, which is the likely intent - hence
-- rfi_priorities in the registry - but it is a guess until Affect confirms. Rather than
-- bake a guess into a column everyone will trust, IsCritical is left NULL and the flag is
-- named honestly. Open question #5.

CREATE OR REPLACE TABLE fct_RfiSubmittal AS
SELECT
    project_id                        AS ProjectKey,
    'Submittal'                       AS ItemType,
    item_id                           AS ItemKey,
    item_number                       AS ItemNumber,
    TRIM(subject)                     AS Subject,
    TRIM(status_label)                AS StatusLabel,
    COALESCE(cost_code_id, 'UNASSIGNED') AS CostCodeKey,
    created_date                      AS CreatedDate,
    due_date                          AS DueDate,
    responded_date                    AS RespondedDate,
    -- Only set when the date falls inside dim_Date. Two submittals came back dated outside
    -- the calendar on the first real run; an unmatched key makes measures silently blank.
    CASE WHEN created_date IS NULL
              OR created_date < DATE '2015-01-01'
              OR created_date > DATE '2035-12-31' THEN NULL
         ELSE make_date(year(created_date), month(created_date), 1) END AS MonthStart,
    CASE WHEN created_date IS NOT NULL
              AND (created_date < DATE '2015-01-01' OR created_date > DATE '2035-12-31')
         THEN TRUE ELSE FALSE END     AS HasOutOfRangeDate,
    -- Open means not yet responded to. Derived from the data rather than from status text,
    -- which varies by Procore configuration.
    CASE WHEN responded_date IS NULL THEN TRUE ELSE FALSE END AS IsOpen,
    CAST(NULL AS BOOLEAN)             AS IsCritical,
    CASE
        WHEN responded_date IS NOT NULL AND created_date IS NOT NULL
            THEN datediff(responded_date, created_date)
        WHEN created_date IS NOT NULL
            THEN datediff(CURRENT_DATE, created_date)
    END                               AS DaysOpen,
    -- Past due only counts while still open: a late-but-answered item is not outstanding.
    CASE WHEN responded_date IS NULL AND due_date IS NOT NULL AND due_date < CURRENT_DATE
         THEN TRUE ELSE FALSE END     AS IsPastDue
FROM sv_submittals
WHERE project_id IS NOT NULL;
