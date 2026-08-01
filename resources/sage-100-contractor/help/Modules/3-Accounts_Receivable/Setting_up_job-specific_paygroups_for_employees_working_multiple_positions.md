<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/3-Accounts_Receivable/Setting_up_job-specific_paygroups_for_employees_working_multiple_positions.htm (Sage 100 Contractor help v20.5) -->

### Setting up job-specific paygroups for employees working multiple positions

When an employee works a variety of positions on a job, you can use paygroups to control the payment of wages and benefits according to the position worked. To do this, you set up a “dummy” paygroup that does not contain any rates. Then you set up the job paygroup positions in the **3-5 Jobs (Accounts Receivable)** window to refer only to the dummy paygroup.

When you enter a timecard, Sage 100 Contractor selects a paygroup by comparing an employee’s position to the list of job-specific paygroups and the associated positions. Regardless which position you enter in the timecard, Sage 100 Contractor selects the dummy paygroup. You can then use a **Lookup** window to select the correct paygroup based on the position worked by the employee.

Suppose you are setting up paygroups for job number 200, a prevailing-wage contract for a housing development. Each member of the crew performs several different tasks, so you set up the following paygroups in **5-3-4 Paygroups**. Paygroup number **200-Sonoma Job** is a dummy paygroup and does not use any wage rates. Paygroups **210-Project Manager**, **220-Superintendent**, and **230-Foreman** are assigned wage rates.

Then the list of job-specific paygroups is set up using only paygroup **200-Sonoma Job**. Because each employee is working several different positions, enter the dummy paygroup on a separate line for each employee position required by job 200.

When entering a timecard information for job 200, Sage 100 Contractor selects paygroup **200-Sonoma Job** when the employee’s file contains position 5, 6, or 7. You can then enter the appropriate paygroup, or select a paygroup by displaying a **Picklist**.

Important! As you press the Enter key to move through the grid, notice that as you move from cell to cell, Sage 100 Contractor autopopulates the cell with information in bold text. You have to press Enter again for Sage 100 Contractor to accept that information and write it to the database. As long as there is bold text in a cell, that information is not yet recognized. Pressing the drop-down arrow in a cell with bold text does not open the “dummy” paygroup.

#### To set up job-specific paygroups:

1. Open **5-3-4 Paygroups**.
2. Create a dummy paygroup for the job that uses the job name and job number as the paygroup description. Do not include any rates in this paygroup.
3. Enter the actual paygroups you want to use for the job, and include the wage and benefit rates. When creating the paygroups, organize the paygroups by job. When numbering the paygroups, skip a few numbers between groups in case you need to add other paygroups later.
4. Open **3-5 Jobs (Accounts Payable)**.
5. From the **Options** menu, select **Job Paygroups**.
6. Set up job paygroups using a “dummy” paygroup for each of the positions. For each position that requires you to use a separate paygroup, enter the dummy paygroup on a separate line and assign an employee position to it.
7. When you are finished, the job-specific paygroups table should contain a list of the same dummy paygroup assigned different employee positions.
8. Open **5-2-2 Job Payroll Records**.
9. Create a timecard.
10. Press the Enter key to move through the grid to the paygroups.
11. Go back to the paygroup cell, and click the drop-down arrow.
12. The correct job paygroup appears.

Tip: To display only the job paygroups from the grid, use the **ENTER** key to move through the “dummy” paygroup that defaults into the grid cell of the timecard lines. Then go back to the timecard line. The dummy paygroup is no longer bold. Click the drop-down arrow to display the **Lookup** window. Now only the correct **Job Paygroups** appear. Alternatively, you can enter the correct **Job Paygroup** number in the timecard line cell, and then click the drop-down arrow to display the dummy **Job Paygroups**.

| Links to more information . . . [About employee positions](../5-Payroll/About_employee_positions.md) [Entering timecards](../5-Payroll/Entering_timecards.md) [About paygroups](../5-Payroll/About_paygroups.md) [Entering job-specific paygroups](Entering_job-specific_paygroups.md) |
|---|
