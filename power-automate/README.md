# power-automate

Two Power Automate flows and the SharePoint they run on, for the BUILD job-setup SOP:
create an estimating folder for a new job, and convert an estimating job into a project.

**Status, 2026-08-19: both flows exist in Affect's tenant, created stopped.**

    Estimating Setup      98d2c411-a668-42f2-a2a2-f68e4d528a54
    Convert to Bidding    d8a239e6-e668-474c-a33d-50145601e7ab

They run against **`AFFECTBUILD1`** — a site Affect already had, not a new site called
`BUILD` — whose libraries, template trees and `Job Register` are provisioned. `dim_Job` reads
the register through the medallion, so the chain is closed end to end.

They are **not turned on**, and two things are needed before they are:

1. **What goes inside the two folder templates.** The SOP names both and never says. Today
   they would copy a correct but empty skeleton.
2. **A service account to own the SharePoint connection.** The flows run as whoever created
   it, so a named person's account means they break when that person leaves.

`flows/*.json` still ship with `REPLACE-ME` as the host, deliberately — the site is passed at
deploy time, and `test_flows.py` asserts no tenant is hardcoded.

```
RUNBOOK.md                       Ordered steps. BOTH SharePoint sites, and Fabric.
deploy_flows.py                  Creates both flows via the API. The route that worked.
bootstrap_site_via_flow.py       Provisions the BUILD site THROUGH a throwaway flow. Why: below.
bootstrap_reporting_site.py      Same trick for the reporting site's 18 intake lists.
provision_build_site.py          Graph provisioner. Reads work, writes 403 - kept as a survey.
provision-sharepoint-build.ps1   PnP PowerShell. Needs a consent this tenant would not give.
make_import_packages.py          Legacy import package. Rejected by the importer - see RUNBOOK.
flows/EstimatingSetup.json       New job  ->  01 ESTIMATING/E-YY-###-Project Name
flows/ConvertToBidding.json      E-YY-### ->  00 PROJECTS/YY-###-Project Name
test_flows.py                    Offline self-check. No network, no tenant. 20 checks.
```

---

## The Job Register is the whole design

One SharePoint list on the BUILD site does four jobs at once:

| Role | How |
|---|---|
| **Trigger** | A new row starts Estimating Setup. Setting `Stage = Bidding` starts Convert to Bidding. |
| **Sequential-number authority** | `max(JobSeq)` for the current `JobYear` is read from this list. There is no counter anywhere else. |
| **Audit log** | Every run writes back to the row it was triggered by. List versioning is on, so every field change has a who and a when. |
| **`dim_Job` source** | The `CD_Manual_Ingest` dataflow reads this list into `cd_bronze_man_job_register`, and it lands in `CD_Gold_Lakehouse` as `dim_Job`. See "How this reaches Fabric" below. |

That is the point: there is no separate log to forget to write to, and no second place a job
number can be issued from. A run that does not update its row is a run that failed, and the
row says so.

### Contract

| Column | Type | Written by | Notes |
|---|---|---|---|
| `Title` | Text, required | person | The project name, exactly as typed. Never sanitised in place - the sanitised form only ever exists as a folder name. |
| `JobYear` | Number | Estimating Setup | Two digits, e.g. `26`. |
| `JobSeq` | Number | Estimating Setup | Sequential within `JobYear`. **Do not edit by hand.** |
| `JobNumber` | Text | Estimating Setup | `YY-###`, e.g. `26-025`. |
| `Stage` | Choice | both | `Requested` / `Estimating` / `Bidding` / `Failed`. Default `Requested`. |
| `EstimatingFolderUrl` | Hyperlink | Estimating Setup | |
| `ProjectFolderUrl` | Hyperlink | Convert to Bidding | Empty until converted. Doubles as the loop guard - see below. |
| `RequestedBy` | Text | Estimating Setup | Email of the row's author. Text, not a Person column: a Person column lands in Fabric as a nested record that silver then has to unpick. |
| `RequestedAt` | DateTime | Estimating Setup | The row's `Created`. |
| `CompletedAt` | DateTime | both | |
| `CopyJobStatus` | Text | both | Last `CreateCopyJobs` outcome, including the skipped-because-it-already-existed cases. |
| `ErrorDetail` | Multi-line | both | Empty on a healthy run. |

### How someone uses it

