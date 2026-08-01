<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/7-Utilities/Setting_up_a_security_group_for_using_the_API.htm (Sage 100 Contractor help v20.5) -->

### Setting up a security group for using the API

The Sage 100 Contractor application program interface (API) enables you to use third-party programs to perform the same tasks that you would perform when using different Sage 100 Contractor windows. The API allows the third-party program to insert, as well as delete, modify, or retrieve data from one or more existing Sage 100 Contractor company databases.

Using the Sage 100 Contractor API to access Sage 100 Contractor company data requires a license use. That is why you have to set up an API security group using **7-2-1 Security Groups**. Then you have to assign a user to the API security group using **7-2-2 User List**.

Note: If no license uses available, the API program alerts you.

#### To set up a security group for using the API:

1. Open **7-2-1 Security Groups**.
2. In the **Group#** cell, type a group number, such as 51.
3. In the **Group Name** cell, type API. Important! The API security group must be named exactly **API**.
4. In the **Save** cell, type **Yes**.
5. In the **Delete** cell, to allow the users of the API group to delete records, type **Yes**. If you do not want to allow them to delete records, type No.
6. In the **Void** cell, type **Yes** to allow API users to void records. Otherwise, type **No**.
7. In the **Chg Period** cell, type **Yes** to allow API users to change periods. Otherwise, type **No**.
8. In the **Print Checks** cell, type **Yes** to allow API users to print Checks. Otherwise, type **No**.
9. To store information that may be relevant or important to that specific group, type a note in the **Notes** cell.
10. On the **File** menu, click **Save**.

Tips:

- Before you can use the API security group to access Sage 100 Contractor company data, you have to assign a user to the API security group.
- Security is set up for each individual company, not for the entire program. Each company can use different user names and passwords. If you have more than one company, you have to set up passwords for multiple companies.

| Links to more information . . . [About passwords for multiple companies](About_passwords_for_multiple_companies.md) [About window and menu-level security](About_window_and_menu-level_security.md) [Setting window and menu-level security](Setting_up_window_and_menu-level_security.md) |
|---|
