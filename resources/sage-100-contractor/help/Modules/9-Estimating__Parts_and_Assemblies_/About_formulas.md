<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/9-Estimating__Parts_and_Assemblies_/About_formulas.htm (Sage 100 Contractor help v20.5) -->

### About formulas

Note: This functionality is available only if you have the [Estimating Module](http://www.na.sage.com/sage-100-contractor/modules/estimating).

Formulas let you shorten the steps necessary to complete a takeoff. Suppose you have a concrete assembly that was designed for pouring slabs. The assembly contains the necessary parts including the forming stakes, rebar, forming ties, and concrete. Because the part quantities depend on the size of the slab, figuring out the part quantities each time you use the assembly can create a great deal of work.

Instead of performing all the necessary mathematical calculations by hand, you can enter a formula and have Sage 100 Contractor calculate dimensions, quantities, or prices for individual parts or assemblies, and even account for waste material costs. In the above example, you could include a formula to compute the cubic yards of concrete that you might need to pour.

With each assembly record, you can enter the formula using variables, which replace actual dimensions. A variable acts as a placeholder for the actual information. Each time that you insert an assembly, declare the values of the variables contained in the formula above the assembly. When you calculate the takeoff, Sage 100 Contractor replaces the variables with the declared values and determines the result.

Some assemblies or parts use values that do not change through a takeoff such as the enclosed square footage or exterior building perimeter. In this case, a takeoff uses one value for the variable throughout a takeoff. Rather than declaring the value for each appearance of the variable, declare the value one time on the **Project Values** tab.

You can assign a formula to individual items in an assembly or to the assembly itself. By assigning a formula to the assembly, Sage 100 Contractor calculates the results for the entire assembly. For example, you have an assembly for roofing that uses a formula to calculate the entire square footage, including overhangs and the roof pitch. Individual items in an assembly can also use formulas. In the same roofing assembly, a line item for roofing paper uses a formula to calculate the quantity of paper necessary to complete the work plus waste.

In a takeoff, you can use formulas with individual parts. Unlike assemblies, part records do not allow you to include formulas. As you enter each part in a takeoff, enter the formula that you want to use with it.

| Links to more information . . . [About variables](About_variables.md) [About Total Labour Units (TLU)](About_Total_Labor_Units__TLU_.md) [Entering project values](Entering_project_values.md) [About solving formulas](About_solving_formulas.md) [Types of calculations you can perform in formulas](Types_of_calculations_you_can_perform_in_formulas.md) [Compensating for materials waste in your takeoffs](Compensating_for_materials_waste_in_your_takeoffs.md) |
|---|
