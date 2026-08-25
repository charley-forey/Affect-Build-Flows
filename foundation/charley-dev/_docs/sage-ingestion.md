# Sage ingestion

`01-ingestion/Sage/CD_Sage_Ingest.Dataflow` — **built, committed and deployed to the
workspace on 2026-08-02** (`9d1dc6db-…`), bound to gateway `1e798beb` and datasource
`835e72c8`, writing to `CD_Bronze_Lakehouse`. Verified live 2026-08-19: the definition reads
back from Fabric exactly as committed — gateway, both connections, all 8 queries,
`DefaultDestination`.

**It is inert, not missing.** The first run failed in about five seconds — too fast to be a
query. As `cforey-c@affect-group.com`, `GET /v1/gateways` and `GET /v1/connections` both
return empty and the gateway itself returns 404, while `Build_Sage_Test` plainly uses it. The
identity cannot see any gateway in the tenant, so the dataflow asks to run through one it has
no rights on and fails before reaching Sage.

**The remaining work is an ownership change, and it needs nothing from Affect.** Measured
2026-08-25 by signing in as the gateway's own registration account: `RBuckley@affect-group.com`
and `IT@affect-group.com` **already hold "Can use"** on `nc-affect-1\sage100con;Affect Group`,
the exact datasource this dataflow is bound to.

A Dataflow Gen2 runs as its **owner**. We deployed this one owned by `cforey-c@`, which has no
gateway rights — so the failure was an ownership choice on our side, not a grant withheld on
theirs. The ask carried since 2026-08-02 was a valid fix but never the only one, and the
framing around it was wrong.

**Fastest fix, available today and costing nothing: Rebecca opens `CD_Sage_Ingest` and clicks
Take over.** It runs on the next refresh. The durable fix is to hand ownership to
`fabricconnector@` so no named person is in the path at all — that needs the account added to
the `Build` workspace and a Power BI Pro licence ($14/mo), and is the target to aim at rather
than the thing to wait for. See [`access-model.md`](access-model.md).

> **Worth raising on the same call:** re-measured live on **2026-08-19**, Rebecca's Sage data
> now runs to **2026-07-31** — up from the **2026-07-20** we recorded on 2026-08-02, so her
> feed refreshed at some point in between rather than stopping dead. It is still **~19 days
> behind**: lag, not a dead feed. Outbuild's **2026-07-14** is as measured on 2026-08-02 and
> has **not been re-verified since**. If her dataflows are lagging on the same gateway, the
> *existing* reporting is running on numbers nearly three weeks old and nobody has noticed —
> which makes the grant below no less urgent, and `CD_Sage_Ingest` still cannot run at all
> without it.

## 2026-08-25 — the gateway is open, and the dataflow ran for real

**`GET /connections` returns 1 for `cforey-c@affect-group.com`.** It had returned 0 since
2026-08-02. `nc-affect-1\sage100con;Affect Group` (`835e72c8-…`, connectivityType
`OnPremisesGateway`) is now visible and usable. The access half of this is finished.

How: signed in as `fabricconnector@affect-group.com` — the gateway's own registration account,
and therefore its admin — and added `cforey-c@` as `Read` on the datasource. Rebecca and IT
already held it. `/gateways` still returns 0 for us, which is correct and does not matter: that
needs gateway *admin*, and nothing here does.

**The dataflow then ran for 3m25s and failed** (`01bdf50b-…`, 08:26:34 → 08:29:59 UTC,
`ActionUserFailure`, no detail). That number is the finding. Its three previous attempts on
2026-08-02/03 all died in about **5 seconds** — too fast to be a query, which is what told us
back then that it was failing before it reached Sage at all. Three and a half minutes is a run
that connected, authenticated, and did work.

No `cd_bronze_sage_*` tables exist in `CD_Bronze_Lakehouse` yet, so it failed before writing.

### What is not yet known, and how to find out

