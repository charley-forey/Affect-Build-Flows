<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/5-Payroll/About_posting_payroll.htm (Sage 100 Contractor help v20.5) -->

### About posting payroll

You can enter timecards, compute payroll, and even print payroll cheques without posting the payroll records. When you are ready, you can post individual payroll records or all payroll records for a specified pay period.

When you post payroll, Sage 100 Contractor:

- Debits gross payroll: Job costs post to the direct expense account. If you have selected the **Post Payroll to WIP** check box in the job record, payroll posts to a WIP account. If the WIP account uses subsidiary accounts, payroll posts to a subsidiary account that uses the job number as the account number. Equipment repair or maintenance costs post to the equipment/shop account. All remaining costs post to the overhead or administrative account, which is determined by the employee position.
- Debits payroll expenses to the ledger accounts as indicated in the payroll calculation.
- Credits net payroll to the chequing account entered in the **Payroll Posting** window.
- Credits the ledger accounts as indicated in the payroll calculation.

If you do not specify which records or pay periods to post, Sage 100 Contractor posts all payroll records assigned **2-Computed** or **4-Reverse**. After posting is complete, Sage 100 Contractor changes records with status **2-Computed** to status **3-Posted**, and records with status **4-Reverse** to status **5-Void**.

| Links to more information . . . [Posting payroll in detail](Posting_payroll_in_detail.md) [Posting payroll in summary](Posting_payroll_in_summary.md) [About work in progress (WIP)](../4-Accounts_Payable/About_work_in_progress__WIP_.md) [About setting up posting accounts for payroll calculations](About_setting_up_posting_accounts_for_payroll_calculations.md) [Methods for entering historical payroll records](Methods_for_entering_historical_payroll_records.md) [Entering historical payroll records](Entering_historical_payroll_records.md) |
|---|
