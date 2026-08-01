<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/5-Payroll/Job_costing_salaried_employees.htm (Sage 100 Contractor help v20.5) -->

### Job costing salaried employees

If a salaried employee spends time working on a job or repairing equipment, you can create the appropriate job or equipment cost records. On the **Timecard** tab, enter the hours the employee has spent working jobs or repairing equipment during the pay period. Also, include the hours spent in an overhead or administrative capacity.

When you compute payroll, Sage 100 Contractor calculates the gross hourly wage (employee salary / total hours = gross hourly wage). If a salaried employee works more than 40 hours in a week, the calculated gross hourly wage is lower. Therefore, to compute a gross hourly wage based on a 40-hour week, enter a timecard line for negative hours and attribute them to a dummy job (created strictly for this purpose). The dummy job allows you to enter all hours worked without affecting the costs attributed to the jobs or equipment.

Suppose Robert, a salaried administrator, worked eight hours as a carpenter on a job. He also worked 32 hours as an administrator. The first timecard line contains the job, cost code, payroll line type, hours, and Workers’ Compensation code. The second timecard line contains the payroll line type, non-job or equipment related hours worked, and the Workers’ Compensation code. When you final-compute the payroll record, Sage 100 Contractor attributes the cost of eight hours labour to the job and 32 hours labour to administration.

#### To job cost a salaried employee:

|  | 1 | Open **5-2-2 Payroll Records**. |
|---|---|---|

|  | 2 | In the **Employee** box, enter the employee number. |
|---|---|---|

|  | 3 | In the **Period Start** box, enter the date when the payroll period begins. |
|---|---|---|

|  | 4 | In the **Period End** box, enter the date when the payroll period ends. |
|---|---|---|

|  | 5 | In the **Cheques Date** box, enter the date when the cheque is to be issued. |
|---|---|---|

|  | 6 | In the **Cheques#** box, type 0000. |
|---|---|---|

When you print the cheque, Sage 100 Contractor assigns the cheque number to the record.

|  | 7 | If you have already issued the cheque, enter the cheque number in the **Cheques#** text box. |
|---|---|---|

|  | 8 | In the **Payroll Type** list, click **1-Regular**. |
|---|---|---|

|  | 9 | In the **Quarter** box, enter the payroll quarter. |
|---|---|---|

|  | 10 | In the **Province** text box, enter the tax province. |
|---|---|---|

|  | 11 | In the **Salary** box, enter the salary. |
|---|---|---|

|  | 12 | In the **Timecard** tab, do the following: |
|---|---|---|

|  | a | In the **Date** cell, enter the date on which the employee worked. |
|---|---|---|

|  | b | If the employee worked on a job, enter the job number in the **Job** cell. |
|---|---|---|

|  | c | If the employee repaired equipment, enter the equipment number in the **Equipment** cell. |
|---|---|---|

|  | d | If the job uses phases, enter the phase number in the **Phase** cell. |
|---|---|---|

|  | e | If the employee worked on a job or repaired equipment, enter the cost code number in the **Cost Code** cell. |
|---|---|---|

|  | f | In the **Pay Type** cell, enter the payroll line type. |
|---|---|---|

|  | g | In the **Compensation Code** cell, enter the Workers’ Compensation code number. |
|---|---|---|

|  | h | If you are using departments, enter the department number in the **Department** cell. |
|---|---|---|

|  | 13 | Repeat step 12 for each payroll item. |
|---|---|---|

|  | 14 | On the **File** menu, click **Save**. |
|---|---|---|

Tip: To compute payroll records correctly, enter the timecard line containing the negative hours first. This ensures deductions, benefits, or other calculations that use calculation maximums compute properly.
