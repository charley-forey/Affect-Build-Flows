<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/13-Review_and_Reporting/Calculated_Fields.htm (Sage 100 Contractor help v20.5) -->

## Calculated Fields

Sage 100 Contractor enables you to create calculated fields and add them to form designs or report designs. A calculated field is a type of field representing an expression. When you generate a report, Sage 100 Contractor determines the result of the calculated field based on information stored in the databases. After creating a calculated field, you can add it to the list of calculated fields available for use in the design.

### Pre-defined calculated fields

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

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To add a calculation to a field](javascript:void(0);)

|  | 1 | Open the report or form to which you want to add the calculation. |
|---|---|---|

|  | 2 | On the toolbar, click the **Calculations** button. |
|---|---|---|

|  | 3 | In the **Calculated Fields** window, locate the **Calculation** text box, then click the drop-down arrow. |
|---|---|---|

|  | 4 | In the **Global Calculated Fields** lookup window, locate and double-click the calculation you want to insert. |
|---|---|---|

Important! The list is much longer than it looks because there is no vertical scroll bar. To locate your calculation, type the first few letters of its name.

|  | 5 | Click the **Add** button, then click **OK**. |
|---|---|---|

|  | 6 | You return to the **Form/Report Page Design** window. |
|---|---|---|

Important:

If you see an **unable to save** message, click **OK** and verify that the calculation has been added.

|  | 7 | Create a text box where you want to add the calculated field. |
|---|---|---|

|  | 8 | On the **Insert** menu, click **Fields**. |
|---|---|---|

|  | 9 | In the **Insert Fields** window, find and select **Calculated Fields**. |
|---|---|---|

|  | 10 | In the **Fields** list, double-click the field you want to insert. |
|---|---|---|

|  | 11 | From the **File** menu, select **Save**. |
|---|---|---|

### Creating calculated fields

When you add the calculated field, its name displays in the **Calculated Fields** list. You can then insert the field as you would insert any other field.[How?](Inserting_calculated_fields_in_reports.md)

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To create a calculated field](javascript:void(0);)

|  | 1 | In either **13-3 Report Writer** or **13-5 Form/Report Page Design**, on the toolbar, select **Edit > Calculated Fields**. |
|---|---|---|

|  | 2 | In the **Calculated Fields** window, in the **Name** text box, enter the name of the calculated field you want to create. |
|---|---|---|

Note: The **Name** text box has a 15 character limit. You can use spaces and special characters in addition to letters and numbers.

|  | 3 | In the **Description** text box, enter a brief description of the field. |
|---|---|---|

|  | 4 | Select **Do Not Total**, if the calculated field should not be totalled. |
|---|---|---|

|  | 5 | Use the **Database Fields**, **Functions**, and **Operators** to build the calculated field expression. |
|---|---|---|

|  | 6 | To save the calculation, click **Save**. |
|---|---|---|

Note: The **Save** button is not available unless all required fields (**Name**, **Description**, and **Calculated Field Expression**) are filled out.

|  | 7 | Click **Close**. |
|---|---|---|

### About expressions

An expression is a formula used to compute the value of a calculated field. An expression can contain fields, constants, operators, and functions.

The examples below help illustrate the syntax of expressions:

- To calculate the year-to-date activity for a ledger account, the following expression subtracts the beginning balance from the ending balance:  
  **LGRACT.ENDBAL-LGRACT.BEGBAL**
- You can create a single field that inserts the employee’s last name, followed by an ampersand, and the first name. When you generate the report, Sage 100 Contractor adjusts the placement of the first name relative to the length of the last name:  
  **EMPLOY.LSTNME&EMPLOY.FSTNME**
- The following expression inserts the ledger account number and the ledger account long name. When you generate the report, Sage 100 Contractor adjusts the placement of the long name relative to the length of the ledger account number:  
  **LGRACT.RECNUM LGRACT.LNGNME**

### Operators

Operators are symbols that represent a type of mathematical or relational process to carry out in an expression. You can select from the following operators:

