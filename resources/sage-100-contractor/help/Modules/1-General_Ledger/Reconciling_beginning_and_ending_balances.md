<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/1-General_Ledger/Reconciling_beginning_and_ending_balances.htm (Sage 100 Contractor help v20.5) -->

### Reconciling beginning and ending balances

There are several reasons a statement ending balance may not match the next month’s beginning balance.

#### Causes

- A transaction with a future date that falls beyond the **Statement Cutoff Date** was entered. See clearing the Statement Cutoff date.
- A transfer was made from one cash account to another cash account without using a clearing account. When the first cash account is reconciled, it balances correctly. When the second account is reconciled, the transaction is already cleared so the beginning balance is off by the amount of cleared transaction. See transferring cash without using a clearing account.
- The status of a transaction was changed outside of the **1-5 Bank Reconciliation**. For example, the status of a transaction was changed in **1-3 Journal Transactions** to **2-Cleared**. See have you changed the status of any transaction that posts to your cash account through 1-3 Journal Transactions?

Important! This step-by-step reconciliation process will help you locate the out-of-balance cause and provide a solution. More than one cause may apply, however, and if you resolve a problem in one of the steps below, fix it, and then look at the **1-5 Bank Reconciliation** balances again. If they are still out or balance, continue to the next step.

#### In the **1-5 Bank Reconciliation** window, do you type a **Statement Cutoff Date**? If you do, clear the **Statement Cutoff Date**. Are the balances still wrong?

Consider the following:

- If the balances are correct, you have a transaction with a future date (a date beyond the **Statement Cutoff Date** you entered) which has been cleared.
- If the balances are still incorrect, but you see the transaction on the bank reconciliation grid, that transaction has a future date. If the date of the transaction is incorrect, go to **1-3 Journal Transactions** and change the date to the correct date.
- If the balances are still incorrect, proceed to step 2.

#### Is this the first bank reconciliation of the new fiscal year?

- If yes, you may have prior year outstanding transactions that were removed during the close fiscal year process. See the topic, [Processing prior year reconciliation items in to the next fiscal year](Processing_prior_year_reconciliation_items_into_the_next_fiscal_year.md).
- If no, continue with step 3.

#### Did you transfer cash from one cash account to another cash account without using a clearing account?

If yes, follow these steps to correct the problem:

- Find the cleared items from the first cash account.
- Open **1-3 Journal Transactions**, and change the **Status** on the transaction to **1-Open**.
- Void the transaction.
- Re-enter the transfer in two transactions using a clearing account. See the topic [Entering clearing account transfers](Entering_clearing_account_transfers.md).
- Display the transaction that represents the cash account that was previously cleared, and change the Status to **2-Cleared**.
- Open **1-5 Bank Reconciliation** to verify the balances are correct.

#### Have you changed the status of any transaction that posts to your cash account through **1-3 Journal Transactions**?

If yes, the beginning balance will be incorrect. To correct the beginning balance, open **1-3 Journal Transactions** and display the transaction.

If the status is **Open** change it to **Cleared**

If the status is **Cleared**, change it to **Open**.

If you do not know whether or not the status of any transactions has been changed, refer to the topic [Creating a query for transaction status changes made in 1-3 Journal Transactions](Creating_a_query_for_finding_transaction_status_changes_made_in_1-3_Journal_Transactions.md).

| Links to more information . . . [About saving trial reconciliations](About_saving_trial_reconciliations.md) [Saving trial reconciliations](Saving_trial_reconciliations.md) [Clearing trial reconciliations](Clearing_trial_reconciliations.md) |
|---|
