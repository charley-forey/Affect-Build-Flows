<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/4-Accounts_Payable/4-4_Vendors__Accounts_Payable_.htm (Sage 100 Contractor help v20.5) -->

## 4-4 Vendors (Accounts Payable)

Vendor records provide quick access to vendor information for payable invoices, T5018 balances, ordering materials, and subcontract management. Create a vendor record for each business that sends you invoices and each business to which you owe money or make regular payments. These vendors may include subcontractors, architects, engineers, and lenders.

In the **4-4 Vendors (Accounts Payable)**window, you can review vendor-related information such as subcontracts, purchase orders, and invoices. You can also record any additional certificates a vendor is required to supply.

- Vendor financial information tab fields
- Vendor invoice defaults tab fields
- Vendor other defaults tab fields
- VendorEFT PaymentSetup fields
- Vendor purchase order warnings
- Vendor types
- Vendor records
- Vendor certifications and expiration dates
- Vendor remittance
- Workers' Compensation rates on vendor records
- Deleting vendors

Important! Sage 100 Contractor uses information entered in the **3-6 Receivable Clients** window and **4-4 Vendors (Accounts Payable)** window for other functions such as scheduling and sending faxes and email messages. If fax numbers and email addresses for vendors are not entered in these windows, client and vendor contacts do not appear on the fax and email distribution lists.

### Internal vendors

You would select the **Internal Vendor** check box to keep track of someone you need in the vendor database, but not someone from whom you get invoices. Flagging a vendor as “internal” causes the program to display a message if you try to enter a payable invoice for that vendor. Examples of internal vendors are architects, engineers, or other professionals who are involved with projects that you work on, but you are not the one contracting with them because you are not the general contractor or owner. You might, however, want to keep that information in the job record. Internal vendors may also be fictitious entities, such as a generic lumber supply or generic tile subcontractor. You might want to use that entity for putting a “type” of vendor on parts for estimating and bid request reasons.

### Vendor financial information fields

| Box | What it does |
|---|---|
| T5018 ID# | The T5018 recipient ID number. If the T5018 type is 1, the T5018 ID# number entered is the individual's Social Insurance Number (SIN). If the T5018 type is 2, the T5018 ID# number entered is the CRA Program Account number. |
| GST/HST ID# | The GST or HST ID number. |
| T5018 Type | Indicates the type of T5018 status. 0—Undetermined 1—Individual 2—Business 3—Do not report |
| Beginning Balance | Displays the beginning balance of outstanding invoices for your current books. You cannot enter or edit an amount in this box. |
| Current Balance | Displays the beginning balance of outstanding invoices for your current books. You cannot enter or edit an amount in this box. |

### Vendor invoice defaults

The information you provide on the **Invoice Defaults** tab helps Sage 100 Contractor post an invoice and create the job cost records.

| Default | What it does |
|---|---|
| Due Terms | Determines the date by which payment is due. In Sage 100 Contractor, a cycle is represented by ##DY (a number of days), ##MO (a number of months), and ##TH (a specified day every month). You replace the ## symbols with the number of days or months, or the day of the month for the processing cycle. For example: **30DY** means due every 30 days. **02MO** means due every two months. **25TH** means due on the 25th day of each month. Sage 100 Contractor displays the 25th of the month following the invoice date when you enter a new invoice for a vendor |
| Discount Terms | Determines the date by which payment is due for your business to receive a discount. |
| Discount Rate | Determines the discount rate for early payment. |
| Work Comp Rate | Sets up the vendor record of a subcontractor with the employer’s compensation rate. When entering the payable invoice, you can charge the subcontractor for coverage based on the invoiced amount. The charge appears as a credit on the subcontractor’s invoice. |
| Tax Code Override | Use this box when you need to assign a tax code to a vendor that is not subject to the primary tax code for the vendor's province. For example, you could assign a tax code that has a zero tax rate to vendors that are tax exempt. (You must first set up the tax code in the **1-8 Canada Sales Tax Setup** window,) Leave this field blank to use the primary tax code for the vendor’s province as the default for new transactions. If the vendor record does not include a province or a tax code override, Sage 100 Contractor does not calculate taxes for the vendor. |
| Ledger Account | Determines the default ledger account to which invoices are posted. For a materials supplier, for example, enter the materials expense account number. When you enter a payable invoice, the material expense account defaults to the grid. Some vendors may not post to one account regularly. If there is not a common account used by a vendor, leave the **Ledger Account** box blank. |
| Cost Code | Determines the cost code to which you post the vendor. Because cost codes may vary each time you post a record, consider leaving the **Cost Code** box blank. Alternately, you can enter the lowest numbered cost code used by the vendor. You can then use the **Lookup** window to display cost codes starting in the appropriate area. |
| Cost Type | Determines the cost type to which you post the vendor. Usually the cost type corresponds to the ledger account. |
| Invoice Status | If you want to review all invoices or payments for a vendor, assign the vendor record Invoice status **2-Review**. Otherwise, Sage 100 Contractor assigns status **1-Open**. |
| Purchase Order Warning | Restricts the ability to save payable invoices. |
| Allow Duplicate Invoice Number | Lets you enter duplicate invoice numbers for a vendor. The **Invoice Number** text box in the **Payable Invoices** window can be set up to require a unique invoice number. The **Allow Duplicate Invoice Number** check box lets you supersede the requirement for a unique invoice number for specific vendors such as the phone company. |
| Separate cheque for each invoice | Tells the system to print separate cheques for each invoice for each vendor. |
| Put on the Hot List | Automatically puts the vendor's invoices on the Hot List. |

