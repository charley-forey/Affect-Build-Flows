<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/7-Utilities/About_Program_Warnings.htm (Sage 100 Contractor help v20.5) -->

## About Program Warnings

Program warnings are displayed to users during processing, but a user can continue with processing regardless of a warning.

If you want to be alerted whenever a user ignores a program warning, subscribe to the program warning in the **7‑9 Alerts Manager** window. You can choose to be notified about a particular program warning by email or through the dashboard.

#### Transaction date doesn't match the posting period

When you save a transaction, Sage 100 Contractor can compare the transaction date to the period to ensure you post to the correct period. If the transaction date does not fall in the correct posting period, Sage 100 Contractor warns you, but does not prevent you from posting the transaction.

To verify the date and period, in the **1-8 General Ledger Setup** window, select the Verify Date/Period check box. [How?](../1-General_Ledger/Verifying_the_date_and_period.md)

#### Subcontract exceeds budget for cost code

When you save a subcontract, Sage 100 Contractor can warn you if actual plus committed costs for a cost code exceed the budget (including changes and the tolerance amount). Sage 100 Contractor does not prevent you from saving the subcontract when it displays a warning.

To use this warning, in the **6‑7‑1 Subcontracts** window, select **Options** > **Set Subcontract Over Budget Warnings**, and then set the Message Type to Warnings and specify a tolerance type.

#### PO exceeds budget for cost code

When you save a purchase order, Sage 100 Contractor can warn you if actual plus committed costs for a cost code exceed the budgeted amount (including changes and the tolerance amount). Sage 100 Contractor does not prevent you from saving the purchase order when it displays a warning.

To use this warning, in the **6‑6‑1 Purchase Orders** window, select **Options** > **Set PO Over Budget Warnings**, and then set the Message Type to Warnings and specify a tolerance type.

#### Job Costs exceed budget for cost code

The Over Budget Warning command notifies you if costs exceed the budgeted amount for a job. When you select the Over Budget Warning command, Sage 100 Contractor determines the costs to date plus committed costs for the jobs by phase, cost code, and cost type. It then compares the data to the original budget plus change orders. When you save the record, Sage 100 Contractor notifies you if costs exceed the budgeted amount for a job.

To use this warning, the Set Over Budget Warning option must be selected and configured for any Job Cost entry window. [How?](../6-Project_Management/Entering_the_settings_for_Cost_Over_Budget_Warning.md)

#### Job costs posted with no budget for cost code

When you select the Budget Verification command, Sage 100 Contractor compares the cost codes and cost types on the job cost screen against the cost codes and cost types in the budgets. When you save the record, Sage 100 Contractor notifies you if a line item does not appear in the budget of a job.

To use this warning, the Budget Verification option must be selected in a Job Cost entry window. [How?](../5-Payroll/Checking_for_budgeted_cost_codes_and_cost_types.md)

#### Payable invoices exceed subcontract total

When saving a payable invoice for a vendor, Sage 100 Contractor refers to the Set Over Subcontract Warning option to determine if the invoice amount exceeds the subcontract balance. If the payable invoice does exceed the balance, Sage 100 Contractor provides you with a warning.

To use this warning, **4-2 AP Invoice > Options > Set Over Subcontract Warning** must be selected and configured. [How?](../4-Accounts_Payable/Verifying_subcontract_balances.md)

Note: When Subcontracts are exported from **9-5 Takeoffs**, the warning that the subcontract exceeds the budget amount plus approved change orders for the job/phase/cost code/ cost type combination is not displayed. After exporting subcontracts through **9-5 Takeoffs**, you should run the **6-1-12-21 Committed Costs** report for the correct job to verify that subcontracts have not exceeded the budget.

#### Payable invoice posted without an expected PO

When saving a payable invoice for a vendor, Sage 100 Contractor refers to the selection made in the Purchase Order Warning list in the vendor’s record. If the payable invoice does not meet the criteria, Sage 100 Contractor provides you with a warning.

To use this warning, **4-4 Vendor > Invoice Defaults Tab > PO Warning > 1—Warn if no PO** must be selected.

#### Payable invoices exceed purchase order total

When saving a payable invoice for a vendor, Sage 100 Contractor refers to the selection made in the Set Over PO Warning settings in **4-2 Payable Invoices/Credits** or **4-4 Vendors (Accounts Payable)**. The setting in **4-4 Vendors (Accounts Payable)** overrides the setting in **4-2 Payable Invoices/Credits**. If the payable invoice does not meet the criteria, Sage 100 Contractor warns you.

To use this warning, **4-4 Vendor > Options > Set Over PO Warning** must be selected and configured. [How?](../4-Accounts_Payable/Entering_settings_for_the_Vendor_Invoice_Over_Purchase_Order_Warning.md)

Note: When Purchase Orders are exported from **9-5 Takeoffs**, the warning that the purchase order exceeds the budget amount plus approved change orders for the job/phase/cost code/ cost type combination is not displayed. After exporting purchase orders, you should run the **6-1-12-21 Committed Costs** report for the correct job to verify that purchase orders have not exceeded the budget.

#### Inventory location has insufficient part quantity on service invoice

When you select the Verify Stock on Save command, Sage 100 Contractor checks whether you have enough stock in the specified inventory location. If there is not enough stock available, Sage 100 Contractor warns you.

To use this warning, **11-2 > Options > Verify Stock on Save** must be selected. [How?](../12-Inventory/Verifying_stock_availability.md)

#### Inventory location has insufficient part quantity on inventory allocation

When you select the Verify Stock on Save command, Sage 100 Contractor checks whether you have enough stock in the specified inventory location. If there is not enough stock available, Sage 100 Contractor warns you.

To use this warning, **12-2 Inventory Allocation > Options > Verify Stock on Save** must be selected. [How?](../12-Inventory/Verifying_stock_availability.md)
