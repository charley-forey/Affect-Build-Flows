<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/DatabaseAdministration/win_DatabaseAdministration.htm (Sage 100 Contractor help v20.5) -->

# Database Administration for Sage 100 Contractor

The Database Administration tool is intended for designated system administrators and company administrators. You use it to set up and maintain your company databases, and to select advanced settings to manage communications with and access to your Microsoft SQL Server instance from other programs.

Important! We highly recommend that you use Database Administration, rather than SQL Management Studio®, to perform the database administration tasks listed below, even if you are an experienced SQL Server user. Besides handling all the database tasks that you are likely to perform in a typical Sage 100 Contractor system, Database Administration was designed to optimize your data for Sage 100 Contractor, for example, by keeping related data in expected locations and creating backups automatically before performing certain critical processes. In the rare event that you need to use SQL Management Studio® to perform a task that is not provided in Database Administration, you should contact Customer Support for assistance.

Database Administration includes the following database and company management utilities:

- Create Company Based on Existing and Create Company create new Microsoft SQL Server databases.
- Rename Company and Delete Company are convenient utilities when working with existing companies.
- Deploy Sample Company helps you install and refresh the sample data that comes with Sage 100 Contractor.
- Tune Up Company Databases performs various maintenance tasks to keep your database functioning efficiently.
- Back Up Company Databases enables you to back up your data "on demand," whenever needed.
- Restore Company from Backup restores a backed-up copy of your database.
- Upgrade Company Databases prepares your SQL company data so that it is compatible with the most recent version of Sage 100 Contractor 2017.
- Migrate Company Data and Migrate Custom Reports transfers your version 19.8 company data and custom reports to a new location for Microsoft SQL Server. Migrated files are located in shared folders under \\ServerName\CompanyName, organized using a folder structure similar to earlier versions.
- Schedule Nightly Maintenance utilities enable you to schedule backup and maintenance operations for times when other users are not logged into the system. You can also select the number of consecutive backups to keep.
- Manage Company Admins/SQL Logins utilities enable you to set up or delete logins to the SQL Server database, and to designate a user as a company administrator for a specified Sage 100 Contractor company.
- Advanced Company Settings lets you specify how long to keep history about database changes for each company, including details about changed records, such as the date and user ID of the employee made the change. Details older than the retention period you specify are cleared during nightly maintenance. (This history is maintained in separate audit tables, which you can query using SQL Server Management Studio.)
- Advanced SQL Server Settings includes convenient, sophisticated access and memory management controls for your SQL database.
- Advanced Backup Settings lets you specify a backup folder if you prefer not to use the default folder. You can also specify the number of days to keep "on demand" backup files.

For detailed information about these utilities and how to use them, see the Database Administration help or refer to the [Database and Company Administration Guide](http://cdn.na.sage.com/docs/en/customer/100contractor/20_4US/open/DatabaseAndCompanyAdministrationGuide.pdf).
