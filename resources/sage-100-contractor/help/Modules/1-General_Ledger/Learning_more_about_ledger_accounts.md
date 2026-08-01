<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/1-General_Ledger/Learning_more_about_ledger_accounts.htm (Sage 100 Contractor help v20.5) -->

### Learning more about ledger accounts

Ledger accounts are divided into two categories: permanent accounts (also called balance sheet accounts) and temporary accounts (also called profit and loss or income statements). Assets, liabilities, and equity accounts are referred to as permanent accounts. With permanent accounts, a period’s ending balance carries forward to become the beginning balance for the following period. Therefore, the period balances provide you with a running total over the course of a fiscal year.

The income and expense accounts are referred to as temporary accounts. With temporary accounts, the balance for each period is recorded separately. When a period closes, the following period starts with a zero balance. Temporary accounts only provide the activity for each individual period and not the year to date.

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

| Links to more information . . . [Selecting a pre-built general ledger structure](Selecting_pre-built_general_ledger_structure.md) [About subsidiary accounts](About_subsidiary_accounts.md) [Creating summary accounts](Creating_summary_accounts.md) [About account ranges](About_account_ranges.md) [About starting balances](About_starting_balances.md) |
|---|
