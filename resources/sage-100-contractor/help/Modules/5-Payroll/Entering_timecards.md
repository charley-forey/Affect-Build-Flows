<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/5-Payroll/Entering_timecards.htm (Sage 100 Contractor help v20.5) -->

### Entering timecards

Consider the following points before entering timecards:

- To determine the default Workers’ Compensation code, Sage 100 Contractor first checks to see if the **Use Emp Comp Code** check box on **5-2-1 Employees**is selected for that employee record. If not, then Sage 100 Contractor looks to the **Comp Code1** column on **6-5 Cost Codes** to determine the default Workers’ Compensation code. If it does not find a compensation code there, then it looks back to the **Comp Code** text box on **5-2-1 Employees**for the Workers’ Compensation code and uses that one for determining the default.
- To determine the department number for posting, Sage 100 Contractor first looks to the job. If Sage 100 Contractor does not find a department, Sage 100 Contractor then looks at the cost code. If it does not contain a department number, Sage 100 Contractor then looks to the employee position.
- You can enter negative hours. To compute payroll records correctly, enter the timecard line containing the negative hours first. This ensures deductions, benefits, or other calculations that use calculation maximums compute properly.
- To make sure all payroll records are final-computed and posted, enter cheques for pay advances, bonuses, vacation pay, or layoffs using the same period ending date as regular payroll.
- You can compute an employee’s hourly rate per piece by using piece pay.

Important! The **Direct Deposit** check box is available only if the **Enable direct deposit** check box is selected for the employee on the **Direct Deposit** tab in the **5-2-1 Employees** window.

#### To enter a timecard:

1. Open **5-2-2 Payroll Records**.
2. In the **Employee** text box, enter the employee number.
3. In the **Period Start** text box, enter the date when the payroll period begins.
4. In the **Period End** text box, enter the date when the payroll period ends.
5. In the **Cheques Date** text box, enter the date when the cheque is to be issued.
6. In the **Cheques#** text box, type 0000. When you print the cheque, Sage 100 Contractor assigns the cheque number to the record. Note: If you have already issued the cheque, enter the cheque number in the **Cheques#** text box.
7. In the **Payroll Type** list, click **1-Regular**.
8. In the **Quarter** text box, enter or accept the payroll quarter.
9. In the **Province** text box, enter or accept the tax province.
10. If you are paying out vacation as a lump sum, enter the lump sum in the **Vacation Payout** text box. Sage 100 Contractor displays the vacation balance accrued to date for the employee beside the Vacation Payout box.
11. On the **Timecard** tab, for each payroll item:
    
    1. In the **Date** cell, enter the date on which the employee worked.
    2. If the employee worked on a job, enter the job number in the **Job** cell. If the employee worked on equipment, enter the equipment number in the **Equipment** cell.
    3. If the job uses phases, enter the phase number in the **Phase** cell.
    4. If the employee worked on a job or repaired equipment, enter the cost code number in the **Cost Code** cell.
    5. In the **Pay Type** cell, enter the pay type.
    6. If you are using paygroups, enter the paygroup number in the **Paygroup** cell.
    7. In the **Pay Rate** cell, enter the employee’s pay rate.
    8. In the **Hours** cell, enter the number of hours the employee worked.
    9. In the **Comp Code** cell, enter the Workers’ Compensation code number.
    10. If you are using departments, enter the department number in the **Department** cell.
    11. In the **Absences** cell, enter the user-defined reason for the employee’s absence.
12. On the **File** menu, click **Save**.

| Links to more information . . . [About pay types](About_pay_types.md) [About absences](About_absences.md) [About paygroups](About_paygroups.md) [About accruing vacation amounts](About_accruing_vacation_amounts.md) [About Workers’ Compensation codes](../6-Project_Management/About_Workers__Compensation_codes.md) [About piece pay](About_piece_pay.md) |
|---|
