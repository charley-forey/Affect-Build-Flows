<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/12-Inventory/Entering_records_to_re-value_existing_inventory.htm (Sage 100 Contractor help v20.5) -->

### Entering records to re-value existing inventory

Note: This functionality is available only if you have the [Inventory Add-On Module](http://www.na.sage.com/sage-100-contractor/modules/service-management).

There are several reasons why you re-value stock. Items lose value over time, are damaged, or need to be re-valued due to an incorrect entry.

You can re-value the entire quantity of a stock item by entering two lines in a single inventory transaction. In the first line, enter the source location of the stock items, the current average cost, and the overhead revaluation account. This removes the items from inventory at the current cost. Then in the second line, enter the new cost of the stock items, the same overhead revaluation account, and the destination location. This moves the items back into inventory at the re-valued cost. The balance remaining in the overhead revaluation account is the difference in value.

Re-valuing a damaged item is similar to the steps outlined above. Suppose you find that you have a water heater with cosmetic damage. Because a client will not pay full price for it, you need to re-value it. Create a part for a damaged water heater in the **Parts** window. Then in the **Inventory Allocation** window, make the adjusting entry. In the first line, enter the source location of the water heater, its cost, and the overhead revaluation account. Then in the second line, enter the new part for damaged water heaters, its adjusted cost, the same overhead revaluation account, and the destination location for the re-valued stock items. The transaction leaves the average cost for undamaged items unchanged, and sets the new value for the damaged item.

#### To enter a record to re-value existing inventory:

|  | 1 | Open **12-2 Inventory Allocation**. |
|---|---|---|

|  | 2 | In the **Ticket#** text box, enter the tag or ticket number/letters. |
|---|---|---|

|  | 3 | In the **Date** text box, enter the date of the transfer. |
|---|---|---|

|  | 4 | In the **Status** list, click the record status. |
|---|---|---|

|  | 5 | In the **Description** text box, enter a brief statement about the transaction. |
|---|---|---|

|  | 6 | Enter the original item in the grid: |
|---|---|---|

|  | a | In the **Part** cell, enter the part number. |
|---|---|---|

|  | b | In the **Quantity** cell, enter the quantity of parts. |
|---|---|---|

|  | c | In the **Cost** cell, enter the cost of the part. |
|---|---|---|

|  | d | In the **Source** cell, enter the location where the part is coming from. |
|---|---|---|

|  | e | In the **Account** cell, enter the overhead revaluation account number. |
|---|---|---|

|  | f | In the **Subaccount** cell, if applicable, enter the appropriate subsidiary account. |
|---|---|---|

|  | 7 | Repeat step 6 for each item you want to re-value. |
|---|---|---|

|  | 8 | On the **File** menu, click **Save**. |
|---|---|---|

| Links to more information . . . [About inventory status](About_inventory_status.md) |
|---|
