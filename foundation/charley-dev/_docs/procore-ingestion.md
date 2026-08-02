# Procore ingestion

Deployed and running in Fabric as `cd_01_extract_procore`, bound to `CD_Bronze_Lakehouse`.
It gets as far as authentication and stops there: **no Procore credentials exist in the
environment or in Key Vault.** That is the only thing missing.

## Verified working, in Fabric

The run reached `load_settings`, which means everything before it succeeded:

| Step | Status |
|---|---|
| Shared library loads from `Files/lib/` | ok — 4 modules, 36,831 bytes |
| Registry loads from `Files/config/endpoints.yml` | ok |
| Registry **validates** — no duplicate names or tables, no missing parent, no cycle | ok |
| Resolution order computed — parents before children | ok |
| `load_settings()` — read the credentials | **fails** |

```
RuntimeError: Secret 'PROCORE_CLIENT_ID' not found. Set it in Key Vault (and
PROCORE_KEYVAULT_URL) or as an environment variable.
```

Captured in `Files/_diag/ingest_run.json`, which also records which secrets were visible:
all five absent. Retrieve it with:

```bash
python foundation/charley-dev/_local/deploy_ingestion.py   # dry run shows the same locally
```

## What is needed

Three values, from a Procore **Data Connector App** using the **client-credentials**
grant:

| Secret | Notes |
|---|---|
| `PROCORE_CLIENT_ID` | |
| `PROCORE_CLIENT_SECRET` | |
| `PROCORE_COMPANY_ID` | The existing `procore_auth.ipynb` hardcodes `562949953444705` — an org identifier, not a credential |
| `PROCORE_BASE_URL` | `https://api.procore.com` for production; a sandbox host while testing |

**Client credentials, not a user token.** A user-based (`authorization_code`) token expires
and breaks the pipeline at the worst moment — flagged in
`resources/procore/endpoints-cheatsheet.md:196-200` as the most common Procore ETL failure
mode. Rebecca's existing notebooks should be checked for which grant they use.

## Two ways to supply them

**Key Vault (production).** Put the three secrets in a vault the Fabric workspace identity
can read, and set `PROCORE_KEYVAULT_URL` on the Spark environment. `get_secret()` resolves
Key Vault first, so nothing else changes. This is the mechanism the Jul 23 warehouse review
asked for — *"credentials are hard-coded in a notebook cell. First fix."*

**Environment variables (local testing only).** Copy
`src/procore/config/settings.example.env` to `.env` at the repo root and fill it in;
`.gitignore:30` already excludes it. This runs the extractor locally against fixtures or a
sandbox without touching Fabric.

Nothing in this repo reads or stores a credential. `deploy_ingestion.py` only reports
whether they are reachable.

## Then

```bash
python foundation/charley-dev/_local/deploy_ingestion.py --run
```

The notebook pulls **active projects only** — the existing notebooks loop every project on
every run, and most are closed (Jul 23 review). It then walks the 36 endpoints in
dependency order, merging each into `cd_bronze_procore_*` on its natural key.

Re-running is safe by construction: the load is a Delta `MERGE`, not an append, which is
also what makes the deliberate one-hour watermark overlap harmless.

## What it unblocks

23 of the 36 endpoints have no equivalent anywhere in the current warehouse
(`_docs/endpoint-inventory.md`). The ones that change the report most:

| Endpoint | Unblocks |
|---|---|
| `rfis` | The missing half of `fct_RfiSubmittal` — no RFI data exists anywhere today |
| `observations` | `man_QualityMonthly` becomes automatic; fixes Excel defect #2 |
| `punch_items` | Quality metrics |
| `incidents` | `man_SafetyMonthly.RecordableIncidents` → scorecard +0.14 weight |
| `daily_log_headers` | `man_DailyLogCompliance` → scorecard +0.02 weight |
| `manpower_daily_totals` | `SCHEDULE!Table14`, without the workbook's 5-subcontractor cap |
| `change_order_requests` | Sharpens age-of-oldest-unapproved-CO |

Between them these take `[Scorecard Coverage %]` from 35% toward 88% without anybody
typing a number into a spreadsheet.

## Sequencing note

Gold currently reads the **existing** `Silver_Lakehouse`, read-only, which is how the model
was validated against real data before credentials landed. Once this ingestion populates
`CD_Bronze`, the path becomes:

```
cd_01_extract_procore  ->  CD_Bronze
cd_10_bronze_to_silver ->  CD_Silver     (not yet written - needs bronze to exist)
cd_30_build_gold       ->  CD_Gold       (only sql/silver/00_source_views.sql changes)
```

No gold file, measure or report visual moves. That was the point of isolating source
naming in the `sv_*` views.
