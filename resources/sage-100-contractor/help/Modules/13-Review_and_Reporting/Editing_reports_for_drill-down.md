<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/13-Review_and_Reporting/Editing_reports_for_drill-down.htm (Sage 100 Contractor help v20.5) -->

### Editing reports for drill-down

When you open a report in print preview, you expect to be able to drill down into the report’s information; however, not all reports contain rows and fields that are immediately drillable. You can edit an existing standard report or a custom report to be able to drill down to information that might be otherwise unavailable.

The following procedure provides an example of how editing a standard report can make more information drillable.

#### To edit a report for drill-down:

Important! The report may contain tables pertaining to different records. In such a case, you must insert the appropriate record number field to enable drilling down into specific rows.

|  | 1 | Open **3-7 Progress Billing**, and select a record using data control. |
|---|---|---|

|  | 2 | On the toolbar, click the **Print records** button. |
|---|---|---|

The **3-7 Report Printing** window opens. By default, the first report is selected, **21-Progress Billing~by Cost Code**.

|  | 3 | On the toolbar, click the **Preview report on screen** button. |
|---|---|---|

The **21—Progress Billing~by Cost Code** report window opens. In this example the report contains three pages.

|  | 4 | Scroll to the second page. Note that fields in the first column are drillable, but none of the fields in the other columns are drillable. |
|---|---|---|

Now let’s edit the report so that the rows are drillable.

|  | 5 | Close the report. |
|---|---|---|

|  | 6 | On the **3-7 Report Printing** window, with **21-Progress Billing~by Cost Code** selected, click the **Modify Report** button. |
|---|---|---|

The **13-3 Report Writer**window opens.

Note: On the left of the report form, you see **Heading**, **Detail**, and **Totals**. To be drillable, fields must be placed in a **Group**, **Detail**, or **Subtotal** row type. Because **Headings** and **Totals** are not drillable, you insert the text field in the **Details** row type.

|  | 7 | In the **Detail** row, to insert a text field, click once. If you insert a text field outside the size of a printable page, the query result for that field will be not be visible to customers. |
|---|---|---|

|  | 8 | On the toolbar, locate and click the **Insert fields from a list** button. The **Insert a Field** window opens. |
|---|---|---|

|  | 9 | From the list of **Fields** in the Progress Billing Lines table, locate and double-click the **Record#** line. |
|---|---|---|

That field now appears in the report form.

Important! The field you insert must be a record number pertaining to the rows in the report. Insert a progress billing record number field to drill down into progress billing rows.

|  | 10 | Click **File > Save**, and save the report under a new name, such as 03070001. |
|---|---|---|

Note: Name your edited report using numbers ending in -01 to -20. Numbers -21 through -99 are reserved for existing reports. If you follow the standard numbering scheme, for example 0307xxxx, the edited reports for **3-7 Progress Billing**, are grouped together.

|  | 11 | Close **13-3 Report Writer**. |
|---|---|---|

You return to **3-7 Report Printing** with the edited report **01-Progress Billing~by Cost Code** selected.

|  | 12 | On the toolbar, click the **Preview report on screen** button. |
|---|---|---|

The **01—Progress Billing~by Cost Code** report window opens.

|  | 13 | Scroll to the second page, and note that fields in the first column are still drillable. |
|---|---|---|

|  | 14 | Move your cursor over a value in the **Contract** column, and then double-click it to go to the progress billing record number for that row. |
|---|---|---|

Tip: We recommend that you try variations of this procedure on other reports to fine-tune drilling down into standard or custom reports to better meet your business needs.

| Links to more information . . . [Printing reports to screen—print preview](Printing_reports_to_screen_-_print_preview.md) [About the Dashboard](../../Appendices/A-Sage_100_Contractor_Features/About_the_Dashboard.md) [Modifying custom reports for drill-down](Modifying_custom_reports_for_drill-down.md) [About report printing](About_report_printing.md) |
|---|
