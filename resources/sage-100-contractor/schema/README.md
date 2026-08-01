# Sage 100 Contractor schema — what we actually know

Sage publishes no table schema for this product ([why](../INTEGRATION-NOTES.md)). But we
are not starting from nothing: **a dataflow already reads Sage in production**, and its
Power Query names real tables and most of their columns.

| File | What it is |
|---|---|
| [`OBSERVED-SCHEMA.md`](OBSERVED-SCHEMA.md) | **Generated.** Tables, columns, renames, foreign keys, derived from the live M code. |
| [`derive_schema.py`](derive_schema.py) | Regenerates it: `python derive_schema.py`. Self-check: `--selftest`. |

Source of truth is
[`foundation/01-ingestion/Sage/Build_Sage_Test.Dataflow/mashup.pq`](../../../foundation/01-ingestion/Sage/Build_Sage_Test.Dataflow/mashup.pq).
Every step there enumerates the columns it drops or renames, so the union of those lists
reconstructs most of each table. Rerun the script whenever that dataflow changes.

---

## The six confirmed tables

Connection: `NC-AFFECT-1\SAGE100CON`, database `Affect Group`, schema `dbo`.

| Table | Holds | Sage screen |
|---|---|---|
| `acpinv` | AP invoices (header) | 4-2 Payable Invoices |
| `acrinv` | AR invoices (header) | 3-2 Receivable Invoices |
| `acppmt` | AP payments / vendor payments | 4-3 Vendor Payments |
| `acrpmt` | AR payments / cash receipts | 3-3-1 Cash Receipts |
| `actpay` | Vendor master | 4-4 Vendors |
| `actrec` | **Job / project master** | 3-5 Jobs |

`actrec` is the job table — the spine everything else hangs off. Note the naming: `actpay`
and `actrec` are *masters* (payable/receivable accounts), not transaction tables. Easy to
misread.

## Naming conventions

Consistent enough to predict table names you have not seen:

- **Six lowercase characters, vowels dropped.** `acpinv` = **ac**counts **p**ayable
  **inv**oice. `acrpmt` = AR payment. `vndnme` = vendor name, `jobnum` = job number,
  `invdte` = invoice date, `dscrpt` = description, `invttl` = invoice total,
  `invbal` = invoice balance, `amtpad` = amount paid.
- **`ac[p|r]` prefix** = accounts payable / receivable. **`act` prefix** = master record.
- **Keys:** every table has `_idnum` and `recnum`. `recnum` is the business key used in
  joins; `_idnum` looks internal. Audit columns are uniform: `insdte`/`insusr` (inserted),
  `upddte`/`updusr` (updated).
- **Navigation properties.** The SQL Server connector surfaces foreign keys as extra
  columns named `table(key)` — e.g. `apivln(recnum)` on `acpinv`. **These are not
  selectable columns**; they are relationship handles. They are also how we learn table
  names we have never queried — see the catalogue at the end of `OBSERVED-SCHEMA.md`.

## Joins that matter

Taken from the relationships in `Sage AP-AR.SemanticModel`, so these are in use today:

```
acpinv.jobnum  ->  actrec.recnum      -- AP invoice to job
acrinv.jobnum  ->  actrec.recnum      -- AR invoice to job
acpinv.vndnum  ->  actpay.recnum      -- AP invoice to vendor
acppmt.acpinv(_idref) -> acpinv       -- payment to the invoice it settles
acrpmt.acrinv(_idref) -> acrinv       -- receipt to the invoice it settles
```

**`jobnum` is a foreign key, not a human-readable job number.** It joins to
`actrec.recnum`. The readable name is `actrec.jobnme`. This matters for the Procore
crosswalk — do not assume `jobnum` matches a Procore project number or the `YY-000` in
the Excel filenames. `dim_projects_procoreXsage` in the Silver lakehouse already carries
a `Sage Project ID` ↔ `Project ID` mapping; reuse it rather than rebuilding it.

## The header/detail split

Sage's docs state that some screens write one table and others two
([About SQL](../help/Modules/13-Review_and_Reporting/About_Structured_Query_Language.md)).
The observed foreign keys confirm which:

- `acpinv` → `apivln` — **AP invoice lines**
- `acrinv` → `arivln` — **AR invoice lines**

Both line tables appear as navigation properties but **neither is queried today**. That is
the gap: the current dataflow reads invoice *headers* only. Anything needing cost codes or
line-level detail has to add `apivln` / `arivln`.

## What the current dataflow does not cover

Against the Excel tracker's Sage scope in the [main README](../README.md):

| Needed | Status |
|---|---|
| Total Billed, AR Outstanding, aging, invoice dates | ✅ covered by `AR_Open` / `Revenue_AllTime` |
| Total Paid | ✅ `Reciepts` (from `acrpmt`) |
| **Retainage** | ⚠️ `retain` column exists on both `acpinv` and `acrinv` — **explicitly dropped** by the current queries |
| **Hours worked / OT** | ❌ no payroll table read; `actrec` exposes `emptme` / `hrscmp`, unexplored |
| **Cost to Complete / Spent to Date** | ❌ no job-cost table read; `actrec` exposes `jobcst` / `budget` / `cstcmp`, unexplored |
| Line-level / cost-code detail | ❌ `apivln` / `arivln` not queried |

The `retain` one is worth a look first — the column is right there and already being
selected away.

## Operational facts worth knowing

- **On-prem gateway is already configured** (`gatewayObjectId` in the dataflow's
  `queryMetadata.json`). The gateway question in the main README is settled — it exists.
- **The dataflow refreshes weekly** (cron interval 10080 minutes, Mondays 06:00 Eastern,
  from `.schedules`). If the Monthly Progress Report needs fresher AR aging than that,
  this is the thing to change.
- **It writes straight to the Silver lakehouse** (`DefaultDestination` → workspace
  `1f7caed6…`, lakehouse `2e05dca7…`) with `UpdateMethod = Replace`. There is **no Bronze
  landing and no incremental load** — every run is a full replace, so no history is
  retained beyond what Sage itself holds. Worth reconciling with the audit-table
  90-day retention note in [`../INTEGRATION-NOTES.md`](../INTEGRATION-NOTES.md).
- Query named `Reciepts` is misspelled in production (sic). Left alone here so searches
  match; renaming it is a breaking change to anything downstream.

## Caveats

`OBSERVED-SCHEMA.md` is observed, not complete — a column missing there only means our
queries never touched it, and data types come from the semantic model's interpretation
rather than SQL Server. Run the `INFORMATION_SCHEMA` queries in
[`../INTEGRATION-NOTES.md`](../INTEGRATION-NOTES.md) to get the authoritative picture;
this folder is what to check it against.
