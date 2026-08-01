-- gold: fct_ChangeOrder - prime contract change orders.
--
-- Turns two hand-typed workbook cells into measures:
--   FINANCIALS!C5  "Pending CO's" - entered as =65000+3158.46+11550+4620, i.e. someone did
--                  mental arithmetic in a value cell and the components are now lost.
--                  Here each addend is a row.
--   FINANCIALS!C6  "Age of oldest unapproved CO" - typed by hand, and derivable from
--                  created_date the moment the data is in a table.
--
-- DaysOpen is computed against the load date. That is deliberately a stored column rather
-- than a measure: "age at the time this snapshot was taken" is what a monthly report
-- needs, and recomputing it against TODAY() is exactly the non-reproducibility that makes
-- the workbook's saved files disagree with themselves (defect #5).

CREATE OR REPLACE TABLE fct_ChangeOrder AS
SELECT
    project_id                       AS ProjectKey,
    change_order_id                  AS ChangeOrderKey,
    contract_id                      AS ContractId,
    co_number                        AS ChangeOrderNumber,
    'Prime'                          AS ChangeOrderType,
    TRIM(status)                     AS StatusLabel,
    amount                           AS Amount,
    created_date                     AS CreatedDate,
    -- MonthStart is only set when the date falls inside dim_Date. The first run against
    -- real data found 4 change orders dated outside the calendar; a MonthStart with no
    -- matching date row makes every measure over it silently return blank, which is the
    -- exact failure dim_Date exists to remove. NULL is honest, an unmatched key is not.
    CASE WHEN created_date IS NULL
              OR created_date < DATE '2015-01-01'
              OR created_date > DATE '2035-12-31' THEN NULL
         ELSE make_date(year(created_date), month(created_date), 1) END AS MonthStart,
    CASE WHEN created_date IS NOT NULL
              AND (created_date < DATE '2015-01-01' OR created_date > DATE '2035-12-31')
         THEN TRUE ELSE FALSE END    AS HasOutOfRangeDate,
    -- "Pending" is anything not yet approved. Matching case-insensitively because status
    -- text casing is not guaranteed consistent across Procore configurations.
    CASE WHEN LOWER(TRIM(status)) IN ('approved', 'closed') THEN FALSE ELSE TRUE END AS IsPending,
    CASE WHEN created_date IS NULL THEN NULL
         ELSE datediff(CURRENT_DATE, created_date) END AS DaysOpen
FROM sv_prime_change_orders
WHERE project_id IS NOT NULL;
