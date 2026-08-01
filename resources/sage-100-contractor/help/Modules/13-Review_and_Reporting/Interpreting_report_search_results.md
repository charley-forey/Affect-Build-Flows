<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/13-Review_and_Reporting/Interpreting_report_search_results.htm (Sage 100 Contractor help v20.5) -->

### Interpreting report search results

Once you make your selection criteria, the program searches the System and Custom Report folders (and if selected, Report Forms folder) and returns a list of all the reports that match. Select the report you want to view and click Run Report.

- Report Design file (rpf) – A Sage 100 Contractor report file that is in menu option **13-3 Report Writer**.
- Form Design – A Sage 100 Contractor form design file saved in menu option **13-5 Form/report Page Design**

Notes:

- If form designs are not included in the search, then Forms column is not shown in the results list box.
- Custom reports are shown after system reports.

If the **Include report forms** option is included, Sage 100 Contractor searches the following locations:

- \\ServerName\Sage100Contractor\Custom Reports
- \\ServerName\Sage100Contractor\User Data\username\Custom Reports
- \Program Files\Sage\Sage 100 Contractor SQL\System Reports or \Program Files Program Files (x86)\Sage\Sage 100 Contractor SQL\System Reports.

If all search criteria is found in the report design (.RPF file), then the row on the Search Results list has the rpf title listed and **<< Any >>** in the Form column in the list which means any form design can be used with the report and there will be a complete match for the search criteria.

If any, but not all, of the criteria is found in the report design, then the form design designated in the rpf is searched, and if the all of the remaining criteria are found in the form design, then the row on the Search Results list has the RPF title listed and the form design file name in the Form column in the list. This means that form design can be used with the report and there will be a complete match for the search criteria.

If the report design uses a *.extension for the form design, then all of the form designs with that extension are examined, and if more than one form finds all the remaining matches, then you can right click on the **<< Right click to view >>** to see all the matching form design file names in a scrollable message box.
