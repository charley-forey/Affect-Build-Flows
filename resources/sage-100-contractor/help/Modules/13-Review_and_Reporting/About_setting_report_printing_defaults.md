<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/13-Review_and_Reporting/About_setting_report_printing_defaults.htm (Sage 100 Contractor help v20.5) -->

### About setting report printing defaults

You can save time and effort by setting up your preferences for report types, form designs, selection criteria, and options in the **Report Printing** window. You can also set preferences for printers, page ranges, page orientation, and number of copies to print. When you save the defaults, Sage 100 Contractor assigns them to the user name currently logged on to Sage 100 Contractor.

#### Displaying the date format on reports

To show which format is used for dates printed on a form design, you can add a global calculated field to the form design to show which date format is used on the printed report. If you add the CP^dtefmt (or cmpany^dtefmt) date field to a form design, when you use the form design to run a report, the header in the printed report (or PDF) will indicate the format your company uses for dates. In this example, the line "(mm/dd/yyyy)" indicates that the date is August 12th, not December 8th:

| Form Design | Printed Report |
|---|---|
| `<<CP^>>` | **AR Invoice List** |
| `<<CP^curdte>>` | 08/12/2020 |
| `<<CP^dtefmt>>` | (mm/dd/yyyy) |

Caution! These calculated fields can be used only on form designs. Inserting them in report details will corrupt the report, causing it to fail when you try to print it.

Note: The date format field is provided for your convenience, and is optional.

| Links to more information . . . [Entering defaults in Report Printing windows](Entering_defaults_in_Report_Printing_windows.md) [Printing documents or grids or reports](Printing_documents__grids__or_reports.md) [Saving printer settings](Saving_printer_settings.md) [Changing the default printer driver](../7-Utilities/Changing_the_default_printer_driver.md) |
|---|
