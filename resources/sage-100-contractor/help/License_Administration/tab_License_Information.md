<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/License_Administration/tab_License_Information.htm (Sage 100 Contractor help v20.5) -->

### License Information tab

The tab, which is available from the [License Administration window](win_License_Administration.md), displays information about your Sage 100 Contractor licenses.

#### Items on this tab

| Item | Notes |
|---|---|
| Support plan expiration date | The date on which your support plan with Sage Customer Support expires. |
| Number of requests which exceeded use count (last 90 days) | Displays the number of times the request for licenses failed in the past three months because there were not enough licenses available. If there are a significant number of requests, you may want to acquire additional licenses. |
| Last license information update | The last date upon which your licenses were verified with Sage's license server. If your system cannot connect to Sage for a period of more than 10 days, you will receive a message indicating there is a connection problem. See [Troubleshooting license activation issues](con_Troubleshooting_license_activation_issues.md) for more information. |
| Licensed modules | Displays a list of licenses available to this server, based on the products you have purchased from Sage. When you purchase new products, the licenses for those products become available to activate here. "Canadian Edition" refers to the basic program, exclusive of the additional modules. The module licenses that are not part of the core Canadian Edition, but are available for purchase, are listed here: Inventory Service Receivables Estimating Document Control Equipment Management There is also a column that shows how many Canadian Edition licenses are checked out from this license server to local machines. |
| Update license information | Click to update the license information manually. This connects your server to the Sage license server, where your current license information is stored, and it updates the information on this window. This also creates entries in the [event log](tab_Event_Log.md). View the event log to monitor the success of your license activations. If you are using multi-server license administration, ensure you have the proper allocations set under Multi-server licensing before you update your license information. |
| Deauthorize license server | Typically, this would be used if you are moving Sage 100 Contractor's license server from one machine to another machine. Important! You need to deauthorize the old server in the **License Information** tab before you authorize Sage 100 Contractor's license server on a new server. |
| Multi-server licensing | This allows you to allocate your Sage licenses to multiple servers. For example, this could happen if you have several corporate offices and want to use separate licenses for each office or if you want to reserve a certain quantity of license uses for a specific group of people. |
