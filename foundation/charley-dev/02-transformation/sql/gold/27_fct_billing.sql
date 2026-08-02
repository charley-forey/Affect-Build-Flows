-- gold: fct_Billing - progress billing, both directions, at period grain.
--
-- One row per contract per billing period. Owner rows are what Affect bills the client
-- (AIA G702 payment applications); Subcontractor rows are what subs bill Affect
-- (requisitions). Same form, opposite direction.
--
-- This is where retainage comes from. fct_Invoice documents, correctly, that Sage holds
-- none at the invoice header - `retain` is zero across all 940 rows. It is held here, in
-- progress billing, and it was already in our bronze:
--
--     retainage currently held    $830,725.87 owner     $486,030.04 sub
--
-- ============================================================================
-- CUMULATIVE COLUMNS. READ THIS BEFORE WRITING A MEASURE OVER THIS TABLE.
-- ============================================================================
--
-- Every column below whose name ends in `ToDate`, plus RetainageHeld and BalanceToFinish,
-- is a RUNNING BALANCE restated in full on each period - not a period movement. Summing
-- one across periods adds the same money once per billing cycle.
--
-- This is not hypothetical. Summing RetainageHeld across all 607 rows gives $9,046,211.75.
-- The real figure is $1,316,755.91. A near-sevenfold overstatement, on a number that would
-- look entirely plausible on a card and that nobody could check without the source.
--
-- The first draft of this comment said $823,034, because the offline probe that produced it
-- let DRAFT billings win the ranking. A draft has not been issued, so its retainage is not
-- held by anyone - which is why IsLatestPeriod excludes drafts, and why the number in a
-- comment is worth less than the number the model returns.
--
-- Two things guard against it:
--
--   IsLatestPeriod   marks the one row per contract that carries the current balance. Any
--                    measure over a cumulative column must filter to it.
--   CurrentPaymentDue  is the ONLY money column here that is a period movement, and so
--                    the only one that is safe to sum across periods. It sums, by design,
--                    to the same total the cumulative column reaches.
--
-- The pair means a correct answer is reachable two independent ways, which is what makes
-- the DQ suite able to check one against the other.
--
-- DRAFTS ARE EXCLUDED FROM IsLatestPeriod. A draft billing has not been issued, so the
-- retainage on it is not held by anyone yet; letting a draft win the ranking would replace
-- a real balance with a speculative one. Drafts stay in the table - they are real pending
-- work, and StatusLabel is exposed so a measure can include them deliberately.

CREATE OR REPLACE TABLE fct_Billing AS
WITH ranked AS (
    SELECT
        b.*,
        -- Partitioned by direction as well as contract: an owner contract id and a
        -- subcontract commitment id come from different id spaces and can collide.
        --
        -- Ordered by period_number as well as period_end because period_end REPEATS - one
        -- contract has three periods all ending 2026-07-31, and two more pairs sharing an
        -- end date. Ordering on the date alone makes the winner arbitrary, and on this
        -- contract the arbitrary winner differs from the true latest by $378,159.
        ROW_NUMBER() OVER (
            PARTITION BY b.billing_type, b.contract_id
            -- Drafts sort last rather than being filtered out, so they stay in the table
            -- as the real pending work they are while never winning the ranking. FALSE
            -- sorts before TRUE, so every issued period outranks every draft.
            ORDER BY (b.status_label = 'DRAFT') ASC,
                     b.period_end DESC NULLS LAST, b.period_number DESC
        ) AS _rank
    FROM sv_billing b
    WHERE b.project_id IS NOT NULL
)
SELECT
    billing_id                       AS BillingKey,
    project_id                       AS ProjectKey,
    billing_type                     AS BillingType,
    contract_id                      AS ContractId,
    contract_name                    AS ContractName,
    contract_type                    AS ContractType,
    vendor_id                        AS VendorKey,
    counterparty_name                AS CounterpartyName,
    invoice_number                   AS InvoiceNumber,
    period_number                    AS PeriodNumber,
    status_label                     AS StatusLabel,
    billing_date                     AS BillingDate,
    period_start                     AS PeriodStart,
    period_end                       AS PeriodEnd,
    payment_date                     AS PaymentDate,
    percent_complete                 AS PercentComplete,

    -- Same guard as every other fact: a MonthStart outside dim_Date makes every measure
    -- over it return blank, which on a card is indistinguishable from zero billed.
    CASE WHEN period_end IS NULL
              OR period_end < DATE '2015-01-01'
              OR period_end > DATE '2035-12-31' THEN NULL
         ELSE make_date(year(period_end), month(period_end), 1) END AS MonthStart,
    CASE WHEN period_end IS NOT NULL
              AND (period_end < DATE '2015-01-01' OR period_end > DATE '2035-12-31')
         THEN TRUE ELSE FALSE END    AS HasOutOfRangeDate,

    -- ---- period movement: SAFE TO SUM ----
    current_payment_due              AS CurrentPaymentDue,

    -- ---- running balances: FILTER TO IsLatestPeriod ----
    original_contract_sum            AS OriginalContractSum,
    net_change_by_change_orders      AS NetChangeByChangeOrders,
    contract_sum_to_date             AS ContractSumToDate,
    completed_to_date                AS CompletedToDate,
    previous_certificates            AS PreviousCertificatesToDate,
    retainage_amount                 AS RetainageHeld,
    total_retainage                  AS TotalRetainageHeld,
    stored_retainage_amount          AS StoredRetainageHeld,
    earned_less_retainage            AS EarnedLessRetainageToDate,
    balance_to_finish                AS BalanceToFinish,
    retainage_percent                AS RetainagePercent,

    -- A contract whose only billing is a draft has no current balance at all, so it gets
    -- no latest row rather than a speculative one.
    (_rank = 1 AND status_label <> 'DRAFT') AS IsLatestPeriod,
    -- Retainage released rather than never withheld. A contract that held retainage in an
    -- earlier period and holds none now has been released; one that never held any was
    -- billed without retention. Both show a current zero and they mean opposite things.
    --
    -- Note this catches the released-to-zero-at-completion case only. Procore ALSO records
    -- a release as a NEGATIVE RetainageHeld on the period it is paid out - on
    -- PO-24-011-012 the retainage is -489.94 against a payment due of +489.94, exactly
    -- offsetting. Those rows are left negative rather than zeroed, because the sign is
    -- what makes the retainage measures net correctly across a release.
    (_rank = 1 AND status_label <> 'DRAFT'
              AND COALESCE(retainage_amount, 0) = 0
              AND COALESCE(percent_complete, 0) >= 100) AS IsRetainageReleased
FROM ranked;
