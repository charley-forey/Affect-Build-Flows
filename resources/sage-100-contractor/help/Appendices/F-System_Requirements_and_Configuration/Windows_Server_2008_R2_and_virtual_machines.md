<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Appendices/F-System_Requirements_and_Configuration/Windows_Server_2008_R2_and_virtual_machines.htm (Sage 100 Contractor help v20.5) -->

### Turning on Microsoft .NET 3.5

Microsoft .NET 3.5 must be available and enabled prior to installing Sage 100 Contractor on a Windows Server 2008 R2 machine. Server 2008 R2 comes with .NET 3.5 loaded but not installed, so Sage 100 Contractor does not install it automatically.

If you attempt to install Sage 100 Contractor without .NET 3.5 installed, you receive the following message during the licensing install: “Sage.CRE.HostingFramework.Service v3.2 has stopped working.” When you click [**OK**], the installation continues, but the services have not been installed so Sage 100 Contractor cannot open. The Sage.CRE.HostingFramework Service will not install unless .NET 3.5 has been installed. If you receive the above message during installation, install .NET Framework 3.5., and then reinstall Sage 100 Contractor.

The following instructions are for Windows Server 2008 R2.

#### To verify that .NET 3.5 is installed on Windows Server 2008 R2:

1. Click the **Start** button in the lower left corner of the display.
2. Highlight **Administrative Tools** and select **Server Manager**.
3. In the **Server Manager** interface, click **Features** to display all the installed Features in the right-hand pane. Verify that .NET Framework 3.5.1 is listed.

#### To enable .NET 3.5 on Windows Server 2008 R2:

1. In the **Server Manager** interface, select **Add Features** to display a list of possible features.
2. In the **Select Features** interface, expand **.NET Framework 3.5.1 Features**.
3. Once you expand **.NET Framework 3.5.1 Features**, you will see two check boxes. Check the box next to .NET Framework 3.5.1 and click **Next**.
4. In the **Confirm Installation Selections** interface, review the selections and then click [**Install**].
5. Allow the installation process to complete and then click [**Close**].

Note: Enabling .NET Framework 3.5.1 may require a reboot.