| Operator | Description |
|---|---|
| + | Addition |
| – | Subtraction |
| * | Multiplication |
| / | Division |
| = | Equal to |
| < > | Not equal to |
| ( ) | Open/close parenthesis. |
| < | Less than |
| > | Greater than |
| <= | Less than or equal to |
| >= | Greater than or equal to |
| & | Ampersand |
| If( )Then( )Else( ) | Tests for a condition. |
| {S} | Inserts a find and replace field for an alphanumeric variable. |
| {N} | Inserts a find and replace field for a numeric variable. |
| {D} | Inserts a find and replace field for a date variable. |
| SQL Queries | Tests for a condition. |

### Parentheses

Using the parentheses, you can group operations in an expression to change the order in which they are performed. Without parentheses, operations are performed in the following order: multiplication/division, addition/subtraction, and relational operations (greater than, less than, not equal to, and so on).

- For example, the expression, 4 + 6 / 2, provides the answer 7, and not 5, because division is performed before addition. When a mathematical expression contains operators that have the same rank, operations are performed left to right. For example, in the expression, 2 + 6 / 3 * 5 – 9, division and multiplication are first performed before the addition and subtraction. The first operation divides 6 by 3, which produces 2. The second operation multiplies 2 by 5, which produces 10. In the third operation, add 2 to 10, which produces 12. In the fourth operation, subtract 9 from 12 to produce 3 as the answer.

By using parentheses, you can change the order of operations in an expression. That is, operations in parentheses are performed first, then operations outside the parentheses are performed.

- For example, the expression, (2 + 6 / 3) * 5 – 9, results in an answer of 11, while the expression, (2 + 6 / 3) * (5 – 9), results in –16 as the answer.

You can also embed parentheses, where operations in the deepest parentheses are performed first.

- For example, the expression, ( (7 + 3) / 2) * 3, contains embedded parentheses. From the example, the first operation is 7 + 3, the second operation is 10 / 2, and the third operation is 5 * 3, which results in 15 as the answer.

### About using If( )Then( )Else( ) in a calculated field

The **If( )Then( )Else( )** operator enables you to conditionally return a value. Within the parentheses of the **If( )Then( )Else( )** expression, you enter the fields, functions, and constants.

```
Syntax: If( expression )Then( result1 )Else( result2 )
```

- Expression is the condition for which you are testing.
- Result1 is returned when the condition in the expression is met.
- Result2 is returned when the condition in the expression is not met.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)**Example**](javascript:void(0);)

A **Trial Balance** report uses calculated fields containing the **If( )Then( )Else( )** operator. The expression

```
If(LGRACT.DBTCRD=1)Then(LGRACT.BEGBAL)Else( )
```

determines whether a ledger account maintains a debit balance. If the ledger account is a debit account, Sage 100 Contractor prints the ledger account’s beginning balance on the report in place of the field. Otherwise, the account is not a debit account and Sage 100 Contractor does not print the balance.

When you set up the ledger account structure, Sage 100 Contractor assigns a value of 1 to debit accounts and a value of 2 to credit accounts. Sage 100 Contractor stores the debit/credit value in a table, which you can query using the LGRACT.DBTCRD field.

In the above example, the **If( )** portion of the expression queries the debit or credit value of each ledger account. If the LGRACT.DBTCRD field returns a value of 1 for a ledger account, Sage 100 Contractor acts on the field indicated in the Then( ) portion of the expression, printing the beginning balance for the ledger account indicated by the LGRACT.BEGBAL field.

However, if the LGRACT.DBTCRD field returns a value not equal to 1, Sage 100 Contractor acts on the **Else( )** portion of the expression. In the example above, **Else()**does not contain a value; therefore, Sage 100 Contractor does not return anything.

### About variables in calculated fields

Variables act as placeholders for actual numeric values. The variables allow you to build calculated fields and save them without having to enter actual figures until you generate the report. When you preview or print a report containing a variable, you assign a numeric value to each variable that you are using. Sage 100 Contractor substitutes the declared values for the variables and computes the results. You can insert a variable for a date ({D}), number ({N}), or alphanumeric string ({S}).

#### {S}

The **{S}** operator lets you insert a variable for an alphanumeric string in the calculated field.

```
Syntax: [variable{S}]
```

- Variable is the variable you want to replace when generating the report.

#### {N}

The **{N}** operator lets you insert a variable for a numeric string in the calculated field.

```
Syntax: [variable{N}]
```

- Variable is the variable you want to replace when generating the report.

#### {D}

The **{D}** operator lets you insert a variable for a date string in the calculated field.

