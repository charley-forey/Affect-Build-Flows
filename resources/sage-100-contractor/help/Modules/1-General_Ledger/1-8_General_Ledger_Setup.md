<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/1-General_Ledger/1-8_General_Ledger_Setup.htm (Sage 100 Contractor help v20.5) -->

## 1-8 General Ledger Setup

One of the first tasks when creating a new company in Sage 100 Contractor is to set up the general ledger structure. When you select a pre-built ledger, Sage 100 Contractor creates the ledger accounts for you.

You can also set up the general ledger manually. If you choose to enter the account ranges, controlling accounts, and posting accounts manually, Sage 100 Contractor will not create the ledger accounts. You will then need to create each ledger account in the **1-7 General Ledger Accounts** window.

Note: Unless you have prior experience setting up general ledgers, it is a good idea to choose a pre-built chart of accounts.

### Accounting setup considerations

Before you begin to set up your general ledger and other parts of accounting, there are several things that you should consider. For example, what is your startup date? It is going to take days and perhaps a couple of weeks to set up your company, so you need to have a startup date for your company in Sage 100 Contractor. You also must know your company’s fiscal year-end. In addition, you’ll need to consider the amount of information that you plan to bring into Sage 100 Contractor and its level of detail.

Here is a list of suggested information:

- **Balance sheet and income statement as of now.**If it’s currently mid-year, you have to merge the income statement from Sage 100 Contractor with the prior system for year-to-date reporting.
- **Balance sheet as of beginning of fiscal year and year-to-date activity as of Sage 100 Contractor start date.**You do not need month-by-month income statements, and you do not need prior year history.
- **Balance sheet as of the beginning of the fiscal year and activity for each month.**You do not need details. All detailed information must come from your prior system.
- **Balance sheet as of beginning of fiscal year and all transactions.**Starting up your accounting this way requires a lot of work unless only a few hundred entries need to be made.

In addition, you need the following information:

- A chart of accounts
- Listing of open accounts payable invoices
- Listing of accounts receivable invoices (including fully paid) for jobs that are in progress
- Job information: names, clients, and addresses
- Contract amounts
- Payroll information regarding employee balances, unions, company deductions, local taxes, and so forth.

Caution! Once you have set up and saved a chart of accounts, you cannot delete it, and you cannot edit it after you have entered a transaction. Call Customer Support or your business partner if you need more information.

### Pre-built chart of accounts

When you select the pre-built chart of accounts, Sage 100 Contractor automatically sets up the account ranges, controlling account numbers, posting account numbers, and then creates the ledger accounts. You can then modify the ledger setup to meet your particular needs. However, you will then need to edit the ledger accounts to match any changes made in the **1-8 General Ledger Setup** window.

You can select from four different pre-built charts of accounts:

- General Contractor Accounts (Four-Digit or Five-Digit)
- Subcontractor Accounts (Four-Digit or Five-Digit)
- Home Builder Accounts
- Remodeler Accounts

After setting up the chart of accounts, you can edit account numbers, delete unnecessary accounts, and set up controlling accounts for subsidiary accounts or departments in the **1-7 Ledger Accounts** window. If you change a controlling or posting account number in **1-8 General Ledger Setup**, you must also change the ledger account number.

Caution! Once you have set up and saved a chart of accounts, you cannot delete it, and you cannot edit it after you have entered a transaction. Call Customer Support or your business partner if you need more information.

### Selecting pre-built general ledger structure

When you create a new company in Sage 100 Contractor, you must set up a minimum number of items in addition to selecting a chart of accounts. You must also set program defaults for the following:

- Date for the **Fiscal Year End**.
- Set the **Current Period**, which is the program default posting period.
- Select an inventory **Valuation Method** (if you have the Inventory add-on module).

Important! When you create a new company and set up accounting, you must set the program default **Current Period**. After that initial setup, you can only change the **Current Period** using **1-6 Period/Fiscal Year Management** > **Change Period**. [How?](Changing_posting_periods.md)

#### To select a pre-built general ledger structure:

|  | 1 | Open **1-8 General Ledger Setup**. |
|---|---|---|

|  | 2 | On the **Options** menu, select one of the four pre-built chart of accounts. |
|---|---|---|

|  | 3 | Modify the account ranges. |
|---|---|---|

