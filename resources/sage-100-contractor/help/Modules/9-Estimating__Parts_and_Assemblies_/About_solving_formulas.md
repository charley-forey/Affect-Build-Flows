<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/9-Estimating__Parts_and_Assemblies_/About_solving_formulas.htm (Sage 100 Contractor help v20.5) -->

### About solving formulas

Note: This functionality is available only if you have the [Estimating Module](http://www.na.sage.com/sage-100-contractor/modules/estimating).

Formulas provide the ability to enter mathematical equations that can be used to determine quantities or prices. In a takeoff, you must declare the values of the variables in a line preceding the line that contains the formula.

Important!

- When using bid items or phases, you have to declare the value of each variable in each grid.
- Sage 100 Contractoruses the value that you assign to a variable until you declare a new value.
- If you do not declare a value for a variable, Sage 100 Contractor ignores the variable and does not assign any value to it.

In any equation, first indicate what you are solving, such as a price, quantity, or storage of a value that you will use in a later formula. Suppose that you want to solve for the cubic feet in a cement slab. Q represents the quantity, with L representing the length in feet, W representing the width in feet, and T representing the thickness in feet. The formula should be: Q = L * W * T.

In the above formula, Sage 100 Contractor solves the equation and inserts the result in the **Quantity** cell. Sage 100 Contractor reserves several variables for specific purposes: Q for quantity, P for price, and TLU for total labour units. When solving for a price, Sage 100 Contractor inserts the result in the **Price** cell.

The variable Q = TLU is used to accumulate the total labour units (TLU) for specific groupings within a takeoff, or for the entire takeoff. Placement of the variable will dictate where the accumulated results will be displayed in the grid.

The reserved variable for Total Labour Units (TLU) totals the labour units by looking at each line of the takeoff. On each line, Sage 100 Contractor finds parts with **Cost Type = 2-Labour** (based on the **Part#** column) and multiplies the **Labour Unit** (as defined in **9-2 Parts**) by the extended quantity of the takeoff line in the grid. The accumulation of these results is assigned to the TLU variable and displayed in the grid where the formula Q = TLU is next placed. TLU is then reset to 0 and the next accumulation will begin; results will then display at the next occurrence of the variable.

Always begin an equation with the variable for the solution. In the equation W = Q, the solution W equals the value of quantity Q, which is the value in the **Quantity** cell. Whereas in Q = W, the solution for quantity Q equals the value of W. In this case, Sage 100 Contractor takes the declared value for W and inserts it in the **Quantity** cell.

| Links to more information . . . [About Total Labour Units (TLU)](About_Total_Labor_Units__TLU_.md) [Declaring the values for variables](Declaring_the_values_for_variables.md) [About reserved variables](About_reserved_variables.md) [Types of calculations you can perform in formulas](Types_of_calculations_you_can_perform_in_formulas.md) |
|---|