1. Add a row. Type the project name in `Title`. Leave everything else.
2. A minute later the row says `Estimating`, `JobNumber` is `26-025`, and
   `EstimatingFolderUrl` links to the new folder.
3. When the job goes to bid, set `Stage` to `Bidding` on the same row.
4. A minute later `ProjectFolderUrl` links to `00 PROJECTS/26-025-Project Name`.

If a row says `Failed`, `ErrorDetail` says why. Fix the cause and set `Stage` back to
`Requested` (or `Bidding`) to retry - both flows are idempotent, so a retry after a partial
run finishes the job rather than duplicating it.

---

## EstimatingSetup.json, step by step

1. **Trigger** - new item in Job Register. **Concurrency = 1.**
2. Derive `/sites/BUILD` and `https://<tenant>.sharepoint.com` from the single `SiteUrl`
   parameter, so there is only one URL to keep correct.
3. Skip rows that are not at `Stage = Requested` (somebody backfilling history).
4. **Sanitise** the project name: strip `" * : < > ? / \ | # %`, trim, then strip up to three
   trailing dots.
5. **Validate, before anything is created**: name non-empty, within the 80-character budget,
   no leading or trailing dot left, and site URL + job folder + a 200-character allowance for
   the template tree beneath it under SharePoint's 400-character limit. Failure writes
   `Stage = Failed` with a specific `ErrorDetail` and stops. Nothing has been created yet.
6. Read the last `JobSeq` for this `JobYear`, add one, format `YY-###`, build
   `E-26-025-Project Name`.
7. **Idempotency probe** - `GET GetFolderByServerRelativeUrl`. If it is already there, write
   the row and exit `Succeeded`. Nothing is duplicated and nothing errors.
8. Create the job folder.
9. Enumerate the template's immediate children (`?$expand=Folders,Files`) - the SOP says copy
   the folders *from* the template, not the template itself.
10. **`POST _api/site/CreateCopyJobs`** with all of them in one batch.
11. **Poll `GetCopyJobProgress`** every 20s until `JobState` is 0. Ceiling: 120 polls / 1 hour.
12. Scan the returned logs for `JobError` / `JobFatalError` - a job can reach `JobState 0` and
    still have failed, and the log is the only place that shows.
13. Write the row: `Stage = Estimating`, number, URL, timestamps, `CopyJobStatus`.
14. `Handle_Failure` scope catches whatever the explicit guards did not.

## ConvertToBidding.json, step by step

1. **Trigger** - item modified in Job Register. **Concurrency = 1.**
2. **Loop guard** - proceed only if `Stage = Bidding` **and** `ProjectFolderUrl` is empty
   **and** `JobNumber` is set. See "Failure modes" below; this one matters.
3. Find the estimating folder **by number**: list `01 ESTIMATING` and match a child whose name
   starts with `E-26-025-`. The SOP converts by number, and matching on the prefix means a
   project title edited after setup still converts.
4. No match - write `Stage = Failed` saying so, and stop before anything is created in
   `00 PROJECTS`.
5. Drop the `E-` prefix: `substring(name, 2)` -> `26-025-Project Name`. The prefix is verified
   first, or a hand-renamed folder would silently lose two real characters. Path length is
   re-checked here too, because the project path is longer than the estimating one.
6. Idempotency probe on `00 PROJECTS/26-025-Project Name`; if present, record and exit clean.
7. Create it, then **`CreateCopyJobs`** the standard project template's children into it, poll,
   scan logs.
8. Probe `01-BIDDING/02-ESTIMATING` inside it, and create it if the template did not supply it -
   one extra folder create is cheaper than a failed run.
9. **Second `CreateCopyJobs`**: the estimating folder's children into `01-BIDDING/02-ESTIMATING`.
   Poll, scan logs.
10. Write the row: `ProjectFolderUrl`, `CompletedAt`, `CopyJobStatus`.
11. `Handle_Failure` scope. It deliberately does **not** write `ProjectFolderUrl`, so a fixed
    problem can be retried by setting `Stage` back to `Bidding`.

---

## Why concurrency 1

Read the current maximum, add one, write it back. Two runs overlapping means both read 24,
both compute 25, and two different projects are called `26-025`.

Nothing errors. No copy job fails. Nobody notices until someone opens the wrong folder weeks
later, and by then both trees have real documents in them.

