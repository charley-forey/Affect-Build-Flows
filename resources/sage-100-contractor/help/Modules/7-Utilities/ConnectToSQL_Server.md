<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/7-Utilities/ConnectToSQL_Server.htm (Sage 100 Contractor help v20.5) -->

### About the Connect to SQL Server window

When you launch Sage 100 Contractor, the first window that appears is **Connect to SQL Server**.

In this window, you select the SQL Server instance where your company database is located. Depending on the authentication method your company uses to verify credentials, you may also need to enter the user name and password that your system administrator has set up for you.

After you enter the required information, and then click [**Connect**], you can select the company you want to work with from a list of companies you are authorized to use.

#### Selecting the SQL Server name

In most business situations, your Sage 100 Contractor company data is not located on your local computer. It is probably located on a server computer on your local area network. (The server could be a dedicated server computer in a client/server configuration or it could be a colleague’s computer in the next office using a peer-to-peer configuration.)

In a network environment, the **SQL Server Name** list displays all the local drives and all the network drives that you have access to. If you can see the shared network drive in the list, you have access to the Sage 100 Contractor company located on that drive.

If you do not see the drive where the company is located, consider the following questions or consult your network administrator to locate your company.

- Have you lost your network connection? If you have, you cannot access network drives and the Sage 100 Contractor company.
- Has the server lost its network access or crashed? If so, you can access the server and the Sage 100 Contractor company after rebooting.
- Has the Sage 100 Contractor company been moved to a different computer and drive? If so, you must map to the network drive in its new location.

#### Authenticating your user name and password

Your system administrator or a company administrator specifies the type of authentication to use to verify your credentials when they add you to the user list for a Sage 100 Contractor company.

With Windows Authentication (called Integrated Security in the **7-2-2 User List**), you not need to enter a user name and password, providing you signed into Windows using the same credentials as those entered for you in the SQL Server database. Sage 100 Contractor authenticates the user name and password you entered when signing into Windows.

With SQL Server Authentication, you must enter the SQL Server login and password your administrator assigned to you.
