<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/3-Accounts_Receivable/About_wage_rates_for_time_and_materials_billing.htm (Sage 100 Contractor help v20.5) -->

### About wage rates for time and materials billing

You can assign a table of wage rates to a time and materials (T&M) job in the **3-10-1 T&M Billing Setup** window. Sage 100 Contractor determines the billing amounts using the wage rate table instead of the labour costs.

You can set up wage rates for:

- **Employees assigned specific cost codes.**For example, you create two lines in the table for Michael. On the first line, you assign Michael a cost code for rough carpentry and the associated wage rates. On the second line, you assign him a cost code for supervision and the associated wage rates. When Michael supervises, Sage 100 Contractor knows to bill out his time differently from when he works as a carpenter.
- **Employees.**For example, you list Michael, Robert, Steve, and Gerald in the table with the appropriate wage rates. Because there are no cost codes assigned to the employees, Sage 100 Contractor bills for employee time based on the billing rates assigned to each employee.
- **Cost codes.**For example, you list cost codes for rough carpentry and finish carpentry and the associated wage rates. No matter who performs rough or finish carpentry, that employee is billed out at the appropriate rate based on the cost code.
- **No employee or cost code.**You can only enter one set of default wage rates—rates that do not have employees and cost codes attached to the wage rates.

For example, you set up a line that does not reference an employee or cost code and has the following wage rates at $15, $22.50, and $30. Sage 100 Contractor bills out the work using the indicated rates for any employee or cost code that does not appear in the list.

Sage 100 Contractor first computes billing amounts for employees appearing in the wage rate table that have been assigned cost codes.

Next, Sage 100 Contractor computes billing amounts for employees appearing in the table that have not been assigned cost codes.

Then Sage 100 Contractor computes billing amounts for cost codes appearing in the table that have not been assigned to specific employees.

Finally, Sage 100 Contractor computes billing amounts for all remaining employees and cost codes that do not appear in the wage rate table.

| Links to more information . . . [Entering time and materials wage rates](Entering_time_and_materials_wage_rates.md) [About cost codes and divisions](../6-Project_Management/About_cost_codes_and_divisions.md) [Setting up time and materials jobs](Setting_up_time_and_materials_jobs.md) |
|---|