The Fabric jobs API returns only "Something went wrong, please try again later" for a Gen2
refresh. The per-query detail is in the **portal refresh history** and nowhere else:

`Build` workspace → `CD_Sage_Ingest` → **Refresh history** → the failed run → expand the
failing query.

Three candidates, in order of likelihood given a 3m25s runtime:

1. **The destination write.** The dataflow writes to `CD_Bronze_Lakehouse` and Gen2 also uses a
   staging lakehouse. Reading Sage for three minutes and then failing at the write end fits the
   timing better than anything else.
2. **A table or column that does not exist in `Affect Group`.** The eight table names were taken
   from the Sage schema reference and from `Build_Sage_Test`, which queries the same instance —
   but `Build_Sage_Test` does not query `arivln` or `apivln` at all, so those two have never
   been proven against this database by anyone.
3. **The Sage logon trigger.** §9 of the Nerds That Care handoff whitelists three application
   names for `FabricReader` from `%LOCALHOST%`, one being `Mashup Engine
   (TridentDataflowNative)`. A Gen2 dataflow should match it. If it does not, the give-away is
   **Event ID 17063** in the Windows Application log on `NC-AFFECT-1` — it will not appear as a
   connection error on the Fabric side.

## 2026-08-25 — SAGE IS LIVE. All 8 tables landed.

`CD_Sage_Ingest` completed at **09:25:10 UTC**, 3m55s, first successful run since it was
built on 2026-08-02. All eight tables exist in `CD_Bronze_Lakehouse/Tables/dbo`, including
**`arivln` and `apivln`** — the AR/AP line tables the existing `Build_Sage_Test` dataflow
explicitly strips the pointer columns for, and which no one at Affect has ever queried.

### What landed, measured

| Table | Rows | |
|---|---:|---|
| `cd_bronze_sage_actpay` | 1,080 | payable accounts |
| **`cd_bronze_sage_apivln`** | **901** | **AP invoice LINES — never queried before** |
| `cd_bronze_sage_acpinv` | 871 | AP invoice headers |
| `cd_bronze_sage_acppmt` | 656 | AP payments |
| **`cd_bronze_sage_arivln`** | **258** | **AR invoice LINES — never queried before** |
| `cd_bronze_sage_acrinv` | 148 | AR invoice headers |
| `cd_bronze_sage_acrpmt` | 86 | AR payments |
| `cd_bronze_sage_actrec` | 27 | jobs / receivable accounts |

**4,027 rows.** AR line value **$25,613,659.66**, AP line value **$15,509,381.78**.

### Retainage: Sage confirms what progress billing already told us

Open question 4 was **already closed on 2026-08-02** — retainage lives in Procore progress
billing, not Sage, and `21_financial_silver.sql` carries the numbers: owner retainage held
**$830,725.87**, sub retainage held **$486,030.04**, net position **$344,695.83**.

What the line tables add is the last piece of proof for the *other* half of that conclusion:
**Sage holds no retainage anywhere.** That had been verified only at header level; the two
line tables and `actrec` were the remaining candidates and needed the gateway. They are now
measured, and they are empty of it:

| Location | Rows checked | Rows with retainage | Total |
|---|---:|---:|---:|
| `acrinv.retain` (header) | 940 | 0 | $0.00 |
| `arivln.hldamt` (AR lines) | 258 | 0 | $0.00 |
| `apivln.hldamt` (AP lines) | 901 | 0 | $0.00 |
| `actrec.retain` (jobs) | 27 | 0 | $0.00 |

So a Sage-sourced retainage figure of $0 is **correct**, and the report's retainage numbers
correctly come from progress billing instead. Nothing to fix, and the last "we should check
that when the gateway lands" item on this subject area is now checked.

Worth one sentence to Rebecca all the same: Affect withholds retainage on Procore contracts
but records none of it in Sage, so the two systems disagree by design. That is a process
observation, not a defect, and she is the right person to say whether it is intended.

### The join keys, verified rather than assumed