SharePoint lists have no atomic increment and no unique constraint we can lean on, so the only
fix available is to stop the runs overlapping:

```json
"runtimeConfiguration": { "concurrency": { "runs": 1 } }
```

This is the single most likely production bug in the whole solution, and it is a **setting**,
not code. It is in the committed definitions, but the Power Automate UI also exposes it under
*trigger -> Settings -> Concurrency Control*, and anyone editing the flow in the designer can
turn it off without touching a line. `test_flows.py` asserts it on both triggers so that
turning it off shows up in a diff.

Cost: jobs are created one at a time. Each run is seconds of flow time plus however long the
copy takes. For a firm creating a handful of jobs a day this is free.

### And the production guard for it lives in Fabric

`test_flows.py` asserts the setting is present, so **removing** it shows up in a diff. That
does nothing about somebody switching it off in the **live** flow through the designer, where
there is no diff to read — and that is the likelier way it happens.

So the check that catches it is at the other end of the chain. `dim_Job` carries a blocking
data-quality expectation on `JobNumber` uniqueness
(`foundation/charley-dev/02-transformation/dq/expectations.py`). Two jobs issued `26-025`
fails the nightly gate on the day it happens, with both offending rows named, instead of
surfacing weeks later as two folder trees that both contain real documents.

That only works because the silver parser deduplicates on the SharePoint **item id**, not on
`JobNumber`. Deduplicating on the number would look reasonable, discard one of the two real
jobs, and hide the exact thing being checked. `test_silver.py` asserts both rows survive.

## How this reaches Fabric

Until 2026-08-19 it did not. This README described the Job Register as the `dim_Job` source
while nothing anywhere read it — no bronze table, no dataflow query, no silver parser, no gold
DDL. The flows created folders and issued job numbers, and not one row reached the platform.

The chain now runs the same medallion every other source does:

```
Job Register (SharePoint, /sites/BUILD)      written by flows/*.json
  -> cd_bronze_man_job_register              CD_Manual_Ingest.Dataflow, the one query
                                             reading SITE_BUILD rather than SITE
  -> cd_silver_man_job_register              sql/silver/30_manual_silver.sql
  -> sv_man_job_register                     sql/silver/01_source_views_cd.sql
  -> dim_Job                                 sql/gold/13_dim_job.sql
```

Two things worth knowing about the shape:

- **There is no `ProjectKey` on `dim_Job`.** A job is registered when somebody asks for an
  estimate, long before anyone knows whether the work will be won, and a job lost at bid never
  becomes a Procore project at all. Giving it a project key would mean inventing one or
  dropping every unwon job — and the second quietly turns "how many jobs did we estimate this
  year" into "how many did we win".
- **`dim_Job` stops at gold.** It is not bound to either semantic model yet, because no report
  visual asks for the job pipeline. Binding it is one TMDL table and a relationship when one
  does; binding it now would add a table nothing reads, which this platform has been bitten by
  before.

Nothing here runs until `CD_Manual_Ingest` is published — see [`RUNBOOK.md`](RUNBOOK.md), step
5. Until then `cd_06_land_manual` declares the bronze table empty so the nightly pipeline stays
green, and `dim_Job` reads as an honest blank rather than breaking the build.

## Why `CreateCopyJobs`, not the connector's "Copy folder"

| | Connector "Copy folder" | `CreateCopyJobs` |
|---|---|---|
| Where the work happens | The flow runtime, item by item | SharePoint's migration engine, server-side |
| Deep trees | Recurses from the flow, one API call per item | One call for the whole batch |
| Throttling | The documented failure mode for exactly this shape of job - a deep template copy is a burst of small calls from a single connection | Queued and rate-managed by SharePoint |
| Metadata | Shallow; loses version history and some column values | Preserves the tree; version history skipped deliberately via `IgnoreVersionHistory` |
| Async | No - the flow blocks and can time out mid-tree | Yes - returns a job id, poll `GetCopyJobProgress` |
| Licensing | Standard | **Standard.** It is called through *Send an HTTP request to SharePoint*. |

That last row is the reason this is viable. `CreateCopyJobs` is a REST call, and the obvious
way to make a REST call in Power Automate is the **HTTP** connector, which is **premium** and
would put a per-user licence between the client and their own folder structure. *Send an HTTP
request to SharePoint* is part of the standard SharePoint connector, is authenticated by the
same connection the rest of the flow uses, and can call any SharePoint REST endpoint.
`test_flows.py` asserts no other connector appears in either definition.

