<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/13-Review_and_Reporting/13-3_Report_Writer.htm (Sage 100 Contractor help v20.5) -->

## 13-3 Report Writer

**13-3 Report Writer** provides tools that help you create custom reports of your Sage 100 Contractor data. With **13-3 Report Writer**, you can modify existing reports or create entirely new reports to suit your company’s needs.

Before creating a report, you need to understand how **13-3 Report Writer** and **13-5 Form/Report Page Design** work together.

- You use **13-5 Form/Report Page Design** to create the page layout for a single page form or a multi-page form that includes text, fields, and calculated fields. Most form designs also have a detail box that indicates to Sage 100 Contractor where the report details will be placed.
- You use **13-3 Report Writer** to create the body of the report, which appears in the detail box of the form design. In the design of the report details, you can include text, fields, and calculated fields. In addition, you can control when the report prints on a new page or on an entirely new form. You also use **13-3 Report Writer** to associate a specific form design with a report. When you select the report for printing, Sage 100 Contractor automatically selects the associated form design. In addition, you can determine the location of the report in Sage 100 Contractor. You can assign custom reports to **13-4 Report Printing**, or to another window that contains reports similar to the custom report.

You can create new reports from scratch, or you can use existing reports as the basis for new reports. When you display a Sage 100 Contractor report, Sage 100 Contractor copies the report and displays the copy in the **13-3 Report Writer** window. You can then edit, rename, and save the new report.

### Creating new reports

Note: Sometimes it is quicker to create a new report by editing an existing report that needs only a few changes or additions.

#### To create a new report:

1. Open **13-3 Report Writer**.
2. On the **New Report Launch** window, select one of the following options:
   
   - **Create a new report using the wizard...**
   - **Start with a blank report**
3. Click [**OK**].

### Modifying existing reports to create new reports

Before you start, locate the report you want to modify, and write down its name.

To identify the report, use its file name, which is a combination of:

- The menu option where the report is located.
- The number of the report.

These two items are combined to form an eight-character file name. For example, 04010221.RPF is the report for **4-1-2 Payable Invoice**, report 21.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To create a new report by modifying an existing report](javascript:void(0);)

1. Open **13-3 Report Writer**.
2. In the New Report Launch wizard, select **Browse for an existing report...**, and then click [**OK**].
3. Click [**Display System Reports**]. If you want to modify a report that you have already customized, select [**Display Private Custom Reports**] or [**Display Shared Custom Reports**]. Note: Alternatively, you can open the report that you want to modify by selecting it on a Report Printing window, and then clicking [**Modify Report**].
4. On the list, locate and then double-click the report you want to open—for example, 04010221.RPF (AP Invoice List).
5. In the **Report Title** text field, type a title for the new report.
6. In the **Report Form** field, select a report form.
7. To modify the grouping and sorting of fields:
   
   1. Click **Edit > Grouping/Sorting...**.
   2. On the **Define Grouping and Sorting** window, select a table, and then double-click items in the **Fields** list to move them to the bottom panel.
   3. In the bottom panel, you can:
      
      - Remove groups by right-clicking a group field
      - Reorder groups by dragging them into the desired order
      - Change sort order by clicking on columns in the main row of the panel
   4. Click **OK**.
8. To modify the report selection criteria:
   
   1. Click **Edit > Selection Criteria...**.
   2. On the **Define the Selection Criteria** window, select a table, and then double-click items in the **Fields** list to move them to the bottom panel.
   3. In the bottom panel, you can choose to enter default criteria, or you can leave the criteria blank.
   4. Click **OK**.
9. Click **File > Save**.
10. In the message box confirming the modification, click [**OK**].
11. Change the last two digits of the report name to a number between 1 and 20.
12. Click [**Save**].

### Using the New Report Launch window

Using the New Report Launch window, you can:

- Create a new report using the wizard.
- Browse for an existing report.
- Start with a blank report.
- Open a recent report. (The last five saved reports are listed.)

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Creating a new report using the wizard](javascript:void(0);)

1. To open the Report Wizard, accept the default **Create a new report using the wizard...** option, and then click [**OK**].
2. Type the title to display at the top of the report, and then click [**Next**]. Note: You can include a subtitle by adding a '~' and then the subtitle text.
3. Choose the report form on which to print the report, and then click [**Next**]. Note: You can use wildcards in the report form name, such as "*.Report," to be able to select .Report file when running the report.
4. Scroll to the menu where the records are located, select the table that holds the primary data for the report, and then click [**Next**]. Tip: You can also list tables by name to view a simple alphabetical list of all data tables. Select **List Tables by Name**.
5. In the **Fields** list on the top right, double-click fields in the primary table to add to the report.You can sort these fields by name if you select the **List Fields by Name** option. You can select fields from related tables by changing the selected table in the list on the top left.In the bottom panel, you can:
   
   - Group fields on the report by dragging columns to the group area in the dark gray band. You can use up to three fields for grouping.
   - Add sorting by clicking on a column. The number that appears next to the column name is the next consecutive number after the last group. If no groups are defined, the sort column displays a 1. You can have multiple sorts in the main column row by holding the shift key when clicking additional columns.
   - Reorder columns by dragging them to a different location.
   - Remove columns from the report by right-clicking them.
