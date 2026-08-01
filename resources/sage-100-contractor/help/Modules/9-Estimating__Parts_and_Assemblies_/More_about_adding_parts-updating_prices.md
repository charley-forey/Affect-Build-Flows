<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/9-Estimating__Parts_and_Assemblies_/More_about_adding_parts-updating_prices.htm (Sage 100 Contractor help v20.5) -->

### More about adding parts-updating prices

Complete functionality is only available if you have purchased the [Estimating Add-On Module](http://www.na.sage.com/sage-100-contractor/modules/estimating).

Some functionality is only available if you have purchased the [Estimating Add-On Module](http://www.na.sage.com/sage-100-contractor/modules/estimating) or the [Inventory Add-on Module](http://na.sage.com/sage-100-contractor/modules/service-management) or the [Service Receivables Add-on Module](http://na.sage.com/sage-100-contractor/modules/service-management).

You can add parts and update prices, as needed or on a regular basis, from many different vendors or pricing services’ databases. Suppose that you receive a disk from a local vendor that contains an electronic file with information on all the parts they can provide to you. Before adding parts or updating prices from this parts database into your company, determine the organization of information within the file. Carefully examine what information it contains and the order and format in which it appears. Usually, each line in the file represents a different part. You can then map the incoming information to existing fields in Sage 100 Contractor.

Important! You should always back up your database before beginning these procedures.

- When adding parts or updating prices, you must complete a number of selections.
- You have the option to assign part numbers to the records that you add.
- When updating prices, you can also specify whether you want to update the default cost and billing amount or the vendor price.
- You can choose to add new parts to your database while updating your part prices from a source file. It is important to understand your existing Sage 100 Contractor parts structure before performing this procedure.
- You must select the appropriate source file.
- Source file fields must be the same alpha/numeric type as required in Sage 100 Contractor. For example, **Part Number**, **Cost Codes**, and **Cost Types** must be numeric.
- Some electronic files contain a heading as the first line (instead of actual parts data) and this information should be ignored as it is imported. Select the option to ignore the first line.

#### Field Mapping and Destination Fields

Adding parts and updating prices involves field mapping. Suppose that a local vendor has supplied you with their database of parts. In the **9-6 Add Parts/Update Prices** window, you can browse to and select the vendor file you want to import. The minimum amount of information that you must enter is **Part#**, **Description**, and **Unit**.

The example contains the following information in the **Source File Fields** from the source file that you have selected: part number, description, default price, selling price, and unit. Before you can add parts or update the prices, you use the **Destination Fields** to determine what fields in Sage 100 Contractor are to be populated with the information from the vendor’s database and where to place it in the Sage 100 Contractor parts database.

By selecting **Source File Fields** and using the arrows to specify the **Destination Fields**, you will create the desired mapping. In some cases, the outside database might contain information that does not directly relate to any of the **Destination Fields**. If you want to include the information, use the **User Def1** and **User Def2** (user-defined fields) as available fields for storing related information.

Note: You can import several different types of files. Be sure to review the vendor’s file type before importing.

| Links to more information . . . [About file types for adding parts-updating prices](About_file_types_for_adding_parts-updating_prices.md) [Saving templates for adding parts-updating prices](Saving_templates_for_adding_parts-updating_prices.md) [Adding parts](Adding_parts.md) [Entering parts](Entering_parts.md) [Important information about updating prices and adding new parts simultaneously](Important_information_about_updating_prices_and_adding_new_parts_simultaneously.md) [Assigning specifications files to part records](Assigning_specification_files_to_part_records.md) |
|---|
