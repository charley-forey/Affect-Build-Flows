<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Appendices/F-System_Requirements_and_Configuration/About_network_configuration_and_TCP_Remoting_Channel.htm (Sage 100 Contractor help v20.5) -->

### About network configuration and TCP Remoting Channel

Sage 100 Contractor uses the TCP Remoting Channel, a Microsoft .NET Framework component, to enable communication among computers on a network. By default, Sage 100 Contractor uses the TCP starting port 48750. Certain configurations can potentially disable the communication:

- You must enable file sharing on your computers. To enable file sharing, follow the instructions in the Windows Help.
- TCP communication requires the selection of port numbers that are not in use by other processes on the local computer.
- Software firewalls running on the local computer can be configured to block processes from opening TCP ports, which will prevent communication through the TCP Remoting Channel.
