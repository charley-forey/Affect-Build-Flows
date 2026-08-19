# Sage ingestion

`01-ingestion/Sage/CD_Sage_Ingest.Dataflow` — **built, committed and deployed.** It is live
in the Fabric workspace `Build`, folder `charley-dev`, bound to gateway `1e798beb` and
datasource `835e72c8`, writing to `CD_Bronze_Lakehouse`. Verified live 2026-08-19.

It is **inert**, not missing. The definition reads back from Fabric exactly as committed —
gateway, both connections, all 8 queries, `DefaultDestination` — and the first run failed in
about five seconds, too fast to be a query: `cforey-c@affect-group.com` cannot see any
gateway or connection in the tenant, so the dataflow asks to run through a gateway its
runner has no rights on.

**The remaining work is one permission grant**, not a build: whoever administers the
on-premises data gateway grants `cforey-c@affect-group.com` the **"Can use"** permission on
the connection `nc-affect-1\sage100con;Affect Group`, in *Manage connections and gateways*.
No subscription, no vault, no code change — it runs on the next refresh.

## What it pulls

Eight tables from `Sql.Database("NC-AFFECT-1\SAGE100CON", "Affect Group")` — the same source
and the same on-premises gateway the existing `Build_Sage_Test` dataflow already uses.

| Table | What it is | In the existing dataflow? |
|---|---|---|
| `acrinv` | AR invoice headers | yes |
| **`arivln`** | **AR invoice lines** | **no** |
| `acrpmt` | AR payments | yes |
| `acpinv` | AP invoice headers | yes |
| **`apivln`** | **AP invoice lines** | **no** |
| `acppmt` | AP payments | yes |
| `actrec` | Jobs / receivable accounts | yes |
| `actpay` | Payable accounts | yes |

## Why the two line tables are the point

The existing dataflow does not merely omit them — it **explicitly removes the columns that
point at them**. `"arivln(recnum)"`, `"arivln(_idnum)"`, `"apivln(recnum)"` and
`"apivln(_idnum)"` appear in `Table.RemoveColumns` calls in `mashup.pq`. The line detail has
never been queried.

Two things live down there that the header does not have:

**Retainage.** `retain` exists on the invoice header and is **zero across all 940 invoices** —
verified in commit `db0d11e`. It is not held there for this company. A report sourced from
the header shows **$0 retainage**, silently, and nobody notices until a client asks where
their retention is. That is exactly the class of defect this whole engagement exists to
remove. The real values are in the line tables, or in `actrec.retain`, or in progress
billing — open question 4, and it cannot be settled until the data is here to look at.

**Cost codes.** The header carries a job number but not a cost code, so header-only AP data
cannot be allocated to a budget line. `apivln` is what makes actual-cost-by-cost-code
possible, and therefore what makes `fct_BudgetLine`'s committed and invoiced columns real
rather than Procore-only.

## Why the tables are landed raw

The existing dataflow filters (`Invoice Balance <> 0`), renames columns and changes types
inside Power Query. Ours lands the tables as they are and shapes them in `sql/silver/`.

That is not a style preference. A Power Query step is not diffable in a pull request, cannot
be tested offline, and cannot be re-run against data already pulled. SQL in `sql/silver/` is
all three — `test_silver.py` runs it through DuckDB with no gateway, no credentials and no
Fabric capacity. It is also the same bronze rule the Procore side follows: never drop a
column at the boundary, so a transform bug is a re-run rather than a re-extract.

The trade is storage, which is cheap, against re-extraction, which needs a gateway and a
maintenance window.

## The join key

Per `resources/sage-100-contractor/schema/README.md`, `jobnum` on an invoice is a **foreign
key to `actrec.recnum`** — not a readable job code. This is why `dim_projects_procoreXsage`
*is* the Procore↔Sage join rather than a convenience lookup, and why `actrec` is not
optional here.

## What is left

1. **Grant *Can use* on the gateway connection.** The dataflow is already bound to
   `1e798beb-cc0f-4f72-bb1e-9c8fca8ba03e` (carried in `queryMetadata.json`, so it was a
   field to confirm rather than one to discover). What is missing is the permission for our
   identity to run through it. This needs Affect — the gateway connection and its
   credential are theirs, and the Sage database is administered by an outside consultant, so
   the ask may route through them.
2. Run it, then write `sql/silver/20_sage_silver.sql` to type and validate the eight tables.
3. Settle open question 4 with the line data in hand, and point `sv_ar_invoices` at
   `cd_silver_*` — it currently still reads the existing warehouse
   (`01_source_views_cd.sql`), which keeps `fct_Invoice` at its 117 rows rather than zero
   while this is blocked.

Worth raising on the same call as `OUTBUILD_API_TOKEN` and the two Procore 403s
(`punch_item_types`, `schedule`) — all four are access Affect grants, not work we can do.

## Isolation

This creates a **new** dataflow in the `charley-dev` folder. The existing
`Build_Sage_Test.Dataflow` is not modified, and its `DefaultDestination` is untouched — ours
writes only to `CD_Bronze_Lakehouse`. Reading the same SQL Server through the same gateway is
a read; it does not disturb the existing dataflow's schedule or output.
