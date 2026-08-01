<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/9-Estimating__Parts_and_Assemblies_/About_variables.htm (Sage 100 Contractor help v20.5) -->

### About variables

Note: This functionality is available only if you have the [Estimating Module](http://www.na.sage.com/sage-100-contractor/modules/estimating).

Each time you create a takeoff, the dimensions and prices and quantities of materials change relative to the project specifications, but the formulas generally remain the same. You could rebuild each formula in a takeoff using the information from the plans, but a much quicker way is to build the formulas using variables.

Variables act as placeholders for actual numeric values. The variables allow you to build formulas and save them in the assemblies without having to enter actual figures until you create a takeoff. As you build a takeoff, you assign a numeric value to each variable that you are using. Sage 100 Contractor substitutes the declared values for the variables and computes the results.

Important! Using undeclared variables in takeoffs may result in inconsistent or incorrect calculations in Version 14 and all previous versions. We recommend that you declare all variables in takeoffs in order for the calculations to be correct.

Suppose that you are creating a takeoff for a job to build a shed. As part of the job, you need to pour a cement slab. You can use a formula to calculate the cubic yards of cement necessary for the pour. In the takeoff, enter the variables for the length, width, and depth of the slab and declare the value for each. The plans require a 15 by 20 by 1 foot slab, so you enter L=15, W=20, and D=1 in the takeoff grid.

The cement assembly already contains the formula Q = L * W * D / 27, which defaults to the **Formula** column when you enter the assembly in the takeoff. When you calculate the takeoff, Sage 100 Contractor uses the declared values in place of the variables in the cement assembly and inserts the result in the **Quantity** column of the cement assembly.

The declared values for variables are limited to the grid in which they are declared. After you declare a value for a variable, Sage 100 Contractor uses the value with subsequent formulas in that takeoff grid. Suppose that you use phases with the takeoff for the shed, and enter the exterior framing and siding assemblies in a different phase from the concrete slab. Though the exterior framing and siding assemblies use the same dimensions for length and width as the cement assembly, Sage 100 Contractor does not refer to the grid containing the cement assembly to determine values. Rather, you must declare the values for the variables in the phase containing the exterior framing and siding assemblies.

If the declared values for variables are constant across multiple takeoff grids, set them up as project values. Project values allow you to declare the value once for a variable and Sage 100 Contractor uses it throughout the takeoff. Continuing with the example, you could declare the values length, width, and depth in the **Project Values** tab. Sage 100 Contractor would use the declared values in the respective phases for concrete, and framing and siding.

You can always declare new values for variables. In some instances, formulas share variables but require different values. Simply declare the new values in the lines preceding the formula requiring them. Sage 100 Contractor uses those values for the variables through the remainder of the takeoff grid.

| Links to more information . . . [About formulas](About_formulas.md) [Entering project values](Entering_project_values.md) [Declaring the values for variables](Declaring_the_values_for_variables.md) [About reserved variables](About_reserved_variables.md) [Types of calculations you can perform in formulas](Types_of_calculations_you_can_perform_in_formulas.md) |
|---|
