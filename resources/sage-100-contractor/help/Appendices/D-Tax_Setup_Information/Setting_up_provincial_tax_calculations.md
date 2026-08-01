<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Appendices/D-Tax_Setup_Information/Setting_up_provincial_tax_calculations.htm (Sage 100 Contractor help v20.5) -->

## Setting Up a Provincial Payroll Tax

To set up a Quebec payroll tax, see [Setting up Quebec payroll tax](Setting_up_Quebec_tax_calculations.md).

To set up a provincial payroll tax, except for Quebec, use the following steps.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To set up a provincial payroll tax](javascript:void(0);)

|  | 1 | Create a provincial tax payroll calculation in **5-3-1 Payroll Calculations**using tax type **7-Provincial Income Tax.** For more information, see [Setting up payroll calculations](../../Modules/5-Payroll/Setting_up_payroll_calculations.md). |
|---|---|---|

|  | 2 | Open **5-2-1 Employees** and select an employee using the data control. |
|---|---|---|

|  | 3 | Click the [**Calculations**] tab. |
|---|---|---|

|  | 4 | In the Province Tax calculation row, do the following: |
|---|---|---|

|  | a | In the **TD1 Claim Code** column, enter the claim code that corresponds to the claim amount on the employee's TD1 form. |
|---|---|---|

|  | b | In the **Other Tax Credits** column, enter any annual provincial non-refundable tax credits requested by the employee. This is where medical expenses or charitable donations authorized by a tax services office or tax centre should be entered. |
|---|---|---|

|  | c | (Optional) If the employee has disabled dependents and works in the Ontario province, enter the number of disabled dependents from the TD1ON form in the **Disabled Dependents** column. |
|---|---|---|

|  | 5 | Select **File > Save**. |
|---|---|---|

Tip:

If you are required by a province where you do business to file an Employer Health Tax (EHT) return, Sage 100 Contractor can track your EHT contributions and produce a report that lists the taxable gross, computed EHT, and EHT liability for each employee, to help you complete the return. Before you can run the **5-1-4-41 Employer Health Tax** report, however, you need to set up a payroll calculation for Employer Health Tax, and assign it to employee records.

There is no dedicated tax type for Employer Health Tax, but you can use **Tax Type = None**.
