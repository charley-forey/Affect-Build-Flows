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
| `CD_Gold_Lakehouse` | Lakehouse | 40 tables at the 2026-08-02 read — dimensions, facts, crosswalks, bridges, `man_*` — plus the PQP tables landed 2026-08-19. `gold_schema.json` now publishes **53** table schemas (was 45) |
| `cd_01_extract_procore` | Notebook | deployed; blocked on the Key Vault role assignment (see below) |
| `cd_05_land_to_bronze` | Notebook | merges landed NDJSON into bronze Delta, no credentials |
| `cd_06_land_manual` | Notebook | manual-input capture path |
| `cd_10_bronze_to_silver` | Notebook | runs clean against real bronze |
| `cd_20_seed_gold` | Notebook | seed dimensions; asserts its own row counts |
| `cd_30_build_gold` | Notebook | 20 gold files + integrity checks; publishes the schema |
| `cd_40_dq_checks` | Notebook | the DQ gate — **103 expectations** (80 blocking, 23 warning) |
| `cd_90_query` | Notebook | ad-hoc query scratchpad against the medallion |
| `CD_Master_Pipeline` | DataPipeline | 5 activities, the nightly DAG |
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

### Two structural gotchas found on the 2026-08-19 deploy

Both are fixed. Both are written down because each will bite the next person, and neither
raised an error when it was wrong.

**1. A gold table missing from `gold_schema.json` cannot appear in any semantic model.**
`deploy_gold.py` carries a **hardcoded `tables` list** — it drives the empty-table guard and
the schema publish. The QC tables had never been added to it, so `fct_QcNcr`, `fct_QcPunch`
and `fct_QcSubmittal` were neither row-checked nor published. `deploy_model.py` types a
column from that file, so a table it does not name cannot be typed, and a Direct Lake model
silently cannot bind it. No error anywhere: the gold SQL runs, the tables hold data, the
model deploys, and the table is simply absent. Fixed — the three `fct_Qc*` are in `tables`,
and the four `qc_seed_*` plus `dim_QcStatus` are in the schema-publish list. **45 → 53 tables
published.** *Adding a gold table means adding it to that list. There is nothing that will
tell you otherwise.*

**2. `20_fieldops_silver.sql` read `$.trade` as an object.** Procore returns
`{"id":…,"name":"Electrical",…}`, and the column was taking the whole object rather than
`$.trade.name`, so it held raw JSON. Two consequences, one of them on the live report:
every `fct_Qc*` trade join failed (**631 of 850 NCRs** resolved to no trade), and
`fct_QualityItem.Trade` on the **live Monthly Progress Report** contained raw JSON. Fixed —
unmapped NCRs **631 → 459**, and `fct_QualityItem.Trade` now reads e.g. `"Windows"`.

The remaining **459** are a real vocabulary difference, not a bug: Procore's trade list says
`HVAC` and `Sprinkler` where the workbook's controlled keys are `HVAC_DUCTWORK` and
`FIRE_SPRINKLER`. They are deliberately **not** guessed — attaching a defect to the wrong
trade is worse than attaching it to none — so they sit behind `HasUnmappedTrade` and a DQ
warning. **This is an open question for Affect:** confirm the alias mapping, and the count
falls to whatever is genuinely unmapped.

### External blockers — re-checked 2026-08-19

Two of the four blockers standing at the last edit have moved. The Azure subscription
exists, a Key Vault exists, and the Outbuild token is in transit. What is left is smaller
and more specific than what it replaced.

| Blocker | Effect | Owner |
|---|---|---|
| **Key Vault role assignment** — vault `OneLake` exists (`https://onelake.vault.azure.net/`, RG `Affect_KeyVault`, East US) but is **RBAC-mode**, and `cforey-c@affect-group.com` holds only **Contributor on the resource group**. Contributor on an RBAC vault can neither read nor write secrets, and cannot grant itself the right to. | No secret can be written, so `cd_01_extract_procore` still cannot hold a credential. Extraction keeps running locally and landing files; `cd_05_land_to_bronze` merges them in Fabric with no secret. **The ask is one role assignment: "Key Vault Secrets Officer" on vault `OneLake` for `cforey-c@affect-group.com`.** | Affect |
| **Sage gateway connection grant** | `CD_Sage_Ingest` is deployed and correct but its runner has no rights on the gateway, so it fails in ~5 seconds before reaching Sage. One grant: *Can use* on `nc-affect-1\sage100con;Affect Group`. | Affect / their Sage consultant |
| **Procore 403s** on `punch_item_types` and `schedule` | Two report sections cannot be sourced. | Affect — Procore role permissions |
| ~~**No Azure subscription** on this tenant~~ | **RESOLVED 2026-08-19.** "Azure subscription 1" (`0bee26ab-eeb7-4dc9-ab92-fb46d068f6b6`) exists on tenant "Affect Build LLC" (`b2a2225b-4b4e-42ec-ba52-c7e1c2dea580`). | — |
| ~~**`OUTBUILD_API_TOKEN` not issued**~~ | **Effectively unblocked** — Rebecca offered to send the token by email on Aug 11. Pending transfer, not pending a decision. | Affect (in transit) |

