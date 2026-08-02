# Full assessment — 2026-08-02

An independent read of everything in `charley-dev`: what is built, whether it is actually
live in Fabric, whether the numbers on the dashboard are right, and what is left.

Every claim here was checked against the running Fabric workspace rather than against the
repo's own documentation. Where the two disagreed, the docs were wrong and have been
corrected — [`build-status.md`](build-status.md) had drifted six rows out of date.

**Read this first if you are new:** [`solution-guide.md`](solution-guide.md) explains what
the platform is and how it works. This document is the audit of it.

---

## Verdict

The platform is real, deployed, and running. The medallion is populated from Affect's
production Procore tenant, the nightly pipeline runs green, the semantic model is a proper
Direct Lake star schema, and all 99 measures evaluate against live data.

One material defect was found, fixed and deployed: **the dashboard understated the portfolio
contract value by $4.85M.** Current Contract now reads $35,102,931.14 and Contract Growth
16.03%, against $30,254,551.24 and 0.00% before. Details below.

A second, smaller defect is diagnosed but **not** fixed: the DQ gate reports success while
silently failing to write its reject detail, so the Data Quality page shows rows from an
older run. Counts are trustworthy; drill-through is not.

Two things that read as failures are not: three gold tables invisible to SQL, and 105 of 105
insurance certificates expired. Both are explained below — do not "fix" either.

---

## What was checked, and how

| Area | Method | Result |
|---|---|---|
| Repo ↔ GitHub | `git` against `origin` | **Out of sync** — see *Source control* |
| Items deployed | `list_items` / `list_folders` on workspace `Build` | 12 of 14 present |
| Bronze / silver / gold populated | `execute_sql_query` row counts | Populated, verified |
| Gold ↔ repo SQL | Table list vs `sql/gold/*.sql` | Matches |
| Semantic model ↔ repo | Deployed TMSL vs `*.tmdl` | Matches — 37 tables |
| Pipeline DAG ↔ repo | `get_pipeline_definition` vs `pipeline-content.json` | **Identical** |
| Which silver feeds gold | Lakehouse GUIDs in deployed notebook | `cd` source, as intended |
| Measures compute | All 99 evaluated via `execute_dax_query` | All evaluate |
| Numbers are *correct* | Recomputed independently in SQL | **One defect found** |
| Pipeline freshness | `meta_PipelineRun` | Ran 2026-08-02 22:06, 0 blocking |
| DQ gate | `cd_dq_rejects` + heartbeat | 63 expectations, 6 failing, 0 blocking |

---

## The defect: $4.85M of change orders were missing from the contract

**Symptom.** The dashboard showed Current Contract $30,254,551.24 — *exactly* equal to
Original Contract — and Contract Growth 0.00%, against 307 change orders in the model.

**Root cause.** `sql/gold/30_fct_financialperiod.sql` aggregated change orders per month and
added only that month's to the contract:

```sql
CurrentContract = OriginalContractAmount
                + <that month's change orders>      -- should be TO DATE
                - <that month's pending>
```

The DAX then reads the table with `LASTNONBLANKVALUE` — the latest row per project — so the
report showed only the **final month's** change orders and silently dropped every approved
CO before it. Per project the contract bounced around instead of accumulating: on the
sample project it went +8,300 in March, +104,240 in May, back to +69,522 in June.

**Impact.** Understated by **$4,848,379.90** — 16% of contract value. Everything dividing by
contract value inherited it: `Total Billed %`, `Billed Cumulative % Of Contract`,
`Balance To Finish`. `Pending Change Orders` was understated the same way, reading
$22,891.76 against a true $59,170.97.

**Why the tests missed it.** The reconciliation gate in `test_gold.py` pins Current Contract
to 9,116,960.48 and Contract Growth to 3.60%, straight from the workbook — and it passed
throughout. The fixture put all three change orders in **one month**, where a per-month and
a cumulative roll-up are arithmetically identical. The gate was watching the right number
through a fixture that could not express the bug.

**Fix.** Change orders now accumulate — running totals over the month spine, so each row
carries the contract as it stood that month. The fixture gained a second month, and three
assertions now cover it, including that the contract is monotonic per project.

**Status: FIXED AND DEPLOYED** — `cd_30_build_gold` re-run 2026-08-02 22:56, model reframed,
DQ gate re-run 23:01 (63 expectations, 0 blocking). Verified live:

