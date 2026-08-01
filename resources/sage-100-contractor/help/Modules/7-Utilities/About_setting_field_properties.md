<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/7-Utilities/About_setting_field_properties.htm (Sage 100 Contractor help v20.5) -->

### About setting field properties

You open the **Field Properties** window by pressing the F7 key when you are using a data entry window, for example, **4-2 Payable Invoices/Credits**. Using the **Field Properties** window, you can set up the default properties for almost any text box, check box, grid cell, or column within a window. You can set the following options:

- **Default Entry to.**Provides a list of entries from which you can select the default. Enter the default data, or click the item in the list you want to appear as the default entry.
- **Permit Access to.** Lets you select which user groups have access to a window, text box, list, or grid column. If no user groups are selected, then all user groups have access. If the user groups appear shaded, then you cannot restrict access.
  
  - When a user group is not granted access to a window, that user group cannot open the window. In addition, the user group cannot access the information by printing documents or reports.
  - When a user group is not granted access to a text box or list, that user group cannot enter or access information in that text box or list, or access the information using a query, quick list, or **Lookup** window. In addition, the user group cannot access the information by printing documents or reports.
  - When a user group is not granted access to a grid column, that grid column is hidden from view and is not accessible by the user group. In addition, the user group cannot access the information by printing documents or reports.
- **Skip During Entry.**During data entry, Sage 100 Contractor skips over the field or list. You can still enter data when you select it.
- **Require Entry.**Requires an entry, or Sage 100 Contractor will not save the record.
- **Require List Match.**Requires that the entry match an item on the **Quick List**.
- **Require Unique.**Prevents users from entering duplicate information. This is available for indexed text boxes that let you enter character-based information.
  
  - When you select this property for the **Invoice#** box in **3-2 Receivable Invoices**, **6-6-1 Purchase Orders**, or **6-7-1 Subcontracts**, Sage 100 Contractor ignores records that have status **5-Void**.
  - When you select this property for the **Work Order** and **Invoice#**boxes in **11-2 Work Orders/Invoices/Credits**, Sage 100 Contractor ignores records that have status **5-Void**.
  - When you select this property for the **Invoice#** box in **4-2 Payable Invoices**, Sage 100 Contractor ignores records that have status **5-Void** for a given vendor. You can set up a vendor to use duplicate invoice numbers.
- **Lock After Save.**Prevents users from editing the information after saving the record. Only a company administrator can edit the information.
- **Lock Quick List.**Prevents users from editing a **Quick List**. Only a company administrator can edit the information.
- **Check Spelling.**Checks the spelling when you move to another text box or cell. If Sage 100 Contractor finds a misspelled word, it displays the **Spelling** dialog box.
- **Mixed Case.**Allows text entry in upper and lower case.
- **Upper Case.**Displays text only in upper case.
- **Lower Case.**Converts entry to lower case text.
- **User Defined Field Type.**Lets you select the type of information the field accepts.
- **System Description.**Displays the default description of the field.
- **User Description.**Lets you change the description of the field. To display the system description again, delete the user description.
- **System Prompt.**Displays the default prompt that appears in the status bar at the bottom of the window.
- **User Prompt.**Allows you to change the default prompt in the status bar at the bottom of the window. When the user prompt is deleted, the system prompt is restored.

| Links to more information . . . [About security groups](About_security_groups.md) [About user-defined fields](../../Appendices/A-Sage_100_Contractor_Features/About_user-defined_fields.md) [About Quick Lists](../../Appendices/A-Sage_100_Contractor_Features/About_Quick_Lists.md) [Setting up properties for text boxes-lists-check boxes-columns and the Dashboard](Setting_up_properties_for_text_boxes__lists__check_boxes__columns__and_the_Dashboard.md) [About vendor invoice defaults](../4-Accounts_Payable/About_vendor_invoice_defaults.md) [About the company administrator](About_the_company_administrator.md) |
|---|
