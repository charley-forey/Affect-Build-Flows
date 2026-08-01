<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/6-Project_Management/About_job_cost_reconciliation.htm (Sage 100 Contractor help v20.5) -->

### About job cost reconciliation

Because discrepancies can appear over time, it is important to reconcile the job cost records with the ledger transactions. During the reconciliation, Sage 100 Contractor compares the ledger transactions with the job cost records and reports any discrepancies that exist.

The reconciliation determines if ledger transactions are missing job cost records, or if variances exist between the cost amount of the ledger transaction and the job cost records. After the audit is complete, print the **Job Cost Reconciliation** report, which lists ledger transactions that are missing cost records or have variances in excess of $1.

To determine the cause of each error, review the ledger transaction in the **1-3 Journal Transactions** window or in the window of original entry. If a transaction does not have a corresponding job cost record, look for situations where cost records have been deleted. For example, when you delete a job Sage 100 Contractor deletes all associated records, including the job cost records.

It is also important to search the job cost records thoroughly. Because historical records do not tie to ledger transactions, it is possible to already have a cost record for a ledger transaction. Make sure that a historical record does not already exist before creating a cost record. If you cannot locate a cost record, you can enter a historical cost record.

Resolving audit variances does not eliminate them from the **Job Cost Reconcile** report, and they will appear on subsequent reports for the fiscal year. It is a good idea to retain a printed copy of the report and any notes you have made to help identify and resolve errors. You can then use the report with future job cost reconciliation reports to identify the job cost errors you have already resolved.

Note: Sage 100 Contractor does not report duplicate or extra job cost records because they are not associated with a specific ledger transaction. Additionally, Sage 100 Contractor cannot audit historical job cost records as they were not created by posting ledger transactions.

| Links to more information . . . [Reconciling job costs](Reconciling_job_costs.md) [About journal transactions](../1-General_Ledger/About_journal_transactions.md) [Methods for entering historical job cost records](Methods_for_entering_historical_job_cost_records.md) |
|---|