`NameConflictBehavior` is `0` (fail on conflict) rather than replace or rename. The
idempotency probe has already established the destination did not exist, so a conflict at this
point means something raced us, and that should surface rather than overwrite.

---

## Failure modes and how each is handled

| Failure | Handled by |
|---|---|
| Two requests race for the same number | Trigger concurrency 1. |
| Flow re-run, or someone re-saves the row | Folder-exists probe before create. Logs `Skipped - folder already existed`, exits `Succeeded`. |
| Project name contains `/`, `:`, `?` ... | Stripped before use. The raw name stays in `Title`. |
| Name is only forbidden characters, or ends in a dot | `Validate_Name` fails the run before any folder exists. |
| Path would breach the 400-character URL limit | Same guard, using `TemplateDepthAllowance` for the tree that will land underneath. Raise the parameter if the template gets deeper. |
| **Convert flow re-triggers on its own write** | Its final action updates the row it was triggered by, which re-fires the trigger. The guard requires `ProjectFolderUrl` to be empty, so the second pass exits immediately. Without this it loops forever. |
| Estimating folder not found on convert | Explicit failure, written to `ErrorDetail`, before anything is created in `00 PROJECTS`. |
| Template folder is empty | Detected. `CreateCopyJobs` 400s on an empty `exportObjectUris`, so the flow says "template is empty" instead. |
| Copy job finishes with errors in its log | Logs are scanned for `JobError` / `JobFatalError`; `JobState 0` alone is not success. |
| Copy takes longer than an hour | `Until` limit trips, `Main` times out, `Handle_Failure` writes `Stage = Failed`. |
| Throttling, 500s, connection expiry | `Handle_Failure` scope, run-after `Failed` / `TimedOut` / `Skipped`, writes `Stage = Failed` and the failed actions' detail into `ErrorDetail`. |
| More than 999 jobs in one year | **Not handled.** `formatNumber(seq, '000')` produces `26-1000`, which is no longer `YY-###`. The SOP has no answer either. `test_flows.py` records this ceiling explicitly. |

---

## Manual import steps

**They live in [`RUNBOOK.md`](RUNBOOK.md)**, in order, covering both SharePoint sites and the
Fabric binding in one sequence. They used to be duplicated here, which is how the reporting
site's script came to be a footnote below rather than a step - and provisioning only the BUILD
site is the mistake that costs the most, because nothing about it fails visibly.

**That sequence is now largely history — most of it has been done.** What actually worked is
`deploy_flows.py`, which posts the workflow definition straight at the Power Automate API and
needs no package, no PnP app and no admin consent. Both flows were created that way on
2026-08-19; `CD_Manual_Ingest` is published; both sites are fully provisioned — the reporting
site's 18 lists on 2026-08-19 and their 142 columns and 19 project rows on 2026-08-20.

What is left: sign the dataflow in, supply the template contents, point the connection at a
service account, confirm trigger concurrency is still 1, then turn the flows on and
smoke-test with `Test / Job: "Alpha"`.

**`flows/*.json` cannot be imported directly.** They are workflow definitions, which is the
right thing to keep in git and not a thing Power Automate accepts — its Import menu offers
only a Dataverse solution or a legacy package. `make_import_packages.py` builds the legacy
package. The admin consent above is for PnP and the SharePoint provisioning; importing a
package needs no consent at all.

Run `python power-automate/test_flows.py` after any edit to the definitions.

### There is a second provisioning script, and it is easy to miss

`provision-sharepoint-build.ps1` creates only what *these two flows* need: the `01 ESTIMATING`
and `00 PROJECTS` libraries, both template trees, and the `Job Register` list.

The **data platform's** intake lists are a separate script:

```
foundation/charley-dev/01-ingestion/Manual/provision-sharepoint.ps1
```

That one creates **18 lists** — 17 data lists (the 9 feeding the Monthly Progress Report's
manual fields plus the 8 PQP quality registers, 140 columns between them) and `CD Projects`,
a lookup that holds no report data and exists so `ProjectKey` cannot be mistyped. Both counts
you may see elsewhere are the same thing. It is generated from the gold DDL by
`_local/make_sharepoint.py`, so it is never hand-edited; regenerate rather than patch.