6. Click [**Next**].
7. In the **Fields** list, double-click the fields to use as report selection criteria. In the bottom panel, you can:
   
   - Select the comparison option to set as the default. Note: For example, if you would like the default to be between or equal, you can set that as the default on the report printing window.
   - Lock criteria values to fix those values permanently in the report. For example, in an invoice report that should exclude voided invoices , lock the invoice status criteria as 'Less than 5-Void.'
8. Click [**Finish**].

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Browse for an existing report...](javascript:void(0);)

1. Select **Browse for an existing report...**, and then click [**OK**].
2. Click the [**Display System Reports**] button, select the report, and then click [**Open**].

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Start with a blank report](javascript:void(0);)

To create a new report without using the Report Wizard, select **Start with a blank report**, and then click [**OK**].

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Open a recent report](javascript:void(0);)

You can select a report from a list of the last five saved reports.

### Modifying reports and form designs

When the [**Modify Report**] button appears in the **Report Printing** window, you can edit the report design and the form design.

If the [**Modify Report**] button does not appear, you cannot edit the report design, but you can still edit the form design.

To open **13-5 Form/Report Page Design** from a **Report Printing** window, click **Edit**> **Form Design**.

If the form name does not appear in the **Report Form** field in the**Report Printing** window, click the [**Modify Report**] button. This opens the custom report in **13-3 Report Writer**. The custom form name is then displayed in the **Form** field. Copy the form design to the \**Report Forms** folder.

Important! Some of the over 1100 system reports are “locked,” and you cannot modify the data portion of the report. In certain cases, some reports allow modification of the design.

### Assigning reports to form designs

When you decide to print a report, Sage 100 Contractor selects the form design you assigned to the report design. You can assign a report design to a specific form or to a group of forms.

Form design uses file name extensions to group similar types of form designs together. To assign a report design to a form design, you need to determine which form design a specific report uses. When you select a report for preview or printing in the **13-4 Report Printing** window, Sage 100 Contractor displays the file name and file name extension of the form design below the **Report** list.

For example, say you create a new report for income statements titled **My Income Statement** and want the new report to use the same form design as the original report for income statements. Having created the report design, assign it a form design to use when Sage 100 Contractor generates the report. In the **Form** text box, you type report.rpt and save the new report. Later, when you print the **My Income Statement** report, Sage 100 Contractor automatically selects the Report.RPT form design.

Suppose, instead of limiting the report to the Report.RPT form design, you want to be able to select any form design using the .RPT file name extension when printing the **My Income Statement** report. In this situation, use a wildcard in place of the report name and indicate the file name extension.

In the **Form** text box, type *.RPT to indicate you want all files using the .RPT file name extension, and save the report. When you select the **My Income Statement** report for printing, you will be able to select from all the form designs using the .RPT file name extension.

When you save a report design, Sage 100 Contractor saves it as a file. The file name determines where you will find the report in Sage 100 Contractor. Whereas form designs use different file name extensions to organize the forms into meaningful groups, all report designs use the .RPF file name extension.

You can assign a custom report to:

- **13-4 Report Printing.**Assign the file any name, and then save it as a shared report that anybody can use or as a private report that only you can use. You can save an unlimited number of reports in this way.
- A specific location where similar reports are found. For example, if you create a new income statement, you might want to make the report available with the other income statements. Each window location can contain up to 20 custom reports. To assign a report to a specific window, you must use a particular file-naming scheme when you save the file:
  
  - The file name must consist of eight numbers.
  - The first six numbers must specify the window location.
  - The last two numbers are user-defined and must fall between 01 and 20.
  
  Examples:
  
  The following examples explain how to convert the window locations into the correct naming format:
  
  - You created a new departmental income statement and want to access the report from **2-8-1 Departmental Income Statement**. Convert each menu and submenu number used to arrive at the **Departmental Income Statement** into a 2-digit number, so the file name becomes 020801. As this is your first custom report in this location, add 01 to the end. The full name of the file becomes 02080101.RPF.
  - Some windows in Sage 100 Contractor are not located under two submenus. To indicate the correct report path, add two zeros in the report name to represent the last submenu. For example, you create a new income statement and want to access it from **2-3 Income Statement**. The numbers representing the location become 0203. Because you need six numbers to represent the menu location, add two zeros. The file name then becomes 020300. As this is your first custom report in this location, add 01 to the end. The full name of the file becomes 02030001.RPF.
