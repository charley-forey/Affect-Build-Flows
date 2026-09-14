# Operations runbook

How the nightly pipeline runs, how to tell whether a night was good, how to validate and
promote a change, and how to back it out. Written 2026-09-14. Current status and open items
are in [validation-and-development-plan.md](validation-and-development-plan.md) (top
section). Measured counts are in [build-status.md](build-status.md).

## 1. Nightly pipeline (`CD_Master_Pipeline`, workspace `Build`)

Notebook stages follow the dependencies below; Sage ingestion can run independently.
Earlier parallel starts at 06:00 starved the Spark session pool:
Land To Bronze and Land Manual Input were cancelled without starting while Extract Procore
held a session for 80-100 minutes. This is the live definition as read on 2026-09-14:

| # | Activity | Item | Depends on | Retry | Timeout |
|---|---|---|---|---|---|
| 1 | Land To Bronze | `cd_05_land_to_bronze` | none | 1 | 1h |
| 1 | Ingest Sage | `CD_Sage_Ingest` (dataflow) | none | 1 | 1h |
| 2 | Land Manual Input | `cd_06_land_manual` | Land To Bronze | 1 | 30m |
| 3 | Extract Outbuild | `cd_02_extract_outbuild` | Land Manual Input | 1 | 30m |
| 4 | Extract Procore | `cd_01_extract_procore` | Extract Outbuild | **0** | 2h |
| 5 | Bronze To Silver | `cd_10_bronze_to_silver` | Extract Procore, Extract Outbuild, Ingest Sage, Land To Bronze, Land Manual Input | 1 | 30m |
| 5 | Seed Gold Dimensions | `cd_20_seed_gold` | Bronze To Silver | 1 | 30m |
| 6 | Build Gold | `cd_30_build_gold` | Bronze To Silver, Seed Gold Dimensions | 1 | 30m |
| 7 | Data Quality Gate | `cd_40_dq_checks` | Build Gold | 1 | 30m |
| 8 | Publish Models | `cd_50_publish_models` | Data Quality Gate | **0** | 1h |

The live definition read back on September 14 contains all 10 activities, including Publish
Models after Data Quality Gate Succeeded. Seed Gold Dimensions depends on Bronze To Silver;
Sage ingestion can run independently. Both models accepted automatic update OFF later that
day. A successful full scheduled cycle and browser confirmation of that setting remain
unverified. The latest observed scheduled run failed; do not equate a deployed DAG with a
healthy schedule.

Succeeded-only dependencies block downstream stages after failure. With automatic update
off, models retain their prior framing until an explicit refresh. This is not atomic
publication across the two models: one can refresh successfully while the other fails.

Why the ordering is what it is:
- Landing runs before extraction. Landing re-merges the newest batch in `Files/_landing`,
  and the live pull that runs after it must overwrite that replay. A Procore landing batch
  must never be left as the newest one there.
- `cd_06_land_manual` creates the `cd_bronze_man_*` tables that silver parses. Silver
  deployed or run before it fails with `System_Cancelled_Session_Statements_Failed`, which
  names no table.
- Extract Procore and Publish Models have no retry. Attempt 1 spends the hourly Procore
  quota, so a retry would only get 429s. A publish retry would resubmit a refresh that may
  still be running.

## 2. Reading manifests and diagnostics

Every notebook writes to `CD_Bronze_Lakehouse` (or the candidate lakehouse) under
`Files/_diag/`:

| File | Writer | Read it for |
|---|---|---|
| `ingestion/<batch>.json` | cd_01 / cd_02 | Per-endpoint status, rows and scopes. Batch status plus `blocking_failures` and `warnings` (Outbuild). One file per batch, written once. |
| `ingestion/<batch>/<endpoint>.audit.json` | cd_01 | Per-scope audit. A 403/404 shows as `unavailable_403_404`, or as `excluded_declared` when the project is listed under the endpoint's `unavailable_projects` |
| `ingest_run.json` | cd_01 / cd_02 | Latest batch only (overwritten) |
| `dq_run.json` | cd_40 | Every rule with severity, failing_rows, passed and blocking. Any blocking rule means the run failed and nothing was published. |
| `publish_run.json` | cd_50 | Refresh request ids per model and the RunId agreement check |
| `<prefix>_candidate_<run_id>.json`, `candidate_counts_<run_id>.json` | cd_9x validation notebooks | Candidate DQ results and immutable row counts |

