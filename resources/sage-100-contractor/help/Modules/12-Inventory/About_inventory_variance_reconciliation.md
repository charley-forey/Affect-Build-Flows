<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/12-Inventory/About_inventory_variance_reconciliation.htm (Sage 100 Contractor help v20.5) -->

### About inventory variance reconciliation

Note: This functionality is available only if you have the [Inventory Add-On Module](http://www.na.sage.com/sage-100-contractor/modules/service-management).

When inventory is removed, it can be sold or expensed to accounts including the job costs, equipment, and work in progress (WIP) account ranges. When this occurs, the cost of the inventory is calculated using the weighted average cost (WAC) in order to provide the most accuracy when job costing. If you use either the LIFO or FIFO valuation methods, it has accounting implications because your inventory general ledger account is reduced by LIFO or FIFO calculations and not by WAC. As a result, a variance develops between the job costs, equipment and WIP accounts, and the inventory general ledger account.

Job cost reconciliation is critical in construction accounting. Sage 100 Contractor audits the job and equipment costs and general ledger values to ensure that they are equal. To do this, you use the **Reconcile** command on the **Options** menu in **6-3 Job Costs**.

Because LIFO and FIFO dictate that the values will not be equal, this process must accommodate variances between the general ledger and the job and equipment costs that can be explained by the inventory variance. If the difference between the general ledger and the job and equipment cost values is the variance, there is no discrepancy between the accounts and the audit should not report those occurrences.

Additionally, two reports provide a way to track and verify the discrepancy among job costs, equipment, and WIP accounts caused by the LIFO or FIFO inventory variance.

- The **12-1-3-61 Inventory Variance** report reconciles the job, equipment, and WIP costs with the general ledger costs on individual transactions.
- The **2-3-61 General Ledger Cost Comparison** report reconciles the total balance of job, equipment, and WIP costs with the general ledger costs in a summary.

| Links to more information . . . [About inventory valuation methods](About_inventory_valuation_methods.md) [About the inventory offset account](About_the_inventory_offset_account.md) [About job cost reconciliation](../6-Project_Management/About_job_cost_reconciliation.md) [About work in progress (WIP)](../4-Accounts_Payable/About_work_in_progress__WIP_.md) |
|---|
