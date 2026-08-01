<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/5-Payroll/Calculation_type_3-Employer_Cost.htm (Sage 100 Contractor help v20.5) -->

### Calculation type 3-Employer Cost

Note: Calculations type 3-Employer Cost can be used can be used to accrue virtually any type of employer cost.

**Payroll Taxes.**For each payroll tax, set up a payroll calculation.

If your company performs work in different provinces, set up a payroll calculation for every province in which your employees work.

At the calendar year-end, verify the tax rates and maximums for each calculation. Sage 100 Contractor provides Federal and Provincial tax updates each year.

Workers’ Compensation Insurance. When you set up a payroll calculation for Workers’ Compensation, Sage 100 Contractor uses the rates set up in the **Workers’ Compensation** window. Select **17-Tables** as the calculation method.

Liability Insurance. You can set up the liability insurance calculation to use the rates from the Workers’ Compensation window. Select **17-Tables** as the calculation method, and credit the account to which you post the insurance payments.

Generally, liability insurance covers field employees and sometimes the owner, but not office employees. For each exempt employee, change the payroll calculation’s rate to 0 on the **Calculations** tab of the employee record.

Some companies compute the liability insurance as a percent of gross pay. In the **Tax Type** list, click **0-None**. In the **Calculation Method** list, click **1-Percent Gross Pay**. The rate is usually the same as the payroll rate on the insurance policy.

Health Insurance. Set up a payroll calculation to deduct the employer’s portion of the cost for medical insurance. The amount is usually a fixed rate per month.

To deduct the health insurance each pay period, convert the monthly amount to a per-period amount. First, convert the monthly amount to an annual amount, then divide by the number of pay periods in a year. If your company pays its employees weekly, for example, divide the annual amount by 52.

**Pension Plans.** To create a pension deduction, set up the payroll calculation as follows: tax type **0-None** and calculation type **3-Employer Cost**. Because each employee can choose to contribute either a flat amount or percent of his or her pay cheque, you might have to create two calculations.

To post the credit, you can post to the same account used to post the employees’ deductions for the pension plan, or you can set up a separate ledger account in the **Current Liabilities** range of accounts. Whether you post the employer portion of the pension plans to subsidiary accounts depends on your particular needs.

Union shops or open shops that perform Davis-Bacon or prevailing-wage work should not use subsidiary accounts to track the individual matching amounts. To make the payment, each subsidiary account would have to be referenced on the cheque. Instead, you can use the certified payroll reports to track the amounts paid. If you are using paygroups, you need to enter the pension rates in the **Paygroup Benefits** window.

Select the **Employee Number as Subaccount** check box to post each employee’s contribution to a subsidiary ledger account using the employee’s record number as the subsidiary account number. The subsidiary accounts help you manage the individual employee contributions, and know what amount to pay on behalf of each employee.

**Tool Use:** You can recover the cost of small tools by setting up a calculation for a flat rate per hour that applies to all working field employees. To determine the hourly rate, look at the amount your company spent purchasing small tools for a time, such as the previous year. Then divide that amount by the number of hours worked by field employees during the same time. For employees that do not work in the field, change the rate to 0 in the Calculations tab in the employee records.

| Links to more information . . . About local payroll taxes [About Workers Compensation](About_Workers__Compensation.md) [About calculations in employee records](About_calculations_in_employee_records.md) [Entering benefits packages for paygroups](Entering_benefits_packages_for_paygroups.md) [Setting up controlling ledger accounts and subaccounts](../1-General_Ledger/Setting_up_controlling_ledger_accounts_and_subaccounts.md) [Using expense pools to recover costs for small tools or equipment](../8-Equipment_Management/Using_expense_pools_to_recover_costs_for_small_tools_or_equipment.md) |
|---|
