# charley-dev

**Current validation work:** see [_docs/validation-and-development-plan.md](_docs/validation-and-development-plan.md)
(2026-09-14 status at the top) and [_docs/operations-runbook.md](_docs/operations-runbook.md).
Production was promoted to a validated build on 2026-09-14; release2 fixes are validated
but not yet promoted. Passing offline checks is not certification of the live report.

A complete, self-contained data solution for Affect Group's Monthly Progress Report **and
Project Quality Plan**, built inside the Fabric workspace **Build** under the folder
`charley-dev` (`25dd1e34-bd57-43ca-aa29-c8fd33013101`). **20 items** as of 2026-08-19.

It has its own bronze → silver → gold lakehouses, its own ingestion, and **two semantic
models over one gold layer** with a report each. It does not depend on, and never writes to,
anything in the existing workspace.

## The isolation rule

**Everything outside `charley-dev/` is read-only.** This is not a convention, it is the
constraint the whole build is designed around:

1. Items are created only inside Fabric folder `25dd1e34-…`. No API call targets an existing
   item id.
2. Pipelines write only to `CD_Bronze_Lakehouse`, `CD_Silver_Lakehouse`, `CD_Gold_Lakehouse`.
3. Reads of `Bronze_Lakehouse` / `Silver_Lakehouse` are for comparison only (see
   `_local/tests/` parity checks) and go through the SQL endpoint, which is read-only.
4. Proof, not promise: re-run `foundation/fabric_backup.py` to a scratch directory and diff
   against `foundation/`. Expect zero changes outside `charley-dev/`.

Affect's existing reporting keeps running untouched while this is built alongside it.

## Layout

```
00-platform/       standards + shared library (secrets, merge, DQ, watermarks)
01-ingestion/      Procore / Sage / Outbuild / SharePoint -> CD_Bronze
02-transformation/ bronze -> silver -> gold, as ordered .sql; seed/ holds the PQP
                   (Project Quality Plan) seed data extracted from the client's QA/QC
                   tracker
03-lakehouses/     the three lakehouse definitions
04-semantic_models/ Affect Project Report (Model A) and Project Quality Plan (Model B),
                   both DirectLake over the SAME gold lakehouse - dim_Project and
                   dim_Date are conformed, not copied
05-reports/        Monthly Progress Report (12 pages) and Project Quality Plan (7 pages)
                   (PDF + page screenshots: ../../resources/power-bi/monthly-progress-report/)
06-orchestration/  the pipeline DAG + schedules
_local/            offline harness: fixtures, DuckDB runner, tests
_docs/             solution-guide.md first; assessment.md is the audit of what is live
```

Folder numbering mirrors `foundation/` so the workspace reads the same way.

## The layers

| Layer | Holds | Rule |
|---|---|---|
| `cd_bronze_*` | Raw API payload, unparsed, plus audit columns | Never transform here. Bronze cannot drop a column it never parsed, so a transform bug is a re-run, not a re-extract. |
| `cd_silver_*` | Typed, trimmed, validated | Rejected rows are logged with a reason, never dropped. |
| `dim_* / fct_* / man_*` | The star schema in `../../powerbi/semantic-model.md` | Column names match the semantic model exactly; the DAX reads them by name. |

## Run order

`06-orchestration/CD_Master_Pipeline` runs these stages serially, nightly (definition read
live 2026-09-14; details and reasons in
[`_docs/operations-runbook.md`](_docs/operations-runbook.md)):

```
    cd_05_land_to_bronze        landing files -> CD_Bronze (runs FIRST: the live pulls must overwrite a replayed batch)
    cd_20_seed_gold             seed dimensions; asserts its own row counts
    CD_Sage_Ingest (dataflow)   Sage via gateway -> CD_Bronze
    cd_06_land_manual           Files/_manual/*.csv -> bronze man_*  (17 tables)
    cd_02_extract_outbuild      Outbuild API -> bronze (the only milestone source)
    cd_01_extract_procore       Procore REST -> bronze (no retry: one attempt spends the hourly quota)
    cd_10_bronze_to_silver
    cd_30_build_gold            builds the star schema; verifies it
    cd_40_dq_checks             THE GATE: fails the run rather than publishing bad numbers
    cd_50_publish_models        refresh both models only after a passed gate
                                (in the repo on release2; NOT yet deployed - until then the
                                models frame gold as it is written)

    cd_90_query                 ad-hoc scratchpad, not part of the DAG
    cd_9x_validate_*            isolated candidate validation, not part of the DAG
```

