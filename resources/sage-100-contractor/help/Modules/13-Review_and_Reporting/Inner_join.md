<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/13-Review_and_Reporting/Inner_join.htm (Sage 100 Contractor help v20.5) -->

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

| Links to more information . . . [Between](Between.md) [About Structured Query Language](About_Structured_Query_Language.md) |
|---|
