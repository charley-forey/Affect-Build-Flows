<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Appendices/F-System_Requirements_and_Configuration/Installing_on_computers_running_Citrix_and_Terminal_Server_using_DOS_commands.htm (Sage 100 Contractor help v20.5) -->

### Installing on computers running Citrix and Terminal Server using DOS commands

To install using DOS commands:

1. Click [**Start**] **> Run**.
2. On the **Run** window: The **\Windows\...\cmd.exe** window appears.
   
   1. In the **Open** drop-down box, type cmd.
   2. Press [**Enter**].
3. When prompted, type change user /install, and then press [**Enter**] to turn on the Install mode.
4. Install Sage 100 Contractor as you would on a typical workstation or Windows Server.
5. At the end of the installation process, launch the **License Administration**program.
6. Use the License Administration window to activate and manage your license.
7. After activation, click **Start > Run**.
8. On the Run window, in the Open drop-down box, type cmd, and then press [**Enter**]. The **\Windows\...\cmd.exe** window appears.
9. When prompted, type change user /execute to turn on the Execute mode, the default mode for running Citrix and Terminal Server.
10. Exit the **Run** window.
11. Restart the server.

Important! If this message appears: “Install mode does not apply to a terminal server configured for remote administration,” it is not necessary to turn on the install mode. You may install the Sage 100 Contractor software as you would on a typical workstation.
