<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/6-Project_Management/Entering_the_settings_for_Purchase_Order_Over_Budget_Warning.htm (Sage 100 Contractor help v20.5) -->

### Entering the settings for Purchase Order Over Budget Warnings

The **Over Budget Warning** command notifies you if costs exceed the budgeted amount for a job. When you select the **Set PO Over Budget Warnings** option, Sage 100 Contractor determines the Actual + Committed costs to date for the job and phase by cost code and cost type.

It then compares the data to the original budget plus approved change orders. When you save the record, Sage 100 Contractor notifies you if costs exceed the budget plus approved change orders for a job and phase, cost code and cost type, plus the tolerance.

Notes:

- When Purchase Orders are exported from **9-5 Takeoffs**, the warning that the purchase order exceeds the budget amount plus approved change orders for the job/phase/cost code/ cost type combination is not displayed. After exporting purchase orders, you should run the **6-1-12-21 Committed Costs** report for the correct job to verify that purchase orders have not exceeded the budget.
- To enable the program alert for **Job costs exceed budget for cost code** you must have a setting of Warning for the Message Type in the job cost screen.
- If you decreased a grid line but the purchase order is still over budget, the Purchase Order Over Budget warning will not display a second time when the record saves. To get the warning a second time, increase one of the amounts or quantities in the grid.

#### [![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Example: Using the Flat Amount with Warning](javascript:void(0);)

| Message Type | Warning |
|---|---|
| Tolerance Type | Flat amount |
| Tolerance Amount | $100 |
| Tolerance Percent | N/A |
| Tolerance Amount Not To Exceed | N/A |

A warning dialog box displays "Warning: The actual plus committed costs exceeds the budget and approved changes plus the tolerance amount." You can now save the record by clicking [**Yes**] or cancel out by clicking [**No**]. An alert is also sent to the Dashboard Alert Viewer if you have selected **Job costs exceed budget for cost code** in the **7-6 Alerts Manager**Program Warning Subscriptions tab.

#### To set the Over Budget Warning:

|  | 1 | In **6-6-1 Purchase Orders**, select **Options > Set Over Budget Warning**. |
|---|---|---|

|  | 2 | In the **Message Type** dropdown, the choices are mutually exclusive. Select one of the following: |
|---|---|---|

- **No message**. No message is generated. All options for tolerance are grayed out.
- **Warning.** A warning and/or alert is generated, but you are allowed to save the record.
- **Not allow.** A warning and/or alert is generated, but you are not allowed to save the record.

|  | 3 | If you select **Warning** or **Not Allow**, you must select one of the following choices in the **Tolerance Type** dropdown: |
|---|---|---|

- No tolerance
- Flat amount
- Percent
- Percent/not to exceed

|  | 4 | Once a **Tolerance Type** has been selected, enter the applicable amount or percent for the type: |
|---|---|---|

- **Flat amount.** Enter the amount in the Tolerance Amount text box.
- **Percent.** Enter the percent in the Tolerance Percent text box.
- **Percent/not to exceed.** Enter the percent of the budget plus approved changes by job, phase, cost code, and cost type allowed in the **Tolerance Percent** text box, and the amount of tolerance in the **Tolerance Amount Not To Exceed** text box.

|  | 5 | Click **OK**. |
|---|---|---|

| Links to more information . . . [About displaying budget recaps](About_displaying_budget_recaps.md) [Setting the original budget](Setting_the_original_budget.md) [How change orders affect budgets and proposals and subcontracts](How_change_orders_affect_budgets__proposals__and_subcontracts.md) [About cost codes and divisions](About_cost_codes_and_divisions.md) [Setting up cost types](Setting_up_cost_types.md) |
|---|
