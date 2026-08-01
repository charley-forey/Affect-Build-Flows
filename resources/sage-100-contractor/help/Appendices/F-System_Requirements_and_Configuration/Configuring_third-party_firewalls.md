<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Appendices/F-System_Requirements_and_Configuration/Configuring_third-party_firewalls.htm (Sage 100 Contractor help v20.5) -->

### Configuring anti-virus software and third-party firewalls

During installation of the Sage 100 Contractor Hosting Framework, the Windows Firewall is configured automatically to allow the Sage 100 Contractor Hosting Framework to act as a TCP server. If you use some other firewall, however, you may need to manually adjust some settings in the firewall in order to ensure proper operation.

You can use the following basic procedure to manually configure the Windows Firewall to allow the Sage 100 Contractor Hosting Framework to communicate with other computers. Use it as the basis for manually configuring other third-party firewall products.

#### To configure the Windows Firewall:

1. For Windows Server 2008, click **Start > Control Panel > Security**. For Windows 7, click **Start > Control Panel > System and Security**. For Windows 8.1 and Windows 10, click **Start > All apps > Control Panel > System and Security**.
2. Open **Windows Firewall**, and then select **Allow a program or feature through Windows Firewall**.
3. Select **Sage 100 Contractor****Hosting Framework** on the list, if it is not selected..

Note: By default, the exception is set to allow access by any computer on the network. You can refine this setting by selecting the **Change Scope** button. Be aware that restricting the scope incorrectly can cause the computer to be unable to connect with some or all of the other machines on the network.

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Files to exclude when manually configuring your firewall for Windows 8.1 Professional 32‑bit](javascript:void(0);)

- C:\ProgramData\Sage\Sage 100 Contractor
- C:\Program Files\Sage\Sage 100 Contractor
- C:\ProgramData\Aatrix Software
- C:\Program Files\Aatrix Software
- C:\%LocalAppData%\Sage\Sage 100 Contractor
- Network location of Sage 100 Contractor data. (If you install SQL Server Express using Database Administration, this location is C:\Sage100Con\Company\.)

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Files to exclude when manually configuring your firewall for Windows 8.1 Professional 64‑bit](javascript:void(0);)

- C:\ProgramData\Sage\Sage 100 Contractor
- C:\Program Files (x86)\Sage\Sage 100 Contractor
- C:\Program Files (x86)\Aatrix Software
- C:\ProgramData\Aatrix Software
- C:\%LocalAppData%\Sage\Sage 100 Contractor
- Network location of Sage 100 Contractor data. (If you install SQL Server Express using Database Administration, this location is C:\Sage100Con\Company\.)

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Files to exclude when manually configuring your firewall for Windows 7 Professional 32‑bit](javascript:void(0);)

- C:\ProgramData\Sage\Sage 100 Contractor
- C:\Program Files\Sage\Sage 100 Contractor
- C:\ProgramData\Aatrix Software
- C:\Program Files\Aatrix Software
- C:\%LocalAppData%\Sage\Sage 100 Contractor
- Network location of Sage 100 Contractor data. (If you install SQL Server Express using Database Administration, this location is C:\Sage100Con\Company\.)

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Files to exclude when manually configuring your firewall for Windows 7 Professional 64‑bit](javascript:void(0);)

- C:\ProgramData\Sage\Sage 100 Contractor
- C:\Program Files (x86)\Sage\Sage 100 Contractor
- C:\Program Files (x86)\Aatrix Software
- C:\ProgramData\Aatrix Software
- C:\%LocalAppData%\Sage\Sage 100 Contractor
- Network location of Sage 100 Contractor data. (If you install SQL Server Express using Database Administration, this location is C:\Sage100Con\Company\.)

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Files to exclude when manually configuring your firewall for Windows 8.1 Professional](javascript:void(0);)

- C:\ProgramData\Sage\Sage 100 Contractor
- C:\Program Files (x86)\Sage\Sage 100 Contractor
- C:\Program Files (x86)\Aatrix Software
- C:\ProgramData\Aatrix Software
- C:\%LocalAppData%\Sage\Sage 100 Contractor
- Network location of Sage 100 Contractor data. (If you install SQL Server Express using Database Administration, this location is C:\Sage100Con\Company\.)

[![Closed](http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Skins/Default/Stylesheets/Images/transparent.gif)Files to exclude when manually configuring your firewall for Windows Server 2008 R2, 2011, 2012](javascript:void(0);)

- C:\ProgramData\Sage\Sage 100 Contractor
- C:\ProgramFiles (x86)\Sage\Sage 100 Contractor
- C:\Program Files (x86)\Aatrix Software
- C:\ProgramData\Aatrix Software
- C:\%LocalAppData%\Sage\Sage 100 Contractor
- Network location of Sage 100 Contractor data. (If you install SQL Server Express using Database Administration, this location is C:\Sage100Con\Company\.)
