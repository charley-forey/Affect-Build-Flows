<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/3-Accounts_Receivable/Creating_new_loan_draw_requests_manually.htm (Sage 100 Contractor help v20.5) -->

### Creating new loan draw applications manually

If the lender requires a classification system other than cost codes, enter the classification system in the **Description** column.

Loan draws do not post to the general ledger and do not affect accounts receivable. After the lender transfers funds to your account, enter a deposit that credits the loan-payable subsidiary account for the loan.

#### To manually create a new loan draw application:

|  | 1 | Open **3-8 Loan Draw Requests**. |
|---|---|---|

|  | 2 | In the header: |
|---|---|---|

1. In the **Job** text box, enter the job number.
2. If the job uses phases, enter the phase number in the **Phase** text box.
3. In the **Description** text box, enter a brief statement about the work completed.
4. In the **Billing Date** text box, enter the date ending the period for which you are submitting the request.
5. In the **Application#** text box, enter the number of the application you are submitting.
6. In the **Loan#** text box, enter your loan number.
7. In the **Lender** text box, enter the vendor number of the lender.

|  | 3 | In a **Cost Code** text box, right-click, and select **Display Picklist Window**. |
|---|---|---|

|  | 4 | Create a **Picklist** of cost codes, and then click the check mark button to insert them in the **Cost Code** column. |
|---|---|---|

|  | 5 | In the grid, for each item: |
|---|---|---|

1. In the **Scheduled** cell, enter the scheduled amount.
2. Do one of the following:
   
   - In the **Current** cell, you can enter the costs incurred. If you provide the costs incurred, do not provide the percent of work completed in the **% Comp** cell.
   - In the **% Comp** cell, you can enter the percent of work completed. If you provide the percent of work completed, do not provide the current costs incurred in the **Current** cell.

|  | 6 | On the menu bar, click **Calculate**. |
|---|---|---|

|  | 7 | On the **File** menu, click **Save**. |
|---|---|---|

Note: Sage 100 Contractor creates a separate series of applications for each phase.

| Links to more information . . . [Creating new loan draw applications automatically](Creating_new_loan_draw_applications_automatically.md) [About updating costs in loan draw applications from change orders](About_updating_costs_in_loan_draw_applications_from_change_orders.md) [About updating project costs automatically](About_updating_project_costs_automatically.md) [Processing loan draw applications](Processing_loan_draw_applications.md) [Voiding loan draw applications](Voiding_loan_draw_applications.md) [About file and link Attachments on records](../../Appendices/A-Sage_100_Contractor_Features/About_file_and_link_Attachments_on_records.md) |
|---|
