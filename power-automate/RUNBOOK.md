# Runbook — provisioning SharePoint, importing the flows, binding it to Fabric

Everything that has to happen in Affect's tenant, in order, once.

**Read this first: there are TWO SharePoint sites and TWO provisioning scripts**, in two
different directories, and doing one and stopping is the failure this document exists to
prevent. Provision only the BUILD site and the job flows work perfectly while every `man_*`
table in Fabric stays empty — which on the report is indistinguishable from "nobody has filled
this in yet". Nothing errors. Nothing announces it.

| | Site | Script | What it is for |
|---|---|---|---|
| **1** | `/sites/BUILD` | `power-automate/provision-sharepoint-build.ps1` | The job-setup SOP: libraries, template trees, `Job Register` |
| **2** | `/sites/AffectProjectReporting` | `foundation/charley-dev/01-ingestion/Manual/provision-sharepoint.ps1` | The data platform's intake: 17 lists, 140 columns, `CD Projects` |

Both scripts are idempotent. Re-running after a change is how you apply one, not something to
avoid.

---

## 0. Once per tenant — the step people stall on

```powershell
Install-Module PnP.PowerShell -Scope CurrentUser -Force
Register-PnPEntraIDAppForInteractiveLogin -ApplicationName 'PnP Rocks' -Tenant <tenant>.onmicrosoft.com -Interactive
```

PnP.PowerShell 2.x **removed** the built-in multi-tenant app, so `Connect-PnPOnline
-Interactive` on its own now fails with `ClientId is required`. The registration prints a
ClientId — keep it, every `Connect-PnPOnline` below needs it.

It asks a tenant admin to consent. **This is the only admin gate in the entire runbook**, and
it gates *provisioning* only. Importing the flows (step 4) is an ordinary user action and needs
no consent — see "If you cannot get the PnP consent" below if you are blocked here.

> Commands are one line each on purpose. A copied backslash is not a PowerShell line
> continuation and fails with a confusing parse error.

### If you cannot get the PnP consent

PnP is a convenience, not a dependency. Nothing in the flows or the dataflow needs it — it
only creates SharePoint structure faster and more repeatably than clicking.

| Blocked on | Do instead |
|---|---|
| **BUILD site** (step 2) | Build it by hand: a Team site, two document libraries (`01 ESTIMATING`, `00 PROJECTS`), and one list, `Job Register`, with the 12 columns in README.md's *Contract* table. That is perhaps 20 minutes, and it is the only hand-work worth doing. |
| **Reporting site** (step 3) | **Do not do this by hand.** 17 lists and 140 columns is hours of clicking and every column name must match the `man_*` tables exactly, with no error if one does not — the column simply stops arriving and the report shows a blank tile. Get the consent, or keep using the CSV path (`Files/_manual/*.csv` + `cd_06_land_manual`), which works today and needs nobody. |
| **Importing the flows** (step 4) | Nothing — this never needed consent. Go straight there. |

If you build `Job Register` by hand, get `Stage` right: a **Choice** column with exactly
`Requested`, `Estimating`, `Bidding`, `Failed`, defaulting to `Requested`. The flows branch on
those four strings. And turn on **versioning** — that is what makes every field change record
a who and a when.

---

## 1. Set the site URLs

Four places, and they are **not all the same site**. Everything ships as `REPLACE-ME` on
purpose — this repo never guesses a tenant.

| Placeholder | File | Which site |
|---|---|---|
| `SITE_URL` | `foundation/charley-dev/_local/make_sharepoint.py` | Reporting |
| `SITE_BUILD` | `foundation/charley-dev/_local/make_sharepoint.py` | BUILD |
| `$BUILD_SITE_URL` | `power-automate/provision-sharepoint-build.ps1` | BUILD |
| `--site-url` | passed to `power-automate/make_import_packages.py` (step 4) — **not** edited into `flows/*.json` | BUILD |

**`provision-sharepoint.ps1`, `mashup.pq` and `queryMetadata.json` are GENERATED.** Do not
edit them. Set the two constants in `make_sharepoint.py` and regenerate:

```bash
cd foundation/charley-dev/_local
python make_sharepoint.py
python make_sharepoint.py --check   # exits non-zero if anything is stale
```

