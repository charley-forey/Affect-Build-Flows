<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/3-Accounts_Receivable/Voiding_unitary_bills.htm (Sage 100 Contractor help v20.5) -->

### Voiding unitary bills

You can void an application assigned status **4-Closed**. If the application precedes a series of applications, Sage 100 Contractor reopens the application, assigning it status **2-Submitted**, and voids the subsequent applications.

Suppose you have just created application 3. However, application 3 contains an error caused in application 2. To remove the error, you must correct application 2 and recreate application 3. When you void application 2, Sage 100 Contractor changes its status from **4-Closed** to **2-Submitted**. In addition, Sage 100 Contractor changes the status of application 3 to **5-Void**. You can then make the necessary adjustment to application 2, and from it then create application 3.

Important! If you have posted an application, and payments have been made to the invoice, you must reverse the payments before voiding the application.

#### To void a unitary bill:

|  | 1 | Open **3-9 Unitary Billing**. |
|---|---|---|

|  | 2 | Using data control, select the record. |
|---|---|---|

|  | 3 | On the **Edit** menu, click **Void Application**. |
|---|---|---|

| Links to more information . . . [About unitary billing holdbacks](About_unitary_billing_retention.md) [About changing unitary bills](About_changing_unitary_bills.md) |
|---|
