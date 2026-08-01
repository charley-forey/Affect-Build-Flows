<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/7-Utilities/MigratingAlertsFromVersion19x.htm (Sage 100 Contractor help v20.5) -->

# Migrating alerts from version 19.8

Alerts are saved for Windows Task Scheduler on the machine they were created on. Therefore, you must use Sage 100 Contractor to migrate alerts created in version 19.8 to version 20.5 for individual workstations.

When you open the **7-6 Alerts Manager** window, Sage 100 Contractor checks whether any alerts exist on that workstation for version 19.8. If it finds any, it displays a migration window that you can use to migrate these alerts to the current version. You can choose whether to take ownership of any alerts created for the Supervisor user, and you can choose to continue to run the alerts in version 19.8 as well as in version 20.5.

Note: After you have migrated all the alerts for the workstation and deleted them from version 19.8, the migration window is no longer available from the **7-6 Alerts Manager** window.

#### Before you start

- Decide whether you want to continue to run alerts in Sage 100 Contractor version 19.8 after migrating them to version 20.5.
- Decide whether to take ownership of Supervisor alerts created in version 19.8.

Tip: If you have a large number of alerts, we suggest that you run Sage 100 Contractor as Administrator to avoid receiving a large number of Windows user access messages as you migrate the alerts. To run Sage 100 Contractor as administrator, right-click the Sage 100 Contractor icon on your Windows desktop, and then click **Run as administrator**.

#### To migrate scheduled reports from version 19.8:

1. Open **7-6 Alerts Manager**. Sage 100 Contractor checks for alerts created in the Task Scheduler for version 19.8.
2. Click [**OK**] to close the message telling you that the program found alerts for version 19.8.
3. When the **7-6 Alerts Manager** window opens, click the [**Migrate**] button that is available when there are version 19.8 alerts to migrate. The **Previous Version Alerts** window opens.
4. Use the **Previous Version Alerts** window to migrate alerts as follows:
   
   1. Select an option either to continue running the alerts in version 19.8 or to remove them all after migration.
   2. If you want to take ownership of the Supervisor alerts, select the **Yes** option. Otherwise, accept **No**.
   3. In the **Windows User Id** and **Windows password** fields, enter your Windows credentials.
   4. Click [**OK**].
