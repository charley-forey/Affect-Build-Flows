# Sage 100 Contractor → Lakehouse: what the docs actually give us

Read this before writing the ingestion notebook. It is the bridge between the raw
corpus in [`help/`](help/INDEX.md) + [`guides/`](guides/) and the code we have to write.

---

## The headline: there is no published table schema

We scraped all 1,937 published help topics and all five PDF guides. Across the entire
corpus **exactly one physical table name appears** — `CMPANY`, in an SQL example in
[About SQL syntax](help/Modules/13-Review_and_Reporting/About_SQL_syntax.md):

```
Select USRDF1 From CMPANY
```

That is the whole of Sage's public schema documentation for this product. The
"Database and Company Administration Guide" is a **SQL Server administration** manual
(connect, back up, restore, archive, manage logins, nightly maintenance) — it contains
no table or column reference. Sage publishes a table-by-table schema for Sage 100 *ERP*,
a different product that shares the name; that documentation does not apply here.

**But we are not starting from zero.** A dataflow already reads Sage in production, and
its Power Query names six real tables and most of their columns. That is extracted and
documented in **[`schema/`](schema/README.md)** — read it before the docs below. It gives
the table names, the naming convention, the joins in use, and what the current dataflow
does *not* cover.

**The authoritative schema is still the live database.** First query of the engagement,
through the existing read-only account — use it to confirm and extend `schema/`:

```sql
SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
FROM   INFORMATION_SCHEMA.TABLES
ORDER  BY TABLE_SCHEMA, TABLE_NAME;

SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM   INFORMATION_SCHEMA.COLUMNS
ORDER  BY TABLE_NAME, ORDINAL_POSITION;
```

Everything below is what the docs *do* give us, which is the semantic layer we need to
turn that raw schema into a model.

---

## What the corpus is good for

### 1. Screen → data mapping (the main value)

Sage organizes both the UI and the docs by numbered module screens (`3-2 Receivable
Invoices`, `4-2 Payable Invoices`). Once `INFORMATION_SCHEMA` gives us table names, the
module docs tell us **what each screen stores and what the fields mean** — that is how
we map tables to business concepts. Folder layout mirrors the module numbering:

| Module | Folder | Relevant to us |
|---|---|---|
| 1 General Ledger | [`help/Modules/1-General_Ledger/`](help/Modules/1-General_Ledger/) | posting periods, account structure |
| 3 Accounts Receivable | [`help/Modules/3-Accounts_Receivable/`](help/Modules/3-Accounts_Receivable/) | **billed, paid, retainage, AR aging, invoice dates** |
| 4 Accounts Payable | [`help/Modules/4-Accounts_Payable/`](help/Modules/4-Accounts_Payable/) | vendor cost |
| 5 Payroll | [`help/Modules/5-Payroll/`](help/Modules/5-Payroll/) | **hours worked, OT hours by job** |
| 6 Project Management | [`help/Modules/6-Project_Management/`](help/Modules/6-Project_Management/) | job cost, cost to complete |
| 7 Utilities | [`help/Modules/7-Utilities/`](help/Modules/7-Utilities/) | company setup, users, SQL connection |
| 13 Review and Reporting | [`help/Modules/13-Review_and_Reporting/`](help/Modules/13-Review_and_Reporting/) | **SQL, calculated fields, Report Writer** |

The ❌ rows in the [main README](README.md) — the irreducible Sage scope the Procore
connector does not cover — land almost entirely in **module 3 (AR)** and **module 5
(Payroll)**. Those two folders are where to start reading.

### 2. The header/detail rule, stated precisely

From [About Structured Query Language](help/Modules/13-Review_and_Reporting/About_Structured_Query_Language.md):

> In windows such as **4-3 Vendor Payments**, **3-5 Jobs**, or **3-3-1 Cash Receipts** a
> single database table exists, containing all the information. In other windows such as
> **4-2 Payable Invoices** or **3-2 Receivable Invoices**, there are two database tables.
> When Sage 100 Contractor uses two tables to store data, the first table stores
> information from the text boxes and lists and the second table stores data from the grid.

