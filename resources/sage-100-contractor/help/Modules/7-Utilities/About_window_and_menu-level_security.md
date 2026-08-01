<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/7-Utilities/About_window_and_menu-level_security.htm (Sage 100 Contractor help v20.5) -->

### About window and menu-level security

Window-level security lets you limit a security group’s ability to open specific windows within Sage 100 Contractor. You can set up window-level security on a menu command that opens a window or sub-level window.

Suppose a small company has three security groups: **General Ledger Clerk**, **A/P A/R Clerk**, and **Payroll Clerk**. Using the window and menu-level security, you can allow only members of the **General Ledger Clerk** group access to windows related to general ledger operations; the **A/P A/R Clerk** group to accounts payable and accounts receivable operations; and the **Payroll Clerk** group to payroll operations.

For menu commands that open a window, Sage 100 Contractor allows access only by users in the selected security groups, and applies the access rights assigned to each group.

For menu commands that open a different menu item, Sage 100 Contractor allows access only by users in the selected security groups. For example, you can provide the **General Ledger Clerk** group access through menu **1-General Ledger**. However, this does not apply the access rights to the items under menu **1-General Ledger**.

Important! Assigning security to a window or menu command does not restrict Dashboard access to the information aggregated by that window or module. You must assign security to Dashboard information separately.

| Links to more information . . . [Setting up window and menu-level security](Setting_up_window_and_menu-level_security.md) [Setting up Dashboard security](Setting_up_Dashboard_security.md) [About access rights regarding window and menu-level security](About_access_rights_regarding_window_and_menu-level_security.md) [Access rights definitions](Window_and_menu-level_access_rights_definitions.md) [About exclusive access](About_exclusive_access.md) |
|---|
