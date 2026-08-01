<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/3-Accounts_Receivable/Receivable_Invoices.htm (Sage 100 Contractor help v20.5) -->

## About receivable invoices

You use the **3-2 Receivable Invoices/Credits** window to enter transactions that affect receivable accounts. You can create invoices or credit invoices, track holdback, or view a history of payments for a specific invoice.

You can also create a simple invoice based on the percentage of work completed for the contract. This type of billing is suitable for subcontractors or small projects.

#### Overriding sales taxes

The Options menu in the **3-2 Receivable Invoices/Credits** window provide the following selections that let you override the sales taxes calculated for the current invoice:

- **Override Sales Tax Rates.** When you click this option, a separate window opens where you can enter a different tax rate for GST, PST, QST, or HST.
- **Override Sales Tax Amounts.** When you click this option, you can overwrite the tax amounts calculated in the grid. Caution! If you select this option, the program will not calculate any taxes for the current invoice.

#### About receivable invoice status

The status of a receivable record indicates its location in the process.

Important! You can change the status of records assigned status **1-Open**, **2-Review**, or **3-Dispute** to another of the first three status settings. However, you cannot assign status **4-Paid** or **5-Void**.

| Status | Description |
|---|---|
| 1-Open | Indicates a record posted to the general ledger. |
| 2-Review | Indicates the management or bookkeeping staff should review the record. |
| 3-Dispute | Indicates a record disputed by the client. |
| 4-Paid | Indicates a record paid in full. |
| 5-Void | Indicates a void record. |

Note: When an invoice or credit is fully paid, Sage 100 Contractor automatically assigns status **4-Paid**. If you void the record, Sage 100 Contractor automatically assigns status **5-Void**.

#### About receivable invoice types

| Type | Description |
|---|---|
| 1-Contract | Use type **1-Contract** when the invoice affects the billing for the contract. A receivable invoice assigned type **1-Contract** increases the job balance, and a credit invoice with this type reduces the job balance. |
| 2-Memo | Use type **2-Memo** when the invoice does not affect the job billing for the contract. For example, when you enter a job deposit as a credit invoice, assign it **2-Memo** so that the credit does not affect the invoiced to date amount. You can also use this type with bad debts. Entering a credit invoice assigned **2-Memo** does not reduce the invoiced to date amount, but clears the debt. |

#### Entering receivable invoices

Tips:

- You can review the record totals before saving the invoice or credit. On the **Options** menu, click **Calculate**.
- You can provide part numbers on an invoice. Sage 100 Contractor only includes the parts on the invoice, and does not use the part information elsewhere.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To enter a receivable invoice](javascript:void(0);)

|  | 1 | Open **3-2 Receivable Invoices/Credits**. |
|---|---|---|

|  | 2 | Do the following: |
|---|---|---|

|  | a | In the **Invoice#** text box, enter the invoice number. |
|---|---|---|

|  | b | In the **Date** text box, enter the date of the invoice. |
|---|---|---|

|  | c | In the **Job** text box, enter the job number. |
|---|---|---|

|  | d | If the job uses phases, enter the phase number in the **Phase** text box. |
|---|---|---|

|  | e | In the **Description** text box, enter a brief statement about the invoice. |
|---|---|---|

|  | f | In the **Due Date** text box, enter the invoice due date. |
|---|---|---|

|  | g | In the **Discount Date** text box, enter the due date by which you must receive payment for the client to receive the discount. |
|---|---|---|

|  | h | In the **Status** list, click the invoice status. |
|---|---|---|

|  | i | In the **Type** list, click the invoice type. The contract affects the invoiced balance when **Type 1-Contract** is selected. Type **2-Memo** does not affect the invoiced balance. |
|---|---|---|

|  | 3 | In the grid, for each item on the invoice: |
|---|---|---|

|  | a | In the **Description** cell, enter a brief statement about the item. |
|---|---|---|

|  | b | In the **Quantity** cell, enter the quantity of items. |
|---|---|---|

|  | c | In the **Price** cell, enter the price for a single item. |
|---|---|---|

|  | d | In the **Account** cell, enter the ledger account number. |
|---|---|---|

|  | 4 | In the **Discount** text box, enter the discount for early payment. |
|---|---|---|

|  | 5 | On the **File** menu, click **Save**. |
|---|---|---|

#### Voiding receivable invoices

If you discover an invoice was entered incorrectly, determine the best method to correct the error. For example, if the error is in the header information, you can edit the information contained in any of the text boxes, except in the **Job** text box, and re-save the record.

