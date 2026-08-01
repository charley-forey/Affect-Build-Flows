<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/4-Accounts_Payable/About_secondary_payees.htm (Sage 100 Contractor help v20.5) -->

### About secondary payees

The **Secondary Payees** window provides a way to add secondary payees to invoices. Secondary payees are most often involved with subcontractor invoices because they have subvendor suppliers who have lien rights to the project. It is critical to ensure that these suppliers get paid. The use of two-party cheques provides this assurance.

There are several ways to enter the secondary payees. You can do so when you enter a new subcontractor’s invoice in the **4-2 Payable Invoices/Credits** window by entering the name and amount payable to each supplier in the **Secondary Payees** window. You can also add one or more secondary payees to existing vendor invoices.

You will notice upon looking at the **Secondary Payees** window that it has three main parts: the grid, the vendor line, and the totals line.

| Grid Columns | Description |
|---|---|
| Secondary Payee | The name for the second party that will appear on the two-party cheque. |
| Amount | The total amount that should be paid on two-party cheques to the payee. |
| Paid | The total amount of payment made to this payee. This column is not editable. |
| Balance | The **Amount** minus the **Paid** as calculated by Sage 100 Contractor. This column is not editable. |
| To Pay | The amount scheduled for a two-party cheque. This column allows you to enter or edit the amount. |

The vendor line appears under the grid. The information in the vendor line reflects information related to the grid columns for the vendor on the invoice.

| Vendor Line | Description |
|---|---|
| Vendor Name | Displays the vendor name and the invoice information that applies directly to the vendor. |
| Amount | The amount is reduced as entry is made in the **Amount** column in the grid. In other words, the vendor receives whatever funds remain after the secondary payee(s) are paid. |
| Paid | The total amount of payment that has been made directly to the vendor. |
| Balance | The **Amount** minus the **Paid**. It is likewise adjusted whenever the **Amount** on this line changes. |
| To Pay | The amount scheduled for payment directly to the vendor. This text box allows you to enter or edit the amount. |

The totals line appears under the double line and reflects the entire invoice. The **To Pay** total reflects the sum of all **To Pay** amounts on this window. Upon saving it is sent back to its corresponding field at the bottom of the **4-2 Payable Invoices/Credits** window.

Holdback values are not reflected on this window. Holdback that is entered on **4-2 Payable Invoices/Credits** is held against the vendor’s balance. You cannot hold a portion of the invoice holdback against a secondary payee; however, you can pay 90% on one cheque and the remaining 10% on a later cheque.

Discounts are not reflected on this screen. They are applied against the vendor’s balance. You cannot apply a portion of the invoice’s discount against the balance of a secondary payee.

After saving the information in the **Secondary Payees** window and subsequently the **4-2 Payable Invoices/Credits** window, the next logical step could be to print and post the cheques using the **4-3 Vendor Payments** window. You will notice that the single invoice appears in the grid as multiple lines with the second payee lines directly under the vendor's portion. When you sort the grid, these lines stay together.

Here is an example. Suppose you subcontracted the electrical work on the construction of a home. Upon completion of the job, the subcontractor sends an $8,500 invoice, the amount of the contract. The invoice lists three suppliers and the associated costs: a materials supplier—$2,000; a lighting supplier—$1,500; and an equipment supplier for a backhoe to perform ground work—$300. To ensure that each of the subcontractor’s suppliers is paid, you can print a two-party cheque for each supplier.

When you print cheques from the **4-3 Vendor Payments** window, Sage 100 Contractor prints four cheques based on the amounts in the **Secondary Payees** window. A cheque to the subcontractor and materials supplier for $2,000; a cheque to the subcontractor and lighting supplier for $1,500; a cheque to the subcontractor and equipment supplier for $300; and a cheque to the subcontractor for $4,700, which is the vendor’s portion that is not attributed to a second payee.

In additional, consider the following points:

- No information on the **Secondary Payees** window may be edited when the invoice has a status of **4-Paid** or **5-Void**.
- You can add multiple additional secondary payees to an invoice.
- You can change amounts to be paid to secondary payees as long as no payment has been made.
- You can change the name of the secondary payee as long as no payments have been made.
- You can remove secondary payees as long as no payments have been made.

| Links to more information . . . [Entering payable invoices that include secondary payees](Entering_payable_invoices_that_include_secondary_payees.md) [Adding secondary payees to existing payable invoices](Adding_secondary_payees_to_existing_payable_invoices.md) [Increasing amounts payable to secondary payees](Increasing_amounts_payable_to_second_payees.md) [Decreasing amounts paid to secondary payees](Decreasing_amounts_payable_to_second_payees.md) [About accounts payable holdback](About_accounts_payable_retention.md) [About 4-3 Vendor Payments](About_4-3_Vendor_Payments.md) |
|---|
