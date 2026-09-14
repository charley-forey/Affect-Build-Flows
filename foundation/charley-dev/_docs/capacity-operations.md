# Capacity operations (Build workspace, F2)

Written 2026-09-14 after the capacity was throttled (interactive delay) by a night of Spark.
Investigation: five `cd_94_validate_full` runs plus the nightly pipeline used about 21-42 CU-h
in six hours. That is 43-87% of an F2's 48 CU-h/day. SKU F2 is from `access-model.md`. The
signed-in user is not a capacity admin, so a capacity admin must **confirm the SKU**.

## How Fabric charges this workload

- **All Spark is a background operation, smoothed over 24 h.** A job keeps using capacity for
  a day after it finishes. Running at night does not free the next business day. Only the
  daily total matters.
- 1 CU = 2 Spark vCores. A Medium node has 8 vCores, so it costs **4 CU while a session is
  active**. That is 2x an F2's size. Idle pool time and cluster start are not billed.
- Throttling stages depend on how far ahead capacity is already used:

  | Future usage | Effect |
  |---|---|
  | Up to 10 min | Nothing |
  | 10-60 min | 20 s interactive delay (DAX, reports) |
  | 60 min to 24 h | Interactive rejection |
  | Over 24 h | Background jobs rejected too |

- An F2 has 4 Spark vCores, or 20 with burst, and a queue of 4. On a throttled capacity,
  interactive and notebook-API runs fail with HTTP 430. Only pipeline, scheduler and SJD runs
  queue.

