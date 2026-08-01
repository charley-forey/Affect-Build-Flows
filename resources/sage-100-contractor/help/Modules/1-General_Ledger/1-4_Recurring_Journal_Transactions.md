<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/1-General_Ledger/1-4_Recurring_Journal_Transactions.htm (Sage 100 Contractor help v20.5) -->

## 1-4 Recurring Journal Transactions

You can set up any transaction that you post on a regular basis for the same amount as a recurring transaction. You can even set a reminder to prompt users in a specific security group when it is time to post recurring transactions.

Note: You control the posting of recurring transactions to the general ledger. Sage 100 Contractor does not automatically post recurring transactions.

Use the posting date to determine when to post a recurring transaction. After you post a recurring transaction, Sage 100 Contractor advances the posting date based on the cycle assigned to the transaction.

The transaction date does not control or affect the period to which you post the transaction. If you need to post a recurring transaction to a different period, change the posting period.

### Examples of recurring transactions

You can set up recurring transactions for identical amounts that you post on a regular basis, such as rent. or expense allocations.

| Transaction | Description |
|---|---|
| Recurring Payments | Regular payments such as rents, vehicle insurance, janitorial services, and subscriptions or dues. |
| Pre-paid Expenses | Payments you need to expense over several periods, rather than a single period, such as a quarterly vehicle insurance payment that you need to expense monthly. Create a recurring transaction to post the monthly expense rate, rather than the quarterly rate. |
| Depreciation | You can depreciate items such as office equipment on a monthly basis. After obtaining the annual depreciated amount from your company accountant, calculate the monthly depreciation. Then set up a transaction to post the monthly depreciation. You can depreciate the value of equipment used on a job in the **8-6 Equipment Depreciation** window. |

Note: You cannot set up recurring transactions for direct expenses, equipment expenses, inventory, or service receivables.

### Setting up recurring journal transactions

You can set up a recurring transaction for printing a cheque. In the **Trans#** box, type four zeros (0000). In the **Vendor#** box enter the vendor number for whom you are printing the cheque. Sage 100 Contractor increases the **Vendor T5018** balance by the total amount of the cheque. Then, in the **Account** column, indicate the chequing account number.

After posting the transaction, you can print the cheque from the **1-1 Cheques/Bank Charges** window with other cheques. As you have posted the transaction, do not enter it in **1-1 Cheques/Bank Charges**.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To set up a recurring journal transaction](javascript:void(0);)

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

### Setting up automatic reminders to post recurring transactions

When a user logs on to a company, Sage 100 Contractor checks the posting dates of recurring transactions. If there are transactions to post and the user is part of the **Recur. Trans. Group**, Sage 100 Contractor prompts you with a reminder. You can set up reminders for recurring transactions by following this procedure.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To set up reminders for recurring transactions](javascript:void(0);)

|  | 1 | Open **7-1 Company Information**. |
|---|---|---|

|  | 2 | In the **Company Name** box, enter the company name. |
|---|---|---|

|  | 3 | In the **Recur. Trans. Group** (Recurring Transactions Group) box, select the security group responsible for posting recurring transactions. |
|---|---|---|

Important! If you want to post to a different period, you must change the posting period. [How?](Changing_posting_periods.md)

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To post a single recurring transaction](javascript:void(0);)

|  | 1 | Open **1-4 Recurring Journal Transactions**. |
|---|---|---|

|  | 2 | Select the transaction. |
|---|---|---|

|  | 3 | On the **Post** menu, click **This Transaction Only.** |
|---|---|---|

To post a group of transactions, use a cutoff date. Sage 100 Contractor posts all transactions through the indicated date.

Important! If you want to post to a different period, you must change the posting period. [How?](Changing_posting_periods.md)

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To post a group of recurring transactions](javascript:void(0);)

|  | 1 | Open **1-4 Recurring Journal Transactions**. |
|---|---|---|

|  | 2 | On the **Post** menu, click **Multiple Transactions**. |
|---|---|---|

|  | 3 | The **Posting Cutoff** window appears. |
|---|---|---|

|  | 4 | In the **Cutoff Date** box, enter the cutoff date, and then click **OK**. |
|---|---|---|
