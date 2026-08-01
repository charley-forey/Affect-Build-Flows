<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/7-Utilities/Alert_Wizard_Define_the_Alert_s_Output_and_Schedule.htm (Sage 100 Contractor help v20.5) -->

# Alert Wizard: Define the Alert's Output and Schedule

|  | 1 | Set how the alert notifications should be delivered. You must select at least one of the options, as indicated by the blue text label. |
|---|---|---|

|  | a | My Dashboard |
|---|---|---|

|  | b | Other Dashboard |
|---|---|---|

|  | c | Email |
|---|---|---|

|  | 2 | The Email Options section is enabled/disabled based on whether the Email check box is checked or not. |
|---|---|---|

|  | a | Enter at least one email address in the **Email “To” addresses** field. |
|---|---|---|

|  | b | Enter recipient addresses as desired, in the **Email “CC” addresses** field. |
|---|---|---|

|  | c | Enter an email subject in the **Email Subject** field. |
|---|---|---|

Note: The email subject field defaults to the alert’s name from the first wizard page, with “SMB ALERT!” prepended. You can change this to anything, but it cannot be blank.

|  | d | Enter any message or description in the **Email Message** field. Any text entered here appears in the email body/message above the detailed “report” of the alert notification as defined on the Layout wizard page. |
|---|---|---|

|  | e | Importance: Choose from Low, Normal, or High. Normal is the default. |
|---|---|---|

|  | f | Request Read Receipt: Check do have read receipt functionality connected with the email message. This is certainly supported by Outlook, but I don’t know if or how this is supported by general SMTP email systems. |
|---|---|---|

• Test buttons allow the user to see how the alert notification will look to ensure that they have the desired Layout. Tests to email also inherently check the user’s email settings, ensuring that SMB can communicate with the email system that’s defined on 7-9. NOTE: Tests are run without any selection criteria because there may be no records in the database that meet the alert’s criteria which would result in no output at all.
