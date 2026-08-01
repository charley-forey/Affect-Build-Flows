<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/7-Utilities/About_7-2-2_User_List_window.htm (Sage 100 Contractor help v20.5) -->

### About the 7-2-2 User List window

The **7-2-2 User List**window controls several important aspects of program security, including user access to a Sage 100 Contractor company. If you are a company administrator, you can use this window to set up a list of users who are permitted access to a Sage 100 Contractor company.

Because Sage 100 Contractor determines access through the user names, a user can log on to Sage 100 Contractor from any workstation in a network environment.

Notes:

- When setting up access rights to a Sage 100 Contractor company, you can add users that already have a SQL Server login, and you can add new users. If a user does not already have a SQL Server login, the program creates a SQL Server login for the user, allowing access to the SQL Server database.
- When setting up user access in a network environment, you must include the Windows domain in the user name (for example, DOMAIN\Dennis42).

#### Using Integrated Security to simplify the login process

Note: Integrated security works only with the Windows authentication method.

Assigning Integrated Security to a user can simplify the login process.

To assign Integrated Security to a user, enter "Yes" beside their user name in the Integrated Security column. Sage 100 Contractor will check the user's Windows credentials when they log into the company. Because they supply a password when signing into Windows, the user is not required to enter another password when logging into the company.

If Integrated Security is blank or "No," the user must supply their SQL Login and password to open the Sage 100 Contractor company.

#### Using security groups for finer access control

By setting up security groups and assigning the groups to user names, you can further limit access to certain modules or windows, and text boxes, lists, and columns within windows.

If you want certain users to see job-related information only for the jobs they manage, you can assign them to job-level security using the **Subject to Job Security** column.

Note: Any user can be a member of the API security group. However, we recommend that you create a specific user to use the API, for example, “APIUser.”

| Links to more information . . . [Setting up user names and passwords](Setting_up_user_names_and_passwords.md) [About the company administrator](About_the_company_administrator.md) [About security groups](About_security_groups.md) [About copying user defaults](About_copying_user_defaults.md) |
|---|
