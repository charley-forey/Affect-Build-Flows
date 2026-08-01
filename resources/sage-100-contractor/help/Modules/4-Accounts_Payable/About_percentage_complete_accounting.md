<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/4-Accounts_Payable/About_percentage_complete_accounting.htm (Sage 100 Contractor help v20.5) -->

### About percentage complete accounting

Using percentage complete accounting, also referred to as over/under billing, you declare income during the period that you earn it, determined by the percentage of work completed. The percentage complete accounting method allows you to compare the expenses and income generated during the same period. Otherwise, reports such as income statements provide a misleading view of the profitability because it contains the expenses for the current period and income for previous periods.

Instead of determining the WIP adjustment manually, you can print the **6-1-7 Over/Under Billing Report** to determine the over or under billing for any job currently in progress. Because the report calculates the WIP adjustment, you only need to post the necessary journal transactions.

Sage 100 Contractor uses the following process to determine the WIP adjustment. To establish the percentage of work completed, the program divides the accumulated costs by the amount of the current budget. Then to determine the income earned, it multiplies the revised contract (the amount of the original contract plus approved change orders) by the percentage of work completed. Finally, the program subtracts the total amount of the receivable invoices assigned type **1-Contact** from the amount of income earned. The resulting amount is the WIP adjustment.

For example, a contractor is working on a home remodel that was budgeted at $100,000 and contracted for $150,000. With $50,000 in costs at the time of billing, the project is 50% complete. The contractor has therefore earned 50% of the contracted amount, which is $75,000. As the contractor has not previously billed anything for the project, there are no billed invoices to deduct from the earnings. The resulting $75,000 WIP adjustment is posted in the **1-3 Journal Transactions** window.

Usually an **Over Billing** account is set up in the **Payable** range of accounts and an **Under Billing** account is set up in the **Receivable** range of accounts. In addition, an **Over/Under Billing** account is set up in the **Income** range of accounts. When you have determined the amount of the WIP adjustment, post a journal transaction. If the WIP adjustment is a positive amount, debit the receivable account and credit the income account. If the WIP adjustment is a negative amount, credit the payable account and debit the income account.

Note: Some companies reverse the WIP adjustment in the subsequent fiscal period.

| Links to more information . . . [About setting up accounts for posting payable invoices](../1-General_Ledger/About_setting_up_accounts_for_posting_payable_invoices.md) [About setting up accounts for posting receivable invoices](../1-General_Ledger/About_setting_up_accounts_for_posting_receivable_invoices.md) [Reversing a transaction in the next period](../1-General_Ledger/Reversing_a_transaction_in_the_next_period.md) |
|---|
