# Build status

What exists, what is verified, and what is not built yet.

**Every number on this page was read back out of Fabric**, not carried forward from the
last edit. The core row counts and Model A figures were measured 2026-08-02; the item
inventory, blockers, Azure position and every PQP figure were measured live on
**2026-08-19**. Where a figure here disagrees with an older doc, this one is the measured
value — see [`assessment.md`](assessment.md) for how each was obtained.

**This page is the single source for two numbers that get restated elsewhere:** the
endpoint-registry count (**44**, generated into
[`endpoint-inventory.md`](endpoint-inventory.md) — 42 before the PQP work added
`checklist_lists` and `checklist_list_items`) and **scorecard coverage (59%)**. Other
documents should link here rather than repeat them.

## Live in Fabric

Workspace `Build`, folder `charley-dev` (`25dd1e34-…`). **Nothing outside `charley-dev` has
been touched** — `fabric_backup.py` diffed to a scratch directory is the acceptance gate, not
a promise.

Re-read on 2026-08-19: **20 items.** The three lakehouses and their SQL endpoints, eight
notebooks, `CD_Master_Pipeline`, the `CD_Sage_Ingest` dataflow, **two semantic models** and
**two reports**. The second model and report are the PQP (Project Quality Plan) subject
area, deployed 2026-08-19 — see [`pqp-solution.md`](pqp-solution.md) for why it is a second
model rather than 19 more tables in the first.

| Item | Type | Contents |
|---|---|---|
| `CD_Bronze_Lakehouse` | Lakehouse | 40 tables, from Affect's **production** Procore tenant |
| `CD_Silver_Lakehouse` | Lakehouse | 15 typed tables, **14,791 rows, 0 rejects** |
| `CD_Gold_Lakehouse` | Lakehouse | 40 tables at the 2026-08-02 read — dimensions, facts, crosswalks, bridges, `man_*` — plus the PQP tables landed 2026-08-19. `gold_schema.json` now publishes **54** table schemas (was 45) |
| `cd_01_extract_procore` | Notebook | deployed; held out of the DAG until the Procore credentials are rotated (see below) |
| `cd_05_land_to_bronze` | Notebook | merges landed NDJSON into bronze Delta, no credentials |
| `cd_06_land_manual` | Notebook | manual-input capture path |
| `cd_10_bronze_to_silver` | Notebook | runs clean against real bronze |
| `cd_20_seed_gold` | Notebook | seed dimensions; asserts its own row counts |
| `cd_30_build_gold` | Notebook | 20 gold files + integrity checks; publishes the schema |
| `cd_40_dq_checks` | Notebook | the DQ gate — **107 expectations** (83 blocking, 24 warning) |
| `cd_90_query` | Notebook | ad-hoc query scratchpad against the medallion |
| `CD_Master_Pipeline` | DataPipeline | 6 activities, the nightly DAG |
| `CD_Sage_Ingest` | Dataflow | **deployed**, bound to the on-prem gateway, inert until the connection grant lands |
| `Affect Project Report` | SemanticModel | Model A — Direct Lake, **37 tables, 99 measures, 45 relationships** |
| `Project Quality Plan` | SemanticModel | Model B — Direct Lake, **19 tables plus `_Measures`, 42 measures, 23 relationships**. New 2026-08-19 |
| `Monthly Progress Report` | Report | **12 pages, 180 visuals**, drill-through, 3 bookmarks — [screenshots of the 10 visible pages](../../../resources/power-bi/monthly-progress-report/) |
| `Project Quality Plan` | Report | **7 pages, 95 visuals**, over Model B. New 2026-08-19 |

### Silver, from our own ingestion

All 15 tables populated, `cd_dq_rejects` empty — nothing was rejected at the silver boundary.

| Silver table | Rows | | Silver table | Rows |
|---|---:|---|---|---:|
| `cd_silver_cost_codes` | 5,433 | | `cd_silver_billing` | 607 |
| `cd_silver_submittals` | 2,245 | | `cd_silver_direct_costs` | 418 |
| `cd_silver_punch_items` | 1,469 | | `cd_silver_budgets` | 402 |
| `cd_silver_vendors` | 1,098 | | `cd_silver_project_vendors` | 393 |
| `cd_silver_manpower_daily` | 911 | | `cd_silver_prime_change_orders` | 307 |
| `cd_silver_observations` | 850 | | `cd_silver_prime_contracts` | 20 |
| `cd_silver_rfis` | 616 | | `cd_silver_projects` | 19 |
| | | | `cd_silver_incidents` | 3 |

`cd_silver_budgets` and `cd_silver_prime_change_orders` — empty at the last edit, waiting on
Procore's 600/hour limit — have since landed.

### Where gold actually reads from

`cd_30_build_gold` runs against **`01_source_views_cd.sql`** — our own `CD_Silver` for 18 of
the source views, with 8 still pointing at the existing `Silver_Lakehouse` for what Procore
does not hold (Sage AR, Outbuild milestones, the Sage vendor crosswalk). Verified by reading
the deployed notebook and counting lakehouse GUIDs.

