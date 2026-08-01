<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/3-Accounts_Receivable/About_electronic_receipts.htm (Sage 100 Contractor help v20.5) -->

### About electronic receipts

If you have a merchant account with Sage Payment Solutions, you can use the **3‑3‑2 Electronic Receipts** window to enter credit card payments electronically for your clients.

Note: Before you can process electronic receipts, you must enter your Sage Payment Solutions merchant ID and merchant key, as well as the general ledger account associated with your merchant account, on the Electronic Receipts Setup tab in the **7-1 Company Information** window. (For more information, see [About Sage Payment Solutions](../../SPS_SageExchange/About_Sage_Payment_Solutions.md)

Processing electronic receipts is very similar to processing cash receipts using the **3-3-1 Cash Receipts** window, with a few notable differences:

- You process an electronic receipt for one client at a time. Therefore:
  
  - You need to enter only the Client number in the transaction header.
  - You display invoices for the selected client in the grid.
- If you use the company option to store client information in the Sage Exchange Vault:
  
  - You can select **Save payment information** to save payment information that you enter for a transaction and client securely in the Sage Exchange Vault.
  - If you processed a payment for the client previously, you can choose to use the same payment method as before. If you processed a payment for the client previously and you also saved the client's payment information in the vault, you can select **Use last credit card**. If you select this option, when you click **Process and Post**, the credit card details stored in the vault for this customer appear on the Sage Exchange integration screen. You can change the credit card information on the Sage Exchange screen.
- Rather than clicking Save to store receipt transactions, you use the following icons or Options menu items:
  
  - You click **Process and Post** to process a receipt electronically through Sage Payment Solutions, where it will be deposited to your bank account, and post the transaction to your Sage 100 Contractor General Ledger.
  - You click **Post** to post a transaction to your Sage 100 Contractor general ledger that you entered directly through the Sage Virtual Terminal or using another payment processing service.

#### Applying receipts

To process receipts, you display client invoices the **3‑3‑2 Electronic Receipts** window, select the invoice being paid, and then enter the amount of the payment and any applicable discount or overpayment. If the payment includes a credit invoice, you enter a negative amount for that invoice.

#### Entering overpayments

When a client pays more than the total balance of an invoice, you can enter the additional money as an overpayment. The total amount of the **Paid** and **Discount** cells must equal the amount in the **Balance** cell before Sage 100 Contractor allows you to enter the overpayment. When you save the cash receipts, Sage 100 Contractor reduces the job balance by the amount of the overpayment. In addition, the invoice now carries a negative balance and acts as a credit invoice.

Suppose a client informs you that he is going on vacation for a few weeks. The client wants to make sure you have enough money to continue building while he is gone, so instead of paying the $5,000 he was billed, he pays $10,000. For the invoice, enter $5,000 in the **Paid** cell and $5,000 in the **Overpayment** cell. After saving transactions, the invoice now carries a –$5,000 balance. The next time you invoice the client, you can apply the credit.

#### Applying discounts

Sometimes clients receive a discount for early payment. Sage 100 Contractor automatically determines whether a discount is available based on the due date you indicated on the invoice. When a discount is available, it is shown in the **Discount Available** text box. If a discount is not available, you can still apply a discount to an invoice.

| Links to more information . . . [About cash receipts](About_cash_receipts.md) [Entering payments against invoices](Entering_payments_against_invoices.md) |
|---|
