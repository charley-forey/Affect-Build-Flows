<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/5-Payroll/About_calculation_methods.htm (Sage 100 Contractor help v20.5) -->

### About calculation methods

The calculation method tells Sage 100 Contractor how to use the calculation.

For example, if a calculation uses a per hour calculation method, Sage 100 Contractor multiples the number of hours worked by the rate assigned to the calculation.

- **Percent Gross Pay (unadjusted)**: Computes a percent of the gross wages.
- **Percent Total Taxable Wages**: Computes a percentage of the EI wages (Taxable wages = gross pay + taxable add-ons – non-taxable deductions). You can use this calculation method for employer calculations that are not subject to taxes, and employee deductions that are subject to all taxes and do not use calculation types 2-Add to Gross or 4-Add/Deduct (taxable). Do not use calculation method 2-Percent Total Taxable Wages for a deduction that is not subject to all taxes, such as most retirement plans.
- **Percent Gross + Paygroup Benefits**: Computes a percentage of the EI wages (Taxable wages = gross pay + taxable add-ons – non-taxable deductions). You can only use this calculation for paygroup benefit packages because Sage 100 Contractor only looks at the taxable add-ons and non-taxable deductions in the paygroup. Calculation method 3-Percentage Gross + Paygroup Benefits requires the calculation to have a calculation number larger than the calculation that adds the benefit to the gross wage. Sage 100 Contractor executes each payroll calculation in the order established by the calculation numbers.
- **Percent Regular Pay (regular hours only)**: Computes a percent of the regular pay based on regular hours only, and does not include any pay from hours marked as overtime or premium. For example, if an employee works an eight-hour day plus two hours of overtime, Sage 100 Contractor computes the percent based on eight hours of regular pay.
- **Percent Regular Pay (all hours)**: Computes a percent of the regular pay based on all hours worked, including overtime and premium hours. For example, if an employee works an eight-hour day plus two hours of overtime, Sage 100 Contractor computes the percent based on ten hours of regular pay.
- **Percent Disposable Income (net)**: Computes a percent of the net pay after taxes. If two or more wage attachments apply to the same employee and you use 6-Percent Disposable Income (net) as the means of calculation, you may need to combine the calculations to withhold the correct amount.
- **Percent Other Calculation** : Computes an amount based on the result from another calculation. Calculation method 7-Percent Other Calculation requires you to select the prior calculation on which you are basing this calculation. In the Based on list, click the calculation you want to use. The based on calculation on must have a calculation number smaller than the current, payroll calculation number. Sage 100 Contractor executes each payroll calculation in the order established by the calculation numbers.
- **Per Hour (all hours)**: Multiplies the rate by the number of hours worked.
- **Per Hour (regular hours only)**: Multiplies the rate by the number of regular hours worked. This excludes overtime and premium hours.
- **Per Day**: Computes an amount based on the number of days worked.
- **Per Pay Period**: Computes a flat amount each pay period.
- **Regular/Overtime/Premium (0*, 1*, 1*)**: Computes overtime and premium wages for add-ons or benefits using overtime and premium wage rates indicated in the employee record. Sage 100 Contractor calculates overtime wages at the rate, and calculates premium wages at the rate.
- **Regular/Overtime/Premium (0*, 1.5*, 2*)**: Computes overtime and premium wages for add-ons or benefits using overtime and premium wage rates indicated in the employee record. Sage 100 Contractor calculates overtime wages at 1.5 times the rate, and calculates premium wages at 2 times the rate.
- **Regular/Overtime/Premium (1*, 1.5*, 1.5*)**: Computes regular, overtime, and premium wages using regular, overtime, and premium wage rates indicated in the employee record. Sage 100 Contractor calculates overtime wages at 1.5 times the rate, and calculates premium wages at 1.5 times the rate.
- **Regular/Overtime/Premium (1*, 1.5*, 2*)**: Computes regular, overtime, and premium wages using regular, overtime, and premium wage rates indicated in the employee record. Sage 100 Contractor calculates overtime wages at 1.5 times the rate, and calculates premium wages at 2 times the rate.
- **Regular/Overtime/Premium (1*, 2*, 2*)**: Computes regular, overtime, and premium wages using regular, overtime, and premium wage rates indicated in the employee record. Sage 100 Contractor calculates overtime wages at 2 times the rate, and calculates premium wages at 2 times the rate.
- **Tables**: Computes taxes using rates from a tax table. Sage 100 Contractor contains the necessary federal and provincial tax tables, but does not display the rates and maximums.
- **Variable (manual calculation)**: Allows you to enter a rate in the payroll record before the final-compute.

| Links to more information . . . [About reviewing rates in tax tables](About_reviewing_rates_in_tax_tables.md) [About calculations in payroll records](About_calculations_in_payroll_records.md) [About paygroups](About_paygroups.md) [Entering benefits packages for paygroups](Entering_benefits_packages_for_paygroups.md) [About tax types](About_tax_types.md) [About calculation types](About_calculation_types.md) |
|---|
