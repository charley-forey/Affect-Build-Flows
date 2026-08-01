# Build status

Where charley-dev actually is. Updated as phases land — the roadmap lives in the approved
plan; this is what exists on disk and what has been verified.

## Verified about the environment (2026-08-01)

Checked directly against the Fabric REST API with the `az` token, not assumed:

| Check | Result |
|---|---|
| `az` login | Live — `cforey-c@affect-group.com` (Affect tenant) |
| Workspace `Build` | `1f7caed6-f88a-4e52-bc83-9a498a165301`, on capacity |
| Folder `charley-dev` | `25dd1e34-bd57-43ca-aa29-c8fd33013101` — exists, **0 items** |
| `Bronze_Lakehouse` | `4256b1ed-3884-4e26-96b5-aac4d8e6281f`, schema-enabled (`dbo`) |
| `Silver_Lakehouse` | `2e05dca7-ff80-4646-b711-6681dd4993e1` |
| SQL endpoint | `lmrkfmsojpwefossy7q4fxvfqa-22xhyh4k7bje5pedtjeyufstae.datawarehouse.fabric.microsoft.com` |

> **`dashboard.md` lists "Fabric workspace access provisioned" as an open blocker. It is
> not.** That should be ticked, and the Phase 0 plan re-read in that light — several items
> were sequenced behind it.

## Built and verified

| Area | What exists | Verified by |
|---|---|---|
| Platform library | `merge_delta` (idempotent Delta MERGE), watermarks, DQ expectations, parent-scope resolution | 4 self-checks |
| Procore registry | 36 endpoints, every path cited to the cheatsheet; 7 incremental | 7 compatibility checks |
| Gold seeds | `dim_Date`, `dim_Owner`, `dim_ActivityCategory`, `dim_ScorecardWeight`, `dim_ScorecardBand` (+ `dim_Trade`/`dim_Status` reused from `src/procore/sql`) | 33 assertions |
| Ingestion notebook | `cd_01_extract_procore.ipynb` — generated, compiles, no stored outputs | generator asserts |
| Lakehouses | `CD_Bronze` / `CD_Silver` / `CD_Gold` `.platform` definitions | JSON validated |
| D1 deliverable | `_docs/endpoint-inventory.md`, generated from the registry | regenerates clean |

Run everything: `python foundation/charley-dev/_local/run_tests.py` → **6 suites, 40 checks.**

The seed assertions are mutation-tested: five deliberate regressions (unsummed weights,
integer schedule bands, a re-opened band gap, an untrimmed trade name, a missing calendar
day) are each caught. A check that cannot fail is decoration.

## Defects fixed so far, and how

| Excel defect | Fix | Where |
|---|---|---|
| #1a Schedule Performance always scores 3/3 | Bands are fractions (0.05 / 0.10), not integers | `06_dim_scorecardband.sql` |
| #1b Completion Variance always scores 0 | 0 days now falls in the 3-point band | `06_dim_scorecardband.sql` |
| #4 Three different month anchors | One contiguous `dim_Date`, 2,922 days, no gaps | `00_dim_date.sql` |
| #5 `TODAY()` makes reports non-reproducible | `MonthOffset` relative to a real calendar | `00_dim_date.sql` |
| #9 Twelve trade names carry trailing whitespace | Seeded pre-trimmed, asserted | `src/procore/sql/20_gold_dim_trade.sql` |
| Full-reload ingestion | `merge_delta` upserts on the natural key | `fabric_common.py` |
| Hard-coded credentials | `get_secret()` — Key Vault in Fabric, env var locally | `fabric_common.py` |

### Two new findings

Both surfaced while seeding the scorecard, neither previously recorded:

1. **The Observations bands leave the value 5 unscored** — the workbook reads `< 5`,
   `6–10`, `>= 11`.
2. **The Daily Reports bands leave the value 2 unscored** — `< 2`, `3–4`, `>= 5`.

Closed here so the bands tile the number line with no hole, and asserted. Worth confirming
Affect intended `<= 5` and `<= 2`.

## Not built yet

Stated plainly so nobody plans around something that does not exist:

