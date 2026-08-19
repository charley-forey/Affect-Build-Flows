# charley-dev

A complete, self-contained data solution for Affect Group's Monthly Progress Report, built
inside the Fabric workspace **Build** under the folder `charley-dev`
(`25dd1e34-bd57-43ca-aa29-c8fd33013101`).

It has its own bronze → silver → gold lakehouses, its own ingestion, its own semantic model
and reports. It does not depend on, and never writes to, anything in the existing workspace.

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

Rebecca's reporting keeps running untouched while this is built alongside it.

## Layout

```
00-platform/       standards + shared library (secrets, merge, DQ, watermarks)
01-ingestion/      Procore / Sage / Outbuild / SharePoint -> CD_Bronze
02-transformation/ bronze -> silver -> gold, as ordered .sql; seed/ holds the PQP
                   (Project Quality Plan) seed data extracted from the client's QA/QC
                   tracker - in progress
03-lakehouses/     the three lakehouse definitions
04-semantic_models/ Affect Project Report (DirectLake over gold); a second PQP model is
                   in progress
05-reports/        Monthly Progress Report
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

The eight notebooks that exist in the workspace, in the order they run:

```
01  cd_01_extract_procore       Procore REST -> landing files   (blocked: Key Vault role)
    cd_05_land_to_bronze        landing files -> CD_Bronze      (no credential needed)
    cd_06_land_manual           Files/_manual/*.csv -> bronze man_*
    CD_Sage_Ingest (dataflow)   Sage 100 via gateway -> CD_Bronze (deployed, inert)
02  cd_10_bronze_to_silver
    cd_20_seed_gold             seed dimensions; asserts its own row counts
    cd_30_build_gold            builds the star schema; verifies it
    cd_40_dq_checks             <- fails the run rather than publishing bad numbers
04  semantic model refresh

    cd_90_query                 ad-hoc scratchpad, not part of the DAG
```

**`06-orchestration/CD_Master_Pipeline` exists and runs this.** It is deployed, has 5
activities, and its last green run was 2026-08-02 22:06. `cd_01_extract_procore` is
deliberately **out** of the DAG until it can authenticate — leaving it in would mark the
run Failed every night, which is how an alert stops meaning anything. `cd_05_land_to_bronze`
takes its place in the pipeline and needs no credential.

Everything in `02-transformation/` runs as ordered `.sql` inside `cd_20_seed_gold` and
`cd_30_build_gold`; there is no separate `silver_to_gold` notebook.

## Verify without Fabric

Every transform is provable offline — no capacity spend, no API quota:

```bash
python foundation/charley-dev/_local/tests/test_seeds.py
python foundation/charley-dev/_local/tests/test_extract.py
python foundation/charley-dev/_local/run_local.py
```

## Secrets

Nothing goes in a notebook cell. `00-platform/lib/fabric_common.py::get_secret()` reads Key
Vault inside Fabric and environment variables locally — the same contract as
`foundation/01-ingestion/Procore_APICalls/procore_auth.ipynb`.

| Secret | Vault URL variable |
|---|---|
| `PROCORE_CLIENT_ID`, `PROCORE_CLIENT_SECRET`, `PROCORE_COMPANY_ID` | `PROCORE_KEYVAULT_URL` |
| `OUTBUILD_API_TOKEN` | `OUTBUILD_KEYVAULT_URL` |

The vault exists as of 2026-08-19 — `OneLake`, `https://onelake.vault.azure.net/` — but
holds nothing yet: it is RBAC-mode and `cforey-c@affect-group.com` has only Contributor on
the resource group, which cannot read or write secrets. One role assignment ("Key Vault
Secrets Officer" on `OneLake`) closes it. Until then extraction runs locally against
environment variables and lands files. See
[`_docs/build-status.md`](_docs/build-status.md).

## Extending it

Adding a Procore endpoint is a YAML entry in `01-ingestion/Procore/config/endpoints.yml`,
not a new notebook. Auth, pagination, the v2.0 header rule, retry and watermarking are
implemented once in the shared extractor. That is the pattern worth learning — it is why
this tree has one extractor instead of twenty-five near-identical notebooks.
