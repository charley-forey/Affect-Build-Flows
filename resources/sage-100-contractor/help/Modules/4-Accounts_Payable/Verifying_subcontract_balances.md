<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/4-Accounts_Payable/Verifying_subcontract_balances.htm (Sage 100 Contractor help v20.5) -->

### Verifying subcontract balances

When saving a payable invoice for a vendor, Sage 100 Contractor refers to the **Set Over Subcontract Warning** option to determine if the invoice amount exceeds the subcontract balance. If the payable invoice does exceed the balance, Sage 100 Contractor provides you with a warning.

Notes:

- After setting, the warning stays on until it is manually changed. In addition, you must be a company administrator to turn this feature on and off.
- When Subcontracts are exported from **9-5 Takeoffs**, the warning that the subcontract exceeds the budget amount plus approved change orders for the job/phase/cost code/ cost type combination is not displayed. After exporting subcontracts through **9-5 Takeoffs**, you should run the **6-1-12-21 Committed Costs** report for the correct job to verify that subcontracts have not exceeded the budget.
- To enable the program alert for **Payable invoices exceed subcontract** you must have a setting of Warning for the Message Type.

#### To verify subcontract balances:

1. Open **4-2 Payable Invoices/Credits**.
2. Select **Options**, then select **Set Over Subcontract Warning**.
3. In the **Invoice Over Subcontract Warning Settings** window, select the applicable fields.
4. In the **Message Type** dropdown, the choices are mutually exclusive. Select one of the following:
   
   - **No message.** No message is generated. All options for tolerance are grayed out.
   - **Warning.** A warning and/or alert is generated, but you are allowed to save the record.
   - **Not allow.** A warning and/or alert is generated, but you are not allowed to save the record.
5. If you select **Warning** or **Not Allow**, you must select one of the following choices in the **Tolerance Type** list:
   
   - No tolerance
   - Flat amount
   - Percent
   - Percent/not to exceed
6. Once a **Tolerance Type** has been selected, enter the amount or percent for the type:
   
   - **Flat amount.** Enter the amount in the Tolerance Amount text box.
   - **Percent.** Enter the percent in the Tolerance Percent text box.
   - **Percent/not to exceed.** Enter the percent of the subcontract line contract amount allowed in the **Tolerance Percent** text box, and the amount of tolerance in the **Tolerance Amount Not To Exceed** text box.
7. Click **OK**.

| Links to more information . . . [Entering payable invoices](Entering_payable_invoices.md) [Options for saving payable invoices](Options_for_saving_payable_invoices.md) |
|---|
