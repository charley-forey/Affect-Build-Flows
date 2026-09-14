# Procore extraction on the Python kernel

`cd_01_extract_procore_py` is `cd_01_extract_procore` running on a Fabric **Python notebook**
(pure Python kernel, no Spark). It writes bronze Delta tables with delta-rs (`deltalake`)
instead of Spark. The Spark notebook stays deployed, so rollback is one pipeline redeploy.

## Why

On 2026-09-14 `cd_01_extract_procore` ran for 81.8 min (06:32-07:53 UTC). Nearly all of that
time is spent waiting on Procore's 600 requests/hour quota. The Spark session held the
workspace Starter Pool (Medium 8-vCore nodes, autoscale 1-2) for the whole run. Evidence is in
the capacity-throttling investigation (2026-09-14).

| | Spark (today) | Python kernel |
|---|---|---|
| Compute held | 1-2 × 8 vCores = **4-8 CU** | 2 vCores = **1 CU** |
| 82-minute run | **5.5-10.9 CU-h** | **~1.4 CU-h** |
| Share of an F2 day (48 CU-h) | 11-23% | ~3% |
| Spark admission (F2: 4 vCores, 20 with burst) | uses 8-16 vCores; queues other jobs | uses no Spark vCores |

**Expected saving: about 4-9.5 CU-h per night.** A second effect matters as much: the other
nightly Spark jobs no longer wait behind this job for Spark cores.
The two `cd_20_seed_gold` runs that were cancelled at 06:01 and 06:31 hit exactly that wait.
The run takes as long as before, because Procore's quota sets the pace, not the compute.

## What changed

- `00-platform/lib/deltars.py` holds delta-rs ports of the four Spark writes:
  - `merge_rows` does the job of `fabric_common.merge_delta`. Exact duplicate rows collapse. Two different rows with the same key raise before anything is written. The join is null-safe (`IS NOT DISTINCT FROM`, the equivalent of `<=>`). Matched rows are updated from the source, unmatched rows are inserted, and the first write creates the table.
  - `read_watermark` / `write_watermark` do the job of `watermark.py`, using the same `cd_meta_watermark` table and schema.
  - `log_run` does the job of `fabric_common.log_run`. It appends to `cd_meta_run_log` and never raises.
- `make_notebooks.py`: the extraction cells call four hooks, `read_since`, `write_bronze`,
  `write_watermark` and `log_run`. Each kernel's setup cell defines them. The Spark notebook
  wraps the existing Spark functions, so its behaviour is unchanged. `extract_procore_python()`
  reuses every extraction cell and swaps only the markdown and setup cells. It writes to
  `abfss://<workspace>@onelake.dfs.fabric.microsoft.com/<lakehouse>/Tables/dbo/<table>` with a
  fresh `notebookutils.credentials.getToken('storage')` token on every write.
- `deploy_ingestion.py --python-kernel` deploys `cd_01_extract_procore_py` as a separate item.
  It also uploads `deltars.py`. Add `--validation-lakehouse NAME:ID` to bind the notebook to a
  validation lakehouse and deploy it as `cd_01_extract_procore_py_validation`.
- `deploy_pipeline.py --procore-python` points the `Extract Procore` stage at the Python item.
  The stage keeps the same name, timeout (2 h) and retry policy (0). The activity type is
  still `TridentNotebook`.
- `_local/tests/test_deltars.py` checks the new write path against the Spark path's own code:
  `prepare_merge` and the `merge_sql` statement, executed by DuckDB. Both paths get the same
  batches (inserts, updates on NULL-project keys, exact duplicates, replays and conflicts) and
  must produce identical rows. The test also covers watermark and run-log behaviour.

## Cutover plan

Capacity is throttled, so run each step on a quiet day and never beside a Spark job.

1. **Create a validation lakehouse.** Create `CD_Bronze_Validation` in charley-dev with
   schemas enabled. Copy `cd_bronze_procore_*`, `cd_meta_watermark` and `cd_meta_run_log` from
   CD_Bronze_Lakehouse into it. Copying the watermark table makes the Python run incremental,
   like production.
   Before copying, check the table protocol on the source (`DESCRIBE DETAIL`). delta-rs cannot
   write tables that use deletion vectors, column mapping, type widening or v2 checkpoints.
   Runtime 1.3 does not enable these by default. If any source table has one, stop here.
2. **Deploy the validation copy.**
   `python deploy_ingestion.py --apply --python-kernel --validation-lakehouse CD_Bronze_Validation:<id>`.
   Then call getDefinition on the new item and confirm that `metadata.microsoft.language_group`
   is `jupyter_python`. If Fabric rewrote it, the notebook would run on Spark and save nothing.
   Also confirm that the first cell runs `import deltalake, yaml, requests` without `%pip`.
