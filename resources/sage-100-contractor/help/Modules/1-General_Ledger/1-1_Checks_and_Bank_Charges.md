<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/1-General_Ledger/1-1_Checks_and_Bank_Charges.htm (Sage 100 Contractor help v20.5) -->

## 1-1 Cheques and Bank Charges

### About cheques and bank charges

Using **1-1 Cheques/Bank Charges**, you can produce general ledgercheques, transfer funds between cash accounts, enter bank charges, and cancel cheque numbers. When entering a cheque, you can break down costs by creating separate line items, and you can even post each item to a different ledger account. To pay a vendor, however, you create the cheque using **[4-3 Vendor Payments](../4-Accounts_Payable/Printing_vendor_payment_checks.md)**.

Suppose you want to issue a cheque to a telephone company for last month’s bill. To indicate to Sage 100 Contractor that a cheque will be printed for the transaction, you type a placeholder consisting of four zeros (0000) in the **Cheques#** box. Then when selecting cheque records for printing, you indicate the cheque number at which you want to begin printing. As Sage 100 Contractor prints cheques, it substitutes the placeholder in the posted record with the appropriate cheque number.

You can also enter transactions that do not require printed cheques. For example, you might issue a hand written cheque and will not need to print a cheque. In this case, you enter the cheque number you issued in the **Cheques#**box.

In the grid, you can itemize the expenses and post them to different expense accounts. When you indicate a direct expense account, equipment expense account, or WIP account, Sage 100 Contractor requires you to create a job cost record in the Job Cost Distribution window. Job cost records are maintained in a separate database from the accounting data, and therefore do not impact the general ledger.

### Entering general ledger cheques

For reference, you can enter the purchase order number in the **Order#** box.

When you enter a vendor number in the **Vendor** box, Sage 100 Contractor increases the **Vendor****T5018** balance by the total amount of the cheque.

When entering a bank charge, use the bank’s transaction number as the cheque number. You can also use a dummy number that is outside the cheque number range, such as 99999, for all bank charges.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To enter a general ledger cheque](javascript:void(0);)

|  | 1 | Open **1-1 Cheques/Bank Charges**. |
|---|---|---|

|  | 2 | In the **Account#** box, enter the ledger account number for the chequing account |
|---|---|---|

|  | 3 | In the **Cheques#** box, type 0000. |
|---|---|---|

|  | a | When you print the cheque, Sage 100 Contractor assigns the cheque number to the record. |
|---|---|---|

|  | b | If you have already issued the cheque, enter the cheque number in the **Cheques#** box. |
|---|---|---|

|  | 4 | In the **Date** box, enter the transaction date of the cheque. |
|---|---|---|

|  | 5 | In the **Description** box, enter a brief statement about the transaction. |
|---|---|---|

|  | 6 | In the **Status** list, click the status of the entry. |
|---|---|---|

|  | 7 | In the grid, do the following: |
|---|---|---|

|  | a | In the **Description** cell, enter a brief statement about the item. |
|---|---|---|

|  | b | In the **Account** cell, enter the ledger account number. |
|---|---|---|

|  | c | In the **Subaccount** cell, enter the subsidiary account number. |
|---|---|---|

|  | d | In the **Debit Amount** cell, enter the amount. |
|---|---|---|

|  | 8 | Repeat step 7 for each item that you want to include in the cheque. |
|---|---|---|

|  | 9 | On the **File** menu, click **Save**. |
|---|---|---|

### Entering outstanding cheques or bank charges

When working with a bank charge, you can type Bank Charge in the **Cheques#** box on the **1-1 Cheques/Bank Charges** window. You can also type it as BCdd/mm/yyyy (where dd/mm/yyyy is the actual date of the bank charge). Sage 100 Contractor saves the information and displays the resulting transaction the **1-5 Bank Reconciliation** window with Bank Charge in the transaction number (**Trans#**) column in the cheques area.

