<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/1-General_Ledger/Learning_about_Ledger_and_Subsidiary_Accounts.htm (Sage 100 Contractor help v20.5) -->

### Learning about Ledger and Subsidiary Accounts

In the **1-7 General Ledger Accounts** window, you can view a summary of activity for an account broken down by fiscal period. As an aid to organizing the financial data, you can use subsidiary accounts or departments.

You can manually enter a budget for each ledger account that takes into consideration the activity of each period within the fiscal year. Over the course of the fiscal year, you can generate reports detailing the budget versus actual account activity. Sage 100 Contractor also stores period balances for the previous fiscal year. When you close the books at the fiscal year-end, Sage 100 Contractor transfers the period balances from the **This Year** column to the **Last Year** column.

Comparisons between the account activity of the current year and the budget or account activity for the prior year provide a valuable way for you to analyze the company finances. The comparisons enable you to create budgets with greater accuracy, determine areas in the company that are over or under budgeted, and compare projections to the actual activity.

Because the **1-7 General Ledger Accounts** window only displays account activity, you cannot enter adjusting entries in this window. If you need to correct a period balance, you can enter the transaction using the **1-3 Journal Transactions** window.

In ledger accounts, you can organize data using departments or subsidiary accounts. Departments allow you to group data across the income and expense accounts, whereas subsidiary accounts allow you to divide data under a single, controlling ledger account. Sage 100 Contractor also allows you to set up summary accounts, which allow you to combine ledger accounts for financial reports.

Ledger accounts are divided into two categories: permanent accounts (also called balance sheet accounts) and temporary accounts (also called profit and loss or income statements).

Asset, liability, and equity accounts are permanent accounts. With permanent accounts, a period’s ending balance carries forward to become the beginning balance for the following period. Therefore, the period balances provide you with a running total over the course of a fiscal year.

The income and expense accounts are temporary accounts. With temporary accounts, the balance for each period is recorded separately. When a period closes, the following period starts with a zero balance. Temporary accounts only provide the activity for each individual period and not the year to date.

When you choose a pre-built chart of accounts, Sage 100 Contractor creates the ledger accounts. You can then edit the ledgers to create the type of accounts needed. When you post the first transaction to a company’s books, Sage 100 Contractor locks the system of ledger account ranges. To change the account number for a ledger account after having posted a transaction to it, create a new ledger account manually and transfer the balance through an adjusting journal entry.

You can rename a ledger account at any time. Sage 100 Contractor uses the short name for **Picklists** and most accounting reports, and uses the long name for the **Balance Sheet**, **Financial Report**, and **Income Statement** reports.

**Subsidiary:**If an account uses departments or subsidiary accounts, the departments or subsidiary accounts must be set up before posting transactions. In the **Subsidiary** list, click departments or subsidiary accounts.

**Summary Account:**Using summary accounts, you can combine multiple ledgers into a single ledger for generating a financial report in **2-8 Financial Reports**. When you generate a financial report, Sage 100 Contractor looks to the **Summary Account** box in each ledger. If Sage 100 Contractor finds an account number, it combines the balance of that account into the indicated summary account. [How?](Creating_summary_accounts.md)

**Account Type:**Displays the account range to which an account belongs and whether the account maintains a debit or credit balance. Ledger accounts that fall within specific account ranges are assigned certain properties:

- Ledgers in the **Cash Accounts** range cannot use subsidiary accounts.
- When posting to **WIP Assets** or **Direct Expense** ranges, Sage 100 Contractor requires you to create job costs before posting transactions.
- When posting to equipment accounts, Sage 100 Contractor requires you to create equipment costs.

**Starting Balance:**Displays the account balance at the beginning of the fiscal year, and that balance does not change by posting transactions to period zero.

**Beginning Balance:**Displays the account balance at the beginning of the fiscal year. The beginning balance is adjusted to reflect any postings made to period zero. Temporary accounts start with a $0 balance, and permanent accounts carry forward the ending balance from the prior fiscal year.

**Ending Balance:**Displays the ending balance as it appears in period 12 for permanent accounts. It is important to note that with temporary accounts, Sage 100 Contractor displays the total of all period balances. Posting to period 0 changes the beginning balances of the active company, and changes the ending balances in the archived company.

Caution! Once set up and saved, you cannot delete a chart of accounts, and you cannot edit it after you have entered a transaction. Call Customer Support or your business partner if you need more information.

### About account ranges

You can set up the ranges for the ledger accounts. The **Account Range** boxes determine the overall range of accounts for the entire chart of accounts. If you are creating a chart of accounts manually, indicate the lowest and highest account numbers in the range. Then set the individual accounts ranges within the chart of accounts. The range for a chart of accounts usually begins with one (100, 1000, or 10,000) and ends with eight (800, 8000, or 80,000). You can create ledger accounts that use up to ten digits. The range of the largest chart of accounts that you can create is 1,000,000,000 to 9,999,999,999.

When an account is set up, its account number cannot exceed the range limit. Suppose the **Current Liabilities** range of accounts is from 200 to 249. You cannot create a current liability using an account number below 200 or above 249.

Note: You cannot use decimals in the account numbers.

### Designating ledger accounts to accept departments

After you determine that your company is going to use departments to track income and expenses, you must designate which ledger accounts will accept departments.

Important! Before you create departments, you must designate ledger accounts to accept departments.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To designate ledger accounts to accept departments:](javascript:void(0);)

