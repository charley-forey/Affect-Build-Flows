<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/1-General_Ledger/Creating_a_query_for_finding_transaction_status_changes_made_in_1-3_Journal_Transactions.htm (Sage 100 Contractor help v20.5) -->

### Creating a query for finding transaction status changes made in 1-3 Journal Transactions

This query’s output shows you entries that were cleared on previous bank reconciliations and helps you find entries that do not appear on the **1-5 Bank Reconciliation**.

#### Creating the query for finding transaction status changes:

|  | 1 | Open **1-3 Journal Transactions**. |
|---|---|---|

|  | 2 | Select **File** > **Find** to display the list of available queries. |
|---|---|---|

|  | 3 | In the **Query List** window, select **Open Ledger Transactions—by Period**, and then click **Edit**. |
|---|---|---|

|  | 4 | In the upper left area of the **Display Fields** window, click **Ledger Transaction Lines**. |
|---|---|---|

|  | 5 | That action selects the table from which you can pick fields for the query. |
|---|---|---|

|  | 6 | Under **Fields**, double-click the following fields to select them for display: |
|---|---|---|

- **lgtnln.lgract Account**
- **lgtnln.dbtamt Debit Amount**
- **lgtnln.crdamt Credit Amount**

The new fields appear with the original fields under **Fields to Display**. If you select an incorrect field, click the field under **Fields to Display**, and press the Delete key. Then click **Next** to accept your changes in the **Display Fields** window.

|  | 7 | Click **Next** through the **Group Fields** and **Sort Fields** windows. |
|---|---|---|

|  | 8 | In the **Selection Fields** window, double-click the **lgtnln.lgract Account** field. It will be added to the list of fields under **Fields to Select By**. |
|---|---|---|

|  | 9 | Click **Next** to display the **Selection Criteria** window, and then click **Next** again to return to the **Query List** window. |
|---|---|---|

#### To run the query:

This query can be used to reconcile previous bank statements again and to look for journal transactions on the results of the query that are not on the bank statements. If you discover a transaction on the bank statement that is not on the results of the query, then the status on a transaction has been changed from **2-Cleared** to **1-Open** or **3-Void**.

|  | 1 | In the **Query List**,click the **Open Ledger Transactions—by Period** query, and then click **Run**. |
|---|---|---|

|  | 2 | In the Selection Criteria window: |
|---|---|---|

|  | a | Leave the **Period**, **Record#**, and **Source** fields blank. |
|---|---|---|

|  | b | In the **Status** field, type 2 to display **Cleared**transactions. |
|---|---|---|

|  | c | In the **Account** field, enter the cash account you want to reconcile. |
|---|---|---|

|  | 3 | Click **Run** to display the transactions within the selection criteria. These results can be printed or exported. |
|---|---|---|

|  | 4 | Select **File** > **Print** to print the information, or select **File** > **Save As** to export the information. |
|---|---|---|

| Links to more information . . . [About saving trial reconciliations](About_saving_trial_reconciliations.md) [Saving trial reconciliations](Saving_trial_reconciliations.md) [Clearing trial reconciliations](Clearing_trial_reconciliations.md) |
|---|
