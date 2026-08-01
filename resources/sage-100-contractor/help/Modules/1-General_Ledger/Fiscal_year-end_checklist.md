<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/1-General_Ledger/Fiscal_year-end_checklist.htm (Sage 100 Contractor help v20.5) -->

# Fiscal year-end checklist

Use this checklist only when the fiscal year-end is **not** December 31.

Follow this process in the order items are listed. Not following the process in order can result in an improper close or a damaged archive file.

Sage 100 Contractor no longer requires you to close your general ledger at the end of the fiscal year. At the end of your fiscal year, advance your fiscal period to period 1 of the next fiscal year. If you have not finished posting items to the current year but need to make entries in the new year, you can post to period 1 of the next fiscal year provided you are on period 12 of your current year. Periods 2-12 of the next fiscal year become available after you advance the fiscal period.

Advance the period to the next fiscal year before archiving your previous fiscal year. Sage 100 Contractor creates a new company file during the archive process. Do not create a new company manually.

If you have an archive from a previous year, post transactions to period 0 of the current year then open the archive company to post the transaction to the archive. As of the version 19.2 release, Sage 100 Contractor no longer supports posting simultaneously to period zero of the current company and period 12 of the archive company.

Prior-year adjustments posted to income and expense accounts update the **Retained Earnings** account in the current year to period zero.

#### Verify Posting Period

![](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Resources/Images/check_box_unchecked.PNG) In **1-6 Period and Fiscal Year Management** > **Change Period**, ensure the posting period is set to **Period 12**.

#### Backup and verification

![](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Resources/Images/check_box_unchecked.PNG) Back up and validate your company file by following your regular backup and verification procedures.

#### Inventory audit (optional, but strongly recommended if you use the Inventory module)

![](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Resources/Images/check_box_unchecked.PNG) If you use inventory, open **12-5 Inventory Audit**, click **Audit.**

#### Verify cheques

![](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Resources/Images/check_box_unchecked.PNG) Verify that there are no unprinted cheques.

#### To find and resolve unprinted cheques:

1. Open **2-5 General Journals**.
2. Print the **2-5-21 General Journal** report with the following settings:
   
   1. In the **Account**box, use the range for all cash accounts listed in **1-8 General Ledger Setup.**
   2. In the **Transaction#** box, select **Equal**, and type 0000.
   3. In the **Credit Amount** box, select **Greater or =**, and type $0.01.
3. If the transaction is an unprinted cheque, open **1-1 Cheques/Bank Charges**, and then click the **Print records** button to print the cheque, if desired. If you don’t need to print a cheque, open **1-3 Ledger Transactions**, and change the **Transaction#** to anything other than 0000.

Note: If it is a **Source 16-Payroll**, click the **Go To Source** button to change the **Check#**. It's highly unusual that the cheque number would have been changed to 0000 unless the cheque had to be reprinted immediately.

#### Period Audit Errors

Some audit errors refer specifically to periods. If period audit errors exist, the **Audit** report displays them prominently. For example, a period audit error will contain the word **Period**in the row.

You can resolve most period audit errors by recalculating the ledger balances. To recalculate the ledger balances, open **1-6 Period and Fiscal Year Management > Recalculate Balances**, and then click **Recalculate Balances**.

#### Audit Errors Requiring Customer Support Assistance to Repair

Any remaining audit errors cannot be repaired by clicking **Recalculate Balances**on **1-6 Period and Fiscal Year Management > Recalculate Balances**. These audit errors might originate in accounts receivable, jobs, vendors, service clients, equipment, or other areas of the program where transactions originate.

Caution! Resolving remaining audit errors after a repair requires assistance from Customer Support. The Knowledgebase article [How do I get technical support for Sage 100 Contractor?](https://support.na.sage.com/selfservice/viewdocument.do?externalId=32073) provides contact information and hours of operation. Be prepared to provide your company name, telephone number, and the company contact person. At that time, a Customer Support technician may request additional reports to help determine the cause of the error.

Additional audit error reports are included with Sage 100 Contractor to assist Customer Support technicians in identifying the transaction sources of audit errors.

#### Job status and removal

![](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Resources/Images/check_box_unchecked.PNG) Verify that the status on each job in **3-5 Jobs (Accounts Receivable)** is correct. Any job that should be removed at year-end must have a status of **6-Closed** or **2-Refused**.

If you need to change several jobs' statuses to **6-Closed**, you can use a Picklist window to close multiple jobs at once. To access this command, open **3-5 Jobs (Accounts Receivable)** and select **Update** > **Closed Status**.

#### Print reports and record counts for after year-end verification

![](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Resources/Images/check_box_unchecked.PNG) Print the following reports that will be used for verification purposes after the books have been closed:

- **2-2-21 Balance Sheet** report for period 12
- **2-3-21 Income Statement** report for periods 1 through 12
- **3-1-3-26 AR Invoice Aging** report for period 12
- **4-1-3-26 AP Invoice Aging** report for period 12
- **5-1-2-41 Payroll Check Register** report with “totals for status” equal to 3-**Posted**
- **6-1-6-21 Job Cost Totals** report for periods 1 through 12
- **11-1-3-26 Service Invoice Aging** report for period 12, if you use Service Receivables

| Links to more information . . . [Finding and resolving unprinted cheques when archiving the books](Finding_and_resolving_unprinted_checks_when_archiving.md) [What happens when you advance the fiscal year](What_happens_when_you_advance_the_fiscal_year.md) |
|---|
