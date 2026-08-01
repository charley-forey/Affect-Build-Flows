<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Appendices/A-Sage_100_Contractor_Features/ViewingChangeHistoryInRecords_Fields.htm (Sage 100 Contractor help v20.5) -->

# Viewing record and field history

Many data entry windows in version 20.5 include a View menu, with options that enable company administrators to view the history of changes to a selected record.

Notes:

- The depth of the change history is determined by the retention policy set for your company in Database Administration. History is retained for 180 days by default, but you can change the retention period.
- You do not have to log into the company with Administrator rights to view history, providing you are set up as a company administrator in the **7‑7‑2 User List**.

When you display a record in a window that has a View menu, you can select one of two options to view history:

- **View** > **Record history.** When you select this option, a separate **View History** window opens, displaying a list of all the changes to the current record. Initially, the list summarizes all the changes to the record, showing for each change If there were many changes, you can filter a long list to show only changes for a particular table, user, or application. To view the details of a particular change, click the row on which the change is listed. Sage 100 Contractor displays a **History Details** window that shows, for each field in the record, the value of each field before and after the change.
  
  - The database table that was updated,
  - Whether new information was inserted or existing information was modified or deleted.
  - The date and time.
  - The login ID of the user who made the change.
  - The ID of the computer where the change originated.
  - The application where the change originated (for example, Sage 100 Contractor, Database Administration, or SQL Server Management Studio).
- **View** > **Field history.** When you select this option, field entries that have changed for the current record are displayed against a yellow background. To view change details for a particular field, click the field, and then press [F12]. Sage 100 Contractor displays a separate **History** window for the field that lists the ID of each person who made a change, the date of the change, the field values before and after the change, and the application where the change originated. With View Field History turned on, you cannot edit the record.

The view history options are turned off when you close the window or move to another record.