**The `--source existing` foot-gun is closed.** `deploy_gold.py`'s `DEFAULT_SOURCE` is now
`cd`, so a bare `--apply` builds gold from our own medallion — which is what has been in
production since 2026-08-02. Previously the default was `existing` and a bare `--apply`
silently reverted the medallion to the legacy warehouse. Older docs and older shell history
still carry the `--source cd` flag; it is now redundant rather than mandatory, and passing it
costs nothing.

### ⚠️ A deploy can report Completed and run the PREVIOUS notebook

**Observed 2026-08-19, cause not proven. Verify the output, not the status.**

`deploy_gold.py --apply` was run after editing `33_fct_qc.sql`. It printed
`updated cd_30_build_gold` and `running ... Completed`, and exited 0. The gold tables it
produced were built from the **pre-edit** SQL: `fct_QcNcr` came back with 459 unmapped trades
rather than the 215 the same code had produced minutes earlier, and every `HVAC` row was
still flagged unmapped despite `qc_seed_TradeAlias` sitting in the lakehouse with the right
entry. Re-running the identical command restored 215 and 0.

What is known: the SQL on disk was correct throughout (verified by re-reading it and by the
offline suite, which executes the same files); the statement splitter parsed it into the
expected three statements; and the seed table existed with 16 rows. So the notebook that ran
was not the notebook that had just been uploaded.

A plausible mechanism — **not confirmed** — is that `updateDefinition` only awaits
`wait_for_operation` when Fabric answers **202**. On a synchronous **200** the script goes
straight to submitting the run, and the definition may not have propagated. That is a
hypothesis; it has not been reproduced deliberately.

**The operational rule, regardless of cause: a green deploy is not evidence that new SQL
ran.** Read a number back out of the lakehouse that the change should have moved, and
compare it. Every figure on this page follows that rule, which is why the regression was
caught within the hour rather than shipping into a report.

### Three structural gotchas found on the 2026-08-19 deploys

All three are fixed. Each is written down because each will bite the next person, and none of
them raised an error when it was wrong.

**1. A gold table missing from `gold_schema.json` cannot appear in any semantic model.**
`deploy_gold.py` carries a **hardcoded `tables` list** — it drives the empty-table guard and
the schema publish. The QC tables had never been added to it, so `fct_QcNcr`, `fct_QcPunch`
and `fct_QcSubmittal` were neither row-checked nor published. `deploy_model.py` types a
column from that file, so a table it does not name cannot be typed, and a Direct Lake model
silently cannot bind it. No error anywhere: the gold SQL runs, the tables hold data, the
model deploys, and the table is simply absent. Fixed — the three `fct_Qc*` are in `tables`,
and the five `qc_seed_*` plus `dim_QcStatus` are in the schema-publish list. **45 → 54 tables
published** (53 on the first pass; `qc_seed_TradeAlias` took it to 54 — see the trade
vocabulary fix below). *Adding a gold table means adding it to that list. There is nothing
that will tell you otherwise.*

**2. `20_fieldops_silver.sql` read `$.trade` as an object.** Procore returns
`{"id":…,"name":"Electrical",…}`, and the column was taking the whole object rather than
`$.trade.name`, so it held raw JSON. Two consequences, one of them on the live report:
every `fct_Qc*` trade join failed (**631 of 850 NCRs** resolved to no trade), and
`fct_QualityItem.Trade` on the **live Monthly Progress Report** contained raw JSON. Fixed —
unmapped NCRs **631 → 459**, and `fct_QualityItem.Trade` now reads e.g. `"Windows"`.

The residual **459** was a vocabulary difference rather than a bug, and is now largely
closed — see the trade-vocabulary fix below.

