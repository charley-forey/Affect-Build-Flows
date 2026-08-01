<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/7-Utilities/MigratingScheduledReportsFromVersion19x.htm (Sage 100 Contractor help v20.5) -->

# Migrating scheduled reports from version 19.8

Scheduled reports are saved in Windows Task Scheduler on the machine they were created on. Therefore, you must use Sage 100 Contractor to migrate tasks scheduled in version 19.8 for individual workstations.

When you open the **7-5 Scheduled Reports Manager** window, Sage 100 Contractor checks whether any scheduled reports exist on that workstation for version 19.8. If it finds any, it displays a migration window that you can use to migrate these scheduled reports to the current version. You can select which reports to migrate, and you can choose to continue to run those reports in version 19.8 as well as in the current version.

Note: After you have migrated all the scheduled reports for the workstation and removed them from version 19.8, the migration window is no longer available from the **7-5 Scheduled Reports Manager** window.

#### Before you start

Decide whether you want to continue to run scheduled reports in Sage 100 Contractor version 19.8 after migrating them to the current version.

Tip: If you have a large number of scheduled reports, we suggest that you run Sage 100 Contractor as Administrator to avoid receiving a large number of Windows user access messages as you migrate the reports. To run Sage 100 Contractor as administrator, right-click the Sage 100 Contractor icon on your Windows desktop, and then click **Run as administrator**.

#### To migrate scheduled reports from version 19.8:

1. Open **7-5 Scheduled Reports Manager**. Sage 100 Contractor checks for scheduled reports saved in the Task Scheduler for version 19.8.
2. Click [**OK**] to close the message telling you that the program found scheduled reports for version 19.8.
3. When the **7-5 Scheduled Reports Manager** window opens, click the [**Migrate**] button that is available when there are version 19.8 scheduled reports to migrate. The **Previous Version Schedule Reports** window opens.
4. Use the **Previous Version Schedule Reports** window to migrate reports as follows:
   
   1. In the **Migrate** column, select the check box beside the scheduled reports you want to migrate to the current version, or click [**Select All**].
   2. Select an option either to continue running the reports in version 19.8 or to remove them after migration.
   3. In the **Windows User Id** and **Windows password** fields, enter your Windows credentials.
   4. Click [**OK**].
