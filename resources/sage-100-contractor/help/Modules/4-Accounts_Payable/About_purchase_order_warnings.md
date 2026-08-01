<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/4-Accounts_Payable/About_purchase_order_warnings.htm (Sage 100 Contractor help v20.5) -->

### About purchase order warnings

When saving a payable invoice for a vendor, Sage 100 Contractor refers to the selection made in the **Purchase Order Warning** list in the vendor’s record. If the payable invoice does not meet the criteria, Sage 100 Contractor provides you with a warning. These warnings are set on the Invoice Defaults tab of **4-4 Vendors** and warn if there is no PO available for the invoice or you can require a PO for the invoice.

| Status | Description |
|---|---|
| 0-None | Provides no warning. |
| 1-Warn if no PO | Provides a warning if the invoice does not contain a purchase order number, but allows you to save the invoice. |
| 2-Require PO | Requires a purchase order number to save the invoice. |

#### Vendor Invoice Over Purchase Order settings

The **Set Over PO Warning** option in **4-4 Vendors** notifies you if the invoice quantity amount exceeds the purchase order. When you select the **Set Over PO Warning** option in the Options menu, Sage 100 Contractor compares the invoice total amount (not including PST/HST/GST) against the total PO balance. The Vendor Invoice Over Purchase Order warning settings supersedes the settings for Invoice Over Purchase Order warning settings in 4-2. [How?](Entering_settings_for_the_Vendor_Invoice_Over_Purchase_Order_Warning.md)

QST calculations do not trigger these warnings.

| Links to more information . . . [Setting up vendor types](Setting_up_vendor_types.md) [About vendor invoice defaults](About_vendor_invoice_defaults.md) [About other vendor defaults](About_other_vendor_defaults.md) [About vendor financial information](About_vendor_financial_information.md) [About vendor certificates and expiration dates](About_vendor_certificates_and_expiration_dates.md) Setting up use taxes for payable invoices Workers Compensation for subcontractors |
|---|
