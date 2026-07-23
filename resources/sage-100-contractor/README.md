# Sage 100 Contractor

Accounting, invoicing, AR/AP, payroll. **Integration status: read-only SQL Server
connection, currently queried live from Power BI — bypasses the Lakehouse entirely.**

---

## Documentation

All links below verified to resolve (HTTP 200), Jul 2026.

| Resource | URL |
|---|---|
| **Database and Company Administration Guide** (2025, v27.2 US) — the schema/SQL reference | https://docs.sage.com/docs/en/customer/100contractor/27_2US/open/DatabaseAndCompanyAdministrationGuide.pdf |
| Database and Company Administration Guide (2024, v26.1) | https://docs.sage.com/docs/en/customer/100contractor/26_1CA/open/DatabaseAndCompanyAdministrationGuide.pdf |
| Database and Company Administration Guide (2022, v24.1) | https://docs.sage.com/docs/en/customer/100contractor/24_1US/open/DatabaseAndCompanyAdministrationGuide.pdf |
| Sage 100 Contractor and Your Business (2026.1 US) | https://docs.sage.com/docs/en/customer/100contractor/2026_1US/open/Sage100ContractorandYourBusiness.pdf |
| User's Guide (2021 SQL, US) | https://docs.sage.com/docs/en/customer/100contractor/23_1US/open/UserGuide.pdf |
| About Structured Query Language (online help) | http://sage100contractorhelp.sagecre.com/help/sage100contractor/US/19_7/Content/Modules/13-Review_and_Reporting/About_Structured_Query_Language.htm |
| Database Administration (online help) | http://sage100contractorhelp.sagecre.com/help/sage100contractor/us/20_2/Content/DatabaseAdministration/win_DatabaseAdministration.htm |
| Sage documentation portal | https://docs.sage.com |
| Sage Construction & Real Estate community | https://communityhub.sage.com/us/sage_construction_and_real_estate/ |

> Sage does not publish a single public table-by-table schema reference for 100 Contractor
> the way it does for 100 ERP. The Database and Company Administration Guide is the closest
> official source. **The most reliable schema reference will be the live database itself**
> — querying `INFORMATION_SCHEMA` through the read-only account.

## What we know about Affect's setup

- **Sage 100 Contractor (SQL)** — SQL Server backed
- **Read-only SQL connection already exists**
- **Power BI queries it live today**, bypassing the Fabric Lakehouse
- The Procore connector is purchased but **not yet rolled out** on a project

## Two-table pattern

Worth knowing before reading any schema. From Sage's own documentation:

> *"When you enter information in a window, Sage 100 Contractor stores the information in
> one or two tables. When it uses two tables, the first stores information from the text
> boxes and lists and the second stores data from the grid."*

So a header/detail split is the norm — an invoice header in one table, its line items in
another. Expect to join, not to find one flat table.

**Audit tables:** Sage 100 Contractor maintains history in separate audit tables, queryable
via SQL Server Management Studio. **If these are available to the read-only account they
give change tracking for free** — worth asking about, because it would make incremental
loading and history straightforward.

## What the Excel tracker needs from Sage

Roughly 15% of the Monthly Progress Report. From
[`../../powerbi/source-mapping.md`](../../powerbi/source-mapping.md):

| Excel field | Sage area | Redundant after connector? |
|---|---|---|
| Total Billed | AR invoice history by job | ❌ not synced |
| Bill This Pay Period | AR | ❌ |
| Total Paid | Cash receipts | ❌ |
| Retainage | AR retainage held | ❌ |
| AR Outstanding | Open AR by job | ❌ |
| Aging balance | AR aging | ❌ |
| Invoice sent / paid dates | AR + cash receipts | ❌ |
| Cost to Complete | Job cost | ✅ likely |
| Spent to Date | Job cost | ✅ likely |
| Hours worked / OT hours | Payroll by job | ❌ (or ADP) |

**The ❌ rows are the irreducible Sage scope** — the connector does not sync any of them.
The ✅ rows may be obtainable from Procore once the connector is live.

## Open questions for the call

1. **Which tables and views does the read-only account actually expose?** Run
   `SELECT * FROM INFORMATION_SCHEMA.TABLES` and we have a real answer in 30 seconds.
2. **Which queries does Power BI run against Sage today?** These are the starting point
   for the ingestion and they encode knowledge that exists nowhere else.
3. **Where does the SQL Server live?** On-prem means an **on-premises data gateway** is
   required for Fabric ingestion — a dependency with procurement lead time. Identify it
   early.
4. **Are the audit tables accessible?** Free change tracking if so.
5. **What is the job numbering scheme,** and does it match Procore project numbers and the
   `YY-000` in the Excel filename convention? *This is the linchpin question for the whole
   model.*
6. **Cost code structure** — segmented? Does it reconcile with Procore's list?
7. **Payroll: Sage or ADP** as the source for hours worked and OT hours?
8. **Which Sage 100 Contractor version?** Determines schema specifics and connector
   eligibility (v20.5+).

## Connecting

- **Native SQL Server connector** is the right choice for a SQL-backed Sage 100 Contractor
  install — not ODBC. Fabric and Power BI both support it directly.
- **On-prem gateway** required if the server is not cloud-hosted.
- **Read-only account, credentials rotated on a schedule**, managed centrally.
- ODBC guidance found online is mostly written for **Sage 100 ERP** and is largely not
  applicable here — another consequence of the two products sharing a name.
