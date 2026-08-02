-- gold: fct_DirectCost - payroll and expenses charged straight to the job.
--
-- 418 rows: 313 expense, 99 payroll, 6 invoice.
--
-- This is the only source of self-performed labour cost anywhere in the platform. It is
-- not in a commitment, not in a requisition, and not in the budget's committed column -
-- those all describe money owed to somebody else. Cost-to-date built without it
-- understates every job Affect's own crews work on, and understates it in the safe-looking
-- direction: the number comes out lower, so the job looks more profitable than it is.
--
-- Unlike fct_Billing, every row here is a discrete transaction. Sums are correct across
-- any grouping - no running balances, no latest-period filter.

CREATE OR REPLACE TABLE fct_DirectCost AS
SELECT
    direct_cost_id                   AS DirectCostKey,
    project_id                       AS ProjectKey,
    vendor_id                        AS VendorKey,
    vendor_name                      AS VendorName,
    description                      AS Description,
    -- payroll | expense | invoice, as Procore records it.
    cost_type                        AS CostType,
    -- Titled for a report axis rather than a database column, since this is what a reader
    -- sees on the page. Self-performed labour is the distinction that matters here: it is
    -- the cost that exists in no other feed.
    CASE cost_type
        WHEN 'payroll' THEN 'Self-Performed Labour'
        WHEN 'expense' THEN 'Direct Expense'
        WHEN 'invoice' THEN 'Direct Invoice'
        -- An unseen fourth type passes through as Procore's own raw value rather than a
        -- prettified one, so it is traceable straight back to the API and obvious that it
        -- is unmapped rather than looking like a category we designed.
        ELSE COALESCE(cost_type, 'Unclassified')
    END                              AS CostCategory,
    employee_name                    AS EmployeeName,
    status_label                     AS StatusLabel,
    cost_date                        AS CostDate,
    -- `amount` reconciles to the source document; `grand_total` includes tax and freight
    -- and is what actually hits the job. GrandTotal is the one to report on, so it is
    -- named unambiguously and Amount is kept beside it for the reconciliation.
    amount                           AS Amount,
    grand_total                      AS GrandTotal,
    CASE WHEN cost_date IS NULL
              OR cost_date < DATE '2015-01-01'
              OR cost_date > DATE '2035-12-31' THEN NULL
         ELSE make_date(year(cost_date), month(cost_date), 1) END AS MonthStart,
    CASE WHEN cost_date IS NOT NULL
              AND (cost_date < DATE '2015-01-01' OR cost_date > DATE '2035-12-31')
         THEN TRUE ELSE FALSE END    AS HasOutOfRangeDate,
    -- Approved is the only status that should reach a cost report. Exposed as a flag
    -- rather than filtered away, because "how much is sitting unapproved" is itself a
    -- question worth asking at month end.
    (UPPER(COALESCE(status_label, '')) = 'APPROVED') AS IsApproved
FROM sv_direct_costs
WHERE project_id IS NOT NULL;
