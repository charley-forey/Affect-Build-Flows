<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/7-Utilities/Entering_company_information.htm (Sage 100 Contractor help v20.5) -->

### Entering company information

After you have created a blank new company, you have to enter the company information.

- General Information
- Payroll Direct Deposit Setup
- Vendor EFT Payment Setup
- Electronic Receipts Setup Note: To process electronic receipts, you must have a valid account with Sage Payment Solutions, including a merchant ID and key.
- Email and Fax Configuration

#### To enter general information:

1. In the **Company** list, click the company.
2. Open **7-1 Company Information**.
3. In the **Company Name** text box, enter the company name.
4. In the **Address 1**, **Address 2**, **City**, **Province**, and **Postal** text boxes, enter the address information.
5. In the **Phone#** text box, enter the telephone number.
6. In the **Fax#**text boxes, enter the fax telephone number.
7. In the **Email** text box, enter the company email address.
8. In the **Business Number** text box, enter the company’s Business Number.
9. (Optional) In the **User Def1** and **User Def2** text box, enter the user-defined information as necessary.
10. In the **Recur. Trans. Group** (Recurring Transactions Group) text box, select the security group responsible for posting recurring transactions. Important! If you do not enter a security group in the **Recurring Transactions Group** text box, Sage 100 Contractor does not provide a reminder that recurring transactions need to be posted.
11. If you prefer to use the United States date format (mm/dd/yyyy) for your company rather than the default format for Canada (dd/mm/yyyy), select the **Use mm/dd/yyyy Date Format** check box. All data entry screens and reports will then use the United States format except cheques, which use the Canadian date format required by the Canadian Payments Association. Note: After you switch the date format, Sage 100 Contractor will not be able to interpret existing event logs that use the old format. The next time an event or scheduled report is executed, Sage 100 Contractor renames the associated existing event log, and starts a new event log, which it can read even if you change the date format again. Tip: If you need to refer to them later, you can find old event log files (*EventLogOld) in the Sage 100 Contractorsubfolder in your local AppData folder—for example, C:\Users\Username\AppData\Local\Sage\Sage 100 Contractor\ProgramAlertsEventLogOld. You can open these files with any text editor, such as Notepad.
12. In the lower left of the window, click the **CRA Program Accounts** button to [enter the company’s program accounts](Setting_up_Canada_Revenue_Agency_Program_Accounts.md) in the **CRA Program Accounts**window.

#### To enter payroll direct deposit setup information:

1. Click the **Payroll Direct Deposit Setup** tab.
2. In the **Company bank information for direct deposit** section:
   
   1. In the **Originator ID#** text box, enter the direct deposit originator's identification number provided by your bank.
   2. In the **Destination Data Centre** text box, enter the destination data centre for the bank.
3. In the **Options for direct deposit EFT file** section, fill out and select the appropriate options for your direct deposit EFT file:
   
   1. In the **Returns Account Information** section, enter the appropriate account information:
      
      1. **Institution ID#**—Bank institution identification number of the returns bank account
      2. **Routing#**—Branch routing number of the returns bank account
      3. **Account#**—Bank account number for returns of EFT payment withdrawals
   2. In the **Settlement Account Information** section, enter the appropriate account information:
      
      1. **Institution ID#**—Bank institution identification number of the settlement bank account
      2. **Routing#**—Branch routing number of the settlement bank account
      3. **Account Indicator#**—Bank account indicator number for settlement of EFT payment withdrawals
   3. For **File formatting options**, select or clear the check boxes appropriate to the preferences of your financial institution.
      
      1. Include optional hard return (this includes a hard return at the end of each line in your EFT payment file)
      2. Include Item Trace# (this includes an item trace number in the EFT payment file)
      3. If your company sends EFT files to the Royal Bank of Canada, select **RBC Header**. Sage 100 Contractor adds a static line to the first line of the associated EFT files, as required by the Royal Bank of Canada.

Note: If you have any questions about which check boxes to select, contact your financial institution.

#### To enter vendor EFT Payment setup information:

1. Click the **Vendor EFT Payment Setup** tab.
2. Complete the following in the **Company bank information for EFT payments** section:
   
   1. In the **EFT Originator ID#** text box, enter the EFT originator's identification number provided by the bank.
   2. In the **Destination Data Centre**text box, enter the destination data centre for the bank.
   3. In the **Posting Cash Account**, display the lookup window and select the applicable cash account.
