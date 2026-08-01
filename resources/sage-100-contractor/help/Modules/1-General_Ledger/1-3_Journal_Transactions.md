<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/1-General_Ledger/1-3_Journal_Transactions.htm (Sage 100 Contractor help v20.5) -->

## 1-3 Journal Transactions

Use the **1-3 Journal Transactions** window to review most accounting records. You can also enter adjusting journal entries and change the status of bank account records. You cannot, however, enter transactions or adjusting journal entries for the **Accounts Payable**, **Accounts Receivable**, **Service Receivables**, **Inventory**.

Best accounting practices require that you do not void transactions that have been processed by the bank. Therefore, it is not possible to void transactions with a status of **2-Cleared**.

Note: You can create a template for journal transactions from the **File** menu from an existing record or from scratch. [How?](../../Appendices/A-Sage_100_Contractor_Features/About_templates.md)

Instead of creating the transaction from scratch, you can begin with an existing Journal Transaction template. From **File**, select **Load/Delete Template**.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To enter a journal transaction](javascript:void(0);)

|  | 1 | Open **1-3 Journal Transactions.** |
|---|---|---|

|  | 2 | In the **Trans#** box, enter the transaction number. |
|---|---|---|

|  | 3 | In the **Date** box, enter the transaction date. |
|---|---|---|

|  | 4 | In the **Description** box, enter a brief statement about the line item. |
|---|---|---|

|  | 5 | In the **Status** list, click the record status. |
|---|---|---|

|  | 6 | In the grid, do the following: |
|---|---|---|

|  | a | In the **Description** cell, enter a brief statement about the line item. |
|---|---|---|

|  | b | In the **Account** cell, enter the ledger account you want. |
|---|---|---|

|  | c | In the **Subaccount** cell, enter the subsidiary account you want. |
|---|---|---|

|  | d | In the appropriate **Debit Amount** or **Credit Amount** cell, enter the amount. |
|---|---|---|

|  | 7 | Repeat step 6 for each item. |
|---|---|---|

|  | 8 | On the **File** menu, click **Save**. |
|---|---|---|

Tips:

- If the transaction references a purchase order number, enter it in the **Order#** box.
- When using over/under billing, you can reverse the entry in the next period. [How?](Reversing_a_transaction_in_the_next_period.md)

### Editing records in 1-3 Journal Transactions

Some fields are generally available to be edited and have a white background. Editing those fields and saving the record just updates the current record.

Some fields have a gray background and are generally not editable. However, in some instances, gray fields in **1-3 Journal Transactions** can be edited. In editing one of these gray background fields, a message displays advising that you are attempting to edit a posted transaction. To maintain the audit trail, saving an unlocked transaction creates a new transaction and voids the currently displayed transaction record. Inventory valuations are recalculated at current rates if applicable.

You can edit the locked field, such as the Account in the grid, by double-clicking on the field and clicking [**Yes**] to confirm unlocking the posted transaction.

Because the original record is voided, a new field was added in the header to all of the menus that shows the original record number. This allows you to view all the related original edited records which are now void.

Note: You must be a company administrator or have both save and void rights to unlock a posted transaction. If you save the transaction after unlocking fields, a new record is created without having to reenter all the information.

Important! To prevent data corruption, the ability to edit records in **1-3 Journal Transactions** is limited. You cannot change the record number.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To edit records in journal transactions](javascript:void(0);)

|  | 1 | Open **1-3 Journal Transactions**. |
|---|---|---|

|  | 2 | Using the data control, select the record. |
|---|---|---|

|  | 3 | Edit the record. |
|---|---|---|

|  | 4 | On the **File** menu, click **Save**. |
|---|---|---|

### Reversing a transaction in the next period

When entering a WIP adjustment in the **1-3 Journal Transactions** window, you can reverse the transaction in the following period. Doing so allows you to calculate the over or under billing without having to compensate for previous WIP adjustments.

