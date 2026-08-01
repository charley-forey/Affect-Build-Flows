<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/5-Payroll/About_payroll_record_errors.htm (Sage 100 Contractor help v20.5) -->

### About payroll record errors

Payroll record errors result from inaccurate timecard entry, employee record setup, or payroll calculation setup. Before attempting to correct the error, determine its cause. In most cases correct the setup problem first, and then correct the payroll record error.

Important! If the wrong payroll posting accounts were set up in the **5-3-3 Employee Positions** window, void the erroneous payroll records. Voiding the payroll records first ensures that reversing transactions are posted to the same accounts. Then enter the correct posting accounts in the **5-3-3 Employee Positions** window. Finally, enter the correct payroll records.

#### There are two status settings:

- **1-Open.**Sage 100 Contractor has not created cost records, printed pay cheques, or posted payroll to the general ledger. You can edit most information in the record. If the record is a duplicate, you can delete it. If you have assigned the wrong payroll type, void the record.
- **2-Computed.**If you have not printed a cheque, void the original record. Then enter a new record with the correct data. You can trial-compute the record to make sure all the data is correct before the final-compute.

If you printed a cheque but did not issue it to the employee, void the original record. Then enter a new record with the correct data. You can trial-compute the record to make sure all the data is correct before the final-compute. To maintain an accurate audit trail, cancel the cheque number of the erroneous cheque.

If you issued the cheque to the employee, void the original record. Then enter a payroll advance for the net amount of the cheque. To maintain an accurate audit trail, enter the original cheque number in the **Cheques Number** box. Then enter a new record with the correct data. You can trial-compute the record to make sure all the data is correct before the final-compute.

Sage 100 Contractor recovers the payroll advance from the subsequent pay cheques. If you overpaid the employee due to error, and the subsequent cheque results in a net $0 amount, print the cheque to plain paper and provide a copy to the employee. If you underpaid the employee due to error, print the new pay cheque and give it to the employee. Always provide the employee with a copy of the correct payroll information.

| Links to more information . . . [Voiding payroll records](Voiding_payroll_records.md) [Entering timecards](Entering_timecards.md) [About employee positions](About_employee_positions.md) [About pay types](About_pay_types.md) [Voiding payroll records and re-entering the correct data for previously issued cheques](Voiding_payroll_records_and_re-entering_the_correct_data_for_previously_issued_checks.md) [Canceling cheque numbers](../1-General_Ledger/Cancelling_check_numbers.md) |
|---|
