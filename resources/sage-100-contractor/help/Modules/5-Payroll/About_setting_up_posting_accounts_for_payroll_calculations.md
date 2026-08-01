<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/5-Payroll/About_setting_up_posting_accounts_for_payroll_calculations.htm (Sage 100 Contractor help v20.5) -->

### About setting up posting accounts for payroll calculations

Many payroll calculations require you to provide the posting accounts. Sage 100 Contractor reads and posts each timecard line amount based on the ledger accounts in the payroll calculation setup.

When the timecard line indicates a job number, Sage 100 Contractor debits the direct labour account.

When the timecard line indicates an equipment number (for repair or maintenance), Sage 100 Contractor debits the shop labour account.

When the timecard line does not indicate a job or equipment number, Sage 100 Contractor looks at the employee’s position to determine whether to post the account to an overhead or administrative labour account.

You can control the job, shop, overhead, and administration labour expense accounts and the credit account for each payroll calculation. The employee positions setup determines to which accounts Sage 100 Contractor posts. Sage 100 Contractor debits employer burden for payroll taxes, Workers’ Compensation, benefits and liability insurance to the accounts indicated in the chart below.

In the example below, Sage 100 Contractor debits gross wages to accounts 5400, 5600, 6400, or 7400 based on the settings in **5-3-3 Employee Positions**.

| Debit | Job | Shop | Overhead | Administration |
|---|---|---|---|---|
| Payroll tax | 5410 | 5610 | 6410 | 7410 |
| Workers’ Comp | 5420 | 5620 | 6420 | 7420 |
| Benefits | 5430 | 5630 | 6430 | 7430 |
| Liability | 5440 | 5640 | 6440 | 7440 |
| Gross Wage | 5400 | 5600 | 6400 | 7400 |

Note: A payroll calculation using calculation type **1-Deduct from Employee** does not allow entry of the posting accounts. Instead, Sage 100 Contractor refers to the posting accounts assigned to the employee position. When you compute timecards, Sage 100 Contractor looks at the employee position to determine where to post labour expenses.

| Links to more information . . . [About employee positions](About_employee_positions.md) [About calculation types](About_calculation_types.md) |
|---|