| Measure | Before | After |
|---|---:|---:|
| `Current Contract` | $30,254,551.24 | **$35,102,931.14** |
| `Contract Growth %` | 0.00% | **16.03%** |
| `Pending Change Orders` | $22,891.76 | **$59,170.97** |
| `Total Billed %` | 73.05% | 62.96% |
| `Billed Cumulative % Of Contract` | 89.90% | 77.48% |

The last two moved *down* because the denominator was corrected — those figures were
flattering the portfolio, not just wrong. All 17 live DAX checks pass, including
`[Current Contract] is a balance, not a running total of months`.

**A contract may still legitimately fall.** Five projects show a decrease, each matching a
negative (credit) change order that month to the cent. The first version of the regression
test asserted plain monotonicity and would have called all five a bug; it now asserts that
every decrease is accounted for by that month's approved COs.

---

## Two findings that look like bugs and are not

**Three gold tables are invisible to SQL.** `bridge_vendorcostcode`, `fct_vendorinsurance`
and `meta_pipelinerun` do not appear in `INFORMATION_SCHEMA.TABLES` on the lakehouse SQL
endpoint. They hold 407, 105 and 3 rows respectively and serve the report correctly —
confirmed by DAX. Direct Lake reads the Delta files and bypasses the endpoint entirely;
this is Fabric's endpoint metadata sync lagging behind table creation. **Verify with DAX
before concluding a table is missing.**

**105 of 105 insurance certificates are expired.** Real, deliberate, and documented at the
top of `32_fct_vendorinsurance.sql`. The most recent expiry is 2025-04-01 and every record
carries Procore's own `non_compliant` status. The likely reading is that the Procore
insurance module was populated once and abandoned, not that Affect's subcontractors are
uninsured — but those are very different facts for a general contractor, and nothing in the
current reporting distinguishes them. **This is a question for Affect, not a data bug.**

---

## Source control: three branches, none merged to main

| Branch | State |
|---|---|
| `origin/main` | Missing **8 commits** — all the Power BI enhancement work |
| `origin/worktree-charley-dev-build` | The real tip. 8 ahead of main |
| `origin/worktree-pbi-enhance` | Merged into charley-dev-build via PR #9 |
| local `main` | **39 commits behind** `origin/main` |

PR #9 merged the dashboard work into `worktree-charley-dev-build`, not into `main`. So
`main` does not have the theme, the navigation, the portfolio page, the staleness footer,
or the scorecard visuals — even though all of it is **deployed and live in Fabric**. The
workspace is ahead of the default branch.

**Action:** open `worktree-charley-dev-build` → `main`, and `git pull` locally.

---

## Data quality: 6 failing expectations, 0 blocking

The gate is working as designed — these fail loudly and let the run through, which is
correct for coverage gaps as opposed to corruption.

| Expectation | Rows | Meaning |
|---|---:|---|
| cost codes parse to a CSI division | 1,000 | Procore free-text codes (`FINAL CLEAN`, `CONTINGENCY`); cannot roll up by division |
| every project is in Outbuild | 17 of 19 | No `OUTBUILD_API_TOKEN`. Outbuild is the **only** milestone source |
| every project is in Sage | 4 | 2 are test/template projects; 2 are real and read as zero revenue |

### The reject detail is stale, and the gate does not say so — ROOT CAUSE FOUND

`cd_dq_rejects` holds only batch `20260802T100451Z`. Four later runs — including one
triggered during this assessment at 23:01 — each reported 6 failing expectations and wrote
**no reject rows**, while the heartbeat recorded `Status: ok` every time.

The persist block in `cd_40_dq_checks` is wrapped in a `try/except` that catches the
failure, prints it to the notebook's stdout, and continues:

```python
try:
    dq._persist_results(spark, results, batch_id)
    for r in results:
        if r.failing_rows > 0:
            dq._persist_rejects(...)
except Exception as exc:
    print(f"PERSIST FAILED ...")   # nobody sees this
```

`_persist_results` writes `cd_dq_results` — **a table that does not exist in
`CD_Gold_Lakehouse`.** It raises, the `except` swallows it, and `_persist_rejects` is never
reached because it is inside the same `try`. The jobs API does not expose cell output, so
the message goes nowhere; the heartbeat then writes `ok` because the *evaluation* succeeded.