When you select the **Reverse in Next Period** check box and post the transaction, Sage 100 Contractor simultaneously posts the transaction you entered and a reversing entry the next period.

To reverse a transaction in the next period, select the **Reverse in Next Period** check box.

Tip: If you receive a message stating that you cannot reverse the transaction in the next period because the next fiscal year is not available, open the **1-6 Period/FIscal Year Management** window, and then advance to period 12 of the current year. You can then post to period 1 of the next fiscal year.

### Changing the journal transaction record status

Important! You cannot change the status of a record to **3-Void**. Instead, you must void the record. [How?](Voiding_records_in_1-3_Journal_Transactions.md)

#### To change the record status:

|  | 1 | Open **1-3 Journal Transactions**. |
|---|---|---|

|  | 2 | Using the data control, select the record. |
|---|---|---|

|  | 3 | In the **Status** list, click **1-Open** or **2-Cleared**. |
|---|---|---|

|  | 4 | On the **File** menu, click **Save**. |
|---|---|---|

Tip: If you accidentally clear a cheque or deposit in **1-5 Bank Reconciliation**, you can change the status of the record from **2-Cleared**back to **1-Open**. After changing the status, the record appears in the **1-5 Bank Reconciliation** window.

### Voiding records in 1-3 Journal Transactions

Records in **1-3 Journal Transactions** can have a status of **1-Open** or **2-Cleared**.

Important!

- Best accounting practices require that you do not void transactions that have been processed by the bank. Therefore, it is not possible to void transactions with a status of **2-Cleared**.
- You can void an electronic receipt that has not been settled in Sage Exchange. If it has been settled and you proceed to void the transaction in Sage 100 Contractor, the program will attempt to create a credit transaction in Sage Exchange. If it cannot create the credit transaction, you must log on to Sage Exchange to correct the receipt manually. You can void records with a status of **1-Open**.

### About zeroing out the clearing account

Previously you entered the ledger account balances for the bank accounts, and those balances already reflect the impact of the outstanding transactions. Entering the outstanding bank transactions, however, affects the ledger balance. To clear the effect of the outstanding transactions, post a journal transaction for the net balance of the clearing account.

For example, suppose you are entering the outstanding transactions for a chequing account. You enter $500 in cheques and $750 in deposits. This is posted to the bank account and the cash clearing account. Because of the entries, the bank account has a net debit of $250 and the clearing account has a net credit balance of $250. Therefore, you post a journal transaction crediting the bank account and debiting the clearing account for $250.

Once you have zeroed out the clearing account, the items have no impact on the ledger account balances. You can then clear the open items when you next reconcile the account.

Important! We strongly recommend that you work on one account at a time from start to finish before moving on to the next account.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To zero out the clearing account](javascript:void(0);)

|  | 1 | Open **1-3 Journal Transactions**. |
|---|---|---|

|  | 2 | In the **Trans#** box, enter the transaction number. |
|---|---|---|

|  | 3 | In the **Date** box, enter the transaction date. |
|---|---|---|

|  | 4 | In the **Description** box, enter a brief statement. |
|---|---|---|

|  | 5 | In the **Status** list, click **2-Cleared**. |
|---|---|---|

|  | 6 | On a grid line, do the following for the bank account: |
|---|---|---|

|  | a | In the **Description** cell, enter a brief statement about the line item. |
|---|---|---|

|  | b | In the **Account** cell, enter the ledger account you want. |
|---|---|---|

|  | c | In the appropriate **Debit Amount** or **Credit Amount** cell, enter the amount. |
|---|---|---|

|  | 7 | Repeat step 7 for the clearing account. |
|---|---|---|

|  | 8 | On the **File** menu, click **Save**. |
|---|---|---|

|  | 9 | To verify that the clearing account has a zero balance, double-click an **Account** box to display a **Lookup** window. You can then locate the account and review its balance. |
|---|---|---|