Caution! Do not enter a vendor number. It would otherwise affect the **Vendor **T5018****balances. The **Vendor **T5018**** balances are set up later.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To enter outstanding cheques or bank charges](javascript:void(0);)

|  | 1 | Open **1-1 Cheques/Bank Charges**. |
|---|---|---|

|  | 2 | In the **Account#** box, enter the ledger account number for the bank account. |
|---|---|---|

|  | 3 | In the **Cheques#** box, enter the cheque number. |
|---|---|---|

|  | 4 | In the **Date** box, enter the transaction date of the cheque. |
|---|---|---|

|  | 5 | In the **Description** box, enter a brief statement about the transaction. |
|---|---|---|

|  | 6 | In the **Status** list, click **1-Open**. |
|---|---|---|

|  | 7 | In the grid, do the following: |
|---|---|---|

|  | a | In the **Description** cell, enter a brief statement about the item. |
|---|---|---|

|  | b | In the **Account** cell, enter the clearing account number. |
|---|---|---|

|  | c | In the **Debit Amount** cell, enter the amount. |
|---|---|---|

|  | 8 | Repeat step 7 for each item that you want to include in the cheque. |
|---|---|---|

|  | 9 | On the **File** menu, click **Save**. |
|---|---|---|

|  | 10 | Repeat steps 3–9 until you have entered all outstanding cheques for the account. |
|---|---|---|

### Setting the default ledger chequing account to a new account

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To set the default ledger chequing account to a new account:](javascript:void(0);)

|  | 1 | Open **1-1 Cheques/Bank Charges**. |
|---|---|---|

|  | 2 | In the **Account#** box, type the number of the chequing account that you want to set as the default. |
|---|---|---|

|  | 3 | Press the Enter key. |
|---|---|---|

|  | 4 | Click in the **Account #**box, and then press the F7 key. |
|---|---|---|

|  | 5 | On the **Field Properties Account#** window, verify that the account you want to be the default is in the **Default Entry to** box, and click **OK**. |
|---|---|---|

|  | 6 | Close **1-1 Cheques/Bank Charges**, and then open it again. |
|---|---|---|

|  | 7 | When the window opens, note that the **Account#** box defaults to the new account. |
|---|---|---|

### Printing general ledger cheques

You can print general ledger cheques from the **1-1 Cheques/Bank Charges** window; however, you must first complete the cheque entry process.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To print general ledger cheques](javascript:void(0);)

|  | 1 | Open **1-1 Cheques/Bank Charges**. |
|---|---|---|

|  | 2 | Click the **Print Records** button. **1-1 Report Printing** opens. |
|---|---|---|

|  | 3 | In the **Account** box, enter the account number, and click the **Print Records** button. |
|---|---|---|

|  | 4 | In the **Cheques Printing** window, enter a valid cheque number and a date. |
|---|---|---|

|  | 5 | In the confirmation box, click **OK**. |
|---|---|---|

|  | 6 | In the **Assign/Post Cheques** window, select **Assign Cheques Numbers**, and click **Continue**. |
|---|---|---|

The cheque prints.

### About reprinting cheques

Occasionally a cheque is misprinted or lost. Sage 100 Contractor provides an easy way to reprint cheques without having to enter a new record. You can recall a cheque record and reassign it a placeholder consisting of four zeros (0000) in the cheque number box or transaction number box. When you reprint the cheque, Sage 100 Contractor assigns the record the new cheque number.

You can reprint a general ledger cheque using a two-step process. First you locate the cheque you want to reprint in **1-3 Journal Transactions** and change its number. Then you print it from the **Report Printing** window.

Sage 100 Contractor automatically updates the existing ledger record and associated job cost/equipment records with the new cheque number when it assigns the new cheque number to the existing ledger record.

Important! When you reprint a general ledger cheque, the transaction record remains unchanged, but no record of the original cheque exists. To maintain an accurate cheque register, cancel the original cheque number. [How?](Cancelling_check_numbers.md)

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To reprint a general ledger cheque](javascript:void(0);)

