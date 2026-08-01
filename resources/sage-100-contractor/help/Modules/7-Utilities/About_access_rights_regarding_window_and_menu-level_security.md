<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/7-Utilities/About_access_rights_regarding_window_and_menu-level_security.htm (Sage 100 Contractor help v20.5) -->

### About access rights regarding window and menu-level security

Caution! If window and menu-level security is not set up, Sage 100 Contractor gives all access rights to any user opening the window.

When you assign a user to a security group, that user gains the access rights associated with its security group. Sage 100 Contractor applies the access rights only when you have set up window-level and menu-level security on a menu command that opens a window.

Suppose you assign to a security group titled **General Ledger Clerk** only the right to save and delete records. Then, you set up window and menu-level security for each window under the general ledger—**1-1 Cheques/Bank Charges**, **1-2 Deposits/Interest**, **1-3 Journal Transactions**, **1-4 Recurring Journal Transactions**, **1-5 Bank Reconciliation**, **1-6 Period/Fiscal Year Management**, **1-7 Ledger Accounts**, **1-8 General Ledger Setup**, and **1-9 Company Departments**—selecting only the **General Ledger Clerk** group to have access to those windows.

- Example 1. Gerald is assigned to the **General Ledger Clerk** group. When Gerald opens the **1-1 Cheques/Bank Charges** window, he can only save and delete records.
- Example 2. A security group titled **Payroll Clerk** has rights to save records, change posting periods, print cheques, and void or delete records. Each window under payroll is assigned window and menu-level security. Only users assigned to the **Payroll** security group can open those windows.
- Example 3. Dianna is assigned to both the **General Ledger Clerk** and **Payroll Clerk** groups. When Dianna opens any of the payroll windows, she has the access rights assigned to the **Payroll Clerk** group. And when Dianna opens any of the general ledger windows, she has the access rights assigned to the **General Ledger Clerk** group.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To set up window and menu-level security](javascript:void(0);)

1. Log on to the company as Administrator.
2. Select the menu command, and then press F7.
3. Select the groups to which you want to provide access.
4. Click **Save**.

| Links to more information . . . [About window and menu-level security](About_window_and_menu-level_security.md) [Setting up user names and passwords](Setting_up_user_names_and_passwords.md) [About security groups](About_security_groups.md) [Setting up window and menu-level security](Setting_up_window_and_menu-level_security.md) [Access rights definitions](Window_and_menu-level_access_rights_definitions.md) |
|---|
