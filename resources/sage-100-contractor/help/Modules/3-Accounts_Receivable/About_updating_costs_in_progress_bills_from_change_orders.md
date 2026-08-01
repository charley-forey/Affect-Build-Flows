<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/3-Accounts_Receivable/About_updating_costs_in_progress_bills_from_change_orders.htm (Sage 100 Contractor help v20.5) -->

### About updating costs in progress bills from change orders

You can automatically or manually update costs in the progress bill from change orders. Choose from two methods to automatically update the costs from change orders. You can either incorporate the changes to costs in the individual cost codes, or include the total amount of the change order as a separate line item.

Important! When using the **Append as New Lines** option, do not change the **Description** values as you have entered them into the grid. Sage 100 Contractor uses an exact match of the text in the **Description** column to match the items from the **Change Order** grid to the **Progress Billing** grid.

#### Method 1: Incorporate changes to costs in the individual cost codes

When you select the **Add to Existing Lines** option in **3-7 Progress Billing**, Sage 100 Contractor only updates cost codes or divisions present in both the change order and the progress bill. If the change order contains cost codes that do not correspond to cost codes or divisions in the progress bill, Sage 100 Contractor will notify you. Review the new cost codes in the change orders, and if necessary, manually add the new cost codes or divisions and update the progress bill again. Sage 100 Contractor displays the amount of change to each cost code in the **Changes** column and the new contract amount in the **Contract** column.

#### Method 2: Include the total amount of the change order as a separate line item

Instead of updating the individual cost codes, you can append each change order as a separate line item at the end of the progress bill. Suppose the client approves change order number 1, and you only want to show the total amount of the changes on the progress bill. When you select the **Append as New Lines** option, Sage 100 Contractor creates a separate line for each change order. Sage 100 Contractor inserts the statement **Change Order #1** in the **Description** column, and displays the total amount of the change order in the **Changes** column and the new contract amount in the **Contract** column.

| Links to more information . . . [Updating costs in progress bills from change orders automatically](Updating_costs_in_progress_bills_from_change_orders_automatically.md) [Updating costs in progress bills from change orders manually](Updating_costs_in_progress_bills_from_change_orders_manually.md) [Appending costs from change orders to progress bills](Appending_costs_from_change_orders_to_progress_bills.md) [About change orders](../6-Project_Management/About_change_orders.md) [About cost codes and divisions](../6-Project_Management/About_cost_codes_and_divisions.md) |
|---|
