<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/1-General_Ledger/Creating_summary_accounts.htm (Sage 100 Contractor help v20.5) -->

### Creating summary accounts

Using summary accounts, you can combine multiple ledgers into a single ledger for generating a financial report in **2-8 Financial Reports**. When you generate a financial report, Sage 100 Contractor looks to the **Summary Account** box in each ledger. If Sage 100 Contractor finds an account number, it combines the balance of that account into the indicated summary account.

Suppose that you have four cash accounts: **1000-General Chequing**, **1002-Payroll Chequing**, **1011-Petty Cash**, and **1020-Savings**. To combine all the cash account balances into the General Chequing ledger account, enter **[1000]** in the **Summary Account** box of the **Payroll Chequing**, **Petty Cash**, and **Savings** ledger accounts.

You must always use the lowest account number of the ledgers you want to combine. In the above example, the cash accounts used **1000-General Chequing** for the summary account because it had the lowest account number.

#### To combine ledger accounts into a summary account:

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
