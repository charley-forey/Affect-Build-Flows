<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/7-Utilities/Setting_up_user_names_and_passwords.htm (Sage 100 Contractor help v20.5) -->

### Setting up user names and passwords

Use the **7-2-2 User List**window to set up new users and user passwords in your company. You can also copy existing user defaults to create new users.

You set up security for each individual company, not for the entire program. Each company can use a different list of users and passwords.

Within a company, security groups control access. After assigning users to security groups, grant the access rights to the security groups.

Caution! Security does not prevent access to databases by highly skilled computer users. Security only manages data access through Sage 100 Contractor.

When setting up user names and passwords, we suggest you:

- Print a list of the user names and security groups to include in your files. When employees have questions about access, you can refer to the printed list.
  
  Tip:
  
  If an employee subsequently forgets their SQL Server password, you can reset it in the 7-2-2 User list window. You cannot see passwords after entering and saving them.
- If you are using SQL Server authentication (not Integrated Security) consider using the employee’s job title as their user name. For example, instead of entering Leslie in the **User Name** cell, use **Accountant**. Then, if the employee leaves the position, their security and report defaults can be used by the next person in that job.

Notes:

- Only company administrators have rights to set up user names and passwords.
- You may receive a **Runtime Error 75** error message upon exiting Sage 100 Contractor if the system has been set up without giving users sufficient rights to update registries.

#### To set up user names and passwords:

1. Open **7-2-2 User List**.
2. For each user:
   
   1. In the **User Name** cell, enter the user’s name.
   2. In the **Integrated Security** cell, if you want Sage 100 Contractorto authenticate the user by evaluating their Windows ID and password, type "Y." Note: Integrated Security works only with the Windows authentication method. If SQL Server authentication has been assigned to the user, enter "N" in this cell.
   3. In the **Password** cell, enter a password.
   4. In the **Group 1** cell, click once in the cell, and then from the drop-down list, select a security group.  
      For example, owners/comptrollers could be in Group 1.
   5. In the **Group 2** cell, click once in the cell, and then from the drop-down list, select a security group.  
      For example, employees with access to general ledger accounts could be in Group 2.
   6. In the **Group 3** cell, click once in the cell, and then from the drop-down list, select a security group.  
      For example, employees with access to payroll could be in Group 3.
   7. In the **Group 4** cell, click once in the cell, and then from the drop-down list, select a security group.  
      For example, employees with access to accounts receivable could be in Group 4.
   8. In the **Group 5** cell, click once in the cell, and then from the drop-down list, select a security group.For example, employees with access to accounts payable could be in Group 5.
   9. In the **Subject to Job Security** cell, click once in the cell, and then type Y if the user is subject to job level security access.
3. Click **File** > **Save**.

| Links to more information . . . [About the company administrator](About_the_company_administrator.md) [About security groups](About_security_groups.md) [About copying user defaults](About_copying_user_defaults.md) |
|---|
