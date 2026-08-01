<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/10-Scheduling/About_lead_and_lag_time_in_scheduling.htm (Sage 100 Contractor help v20.5) -->

### About lead and lag time in scheduling

With each dependency, you can assign lead time or lag time. Lead or lag allows you to further adjust the starting date of a task in relation to its predecessor.

#### Lag time

Lag provides a delay between tasks. For example, in the **Predecessor** window for the task **Stripping Forms**, you assign the task **Pouring the Foundation** as its predecessor. Because you cannot strip the forms until the concrete is poured, click **1-Start/Finish** in the **Relation** list. However, the forms cannot be removed until the concrete has cured, so enter 3 in the **Lead/Lag**text box. When looking at the schedule, the **Stripping Forms** task cannot start until three days after the completion of **Pouring the Foundation**. Therefore, you enter lag as a positive value.

#### Lead time

Lead provides an overlap between tasks. For example, in the **Predecessor** window for the task **Electrical**, you assign the task **Roofing** as its predecessor and enter **1-Start/Finish** in the **Relation** column. An electrician can begin wiring the building a couple of days before the roofing task is completed since the structure is now partially covered by roofing. In the **Lag/Lead** column, enter -2. When looking at the schedule, the **Electrical** task can begin two days before the finish of the **Roofing** task. Therefore, you enter lead as a negative value.

| Links to more information . . . [About dependencies in scheduling](About_dependencies_in_scheduling.md) [Accelerating schedules](Accelerating_schedules.md) [Automatically assigning the start-finish dependency](Automatically_assigning_the_start-finish_dependency.md) |
|---|
