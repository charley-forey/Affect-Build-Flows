<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/3-Accounts_Receivable/3-3-2_Electronic_Receipts.htm (Sage 100 Contractor help v20.5) -->

## 3-3-2 Electronic Receipts

You use the **3-3-2 Electronic Receipts** window to process credit card payments for receivable invoices.

Note: Before you can process electronic receipts, you must open a merchant account with Sage Payment Solutions. You must also enter your merchant credentials, as well as the general ledger account associated with your merchant account, in the **7-1 Company Information** window.

For more information about Sage Exchange and the Sage Exchange Vault, see [About Sage Exchange](../../SPS_SageExchange/About_Sage_Exchange.md).

For conceptual information about processing electronic receipts, see [About electronic receipts](About_electronic_receipts.md).

### Entering a payment against an invoice

Entering an electronic payment is similar to entering a cash receipt. Because you enter electronic invoices for only one client at a time,you need to enter only the Client number in the transaction header.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To enter a payment against an invoice](javascript:void(0);)

|  | 1 | Open **3-3-2 Electronic Receipts**. |
|---|---|---|

|  | 2 | In the **Client** text box, enter the client number. |
|---|---|---|

|  | 3 | Do one of the following: |
|---|---|---|

- Click the **Contract Invoices** tab.
- Click the **Service Invoices** tab.

|  | 4 | Click the **Display** button. |
|---|---|---|

|  | 5 | For each invoice you want to pay, in the grid: |
|---|---|---|

|  | a | In the **Paid** cell, enter the total amount received.<br>Do not include any discount or credit in this amount. |
|---|---|---|

|  | b | If you are using discounts, in the **Disc Available** cell, enter the amount of the discount.<br>If you are not using discounts, skip step b. |
|---|---|---|

Important! To enter an overpayment for an invoice, the total of the **Paid** and **Discount** cells must equal the amount in the **Balance** text box. Then in the **Overpayment** cell, enter the amount paid in addition to the **invoice**payment, not the total amount.

If you use the company option to store client information in the Sage Exchange Vault:

- You can select **Save payment information** to save payment information that you enter for a transaction and client securely in the Sage Exchange Vault.
- If you processed a payment for the client previously, you can choose to use the same payment method as before. If you processed a payment for the client previously and you also saved the client's payment information in the vault, you can select **Use last credit card**. If you select this option, when you click **Process and Post**, the credit card details stored in the vault for this customer appear on the Sage Exchange integration screen. You can change the credit card information on the Sage Exchange screen.

|  | 6 | Choose to process and post the payment, or only post the payment to your ledger, as follows: |
|---|---|---|

- To process the payment through Sage Payment Solutions and post the transaction to your ledger, click **Process and Post**. A separate Sage Exchange integration window appears, where you can proceed with payment (entering credit card information as needed), cancel the payment, or change payment card details.
- To post a payment to your ledger that has already been processed through Sage Virtual Terminal or through a third-party payment service, click **Post Only**. A separate **Electronic Receipt** window appears, where you enter details about the receipt, including the date, reference number, payer's name, the last four digits of the deposit account number, and the type of credit card used.

### Entering payments and applying credits to invoices simultaneously

You can simultaneously enter a payment and apply a credit invoice. Suppose a job has a $500.00 credit invoice, a $1,000 invoice, and a $3,000 invoice. The client sends a payment of $3,500, the total amount due. You can apply the credit to either invoice, then apply the payment to the remaining balance.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To enter a payment and apply a credit to an invoice](javascript:void(0);)

|  | 1 | Open **3-3-2 Electronic Receipts**. |
|---|---|---|

|  | 2 | In the **Client** text box, enter the client number. |
|---|---|---|

|  | 3 | Do one of the following: |
|---|---|---|

- Click the **Contract Invoices** tab.
- Click the **Service Invoices** tab.

|  | 4 | Click the **Display** button. |
|---|---|---|

|  | 5 | For each item in the grid: |
|---|---|---|

|  | a | In the **Paid** cell, enter the total amount received. |
|---|---|---|

|  | b | In the **Discount Available** cell, enter the amount of the discount. |
|---|---|---|

|  | c | To apply the credit in the **Paid** cell of the credit invoice, enter the credit as a negative amount. |
|---|---|---|

|  | 6 | Choose to process and post the payment, or only post the payment to your ledger, as follows: |
|---|---|---|

- To process the payment through Sage Payment Solutions and post the transaction to your ledger, click **Process and Post**. A separate Sage Exchange integration window appears, where you can proceed with payment (entering credit card information as needed), cancel the payment, or change payment card details.
- To post a payment to your ledger that has already been processed through Sage Virtual Terminal or through a third-party payment service, click **Post Only**. A separate **Electronic Receipt** window appears, where you enter details about the receipt, including the date, reference number, payer's name, the last four digits of the deposit account number, and the type of credit card used.

### Applying credit invoices to receivable invoices

You can apply the balance of a credit invoice to one or more receivable invoices. It is also possible to apply only a portion of the credit invoice balance to an invoice and apply the remaining balance later.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To apply a credit invoice to a receivable invoice](javascript:void(0);)

|  | 1 | Open **3-3-2 Electronic Receipts**. |
|---|---|---|

|  | 2 | In the **Client** text box, enter the client number. |
|---|---|---|

|  | 3 | Do one of the following: |
|---|---|---|

- Click the **Service Invoices** tab.
- Click the **Contract Invoices** tab.

|  | 4 | Click the **Display** button. |
|---|---|---|

|  | 5 | For each invoice to which you want to apply a credit, in the grid, enter the credit as a negative amount in the **Paid** cell. |
|---|---|---|

|  | 6 | Choose to process and post the payment, or only post the payment to your ledger, as follows: |
|---|---|---|

- To process the payment through Sage Payment Solutions and post the transaction to your ledger, click **Process and Post**. A separate Sage Exchange integration window appears, where you can proceed with payment (entering credit card information as needed), cancel the payment, or change payment card details.
- To post a payment to your ledger that has already been processed through Sage Virtual Terminal or through a third-party payment service, click **Post Only**. A separate **Electronic Receipt** window appears, where you enter details about the receipt, including the date, reference number, payer's name, the last four digits of the deposit account number, and the type of credit card used.

| Links to more information . . . [About cash receipts and electronic receipts](About_cash_receipts.md) [About Sage Payment Solutions](../../SPS_SageExchange/About_Sage_Payment_Solutions.md) [About Sage Exchange](../../SPS_SageExchange/About_Sage_Exchange.md) [3-3-1 Cash Receipts](3-3-1_Cash_Receipts.md) |
|---|
