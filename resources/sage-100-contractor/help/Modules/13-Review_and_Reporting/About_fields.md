<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/13-Review_and_Reporting/About_fields.htm (Sage 100 Contractor help v20.5) -->

### About fields

Fields are special codes that instruct Sage 100 Contractor to replace the field with information from a database. For example, you might want to include the job number on a report for payable invoices. You can insert the **ACPINV.JOBNUM** field in the report design. Then, when you generate the report, Sage 100 Contractor fills in the appropriate information for you.

With fields, you can create form designs and report designs to add or update information automatically in your reports and documents. Fields provide access to data throughout Sage 100 Contractor. Because you can place fields in both report designs and form designs, you need to determine which fields are necessary and then decide where to insert them. It is a good idea to place most all fields in the report design if possible, as this lets you reuse a small number of form designs for a variety of reports.

Like other objects in a form or report design, you can set object properties for fields. When you generate a report or document, Sage 100 Contractor inserts the information indicated by the field. If the database does not contain information requested by the field, Sage 100 Contractor leaves the field blank in the resulting report or document. However, you can set the property of a field to print a zero rather than leaving the field blank.

| Links to more information . . . [Inserting fields](Inserting_fields.md) [About calculated fields](About_calculated_fields.md) [Setting object properties](Setting_object_properties.md) |
|---|