### Other vendor defaults

The information you provide on the **Other Defaults** tab helps Sage 100 Contractor create or export records.

| Default | What it does |
|---|---|
| Purchase Order Type | Determines the type of purchase order you normally create for the vendor. |
| Subcontract Type | Determines the type of subcontract you normally create for the vendor. |

### Vendor EFT Payment Setup fields

| Field | Description |
|---|---|
| Institution ID# | Vendor's bank institution identification number. |
| Branch Routing# | Vendor's bank routing number |
| Bank Account Number | Vendor's bank account number. |
| Email Receipt to | The email address to receive the vendor EFT payment receipt. |

### Vendor purchase order warnings

When saving a payable invoice for a vendor, Sage 100 Contractor refers to the selection made in the **Purchase Order Warning** list in the vendor’s record. If the payable invoice does not meet the criteria, Sage 100 Contractor provides you with a warning. These warnings are set on the Invoice Defaults tab of **4-4 Vendors** and warn if there is no PO available for the invoice or you can require a PO for the invoice.

| Status | Description |
|---|---|
| 0-None | Provides no warning. |
| 1-Warn if no PO | Provides a warning if the invoice does not contain a purchase order number, but allows you to save the invoice. |
| 2-Require PO | Requires a purchase order number to save the invoice. |

#### Vendor Invoice Over Purchase Order settings

The **Set Over PO Warning** option in **4-4 Vendors** notifies you if the invoice quantity amount exceeds the purchase order. When you select the **Set Over PO Warning** option in the Options menu, Sage 100 Contractor compares the invoice total amount against the total PO balance. The Vendor Invoice Over Purchase Order warning settings supersedes the settings for Invoice Over Purchase Order warning settings in 4-2. [How?](Entering_settings_for_the_Vendor_Invoice_Over_Purchase_Order_Warning.md)

### Setting up vendor types

You can use vendor types to group or categorize vendors. Types give you the ability to select specific vendors when printing bid requests, vendor lists, or other vendor related documents.

If you create a long list of vendor types, you can simplify it by abbreviating vendor categories. For example, use **M** for material suppliers and **S** for subcontractors in the **Type Name**. For example, the description for a lumber supplier is **M-Lumber**, and an electrical supplier is **S-Electrical**.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To set up vendor types](javascript:void(0);)

1. Open **4-4 Vendors (Accounts Payable)**.
2. Next to the **Vendor Type** list, click the detail button.
3. The **Vendor Type** window opens.
4. In the **Vendor Type#** text box, enter the type number.
5. In the **Type Name** text box, enter a description of the vendor type.
6. Repeat steps 3–5 for each type.
7. On the **File** menu, click **Save**.

### Entering vendor records

Consider these points before entering vendor records:

- Be sure to enter all the important information regarding vendors. Entries made in the **4-4 Vendors (Accounts Payable)** window are used for other functions, such as fax and email scheduling.
- Select the **Internal Vendor** check box to mark the vendor as an internal supplier, which only affects vendor reports.
- Select the **Separate cheque for each invoice** check box to tell the system to print separate cheques for each invoice for each vendor.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To add a vendor](javascript:void(0);)

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

|  | a | In the **Federal Id#** text box, enter the vendor’s Federal Identification Number. |
|---|---|---|

|  | b | In the **Province Id#** text box, enter the vendor’s **Province** Identification number. |
|---|---|---|

|  | c | In the **Account#** text box, enter your account number the vendor uses to identify your company. |
|---|---|---|

|  | d | In the **License#** text box, enter the contractor’s license number. |
|---|---|---|

|  | e | In the **Resale#** text box, enter the vendor’s resale number. |
|---|---|---|

|  | f | In the **T5018 Type** list, click the **T5018** status. |
|---|---|---|

|  | 8 | As necessary, select the **Internal Vendor** check box. |
|---|---|---|

|  | 9 | Click the **Invoice Defaults** tab, and then: |
|---|---|---|

|  | a | In the **Due Terms** text box, enter the cycle for the date when the invoice is due. |
|---|---|---|

