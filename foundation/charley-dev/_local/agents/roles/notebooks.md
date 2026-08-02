# Role: Notebooks

You own the four Fabric notebooks and the generator that produces them.

## The generator is the source, not the notebook

`_local/make_notebooks.py` builds `.ipynb` payloads from `cell()` / `notebook()`; the deploy
scripts assemble and push them. **Edit the generator or the SQL, never a generated notebook
body** — a hand-edited notebook is overwritten on the next deploy and the change is lost
silently.

| Notebook | Built by | State |
|---|---|---|
| `cd_01_extract_procore` | `deploy_ingestion.py` | Reaches `load_settings` and stops — no credentials |
| `cd_10_bronze_to_silver` | `deploy_silver.py` | Runs clean, produces empty silver (bronze is empty) |
| `cd_20_seed_gold` | `deploy_seeds.py` | Populated |
| `cd_30_build_gold` | `deploy_gold.py` | 16 gold tables populated |

## Constraints

- **Fabric's job API gives no per-cell detail.** A failed notebook reports "Failed" and
  nothing else. Every notebook therefore writes structured diagnostics to
  `Files/_diag/*.json`, and the deploy scripts read them back over the OneLake DFS API. This
  is how the pre-1582 date problem was found. Keep it — a notebook that fails without a
  diagnostic is a notebook that costs an hour to debug.
- **Notebooks assert their own row counts** and raise on an unexpected result. A stage that
  fails loudly is worth more than one that half-succeeds, because `CD_Master_Pipeline` gates
  on `Succeeded` and a quiet partial failure would let gold rebuild over stale bronze.
- **Zero rows is a legitimate state, not an error.** Bronze is empty until Procore
  authenticates. Print it clearly; do not raise on it.
- **Cross-lakehouse reads go through `abfss://` temp views**, not the default catalog —
  bronze and silver are different lakehouses. `CREATE OR REPLACE TEMPORARY VIEW ... WHERE 1=0`
  declares the shape when a table does not exist yet, so transforms are exercisable before
  ingestion has ever run.
- **Secrets come from `lib/fabric_common.get_secret()`** — Key Vault inside Fabric, env var
  locally. Never a literal, never a widget default, never a printed value.
- Spark lowercases table names on write. Anything downstream that names a table (TMDL
  `entityName`, a SQL endpoint query) must use lowercase.

## The current gap

`cd_01_extract_procore` stopping at `load_settings` is correct behaviour with no
credentials, but it is nearly indistinguishable from a hang. It should say exactly which
secret is missing and where to put it.
