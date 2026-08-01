<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/1-General_Ledger/About_setting_up_sales_taxes_for_Canadian_provinces.htm (Sage 100 Contractor help v20.5) -->

# About setting up sales taxes for Canadian provinces

You use the **Canada Sales Tax Setup** table in the **1-8 General Ledger Setup** window to set up the tax codes required for each province. You can create different tax codes to apply different tax rates to certain items, as required by a province, and you can set up tax codes with a zero tax rate for tax-exempt vendors.

Also, for provinces that require the recapture of input tax credits (RITC) on specified property and services, you can create a tax code for goods and services that are subject to RITC. Sage 100 Contractor can then compute and track Recaptured Input Tax Credits (RITC) on Accounts Payable invoices and credit notes for provinces that have HST.

Where there are multiple tax codes for a province, you use the **Is Primary Code** column in the table to indicate which tax code Sage 100 Contractor uses as the primary tax code for the province.

Although the primary tax code becomes the default for each province, you can override this code for specific transactions and vendors. When you enter Accounts Payable transactions in the **4-2 Payable Invoices/Credits**, **4-6 Recurring Payables**, and **4‑7‑3 Credit Card Receipts** windows, Sage 100 Contractor automatically applies the tax code override from the vendor record, if one is specified for the vendor. If no tax override is specified in the vendor record, the primary tax code for the province is used.

Important! When defining multiple tax codes for a province, you must assign an identical set of accounts to each tax code for the province.

| Links to more information . . . [Setting up Canadian sales taxes by province](Setting_up_Canada_sales_tax_by_province.md) |
|---|
