<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Appendices/H-Working_with_the_Sage_ACT__Plug-in/Creating_a_Sage_100_Contractor_Job_from_an_ACT__Opportunity.htm (Sage 100 Contractor help v20.5) -->

## Creating a Sage 100 Contractor Client/Job from an Act! Opportunity

Note: To create a client/job in Sage 100 Contractor from an Act! opportunity, the opportunity status must be Closed-Won.

The client and job are created from an opportunity unless the client already exists. You cannot create the job without an associated client. The Act! company must be associated with a Sage 100 Contractor client to create the job from the Act! opportunity.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)To create a client/job in Sage 100 Contractor from an Act! company](javascript:void(0);)

|  | 1 | In the Act! Opportunity record, select the Sage 100 Contractor tab. |
|---|---|---|

|  | 2 | Click the [**Create job...**] button. |
|---|---|---|

Note: If the **Create job...** button is not visible, click and drag the splitter bar (located above the tabs) until you see the button.

|  | a | If the opportunity is associated with more than one Act! company, select the company to associate with this job, and then click [**OK**]. |
|---|---|---|

|  | b | If the Act! company is not associated with a Sage 100 Contractor client, create a client now by clicking [**Yes**], then filling out the requested information. |
|---|---|---|

Important! The Act! company must be associated with a Sage 100 Contractor client to continue creating the job from the Act! opportunity.

|  | c | In the Sage 100 Contractor—Client Information window, do the following: |
|---|---|---|

|  | i | (Required) Select the **Client status**. |
|---|---|---|

|  | ii | (Optional) Select the **Lead source**. |
|---|---|---|

|  | iii | (Optional) Select the **Salesperson**. |
|---|---|---|

Note: You cannot select a salesperson if you restrict access to **5-2-1 Employees** in Sage 100 Contractor.

|  | iv | Enter a **Client ID**, or leave blank to automatically assign a **Client ID** number. |
|---|---|---|

|  | v | If necessary, update the value in the **Client name** field. |
|---|---|---|

|  | vi | If necessary, update the value in the **Client short name** field. |
|---|---|---|

|  | vii | Click [**OK**]. |
|---|---|---|

|  | 3 | (Required) Select the **Job status**. |
|---|---|---|

|  | 4 | (Optional) Select the **Job type**. |
|---|---|---|

|  | 5 | Enter a **Job ID**, or leave blank to automatically assign a **Job ID** number. |
|---|---|---|

|  | 6 | If necessary, update the value in the **Job name** field. |
|---|---|---|

|  | 7 | If necessary, update the value in the **Job short name** field. |
|---|---|---|

|  | 8 | Click [**OK**]. |
|---|---|---|

Once the job is created in Sage 100 Contractor, Act! keeps track of that job to prevent the same job from being created twice in the same company.

The fields associated with the Act! company are written to the appropriate job record in Sage 100 Contractor, as shown in the table below.

| ACT! Company Field | Job Field |
|---|---|
| N/A | Job Status |
| N/A | Job Type |
| Opportunity Name | Job Name/Short Name |
| Associated Company's Client | Client |
| Actual Closed Date | Contract Signed |
| Open Date | Bid Opening |
| Total | Contract Amount |

The contacts associated with the ACT! company are written to the appropriate record in Sage 100 Contractor.

| ACT! Contact Field | Job Contact Field |
|---|---|
| Contact | Contact Name |
| Title | Job Title |
| Phone | Phone |
| Ext | Ext |
| Email | Email |
| Mobile | Cell Phone |
| Fax | Fax |
| Alternate | Other |
| N/A | Other Description |

When an Act! Opportunity is opened in Detail View, the tab row at the bottom contains a Sage 100 Contractor tab. This tab contains a list of current Sage 100 Contractor entities for this company.

Note: This information only appears after the creation of the client and remains until the association is removed.

Associations in Sage 100 Contractor:

| Field | Description |
|---|---|
| Drive | The drive that the Sage 100 Contractor company is located on. |
| Sage 100 Contractor Company | The Sage 100 Contractor company name. |
| Job Number | Job ID |
| Job Name | Job Name |
| Client Number | Client ID |
| Client Name | Client Name |
