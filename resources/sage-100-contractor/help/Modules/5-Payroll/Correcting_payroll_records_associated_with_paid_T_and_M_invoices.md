<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/5-Payroll/Correcting_payroll_records_associated_with_paid_T_and_M_invoices.htm (Sage 100 Contractor help v20.5) -->

### Correcting payroll records associated with paid T and M invoices

Completing this task requires that you complete five procedures:

- Part A—Reverse the payment
- Part B—Void the T&M invoice
- Part C—Void and re-create the payroll record
- Part D—Recompute and post the T&M invoice
- Part E—Repay the T&M invoice in the **3-3-1 Cash Receipts** window

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Part A—To reverse the cash receipt payment.](javascript:void(0);)

|  | 1 | Open **3-3-1 Cash Receipts**. |
|---|---|---|

|  | 2 | Do the following: |
|---|---|---|

|  | a | In the **Account** box, enter the ledger account number for the cash account. |
|---|---|---|

|  | b | In the **Deposit#** box, enter the deposit transaction number. |
|---|---|---|

|  | c | In the **Date** box, enter the deposit date. |
|---|---|---|

|  | d | In the **Description** box, enter a brief statement about the transaction. |
|---|---|---|

|  | 3 | Do one of the following: |
|---|---|---|

- In the **Client** box, enter the client number.
- In the **Job** box, enter the job number.

|  | 4 | Do one of the following: |
|---|---|---|

- Click the **Contract Invoices** tab.
- Click the **Service Invoices** tab.

|  | 5 | Consider the following: |
|---|---|---|

- If the invoices are partially paid, select the **Open** only option.
- If the invoices are completely paid, select the **Paid only** option.
- If you have a combination of paid and partially paid invoices, select the **All**option.

|  | 6 | Click the **Display** button. |
|---|---|---|

|  | 7 | In the grid, do the following: |
|---|---|---|

1. In the **Paid (Cash)** cell, enter the amount as a negative amount.
2. In the **Discount** cell, enter the discount amount, if any, as a negative amount.

|  | 8 | Repeat step 7 for each payment you want to reverse. |
|---|---|---|

|  | 9 | On the **File** menu, click **Save**. |
|---|---|---|

> Tip: When you reverse a payment made to an invoice with status **4-Paid**, Sage 100 Contractor changes the status to **1-Open**.

|  | 10 | After reversing all payments made to an invoice, you can void the invoice. |
|---|---|---|

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Part B—Void the T&M invoice](javascript:void(0);)

|  | 1 | Open **3-2 Receivable Invoices/Credits**. |
|---|---|---|

|  | 2 | Display the invoice that you need to void. |
|---|---|---|

|  | 3 | From the **Edit** menu, select **Void Invoice**. |
|---|---|---|

|  | 4 | To the message, **This invoice was created from Time and Materials Billing. Are you sure you want to continue?** click **Yes**. |
|---|---|---|

> Tip: For more information, see the topic, Voiding time and materials invoices.

|  | 5 | To the message, **You are about to void this record. Do you want to continue?** click **Yes**. |
|---|---|---|

|  | 6 | To the message, **Do you want to reset 'Billing Status' to Open on the job cost records?** click **Yes**. |
|---|---|---|

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Part C—Void and re-create the payroll record.](javascript:void(0);)

|  | 1 | Open **5-2-2 Payroll Records**. |
|---|---|---|

|  | 2 | Display the record you need to correct. |
|---|---|---|

|  | 3 | From the **Edit** menu, select **Copy Payroll Record**. |
|---|---|---|

|  | 4 | From the **Edit** menu, select **Void Payroll Record**. |
|---|---|---|

|  | 5 | To the message, **You are about to void this record. Do you want to continue?** click **Yes**. |
|---|---|---|

|  | 6 | To the message, **Ledger transaction found for this payroll record. Do you want to have the existing transaction altered to 'Void'?** click **Yes**. |
|---|---|---|

> Tip: Answer **No** to post a new, reversing transaction.

|  | 7 | To the message, **Payroll record, cost records, and ledger transaction have all been voided**, click **OK**. |
|---|---|---|

|  | 8 | From the **Edit**menu, select **Paste Payroll Record**. |
|---|---|---|

|  | 9 | Make the necessary changes to the payroll record. |
|---|---|---|

|  | 10 | From the **File** menu, select **Save**. |
|---|---|---|

|  | 11 | Recompute and re-post the payroll as usual. |
|---|---|---|

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Part D—Recompute and re-post the T&M invoice](javascript:void(0);)

|  | 1 | Open **3-10-2 Compute T&M Invoices**. |
|---|---|---|

|  | 2 | In the **Invoice Date** box, enter the date you want to assign the invoices. |
|---|---|---|

|  | 3 | Select the criteria to choose the invoices you want to calculate. |
|---|---|---|

|  | 4 | Click **Compute**. |
|---|---|---|

|  | 5 | Next, you have to post time and materials invoices: |
|---|---|---|

1. Open **3-10-4 Post T&M Invoices**.
2. Select the invoices you want to post.
3. Click **Post**.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Part E—Repay the T&M invoice using the 3-3-1 Cash Receipts window](javascript:void(0);)

To enter a payment against an invoice:

|  | 1 | Open **3-3-1 Cash Receipts**. |
|---|---|---|

|  | 2 | Do the following: |
|---|---|---|

1. In the **Account** text box, enter the ledger account number for the cash account.
2. In the **Deposit#** text box, enter the deposit number.
3. In the **Date** text box, enter the deposit date.
4. In the **Description** text box, enter a brief statement about the transaction.

|  | 3 | Do one of the following: |
|---|---|---|

- In the **Client** text box, enter the client number.
- In the **Job** text box, enter the job number.

|  | 4 | Do one of the following: |
|---|---|---|

- Click the **Contract Invoices** tab.
- Click the **Service Invoices** tab.
- Click the **Display** button.

|  | 5 | In the grid: |
|---|---|---|

1. In the **Paid (Cash)** cell, enter the total amount received.
2. Do not include any discount or credit in this amount.
   
   1. If you are using discounts, in the **Disc Available** cell, enter the amount of the discount.
   2. If you are not using discounts, skip step b.

> Important! To enter an overpayment for an invoice, the total of the **Paid (Cash)** and Discount cells must equal the amount in the **Balance** text box. Then in the **Overpayment** cell, enter the amount paid in addition to the **invoice**payment, not the total amount.

|  | 6 | Repeat step 5 for each invoice you want to pay. |
|---|---|---|

|  | 7 | On the **File** menu, click **Save**. |
|---|---|---|

Tip: If you do not enter a job number or client number, Sage 100 Contractor displays all invoices.

| Links to more information . . . [Voiding payroll records](Voiding_payroll_records.md) [Entering payroll advances](Entering_payroll_advances.md) [Entering timecards](Entering_timecards.md) |
|---|
