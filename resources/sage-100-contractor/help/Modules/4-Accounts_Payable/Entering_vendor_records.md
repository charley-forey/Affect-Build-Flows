<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/4-Accounts_Payable/Entering_vendor_records.htm (Sage 100 Contractor help v20.5) -->

### Entering vendor records

Consider these points before entering vendor records:

- Be sure to enter all the important information regarding vendors. Entries made in the **4-4 Vendors (Accounts Payable)** window are used for other functions, such as fax and email scheduling.
- Select the **Internal Vendor** check box to mark the vendor as an internal supplier, which only affects vendor reports.
- Select the **Separate cheque for each invoice** check box to tell the system to print separate cheques for each invoice for each vendor.

Important! Sage 100 Contractor uses information entered in the **3-6 Receivable Clients** window and **4-4 Vendors (Accounts Payable)** window for other functions such as scheduling and sending faxes and email messages. If fax numbers and email addresses for vendors are not entered in these windows, then client and vendor contacts do not appear on the fax and email distribution lists.

#### To enter a vendor:

|  | 1 | Open **4-4 Vendors (Accounts Payable)**. |
|---|---|---|

|  | 2 | In the data control text box, enter the vendor number. |
|---|---|---|

|  | 3 | In the **Vendor Name** text box, enter the full vendor name. |
|---|---|---|

|  | 4 | In the **Short Name** text box, enter a brief name for the vendor. |
|---|---|---|

|  | 5 | In the **Vendor Type** list, click the vendor type. |
|---|---|---|

|  | 6 | In the **General Information** tab: |
|---|---|---|

|  | a | In the **Owner** text box, enter the name of the person to contact at the vendor’s office. |
|---|---|---|

|  | b | In the **Address 1**, **Address 2**, **City**, **Province**, and **Postal** text boxes, enter the address. |
|---|---|---|

|  | c | In the **User Def1** and **User Def2** text boxes, enter the [user-defined information](../7-Utilities/About_setting_field_properties.md) as necessary. |
|---|---|---|

|  | 7 | In the **Financial Information** tab: |
|---|---|---|

|  | a | In the **T5018 ID#** text box, enter the vendor’s federal identification number. |
|---|---|---|

|  | b | In the **GST/HST ID#** text box, enter the vendor’s GST/HST number. |
|---|---|---|

|  | c | In the **Account#** text box, enter your account number the vendor uses to identify your company. |
|---|---|---|

|  | d | In the **License#** text box, enter the contractor’s license number. |
|---|---|---|

|  | e | In the **Resale#** text box, enter the vendor’s resale number. |
|---|---|---|

|  | f | In the **T5018 Type** list, select the type of GST/HST report required for this vendor. |
|---|---|---|

|  | 8 | As necessary, select the **Internal Vendor** check box. |
|---|---|---|

|  | 9 | Click the **Invoice Defaults** tab, then: |
|---|---|---|

|  | a | In the **Due Terms** text box, enter the cycle for the date when the invoice is due. In Sage 100 Contractor, a cycle is represented by ##DY (a number of days), ##MO (a number of months), and ##TH (a specified day every month). You replace the ## symbols with the number of days or months, or the day of the month for the processing cycle. For example:**30DY** means due every 30 days. **02MO** means due every two months.**25TH** means due on the 25th day of each month. Sage 100 Contractor displays the 25th of the month following the invoice date when you enter a new invoice for a vendor |
|---|---|---|

|  | b | In the **Discount Terms** text box, enter the cycle for the date by which the vendor must receive payment for the discount to apply. |
|---|---|---|

|  | c | In the **Discount Rate** text box, enter the discount rate. |
|---|---|---|

|  | d | In the **Work Comp Rate** text box, enter the workers' compensation rate. |
|---|---|---|

|  | e | In the **Tax Code Override** text box, if the vendor is not subject to the primary tax code for the vendor's province, enter the tax code for this vendor. (Leave this box blank if you want to use the primary tax code as the default for new transactions for the vendor.) |
|---|---|---|

|  | f | In the **Ledger Account** text box, enter the ledger account to which you want to post. |
|---|---|---|

|  | g | In the **Cost Code** text box, enter the default cost code. |
|---|---|---|

|  | h | In the **Cost Type** list, click the default cost type to assign. |
|---|---|---|

|  | i | In the **Invoice Status** list, click the status to assign an invoice or credit. |
|---|---|---|

