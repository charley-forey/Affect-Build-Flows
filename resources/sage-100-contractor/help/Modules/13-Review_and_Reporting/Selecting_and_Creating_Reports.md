<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/13-Review_and_Reporting/Selecting_and_Creating_Reports.htm (Sage 100 Contractor help v20.5) -->

## Selecting and Creating Reports

Sage 100 Contractor comes with over 1,200 reports, providing you with many ways to understand your business and to communicate with your clients. Standard reports include selection criteria that allow you to save your personal defaults for repeated use. For quick access to reports that you use often, you can drag them to the **Sage 100 Contractor Desktop** to create an icon.

You can drill down into special **Dashboard** reports and from there to the record source. This feature makes getting to the source of financial data just one mouse-click away.

You can also drill down into the 1,200 program-wide reports by running a report in print preview, which is available via the **Preview report on screen** button. With your pointer appearing as a magnifying glass with a red lens, double-clicking rows or fields drills down to report details and records.

#### Notes about reports

- When viewing a report, if there is no magnifying glass pointer on that page, then there are no drillable rows or fields on that page. For example, the first page of a report may contain design elements and no data, which are not drillable. The second page may contain drillable data.
- If your pointer becomes an hourglass when closing a report, be aware that long reports containing a hundred or more pages may take a few seconds to close.
- Running large reports may take several minutes. You can disable drilling down from any **Report Printing** window for that instance by choosing **Options > Disable print preview drill down** to speed up running the report.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To drill down into report information](javascript:void(0);)

|  | 1 | Open a record window (**3-5 Jobs (Accounts Receivable**), and select a record (for example, 186). |
|---|---|---|

|  | 2 | Click the **Print records** button. |
|---|---|---|

|  | 3 | Select a report, and click the **Preview report on screen** button. |
|---|---|---|

|  | 4 | The report appears in “print preview” mode. |
|---|---|---|

### Examples of Drilling Down into Report Information

In the following examples, Sage 100 Contractor is running the Sample Company, menu **3-1-3 Receivable Aging**, and the**31-Current Job Aging** report. The report was run without selection criteria.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Drilling down into rows](javascript:void(0);)

A single click on the information reveals whether you are drilling to information contained in a row (notice the arrows at each end of the row) or an individual field. In this case, the first line contains a drillable row in addition to two drillable fields, **Job#** and **Current Holdback**.

| Job# | Description | Current + Holdback |
|---|---|---|
| 186 | Williams Post Office | 149,696.25 |
| 201 | Trappen Motel | 156,053.48 |
| 207 | Wood Elementary School |  |

Double-clicking the row drills down to the job record **186**—**Williams Post Office** in the **3-5 Jobs (Accounts Receivable)** window.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Drilling down into fields](javascript:void(0);)

Drillable information contained in a single field is depicted differently. In a drillable field, you see arrows at each end of the field.Double-clicking the field opens a grid window that shows the details of the value, as shown in the **31—Job Current Aging~Current + Holdback** window.

Notice that the grid window displays the value in addition to the values that have been added together to create the drillable field value. At the bottom left corner of the grid window is a **Drill Down** button. By selecting a grid cell in the **A/R Invoices Balance** column (9,569.34) and clicking **Drill Down**, you can drill to the invoice.

From that invoice, you can continue to drill down to information through other reports. In addition, the status bar below the grid displays the selection criteria of the cell when the query selection criteria contains a “Where” clause.

This information can help you understand why certain information is in a grid and (equally as important) why certain information is not in the grid. For example, if you are expecting to see an important invoice on a grid but it’s not showing up, the information in the status bar can show information revealing that the invoice has incorrect status. This allows you to locate the invoice and correct its status.

#### Basic Rules for Drilling Down into Reports

Note: We recommend that you try drilling down into your own business’s reports. Hands-on practice with familiar reports is the best way to understand how drilling down into reports actually works.

- To be drillable, a row or field must have a “non-zero” value.
- Only fields that are located within a detail section of a report may be drillable. Fields on the form design portion of the report are not drillable. Headings, totals, and no print fields are not drillable.
- Screen review of grid printing is not drillable.
- To be drillable, fields must be placed in a “Group,” “Detail,” or “Subtotal” row type.

### About report selection criteria

You can use the selection criteria to limit the scope of documents; however, many reports do not require you to use selection criteria. If a criterion is left blank, Sage 100 Contractor does not use the criterion when creating the document.

Specific criteria is required to print cheques. You must provide the first cheque form number, cheque date, and ledger account number of the chequing account.

If a document does not include information that you were expecting, examine the selection criteria. If all the criteria are correct, the scope of the criteria might be too narrow. Try removing some of the criteria.

### GAAP-standard reports

Sage 100 Contractor provides several reports to reflect generally accepted accounting principles, or GAAP. These reports include the following:

- 2-2-0-21 Balance Sheet
- 2-2-0-31 Balance Sheet~This Year/Last Year Comparison
- 2-3-0-21 Income Statement
- 2-3-0-31 Income Statement~Period and YTD
- 2-3-0-32 Income Statement~This Year/Last Year Comparison
- 2-3-0-33 Income Statement~Actual/Budget Comparison
- 2-3-0-41 Dept. Income Statement
- 2-3-0-51 Dept. Income Statement~Period/Year
- 2-3-0-53 Dept. Income Statement~Actual/Budget Comparison
- 2-3-0-71 Income Summary~With Subaccount Detail Period and YTD
- 2-8-0-21 Financial Report
- 2-9-0-21 Statement of Cash Flows

### Viewing reports

You can view a list of reports in three ways:

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To view a list of available reports](javascript:void(0);)

|  | 1 | Open a Sage 100 Contractor window, for example **3-2 Receivable Invoices/Credits**. |
|---|---|---|

|  | 2 | Select the record you want to view in the data control. |
|---|---|---|

|  | 3 | In the toolbar, click the **Print Records** button. |
|---|---|---|

|  | 4 | In the **Report Printing** window, click the **Report Criteria** tab. |
|---|---|---|

|  | 5 | Double-click the report you want to view or print. |
|---|---|---|

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To view a list of all reports by menu command](javascript:void(0);)

Note: You can only edit a calculated field on an existing report containing an existing calculated field.

|  | 1 | Open **13-6 Report/Query Lists**. |
|---|---|---|

|  | 2 | The **13-6 Report/Query Lists** window opens. |
|---|---|---|

|  | 3 | If not already selected, select **21-Report List~by Menu**. |
|---|---|---|

|  | 4 | On the toolbar, click **Preview report on screen** to view the report. |
|---|---|---|

|  | 5 | Alternatively, select other printing and export options. |
|---|---|---|

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To view the list of all reports by menu option](javascript:void(0);)

Note: You can only edit a calculated field on an existing report containing an existing calculated field.

|  | 1 | Open **13-6 Report/Query Lists**. |
|---|---|---|

|  | 2 | The **13-6 Report/Query Lists** window opens. |
|---|---|---|

|  | 3 | If not already selected, select **26-Report List~by Menu Option**. |
|---|---|---|

|  | 4 | On the toolbar, click **Preview report on screen** to view the report. |
|---|---|---|

|  | 5 | Alternatively, select other printing and export options. |
|---|---|---|

### Viewing sample reports

Sage 100 Contractor provides representative samples of most reports that the system produces. These samples are not generated from the sample data, but are images for you to view. By viewing sample reports, you can get an idea of the report’s content without having to actually generate the report.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To view a sample report](javascript:void(0);)

|  | 1 | Open a Sage 100 Contractor window, for example **4-2 Payable Invoices/Credits**. |
|---|---|---|

|  | 2 | On the toolbar, click the **Print Records** button. |
|---|---|---|

|  | 3 | In the **Report Printing** window, click the **Samples** tab. |
|---|---|---|

|  | 4 | In the reports list, click a report. |
|---|---|---|

|  | 5 | The sample appears in the right pane. |
|---|---|---|

Note: Not all reports have a sample. If there is no sample, a message appears: **There is no example available for this report**.

### Working with Quick Reports

Sage 100 Contractor’s Quick Reports feature lets you create simple reports for review. When you view a Quick Report, Sage 100 Contractor displays the report information in a grid.

For example, here are some of the windows in which you can create Quick Reports:

- **1-9 Departments**
- **6-5 Cost Codes**
- **7-2-1 Security Groups**
- **7-2-2 User List**
- **9-8 Board Footage**
- **10-2 Task List**
- **12-3 Inventory Locations**

You can change the font styles in individual cells or for the entire grid. In addition, you can hide columns of information. When you print the report, any information hidden in the **Quick Report** window will not appear on the printed report.

Although you can change the formatting of a Quick Report, the changes are not saved. They are only used for printing a Quick Report. For example, open **6-5 Cost Codes**, and using the **B**, **I**, and **U**buttons located under the menu bar, apply bold, italic, or underline formatting to the contents of cells.

You can hide the columns by right-clicking the column heading and selecting the **Hide Selected Column** command from the drop-down menu. Then click the **Print Records** button. When the **Grid Printing** window opens, click the **Preview report on screen** button to view a preview of your changes.

In some cases, a grid may display too many columns for the report to fit on a standard-sized piece of paper even in landscape orientation. In such cases, we recommend that you export the quick report to Microsoft Excel, which has the capability to capture all the data on any grid in Sage 100 Contractor.

### Setting up a shortcut from a report printing window

#### To create a shortcut to a specific report:

|  | 1 | Open any **Report Printing** window. |
|---|---|---|

|  | 2 | Click the **Report Criteria**tab. |
|---|---|---|

|  | 3 | Select a report. |
|---|---|---|

|  | 4 | In the lower left of the window, click **Create a Shortcut to Selected Report**. |
|---|---|---|
