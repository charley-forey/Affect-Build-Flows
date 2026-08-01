<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/1-General_Ledger/About_removing_jobs_at_fiscal_year-end.htm (Sage 100 Contractor help v20.5) -->

### About removing jobs at fiscal year end

Caution! If you need to review any deleted records, refer to the company’s archive or restore a backup made prior to the archiving of your fiscal year.

When archiving your accounting data, you can remove job records from the company database. When a job is completed, fully invoiced, completely paid, and you do not want to carry its data into the next fiscal year, change the job record status to **6-Closed**.

Important! All jobs with a job record status of **2-Refused** will also be removed when archiving your data if you select the **Remove jobs with closed or refused status** maintenance option.

When Sage 100 Contractor removes a job record, it also removes job-related records, including schedules, takeoffs, progress billing, time and materials setup, closed purchase orders, subcontracts, change orders, budgets, proposals, and accounts payable and receivable invoices assigned status **4-Paid** or **5-Void**.

The archive process does not remove a closed or refused job unless the job has a zero balance, no open payable invoices/credits, no job costs in the current books, no payable invoices/credits in the current books (even if they are paid or void), and no balance in a WIP account. You can confirm that the jobs meet the criteria for removal. [How?](Verifying_job_removal.md)

Note: If jobs, vendors, employees, and equipment records created in subsequent years exist at the time you archive, these records are copied to the archive company, although the associated accounting data is removed.

| Links to more information . . . [Verifying job removal](Verifying_job_removal.md) |
|---|