Every dependency is Succeeded-only, so any upstream failure skips silver, gold and the gate
and the report stays on the last good build. The earlier notes that `cd_01_extract_procore`
and `cd_06_land_manual` were outside the DAG are obsolete: both have been in it since
2026-08-25, and the stages were serialised on 2026-09-13 after parallel starts starved the
Spark session pool.

Everything in `02-transformation/` runs as ordered `.sql` inside `cd_20_seed_gold` and
`cd_30_build_gold`; there is no separate `silver_to_gold` notebook.

**Deploy order matters:** seeds, manual, silver, gold, DQ, models, reports (full order in the
runbook). Gold reads `seed_ProjectCrosswalk` and `cd_silver_sage_vendors`, so seeds and silver
must precede it, and `_local/deploy_manual.py` must run before `_local/deploy_silver.py`. Silver parses the `cd_bronze_man_*` tables and `cd_06_land_manual`
is what creates them. Run silver first and it fails with
`System_Cancelled_Session_Statements_Failed` — which names no table and reads like a Spark
fault rather than a missing input.

## Verify without Fabric

Every transform is provable offline — no capacity spend, no API quota:

```bash
python foundation/charley-dev/_local/run_tests.py   # 19 suites (release2), no network, no Fabric
```

The `.sql` runs through DuckDB via compatibility macros, so the suites exercise the
*production* Spark SQL rather than a re-implementation.

## Secrets

Nothing goes in a notebook cell. `00-platform/lib/fabric_common.py::get_secret()` reads Key
Vault inside Fabric and environment variables locally.

The vault is **`AffectKeyVault`** — `https://affectkeyvault.vault.azure.net/`, resource group
`Affect_Data`, subscription `73932b34-3bb6-4a94-bd4b-4b7623d4f7d6`, tenant "Affect Build LLC"
`b2a2225b-4b4e-42ec-ba52-c7e1c2dea580`. The build account holds **Key Vault
Administrator** on the resource group, so reading and writing secrets needs no further grant.

Key Vault names cannot contain underscores, so the environment-variable name is never the
secret name. `fabric_common.kv_secret_name` owns the translation and `setup_keyvault.py`
imports it, so the write side and the read side cannot disagree:

| Environment variable | Key Vault secret | State |
|---|---|---|
| `PROCORE_CLIENT_ID` | `ProcoreClientID` | **live** |
| `PROCORE_CLIENT_SECRET` | `ProcoreClientSecret` | **live** |
| `PROCORE_COMPANY_ID` | `ProcoreCompanyID` | **live** |
| `OUTBUILD_API_TOKEN` | `OutbuildToken` | **live** |

The vault also holds five Sage/gateway credentials Affect's reporting lead added on 2026-08-22 (the
`FabricReader` SQL login, the connector service account and the gateway recovery
key). Nothing reads them, and they do **not** unblock `CD_Sage_Ingest` — see the runbook.

The vault URL is a default in code, not an environment variable to set. `AFFECT_KEYVAULT_URL`
overrides it. Inside Fabric `get_secret` **fails closed** — it will not silently fall back to
`os.environ` when the vault lookup does not produce the secret.

Until 2026-08-19 every document here named a different vault (`OneLake`, in subscription
`0bee26ab-…`) that this account cannot read at all. That vault holds nothing we depend on.
See [`_docs/keyvault-runbook.md`](_docs/keyvault-runbook.md) for the correction, the Procore
rotation runbook, and what Outbuild took to get live.

## Extending it

Adding a Procore endpoint is a YAML entry in `01-ingestion/Procore/config/endpoints.yml`,
not a new notebook. Auth, pagination, the v2.0 header rule, retry and watermarking are
implemented once in the shared extractor. That is the pattern worth learning — it is why
this tree has one extractor instead of twenty-five near-identical notebooks.

Adding a **subject area** follows the same rule. `_local/deploy_model_qc.py` and
`_local/deploy_report_qc.py` import `deploy_model` / `deploy_report` and override three
module-level lists (`MODEL_TABLES`, `RELATIONSHIPS`, `MEASURES`, and `PAGES`) rather than
copying 800 and 1,171 lines. Every generator function reads those globals at call time, so a
new model is three lists and a name — and the Direct Lake traps encoded in the original stay
encoded in exactly one place.

**One thing that will bite you:** `_local/deploy_gold.py` carries a hardcoded `tables` list
that drives both the empty-table guard and the schema publish to `gold_schema.json`. A gold
table missing from that file cannot be typed by `deploy_model.py`, so it **silently cannot
appear in any semantic model** — no error, anywhere. Add the table to the list.
