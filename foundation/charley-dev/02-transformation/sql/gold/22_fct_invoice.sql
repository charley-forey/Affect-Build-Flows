-- gold: fct_Invoice - Sage AR invoices, joined to the project spine.
--
-- Replaces FINANCIALS!Table11012, whose DELTA column computes days-to-payment by hand and
-- whose F56 average (8.82 days) feeds the dashboard's "AVG. DAYS FOR PAYMENT RECEIVED".
--
-- The join is via dim_Project[SageJobNumber], because Sage `jobnum` is a foreign key to
-- actrec.recnum and NOT a readable job code
-- (resources/sage-100-contractor/schema/README.md). Joining on job-number text would
-- silently match nothing, or worse, match wrongly.
--
-- RETAINAGE IS DELIBERATELY ABSENT. Commit db0d11e verified that `retain` on the Sage
-- invoice header is ZERO across all 940 invoices (135 AR, 805 AP) - retainage is not held
-- at header level for this company. Surfacing it here would report $0 with total
-- confidence. It has to come from arivln, actrec.retain, or progress billing, none of
-- which the current dataflow reads.

--
-- PAID DATE COMES FROM THE RECEIPTS, NOT THE HEADER. sv_ar_payments (Sage acrpmt) carries a
-- date per receipt; see 26_sage_silver.sql for the measured key and reconciliation.
-- Receipts are netted per day first, so a same-day +X/-X reversal never counts as payment.
-- PaidDate is the first day the running total reached the invoice total AND never fell
-- back below it afterwards (a later reversal reopens the invoice). NULL when not fully
-- paid by receipts - including opening-balance invoices whose header says paid but which
-- have no receipt rows; a due date is never substituted.

--
-- VOIDS ARE ZEROED HERE, ONCE (2026-10-30). Sage 100 Contractor keeps a voided invoice (status
-- 5) with its full amount as a balance: 55 of them, $5.46M, read as billed revenue and as
-- unpaid AR on every page - most of the gap between the dashboard's $17.7M revenue to the end
-- of September and Affect's $15.8M, and of AR that "didn't seem correct". Every reader sums
-- Amount / Balance, so zeroing them here fixes them all; the row stays, with VoidedAmount,
-- so the drill-down still shows what was left out and why.
--
-- A SECOND SAGE JOB FOR ONE PROJECT. dim_Project holds one Sage job per project (the
-- 'primary' crosswalk row). Affect sometimes opens a second job for the same Procore project
-- (job 30 beside job 27 for 360 Lexington 15th floor); seed rows marked 'additional' attach
-- that job's invoices to the project without changing the project's own Sage id.