A quick triage order for a red night:
1. Find the failing activity in the pipeline run.
2. For ingestion, open `ingestion/<batch>.json`. A 403/404 on a project that is not declared
   is a real coverage gap. 429s mean the quota was spent, usually by a manual re-run in the
   same hour.
3. For the gate, filter `dq_run.json` to `blocking: true`.
4. A notebook that shows Cancelled with start time `0001-01-01` never got a Spark session.
   It is not a code failure.

In the models, `meta_PipelineRun` holds the last checked run. The footer's Last Refresh and
Pipeline Status read from it, and `reconcile_live.py` check 8 compares it across both
models.

## 3. Candidate validation (isolated data, shared capacity)

Read [capacity-operations.md](capacity-operations.md) before starting a live job. The
September 14 capacity rejection stopped further heavy validation. Do not restart full
builds or query sweeps until measured capacity has recovered. Prefer targeted validation
of the changed stage. Do not resubmit a job because a polling command timed out.

The latest expanded candidate has a passing silver checkpoint but lacks its final
run-specific gate evidence. Snapshot certification is still pending. The examples below
are commands to use when capacity and prerequisites permit, not a direction to run now.


A candidate builds silver and gold from existing bronze in the isolated validation
lakehouse and runs the full DQ suite there:

```bash
cd foundation/charley-dev/_local
python validate_sage_spark.py --full --start    # deploys cd_94_validate_full, starts one job
python validate_sage_spark.py --full --status   # poll once; fetches the diagnostic when done
```

The evidence lands in `_docs/full-spark-evidence.json`, `full-spark-job.json` and
`full-candidate-{seed,silver,gold}_run.json`. The bar is a completed job AND matching run-specific evidence with no blocking or unexecuted checks. Missing evidence is not a pass. Record the run id,
rule count and the pass and warn counts in the commit message. `--silver` and `--gold` run
one layer each. The candidate's scope is "silver and gold from existing bronze". It does not
certify upstream freshness.

Offline first, from the repository root: `python foundation/charley-dev/_local/run_tests.py` (21 suites, no network).

## 4. Promotion order

Run from `_local/`, each with `--apply`, and stop at the first non-zero exit:

1. `deploy_ingestion.py`: shared library and extractors. NOT while a nightly run is in
   progress - it replaces files the running notebooks import.
2. `deploy_outbuild.py`
3. `deploy_seeds.py`: gold reads `seed_ProjectCrosswalk`
4. `deploy_manual.py`: creates `cd_bronze_man_*`
5. `deploy_silver.py`
6. `deploy_gold.py`: publishes `gold_schema.json`, which the model generators read
7. `deploy_dq.py`: run the gate and confirm the result matches the candidate. Exits
   non-zero on a Failed, Cancelled or Deduped run.
8. `deploy_model.py`, then `deploy_model_qc.py`
9. `deploy_report.py`, then `deploy_report_qc.py`
10. `deploy_publish.py --apply`: the Publish Models notebook. An out-of-band publish is
    `deploy_publish.py --apply --run`. Only do it after a passing gate.
11. `deploy_pipeline.py --apply`: the nightly pipeline, including Publish Models after the
    gate and Seed Gold Dimensions after Bronze To Silver.
12. `set_autosync.py --apply`: both models accepted OFF on September 14. Verify the
    setting in the portal and validate Publish Models plus failure notification. A failed
    publish can leave a stale or split release; do not re-enable automatic updates to hide it.
