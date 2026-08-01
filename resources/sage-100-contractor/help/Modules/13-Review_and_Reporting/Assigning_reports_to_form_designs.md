<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/13-Review_and_Reporting/Assigning_reports_to_form_designs.htm (Sage 100 Contractor help v20.5) -->

### Assigning reports to form designs

When you decide to print a report, Sage 100 Contractor selects the form design you assigned to the report design. You can assign a report design to a specific form or to a group of forms.

Form design uses file name extensions to group similar types of form designs together. To assign a report design to a form design, you need to determine which form design a specific report uses. When you select a report for preview or printing in the **13-4 Report Printing** window, Sage 100 Contractor displays the file name and file name extension of the form design below the **Report** list.

For example, you create a new report for income statements titled **My Income Statement** and want the new report to use the same form design as the original report for income statements. Having created the report design, assign it a form design to use when Sage 100 Contractor generates the report. In the **Form** text box, you type report.RPT and save the new report. Later, when you print the **My Income Statement** report, Sage 100 Contractor automatically selects the Report.RPT form design.

Suppose, instead of limiting the report to the Report.RPT form design, you want to be able to select any form design using the .RPT file name extension when printing the **My Income Statement** report. In this situation, use a wildcard in place of the report name and indicate the file name extension.

In the **Form** text box, type *.RPT to indicate you want all files using the .RPT file name extension, and save the report. When you select the **My Income Statement** report for printing, you will be able to select from all the form designs using the .RPT file name extension.

| Links to more information . . . [Saving and naming reports](Saving_and_naming_reports.md) [About report printing](About_report_printing.md) [About report selection criteria](About_report_selection_criteria.md) |
|---|
