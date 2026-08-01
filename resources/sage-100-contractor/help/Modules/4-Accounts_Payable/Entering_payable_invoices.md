<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/4-Accounts_Payable/Entering_payable_invoices.htm (Sage 100 Contractor help v20.5) -->

### Entering payable invoices

Consider the following points when entering payable invoices:

- When using the **Inventory** module, you can assign inventory to a specific location.
- To track parts using the serial numbers, enter each part as a separate item. Then for each item, enter the serial number in the **Part Serial#** box. Sage 100 Contractor does not check for duplicate entry of serial numbers.

#### To enter a payable invoice:

|  | 1 | Open **4-2 Payable Invoices/Credits**. |
|---|---|---|

|  | 2 | In the **Invoice#** box, enter the invoice number. |
|---|---|---|

|  | 3 | The **Order#** box and **Subcontract#** box are mutually exclusive. Do one of the following: |
|---|---|---|

- If the invoice is for a purchase order, in the **Order#** box, enter the purchase order number, and then press the Enter key.
- If the invoice is for a subcontract, in the **Subcontract#** box, enter the subcontract number, and then press the Enter key.

|  | 4 | After pressing the Enter key, the program may automatically fill in some boxes and grid cells with data and values. |
|---|---|---|

Tip: You can turn on an option to verify the contract balance against the invoice.

|  | 5 | In the **Vendor** box, enter the vendor number. |
|---|---|---|

|  | 6 | In the **Job** box, enter the job number. |
|---|---|---|

|  | 7 | If the job uses phases, enter the phase number in the **Phase** box. |
|---|---|---|

|  | 8 | In the **Description** box, enter a description. |
|---|---|---|

|  | 9 | In the**Invoice Date** box, enter the date of the invoice. |
|---|---|---|

|  | 10 | In the **Due Date** box, enter the invoice due date. |
|---|---|---|

Note: The default due terms in the vendor record determine the default invoice due date. If the default terms are for the "xxTH" date, Sage 100 Contractor displays the "xxTH" date for the following month.

|  | 11 | In the **Discount Date** box, enter the discount due date. This is the last day by which the vendor can receive payment for you to receive a discount. |
|---|---|---|

|  | 12 | If needed, in the **Shipping#** box, enter the shipping tag or ticket number. |
|---|---|---|

|  | 13 | If needed, in the **Reference#** box, enter an invoice or credit number to apply this entry to. |
|---|---|---|

|  | 14 | If needed, check the **Hot List** button to add the record to the hot list. |
|---|---|---|

|  | 15 | In the **Status** list, click the invoice status. |
|---|---|---|

|  | 16 | In the **Type** list, click the invoice type. |
|---|---|---|

|  | 17 | (Optional) In the **User Def** and **User Def2** text boxes, enter the [user-defined information](../7-Utilities/About_setting_field_properties.md) as necessary. |
|---|---|---|

|  | 18 | If the vendor is set up with a Workers’ Compensation rate, and you want it to be calculated with this record, click the **Wk/Comp**button. |
|---|---|---|

Important! You have to manually click the **Wk/Comp** button in order for the record to calculate the vendor's Workers' Compensation rate. You can set up the Workers' Compensation rate on the **Invoice Details** tab of **4-4 Vendors (Accounts Payable)**.

|  | 19 | In the grid, do the following: |
|---|---|---|

|  | a | In the **Description** cell, enter a brief statement about the item. |
|---|---|---|

|  | b | In the **Price** cell, enter the price per unit. |
|---|---|---|

|  | c | In the **Account** cell, enter the ledger account number. |
|---|---|---|

|  | d | In the **Holdback** cell, enter the amount of holdback. By default, Sage 100 Contractor calculates the holdback (if applicable) using the rate from the subcontract, which is found in **6-7-1-Subcontracts**. |
|---|---|---|

|  | 20 | Repeat step 19 for each item. |
|---|---|---|

|  | 21 | Below the grid, in the **Discount** box, enter the discount for early payment. By default, Sage 100 Contractor calculates the discount amount using the rate from the vendor record. |
|---|---|---|

|  | 22 | Save the invoice. |
|---|---|---|

| Links to more information . . . [About vendor invoice defaults](About_vendor_invoice_defaults.md) [Entering accounts payable invoices for subcontract lines](Entering_accounts_payable_invoices_for_subcontract_lines.md) [Entering vendor records](Entering_vendor_records.md) [Options for saving payable invoices](Options_for_saving_payable_invoices.md) [Verifying contract balances](Verifying_subcontract_balances.md) |
|---|
