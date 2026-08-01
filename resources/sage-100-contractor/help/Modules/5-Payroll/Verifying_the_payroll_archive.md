<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/5-Payroll/Verifying_the_payroll_archive.htm (Sage 100 Contractor help v20.5) -->

### Verifying the payroll archive

#### To verify the payroll archive:

1. Open Sage 100 Contractor, and then select the company that you want to archive and close.
2. Open **5-2-2 Payroll Records**, click **File** > **Count**, and then note the total number of records.
3. Open **4-2 Accounts Payable Invoices**, click **File** > **Count**, and note the total number of records.
4. Exit Sage 100 Contractor.
5. Start **Database Administration for Sage 100 Contractor**. Archive and then close the payroll. Note: You must have administrator access to use Database Administration.
6. Start Sage 100 Contractor, and select the archive you have just created.
7. Open **5-2-2 Payroll Records**, click **File** > **Count**, and then note the total number of records.
8. Open **4-2 Accounts Payable Invoices**, click **File** > **Count**, and then note the total number of records.

Compare the record totals taken before archiving from each of the three databases before archiving to those taken from the archive. When the totals agree, the records have been archived correctly. If you find that the archive is incomplete, restore a backup and create new archives.
