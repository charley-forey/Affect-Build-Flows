<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/13-Review_and_Reporting/About_using_If___Then___Else____in_a_calculated_field.htm (Sage 100 Contractor help v20.5) -->

### About using If( )Then( )Else( ) in a calculated field

The **If( )Then( )Else( )** operator enables you to conditionally return a value. Within the parentheses of the **If( )Then( )Else( )** expression, you enter the fields, functions, and constants.

```
Syntax: If( expression )Then( result1 )Else( result2 )
```

- Expression is the condition for which you are testing.
- Result1 is returned when the condition in the expression is met.
- Result2 is returned when the condition in the expression is not met.

#### **Example:**

A **Trial Balance** report uses calculated fields containing the **If( )Then( )Else( )** operator. The expression

```
If(LGRACT.DBTCRD=1)Then(LGRACT.BEGBAL)Else( )
```

determines whether a ledger account maintains a debit balance. If the ledger account is a debit account, Sage 100 Contractor prints the ledger account’s beginning balance on the report in place of the field. Otherwise, the account is not a debit account and Sage 100 Contractor does not print the balance.

When you set up the ledger account structure, Sage 100 Contractor assigns a value of 1 to debit accounts and a value of 2 to credit accounts. Sage 100 Contractor stores the debit/credit value in a table, which you can query using the LGRACT.DBTCRD field.

In the above example, the **If( )** portion of the expression queries the debit or credit value of each ledger account. If the LGRACT.DBTCRD field returns a value of 1 for a ledger account, Sage 100 Contractor acts on the field indicated in the Then( ) portion of the expression, printing the beginning balance for the ledger account indicated by the LGRACT.BEGBAL field.

However, if the LGRACT.DBTCRD field returns a value not equal to 1, Sage 100 Contractor acts on the **Else( )** portion of the expression. In the example above, **Else()**does not contain a value; therefore, Sage 100 Contractor does not return anything.

| Links to more information . . . [About operators](About_operators.md) [About parentheses](About_parentheses.md) [About fields](About_fields.md) [About functions](About_functions.md) [About constants](About_constants.md) [About Structured Query Language](About_Structured_Query_Language.md) |
|---|
