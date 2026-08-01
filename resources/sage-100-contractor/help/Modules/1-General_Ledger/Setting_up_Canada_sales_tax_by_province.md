<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/1-General_Ledger/Setting_up_Canada_sales_tax_by_province.htm (Sage 100 Contractor help v20.5) -->

# Setting up Canadian taxes by province

After you have set up the account ranges, dedicated accounts, and posting accounts in your general ledger, you must set up taxes by province.

Notes:

- The collected account should be selected from one of the Liabilities account ranges.
- The paid account should be selected from one of the Asset account ranges.
- The PST Rate column requires a PST Collected Account.
- The QST Paid account is used for Quebec, only. QST is not included in job costs or committed costs, and does not trigger warnings over-budget or over-subcontract warnings.
- Subaccounts are not allowed for any of the posting accounts.

#### To set up sales tax by province

1. Open **1-8 General Ledger Setup**.
2. On the Options menu, click **Canada Sales Tax Setup**.
3. In the grid on the **Canada Sales Tax Setup** window that appears, enter the information for each province your company deals with.

| Column Name | Description |
|---|---|
| Province | Tip: The **9999--Unidentified Province** tax code uses "ZZ" as the Province code, which the Canadian Revenue Agency recognizes as the code for vendors located outside Canada. |
| Is Primary Code | Enter a value of **Y**, unless the tax is a secondary tax or a surtax. |
| Province Name | The Province Name is used when overriding the sales tax rate for one or more lines on a record. |
| GST Rate | Sets the GST rate for the following windows: 3-2 Receivable Invoices/Credits 4-2 Payable Invoices/Credits 11-2 Work Orders/Invoices/Credits |
| PST Rate | Sets the PST rate for the following windows: 3-2 Receivable Invoices/Credits 4-2 Payable Invoices/Credits 11-2 Work Orders/Invoices/Credits |
| PST Compounded | Enter a value of **Y**, if applicable. |
| HST Rate | Sets the HST tax rate. |
| RITC Rate | Recaptured Input Tax Credits (RITC) apply to large businesses that are HST registrants in provinces that use the HST. Enter the current recapture rate for the province. |
| PST Collected Account | Enter the ledger account for the collected PST. The ledger account should be selected from one of the Liabilities account ranges. |
| GST/HST Collected Account | Enter the ledger account for the collected GST/HST. The ledger account should be selected from one of the Liabilities account ranges. |
| GST/HST Paid Account | Enter the ledger account for the collected PST. The ledger account should be selected from one of the Current Assets account ranges. |
| QST Paid Account | Enter an asset or liability account (not a WIP asset). When you use a QST tax code in Accounts Receivable invoices, credit card receipts, and credit card charges, or in Accounts Payable invoices, recurring payables, purchase orders, and subcontracts, QST rather than PST fields appear in the transaction window. |
| RITC Paid Account | Enter the ledger account for the Recaptured Input Tax Credits (RITC). |

| Links to more information . . . [About setting up sales taxes for Canadian provinces](About_setting_up_sales_taxes_for_Canadian_provinces.md) |
|---|
