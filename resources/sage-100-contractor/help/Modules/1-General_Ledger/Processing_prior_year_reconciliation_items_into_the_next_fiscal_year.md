<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/1-General_Ledger/Processing_prior_year_reconciliation_items_into_the_next_fiscal_year.htm (Sage 100 Contractor help v20.5) -->

### Processing prior year reconciliation items into the next fiscal year

If you notice that cheques, deposits, or adjustments are missing from your bank reconciliation after archiving a fiscal year, this topic can help you to resolve those issues.

#### Solutions

You might be missing cheques, deposits, adjustments, or a combination of these. Choose the solution according to your situation:

- Solution A: You are missing cheques or negative adjustments.
- Solution B: You are missing deposits or positive adjustments.
- Solution C: You are missing a combination of cheques, deposits, and adjustments.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Solution A](javascript:void(0);)

|  | 1 | Open **1-1 Cheques/Bank Charges**, and then enter each missing cheque. |
|---|---|---|

|  | 2 | For each missing cheque: |
|---|---|---|

|  | a | In the **Account#** box, enter the account from which original cheque was written. |
|---|---|---|

|  | b | In the **Cheques#** box, enter the original cheque number. |
|---|---|---|

|  | c | In the **Date** box, enter the date of the original cheque. |
|---|---|---|

|  | d | In the **Description** box, type a description.<br>It could be the description from the original entry. You may want to make a note that this was re-entered after the entry was removed during the close books process at year-end. |
|---|---|---|

|  | e | Type information in other boxes in the header section, as required. |
|---|---|---|

|  | f | Leave the **Status** set to **1-Open**. |
|---|---|---|

|  | 3 | In the grid, do the following: |
|---|---|---|

|  | a | In the **Account** cell, enter a clearing account in the cash range. If you do not have a clearing account set up, go to **1-7 General Ledger Accounts** and create one. Be sure the number is in the **Cash Accounts** range defined in **1-8 General Ledger Setup**. |
|---|---|---|

|  | b | In the **Debit** cell, type the amount of the original cheque. |
|---|---|---|

|  | 4 | From the **Edit** menu, select **Period** and then select **Period 00 – Prior Year**. Any entries posted to **Period 00** cannot be voided after they have been entered. Verify all of your entry information is correct before you save the entry. |
|---|---|---|

|  | 5 | Save the entry. |
|---|---|---|

|  | 6 | Repeat steps 1 through 3 for each missing cheque. |
|---|---|---|

|  | 7 | Enter a deposit in **1-2 Deposits/Interest** for the total amount of cheques from step 1, |
|---|---|---|

|  | 8 | Then do the following: |
|---|---|---|

|  | a | In the **Account#** box, enter the original cash account from the original cheque. |
|---|---|---|

|  | b | In the **Deposit#** box, type an entry, as required. |
|---|---|---|

|  | c | In the **Date** box, enter the date of original cheque.<br>If there are multiple cheques, you may use the last day of your last fiscal year. |
|---|---|---|

|  | d | In the **Description** box, type a description, as required. |
|---|---|---|

|  | e | Type information in other boxes in the header section, as required. |
|---|---|---|

|  | f | Leave the **Status** set to **1-Open**. |
|---|---|---|

|  | 9 | In the grid, do the following: |
|---|---|---|

|  | a | In the **Account**cell, use the same cash clearing account used in step 1. |
|---|---|---|

|  | b | In the **Credit Amount** cell, type the total of all chequesentered in step 1. |
|---|---|---|

|  | 10 | From the **Edit** menu, select **Period** and double-click **Period 00 – Prior Year**. Any entries posted to **Period 00** cannot be voided after they have been entered. Verify all of your entry information is correct before you save the entry. |
|---|---|---|

|  | 11 | Save the entry, but select **No** when prompted to **Post to Archive** because it already exists in the archive. |
|---|---|---|

|  | 12 | Open **1-3 Journal Transactions**, and find the deposit transaction created in steps 5 through 7; then change the Status to **2-Cleared**, and finally save the transaction. |
|---|---|---|

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Solution B](javascript:void(0);)

|  | 1 | Open **1-2 Deposits/Interest**, and then enter each missing deposit. |
|---|---|---|

|  | 2 | For each missing deposit: |
|---|---|---|

|  | a | In the **Account#** box, enter the account to which the original cheque was entered. |
|---|---|---|

|  | b | In the **Deposit#** box, enter the original deposit number. |
|---|---|---|

|  | c | In the **Date** box, enter the date of the original deposit. |
|---|---|---|

|  | d | In the **Description** box, type a description. |
|---|---|---|

|  | e | Leave the **Status** set to **1-Open**. |
|---|---|---|

|  | 3 | In the grid, do the following: |
|---|---|---|