Important! You must make any changes to the account structure or to ledger accounts before posting transactions to the general ledger.

|  | 4 | In the **Fiscal Year End** box, enter the date of the fiscal year-end. |
|---|---|---|

|  | 5 | Do one of the following: |
|---|---|---|

- To begin entering transactions for the current fiscal year, enter the number of the current period in the **Current Period** box.
- To enter a few startup transactions, set the current period in the **Current Period** box. You can change the period in the window of entry for individual transaction records without changing the programs default for the current posting period.
- To enter a large number of startup transactions, type 0 in the **Current Period** box. Then after entering the startup transactions, enter the current accounting period in the **Current Period** box using **1-6 Period/Fiscal Year Management**.

|  | 6 | On the **File** menu, click **Save**. |
|---|---|---|

Tip: After selecting an account structure, print the entire chart of accounts from **2-7 Chart of Accounts**. Review the accounts and determine which accounts you want to edit or delete before you enter any transactions.

### About posting periods

Based on the fiscal year-end date in the **1-8 General Ledger Setup** window, Sage 100 Contractor determines the current default posting period, which is used program-wide. The **Current Period** in **1-8 General Ledger Setup** corresponds to the **Change Period** in **1-6 Period/Fiscal Year Management** > **Change Period**.

Note: When you create a new company, you must set the program default **Current Period**. After the initial setup, you can only change the **Current Period** using **1-6 Period/Fiscal Year Management** > **Change Period**. When you create a new company from existing company data, the new company's default posting period is set to the same posting period as the existing company. If you want to change the default posting period, you can only change it using **1-6 Period/Fiscal Year Management** > **Change Period**. [How?](Changing_posting_periods.md)

In any accounting transactions window, such as **4-2 Payable Invoice/Credits**, you can, if necessary, post individual transaction records to a different posting period. The following bullet points describe some of the features related to posting periods:

Accounting transaction windows contain a **Change the posting period** button that displays the posting period to which you are posting transactions. By changing the posting period, you can post transactions to the specified period until you change the period again or close the window. When the window opens again, the posting period is set to the current default posting period.

Users at different workstations can work in the same window and post to different periods. For example, while Andy and Melissa are entering invoices in the **Accounts Payable Invoices** window, Andy finds a few invoices that need posting to a previous period. While Melissa continues entering invoices in the current fiscal period, Andy can change the fiscal period and enter those invoices.

When you change the posting period to something other than the default current posting period, Sage 100 Contractor changes the color of the **Posting Period** button to yellow.

At the end of the period, open **1-6 Period/Fiscal Year Management** > **Change Period** and advance the current default posting period to the next one.

When advancing to the next posting period, the program performs a complete audit of the books. If you discover audit errors, you can view them and possibly repair the ledger balances at that time rather than at the end of the fiscal year.

Important! We strongly recommend that you recalculate balances to repair discrepancies if they are discovered during audits at the end of each posting period. Repairing audit errors as you advance to the next posting period is much more efficient than waiting until the year-end close to repair a year’s worth of audit errors. [How?](About_the_Recalculate_Balances_window_and_repairing_the_balances.md)

You can restrict users from posting transactions to previous or future periods. [How?](Locking_access_to_posting_periods.md)

If you have an archive from the previous year, you can simultaneously post transactions to period 0 of the current year and period 12 in the archive.

When using Sage 100 Contractor across a network, changing the current period using **1-6 Period/Fiscal Year Management** > **Change Period** affects all workstations that access Sage 100 Contractor.

### About starting balances

You can enter the starting balances for asset and liability accounts by posting a journal transaction—usually to period zero. As journal transactions can contain up to 999 lines, it is possible to enter most starting balances in a single journal transaction. Enter each account balance on a separate line.

Larger companies may not be able to enter the balances in one transaction. If you need to enter two journal transactions, use a clearing account to create a balanced entry.

At the end of the first transaction, enter the clearing account number and the amount necessary to balance the transaction. In the second journal transaction, finish entering the starting balances. Then at the end of the second transaction, enter the clearing account number and the amount necessary to balance the transaction. After you complete the entry of the starting balances, the clearing account returns to a zero balance.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To enter starting balances](javascript:void(0);)

|  | 1 | Open **1-3 Journal Transactions**. |
|---|---|---|

