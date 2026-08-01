<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/9-Estimating__Parts_and_Assemblies_/Declaring_the_values_for_variables.htm (Sage 100 Contractor help v20.5) -->

### Declaring the values for variables

Note: This functionality is available only if you have the [Estimating Module](http://www.na.sage.com/sage-100-contractor/modules/estimating).

Important! The math evaluator requires that you declare all variables. If the math evaluator finds undeclared variables in takeoff formulas, the program proceeds through the calculations using zero for each undeclared variable. Then it displays a message telling you that you have undeclared variables and lists the lines where they are located in the takeoff so that you can declare them.

To solve a formula, assign a value to each variable in each takeoff grid. Suppose that you entered an assembly for cement in the takeoff grid, and it contains a formula to calculate the cubic yards of cement needed for the project. For each variable, enter a description and the units of measurement. In the **Quantity** column, enter the value. Then in the **Formula** column, set the variable equal to the **Quantity** column. The values must precede the formulas; otherwise, Sage 100 Contractor will not use the values.

| Row | Assmb# | Dscrpt | Unit | Qty | Formula |
|---|---|---|---|---|---|
| 1 |  | Length | feet | 15 | L=Q |
| 2 |  | Width | feet | 20 | W=Q |
| 3 |  | Depth | feet | 1 | D=Q |
| 4 | 3001 | Cement | CuYd | 11.11 | Q=L*W*D/27 |

You can declare new values for variables in the same takeoff grid. Some formulas might use the same variables but will require different values. Simply declare the new values on the lines preceding the formula that will use them. In a takeoff grid, Sage 100 Contractor uses the assigned values until you declare new values for those same variables.

Important! Using undeclared variables in takeoffs may result in inconsistent or incorrect calculations. We recommend that you declare all variables in takeoffs in order for the calculations to be correct.

| Links to more information . . . [About formulas](About_formulas.md) [Entering project values](Entering_project_values.md) [About reserved variables](About_reserved_variables.md) [Types of calculations you can perform in formulas](Types_of_calculations_you_can_perform_in_formulas.md) |
|---|
