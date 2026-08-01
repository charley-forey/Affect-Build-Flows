<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/9-Estimating__Parts_and_Assemblies_/Updating_part_prices.htm (Sage 100 Contractor help v20.5) -->

### Updating part prices

Note: This functionality is available only if you have the [Estimating Module](http://www.na.sage.com/sage-100-contractor/modules/estimating).

Caution! Always make a backup of your data before you add parts or update prices.

Consider the following points before updating part prices:

- Updating only requires a **Part#**.
- You can remove field mapping for a specific row by selecting the **Destination Field** and using the right arrow key to move it back to the **Destination Fields** list.
- The part numbers from the vendor's source file must match the **Part#** in Sage 100 Contractor in order for the update to properly occur.

#### To update part prices:

|  | 1 | Open **9-6 Add Parts/Update Prices**. |
|---|---|---|

|  | 2 | Select **Update Part Prices** and complete the following as necessary: |
|---|---|---|

|  | a | If you want Sage 100 Contractor to match parts based on the **Alpha Part#**, select **Match Alpha Part#**. |
|---|---|---|

|  | b | **Default Cost/Billing Amount** is selected by default. Sage 100 Contractor updates the default cost/billing amount for parts in the database. |
|---|---|---|

Note: Vendor-specific prices will not be applied to new parts but will be applied to **Default Cost/Billing Amount**.

|  | c | If you want Sage 100 Contractor to update the **Vendor Price** instead of the **Default Cost/Billing Amount** of the **9-2 Parts** window, select **Vendor Price**. |
|---|---|---|

|  | d | If you have selected **Vendor Price** as your update method, in the drop-down list, select the vendor whose source file you are using. |
|---|---|---|

|  | e | The path name for the source file appears in the window. |
|---|---|---|

|  | 3 | Choose **Select Source File**, browse, and then select the database file to use for adding parts. |
|---|---|---|

|  | a | The **Source File Fields** under **Field Mapping** appears. |
|---|---|---|

|  | b | If the source file contains descriptive headers or labels as its first line, select **First Line is Header**. This line is ignored during the import function. |
|---|---|---|

|  | 4 | Map the **Destination Fields** from the Sage 100 Contractor database that correspond to the imported **Source File Fields**. |
|---|---|---|

|  | a | On the left side of the window, under **Field Mapping**, select the **Source File Fields** row and the **Destination Fields** cell that you want to map. |
|---|---|---|

|  | b | Under **Destination Fields** on the right side of the window, select the corresponding Sage 100 Contractor field by double-clicking the field. Alternately, select the Sage 100 Contractor field and then select ENTER or the arrow key to map the field. |
|---|---|---|

|  | 5 | Repeat step 4 until you have mapped all fields you want to import to Sage 100 Contractor from the external database. |
|---|---|---|

|  | 6 | Click **Add/Update**. |
|---|---|---|

|  | 7 | If any failures occur during the process, an error log appears for your review. |
|---|---|---|

Tip: You can use your selections to save as a template for future use.

| Links to more information . . . [About vendor pricing](About_vendor_pricing.md) |
|---|