13. `validate_model.py`: live row counts, measure evaluation and independent checks. It does
    not reframe production unless given `--allow-production-reframe`.
14. `reconcile_live.py`: ten read-only checks, aggregates-only evidence to
    `_docs/live-reconciliation/<UTC>.json`, exit 1 on any ERROR-severity FAIL. For a
    candidate, pass `--model-id`, `--qc-model-id` and `--lakehouse`.

Historical early-morning promotion: candidate `cadcd0d8` followed what are now steps 3-9 and 13. The gold step ran
117 statements with 0 failed. The DQ gate ran 189 rules with 0 blocking, the same as the
candidate. `validate_model.py` passed 18 checks.

For step 12, run `set_autosync.py` (dry run) first, then `set_autosync.py --apply`. Confirm in the portal (Semantic model settings > Refresh > "Keep
your Direct Lake data up to date" = Off), because no API can read that setting back.

## 5. Rollback

Owned Fabric definitions and gold tables are updated in place. Rollback requires a
reviewed prior version, preservation of current work and data, and another validated
publish. The following checkout example changes local files; use an isolated checkout
or preserve uncommitted work before using it:

```bash
git checkout <previous promoted commit> -- foundation/charley-dev
# re-run the promotion order (section 4) for the layers that changed
git checkout HEAD -- foundation/charley-dev
```

- Gold tables are `CREATE OR REPLACE`, so a redeploy of the old gold SQL rebuilds the old
  shape. Redeploy the models afterwards so TMDL types match.
- `fct_DailySnapshot` retains captures by date. A same-date re-run replaces
  that date. Rolling back code does not delete captured history.
- Both models accepted automatic update OFF on September 14; confirm that setting before
  rebuilding. Gold is replaced in place, and publication across models is not atomic.
- Select a rollback definition using the dated deployment evidence, not the latest Git
  commit alone. Repository commits and live refreshes are separate operations.

## 6. Procore quota

- Limit: 600 requests per hour (`X-Rate-Limit-Limit`, measured 2026-08-02).
- A full extract made about 1,165 requests (batch `20260913T060433`). After endpoint removals
  and `per_page: 1000` on nine top-level v1.x collections, the estimate is about 954. That
  still spans two hourly windows, so the extractor sleeps on the quota inside one run.
- The loader refuses `per_page` > 100 on nested, v2.0 and daily_logs paths, which the tenant
  rejects with 400. Commitment line items stay at one call per contract.
- **Do not re-run extraction by hand within the same hour as the nightly run** or another
  manual run. On 2026-09-10 four manual runs after the scheduled one burned the quota.

## 7. Declared scope exclusions

Procore 403/404 fails the run unless it is declared in
`01-ingestion/Procore/config/endpoints.yml`:

| Endpoint | Project | Reason |
|---|---|---|
| `prime_contracts` (and inheriting children `prime_contract_line_items`, `payment_applications`) | `562949955173068` | Prime Contracts tool not enabled on this project. 403/404 observed 2026-09-11..09-13, while the same project returns 200 on 27 other endpoints. |

These endpoints were removed rather than excluded, because they were malformed or unused and
nothing reads them: `standard_cost_codes`, `change_order_requests`, `punch_item_types`,
`schedule` (all 2026-09-13) and `commitments` (2026-09-14, a strict duplicate of work-order
plus purchase-order contracts). Add an exclusion only with the observed status, dates and a
reason. Never add one to make a red night green.

## 8. Evidence files: PII rule

This repository is **public**.
- Evidence committed under `_docs/` holds **aggregates, ids, job numbers and invoice record
  numbers only**. No person names, no emails, no phone numbers, no free-text comments.
- Raw Procore captures, API payloads and notebook driver logs stay local
  (`.gitignore`), because they carry people's emails.
- Refer to people by role (for example "Affect finance lead", "platform engineer").
- Sage vendor ids in `live-reconciliation/*.json` are numeric record ids, not names. Keep it
  that way.