|  | a | In the **Account** cell, enter a clearing account in the cash range. If you do not have a clearing account set up, go to **1-7 General Ledger Accounts** and create one. Be sure the number is in the **Cash Accounts** range defined in **1-8 General Ledger Setup**. |
|---|---|---|

|  | b | In the **Credit Amount** cell, type the amount of original deposit. |
|---|---|---|

|  | 4 | From the **Edit** menu, select **Period** and then select **Period 00 – Prior Year**. Any entries posted to **Period 00** cannot be voided after they have been entered. Verify all of your entry information is correct before you save the entry. |
|---|---|---|

|  | 5 | Save the entry, but select **No** when prompted to **Post to Archive** because it already exists in the archive. |
|---|---|---|

|  | 6 | Repeat steps 1 through 3 for each missing deposit. |
|---|---|---|

|  | 7 | Open **1-1 Cheques/Bank Charges**, and enter the total amount of the deposit from step 1. |
|---|---|---|

|  | 8 | For each item: |
|---|---|---|

|  | a | In the **Account#** box, type the cash account from which original deposit was entered. |
|---|---|---|

|  | b | In the **Cheques#** box, type a number, as required. |
|---|---|---|

|  | c | In the **Date** box, type the date of original deposit. |
|---|---|---|

|  | d | In the **Description** box, type a description. |
|---|---|---|

|  | e | Type information in other boxes in the header section, as required. |
|---|---|---|

|  | f | Leave the **Status** set to **1-Open**. |
|---|---|---|

|  | 9 | In the grid, do the following: |
|---|---|---|

|  | a | In the **Account** cell, enter the same clearing account used in step 1. |
|---|---|---|

|  | b | In the **Debit** cell, type the total of all deposits entered in step 1. |
|---|---|---|

|  | 10 | From the **Edit** menu, select **Period** and then select **Period 00 – Prior Year**. |
|---|---|---|

|  | 11 | Save the entry, but select **No** when prompted to **Post to Archive** because it already exists in the archive. |
|---|---|---|

|  | 12 | Open **1-3 Journal Transactions**, find the cheque transaction created in steps 5 through 7, change the **Status** to **2**-**Cleared**, and then save the transaction. |
|---|---|---|

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Solution C](javascript:void(0);)

|  | 1 | Create the cheques as stated in Solution A steps 1, 2, 3, and 4, but skip all other steps. |
|---|---|---|

|  | 2 | Create the deposits as stated in Solution B steps 1, 2, 3, and 4, but skip all other steps. |
|---|---|---|

|  | 3 | Open **2-4-21 General Ledger** report. |
|---|---|---|

|  | 4 | In the **Account** selection box, enter the cash clearing account used in steps 1 and 2. |
|---|---|---|

|  | 5 | From the **File** menu, select **Print Preview**. |
|---|---|---|

|  | 6 | Note the **Totals** in the **Balance** column, and write this amount down. You will need it later. |
|---|---|---|

|  | 7 | Open **1-3 Journal Transactions**, create an adjusting entry to zero out the amount in your cash clearing account. |
|---|---|---|

|  | 8 | Do the following: |
|---|---|---|

|  | a | In the **Trans#** box, type any transaction number; for example ADJ2007. |
|---|---|---|

|  | b | In the **Date** box, type the date of your fiscal year-end. |
|---|---|---|

|  | c | In the **Description** box, type a description. |
|---|---|---|

|  | 9 | In the grid, do the following: |
|---|---|---|

|  | a | **Row 1—Account box**: Enter the same cash account used for your cheques and deposits. |
|---|---|---|

|  | b | If the noted amount from step 3 was positive, debit that amount. |
|---|---|---|

|  | c | If the noted amount from step 3 was negative, credit that amount. |
|---|---|---|

|  | d | **Row 2—Account box**: Enter the same cash clearing account used for your cheques and deposits. |
|---|---|---|

|  | e | If the noted amount from step 3 was positive, credit that amount. |
|---|---|---|

|  | f | If the noted amount from step 3 was negative, debit that amount. |
|---|---|---|

|  | 10 | From the **Edit** menu, select **Period**, and then select **Period 00 – Prior Year**. Any entries posted to **Period 00** cannot be voided after they have been entered. Verify all of your entry information is correct before you save the entry. |
|---|---|---|

|  | 11 | Save the entry, but select **No** when prompted to **Post to Archive** because it already exists in the archive. |
|---|---|---|

|  | 12 | From the **File** menu, select **Recall the transaction**. |
|---|---|---|

|  | 13 | Change the **Status** to **2-Cleared**. |
|---|---|---|

| Links to more information . . . [Fiscal year-end close checklist](Fiscal_year-end_checklist.md) [Reconciling beginning and ending balances](Reconciling_beginning_and_ending_balances.md) |
|---|
