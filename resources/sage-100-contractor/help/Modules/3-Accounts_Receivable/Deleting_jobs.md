<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/3-Accounts_Receivable/Deleting_jobs.htm (Sage 100 Contractor help v20.5) -->

### Deleting jobs

Deleting a job in the **3-5 Jobs (Accounts Receivable)** window requires that the job have a status of **Closed** or **Refused**. In addition, the job cost records existing in the current year must have a status of **Open**.

You may not delete a job in **3-5 Jobs (Accounts Receivable)** if:

- There is a balance in a WIP Asset subaccount that matches the job number, and;
- The job is marked as **Post expenses to WIP asset account** in **3-5 Jobs (Accounts Receivable)**, and;
- The WIP Asset account is marked to use the **Job#** as Subaccount in **1-7 Ledger Accounts**.

These restrictions help maintain the balance between job costs and the general ledger and the consistency between deleting jobs in **3-5 Jobs (Accounts Receivable)** and removing jobs in **1-6 Period/Fiscal Year Management**.

#### To delete a job:

|  | 1 | Open **3-5 Jobs (Accounts Receivable)**. |
|---|---|---|

|  | 2 | Using the data control, select the record. |
|---|---|---|

|  | 3 | On the **Edit** menu, click **Delete Job**. |
|---|---|---|

Note: If a WIP job with a balance does not have any current year job costs, you may delete it, but first you have to clear the **Post expenses to WIP asset account** check box.

| Links to more information . . . [Closing jobs](Closing_jobs.md) [About removing jobs at fiscal year-end](../1-General_Ledger/About_removing_jobs_at_fiscal_year-end.md) |
|---|