CREATE OR REPLACE TABLE fct_Invoice AS
WITH extra_job AS (
    SELECT SageJobNumber, MAX(ProcoreProjectId) AS ProjectKey
    FROM seed_ProjectCrosswalk WHERE Relationship = 'additional' GROUP BY SageJobNumber
), daily AS (
    SELECT invoice_uid, payment_date, SUM(amount) AS amount
    FROM sv_ar_payments
    GROUP BY invoice_uid, payment_date
), running AS (
    SELECT d.invoice_uid, d.payment_date, d.amount, i.invoice_total,
           SUM(d.amount) OVER (PARTITION BY d.invoice_uid ORDER BY d.payment_date
                               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative
    FROM daily d
    JOIN sv_ar_invoices i ON i.invoice_uid = d.invoice_uid
), last_short AS (
    SELECT invoice_uid, MAX(CASE WHEN cumulative < invoice_total - 0.005 THEN payment_date END) AS short_date
    FROM running
    GROUP BY invoice_uid
), payments AS (
    SELECT r.invoice_uid,
           SUM(r.amount)                AS payments_received,
           MIN(r.payment_date)          AS first_payment_date,
           MAX(r.payment_date)          AS last_payment_date,
           MIN(CASE WHEN r.cumulative >= r.invoice_total - 0.005
                     AND (s.short_date IS NULL OR r.payment_date > s.short_date)
                    THEN r.payment_date END) AS paid_date
    FROM running r
    JOIN last_short s ON s.invoice_uid = r.invoice_uid
    GROUP BY r.invoice_uid
)
SELECT
    i.invoice_uid AS InvoiceKey,
    i.invoice_id AS InvoiceID,
    i.invoice_number AS InvoiceNumber,
    COALESCE(p.ProjectKey, xp.ProjectKey, 'UNMATCHED') AS ProjectKey,
    i.sage_project_id                   AS SageJobNumber,
    i.job_name                          AS SageJobName,
    i.invoice_date                      AS SentDate,
    i.due_date                          AS DueDate,
    CASE WHEN i.invoice_date IS NULL THEN NULL
         ELSE make_date(year(i.invoice_date), month(i.invoice_date), 1) END AS MonthStart,
    TRIM(i.description)                 AS Description,
    i.billing_period                    AS BillingPeriod,
    CASE WHEN i.status_code = 5 THEN 0 ELSE i.invoice_total END   AS Amount,
    CASE WHEN i.status_code = 5 THEN 0 ELSE i.amount_paid END     AS AmountPaid,
    CASE WHEN i.status_code = 5 THEN 0 ELSE i.invoice_balance END AS Balance,
    CASE WHEN i.status_code = 5 THEN NULL
         WHEN i.invoice_balance IS NULL THEN NULL
         WHEN i.invoice_balance = 0 THEN TRUE ELSE FALSE END AS IsPaid,
    COALESCE(i.status_code = 5, FALSE)  AS IsVoid,
    CASE WHEN i.status_code = 5 THEN i.invoice_total END AS VoidedAmount,
    CASE i.status_code WHEN 1 THEN 'Open' WHEN 2 THEN 'Review' WHEN 3 THEN 'Dispute'
                       WHEN 4 THEN 'Paid' WHEN 5 THEN 'Void' END AS SageStatus,
    -- Receipts, from sv_ar_payments. PaymentsReceived is NULL when there are none, so an
    -- invoice with no receipt rows is distinguishable from one whose receipts net to 0.
    -- A void is not a paid invoice: its receipts (if any) are not its payment history.
    CASE WHEN i.status_code = 5 THEN NULL ELSE pm.payments_received END  AS PaymentsReceived,
    CASE WHEN i.status_code = 5 THEN NULL ELSE pm.first_payment_date END AS FirstPaymentDate,
    CASE WHEN i.status_code = 5 THEN NULL ELSE pm.last_payment_date END  AS LastPaymentDate,
    CASE WHEN i.status_code = 5 THEN NULL ELSE pm.paid_date END          AS PaidDate,
    -- The workbook's DELTA column: sent to PAID. Drives [Avg Days To Payment].
    CASE WHEN i.invoice_date IS NULL OR pm.paid_date IS NULL OR i.status_code = 5 THEN NULL
         ELSE datediff(pm.paid_date, i.invoice_date) END AS DaysToPayment,
    -- Days from invoice to due date. Terms, NOT payment: never a stand-in for DaysToPayment.
    CASE WHEN i.invoice_date IS NULL OR i.due_date IS NULL THEN NULL
         ELSE datediff(i.due_date, i.invoice_date) END AS DaysToDue,
    -- Data-quality flag: an AR row whose job does not resolve to a project. Surfaced on
    -- the diagnostics page rather than dropped, which is how the Excel's defects survived.
    CASE WHEN p.ProjectKey IS NULL AND xp.ProjectKey IS NULL THEN TRUE ELSE FALSE END AS HasUnmatchedProject
FROM sv_ar_invoices i
LEFT JOIN dim_Project p ON i.sage_project_id = p.SageJobNumber
LEFT JOIN extra_job xp ON xp.SageJobNumber = i.sage_project_id
LEFT JOIN payments pm ON pm.invoice_uid = i.invoice_uid;
