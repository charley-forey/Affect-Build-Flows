<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/5-Payroll/About_direct_deposit.htm (Sage 100 Contractor help v20.5) -->

### About direct deposit

Direct deposit allows your employees to have their pay cheques deposited directly into their bank account. Banks require electronic delivery of payroll information by companies wanting to provide employees with direct deposit. Sage 100 Contractor supports the creation of a file in electronic file transfer (EFT) format. You can then send this file to your bank. Your bank will extract records from the file and create files that are routed through EFT providers to the various employee banks.

Notes:

- Contact your bank to determine any delivery requirements, including encryption, additional file format requirements, or other requirements. After establishing and agreeing on a method of delivery with your bank, you can create the file and deliver it in the agreed-upon method.
- Whenever any changes are made to your direct deposit file format by changing any of the formatting options, you should contact your bank and request a retest to be sure your bank is ready for the changes.
- After creating the **Direct Deposit File**, Sage 100 Contractor prompts you to print a **Direct Deposit File Report** that shows your **Direct Deposit File** information. If you do not print that report at that time and need to reprint the report, use **Options** > **Reprint Direct Deposit Report**.

Two documents can be created during a direct deposit run: the **Direct Deposit File** and the **Direct Deposit File Report**.

- Direct Deposit File. The Direct Deposit file is created in Electronic File Transer (EFT) format and is saved as a .txt file used by the bank. By default it is saved in the x:\\[ServerName]\[CompanyName]\Direct Deposit folder (where x: is your network drive). The next time you save your direct deposit file, Sage 100 Contractor defaults to the directory where the file was last saved. The exact location of your direct file appears on the **Direct Deposit File Report**.
- **Direct Deposit File Report.**The generated report is saved in the \\[ServerName]\[CompanyName]\Reports folder as an .rtf or .pdf.

Printed cheques have a unique cheque number and an electronic deposit number that correspond to the payroll record number. Sage 100 Contractor users with cheques pre-printed with cheque numbers should process cheque runs in sequence.

Printing direct deposit payroll cheques creates and prints a non-negotiable cheque and supplies the employee with a record of the payroll. You have three options for printing direct deposit cheques in **5-2-4 Payroll Cheques**.

Direct deposit is limited to employee payroll. Sage 100 Contractor does not support electronic payment or electronic transfer of funds for such things as:

- Federal or provincial taxes
- Child care support payments
- Wage garnishment

| Links to more information . . . [About setting up direct deposit](About_setting_up_direct_deposit.md) [About Direct Deposit File Manager](About_Direct_Deposit_File_Manager.md) [Setting up company information for direct deposit](Setting_up_company_information_for_direct_deposit.md) [Setting up employee records for direct deposit](Setting_up_employee_records_for_direct_deposit.md) [Creating a direct deposit file](Creating_a_direct_deposit_file.md) [Processing direct deposit](Processing_direct_deposit.md) |
|---|
