<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/9-Estimating__Parts_and_Assemblies_/Important_information_about_updating_prices_and_adding_new_parts_simultaneously.htm (Sage 100 Contractor help v20.5) -->

### Important information about updating prices and adding new parts simultaneously

Note: This functionality is available only if you have the [Estimating Module](http://www.na.sage.com/sage-100-contractor/modules/estimating).

In the **9-6 Add Parts/Update Prices** window, you can choose to add new parts to your database from a source file while updating your part prices. Because you may be doing this on a regular basis and your vendor may change their file configuration or numbering scheme, it is important to understand your existing Sage 100 Contractor parts structure before performing this procedure.

When performing this procedure, there are several things to be aware of:

- Any parts in the source file that are not currently in your parts database will be added to your parts database. You cannot select specific parts or ranges of parts to add.
- When updating prices and adding parts, all **Destination Fields** are available for mapping, but only **Description**, **Unit**, **Default Cost** and **Billing Amount** (if mapped) are updated. Any new parts are added.

If you have selected **Vendor Price** from the **Update Part Prices** menu, there are additional considerations:

- If you choose to update your part’s **Vendor Price** and to add parts at the same time, the prices on the **Vendor** window are updated. However, the update process is not going to attach your selected vendor to any new parts.
- In order for a new added part to have a price entered in the **9-2 Parts** window, you must map an additional field(s) from the **Source File Fields** to the **Default Cost** and/or **Billing Amount Destination Fields** because the **Vendor Price** can only be updated on existing **Vendor** windows.

Note: If this is the first time you are performing this combined process or if you are unsure about what fields in your database are affected, we recommend that you perform these processes individually.

| Links to more information . . . [Updating prices and adding new parts simultaneously](Updating_prices_and_adding_new_parts_simultaneously.md) [More about adding parts-updating prices](More_about_adding_parts-updating_prices.md) [Entering vendor prices for part records](Entering_vendor_prices_for_part_records.md) [About file types for adding parts-updating prices](About_file_types_for_adding_parts-updating_prices.md) [Adding parts](Adding_parts.md) [Updating part prices](Updating_part_prices.md) |
|---|
