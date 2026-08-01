<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/13-Review_and_Reporting/About_pre-defined_calculated_fields.htm (Sage 100 Contractor help v20.5) -->

### About pre-defined calculated fields

Pre-defined calculated fields are fields that Sage 100 Contractor recognizes and automatically replaces with the proper data. These are locked fields that cannot be changed. Unlike other fields, standard or calculated, which you insert, create and/or add to the report, pre-defined calculated fields must be typed directly into the form design.

Most, but not all of these pre-defined calculated fields are also global calculated fields. For example, **cmpany^cmpnme** is the same as **CP^cmpnme**. Both fields pull the company name from the database.

Important! There is only one difference between the two types of calculated fields. Pre-defined calculated fields must be typed directly into the form design, whereas global calculated fields must be added from the **Calculated Fields** window.

The fields listed in the table below work only in **13-5 Form/Report Page Design**, not in **13-3 Report Writer**. Many of these pre-defined fields exist in the form designs that come with Sage 100 Contractor.

| Pre-Defined Field | Data |
|---|---|
| CP^cmpnme | Company Name |
| CP^cmpad1 | Company Address 1 |
| CP^cmpad2 | Company Address 2 |
| CP^ctyste | Company City & Province |
| CP^zipcde | Company Postal Code |
| CP^mallbl | Company Mail Label |
| CP^licnum | Company License Number |
| CP^ctynme | Company City Name |
| CP^state | Company Province Name |
| CP^phnnum | Company Phone Number |
| CP^curdte | Current Date |
| CP^curtme | Current Time |
| CP^curusr | Current User |
| CP^pagnum | Page Number |
| CP^pagnxt | Consecutive Page Number (will ignore new page one for new groups, and so on) |
| CP^stetax | Company Province Tax ID# |
| CP^fedtax | Company Federal Tax ID# |
| CP^memnte | Notes entered on report selection window |
| CP^select | Report Selection Criteria |
| CP^subttl | Report Subtitle |
| CP^faxnum | Company Fax Number |
| CP^rslnum | Company Resale Number |
| CP^usrdf1 | Company User Defined 1 |
| CP^usrdf2 | Company User Defined 2 |
| CP^e_mail | Company Email address |
| CP^bnkact | Company Bank Account Number (for Direct Deposit) |
| CP^rtnmbr | Company Routing Number (for Direct Deposit) |
| CP^ntetxt | Company Note |
| CP^rptttl | Report Title |
| CP^rptopt | Report Option |
| CP^stmdte | Statement Date (for printing from **3-4 Statements**) |

| Links to more information . . . [Adding calculations to fields](Adding_calculations_to_fields.md) [Inserting calculated fields in reports](Inserting_calculated_fields_in_reports.md) |
|---|
