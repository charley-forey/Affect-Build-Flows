<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Appendices/I-Working_with_Sage_Construction_Anywhere/Setting_up_an_API_security_group_and_an_API_user_in_Sage_100_Contractor.htm (Sage 100 Contractor help v20.5) -->

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

Important! If you use security groups for the tasks performed by the employee in Sage 100 Contractor, make sure the Sage Construction Anywhere user has access to all areas of Sage 100 Contractor.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)](javascript:void(0);)[To set up a security group for using the API](javascript:void(0);)

1. Open **7-2-1 Security Groups**.
2. In the **Group#** cell, type a group number, such as 51.
3. In the **Group Name** cell, type API and do the following: Important! The API security group must be named exactly **API**.
   
   1. In the **Save**, **Delete**, **Void**, **Chg Period**, and **Print Cheques** cells, type **Yes**.
   2. To store information that may be relevant or important to that specific group, type a note in the **Notes** cell.
4. On the **File** menu, click **Save**.

Tips:

- Before you can use the API security group to access Sage 100 Contractor company data, you have to assign a user to the API security group.
- Security is set up for each individual company, not for the entire program. Each company can use different user names and passwords. If you have more than one company, you have to set up passwords for multiple companies.

Then you have to assign a user to the API security group using **7-2-2 User List**.

The **7-2-2 User List** window controls major features dealing with users and program security.

Note: The user name and password created are for administrative use only. This information is for use by the Sage Construction Anywhere Connector program only, and is not needed by the individual employee(s) using Sage Construction Anywhere.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)](javascript:void(0);)[To assign a new user to the API security group](javascript:void(0);)

1. Open **7-2-2 User List**.
2. In the **User Name** cell, enter a user name, such as SCAUser.
3. In the **Password** cell, enter a password.
4. In the **Group 1** cell, click once in the cell, and from the drop-down list, select the API group.
5. Click **File** > **Save**.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To assign an existing user to the API security group](javascript:void(0);)

1. Open **7-2-2 User List**.
2. Find the **User Name** for the person who will use Sage Construction Anywhere.
3. In the **Group 1**, **Group 2**, **Group 3**, **Group 4**, or **Group 5** cell, click once in the cell, and from the drop-down list, select the API group.
4. Click **File** > **Save**.
