<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/4-Accounts_Payable/4-7-3_Enter_Credit_Card_Receipts.htm (Sage 100 Contractor help v20.5) -->

### 4-7-3 Enter Credit Card Receipts

Use this window to enter credit card receipts. The window’s grid functions very much like the grid in the **4-2 Payable Invoices/Credits** window.

You can choose whether to enter a vendor for this record and to cost jobs automatically if there is an associated job and vendor.

If the credit card receipt does not have a breakdown showing tax amounts, you can enter the receipt total, including tax, and let Sage 100 Contractor calculate the taxes for you.

#### **Why should I consider entering a vendor?**

If you enter a vendor, the program creates a paid invoice when you save the record. If you look in **1-3 Journal Transactions**, you see that two journal transactions have been created. This is a typical journal transaction and a record of the payment (the paid invoice).

Note: If necessary, you can void the payment, and then the invoice will be re-opened.

If you do not enter a vendor, the program creates a typical journal transaction without creating a paid invoice.

Note: You can job cost automatically when you have entered a vendor on the record. You have to job cost manually if the record has no vendor.

### Entering credit card receipts

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To enter credit card receipts:](javascript:void(0);)

1. Open **4-7-3 Enter Credit Card Receipts**.
2. In the **Card Issuer Account** box, select a card issuer account. If card issuer accounts and credit cards are set up, the program displays the first **Card Issuer Account**. You can click the drop-down arrow to select a different **Card Issuer Account** from the list, or you can click the **Add/View records** icon to enter a new **Card Issuer Account** or a new **Credit Card**.
3. In the **Credit Card** box, select a credit card.
4. (Optional) Under **Entering a vendor creates a paid invoice when saved**, enter a **Vendor**.  
   You can select an existing vendor from the list, or click the **Add/View records** icon to enter a new vendor.
5. In the **Payee**box, enter the payee/merchant name.
6. In the **Description** box, enter a description.
7. In the **Trans#** box, enter the credit card transaction number.
8. In the **Invoice Date** box, accept the default transaction date or enter a different transaction date.
9. (Optional) In the **Job** box, enter the job to which to assign costs. You can select an existing job from the list, or click the **Add/View records** icon to enter a new one.
10. If the receipt does not itemize taxes, in the **Optional Total Receipt** box, type the receipt total, and then click the [**Calculate**] button. The program creates one line for the receipt in the grid.
11. Enter receipt details in the grid:
    
    1. In the **Description** column, click a cell and enter a description.
    2. Press the Enter key to move through the grid, and accept or type information in each cell, as required. You are required to enter information under the column titles with an asterisk.Note: If you entered a total amount in the receipt header, you can change only the accounts and the entry in the **User Defined** column for the generated line.
12. Save the record as follows:
    
    - If you entered a job and a vendor, click the **Automatically job cost while saving the current record** icon.
    - If you are not job costing automatically, click **File** > **Save**.
