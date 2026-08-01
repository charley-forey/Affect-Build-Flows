<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/1-General_Ledger/Finding_and_resolving_unprinted_checks_when_archiving.htm (Sage 100 Contractor help v20.5) -->

### Finding and resolving unprinted cheques when archiving the books

When there is a credit to an account in the cash range with a transaction number of 0000 when you are archiving, Sage 100 Contractor displays a message stating that unprinted cheques were found.

Tip: This message is informational only. It does not stop you from archiving. However, you should resolve the unprinted cheques issue.

#### To find and resolve unprinted cheques:

|  | 1 | Open **2-5 General Journals**. |
|---|---|---|

|  | 2 | Print the **2-5-21 General Journal** report with the following settings: |
|---|---|---|

|  | a | In the **Account**box, use the range for all cash accounts listed in **1-8 General Ledger Setup.** |
|---|---|---|

|  | b | In the **Trans#** box, select **Equal**, and type 0000. |
|---|---|---|

|  | c | In the **Credit** box, select **Greater or =**, and type $0.01. |
|---|---|---|

|  | 3 | If the transaction is an unprinted cheque, open **1-1 Cheques/Bank Charges** and click the **Print Records** button to print the cheque if desired. If you do not need to print a cheque, open **1-3 Ledger Transactions**, and then change the **Trans#** to anything other than 0000. |
|---|---|---|

Note: If it is a **Source 16-Payroll**, click on the **Go To Source** button to change the **Cheques#**. It is highly unusual that the cheque number would have been changed to 0000 unless the paycheque had to be reprinted immediately.

| Links to more information . . . [About customer support and resources](../../Welcome_to_Sage_100_Contractor/Customer_Support_and_Resources.md) [About audit errors](About_audit_errors.md) |
|---|
