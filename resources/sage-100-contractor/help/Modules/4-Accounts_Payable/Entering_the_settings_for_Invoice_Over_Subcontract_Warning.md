<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/4-Accounts_Payable/Entering_the_settings_for_Invoice_Over_Subcontract_Warning.htm (Sage 100 Contractor help v20.5) -->

### Entering settings for the Invoice Over Subcontract Warning

When you select the **Set Over Subcontract Warning** option, Sage 100 Contractor compares each line of the invoice against the corresponding subcontract line.

When an invoice is saved with a subcontract, the individual lines on the invoice are compared to the corresponding lines on the subcontract line remaining amount, plus the tolerance. The percent of tolerance is calculated from the line's subcontract amount.

Notes:

- This option is only visible to company administrators.
- This warning will not work for subcontracts entered prior to version 14.2 when new columns were added to the subcontract grid.

#### [![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Example: Using the Flat Amount with Warning](javascript:void(0);)

| Message Type | Warning |
|---|---|
| Tolerance Type | Flat amount |
| Tolerance Amount | $100 |
| Tolerance Percent | N/A |
| Tolerance Amount Not To Exceed | N/A |

#### To set the invoice over subcontract warning:

|  | 1 | In **4-2 Payable Invoices/Credits**, select **Options > Set Over Subcontract Warning**. |
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
- **Percent/not to exceed.** Enter the percent of the subcontract line contract amount allowed in the **Tolerance Percent** text box, and the amount of tolerance in the **Tolerance Amount Not To Exceed** text box.

|  | 5 | Click OK. |
|---|---|---|

| Links to more information . . . [About displaying budget recaps](../6-Project_Management/About_displaying_budget_recaps.md) [Setting the original budget](../6-Project_Management/Setting_the_original_budget.md) [How change orders affect budgets and proposals and subcontracts](../6-Project_Management/How_change_orders_affect_budgets__proposals__and_subcontracts.md) [About cost codes and divisions](../6-Project_Management/About_cost_codes_and_divisions.md) [Setting up cost types](../6-Project_Management/Setting_up_cost_types.md) |
|---|
