<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/5-Payroll/Posting_payroll_in_summary.htm (Sage 100 Contractor help v20.5) -->

### Posting payroll in summary

Summary posting provides an advantage over detailed posting for companies with very large payrolls. It reduces the total number of line items posted to the general ledger, and it also reduces the detail posted for each employee pay cheque.

The following compares detailed posting to summary posting:

- In detailed posting, Sage 100 Contractor creates a journal transaction for the total cost of each pay cheque. Each journal transaction contains line items for the labour costs and each payroll calculation.
- In summary posting, Sage 100 Contractor requires you to provide a clearing (summary) account in addition to a chequing account, where the clearing account temporarily holds the net pay.

Posting creates a separate journal transaction for the net amount of each pay cheque, which posts to the clearing account and the chequing account. Then Sage 100 Contractor creates a journal transaction containing a summary of the payroll expenses. The expenses post to the accounts as directed in the setup for each payroll calculation; the net amount of the payroll records posts against the clearing account. After the summary posting is complete, the clearing account balance returns to its original balance.

The **Post Payroll to GL** window has six text boxes in which to enter information. Use the **Pay Period Ending** and **Record#** text boxes to select a range of pay periods and records. Alternatively, you can use the **Record Pick List** to select a specific pay period and record.

In addition, consider the following points:

- You can limit the posting to a range of pay periods. In the first **Pay Period Ending** text box, enter the ending date of the first pay period you want to post. In the second **Pay Period Ending** text box, enter the ending date of the last pay period you want to post.
- You can limit the posting to a range of records. In the first **Record#** text box, enter the first payroll record you want to post. In the second **Record#** text box, enter the last payroll record you want to post.

#### To post payroll in summary:

|  | 1 | Open **5-2-6 Post Payroll to GL**. |
|---|---|---|

|  | 2 | In the **Chequing Account** text box, enter the ledger account number for the chequing account. |
|---|---|---|

|  | 3 | In the **Pay Period Ending** text boxes, enter the pay period ranges. |
|---|---|---|

|  | 4 | Do one of the following: |
|---|---|---|

|  | a | In the **Record#** text boxes, enter the record number ranges. |
|---|---|---|

|  | b | Next to the **Record Pick List** text box, click **Display pick list window** to select a specific list of record numbers. |
|---|---|---|

|  | 5 | Select the **Post in Summary** check box. |
|---|---|---|

|  | 6 | In the **Summary Account** text box, enter the clearing account number. |
|---|---|---|

|  | 7 | Click **Post Payroll**. |
|---|---|---|

Tip: You can create a **Record Pick List** of payroll records to post.

| Links to more information . . . [Posting payroll in detail](Posting_payroll_in_detail.md) [About work in progress (WIP)](../4-Accounts_Payable/About_work_in_progress__WIP_.md) [About setting up posting accounts for payroll calculations](About_setting_up_posting_accounts_for_payroll_calculations.md) [Methods for entering historical payroll records](Methods_for_entering_historical_payroll_records.md) [Entering historical payroll records](Entering_historical_payroll_records.md) |
|---|
