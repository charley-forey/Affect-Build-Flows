<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/1-General_Ledger/1-2_Deposits___Interest.htm (Sage 100 Contractor help v20.5) -->

## 1-2 Deposits & Interest

You can enter deposits and accrued interest for chequing or savings accounts in the **1-2 Deposits/Interest** window. When you enter a deposit, enter individual cheques or accrued interest as separate line items. If you have cash receipts for receivable or service invoices, enter these transactions using the **3-3-1 Cash Receipts** window.

#### To enter a deposit:

|  | 1 | Open **1-2 Deposits/Interest**. |
|---|---|---|

|  | 2 | In the **Account#** box, enter the cash account number. |
|---|---|---|

|  | 3 | In the **Deposit#** box, enter the deposit transaction number. |
|---|---|---|

|  | 4 | In the **Date** box, enter the date of the deposit. |
|---|---|---|

|  | 5 | In the **Description** box, enter a brief statement about the transaction. |
|---|---|---|

|  | 6 | In the **Status** list, click the status of the entry. |
|---|---|---|

|  | 7 | In the grid, do the following: |
|---|---|---|

|  | a | In the **Description** cell, enter a brief statement about the transaction. |
|---|---|---|

|  | b | In the **Account** cell, enter the general ledger account number. |
|---|---|---|

|  | c | In the **Subaccount** cell, enter the subsidiary account number. |
|---|---|---|

|  | d | In the **Credit Amount** cell, enter the amount. |
|---|---|---|

|  | 8 | Repeat step 7 for each item that you want to include in the deposit. |
|---|---|---|

|  | 9 | On the **File** menu, click **Save**. |
|---|---|---|

### About deposits on jobs

Some contracts require a client to supply a deposit before work can begin. When you receive the deposit, you need to decide how to enter the deposit, as well as when and how to apply the deposit when invoicing the client. This often depends on the terms agreed upon in the contract. The following outlines the most common methods for handling job deposits:

You can enter the cheque for the job deposit in the **1-2 Deposits/Interest** window. If you only receive a few deposits each fiscal year, deposit the cheque to the chequing account and credit the **Deposits on Jobs** account. If you receive numerous deposits, create a subsidiary account for each deposit using the job number as the subsidiary account number. This enables you to track deposits independently.

You can enter the job deposit as a receivable credit in the **3-2 Receivable Invoices/Credits** window, debiting the **Deposits on Jobs** account and crediting the accounts receivable account. You can enter the deposit as an open credit, assigning it invoice status **1-Open**, and invoice type **2-Memo**.

Later, you can apply the credit as you enter receivable invoices or you can apply the credit as you enter receipts in the **3-3-1 Cash Receipts** window. The credit affects the statement balance, but does not affect the contract balance.

Tip: By entering the job deposit as a credit, you can supply the client with a copy of the credit. This allows the client to see how you applied the job deposit to invoices. Another way to inform the client about the job deposit is to send the client a statement detailing the activity for the job.

Important! Best accounting practices require that you do not void transactions that have been processed by the bank. Therefore, it is not possible to void transactions with a status of **2‑Cleared**.

#### To void a deposit:

|  | 1 | Open **1-3 Journal Transactions**. |
|---|---|---|

|  | 2 | Using the data control, select the record of the deposit (**Trans#**) you want to void. |
|---|---|---|

|  | 3 | Verify that the **Status** is **1-Open**. |
|---|---|---|

|  | 4 | If necessary, in the **Status** drop-down list, change the status to **1-Open**. |
|---|---|---|

|  | 5 | On the **Edit** menu, click **Void Transaction**. |
|---|---|---|

Tip: After voiding all payments made to an invoice, you can void the invoice itself.