**Provisioned, in two parts.** The **18 lists** landed 2026-08-19; their **142 of 142
columns** and the 19 `CD Projects` rows landed 2026-08-20. Worth keeping straight, because
the run that created the lists was recorded at the time as having created *nothing* — it had
finished phase 1 and stalled on phase 2, and nothing in the run status said which.

Confirm with `--verify`, which reads the site back through Graph; `--probe` is the one-call
check for whether a *newly created* site is being served yet.

### The three phases are not equally re-runnable, and one of them bit

Creating a list or a column **fails** when it already exists, which is what makes phases 1
and 2 safe to re-run. Creating a list **item** always succeeds — so phase 3, the `CD Projects`
seed, had no such protection. A second `--apply` on 2026-08-20 left the list holding **38 rows
where 19 were real**, and every batch reported `Succeeded` throughout. `ProjectKey` is a
Lookup at that list, so duplicate rows make the target ambiguous; this is not cosmetic.

Fixed at the source: the seed is now filtered against the keys already in the list, and
`test_flows.py` asserts it. The duplicates were removed.

**Neither the run status nor the dry run could have told you.** A batch reports `Succeeded`
as long as its *last* action did, and the dry run counts only lists — it prints all 142
columns and 19 rows as outstanding whether or not they exist. That is what `--verify` is
for, and it is the only one of the three that answers the question.

Both scripts must run. Provision only the first and the flows work while every `man_*` table
in Fabric stays empty — which looks exactly like "nobody has filled it in yet", so the gap
will not announce itself. Detail: [`_docs/sharepoint-lists.md`](../foundation/charley-dev/_docs/sharepoint-lists.md).

---

## What Affect must supply

| | |
|---|---|
| ~~**The BUILD site URL**~~ | ✅ **Answered.** `AFFECTBUILD1` — Affect reused an existing site rather than creating a `BUILD` one. `flows/*.json` still carry `REPLACE-ME` on purpose; the site is supplied at deploy time and `test_flows.py` asserts no tenant is hardcoded. |
| **Template folder contents** | See the open question below. |
| **The real template folder names** | Both are taken literally from the SOP. Evidence says `YY` is Affect's own placeholder convention, not a year: the repo root holds `YY-000 PROJECT NAME_InternalReport_YYMMDD.xlsx`, using `YY` and `YYMMDD` the same way. So `YY-000 STANDARD PROJECT TEMPLATE` is most likely the literal folder name, and is year-agnostic — good. **`02 E26-000 BOILER PLATE` is the problem**: it bakes in `26`, so in January someone must either rename the folder or edit `$EstimatingTemplateRoot` and the flow parameter. The two templates follow different conventions. Confirm both names, and prefer renaming the estimating one to carry no year. |
| **A service account for the connection** | The flows run as whoever owns the SharePoint connection. A named person's account means the flows break when they leave, and `RequestedBy` still records the requester correctly either way. |
| **Who may add rows to Job Register** | Anyone who can add a row can issue a job number. |
| **Confirmation that `01-BIDDING/02-ESTIMATING` is right** | It is derived from the SOP wording, not from a folder anyone has seen. |
| **The 1000-jobs-per-year answer** | Only if it could ever matter. |

### Open question: what is actually inside the two templates?

**The SOP names both template folders but never says what is in them.** The provisioning script
creates the folder *structure* so the flows have something real to copy and so the shape is
reviewable, but every folder name in `$EstimatingTemplate` and `$ProjectTemplate` in
`provision-sharepoint-build.ps1` is a **placeholder** except one:

- `01-BIDDING/02-ESTIMATING` is the single certainty. The Convert-to-Bidding SOP step copies
  the estimating folder into exactly that path, so the standard project template must contain
  it or the flow has nowhere to land.

The **boilerplate documents** inside those trees - blank forms, checklists, the standard
subcontract, whatever the firm actually starts a job with - cannot be inferred from anything in
the SOP. They must come from the client, or be lifted wholesale from an existing job that is
known to be set up correctly.

Until that is done, the flows will run, create the right folders, and copy a correct but empty
skeleton. `EstimatingSetup` detects a completely empty template and says so rather than
reporting a successful copy of nothing.