|  | b | In the **Discount Terms** text box, enter the cycle for the date by which the vendor must receive payment for the discount to apply. |
|---|---|---|

In Sage 100 Contractor, a cycle is represented by ##DY (a number of days), ##MO (a number of months), and ##TH (a specified day every month). You replace the ## symbols with the number of days or months, or the day of the month for the processing cycle. For example:

- **30DY** means due every 30 days.
- **02MO** means due every two months.
- **25TH** means due on the 25th day of each month. Sage 100 Contractor displays the 25th of the month following the invoice date when you enter a new invoice for a vendor

|  | c | In the **Discount Rate** text box, enter the discount rate. |
|---|---|---|

|  | d | In the **Work Comp Rate** text box, enter the workers' compensation rate. |
|---|---|---|

|  | e | In the **Ledger Account** text box, enter the ledger account to which you want to post. |
|---|---|---|

|  | f | In the **Cost Code** text box, enter the default cost code. |
|---|---|---|

|  | g | In the **Cost Type** list, click the default cost type to assign. |
|---|---|---|

|  | h | In the **Invoice Status** list, click the status to assign an invoice or credit. |
|---|---|---|

|  | i | In the **PO Warning** list, click the warning status you want to assign to the vendor. |
|---|---|---|

|  | j | If you need to send a separate cheque for each invoice, select the **Separate cheque for each invoice** check box. |
|---|---|---|

|  | k | If you want to automatically put the vendor's invoices on the Hot List, select the **Put on the Hot List** check box. |
|---|---|---|

|  | l | If you want to allow duplicate invoice numbers, select the **Allow duplicate invoice numbers** check box. |
|---|---|---|

|  | 10 | Click the **Other Defaults** tab, and then: |
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

|  | 11 | Click the **EFTPayment Setup** tab, and then: |
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

|  | 12 | On the **Contact** grid: |
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

|  | 14 | Click **File** > **Save**. |
|---|---|---|

|  | 15 | If you want to set the vendor's T5018 balance for the calendar year: |
|---|---|---|

|  | a | Refresh the vendor record by clicking the back arrow button (next to the record number in the upper left-hand corner), and then clicking the forward arrow button to advance to the new record again. |
|---|---|---|

|  | b | Select **Options >****T5018 Balance Startup/Adjustment** to open the [T5018 Balance Startup/Adjustment window](About_1099_Balance_Startup_and_Adjustment.md). |
|---|---|---|

|  | c | Select the current date in the **Adjustment Date** box; then type the vendor's starting T5018 balance in the **T5018 Balance Startup/Adjustment** box. |
|---|---|---|

|  | d | Click **File** > **Save**. |
|---|---|---|

### Vendor certificates and expiration dates

You can track the expiration dates for Workers’ Compensation, liability insurance, contractor’s licenses, and other required certificates and licenses. When you enter a certificate or license, always enter an expiration date. If you do not have a date, enter one that is obviously expired such as 01/01/1980. Later, you can determine which vendors have insurance or licenses that have expired.

Important! The **4-1-5-31 Vendor Worker's Comp Report** requires that the Workers’ Compensation insurance certificate information be in Row 1 of the **Certificates** window grid.

You can control whether you receive a warning that a certificate has expired when creating a subcontract. You can also stop payment to a vendor if a certificate has expired.

When selecting vendor invoices for payment, you can exclude vendors with expired licenses. You can also print documents that you can send to vendors with expired licenses, requesting the new expiration dates to update your records. When you do not need dates for vendors such as lending institutions, leave the text boxes blank.

#### Reports on vendor certificates and expiration dates

You can run insurance reports to view which vendors have current and/or expired certificates. [How?](../13-Review_and_Reporting/About_report_printing.md)

- **4-1-1-41 Insurance Report**
- **4-1-1-42 Insurance Report~by Vendor Type**
- **4-1-1-43 Insurance Report~Alpha**
- **4-1-1-46 Insurance Report~with Notes**
- **4-1-1-47 Insurance Report~by Vendor Type; with Notes**
- **4-1-1-48 Insurance Report~Alpha; with Notes**

In the **Certificates** window, you can create a list of the certificates a vendor must supply. For example, you might list the Workers’ Compensation insurance certificate, liability insurance certificate, contractor’s license, and hazardous materials certificate.

Because you can generate expired certificate reports based on a specific line number, consider entering the certificates in a specific order for each vendor. For example, Row 1 is the Workers’ Compensation insurance certificate, Row 2 is the liability insurance certificate, and Row 3 is the contractor’s license.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To enter vendor certificates](javascript:void(0);)

|  | 1 | In the **4-4 Vendors** window, display the vendor. |
|---|---|---|

|  | 2 | Click **Options** > **Certificates** |
|---|---|---|

|  | 3 | In the **Description** text box, enter a brief statement about the certificate. |
|---|---|---|

