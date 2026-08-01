<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Appendices/H-Working_with_the_Sage_ACT__Plug-in/Setting_up_an_API_security_group_and_an_API_user_in_Sage_100_Contractor.htm (Sage 100 Contractor help v20.5) -->

## Setting up an API security group and an API user in Sage 100 Contractor

Security groups let you control users’ ability to open windows as well as perform specific actions within a window. The **7-2-1 Security Groups**window in Sage 100 Contractor contains a grid with numbered rows on the left and eight columns:

- Group# (User input is required to save the record.)
- Group Name (User input is required to save the record.)
- Save
- Delete
- Void
- Chg Period
- Print Cheques
- Notes

When you set up user groups, you type a group number and group name. Then you determine whether or not that group will have rights to **Save**, **Delete**, and **Void** records, as well as to change the accounting period and print cheques. You may use the Notes column to add any pertinent information about each group.

You must create an API security group that is named exactly **API**. At least one user must be added to the API security group. You have to set rights to save, void, and so on.

Important! If you use security groups for the tasks performed by the employee in Sage 100 Contractor, make sure the API security group has access to **3-Accounts Receivable**, **3-5 Jobs (Accounts Receivable)**, **3-6 Receivable Clients**, **4-Accounts Payable**, **4-4 Vendors (Accounts Payable)**, **5-Payroll**, and **5-2-1 Employees**.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)](javascript:void(0);)[To set up a security group for using the API](javascript:void(0);)

1. Open **7-2-1 Security Groups**.
2. In the **Group#** cell, type a group number, such as 51.
3. In the **Group Name** cell, type API, and then: Important! The API security group must be named exactly **API**.
   
   1. In the **Save** cell, type Yes.
   2. In the **Delete** cell, if you want to allow the users of the API group to delete records, type Yes. If you do not want these users to delete records, type No.
   3. In the **Void** cell, type Yes. If you do not want these users to void transactions, type No.
   4. In the **Chg Period** cell, type Yes. If you do not want these users to change periods, type No.
   5. In the **Print Cheques** cell, type Yes. If you do not want these users to print Cheques, type No.
   6. To store information that may be relevant or important to that specific group, type a note in the **Notes** cell.
4. Click **File** > **Save**.

Tips:

- Before you can use the API security group to access Sage 100 Contractor company data, you have to assign a user to the API security group.
- Security is set up for each individual company, not for the entire program. Each company can use different user names and passwords. If you have more than one company, you have to set up passwords for multiple companies.

Then you have to assign a user to the API security group using **7-2-2 User List**.

The **7-2-2 User List** window controls major features dealing with users and program security.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)](javascript:void(0);)[To assign a user to the API security group](javascript:void(0);)

1. Open **7-2-2 User List**.
2. In the **User Name** cell, enter a user name, such as APIUser.
3. For each API user:
   
   1. In the **Password** cell, enter a password.
   2. In the **Group 1** cell, click once in the cell, and then from the drop-down list, select the API group.
4. Click **File** > **Save**.

### Restricting employee access to Sage 100 Contractor

You can use one of the two following scenarios as an alternate way to provide the access to send information to Sage 100 Contractor from Act!.

#### Scenario 1: Have a system administrator enter the API user and password on a workstation

If you would like the user to be able to select a salesperson when creating clients in Sage 100 Contractor, but not give the user the ability to log into Sage Sage 100 Contractor, use this method.

A single API user/password can be entered by a system administrator on one or more workstations, allowing the user to create vendors, clients, and jobs without gaining these additional permissions when logging into Sage 100 Contractor. Essentially, this means users cannot log into Sage 100 Contractor using the API credentials, but can send information to Sage 100 Contractor.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To set up security for Scenario 1](javascript:void(0);)

1. Create the API security group and API user and password as usual in Sage 100 Contractor.
2. Open Act!.
3. On each workstation that has the Act! integration:
   
   1. In the Tools menu, select **Sage 100 Contractor Company Settings…**.
   2. Click to enable the company the user can access.
   3. In the **User Name** field, enter the API username.
   4. In the **Password** field, enter the API user password.
   5. Click [**OK**].

Individual workstation users will not be able to log into Sage 100 Contractor and access employees.

#### Scenario 2: Restrict menu level security access to 5-2-1 Employees so employee cannot select a salesperson

If you would like to give each user their own username and password for the API, but not allow the user to select a salesperson when creating clients in Sage 100 Contractor, use this method.

You can choose to restrict menu level security access in Sage 100 Contractor to **5-2-1 Employees** for an ACT! user that has access to the API user login and password.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To set up menu level security for the API user](javascript:void(0);)

1. Open Sage 100 Contractor.
2. Create the API security group and API user and password as usual in Sage 100 Contractor.
3. In the System Menu tab, select **5-2-1 Employees**.
4. Click F7 .
5. Clear the check box for API in the **Menu Level Security** dialog box.
6. Click [**Save**].

Important! Users will not be able to select a salesperson if you restrict access to **5-2-1 Employees** in Sage 100 Contractor.

| Links to more information . . . [Creating a Sage 100 Contractor Vendor from an Act! Company](Creating_a_Sage_100_Contractor_Vendor_from_an_ACT__Company.md) [Initializing the Act! database for use with Sage 100 Contractor](Initializing_the_ACT__database_for_use_with_Sage_100_Contractor.md) [Setting up Act! Integration](Setting_up_ACT__Integration.md) [Setting up Sage Sage 100 Contractorcompanies in Act!](Setting_up_companies_in_Sage_ACT_.md) |
|---|
