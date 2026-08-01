<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/4-Accounts_Payable/Entering_settings_for_the_Invoice_Over_Purchase_Order_Warning.htm (Sage 100 Contractor help v20.5) -->

### Entering settings for the Invoice Over Purchase Order Warning

The **Set Over PO Warning** command notifies you if the invoice exceeds the purchase order for a job. When you select the **Set Over PO Warning** option, Sage 100 Contractor compares the invoice total amount (not including PST/HST/GST) against the total PO balance. If it exceeds it, then it is compared against the tolerance settings.

Notes:

- The Invoice Over Purchase Order warning in 4-2 Payable Invoices/Credits is global and set for all vendors except the vendors that have the Vendor Invoice Over Purchase Order warning set in **4-4 Vendors**. The Vendor Invoice Over Purchase Order warning set in 4-4 overrides the Invoice Over Purchase Order warning setting in 4-2.
- When you save the Invoice Over Purchase Order warning setting in 4-2 Payable Invoices/Credits, if vendors have Vendor Invoice Over Purchase Order warning settings you get the following message with the list of vendors with settings: The following vendors have their own invoice over PO Warning Settings that supersede this company wide Invoice Over PO Warning.
- QST calculations do not trigger these warnings.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Example: Using the Flat Amount with Warning](javascript:void(0);)

| Message Type | Warning |
|---|---|
| Tolerance Type | Flat amount |
| Tolerance Amount | $100 |
| Tolerance Percent | N/A |
| Tolerance Amount Not To Exceed | N/A |

A warning dialog box displays "Warning: The invoiced amount of this record exceeds the remaining balance on the designated purchase order plus the tolerance amount." You can now save the record by clicking [**Yes**] or cancel out by clicking [**No**]. An alert is also sent to the Dashboard Alert Viewer if you have selected **Payable invoices exceed purchase order total** in the **7-6 Alerts Manager**Program Warning Subscriptions tab.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To set the Invoice Over Purchase Order Warning](javascript:void(0);)

|  | 1 | In **4-2 Payable Invoices/Credits**, select **Options > Set Over PO Warning**. |
|---|---|---|

|  | 2 | In the **Message Type** dropdown, the choices are mutually exclusive. Select one of the following: |
|---|---|---|

- **No message.** No message is generated. All options for tolerance are grayed out.
- **Warning.** A warning and/or alert is generated, but you are allowed to save the record.
- **Not allow.** A warning and/or alert is generated, but you are not allowed to save the record.

|  | 3 | If you select **Warning** or **Not Allow**, you must select one of the following choices in from **Tolerance Type** list: |
|---|---|---|

- No tolerance
- Flat amount
- Percent
- Percent/not to exceed

|  | 4 | Once a **Tolerance Type** has been selected, enter the amount or percent for the type: |
|---|---|---|

- Flat amount. Enter the amount in the Tolerance Amount text box.
- Percent. Enter the percent in the Tolerance Percent text box.
- Percent/not to exceed. Enter the percent of the purchase order allowed in the **Tolerance Percent** text box, and the amount of tolerance in the **Tolerance Amount Not To Exceed** text box.

|  | 5 | Click **OK**. |
|---|---|---|

| Links to more information . . . [About displaying budget recaps](../6-Project_Management/About_displaying_budget_recaps.md) [Setting the original budget](../6-Project_Management/Setting_the_original_budget.md) [How change orders affect budgets and proposals and subcontracts](../6-Project_Management/How_change_orders_affect_budgets__proposals__and_subcontracts.md) [About cost codes and divisions](../6-Project_Management/About_cost_codes_and_divisions.md) [Setting up cost types](../6-Project_Management/Setting_up_cost_types.md) |
|---|
