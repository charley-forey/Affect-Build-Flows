<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/13-Review_and_Reporting/Tools_for_Building_Form_Designs.htm (Sage 100 Contractor help v20.5) -->

### Tools for Building Form Designs

You can use the following tools for building form designs:

- Lines
- Boxes
- Logos, Pictures, and Objects
- Fields

Note: To undo changes to a form, on the **Edit** menu, click **Undo**.

#### To move a selection:

|  | 1 | In **13-5 Form/Report Page Design**, open the form in which you want to move a selection. |
|---|---|---|

|  | 2 | Select the item you want to move. |
|---|---|---|

|  | 3 | Drag the selection to the desired location. |
|---|---|---|

|  | 4 | To move multiple selections at the same time, hold down the [**Ctrl**] key and drag the mouse over the objects to be selected. |
|---|---|---|

### Lines

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To draw a line](javascript:void(0);)

|  | 1 | In **13-5 Form/Report Page Design**, open the form in which you want to draw a line. |
|---|---|---|

|  | 2 | In the **Insert** menu, click **Line**. |
|---|---|---|

|  | 3 | In the status bar area, select the line width and type of line you want to draw. |
|---|---|---|

|  | 4 | Click in the grid to draw the line and drag the pointer. |
|---|---|---|

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To set the line color](javascript:void(0);)

|  | 1 | In **13-5 Form/Report Page Design**, select the line on which to change the color. |
|---|---|---|

|  | 2 | In the **Edit** menu, click **Color**. |
|---|---|---|

|  | 3 | Click the color you want to use. |
|---|---|---|

|  | 4 | Click **OK**. |
|---|---|---|

### Boxes

Note: You can insert a text box directly inside a box or detail area box, or drag an existing text box and drop it into a box or detail area box.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To draw a box](javascript:void(0);)

|  | 1 | In **13-5 Form/Report Page Design**, open the form in which you want to draw a box. |
|---|---|---|

|  | 2 | On the **Insert** menu, click **Box**. |
|---|---|---|

|  | 3 | Click in the location where you want to place one corner of the box and drag the pointer diagonally to the size you want. |
|---|---|---|

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To create a detail area box](javascript:void(0);)

The detail box determines where the body of the report appears on a form design when you generate the report.

|  | 1 | In **13-5 Form/Report Page Design**, open the form in which you want to create a detail area box. |
|---|---|---|

|  | 2 | On the **Insert** menu, click **Detail Area**. |
|---|---|---|

|  | 3 | Click in the location where you want to place one corner of the detail area box and drag the pointer diagonally to the size you want. |
|---|---|---|

### Logos, Pictures, and Objects

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To insert a picture or logo](javascript:void(0);)

|  | 1 | In **13-5 Form/Report Page Design**, open the form into which you want to insert a graphic. |
|---|---|---|

|  | 2 | On the **Insert** menu, click **Picture**. |
|---|---|---|

|  | 3 | The **Assign Picture** dialog box appears. |
|---|---|---|

|  | 4 | Select the bitmap file that you want to insert. |
|---|---|---|

|  | 5 | Click **Open**. |
|---|---|---|

|  | 6 | On the **Edit** menu, click **Select Objects**, then click the picture and move to the appropriate area on the form. |
|---|---|---|

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To add a company logo to all report forms](javascript:void(0);)

This procedure adds a company logo to all report forms that share the same logo. The sample logo available in Sage 100 Contractor calls one specific file from the \Report Forms folder and inserts it in all reports that display a logo. You can rename your logo file to this name and it will be displayed in those reports automatically.

Important! You may need to stretch or shrink your logo on the reports.

|  | 1 | Using Windows Explorer, navigate to the \Program Files (or Program Files (x86))\Sage\Sage 100 Contractor\Report Forms folder on the local drive where you installed Sage 100 Contractor or the drive from which you print. |
|---|---|---|

|  | 2 | Rename the existing sample logo from logo.bmp to originallogo.bmp. |
|---|---|---|

|  | 3 | Copy your own logo file into the folder, and rename it logo.bmp. |
|---|---|---|

|  | 4 | Your logo will now automatically display in reports that use a logo. |
|---|---|---|

Note: If you re-install Sage 100 Contractor, Sage 100 Contractor saves the logo.bmp file with the most recent date. It will not overwrite your file.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To adjust the proportions of a picture or object](javascript:void(0);)

|  | 1 | In **13-5 Form/Report Page Design**, open the form in which you want to reproportion a graphic or object. |
|---|---|---|

|  | 2 | Drag the picture in the direction that you want to stretch or shrink it. |
|---|---|---|

|  | 3 | Click the image to change its proportions. |
|---|---|---|

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To delete an object](javascript:void(0);)

|  | 1 | In **13-5 Form/Report Page Design**, open the form in which you want to delete an object. |
|---|---|---|

|  | 2 | Click the object or text block that you want to delete. |
|---|---|---|

|  | 3 | Right click on the object or text box, then click **Delete**. |
|---|---|---|

### Fields

Fields are special codes that instruct Sage 100 Contractor to replace the field with information from a database. For example, you might want to include the job number on a report for payable invoices. You can insert the **ACPINV.JOBNUM** field in the report design. Then, when you generate the report, Sage 100 Contractor fills in the appropriate information for you.

With fields, you can create form designs and report designs to automatically add or update information in your reports and documents. Fields provide you access to data throughout Sage 100 Contractor. Because you can place fields in both report designs and form designs, you need to determine which fields are necessary and then decide where to insert them. It is a good idea to place most all fields in the report design if possible, as this lets you reuse a small number of form designs for a variety of reports.

Like other objects in a form or report design, you can set object properties for fields. When you generate a report or document, Sage 100 Contractor inserts the information indicated by the field. If the database does not contain information requested by the field, Sage 100 Contractor leaves the field blank in the resulting report or document. However, you can set the property of a field to print a zero rather than leaving the field blank.

Notes:

- For each field you want to insert, create a new text box.
- You can format text or graphics by setting the object properties.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To insert fields](javascript:void(0);)

|  | 1 | In **13-5 Form/Report Page Design**, open the form into which you want to insert fields. |
|---|---|---|

|  | 2 | On the **Insert** menu, click **Text**. |
|---|---|---|

|  | 3 | Insert the pointer where you want to place the text. |
|---|---|---|

|  | 4 | On the **Insert** menu, click **Fields**. |
|---|---|---|

|  | 5 | In the **Tables by Menu** section, click the table that you want to use. |
|---|---|---|

|  | 6 | In the **Fields in {table name}** section, double-click the field that you want to use. |
|---|---|---|
