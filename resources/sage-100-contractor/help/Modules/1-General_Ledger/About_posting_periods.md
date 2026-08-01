<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/1-General_Ledger/About_posting_periods.htm (Sage 100 Contractor help v20.5) -->

### About posting periods

Use the Posting Period window to select the period where you want to post your transactions.

In any accounting transactions window, such as **4-2 Payable Invoice/Credits**, you can post individual transaction records to a different posting period. For example, if you need to post a transaction to period 1 of a new fiscal year, but you are still currently in period 12 of the current fiscal year, use this window to post the transaction to period 1 of the new fiscal year.

Note: If you want to change the default posting period for all transactions, you can only change it using **1-6 Period and Fiscal Year Management**> **Change Period**. [How?](Changing_posting_periods.md)

Period 1 of the next fiscal year becomes available only after you advance your current fiscal period to **period 12** (using the [Change Period feature](Changing_posting_periods.md)). Advance your current period to **period 1** to make periods 2 through 12 available for the next fiscal year.

#### To use Posting Period:

Select the period to which you want to post transactions and click [**Select**].

#### Important Posting Period features

The following bullet points describe some of the features related to posting periods:

|  | n | Accounting transaction windows contain a **Change the posting period** button that displays the posting period to which you are posting transactions. By changing the posting period, you can post transactions to the specified period until you change the period again or close the window. When the window opens again, the posting period is set to the current default posting period. |
|---|---|---|

|  | n | Users at different workstations can work in the same window and post to different periods. For example, while Andy and Melissa are entering invoices in the **Accounts Payable Invoices** window, Andy finds a few invoices that need posting to a previous period. While Melissa continues entering invoices in the current fiscal period, Andy can change the fiscal period and enter those invoices. |
|---|---|---|

|  | n | When you change the posting period to something other than the default current posting period, Sage 100 Contractor changes the color of the **Posting Period** button to yellow. |
|---|---|---|

|  | n | At the end of the period, open **1-6 Period and Fiscal Year Management** > **Change Period** and advance the current default posting period to the next one. |
|---|---|---|

|  | n | When advancing to the next posting period, the program performs a complete audit of the books. If you discover audit errors, you can view them and possibly repair the ledger balances at that time rather than at the end of the fiscal year. |
|---|---|---|

Important! We strongly recommend that you recalculate balances to repair discrepancies if they are discovered during audits at the end of each posting period. Repairing audit errors as you advance to the next posting period is much more efficient than waiting until year-end to repair a year’s worth of audit errors. [How?](About_the_Recalculate_Balances_window_and_repairing_the_balances.md)

|  | n | You can restrict users from posting transactions to previous or future periods. [How?](Locking_access_to_posting_periods.md) |
|---|---|---|

|  | n | If you have an archive from a previous year, you can post transactions to the archive; however, you must open the archive company first. Sage 100 Contractor does not post entries simultaneously to period 12 of an archive company and period 0 of the current company. |
|---|---|---|

|  | n | When using Sage 100 Contractor across a network, changing the current period using **1-6 Period and Fiscal Year Management** > **Change Period** affects all workstations that access Sage 100 Contractor. |
|---|---|---|

| Links to more information . . . [About the Recalculate Balances window and repairing the ledger balances](About_the_Recalculate_Balances_window_and_repairing_the_balances.md) [Locking access to posting periods](Locking_access_to_posting_periods.md) [Changing posting periods](Changing_posting_periods.md) [About year-end processes](About_Year-End_Processes.md) [About posting to the period 0 archive](About_posting_to_the_period_0_archive.md) |
|---|
