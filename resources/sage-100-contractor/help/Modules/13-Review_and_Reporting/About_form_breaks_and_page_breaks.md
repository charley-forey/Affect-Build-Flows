<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/13-Review_and_Reporting/About_form_breaks_and_page_breaks.htm (Sage 100 Contractor help v20.5) -->

### About form breaks and page breaks

You can control the point at which Sage 100 Contractor begins printing information on a new form design or a new page. Initially, when you create a new report design there are no form breaks or page breaks. You can select the form and page breaks for a custom report based on band types in the **Form Break** and **Page Break** lists.

Use the form break to determine when Sage 100 Contractor prints information on a new form. Suppose you create a **Vendor** report that lists invoices sorted by job. When printing the report, you want to be able to select a range of vendors and print a separate list for each vendor. The report contains the following bands and fields:

- The **Group 1** band contains fields for the vendor number and name.
- The **Group 2** band contains fields for the job number and job name.
- The **Detail** band contains fields for the invoice number and description.

The form break is set to **Group 1**, which tells Sage 100 Contractor to print a new form for each vendor.

Use the page break to determine when Sage 100 Contractor prints information on the next page of a multi-page form design. To continue the example above, the form design you want to use has two pages. The front page includes your company logo, address, and boilerplate text, and a continuation page includes only your company name. When creating the custom report, the page break is set to **Group 2**, which tells Sage 100 Contractor to print a new continuation page for each job.

You can also let Sage 100 Contractor automatically determine where to place form or page breaks when generating a report. When you set the form break to automatic and the form design contains a single page, Sage 100 Contractor prints a new form for each page in the report. However, if the form design contains multiple pages, Sage 100 Contractor prints a new form when there are no more pages in the form design to use. When you set the page break to automatic, the report advances to a new page when the printed page is full.

| Links to more information . . . [Inserting form breaks](Inserting_form_breaks.md) [Inserting page breaks](Inserting_page_breaks.md) [About bands](About_bands.md) |
|---|
