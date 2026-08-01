<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/5-Payroll/Setting_up_payroll_calculations.htm (Sage 100 Contractor help v20.5) -->

### Setting up payroll calculations

The taxes to which calculations are subject vary by province or territory. Verify the selections with your accountant, or if it is a benefit, the benefit plan administrator.

For details on setting up tax calculations for specific provinces or territories, see [About tax setup information.](../../Appendices/D-Tax_Setup_Information/About_tax_setup_information.md)

Caution! Verify that all your calculations are correct before running a trial-compute of your payroll. If you are unsure about the results, contact Customer Support or your business partner for assistance.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To set up payroll calculations](javascript:void(0);)

1. Open **5-3-1 Payroll Calculations**.
2. In the data control box, enter the number you want to assign the new calculation.
3. In the **Description** box, enter a brief statement about the calculation.
4. In the **Tax Type** list, click the type of earning, accrual, or deduction that you are setting up.
5. Depending on the tax type you selected, make additional selections as required for:
   
   - **Calculation Type.** If you selected **None** as the Tax Type, you need to specify the type of earning, accrual, or deduction.
   - **Calculation Method.** This list is available if you selected **None** or **19 - Employee RPP Contributions** as the Tax Type. Click the method to use to compute the earning, accrual, or deduction,
   - **Based On.** This list is available if you selected **None** as the Tax Type and **7 - %Other Calculation** for the Calculation Method. Click the type of amount on which to base the payroll calculation.
   - **Default Rate.**Enter the standard calculation rate. Important! When you use calculation method **17-Tables** for federal or provincial income taxes, Sage 100 Contractor sets the rate. The rate does not appear in the payroll calculation or the employee record.
   - **Default Max.** Enter the calculation maximum.
   - **Max Type.** Click the type of maximum for the calculation. Note: If you plan to set maximum wages for workers' compensation codes for states other than Ohio, New York, and Nevada, you must select **4-Wages/Year**.
6. Specify the accounts that will be affected by this payroll calculation: Important! The **Credit Account** and **Credit Subaccount** are typically liability accounts. You must specify a **Credit Account**, but a **Credit Subaccount** is only necessary dependent upon your general ledger setup.
   
   1. In the **Job Expense**, **Shop Expense**, **Overhead Expense**, and **Admin Expense** boxes, enter the ledger account numbers to debit for each type of expense.
   2. In the **Credit Account** box, enter the liability account number to credit.
   3. In the **Credit Subaccount** box, enter the ledger subaccount number to credit. Note: If you want to use the employee number as the subsidiary account number, click **Use employee# as subaccount**.
7. Under **Subject to**, verify the deductions to which the calculation is subject.
8. In the **Tax Area**, if the calculation is for a specific province, enter the province abbreviation in the **Tax Province** box.
9. Under **Reporting**:
   
   1. To include the calculation on a union report, select the union from the **Union** list.
   2. To include the payroll calculation on certified payroll reports, select the type of benefit in the **Benefit** list.
   3. To report the calculation total in a box on T-4 slips, enter the box number in the **T-4 Box** field.
   4. To exclude the calculation from T-4 slips, select the **Exclude from T-4 slips** box.
10. Select the following check boxes that apply to the payroll calculation:
    
    - Use in Paygroup Benefits
    - Display on Cheques
    - Disposable Earnings
    - Default to New Employees
11. On the **File** menu, click **Save**.

| Links to more information . . . [About calculation types](About_calculation_types.md) [About pre-built standard payroll calculations](About_pre-built_standard_payroll_calculations.md) [About accruing vacation amounts](About_accruing_vacation_amounts.md) [Creating standard payroll calculations](Creating_standard_payroll_calculations.md) [Payroll calculation check boxes](Payroll_calculation_check_boxes.md) [About the T-4 Box in payroll calculations](About_W-2_Box_and_W-2_Code_in_payroll_calculations.md) [About tax tables for setting up federal and provinciale tax calculations](About_tax_tables_for_setting_up_federal_and_state_tax_calculations.md) |
|---|
