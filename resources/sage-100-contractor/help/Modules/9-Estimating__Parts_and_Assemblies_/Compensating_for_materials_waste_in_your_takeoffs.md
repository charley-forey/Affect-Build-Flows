<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/9-Estimating__Parts_and_Assemblies_/Compensating_for_materials_waste_in_your_takeoffs.htm (Sage 100 Contractor help v20.5) -->

### Compensating for materials waste in your takeoffs

Note: This functionality is available only if you have the [Estimating Module](http://www.na.sage.com/sage-100-contractor/modules/estimating).

Waste materials add to the job costs and impact profitability. By compensating for the costs of waste materials generated during certain job tasks, the accuracy of takeoffs improves. As the estimates become more accurate, jobs become more profitable.

Suppose that in creating a takeoff for the construction of a new home you calculate the number of pounds of nails necessary to complete the job and no more. During the construction, the crew falls short on nails. Consequently, you incur an unforeseen job cost for the purchase of additional nails, which cuts into profits. A single instance such as this might not seriously impact the profitability of a single job. However, consider the effect on profitability when dealing with a variety of materials that generate large amounts of waste.

The following are examples of materials that produce large amounts of waste:

- Concrete and grout
- Concrete reinforcing materials
- Brick and masonry block
- Screws, nails, and other fasteners
- Rough lumber and plywood
- Electrical conduit and wire
- Building wrap and visquene
- Finish lumber
- Roofing materials

Keep your takeoffs simple. Waste factors are not necessary for all materials. To compensate for waste, select from two methods to adjust materials quantities. In the first method, adjust the part quantities in assemblies to include possible waste. This method is faster in its initial setup; however, as you use the assemblies, it is not as easy to go back and refine the part quantities.

With the second method, you can create project values for waste factors. As you build formulas that calculate part quantities, whether for individual parts or parts in assemblies, you can include a variable for waste. Setting up the waste factors as project values allows you to refine waste factors as you use them.

Suppose that 5 percent of the cement you pour always becomes wasted material. To calculate the quantity plus waste, you need to increase the quantity by 5 percent. To do this, multiply the quantity formula by 105 percent (expressed as 1.05). The examples below illustrate how to use project values for waste factors.

| Item | Formula | Description |
|---|---|---|
| Visquene | Q = “quantity formula” * WCF | WCF (Waste Concrete Film): Declare the value equal to 1.2 to allow for overlapping of adjacent rolls and loss at the edges of the slab due to partial roll width. |
| Rebar | Q = “quantity formula” * WCR | WCR (Waste Concrete Reinforcing): Declare the value equal to 1.25 to allow 2 foot overlap when bars are spliced together and loss due to unused short pieces of bar. |
| Concrete | Q = “quantity formula” * WCR | WCR (Waste Concrete): Declare the value equal to 1.2 to allow for spillage. |

| Links to more information . . . [Entering project values](Entering_project_values.md) [Declaring the values for variables](Declaring_the_values_for_variables.md) [About reserved variables](About_reserved_variables.md) [About solving formulas](About_solving_formulas.md) [Entering assemblies](Entering_assemblies.md) |
|---|
