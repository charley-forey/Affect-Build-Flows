# src — pipeline code

> **Status — superseded but deliberately kept (2026-08-19).** Written 26 Jul 2026 as the
> first end-to-end slice: Procore RFIs and submittals, bronze → silver → gold, runnable on a
> laptop with no Fabric licence. Production has moved to `foundation/charley-dev/` — 44
> registered Procore endpoints, eight `cd_*` Fabric notebooks, a six-stage
> `CD_Master_Pipeline`, a gold layer publishing 53 table schemas, and two semantic models.
> This folder stays because it is the smallest complete example of that pattern and the only
> version you can run offline in one command. **Add new work to `foundation/charley-dev/`,
> not here.** Current truth: `foundation/charley-dev/_docs/solution-guide.md`.

Code that moves data into the Fabric Lakehouse. One folder per source system, as
[`dashboard.md`](../dashboard.md) sets out.

## In this folder

| Folder | What it is |
|---|---|
| [`procore/`](procore/) | Procore REST API → bronze → silver → gold. Slice 1 (RFIs & submittals) is complete and runnable. |

Sage 100 (D3) was to follow the same shape: a config-driven extractor, `.sql` transforms,
and a local runner, so there is one pattern to learn rather than one per source. It was not
built here — Sage ingestion ships as the `CD_Sage_Ingest` Dataflow Gen2 in
`foundation/charley-dev/`, because the on-prem SQL source needs a gateway-bound mashup.

## The layers

| Layer | Holds | Rule |
|---|---|---|
| `bronze` | The raw API payload, unparsed, plus `_ingested_at` and `_source_endpoint` | Never transform here. A transform bug becomes a re-run, not a re-extract — and bronze cannot drop a column it never parsed. |
| `silver` | Typed, trimmed, validated | Rejected rows are logged with a reason, never dropped. |
| `gold` | The `fct_*` / `dim_*` tables in [`../powerbi/semantic-model.md`](../powerbi/semantic-model.md) | Column names match the semantic model exactly; the DAX reads them by name. |

## Run it

```bash
pip install duckdb pyyaml requests
python src/procore/tests/test_extract.py     # extractor logic, no network
python src/procore/tests/test_pipeline.py    # the SQL, end to end
python src/procore/run_local.py              # full pipeline from fixtures
```

`run_local.py` writes `.local/gold/*.parquet` (gitignored) and `.local/preview.html`, a
standalone page rendering the result. Add `--live` once Procore sandbox credentials are in
a root `.env` — see [`procore/config/settings.example.env`](procore/config/settings.example.env).

## Two dialects, one set of SQL

The `.sql` files are written in **Spark SQL**, because Fabric is the production target.
`run_local.py` runs those same files through DuckDB with two compatibility macros
(`get_json_object`, `datediff`). So local runs verify the *logic* — joins, key
resolution, rejects, row counts — but not Spark dialect edge cases. Those get checked in
Fabric on first run.

## Getting it into Fabric

1. Upload `procore_extract.py`, `config/` and `sql/` to the Lakehouse under
   `Files/procore/`.
2. Import `notebooks/01_extract_bronze.py` and `notebooks/02_transform.py` as notebooks
   (they are plain Python in Fabric's notebook format).
3. Put `PROCORE_CLIENT_ID` / `PROCORE_CLIENT_SECRET` / `PROCORE_COMPANY_ID` in Key Vault
   and set `PROCORE_KEYVAULT_URL`. **Nothing goes in a notebook cell.**
4. Schedule `01` then `02` in a Data Pipeline.

## Confirming field names

The Procore JSON field names in the `.sql` files come from Procore's documented v1.0 RFI
and v1.1 submittal shapes, and the fixtures were hand-built to match — **neither has been
checked against a live tenant yet.** First thing to do with sandbox access:

```bash
python src/procore/run_local.py --capture   # overwrites fixtures with real responses
python src/procore/tests/test_pipeline.py   # counts will shift; the assertions show what
```

A field name that turns out wrong surfaces as a `missing_*` reject in the data-quality
log rather than as a silently empty column — which is the point of rejecting loudly.