Step-by-step for whoever grants it: [`keyvault-runbook.md`](keyvault-runbook.md).

**Key Vault `OneLake`, as provisioned:** RBAC authorization on, soft-delete on with a
90-day retention, **purge protection disabled**. Purge protection is worth turning on
before the vault holds anything that matters — without it a deleted vault can be purged
inside the retention window, which defeats the recovery the soft-delete is there to give.

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
4. **23 AR invoices reference a Sage job that resolves to no project.**
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
| Manual dataflow (`CD_Manual_Ingest`) | Defined in the repo, **not deployed** to the workspace — `SITE` in `mashup.pq` is still a `REPLACE-ME` placeholder, so deploying it would create an item that cannot run. The list-name defect it used to carry is **fixed at the source**: `_local/make_sharepoint.py` now generates the PS1, the mashup, `queryMetadata.json` and `deploy_manual.LISTS` from the `man_*` gold DDL, so one function decides a list name and `test_sharepoint.py` fails the build if the four writers drift. See [`sharepoint-lists.md`](sharepoint-lists.md) |
| Outbuild ingestion | Built and verified, cannot run — `OUTBUILD_API_TOKEN` not issued. Outbuild is the only milestone source, and 17 of 19 projects are missing from it |
| `man_*` manual tables | **Built and deployed** — 9 tables live in gold, currently empty. The silver → gold `INSERT`s are now written, so the chain runs end to end; the tables stay empty because nobody has entered a row, not because the join is missing. Four column-spec questions still need Affect — [`manual-input.md`](manual-input.md) |
| Orchestration pipeline | **Built and running** — `CD_Master_Pipeline`, 5 activities, last green run 2026-08-02 22:06 |
| Scorecard measures | **Written** — 9 category measures live. **Scorecard coverage is 59%** (`[Scorecard Coverage %]`, live): 5 of 9 categories score from real data, 4 return BLANK for want of source data. This is the canonical figure — other documents reference it rather than restate it. Coverage read 35% before field ops landed and went 35% → 45% → 59%; filling the `man_*` tables is projected to take it to 88%, which is a projection, not a measurement |
| `Vendor & Insurance List` report | **Never built, and no longer planned.** The insurance data reached the Monthly Progress Report instead, as `fct_VendorInsurance` (105 rows) plus a Vendor Insurance page. The stale reference has been removed from `README.md` |
| PQP (Project Quality Plan) subject area | **Deployed and running end to end, 2026-08-19.** Seeds, silver, gold and the DQ gate all ran to Completed against `CD_Gold_Lakehouse`, and the semantic model (`Project Quality Plan`, 19 tables plus `_Measures` / 42 measures / 23 relationships) and its 7-page, 95-visual report are live. Counts below were read back out of Fabric with `query_fabric.py`, not carried forward from the build. [`pqp-solution.md`](pqp-solution.md) |
| Power Automate flows (Estimating Setup, Convert to Bidding) | **Built locally, not deployed, 2026-08-19.** `power-automate/` holds both flow definitions, the PnP provisioning script and 14 passing offline checks. Nothing exists in the client's SharePoint or Power Automate yet — the site URL is still a `REPLACE-ME` placeholder |

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
| **`fct_QcSubmittal`** | **2,245** | live, from the production Procore tenant |
| **`fct_QcPunch`** | **1,469** | live |
| **`fct_QcNcr`** | **850** | live, from Procore Observations. **459 still resolve to no trade** — see the trade-vocabulary gotcha above |
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

Related and still open: **`cd_06_land_manual` is not in `CD_Master_Pipeline`.** The nightly run
rebuilds silver and gold without refreshing manual bronze first. Harmless while every `man_*`
is empty, and a real staleness bug the day somebody starts entering data — it should join the
DAG ahead of `Bronze To Silver` before the SharePoint lists go live.

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