That regeneration is the whole point: one function decides every list name, and a list name
that differs by one character does not error — the column simply stops arriving and the report
renders a blank tile.

---

## 2. Provision the BUILD site

Connect to the **tenant root**, not the site — step 5 of the script creates the site, so it
does not exist yet.

```powershell
Connect-PnPOnline -Url https://<tenant>.sharepoint.com -Interactive -ClientId <id from step 0>
./provision-sharepoint-build.ps1
```

That is a **dry run**. It reads and prints and writes nothing. Read the output, then:

```powershell
./provision-sharepoint-build.ps1 -Apply
```

Creates the site, `01 ESTIMATING` and `00 PROJECTS`, both template trees, and the `Job
Register` list.

---

## 3. Provision the reporting site

The site must already exist — create it first if it does not (SharePoint → Create site → Team
site → `Affect Project Reporting`).

```powershell
Connect-PnPOnline -Url https://<tenant>.sharepoint.com/sites/AffectProjectReporting -Interactive -ClientId <id from step 0>
cd foundation/charley-dev/01-ingestion/Manual
./provision-sharepoint.ps1
```

**Run it from that directory.** It reads `cd-projects.csv` from next to itself to populate the
`CD Projects` lookup, and skips the population silently if it cannot find it — leaving you a
lookup list with no projects in it and every intake list unusable.

17 lists, 140 columns, versioning on, `ProjectKey` a lookup everywhere.

---

## 4. Create the two flows

`flows/*.json` are **workflow definitions** — the right thing to keep in git, and not
something Power Automate's Import menu accepts. Use the API instead:

```bash
cd power-automate
python deploy_flows.py                       # dry run - reads, writes nothing
python deploy_flows.py --site-url https://<tenant>.sharepoint.com/sites/<site> --apply
```

The dry run prints your environment, the SharePoint connection it will use, and which flows
it would create. Nothing is written without `--apply`.

**Prerequisites**, both checked by the dry run:

- `az login` in the tenant. The script takes a Power Automate token from your existing CLI
  session — nothing is stored, printed, or written to a file.
- **A SharePoint connection must already exist** in the environment. A connection is a
  credential and cannot be created from a definition: make one at *Power Automate →
  Connections → New connection → SharePoint*, signed in as the account the flows should run
  as. Use a **service account**, not a named person — the flows run as whoever owns the
  connection and break when that person leaves. `RequestedBy` still records the real
  requester either way.

The script **never overwrites** an existing flow of the same name; it skips and says so. A
flow somebody has since edited in the designer is not something to silently replace from a
file, and a second flow side by side is recoverable where a clobbered one is not.

Both flows are created **stopped**. Before turning them on:

1. **Confirm trigger concurrency is 1** — Trigger → Settings → Concurrency Control. It is in
   the definition and `test_flows.py` asserts it, but confirm on the live flow: without it,
   two jobs get issued the same number and nothing anywhere errors.
2. **Confirm the site structure exists** — `01 ESTIMATING`, `00 PROJECTS`, `Job Register`,
   and both template folders. The flows will fail on their first run otherwise.
3. Check `EstimatingTemplate` and `ProjectTemplate` match the real folder names. See the open
   questions at the bottom — one of them almost certainly does not.

> **The site URL is set at creation time and cannot be changed afterwards.** `SiteUrl` is a
> *definition* parameter, not one of the "flow parameters" the designer exposes. To move the
> flows to a different site, delete them and re-run with the new `--site-url`.

### The package route, and why it is not the one above

`make_import_packages.py` builds a legacy import package (`dist/*.zip`) for *My flows →
Import → Import Package (Legacy)*. **It does not currently work.** Two attempts against a
live tenant, both rejected identically:

```
MissingPackageManifest: The package manifest file 'manifest.json'
under 'Microsoft.Flow' folder missing.
```

The manifest **content** is right — the review screen renders the flow's name, description
and *Create as new* straight out of it. Some third location is expected for a second copy and
the error does not say where; adding one at `Microsoft.Flow/manifest.json` changed nothing.

It is kept rather than deleted because the answer is one observation away: **export any
existing flow from this tenant as a package and look at its zip layout.** That gives the
expected paths exactly, and the generator can be corrected in a line. Until somebody does
that, use the API route above.

