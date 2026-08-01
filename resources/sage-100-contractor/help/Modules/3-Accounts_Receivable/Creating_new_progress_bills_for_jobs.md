<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/3-Accounts_Receivable/Creating_new_progress_bills_for_jobs.htm (Sage 100 Contractor help v20.5) -->

### Creating new progress bills for jobs

When you create a new progress bill for a job, you can enter the scheduled costs for each cost code or division in the **Scheduled** column. After saving the first application, Sage 100 Contractor does not allow any changes to the scheduled costs unless the **Allow Editing Scheduled $** option is selected. On subsequent applications, enter changes to costs in the **Changes** column.

In the **Current Stored** column, you can enter the amount of material currently being stored. When you create the next application, Sage 100 Contractor moves the costs from the **Current Stored** column to the **Previous Stored** column. As you complete work, remove the costs for items no longer being stored. To remove costs, enter the costs as a negative amount.

#### To create a new progress bill for a job:

|  | 1 | Open **3-7 Progress Billing**. |
|---|---|---|

|  | 2 | In the header: |
|---|---|---|

1. In the **Job** text box, enter the job number.
2. If the job uses phases, enter the phase number in the **Phase** text box.
3. In the **Description** text box, enter a brief statement about the work completed.
4. If you want this billing to include all the phases for the job, select the **Combine phases into single application** check box before you import the budget or proposal. Note: Costs for all phases will be combined when you update costs.
5. If you want to include this progress billing in the **6-12 Project Work Center**, select the **Hot List** check box.
6. In the **Application#** text box, enter the number of the application you are submitting.
7. In the **Billing Date** text box, enter the date ending the period for which you are submitting the request.
8. In the **Billing Cycle** text box, enter the billing cycle.
9. In the **Submitted** text box, enter the submittal date.
10. In the **Approved** text box, enter the approval date.

|  | 3 | Under **Billing Basis**, select the **Bill by cost codes** or **Bill by cost divisions** option. |
|---|---|---|

|  | 4 | On the **Options** menu, click **Setup** and complete the **Progress Billing Setup** window. |
|---|---|---|

|  | 5 | Do one of the following: |
|---|---|---|

- On the **Options** menu, select **Import**, then click **Import Budget**.
- On the **Options** menu, select **Import**, then click **Import Proposal**.

|  | 6 | In the grid, for each item: |
|---|---|---|

1. In the **Current Complete** text box, you can enter the costs incurred. If you provide the costs incurred, do not provide the percent of work completed in the **% Completed** text box.
2. In the **HoldbackRate** text box, you can accept the default primary rate from the **Progress Billing Setup** window, or you can enter a different rate for the item.
3. In the **Current Stored** text box, enter the current cost of materials stored for the job.
4. In the **% Completed** text box, you can enter the percent of work completed. If you provide the percent of work completed, do not provide the current costs incurred in the **Current Complete** text box.
5. In the **Subject to GST**, **Subject to PST**, and **Subject to HST** text boxes, type Yes if the item is taxable or No if the item is non-taxable. Note: QST is not processed for job costs.

|  | 7 | On the menu bar, click **Calculate** to select one option in the **Calculate Grid** window, then click [**Calculate**]. |
|---|---|---|

1. **Calculate the Current column based on the amounts entered in the Percentage column** (this is based on the amount entered in the **% Completed** text box in step 10e)
2. **Calculate the Percent column based on the amounts entered in the Current and Stored columns** (this is based on the amounts entered in the Current Complete and Current Stored text boxes in step 10a and 10c, respectively)

Note: Sage 100 Contractor creates a separate series of applications for each phase.

| Links to more information . . . [Entering setup data for progress bills](Entering_setup_data_for_progress_bills.md) [About updating costs in progress bills from change orders](About_updating_costs_in_progress_bills_from_change_orders.md) [About progress billing holdbacks](About_progress_billing_retention.md) [Processing progress bills](Processing_progress_bills.md) [Voiding progress bills](Voiding_progress_bills.md) |
|---|
