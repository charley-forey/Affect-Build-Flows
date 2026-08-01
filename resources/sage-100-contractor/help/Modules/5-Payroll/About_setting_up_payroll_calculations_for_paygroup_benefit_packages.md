<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/5-Payroll/About_setting_up_payroll_calculations_for_paygroup_benefit_packages.htm (Sage 100 Contractor help v20.5) -->

### About setting up payroll calculations for paygroup benefit packages

Use the **5-3-4 Paygroups** window to assign each paygroup its own set of payroll calculations that Sage 100 Contractor uses to compute its associated benefits. First you select the payroll calculations, and then you assign each a rate. When you perform the final compute of the payroll, **5-3-4 Paygroups** is the source for the benefit rates.

In some cases, the calculation methods or the taxes to which a calculation is subject differ from union to union or from job to job. When the calculation method or taxes differ for a similar payroll calculation, you have to set up a separate payroll calculation.

For each paygroup benefit, create a separate payroll calculation in **5-3-1 Payroll Calculations** in the **Calc Method** drop-down list, using the following guidelines:

- You can use most calculation methods for paygroups with the following exceptions: Benefits set up using these methods are excluded from reports.
  
  - 2-%Total Taxable Wages
  - 10-Per Day
  - 11-Per Pay Period,
  - 17-Tables
  - 18-Variable (manual calc)
- Some payroll calculations are computed after a paygroup benefit has been computed and its result has been added to the gross wages. In the **Calc Method** list, click **3-%Gross + Paygroup Benefits**. For example, you might need to compute union dues after the vacation benefit has been added to the gross wage.
- Calculation method **3-%Gross + Paygroup Benefits** requires the calculation to have a calculation number larger than that of the calculation that adds the benefit to the gross wage. Sage 100 Contractor executes each payroll calculation in the order established by the calculation numbers.
- To use the calculation for paygroup benefit packages only, select the **Use in Paygroup Benefits** check box.
- To include the calculation on a union report, under **Reporting**, select the union from the **Union** drop-down list. Union reports can only be included with the calculations of their own union number. If you are using union reports and have more than one union, you must create a set of calculations for each union.
- To include the calculation on certified payroll reports, under **Reporting**, select the type of benefit in the **Benefit** list.

You can use the same payroll calculation in different paygroups, but assign different rates.

| Links to more information . . . [About payroll calculations](About_payroll_calculations.md) [About calculation methods](About_calculation_methods.md) |
|---|
