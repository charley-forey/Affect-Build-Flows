<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/1-General_Ledger/Transferring_Funds_Among_Accounts.htm (Sage 100 Contractor help v20.5) -->

### Transferring Funds among Accounts

Note: We recommend that you do not attempt to transfer funds directly between accounts in the **1-1 Cheques and Bank Charges** or the **1-2 Deposits and Interest** window. When you transfer funds directly from one account to another, Sage 100 Contractor creates a single record for the transfer. The record of the transfer appears in the cheque reconciliation of both accounts only until you clear it from one account or the other. After you clear the transaction for one account, it no longer appears in the reconciliation for the other account.

If you need to transfer funds between accounts, you should use a two-step procedure to transfer funds to and from a clearing account. Using this method creates a transaction to reconcile for each account.

Before you try to transfer funds, make sure you have a clearing account in the **Cash Accounts** range in the general ledger.

### About clearing accounts

Some transactions can become quite complex. With clearing accounts, you can create transactions that prove you have posted the amounts correctly. In addition, clearing accounts provide a means of posting transactions or balances to accounts that normally do not allow direct posting.

Note: Clearing accounts do not carry a balance for any length of time. If you want to hold a transaction in an account, use a suspense account. [How?](About_suspense_accounts.md)

Before posting a transaction, make sure the clearing account does not contain a balance. Posting a transaction to a clearing account moves a balance into the account. To move the balance from the clearing account, post a transaction or series of transactions against the clearing account. When the account balance reaches zero, you have completely posted the balance.

Suppose that you have transferred money from a general chequing account to a payroll chequing account. Using a clearing account, you would create a transaction in each account.

| Window of entry | Debit | Credit |
|---|---|---|
| Cheques/Bank Charges | Clearing | General Chequing |
| Deposits/Interest | Payroll Chequing | Clearing |

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To create a clearing account:](javascript:void(0);)

1. Open **1-7 General Ledger Accounts**.
2. In the data control box, enter the ledger account number in the cash accounts range of 1000 to 1999.
3. In the **Short Name** box, enter a brief description of the clearing account. Important! If an account uses departments or subsidiary accounts, the departments or subsidiary accounts must be set up before posting transactions. In the **Subsidiary** list, click **1‑Subaccounts** or **2-Departments**.
4. As required, in the **Subsidiary** list, click **1-Subaccounts** or **2-Departments**. You can assign a cost type to ledger accounts, providing an additional way to verify transactions are posted to the proper accounts. When you post a transaction that has cost types, Sage 100 Contractor compares the transaction’s cost type with the ledger account cost type. If the cost types do not match, Sage 100 Contractor provides a warning, but does not prevent posting the transaction.
5. In the **Cost Type** list, click the cost type you want to assign the ledger account.
6. On the **File** menu, click **Save**.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To transfer funds](javascript:void(0);)

1. Transfer the funds from the source account to the clearing account:
   
   1. Open **1-1 Cheques and Bank Charges**.
   2. In the **Account#** box, enter the cash account from which you need to transfer the funds.
   3. In the **Cheques#** box, enter the bank transaction number or a dummy transaction number.
   4. In the **Date** box, enter the date of transfer.
   5. In the **Description** box, type a brief description of the transfer.
   6. In the **Status** list, click **1-Open**.
   7. In the grid:
      
      1. In the **Account** cell, enter the clearing account to which you are transferring funds.
      2. If the selected account has subsidiary accounts, enter the number in the **Subaccount** cell.
      3. In the **Debit Amount** cell, enter the amount of the transfer.
   8. Click **Edit** > **Period**, and then verify that the posting period is correct.
   9. Click **File** > **Save**.
2. Transfer the funds from the clearing account to the destination account:
   
   1. Open **1-2 Deposits and Interest**.
   2. In the **Account#** box, enter the cash account into which you need to transfer the funds.
   3. In the **Deposit#** box, enter the bank transaction number or a dummy transaction number.
   4. In the **Date** box, enter the date of the transfer.
   5. In the **Description** box, type a brief description of the transfer.
   6. In the **Status** list, click **1-Open**.
   7. In the grid:
      
      1. In the **Account** cell, enter the clearing account you used in step 1.
      2. If the selected account has subsidiary accounts, enter the number in the **Subaccount** cell.
      3. In the **Credit Amount** cell, enter the amount of the transfer.
3. Click **Edit** > **Period**, and then verify the posting period.
4. Click **File**> **Save**.

Tip: You can verify the complete transfer of funds by viewing the clearing account balance in **1-7 General Ledger Accounts**.

### About suspense accounts

Suppose your company receives a corporate tax refund, and you want to deposit the cheque, but you do not know how to correctly post the transaction. The correct approach is to deposit the cheque and credit it to a suspense account in the **Cash Accounts** range. The amount remains in the suspense account until you determine where to post the credit.

Suspense accounts provide a temporary location where you can post a transaction until you determine the proper accounts. Similar in function to a clearing account, suspense accounts allow transactions to pass through the account. When you post transactions to a suspense account, however, the transactions can remain for an extended time until you determine the proper accounts.

It is a good idea to use a suspense account in the account range to which you will eventually post the transactions. For example, you are not sure how to post a transaction related to equipment. You can use a suspense account in the **Equipment** range of ledger accounts.
