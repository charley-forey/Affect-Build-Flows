<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/13-Review_and_Reporting/Modifying_custom_reports_for_drill-down.htm (Sage 100 Contractor help v20.5) -->

### Modifying custom reports for drill-down

Important! If you have modified reports, read this information regarding drilling down into report information, custom reports, and Version 13 or later.

In a few cases, some Sage 100 Contractor reports were modified so that drilling down works correctly. Therefore, any custom reports based on these following reports must be modified.

### Modifiable reports with changed calculated fields

#### 6-1-2 Job Cost Journal modifiable reports 6-1-2-21 through 6-1-2-54

The calculated field **jobcst^veenum** was changed to allow you to drill down to employees, vendors, and equipment correctly. Custom reports based on any of these reports must be modified with the new calculated field **jobcst^veenum** found in Version 13 or later reports.

#### 9-5 Takeoff Worksheet modifiable reports 9-5-0-21 through 9-5-0-47

The calculated field **tkflin^recnum** was changed to allow drilling to the job. Custom reports based on any of these reports should be modified with the new calculated field **tkflin^recnum** found in Version 13 or later reports.

### Modifiable reports adjusted for drill-down:

#### **3-10-3-91 T & M Detail Worksheet~with Total Markup Percentage** and supplemental report **3-10-3-19 T & M~Internal Use (Reprint)~ with Total Markup Percentage**

The calculated field **tmintl^markup** was adjusted to the right to allow drilling down on the last column of the report. The tax **Yes/No** calculated field was hiding the ability to drill down for this column.

#### **5-1-4-46 Local Tax Report~with Differentia**l

The employee field **payrec.empnum** was moved to the right to separate it from the timecard record number in order to allow drilling down to the payroll record.

| Links to more information . . . [Printing reports to screen—print preview](Printing_reports_to_screen_-_print_preview.md) [About the Dashboard](../../Appendices/A-Sage_100_Contractor_Features/About_the_Dashboard.md) [Editing reports for drill-down](Editing_reports_for_drill-down.md) [About report printing](About_report_printing.md) |
|---|