So the doc names which screens are one-table and which are two. **`3-2 Receivable
Invoices` is a two-table header/detail split** — that is the single most important
structural fact for the AR ingestion, and it is stated outright.

### 3. Audit tables exist — but they expire

The README flagged "free change tracking if the audit tables are accessible." The 2025
guide (Company Tools chapter) confirms they exist and adds the catch:

> This tool queries all audit (or history) tables and reports on changes made by any
> third-party applications.
>
> Note: The data contained in the report is time-sensitive, and depends on the history
> retention policy specified for your company in **Advanced Company Settings**. (The
> default period is **90 days**.)

> Details older than the retention period you specify are removed during nightly maintenance.

**This changes the incremental-load design.** Audit tables are a rolling ~90-day window,
purged nightly — not a permanent history store. They are usable as a CDC feed for
incremental loads *provided* we land full snapshots in Bronze and never rely on the audit
tables to reconstruct history older than the retention window. Confirm the actual
retention setting for Affect's company before depending on it.

### 4. Connection and auth mechanics

Chapter 1 of the [DB administration guide](guides/database-and-company-administration-2025-v27.2.md):
Windows Authentication or SQL Server Authentication; databases live on a named SQL Server
instance. Chapter 7 covers company admins and SQL logins — relevant when we ask for the
read-only account's grants. The guide's file-layout section shows the on-prem convention
(`[drive]:\Sage100Con\Company\[Company Name]`), which is a strong hint that this install is
on-prem and therefore **needs an on-premises data gateway** for Fabric.

### 5. ODBC is a dead end — now confirmed

[About Open Database Connectivity (ODBC)](help/Appendices/A-Sage_100_Contractor_Features/About_Open_Database_Connectivity__ODBC_.md):

> The files in Sage 100 Contractor are ODBC-compliant using the **FoxPro version 2.6**
> database file format. […] **Sage 100 Contractor itself is not ODBC-compliant.**

That topic describes the pre-SQL FoxPro era. For the SQL-backed version, use the **native
SQL Server connector**. This settles the README's note that online ODBC guidance is not
applicable.

---

## Version caveat

The HTML help corpus is **v20.5** — the newest published on the WebHelp host (we probed
19.7 through 28.1; 20.6+ return 404). Sage moved later versions to `docs.sage.com`, which
**403s all HTML paths** and serves only PDFs, so the newer content we could retrieve is the
PDF set in [`guides/`](guides/) (up to 2026.1 / v27.2).

Module numbering and screen semantics are stable across these versions, so v20.5 remains
a sound semantic reference. Anything version-sensitive — and **the schema above all** —
gets verified against the live database, not the docs.

---

## Concrete next steps

1. Run the two `INFORMATION_SCHEMA` queries above, and diff the result against
   [`schema/OBSERVED-SCHEMA.md`](schema/OBSERVED-SCHEMA.md). That closes the schema
   question outright.
2. ~~Pull the queries Power BI runs against Sage today~~ — **done**, they were in the repo:
   [`schema/README.md`](schema/README.md).
3. Add `apivln` / `arivln` (invoice lines) — the current dataflow reads headers only, so
   there is no line-level or cost-code detail today.
4. Find the job-cost and payroll tables. `actrec` exposes `jobcst`, `budget`, `cstcmp`,
   `emptme`, `hrscmp` as relationships; none are queried yet.
5. Stop dropping `retain` — retainage is a required Excel field and the column is already
   present on `acpinv` and `acrinv`.
6. Check `Advanced Company Settings` for the real history-retention period before
   designing incremental loads.
7. ~~Confirm SQL Server host location → gateway requirement~~ — **settled**: an on-prem
   gateway is already configured and in use by the dataflow.

---

## Regenerating

```bash
python refresh.py           # rewrites help/ + guides/ + help/INDEX.md
```

Topic list comes from the help system's own `Data/Toc_Chunk*.js` and `Data/Alias.js`, so
it is the complete published set rather than a link crawl. PDFs are converted with
`pdftotext -layout` and the binaries are discarded — only the markdown is versioned.
