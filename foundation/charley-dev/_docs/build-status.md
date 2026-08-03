# Build status

What exists, what is verified, and what is not built yet.

**Every number on this page was read back out of Fabric on 2026-08-02**, not carried
forward from the last edit. Where a figure here disagrees with an older doc, this one is
the measured value — see [`assessment.md`](assessment.md) for how each was obtained.

## Live in Fabric

Workspace `Build`, folder `charley-dev` (`25dd1e34-…`). **Nothing outside `charley-dev` has
been touched** — `fabric_backup.py` diffed to a scratch directory is the acceptance gate, not
a promise.

| Item | Type | Contents |
|---|---|---|
| `CD_Bronze_Lakehouse` | Lakehouse | 40 tables, from Affect's **production** Procore tenant |
| `CD_Silver_Lakehouse` | Lakehouse | 15 typed tables, **14,791 rows, 0 rejects** |
| `CD_Gold_Lakehouse` | Lakehouse | 40 tables — dimensions, facts, crosswalks, bridges, `man_*` |
| `cd_01_extract_procore` | Notebook | deployed; blocked on Key Vault (see below) |
| `cd_05_land_to_bronze` | Notebook | merges landed NDJSON into bronze Delta, no credentials |
| `cd_06_land_manual` | Notebook | manual-input capture path |
| `cd_10_bronze_to_silver` | Notebook | runs clean against real bronze |
| `cd_20_seed_gold` | Notebook | seed dimensions; asserts its own row counts |
| `cd_30_build_gold` | Notebook | 20 gold files + integrity checks; publishes the schema |
| `cd_40_dq_checks` | Notebook | the DQ gate — 63 expectations |
| `CD_Master_Pipeline` | DataPipeline | 5 activities, the nightly DAG |
| `Affect Project Report` | SemanticModel | Direct Lake, **37 tables, 99 measures, 45 relationships** |
| `Monthly Progress Report` | Report | **12 pages, 180 visuals**, drill-through, 3 bookmarks — [screenshots of the 10 visible pages](../../../resources/power-bi/monthly-progress-report/) |

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
the deployed notebook and counting lakehouse GUIDs, because `deploy_gold.py` still defaults
to `--source existing`: **re-deploying without `--source cd` silently reverts the medallion
to the legacy warehouse.** That default is a live foot-gun, not a preference.

### Two blockers, both external

| Blocker | Effect | Owner |
|---|---|---|
| **No Azure subscription** on this tenant (`az account list` returns a tenant-level account only) | Key Vault cannot be created, so `cd_01_extract_procore` cannot hold a credential. Extraction runs locally instead and lands files; `cd_05_land_to_bronze` merges them in Fabric with no secret. A bridge, not the destination — `procore-ingestion.md` has the steps to retire it. | Affect |
| **`OUTBUILD_API_TOKEN` not issued** | Outbuild ingestion is built and verified but cannot run. Outbuild is the only milestone source anywhere. | Affect (via Outbuild CS) |

Plus three access items worth raising on the same call: Procore 403s on `punch_item_types`
and `schedule`, and the on-prem gateway binding for `CD_Sage_Ingest`.

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

The nine `man_*` tables are deployed and empty, pending the SharePoint decision.

**Three tables are invisible to the SQL analytics endpoint** — `bridge_vendorcostcode`,
`fct_vendorinsurance` and `meta_pipelinerun` do not appear in `INFORMATION_SCHEMA.TABLES`,
though all three hold data and serve the report correctly. Direct Lake reads the Delta
files and is unaffected; only T-SQL against the endpoint cannot see them. This is Fabric's
endpoint metadata sync lagging, not a build failure — but anyone verifying by SQL will
conclude the tables are missing, so check with DAX before believing it.

## How to run it

```bash
python foundation/charley-dev/_local/run_tests.py         # 12 suites, offline, no Fabric
python foundation/charley-dev/_local/deploy.py --verify   # items + schema check
python foundation/charley-dev/_local/deploy_seeds.py --apply
python foundation/charley-dev/_local/deploy_gold.py --source cd --apply   # NOT bare --apply
python foundation/charley-dev/_local/deploy_model.py --apply
python foundation/charley-dev/_local/deploy_report.py --apply
python foundation/charley-dev/_local/validate_model.py    # reframe + DAX assertions
python foundation/charley-dev/_local/deploy_gold.py --diag # last run's diagnostics
```

Every deploy script is idempotent, dry-run by default, and refuses to write outside the
`charley-dev` folder.

## Verification

**Offline — 12 suites, no network, no Fabric.** The `.sql` runs through DuckDB via three
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
still listed as not started. Corrected below.

| Area | Status |
|---|---|
| Procore ingestion **run inside Fabric** | Notebook and 42-endpoint registry built and tested; still needs `PROCORE_CLIENT_ID`/`SECRET` in Key Vault. Extraction runs **locally** and lands files; `cd_05_land_to_bronze` merges them. The nightly pipeline therefore re-processes whatever was last landed — **it does not call the Procore API.** |
| Sage dataflow (`CD_Sage_Ingest`) | Defined in the repo, **not deployed** to the workspace — needs the on-prem gateway confirmed |
| Manual dataflow (`CD_Manual_Ingest`) | Defined in the repo, **not deployed** to the workspace |
| Outbuild ingestion | Built and verified, cannot run — `OUTBUILD_API_TOKEN` not issued. Outbuild is the only milestone source, and 17 of 19 projects are missing from it |
| `man_*` manual tables | **Built and deployed** — 9 tables live in gold, currently empty pending the SharePoint decision |
| Orchestration pipeline | **Built and running** — `CD_Master_Pipeline`, 5 activities, last green run 2026-08-02 22:06 |
| Scorecard measures | **Written** — 9 category measures live; coverage 59%, 4 of 9 categories still unscored for want of source data |
| `Vendor & Insurance List` report | Named in `README.md`, never built. The insurance data reached the Monthly Progress Report instead |

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
