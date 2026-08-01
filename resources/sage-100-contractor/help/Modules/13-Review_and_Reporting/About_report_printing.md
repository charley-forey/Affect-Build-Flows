<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/13-Review_and_Reporting/About_report_printing.htm (Sage 100 Contractor help v20.5) -->

### About report printing

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

Important! Scheduling reports to email, fax, or print will not work if the company data is opened exclusively. If you have a question, you may review the file **SARAEventLog.txt** found in **\Program Files (or Program Files (x86))\Sage\Sage 100 Contractor** to see if a scheduled report has been sent or not and if the company was “opened for exclusive access by another user.”

#### **To print a legal-sized PDF or RTF report:**

|  | 1 | From the printers drop-down list, select either **Sage 100 Contractor RTF Export** or **Sage 100 Contractor SagePDF Export**. |
|---|---|---|

|  | 2 | From the **Size** drop-down list, select **Legal**. |
|---|---|---|

|  | 3 | On the toolbar, click the **Print records** button. |
|---|---|---|

Note: To avoid truncating the **2-3-0-34 Income Statement~All Periods** report, you must print it on legal-sized paper. One-click printing using the **Create a PDF file of this report** button does not print on legal-sized paper, even if you select this paper size, because one-click buttons use the default printer’s default settings, which are typically set to letter-sized paper.

| Links to more information . . . [About program-wide drill-down into report information](About_program-wide_drill-down_into_report_information.md) [Editing reports for drill-down](Editing_reports_for_drill-down.md) [About setting report printing defaults](About_setting_report_printing_defaults.md) [About cheque forms](About_check_forms.md) [About report scheduling](About_report_scheduling.md) [About setting up emailing and faxing through Sage 100 Contractor](About_setting_up_emailing_and_faxing_through_Sage_100_Contractor.md) |
|---|
