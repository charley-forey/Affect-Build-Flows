<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/3-Accounts_Receivable/About_updating_costs_in_loan_draw_applications_from_change_orders.htm (Sage 100 Contractor help v20.5) -->

### About updating costs in loan draw applications from change orders

You can automatically or manually update costs in the loan draw application from change orders. Choose from two methods to automatically update the costs from change orders. You can either incorporate the changes to costs in the individual cost codes, or include the total amount of the change order as a separate line item.

When you select the **Add to Existing Lines** option, Sage 100 Contractor only updates cost codes present in both the change order and the loan draw application. If the change order contains cost codes that do not appear in the loan draw application, Sage 100 Contractor will notify you. Review the new cost codes in the change orders, and if necessary, manually add the new cost codes to the loan draw application and update the loan draw application again. Sage 100 Contractor displays the amount of change to each cost code in the **Changes** column and the new contract amount in the **Contract** column.

Instead of updating the individual cost codes, you can append each change order as a separate line item at the end of the loan draw application. Suppose the client approves change order number 1, and you only want to show the total amount of the changes on the loan draw application. When you select the **Append as New Lines** option, Sage 100 Contractor creates a separate line for each change order. Sage 100 Contractor inserts the statement **Change Order# 1** in the **Description** column, and displays the total amount of the change order in the **Changes** column and the new contract amount in the **Contract** column.

Important! If you are using the **Append as New Lines** option, do not change the **Description** values as you have entered them into the grid. Sage 100 Contractor uses an exact match of the text in the **Description** column to match the items from the **Change Order** grid to the **Loan Draw** grid.

When the lender requires a classification system that differs from your cost codes, manually enter the costs of the change work.

| Links to more information . . . [Creating new loan draw applications automatically](Creating_new_loan_draw_applications_automatically.md) [Creating new loan draw applications manually](Creating_new_loan_draw_requests_manually.md) [About updating project costs automatically](About_updating_project_costs_automatically.md) [Processing loan draw applications](Processing_loan_draw_applications.md) [Voiding loan draw applications](Voiding_loan_draw_applications.md) [About file and link Attachments on records](../../Appendices/A-Sage_100_Contractor_Features/About_file_and_link_Attachments_on_records.md) |
|---|