|  | j | In the **PO Warning** list, click the warning status you want to assign to the vendor. |
|---|---|---|

|  | k | If you need to send a separate cheque for each invoice, select the **Separate cheque for each invoice** check box. |
|---|---|---|

|  | l | If you want to automatically put the vendor's invoices on the Hot List, select the **Put on the Hot List** check box. |
|---|---|---|

|  | m | If you want to allow duplicate invoice numbers, select the **Allow duplicate invoice numbers** check box. |
|---|---|---|

|  | 10 | Click the **Other Defaults** tab, then: |
|---|---|---|

|  | a | In the **RFP Type** list, click the type of RFP you often create for the vendor. |
|---|---|---|

|  | b | In the **Description** text box, enter the default description for RFPs. |
|---|---|---|

|  | c | In the **Purchase Order Type** list, click the type of order you often create for the vendor. |
|---|---|---|

|  | d | In the **Description** text box, enter a brief statement about the purchase order. |
|---|---|---|

|  | e | In the **Subcontract Type** list, click the type of subcontract you often create for the vendor. |
|---|---|---|

|  | f | In the **Description** text box, enter a brief statement about the subcontract. |
|---|---|---|

|  | 11 | Click the **EFTPayment Setup** tab, then do the following: |
|---|---|---|

|  | a | Select the **Enable EFT payment** box. |
|---|---|---|

|  | b | In the **Institution ID#** text box, enter the bank institution's identification number. |
|---|---|---|

|  | c | In the **Branch Routing#** text box, enter the vendor's bank routing number. |
|---|---|---|

|  | d | In the **Bank Account#** text box, enter the vendor's bank account number. |
|---|---|---|

|  | e | In the **Transaction Type** text box, enter the transaction code approved by the CPA Standard 005 in Section E, Appendix 2 or leave the text box blank for a generic vendor payment. |
|---|---|---|

|  | f | In the **Email Receipt to** text box, enter the email address to receive the EFT payment receipt. |
|---|---|---|

|  | 12 | Click the **Contact** grid, do the following: |
|---|---|---|

|  | a | In the **Contact Name** text box, enter the contact's name. |
|---|---|---|

Important! The first contact in the list is considered to be the primary contact in reports.

|  | b | In the **Job Title** text box, enter the contact's job title. |
|---|---|---|

|  | c | In the **Phone#** text box, enter the contact’s telephone number. |
|---|---|---|

|  | d | In the **Extension** text box, enter the contact's telephone extension, as necessary. |
|---|---|---|

|  | e | In the **Email** text box, enter the contact's email address. |
|---|---|---|

|  | f | In the **Cell#** text box, enter the contact’s cellular number. |
|---|---|---|

|  | g | In the **Fax#** text box, enter the contact’s fax number. |
|---|---|---|

|  | h | In the **Other#** text box, enter the contact’s other telephone number. |
|---|---|---|

|  | i | In the **Other Description** text box, enter the contact’s other telephone number description. |
|---|---|---|

|  | j | In the **Notes** text box, enter any applicable notes about the contact. |
|---|---|---|

|  | 13 | Enter the vendor licenses and certificates. |
|---|---|---|

|  | 14 | On the **File** menu, click **Save**. |
|---|---|---|

|  | 15 | If you want to set the vendor's T5018 balance for the calendar year: |
|---|---|---|

|  | a | Refresh the vendor record by clicking the back arrow button (next to the record number in the upper left-hand corner) then clicking the forward arrow button advance to the new record again. |
|---|---|---|

|  | b | Select **Options > T5018 Balance Startup/Adjustment** to open the [T5018 Balance Startup/Adjustment window](About_1099_Balance_Startup_and_Adjustment.md). |
|---|---|---|

|  | c | Select the current date in the **Adjustment Date** box, and then type the vendor's starting T5018 balance in the **T5018 Balance Startup/Adjustment** box. |
|---|---|---|

|  | d | Click [**Save**]. |
|---|---|---|

| Links to more information . . . [Setting up vendor types](Setting_up_vendor_types.md) [About vendor invoice defaults](About_vendor_invoice_defaults.md) [About purchase order warnings](About_purchase_order_warnings.md) [About other vendor defaults](About_other_vendor_defaults.md) [About vendor financial information](About_vendor_financial_information.md) [About vendor certificates and expiration dates](About_vendor_certificates_and_expiration_dates.md) Workers Compensation for subcontractors |
|---|