```
Syntax: [variable{D}]
```

- Variable is the variable you want to replace when generating the report.

### Constants

Constants are parameters or values in an expression that do not change.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Constant Example](javascript:void(0);)

Suppose you create an expression for a calculated field that determines the holdback of a payable invoice by multiplying the invoice total times the holdback rate.

The holdback rate .05 is the constant in the expression:

```
ACPINV.INVTTL * .05.
```

### Functions

An expression can contain functions, which perform special operations.

You can use a single function to represent the expression in a calculated field, or you can use functions in a larger expression.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Example—System date in a report](javascript:void(0);)

Suppose you want to include the system date in a report. You create a calculated field called “Todate,” which uses the DATE$ function as the expression, and insert the field in the report design. When you generate the report, Sage 100 Contractor inserts the system date.

You can also embed functions, which lets you nest functions within each other.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Example—Return day of the month](javascript:void(0);)

For example, the expression DAY( DATE$ ) returns only the day of the month. The function DATE$ locates the system date, then the DAY( ) function returns only the value for the day. So, if today’s system date is 03/15/2010, the expression DAY( DATE$ ) returns 15 when you generate the report.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Functions available in Sage 100 Contractor](javascript:void(0);)

| Function | Description |
|---|---|
| ADDINT$ | The ADDINT$ function adds an interval to a date. Syntax: ADDINT$(interval,number,date) Interval is the period of time by which you want to increment a date. Use the following to denote the interval: d = day, w = week, m = month, q = quarter, y = year. Number specifies number of intervals by which you want to increment a date. Date is the date or date field to which the intervals are added. Example: To create a list of payable invoices whose payments are overdue by two days for the given discount date, use the following expression: ADDINT$(d,2,acpinv.dscdte)£DATE$ The expression adds two days to the payable invoice discount date and compares the new value to the system date (today’s date) provided by the DATE$ function. |
| AGED | The AGED function determines if a date falls between two values. Syntax: AGED (date,number1,number2) Date is a date or date field. Number1 and number2 specify the number of days that the date must fall between to return a logical True. A “1” is returned by the AGED function when the date falls within the range and “0” returned when it doesn’t. Example: To create a calculation that checks the age of receivable invoices based on their due dates, use the following expression: AGED(acrinv.duedte, 1, 30) The expression determines if the due date is less than or equal to the system date plus 30 days. |
| CASE | The CASE function conditionally returns a result based on the value of an item. Syntax: CASE(item,value-n,result-n,default) Item is the type of data being checked. Value-n is the value for which the CASE function is searching. Result-n is the result the CASE function returns when the CASE function finds Value-n. Default is the result if the CASE function does not find Value-n. Example: Suppose you want to print or display a description of the payable invoice status. To do this, create the following expression: CASE(acpinv.status,1,Open,2,Review,3, Dispute,4,Paid,Void) The expression includes a value and a result for invoice statuses 1–4. If the data that is returned by the acpinv.status field does not match any of the values, then the expression returns the default found at the end of the expression, Void. |
| DATE$ | The DATE$ function returns the system date. Syntax: DATE$ No additional information is necessary. Example: To print or display the system date when the report was created, insert the following function where you want the date to appear in your report: DATE$ If the system date is 09/05/10, the field returns the value 09/05/2010. |
| DAY | The DAY function returns the number of the day of the month. Syntax: DAY(date) Date is the date field. Example: To print or display the day of the month for a receivable invoice date, use the following expression: DAY(acrinv.invdte) If the date is 09/05/2010, the field returns the value 5. |
| DAY$ | The DAY$ function returns of day of the month as a character string. Syntax: DAY$(number) Number is the number of the day, where 1 through 7 represents Sunday through Saturday. Example: To print or display the day of the week for a fixed date in a schedule, use the following expression: DAY$(schlin.fxddte) If the fixed date 09/05/2010 falls on a Wednesday, the field returns Wednesday. |
| LEFT$ | The LEFT$ function returns a specified number of characters beginning at the left-most character. Syntax: LEFT$(string,number) String is the field that contains the characters you want to select. Number specifies the number of characters you want to select. Example: Suppose you are creating an employee list and you want to include the employee’s first initial and last name. To print or display the first letter of the employee’s first name, use the following expression: LEFT$(employ.fstnme,1) If the employee’s first name is Ron, Sage 100 Contractor returns R. |
| MID$ | The MID$ function returns a number of characters from a character string, starting at a position you specify. Syntax: MID$(string,number1,number2) String is the field that contains the characters you want to select. Number1 specifies the position of the first character. Number2 specifies the number of characters you want to select. Example: Suppose you are creating a lumber list, and you only want to include dimensional lumber that is described in six characters, such as 2x4x20. You do not want to print or display other lumber sizes such as 4x8. MID$(string,1,6) If the string contains six characters, this function returns six-character strings, such as 2x4x20. |
| MONTH | The MONTH function returns the number of the month from a date field. Syntax: MONTH(date) Date is the date field. Example: To print or display the month for a fixed date in a schedule, use the following expression: MONTH(schlin.fxddte) If the fixed date is 09/05/2010, the field returns the value 9. |
| MONTH$ | The MONTH$ function returns the month as a character string. Syntax: MONTH$(number) Number is the number of the month, where 1 through 12 represents January through December. Example: To print or display the month for a fixed date in a schedule, use the following expression: MONTH$(schlin.fxddte) If the fixed date is 09/05/2010, the field returns September. |
| RIGHT$ | The RIGHT$ function returns a specified number of characters beginning at the right-most character. Syntax: RIGHT$(string,number) String is the field that contains the characters you want to select. Number specifies the number of characters you want to select. Example: Suppose you want to create a list of equipment that includes the model year, which you include as the last information in the equipment description: RIGHT$(eqpmnt.eqpnme,4) If the equipment description is Cat 3054T Diesel Engine 2000, Sage 100 Contractor returns 2000. |
| SPELL$ | The SPELL$ function spells out the currency value. Report Writer returns ***VOID*** if the number is zero or a negative. Syntax: SPELL$(number) Number is the number or field you want to spell out. Example: To print or display the payable invoice balance, use the following expression: SPELL$(acpinv.invbal) If the payable invoice balance is $535.00, the field returns FIVE HUNDRED THIRTY FIVE DOLLARS. |
| TRIM$ | The TRIM$ function removes the trailing spaces in a character expression. Syntax: TRIM$(string) String is the field from which you want to remove the trailing spaces. Example: The employee first name field can contain up to 20 characters. If an employee’s first name is Gerald, which contains six characters, the employee first name field would return the name plus 14 empty spaces. TRIM$(employ.fstnme) Using TRIM$ removes the trailing 16 spaces. |
| YEAR | The YEAR function returns the year from a date field. Syntax: YEAR(date) Date is the date field. Example: To print or display the year for a report, use the following expression: YEAR(DATE$) If the system date is 09/05/10, the field returns the value 2010. |

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To edit a calculated field](javascript:void(0);)

