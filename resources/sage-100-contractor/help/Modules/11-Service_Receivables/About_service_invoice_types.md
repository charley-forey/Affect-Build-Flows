<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/11-Service_Receivables/About_service_invoice_types.htm (Sage 100 Contractor help v20.5) -->

### About service invoice types

Note: Service Receivables features are available only if you have purchased the [Service Receivables Add-On Module](http://na.sage.com/sage-100-contractor/modules/service-management).

Service invoice types let you categorize transactions and control to which ledger accounts you post. For each type, indicate the cash, taxable income, non-taxable income, discounts given, and cost of goods accounts as well as the cost code and cost type. In addition, you can include a department.

On the **Invoice Details** tab, Sage 100 Contractor inserts the appropriate income account based on the service invoice type selected. For taxable items, Sage 100 Contractor suggests the taxable income account. For non-taxable items, Sage 100 Contractor suggests the non-taxable income account. You can change the suggested account if needed.

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

| Links to more information . . . [Setting up service invoice types](Setting_up_service_invoice_types.md) [Setting up finance charges for service work](Setting_up_finance_charges_for_service_work.md) [About service invoice status](About_service_invoice_status.md) |
|---|
