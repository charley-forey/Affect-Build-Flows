<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/3-Accounts_Receivable/About_time_and_materials_billing.htm (Sage 100 Contractor help v20.5) -->

## 3-10 Time and Materials

You can bill clients on a cost-plus basis, which is the cost for time and materials plus overhead and profit. Sage 100 Contractor uses the job cost records as the basis for the billing amounts on the time and materials (T&M) invoices.

When setting up a job for T&M billing, you can:

- Assign separate overhead and profit markup rates to each cost type.
- Assign a shown markup rate to each cost type.
- Assign a hidden markup rate to each cost type. When you calculate T&M invoices, Sage 100 Contractor adds the hidden markup to the job cost. The other markups shown, overhead and profit, are computed on top of the new billing amount. The hidden markup does not appear on the T&M invoice.
- Assign wage rate and equipment rate tables to the job. You can use the tables in place of using labour and equipment costs plus hidden markup. In addition, you can set a minimum daily charge, which is the minimum number of hours per labourer , or you can set the minimum units per piece of equipment to charge.

Suppose you own a backhoe and determine it is necessary to charge a minimum of three hours to recover the costs of ownership, maintenance, and mobilization. At a job site, you only use the backhoe for one hour. When you allocate the equipment use, Sage 100 Contractor bills the client for three hours instead of one.

Consider the following additional points:

- If equipment records contain rental billing rates, Sage 100 Contractor creates the job cost with the rental billing rate in the **Billing Amount** text box and with the **Override** check box selected. The program uses this amount when calculating the T&M Invoices even if an **Equipment Rate** table is selected for the T & M job.
- If you want to use the T & M **Equipment Rate** table you must either: (1) clear the **Override** check box on the job cost record and exclude billing rates from the equipment record before the job cost records are created; or (2) enter the job cost record directly into **6-3 Job Cost** record.
- If equipment records do not contain billing rates when you calculate the T & M invoices, Sage 100 Contractor replaces the billing amount with the rate from the **Equipment Rate** table. If an **Equipment Rate** table is not assigned to the T&M job, Sage 100 Contractor replaces the billing amount with the cost plus hidden markup.

| Links to more information . . . [Setting up time and materials jobs](Setting_up_time_and_materials_jobs.md) [Creating time and materials invoices by phase](Creating_time_and_materials_invoices_by_phase.md) [About wage rates for time and materials billing](About_wage_rates_for_time_and_materials_billing.md) [About equipment rates for time and materials billing](About_equipment_rates_for_time_and_materials_billing.md) [About computing time and materials invoices](About_computing_time_and_materials_invoices.md) [Processing time and materials invoices](Processing_time_and_materials_invoices.md) |
|---|
