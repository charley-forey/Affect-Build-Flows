<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/13-Review_and_Reporting/Saving_and_naming_reports.htm (Sage 100 Contractor help v20.5) -->

### Saving and naming reports

When you save a report design, Sage 100 Contractor saves it as a file. The file name determines where you will find the report in Sage 100 Contractor. Where form designs use different file name extensions to organize the forms into meaningful groups, all report designs use the .RPF file name extension.

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

| Links to more information . . . [Creating new reports](Creating_new_reports.md) [Assigning reports to form designs](Assigning_reports_to_form_designs.md) |
|---|