Important! You can only edit a calculated field in an existing report containing a calculated field.

|  | 1 | In either **13-3 Report Writer** or **13-5 Form/Report Page Design**, on the toolbar, select **Edit > Calculated Fields**. |
|---|---|---|

|  | 2 | In the **Calculated Fields** window, select the calculation from the **Name**text box list. |
|---|---|---|

|  | 3 | Make the changes you want to the expression. |
|---|---|---|

|  | 4 | Edit the **Name** and **Description** if desired. |
|---|---|---|

|  | 5 | To save the calculation, click **Save**. |
|---|---|---|

|  | 6 | Click **Close**. |
|---|---|---|

Saving calculations to the **Global Calculated Fields** list is a good way to copy a calculation from one report to another. Many calculations are in the **Global Calculated Fields** list, but not all. Here’s how to add the ones you want.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To save a calculated field to the Global Calculated Fields list](javascript:void(0);)

|  | 1 | In **13-3 Report Writer**, open a report that contains the calculation you want to copy. |
|---|---|---|

|  | 2 | Select **Edit > Calculated Fields**. |
|---|---|---|

|  | 3 | In the **Name** field, click the drop-down arrow. |
|---|---|---|

|  | 4 | Click the desired calculation. |
|---|---|---|

|  | 5 | To add the calculation to the Global Calculated Fields list, click **Save to Global Calculations**. |
|---|---|---|

|  | 6 | This adds the desired calculation to the **Global Calculated Fields** lookup window. |
|---|---|---|

