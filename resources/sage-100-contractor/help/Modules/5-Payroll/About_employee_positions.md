<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/5-Payroll/About_employee_positions.htm (Sage 100 Contractor help v20.5) -->

### About employee positions

Employee positions determine how you post payroll costs to the general ledger. Create employee positions that represent the type of work performed by employees such as office workers, job supervisors, and labourers. The list does not need to be complex. However, you must create at least one employee position.

After creating the employee positions, assign them to employee records. When you post a payroll record, Sage 100 Contractor looks at the position in an employee’s record, and the ledger accounts in the employee positions table:

- When a timecard line contains a job number, payroll posts to the ledger account in the **Job Wages** cell.
- When a timecard line contains an equipment number (for maintenance or repair), payroll posts to the ledger account in the **Equipment Wages** cell.
- When a payroll record does not contain timecard lines, or a timecard line does not contain a job number or equipment number, Sage 100 Contractor posts to the ledger account in the **Other Wages** cell.

You can also add a department to each position. When you post a payroll record, Sage 100 Contractor first looks to the job record for a department number. If Sage 100 Contractor does not find a department number in the job record, it next looks to the cost code. If the cost code does not contain a department number, Sage 100 Contractor then looks to the employee position.

| Links to more information . . . [Setting up employee positions](Setting_up_employee_positions.md) [About paygroups](About_paygroups.md) [Setting up payroll unions](Setting_up_payroll_unions.md) [About posting payroll](About_posting_payroll.md) [About setting up posting accounts for payroll calculations](About_setting_up_posting_accounts_for_payroll_calculations.md) [About company departments](../1-General_Ledger/About_Company_Departments.md) |
|---|
