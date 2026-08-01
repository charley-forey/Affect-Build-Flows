<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/9-Estimating__Parts_and_Assemblies_/About_Total_Labor_Units__TLU_.htm (Sage 100 Contractor help v20.5) -->

### About Total Labour Units (TLU)

Note: This functionality is available only if you have the [Estimating Module](http://www.na.sage.com/sage-100-contractor/modules/estimating).

The formula Q = TLU is used to accumulate the total labour units (TLU) for specific groupings within a takeoff or for the entire takeoff. Placement of the variable will dictate where the accumulated results are displayed in the grid.

The reserved variable for Total Labour Units (TLU) totals the labour units by looking at each line of the takeoff. On each line, Sage 100 Contractor finds parts with **Cost Type = 2-Labour** (based on the **Part#** column) and multiplies the **Labour Unit** (as defined in **9-2 Parts**) by the extended quantity of the takeoff line in the grid. The accumulation of these results is assigned to the TLU variable and displayed in the grid where the formula Q = TLU is next placed. TLU is then reset to 0 and the next accumulation will begin; results will then display at the next occurrence of the variable.

Note: If a part has been assigned a labour part number in addition to labour units, then that particular line of the takeoff does not affect the TLU. When the part was initially added to the takeoff, the labour part was included so the total labour for that part will be accounted for in the takeoff.

| Links to more information . . . [About variables](About_variables.md) [Entering project values](Entering_project_values.md) [About solving formulas](About_solving_formulas.md) [Types of calculations you can perform in formulas](Types_of_calculations_you_can_perform_in_formulas.md) |
|---|