Now you can insert the global calculated field into other reports without creating a calculated field for each report. [How?](Inserting_calculated_fields_in_reports.md)

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To delete a calculated field](javascript:void(0);)

|  | 1 | In either **13-3 Report Writer** or **13-5 Form/Report Page Design**, select **Edit > Calculated Fields**. |
|---|---|---|

Note: You cannot delete a calculated field if it is still in use on the report or form you've opened. Remove the object from the report or form first, then delete the calculated field.

|  | 2 | In the **Calculated Fields** window, click the **Name** list and select the calculated field that you would like to delete. |
|---|---|---|

|  | 3 | Click **Delete**. |
|---|---|---|

|  | 4 | Click **OK**. |
|---|---|---|

### About Structured Query Language

With Structured Query Language (SQL), you design expressions to query databases for data that is not available in standard reports or documents. With SQL, you can apply arithmetic operations to select and obtain new data. This can be as simple as adding two different fields together, or as complex as computing the billings in excess for a project.

Before you create an SQL expression, it is important to understand how Sage 100 Contractor uses databases to store information. When you enter information in a window, Sage 100 Contractor stores the information in tables. Depending on the window, Sage 100 Contractor either stores information in one or two tables.

In windows such as **4-3 Vendor Payments**, **3-5 Jobs**, or **3-3-1 Cash Receipts** a single database table exists, containing all the information. In other windows such as **4-2 Payable Invoices** or **3-2 Receivable Invoices**, there are two database tables. When Sage 100 Contractor uses two tables to store data, the first table stores information from the text boxes and lists and the second table stores data from the grid.

### About SQL syntax

The **SQL Queries** operator enables you to return a value that meets specific conditions. Within the **Select From Where** expression, you enter the fields, functions, and constants.

When building an SQL expression, you can use any mathematical or relational operations, as well as language operators. The placement of operators is critical to proper calculation, and some operators are placed before rather than after the fields. The following list describes the language operators you can use in an SQL expression:

| Operator | Description |
|---|---|
| Select | Locates data for the selected field. |
| Select Sum | Locates and totals all figures for the selected field. You can use **Select Sum** in place of the **Select** portion of the expression. |
| From | Indicates the source database. Usually follows the **Select** portion of the expression. |
| Where | Defines the criteria that data must meet for use in the query. Usually follows the **From** portion of the expression. |
| Between | Defines a range of data. The **Between** operator works similar to **>=** and **<=**. (See links) |
| Inner Join | Creates a relationship between two tables. (See links) |

#### Example Syntax:

```
Syntax: Select table1 From table2 Where value
```

- Table1 is the data you want to select.
- Table2 is the table from which you want to select the data.
- Value is the value for which the SQL function is searching.

Important! The syntax for an SQL expression can vary greatly depending on the complexity. The syntax above only outlines a simple SQL expression.

#### **Example:**

If you store information in the user-defined fields in **7-1 Company Information**, you can use an SQL query to extract the information.

```
Syntax: Select USRDF1 From CMPANY
```

Queries follow these specific guidelines:

- Brackets [ ] let you create separate SQL expressions and perform mathematical operations on them.
- In the query expression, you can use the equal to (=), greater than (>), or less than (<) signs to test for a value returned by the field.
- Use mathematical operators such as addition (+), subtraction (–), multiplication (*), or division (/) between two or more SQL queries to create a single expression. Use the operators to combine two or more embedded queries.

### Between

The **Between** operator defines a range of numbers similar to using to >= and <=. The range is inclusive of the two numbers you indicate.

```
Syntax: Between number1 and number2
```

- Number1 is the low number.
- Number2 is the high number.
- **Example:**When you set the range between 5 and 10, the query searches for the numbers 5, 6, 7, 8, 9, and 10.

### Inner join

The **inner join** operator joins two tables and creates a one-to-one relationship between records in the table.

```
Syntax: Table1 Inner Join table2 on string1=string2
```

- Table1 is a table
- Table2 is the table you want to join to table1.
- String1 is a field.
- String2 is the field that you want to relate to string1.

#### **Example:**

Suppose you create a change order report that includes the budgeted costs by job. The job number is found in the **Change Order**table, and the budgeted amounts and cost codes are found in the **Subcontract Change Order Lines** table.
