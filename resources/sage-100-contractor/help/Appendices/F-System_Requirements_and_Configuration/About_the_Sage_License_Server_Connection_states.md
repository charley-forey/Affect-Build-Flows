<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Appendices/F-System_Requirements_and_Configuration/About_the_Sage_License_Server_Connection_states.htm (Sage 100 Contractor help v20.5) -->

### About the Sage 100 Contractor license use status

You can view the current state of your Sage license use in the About Sage 100 Contractor window. Your license use status is defined by several factors involving your network connectivity and the availability of license uses. The following table presents license use status definitions:

| About Sage 100 Contractor window displays | License use status definition |
|---|---|
| License use not acquired | You don’t have a license use. (You haven’t logged into a company database yet, or requesting a use at login failed to retrieve one.) |
| License use acquired from server | Normal operating condition when you're logged into a company. |
| License use returned to server | You’re at the main menu and logged out of the company database after having acquired a license use previously. |
| License use lost from server | You’re previously acquired license use has been taken back by the license server because you’ve lost communication. You’re in the “restricted” condition. |
| License use is checked out | Equivalent to “License use acquired from server” except that you’re using a checked out license. |
| Connection not established | There’s a communication error and the machine can’t talk to the license server. (The server isn’t available, the licensing service isn’t running on the server, or it’s not open on the designated port.) |

Note: If the computer running the Sage license server becomes disconnected from the other computers on your network, or if your computer becomes disconnected from the Sage license server, you may see an alert message from Sage 100 Contractor telling you that you are disconnected.
