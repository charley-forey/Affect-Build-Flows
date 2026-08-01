<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Modules/7-Utilities/Troubleshooting_the_Alerts_Manager.htm (Sage 100 Contractor help v20.5) -->

### Troubleshooting the 7-6 Alerts Manager

This topic describes how to resolve problems that can occur with the **7-6 Alerts Manager**.

#### You set up alerts, but you are not receiving messages

If you set up alerts for certain conditions in your Sage 100 Contract data, but you do not receive any alerts, either the conditions did not exist when the alerts were processed or the Alerts Manager did not process the alerts according to the schedule for some reason.

You can select an option to receive a warning when the Alerts Manager fails to process alerts.

Tip: We recommend that you select the **Show warning at login when alert processing misses** option in the **7-6 Alerts Manager** window.

If the Alerts Manager did not process alerts as expected, you need to determine why. The following situations are possible causes, which you should check and rectify, as follows:

- The computer that was set up to process the alerts may have been replaced with a different computer. You need to configure the new computer to process the alerts. See Alerts processing is set up to run on a computer that is no longer functioning.
- The computer that was set up to process the alerts may not have been working at the time the alerts were supposed to have been processed. For example, it may have been turned off, or it could be hibernating or malfunctioning. Do not schedule processing for a time when the computer will be offline. Either reschedule alert processing, or ensure that the computer will not hibernate when alerts are scheduled for processing.
- If the computer is permanently disabled, you need to set up the alerts on a different computer. See Alerts processing is set up to run on a computer that is no longer functioning. There may be a problem with the Windows Task Scheduler service. You need to ensure that:For information on using Windows Task Scheduler, see the Windows help.
  
  - The Task Scheduler service is running.
  - The Task Scheduler record exists in the Task Scheduler window.

#### Alerts processing is set up to run on a computer that is no longer functioning

If the computer that is set up to process alerts becomes disabled or is replaced, you need to set up processing on a different computer.

Open **7-6 Alerts Manager**, and then, on the **Options** menu, click **Allow me to set up processing on this computer**.

Note: You need administrator rights for a computer to set up a computer to process alerts.

#### You receive multiple messages for the same alert conditions

This condition can occur if you have set up processing on more than one computer.

Decide which computer should process the alerts.

On the other computer(s), open **7-6 Alerts Manager**, and then, on the **Options** menu, click **Remove my alert processing from this computer**.