`resources/sage-100-contractor/schema` implies the line tables hang off the header by
`invrec`. **They do not.** Measured:

| Join | Result |
|---|---|
| `arivln.invrec` → `acrinv.recnum` | **258 of 258 orphaned** |
| `apivln.invrec` → `acpinv.recnum` | **901 of 901 orphaned** |
| **`arivln._idref` → `acrinv._idnum`** | **0 orphaned** |
| **`apivln._idref` → `acpinv._idnum`** | **0 orphaned** |
| `acrinv.jobnum` → `actrec.recnum` | **0 orphaned** across 148 invoices, 24 distinct jobs |

`_idref` is the foreign key, not `invrec`. Silver must join on it, and a `_idnum`/`_idref`
pair that looks like an internal GUID is easy to dismiss as plumbing — which is presumably
how the documented answer came to be wrong. The `jobnum` FK the whole Procore↔Sage crosswalk
rests on is confirmed sound.

### Cost codes: AP is complete, AR is not

- **`apivln`: 901 of 901 lines carry `actnum`** (GL account). Actual-cost-by-account is now
  possible for the first time — this is what makes `fct_BudgetLine`'s invoiced column real
  rather than Procore-only.
- `arivln`: only **25 of 258** lines carry `cstcde`. AR line detail is mostly uncoded, so
  revenue-by-cost-code is not available from this source and should not be promised.

Note the two line tables do not share a shape: AP codes to `actnum`/`subact`, AR to `cstcde`.
Silver has to treat them separately rather than unioning them.

### The actual root cause, which was none of the three we guessed

The destination failed because **the Lakehouse connection was being forced through the
on-premises gateway.** `queryMetadata.json` carries `gatewayObjectId` at the dataflow level,
and Power Query applies it to *every* connection in the dataflow — so Fabric was trying to
reach OneLake by going out to a server in Affect's office and back. The connection dialog
showed it plainly once we looked:

```
Data gateway: [On-premises][User] AffectGroup-Sage-Gateway
[x] This connection can be used with on-premises data gateways    <- checked AND DISABLED
    You are not signed in. Please sign in.
```

Signing in could never have worked. It was not asking *the user* to authenticate — the user
was already signed in. It was asking *the gateway* to authenticate to OneLake, which is not
something an on-premises gateway does.

Removing `gatewayObjectId` from the definition does not fix it either: that binding is what
routes the on-premises **source**, so without it the refresh dies in five seconds with the
old "cannot see any gateway" signature. It is all-or-nothing at the definition level.

**The fix is in the destination's own connection dialog, where the gateway is a dropdown with
a `(none)` option.** Setting it to `(none)` detaches the Lakehouse connection from the gateway
while the SQL source keeps using it, and the sign-in state immediately flips from "You are not
signed in" to "You are currently signed in as…". The connection `Lakehouse cforey-c (none)` is
created against the signed-in identity, and the refresh works.

That dropdown only appears when the default destination is **re-added from scratch**. On the
existing broken destination the same field is static text with no dropdown at all, which is
why this looked unfixable from the UI as well as from the API.

### Why Build_Sage_Test was never a useful comparison

Its definition is byte-identical to ours — same `gatewayObjectId`, same SQL connection, same
Lakehouse connection `44379bed-…` on cluster `e1e7d5c7-…`. It works because it runs as Rebecca
and `44379bed` is **her personal connection**; `e1e7d5c7` returns 404 for us because it is a
per-user cloud cluster. Personal connections cannot be shared. Whoever owns the dataflow needs
their own, and ours is now `Lakehouse cforey-c`.

We had copied her definition wholesale, connection ids and all, when this dataflow was
authored — and it survived unnoticed from 2026-08-02 until now because the item had no deploy
script. It has one now (`deploy_sage.py`).

### Reproducing it, if the destination ever breaks again

1. `python _local/deploy_sage.py --apply` — pushes the definition with the Lakehouse binding
   stripped, so the destination is genuinely absent rather than broken
