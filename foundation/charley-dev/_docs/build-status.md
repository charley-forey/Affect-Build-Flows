# Build status

What exists, what is verified, and what is not built yet.

## Live in Fabric

Workspace `Build`, folder `charley-dev` (`25dd1e34-…`). **65 items in the workspace;
nothing outside `charley-dev` has been touched.**

| Item | Type | Contents |
|---|---|---|
| `CD_Bronze_Lakehouse` | Lakehouse | schema-enabled, awaiting Procore credentials |
| `CD_Silver_Lakehouse` | Lakehouse | schema-enabled, awaiting our own ingestion |
| `CD_Gold_Lakehouse` | Lakehouse | **16 tables, populated with real data** |
| `cd_20_seed_gold` | Notebook | 7 seed dimensions; asserts its own row counts |
| `cd_30_build_gold` | Notebook | 9 dimensions/facts + integrity checks; publishes the schema |
| `Affect Project Report` | SemanticModel | Direct Lake, 17 tables, 30 measures, 14 relationships |
| `Monthly Progress Report` | Report | 4 pages, 42 visuals |

### The gold model, with real data

| Table | Rows | | Table | Rows |
|---|---|---|---|---|
| `dim_Date` | 7,670 | | `fct_BudgetLine` | 404 |
| `dim_Project` | 17 | | `fct_ChangeOrder` | 1,812 |
| `dim_Vendor` | 126 | | `fct_Invoice` | 117 |
| `dim_CostCode` | 4,837 | | `fct_RfiSubmittal` | 2,242 |
| `dim_Trade` | 29 | | `fct_Milestone` | 52 |
| `dim_Status` | 32 | | `fct_FinancialPeriod` | 128 |
| `dim_Owner` | 10 | | `dim_ScorecardWeight` | 9 |
| `dim_ActivityCategory` | 28 | | `dim_ScorecardBand` | 27 |

Source is the existing `Silver_Lakehouse`, **read-only**, so the model could be validated
against real numbers before Procore credentials land. When our own ingestion populates
`CD_Silver`, only `sql/silver/00_source_views.sql` changes — no gold file moves.

## How to run it

```bash
python foundation/charley-dev/_local/run_tests.py         # 7 suites, offline, no Fabric
python foundation/charley-dev/_local/deploy.py --verify   # items + schema check
python foundation/charley-dev/_local/deploy_seeds.py --apply
python foundation/charley-dev/_local/deploy_gold.py --apply
python foundation/charley-dev/_local/deploy_model.py --apply
python foundation/charley-dev/_local/deploy_report.py --apply
python foundation/charley-dev/_local/validate_model.py    # reframe + DAX assertions
python foundation/charley-dev/_local/deploy_gold.py --diag # last run's diagnostics
```

Every deploy script is idempotent, dry-run by default, and refuses to write outside the
`charley-dev` folder.

## Verification

**Offline — 7 suites, no network, no Fabric.** The `.sql` runs through DuckDB via three
macros, so the tests exercise the *production* Spark SQL rather than a re-implementation.
33 seed assertions, 29 gold assertions (two reproducing the reconciliation gate exactly:
Current Contract 9,116,960.48 and Contract Growth 3.60%), 7 extractor-contract checks, and
4 library self-checks. Mutation-tested: five deliberate regressions are each caught.

**In Fabric — the runs assert themselves.** A notebook that builds empty tables still
reports Completed, so both notebooks check their own output and fail the run otherwise.
Currently: expected row counts, zero orphans, every `MonthStart` resolving to `dim_Date`,
no sentinel dates surviving. Proven by injecting a wrong expected count and confirming the
run fails.

**Live DAX — 6 checks.** `validate_model.py` reframes the model and queries it: all tables
readable at expected counts, all 26 queried measures evaluate, `[Budget Variance]` equals
Budget − Spent, `[Total Billed]` reconciles to Paid + Outstanding, and `DATEADD` over
`dim_Date` works — the real proof that `dim_Date` replaced the workbook's `AU4`
`INDEX/MATCH` mechanic.

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

| Area | Status |
|---|---|
| Procore ingestion **run** | Notebook and 36-endpoint registry are built and tested; needs `PROCORE_CLIENT_ID`/`SECRET` in Key Vault to execute |
| Silver transforms (`cd_10_bronze_to_silver`) | Not needed until our own bronze is populated |
| RFIs | In the registry, never ingested — no RFI data exists anywhere in the warehouse yet |
| Sage dataflow (`CD_Sage_Ingest`) | Needs the on-prem gateway confirmed |
| Outbuild + SharePoint ingestion | Not started; Outbuild data reached gold via the existing Silver |
| `man_*` manual tables | Blocked on the SharePoint decision (~40% of the report) |
| Orchestration pipeline | Not started; notebooks run in documented order |
| Scorecard measures | Bands and weights are seeded; the 9 category measures are not written |

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
