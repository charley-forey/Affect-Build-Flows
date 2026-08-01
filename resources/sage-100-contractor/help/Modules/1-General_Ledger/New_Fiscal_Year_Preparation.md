<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/1-General_Ledger/New_Fiscal_Year_Preparation.htm (Sage 100 Contractor help v20.5) -->

# New Fiscal Year Preparation

#### Make changes to existing general ledger accounts

At this point, you can make changes to existing general ledger accounts and make entries for the new fiscal year.

To post a period 00-Prior Year transaction, post the transaction to period 00 of the current year. Then, to post the transaction to the archive, open the archive company then post the transaction to period 12. As of the version 19.2 release, Sage 100 Contractor no longer supports posting simultaneously to period zero of the current company and period 12 of the archive company.

Prior year adjustments posted to income and expense accounts update the **Retained Earnings** account in the current year in period zero(0).

#### Change security in the archive company

![](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Resources/Images/check_box_unchecked.PNG) If you archived your previous fiscal year after advancing the fiscal period (recommended), change security in the archive company if required by changing the rights of all user groups in **7-2-1 Security Groups** to **No** for **Save**, **Delete**, **Void**, **Change Period**, and **Print Cheques**. This prevents users from accidentally saving or printing records in the archive.

By setting Groups to **No**, reports can still be printed, but cheques cannot be printed. Then each user will have access to everything they had access to before closing. They will be able to print reports but only view cheques.

![](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Resources/Images/check_box_unchecked.PNG) For additional security, in **7-2-2 User List**, change the password for the company administrator.