|  | 1 | Open **1-3 Journal Transactions**, and select the cheque record that you want to reprint. |
|---|---|---|

|  | 2 | In the **Trans#** box, delete the original cheque number, and type 0000. |
|---|---|---|

|  | 3 | On the **File** menu, click **Save**. |
|---|---|---|

|  | 4 | Open **1-1 Cheques/Bank Charges**. |
|---|---|---|

|  | 5 | Click the **Print Records** button. **1-1 Report Printing** opens. |
|---|---|---|

|  | 6 | In the **Account** box, enter the account number, and click the **Print Records** button. |
|---|---|---|

|  | 7 | In the **Cheques Printing** window, enter a valid cheque number and a date. |
|---|---|---|

|  | 8 | In the confirmation box, click **OK**. |
|---|---|---|

|  | 9 | On the **Assign/Post Cheques** window, select **Assign Cheques Numbers**, and click **Continue**. |
|---|---|---|

The cheque prints.

### Cancelling cheque numbers

When you cancel a cheque number, Sage 100 Contractor creates a record for the cheque number. Suppose that you accidentally print an invoice on a few cheque forms. Because you cannot use the forms now, you have to cancel the cheque numbers.

Important! To cancel a series of cheque numbers, you must cancel each number through a separate transaction.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To cancel a cheque number](javascript:void(0);)

|  | 1 | Open **1-1 Cheques/Bank Charges**. |
|---|---|---|

|  | 2 | In the **Account#** box, enter the ledger account number for the chequing account. |
|---|---|---|

|  | 3 | In the **Cheques#** box, enter the cheque number you want to cancel. |
|---|---|---|

|  | 4 | In the **Date** box, enter the date. |
|---|---|---|

|  | 5 | In the **Description** box, enter a brief statement about the transaction. |
|---|---|---|

|  | 6 | In the **Status** list, click **3-Void**. |
|---|---|---|

|  | 7 | On the **File** menu, click **Save**. |
|---|---|---|

### About voiding cheques

Important! You cannot void a transaction in a different period than that in which it was originally posted.

When you create an accounts payable, general ledger, or equipment cheque and save it, Sage 100 Contractor posts the cheque to the general ledger. You cannot void these cheques in the **1-3 Journal Transactions** window unless the status is **1-Open**. When you do void a cheque, Sage 100 Contractor assigns the cheque status **3-Void** and adjusts the invoice and vendor balances accordingly. If the cheque was applied to an invoice and the invoice was closed, Sage 100 Contractor reopens the invoice and adjusts the balance to what is due. Best practices in accounting procedures require that you do not void transactions that have been processed by the bank. Therefore, it is not possible to void transactions with a status of **2-Cleared**.

After voiding all payments made to an invoice, you can void the invoice itself. Best practices in accounting procedures require that you do not void transactions that have been processed by the bank. Therefore, it is not possible to void transactions with a status of **2-Cleared**.

Important! You cannot void a transaction in a different period than that in which it was originally posted.

#### To void a cheque:

|  | 1 | Open **1-3 Journal Transactions**. |
|---|---|---|

