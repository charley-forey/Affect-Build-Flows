<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/6-Project_Management/About_RFP_and_RFI_numbering_by_job_and_phase.htm (Sage 100 Contractor help v20.5) -->

### About RFP and RFI numbering by job and phase

Note: This functionality is available only if you have the [Document Control Module](http://www.na.sage.com/sage-100-contractor/modules/project-management).

Sage 100 Contractor supports RFP and RFI numbering by job, and if the job has phases, by job and phase. This feature makes it easier to keep track of RFIs and RFPs because they are associated with the job in which they were initiated.

Because this is a new feature, when you first open the **6-11-1 Requests for Proposal** or **6-11-2 Requests for Information** windows after an upgrade installation, the program displays a default setting window with instructions for changing the RFP (**Request#** box) and RFI (**RFI#** box) default setting to **Next by Job** default instead of the previous default setting of **Next**.

Tip: With new installations, the default setting is **Next by Job** and the program does not display this window.

The following table describes the actions of each button on the default settings window when you click it.

| Button | Action |
|---|---|
| Yes | Changes the default setting for **Request#** or **RFI#** to Next by Job. |
| No | Retains **Next** as the default setting. |
| Ask Me Later | Retains **Next** as the default setting, but the program prompts you to make a selection by displaying the default settings window each time you open either **6-11-1 Requests for Proposal** or **6-11-2 windows**. |
| Help | Opens this Help topic. |

#### Rules for using RFP/RFI Numbering by Job

The program uses this functionality using specific rules. Following are some ideas to keep in mind.

- When beginning a new numbering scheme for your RFP/RFIs, type a pattern like this [number][hyphen][number] (without brackets), for example, 216-1, with 216 representing the job number and 1 representing the first RFP or RFI record. When creating the next new RFP or RFI record, the program looks for the final hyphen (—) and increments the number following the it by 1 in the new record, for example, 216-2, 216-3, and so forth.
- Numbering for jobs with phases could look like this: 216-1-1, 216 for the job, 1 for phase, and 1 for the first RFP or RFI. This numbering scheme would increment to 216-1-2, 216-1-3 automatically in new records.
- If 216-1-3 were the last RFI or RFP for phase 1, then when you create the next RFP or RFI record, the program would insert 216-1-4. You must replace the -1- with -2- to represent phase 2. The result would look like this: 216-2-4. The program then increments the subsequent new records to 216-2-5, 216-2-7, and so forth.
- In the numbering scheme described above, the program increments the number that it finds after the final hyphen. If you do not type a hyphen as part of the entry, the program increments the number by 1. For example, the number 216 increments to 217.

Important! To increment the numbering, the program looks for the final number in a series of numbers preceded by a hyphen. The program does not recognize an alpha character preceded by a hyphen in the final position and will not increment it, for example from “a” to “b.” We strongly recommend that you use an “all-number” numbering scheme.

| Links to more information . . . [Creating RFPs](Creating_RFPs.md) [Creating purchase orders from RFPs](Creating_purchase_orders_from_RFPs.md) [Setting up RFP types](Setting_up_RFP_types.md) [Deleting RFPs](Deleting_RFPs.md) [About file and link Attachments on records](../../Appendices/A-Sage_100_Contractor_Features/About_file_and_link_Attachments_on_records.md) |
|---|
