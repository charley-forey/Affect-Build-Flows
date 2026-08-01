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
| **Retainage** | ❌ **not where you would expect** — see below |
| **Hours worked / OT** | ❌ no payroll table read; `actrec` exposes `emptme` / `hrscmp`, unexplored |
| **Cost to Complete / Spent to Date** | ❌ no job-cost table read; `actrec` exposes `jobcst` / `budget` / `cstcmp`, unexplored |
| Line-level / cost-code detail | ❌ `apivln` / `arivln` not queried |

### Retainage is not in the invoice header

`acpinv.retain` and `acrinv.retain` exist, are typed `decimal`, and **already land in
Silver** in the `_raw` tables — they are dropped only from the curated tables downstream.
So surfacing them looks like a free win. It is not:

```sql
-- verified against Silver_Lakehouse, Aug 2026
-- AR: 135 rows, 0 with retain <> 0
-- AP: 805 rows, 0 with retain <> 0
```

**Every value is zero.** Retainage for this company is not held on the invoice header.
Before building anything, find where it actually lives — most likely candidates are the
line tables (`arivln`), the job master (`actrec` has a `retain` column of its own), or
progress billing (screen 3-7). Do not wire `acrinv.retain` into the Monthly Progress
Report; it will silently report zero.

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

## Verified against live data

The Sage server itself is not reachable from a dev machine (`NC-AFFECT-1` does not
resolve off the client network), but **the Silver lakehouse is** — and its `_raw` tables
are Sage columns with Sage data, so they confirm much of the above. Checked Aug 2026 via
the Fabric SQL endpoint on `Silver_Lakehouse`:

| Check | Result |
|---|---|
| `jobnum` / `Job Number` type | `bigint` — confirms it is a numeric surrogate key, not a readable job code |
| AR invoices (`acrinv`) | 135 rows, 2024-12-31 → 2026-07-20 |
| AP invoices (`acpinv`) | 805 rows, 2025-01-02 → 2026-07-24 |
| Rows with non-zero `retain` | **0 of 940** — see the retainage section above |
| Sage projects vs. crosswalk | 23 projects in `Dim__Sage_Projects`, **15** rows in `dim_projects_procoreXsage` |
| AR job numbers with no crosswalk entry | **6** |

Two things to take from this:

- **The crosswalk is incomplete.** 15 of 23 Sage projects are mapped to Procore, and six
  job numbers that appear on real AR invoices have no mapping at all. Anything joining
  Sage to Procore through `dim_projects_procoreXsage` silently drops those jobs today.
  This is the concrete form of the README's "linchpin" question.
- **History is about 19 months deep and does not accumulate.** The dataflow is a weekly
  full replace, so Silver holds whatever Sage holds — there is no growing history. If the
  report ever needs a longer look-back than Sage retains, that has to be designed in.

Data types in `OBSERVED-SCHEMA.md` come from the semantic model's interpretation; the
types in the table above come from SQL Server via the lakehouse and are more trustworthy.
Note `vodrec` is `varchar` on `acpinv` but `bigint` on `acrinv` — the M code tests
`= ""` for one and `= 0` for the other. Not a typo; mirror it if you rewrite the query.

## Caveats

`OBSERVED-SCHEMA.md` is observed, not complete — a column missing there only means our
queries never touched it, and data types come from the semantic model's interpretation
rather than SQL Server. Run the `INFORMATION_SCHEMA` queries in
[`../INTEGRATION-NOTES.md`](../INTEGRATION-NOTES.md) to get the authoritative picture;
this folder is what to check it against.
