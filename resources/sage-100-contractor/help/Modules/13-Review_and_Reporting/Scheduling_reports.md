<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/13-Review_and_Reporting/Scheduling_reports.htm (Sage 100 Contractor help v20.5) -->

### Scheduling reports

Important!

- Scheduling reports to email, fax or print will not work if the company data is opened exclusively. If you have a question, you may review the file SARAEventLog.txt found in Users\username\AppData\Local\Sage\Sage 100 Contractor to see if a scheduled report has been sent or not and if the company was “opened for exclusive access by another user.”
- If you try to schedule a report that cannot be scheduled—for example, one that prints cheques or posts to the general ledger—you are prompted when saving that it is not valid for scheduling.

#### To schedule reports:

1. From any **Report Printing** window (except the 13-4 Report Printing window), open the Report Scheduling windows using one of the following methods:
   
   - From the **File** menu, click **Scheduling**.
   - From the toolbar, click the scheduling button.
2. Under **Output Options**, select one or more of the following options:
   
   - **Printer/File.**Select **Change Printer Settings** to change any of your default printer settings for this report.
   - **Fax.**Select **Edit Fax Settings** to select or change the fax recipients for this report. Note: The **Fax** option is available only if your system recognizes that a fax modem is connected. Otherwise, the selection button is not available.
   - **Email.**Select **Edit Email Settings** to select or change the email recipients for this report.
3. Under **Frequency Options**:
   
   1. In the **Time of day** drop-down list, select the time of day that you want the report to run.
   2. Select one of the following frequencies:
      
      - Select **Daily** to run the report every day at the time you have specified.
      - Select **Weekly** to run the report on a weekly schedule.
      - Select **Bi-weekly**to run the report every other week.
      - Select **Monthly** to run the report on a monthly schedule.
   3. If you selected Weekly or Bi-weekly as the frequency, under **Weekly/Bi-weekly: Day Selection**, select which day(s) of the week that you want the report to run at the specified time. For the Bi-weekly frequency, the report will run on the selected days every other week.
   4. If you selected Monthly as the frequency, under **Monthly: Day Selection**, select one of the following options:
      
      - **Print on day**(#)**of each month.**Specify which day each month that you want the report to run. For example, you can specify the report to run the 15th of each month.
      - **Print on the** (occurrence) (day) **of each month**. Select which occurrence (**first**, **second**, **third**, **fourth**, or **last**) of the month and which day of the week (**Sunday** through **Saturday**) that your report should run. For example, you can specify the report to run on the third Wednesday of each month.
4. Under **Recurrence Options**, select one of the following options:
   
   - **Print report (#) time(s).**Enter the total number of times you want the report to print for the schedule you have designated.
   - **Repeat until date.**Enter the last date that you want the report to run.
   - **Print report until the schedule is deleted.**The report runs indefinitely until you delete it using the **7-5 Scheduled Reports Manager**.
5. Under **Windows Authentication**: Caution! You must enter a valid **Windows User ID** and **Windows Password** as set up for your business in your user profile. If you do not enter a valid password, the scheduled report will not run. Moreover, you will not receive any notification that the report failed due to an invalid or missing password. Also, if you change your password, you must reschedule any previously scheduled reports using your **Windows User ID** and your new **Windows Password**.
   
   1. Enter your **Windows User ID**.
   2. Enter your **Windows Password**.
6. Under **Message for Email/Fax**:
   
   1. In the **Enter Subject Line** text box, enter the information to appear in the email or fax subject line.
   2. In the **Message** text box, enter additional text to be included as the email message or the fax cover page.
   3. Alphanumeric text and characters can be entered into the **Message** text box. You can paste text into the text box from other sources.
7. Click **Save Schedule**.

The report runs as many times or until the date specified in the schedule's **Recurrence Options**, or until you delete the schedule using the **7-5 Scheduled Reports Manager**.

Note: You cannot use the **Report Printing** window to edit or delete existing schedules. You must use the **7-5 Scheduled Reports Manager** window to edit or delete schedules.

| Links to more information . . . [Editing report schedules](Editing_report_schedules.md) [Deleting report schedules](Deleting_report_schedules.md) |
|---|
