<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/13-Review_and_Reporting/13-5_Form-Report_Page_Design.htm (Sage 100 Contractor help v20.5) -->

## 13-5 Form/Report Page Design

Every report, document, or letter that you generate uses a form design. A form design is a template for the layout of a page or pages. With **13-5 Form/Report Page Design**, you can edit any of the form designs supplied with Sage 100 Contractor, or create entirely new forms. You can change the graphic elements and layout of the form, as well as the boilerplate text. This is especially useful when a company has several different businesses, and needs to use different forms for each business.

Before creating a report, it is important to understand how **13-3 Report Writer** and **Form/Report Page Design** work together.

- In **13-5 Form/Report Page Design**, you create the page layout for a single page form or a multi-page form that includes text, fields, and calculated fields. Form designs also use a detail box, which indicates where the details of the report will be placed.
- In **13-3 Report Writer**, you create the body of the report that appears in the detail box of the form design. In the design of the report details, you can include text, fields, and calculated fields. In addition, you can control when a report prints on a new page or on an entirely new form.

**13-5 Form/Report Page Design** provides the ability to create multi-page forms. Suppose that you always send a cover letter with each proposal to potential clients. You can incorporate both the cover letter and the proposal forms in a single design. Then when you print proposals, the cover letter always prints with the proposal. A form can have up to 100 pages, each of which you can format differently.

- Creating new forms
- Creating new forms using existing forms
- Editing existing forms
- Previewing forms

#### Creating new forms

Note: Be aware that sometimes it is quicker to create a new form from an existing form if you only have to make a few changes or additions.

To create a new form, open **13-5 Form Report/Page Design**. The **13-5 Form Report/Page Design** window appears and displays a blank page on which you can begin creating your new form.

#### Creating new forms using existing forms

It may be easier for you to use an existing form to create a new form. For example, in the **3-2 Report Printing** window, on the **Report Criteria** tab, you see a list of reports. When you click a report in the **Report Criteria** list, the form upon which the report is based is displayed in the **Report Form** drop-down list.

| Report | Report Form |
|---|---|
| 21—Receivable Invoice | System.Invoice_AR |
| 22—Receivable Invoice~with Notes | System.Invoice_AR |
| 23—Receivable Invoice~Holdback | System.Invoice_AR_Holdback |
| 24—Receivable Invoice~Holdback; with Notes | System.Invoice_AR_Holdback |
| 31—Receivable Credit | System.Credit_AR |

The system forms follow a specific naming pattern, for example, **System.Invoice_AR**. For the new report to appear in Sage 100 Contractor in the area in which you would want it to appear, it must be saved with a similar naming scheme. For example, **YourName.Invoice_AR**. You do not need to preserve “System” in the name, you must retain the **.Invoice_AR** in the name. The "System" designation is intended to identify the forms that are included with the program installation. Forms that you create or modify should not include "System" in the name.

Note: Form designs are listed alphabetically in the report form list. To see your new forms listed before the "System" reports, use a name that will appear before the word system.

When you open a system report and save it with a new name, it is saved by default to the **\Report Forms folder**; however, you can choose to save it in a different folder. If you save it to a different folder, it will not appear in the program.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To create a new form using an existing form](javascript:void(0);)

|  | 1 | Open, for example, the **3-2 Receivable Invoices/Credits** window. |
|---|---|---|

|  | 2 | Click the **Print Records** button. |
|---|---|---|

|  | 3 | On the **3-2 Report Printing** window, in the **Report Form** list, click the drop-down arrow and select the form design that you want to edit. |
|---|---|---|

|  | 4 | From the **Edit** menu, select **Form Design**. |
|---|---|---|

|  | 5 | On **13-5 Form/Report Page Design**, edit the form. |
|---|---|---|

|  | 6 | From the **File** menu, select **Save**. |
|---|---|---|

|  | 7 | On the **Save File** window, name the new form and then click **Save**. |
|---|---|---|

Tip:

When you need to make a large number of changes, it might be easier to create a new form from scratch in the

**13-5 Form/Report Page Design**

window.

### Editing existing forms

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To edit an existing form design in 13-5 Form/Report Page Design](javascript:void(0);)

|  | 1 | Open **13-5 Report/Form Page Design**. |
|---|---|---|

|  | 2 | Select **File > Open**. |
|---|---|---|

|  | 3 | Do one of the following in the Select a Report Form window: |
|---|---|---|

|  | a | Select the [**Display Private Report Forms**] button to select from a list of forms stored on your local drive that only you have access to. These forms are stored in the \Users\Username\AppData\Local\Sage\Sage 100 Contractor\Custom Reports folder. |
|---|---|---|

|  | b | Select the [**Display Shared Report Forms**] button to select from a list of forms stored on a shared drive that all users have access to. |
|---|---|---|

|  | c | Select the [**Display System Report Forms**] button to select from a list of system forms that you may customize. |
|---|---|---|

|  | 4 | Select the form design that you want to edit. |
|---|---|---|

|  | 5 | On the **13-5 Form/Report Page Design** window, edit the form. |
|---|---|---|

|  | 6 | Select **File > Save** and save as a shared form design or as a private form design, depending on your preference. |
|---|---|---|

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To edit an existing form design from a Report Printing window](javascript:void(0);)

|  | 1 | Open any **Report Printing** window, for example **3-2 Receivable Invoices/Credits**. |
|---|---|---|

|  | 2 | Click the **Print Records** button. |
|---|---|---|

|  | 3 | Select the form design that you want to edit. |
|---|---|---|

|  | 4 | From the **Edit** menu, select **Form Design**. |
|---|---|---|

|  | 5 | On the **13-5 Form/Report Page Design** window, edit the form. |
|---|---|---|

|  | 6 | Select **File > Save** and save as a shared form design or as a private form design, depending on your preference. |
|---|---|---|

### Previewing forms

#### To preview a form within 13-5 Form/Report Page Design:

|  | 1 | From the **13-5 Form/Report Page Design** window, select **Pages > View Page**. |
|---|---|---|

#### To preview a form from within a Report Printing window:

|  | 1 | Open the report and select the Report Form for preview. |
|---|---|---|

|  | 2 | Select **Edit > Form Design**. |
|---|---|---|

|  | 3 | Select **Pages > View Page**. |
|---|---|---|

#### Reducing the document size when previewing forms

When previewing a form, you can reduce the size of a document displayed in the **Screen Review** window.

In the

**Screen Review**

window, select

**View Options**

, then select the percentage size (100%, 85%, 70%, or 50%) at which you want to view the report.
