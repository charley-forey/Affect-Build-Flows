<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/1-General_Ledger/About_voiding_checks.htm (Sage 100 Contractor help v20.5) -->

### About voiding cheques

Important! You cannot void a transaction in a different period than that in which it was originally posted.

When you create an accounts payable, general ledger, or equipment cheque and save it, Sage 100 Contractor posts the cheque to the general ledger. You cannot void these cheques in the **1-3 Journal Transactions** window unless the status is **1-Open**. When you do void a cheque, Sage 100 Contractor assigns the cheque status **3-Void** and adjusts the invoice and vendor balances accordingly. If the cheque was applied to an invoice and the invoice was closed, Sage 100 Contractor reopens the invoice and adjusts the balance to what is due. Best practices in accounting procedures require that you do not void transactions that have been processed by the bank. Therefore, it is not possible to void transactions with a status of **2-Cleared**.

Payroll cheques are processed by Sage 100 Contractor differently from other types of cheques. Therefore, you need to void payroll cheques through the **5-2-2 Payroll Records** window. To void a payroll cheque, void the timecard record that Sage 100 Contractor used to create the cheque. This reverses the amounts applied to the employee quarterly totals and year-to-date totals, and voids the job costs.

| Links to more information . . . [Voiding cheques](Voiding_checks.md) [Reversing general ledger cheques from an archived year](Voiding_general_ledger_checks_from_a_prior_year.md) |
|---|
