<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/9-Estimating__Parts_and_Assemblies_/Updating_prices_and_adding_new_parts_simultaneously.htm (Sage 100 Contractor help v20.5) -->

### Updating prices and adding new parts simultaneously

Note: This functionality is available only if you have the [Estimating Module](http://www.na.sage.com/sage-100-contractor/modules/estimating).

Caution! Always make a backup of your data before you update prices or add parts.

#### To update prices and add new parts simultaneously:

|  | 1 | Open **9-6 Add Parts/Update Prices**. |
|---|---|---|

|  | 2 | Select **Add New Parts**. |
|---|---|---|

|  | a | If you want to automatically assign part numbers to the imported parts, select **Assign Part#**. |
|---|---|---|

|  | b | In the **Start#** text box, enter the starting number to assign to the new parts. This must be in numeric form only. |
|---|---|---|

|  | 3 | Select **Update Part Prices** and complete the following as necessary: |
|---|---|---|

|  | a | If you want Sage 100 Contractor to match parts based on the **Alpha Part#**, select **Match Alpha Part#**. |
|---|---|---|

|  | b | **Default Cost/Billing Amount** is selected by default. |
|---|---|---|

Note: Vendor-specific prices will not be applied to new parts but will be applied to **Default Cost/Billing Amount**.Sage 100 Contractor updates the default cost/billing amount for parts in the database.

|  | a | If you want Sage 100 Contractor to update the **Vendor Price** instead of the **Default Cost/Billing Amount** in the **9-2 Parts** window, select **Vendor Price**. |
|---|---|---|

|  | b | If you have selected **Vendor Price** as your update method, select from the drop-down list the vendor whose source file you are using. |
|---|---|---|

|  | 4 | Choose **Select Source File**, browse, and then select the database file to use for adding parts. The path name for the source file appears in the window. |
|---|---|---|

|  | a | The **Source File Fields** under **Field Mapping** appears. |
|---|---|---|

|  | b | If the source file contains descriptive headers or labels as its first line, select **First Line is Header**. |
|---|---|---|

This line is ignored during the add/update function.

|  | 5 | Map which **Destination Fields** from the Sage 100 Contractor database correspond to the imported **Source File Fields**. |
|---|---|---|

|  | a | On the left side of the window, under **Field Mapping**, select the **Source File Fields** row and the **Destination Fields** cell that you want to map. |
|---|---|---|

|  | b | Under **Destination Fields** on the right side of the window, select the corresponding Sage 100 Contractor field and click the left arrow key. Alternately, select the Sage 100 Contractor field, and then select ENTER. Alternatively, you can double-click the field. |
|---|---|---|

Important! At minimum, you must select **Part#**, **Description**, and **Unit** as **Destination Fields** to be mapped.

The part numbers from the vendor's source file must match the **Part#** in Sage 100 Contractor in order for the update to properly occur.

|  | 6 | Repeat step 5 until you have mapped all fields you want to import to Sage 100 Contractor from the external database. |
|---|---|---|

|  | 7 | Click **Add/Update**. |
|---|---|---|

|  | 8 | If any failures occur during the process, an error log appears for your review. |
|---|---|---|

Note: You can remove field mapping for a specific row by selecting the **Destination Field** and use the right arrow key to move it back to the **Destination Fields** list.

Tip: You can use your selections to save as a template for future use.

| Links to more information . . . Updating prices and adding new parts simultaneously [More about adding parts-updating prices](More_about_adding_parts-updating_prices.md) [Entering vendor prices for part records](Entering_vendor_prices_for_part_records.md) [About file types for adding parts-updating prices](About_file_types_for_adding_parts-updating_prices.md) [Adding parts](Adding_parts.md) [Updating part prices](Updating_part_prices.md) |
|---|
