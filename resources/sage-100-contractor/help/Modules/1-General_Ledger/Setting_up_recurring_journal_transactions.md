<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/1-General_Ledger/Setting_up_recurring_journal_transactions.htm (Sage 100 Contractor help v20.5) -->

### Setting up recurring journal transactions

You can set up a recurring transaction for printing a cheque. In the **Trans#** box, type four zeros (0000). In the **Vendor#** box enter the vendor number for whom you are printing the cheque. Sage 100 Contractor increases the vendor T5018 balance by the total amount of the cheque. Then, in the **Account** column, indicate the chequing account number.

After posting the transaction, you can print the cheque from the **1-1 Cheques/Bank Charges** window with other cheques. As you have posted the transaction, do not enter it in **1-1 Cheques/Bank Charges**.

#### To set up a recurring journal transaction:

|  | 1 | Open **1-4 Recurring Journal Transactions**. |
|---|---|---|

|  | 2 | In the **Trans#** box, enter the transaction number. |
|---|---|---|

|  | 3 | In the **Next Date** box, enter the next date when the transaction needs to post. |
|---|---|---|

|  | 4 | In the **Cycle** box, enter the transaction cycle. In Sage 100 Contractor, a cycle is represented by ##DY (a number of days), ##MO (a number of months), and ##TH (a specified day every month). You replace the ## symbols with the number of days or months, or the day of the month for the processing cycle. For example:**30DY** means due every 30 days. **02MO** means due every two months.**25TH** means due on the 25th day of each month. Sage 100 Contractor displays the 25th of the month following the invoice date when you enter a new invoice for a vendor |
|---|---|---|

|  | 5 | In the **Description** box, enter a brief statement about the line item. |
|---|---|---|

|  | 6 | In the grid, for each item: |
|---|---|---|

|  | a | In the **Description** cell, enter a brief statement about the line item. |
|---|---|---|

|  | b | In the **Account** cell, enter the ledger account. |
|---|---|---|

|  | c | In the **Subaccount** cell, enter the subsidiary account. |
|---|---|---|

|  | d | Enter the amount in the appropriate **Debit Amount** or **Credit Amount** cell. |
|---|---|---|

|  | 7 | Click **File** > **Save**. |
|---|---|---|

| Links to more information . . . [About recurring transactions](About_recurring_journal_transactions.md) [Examples of recurring transactions](Examples_of_recurring_transactions.md) [Cycle symbols](../../Glossary/Glossary_-_cycle_symbols.md) |
|---|
