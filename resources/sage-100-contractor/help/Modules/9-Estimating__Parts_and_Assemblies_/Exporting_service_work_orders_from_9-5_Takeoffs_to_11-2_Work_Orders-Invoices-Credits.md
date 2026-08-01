<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/9-Estimating__Parts_and_Assemblies_/Exporting_service_work_orders_from_9-5_Takeoffs_to_11-2_Work_Orders-Invoices-Credits.htm (Sage 100 Contractor help v20.5) -->

### Exporting service work orders from 9-5 Takeoffs to 11-2 Work Orders-Invoices-Credits

Note: This functionality is available only if you have the [Estimating Module](http://www.na.sage.com/sage-100-contractor/modules/estimating).

You can export a single grid from a takeoff or an entire takeoff to the **11-2 Work Orders/Invoices/Credits** window.

When you export a grid, job and client information from the current grid are included on the work order record.

When export a takeoff, Sage 100 Contractor copies all the lines from all the bid items and phases from the **Takeoff Details** grids and inserts them in the **Invoice Details** grid in the **11-2 Work Orders/Invoices/Credits** window, with a blank line separating each bid item or phase section.

Important! Insurance, use tax, and bonding amounts must be zero before you can export a takeoff to **11-2 Work Orders**.

If you have a **Gross Margin Override**, Sage 100 Contractor exports as if the **Bid Amount** is locked. Markup information is inserted directly into the work order as follows:

- **Markup %** goes to either the **Taxable** or **Non-Tax Markup %** text boxes in the **11-2 Work Orders/Invoices/Credits** window.
- **Dollar Markup** goes to either the **Taxable**or **Non-Tax Markup $** text boxes in **11-2 Work Orders/Invoices/Credits**.
- Job and client information are included in the work order record. Address and contact information from the job record or the client record are included .

#### To export a takeoff as a work order:

1. From the Sage 100 Contractor main menu tree, double-click **9-5 Takeoffs**.
2. In the **Takeoff Launch** window, double-click a job to start a takeoff.
3. If you are exporting the current grid: If you are exporting the entire takeoff, skip this step.
   
   1. From the **Bid Item** list, select a bid item.
   2. From the **Phase** list, select a phase.
4. On the **Export** menu, point to **Service Work Order**, and then select one of the following commands: Sage 100 Contractor opens the **11-2 Work Orders/Invoices/Credits** window.
   
   - **Current Grid Only**
   - **Entire Takeoff**
5. Continue working with the service work order in the **11-2 Work Orders/Invoices/Credits** window.
6. From the **Type** list, select an invoice type.
7. On the **File** menu, click **Save**.

Important! You must have security access to **11-2 Work Orders/Invoices/Credits** to export a takeoff or a grid as a work order. Without rights, the export is blocked.

Notes:

- If you lock the **Bid Amount** on **9-5 Takeoffs**or have a **Gross Margin Override**, Sage 100 Contractor locks the **Billing Amount** in **11-2 Work Orders**.
- The **11-2 Work Orders** window calculates PST if the **Subject to PST** column is set to **Yes**. The **11-2 Work Orders** window also calculates GST or HST if it is required for the client's province, independent of PST.
- There may be a small variance between the bid amount in **9-5 Takeoffs** and the work order total in **11-2 Work Orders** due to rounding.
- When exporting **Current Grid Only**, Sage 100 Contractor exports only the grid you displayed.

| Links to more information . . . [Exporting grids from 9-5 Takeoffs to 11-2 Work Orders](Exporting_grids_from_9-5_Takeoffs_to_11-2_Work_Orders.md) [Adjusting bid totals with a bid amount override](Adjusting_bid_totals_with_a_bid_amount_override.md) Including tax costs in 9-5 Takeoffs |
|---|
