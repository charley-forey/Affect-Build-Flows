<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/6-Project_Management/Importing_cost_codes.htm (Sage 100 Contractor help v20.5) -->

### Importing cost codes

If you have a cost code list from another source, you can import it. Arrange the data in the following order: **Cost Code#**, **Description**, **Unit**, **Division**, **Comp Code1**, **Wage Max**, **Comp Code2**, and **Department**. Then save the file in comma delimited (*.cma), tab delimited (*.tab), or comma-quote (*.qte) file format. You can also copy and paste from a spreadsheet using the clipboard (Ctrl+C, Ctrl+V).

Because Sage 100 Contractor uses cost code numbers as the means to access all other cost code information, replacing the existing cost codes can seriously affect the accuracy of many reports. The imported cost codes overwrite existing cost codes. If your active company uses the same cost code numbers as the file you import, the existing cost codes will be overwritten.

Important!

- Before importing a file from other software, you must create a compatible comma-delimited, tab-delimited, comma-quote file using a spreadsheet program, word processing program, or other software.
- You must import the **Cost Divisions** separately before you import the **Cost Codes**.
- When importing cost codes into a company with existing cost divisions, use a placeholder in your import file to avoid overwriting information in the **Division** column. A placeholder in a comma-delimited file would be, for example, a comma, two quotation marks, and another comma (," ",).

#### To import cost codes:

1. Open **6-5 Cost Codes**.
2. On the **File** menu, point to **Open**, and then select the type of file to import.
3. In the **Open** window that appears:
   
   1. Browse to and then select the file to import.
   2. Click **Open**. Sage 100 Contractor imports the cost codes.
4. Click **Save**.

| Links to more information . . . [Entering divisions](Entering_divisions.md) [Importing cost divisions](Importing_cost_divisions.md) |
|---|
