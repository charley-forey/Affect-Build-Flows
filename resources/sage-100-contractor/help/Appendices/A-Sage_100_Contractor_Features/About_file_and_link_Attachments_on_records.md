<!-- Source: http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/20_5/Content/Appendices/A-Sage_100_Contractor_Features/About_file_and_link_Attachments_on_records.htm (Sage 100 Contractor help v20.5) -->

### About file and link Attachments on records

### What are attachments?

Attachments provide functionality to attach files and/or Web links to selected records in Sage 100 Contractor. There are two methods for attaching files and links. You can add them individually using the **Attachments** window (**Edit > Attachments**), or you can simply drag-and-drop files and/or Web links onto a Sage 100 Contractor window that accepts attachments.

A few examples of Sage 100 Contractor windows that accept attachments are payable invoices, requests for proposal, progress bills, change orders, purchase orders, jobs.

#### How can I use attachments?

Here are a few examples:

- After receiving a hard copy document that you would like to attach to a payable invoice record in **4-2 Payable Invoices/Credits**, you scan the document into your computer to create a file, then attach the file to the payable invoice record.
- You have several digital photos of work being done on by a subcontractor on a remodel job. You can transfer these files to your computer, and then attach them to a record in **6-7-1 Subcontracts**.
- After sending an RFP to an architect who has a Web site, you want to attach the architect's web site URL link to the RFP record. From the open the site in your browser, you drag and drop the link from the browser's **Address** box onto the **6-11-1 Requests for Proposal** record.

#### How does attachment functionality work?

You create an attachment as either a “local” attachment or a “link” attachment. Link attachments can either be a file or a URL (Web site link).

Creating a “local” attachment, associates the a local file (on your local computer) or a copy of a network file (copied from a network computer) to an Sage 100 Contractor record in your local computer's company data. In this process, the program creates a local folder and subfolder structure in your local company where the record is located.

Creating a “link” attachment, attaches a link to the remote file (on a network computer) or URL link to Web page on a remote computer. The program does not create a local folder and subfolder structure in your local company for linked attachments.

Important! For link attachments, do not rename an attachment's file server after attaching a file. Sage 100 Contractor cannot locate a linked file if the file server is renamed or replaced by a server with another name.

#### Can I drag and drop files to create attachments?

If a record accepts attachments, you can drag and drop files onto the window to create an attachment. This includes graphic files, Web links, email messages, desktop shortcuts, or any other file type.

Note: If you use Microsoft Outlook, you can drag and drop email messages from your Inbox list directly onto a Sage 100 Contractor record.

### Where are attachments located?

First, let's look at what happens when you attach a local file to a record. When you add the attachment and save the record, the program creates an Attachments folder and folder structure under \\[ServerName]\[CompanyName]\Attachments. To prevent naming conflicts between files, each file in placed into a subfolder with a unique name.

For example, let's suppose you are working in Sample Company job **Jiminez Burrito #8**, and you attach a local graphic file to record **8** in **6-4-1 Change Order**, **Floor Tile Upgrade**. After saving the record, in Windows Explorer, you will find this path: \\[ServerName]\Sample Company\Attachments\Jobs\Change Orders\(unique subfolder name)\(file name).gif.

Tip: Sample Company data can be changed on any computer. The Sample Company data in these examples may not match the Sample Company data on your computer exactly.

#### What is the attachment parent-child structure?

You probably noted that the Change Order folder is a subfolder of Jobs. That's because the program creates Attachments according to the existing parent-child relationships that already exist in the program for Jobs and Change Orders.

For example, the parent record for the change order is the job, **215-Jiminez Burrito #8**. If you were to open, **6-6-1 Purchase Orders** to record **38**, clear the **Lock Edit**, and add the same graphic file to this record and then look at the folder structure, you will find \\[ServerName]\Sample Company\Attachments\Jobs\Purchase Orders\(unique subfolder name)\graphic.gif. The attachments to the purchase order record and the change order record are both “children” of job **215—Jiminez Burrito #8**, which is located in **3-5 Jobs (Accounts Receivable)**.

#### What do I see when opening parent record when children have attachments?