**3. `dim_Project` took the Sage id from a view that hardcodes it to NULL.** Found and fixed
2026-08-19 (second deploy). `10_dim_project.sql` read `SageJobNumber` from `sv_projects`, but
under `--source cd` that view is `SELECT ... CAST(NULL AS STRING) AS sage_project_id`
(`01_source_views_cd.sql:43`) — the Procore project record carries no Sage id. So the column was
NULL for all 19 projects, `fct_Invoice`'s `LEFT JOIN dim_Project ON i.sage_project_id =
p.SageJobNumber` matched nothing, and **all 122 AR invoices — $23,695,760.48 — resolved to
`UNMATCHED`.**

Nothing errored, and this is the instructive part:

- It is a `LEFT JOIN`, so the **row count never changed**. `fct_Invoice` held 117 rows before
  the switch and 117 after, which is exactly the check that was run to prove the switch was
  safe (`01_source_views_cd.sql:38` records it). The rows survived; the *join* did not.
- `IsInCrosswalk` — the flag whose entire job is to catch this — was derived from
  `x.project_id IS NULL` against the same wrong view, so it read **TRUE for every project**. A
  broken join reported itself as fully mapped.
- No DQ expectation covered it. The gate checks invoice dates and `MonthStart` resolution, and
  had nothing asserting the Sage join resolves anything at all.

**Why it regressed:** the legacy `sv_projects` (`00_source_views.sql:25`) reads
`FROM dim_projects_procoreXsage` — under `--source existing`, `sv_projects` *was* the crosswalk,
so both columns were right by accident. Moving to `--source cd` repointed it at the real Procore
project list and silently broke both.

**Fixed** — `10_dim_project.sql` now joins `sv_project_crosswalk` explicitly (deduped with
`MAX`/`GROUP BY`, because a duplicate would fan out the project spine itself), so it is correct
under either source. Measured after the rebuild: projects with a Sage job **0 → 15**,
`IsInCrosswalk` TRUE **19 → 15**, unmatched invoices **122 → 24**, and **$22,548,861.96 of AR is
attributed to a project again**. `fct_FinancialPeriod` went **130 → 142** rows — not a
regression: while every invoice carried `UNMATCHED`, all AR months collapsed onto one fake
project key, so 130 was an undercount.

Three guards were added, because the offline suite passed throughout:

1. The `sv_projects` fixture in `seedrunner.py` supplied `'S100'` for `sage_project_id` where
   production supplies NULL. **The fixture disagreed with production**, so the suite exercised a
   path that cannot exist live. It is now NULL on both rows, matching the real view.
2. `test_gold.py` asserts `SageJobNumber` resolves through the crosswalk, that `IsInCrosswalk` is
   FALSE for an unmapped project, and that `fct_Invoice` matches at least one row to a project —
   the last is the guard that fails when the join dies but the row count does not. Mutation-tested:
   reintroducing the bug fails the suite.
3. A new **ERROR** expectation, `dim_Project.SageJobNumber resolves for at least one project`. A
   project missing from Sage stays a WARN; *every* project missing means the join is dead, not
   sparse, and that is structural enough to block.

*A row count surviving a source change proves the rows survived. It says nothing about whether
### Four data-quality defects fixed 2026-08-19 — all verified live

Three of the four presented as findings about Affect's data and turned out to be our code
being wrong about Affect's conventions. That is the same shape as the `$.trade` defect
above, and it is worth naming: a data-quality flag is a claim about the client, and it has
to survive being checked before it is reported as one.

**1. Submittal statuses: 223 → 0.** The silver `CASE` in `24_qc_procore_silver.sql` handled
`'FOR RECORD ONLY'` — the workbook's dropdown wording — but Procore actually sends
`'For Record'`, and `'Not Reviewed'` was unhandled entirely. **222 of 2,245 submittals**, a
tenth of the register, fell out of every status slicer: not shown wrong, not shown at all.
Both spellings now map to `FOR_RECORD_ONLY`, and `'Not Reviewed'` maps to `PENDING`.

**2. Trade vocabulary: 970 → 506 unmapped, and what is left is narrower.** New seed table
**`qc_seed_TradeAlias` (16 rows)**, generated from `seed/qc_trade_alias.csv` by
`_local/make_qc_seeds.py` and joined in `33_fct_qc.sql` as a fallback **after** the exact
match — on the raw Procore label, because an alias exists precisely when the label does not
normalise to a key. **464 rows recovered.** `fct_QcNcr` **459 → 215**, `fct_QcPunch`
**511 → 291**.

The table carries only unambiguous pairs — `HVAC` → `HVAC_DUCTWORK`, `Sprinkler` →
`FIRE_SPRINKLER`, `Ceramic Tile` → `TILE_STONE`, and so on. Two things are deliberately
still open, and they are different questions:

- **Three ambiguous labels, still unmapped:** `Drywall/Carpentry` (255 rows),
  `Concrete Superstructure` (110) and `Concrete` (64). Framing vs board vs millwork, and
  cast-in-place vs formwork vs slab-on-deck. Only Affect can say which. Attaching a defect
  to the wrong trade is worse than attaching it to none.
- **A separate finding: trades with no equivalent in the library at all.** Roofing, Glazing,
  Windows, Structural Steel, Low Voltage, Demolition, Housekeeping, Light Fixtures, Window
  Treatments and others appear in Affect's Procore trade list and have no counterpart in the
  26-sheet checklist library. That is not a mapping gap — Affect's Procore vocabulary is
  broader than the SaunaLounge workbook. It is a **scope question**: does the checklist
  library want those trades?

The `ponytail:` marker in `33_fct_qc.sql` that predicted this alias table is resolved and
removed.

**3. Cost-code CSI divisions: 807 → 0.** `17_dim_costcodecrosswalk.sql` required two leading
digits, but Affect writes divisions 1–9 **without the leading zero** — `1-1000 GENERAL
REQUIREMENTS` is CSI Division **01**, not an unparseable code. All 807 were fixable (780 as
`N-`, 27 as a bare digit); **not one was genuinely malformed.** The division parse now
zero-pads. **807 cost codes — 15% of the 5,433-code master, spanning divisions 1–9 — had
been silently absent from every by-division rollup.** Divisions 01–09 now hold 2,941 codes,
with 1,540 in division 01 alone.

**4. A new ERROR-severity guard, so the fix cannot rot.**
`referential("qc_seed_TradeAlias","TradeKey","qc_seed_Trade","TradeKey")`. An alias pointing
at a `TradeKey` that does not exist resolves to NULL and reads as *"unmapped"* — so a typo
in a CSV we control would look identical to a trade Affect never aliased. ERROR rather than
warn, because an unmapped trade is a fact about Procore and a broken alias is our bug.

**The suite defines 107 expectations (83 blocking, 24 warning)**, counted out of
`build_suite()` rather than carried forward. It moved three times on 2026-08-19: the
`SageJobNumber` guard came with the crosswalk repair, the trade-alias guard with the
data-quality work, and the two `dim_Job` job-number checks with the Power Automate link.

**The last live run measured 8 warnings and 0 blocking** — against the suite as it stood
that morning, not against all 107. The two `dim_Job` expectations have never been evaluated
live, because the dataflow that fills `dim_Job` has not been signed in and run yet; they
will first fire the night after it does. Where each of the measured ones stands after the
fixes:

| Expectation | Rows |
|---|---:|
| cost codes parse to a CSI division | **0** — passes |
| vendors with no certificate on file | 376 |
| trades unmapped | 215 |
| certificates out of date | 105 |
| projects not in Outbuild | 17 |
| projects not in Sage | 4 |
| retainage released | 3 |
| direct cost stale | 1 |

Every remaining row is a coverage gap or a question for Affect, not corruption — which is
why they warn rather than block.

the joins did.*

### External blockers — re-checked 2026-08-19

Re-checked again late on 2026-08-19, against Azure and the live Outbuild API. **The Key
Vault blocker is gone and Outbuild is live.** Neither turned out to be what it was recorded
as: the vault every document named was the wrong vault, and the Outbuild client had never
been run against the real API. Both are written up in
[`keyvault-runbook.md`](keyvault-runbook.md).

| Blocker | Effect | Owner |
|---|---|---|
| ~~**Key Vault role assignment** on vault `OneLake`~~ | **RESOLVED 2026-08-19 — and the ask is withdrawn.** It targeted the wrong vault. The vault in use is **`AffectKeyVault`** (`https://affectkeyvault.vault.azure.net/`, RG `Affect_Data`, subscription `73932b34-…`), where `cforey-c@affect-group.com` already holds **Key Vault Administrator** inherited at resource-group scope. Reading and writing secrets needs no grant from anyone. `OneLake` remains unreadable by this account and holds nothing we depend on. | — |
| **Procore credentials not yet rotated** | `cd_01_extract_procore` has failed on every run since 2026-08-02 with `Secret 'PROCORE_CLIENT_ID' not found`, and is held out of the nightly DAG so it does not redden it. The vault path is now built and proven; what is missing is the credential itself. Runbook: [`keyvault-runbook.md`](keyvault-runbook.md). | Affect — regenerate in Procore, then `setup_keyvault.py --apply` |
| **Sage gateway connection grant** | `CD_Sage_Ingest` is deployed and correct but its runner has no rights on the gateway, so it fails in ~5 seconds before reaching Sage. One grant: *Can use* on `nc-affect-1\sage100con;Affect Group`. | Affect / their Sage consultant |
| **Procore 403s** on `punch_item_types` and `schedule` | Two report sections cannot be sourced. | Affect — Procore role permissions |
| ~~**No Azure subscription** on this tenant~~ | **RESOLVED 2026-08-19.** "Azure subscription 1" (`0bee26ab-eeb7-4dc9-ab92-fb46d068f6b6`) exists on tenant "Affect Build LLC" (`b2a2225b-4b4e-42ec-ba52-c7e1c2dea580`). | — |
| ~~**`OUTBUILD_API_TOKEN` not issued**~~ | **RESOLVED 2026-08-19.** Rebecca placed it in `AffectKeyVault` as `OutbuildToken` at 18:27 UTC. It reads back through `get_secret` and authenticates: **3,078 rows across 15 endpoints** landed into `cd_bronze_outbuild_*`. | — |

