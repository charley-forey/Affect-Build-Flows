<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/13-Review_and_Reporting/13-8_Search_Reports.htm (Sage 100 Contractor help v20.5) -->

## 13-8 Search Reports

Enter keywords in the text box to search for applicable reports.

Notes:

- The search results match on all entries and are not case sensitive.
- Surround entries by quotes to find literal blocks.

You can show more advanced options by clicking on the **Show other search options** link.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To search by keywords](javascript:void(0);)

|  | 1 | Open **13-8 Search Reports**. |
|---|---|---|

|  | 2 | Enter a keyword in the Search text box. |
|---|---|---|

|  | 3 | Click [**Search**]. |
|---|---|---|

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To search by specific program area](javascript:void(0);)

Sage 100 Contractor searches the first level menu number equivalent to the listed area of the program. If the **Include report forms** option is included, Sage 100 Contractor will also search the Report Forms subdirectory.

|  | 1 | Open **13-8 Search Reports**. |
|---|---|---|

|  | 2 | Click the **Show other search options** link. |
|---|---|---|

|  | 3 | Enter a keyword in the Search text box. |
|---|---|---|

|  | 4 | In the **Limit search to a specific program area** list, select the program area. |
|---|---|---|

|  | 5 | Click [**Search**]. |
|---|---|---|

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To search by specific data table](javascript:void(0);)

|  | 1 | Open **13-8 Search Reports**. |
|---|---|---|

|  | 2 | Click the **Show other search options** link. |
|---|---|---|

|  | 3 | Enter a keyword in the Search text box. |
|---|---|---|

|  | 4 | In the **Limit search to a specific data table** list, select the data table. |
|---|---|---|

|  | 5 | Click [**Search**]. |
|---|---|---|

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Including database fields in search](javascript:void(0);)

|  | 1 | Open **13-8 Search Reports**. |
|---|---|---|

|  | 2 | Click the **Show other search options** link. |
|---|---|---|

|  | 3 | In the **Tables** column, select the table to choose fields from. |
|---|---|---|

|  | 4 | In the **Fields** column, select the field and click [**OK**]. |
|---|---|---|

|  | 5 | Click [**Search**]. |
|---|---|---|

#### Search options

When the **Search into calculated fields** option is included in the search, a match is found if the calculated field exists in the report or form design. The report search is not validating that the calculated field is being used in either the report or form design.

If the **Include report forms** option is included in the search, and all search criteria is found in the report design (.RPF file), then the row on the Search Results list has the .RPF title listed and **<< Any >>** in the **Forms** column in the list.

If the **Include report forms** option is not included in the search, then Forms column is not shown in the results list box.

### Interpreting report search results

Once you make your selection criteria, the program searches the System and Custom Report folders (and if selected, Report Forms folder) and returns a list of all the reports that match. Select the report you want to view and click Run Report.

- Report Design file (rpf) – A Sage 100 Contractor report file that is in menu option **13-3 Report Writer**.
- Form Design – A Sage 100 Contractor form design file saved in menu option **13-5 Form/report Page Design**

Notes:

- If form designs are not included in the search, the Forms column is not shown in the results list box.
- Custom reports are shown after system reports.

A finished report is the combination of the form design which is usually a logo, header and footer and the report design which is the detail of the report.

If all search criteria is found in the report design (.RPF file), then the row on the Search Results list has the rpf title listed and **<< Any >>** in the Form column in the list which means any form design can be used with the report and there will be a complete match for the search criteria.

If any, but not all, of the criteria is found in the report design, then the form design designated in the rpf is searched, and if the all of the remaining criteria are found in the form design, then the row on the Search Results list has the rpf title listed and the form design file name in the Form column in the list. This means that form design can be used with the report and there will be a complete match for the search criteria.

If the report design uses a *.extension for the form design, then all of the form designs with that extension are examined, and if more than one form finds all the remaining matches, then you can right click on the **<< Right click to view >>** to see all the matching form design file names in a scrollable message box.
