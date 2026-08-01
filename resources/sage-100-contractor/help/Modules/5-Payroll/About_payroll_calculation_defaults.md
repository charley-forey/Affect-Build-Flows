<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/5-Payroll/About_payroll_calculation_defaults.htm (Sage 100 Contractor help v20.5) -->

### About payroll calculation defaults

Important! The **Default Rate**, **Default Max** and **Max Type** boxes in **5-3-1 Payroll Calculations** are defaults. When you create standard payroll calculations, these amounts are automatically created for many of the calculations. This information from **5-3-1 Payroll Calculations** is not used to compute payroll; however, **Max Type** is used when the records are computed.

#### Default Rate

When entering the default rate, ask yourself: Will a default rate help me when entering new employees?

Some calculations apply to all employees and have fixed rates, such as Canada Pension Plan and Employment Insurance taxes. Other calculations apply to all employees but may have varying rates, such as health insurance premiums and other benefits. Some other additional calculations apply to only a subset of employees and may have fixed rates too.

When entering default rates, it is very important to remember that this field is only a default. The actual rate used when payroll records are computed comes from either the individual employee record or the paygroup.

If there is a common rate, you may want to enter it so that it will then default to the employee record when entering a new employee. You may feel, however, that it is “safer” to require yourself to directly enter the rate for each employee to ensure having the correct rate every time rather than having an incorrect default accepted.

Moreover, some default calculations apply to only a subset of employees and may have varying rates, such as child support and other wage garnishments. There is no common rate for this group because this calculation doesn't apply to most employees, and therefore the common rate is actually zero.

#### Default Max

When considering the default maximum, use the same criteria as you use for the default rate. Ask yourself this question: Will a maximum rate help me when entering new employees?

#### Max Type

Wage-based maximum types mean that the calculation stops computing when the employee’s wages reach the maximum level.

This kind of maximum is usually used in connection with tax calculations because they are usually published in this style by the government agency.

- Per Quarter and Per Year types are based on wages that are subject to Canada Pension Plan.
- Per Cheques and Per Month types are based on unadjusted gross wages.

Dollar-based maximum types mean that the calculation stops computing when the amount of the calculation reaches the maximum level.

This kind of maximum is useful when a dollar amount needs to be calculated without regard to the employee’s earnings. For example, you may want to calculate an employer-matching 401(k) at 50% of what the employee contributes, but the matching is not to exceed $1,000 per year.

- Per Year types are based on all computed payrolls to date.
- Per Quarter types are based on all computed payrolls assigned to the same quarter number that is on the current payroll record.
- Per Month types are based on all computed payrolls that have a cheque date in the same month as the current payroll record. Important! It is important to enter the correct cheque date on the payroll records prior to computing so that Sage 100 Contractor is aware of the month to which the current payroll is assigned.

- **Per Cheques** types are based solely on the current payroll record.

| Links to more information . . . [About pre-built standard payroll calculations](About_pre-built_standard_payroll_calculations.md) [Creating standard payroll calculations](Creating_standard_payroll_calculations.md) [Setting up payroll calculations](Setting_up_payroll_calculations.md) |
|---|
