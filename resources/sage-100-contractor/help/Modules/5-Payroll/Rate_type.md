<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/5-Payroll/Rate_type.htm (Sage 100 Contractor help v20.5) -->

### Rate type

**Rate Type** determines if the rate is a percentage or dollar amount.

| Rate Type | Description |
|---|---|
| 0-None | The rate type is set to none. |
| 1-Dollar amount | The amount is in dollars. |
| 2-Percent of net pay | The amount is a percentage of the total. |
| 3-Remainder of cheque | The amount is whatever is left over from the other designated deposits. |

Note: The four lines of **Direct Deposit** are read by Sage 100 Contractor according to **Rate Type** first. It looks first at **1-Dollar amount**, then **2-Percent of net pay**, and last, **3-Remainder of cheque**. If all lines are set to **1-Dollar amount**, Sage 100 Contractor looks at the lines in order from top to bottom.

| If… | Then... |
|---|---|
| It is a single row entry and the **Rate Type** is **2-Percent of Net**… | …The **Rate** must equal 100%. |
| It is a multiple row entry and the **Rate Type** is **2-Percent of Net**… | …The **Rate** must equal 100 or the last row must be set to **Remainder of Cheques**. |
| It is a single row entry and the **Rate Type** is **1-Dollar Amount**… | …A second row must be created and set to **Remainder of Cheques**. |
| It is a single row entry and the **Rate Type** is **3-Remainder of Cheques**… | …The system assumes this is the entire cheque. |

| Links to more information . . . [Use Direct Deposit check box](Use_Direct_Deposit_check_box.md) [Rate](Rate.md) |
|---|
