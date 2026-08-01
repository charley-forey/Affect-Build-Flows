<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/7-Utilities/About_security_groups.htm (Sage 100 Contractor help v20.5) -->

### About security groups

Use the **7-2-1 Security Groups**window to set up security groups for your company’s employees.

Security groups let you control users’ ability to open windows as well as perform specific actions within a window. The **7-2-1 Security Groups**window contains a grid with numbered rows on the left and eight columns:

- Group# (User input is required to save the record.)
- Group Name (User input is required to save the record.)
- Save
- Delete
- Void
- Chg Period
- Print Cheques
- Notes

When you set up user groups, you type a group number and group name. Then you determine whether or not that group will have rights to **Save**, **Delete**, and **Void** records, as well as to change the accounting period and print cheques. You may use the Notes column to add any pertinent information about each group.

While you might create security groups for specific employees, it is a good idea to build each security group for the tasks performed by the employee. This allows you to add or remove employees from security groups rather than having to build new security groups for each new employee.

As the company size increases, the need for additional security groups increases. For example, a large company has an office staff that includes several accounts payable clerks, an accounts receivables clerk, a payroll clerk, a controller, project managers, and estimators. In this company, six different security groups are set up to accommodate the specific needs of the employees engaged in six different task areas.

In addition to creating task-oriented security groups, it is a good idea to create one security group with full access to the entire program. This allows owners or managers to log in with full access, but prevents unauthorized access to program features that only a company administrator can use.

It is important to consider the scope of tasks performed by users as well as the number of users that access Sage 100 Contractor. Before designing security groups, examine which users need access to specific windows in Sage 100 Contractor. After you set up the security groups, you can then set up window and menu-level security.

For example, a small company has three clerks: a general accounting clerk, an accounts payable and accounts receivable clerk, and a payroll clerk. For this company, it is only necessary to create three security groups. The first group, titled **Payroll Clerk**, only provides access to payroll operations. The second group, titled **A**/**P A**/**R Clerk**, provides access to accounts payable and accounts receivable operations. The third group, titled **General Ledger Clerk**, provides access to general ledger operations not covered by accounts payable and accounts receivable.

Consider the following before setting up security groups:

- Do you need to create separate security groups for employees who perform specific tasks? For example, does your company have a payables clerk who only enters payables data?
- Do you need to create separate security groups for accounts payable, accounts receivable, and payroll supervisors, or can you just create one group for the supervisors?
- Do estimators perform different tasks than project managers?
- Do you need to provide differing levels of access to owners, controllers, or managers?
- Are you going to use the Sage 100 Contractor API to integrate with other programs? If so, create a security group named **API** with a group number such as 51.

Important! To use the Sage 100 Contractor API program, you must create an API security group that is named exactly **API**. At least one user must be added to the API security group. You have to set rights to save, void, and so on.

| Links to more information . . . [About the 7-2-2 User List window](About_7-2-2_User_List_window.md) [About copying user defaults](About_copying_user_defaults.md) [About window and menu-level security](About_window_and_menu-level_security.md) [About access rights regarding window and menu-level security](About_access_rights_regarding_window_and_menu-level_security.md) [About the company administrator](About_the_company_administrator.md) |
|---|
