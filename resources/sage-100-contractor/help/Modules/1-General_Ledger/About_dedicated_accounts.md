<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/1-General_Ledger/About_dedicated_accounts.htm (Sage 100 Contractor help v20.5) -->

### About dedicated accounts

Sage 100 Contractor does not let you post journal transactions directly to the **Accounts Receivable**, **Accounts Payable**, **Service Receivables**, or **Inventory** ledger accounts; you can only post to those accounts through invoices. Therefore, entering the starting balances is a two-part process.

During the first part of the process, the **Accounts Receivable**, **Accounts Payable**, **Service Receivables**, and **Inventory** balances are posted to clearing accounts. Later, the individual open invoices are posted against the clearing accounts, thereby moving the balances into the proper accounts.

Similarly, you cannot directly post to the **Inventory** ledger account. Normally, you move inventory into the accounting system through payable invoices. For startup purposes, however, it is necessary to post a journal transaction to an **Inventory** clearing account. Later, the inventory is posted against the clearing account and allocated to specific inventory locations and parts, thereby moving the balances into the **Inventory** ledger account.

In this portion of the setup process, post the starting balances to the clearing accounts. If you are using a pre-built general ledger structure, Sage 100 Contractor already has the necessary clearing accounts established. At the fiscal year-end, you can delete the setup clearing accounts, as they are no longer needed.

Important! After posting the invoice and allocations for inventory, your clearing accounts should have a zero balance. If not, review your data to find out why.

| Links to more information . . . [Entering starting balances](Entering_starting_balances.md) [About clearing accounts](About_clearing_accounts.md) [Pre-built chart of accounts](Pre-built_chart_of_accounts.md) [About setting up accounts for posting payable invoices](About_setting_up_accounts_for_posting_payable_invoices.md) [About setting up accounts for posting receivable invoices](About_setting_up_accounts_for_posting_receivable_invoices.md) |
|---|
