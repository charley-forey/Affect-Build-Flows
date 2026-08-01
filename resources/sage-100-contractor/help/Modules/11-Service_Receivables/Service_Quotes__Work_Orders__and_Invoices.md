<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/11-Service_Receivables/Service_Quotes__Work_Orders__and_Invoices.htm (Sage 100 Contractor help v20.5) -->

### Service Quotes, Work Orders, and Invoices

### About service invoice types

Note: Service Receivables features are available only if you have purchased the [Service Receivables Add-On Module](http://na.sage.com/sage-100-contractor/modules/service-management).

Service invoice types let you categorize transactions and control to which ledger accounts you post. For each type, indicate the cash, taxable income, non-taxable income, discounts given, and cost of goods accounts as well as the cost code and cost type. In addition, you can include a department.

On the **Invoice Details** tab, Sage 100 Contractor inserts the appropriate income account for the selected service invoice type. For taxable items, Sage 100 Contractor suggests the taxable income account. For non-taxable items, Sage 100 Contractor suggests the non-taxable income account. You can change the account if needed.

When you post the work order or invoice, Sage 100 Contractor creates the journal transaction, debiting the service receivables account and crediting the appropriate taxable or non-taxable accounts for each item. Under certain circumstances, Sage 100 Contractor also posts to the cash, discounts given, or cost of goods accounts indicated in the service invoice type.

- **Cash Account:** When a client or customer pays cash for an over-the-counter sale, enter the invoice and assign it status **4-Paid**. When you post the transaction, Sage 100 Contractor creates additional lines in the journal transaction-debiting the cash account and crediting the service receivables account.
- **Cost of Goods:** When the items come from inventory, Sage 100 Contractor creates additional lines in the journal transaction-debiting the cost of goods account and crediting the inventory account.

You can set up service invoice types to classify the types of work you perform, and provide suggested ledger accounts for posting transactions. If there are a large number of startup invoices, create a service invoice type designed to post to the service receivables clearing account.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Example of service invoice types for a plumbing company](javascript:void(0);)

| Invoice Type # | Type Name |
|---|---|
| 1 | Over-the-counter |
| 2 | Faucet repair |
| 3 | Grease/drain clean out |
| 4 | Leak detection |
| 5 | Back flow test |
| 6 | Plumbing repair |
| 7 | Old debt |

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Example of service invoice types for an electrical company](javascript:void(0);)

| Invoice Type # | Type Name |
|---|---|
| 1 | New fixture |
| 2 | Fixture replacement |
| 3 | Rewire |
| 4 | New meter/service |
| 5 | Upgrade meter/service |
| 6 | Troubleshooting |
| 7 | Old debt |

### About service invoice status