When the invoice contains an incorrect job number, ledger account, or amount, void the invoice and then re-enter it with the correct information. By voiding and re-entering the invoice, you create a clear audit trail.

There are also circumstances when you cannot void the original record. For example, you cannot void a credit invoice that has been applied in full, or an invoice posted to period 0. Because you cannot void these types of transactions, it is necessary to enter an adjusting invoice.

Before voiding an invoice, reverse all the payments posted to it. You can then enter the invoice correctly and reapply the payments.

You can void a receivable invoice with an assigned status of **1-Open**, **2-Review**, or **3-Dispute**.

When voiding an invoice that contains discretionary taxes, Sage 100 Contractor also voids the tax amount. If the voided invoice reduces the discretionary taxes below the billing maximum, Sage 100 Contractor continues to calculate the discretionary taxes until the tax maximum is met.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To void a receivable invoice](javascript:void(0);)

|  | 1 | Open **3-2 Receivable Invoices/Credits**. |
|---|---|---|

|  | 2 | Using the data control, select the record. |
|---|---|---|

|  | 3 | If an amount appears in the **Paid** text box, reverse the payments. [How?](Reversing_cash_receipts.md) |
|---|---|---|

|  | 4 | On the **Edit** menu, click **Void Invoice**. |
|---|---|---|

#### Creating invoices based on contract balances

You can create a receivable invoice for a job based on the amount of work completed. Using the original contract amount or the new contract amount and the amount you have invoiced to date, Sage 100 Contractor determines the balance remaining on the contract.

When you supply the percentage of the contract that is completed, Sage 100 Contractor computes the amount to bill. This method is similar to progress billing, but does not provide a detailed breakdown by cost code of the progress. Instead, the invoice contains a single line describing the percentage of work completed and the invoice amount. This method of billing is best suited for subcontractors.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To create an invoice based on the contract balance](javascript:void(0);)

|  | 1 | Open **3-2 Receivable Invoices/Credits**. |
|---|---|---|

|  | 2 | Enter the invoice. [How?](Entering_receivable_invoices.md) |
|---|---|---|

|  | 3 | On the **Options** menu, click **Contract Summary**. |
|---|---|---|

|  | 4 | Choose the type of invoice you want to create by selecting the **Percentage of Contract** or **Percentage of New Contract** option. |
|---|---|---|

|  | 5 | In the **Percent Complete** text box, enter the total amount of the contract that is completed. |
|---|---|---|

|  | 6 | The **Amount to Bill** text box displays the computed amount. You can edit both figures if necessary. |
|---|---|---|

|  | 7 | Click **OK**. |
|---|---|---|

Note: Sage 100 Contractor automatically increments the new contract amount as change orders are approved. The amount billed does not change, but the percent billed changes since it is determined from the new contract amount.

#### About receivable credits

Important! You cannot reverse a credit invoice after applying it to an invoice. If you apply a credit invoice to the wrong invoice, make adjusting invoice entries to correct the error.

Many situations could cause you to enter a credit invoice. Suppose a client provides a prepayment on a job, or overpays an invoice. In either case, it is necessary to reduce the accounts receivable.

When you save a credit invoice, Sage 100 Contractor reduces the job balance. However, the credit invoice retains status **1-Open** until you apply it against other invoices in the **3-3-1 Cash Receipts** window. After you have applied the credit balance to other invoices, Sage 100 Contractor assigns the credit invoice status **4-Paid**.

You can also apply a credit invoice to an invoice at the time you save the record. If the invoice is fully paid by means of the credit invoice, Sage 100 Contractor changes the status of the invoice to **4-Paid**. If the invoice still has a balance after applying the credit, the invoice status is not changed. Likewise, if the entire amount of the credit is applied, the status of the credit invoice changes to **4-Paid**. If a credit invoice still has a balance after applying it to an invoice, the status of the credit invoice remains unchanged. You can then apply the remaining credit invoice balance to other invoices in the **3-3-1 Cash Receipts** window.

#### Recalculating invoices or credits

After making changes, you can recalculate the new totals.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To recalculate an invoice or credit](javascript:void(0);)

To calculate the invoice balances, on the **Options** menu, click **Calculate**.

### Issuing refund cheques to customers

Situations arise where you might have to issue a refund cheque to a customer. This process progresses through several windows and multiple steps.

