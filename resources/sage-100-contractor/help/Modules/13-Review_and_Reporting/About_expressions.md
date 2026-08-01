<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/13-Review_and_Reporting/About_expressions.htm (Sage 100 Contractor help v20.5) -->

### About expressions

An expression is a formula used to compute the value of a calculated field. An expression can contain fields, constants, operators, and functions.

The examples below help illustrate the syntax of expressions:

- To calculate the year-to-date activity for a ledger account, the following expression subtracts the beginning balance from the ending balance:  
  **LGRACT.ENDBAL-LGRACT.BEGBAL**
- You can create a single field that inserts the employee’s last name, followed by an ampersand, and the first name. When you generate the report, Sage 100 Contractor adjusts the placement of the first name relative to the length of the last name:  
  **EMPLOY.LSTNME&EMPLOY.FSTNME**
- The following expression inserts the ledger account number and the ledger account long name. When you generate the report, Sage 100 Contractor adjusts the placement of the long name relative to the length of the ledger account number:  
  **LGRACT.RECNUM LGRACT.LNGNME**

| Links to more information . . . [About operators](About_operators.md) [About parentheses](About_parentheses.md) [About using If( )Then( )Else( ) in a calculated field](About_using_If___Then___Else____in_a_calculated_field.md) [About variables in calculated fields](About_variables_in_calculated_fields.md) |
|---|