Note: Service Receivables features are available only if you have purchased the [Service Receivables Add-On Module](http://na.sage.com/sage-100-contractor/modules/service-management).

The status of a service record indicates its location in the process.

Important! You can change the status of records assigned status **1-Open**, **2-Review**, or **3-Dispute** to another of the first three status settings. However, you cannot assign status **4-Paid** or **5-Void**.

| Status | Description |
|---|---|
| 1-Open | Indicates you have invoiced the customer. Sage 100 Contractor posts the record to the general ledger. |
| 2-Review | Indicates the management or bookkeeping staff should review the record. |
| 3-Dispute | Indicates a record disputed by the client. |
| 4-Paid | Indicates a record paid in full. |
| 5-Void | Indicates a void record. |
| 6-Quote | Indicates a quote has been provided to a potential customer. A service call has not been scheduled. You cannot hold stock for a service record assigned this status. |
| 7-Work Order | Indicates a service call is scheduled. You cannot hold stock for a service record assigned this status. When you post a work order, Sage 100 Contractor assigns the record status **1-Open**. |
| 8-Complete | Indicates the service work is complete, but you will not bill the customer for the work. |
| 9-Route | Indicates the work order is for a service route. You cannot use serialized part numbers in the record. However, you can enter parts without serial numbers. |
| 10-Contract | Indicates a service provided on a regular basis. You cannot use serialized part numbers in the record. However, you can enter parts without serial numbers. |

Note: When an invoice or credit is fully paid, Sage 100 Contractor automatically assigns status **4-Paid**. If you void the record, Sage 100 Contractor automatically assigns status **5-Void**.

### Entering quotes or work orders or invoices

Note: Service Receivables features are available only if you have purchased the [Service Receivables Add-On Module](http://na.sage.com/sage-100-contractor/modules/service-management).

Consider the following points before entering quotes, work order, or invoices:

- To create a quote or work order, you only need to provide the information required in the header.
- To create an invoice, you must include a price and quantity on the ****Invoice Details**** tab; otherwise, Sage 100 Contractor cannot calculate the invoice amount.
- When you save a record assigned status **1-Open**, **2-Review**, or **3-Dispute**, Sage 100 Contractor posts an invoice to the general ledger.
- The work order shows up on the **Dispatch Board** when the **Scheduled** and **Priority** text boxes on the **Dispatch** tab are filled in.
- You can use markups and overrides when entering a new quote, work order, or invoice.

To locate an existing client's records, you can make an entry in the **Phone#**, or **Address 1**, on the **Location** tab when **F9** is used. Sage 100 Contractor searches the client and client locations and displays the record when it finds an exact match. When you enter client records, be consistent in how the information is formatted.

Suppose a client's address appears in the client record as 555 Main St. When entering a work order for the client, you enter 555 Main Street in the **Address 1** text box on the **Location** tab. Because the address does not precisely match what is given in the client record, Sage 100 Contractor is unable to find the client record.

Some companies provide technicians with preprinted numbered invoices, which you can track on the service record. After a technician has provided the customer with an invoice, select the service record and enter the invoice number in the **Invoice#** text box. If you leave the **Invoice#** box blank, Sage 100 Contractor inserts the work order number.

Tip: With the cursor in the **Order#** text box, you can have Sage 100 Contractor auto-populate the **Order#** and the **Invoice#** text boxes by setting the **Default Entry to Next** in the **Field Properties** (F7). Alternatively, on saving a record, if no **Invoice#** is assigned, Sage 100 Contractor copies the order number to the invoice number.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To enter a quote, work order, or invoice](javascript:void(0);)

|  | 1 | Open **11-2 Work Orders/Invoices/Credits**. |
|---|---|---|

|  | 2 | In the **Order#** text box, enter the work order number. |
|---|---|---|

|  | 3 | In the **Invoice#** text box, enter the invoice number. |
|---|---|---|

|  | 4 | In the **Date** text box, enter the work order date. |
|---|---|---|

|  | 5 | In the **Client#** text box, enter a client number. |
|---|---|---|

|  | 6 | In the **Description** text box, enter a brief statement about the transaction. |
|---|---|---|

|  | 7 | In the **Job** text box, enter the job number. |
|---|---|---|

|  | 8 | In the **Status** list, click the invoice status. |
|---|---|---|

|  | 9 | In the **Type** list, click the invoice type. |
|---|---|---|

|  | 10 | If you want to enter the customer or client location, [enter the data](Entering_locations_on_a_work_order.md) on the **Location** tab. |
|---|---|---|

|  | 11 | If you want to schedule the service call, [enter the data](Scheduling_service_calls_on_a_work_order.md) on the **Dispatch** tab. |
|---|---|---|

|  | 12 | If you want to enter the billing information, [enter the data](Entering_billing_information_for_work_orders_and_invoices.md) on the **Billing** tab. |
|---|---|---|

|  | 13 | If you want to enter the parts or assemblies necessary to complete the work, [enter the data](Entering_invoice_details_for_service_calls.md) on the **Invoice Details** tab. |
|---|---|---|

|  | 14 | If you want to enter the insurance information, [enter the data](Entering_insurance_information.md) on the **Insurance** tab. |
|---|---|---|

|  | 15 | On the **File** menu, click **Save**. |
|---|---|---|

| [Entering quotes or work orders or invoices](Entering_quotes_or_work_orders_or_invoices.md) [About insurance information](About_insurance_information.md) [Entering insurance information](Entering_insurance_information.md) [Creating multiple work orders and invoices](Creating_multiple_work_orders_and_invoices.md) [Creating purchase orders from work orders or invoices](Creating_purchase_orders_from_work_orders_or_invoices.md) [Deleting service records](Deleting_service_records.md) [Managing bad debts in service receivables](Managing_bad_debts_in_service_receivables.md) |
|---|