3. In the **Options for EFT payment file** section, fill out and select the appropriate options for your EFT payment file. This information is optional, and should be entered as required by your financial institution.
4. In the **Returns Account Information** section, enter the appropriate account information:
   
   1. **Institution ID#**—Bank institution identification number of the returns bank account
   2. **Routing#**—Branch routing number of the returns bank account
   3. **Account#**—Bank account number for returns of EFT payment withdrawals
5. In the **Settlement Account Information** section, enter the appropriate account information:
   
   1. **Institution ID#**—Bank institution identification number of the settlement bank account
   2. **Routing#**—Branch routing number of the settlement bank account
   3. **Account Indicator#**—Bank account indicator number for settlement of EFT payment withdrawals
6. For **File formatting options**, select or clear the check boxes appropriate to the preferences of your financial institution.
   
   1. Include optional hard return (this includes a hard return at the end of each line in your EFT payment file)
   2. Include Item Trace# (this includes an item trace number in the EFT payment file)
   3. If your company sends EFT files to the Royal Bank of Canada, in the **RBC Header** box, type the RBC header information. Sage 100 Contractor adds a static line to the first line of the associated EFT files, as required by the Royal Bank of Canada.

Note: If you have any questions about which check boxes to select, contact your financial institution.

#### To set up your company to process electronic receipts:

1. Make sure you have your Sage Payment Solutions merchant ID and merchant key handy. Note: Sage sends you these credentials when you purchase a Sage Payment Solutions account.
2. On the Electronic Receipts tab:
   
   1. In the Merchant ID and Merchant Key fields, enter your Sage Payment Solutionsmerchant credentials.
   2. To ensure that you have entered the correct information and that your account is valid, click **Validate Credentials**.
   3. In the **Posting Cash Account** field, enter the general ledger cash account associated with the bank account to which you will deposit electronic receipts. (This account should correspond to the bank account used in Sage Exchange.)
   4. If you want to use the Sage Exchange Vault to store credit card and bank account information from your client, select **Allow client credit card and bank account information to be securely stored in the Sage Exchange Vault**.

For information about the Sage Exchange Vault, see [About Sage Exchange](../../SPS_SageExchange/About_Sage_Exchange.md).

#### To configure Email and Fax:

1. Fill in the information on the **Email and Fax Configuration** tab after reading the following information:
   
   - User authentication is typically required for emailing through an ISP’s simple mail transfer protocol (SMTP) server. An example of an email server name is “smtp.att.sbcglobal.net.”
   - Server name must be SMTP server name, not a numeric IP address. An example of an IP address is “10.227.16.33.”
   - Different ISPs may use different terms when referring to user authentication. In general, however, user authentication means verifying the identity of the user by means of a “user name” and “password.”
   - In this context using an ISP’s SMTP server to send email through Sage 100 Contractor, user authentication refers to verifying a user’s identity at the ISP’s SMTP server. It does not refer to your Sage 100 Contractor username and password or to your network username and password.
   - Some Internet-based email providers do not support SMTP protocol. For more details, contact the Internet-based email providers that you use.
2. In the **SMTP Mail Configuration** section, do the following:
   
   1. In the **Email Server**text box, enter the name of the email server.
   2. In the **Port#** box, type the email server port number.
   3. Select **Requires authentication**, if the Internet service provider (ISP) service handling your email service requires user authentication.
   4. Select **Uses SSL for email**, if required by the Internet service provider.
3. In the **Fax Configuration** section, type your fax line number in the **Phone Dial Out** text box. Tip: You can change the email server and fax line access selections to accommodate sending reports from multiple locations with different requirements.
4. On the **File** menu, click **Save**.

#### To set a company as an archive:

1. From the menu, select **Options**.
2. Select **Set as Company Archive**.

Note: Anyone can set a company as an archive, but only a company administrator can remove this setting.

| Links to more information . . . [Setting up Canada Revenue Agency Program Accounts](Setting_up_Canada_Revenue_Agency_Program_Accounts.md) [About changing the date format for your company](About_changing_the_date_format_for_your_company.md) [About posting to the period 0 archive](../1-General_Ledger/About_posting_to_the_period_0_archive.md) [About email server-fax line access selection](../13-Review_and_Reporting/About_fax_line_access_selection.md) [About Sage Payment Solutions](../../SPS_SageExchange/About_Sage_Payment_Solutions.md) |
|---|
