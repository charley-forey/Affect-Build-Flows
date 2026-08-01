<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/13-Review_and_Reporting/Working_With_Pages_in_13-3_Report_Writer.htm (Sage 100 Contractor help v20.5) -->

### Working with Pages in 13-3 Report Writer

### About form breaks and page breaks

You can control the point at which Sage 100 Contractor begins printing information on a new form design or a new page. Initially, when you create a new report design there are no form breaks or page breaks. You can select the form and page breaks for a custom report based on band types in the **Form Break** and **Page Break** lists.

Use the form break to determine when Sage 100 Contractor prints information on a new form. Suppose you create a **Vendor** report that lists invoices sorted by job. When printing the report, you want to be able to select a range of vendors and print a separate list for each vendor. The report contains the following bands and fields:

- The **Group 1** band contains fields for the vendor number and name.
- The **Group 2** band contains fields for the job number and job name.
- The **Detail** band contains fields for the invoice number and description.

The form break is set to **Group 1**, which tells Sage 100 Contractor to print a new form for each vendor.

Use the page break to determine when Sage 100 Contractor prints information on the next page of a multi-page form design. To continue the example above, the form design you want to use has two pages. The front page includes your company logo, address, and boilerplate text, and a continuation page includes only your company name. When creating the custom report, the page break is set to **Group 2**, which tells Sage 100 Contractor to print a new continuation page for each job.

You can also let Sage 100 Contractor automatically determine where to place form or page breaks when generating a report. When you set the form break to automatic and the form design contains a single page, Sage 100 Contractor prints a new form for each page in the report. However, if the form design contains multiple pages, Sage 100 Contractor prints a new form when there are no more pages in the form design to use. When you set the page break to automatic, the report advances to a new page when the printed page is full.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To insert a form break](javascript:void(0);)

|  | 1 | In **13-3 Report Writer**, open the report into which you wish to insert a form break. |
|---|---|---|

|  | 2 | In the **New Form** list, click the type of band that you want to begin a new form when printing the report. You can choose from the following options: |
|---|---|---|

> - Automatic
> - On Detail
> - On Group1
> - On Group2
> - On Group3

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To insert a page break](javascript:void(0);)

|  | 1 | In **13-3 Report Writer**, open the report into which you wish to insert a page break. |
|---|---|---|

|  | 2 | In the **New Page** list, click the type of band that you want to begin a new page when printing the report. You can choose from the following options: |
|---|---|---|

> - Automatic
> - On Detail
> - On Group1
> - On Group2
> - On Group3
