# Procore → Fabric Lakehouse

> **Status — superseded but deliberately kept (2026-08-19).** The reference slice, written
> 26 Jul 2026. Its extractor, endpoint registry and layered SQL are the pattern that
> `foundation/charley-dev/01-ingestion/Procore/` now runs at full scale (44 registered
> endpoints against this slice's four). Kept as the teaching artifact: one source, one fact
> table, runnable offline with `python src/procore/run_local.py`. Everything below still
> describes this folder accurately; it is not a description of the production pipeline.

Slice 1: **RFIs & submittals, end to end.** Four endpoints, one gold fact table, the
figure behind the workbook's only chart. Chosen as the first build because it is the
smallest thing that proves the whole pattern.

## In this folder

| File | What it is |
|---|---|
| `procore_extract.py` | The engine. Auth, pagination, retry, the v2.0 header rule, watermarking. Pure Python — no Spark, no Fabric imports. Imported by both the notebook and the local runner so it exists **once**. |
| `config/endpoints.yml` | The endpoint registry. The only file that grows when we add an endpoint. |
| `config/settings.example.env` | Copy to `.env` at the repo root. Never commit the real one. |
| `notebooks/01_extract_bronze.py` | Fabric notebook — pulls every registered endpoint into bronze via a Delta merge. |
| `notebooks/02_transform.py` | Fabric notebook — runs every `.sql` file in order. About five lines. |
| `sql/*.sql` | The transform logic, in filename order. Spark SQL. |
| `run_local.py` | Runs the whole pipeline locally on DuckDB and renders `preview.html`. |
| `preview/template.html` | The preview page; `run_local.py` injects the data each run so it cannot go stale. |
| `tests/test_extract.py` | 21 checks on the extractor. Fake HTTP session, no network. |
| `tests/test_pipeline.py` | 13 checks on the SQL, run against the real files. |
| `tests/fixtures/*.json` | Sample API responses. **Hand-built from Procore's documented shapes, not captured from a live tenant** — replace with `run_local.py --capture`. |

## Why one extractor instead of one notebook per entity

The four defects recorded in
[`../../deliverables/02-procore-etl-validation.md`](../../deliverables/02-procore-etl-validation.md)
are not four bugs. They are one bug duplicated per notebook: when auth, pagination and
load strategy are copy-pasted N times, every fix has to be applied N times, and the
credential has N places to hide.

| Defect | Where it is fixed now |
|---|---|
| Credentials hard-coded in a cell | `get_secret()` — Key Vault in Fabric, env vars locally. One function produces a credential. |
| Full table reload every run | `merge_bronze()` merges on the natural key; `watermark_params()` limits the pull. Re-running does not double rows — asserted by `test_rerun_is_idempotent`. |
| Loops every project regardless of status | `iter_active_projects()` filters to active. |
| Financial-only endpoint coverage | Adding an endpoint is a YAML entry. |
| Transforms dropping vendor / cost-code IDs | Bronze stores the **unparsed** payload. It cannot drop a column it never parsed. |

## Adding an endpoint

Append to `config/endpoints.yml`:

```yaml
- name: commitment_contracts
  path: /rest/v2.0/companies/{company_id}/projects/{project_id}/commitment_contracts
  scope: project
  api_version: "2.0"        # >= 2.0 automatically gets the Procore-Company-Id header
  bronze_table: bronze_procore_commitment_contracts
  incremental: filters[updated_at]
```

That is the whole change for bronze. Silver/gold need a `.sql` file only when the data
has to reach the semantic model.

## Two things the client still has to define

Both are isolated to a single expression so confirming them is a one-line edit. Neither
is a gap in the pipeline — they are genuinely undefined in the source workbook:

- **"Critical"** (`sql/30_gold_fct_rfisubmittal.sql`) — currently Procore priority
  High/Urgent. The workbook never defines the word (open question #5), and it drives
  every number on the SUBMITTALS & RFI tab.
- **Trade mapping** (same file) — RFIs carry a cost code, submittals a spec section,
  neither of which maps onto Affect's 29 trades. Unmatched items land on
  `TradeKey = 0` (*Unassigned*) and are logged as warnings, so the gap shows up as a
  labelled bar rather than a quietly missing one.

## Also worth knowing

`endpoints.yml` marks RFIs and submittals as **full reload**, not incremental. The
endpoint cheatsheet lists `filters[created_at]` for both but not `filters[updated_at]`,
and incrementing on creation date would miss the status changes that "open critical RFI"
depends on. The merge keeps it idempotent regardless. Worth re-checking against the live
API — the filter list was read from the OpenAPI spec, which may be incomplete.
