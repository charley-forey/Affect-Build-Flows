<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/5-Payroll/Calculation_type_1-Deduct_from_Employee.htm (Sage 100 Contractor help v20.5) -->

### Calculation type 1-Deduct from Employee

**Payroll Taxes.**For each payroll tax, set up a payroll calculation.

If your company performs work in different provinces, set up a payroll calculation for every province in which your employees work.

At the calendar year-end, verify the tax rates and maximums for each calculation. Sage 100 Contractor provides Federal and Provincial tax updates each year.

Payroll Advance. Create a calculation for payroll advances. Sage 100 Contractor automatically recovers the advance for you.

Tool Purchases. Some companies allow employees to purchase personal tools from vendors using the company account. You can set up a payroll calculation to deduct the employee’s purchases from his or her pay cheque.

When you post the vendor’s original invoice for the tool purchase, post it to the **Small Tools** account in the **Overhead Expense** range of accounts. To then deduct the tool purchases from an employee’s pay cheque, set up the payroll calculation to post a credit to the **Small Tools** account. Because the amount deducted from an employee’s pay cheque varies based on the cost of the tools purchased, select calculation method **18-Variable (manual calculation)**.

While you can deduct the cost of tools from the employee’s pay cheque, it is a better practice for employees to reimburse tool purchases through personal cheques, made payable to your company.

Health Insurance. Create a payroll calculation to deduct the employee’s portion of the cost for medical insurance. Usually this is a fixed amount per month.

If you need to deduct the health insurance each pay period, convert the monthly amount to a per-period amount. From the monthly amount, compute the annual amount and divide by the number of pay periods in a year. If your company pays its employees weekly, for example, divide the annual amount by 52. Then enter the per-period amount in each employee’s record on the **Calculations** tab.

When employees cannot earn pay cheques regularly, due to weather or other circumstances, set up the **Health Insurance** calculation with a maximum type of **6-Dollars/Month**. Then on the **Calculations** tab in the employee records, enter an accelerated rate and a monthly maximum for the payroll calculation.

Garnishments. (Child support, Previous Year Income Taxes, Court Judgments, and so on) Create a payroll calculation for each type of garnishment. If similar garnishments require different methods of calculation, create a separate calculation for each garnishment.

Suppose you need to garnish the wages of two employees for child support, and a third employee’s wages for back taxes. The first employee’s garnishment is for a set dollar amount each pay period and the second employee’s garnishment is for a percentage of the net pay. Set up two separate calculations for child support garnishments, though both can post to the same payable account. Then set up a third calculation for the garnishment of back taxes, which posts to a different payable account.

If you want to post each garnishment to a different ledger account, create the separate ledger accounts in the **Current Liabilities** range of accounts. Select the **Employee Number as Subaccount** check box to post the garnishment to a subsidiary ledger account using the employee’s record number as the subsidiary account number.

Some methods of computing garnishments might be too complex for Sage 100 Contractor to automatically calculate, such as a percentage of the net pay with a minimum or maximum amount. In this case, set up a payroll calculation with a variable calculation method.

**Pension Plans.** Many pension plans allow employees to contribute a flat amount or a percent of the employee’s pay cheque. You may need to create two payroll calculations and assign the appropriate calculation to each employee based on how he or she wants to contribute.

To create a pension plan deduction, set up the payroll calculation with tax type **19-Employee RPP Contributions** and calculation type **1-Deduct from Employee**. Because each employee can choose the flat amount or percent of his or her pay cheque to contribute, enter the employee’s amount or rate in the **Calculations** tab of each employee record.

To post the credit, set up a separate ledger account in the **Current Liabilities** range of accounts. Select the **Employee Number as Subaccount** check box to post each employee’s contribution to a subsidiary ledger account using the employee’s record number as the subsidiary account number. The subsidiary accounts help you manage the individual employee contributions, and know what amount to pay on behalf of each employee.

| Links to more information . . . [Recovering payroll advances](Recovering_payroll_advances.md) [About calculation methods](About_calculation_methods.md) [About calculations in employee records](About_calculations_in_employee_records.md) [About tax types](About_tax_types.md) [Setting up controlling ledger accounts and subaccounts](../1-General_Ledger/Setting_up_controlling_ledger_accounts_and_subaccounts.md) |
|---|