2. Power Query → **Default data destination → Remove**, then **Add → Lakehouse**
3. **Data gateway → `(none)`** — this is the whole trick
4. Pick `CD_Bronze_Lakehouse` → `dbo`, update method **Replace**
5. **Bind selected queries** (all 8 are pre-checked), then **Save & run**

## OPERATIONAL WARNING: deploy_sage.py used to clobber the destination

**Fixed 2026-08-25, and worth reading before touching this dataflow.**

The connection bindings in `queryMetadata.json` are **environment state, not source.** The
script originally wrote them from the committed file, so running `--apply` overwrote whatever
the portal had configured — which is precisely what happened after the destination was fixed
by hand: the next deploy silently reverted it and took Sage down again. Twice, because the
first time it was not understood.

`build_definition()` now reads the LIVE `connections` and `gatewayObjectId` off the deployed
item and preserves them, taking only the mashup from git. The mashup is the versioned
artifact — it is the logic, it is diffable. The connection ids are not: `Lakehouse cforey-c`
is a personal cloud connection, and the one originally committed here was **Rebecca's**,
which is the root cause of the whole destination saga.

**If the destination breaks again**, the repair is in the portal and takes about six clicks:
Power Query → **Default data destination → Remove**, then **Add → Lakehouse**, set
**Data gateway → `(none)`** (this is the whole trick), pick `CD_Bronze_Lakehouse` → `dbo`,
update method **Replace**, **Bind selected queries** (all pre-checked), **Save & run**.

## Actual-cost-by-cost-code is NOT available from Sage (measured 2026-08-25)

This was written up on 2026-08-25 as "the prize" — `apivln` carries an account on 901 of 901
lines, so `fct_BudgetLine`'s invoiced column could finally stop being Procore-only. **That was
wrong, and it was wrong because "901 of 901 carry an account" was reported without checking
what those accounts are.**

They are **GL accounts, not cost codes**, and the distribution kills the idea outright:

| `actnum` | Lines | Value |
|---|---:|---:|
| **50004** | **431** | **$10,437,732.28** |
| 50001 | 160 | $2,777,337.76 |
| 50005 | 56 | $137,715.03 |
| 50400 | 41 | $422,154.68 |
| everything else | 213 | $1,734,442.03 |

**Two-thirds of the money sits on one account.** `sub_account` is NULL on every row, and
`phsnum` — the phase, the other candidate — is **0 on all 871 AP headers**. So the only
dimensions Sage AP offers are project and a four-way-ish GL split.

Repointing `fct_BudgetLine.SpentToDate` onto this would **replace cost-code-level Procore
figures with a project-level number that is 67% one bucket**. It would make the report worse
and would look like an upgrade. Not done, deliberately.

### What would make it possible

Sage 100 Contractor keeps job cost in dedicated tables that these eight do not include. We
cannot enumerate them: a Power Query navigation to `INFORMATION_SCHEMA.TABLES` fails with
`Expression.Error 10061` because the gateway connection exposes only `dbo`, and the pipeline
Copy route is blocked by the logon trigger (§9).

**So this needs one question answered by someone with direct database access** — Rebecca, or
Nerds That Care: *which table holds job cost detail by cost code?* Add it to `mashup.pq`, and
the budget fact becomes real. Until then, the honest position is that Procore is the only
source of cost-coded actuals and Sage is the source of truth for AR/AP totals.

## The two routes are broken at opposite ends (measured 2026-08-25)

Both were tried against the live tenant. Neither guess would have survived contact.

| Route | Connects to Sage as | Source | Lakehouse destination |
|---|---|---|---|
| **Dataflow Gen2** (`CD_Sage_Ingest`) | `Mashup Engine (TridentDataflowNative)` | **works** — read for 3m25s and 3m55s | **fails** — binding points at a connection we do not own |
| **Copy activity** (`CD_Sage_Copy`) | `.Net SqlClient Data Provider` | **blocked** — SQL error 17892 | works — needs no connection at all |

