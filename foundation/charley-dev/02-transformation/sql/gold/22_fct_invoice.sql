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

CREATE OR REPLACE TABLE fct_Invoice AS
SELECT
    COALESCE(p.ProjectKey, 'UNMATCHED') AS ProjectKey,
    i.sage_project_id                   AS SageJobNumber,
    i.invoice_date                      AS SentDate,
    i.due_date                          AS DueDate,
    CASE WHEN i.invoice_date IS NULL THEN NULL
         ELSE make_date(year(i.invoice_date), month(i.invoice_date), 1) END AS MonthStart,
    TRIM(i.description)                 AS Description,
    i.billing_period                    AS BillingPeriod,
    i.invoice_total                     AS Amount,
    i.amount_paid                       AS AmountPaid,
    i.invoice_balance                   AS Balance,
    CASE WHEN i.invoice_balance IS NULL OR i.invoice_balance = 0 THEN TRUE ELSE FALSE END AS IsPaid,
    -- Days from invoice to due date. The workbook's DELTA column measures sent-to-PAID,
    -- but the paid DATE is not on the AR header - only the amount. Recording what the data
    -- actually supports, and flagging the gap, beats inventing a paid date.
    CASE WHEN i.invoice_date IS NULL OR i.due_date IS NULL THEN NULL
         ELSE datediff(i.due_date, i.invoice_date) END AS DaysToDue,
    -- Data-quality flag: an AR row whose job does not resolve to a project. Surfaced on
    -- the diagnostics page rather than dropped, which is how the Excel's defects survived.
    CASE WHEN p.ProjectKey IS NULL THEN TRUE ELSE FALSE END AS HasUnmatchedProject
FROM sv_ar_invoices i
LEFT JOIN dim_Project p ON i.sage_project_id = p.SageJobNumber;
