<!-- Source: https://docs.sage.com/docs/en/customer/100contractor/24_1US/open/DatabaseAndCompanyAdministrationGuide.pdf -->

```
Sage 100 Contractor 2022

Database and Company Administration
Guide

Version 24.1

May 2022
This is a publication of Sage Software, Inc.

� 2022 The Sage Group plc or its licensors. All rights reserved. Sage, Sage logos, and Sage product and
service names mentioned herein are the trademarks of The Sage Group plc or its licensors. All other
trademarks are the property of their respective owners.

Last updated: May 24, 2022
Contents

Introduction                                                                     1

How to read this document                                                        2

Sage 100 Contractor data folders                                                 2

Chapter 1: Connecting to SQL Server                                              6

Selecting the SQL Server name                                                    6

Authenticating your user name and password                                       6

Chapter 2: Adding and Deleting Companies                                         7

About adding companies                                                           7

Creating a company based on an existing company's information                    10

Creating a new company                                                           11

About renaming companies                                                         12

Renaming a company                                                               12

Deleting a company                                                               12

About the Sample Company                                                         13

Deploying the Sample Company                                                     15

Chapter 3: Tuning Up, Backing Up, and Restoring Company Databases 16

About tuning up your company database                                            16

Tuning up a company database                                                     16

About backing up your company data                                               17

Backing up a company database                                                    18

About restoring a company from a backup copy                                     19

Restoring a company database from a backup copy                                  20

About creating a backup for Sage Support                                         21

Creating a backup for Sage Support                                               21

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  i
Contents

Chapter 4: Upgrading Databases                                                   22

About upgrading company databases                                                22

Upgrading a company database from an earlier version                             22

Chapter 5: Archiving Company Data                                                24

What is a company archive?                                                       24

About archiving company data                                                     25

Archiving the oldest fiscal year                                                 25

About archiving payroll data                                                     27

Archiving payroll data                                                           28

Chapter 6: Scheduling Nightly Maintenance                                        31

About scheduling nightly maintenance                                             31

Creating a maintenance schedule                                                  31

Modifying a maintenance schedule                                                 32

Removing a maintenance schedule                                                  32

Chapter 7: Managing Company Admins and SQL Logins                                33

About managing access to your SQL Server instance and to company databases       33

Adding a company administrator                                                   35

Modifying company administrators                                                 36

Adding a SQL Server login                                                        36

Deleting a SQL Server login                                                      37

Modifying SQL Server administrators                                              38

Chapter 8: Migrating Your Data from Version 19.8                                 39

About migrating your data from version 19.8                                      39

Migrating company data                                                           42

Migrating custom reports and report forms                                        45

Chapter 9: Server Management Tools                                               46

About managing your server                                                       46

Creating a new SQL Server instance                                               47

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  ii
Contents

Moving Sage 100 Contractor companies to a new SQL Server instance                48

Removing a SQL Server instance                                                   49

Moving your data to a new drive                                                  49

Enabling Sage Mobile Apps                                                        51

Chapter 10: The Toolbox and Troubleshooting                                      54

About using the Toolbox for troubleshooting                                      54

About Dashboard                                                                  54

Server Tools                                                                     58

Company Tools                                                                    59

Copying User Files                                                               62

Support Script                                                                   62

Warning Messages                                                                 63

Chapter 11: Advanced Settings                                                    66

Using Advanced Company Settings to maintain database history                     66

Selecting Advanced SQL Server Settings                                           66

Selecting Backup Settings                                                        67

Selecting Advanced File Attachment Settings                                      68

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  iii
Introduction

The Database Administration tool is intended for system and company administrators. You use it to set up and
maintain your company databases and to manage communications with your Microsoft SQL Server instance.
If you have used earlier versions of Sage 100 Contractor, several of these tasks will be familiar to you. For
example, Database Administration includes utilities for creating and deleting a company, backing up and
restoring company files, and archiving company data that you used in previous Sage 100 Contractor versions.

      Important! Use Database Administration, rather than SQL Management Studio�, to perform the
      database administration tasks listed below, even if you are an experienced SQL Server user. Besides
      handling all the database tasks that you are likely to perform in a typical Sage 100 Contractor system,
      Database Administration was designed to optimize your data for Sage 100 Contractor, for example, by
      keeping related data in expected locations and creating backups automatically before performing certain
      critical processes. In the rare event that you need to use SQL Management Studio� to perform a task
      that is not provided in Database Administration, you should contact Customer Support for assistance.

Database Administration includes the following database and company management utilities:
  l Create Company Based on Existing and Create Company create new Microsoft SQL Server databases.
  l Rename Company and Delete Company are convenient utilities for working with existing companies.
  l Deploy Sample Company helps you install and refresh the sample data that comes with Sage 100 Contractor.
  l Tune Up Company Databases performs various maintenance tasks to keep your database functioning
     efficiently.
  l Back Up Company Databases enables you to back up your data "on demand," whenever needed.
  l Restore Company from Backup restores a selected backed-up copy of your database.
  l Upgrade Company Databases enables you to upgrade your databases smoothly from an earlier version of
     Sage 100 Contractor (SQL).
  l Archive Company Data utilities enable you to archive data for your oldest fiscal year and you Payroll data.
  l Migrate Company Data and Migrate Custom Reports transfers your version 19.8 company data and custom
     reports to a new location for Microsoft SQL Server. Migrated files are located in shared folders under
     C:\Sage100Con\Company\[Company Name], organized using a folder structure similar to earlier versions.
  l Schedule Nightly Maintenance utilities enable you to schedule backup and maintenance operations for times
     when other users are not logged into the system. You can also select the number of consecutive backups to

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  1
     keep.

  l Company Admins/SQL Logins utilities enable you to set up or delete logins to the SQL Server database, and
     to designate a user as a company administrator for a specified Sage 100 Contractor company.

  l Server Management tools enable you to control the SQL Server instances you use with Sage 100 Contractor
     easily and efficiently. You can create a new instance on your computer, move companies to the new instance,
     and remove an instance you no longer need. You can also automatically configure a secure connection to
     enable approved remote users to send information to Sage 100 Contractor.

  l Advanced Settings lets you specify how long to keep history about database changes for each company,
     including details about changed records, such as the date and user ID of the employee made the change.
     Details older than the retention period you specify are cleared during nightly maintenance. (This history is
     maintained in separate audit tables, which you can query using SQL Server Management Studio.)

  l The Toolbox provides a variety of troubleshooting tools to help you track changes in your database, and to
     diagnose and fix certain types of problems.

  l Advanced SQL Server Settings includes convenient, sophisticated access and memory management
     controls for your SQL database.

The Database and Company Administration Guide includes detailed information about these utilities and how
to use them.

How to read this document

This document uses the following conventions:

  l The names of screens, windows, fields, and other features displayed by the software are shown in bold
     type.

  l Information you enter into the software is in bold type, as in the following example:
     Enter Miscellaneous in the Amount Type box.

  l Names of keys are shown in capitals; for example, ENTER, TAB. A plus sign (+) between two key
     names indicates that you should press both keys at the same time; for example, SHIFT + TAB.

  l The names of buttons you can click with your mouse are enclosed in bold type; for example, [OK] and
     [Post].

Sage 100 Contractor data folders

When you are working locally on the server computer, the Sage 100 Contractor folders you see are presented
differently than when you connect to the server from a workstation. When discussing the location of Sage 100
Contractor files and folders with other users, administrators should keep in mind that, although you are viewing
the same underlying data, users connecting to the database through Sage 100 Contractor have a different
view of the data than server administrators.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  2
When you are using Database Administration directly on the server computer, you have access to folders on
the server as you would on any local machine. You can navigate using the local folder structure described
under "Local folder structure (database administrators)" in the table below.

                Folder                 Folder structure on the server
               contents
                                                                       Local folder structure
                                                                    (database administrators)

Main shared folder                        [Local drive]:\Sage100Con

Shared dictionary, and other shared       [Local drive]:\Sage100Con\Common
files (not visible to clients)

Shared custom reports                     [Local drive]:\Sage100Con\Common\Custom Reports

Readme and installation file for          [Local drive]:\Sage100Con\Common\Installation

installing the software on workstations

Shared report forms                       [Local drive]:\Sage100Con\Common\Report Forms

Files and folders for the user's private  [Local drive]:\Sage100Con\Common\User Data\[Windows
reports, forms, user maps, dictionary,    user name]
printer settings, and so on

Company database and subfolders ,         [Local drive]:\Sage100Con\Company\[Company Name]
including Aatrix Forms, Attachments,
Direct Deposit, Images, and Reports

Migration log, audit history log (not     [Local drive]:\Sage100Con\Company\[Company
visible to clients)                       Name]\Files

Payroll a vendor payment folders          [Local drive]:\Sage100Con\Company\[Company
                                          Name]\Files\Direct Deposit

Saved reports                             [Local drive]:\Sage100Con\Company\[Company
                                          Name]\Files\Reports

SQL Express download file (not visible [Local drive]:\Sage100Con\Downloads
to clients)

Sage 100 Contractor restricted            [Local drive]:\Sage100Con\Settings
applications XML file (not visible to
clients)

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1                            3
Because access to Sage 100 Contractor user is limited to certain shared folders on the server, the underlying
folder structure on the server machine is not exposed. Navigation for these users follows different apparent
paths. For example, the main shared folder on the server is called Sage100Contractor, whereas the local
folder is named Sage100Con. Furthermore, the paths to some folders, such as the Custom Reports folder, the
Installation folder, and the company folders, are abbreviated, and do not display the nesting patterns that are
visible on the local machine. Sage 100 Contractor users navigate to folders on the server according to the
folder structure described under "Server folder structure (clients connecting to the server)," below.

                     Folder structure as it appears to other users on the network

                Folder                                Server folder structure
               contents                        (clients connecting to the server)

Main shared folder                        [Server name]\Sage100Contractor

Shared dictionary, and other shared N/A
files (not visible to clients)

Shared custom reports                     [Server name]\Sage100Contractor\Custom Reports

Readme and installation file for          [Server name]\Sage100Contractor\Installation

installing the software on workstations

Shared report forms                       [Server name]\Sage100Contractor\Report Forms

Files and folders for the user's private  [Server name]\Common\User Data\[Windows user name]
reports, forms, user maps, dictionary,
printer settings, and so on

Company database and subfolders ,         [Server name]\Sage100Contractor\[Company Name]
including Aatrix Forms, Attachments,
Direct Deposit, Images, and Reports

Migration log, audit history log (not     N/A

visible to clients)

Payroll a vendor payment folders          [Server name]\Sage100Contractor\[Company Name]\Direct
                                          Deposit

Saved reports                             [Server name]\Sage100Contractor\[Company
                                          Name]\Reports

SQL Express download file (not visible N/A
to clients)

Sage 100 Contractor restricted            N/A

applications XML file (not visible to

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1                  4
           Folder          Server folder structure
          contents  (clients connecting to the server)

clients)

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  5
Chapter 1: Connecting to SQL Server

When you launch Database Administration, the first window that appears is Connect to SQL Server.
In this window, you select the SQL Server instance where your databases are located. Depending on the
authentication method SQL Server uses to verify credentials for this instance, you may also need to enter your
SQL login and password.
After you enter the required information, and then click [Connect], you can use Database Administration to
perform a variety of administrative and database maintenance tasks for all the companies for which you have
access.

Selecting the SQL Server name

In most business situations, your data is probably located on a server computer on your local area network. In
a network environment, the SQL Server Name list displays all the local and network drives to which you have
access.
If you can see the shared network drive in the list, you have access to the databases located on that drive.
If you do not see the drive where the company is located, consider the following possibilities:

  l Have you lost your network connection? If you have, you cannot access network drives or the
     companies on that drive.

  l Has the server lost its network access or crashed? If so, you can access the server and the company
     after rebooting.

  l Has the company been moved to a different computer and drive? If so, you need to map to the network
     drive in its new location.

Authenticating your user name and password

Select the type of authentication your SQL Server database uses to verify your credentials.
With Windows Authentication, you not need to enter a user name and password, providing you signed into
Windows using the same credentials as those entered for you in the SQL Server database. Database
Administration authenticates the user name and password you entered when signing into Windows.
With SQL Server Authentication, you must enter your SQL Server login and password.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  6
Chapter 2: Adding and Deleting
Companies

The Add / Delete Companies utilities enable you to create SQL databases easily for each company for which
you keep books, and to rename and delete existing company databases efficiently.
There is also a utility for deploying the Sample Company that comes with Sage 100 Contractor, and
redeploying it whenever you need to refresh the sample data.

About adding companies

You should create a separate company database for each company that you manage.
The Add / Delete Companies utilities enable you to create SQL databases easily for each company for which
you keep books.

      Note: Sage 100 Contractor handles all aspects of creating, setting up, and administering your company
      database in Microsoft SQL Server. You do not need to learn to use separate database management
      software to take advantage of the benefits of an up-to-date and secure database system.

There are two ways to create a new company. You can either:
  l Create a blank new company "from scratch" using the Create Company utility.
     For more information, see "About creating a company containing no existing company information" (page 9).
  l Create a new company that uses some of the same data as an existing company (such as lists of clients,
     employees, accounts, cost codes, and external files, such as Takeoff grid files, that have no job references).
     You use the Create Company Based on Existing utility to create a company based on an existing one.
     For more information, see "About creating a company based on an existing company " (page 8).

Each new company requires a minimum of 50 megabytes of hard disk space, and as you enter information for
each company, it requires more space. The number of company folders you can retain on your hard disk is
only limited by the amount of available hard disk space.
By storing each company's information in a separate folder, you can back up and restore company information.

      Important! You cannot create a company with the following characters in the company name: :?/ \ |@ . #
      $%^&()

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  7
About creating a company based on an existing company

Setting up new companies from scratch can be very time-consuming, so Sage 100 Contractor provides a
convenient utility that creates a new company based on information in an existing company. If you have an
existing company with a similar structure that uses the features you want to use in a new company, the Create
Company Based on Existing utility can save you a lot of time and effort.

When you use this method to create a new company:

  l The Create Company Based on Existing utility populates the new company database with select
     information from the existing company. Transactions are not transferred to the new company.

  l The new company's default posting period is set to the same posting period as the existing company. If
     necessary, you can change the default posting period for the new company using the Change Period
     feature in the Sage 100 Contractor 1-6 Period/Fiscal Year Management window.

      Note: Do not use this feature to create backup copies of your data. Sage 100 Contractor provides a
      separate, convenient method to back up company data on a regular basis. For more information, see
      "Backing up a company database" (page 18).

Before creating a company based on an existing company

Before creating a new company from an existing company, you should:
  l Determine whether an existing company is a good match for your new company.
  l Make sure that you have exclusive access to the existing company database. You can create a new company
     from an existing company only if you have exclusive access to the database.
  l Make sure you have sufficient hard disk space to create the new company (at least 50 megabytes to start,
     with space to grow).
  l Make sure your network administrator has given you Write access to the selected drive.

Information transferred to the new company

Information transferred to the new company includes:

           Type                   Includes, but not limited to

List data        Clients
                 General Ledger Accounts
                 Employees
                 Cost Codes
                 Parts
                 Vendors

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1                               8
Type                                     Includes, but not limited to

External files with no job reference     Takeoff template files
                                         Takeoff grid files
                                         Bitmap images for clients, employees, and so on
                                         Attachments

Note: The program does not transfer balances for these records.

If a field within a table contains transactional data, it is not copied.

                       Type                               Includes, but not limited to
Transactional data directly related to
jobs                                     Accounts receivable
                                         Field reports
Transactional data contained in a field  Inventory allocations
within a table                           Payroll records

                                         Accounts payable--beginning balance and ending
                                         balance
                                         Employees--Qtr1 gross, Qtr2 gross, and so on
                                         Ledger accounts--beginning balance and ending
                                         balance

About creating a company containing no existing company information

When you create a brand new company, not based on existing company information, Sage 100 Contractor
creates a new company database with table headings, but no other information.

After creating the new company, you need to enter the following information using windows in Sage 100
Contractor:

  l Enter new company information on the 7-1 Company Information window. You will find it helpful to have
     the following information on hand:
        l Complete company address
        l License number
        l Federal tax identification number
        l State tax identification number
        l Business Number
        l Canada Revenue Agency Program Accounts
        l Resale number

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1                            9
        l Telephone and fax numbers
        l Email address
        l Direct deposit information, which is the account number, routing number, and the account type.
  l Use the 1-8 General Ledger Setup window in Sage 100 Contractor to set up your accounting structure,
     fiscal year date, current period, sales tax setup, and inventory valuation method (if you have the
     Inventory Add-on Module).

Creating a company based on an existing company's
information

Using the Create Company Based on Existing utility can save you a lot of time and effort when creating new
companies.

Before you start

  l Determine whether an existing company is a good match for your new company.
  l Make sure that you have exclusive access to the existing company database. You can create a new

     company from an existing company only if you have exclusive access to the database.
  l Make sure you have sufficient hard disk space to create the new company (at least 50 megabytes to start,

     with space to grow).
  l Make sure your network administrator has given you Write access to the selected drive.

To create a new company based on an existing company's information

1. Click Add / Delete Companies > Create Company Based on Existing.
2. From the Select the source company list, select the name of the existing company you want to use as

     the basis for the new company.
3. In the Enter a name for the new company text box, type the name of the new company.
4. Use the options in the Maintenance section to specify:

       l The time to run nightly maintenance.
       l The number of backups to keep.
5. Click [Create Company].
     A status message in the lower left corner of the tab displays the progress of company creation.

After creating the new company

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1                               10
  l Enter company information on the 7-1 Company Information window Sage 100 Contractor.
  l Use the 1-8 General Ledger Setup window in Sage 100 Contractor to set up your accounting structure,

     fiscal year date, current period, sales tax setup, and inventory valuation method (if you have the
     Inventory Add-on Module).

Creating a new company

When you create a brand new company, not based on existing company information, Sage 100 Contractor
creates a new company database with table headings, but no other information.

      Note: Setting up new blank companies is a time-consuming process. If you have an existing company
      that has the same structure and uses the same features as the one you want to create, consider using
      the Create Company Based on Existing utility, which can save you a lot of time and effort.

Before creating a new company

When creating a new company, you must specify a company administrator who has been added as a user to
your SQL Server database. Therefore, be sure you have created a SQL Server login for the user you want to
designate as the administrator for this company.

To create a new company containing no existing company information:

1. Click Add / Delete Companies > Create Company.
2. In the Enter a name for the company text box, type the name of the new company.
3. From the Select a company administrator list, select the user you want to designate as the administrator

     for this company.
4. Use the options in the Maintenance section to specify:

       l The time to run nightly maintenance.
       l The number of backups to keep.
5. Click [Create Company].
     A status message in the lower left corner of the tab displays the progress of company creation.

After creating a new company

  l Enter new company information on the 7-1 Company Information window Sage 100 Contractor.
  l Use the 1-8 General Ledger Setup window in Sage 100 Contractor to set up your accounting structure,

     fiscal year date, current period, sales tax setup, and inventory valuation method (if you have the
     Inventory Add-on Module).

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1                              11
About renaming companies

If your company, or one of the companies you manage, changes the name under which it does business, you
probably want to change the name of the company in your Sage 100 Contractor program. Renaming a
company using Database Administration for Sage 100 Contractor is a very easy, straightforward process.
On the Rename Company tab, you simply select the company you want to rename, enter the new name, and
then click the [Rename Company] button.
The program creates a backup copy of the existing company before renaming it.
When renaming a company, you can also change the nightly maintenance schedule or the number of backups
to keep for the company.

Renaming a company

If your company, or one of the companies you manage, changes the name under which it does business, you
probably want to change the name of the company in your Sage 100 Contractor program. Renaming a
company using Database Administration for Sage 100 Contractor is a very easy, straightforward process.

To rename a Sage 100 Contractor company

1. Click Add / Delete Companies > Rename Company.
2. From the Select the company to rename list, select the existing company name.
3. In the Enter a new name for the company text box, type the new name for the company.
4. (Optional) Use the options in the Maintenance section to specify:

       l The time to run nightly maintenance.
       l The number of backups to keep.
5. Click [Rename Company].
     A message appears asking whether you are sure you want to rename the selected company.
6. Click [Yes] to rename the company.
     The program creates a backup copy of the existing company before renaming it.
     A status message appears when renaming is complete.

Deleting a company

You use the Delete Company tab to delete a selected company.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  12
To delete a company database

1. Click Add / Delete Companies > Delete Company.
2. From the Select the company to delete list, select the name of the company you want to delete.
3. Click [Delete Company].

     A warning message asks whether you are sure you want to delete the selected company.
4. If you are sure you want to delete the company, click [Yes].

      Note: Sage 100 Contractor creates a backup copy of the company before deleting it. You can find the
      backup copy in the DeletedCompanies folder in your usual backup location.

About the Sample Company

Sage 100 Contractor comes with a set of sample data, "Sample Company," installed together with the Sage
100 Contractor software.

The Sample Company includes:
  l Sample accounts, sample employees, sample takeoffs, and much more.
  l Starter lists for many values you will need to set up cost codes, cost types, tasks, client status, client
     type, employee positions, paygroups, and so on.
  l Samples of many Sage 100 Contractor forms that are already filled in, making it easy to understand
     many concepts.
  l Live data to investigate the content of Sage 100 Contractor reports.

 Note: We highly recommend that you deploy the Sample Company data. While taking little space on your
 hard disk, Sample Company lets you and other users practice using Sage 100 Contractor without any risk to
 your own company data. Sage 100 Contractor master trainers use Sample Company extensively during
 Sage 100 Contractor training classes, and in many online and recorded classes.

About deploying Sample Company

After installation, or any time you want to restore Sample Company to its original state after users have worked
with it, you use the Deploy Sample Company tab to make Sample Company available for use in Sage 100
Contractor.

When you deploy Sample Company, you are added as a company administrator to the list of Sample Company
users in Sage 100 Contractor, along with a set of sample users. For more information, see "Sample user
names and passwords" (page 14).

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  13
When you redeploy Sample Company, any users that have been added to Sample Company in Sage 100
Contractor are retained.
For steps on deploying Sample Company, see "Deploying the Sample Company" (page 15).

Sample user names and passwords

Users can log in to the sample company using one of the user names that comes with the sample data, or they
can use their usual Sage 100 Contractor credentials, providing the company administrator adds them as users
in the Sample Company.
When you deploy sample data for the current version, the "sample users" are:

  l For the U.S. Edition:
        l Bryan - Sample User (Owner/Comptroller)
        l Debra - Sample User (Owner/Comptroller)
        l Ginger - Sample User (Payables)
        l Jenny - Sample User (GL/Receivables/Payables)
        l Josh - Sample User (Estimator/PM)
        l Lynn - Sample User (Owner/Comptroller)
        l Scott - Sample User (Estimator/PM)

  l For the Canadian Edition:
        l Angela - Sample User
        l Becky - Sample User
        l Brandi - Sample User
        l Brandy - Sample User
        l Denise - Sample User
        l Gerald - Sample User
        l Heidi - Sample User
        l Ken - Sample User
        l Kyle - Sample User
        l Melinda - Sample User
        l Rachel - Sample User
        l Scott - Sample User
        l Vincent - Sample User

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  14
If you migrated the Sample Company from version 19.8, the list of users will be the same as it was in that
version. If the user names were not modified in the earlier version, the users names are the same as those
listed here, but without "Sample User" at the end. (For example, rather than "Bryan � Sample User," the user is
simply "Bryan.")

      Note: These sample users all use the password password.

Deploying the Sample Company

Sage 100 Contractor comes with a set of sample data, "Sample Company," installed together with the Sage
100 Contractor software.

You can deploy the Sample Company after installation, or any time you want to restore Sample Company to its
original state after users have worked with it.

When you deploy Sample Company, you are added as a company administrator to the list of Sample Company
users, which includes a set of sample users, in Sage 100 Contractor.

When you redeploy Sample Company, any users that have been added to Sample Company in Sage 100
Contractor are retained.

To deploy the Sage 100 Contractor Sample Company

1. Click Add / Delete Companies > Deploy Sample Company.
2. Click [Deploy Sample].

After deploying Sample Company

  l Use the tabs under the Company Admins / SQL Logins menu to add or change company administrators
     for Sample Company.

  l Open the Sage 100 Contractor program as a copmany administrator, and then use the 7-2-2 User List
     window to set up additional users.

  l Provide user names and passwords to users in your own company who want to work with the sample data.
     For information about the names and roles of the sample users, see "About the Sample Company" (page
     13).

            Note: The password for the sample users that come with Sample Company is password.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  15
Chapter 3: Tuning Up, Backing Up, and
Restoring Company Databases

About tuning up your company database

Database Administration automatically performs maintenance tasks to keep your database functioning
efficiently. This maintenance takes place according to schedules you create and assign to companies using
the tabs under Schedule Nightly Maintenance. For more information about nightly maintenance schedules, see
"About scheduling nightly maintenance" (page 31).
You can also use the Tune Up Company Databases utility to run maintenance tasks at other times, whenever
you need to. For more information about running maintenance "on demand," see "Tuning up a company
database" (page 16).

      Note: The Tune Up Company Databases tab shows the last time maintenance was performed for each
      Sage 100 Contractor company in your SQL Server instance.

Tuning up a company database

Tuning up your company database optimizes your company data to help it run efficiently and without errors in
Sage 100 Contractor.
Your database is tuned up automatically during nightly maintenance according to the schedule you specify on
the Create Maintenance Schedules or the Modify Maintenance Schedules tab. However, you can also tune up
your database on demand from the Tune Up Company Databases tab.

Before you tune up a company database

      Make sure no users are logged in to the company. Sage 100 Contractor will terminate their connections
      60 seconds after you start the tune up. Terminating connections in this way can cause problems if a
      user is actively working in the company when their connection is cut off (for example, if they are posting
      payroll to the general ledger or working in an estimate that they haven't saved recently).

To tune up a company database on demand:

1. Click Tune Up / Back Up / Restore > Tune Up Company Databases.
2. On the tab to the right, select the company or companies you want to tune up.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  16
3. Click [Tune Up Databases].

      Note: Any users who are logged in to the database when you perform a tuneup are warned that they will
      be disconnected in 60 seconds. Terminating connections can cause problems if the user is actively
      working in the company when their connection is cut off (for example, if they are posting payroll to the
      general ledger or working in an estimate that they haven't saved recently.

About backing up your company data

Routinely backing up your accounting data is essential to ensure its safety and integrity.

There are many causes for data corruption, ranging from faulty hardware to power fluctuations. While you can
replace program files or computer hardware, you cannot easily replace accounting data without a backup
copy.

Database Administration for Sage 100 Contractor provides a utility for backing up your company data
automatically to a network location or a local folder during nightly maintenance. Creating a series of backup
copies over time enables you to restore your data from a point prior to the errors, without needing to re-enter all
your accounting data manually.

      Important! You should store at least one copy of your backed-up data off premises or in a fireproof safe.
      If a burglary or fire occurs, a copy of your data is safe from harm. We strongly recommend that you
      routinely store backed-up copies of your data in a safe environment that is separate from your server,
      preferably off site.

Backing up during nightly maintenance

You use the tabs under Schedule Nightly Maintenance to schedule the time that maintenance and backup
occur, as well as the number of backup copies to keep. For more information about scheduling, see "About
scheduling nightly maintenance" (page 31).

Database Administration saves backup copies created during nightly maintenance to the
C:\Sage100Con\Backup\Nightly folder.

      Important! You need to ensure that both the server that hosts your company database and the computer
      where the backup copies are saved are always turned on at the scheduled time.

The automated backup procedure creates a separate zipped file for each company by date. The zipped file
includes the following data:

  l A backup copy of the company's SQL database.
  l All the company files.
  l The files in the Sage100Con\Common folder.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  17
Backing up "on demand"

You can also create backup copies manually, "on demand," at any time using the Back Up Companies tab. For
steps on backing up your company manually, see "Backing up a company database" (page 18).
The default location for backup copies you create manually is C:\Sage100Con\Backup\On Demand. Database
Administration also saves backup copies to this folder whenever you archive company data or delete a
company.

Backing up a company database

Database Administration for Sage 100 Contractor provides a utility for backing up your company data to a
network location or a local folder automatically, according to a nightly maintenance schedule.
You can also create backup copies manually, "on demand," at any time using the Back Up Companies tab.

      Important! Always use Database Administration to back up your data. Database Administration backs up
      numerous files (including external files, such as attachments) that are not part of the SQL database, and
      it performs additional steps to ensure that you can successfully restore your data from a backup copy. Do
      not attempt to back up Sage 100 Contractor data using Microsoft SQL Server Management Studio or
      other third-party software, or you will be unable to restore the company.

Before backing up

      Important! Ensure that both the server that hosts your company database and the computer where the
      backups are to be saved will always be turned on at the scheduled time.

To back up a company "on demand":

1. Click Tune Up / Back Up / Restore > Back Up Companies.
2. In the grid on the tab, select the check mark beside each company you want to back up at this time.
3. If you want to store the backup file in a different location than the default folder (C:\Sage100Con\Backup\On

     Demand), browse to and then select the backup folder you want to use.

       Tip: If the folder does not yet exist, you can make a new folder.

4. Click [Create Backup].

After backing up

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  18
Consider copying your backed-up data to additional media for off-site storage or to another network location,
in case of fire or a burglary at the location where you keep the computer that runs Sage 100 Contractor. For
more information, see "Backing up your data to a CD or DVD" (page 19).

Backing up your data to a CD or DVD

This topic suggests a way to copy backed-up data to a CD or DVD for offsite storage.
Sage 100 Contractor automatically backs up your data to a server location and according to the maintenance
schedule specified for your company. You can also back up your data at any time using the backup function in
Sage 100 Contractor.

To copy your data to a CD or DVD:

1. On your server machine, place the CD or DVD media in the CD or DVD drive.
2. On your Windows desktop, right-click [Start] > Explore.
3. In Windows Explorer:

      a. Locate and then right-click the C:\Sage100Con\Backup\On Demand folder.
      b. In the On Demand folder, right-click the backup that you want to copy.
      c. From the menu, select Copy.
4. Locate and then click the CD or DVD drive.
5. In the right-pane, right-click and then select [Paste].
     Depending on your hardware and software, the folder is copied to the CD or DVD media.
For further information or support, contact your CD or DVD manufacturer.

About restoring a company from a backup copy

Database Administration makes restoring your company data following a system failure or the purchase of new
hardware a very straightforward process, assuming you have kept backups up to date in an accessible
location.
On the Restore Company from Backup tab, you select the backup file you want to restore, select maintenance
and backup options for the restored company, and then click the [Restore Company] button.

      Note: If you installed a new version of Sage 100 Contractor since you backed up your company, you can
      choose to upgrade the company database automatically during the restoration process.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  19
Restoring a company using a different name

There may be occasions when you want to restore a company from a backup copy without overwriting the
company you are using in your production environment. For example, you might want to work with a temporary
copy of the data for research purposes, without disrupting work in your current company.
Database Administration enables you to create a copy of your backed-up data by restoring the company using
a different name, leaving the current company intact. Before you click [Restore Company], type the name you
want to use for the copied company in the Restore as box.

Restoring a company database from a backup copy

If your computer is damaged or your data becomes corrupted, you use the Restore Company from Backup tab
to restore your company from a backup file.

Before restoring a company

  l Determine the date when valid data you want to restore was most recently backed up.
  l Identify the name and location of the backup file for that date for the company.

     The default location for backup files is: C:\Sage100Con\Backup.
  l Make sure no other users are logged into the company database.

To restore a company from a backup copy:

1. Click Tune Up / Back Up / Restore > Restore Company from Backup.
2. In the Enter the backup file you want to restore box, browse to and then select the backup file from which you

     want to restore your company database.
3. If you want to restore the data using a different name for the company, leaving the existing company intact, in

     the Restore as box, type the name you want to use for the copied company.
4. If you installed a new version of Sage 100 Contractor since you backed up your company, select

     Upgrade the company database to the latest version after restoration.
5. If you want to run nightly maintenance on the restored database, select Set up a nightly maintenance

     schedule and backup task for the restored company, and then:
      a. Select the time to run the maintenance.

            Select the number of backups to keep.
6. Click [Restore Company].

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  20
About creating a backup for Sage Support

If Sage Customer Support needs to examine a copy of your company to help you to resolve a problem with
Sage 100 Contractor, they will ask you to create a special backup copy of your company files. This backup is a
stripped-down version of your company that does not include sensitive or personal information, and does not
include external files, such as attachments.

On the Create Sage Support Backup tab, you select the company whose files you want to send to Sage
Support, and then click the [Create Backup] button.

      Note: Because this backup is incomplete, you should never use it to restore your company data. For this
      reason, backups are saved in a separate Support Backups folder and include BackupForSage in the file
      name.

Creating a backup for Sage Support

If Sage Customer Support needs to examine a copy of your company to help you to resolve a problem with
Sage 100 Contractor, they will ask you to create a special backup copy of your company files. This backup is a
stripped-down version of your company that does not include sensitive or personal information, and does not
include external files, such as attachments.

To back up a company for Sage Customer Support:

1. Click Tune Up / Back Up / Restore >Create Sage Support Backup.
2. On the Create Sage Support Backup tab, in the Select company to send to Sage box, select the company you

     want to back up.

     Sage 100 Contractor uses ..\Sage100Con\Backups\Support Backups on the drive where you store your
     company data as the default location, but you can browse to a different location or type a different path in the
     Enter the location for the backup file box.
3. Click [Create Backup].

     Sage 100 Contractor creates a ZIP file, automatically naming the file after the company you are backing up
     and including BackupForSage in the file name.

After backing up

Send the file to Customer Support as instructed.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  21
Chapter 4: Upgrading Databases

About upgrading company databases

Upgrade Company Databases prepares your SQL company data so that it is compatible with the most recent
version of Sage 100 Contractor.
You can update the databases for multiple companies at once, or you can update them one at a time, as
needed.

      Note: Do not use this utility to upgrade your data from version 19.8. You use Migrate Company Data and
      Migrate Custom Reports to migrate your data to a Microsoft SQL Server database from version 19.8.

Upgrading a company database from an earlier version

After installing a new version of Sage 100 Contractor, you may need to upgrade existing company databases
so they are compatible with the new version.

      Important! Do not use this utility to upgrade your data from version 19.8! Use the Migration utility instead.
      For more information, see "About migrating your data from version 19.8" (page 39)

Before upgrading a company database

  l Install the latest version of Sage 100 Contractor.
  l Make sure no other users are logged into any of the company databases you are upgrading.

To upgrade a company from an earlier version:

1. Click Upgrade Company Databases.
2. In the grid on the tab, select the checkbox beside each company you want to upgrade to the current version of

     Sage 100 Contractor.
     You can upgrade the databases for several companies at once, or you can upgrade them one at a time, as
     needed.

            Tip: Use the [Clear All] button to clear your selections of databases al at once
3. Click [Upgrade Database].

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  22
After upgrading a database

Be sure to upgrade all workstations that need access to the database to the same version of Sage 100
Contractor!

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1                       23
Chapter 5: Archiving Company Data

What is a company archive?

Over the course of a year, the accounting and payroll databases grow as you enter records. In a manual
accounting system, you might move previous years' records to storage boxes or a storage facility. Similarly,
you can move Sage 100 Contractor records to an archive file when you no longer need the data for a fiscal
year.

When you archive company data, Sage 100 Contractor:

  l Removes the accounting activity from the oldest fiscal year (12 periods) in your current company, and
     places it in an archive company.

  l In your current company books, adjusts the beginning balances for asset, liability and equity accounts
     and sub-accounts, as well as jobs, vendors, service clients, and equipment to match the archive year's
     corresponding ending balances.

  l Rolls income and expense balances for the archive year roll into the beginning balance for the Retained
     Earnings account in the current company.

At year end, if I don't have enough hard disk drive space to create an archive
company, what can I do?

If you do not have enough disk space, free up disk space by deleting unnecessary files or programs, or
manually copy the data to another hard disk drive, CD, or DVD.

When do I create the company archive?

You can create a company archive at any time after you have advanced to at least period 1 of the next fiscal
year.

We recommend that you archive as soon as you have resolved all audit errors, and you have received and
entered all accounting entries, including adjustments.

      Important!

        l If you have more than one fiscal year to archive, you may perform the archive process more than
           once.

        l If you have only one year's worth of data to archive, you must advance to at least period 1 of the
           next fiscal year in your current company books.

        l The company folder cannot be in the same fiscal year that you are trying to archive.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1                               24
Where in the program do I create a company archive?

You use the Archive Oldest Fiscal Year utility in Database Administration to archive your company.
You use the Archive Payroll Data utility in Database Administration to archive your Payroll data.

What about data backup?

To prevent loss of data, we highly recommend that you always store one copy of your backed-up data off site
for added security.
After creating the company archive, review it to make certain that all records were copied correctly. If you find
that the archive is incomplete, restore from a backup copy, and then create a new archive.

About archiving company data

You can archive your data from a given fiscal year at any time. You can advance your fiscal period and archive
fiscal data separately. You do not need to close the books at year end, and you do not have to archive your
data before advancing to the next fiscal year.
You can archive up to 12 periods at one time. If you have more than one year of fiscal data to archive, perform
the archive process more than once.
The Archive Data wizard leads you through the process of archiving your data from previous fiscal periods. It
removes the oldest fiscal year of data from your current company, and places it in a separate archive company.
Therefore, before archiving a fiscal year, ensure your current period is not in the same fiscal year.

      Note: You cannot archive a fiscal year until you advance the default posting period to at least period 1 of
      the following year. You must advance your fiscal period using the Change Period window in the Sage
      100 Contractor application.

      Important! Closing the payroll is not the same as closing the accounting books. All companies close
      payroll at the end of the calendar year, but not all companies close the fiscal year in the general ledger at
      the end of the calendar year.

Archiving the oldest fiscal year

The data archive process removes the oldest fiscal year of data from your current company, and places it in a
separate archive company. Therefore, before archiving a fiscal year, ensure your current period is not in the
same fiscal year.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  25
The Archive Data wizard leads you through the process of archiving your data from previous fiscal periods.
You can archive up to 12 periods at one time. You do not have to close your fiscal year before archiving your
data.

Before archiving

Make sure you have:
  l Administrator rights for the company you want to archive.
  l Posted all transactions for the year you are archiving.
  l Advanced the default posting period to at least period 1 of the year following the one you are archiving.
     (You advance your fiscal period using the Change Period window in the Sage 100 Contractor
     application.)
  l Created at least two backups of your company data.

To archive a fiscal year

1. Click Archive Company Data >Archive Oldest Fiscal Year.
2. On the Archive Oldest Fiscal Year tab, select the company you want to archive from the list box.

            Note: You can archive only companies for which you have administrator rights.

     The Archive Data wizard opens, displaying information about the archiving process and the tasks you should
     have completed before archiving.

            Tip: As you proceed through the wizard, you can click the [Help] button to view more detailed
            information about each page.

3. Click [Next] .
4. On the Preparation page:

      a. Click [Begin Preparation] to start performing all the listed preparatory tasks.

                  Note: If any problems are encountered, the process stops, and the text on this button changes to
                  [Resume Preparation]. Click [Resume Preparation] to continue running subsequent tasks to see if
                  there are additional items that require your attention.

      b. When all the preparatory tasks are complete and without error, click [Next].

                  Note: You can click [Next] only when all tasks have been completed successfully.

5. On the Maintenance Options page, select one or more maintenance tasks you want to perform prior to
     archiving, and then click [Next].

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1                                     26
6. On the Archive Data page:
      a. Type a name for the company archive in the Enter name for the company archive box. The name cannot
            contain any special characters
      b. Click [Begin Archiving], and then click [Yes] if you are sure you have backed up your data and completed the
            other tasks in the "Before archiving" section.

                  Note: If the archive folder exists, it must be empty. Click [Yes] to continue the process, or click [No] to
                  go back to the Archive Data page.

            If you selected maintenance options before archiving, you can click View Result to display a message box
            that lists information about the maintenance tasks completed.
      c. Click [Next].
            When the archiving process has finished, the wizard backs up your data, and then displays information
            about working with your archive company.
7. Click [Close] .

After archiving a fiscal year

If you have more than one year of fiscal data to archive, you will need to run the archive process separately for
each year.

About archiving payroll data

At the end of the calendar year, you archive the payroll to close it and prepare for the new calendar year.
During the close, Sage 100 Contractor removes all payroll records and resets the quarter-to-date and year-to-
date totals to $0. You can also delete old or unneeded employee records.

      Important! Closing payroll does not affect the accrued vacation, sick, and compensation times in the
      employee records that you choose to retain.

      Note: The payroll archive company is different from the general ledger archive company. If you enter
      transactions between closing the fiscal year and closing payroll, back up and archive your accounting
      and payroll records separately to ensure that you have permanent records of all your data.

Before entering timecards for the new calendar year, audit, back up, and then close/archive the payroll.
Although you may back up your company data at any time, in the context of closing the payroll, it makes sense
to back up your data after you have audited it and corrected any errors.

Closing payroll can be time consuming, and the time necessary to create an archive may be considerable
depending on the number of payroll records and employees contained in each company. We recommend
creating a schedule of tasks to perform leading up to the close. For example, consider auditing the payroll a

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  27
month in advance of the scheduled closing date. This should provide enough time to resolve any errors that
might exist.
Before archiving, ensure that there are no uncomputed or unposted payroll records. You need to post or void
an unposted payroll records before you can archive payroll.

      Note: When you close a payroll year, Sage 100 Contractorcreates new ACA records for the new payroll
      year. It uses the December values from the previous year as defaults for each month of the new year.

Verifying the payroll archive

You should check the number of payroll records and Accounts Payable invoices before and after archiving to
ensure that your payroll archive is not missing any records.

To verify the payroll archive:

1. Open Sage 100 Contractor, and then:
      a. Select the company whose payroll you are going to archive.
      b. Open 5-2-2 Payroll Records, click File > Count, and then note the total number of records.
      c. Open 4-2 Accounts Payable Invoices, click File > Count, and note the total number of records.
      d. Exit Sage 100 Contractor.

2. In Database Administration for Sage 100 Contractor, archive the payroll.
3. Open Sage 100 Contractor, and then:

      a. Select the archive you created in step 2.
      b. Open 5-2-2 Payroll Records, click File > Count, and then note the total number of records.
      c. Open 4-2 Accounts Payable Invoices, click File > Count, and then note the total number of records.
4. Compare the record totals before archiving with those from the archive.
       l If the totals agree, the records have been archived correctly.
       l If the totals do not agree, the archive is incomplete. Restore the company from a backup, and create

          new archives.

Archiving payroll data

        l Archiving and closing payroll at the end of the calendar year is a separate process from closing
           the fiscal year in the general ledger.

        l You cannot process payroll for the new calendar year until you close payroll for the previous year.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  28
        l You cannot enter payroll data with check dates in the new calendar year until you close payroll for
           the previous year.

Before you archive payroll data

  l Review the Year End Guide to make sure you are familiar with all aspects of closing a payroll year.
  l Make sure that there are no uncomputed or unposted payroll records.
  l Make sure that you are in your current company and not in your general ledger archive company.
  l Back up and verify two copies of your Sage 100 Contractor data.

        l Put one copy in a safe storage area.
        l Save at least one of your backup copies on a separate removable storage device.

                  Note: You can use this backup copy to verify data integrity if you have to close again.

  l Make sure no other users are logged into the company.

To archive payroll data:

1. Click Archive Company Data >Archive Payroll Data.
2. On the Archive Payroll Data tab:

      a. From the Select the company to archive list box, select the company for which you want to archive
           payroll .

      b. In the text box, type a name for the payroll archive.
      c. If you want to remove records for employees who no longer work for the company, select their statuses as

            follows:
             l To remove records with 3-Quit status, select the Quit checkbox.
             l To remove records with 4-Laid Off status, select the Laid Off checkbox.
             l To remove records with 5-Terminated status, select the Terminated checkbox.
             l To remove records with 7-Deceased status, select the Deceased checkbox.
      d. If you want to verify the removal of each employee during the archive process, select Approve each
            employee's removal.
3. Click [Create Archive] .

      Tip: The first payroll of a new year may include ACA hours attributable to the previous year. in the Sage
      100 Contractor application, when you run the 5-4-3-21 ACA Hours Allocation report for an archive
      company, you can use the Combine Company for ACA Hours Allocation window Sage 100 Contractor to

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1                                    29
combine the report results with the hours entered in the active company. The ACA report then includes
payroll records entered for the previous year in the active company's new year.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1                        30
Chapter 6: Scheduling Nightly
Maintenance

Schedule Nightly Maintenance utilities enable you to schedule backup and maintenance operations for times
when other users are not logged into the system. You can also select the number of consecutive backups to
keep.

About scheduling nightly maintenance

You create maintenance schedules so that Sage 100 Contractor will perform maintenance tasks (such as
checking data integrity, creating backup copies of your company databases, and removing expired backup
files and history tables) at a time when no other users are logged into the system.
You can specify a single schedule for all your Sage 100 Contractor companies, or you can use separate
schedules for each company. For example, if you need to keep backup files longer for some companies than
for others, you can create separate schedules based on the number of weeks of backup to maintain.

Creating a maintenance schedule

You create maintenance schedules so that Sage 100 Contractor will perform maintenance tasks (such as
checking data integrity, creating backup copies of your company databases, and removing expired backup
files and history tables) at a time when no other users are logged into the system.
You can specify a single schedule for all your Sage 100 Contractor companies, or you can use separate
schedules for each company. For example, if you need to keep backup files longer for some companies than
for others, you can create separate schedules based on the number of weeks of backup to maintain.

Before you start

  l Determine the best time to perform maintenance for each company (or for all companies).
  l Decide whether to keep backup files for one, two, three, or four weeks, or to keep only the latest backup (not

     recommended!). Expired backup files are deleted during nightly maintenance.
     You can also keep all backup files, if you prefer.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1                                     31
To create a backup schedule:

1. Click Schedule Nightly Maintenance >Create Maintenance Schedules.
2. On the Create Maintenance Schedules tab, select the checkbox beside each company that will follow this

     maintenance schedule.
3. From the Select the time for nightly maintenance list, select the time to perform maintenance for these

     companies.
4. From the Select the number of backups to keep list, select the period of time to maintain backup files for

     these companies.
5. Click [Save Schedule].

Modifying a maintenance schedule

You can change an established maintenance schedule for any company at any time.

To modify a maintenance schedule:

1. Click Schedule Nightly Maintenance >Modify Maintenance Schedules.
2. On the Modify Maintenance Schedules tab, select the checkbox beside each company for which you

     want to change the maintenance schedule.
3. Click [Modify Schedule].

Removing a maintenance schedule

If you no longer want maintenance performed for a company, you can remove its maintenance schedule.

To remove a maintenance schedule:

1. Click Schedule Nightly Maintenance >Remove Maintenance Schedules.
2. On the Remove Maintenance Schedules tab, select the checkbox beside each company for which you want

     to remove the maintenance schedule.
3. Click [Remove Schedule].

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1                                32
Chapter 7: Managing Company Admins
and SQL Logins

You use the Company Admins / SQL Logins utilities to authorize user access to the SQL Server database, to
designate one or more users as a SQL Server administrator, and to assign administrative privileges to certain
users for a Sage 100 Contractor company.

About managing access to your SQL Server instance and to
company databases

Sage 100 Contractor2022 provides strong security for your company data.
You use the Company Admins / SQL Logins utilities to authorize user access to the SQL Server database, to
designate one or more users as a SQL Server administrator, and to assign administrative privileges to certain
users for a Sage 100 Contractor company.
You can use Database Administration to set up employees as users in your SQL Server instance, and to
designate a user as a company administrator for a specified Sage 100 Contractor company.
A company administrator can always set up additional users and access privileges for those users in a Sage
100 Contractor company for which they have administrative rights.
However, you must use Database Administration to designate a user as a SQL Server system administrator
(with a 'sysadmin' role).

Allowing access to the SQL Server database

All Sage 100 Contractor users must be registered in your SQL Server system database, which is separate from
your company database.
When you or another company administrator adds employees as users in Sage 100 Contractor, you authorize
them to use your SQL Server database by:

  l Adding their user names to your SQL Server instance.
  l Selecting a method to authenticate their user names and passwords.
  l Defining their passwords (depending on the authentication method you select).
  l Optionally, assigning a system administrator role to a user.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  33
You use the Add SQL Server Login tab to add users, along with their credentials, to your SQL Server instance.
Also, when a company administrator adds a user to the 7-2-2 User List in Sage 100 Contractor, the program
automatically creates a SQL Server login if the user ID does not yet exist in the SQL Server database.

      Important! The migration utility creates logins for all existing users in the version 19.8 company,
      assigning the same user names and passwords as before.

Prohibiting all access to the SQL Server database

If an employee leaves your company, use the Delete SQL Server Logins tab to remove all access to the SQL
Server instance for that employee.

     Important! After you delete a user's SQL Server login, they can no longer sign in to any Sage 100
      Contractorcompany.

If you need to remove a user's access rights to one company, while maintaining their access to other
companies, remove the user from the 7-2-2 User List for the company in Sage 100 Contractor.

Assigning administrator privileges for a selected company

Users you designate as company administrators have access rights to the entire Sage 100 Contractor
program. In addition, only company administrators can perform the following tasks in Sage 100 Contractor:

  l Create security groups.
  l Grant access rights to security groups for windows and certain items within windows.
  l Grant job-level security to specific users.
  l Display field properties for a dialog box to set security properties for its various elements or to customize

     the window in other ways.
  l Create user names and passwords, and assign user names to security groups in the 7-2-2 User List

     window.
  l Set up and modify the General Ledger.
  l Restrict posting to specific accounting posting periods.
You use the Add Company Administrators tab to designate existing users as administrators for a selected
company.

You use the Modify Company Administrators if you need to remove a user's administrator access to a selected
company, or to restore administrator access to a user that has had it before.

      Note: When you migrate a company, you can select a company administrator from the list of users in the
      version19.8 company.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  34
SQL Server System administrators ("sysadmin")

Only a user with a sysadmin role in Microsoft SQL Server can administer access to the SQL Server database
and assign the sysadmin role to another user. Therefore, it is vital at all times that more than one user has a
sysadmin server role. If the principal system administrator should suddenly fall ill, or leave your company, or
otherwise be unable to perform their duties, another person with administrative access to the SQL Server
database must be able to take over that role.

      Note: The person who installs Sage 100 Contractor is automatically assigned a sysadmin role.

You can designate a user as a sysadmin either when you add their SQL Server login or by using the Modify
SQL Server Administrators tab.

You also use the Modify SQL Server Administrators tab to remove the sysadmin role for a user.

Adding a company administrator

Users you designate as company administrators have access rights to the entire Sage 100 Contractor
program. In addition, only company administrators can perform the following tasks in Sage 100 Contractor:

  l Create security groups.
  l Grant access rights to security groups for windows and certain items within windows.
  l Grant job-level security to specific users.
  l Display field properties for a dialog box to set security properties for its various elements or to customize

     the window in other ways.
  l Create user names and passwords, and assign user names to security groups in the 7-2-2 User List

     window.
  l Set up and modify the General Ledger.
  l Restrict posting to specific accounting posting periods.

To add a user to the list of Company Administrators:

1. Click Company admins / SQL Logins > Add Company Administrator.
2. From the Select the company to manage list, select your company.
3. From the Select a company administrator list select the user you want to designate as a company

     administrator.
4. Click Create Admin User.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  35
Modifying company administrators

You use the Modify Company Administrators if you need to remove a user's administrator access to a selected
company, or to restore administrator access to a user that has had it before.

To change a user's administrator access for a selected company:

1. Click Company admins / SQL Logins > Modify Company Administrators.
2. On the list of users:

       l Select the checkbox for each user you want to designate as an administrator for this company
       l Clear the checkbox for each user you want to demote to ordinary access to the company.
3. Click [Update Admin Users].

Adding a SQL Server login

When you or another company administrator adds employees as users in Sage 100 Contractor, you authorize
them to use your SQL Server database by:

  l Adding their user names to your SQL Server instance.
  l Selecting a method to authenticate their user names and passwords.
  l Defining their passwords (depending on the authentication method you select).
  l Optionally, assigning a system administrator role to a user.
Although you can use SQL Server Management Studio to add SQL Server users, Database Administration for
Sage 100 Contractor provides a much simpler way to set up SQL Server login credentials.

To add a SQL Server login for a user:

1. Click Company admins / SQL Logins > Add SQL Server Login.
2. From the Authentication list, select an authentication method.

       l If you select Windows Authentication, in the User name box, type the Windows user name for this user.

            Note: You must enter a user name that is valid for the Windows domain or workgroup that hosts the SQL
            Server instance.

           When the user signs into the company with their Windows user name, Sage 100 Contractor authenticates
           the user name and password they entered when signing into Windows.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  36
       l If you select SQL Server Authentication, type the SQL Server login and password to use to authenticate this
           user when they sign into the company.

3. If this user should also be a SQL Server administrator, select the Add as a member of 'sysadmin' server
     role checkbox.

4. Click [Create SQL Login].

After adding a SQL Server login

  l In Sage 100 Contractor, add the user to the 7-2-2 User List.
  l If the user requires administrative privileges in Sage 100 Contractor, add them as a company

     administrator using the Database Administration tool.

About resetting lost passwords

To provide a secure environment, Sage 100 Contractor SQL does not retain users' passwords. Therefore, if a
user forgets their password, you will not be able to see it in the 7-2-2 User List.
If your Sage 100 Contractor system uses Integrated Security, the user simply enters their Windows ID and
password when logging into the Sage 100 Contractor company.
If you set up the user with SQL Server authentication, however, you must reset their password in the 7-2-2
User List by typing a new password to replace the old one, and then saving it.

Deleting a SQL Server login

If an employee leaves your company, use the Delete SQL Server Logins tab to remove all access to the SQL
Server instance for that employee.

     Important! After you delete a user's SQL Server login, they can no longer sign in to any Sage 100
      Contractorcompany.

If you need to remove a user's access rights to one company, while maintaining their access to other
companies, remove the user from the 7-2-2 User List for the company in Sage 100 Contractor.

To delete a SQL Server login:

1. Click Company admins / SQL Logins > Delete SQL Server Logins.
2. On the list of users:

       l Select the checkbox for each user you want to delete from the SQL Server database.
       l Clear the checkbox for users whose access to the SQL Server database you want to maintain.
3. Click [Delete SQL Login].

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  37
Modifying SQL Server administrators

If you do not designate a user as 'sysadmin' when you add their SQL Server login, you can so using the Modify
SQL Server Administrators tab.
You also use the Modify SQL Server Administrators tab to remove the 'sysadmin' role for a user.

To change a user's 'sysadmin' role:

1. Click Company admins / SQL Logins > Modify SQL Server Administrators.
2. On the list of users:

       l Select the checkbox for each user you want to designate as an administrator for the SQL Server
          database.

       l Clear the checkbox for each user you want to demote to ordinary access to the database.
3. Click [Update sysadmins].

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  38
Chapter 8: Migrating Your Data from
Version 19.8

You use the Database Administration tool to migrate your version 19.8 data (including all company data in
folders and subfolders of ...\MB7\[CompanyName]) to the current version. The migration process automatically
creates a new SQL Server database and stores your migrated SQL data in a new location.

About migrating your data from version 19.8

You use the Database Administration tool to migrate your version 19.8 data (including all company data in
folders and subfolders of ...\MB7\[CompanyName]) to the current version. The migration process automatically
creates a new SQL Server database and stores your migrated SQL data in a new location.
Your original data remains intact and available in version 19.8.
You can migrate data to version 24.1 only from version 19.8. If your company databases are in an earlier
version of Sage 100 Contractor, you must upgrade them to version 19.8 first.
Migrated files are located in shared folders under C:\Sage100Con\Company\[Company Name]. (Users
navigate to the \Sage100Contractor\[Company Name] on the server.) Subfolders are organized using a similar
folder structure as in earlier versions, and include:

  l Aatrix Forms
  l Attachments
  l Direct Deposit
  l Images
  l Reports

      Note: The Direct Deposit and Reports folders are available as soon as you open the company in Sage
      100 Contractor. The remaining folders are created as needed.

Migrating shared custom reports

If you customized any of the reports that came with version 19.8, you need to migrate them to version 24.1,
also.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  39
      Note: If you created custom reports using third-party applications, you must use the report views to adapt
      them, separately, for Sage 100 Contractor 2022.

Private custom reports

In version 19.8, private reports were stored on individual workstations with each user's Windows application
data, and therefore cannot be migrated along with the shared custom reports.

In version 24.1, when a user logs into Sage 100 Contractor, the server checks their Windows User Data folder
to see if they have any private Sage 100 Contractor. If they do, the program creates a User Data folder on the
server for that user's Windows ID, and copies their reports to this folder.

      Note: The Backup program backs up private reports and other user-specific data for each user.
      However, the Restore program does not restore them. If a user somehow loses their private reports, you
      can retrieve them by navigating to a recent backup file (in the local Backup folder) and extracting the
      user's data folder.

Changes to converted data

During migration, the program may encounter problems in that might prevent it from writing a particular record
to the SQL database.

If the problem is one that the migration program can fix, it changes the record, and then writes the updated
record to the SQL database. For a list of these errors, see "Errors fixed during migration" (page 44).

However, not all errors can be fixed. In these cases, the record is not written to the new database.

The migration log file

The program keeps a log of all changed (fixed) records and records that were not migrated because of an
unresolvable error, unless the record was invalid in version 19.8. Invalid records are neither migrated nor
logged.

      Important! After migration, you should check the log file to see what changes were made to your data
      during conversion, or whether any records were not migrated to the new SQL database.

The _SQL_MIGRATION_LOG.TXT file is located in the source company's main folder (for example,
C:\MB7\Sample Company). A supplemental file, _SQL_MIGRATION_LOG_VERBOSE.TXT, includes more
detailed information about each error found.

After migrating company data and reports

After migrating your data, you will likely need to perform the following additional steps to prepare your
company for use in Sage 100 Contractor:

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  40
  l Add company administrators. There is no longer a generic "supervisor" user as there was in version
     19.8. All users must sign into the company using their personal IDs, and only users designated as
     company administrators have heightened privileges previously associated with the "supervisor" role.
     You can designate one user as a company administrator during migration, but you can add others later.

  l Add SQL logins for new users. If you have new users that did not exist in your version 19.8 company, add
     them as users to the SQL database.

     You must also add them as users and assign security in Sage 100 Contractor.

  l Designate an additional SQL Server administrator. Only a user with a 'sysadmin' role can administer users for
     SQL Server and assign the 'sysadmin' role to another user. Therefore, it is vital at all times that more than one
     user has a 'sysadmin' server role. If the principal system administrator should suddenly fall ill, or leave your
     company, or otherwise be unable to perform their duties, another person with administrative access to the
     SQL Server database must be able to take over that role.

            Note: The person who installs Sage 100 Contractor is automatically assigned a 'sysadmin' role.

  l Migrate scheduled reports and alerts. You must use Sage 100 Contractor to migrate tasks scheduled in
     version 19.8 for individual workstations. When you open the 7-5 Scheduled Reports Manager window or the
     7-6 Alerts Manager window, Sage 100 Contractor checks whether any scheduled reports or alerts exist,
     respectively, for version 19.7. If it finds any, it displays a migration window that you can use to migrate these
     tasks to the current version. For more information, see the help for these windows in the Sage 100 Contractor
     application.

  l Claim Supervisor process maps. If process maps existed for the Supervisor user in version 19.8, Sage 100
     Contractor will attempt to assign them automatically to users that log in to Sage 100 Contractor until the
     process maps are claimed.

Copying default settings from the Supervisor user

Because each user must have a unique SQL Login to identify them to the SQL server, there is no longer a
generic Supervisor user as there was in version 19.8.

Although the migration program does not bring the Supervisor user into the new version of Sage 100
Contractor, you can copy default settings, such as grid views and reporting defaults, from the Supervisor to an
individual user in version 19.8. After you migrate your data, you can select this user as the Company
Administrator in version 24.1.

      Note: Copying the Supervisor settings does not copy security settings or desktop settings to users.

To copy default settings for the Supervisor user:

1. In version 19.8, log in to the Sage 100 Contractor company as the Supervisor.
2. Open the 7-3-2 User List window.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  41
3. If the grid doesn't include a user to whom you want to copy supervisor rights, create the user, and then
     click the Save button.

4. Click the [Copy User Defaults] button, or click Options > Copy User Defaults.
5. In the Copy User Defaults window:

      a. On the Copy defaults from pane, select Supervisor.
      b. On the Copy to pane, select the user to whom you want to assign the default Supervisor settings.

                  Tip: To copy the settings to more than one user, hold down the Control key while you make multiple
                  selections in the Copy to pane.

      c. Click [OK].
      d. In the message box, click [Yes] to continue.

Migrating company data

You use the Database Administration tool to migrate your version 19.8 data (including all company data in
folders and subfolders of ...\MB7\[CompanyName]) to the current version. The migration process automatically
creates a new SQL Server database and stores your migrated SQL data in a new location.

Before migrating

Migration should proceed smoothly in most instances. However, you should perform the following audits in
version 19.8, and then fix any errors, before attempting migration:

  l 1-6 Period and Fiscal Year Management > Audit Books
  l 5-3-7 Payroll Audit
  l 6-6-3 Purchase Order Audit
  l 6-7-4 Subcontract Audit
  l 12-5 Inventory Audit
In addition, to ensure that all records exist and are properly indexed:
  l In the 7-4 Rebuild Indexes window, rebuild indexes.
  l In the 1-8 General Ledger Setup window, verify that all the required accounts exist.
  l In the 6-5 Cost Codes window, make sure that all cost codes are assigned to a cost division.

      Note: If your version 19.8 company data includes serious audit errors, you may need assistance from
      your business partner or consultant to prepare your database for migration.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  42
To migrate your data from version 19.8:

1. Click Migrate from Version 19.8 > Migrate Company Data.
2. On the Migrate Company Data tab:

      a. Click [Browse], and then navigate to and select the folder where your version19.8 company data is
           stored.

      b. Select a company administrator from the list of users that were set up for your company in version19.8.

      c. Specify a maintenance schedule, including the time and the number of backups to keep.
      d. Click [Migrate Company].

3. After the migration process has finished, check the SQL Migration Log file, where any errors or changes to
     your data are recorded.

     The _SQL_MIGRATION_LOG.TXT file is located in the source company's main folder (for example,
     C:\MB7\Sample Company). A supplemental file, _SQL_MIGRATION_LOG_VERBOSE.TXT, includes more
     detailed information about each error found.

Converted files are located in shared folders under C:\Sage100Con\Company\[Company Name], organized
using a folder structure similar to earlier versions.

After migrating your data

  l Add company administrators. There is no longer a generic "supervisor" user as there was in version
     19.8. All users must sign into the company using their personal IDs, and only users designated as
     company administrators have heightened privileges previously associated with the "supervisor" role.
     You can designate one user as a company administrator during migration, but you can add others
     later.

  l Add SQL logins for new users. If you have new users that did not exist in your version 19.8 company, add
     them as users to the SQL database.

     You must also add them as users and assign security in Sage 100 Contractor.

  l Designate an additional SQL Server administrator. Only a user with a 'sysadmin' role can administer users
     for SQL Server and assign the 'sysadmin' role to another user. Therefore, it is vital at all times that more than
     one user has a 'sysadmin' server role. If the principal system administrator should suddenly fall ill, or leave
     your company, or otherwise be unable to perform their duties, another person with administrative access to
     the SQL Server database must be able to take over that role.

            Note: The person who installs Sage 100 Contractor is automatically assigned a 'sysadmin' role.

  l Migrate scheduled reports and alerts. You must use Sage 100 Contractor to migrate tasks scheduled in
     version 19.8 for individual workstations. When you open the 7-5 Scheduled Reports Manager window or the
     7-6 Alerts Manager window, Sage 100 Contractor checks whether any scheduled reports or alerts exist,

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1                                         43
     respectively, for version 19.7. If it finds any, it displays a migration window that you can use to migrate these
     tasks to the current version. For more information, see the help for these windows in the Sage 100
     Contractor application.

  l Claim Supervisor process maps. If process maps existed for the Supervisor user in version 19.8, Sage 100
     Contractor will attempt to assign them automatically to users that log in to Sage 100 Contractor until the
     process maps are claimed.

Errors fixed during migration

During the migration process, the program may encounter problems in that might prevent writing a particular
record to the SQL database.

If the problem is one that the migration program can fix, it changes the record, and then writes the updated
record to the SQL database. For example:

  l If a record contains a reference to a record that does not exist, the program creates the missing
     referenced record using the name or description "Unknown [record]," with any required fields, and the
     record is set to Inactive.

  l If a record contains a defined error that has a prescribed solution, the program applies the solution as it
     creates the record in the SQL database.

The migration program applies solutions, as described, when it encounters these specific errors:

  l Canadian-specific fields that include values in a United States company. These fields are cleared.
  l Line tables that include Quantity and Price or Cost fields, where the Price/Cost is negative. The

     Price/Cost is written as a positive value and the Quantity is made negative.*
  l Parts with negative values for Average Cost, Default Cost or Billing Amount. These fields are cleared.*
  l Bid Items that are Item# 0 with no value for Item Type. The Item Type is assigned 1-Base Bid.
  l Job Costs with no value for Billing Status. The Billing Status is assigned 2-Not Billable.
  l Job Costs with no value (or an otherwise invalid value) for Cost Type. The Cost Type is assigned 5-

     Other.
  l Payroll Calculations with negative value for Benefit. The Benefit is changed to 0.
  l Purchase Order Lines with AR, AP or SR for the Account. The Account and Subaccount fields are

     cleared.
  l Clients with no value for Part Billing Basis. The Billing Basis is assigned 3 (Billing Amount).
  l Clients with no value for Status. The Status is assigned to a new Status record, which is created using

     the highest available number and description of Unknown Status.*
  l Tasks with no value for Task Type. The Task Type is assigned to a new Task Type record, which is

     created using the highest available number and description of Unknown Type.*

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1                                         44
  l Service Work Orders/Invoices with no value for Priority (in either the header or Dispatch grid). The
     Priority is assigned to the default value (either 3 or the customer's setting from F7).

  l T&M Billing Setup with no value for Income Account. The Income Account is assigned to the default
     Income Account from the Job record. (If there is no default value on the Job, the SQL record is not
     created, and the error is reported in the migration log.)

  l Parts with any value other than 0 or 1 for Required from Inventory. The field is assigned 0 (not selected).
  l Dispatch Board Column Setup with no value for Record Type. The Record Type is assigned E

     (Employee).
  l Service Areas with no value for Dispatch Color. The Dispatch Color is assigned Black.
  l Any Yes/No field with any value other than Y, N, or blank. These fields are cleared.
*These changes are reported in the migration log.

Migrating custom reports and report forms

If you customized any of the reports that came with version 19.8, you need to migrate them to version 24.1,
also.

      Note: If you created custom reports using third-party applications, you must use the report views to adapt
      them, separately, for Sage 100 Contractor 2022.

To migrate your shared custom reports and forms from version 19.8:

1. Click Migrate from Version 19.8 > Migrate Custom Reports.
2. On the Migrate Custom Reports tab, click [Browse], and then browse to the MB7 folder where your version

     19.8 data is stored.
3. Click the MB7 folder, and then:

      a. If you have custom reports, select the Custom Reports folder.
      b. Click [Migrate Reports].
      c. Select the Report Forms folder.
      d. Click [Migrate Reports].

      In version 19.8, private reports were stored on individual workstations with each user's Windows application
      data, and therefore cannot be migrated along with the shared custom reports.

      In version 24.1, when a user logs into Sage 100 Contractor, the server checks their Windows User Data folder
      to see if they have any private Sage 100 Contractor. If they do, the program creates a User Data folder on the
      server for that user's Windows ID, and copies their reports to this folder.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  45
Chapter 9: Server Management Tools

The tools in Server Management in Database Administration enable you to control the SQL Server instances
you use with Sage 100 Contractor easily and efficiently.
You use the Server Management tools to create a new SQL Server instance, to move your Sage 100
Contractor companies to a different instance or a different drive on your computer, to remove a SQL Server
instance, and to enable communication with Sage mobile apps.

About managing your server

The tools in Server Management in Database Administration enable you to control the SQL Server instances
you use with Sage 100 Contractor easily and efficiently.

Creating a SQL Server instance

If you need to create a new SQL Server instance (for example, if you want to move your Sage 100 Contractor
archive companies to a different drive on your computer), use this tool to create a new SQL Server instance.
When you use this tool to create a new instance, the program configures the instance using the settings that
Sage 100 Contractor requires.

Moving Sage 100 Contractor companies to a different SQL Server instance

Use this procedure if you want to move your companies to a different SQL Server instance on the same
computer. (For example, you might want to keep your current and archive companies in separate instances.)

Removing a SQL Server instance

Use this tool to to remove a SQL Server instance (for example, if you have moved your Sage 100 Contractor
companies to a different drive on your computer, and now need to delete the original instance, or if you create
an instance in error).

Moving data to a new drive

Use this procedure if you want to move all your Sage 100 Contractor data to a different drive on the same
computer. (For example, you would do this if you want to host your data on a faster, bigger drive than the one
you are currently using.)

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  46
Enabling mobile apps

Use the tools on this tab to enable Sage 100 Contractor to communicate securely with Sage mobile apps, such
as the Time app.

Creating a new SQL Server instance

If you need to create a new SQL Server instance (for example, if you want to move your Sage 100 Contractor
archive companies to a different drive on your computer), use this tool to create a new SQL Server instance.
When you use this tool to create a new instance, the program configures the instance using the settings that
Sage 100 Contractor requires.

      Important! The version of SQL Server on the new instance should be the same or a later version than
      that used for your Sage 100 Contractor data.

To create a new SQL Server instance:

1. Start Database Administration and connect to your current SQL Server instance.
2. Click Server Management > Create SQL Server instance.
3. Fill out the fields on the Create SQL Server Instance tab:

      a. Enter a name for the new SQL Server instance. You can use up to 16 characters for the new instance name.

                  Note: The name cannot start with a space or a $ sign.

      b. Enter the setup file for the SQL Server installation. Browse to the location where you stored the SQL Server
            installation files, and then select the executable file.
            If you installed SQL Server Express when you installed Sage 100 Contractor, this will likely be the Sage 100
            Contractor download folder--for example, C:\Sage100Con\Downloads\SQLEXPRADV_v64_ENU.EXE.

      c. Select the checkboxes for the access and communication options you want to enable for the new instance.
            If you are allowing access to the new instance only for approved applications:

          i. Click [Edit Approvals].
         ii. In the Enable Access from Other Applications window, select the checkboxes for the applications

             that are allowed to connect to the instance.
        iii. Click [OK].
4. Click [Create instance].

After creating an instance

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  47
  l The next time you open Database Administration, the Connect window includes the new instance.
  l You can move company data to the new instance. Follow the instructions in "Moving Sage 100

     Contractor companies to a new SQL Server instance" (page 48).

Moving Sage 100 Contractor companies to a new SQL Server
instance

Use this procedure if you want to move your companies to a different SQL Server instance on the same
computer. (For example, you might want to keep your current and archive companies in separate instances.)

      Note: When you move a company to a new instance, any scheduled maintenance tasks are also moved
      to the new instance, and removed from the old instance.

Before you start

Make sure that the SQL Server instance to which you plan to move your data is compatible with your
company data. You cannot move your company to an instance created with an earlier version of Microsoft
SQL Server.

To create a new SQL Server instance:

1. Start Database Administration and connect to your current SQL Server instance.
2. Click Server Management > Move Companies to Other Instance.
3. Fill out the fields on the Move Companies to Other Instance tab:

      a. In the Company list, select the checkbox for the company that you want to move.
      b. Select the destination SQL Server instance. From the drop-down list, select the instance where you want to

            move the company.
      c. Select the option to set up nightly maintenance and backup tasks for the company in the new location, and

            then:
              i. From the Select the time for nightly maintenance list, select the time to perform maintenance for this
                  company.
             ii. From the Select the number of backups to keep list, select the period of time to maintain backup files
                  for this company.

4. Click [Move company].

After moving a company to a different instance

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  48
This process does not upgrade your company data. Therefore, if you are moving archived companies created
with an earlier version of Sage 100 Contractor, you will need to upgrade the company data on the new
instance after you move the company.

Removing a SQL Server instance

Use this tool to to remove a SQL Server instance (for example, if you have moved your Sage 100 Contractor
companies to a different drive on your computer, and now need to delete the original instance, or if you create
an instance in error).

Before you start

  l On your computer, locate the Microsoft SQL Server setup file with which you created the instance you now
     want to remove. If you installed SQL Server Express when you installed Sage 100 Contractor, this will likely
     be the Sage 100 Contractor download folder--for example, C:\Sage100Con\Downloads\SQLEXPRADV_
     v64_ENU.EXE.
     If you created the instance with an earlier version of Microsoft SQL Server, and overwrote the original setup
     file with a later version, you may need to download the earlier version again. (We recommend that if you do
     so, you download it to a distinct folder to avoid overwriting the existing setup file.)

  l Remove any companies that are connected to the SQL Server instance. See Deleting a Company for
     instructions.

To remove a SQL Server instance:

1. Start Database Administration, and connect to your current SQL Server instance.
2. Click Server Management > Remove SQL Server instance.
3. Fill out the fields on the Create SQL Server instance tab:

      a. Select the SQL Server instance to remove. Select the instance from the list.
      b. Enter the Setup file for the SQL Server installation. Browse to the location where you stored the SQL Server

            installation files, and then select the executable file.
4. Click [Remove instance].

Moving your data to a new drive

Use this procedure if you want to move all your Sage 100 Contractor data to a different drive on the same
computer. (For example, you would do this if you want to host your data on a faster, bigger drive than the one
you are currently using.)

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  49
      Important! Moving data to a new drive moves all Sage 100 Contractor data. Only one drive on a server
      can contain Sage 100 Contractor data, and once you move your data, Sage 100 Contractor no longer
      uses or references the old drive.

Before you start

  l Make sure no other users are logged into the system.

To move your data to a new drive:

1. Start Database Administration and connect to your current SQL Server instance.
2. Click Server Management > Move Data to New Drive.

     The Move Data to New Drive tab displays the letter representing the current drive.
3. Fill out the fields on the Move Data to New Drive tab:

      a. Click [Select New Data Drive].
      b. In the Select Data Location window, select (highlight) the drive where you want to move your data from the

            list. The drive must be formatted as NTFS and have at least three times the available space as the data you
            want to move.
            You cannot select a removable drive.

             Note: The Select Data Location window displays the local, fixed drives on your computer and shows
             information, such as the drive name and the amount of available space, for each one.

      c. Make a note of the drive you selected so that you can update your maintenance and backup schedules.
      d. Click [OK].

            You are returned to the Move Data to New Drive tab.
4. Click [Move Data].

     If any users are connected to the database, you receive a message. You must terminate their connections
     before you can continue.
     If you change your mind about moving your data (for example, if you do not want to terminate user
     connections without notice), click [Cancel], and then click [OK] at the message asking you to confirm that you
     do not want to move your data.
     If the program cannot relocate your data, you receive an error message, and the program returns your data its
     state before you attempted to move it.

After moving a company to a different instance

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1                                          50
  l Update the location for your backup files. (Click Tune Up / Back Up / Restore > Back Up Companies,
     and then browse to the new backup location.)

Enabling Sage Mobile Apps

Use the tools on this tab to enable Sage 100 Contractor to communicate securely with Sage mobile apps, such
as the Time app.
When you enable access to mobile apps, Database Administration performs a several tasks to ensure that
Sage 100 Contractor can connect to your cloud server. For example, it checks that IIS and Windows Activation
Service are installed and configured properly, and it opens required communication ports on your server.

To enable Sage Mobile apps:

1. Click [Request Invitation] to ask Sage to activate your Azure Active Directory account.

            Note: Sage 100 Contractor includes an Azure Active Directory account.

     Sage will email a confirmation and further instructions to the email account associated with your Sage ID.
2. After you receive the confirmation email and follow the instructions to activate your AAD account, click [Install

     Proxy] to install the Azure Active Directory Account Proxy (AADAP).

            Note: Azure Active Directory Application Proxy is software that enables remote users to connect
            securely to your on-premises Sage 100 Contractor server.

     When the installation process is complete, the button changes to [Uninstall Proxy]. Do not click it unless you
     need to uninstall and then reinstall the AADAP.
You should only have to performs these steps once, unless you change the Sage 100 Contractor server.

After enabling Sage Mobile Apps

In Sage 100 Contractor, use the 7-2-3 Mobile Users window to set up mobile users and send them an email
inviting them to use Sage mobile apps.
You also use the Sage 100 Contractor application to review, approve, and post entries sent by Sage Mobile
users.
If you change the Sage 100 Contractor server, you will need to uninstall, and then reinstall the AADAP. In this
case, click [Uninstall Proxy].

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  51
About Microsoft Azure Active Directory Application Proxy (AADAP)

Azure Active Directory Application Proxy is software that enables remote users to connect securely to your on-
premises Sage 100 Contractor server.
For example, when you invite users to the Sage Time app, the email you send them includes a connection to
your server (your company URL) as well as a unique code that identifies them as a user of your Sage 100
Contractor system. The Application Proxy uses that information to connect the user safely to your Sage 100
Contractor "back office."

Enabling Sage Mobile Apps

Use the tools on this tab to enable Sage 100 Contractor to communicate securely with Sage mobile apps, such
as the Time app.
When you enable access to mobile apps, Database Administration performs a several tasks to ensure that
Sage 100 Contractor can connect to your cloud server. For example, it checks that IIS and Windows Activation
Service are installed and configured properly, and it opens required communication ports on your server.

To enable Sage Mobile apps:

1. Click [Request Invitation] to ask Sage to activate your Azure Active Directory account.

            Note: Sage 100 Contractor includes an Azure Active Directory account.

     Sage will email a confirmation and further instructions to the email account associated with your Sage ID.
2. After you receive the confirmation email and follow the instructions to activate your AAD account, click [Install

     Proxy] to install the Azure Active Directory Account Proxy (AADAP).

            Note: Azure Active Directory Application Proxy is software that enables remote users to connect
            securely to your on-premises Sage 100 Contractor server.

     When the installation process is complete, the button changes to [Uninstall Proxy]. Do not click it unless you
     need to uninstall and then reinstall the AADAP.
You should only have to performs these steps once, unless you change the Sage 100 Contractor server.

After enabling Sage Mobile Apps

In Sage 100 Contractor, use the 7-2-3 Mobile Users window to set up mobile users and send them an email
inviting them to use Sage mobile apps.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  52
You also use the Sage 100 Contractor application to review, approve, and post entries sent by Sage Mobile
users.
If you change the Sage 100 Contractor server, you will need to uninstall, and then reinstall the AADAP. In this
case, click [Uninstall Proxy].

Troubleshooting Sage Mobile Apps

If you encounter connectivity problems with Sage Mobile apps, you may need to contact Customer Support to
resolve them. The support analyst will walk you through a series of tests to rule out problems.
The buttons in the Diagnostic Tools section of the Enable Sage Mobile Apps tab represent these tests, as
follows:

  l Restart AADAP. When instructed by Sage Support during troubleshooting, you click this button to restart the
     connector service.

  l Test AADAP. You click this button to verify that the connector service is working properly and can
     communicate with the server API.

  l Stop Server API. You click this button to block communication from mobile apps.
  l Start Server API. When the server API is stopped, you click this button to restore communication from mobile

     apps.
  l Test Server API. You click this button to test the server's mobile apps API.
  l Open Log File. You click this button to display a log that a support analyst can use to check the results of the

     tests or to see if any other errors were logged (such as configuration errors) and find out what the errors were.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  53
Chapter 10: The Toolbox and
Troubleshooting

About using the Toolbox for troubleshooting

Database Administration for Sage 100 Contractor provides a variety of troubleshooting tools to help you track
changes in your database, and to diagnose and fix certain types of problems.

The following sections describe these tools in more detail.

About Dashboard

The Dashboard provides visual feedback showing whether your Sage 100 Contractor system is configured
using the recommended settings and is operating satisfactorily.

      Note: The Dashboard was not designed as a sophisticated performance analyzer, but to provide a quick
      "health check" on your system.

Status indicators

Each of the following factors contributes to the efficient operation of your system:
  l Computer's Power Plan. For more information, see "About Computer's Power Plan" (page 55).
  l Database Usage. For more information, see "About Database Usage" (page 56).
  l SQL Memory Allocation. For more information, see "About SQL Memory Allocation" (page 56).
  l Disk Performance. For more information, see "About Disk Performance" (page 57).
  l Network Configuration. For more information, see "About Network Configuration" (page 57).

The Dashboard's "traffic lights" provide visual cues about the status of each factor:

Status                                 Condition of your system

        Your system is using the recommended settings and is operating as
        expected.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1                54
Status                                 Condition of your system
        There is a potential problem that you should investigate.

        There is a serious problem that needs your attention.

        The program could not perform this test.

When viewing the Dashboard, you can:

  l Obtain additional information about a particular condition by clicking the adjacent view details link.
  l Update the entire dashboard with the latest conditions--particularly after adjusting these settings--by

     clicking [Refresh].

About Computer's Power Plan

This Dashboard indicator shows whether your computer's power plan is supporting or impairing users'
connections to the server.

The server must be available at all times so that users at workstations can connect to it. If the computer's
power plan allows the computer to sleep or hibernate, or turns off the hard disks during periods of inactivity,
performance will be degraded.

Status                                           Condition of your system

        The computer's power plan uses Sage's recommendations. The settings do not allow the
        computer to sleep, hibernate, or turns off hard disks during inactive periods.

        We could not determine your computer's power plan settings. You should ensure that the
        power plan does not permit the computer to sleep or hibernate, or turns off hard disks during
        inactive periods.
        Click the adjacent view details link on the Dashboard for help in resolving your computer's
        power settings.

        The power plan does not meet our recommendations. Performance will be impaired unless
        you adjust the settings.
        Click the adjacent view details link on the Dashboard for help in resolving your computer's
        power settings.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1                                  55
About Database Usage

This Dashboard indicator helps you to determine whether there is sufficient disk space for databases to
expand. It warns you if existing storage is nearing the maximum capacity of the disk.

Status                                           Condition of your system

        Overall used disk capacity is less than 85% and (if you are running SQL Express) the
        capacity used for every database is less than 70% .

        Overall used disk capacity is 85 to 90%, or (if you are running SQL Express) the capacity
        used by at least one database is between 70% and 80%.
        Click the adjacent view details link on the Dashboard for more information about your
        computer's settings.

        Overall used disk capacity is more than 90%, or (if you are running SQL Express) at least
        one database is using more than 80% of overall capacity.
        Click the adjacent view details link on the Dashboard for more information about your
        computer's settings.

About SQL Memory Allocation

This Dashboard indicator shows whether the memory allocated to SQL Server is sufficient to handle the load
efficiently. The status light reflects the lowest status determined for the following measurements:

  l The amount of the server's memory that is dedicated to SQL Server.

  l The average number of seconds the allocated memory can hold SQL data before it needs to be dumped in
     order to handle new processes. Called "page life expectancy" (PLE), this value is measured for each
     database during nightly maintenance or a manual tune-up.

For example, if either the memory allocation or the PLE of any database is red, the Dashboard status light is
red.

      Note: A gray status and "Insufficient data" is displayed if there are fewer than 20 PLE records in the
      database.

Status                                           Condition of your system

        The computer's memory allocation is at least 4 GB (or 25% of total memory, if less than 4
        GB), and the PLE for all databases is at least 36,000 seconds.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1                          56
Status                                           Condition of your system

        The computer's memory allocation is between 1 GB and 4 GB (and less than 25% of total
        memory), or the PLE for any database is between 3,600 and 36,000.
        Click the adjacent view details link on the Dashboard for more information about your
        computer's settings.

        The computer's memory allocation is below 1 GB, or the PLE for any database is below
        3,600. Performance will be impaired unless you adjust the settings.
        Click the adjacent view details link on the Dashboard for more information about your
        computer's settings.

About Disk Performance

This Dashboard indicator shows whether the average speed with which the computer writes to and reads from
the data drive is adequate.

      Important! Operating system-based disk caching is disabled for this test, so the actual performance may
      be much greater than reported here.

Status                                           Condition of your system
        The computer reads and writes at a minimum rate of 100 MBps.

        The computer reads or writes at a rate between 50 MBps and 100 MBps.
        Click the adjacent view details link on the Dashboard for more information about your
        computer's settings.

        The computer reads or writes at a rate below 50 MBps.
        Click the adjacent view details link on the Dashboard for more information about your
        computer's settings.

About Network Configuration

This indicator shows whether the network adapters used on the server and on each computer that connects to
a Sage 100 Contractor database matches the recommended speed of 1 gigabit per second.

Status                                            Condition of your system
        1-gigabit connections are available for all reporting computers.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1                57
Status                                            Condition of your system

        100-megabit connections are used by at least one reporting computer.
        Click the adjacent view details link on the Dashboard for more information about your
        computer's settings.

        10-megabit connections are used by at least one reporting computer.
        Click the adjacent view details link on the Dashboard for more information about your
        computer's settings.

Server Tools

      Important! These sophisticated tools were designed to help Customer Support personnel efficiently
      resolve certain system problems that, although rare, would be time-consuming to fix otherwise.

      Note: Although running these tools causes no harm to your system, there is no advantage to doing so
      unless you have one of the problems that the tools are designed to fix.

  l Start Microsoft SQL Server Profiler. You use the SQL Server Profiler to monitor the effect of changes to your
     database on your SQL Server instance.

       Note: To take advantage of this feature, you should be familiar with SQL Server Profiler concepts and
       tasks.

  l Remove orphaned file shares. Every company has a folder on the server that provides access from
     workstations to external files, such as file attachments, that are associated with the company.

     If a file share is not removed automatically when you delete a company--for example, if you deleted a
     database using SQL Server Management Studio and did not remove the corresponding file share manually--
     you could remove it using this tool. (Note that we strongly recommend that you only ever use Database
     Administration to delete companies.)

  l Remove orphaned nightly maintenance tasks. If the scheduled maintenance task for a company is not
     removed automatically from Windows Task Scheduler when you delete the company, this tool can remove
     the task.

       Note: We strongly recommend that you only ever use Sage 100 Contractor Database Administrationto
       delete companies!

  l Reapply file permissions. Sage 100 Contractor maintains a system for managing access to data, and assigns
     security settings to each folder when the folder is created. Changing these security settings can have a
     detrimental effect on the normal operation of the software. This function reassigns the original security

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1                                    58
     settings to each
     folder in the Sage 100 Contractor system.
  l Reapply firewall rules. Selecting the Enable other machines to connect to this SQL server instance, in
     Advanced Settings, creates the firewall rules required for workstations to connect to the server.
     However, if the rules are later deleted in the firewall software, this tool reinstates them. For example,
     Windows 10 might have altered the firewall rules during an upgrade from an earlier version of Windows, or
     another user may have changed the firewall rules without realizing the implications for Sage 100 Contractor.
  l Move default `tempdb' to Sage 100 Contractor's preferred location. SQL Server uses the tempdb directory to
     hold temporary objects required for processing, and is recreated each time you start SQL Server.
     The first time you run Sage 100 Contractor Database Administration, it moves the tempdb location to the
     \Sage100Con\Company directory. This is the preferred location because:

        l The program sets the directory permissions correctly.
        l You can select a drive that has sufficient space and performance characteristics during setup.

       Important! You cannot delete this directory while the tempdb MDF and LDF files are stored here. Do not
       attempt to stop the SQL Server service, and then delete the directory. You will not be able to restart the
       SQL Server service because the tempdb location will be invalid.

  l Move default `tempdb' to SQL Server's default location. When you create the SQL Server instance, the
     tempdb is created automatically in the SQL Server default location (typically C:\Program Files\Microsoft SQL
     Server\MSSQL12.SAGE100CON\MSSQL\DATA). However, this location is not optimal because:
        l The C:\ drive may have limited space, and the tempdb is likely to grow, which can cause operational
           problems. For example, if a query requires more tempdb space than can be allocated, the query will
           fail.
        l The C:\ drive may be slow.
        l The permissions to the C:\drive may be very restricted.
     Although it is not optimal, you can relocate the tempdb location if you need to delete the directory at the Sage
     100 Contractor preferred location.

Company Tools

      Important! Company Tools generate reports designed to help expert users, such as Customer Support
      personnel and business partners, identify changes that third-party applications have made to your
      company data or to the database schema.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1                                        59
Displaying modifications and alterations made by other programs

You can generate one of the following reports at a time:
  l Display all data modifications made by other programs. This tool queries all audit (or history) tables and
     reports on changes made by any third-party applications.

            Note: The data contained in the report is time-sensitive, and depends on the history retention policy
            specified for your company in Advanced Company Settings. (The default period is 90 days.)

  l Display all database schema alterations made by other programs. This tool reports all changes to the schema
     made by third-party applications. The database schema functions as the blueprint for your database, and
     determines the type and format of information you can enter into it. Unauthorized schema changes can cause
     unpredictable behavior, and problems during updates or upgrades.

The report contents are presented in a grid in a separate window. Although you cannot edit the data in the grid,
you can use the column headings to sort the items that appear in it, and (in the data modifications report) you
can also use filters to restrict the selection of data modifications.

Displaying data modifications

The data modifications tool provides three filters (located at the top of the results window) that you can use to
restrict the results that appear in the grid. You can filter records by:

  l Tables. You can select All Tables or a particular table from the list.
  l Users. You can select All Users or a particular user.
  l Applications. You can select All Applications or a particular application.
The resulting report provides information about these types of data changes for the selected company:
  l Insertions
  l Deletions
  l Modifications

Drilling down to view details about a change
To view details about a specific change, you click the Row# cell, or select the row, and then press [Enter].
The details window displays all the fields for the selected record, and shows the value of each field before and
after the change.

Displaying schema changes

The schema should not be modified, except by Sage.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  60
If certain types of problems arising during a software update or an upgrade, or if you are suddenly unable to
save records, Customer Support may ask you to run this tool to rule out possible schema changes or to identify
the third party responsible for the changes.

Rebuilding field definitions for the schema

If your database is not synchronized with your program version, you will receive a SQL error message to that
effect. This could occur, for example, if a database upgrade did not finish properly.

In this case, Customer Support will ask you to run Rebuild field definitions for the database schema to fix the
error.

Checking database integrity

The Check the logical and physical integrity of the database option runs the DBCC CHECKDB command, a
SQL Server command. Sage 100 Contractor runs this command routinely, as part of nightly maintenance, but
you could also run it if you receive a message indicating that there is a problem, or a potential problem, with
database integrity. For example, if you receive a message saying that nightly maintenance could not perform a
data integrity check or a more serious error message about corruption in your database.

If Sage 100 Contractor, finds no data corruption when you run this command, it removes the error condition
flag that triggered the message, and you have nothing more to do.

However, if it does find data corruption, you need to contact Customer Support to help you resolve the issue.

Restoring orphaned SQL users

Normally, you do not use this option unless Customer Support recommends it. It is used to repair certain
unusual conditions.

Fixing file paths to attachments after moving data

If you move your data to a new server, the UNC paths to attachment files located outside of the company file
structure will be incorrect. The Toolbox provides a utility to fix the paths to attachments after you move data to
a new server.

When you select the Assign new server name in file paths for linked file attachments option, two boxes
become available:

  l Old server name, from which you select the name of the old server.

     If no servers are listed here, the database has no record of any linked attachments outside the company file
     structure.

  l New server name, in which you type the name of the new server.

After you enter the old and new server names, click [Update File Paths].

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  61
Copying User Files

You use the Copy User Files tab to copy one user's process maps, private custom reports and private custom
forms to another user.

      Note: Because process maps, custom reports and custom forms are located in each user's private User
      Data folder and not in a database, you cannot use the 7-2-2 User List in Sage 100 Contractor to copy a
      user's process maps or private custom reports and forms to another user.

To copy files from one user to another:

1. In Database Administration, click Toolbox > Copy User Files.
2. In the Select user to copy file from box, select the user whose files you want to copy.
3. In the Select type of files to copy box, select one of the following types of files:

       l Private custom reports
       l Private report forms
       l Process maps
     On the lower left side of the tab, a checklist appears, showing all the external files for the selected user.
     Another list shows all the Sage 100 Contractor users that have a personal User Data folder.
4. In the Select files to copy box, select specific files to copy to other users.
5. In the Copy files to selected users box, select the users who need the copied files.

       Tip: To select all the displayed files, click the first file in the list, press Shift+End, and then press the
       Spacebar.

6. Click [Copy Files].

       Note: If a file in the target folder has the same name as a file you are copying, you must confirm whether to
       overwrite the existing file or skip it.

Support Script

You use this utility to run scripts that Sage Customer Support provides to repair your data.

Before you start

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  62
  l When you receive a support script file from Sage, download it to the \Sage100Con\SupportScripts folder on
     your server.
     If the SupportScripts folder doesn't exist in the Sage100Con folder, create it manually.

  l Make sure that all other users are logged out of the company.

To run a support script:

1. In Database Administration, click Toolbox> Support Script.
2. On the Support Script tab:

      a. Select the company from the list box.
      b. Click the [Browse] button, select the SQL script file you saved earlier, and then click [Open].

            The program displays the support ticket number, Knowledgebase article ID, and a description of the work
            that the script will perform.
      c. Click [Run Script].

             Note: If any users are still logged into the company, you receive a message showing who the users are.
             You cannot continue running the script until these users have logged out.

            If the script stops running for any reason, the program restores your data to its state before your tried to run
            the script, and it displays a message explaining why the script did not finish running.

Warning Messages

Database Capacity Warning Message

If your company data is approaching the maximum capacity of the database, Sage 100 Contractor users see a
critical warning advising them to contact their company administrator.
To ensure that you do not run out of space in the database, we recommend that you take one or more of the
following actions if you receive this message:

  l Archive some of your data to another database.
  l In Sage 100 Contractor, remove jobs (using the 3-5 Jobs window), purchase orders (using the 6-6-1

     Purchase Orders window), and/or service invoices (using the 11-2 Work
     Orders/Invoices/Creditswindow).
  l Purchase an edition of Microsoft SQL Server other than Microsoft SQL Express.
  l Purge History tables or reduce the period of time to keep history tables (only if necessary!).

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  63
No Backup Warning Message

If your company files have not been backed up as scheduled in Database Administration, Sage 100 Contractor
users see a warning advising them to contact their company administrator.

Depending on when the files were last backed up successfully, the message conveys the degree of urgency
for the administrator to respond to the problem:

  l A warning appears if the scheduled backup failed to run the previous night.
  l A critical warning appears if the scheduled backup has not run for a number of days.
  l A critical warning also appears if the scheduled backup has never run.

      Important! If you are a Sage 100 Contractor user and you see this message, inform your company
      administrator immediately. Be sure to note the type of warning, including the information about the last
      successful backup.

If you are the company administrator, you should:

  l Immediately back up your company files, manually, using the Back Up Companies utility in Database
     Administration.

     Back up manually each day until you resolve the problem that is preventing the scheduled backup procedure.

  l In Database Administration, check whether a scheduled maintenance task exists for the company on the
     Modify Maintenance Schedules tab.

     You can check the status of the nightly maintenance and backup task by opening the _
     SADMBLastResultLog.txt file in the folder where you store your nightly backups. This log file shows any
     errors encountered during the last attempted maintenance.

     If no maintenance task exists for the company, use the Create Maintenance Schedules tab to create one.

     If a task does exist, you may be able to resolve the problem either by modifying the task (using Modify
     Maintenance Schedules), or by removing it (using Remove Maintenance Schedules), and then creating a new
     one.

  l Check whether another server event occurs at the same time as the maintenance is scheduled to run, which
     could interfere with the maintenance process.

     If another server event is scheduled at the same time, try changing the time of one or the other task, so they
     do not conflict.

If you are unable to resolve the problem using these methods, contact support for further assistance.

Depending on your Sage service plan, you may be able to contact the Sage Customer Support Call Center to
work with one of our highly trained customer support professionals. The Knowledgebase article How do I get

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  64
technical support for Sage 100 Contractor? provides contact information and hours of operation, and it can
help you to determine which service works best for you.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1                             65
Chapter 11: Advanced Settings

Using Advanced Company Settings to maintain database
history

You use the options on the Advanced Company Settings tab to specify how long to keep history about
database changes for each Sage 100 Contractor company you manage. Details older than the retention period
you specify are removed during nightly maintenance.
You can remove all database history for a selected company by clicking the [Purge History Tables] button.

      Caution! Purging history tables and reducing the retention time for database history affects the
      information available in the 7-7 User Activity Report and in the individual record histories in Sage 100
      Contractor.

To set a retention period for database history:

1. Click Advanced Settings > Advanced Company Settings.
2. Select the company for which you are setting the history retention period.
3. Select the number of days for which to retain history.
4. Click [Save Changes].

Selecting Advanced SQL Server Settings

You use the options on the Advanced SQL Server Settings tab to reconfigure certain aspects of your SQL
Server instance, including memory management, connection timeout, communication encryption , and certain
types of access.

      Important! The settings you choose on this tab apply to all the databases in the SQL Server instance, not
      just to one company.

      Tip: If you want to monitor the effect of changes to these settings on your SQL Server instance, open the
      Microsoft SQL Server Profiler from the Toolbox.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  66
To reconfigure advanced SQL Server settings:

1. Click Advanced Settings > Advanced SQL Server Settings.
2. Select or enter settings on the Advanced SQL Server Settings tab, as follows:

       l Maximum SQL Server memory. Type the maximum amount of memory to allow this instance to use, in
           megabytes.

       l Server connection timeout. Type the maximum number of seconds to allow the server to respond to a
           request from another machine before dropping the request and displaying a connection error to the user.

       l Enable other machines to connect to this SQL Server instance. This option is selected by default to allow
           other machines in a networked environment to connect to the SQL Server instance.

           You may want to clear this option to prevent connections while you perform maintenance on the database, or
           if you need to isolate the instance from an immediate threat.

       l Encrypt communication from Sage 100 Contractor to this SQL Server instance. Select this option if you need
           to encrypt all communication from Sage 100 Contractor.

       l Limit access for members of the 'sysadmin' role to this machine only. This option ensures that the sysadmin
           role can obtain access to the SQL Server instance only from the machine that is acting as the server.

       l Limit access to this SQL Server instance to approved applications. Access to the SQL Server instance is
           always approved for Sage 100 Contractor because it is necessary to run the software. However, you might
           want to allow other applications, such as Microsoft Excel, to communicate with the instance as well. You can
           select which applications can communicate with this SQL Server instance, as follows:
            a. Click [Edit Approvals].
            b. In the Enable Access from Other Applications window, select the checkbox beside each application that
                  you allow to communicate with this SQL Server instance.

                   Note: You can select only applications that include an application name in their database connection
                   strings. You cannot allow applications to connect that do not identify themselves properly.

            c. To edit the XML configuration file directly, click Edit advanced restrictions, and then follow the instructions
                  in the XML file to define the restrictions that you need.

3. If you want to restore the "factory settings" after reconfiguring any of these settings, click [Restore Defaults] .
4. When you are satisfied with your selections, click [Save Changes].

Selecting Backup Settings

You use the options on the Advanced Backup Settings tab to:

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1                                                 67
  l Specify the local folder to store backup files.
  l Specify a secondary network location to which to copy nightly backup files for additional security (for

     example, an external USB drive or another computer on the network).

            Note:
               l Retention options do not apply to secondary backup locations.
               l You receive no notification if the main backup is successful, but the backup to the additional location
                  fails.

  l Specify a retention plan for local "on demand" backup files.

      Important! The settings you choose on this tab apply to all the databases in the SQL Server instance, not
      just to one company.

To specify advanced settings for On Demand backups:

1. Click Advanced Settings > Advanced Backup Settings.
2. In the Set local backup folder box, type the path and name of the folder on the server machine where you

     want to store backup files, or browse to the folder.
     When you browse to a location, you can create a new folder, if one does not already exist.
3. (Optional) If you want to copy your nightly backup files to a secondary location on your network or to a
     USB drive attached to your computer, specify the path and name of the folder in the Copy nightly backup files
     to this additional location box.
4. For each type of "on demand" backup, specify the number of days to retain back files.
5. Click [Save Changes].
     When you save your changes, Database Administration sets the permissions on the backup folder. That is,
     only administrator users have access to the folder.
     Permissions are not modified for the secondary backup location.

Selecting Advanced File Attachment Settings

Sage knows that the ability to attach documents to records is used extensively. Some attachments, particularly
to employee records, may contain sensitive information, so it's important to save them securely! For example,
attaching a garnishment order to an employee's record should not be saved with your company files, where
anyone with access to the server can see it.
Your selections on the Advanced File Attachment Settings tab determine how users can attach files in Sage
100 Contractor. The options you select can affect how securely the attachments are stored.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  68
      Note: The settings on this tab apply to all users and all companies on the server.

You can allow users to:

  l Copy attachments to your company data, where all users have access.

  l Link to files stored at other locations, where you can restrict access.

For each type of record listed on the tab, you can choose whether to copy attachments or link to external files
(or both, if needed). Before choosing the type of location, consider:

  l Whether the attachment includes sensitive or personal information. If the attachment includes information
     that only certain people should view, do not copy it into your company data.

        l If all users require access to the attachment or the information is not sensitive, select Allow Copy.

        l If only certain people require access to the attachment or it contains sensitive information, select Allow
            Links. If you select this option, users saving attachments as links need to ensure that the files they are
            linking to are placed in a restricted folder, or the attachments will not be as secure as you want.

        l If you don't want users to save any attachments with a record, clear both options.

  l Whether you need to back up the attachment along with all your other company data. Only the Allow Copy
     option saves attachments automatically to a location where they will be included in nightly backups.

     If you select Allow Links and you need to back up attachments, you can back them up separately using
     secure media.

  l Whether the file will need to be updated periodically. For example, if you attach a link to a maintenance order
     in an employee record, and the amount of monthly maintenance changes later, you can replace the obsolete
     order with the current one using the software you used to save the original in the secure location.

     Documents copied into your company files are write-protected when you save the attachments.

      Example:

        l Storing emails attached to a Request for Information (RFI) record in the shared company data folder
            preserves the details of the communication and is available to anyone looking at the RFI.

            The company data folder used for copied attachments is not highly-restricted but is accessible to all
            users.

        l A court-ordered garnishment attached to an employee record contains personally Identifiable
            Information (PII) and other sensitive information to which only Human Resources should have access.

            This type of document should not be copied to the company data. A digital document of this nature
            should be secured in a highly-restricted location on the file server. In this case, save the attachment as
            a link.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  69
Important! Apart from using this tab to specify the types of locations where attachments are stored, keep
in mind that an attachment can be restricted depending on where the user saves it. For example, an
attachment that is a link to a file on a computer's local drive is available only to someone signed in to that
computer.

Sage 100 Contractor 2022 Database and Company Administration Guide Version 24.1  70
```