|  | 2 | On the **Edit** menu, click **Period**, and then select period **0**. |
|---|---|---|

|  | 3 | In the **Trans#** box, enter the transaction number. |
|---|---|---|

|  | 4 | In the **Date** box, enter the transaction date. |
|---|---|---|

|  | 5 | In the **Description** box, type Starting balances. |
|---|---|---|

|  | 6 | In the **Status** list, click **1-Open**. |
|---|---|---|

|  | 7 | In the grid, do the following: |
|---|---|---|

|  | a | In the **Description** cell, enter a brief statement about the line item. |
|---|---|---|

|  | b | In the **Account** cell, enter the ledger account you want. |
|---|---|---|

|  | c | In the **Subaccount** cell, enter the subsidiary account you want. |
|---|---|---|

|  | d | Enter the amount in the appropriate **Debit Amount** cell or **Credit Amount** cell. |
|---|---|---|

|  | 8 | Repeat step 7 for each account. |
|---|---|---|

|  | 9 | On the **File** menu, click **Save**. |
|---|---|---|

### Methods for entering financial activity for the current year

After you have entered the starting balances, enter the net activity of the ledger accounts for the current year. It is important to note that you cannot directly enter the startup balances for the dedicated ledger accounts: **Accounts Receivable**, **Accounts Payable**, **Service Receivables**, and **Inventory**. [How?](About_dedicated_accounts.md)

You can choose from four methods for entering the net activity. Entering the current activity for ledger accounts is nearly identical to entering the starting balances. Remember to adjust the posting period as necessary, and provide a description of what is reflected in the period balances.

Each successive method provides more detail for reports than the previous method and requires more time to enter data. Read each of the methods thoroughly before deciding which to use. Except where noted, you must first enter the starting balances of all the ledger accounts.

#### Method 1

When you post the starting balances, include all the period activity in the beginning balance. Post a single journal transaction to the period before the current posting period. Suppose you are setting up a new company during period 2. The net activity for period 1 is added to the starting balances. In the journal transaction, enter the total for each ledger account (beginning balance + period one net activity) and post the transaction to the end of period 1.

Method 1 is best suited for use near the start of a fiscal year. The method does not include the entry of historical information. It is not recommended for use during the middle of the fiscal year.

#### Method 2

Post the starting balances to period 0; then post a journal transaction that contains the net activity for each ledger account during the current fiscal year. Post the transaction to the period before the current posting period. Suppose you are setting up during period 7. Create a journal transaction that contains the net activity for each account through the end of period 6. Then post the journal transaction to the end of period 6.

Method 2 provides data for a Year-to-Date Income Statement, and lets you view the entire activity for the year, but does not provide data for reports in periods before the setup.

When you close the books at the fiscal year-end, the balances roll over to the **Last Year** column in the **Ledger Accounts** window. This method does not set up individual period balances, so the period balances do not represent the true period activity.

#### Method 3

Post the starting balances to period 0; then in each of the prior periods, post a journal transaction that contains the net activity of each ledger account for that period. Suppose you are setting up during period 7. Create and post a journal transaction that contains the net activity for each account during period 1. Then repeat the process for periods 2 through 6.

Method 3 provides accurate period balances. Each account contains its correct period balances for the current fiscal year. When you close books at the fiscal year-end, the balances roll over to the **Last Year** column in the **Ledger Accounts** window. The ledger accounts therefore reflect the true activity in each period. This method lets you generate reports that compare data from the previous year to data in the current year.

#### Method 4

Post the starting balances to period 0; then enter each transaction for the current year. Method 4 requires a great deal of work. This method is only practical when no accounting has been posted for the current year, or it is only a few weeks into the new fiscal year.

### About dedicated accounts

Sage 100 Contractor does not let you post journal transactions directly to the **Accounts Receivable**, **Accounts Payable**, **Service Receivables**, or **Inventory** ledger accounts. You can post to those accounts only through invoices. Therefore, entering the starting balances is a two-part process.

During the first part of the process, the **Accounts Receivable**, **Accounts Payable**, **Service Receivables**, and **Inventory** balances are posted to clearing accounts. Later, the individual open invoices are posted against the clearing accounts, thereby moving the balances into the proper accounts.

