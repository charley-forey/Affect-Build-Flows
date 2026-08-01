<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/6-Project_Management/Entering_the_settings_for_Subcontract_Over_Budget_Warning.htm (Sage 100 Contractor help v20.5) -->

### Entering the settings for Subcontract Over Budget Warnings

The **Over Budget Warning** command notifies you if costs exceed the budgeted amount for a job. When you select the **Set Subcontract Over Budget Warnings** option, Sage 100 Contractor determines the Actual + Committed costs to date for the job and phase by cost code and cost type.

It then compares the data to the original budget plus approved change orders. When you save the record, Sage 100 Contractor notifies you if costs exceed the budget plus approved change orders for a job and phase, cost code and cost type, plus the tolerance.

Notes:

- When Subcontracts are exported from **9-5 Takeoffs**, the warning that the subcontract exceeds the budget amount plus approved change orders for the job/phase/cost code/ cost type combination is not displayed. We recommend that after exporting subcontracts you should run the **6-1-12-21 Committed Costs** report for the correct job to verify that subcontracts have not exceeded the budget.
- If you decreased a grid line but the subcontract is still over budget, the Subcontract Over Budget warning will not display a second time when the record saves. To get the warning a second time, increase one of the amounts or quantities in the grid.

#### Example: Using the Flat Amount with Warning

| Message Type | Warning |
|---|---|
| Tolerance Type | Flat amount |
| Tolerance Amount | $100 |
| Tolerance Percent | N/A |
| Tolerance Amount Not To Exceed | N/A |

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To set the Over Budget Warning](javascript:void(0);)

|  | 1 | In **6-7-1 Subcontracts**, select **Options > Set Over Subcontract Warning**. |
|---|---|---|

|  | 2 | In the **Message Type** dropdown, the choices are mutually exclusive. Select one of the following: |
|---|---|---|

- **No message.** No message is generated. All options for tolerance are grayed out.
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
