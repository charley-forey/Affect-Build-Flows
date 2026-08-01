<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/5-Payroll/About_accruing_vacation_amounts.htm (Sage 100 Contractor help v20.5) -->

# About accruing vacation pay

Sage 100 Contractor can track the dollar balance of employee vacation earned but not yet paid. Accrued vacation can be paid out with each pay cheque, or it can accumulate in a payroll liability account to be paid out later.

The vacation balance is calculated and posted whenever you final-compute payroll:

- Vacation accrual is posted as a credit to the liability account specified for the accrued vacation payroll calculation, using the employee# as the subaccount.
- Vacation payout is posted as a debit to the liability account specified for the accrued vacation payroll calculation, using the employee# as the subaccount.

Notes:

- Accrued vacation pay and accrued vacation time are independent of each other. Paying out accrued vacation as a lump sum does not reduce accrued vacation time on the employee record. Similarly, entering a timecard line using **Pay Type 5 - Vacation** does not reduce the balance of an employee's accrued vacation pay (**Accrued Vacation Due** in the employee record).
- Vacation is not accrued on any vacation payout amount.
- While Sage 100 Contractor does not automatically audit or verify the vacation amounts, you can query the accrued vacation for all employees in the **5-2-1 Employees** window, and then compare the amounts on the resulting report to the subsidiary balances in the liability account.

Important! Vacation is taxed when it is paid out, not when it is accrued.

## Payroll calculations to accrue vacation pay

When setting up a payroll calculation to accrue vacation pay, you use **Tax Type 6 ‑ Vacation Accrual**. If vacation is earned and accrued on vacation, you calculate a different default rate by multiplying the recursive portion of the tax by the base rate. For example, if employees accrue additional vacation at 4% on a basic accrual rate of 4%, you would enter 4.16 in the **Default Rate** box.

The Credit Account you use to maintain the vacation balance must be an account that is set up to use subaccounts, and it cannot already have subaccounts associated with it. The check box **Use employee# as subaccount** is selected automatically for vacation accruals, and you cannot change this selection.

Other payroll calculations can affect vacation calculations. A new **Vacation Accrual** check box in the **Subject to** section of the window lets you control which taxable benefits or non-taxable deductions affect the accrual amount.

## Tracking accrued vacation for an employee

In the **5-2-1 Employees** window, you use the **Accrued Vacation Due** box on the Compensation tab to track each employee’s accrued vacation pay.

Whenever you perform a final payroll computation, Sage 100 Contractor updates the **Accrued Vacation Due** amount. Any vacation pay accrued for the period increases the amount in the **Accrued Vacation Due** box. Any vacation payout reduces the amount. (Similar to the Advances Due field, the Accrued Vacation Due field is not cleared at year-end, but continues to accumulate accrued vacation until vacation is paid out.)

The Calculations tab in each employee record displays the vacation accrual rate, as well as the vacation that has accrued for each quarter and for the year to date. It also lets you specify the maximum vacation that can accrue, if there is a maximum.

Tip: You can query **Employees~Accrued Vacation Due** to view the vacation balance for employees who have vacation due.

## Paying out vacation

When it is time to pay out an employee's vacation, you enter a lump sum payout amount for a pay period in the **Vacation Payout** box in the **5-2-2 Payroll Records** window. Sage 100 Contractor displays the current vacation balance accrued for the employee in the **(Vacation balance is …)** information field.

Note: You can pay out vacation for all payroll types, except advances, for new or existing open payroll records.

Together, the Vacation Payout and the Salary amounts make up the amount that appears as the total pay for the period.

Tip: You can run a **Payroll Records~Vacation Payout** query in this window to view a list of vacation payouts for a specified range of employees and pay periods. You can also drill down from the query to view the underlying transaction for a selected payout.
