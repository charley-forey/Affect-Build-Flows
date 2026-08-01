<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/7-Utilities/About_changing_the_date_format_for_your_company.htm (Sage 100 Contractor help v20.5) -->

# About changing the date format for your company

If your company does not want to use the default Canadian format for dates (dd/mm/yyyy), you can use the United States format (mm/dd/yyyy).

You choose the United States date format by selecting the **Use mm/dd/yyyy Date Format** option in the **7-1 Company Information** window, on the Options menu.

When you select the option, all data entry screens and reports will use the United States date format, except dates on cheques, which continue to use the special Canadian date format (consistent with our cheque stock and Canadian requirements). The stub portion on a cheque will use the date format specified in the **7-1 Company Information** window.

Note: After you switch the date format, Sage 100 Contractor will not be able to interpret existing event logs that use the old format. The next time an event or scheduled report is executed, Sage 100 Contractor renames the associated existing event log, and starts a new event log, which it can read even if you change the date format again.

Tip: If you need to refer to them later, you can find old event log files (*EventLogOld) in the Sage 100 Contractorsubfolder in your local AppData folder—for example, C:\Users\Username\AppData\Local\Sage\Sage 100 Contractor\ProgramAlertsEventLogOld. You can open these files with any text editor, such as Notepad.

### Resetting formats for dates used in alerts, warnings, and report defaults

If you change the date format in the **7-1 Company Information** window, you will need to manually update any dates used in alerts, program warnings, and report selection criteria saved as defaults.

For example, if you have saved defaults for printing a report that includes a date you specify at print time, and then you change the date format for the company, you must reset the report defaults to use a date format that the report can process.

To reset the report defaults:

1. Delete the existing defaults.
2. Enter the date in the proper format.
3. Save the updated report defaults.

### Displaying the date format on printed reports

To show which format is used for dates printed on a form design, you can add a global calculated field to the form design to show which date format is used on the printed report. If you add the CP^dtefmt (or cmpany^dtefmt) date field to a form design, when you use the form design to run a report, the header in the printed report (or PDF) will indicate the format your company uses for dates. In this example, the line "(mm/dd/yyyy)" indicates that the date is August 12th, not December 8th:

| Form Design | Printed Report |
|---|---|
| `<<CP^>>` | **AR Invoice List** |
| `<<CP^curdte>>` | 08/12/2020 |
| `<<CP^dtefmt>>` | (mm/dd/yyyy) |

Caution! These calculated fields can be used only on form designs. Inserting them in report details will corrupt the report, causing it to fail when you try to print it.

Note: The date format field is provided for your convenience, and is optional.
