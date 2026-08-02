# Role: Lakehouse

You own the medallion's physical shape: table layout, the merge/watermark machinery in
`00-platform/lib/`, and the metadata tables the rest of the platform reads.

## State

`CD_Bronze_Lakehouse`, `CD_Silver_Lakehouse`, `CD_Gold_Lakehouse` all exist and are
schema-enabled (`dbo`). Gold holds 16 populated tables plus 9 empty `man_*`.

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

## The gap

`cd_meta_watermark` and `cd_dq_results` are designed and coded against, but the tables do not
exist in any lakehouse. Until they do, incremental loads have nothing to read and the DQ
suite has nowhere to write. Physical tables must be created by writing an empty DataFrame
with `overwriteSchema` — `CREATE TABLE (cols)` writes no data files, and anything Direct Lake
later touches cannot bind to a file-less table.

## Constraint

Reads of `Bronze_Lakehouse` / `Silver_Lakehouse` are comparison-only and go through the SQL
endpoint, which is read-only by construction. Our pipelines write only to `CD_*`.
