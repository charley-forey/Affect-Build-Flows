# Naming standards

One page. Follow it and the DAX, the SQL and the model agree without translation.

## Tables

| Prefix | Layer | Example |
|---|---|---|
| `cd_bronze_` | Raw payload + audit columns | `cd_bronze_procore_rfis` |
| `cd_silver_` | Typed, trimmed, validated | `cd_silver_procore_rfis` |
| `dim_` | Gold dimension | `dim_Project` |
| `fct_` | Gold fact | `fct_RfiSubmittal` |
| `man_` | Gold, manually sourced | `man_Risks` |
| `cd_meta_` | Pipeline state | `cd_meta_watermark`, `cd_meta_run_log` |
| `cd_dq_` | Data quality output | `cd_dq_results`, `cd_dq_rejects` |

`cd_` marks "built by charley-dev" so a table's origin is obvious in a lakehouse listing that
also contains Rebecca's. Gold tables drop the prefix because their names are the semantic
model's contract — the DAX in `powerbi/measures.dax` reads `fct_SafetyMonthly[HoursWorked]`
by name, so the table must be called exactly that.

## Columns

| Layer | Convention | Example |
|---|---|---|
| bronze | `snake_case`, plus `_`-prefixed audit columns | `payload`, `_ingested_at` |
| silver | `snake_case`, source names preserved | `project_id`, `updated_at` |
| gold | `PascalCase`, matching `powerbi/semantic-model.md` exactly | `ProjectKey`, `HoursWorked` |

The case change at the silver→gold boundary is deliberate: it makes it visually obvious
whether you are looking at source-shaped data or model-shaped data.

## Audit columns (every bronze and silver table)

| Column | Meaning |
|---|---|
| `_ingested_at` | UTC timestamp the row landed |
| `_source_endpoint` | Logical endpoint name from `endpoints.yml` |
| `_batch_id` | Run identifier — ties a row to a `cd_meta_run_log` entry |
| `_row_hash` | Hash of the source payload; drives change detection |

These exist so "why did this number change?" is answerable. Today it is not.

## Keys

- `*Key` — surrogate, integer, generated in gold. Joined on.
- `*Id` — the source system's own identifier, carried through. Never joined on across systems.
- `*Number` — human-readable business identifier (`ProjectNumber`, `InvoiceNumber`).

`ProcoreProjectId` and `SageJobNumber` both live on `dim_Project` as attributes; facts join
on `ProjectKey` only. This is what stops the two systems' identifiers leaking into the model.

## Fabric items

| Item | Pattern | Example |
|---|---|---|
| Lakehouse | `CD_<Layer>_Lakehouse` | `CD_Gold_Lakehouse` |
| Notebook | `cd_<nn>_<verb>_<subject>` | `cd_20_silver_to_gold` |
| Dataflow | `CD_<Source>_Ingest` | `CD_Sage_Ingest` |
| Pipeline | `CD_<Purpose>_Pipeline` | `CD_Master_Pipeline` |
| Semantic model | Business name, no prefix | `Affect Project Report` |
| Report | Business name, no prefix | `Monthly Progress Report` |

Numbered notebook prefixes give the run order at a glance and sort correctly in the Fabric
item list. Semantic models and reports drop the prefix because end users see those names.

## SQL files

`sql/<layer>/<nn>_<table>.sql`, executed in filename order. The number band carries meaning:

| Band | Contains |
|---|---|
| `0*` | Seeds — static reference data |
| `1*` | Dimensions |
| `2*`–`3*` | Facts |
| `4*` | Manual (`man_*`) |
| `9*` | Data quality |

## Two things that are not negotiable

1. **`TRIM()` every text value on the way in.** Twelve of the workbook's trade values carry
   trailing whitespace today; `"Metals  "` never equals `"Metals"` in a join.
2. **Reject unmatched values loudly.** An unmatched status goes to `cd_dq_rejects` with a
   reason. It does not silently disappear — that is precisely how the Excel's defects #2 and
   #6 survived unnoticed.