### Why the Copy route is blocked

All eight activities failed identically:

```
Logon failed for login 'FabricReader' due to trigger execution.
SqlErrorNumber=17892   Source=.Net SqlClient Data Provider
```

That is §9 of the Nerds That Care handoff doing its job. Sage 100 runs a SQL Server logon
trigger that refuses any application not named in an XML allow-list. The document lists
`.Net SqlClient Data Provider` as approved — so either the XML on the server does not match
the document, or the host check (`%LOCALHOST%`) resolves differently for the Copy runtime
than for the mashup engine.

**§9 names the diagnostic itself:** Windows Event Viewer on `NC-AFFECT-1`, Application log,
**Event ID 17063**, which logs the exact application name being blocked. That is one lookup
by whoever administers the Sage box, and it would settle the question outright.

`CD_Sage_Copy` is left deployed and failing on purpose. It is correct, and it starts working
the day that XML entry lands — which makes it a concrete ask with a demonstrated failure
attached rather than a theoretical request.

### Why the Dataflow route is the one to finish

The mashup engine is demonstrably allowed: `Build_Sage_Test` runs on it today, and ours read
Sage for minutes before failing. The source half is solved and needs nothing from anyone.

What is left is one connection. `queryMetadata.json` bound the destination to Lakehouse
connection `44379bed-…`, which belongs to somebody else — `GET /connections/44379bed-…`
returns **403 InsufficientPermissionsToManageConnection**, and the refresh fails on
`*_WriteToDataDestination` with "Data source credentials are missing or invalid" (error
999999). Those ids were almost certainly copied from `Build_Sage_Test` when this dataflow was
authored, and survived unnoticed because the dataflow had no deploy script until now
(`deploy_sage.py`).

A Lakehouse connection cannot be created from the REST API without interactive consent:
`POST /connections` accepts the shape once `credentialDetails.credentials.useCallerIdentity`
is set, then fails with `OAuthTokenLoginFailed`. So this last step is a portal action, and
there is no way around that:

> **`Build` → `charley-dev` → `CD_Sage_Ingest` → Edit → set the data destination to
> `CD_Bronze_Lakehouse` → Save/Publish → Refresh.**

Setting the destination in the UI creates the Lakehouse connection under the signed-in
identity, which is the one thing the API will not do. Roughly two minutes, and it is the last
mile of the whole Sage subject area.

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

1. ~~Bind the dataflow to the on-prem gateway.~~ **Done** — deployed and bound 2026-08-02 to
   `1e798beb-cc0f-4f72-bb1e-9c8fca8ba03e` (carried in `queryMetadata.json`, so it was a field
   to confirm rather than one to discover). What replaced it is the single **"Can use"** grant
   described at the top of this document. That needs Affect — the gateway connection and its
   credential are theirs, and the Sage database is administered by an outside consultant, so
   the ask may route through them.
2. Run it, then write `sql/silver/20_sage_silver.sql` to type and validate the eight tables.
3. Settle open question 4 with the line data in hand, and point `sv_ar_invoices` at
   `cd_silver_*` — it currently still reads the existing warehouse
   (`01_source_views_cd.sql`), which keeps `fct_Invoice` at its 122 rows rather than zero
   while this is blocked.

**This is now the only access grant left.** The Outbuild token arrived on 2026-08-19, and the
Key Vault ask was withdrawn the same evening as having named the wrong vault. Worth raising on
the same call as the two Procore 403s (`punch_item_types`, `schedule`), which are the only
other thing here Affect grants rather than us building.

## Isolation

This creates a **new** dataflow in the `charley-dev` folder. The existing
`Build_Sage_Test.Dataflow` is not modified, and its `DefaultDestination` is untouched — ours
writes only to `CD_Bronze_Lakehouse`. Reading the same SQL Server through the same gateway is
a read; it does not disturb the existing dataflow's schedule or output.