---

## 5. Publish and bind `CD_Manual_Ingest`

**There is no deploy script for dataflows.** `_local/` has one for notebooks, seeds, silver,
gold, models and reports, but `CD_Sage_Ingest` was published by hand and this one is the same.
Publish it into workspace `Build`, folder `charley-dev`, from
`foundation/charley-dev/01-ingestion/Manual/CD_Manual_Ingest.Dataflow/`.

Then:

1. **Authenticate the destination.** `queryMetadata.json` ships with `"connections": []` — the
   honest "not bound yet" state. Fabric writes that block itself once you sign in. The
   *target* is not in the connection, it is pinned in `mashup.pq` as `shared
   DefaultDestination`, so the dataflow cannot write anywhere unintended while it waits.
2. **Confirm all 19 queries resolve** — 18 against the reporting site plus
   `cd_bronze_man_job_register` against BUILD. That last one uses `SITE_BUILD`; if it fails
   while the others pass, the BUILD URL is wrong or the connection has no rights there.
3. **Set the refresh to hourly during business hours.** Someone edits a risk and sees it in
   the report a few minutes later, which is what removes the "when will my change show up?"
   question.
4. Confirm it landed:

   ```
   mcp__fabric__list_items(workspace_name="Build")   # CD_Manual_Ingest, type Dataflow
   ```

Once it is published, `cd_06_land_manual` leaves `cd_bronze_man_job_register` alone — it only
declares the table when the dataflow has not created it yet, so the nightly pipeline stays
green in the meantime and never overwrites what the dataflow lands.

---

## 6. Smoke test

Add one row to `Job Register` with the Title:

```
Test / Job: "Alpha"
```

Confirm within a minute or so that the row shows `Estimating`, a `JobNumber` of `26-001`, and
an `EstimatingFolderUrl` pointing at:

```
01 ESTIMATING/E-26-001-Test Job Alpha
```

One action exercises the sanitiser (`/`, `:` and `"` all stripped), the number issuer, the
folder create and the copy job. Then set `Stage` to `Bidding` on the same row and confirm
`ProjectFolderUrl` fills in.

Delete the test row and both folders afterwards. The next real job will then be `26-001` —
which is correct, because `JobSeq` is read from the register, not from a counter.

After the next nightly run, `dim_Job` in `CD_Gold_Lakehouse` should hold that row. That is the
end-to-end proof the flows reach Fabric.

---

## 7. Two things Affect has to decide

Neither is ours, and both are cheaper to answer before the templates are populated than after.

**The template trees are placeholder structure.** The SOP names both template folders and
never says what is inside them. `provision-sharepoint-build.ps1` creates a folder *shape* so
the flows have something real to copy, but every folder name in it is a guess **except
`01-BIDDING/02-ESTIMATING`**, which the Convert-to-Bidding step copies into by name and which
must therefore exist. The boilerplate **documents** — blank forms, checklists, the standard
subcontract — cannot be inferred from anything and have to come from the client, or be lifted
wholesale from an existing job known to be set up correctly.

Until then the flows run, create the right folders, and copy a correct but empty skeleton.
`EstimatingSetup` detects a completely empty template and says so rather than reporting a
successful copy of nothing.

**`02 E26-000 BOILER PLATE` bakes in the year.** The project template
(`YY-000 STANDARD PROJECT TEMPLATE`) uses `YY` as a placeholder — the same convention as
`YY-000 PROJECT NAME_InternalReport_YYMMDD.xlsx` in the repo root — and is year-agnostic. The
estimating one is not: in January somebody must rename the folder or edit both
`$EstimatingTemplateRoot` and the flow parameter, and if they do neither the flow fails on a
folder that no longer exists. **Recommend renaming it to carry no year**, and confirm both
names before go-live.

---

## Verifying without a tenant

Everything below runs offline, no network and no SharePoint:

```bash
python power-automate/test_flows.py                      # 14 checks on the definitions
cd foundation/charley-dev/_local
python make_sharepoint.py --check                        # generated artefacts are current
python run_tests.py                                      # 14 suites, incl. dim_Job end to end
```