The intent was sound — a persistence failure should not discard a good evaluation. But the
run now reports healthy while the Data Quality page shows rows from a different, older run
sitting under a summary from the current one. Two fixes, both small:

1. Move `_persist_rejects` out of the shared `try`, so a results failure cannot suppress it.
2. Record the persist outcome on the heartbeat, so `Status: ok` means the whole gate
   completed rather than just the part that was measured.

The **counts are trustworthy** — `Files/_diag/dq_run.json` is written before the persist and
was current at 23:01:37. Only the drill-through detail is stale.

**Source coverage is 5.26%** — 1 of 19 projects present in all three systems. This is the
single biggest limit on the report, and it is an access problem, not a build problem.

---

## Scorecard coverage: 59%

Four of nine categories cannot be scored, and all four are blocked on data rather than code:

| Category | Blocked on |
|---|---|
| Accounts Receivable | Sage AR coverage |
| Profitability | Genuine human judgement — stays manual by design |
| Completion Variance | Outbuild milestones |
| Daily Reports | SharePoint manual input |

`Project Scorecard` reads 0.26 across all categories; `Project Scorecard (Measured Only)`
reads 0.44 across the five that have data. **Quote the measured-only figure**, or the
scorecard reads as poor performance when it is actually absent data.

---

## Numbers worth a second look

Not defects, but they do not reconcile at face value and someone will ask:

- **`Total Billed` $22.1M vs `Owner Billed To Date` $28.0M.** Different sources — Sage AR
  invoices against Procore payment applications — at different grains. Expected to differ,
  but the gap is not currently explained anywhere on the report.
- **`Vendors Missing From ERP` = 125 of 251.** Half the vendor master is unmatched.
- **`Expired Certificates` = 105 of 105.** See above.
- **`Report Month Label` = "January 2015 – December 2035"** with no slicer applied. Correct
  behaviour, but it looks broken on first load — the month slicer defaults to everything.

---

## Deploying

The full sequence, in order. This is what was run on 2026-08-02:

```bash
python foundation/charley-dev/_local/run_tests.py                        # 12 suites offline
python foundation/charley-dev/_local/deploy_gold.py --source cd --apply  # rebuild gold
python foundation/charley-dev/_local/validate_model.py                   # reframe + 17 DAX checks
```

Then re-run `cd_40_dq_checks` to refresh the gate and heartbeat.

**`--source cd` is not optional.** `deploy_gold.py` defaults to `--source existing`, and a
bare `--apply` silently reverts gold to reading the legacy `Silver_Lakehouse` instead of our
own medallion. **That default should be changed** — it is the easiest way to quietly undo
the source migration.

Confirm any gold rebuild landed:

```
EVALUATE ROW("Current", [Current Contract], "Growth", [Contract Growth %])
```

Expect ≈ $35,102,931 and ≈ 16%. If it reads $30,254,551 and 0.00%, the change-order
regression is back.

---

## External blockers, unchanged

| Blocker | Effect | Owner |
|---|---|---|
| No Azure subscription → no Key Vault | Procore extraction runs on a laptop and lands files. **The nightly pipeline does not call the Procore API** — it re-processes whatever was last landed. Landing files were last written 04:44 on 2026-08-02 | Affect |
| `OUTBUILD_API_TOKEN` not issued | No milestones for 17 of 19 projects. Outbuild is the only source | Affect / Outbuild CS |
| On-prem gateway for Sage | `CD_Sage_Ingest` is defined in the repo but **not deployed** | Affect |
| SharePoint decision | Nine `man_*` tables are deployed and empty; ~40% of the report | Affect |

---

## Recommended order

1. ~~Deploy the change-order fix.~~ **Done** — deployed and verified 2026-08-02 22:56.
2. Fix the DQ persist gap: create `cd_dq_results`, move `_persist_rejects` out of the shared
   `try`, and put the persist outcome on the heartbeat. Until then a green gate does not
   mean the Data Quality page is current.
3. Merge `worktree-charley-dev-build` → `main`. The default branch is still 9 commits behind
   what is deployed, and does not contain this fix.
4. Change `deploy_gold.py`'s default to `cd`, so a bare `--apply` cannot regress the source.
5. Chase the Outbuild token. It is the largest single coverage gain available — 17 of 19
   projects have no milestones.
6. Put the insurance finding in front of Affect as a question, not a metric.