Docs:
- [Throttling](https://learn.microsoft.com/fabric/enterprise/throttling)
- [Spark concurrency and queueing](https://learn.microsoft.com/fabric/data-engineering/spark-job-concurrency-and-queueing)
- [Spark compute and billing](https://learn.microsoft.com/fabric/data-engineering/spark-compute)

## Budget rules

1. **Keep Spark at or below 25 CU-h/day** (about half of 48). The rest is for DAX and SQL.
2. **Run one Spark job at a time.** Chain notebooks in a pipeline. Don't start a manual
   notebook while the pipeline runs.
3. **Run at most one full candidate validation (`cd_94_validate_full`) per day.** Never run
   two back to back, and avoid the same 24 h as a manual rebuild. Iterate with the targeted
   validators (cd_91/92/93).
4. **Don't run a manual rebuild on a day the 06:00 UTC nightly runs.**
5. **Don't run DAX sweeps (`execute_dax_query` validation) while heavy Spark is in the
   24-hour window.**
6. **After a throttle, start no more Spark until "minutes to burndown" is back to zero.**

### Estimated CU per stage

Based on run durations measured on 2026-09-14. These are estimates from node size, not
metered values. The Capacity Metrics app is authoritative.

| Stage | Minutes | CU-h, 2 Medium nodes (before) | CU-h, 1 Medium node (after `deploy_spark_settings.py`) |
|---|---|---|---|
| cd_05_land_to_bronze | 3 | 0.4 | 0.2 |
| cd_06_land_manual | 1.5 | 0.2 | 0.1 |
| cd_02_extract_outbuild | 5 | 0.7 | 0.3 |
| cd_01_extract_procore | 82 | 11 | 5.5 |
| cd_10_bronze_to_silver | 9 | 1.2 | 0.6 |
| cd_20_seed_gold | 2.5 | 0.3 | 0.2 |
| cd_30_build_gold | 12 | 1.6 | 0.8 |
| cd_40_dq_checks | 7 | 0.9 | 0.5 |
| **Nightly pipeline total** | ~122 | **~16** | **~8** |
| cd_94_validate_full (each) | 30 | 4 | 2 |

Procore extraction is two thirds of the nightly cost, and most of it is waiting on the API.
The next saving is to move it to a Python notebook (2 vCores, no JVM) or to a pipeline
Copy/Web activity. That is not done here.

## Spark settings (`_local/deploy_spark_settings.py`)

Dry run by default. `--apply` needs the workspace admin role. The script refuses any
workspace other than Build. The pre-change values are in `spark-settings-before.json`.

| Setting | Before | After | Why |
|---|---|---|---|
| `pool.starterPool.maxNodeCount` | 2 | 1 | Single node, ~4 CU instead of ~8. The starter-pool docs list 1 as the F2 maximum. |
| `job.sessionTimeoutInMinutes` | 20 | 10 | Idle interactive sessions stop sooner. |
| `highConcurrency.notebookPipelineRunEnabled` | false | true | Pipeline notebooks share a session instead of starting one each. |
| `--small-pool` (opt-in) | Starter Pool | `cd_small`: Small, 1 node, autoscale off | ~2 CU per job. See the caveats below. |

`--small-pool` caveats:
- Custom pools start on demand, which takes 2-5 min (not billed).
- A single node halves the 32 GB node between driver and executor.
- The capacity admin must allow workspace-level pool sizing.
- Trial it before relying on it for gold or DQ.

References:
- [Update Spark Settings](https://learn.microsoft.com/rest/api/fabric/spark/workspace-settings/update-spark-settings)
- [Create Workspace Custom Pool](https://learn.microsoft.com/rest/api/fabric/spark/custom-pools/create-workspace-custom-pool)
- [Starter pools](https://learn.microsoft.com/fabric/data-engineering/configure-starter-pools)
- [High concurrency in pipelines](https://learn.microsoft.com/fabric/data-engineering/configure-high-concurrency-session-notebooks-in-pipelines)

**Pipeline session tag.** Every notebook activity in `CD_Master_Pipeline` has
`sessionTag: cd_master` (`deploy_pipeline.SESSION_TAG`). Sessions are shared only between
notebooks that have:
- the same user
- the same default lakehouse
- the same compute config and libraries

A session holds at most 5 notebooks. In practice sharing happens between consecutive stages
on the same lakehouse.

**No `%%configure` in generated notebooks.** This is deliberate, and `test_notebooks` asserts
it:
- Custom session properties skip the starter-pool fast start.
- The smallest documented `driverCores` is 4, which a single-node Medium pool already gives.
- A differing config splits high-concurrency sharing.
- A `%%configure` outside the first code cell fails pipeline runs.

Cap CU at the pool instead.

## Check the capacity (capacity admin)

Install the Microsoft Fabric Capacity Metrics app, then go to **Compute** and select the
capacity.
- **Throttling tab:** interactive delay and rejection percentages. Sustained above 100% means
  throttling.
- **Overages tab:** add %, burndown %, cumulative % and **minutes to burndown**. Wait until
  it reaches 0.
- Filter items by workspace **Build** to see CU per notebook and pipeline run.

[Metrics app compute page](https://learn.microsoft.com/fabric/enterprise/metrics-app-compute-page)

## Pause or resume (capacity admin, F SKU only)

Pausing ends throttling immediately:
- The remaining smoothed and carried-forward CU is billed at pause (a few dollars at F2).
- Every item on the capacity is unavailable while paused, including reports and the nightly
  pipeline.

To pause:
1. Check that no pipeline is running.
2. In the Azure portal, open the Fabric capacity and select **Pause**.
3. Select **Resume**.
4. Check that a report loads.

Don't pause during the 06:00 UTC nightly window.

[Pause and resume](https://learn.microsoft.com/fabric/enterprise/pause-resume)

## SKU options

1. **Autoscale Billing for Spark** (on-demand billing). The capacity admin turns it on per
   capacity and sets a max CU limit.
   - Spark stops consuming F2 CU and is billed pay-as-you-go at the Spark rate for active job
     time only.
   - No smoothing or bursting. Batch jobs queue at the limit.
   - DAX gets the whole F2.
   - Best fit for this build phase.
   - [Autoscale Billing for Spark](https://learn.microsoft.com/fabric/data-engineering/autoscale-billing-for-spark-overview)
2. **F4** for the build and release phase. It doubles headroom and still allows only one
   starter-pool node. Drop back to F2 once the nightly run is about 8 CU-h and validations
   are rare.
3. **Temporary scale-up** (F8 for 24 h) for heavy validation days, or to burn down a throttle
   faster.

Steady state (nightly run only, single node, ~8 CU-h/day) fits F2 with room for reports.
