<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/11-Service_Receivables/About_11-2_Work_Orders-Invoices-Credits.htm (Sage 100 Contractor help v20.5) -->

### About 11-2 Work Orders-Invoices-Credits

Note: Service Receivables features are available only if you have purchased the [Service Receivables Add-On Module](http://na.sage.com/sage-100-contractor/modules/service-management).

The **11-2 Work Orders/Invoices/Credits** window lets you enter transactions that affect service receivable accounts. You can create quotes, work orders, invoices, credits, and service routes and contracts. You can also view many different summaries such as service contracts for clients, client equipment, equipment by location, quotes, work orders, and open invoices.

As you create records, you can schedule the service call and provide the location of the work and the parts and assemblies necessary to complete the work. When performing service work for insurance recovery, you can also supply the necessary policy details.

Use the **Remove Paid/Void/Completed Records** option to service invoices that meet the following criteria:

|  | n | The status is **Paid**, **Completed**, or **Void**. |
|---|---|---|

|  | n | The service invoice and associated payments has been posted prior to the current year. |
|---|---|---|

### About setting up service jobs

For service jobs, you need to include a job number on each record. When you post a direct expense, Sage 100 Contractor creates a cost record using the job number.

It is not necessary to create a job for each quote, work order, or invoice. Instead, create a dummy job that is assigned to all service records.

For companies with up to 2,000 completed work orders a year, create a single dummy job. After several years, remove the dummy job when closing the books for the fiscal year. Then create a new dummy job.

To make the dummy job identifiable, give it a name such as **Service Work**.

For companies with up to 10,000 completed work orders a year, create a new dummy job each fiscal year. After keeping a dummy job for two years, remove the dummy job when closing the books for the fiscal year.

To make the dummy job identifiable, give it a name that includes the year. For example, Service 2001, Service 2002, Service 2003, and so on.

For companies with over 10,000 completed, work orders a year, create a new dummy job each fiscal quarter.

To make the dummy job identifiable, give it a name that includes the year and fiscal quarter. For example, Service 2002 Q1, Service 2002 Q2, Service 2002 Q3, and so on.

There is no correlation between the job number and work order number. You can run job cost reports for a specific work order.

### About entering service receivable items at initial setup

Post the service receivable items against the same clearing account used earlier to enter the service receivable balances. The process transfers the balances into the **Service Receivables** ledger account.

When entering the receivable items, post the records to the appropriate posting periods. Post any open items from the prior year to period 0.

It is not necessary to enter the individual parts as line items in the grid. A single line containing a description, quantity, price, and ledger account number is all that is necessary.

| Links to more information . . . [Entering quotes or work orders or invoices](Entering_quotes_or_work_orders_or_invoices.md) [About work order deposits](About_work_order_deposits.md) [About service invoice types](About_service_invoice_types.md) [About service invoice status](About_service_invoice_status.md) [About service credits](About_service_credits.md) |
|---|