#### Outbuild — measured live, 2026-08-19

| Table | Rows | | Table | Rows |
|---|---|---|---|---|
| `cd_bronze_outbuild_activities` | 1,860 | | `cd_bronze_outbuild_roadblock_types` | 147 |
| `cd_bronze_outbuild_tasks` | 483 | | `cd_bronze_outbuild_companies` | 82 |
| `cd_bronze_outbuild_rfv_types` | 200 | | `cd_bronze_outbuild_tags` | 35 |
| `cd_bronze_outbuild_roadblocks` | 165 | | `cd_bronze_outbuild_projects` | 15 |
| `cd_bronze_outbuild_roadblock_tasks` | 55 | | `cd_bronze_outbuild_users` | 12 |
| `cd_bronze_outbuild_task_tags` | 10 | | `cd_bronze_outbuild_weekly_commitments` | 5 |
| `cd_bronze_outbuild_activity_tags` | 5 | | `cd_bronze_outbuild_rfvs` / `_rfv_tasks` | 2 / 2 |

Read out of Delta via Spark, **not** the Lakehouse SQL endpoint — the endpoint lagged by
hours on this workspace and reported zero Outbuild tables while all 15 existed. It also
reported `dim_Project.SageJobNumber` as null for all 19 projects when Direct Lake showed 15
populated. Treat the SQL endpoint as a convenience, and confirm anything surprising against
Delta or DAX before acting on it.

**Not yet wired:** `sv_outbuild_activities` still reads Rebecca's
`Silver_Lakehouse/Outbuild_activities` dataflow, so `fct_Milestone`'s 52 rows come from her
path, not from `cd_bronze_outbuild_*`. Repointing it risks taking milestones to zero and is
its own piece of work.

#### SharePoint writes: every direct route from a script is closed on this tenant

Measured 2026-08-19, not assumed. Worth recording because the next attempt should not have to
rediscover that two whole auth routes are dead ends.

