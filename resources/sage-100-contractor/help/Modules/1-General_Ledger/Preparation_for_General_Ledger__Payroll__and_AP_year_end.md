<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/1-General_Ledger/Preparation_for_General_Ledger__Payroll__and_AP_year_end.htm (Sage 100 Contractor help v20.5) -->

### Preparation for General Ledger, Payroll, and T5018 Year End

The following instructions assume that these steps are performed at the Sage 100 Contractor server location. Sage 100 Contractor strongly recommends this method because it avoids network irregularities that can disrupt the closing process.

Important! You must have exclusive access to your company file to perform these steps.

Each task listed below should be completed in preparation for a combined fiscal year end and calendar year end. Resolve audit errors as found during each step.

- Verify Posting Period
- Backup and verification
- Record counts
- Inventory audit (optional)
- Verify cheques
- Job status and removal
- Payroll Audit
- Reconcile quarterlies
- Employee status and removal
- Verify vendor information
- Print reports for after-close verification

Note: These steps assume you will not have your bank statement before your year end. If you have your bank statement, you may complete your bank reconciliation before your year end in the current company or after you archive your fiscal year in the new company file. If you do your bank reconciliation after you archive your data, the archive file is not updated. If you want the archive file updated, you will need to do the bank reconciliation again in your archive.

#### Verify Posting Period

![](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Resources/Images/check_box_unchecked.PNG) In **1-6 Period and Fiscal Year Management**> **Change Period**, the posting period must be set to **Period 12**.

#### Backup and verification

![](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Resources/Images/check_box_unchecked.PNG) Back up and validate your company file by following your regular backup and verification procedures.

#### Record Counts

![](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Resources/Images/check_box_unchecked.PNG) On the **5-2-2 Payroll Records** window, select **File** > **Count**, and then write down the record number counts. This record count will be used for verification after closing payroll.

#### Inventory Audit (optional)

![](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Resources/Images/check_box_unchecked.PNG) If you use inventory, open **12-5 Inventory Audit**, click **Audit**.

#### Verify cheques

![](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Resources/Images/check_box_unchecked.PNG) Verify that there are no unprinted cheques.

#### To find and resolve unprinted cheques:

1. Open **2-5 General Journals**.
2. Print the **2-5-21 General Journal** report with the following settings:
   
   1. In the **Account**box, use the range for all cash accounts listed in **1-8 General Ledger Setup.**
   2. In the **Trans#** box, select **Equal**, and type 0000.
   3. In the **Credit** box, select **Greater or =**, and type $0.01.
3. If the transaction is an unprinted cheque, open **1-1 Cheques/Bank Charges** and click the **Print Records** button to print the cheque if desired. If you don’t need to print a cheque, open **1-3 Ledger Transactions**, and change the **Trans#** to anything other than 0000.

Note: If it is a **Source 16-Payroll**, click on the **Go To Source** button to change the **Check#**. It's highly unusual that the cheque number would have been changed to 0000 unless the cheque had to be reprinted immediately.

#### Job status and removal

![](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Resources/Images/check_box_unchecked.PNG) Verify that the status on each job in **3-5 Jobs (Accounts Receivable)** is correct. Any job that should be removed at year-end must have a status of **6-Closed** or **2-Refused**. [How?](Verifying_job_removal.md)

If you need to change several jobs' statuses to **6-Closed**, you can use a Picklist window to close multiple jobs at once. To access this command, open **3-5 Jobs (Accounts Receivable)** and select **Update** > **Closed Status**.

#### Payroll Audit

![](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Resources/Images/check_box_unchecked.PNG) Open **5-3-7 Payroll Audit**, and click **Audit**.

If Payroll is outsourced, it is okay to close with payroll audit errors.

Important! If there are audit errors, resolve them before continuing.

#### Period Audit Errors

Some audit errors refer specifically to periods. If period audit errors exist, the **Audit** report displays them prominently. For example, a period audit error will contain the word **Period**in the row.

You can resolve most period audit errors by recalculating the ledger balances. To recalculate the ledger balances, open **1-6 Period and Fiscal Year Management > Recalculate Balances**, and then click **Recalculate Balances**.

#### Audit Errors Requiring Customer Support Assistance to Repair

Any remaining audit errors cannot be repaired by clicking **Recalculate Balances**on **1-6 Period and Fiscal Year Management > Recalculate Balances**. These audit errors might originate in accounts receivable, jobs, vendors, service clients, equipment, or other areas of the program where transactions originate.

Caution! Resolving remaining audit errors after a repair requires assistance from Customer Support. You can contact Customer Support at 800-866-8049. Be prepared to provide your company name, telephone number, and the company contact person. At that time, a Customer Support technician may request additional reports to help determine the cause of the error.

Additional audit error reports are now included with Sage 100 Contractor to assist Customer Support technicians in identifying the transaction sources of audit errors.

#### Reconcile quarterlies

![](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Resources/Images/check_box_unchecked.PNG) Reconcile quarterlies.

#### Employee status and removal

![](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Resources/Images/check_box_unchecked.PNG) Review employee statuses in **5-2-1 Employees**, and change employee statuses as needed.

If you want to remove employees, they must have a status of **Quit**, **Laid Off**, **Terminated**, or **Deceased**.

Verify vendor information

![](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Resources/Images/check_box_unchecked.PNG) Verify **Vendor Tax ID** and **Vendor T5018 Types** by printing the **4-1-1-31 Vendor List** report.

Important! Be sure to verify that the tax ID for each vendor is correct. For more information, see the Help topic, **[About T5018 types](../4-Accounts_Payable/About_T5018_types.md)**.

![](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Resources/Images/check_box_unchecked.PNG) Verify T5018 balances using the **4-1-5-21 Vendor Payment**report by date.

#### Print reports for after year-end verification

![](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Resources/Images/check_box_unchecked.PNG) Print the following reports to use for verification purposes after year end:

- **2-2-21 Balance Sheet** report for period 12
- **2-3-21 Income Statement** report for periods 1 through 12
- **3-1-3-26 AR Invoice Aging** report for period 12
- **4-1-3-26 AP Invoice Aging** report for period 12
- **5-1-2-41 Payroll Check Register** report with totals for status equal to **3-Posted**
- **6-1-6-21 Job Cost Totals** report for periods 1 through 12
- **11-1-3-26 Service Invoice Aging** report for period 12, if you use Service Receivables