For example, type Workers’ Compensation.

|  | 4 | In the **Received** text box, enter the date you received the certificate. |
|---|---|---|

|  | 5 | In the **Expires** text box, enter the date when the certificate has expired. |
|---|---|---|

|  | 6 | In the **Warning** text box, type Y if you want to receive a warning. Type N if you do not want to receive a warning even though the certificate has expired. |
|---|---|---|

The **Warning** column lets you control whether you receive a warning when creating a subcontract for a vendor with an expired certificate. You must select **Exclude Vendors with Overdue Certificates** or **Warn on Vendors with Overdue Certificates** in the **4-3 Vendor Payments** window. To activate these options, click the **Selection** button in **4-3 Vendor Payments**.

|  | 7 | In the **Stop Pay** text box, type Y to stop payments to the vendor when the certificate expires. Type N if you want to pay the vendor even though the certificate has expired. |
|---|---|---|

The **Stop Pay** column lets you control payments to the vendor by accessing the **Invoice Selection** window from the **4-3 Vendor Payments** window. In the **Invoice Selection** window, you must also select **Exclude Vendors with Overdue Certificates** in order to exclude those vendors who meet the expiration criteria from receiving payment. It does not affect payments through the **1-1 Cheques/Bank Charges** window.

|  | 8 | Repeat steps 3–7 for each certificate. |
|---|---|---|

|  | 9 | Click **File** > **Save**. |
|---|---|---|

### Setting up vendor remittance

Occasionally, it is necessary to substitute a different name on a vendor cheque. In the **Vendor Remit** window, you can add more lines to the grid by clicking in the last cell in the last row and pressing the ENTER key.

When you print the vendor cheques, Sage 100 Contractor looks to the vendor remit table. If the vendor appears in the table, Sage 100 Contractor uses the payee information from the table in place of the information from the vendor record.

#### To set up vendor remittance:

|  | 1 | Open **4-4 Vendors (Accounts Payable)**. |
|---|---|---|

|  | 2 | Click **Options** > **Vendor Remit** on the menu. |
|---|---|---|

The **Vendor Remit Information** window opens.

|  | 3 | For each vendor you want to include: |
|---|---|---|

|  | a | In the **Vendor** cell, enter the vendor number. |
|---|---|---|

|  | b | In the **Payee Remit** cell, enter the payee’s name. |
|---|---|---|

|  | c | In the **Address 1** cell, enter the payee’s address. |
|---|---|---|

|  | d | In the **Address 2** cell, enter any remainder of the payee’s address, if necessary. |
|---|---|---|

|  | e | In the **City/Province** cell, enter the payee’s city and province. |
|---|---|---|

|  | f | In the **Postal** cell, enter the payee’s postsal code. |
|---|---|---|

|  | 4 | Click **File** > **Save**. |
|---|---|---|

### Deleting vendors

If a vendor has current year ledger activity or open invoices from a prior year, you cannot delete that vendor.

Caution! When you delete a vendor, all prior year, paid, or void invoices related to that vendor are also deleted. This can affect invoices associated with current jobs. In addition, because the vendor has been deleted, only the vendor number will appear in job cost records.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To delete a vendor](javascript:void(0);)

|  | 1 | Open **4-4 Vendors (Accounts Payable)**. |
|---|---|---|

|  | 2 | Using the data control, select the record. |
|---|---|---|

|  | 3 | On the **Edit** menu, click **Delete Vendor**. |
|---|---|---|

### Setting up Workers Compensation rates for payable invoices

Each province and territory has its own exclusive Workers’ Compensation Board/Commission (WCB). Check with your provincial WCB for compliance requirements, as laws may vary in each province and territory.

Sage 100 Contractor uses the Workers’ Compensation account indicated on the **Payables** tab in the **General Ledger Setup** window to post payable invoice transactions.

#### To set up a Workers’ Compensation rate for payable invoices:

|  | 1 | Open **4-4 Vendors (Accounts Payable)**. |
|---|---|---|

|  | 2 | Using the data control, select the vendor. |
|---|---|---|

|  | 3 | Click the **Invoice Defaults** tab. |
|---|---|---|

|  | 4 | In the **Work Comp Rate** box, enter the rate at which you are charging the subcontractor. |
|---|---|---|

|  | 5 | On the **File** menu, click **Save**. |
|---|---|---|

|  | 6 | Open **1-8 General Ledger Setup**. |
|---|---|---|

|  | 7 | On the **Payables** tab, enter the ledger account to which you are posting the charge to subcontractors in the **Workers’ Compensation** box. |
|---|---|---|

|  | 8 | Click **File** > **Save**. |
|---|---|---|

Tip: The credit does not appear on the Workers’ Compensation report, which only uses data from payroll records. To track and report the costs, create a separate Workers’ Compensation ledger account.
