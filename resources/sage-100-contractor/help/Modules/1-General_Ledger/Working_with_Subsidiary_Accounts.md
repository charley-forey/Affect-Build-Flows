<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/1-General_Ledger/Working_with_Subsidiary_Accounts.htm (Sage 100 Contractor help v20.5) -->

### Working with Subsidiary Accounts

Using subsidiary accounts, you can arrange financial information into related categories under a single ledger account, providing quick access to specific information. A ledger account that uses subsidiary accounts is known as the controlling account. You use subsidiary accounts primarily with asset and liability accounts, but you can also use subsidiary accounts with income and expense accounts.

Note: You cannot create subsidiary accounts for cash accounts.

Suppose that you want to track telephone expenses. You can split the telephone account into subsidiary accounts such as **Basic Service**, **Long Distance**, **Cellular**, and **Paging**. The **Telephone** ledger account then provides you with the overall expenses as well as a breakdown of the expenses by the subsidiary accounts.

Sage 100 Contractor automatically sets up subsidiary accounts for accounts receivable, accounts payable, and service receivables using the job, vendor, and client numbers as the subsidiary account numbers. However, Sage 100 Contractor does not provide access to these subsidiary accounts through the **Ledger Accounts** window because you can view the subsidiary account balances in the **Job**, **Vendor**, and **Client** windows. Sage 100 Contractor also sets up subsidiary accounts for **Equipment Assets**, **Equipment Depreciation**, and **Equipment Loans** using the equipment numbers as the subsidiary account numbers. Similarly, you view the subsidiary account balances for equipment in the **Equipment** window.

Setting up subsidiary accounts takes careful planning. Like ledger accounts, you cannot change the subsidiary account number after posting a transaction to a subsidiary account. It is important to note that you can always add subsidiary accounts to an existing controlling account.

You cannot make a ledger account into a controlling account if that ledger account that has had any activity or carried a balance. You can, however, create a new controlling account, set up subsidiary accounts, and transfer the balance from the ledger account into the subsidiary accounts of the new controlling account.

### Creating subaccounts automatically

Subaccounts can be created automatically when you create and save a job in the **3-5 Jobs (Accounts Receivable)**window, when the job is specified for WIP posting. This will create the subaccounts with the same job number and name as the job.

To allow for the generation of subaccounts from **3-5 Jobs** for any given general ledger account, you must specify for each general ledger account that you want to activate this feature.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To set up automatic subaccount generation](javascript:void(0);)

|  | 1 | Open **1-7 General Ledger Accounts**. |
|---|---|---|

|  | 2 | Using the data control, select or specify the ledger account. |
|---|---|---|

|  | 3 | In the **Subsidiary** list, click **1-Subaccounts**. |
|---|---|---|

|  | 4 | Select **Job# as Subaccount#**. |
|---|---|---|

|  | 5 | Repeat steps 2–3 for all general ledger accounts that you want to activate this feature for. |
|---|---|---|

|  | 6 | Open **3-5 Jobs (Accounts Receivable)**. |
|---|---|---|

|  | 7 | Using the data control, select or create the job. |
|---|---|---|

|  | 8 | Complete any necessary data. |
|---|---|---|

|  | 9 | Select **Post expenses to WIP asset account**. |
|---|---|---|

|  | 10 | On the **File** menu, click **Save**. |
|---|---|---|

|  | 11 | A prompt appears listing all the general ledger accounts that you designated as controlling accounts. You have the option of automatically creating subaccounts under each of the displayed accounts. |
|---|---|---|

|  | 12 | Select **OK**. |
|---|---|---|

Tip: When creating subaccounts, either manually or automatically, it is critical to plan wisely before you make your designations.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To view subsidiary accounts](javascript:void(0);)

|  | 1 | Open **1-7 General Ledger Accounts**. |
|---|---|---|

|  | 2 | Select the ledger account. |
|---|---|---|

|  | 3 | Click the **Subaccount** button. |
|---|---|---|

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To delete a subaccount:](javascript:void(0);)

|  | 1 | Open **1-7 General Ledger Accounts**. |
|---|---|---|

|  | 2 | Using the data control, locate the ledger account with the subaccount you want to delete. |
|---|---|---|

|  | 3 | Ledger accounts with subaccounts display **1 – Subaccounts** in the **Subsidiary** box. |
|---|---|---|

|  | 4 | From the **Edit** menu, select **Delete Account**. |
|---|---|---|

|  | 5 | On the verify delete message, click **Yes**. |
|---|---|---|

### Transferring balances from ledger accounts to subsidiary accounts

Important! Before you can transfer the balance from a ledger account to a subsidiary account, you must create the new controlling account and subsidiary accounts or departments. [How?](Setting_up_controlling_ledger_accounts_and_subaccounts.md)

#### To transfer balances from a ledger account to a subsidiary account:

|  | 1 | Open **1-3 Journal Transactions**. |
|---|---|---|

|  | 2 | In the **Trans#** box, enter the transaction number. |
|---|---|---|

|  | 3 | In the **Date** box, enter the transaction date. |
|---|---|---|

|  | 4 | In the **Description** box, enter a brief statement about the transaction. |
|---|---|---|

|  | 5 | In the grid, create a line that clears the old ledger account’s balance: |
|---|---|---|

|  | a | In the **Description** cell, enter a brief statement about the line item. |
|---|---|---|

|  | b | In the **Account** cell, enter the ledger account you want to clear. |
|---|---|---|

|  | c | Enter the amount in the appropriate **Debit Amount** cell or **Credit Amount** cell. |
|---|---|---|

|  | 6 | In the grid, create as many lines as necessary to move the balance into the appropriate subsidiary accounts under the new controlling account: |
|---|---|---|

|  | a | In the **Description** cell, enter a brief statement about the line item. |
|---|---|---|

|  | b | In the **Account** cell, enter the controlling account. |
|---|---|---|

|  | c | In the **Subaccount** cell, enter the subsidiary account you want. |
|---|---|---|

|  | d | Enter the amount in the appropriate **Debit Amount** cell or **Credit Amount** cell. |
|---|---|---|

|  | 7 | On the **File** menu, click **Save**. |
|---|---|---|
