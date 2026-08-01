<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Appendices/F-System_Requirements_and_Configuration/Configuring_the_Sage_100_Contractor_Hosting_Framework_TCP_port_number.htm (Sage 100 Contractor help v20.5) -->

### Configuring Sage 100 Contractor Hosting Framework TCP port number

Sage 100 Contractor uses the TCP starting port number 48750 as the default. You can configure the port number using the XML file Sage.CRE.HostingFramework.Service-InstanceConfig.xml, located in the **Programs (x86)\Sage\Sage 100 Contractor** folder.

If you need to change the default port numbers for the Sage 100 Contractor Hosting Framework using the Sage.CRE.HostingFramework.Service-InstanceConfig.xml file, you must change it on every computer on the network where Sage 100 Contractor is installed. In addition, after making this change, the Sage 100 Contractor Hosting Framework on each computer running Sage 100 Contractor must be restarted.

Note: Consult your IT administrator for alternative port numbers.

#### To change the port numbers:

1. In Window Explorer, locate Sage.CRE.HostingFramework.Service-InstanceConfig.xml in the path Programs(x86)\Sage\Sage 100 Contractor.
2. Right-click Sage.CRE.HostingFramework.Service-InstanceConfig.xml, then open it with a text editor, such as Notepad.
3. Near the end of the file, between the **<StartingPort> </StartingPort>** tags, locate the port number.
4. Change the port number.
5. Save, and then close the file.

Repeat these steps on every computer running Sage 100 Contractor.
