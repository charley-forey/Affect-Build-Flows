<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/9-Estimating__Parts_and_Assemblies_/Exporting_purchase_orders_from_9-5_Takeoffs_to_6-6-1_Purchase_Orders.htm (Sage 100 Contractor help v20.5) -->

### Exporting purchase orders from 9-5 Takeoffs to 6-6-1 Purchase Orders

Note: This functionality is available only if you have the [Estimating Module](http://www.na.sage.com/sage-100-contractor/modules/estimating).

Sage 100 Contractor creates purchase orders for lines assigned to a Vendor.

If a price and/or quantity adjustment occurs after you export purchase orders, you must also adjust the purchase order in **6-6-1 Purchase Orders**.

In addition, if you exported the purchase order previously, the export amount that is displayed changes to the new amount even though the full amount was not exported. An alternate method for making the adjustment in **6-6-1 Purchase Orders** is to re-export the purchase order with the new amount, and then delete the previously exported purchase order in **6-6-1 Purchase Orders**.

When exporting purchase orders from **9-5 Takeoffs** to **6-6-1 Purchase Orders**, remember that:

- Exporting by **Job** exports the combined Vendor total for all bid items.
- Exporting by **Job/Phase** exports the combined Vendor total for all bid items.
- Exporting by **Change Order** exports the combined Vendor total for all **Type-4** items.
- Exporting by **Task** exports the items with a Vendor and Task. To use this option, a Vendor and Task must be assigned to the item on the takeoff line.
- When Purchase Orders are exported from **9-5 Takeoffs**, the warning that the purchase order exceeds the budget amount plus approved change orders for the job/phase/cost code/ cost type combination is not displayed. After exporting purchase orders, you should run the **6-1-12-21 Committed Costs** report for the correct job to verify that purchase orders have not exceeded the budget.

#### To export a purchase order:

1. From the Sage 100 Contractor main menu tree, double-click **9-5 Takeoffs**.
2. In the **Takeoff Launch** window, double-click a job to start a takeoff.
3. On the **Export** menu, point to **Purchase Orders**, and then click one of the following:
   
   - **Job**
   - **Job/Phase**
   - **Change Order**
   - **Task**
4. Select the purchase orders you want to export, and then click **Export**.
5. Close **9-5 Takeoffs**.
6. Open **6-6-1 Purchase Orders**.
7. In the data control text box, enter the record number for the purchase order that you want to view.

| Links to more information . . . [Exporting takeoffs to files](Exporting_takeoffs_to_files.md) [Exporting takeoff prices to part prices](Exporting_takeoff_prices_to_part_prices.md) [Exporting takeoff grids to files](Exporting_takeoff_grids_to_files.md) |
|---|
