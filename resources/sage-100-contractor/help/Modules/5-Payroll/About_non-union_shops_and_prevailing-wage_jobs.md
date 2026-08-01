<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/5-Payroll/About_non-union_shops_and_prevailing-wage_jobs.htm (Sage 100 Contractor help v20.5) -->

### About non-union shops and prevailing-wage jobs

When an open-shop contractor receives a contract for a Davis-Bacon job, the contractor is required to provide his employees the wages and benefits package as stipulated by the governing agency, usually union scale for the area.

For example, a union local might provide a health care benefit that the open-shop contractor does not. For work performed on the prevailing-wage job, the contractor is required to pay his employees the money that would otherwise be paid for a health care benefit if it were a union shop.

The governing agency determines the prevailing wage and benefits package requirements for each job. To manage the requirements for each prevailing-wage job, use paygroups to set up a separate wage group for each category of worker. When entering a timecard, you specify the paygroup on each timecard line, and Sage 100 Contractor uses the wages and benefits package from the paygroup in place of the wages and benefits package in the employee record.

When your company offers a benefit that is also in the prevailing benefits package, your company receives a credit, determined by the job’s governing agency. In some cases, you might be required to pay the employee the difference between the regular benefit and the prevailing benefit. Set up the payroll calculation for the benefit as a cash add-on, and include the offsetting credit for the new calculation in the employee’s record. When you compute payroll, Sage 100 Contractor uses the offset credit to determine the difference between the benefit provided and the prevailing benefit. The employee is paid the difference as cash.

For example, you pay a health benefit of $180 per month on behalf of Joe, and $120 per month on behalf of Bill using **Calculation A: Company Health** (paid by the employer). The requirements for a prevailing-wage job include a $2 per hour health benefit. To calculate the required health benefit correctly, you set up a new calculation, called **Calculation B: Davis/Bacon Health** (cash add-on) and add it to the employee records. The new calculation has a calculation type **2-Add to Gross**, and a rate of $2 per hour.

The governing agency, after reviewing the health benefit you supply, determines you get a $1 per hour credit for Joe’s health care benefit and a $0.67 per hour credit for Bill’s health care benefit.

After setting up the paygroups and benefits packages, which includes **Calculation B**, enter the health care credit in the **Calculations** tab of the employee records. In Joe’s employee record, enter the $1 credit in the **Offset** cell for **Calculation B**. Then in Bill’s employee record, enter the $0.67 credit in the **Offset** cell for **Calculation B**.

Joe and Bill work 40 hours on the prevailing-wage job. When entering their timecards, you indicate the appropriate paygroups. When you compute payroll, Sage 100 Contractor determines the amount to add to each cheque, which is the difference between the health benefit you provide and the prevailing health care benefit [(benefit rate – offsetting credit) * hours worked].

Joe receives an additional $40 [($2 – $1) * 40] on his cheque; and Bill receives an additional $53.20 [($2 – $0.67) * 40] on his cheque. For the certified payroll report, Sage 100 Contractor computes the health benefit at $2 per hour for both Joe and Bill.

For companies that perform considerable amounts of prevailing-wage work, you can create a table of paygroups to use with each job. When you enter the job number on a timecard, Sage 100 Contractor determines which paygroup to use based on the employee’s position.

| Links to more information . . . [Adding payroll calculations to employee records](Adding_payroll_calculations_to_employee_records.md) [About reviewing rates in tax tables](About_reviewing_rates_in_tax_tables.md) [About paygroups](About_paygroups.md) [About setting up payroll calculations for paygroup benefit packages](About_setting_up_payroll_calculations_for_paygroup_benefit_packages.md) |
|---|
