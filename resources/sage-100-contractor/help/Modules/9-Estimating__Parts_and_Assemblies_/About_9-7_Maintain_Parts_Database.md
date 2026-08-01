<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/9-Estimating__Parts_and_Assemblies_/About_9-7_Maintain_Parts_Database.htm (Sage 100 Contractor help v20.5) -->

### About 9-7 Maintain Parts Database

Notes:

- Complete functionality is available only if you have purchased the [Estimating Add-On Module](http://www.na.sage.com/sage-100-contractor/modules/estimating).
- Some functionality is available only if you have purchased the [Estimating Add-On Module](http://www.na.sage.com/sage-100-contractor/modules/estimating), the [Inventory Add-on Module](http://na.sage.com/sage-100-contractor/modules/service-management), or the [Service Receivables Add-on Module](http://na.sage.com/sage-100-contractor/modules/service-management).

In the **9-7 Maintain Parts Database** window, you can make changes to the parts database or set up the vendor preference list for part records.

To determine the scope of an update, under **Selection Criteria**, select specific part numbers, part classes, a range of parts, or the entire database. In the **Field** list, click the field on which you want to base the update. Then in the **Operator** list, click the mathematical operator such as equal to or greater than. Then in the **Value** text box, enter the value for which you are searching.

Under **Fields to Change**, specify the information you want to change. Suppose that you add parts from a database that uses cost codes that differ from your own. In the **Maintain Parts Database** window, you set up the selection criteria to choose only those cost codes that you want to change. Then in the **Fields** list you select **Cost Code**, in the **Operator** list you select **Replace With**, and in the new **Value** text box you enter the cost code that you want to use. When you update the database, Sage 100 Contractor automatically replaces the data in the cost code box from the selected part records with the information you entered in the new **Value** text box.

Instead of replacing information, you can factor it. Factoring allows you to increase or decrease values. For example, your lumber supplier has increased prices by 15 percent. You set up the selection criteria to choose only the lumber parts. Then in the **Fields** list you select **Default Cost**, in the **Operator** list you select **Factor by**, and in the new **Value** text box you enter 1.15, which multiplies the existing amounts by 15 percent.

You can also use the **Maintain Parts Database** window under **Assign Vendor Preferences** to set up vendor preference lists in part records, which allows you to rank the vendors in order of preferred use. Before creating a takeoff, you can elect to use only preferred vendors for parts. Then each time you enter an assembly or part in the takeoff, Sage 100 Contractor uses the price for the preferred vendor.

Caution! To avoid a possible loss of data, always make a backup file before using the **9-7 Maintain Parts Database** window.

| Links to more information . . . [Maintaining the parts database](Maintaining_the_parts_database.md) [Deleting ranges of parts](Deleting_ranges_of_parts.md) [About vendor pricing](About_vendor_pricing.md) [About assembly and part classes](About_assembly_and_part_classes.md) [Updating part costs using the preferred vendor](Updating_part_costs_using_the_preferred_vendor.md) |
|---|
