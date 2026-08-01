<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/4-Accounts_Payable/About_vendor_invoice_defaults.htm (Sage 100 Contractor help v20.5) -->

### About vendor invoice defaults

The information you provide on the **Invoice Defaults** tab helps Sage 100 Contractor post an invoice and create the job cost records.

| Default | What it does |
|---|---|
| Due Terms | Determines the date by which payment is due. In Sage 100 Contractor, a cycle is represented by ##DY (a number of days), ##MO (a number of months), and ##TH (a specified day every month). You replace the ## symbols with the number of days or months, or the day of the month for the processing cycle. For example: **30DY** means due every 30 days. **02MO** means due every two months. **25TH** means due on the 25th day of each month. Sage 100 Contractor displays the 25th of the month following the invoice date when you enter a new invoice for a vendor |
| Discount Terms | Determines the date by which payment is due for your business to receive a discount. |
| Discount Rate | Determines the discount rate for early payment. |
| Work Comp Rate | Sets up the vendor record of a subcontractor with the employer’s compensation rate. When entering the payable invoice, you can charge the subcontractor for coverage based on the invoiced amount. The charge appears as a credit on the subcontractor’s invoice. |
| Ledger Account | Determines the default ledger account to which invoices are posted. For a materials supplier, for example, enter the materials expense account number. When you enter a payable invoice, the material expense account defaults to the grid. Some vendors may not post to one account regularly. If there is not a common account used by a vendor, leave the **Ledger Account** box blank. |
| Cost Code | Determines the cost code to which you post the vendor. Because cost codes may vary each time you post a record, consider leaving the **Cost Code** box blank. Alternately, you can enter the lowest numbered cost code used by the vendor. You can then use the **Lookup** window to display cost codes starting in the appropriate area. |
| Cost Type | Determines the cost type to which you post the vendor. Usually the cost type corresponds to the ledger account. |
| Invoice Status | If you want to review all invoices or payments for a vendor, assign the vendor record Invoice status **2-Review**. Otherwise, Sage 100 Contractor assigns status **1-Open**. |
| Purchase Order Warning | Restricts the ability to save payable invoices. |
| Allow Duplicate Invoice Number | Lets you enter duplicate invoice numbers for a vendor. The **Invoice Number** text box in the **Payable Invoices** window can be set up to require a unique invoice number. The **Allow Duplicate Invoice Number** check box lets you supersede the requirement for a unique invoice number for specific vendors such as the phone company. |
| Separate cheque for each invoice | Tells the system to print separate cheques for each invoice for each vendor. |
| Put on the Hot List | Automatically puts the vendor's invoices on the Hot List. |

| Links to more information . . . [About other vendor defaults](About_other_vendor_defaults.md) [About cost codes](../6-Project_Management/About_cost_codes_and_divisions.md) [About purchase order warnings](About_purchase_order_warnings.md) |
|---|