You can attach files to both “parent” records and “child” records. For example, you can attach files and links to job **215-Jimenez Burrito #8** directly from that job's record in **3-5 Jobs (Accounts Receivable)** or to that job through other records such as Change Orders, Purchase Orders, Subcontracts, and so forth. As described above, you can add attachments to records that are children of the job.

Because of the parent-child structure of the program, when you open the Attachments window from the parent window **3-5 Jobs (Accounts Receivable) 215-Jimenez Burrito #8**, you can select different ways to view the Attachment related to this job using the box with the title, **Show items attached to**:

- **this job directly.** If the parent record has attachments, the attachments would be displayed in this list.
- **Purchase Orders for this job**. If a “child” purchase order record of this job has attachments, then the attachments would be displayed in this list.
- **Change Orders for this job.** If a “child” change order record of this job has attachments, then the attachments would be displayed in this list.

#### How does attaching network files work?

When you select a network file to attach to a record, the program recognizes that it isn't a local file and offers two choices, **Copy the file to my company data** (my local computer), or **Link to the existing file** (on a network computer).

If you select to **Copy the file to my company data**, the program makes a copy of it and places it in a folder\subfolder structure under \\[ServerName]\[CompanyName]\Attachments\ in its parent-child relationship.

If you select to **Link to the existing file**, the file remains on the network computer. A copy of it is not created, and it does not appear in a folder under \\[ServerName]\[CompanyName]\Attachments\. In fact, if you never link to a local file or copy a attachment file to your computer, you will never see an Attachments folder under the company folder.

#### What happens if I select “Protect this file from being changed”

After you link to a network file by selecting **Copy the file to your company data**, you have the option to **Protect this file from being changed**. After saving the record, if you were to open the linked file and try to edit it, the program that opens it displays a message stating that the file cannot be changed, is read-only, or something similar. The message displayed depends on the program that opens it.

Note: If you select the option, **Link to the existing file**, the **Protect this file from being changed** option is unavailable. If you need to prevent an attachment from being changed, select the **Copy file to my company data** option.

#### How do I attach Web links?

When adding a link to a Web page as an attachment, you are encouraged to copy and paste the contents of your browser's **Address** box (a URL—unique resource locator) into the box on the Add Attachment window. You can type the URL in the box, but it's much easier to copy and paste it to avoid possible errors from typing mistakes.

Tip: Attachments that are Web links are always remote and never appear in an Attachments folder under \\[ServerName]\[CompanyName]\.

#### How do I know that a record has attachments? Are there visual indicators?

An **Attachment** button has been added to the toolbar. It displays a paper clip against a grey background if the record has no attachments. It displays a paper clip against a white rectangle if the record has attachments. You can click the **Attachments** button to open the **Attachments** window whether the record has attachments or not.

Important! To provide room for the **Attachments** button, the **Count** button has been removed from the toolbar. On windows that provide the count files functionality, the **Count** command is available from the menu bar.

#### Can I email attachments?

Important! Emailing attachment functionality only works if Microsoft Outlook is your default Email client.

Yes, just open an **Attachments** window, and select one or more attachments. Click **Email**, and the program opens an email message with the attachments included in the **Attach...** box.

#### Can I print Attachments?

Yes, just open an **Attachments** window, and select an attachment. Click Print, and the program opens the file in the program that is controlled by your Windows settings.

Note: Printing from the **Attachments** window behaves the same as right-clicking the file in Window Explorer and selecting **Print** from the menu.

| Links to more information . . . [Attachment windows—parent-child relationships](../../Glossary/Glossary_-_attachment_windows_-_parent_and_child_relationships.md) [Dragging and dropping multiple files onto records](Dragging_and_dropping_multiple_files_onto_records.md) [Attaching files individually using the Add Attachment window](Attaching_files_individually_using_the_Add_Attachment_window.md) [Attaching Web links individually using the Add Attachment window](Attaching_Web_links_individually_using_the_Add_Attachment_window.md) [Removing attachments from records](Removing_attachments_from_records.md) [Emailing files attached to records](Emailing_files_attached_to_records.md) |
|---|