| Route | Result |
|---|---|
| **SharePoint REST**, `{site}/_api/web` | **401** `{"error":"invalid_request"}` with a token whose audience is correct (`00000003-0000-0ff1-ce00-000000000000`, SharePoint's own app id). The tenant does not accept Azure CLI tokens at the legacy endpoint at all |
| **Microsoft Graph** | Reads **200**. `POST /sites/{id}/lists` → **403 accessDenied**. The CLI's Graph token carries **no `Sites.*` scope**; reads slip through on `Directory.AccessAsUser.All`, and creating a list needs `Sites.Manage.All`. The CLI is a fixed first-party app, so this cannot be widened |
| **PnP PowerShell** | `AADSTS700016`. 3.x needs PowerShell 7 (this machine has 5.1); 1.12.0 signs in through the shared *PnP Management Shell* app, which Microsoft retired and which exists in no directory — so it is not a consent a click can fix |
| **Power Automate API** | ✅ **Works.** A flow's SharePoint actions run server-side **as the connection**, which carries the site permissions of whoever made it. So a flow can do what no script token here can |

That last row is how the sites were provisioned: a throwaway helper flow whose actions are the
REST calls, run once and deleted (`bootstrap_site_via_flow.py`, `bootstrap_reporting_site.py`).
No new consent, no application registered, no credential left behind. **It is a bootstrap, not
a pattern** — it exists only because Power Automate resolves a trigger's list at *save* time,
so the site structure had to exist before the real flows could even be created.

Three things that cost time and are worth knowing:

- **A run reporting `Succeeded` proves nothing here.** Every action runs after the previous one
  on `Succeeded` *or* `Failed`, so the chain survives an already-exists error — which also means
  the run's status only reflects its *last* action. One run reported `Succeeded` while creating
  nothing at all. Read the per-action results, not the run.
- **The SharePoint connector retries 502 silently**, so a call failing repeatedly looks exactly
  like a call making progress. `--probe` in `bootstrap_reporting_site.py` answers it in one call.
- **A newly created site returns 502 from SharePoint REST for roughly its first half hour**
  while Graph reads it perfectly. The site is real; only its REST endpoint lags.

Also from the same token: this account holds `Application.ReadWrite.All`,
`AppRoleAssignment.ReadWrite.All` and `DelegatedPermissionGrant.ReadWrite.All` — so the PnP
consent that `provision-sharepoint-build.ps1` was blocked on all along is something **this
account can approve itself**, if the PnP route is ever wanted.

#### Sage: the database name is `Affect Group`, not `ABMI`

The Sage 100 handoff document (Nerds That Care, May 20 2026) records the validated gateway
connection as database **`ABMI`**, and §12 admits the choice was inferred from Rebecca saying
"Affect Build", listing `Affect Group` among the other databases on the instance. The repo's
`CD_Sage_Ingest` queries `Affect Group`.

`Affect Group` is correct, on the evidence: it yields Sage job numbers 1–22 that resolve to
**15 of the 16 real Procore projects**, carrying $22.5M of AR. The four projects without a job
number are `Standard Project Template`, `Sandbox Test Project`, `TEST - ABM SUBORDINATE` — all
templates, which should have none — and City Harvest, genuinely not yet in Sage. A wrong
database does not join 15 of 16 projects. **No change made;** the handoff document is the thing
that is wrong, and §12 already flags it as needing confirmation.

### The gold model, with real data

Read out of `CD_Gold_Lakehouse` on 2026-08-02.

| Table | Rows | | Table | Rows |
|---|---:|---|---|---:|
| `dim_Date` | 7,670 | | `fct_RfiSubmittal` | 2,861 |
| `dim_CostCode` | 5,434 | | `fct_QualityItem` | 2,319 |
| `dim_CostCodeCrosswalk` | 5,433 | | `fct_Billing` | 607 |
| `dim_Vendor` | 126 | | `fct_DirectCost` | 418 |
| `dim_VendorCrosswalk` | 125 | | `bridge_VendorCostCode` | 407 |
| `dim_Status` | 32 | | `fct_BudgetLine` | 402 |
| `dim_Trade` | 29 | | `bridge_ProjectVendor` | 393 |
| `dim_ActivityCategory` | 28 | | `fct_ChangeOrder` | 307 |
| `dim_ScorecardBand` | 27 | | `fct_FinancialPeriod` | 130 |
| `dim_Project` | 19 | | `fct_Invoice` | 117 |
| `dim_ProjectCrosswalk` | 19 | | `fct_VendorInsurance` | 105 |
| `dim_Owner` | 10 | | `fct_SafetyMonthly` | 59 |
| `dim_ScorecardWeight` | 9 | | `fct_Milestone` | 52 |

`fct_ChangeOrder` is 307, not the 1,812 recorded at the last edit. That is not a
regression: 1,812 counted change order *line items*, 307 counts the change orders
themselves. `validate_model.py:151` records the investigation.

`bridge_VendorCostCode`'s 407 rows cover **398 distinct vendor↔cost-code pairs** — the
remainder are the same pair reached through more than one direct-cost line.
`meta_PipelineRun` now holds **22** rows.

The **17** `man_*` tables (9 original plus 8 PQP intake registers) are deployed and empty,
pending the SharePoint decision. `cd_06_land_manual` creates all 17 bronze tables — typed
and empty when no CSV has been uploaded.

**Three tables are invisible to the SQL analytics endpoint** — `bridge_vendorcostcode`,
`fct_vendorinsurance` and `meta_pipelinerun` do not appear in `INFORMATION_SCHEMA.TABLES`,
though all three hold data and serve the report correctly. Direct Lake reads the Delta
files and is unaffected; only T-SQL against the endpoint cannot see them. This is Fabric's
endpoint metadata sync lagging, not a build failure — but anyone verifying by SQL will
conclude the tables are missing, so check with DAX before believing it.

## How to run it

```bash
python foundation/charley-dev/_local/run_tests.py         # 14 suites, offline, no Fabric
python foundation/charley-dev/_local/deploy.py --verify   # items + schema check
python foundation/charley-dev/_local/deploy_seeds.py --apply
python foundation/charley-dev/_local/deploy_manual.py --apply   # MUST precede deploy_silver
python foundation/charley-dev/_local/deploy_silver.py --apply
python foundation/charley-dev/_local/deploy_gold.py --apply     # --source cd is now the default
python foundation/charley-dev/_local/deploy_dq.py --apply
python foundation/charley-dev/_local/deploy_model.py --apply       # Model A
python foundation/charley-dev/_local/deploy_report.py --apply      # Monthly Progress Report
python foundation/charley-dev/_local/deploy_model_qc.py --apply    # Model B (PQP)
python foundation/charley-dev/_local/deploy_report_qc.py --apply   # Project Quality Plan report
python foundation/charley-dev/_local/validate_model.py    # reframe + DAX assertions
python foundation/charley-dev/_local/deploy_gold.py --diag # last run's diagnostics
```

**`deploy_manual.py` must run before `deploy_silver.py`, and the order is load-bearing.**
Silver parses the `cd_bronze_man_*` tables and `cd_06_land_manual` is what creates them. Run
silver first and the whole notebook fails with `System_Cancelled_Session_Statements_Failed`
— an error that names no table and reads like a Spark fault rather than a missing input. Hit
on the 2026-08-19 deploy; the fix is one earlier step, not a code change.

Every deploy script is idempotent, dry-run by default, and refuses to write outside the
`charley-dev` folder.

## Verification

**Offline — 14 suites, no network, no Fabric.** The `.sql` runs through DuckDB via three
macros, so the tests exercise the *production* Spark SQL rather than a re-implementation.
66 gold assertions (two reproducing the reconciliation gate exactly: Current Contract
9,116,960.48 and Contract Growth 3.60%), plus seed, silver, extractor-contract, report
accessibility and library self-checks. Mutation-tested: five deliberate regressions are
each caught.

A gate passing is not the same as a gate watching. The change-order fixture put all three
COs in one month, which makes a per-month roll-up and a cumulative one arithmetically
identical — so the reconciliation gate passed for two months while the portfolio
understated by $4.85M. The fixture now spans two months and three assertions cover the
difference. Worth checking any other fixture that has only one of something.

**In Fabric — the runs assert themselves.** A notebook that builds empty tables still
reports Completed, so both notebooks check their own output and fail the run otherwise.
Currently: expected row counts, zero orphans, every `MonthStart` resolving to `dim_Date`,
no sentinel dates surviving. Proven by injecting a wrong expected count and confirming the
run fails.

**Live DAX — 14 checks.** `validate_model.py` reframes the model and queries it: all tables
readable at expected counts, the queried measures evaluate, `[Budget Variance]` equals
Budget − Spent, `[Total Billed]` reconciles to Paid + Outstanding, and `DATEADD` over
`dim_Date` works — the real proof that `dim_Date` replaced the workbook's `AU4`
`INDEX/MATCH` mechanic.

Separately, on 2026-08-02 **all 99 deployed measures were evaluated against live data** and
none errored. Evaluating without erroring is a weaker claim than being correct: `[Current
Contract]` returned a clean, plausible, wrong number for two months. Nine measures return
blank at portfolio grain — five legitimately (DQ counters with nothing to report) and four
because their source data does not exist yet (`Score - Accounts Receivable`,
`Score - Profitability`, `Score - Completion Variance`, `Score - Daily Reports`).

**Isolation.** `git status` shows nothing modified outside `charley-dev/`; every deploy
asserts the target folder before writing.

## Findings for Affect

### Excel defects now fixed

| Defect | Fix |
|---|---|
| #1a Schedule Performance always scored 3/3 | Bands are fractions (`0.05`/`0.10`), not integers |
| #1b Completion Variance always scored 0 | 0 days now falls in the 3-point band |
| #4 Three different month anchors | One contiguous `dim_Date`, 7,670 days, no gaps |
| #5 `TODAY()` non-reproducibility | `MonthOffset` against a real calendar |
| #6 Inverted milestone dates never flagged | `HasDateInversion`, surfaced on the DQ page |
| #7 `"NA"` string sentinels in date columns | Floored to real NULLs at the silver boundary |
| #9 Trailing whitespace on 12 trades | Seeded pre-trimmed, asserted |
| Full-reload ingestion | `merge_delta` upserts on the natural key |
| Hard-coded credentials | `get_secret()` — Key Vault in Fabric, env var locally |

### New findings — none previously recorded

1. **Sentinel dates in the submittals data.** Dates before 1582-10-15, which Spark refuses
   to read from Parquet at all. Placeholders for "unknown", now floored to NULL.
2. **2 projects have no Sage crosswalk entry** — they cannot join to any financial data
   until the crosswalk is extended.
3. **70 cost codes are absent from master data.**
4. **24 AR invoices reference a Sage job that resolves to no project** ($1,146,898.52).
   Was briefly *every* invoice — see gotcha 3 above.
5. **The scorecard bands have holes** — Observations leaves the value 5 unscored, Daily
   Reports leaves 2. Closed so the bands tile; worth confirming intent.

Findings 2–4 are visible on the hidden Data Quality page. All would have been invisible in
the Excel — 22 facts referencing unmastered keys would simply have been dropped from a
join, understating budgets and change orders with no error anywhere.

## Not built yet

Six rows of this table were stale on 2026-08-02 — silver transforms, RFIs, the `man_*`
tables, the orchestration pipeline and the scorecard measures had all shipped but were
still listed as not started. A seventh was stale on 2026-08-19: `CD_Sage_Ingest` was
listed as "not deployed" for two weeks after it was deployed. Corrected below.

| Area | Status |
|---|---|
| Procore ingestion **run inside Fabric** | Notebook and 44-endpoint registry built and tested; still needs `PROCORE_CLIENT_ID`/`SECRET` in Key Vault. Extraction runs **locally** and lands files; `cd_05_land_to_bronze` merges them. The nightly pipeline therefore re-processes whatever was last landed — **it does not call the Procore API.** |
| Sage dataflow (`CD_Sage_Ingest`) | **Built and deployed** — live in the `charley-dev` folder, bound to gateway `1e798beb` and datasource `835e72c8`, writing to `CD_Bronze`. Inert until `cforey-c@affect-group.com` is granted *Can use* on `nc-affect-1\sage100con;Affect Group`. Deployed-and-inert is deliberate: it turns the remaining work into one grant plus one refresh |
| Manual dataflow (`CD_Manual_Ingest`) | **Published 2026-08-19**, workspace `Build`, folder `charley-dev`, item `54addfb1-df2f-4ab0-9f5f-d0f36c64376e`. **19 queries** — 18 against the reporting site plus `cd_bronze_man_job_register` against BUILD, which is why the generator carries two site constants rather than one. **Not yet authenticated or refreshed**: `queryMetadata.json` ships `connections: []`, the honest not-bound-yet state Fabric fills in on first sign-in, and the destination is pinned in the mashup as `shared DefaultDestination` so it cannot write anywhere unintended while it waits. **The lists it reads are complete**: the 18 lists were created 2026-08-19 and their **142 of 142 columns** and 19 `CD Projects` rows 2026-08-20, read back through Graph rather than taken from the run status. Both site constants were `REPLACE-ME` until 2026-08-19 and are now the real sites. A second defect was found and fixed 2026-08-19: the mashup bound all 18 queries to a `DefaultDestination` it never defined, so it would have deployed and then failed at run on every query. `test_sharepoint.py` now asserts the destination exists. The list-name defect it used to carry is **fixed at the source**: `_local/make_sharepoint.py` now generates the PS1, the mashup, `queryMetadata.json` and `deploy_manual.LISTS` from the `man_*` gold DDL, so one function decides a list name and `test_sharepoint.py` fails the build if the four writers drift. See [`sharepoint-lists.md`](sharepoint-lists.md) |
| Outbuild ingestion | **Live as of 2026-08-19** — token in Key Vault, 3,078 rows landed in `cd_bronze_outbuild_*`. Silver still reads Rebecca's dataflow, so `fct_Milestone` does not consume this yet |
| `man_*` manual tables | **Built and deployed** — 9 tables live in gold, currently empty. The silver → gold `INSERT`s are now written, so the chain runs end to end; the tables stay empty because nobody has entered a row, not because the join is missing. Four column-spec questions still need Affect — [`manual-input.md`](manual-input.md) |
| Orchestration pipeline | **Built and running** — `CD_Master_Pipeline`, 6 activities. Read out of the live pipeline definition 2026-08-19; a pipeline-triggered run of the DQ gate completed 2026-08-19 06:16 UTC |
| Scorecard measures | **Written** — 9 category measures live. **Scorecard coverage is 59%** (`[Scorecard Coverage %]`, live): 5 of 9 categories score from real data, 4 return BLANK for want of source data. This is the canonical figure — other documents reference it rather than restate it. Coverage read 35% before field ops landed and went 35% → 45% → 59%; filling the `man_*` tables is projected to take it to 88%, which is a projection, not a measurement |
| `Vendor & Insurance List` report | **Never built, and no longer planned.** The insurance data reached the Monthly Progress Report instead, as `fct_VendorInsurance` (105 rows) plus a Vendor Insurance page. The stale reference has been removed from `README.md` |
| PQP (Project Quality Plan) subject area | **Deployed and running end to end, 2026-08-19.** Seeds, silver, gold and the DQ gate all ran to Completed against `CD_Gold_Lakehouse`, and the semantic model (`Project Quality Plan`, 19 tables plus `_Measures` / 42 measures / 23 relationships) and its 7-page, 95-visual report are live. Counts below were read back out of Fabric with `query_fabric.py`, not carried forward from the build. [`pqp-solution.md`](pqp-solution.md) |
| Power Automate flows (Estimating Setup, Convert to Bidding) | **Created in the client's tenant 2026-08-19, both stopped.** `Estimating Setup` `98d2c411-a668-42f2-a2a2-f68e4d528a54`, `Convert to Bidding` `d8a239e6-e668-474c-a33d-50145601e7ab`. The BUILD-site structure they trigger on is provisioned on **`AFFECTBUILD1`** — a site Affect already had, not a new `BUILD` site. `power-automate/` holds both definitions, `deploy_flows.py` (the working API route), the bootstrap provisioners, [`RUNBOOK.md`](../../../power-automate/RUNBOOK.md) and 20 passing offline checks. Not yet turned on: the two folder templates' contents are unspecified by the SOP, and the connection owner should be a service account. **Their link to Fabric is now built**: `dim_Job` (`sql/gold/13_dim_job.sql`) lands the Job Register through the medallion, with a blocking DQ expectation on `JobNumber` uniqueness. It had been *described* in `power-automate/README.md` and never implemented — no bronze table, no parser, no DDL |

### PQP tables, measured out of Fabric 2026-08-19

Seeds match the offline expectation exactly, which is the point of the extractor asserting its
own counts.

| Table | Rows | Note |
|---|---:|---|
| `qc_seed_ChecklistItem` | 625 | 26 trade sheets collapsed to one table |
| `qc_seed_Gate` | 93 | 46 TCO + 23 Fire Alarm + 24 Statutory |
| `dim_QcStatus` | 141 | 25 workbook dropdowns, deduplicated |
| `qc_seed_DohItem` | 101 | |
| `qc_seed_Trade` | 26 | |
| `qc_seed_TradeAlias` | 16 | added 2026-08-19 — Procore label → workbook `TradeKey`, unambiguous pairs only |
| **`fct_QcSubmittal`** | **2,245** | live, from the production Procore tenant. **0 now resolve to no status** (was 223) |
| **`fct_QcPunch`** | **1,469** | live. **291 still resolve to no trade** (was 511) |
| **`fct_QcNcr`** | **850** | live, from Procore Observations. **215 still resolve to no trade** (was 459) — see the trade-vocabulary fix above |
| `man_Qc*` (8 tables) | 0 | correct — typed and empty until the SharePoint lists exist |

The three `fct_Qc*` tables carry real production data because the client's workbook names
Procore as the system of record for quality, so NCRs, punch items and submittals are read from
the API rather than retyped. **4,564 quality records reached the platform without anyone
entering anything.**

The regression check also passed: `dim_Project` 19 rows and `fct_BudgetLine` 402 rows are
unchanged, and the nine pre-existing `man_*` tables are now genuinely reachable from silver
rather than orphaned placeholders.

**Deploy order: `deploy_manual.py` must run before `deploy_silver.py`.** Silver now parses
`cd_bronze_man_*`, and those tables are created by `cd_06_land_manual` — typed and empty when
there is no CSV. Running silver first fails the whole notebook with
`System_Cancelled_Session_Statements_Failed`, which names no table and reads like a Spark
problem rather than a missing input. Hit on the 2026-08-19 deploy; the fix is one earlier step,
not a code change.

Related, and **now closed**: `cd_06_land_manual` *is* in `CD_Master_Pipeline`. The live
pipeline definition read on 2026-08-19 has six activities — `Land Manual Input` runs alongside
`Land To Bronze`, and `Bronze To Silver` depends on both. The staleness bug this section used to
describe cannot occur: manual bronze is refreshed before silver reads it. This page recorded the
issue as open for longer than it actually was.

## Environment notes

- **Fabric MCP server is healthy** (`claude mcp list` → `✔ Connected`) but its tools bind
  at session start. The committed REST path in `deploy.py` is the better mechanism for
  *creating* items anyway — idempotent, reviewable as a diff, and folder-scoped. MCP earns
  its keep on exploration (`execute_sql_query`, `execute_dax_query`).
- `pyodbc` + ODBC Driver 18 would allow local SQL-endpoint queries; not required, since
  `validate_model.py` covers the same ground through DAX.

## Fabric behaviours worth knowing

Each of these failed silently or misleadingly, and cost real time:

1. **Direct Lake does not support calculated tables.** The model deploys, reports success,
   and loads *no tables at all*. Every DAX query returns "Failed to resolve name".
2. **`entityName` binds to the physical table, and Spark lowercases table names on write.**
   Fails only at reframe.
3. **A deployed model is not loaded until it is reframed.** A correct definition is not the
   same as a working model.
4. **Partition type cannot change in place** — calculated ↔ Direct Lake requires recreation.
5. **`enableSchemas` is creation-only** on a lakehouse.
6. **A deleted item's name is held for minutes** — retriable 409.
7. **Long-running-operation `Location` headers are absolute** and point at a different host.
8. **Bare `VARCHAR` is invalid in Spark** — it wants `STRING`.
9. **The jobs API reports statement failures with no cell detail** — hence the diagnostics
   written to `Files/_diag/` and downloaded over the OneLake DFS API.