| Area | Status |
|---|---|
| Silver transforms (`cd_10_bronze_to_silver`) | Not started |
| Fact tables — `fct_RfiSubmittal` onward | Not started (`src/procore/sql/30_gold_fct_rfisubmittal.sql` is the slice-1 prototype to adapt) |
| Sage dataflow (`CD_Sage_Ingest`) | Not started — needs the on-prem gateway confirmed |
| Outbuild + SharePoint ingestion | Not started |
| Semantic model TMDL | Not started |
| Reports (Monthly Progress, Vendor & Insurance) | Not started |
| Orchestration pipeline | Not started |

## Live in Fabric

Workspace `Build`, folder `charley-dev`. **62 items in the workspace; nothing outside
`charley-dev` touched.**

| Item | Type | Note |
|---|---|---|
| `CD_Bronze_Lakehouse` | Lakehouse | schema-enabled (`dbo`) |
| `CD_Silver_Lakehouse` | Lakehouse | schema-enabled (`dbo`) |
| `CD_Gold_Lakehouse` | Lakehouse | schema-enabled (`dbo`) — holds the 7 seeded dimensions |
| `cd_20_seed_gold` | Notebook | generated from the `.sql`, asserts its own row counts |

Deploy and verify:

```bash
python foundation/charley-dev/_local/deploy.py --verify        # items + schema check
python foundation/charley-dev/_local/deploy_seeds.py --apply   # rebuild + rerun the seeds
```

Both are idempotent, dry-run by default, and refuse to write outside the `charley-dev`
folder.

**The seed run verifies itself.** A notebook that prints "0 rows" still reports
Completed, so the final cell asserts the exact row counts the offline suite checked, plus
the weights summing to 1.00. Proven by injecting a wrong expected count and confirming the
run fails — so `Completed` means the tables exist at the right size, not merely that the
SQL parsed.

### Found only by running it in Fabric

Exactly the class of problem the plan said offline testing could not cover:

1. **Bare `VARCHAR` is invalid in Spark** — it wants `STRING`. 36 casts affected. DuckDB
   accepts `STRING` too, so one spelling now serves both engines.
2. **Long-running-operation `Location` headers are absolute** and point at a different
   host (a regional `wabi-*` redirect); they must be followed as given.
3. **`enableSchemas` is creation-only** — the first three lakehouses came out without
   schemas and had to be dropped and recreated.
4. **Deleting an item does not release its name** — Fabric returns a retriable 409 for
   some minutes, so `deploy.py` retries on it.

## First-run checks, once anything is pushed to Fabric

The offline suite verifies logic. These need a live tenant and cannot be done here:

1. **Spark dialect.** The `.sql` runs through DuckDB with two macros; Spark edge cases
   surface on first execution.
2. **Live Procore field names.** Paths are verified against the cheatsheet; the JSON field
   names inside each payload have never been checked against Affect's tenant.
3. **Row-count parity** against the existing lakehouses (Bronze 29,307 / Silver 29,917 as
   of 2026-08-01) for the 13 endpoints that overlap. A gap means one of the two
   extractions is wrong — either is worth knowing.
4. **Isolation gate.** Re-run `foundation/fabric_backup.py` to a scratch directory and
   diff. Expect zero changes outside `charley-dev/`.

## Environment gaps to close

- `pyodbc` + Microsoft ODBC Driver 18 — needed for local SQL-endpoint verification.
- **Fabric MCP server is healthy but its tools bind at session start.**
  `claude mcp list` reports `fabric: ✔ Connected`, and the server runs fine
  (`uvx --from ms-fabric-mcp-server[sql] ms-fabric-mcp-server --help` works). A session
  that starts *before* it finishes connecting never gets the tool schemas — restart
  Claude Code and the ~57 tools appear. Nothing is wrong with the `az` login.

  Worth knowing regardless: the REST path in `deploy.py` is the better mechanism for
  *creating* items, because it is committed, idempotent, reviewable in a diff, and
  refuses to write outside `charley-dev`. The MCP tools are more useful for
  *exploration* — `execute_sql_query` against the SQL endpoint, `execute_dax_query`
  against a model — which is exactly what the reconciliation gate will need.