|  | 2 | Using the data control, select the record of the cheque (**Trans#**) you want to void. |
|---|---|---|

|  | 3 | Verify that the **Status** is **1-Open**. cheques |
|---|---|---|

|  | 4 | If necessary, in the **Status** drop-down list, change the status to **1-Open**. |
|---|---|---|

|  | 5 | On the **Edit** menu, click **Void Transaction**. |
|---|---|---|

Payroll cheques are processed by Sage 100 Contractor differently from other types of cheques. Therefore, you need to void payroll cheques through the **5-2-2 Payroll Records** window. To void a payroll cheque, void the timecard record that Sage 100 Contractor used to create the cheque. This reverses the amounts applied to the employee quarterly totals and year-to-date totals, and voids the job costs.

### Voiding general ledger cheques from an archived year

The **Void Transaction** command on the **Edit** menu is not available for cash transactions posted to archived years. To maintain an audit trail, you must reverse transactions posted to archived years.

To reverse the general ledger cheque, you enter a reversing transaction, and then clear both the original cheque and the reversing transaction. This task is in two parts.

Note: Cheques and deposits from a prior year can also be cleared in the **1-5 Bank Reconciliation** window. For each item you want to clear, select the item, and then click the **Clear** button.

#### Part 1—Enter the reversing transaction:

|  | 1 | Open **1-2 Deposits and Interest**, and then from the **Edit** menu, choose **Period**. |
|---|---|---|

|  | 2 | In the **Posting Period** window, select the fiscal year, and then double-click **0-Prior Year**. |
|---|---|---|

|  | 3 | At the message verifying that you want to use this period, click **Yes**. |
|---|---|---|

|  | 4 | In the **Account#**box, enter the account from which the original cheque was drawn. |
|---|---|---|

|  | 5 | In the **Deposit#** box, enter the original cheque number. |
|---|---|---|

|  | 6 | In the **Date** box, enter the date of the original cheque. |
|---|---|---|

|  | 7 | In the **Description** box, enter a brief statement about the transaction. |
|---|---|---|

|  | 8 | In the grid, enter the following information: |
|---|---|---|

|  | a | In the **Account** column, enter the general ledger account that was debited in the original transaction. |
|---|---|---|

|  | b | In the **Credit Amount** column, enter the original amount of the cheque. |
|---|---|---|

|  | 9 | From the **File** menu, select **Save**. |
|---|---|---|

#### Part 2—Clear the original cheque and reversing transaction:

|  | 1 | Open **1-5 Bank Reconciliation**. |
|---|---|---|

|  | 2 | In the **Account#**box, enter the bank account number. |
|---|---|---|

|  | 3 | In the **Statement Cutoff Date** box, enter the date of the transactions. |
|---|---|---|

Note: The date of the reversing transaction should match the original cheque date.

|  | 4 | Click the **Display Items** button. |
|---|---|---|

|  | 5 | In the grid, select the original cheque and the reversing transaction and then click the **Clear** button. |
|---|---|---|

|  | 6 | From the **File** menu, select **Save**. |
|---|---|---|

### Finding and resolving unprinted cheques when closing the books

When there is a credit to an account in the cash range with a transaction number of 0000 when you are closing the books, Sage 100 Contractor displays a message stating that unprinted cheques were found.

Tip: This message is informational only. It does not stop you from closing your books; however, you should resolve the unprinted cheques issue.

#### To find and resolve unprinted cheques:

|  | 1 | Open **2-5 General Journals**. |
|---|---|---|

|  | 2 | Print the **2-5-21 General Journal** report with the following settings: |
|---|---|---|

|  | a | In the **Account**box, use the range for all cash accounts listed in **1-8 General Ledger Setup.** |
|---|---|---|

|  | b | In the **Trans#** box, select **Equal**, and type 0000. |
|---|---|---|

|  | c | In the **Credit** box, select **Greater or =**, and type $0.01. |
|---|---|---|

|  | 3 | If the transaction is an unprinted cheque, open **1-1 Cheques/Bank Charges** and click the **Print Records** button to print the cheque if desired. If you don’t need to print a cheque, open **1-3 Ledger Transactions**, and change the **Trans#** to anything other than 0000. |
|---|---|---|

Note: If it is a **Source 16-Payroll**, click on the **Go To Source** button to change the **Cheques#**. It's highly unusual that the cheque number would have been changed to 0000 unless the paycheque had to be reprinted immediately.

| [About cheques and bank charges](About_checks_and_bank_charges.md) [Entering general ledger cheques](Entering_general_ledger_checks.md) [Cancelling cheque numbers](Cancelling_check_numbers.md) [Entering outstanding cheques or bank charges](Entering_outstanding_checks_or_bank_charges.md) [Setting the default ledger chequing account to a new account](Setting_the_default_ledger_checking_account_to_a_new_account.md) [Working with Cheques](Working_with_Checks.md) |
|---|
