<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/13-Review_and_Reporting/About_SQL_syntax.htm (Sage 100 Contractor help v20.5) -->

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

#### **Example**

If you store information in the user-defined fields in **7-1 Company Information**, you can use an SQL query to extract the information.

```
Syntax: Select USRDF1 From CMPANY
```

Queries follow these specific guidelines:

- Brackets [ ] let you create separate SQL expressions and perform mathematical operations on them.
- In the query expression, you can use the equal to (=), greater than (>), or less than (<) signs to test for a value returned by the field.
- Use mathematical operators such as addition (+), subtraction (–), multiplication (*), or division (/) between two or more SQL queries to create a single expression. Use the operators to combine two or more embedded queries.

| Links to more information . . . [Between](Between.md) [Inner join](Inner_join.md) [About operators](About_operators.md) |
|---|
