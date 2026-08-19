# Role: Lakehouse

You own the medallion's physical shape: table layout, the merge/watermark machinery in
`00-platform/lib/`, and the metadata tables the rest of the platform reads.

## State

`CD_Bronze_Lakehouse`, `CD_Silver_Lakehouse`, `CD_Gold_Lakehouse` all exist and are
schema-enabled (`dbo`). Gold now publishes **54** table schemas via `gold_schema.json`, including **17** `man_*`
tables (9 original plus 8 for the Project Quality Plan). All 17 `man_*` are still empty —
the silver→gold link is written now, but nobody has entered data and no SharePoint site
exists yet.

**`enableSchemas` is creation-only.** There is no API to enable schemas on an existing
lakehouse — getting it wrong means dropping and recreating, which is free while empty and
expensive once it is not. `deploy.py --verify` checks this on every run.

## The library is the important part

`lib/fabric_common.py`:

- `merge_delta()` / `merge_sql()` — Delta MERGE on the natural key. The existing foundation
  notebooks do `DROP TABLE IF EXISTS` + `.mode("append")`, which loses history, breaks
  concurrent readers, and duplicates on re-run. MERGE is idempotent, which is what makes
  incremental loading and safe re-runs possible at all. This is the single biggest
  robustness difference between charley-dev and what it replaces.
- `row_hash()` uses `sort_keys` so the hash is order-independent — otherwise a re-serialised
  payload looks like a change.
- `audit_columns()` — `_ingested_at`, `_source_endpoint`, `_batch_id`, `_row_hash` on every
  bronze row. This is what makes "why did this number change?" answerable.
- `get_secret()` — Key Vault in Fabric, env var locally.

`lib/watermark.py`: `OVERLAP = timedelta(hours=1)` backward overlap; the watermark advances
**only on success**, and `high_water([])` returns None so an empty pull cannot advance it
past unfetched data.

`lib/dq.py`: expectations return **failing rows**, not booleans — a boolean tells you
something is wrong, the rows tell you what. `SEVERITY_ERROR` failures call
`assert_no_blocking()`, which raises and stops the pipeline rather than publishing.

## The metadata tables

Physical tables must be created by writing an empty DataFrame with `overwriteSchema` —
`CREATE TABLE (cols)` writes no data files, and anything Direct Lake later touches cannot
bind to a file-less table.

`cd_dq_results` **now exists and holds 104 rows** (one per expectation). It was silently
absent for weeks: `_persist_results` used a relative import that cannot resolve in the flat
`Files/lib` import context, and the failure was swallowed by a `try`/`except`. Fixed
2026-08-19. The lesson generalises — a bare `except` around a write is how a table goes
missing without a single failed run.

`cd_meta_watermark` has not been re-verified since; treat its existence as unconfirmed.

## Constraint

Reads of `Bronze_Lakehouse` / `Silver_Lakehouse` are comparison-only and go through the SQL
endpoint, which is read-only by construction. Our pipelines write only to `CD_*`.