3. **Run side by side.** Let the nightly pipeline run the Spark notebook as usual. As soon as
   it finishes, run `cd_01_extract_procore_py_validation` on demand. Do not run them at the same
   time: both draw on the same Procore quota.
4. **Compare bronze.** For each table, compare the set of `(_key, _project_id, _row_hash)`
   between the two lakehouses. `_ingested_at` and `_batch_id` are expected to differ. Also
   compare the evidence files: status, `written_rows` and `duplicate_rows_removed` per
   endpoint in each lakehouse's `Files/_diag/ingestion/<batch>.json`.
   Differences are only acceptable on records whose Procore `updated_at` falls between the two
   runs. Then run `cd_10_bronze_to_silver` against the validation bronze, or diff silver row
   counts, to confirm that silver reads delta-rs-written tables.
5. **Record CU use.** In the Capacity Metrics app, compare CU-seconds for the two runs. The
   expected ratio is 4-8×.
6. **Switch.** Run `python deploy_ingestion.py --apply --python-kernel`, which binds the
   notebook to CD_Bronze_Lakehouse. Then run `python deploy_pipeline.py --apply --procore-python`.
   Watch the first nightly run.
7. **Rollback.** Run `python deploy_pipeline.py --apply` (without the flag). The Spark notebook
   was never removed. Bronze written by delta-rs stays readable by Spark: it uses the same
   schema and plain Delta protocol.
8. **After a stable week,** run `OPTIMIZE` on the Procore bronze tables from an existing Spark
   job. delta-rs merges do not compact files or apply V-Order, and they checkpoint every 100
   commits instead of Spark's 10.

## Verified documentation facts

- The Python notebook is a pure Python kernel. It defaults to a single node with 2 vCores
  and 16 GB, and it can run as a pipeline notebook activity, on a schedule, or through the
  public API. `notebookutils` is preinstalled, the default lakehouse is available, and `%%configure`
  (vCores, defaultLakehouse) is supported. delta-rs and DuckDB are preinstalled.
  Environment items and session timeout settings are not available.
  https://learn.microsoft.com/en-us/fabric/data-engineering/using-python-experience-on-notebook
- The Python kernel defaults to 2 vCores, which is 1 CU. An 8-vCore Starter Pool node is 8 CU
  after scale-up, or 4 CU as a single node. delta-rs supports MERGE and OCC but cannot write
  deletion vectors, column mapping or v2 checkpoints, and it checkpoints every 100 commits.
  https://learn.microsoft.com/en-us/fabric/data-engineering/fabric-notebook-selection-guide
- `notebookutils.credentials.getToken('storage')` and `getSecret('https://<vault>.vault.azure.net/', name)`
  work in Python notebooks. Tokens expire, so long runs should request a new one.
  https://learn.microsoft.com/en-us/fabric/data-engineering/notebookutils/notebookutils-credentials
- The public API docs say the language and kernel properties in notebook metadata must be
  set correctly. Microsoft's definition docs only show the `synapse_pyspark` example.
  https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/notebook-definition
- The pipeline Notebook activity runs any notebook item. Session tags and high concurrency
  apply to Spark only.
  https://learn.microsoft.com/en-us/fabric/data-factory/notebook-activity

## Open risks

- **Kernel metadata is not documented.** The generator writes
  `kernel_info {name: jupyter, jupyter_kernel_name: python3.11}`, `kernelspec {name: jupyter}`
  and `microsoft.language_group: jupyter_python`. These values come from Fabric's own export
  format, not from Microsoft Learn. Step 2 verifies them.
- **The runtime library versions differ from CI.** CI pins `deltalake==1.6.3`, but the Fabric
  Python runtime ships its own version. `merge(...).when_matched_update_all()` and
  `is_deltatable` exist in 0.18 and later. Confirm the runtime version in step 2. Also confirm
  that `yaml` (PyYAML, used by `procore_scope`) and `requests` are preinstalled. If they are
  not, add `%pip install` to the setup cell.
- **Table features.** delta-rs refuses to write a table that has deletion vectors or column
  mapping enabled. Step 1 checks for this. Fabric Runtime 2.0 enables deletion vectors by
  default, so a future runtime upgrade of the Spark jobs that recreate these tables would
  break this path.
- **Concurrent writers.** If a Spark job writes a Procore bronze table while this notebook
  merges into it, delta-rs's optimistic concurrency fails the commit. The pipeline is serial,
  so this cannot happen today.
- **Memory.** Rows for one endpoint are held in memory, as the Spark driver held them before.
  2 vCores come with 16 GB. The largest endpoint is well under that, but `%%configure`
  `{"vCores": 4}` is the fallback.
- **No live monitoring.** There is no Spark UI. The per-endpoint evidence in
  `Files/_diag/ingestion/` is unchanged and remains the record of each run.
