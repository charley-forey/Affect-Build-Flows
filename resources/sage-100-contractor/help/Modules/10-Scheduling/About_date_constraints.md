<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/10-Scheduling/About_date_constraints.htm (Sage 100 Contractor help v20.5) -->

### About date constraints

In addition to using dependencies, durations, and lag or lead times, you can further constrain when a task begins or ends. In the schedule grid, you can enter dates for a task that restrict when it may begin or end.

| Column | Description |
|---|---|
| Fixed Date | Establishes a permanent date when a task must begin. A fixed date does not move when a schedule is delayed or accelerated. Most tasks do not use a fixed date, and begin or end in relation to the predecessors tasks. |
| Not Before | Establishes the earliest date when a task can begin. Though a task cannot begin before the indicated date, the task can begin after the date. If you provide a date in the **Not Before** column for a critical task, Sage 100 Contractor adjusts the start and finish dates for subsequent tasks. |
| Not After | Establishes the latest date when a task can begin. If you provide a date in the **Not After** column for a critical task, Sage 100 Contractor adjusts the start and finish dates for subsequent tasks. |
| Late Start | Displays the last day a non-critical task can begin and remain on schedule. Only for tasks with [float](../../Glossary/Glossary_-_float.md). |
| Late Finish | Displays the last day a non-critical task can end and remain on schedule. Only for tasks with float. |

| Links to more information . . . [About dependencies in scheduling](About_dependencies_in_scheduling.md) [About lead and lag time in scheduling](About_lead_and_lag_time_in_scheduling.md) [Accelerating schedules](Accelerating_schedules.md) [Automatically assigning the start-finish dependency](Automatically_assigning_the_start-finish_dependency.md) |
|---|
