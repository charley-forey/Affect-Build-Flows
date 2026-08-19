# Fabric "Build" Workspace — Backup

Read-only export of the Microsoft Fabric workspace **Build**
(`1f7caed6-f88a-4e52-bc83-9a498a165301`), taken 2026-08-01.

Nothing in Fabric was modified. Folder layout mirrors the workspace; see
`_manifest.json` for the full item list, item IDs, and the Fabric-folder →
local-folder mapping.

## What's here — 55 items, 228 files

| Type | Count | Format on disk |
|---|---|---|
| Notebook | 22 | `<name>.ipynb` (outputs kept, except those holding tokens — see Credentials) |
| Dataflow Gen2 | 18 | `<name>.Dataflow/` → `mashup.pq`, `queryMetadata.json`, `.platform` |
| Semantic model | 4 | `<name>.SemanticModel/` → TMDL (`definition/tables/*.tmdl`) |
| Report | 4 | `<name>.Report/` → `definition.pbir`, `report.json`, static resources |
| Lakehouse | 3 | schema inventory only (see below) |
| SQL endpoint | 3 | metadata only (`_manifest.json`) |
| Warehouse | 1 | metadata only (`_manifest.json`) |

Folder layout:

```
01-ingestion/          Procore_APICalls/{Dimensions,Financial_Facts,Testing}, Outbuild_APICalls, Sage, Ramp_APICalls
02 transformation/     Procore/{Dimension,Financial Facts}, Outbuild
03-lakehouses/         Bronze_Lakehouse, Silver_Lakehouse schema inventories
04-semantic_models/    3 models
05-reports/            4 reports
_workspace-root/       items sitting outside any Fabric folder
charley-dev/           empty in Fabric when this backup was taken (2026-08-01)
```

> **`charley-dev` is no longer empty.** It now holds **20 items** — three lakehouses and
> their SQL endpoints, eight notebooks, a pipeline, a dataflow, two semantic models and two
> reports — all created after this backup was taken. They are **not** in the counts above,
> which are a snapshot of the pre-existing workspace. See
> [`charley-dev/README.md`](charley-dev/README.md) and
> [`charley-dev/_docs/build-status.md`](charley-dev/_docs/build-status.md); the backup tree
> is deliberately not re-taken, because its job is to record what existed *before*.

Local folder names keep the pre-existing spelling (`01-ingestion`,
`02 transformation`, `Financial_Facts`) rather than Fabric's
(`01- Ingestion`, `02- Transformation`, `Financial Facts`). `_manifest.json`
records both.

## Credentials

**No credential belongs in this tree.** The original Fabric export contained live
secrets; they were removed on 2026-08-01 before anything was committed:

- Procore `client_id` / `client_secret`, previously hardcoded in
  `01-ingestion/Procore_APICalls/procore_auth.ipynb`
- An Outbuild `superadmin` bearer token with no expiry claim, hardcoded in both
  `01-ingestion/Outbuild_APICalls/*.ipynb`
- 18 saved cell outputs holding Procore access tokens

Notebooks now read secrets through a `get_secret()` helper that mirrors
`src/procore/procore_extract.py` — Key Vault inside Fabric, environment variable
locally:

| Secret name | Vault URL variable | Used by |
|---|---|---|
| `PROCORE_CLIENT_ID`, `PROCORE_CLIENT_SECRET` | `PROCORE_KEYVAULT_URL` | `procore_auth.ipynb` |
| `OUTBUILD_API_TOKEN` | `OUTBUILD_KEYVAULT_URL` | `Outbuild_Test.ipynb`, `outbuild_activities_variance.ipynb` |

`procore_auth.ipynb` is the only notebook that holds Procore credentials — the other
17 obtain a token via `mssparkutils.notebook.run("procore_auth")`.

### Re-taking this backup

A fresh Fabric export re-embeds live tokens in notebook outputs. Run the scrubber
before committing:

```
python foundation/scrub-secrets.py
```

It rewrites credential literals to `get_secret()` calls, drops any output containing a
JWT, and is idempotent — a clean tree reports zero changes.

## Known gaps

- **Lakehouse data is not backed up.** Only table/column schemas and row counts,
  in `03-lakehouses/*.Lakehouse.schema.json` — Bronze: 17 tables / 503 columns /
  29,307 rows; Silver: 32 tables / 427 columns / 29,917 rows (counts as of
  2026-08-01, `dbo` only). Both lakehouses are schema-enabled, so Fabric's
  list-tables API rejects them; schemas were read from `INFORMATION_SCHEMA` on
  the SQL endpoint instead.
- **Dataflow/report data source credentials** are not exportable via the API —
  connections must be re-bound by hand on any restore.
- `Ramp_APICalls` was empty in Fabric, not missed. `charley-dev` was empty when this backup
  was taken and is not any more — see the note above.

## Re-running

`fabric_backup.py` (Fabric REST API, `az` CLI auth) — overwrites in place.
