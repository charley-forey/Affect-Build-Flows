<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/13-Review_and_Reporting/Creating_new_forms_using_existing_forms.htm (Sage 100 Contractor help v20.5) -->

### Creating new forms using existing forms

If you have to make only a few changes or additions to a form, it can be easier to create a new form from an existing one than to create a form from scratch.

For example, in the **3-2 Report Printing** window, on the **Report Criteria** tab, you see a list of reports. When you click a report in the **Report Criteria** list, the form on which the report is based is displayed in the **Report Form** drop-down list.

| Report | Report Form |
|---|---|
| 21—Receivable Invoice | System.Invoice_AR |
| 22—Receivable Invoice~with Notes | System.Invoice_AR |
| 23—Receivable Invoice~Holdback | System.Invoice_AR_Holdback |
| 24—Receivable Invoice~Holdback; with Notes | System.Invoice_AR_Holdback |
| 31—Receivable Credit | System.Credit_AR |

The system forms follow a specific naming scheme, for example, System.Invoice_AR. Follow this naming scheme when saving new reports to ensure that they appear in consistent and predictable locations in Sage 100 Contractor. For example, you could save a report as YourName.Invoice_AR. You should not use “System” when naming new or modified reports, but you must retain the ".Invoice_AR". (The "System" designation is to identify forms that are included with the program installation.)

Note: Form designs are listed alphabetically in the report form list. To see your new forms listed before the "System" reports, use a name that will appear before the word system.

When you open a system report and save it with a new name, it is saved by default to the \\ServerName\Sage100Contractor\Custom Reports folder. You can save it in a different folder. However, if you save it to a different folder, it will not appear in the program.

Tip: If you need to make a large number of changes to a form, it might be easier to create a new form from scratch in the **13-5 Form/Report Page Design** window.

#### To create a new form using an existing form:

1. Open an application window, for example, **3-2 Receivable Invoices/Credits**.
2. Click the [**Print Records**] button.
3. On the **3-2 Report Printing** window, in the **Report Form** list, click the drop-down arrow, and then select the form design that you want to edit.
4. Click **Edit** > **Form Design**.
5. On **13-5 Form/Report Page Design**, edit the form.
6. Click **File** > **Save**.
7. On the **Save File** window, name the new form, and then click [**Save**].

| Links to more information . . . [Creating new forms](Creating_new_forms.md) [Editing existing forms](Editing_existing_forms.md) [Undoing changes in forms](Undoing_changes_in_forms.md) [Previewing forms](Previewing_forms.md) |
|---|
