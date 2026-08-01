<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/12-Inventory/About_inventory_allocation.htm (Sage 100 Contractor help v20.5) -->

### About inventory allocation

Note: This functionality is available only if you have the [Inventory Add-On Module](http://www.na.sage.com/sage-100-contractor/modules/service-management).

Inventory moves into the control system through payable invoices, service receivables credits, inventory allocation, or purchase order receipts. After the inventory is entered into the system, you can use the **12-2 Inventory Allocation** window to track movement among locations and to place stock on hold. You can also post transactions to the general ledger for the consumption of stock items by your company, the loss or shrinkage of stock items, and the revaluation of stock.

The grid contains **Source** and **Destination** columns.

- **Source** specifies the location inventory was moved from
- **Destination** specifies the location inventory is moved to

The grid also contains an **Account** column. If the transaction affects the general ledger, you must enter the account number.

On a single grid line, you can provide information in only two of these three columns and the type of transaction determines which columns to use. For example, to move inventory to a different location, enter where the inventory is coming from in the **Source** cell and where the inventory is moving to in the **Destination** cell. Or if you want to adjust the quantity for a particular item for shrinkage, enter the quantity lost to shrinkage in the **Quantity**cell, the location of the quantity that was lost in the **Source** cell, and then enter the overhead expense account in the **Account** cell.

Note: Inventory allocations always use the weighted average cost for items, regardless of the inventory valuation method specified for the general ledger. If you use the LIFO or FIFO valuation method for general ledger, you can print the General Ledger Cost Comparison report (using the 2-3 Income Statement menu) to view inventory variances created by allocations. [For more information, see About inventory variance reconciliation.](About_inventory_variance_reconciliation.md).

| Links to more information . . . [Moving inventory among locations](Moving_inventory_among_locations.md) [Placing stock on hold](Placing_stock_on_hold.md) [Entering records for inventory used on contracts](Entering_records_for_inventory_used_on_contracts.md) [Entering records for internal consumption](Entering_records_for_internal_consumption.md) [Entering records for inventory shrinkage](Entering_records_for_inventory_shrinkage.md) [Entering records to re-value existing inventory](Entering_records_to_re-value_existing_inventory.md) |
|---|