Similarly, you cannot directly post to the **Inventory** ledger account. Normally, you move inventory into the accounting system through payable invoices. For startup purposes, however, it is necessary to post a journal transaction to an **Inventory** clearing account. Later, the inventory is posted against the clearing account and allocated to specific inventory locations and parts, thereby moving the balances into the **Inventory** ledger account.

In this portion of the setup process, post the starting balances to the clearing accounts. If you are using a pre-built general ledger structure, Sage 100 Contractor already has the necessary clearing accounts established. At the fiscal year-end, you can delete the setup clearing accounts, as they are no longer needed.

Important! After posting the invoice and allocations for inventory, your clearing accounts should have a zero balance. If they do not, review your data to find out why.

### About setting up accounts for posting equipment

**Direct Equipment:**Enter the ledger account to which you are posting equipment expenses attributable to a job.

When you enter a direct equipment expense in the **5-5 Daily Payroll** or **8-4 Equipment Allocation** windows, Sage 100 Contractor posts a debit to the account in the **Direct Equipment** box, and a credit to the account in the **Equipment Revenue** box.

**Equipment Repair:**Enter the ledger account to which you are posting equipment expenses attributable to equipment repair or maintenance.

When you enter an equipment expense for repairs or maintenance in the **5-5 Daily Payroll** or **8-4 Equipment Allocation** window, Sage 100 Contractor posts a debit to the account in the **Equipment Repair** box, and a credit to the account in the **Equipment Revenue** box.

**Equipment Revenue:**Enter the ledger account to which you are posting equipment expenses.

When you enter an equipment expense, Sage 100 Contractor always posts the credit to the account in the **Equipment Revenue** box.

### About setting up accounts for posting payable invoices

Sage 100 Contractor uses the accounts indicated on the **Payables** tab in the **1-8 General Ledger Setup** window to post payable invoice transactions.

**Workers’ Compensation:**Enter the ledger account to which you are posting the charge to subcontractors for Workers’ Compensation insurance.

**Discounts Earned:**Enter the ledger account to which you are posting discounts taken on payable invoices.

#### Freight

**WIP Cost Account:**Enter the WIP cost account to which you are posting freight costs.

When posting the invoiced costs against a job, Sage 100 Contractor looks at the **WIP Posting** check box in the job file. If you selected the **WIP Posting** check box, Sage 100 Contractor posts freight costs to the account in the **WIP Cost Account** box.

**Direct Cost Account:**Enter the direct cost account to which you are posting freight costs.

When posting the invoiced costs against a job, Sage 100 Contractor looks at the **WIP Posting** check box in the job file. If the **WIP Posting** check box is clear, Sage 100 Contractor posts freight costs to the account in the **Direct Cost Account** box.

**Overhead Costs Account:**Enter the overhead cost account to which you are posting freight costs.

When posting the invoiced costs to overhead (posting the invoice without a job number), Sage 100 Contractor posts costs to the account in the **Overhead Cost Account** box.

Note: When posting the invoiced costs against a job, Sage 100 Contractor assigns the total of the freight costs to the first job cost record.

#### Variance

Variances in materials costs are posted to the **Overhead Costs Account**.

Note: Freight costs and the variance in materials costs each appear as separate lines in the journal transaction.

### About setting up accounts for posting receivable invoices

**Finance Charges:**Enter the ledger account to which you are posting the finance charges.

When printing client statements, you can create the finance charges for overdue invoices. Select the Calculate Finance Charges check box, and generate the statements. Sage 100 Contractor uses the finance rate set up in the job record to compute the finance charge and create a separate invoice for the amount.

**Discounts Given:**Enter the ledger account to which you are posting discounts given to cash receipts.

**WIP Payroll:**Enter the ledger account to which you are posting WIP payroll.[How?](../4-Accounts_Payable/About_work_in_progress__WIP_.md)

When posting the invoiced costs against a job, Sage 100 Contractor looks at the **WIP Posting** check box in the job file. If you selected the **WIP Posting** check box, Sage 100 Contractor posts payroll costs to the account in the **WIP Payroll** box.

**Retained Earnings:**Enter the ledger account to which you are posting the net profit when closing the books at the fiscal year-end.

You can change the account numbers on the Receivables tab regardless of whether you have posted transactions. If you change the account number, you have to move the balances to the new account through a journal transaction.