|  | 1 | Open **1-7 General Ledger Accounts**. |
|---|---|---|

|  | 2 | Open the account that you want to designate to accept departments. |
|---|---|---|

|  | 3 | In the Subsidiary box drop-down menu, select **2-Departments** and then click **Save**. |
|---|---|---|

|  | 4 | Repeat steps 1 through 3 to designate other accounts. |
|---|---|---|

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To create a ledger account](javascript:void(0);)

|  | 1 | Open **1-7 General Ledger Accounts**. |
|---|---|---|

|  | 2 | In the data control box, enter the ledger account number. |
|---|---|---|

|  | 3 | In the **Short Name** box, enter a brief description of the ledger account. |
|---|---|---|

|  | 4 | If an account uses departments or subsidiary accounts, the departments or subsidiary accounts must be set up before posting transactions. In the **Subsidiary** list, click **1-Subaccounts** or **2-Departments**. |
|---|---|---|

|  | 5 | On the **File** menu, click **Save**. |
|---|---|---|

Tip: Summary accounts let you combine ledger accounts for reports.[How?](Setting_up_controlling_ledger_accounts_and_subaccounts.md)

### Creating summary accounts

Using summary accounts, you can combine multiple ledgers into a single ledger for generating a financial report in **2-8 Financial Reports**. When you generate a financial report, Sage 100 Contractor looks to the **Summary Account** box in each ledger. If Sage 100 Contractor finds an account number, it combines the balance of that account into the indicated summary account.

Suppose that you have four cash accounts: **1000-General Chequing**, **1002-Payroll Chequing**, **1011-Petty Cash**, and **1020-Savings**. To combine all the cash account balances into the General Chequing ledger account, enter **[1000]** in the **Summary Account** box of the **Payroll Chequing**, **Petty Cash**, and **Savings** ledger accounts.

You must always use the lowest account number of the ledgers you want to combine. In the above example, the cash accounts used **1000-General Chequing** for the summary account because it had the lowest account number.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To combine ledger accounts into a summary account](javascript:void(0);)

|  | 1 | Open **1-7 Ledger Accounts**, and select the account. |
|---|---|---|

|  | 2 | In the **Summary Account** box, enter the ledger account number to which you want to add the current account balance. |
|---|---|---|

|  | 3 | On the **File** menu, click **Save**. |
|---|---|---|

Tips:

- The **Financial Report** uses the long name of each account. Before printing the report, you can change the long name of each summary account to accurately represent the data.
- The **Financial Report** gives you the ability to produce a single report that combines two or more companies.
- If you produce summarized reports frequently, create accounts dedicated to this purpose. Dedicated summary accounts eliminate the need to rename summary accounts each time you produce a report.

### About controlling accounts

A controlling account is a ledger account in the general ledger that summarizes the balances for a group of similar subsidiary accounts. With specific, dedicated controlling accounts, the program uses the accounts you designate to automatically post certain transactions to the correct ledger accounts.

When you select a pre-built chart of accounts, Sage 100 Contractor assigns the account numbers to the ledger accounts. You can change the account numbers during setup; each account number must fall within the correct range.

Under **Controlling Accounts**, Sage 100 Contractor uses the accounts you designate to automatically post certain transactions to the correct ledger accounts. For example, when you post a receivable invoice, you do not need to supply the accounts receivable ledger account. After posting a transaction to the general ledger, Sage 100 Contractor locks the account numbers for the accounts under **Controlling Accounts**. The account numbers will appear shaded.

You can change the account numbers on the **Receivables**, **Payables**, **Equipment**, and **Inventory** tabs whether or not you have posted transactions. If you change the account number on the **Receivables**, **Payables** or **Equipment** tabs, you will have to move the balances to the new account through a journal transaction.

### Verifying the date and period

When you save a transaction, Sage 100 Contractor can compare the transaction date to the period to ensure you post to the correct period. If the transaction date does not fall under the correct posting period, Sage 100 Contractor provides a warning, but does not prevent posting the transaction.

To verify the date and period, in the **1-8 General Ledger Setup** window, select the **Verify Date/Period** check box.

### Adding ledger accounts to an existing account structure

When you first set up your account structure, you would typically use the pre-build chart of accounts. The pre-build chart of accounts may not have all the accounts that you need for your business needs; however, you can add ledger accounts to the your existing account structure.

#### To add a ledger account to an existing account structure:

|  | 1 | Open **1-7 General Ledger Accounts**, and click the data control drop-down arrow. |
|---|---|---|

|  | 2 | On the **Ledger Accounts** window, review the account numbers that are available in the **Current Liabilities** range. If you have three business credit cards by three different issuers, determine three account numbers to use. |
|---|---|---|

|  | 3 | Close the **Ledger Accounts** window, and in the data control box, enter a ledger account number. |
|---|---|---|

|  | 4 | In the **Short Name** and **Long Name** boxes, type names.<br>For example, for a bank issued credit card, you could type, “Bank name—VISA.” |
|---|---|---|

|  | 5 | Press Ctrl+S or **File** > **Save**. |
|---|---|---|

### Deleting ledger accounts

You cannot delete an account if it has a balance or any activity during the fiscal year.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To delete a ledger account](javascript:void(0);)

|  | 1 | Open **1-7 General Ledger Accounts**. |
|---|---|---|

|  | 2 | Using the data control, select the ledger account number. |
|---|---|---|

|  | 3 | On the **Edit** menu, click **Delete Account**. |
|---|---|---|
