<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/6-Project_Management/About_adding_change_orders_to_subcontracts.htm (Sage 100 Contractor help v20.5) -->

### About adding change orders to subcontracts

It is likely that you will have to add one or more change orders to subcontracts during the course of a project.

Note: **6-7-1 Subcontracts** control subcontract records and their interaction and integration with **6-4-1 Change Orders** and **4-2 Payable Invoices/Credits**. Changes made to records in **6-4-1 Change Orders** and in **4-2 Payable Invoices/Credits** are displayed in **6-7-1 Subcontracts**.

The process of entering a change order for a contract is straight forward. You begin by referencing the job in the header section of the widow. Then after entering the required information, such as **Description**, **Change#**, **Date**, and **Status** in the header, you enter information in the tabs, **Prime Change Details** and **Budget and Sub Change Details**.

On the **Prime Change Details** tab, you only need to enter required information for **Description**, **Cost Code**, and **Cost Type**. Then you click the **Budget and Sub Change Details** tab to enter the changes.

There is a new column, **Subcontract Line,** in the **Budget and Sub Change Details** grid. Five of the columns of the grid now act as a unit. These columns are:

- **Vendor**—Enter a vendor, or accept the default vendor.
- **Subcontract**—Enter a subcontract number, or accept the default subcontract number.
- **Subcontract Line**- Select the line to affect in the subcontract, leave the cell blank to create a new line in the subcontract.
- **Change#**—Enter a **Change#**, or accept the default **Change#**.
- **Status**—Enter a **Status**.

Important! These five columns act as a unit. In addition to required fields, a value must be entered under each of these columns except **Subcontract Line** to be able to save the change order record. If the **Subcontract Line** cell is blank, you have to enter a **Cost Code** and **Cost Type**. If you enter data in the **Subcontract Line** cell, **Cost Code** and **Cost Type** autofill.

#### Change a line or create a new line in a 6-7-1 Subcontract record

When entering a subcontract change, you can add or subtract the existing value of a subcontract record line or you can add a new line to the subcontract record. When working in the grid with your cursor in the a cell under the **Subcontract Line** column, you can press F5 to open the **Subcontract Lines** lookup window. Then select the line you want to affect by double-clicking it. Alternatively, leaving the **Subcontract Line** cell blank when creating a new line in the grid, creates a new line in the subcontract record.

After saving the record, you can see the changes to the subcontract record by opening the subcontract in **6-7-1 Subcontracts**. In the grid, notice that the **Changes** column will have an entry in the line you selected when creating the change. The change is also displayed in the details summary boxes at the bottom of the window.

| Links to more information . . . [Creating purchase orders from change orders](Creating_purchase_orders_from_change_orders.md) [Entering accounts payable invoices for subcontract lines](../4-Accounts_Payable/Entering_accounts_payable_invoices_for_subcontract_lines.md) [About change order status](About_change_order_status.md) |
|---|
