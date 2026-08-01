<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/13-Review_and_Reporting/Printing_Reports.htm (Sage 100 Contractor help v20.5) -->

### Printing Reports

Clicking the **Print Records** button on many Sage 100 Contractor windows opens a **Report Printing** window that is pre-loaded with reports specific to the area in which you are working. For example, if you are working in **3-2 Receivable Invoices/Credits**, Sage 100 Contractor opens **3-2 Report Printing**.

#### Report Printing window toolbar

The toolbar buttons in the **Report Printing** window provide versatile tools for working with reports. From right to left:

- **Send report to the selected printer** sends the selected report to the default printer or the printer you select from the printer selection drop-down menu.
- **Preview report on screen** opens the selected report in print preview mode with drill-down functionality (when available).
- **Send report data to Excel** opens the report in an Excel worksheet.
- **Send report to Word** sends the report to an **Export to File** window. Click **Save** to open the report in Word as an RTF file. The default **Save in** folder is the **Reports** folder under the company folder.
- **Create a PDF file of this report** sends the report to an **Export to File** window. Click **Save** to open the report in Adobe Reader as a PDF file. The default **Save in** folder is the **Reports** folder under the company folder.
- **Send report as an Outlook email attachment** launches Outlook with the report attached to an email message as a PDF file.
- **Email this report** opens the **Email Distribution** window which provides the means to send a message through Sage 100 Contractor email functionality.
- **Fax this report** opens the **Fax Distribution** window which provides the means to send a fax through Sage 100 Contractor faxing functionality. (Requires an installed fax/modem)
- **Schedule this report** opens the **Report Scheduling** window, which provides the means for you to schedule sending the selected report. Note: This button is not available in the **13-4 Report Printing** window.
- **Set the print orientation to landscape or portrait** becomes available when printing graphs or charts.
- **Enter notes for this record** opens the **Notes** window and, if the form design contains the field for inserting a note, the text of the note is inserted in the selected report.
- **Enter a new record** clears the selection criteria and resets the form design to the saved default.

Notes:

- Printing reports on legal-sized paper is a special condition.
- Printing Gantt charts works differently than other report printing. For example, you must select a form design with either portrait or landscape orientation. Paper size and the size of the detail section do not matter because the program takes the selected form design elements and resizes them to fit the size of the selected printer page size.

#### Selection criteria and form designs

In the **Report Printing** window, you can select which report design is printed. Using the selection criteria, you can narrow the scope of a report to provide only the information you need. In addition, you can make changes to a report before printing it.

Report printing allows you to set up printer defaults. Most windows from which you can print have a dedicated **Report Printing** window. Suppose that you have two printers: a tractor feed printer that is used to only print cheques and a laser printer that is used to print all other documents. In the **Report Printing** window from which you print general ledger cheques, you can set the dot matrix printer as the default.

Important! Scheduling reports to email, fax, or print will not work if the company data is opened exclusively. If you have a question, you may review the file **SARAEventLog.txt** found in \Users\Username\AppData\Local\Sage\Sage 100 Contractor\ to see if a scheduled report has been sent or not and if the company was “opened for exclusive access by another user.”

#### **To print a legal-sized PDF or RTF report:**

|  | 1 | From the printers drop-down menu, select either **Sage 100 Contractor RTF Export** or **Sage 100 Contractor SagePDF Export**. |
|---|---|---|

|  | 2 | From the **Size** drop-down menu, select **Legal**. |
|---|---|---|

|  | 3 | On the right end of the toolbar, click the **Print records** button. |
|---|---|---|

Note: The report, **2-3-0-34 Income Statement~All Periods**, must be printed on legal-sized paper to avoid being truncated. One-click printing using the **Create a PDF file of this report** button on the toolbar, for example, does not print to legal-sized paper even when selected because one-click buttons use the default printer’s default settings, which are typically set to letter-sized paper.

### Setting report printing defaults

You can save time and effort by setting up your preferences for report types, form designs, selection criteria, and options in the **Report Printing** window. You can also set preferences for printers, page ranges, page orientation, and number of copies to print. When you save the defaults, Sage 100 Contractor assigns them to the user name currently logged on to Sage 100 Contractor.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To enter defaults in a Report Printing window](javascript:void(0);)

|  | 1 | Open the **Report Printing** window for which you want to set up defaults. |
|---|---|---|

|  | 2 | In the **Form Design** list, click the form design that you want. |
|---|---|---|

|  | 3 | On the **Selection Criteria** tab, enter the criteria that you want to use for selecting data. |
|---|---|---|

|  | 4 | On the **Default** menu, click **Save Defaults**. |
|---|---|---|

### Printing documents, grids, or reports

You can print reports, records, or grids from most windows in Sage 100 Contractor.

Important! Edit or delete an existing schedule from **7-5 Scheduled Reports Manager**. Schedules cannot be edited or deleted from the **Report Printing** window.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To print a document, grid, or report](javascript:void(0);)

|  | 1 | From the **File** menu, select **Print**. |
|---|---|---|

|  | 2 | In the **Report Printing** window, click the **Report Criteria** tab, then click the report that you want to print. |
|---|---|---|

|  | 3 | Select the **Report Form** from the drop-down list. |
|---|---|---|

|  | 4 | In the selection criteria, enter the conditions that you want to use to select data. |
|---|---|---|

|  | 5 | Select a printer from the drop-down list. |
|---|---|---|

|  | 6 | Select the paper size, tray, and quality settings. The list of these options depends on your printer. |
|---|---|---|

|  | 7 | To print specific pages, enter their numbers in the text boxes next to **Pages**. |
|---|---|---|

|  | 8 | Select how many copies you want by clicking on the up and down arrows next to **Copies**. |
|---|---|---|

|  | 9 | To preview the document, click the **Preview** button. |
|---|---|---|

|  | 10 | Do one of the following: |
|---|---|---|

- From the **File** menu, select **Print**.
- On the toolbar, click the **Print Records** button.

Notes:

- Reports can be [scheduled](Scheduling_reports.md) to be printed, faxed, or emailed at a specific time and frequency.
- Reports can be [faxed](Faxing_reports_to_clients_and_vendors_and_employees.md) or [emailed](Emailing_reports_to_clients_and_vendors_and_employees.md) immediately to a recipient from this window.
- Use the **Defaults** command from the menu to save a default report type and automatically have that report at the top of the list the next time you return to **Report Printing**.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To save printer settings](javascript:void(0);)

|  | 1 | Select a printer from the drop-down list. |
|---|---|---|

|  | 2 | Select the paper size in the **Size** drop-down list. |
|---|---|---|

|  | 3 | Select the tray settings in the **Tray** drop-down list. |
|---|---|---|

|  | 4 | Select the quality in the **Quality** drop-down list. |
|---|---|---|

|  | 5 | The list of these options depends on your printer. |
|---|---|---|

|  | 6 | To print specific pages, enter their numbers in the text boxes next to **Pages**. |
|---|---|---|

|  | 7 | Select how many copies you want by clicking on the up and down arrows next to **Copies**. |
|---|---|---|

|  | 8 | Select **Save Printer Settings**. |
|---|---|---|

### Printing reports to screen—print preview

You can preview reports before you print them by clicking the **Preview report on screen** button. It is located on each report printing window on the toolbar in the upper right. It is indicated by the button displaying a magnifying glass.

Viewing reports in print preview also provides the platform for drilling down into report information. When you are viewing a report in print preview and if there is drillable information on that report page, your cursor becomes a magnifying glass. When the lens displays a red circle, you can double-click the row or field to drill down to the details of the report information.