You begin the process to issue a refund in **3-2 Receivable Invoices**, then you work in **1-3 Journal Transactions**, **1-1 Cheques/ Bank Charges**,and you complete the process in **3-2 Receivable Invoices**.

Refunding a service receivables cheque uses a procedure similar to refunding an accounts receivable cheque.

#### To issue a refund cheque to a customer:

|  | 1 | Open **3-2 Receivable Invoices**, and create a type **2-Memo** accounts receivable invoice. In **11-2 Service Receivables**, create an invoice with a status of **1-Open**. [How?](Entering_receivable_invoices.md) |
|---|---|---|

|  | 2 | In the **Invoice#**box, enter 0000. |
|---|---|---|

|  | 3 | In the grid, in the **Quantity** column, type 1. |
|---|---|---|

|  | 4 | In the grid in the **Price** column, type the amount of the refund. |
|---|---|---|

|  | 5 | In the grid, use your chequing account as the offsetting account. |
|---|---|---|

Important! You must use transaction number 0000 in order to print the cheque. If you have recorded other journal transactions with the 0000 number and they are still in an open status, they will also print when you print the cheque.

|  | 6 | From the **File** menu, select **Save**. |
|---|---|---|

|  | 7 | From the **File** menu, select **Recall**. |
|---|---|---|

|  | 8 | Click **Go to Transaction** to open the **1-3 Journal Transactions** window for this invoice. |
|---|---|---|

|  | 9 | In the **Payee** box, enter the name of the customer. |
|---|---|---|

|  | 10 | From the **File** menu, select **Save**. |
|---|---|---|

|  | 11 | Open **1-1 Cheques/Bank Charges**. |
|---|---|---|

|  | 12 | From the **File** menu, select **Print**. |
|---|---|---|

|  | 13 | From the drop-down list in the first field on the first line, choose the appropriate report form. |
|---|---|---|

|  | 14 | In the blank field on the **Account** line, enter the appropriate chequing account number. |
|---|---|---|

Tip: If you need a list of accounts, double-click in the blank field.

|  | 15 | From the **File** menu, choose **Print**. |
|---|---|---|

|  | 16 | Verify that the cheque number and date are correct, and then click **OK** to print the cheque. |
|---|---|---|

|  | 17 | Open **3-2 Receivable Invoices**, change the number in the **Invoice#** box to match the printed cheque number. |
|---|---|---|

> Note: In **11-2 Service Receivables**, you cannot change the Invoice #.

|  | 18 | Create a credit to apply to the invoice created in step 1. |
|---|---|---|

### Managing old debts in accounts receivable

Sometimes there are situations where you have completely billed a contract, but you never receive full payment. You can post a credit invoice to the job, crediting the **Bad Debt Expense** account, for the uncollected amount. By not applying the credit to the open invoice, the credit invoice creates a $0 job balance but the invoice remains open. If you eventually collect the remaining contract balance, you can still post the payment to the invoice and void the credit.

At the fiscal year-end, you can close the job and remove it from the job database as long as it meets all the closing criteria.

### About accounts receivable payment history

Each time you post a payment to an invoice, Sage 100 Contractor creates a separate record of the payment. To review the individual payments made to a particular invoice, you can select the invoice and display its payment history.

When you void an accounts receivable payment, Sage 100 Contractor deletes the historical record of the payment and increases the invoice balance by the amount of the voided cheque.

Suppose you void a payment that applies to five invoices. Sage 100 Contractor deletes the record for payment in each of the related invoice histories and increases each invoice’s balance appropriately.

When you reverse a cash receipt, Sage 100 Contractor creates an additional record in the payment history for a negative amount.

You can use the payment history to reconstruct account balances for aging reports. To do this, first determine the fiscal period for which you want to recreate the aging. Then subtract the payments made after that fiscal period from the ending balance.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To view accounts receivable payment history for an invoice](javascript:void(0);)

|  | 1 | Open **3-2 Receivable Invoices/Credits**. |
|---|---|---|

|  | 2 | Select the invoice for which you want to view a payment history. |
|---|---|---|

|  | 3 | On the **Options** menu, click **Payment History**. |
|---|---|---|

| [Recalculating invoices or credits](Recalculating_invoices_or_credits.md) [About voiding receivable invoices](About_voiding_receivable_invoices.md) [Issuing refund cheques to customers](Issuing_refund_checks_to_customers.md) [Managing old debts in accounts receivable](Managing_old_debts_in_accounts_receivable.md) [About accounts receivable payment history](About_accounts_receivable_payment_history.md) |
|---|
