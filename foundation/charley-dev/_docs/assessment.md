# Full assessment — 2026-08-02, blockers re-checked 2026-08-19

An independent read of everything in `charley-dev`: what is built, whether it is actually
live in Fabric, whether the numbers on the dashboard are right, and what is left.

**Refreshed 2026-08-19.** The audit of the build stands as written; the *external blocker*
picture underneath it has changed and is corrected throughout. An Azure subscription and a
Key Vault now exist, and `CD_Sage_Ingest` is deployed. Row counts, measure values and the
defect analysis are unchanged from the 2026-08-02 measurement.

**Also 2026-08-19: the PQP subject area shipped**, taking the folder to **20 items** — a
second semantic model and a second report over the same gold lakehouse. Three of this
document's own recommendations were closed at the same time: `deploy_gold.py`'s default is
now `cd` (#4), the SharePoint list-name mismatch is fixed at the source (#7), and the branch
consolidation (#3) was done on 2026-08-03. See [`pqp-solution.md`](pqp-solution.md) and
[`build-status.md`](build-status.md).

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
| Repo ↔ GitHub | `git` against `origin` | Consolidated onto `main` 2026-08-03 |
| Items deployed | `list_items` / `list_folders` on workspace `Build` | 13 of 14 at this audit; **20 items** on the 2026-08-19 re-read, after the PQP model and report |
| Bronze / silver / gold populated | `execute_sql_query` row counts | Populated, verified |
| Gold ↔ repo SQL | Table list vs `sql/gold/*.sql` | Matches |
| Semantic model ↔ repo | Deployed TMSL vs `*.tmdl` | Matches — 37 tables |
| Pipeline DAG ↔ repo | `get_pipeline_definition` vs `pipeline-content.json` | **Identical** |
| Which silver feeds gold | Lakehouse GUIDs in deployed notebook | `cd` source, as intended |
| Measures compute | All 99 evaluated via `execute_dax_query` | All evaluate |
| Numbers are *correct* | Recomputed independently in SQL | **One defect found** |
| Pipeline freshness | `meta_PipelineRun` | Ran 2026-08-02 22:06, 0 blocking |
| DQ gate | `cd_dq_rejects` + heartbeat | 63 expectations at this audit, 6 failing, 0 blocking. The suite is now **104** (81 blocking, 23 warning) |

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

## Are we pulling from Sage? No. Here is exactly what feeds the dashboard

This is the question to be clear about before the Affect call, because the honest answer has
two halves: **Sage data is on the dashboard, and we are not the ones pulling it.**

| Source | Who pulls it | Into | Latest data | Ours? |
|---|---|---|---|---|
| **Procore** | **us** — the endpoint registry (42 at this audit, 44 since the PQP work), run locally, landed as NDJSON | `CD_Bronze` → `CD_Silver` | 2026-08-02 04:44 | **yes** |
| **Sage 100** | Rebecca's `Build_Sage_Test` dataflow | existing `Silver_Lakehouse` | invoice **2026-07-31** (re-measured 2026-08-19; was 2026-07-20 on 2026-08-02) | no |
| **Outbuild** | Rebecca's `Outbuild_activities` dataflow | existing `Silver_Lakehouse` | updated 2026-07-14 *(as measured 2026-08-02, not re-verified)* | no |

`01_source_views_cd.sql` points 18 of its views at our own `CD_Silver` and leaves 8 reading
the existing warehouse — deliberately, per-view rather than all-or-nothing, because a view
pointing at the old source is a smaller problem than one pointing at an empty new one. The
three that matter:

- `sv_ar_invoices` → Sage AR. **All 122 rows of `fct_Invoice` come from here.**
- `sv_outbuild_activities` → Outbuild. **All 52 rows of `fct_Milestone` come from here.**
- `sv_vendors` → carries `sage_vendor_id`, which Procore does not put on a vendor record.

**So if Rebecca's dataflows stop, our dashboard's financial and schedule data stops with
them** — and it would not error, it would just quietly stop moving. Nothing currently alerts
on that. Sage is running **~19 days behind** as re-measured on 2026-08-19: max `SentDate`
reached **2026-07-31**, up from the **2026-07-20** recorded on 2026-08-02, so her feed did
refresh at some point in between rather than stopping dead in July. The Outbuild figure of
**2026-07-14** is as measured on 2026-08-02 and has **not been re-verified since** —
`fct_Milestone` is unchanged at 52 rows, and the only date the table carries
(`CurrentFinish`, max 2026-11-09) is a *forecast* finish and says nothing about freshness.
Lag rather than a dead feed, but the concern stands, and it is still a reason to fix the
gateway.

**How we noticed:** `validate_model.py` asserts *exact* row counts against this live external
source. `[Invoices]` failed at 117 when the model returned 122, and `[Periods]` moved 130 →
142 alongside it — `Periods` is derived from the fact date range, so eleven more days of Sage
AR widened it by twelve project-months. Both expectations are updated. Asserting an exact
count against somebody else's warehouse is fragile by design — it moves whenever Rebecca's
dataflow runs — and that fragility is exactly what surfaced the change; nothing else would
have.

There is also not much of it. 122 revenue invoices and **13 open AR rows** for a $35M
portfolio is thin — worth asking Affect whether that is the real shape of their AR or whether
the existing dataflow is filtering most of it away. It does filter: `Invoice Balance <> 0`.

### What Sage actually needs — and it is not Key Vault

**There is no hard-coded Sage credential to find.** Sage 100 is on-premises; the dataflow
connects via `Sql.Database("NC-AFFECT-1\SAGE100CON", "Affect Group")` through the
**on-premises data gateway**, and the credential lives in the gateway's connection
configuration, not in any notebook. That is the correct design, and it is recorded as F3 in
[`security-findings.md`](security-findings.md).

The one hard-coded credential in the estate is **Procore** (F1, in the live `procore_auth`
notebook) — and that path is already in use: extraction runs locally with it and lands files.
Procore data is flowing today because of it.

Which means:

> **Sage is not blocked on the Azure subscription or on Key Vault.** It is blocked on
> permission to bind `CD_Sage_Ingest` to a gateway connection that **already exists and
> already works**, because `Build_Sage_Test` uses it every time it runs.

### Deployed 2026-08-03, and the blocker is now one line

`CD_Sage_Ingest` is **live in the `charley-dev` folder** (`9d1dc6db-…`), wired to gateway
`1e798beb` and datasource `835e72c8`, writing to `CD_Bronze`. The definition reads back from
Fabric exactly as committed — gateway, both connections, all 8 queries, `DefaultDestination`.

The first run **failed in 5 seconds**, which is too fast to be a query. The cause is not our
code:

| Call as `cforey-c@affect-group.com` | Result |
|---|---|
| `GET /v1/gateways` | `{"value": []}` |
| `GET /v1/connections` | `{"value": []}` |
| `GET /v1/gateways/1e798beb-…` | **404 `EntityNotFound`** |

The gateway demonstrably exists — `Build_Sage_Test` references it — but **this identity
cannot see any gateway or connection in the tenant.** The dataflow asks to run through a
gateway its runner has no rights on, and fails before reaching Sage.

**The ask, precisely:** whoever administers the on-premises data gateway grants
`cforey-c@affect-group.com` the **"Can use"** permission on the connection
`nc-affect-1\sage100con;Affect Group`. That is a single grant in *Manage connections and
gateways*. No subscription, no vault, no code change — the dataflow runs the moment it lands.

Leaving the failed dataflow deployed is deliberate: it is correct, it is inert until run,
and it turns the remaining work into one permission grant plus one refresh.

**Worth raising on the same call:** Rebecca's Sage data reached 2026-07-31 when re-measured
on 2026-08-19 — it moved on from the 2026-07-20 recorded on 2026-08-02, so it is lagging
~19 days rather than dead. Outbuild's 2026-07-14 is as measured on 2026-08-02 and has not
been re-verified. If those dataflows are lagging on the same gateway, the existing reporting
is quietly running on numbers nearly three weeks old.

Key Vault is needed to move *Procore* extraction off a laptop and into Fabric. Sage needs a
connection binding. They are separate asks with separate owners, and conflating them has been
costing us the one that could have been done weeks ago.

**Outbuild was the genuine blocker** — `OUTBUILD_API_TOKEN` had never been issued and no
workaround exists. As of Aug 11 Rebecca has offered to send it by email, so it is now
pending a transfer rather than a decision. It remains the highest-value gap until it
arrives: 17 of 19 projects have no milestones, and Outbuild is the only milestone source
anywhere.

### What to ask for on the call

1. **Bind `CD_Sage_Ingest` to the existing gateway connection.** Needs someone with
   permission on that connection — not a subscription. This is the single highest-value ask
   and it can be done the same day.
2. **Send `OUTBUILD_API_TOKEN`.** Offered by email Aug 11 and still to arrive. Unblocks
   milestones for 17 projects.
3. **Grant Key Vault Secrets Officer on vault `OneLake`** to `cforey-c@affect-group.com`.
   The subscription and the vault both exist as of 2026-08-19; the vault is RBAC-mode and
   Contributor on the resource group cannot read or write a secret. One role assignment.
4. **Rotate the Procore credential** (F1), then edit the notebook — in that order. Rotation
   should not wait for the vault: the old pair has been readable by anyone with Viewer on
   the workspace, so editing the literal out first changes nothing about the exposure.
5. Confirm the gateway account is **read-only** on the Sage database.
6. Ask whether 13 open AR rows is real, or a filter artefact.

---

## Every field on the report resolves — now

The Project Detail page rendered "There's something wrong with one or more fields". One
visual, two broken references: `fct_ChangeOrder[Status]` (the column has always been
`StatusLabel`) and `[Approved Change Orders]`, a measure the table asked for by name that had
never been written.

Neither failed the deploy, the refresh, or any log. **A visual bound to a name the model does
not have is invisible to everything except a person looking at that page.** Both are fixed,
and `test_report.py` now resolves all 138 field references against the model offline, so this
class of defect cannot reach the report again.

If a page still looks wrong, it is almost certainly the *other* failure mode — a measure that
resolves fine and returns BLANK because its source data does not exist. Those are listed
under *Scorecard coverage* and *Data quality* below, and they are access problems, not bugs.

---

## Source control: consolidated — `main` is the only branch

Resolved 2026-08-03. Everything is on `main`; the feature branches are gone.

| Was | Now |
|---|---|
| `origin/main` missing 8 commits of Power BI work | contains everything, PRs #8–#12 merged |
| `origin/worktree-charley-dev-build` | **deleted** — fully merged |
| `origin/worktree-pbi-enhance` | **deleted** — fully merged |
| local `main`, 39 behind | fast-forwarded to `origin/main` |

The two branches were deleted with `git branch -d`, which refuses on anything unmerged, and
each key commit was confirmed reachable from `main` first. The only commits **not** in
`main` were the merge commits of PRs #10 and #11 — those merged into
`worktree-charley-dev-build`, and their content reached `main` by a different route via
PR #12. The only content unique to that branch was the *older, broken* state: the unbound
Sage dataflow (`"connections": []`) and the `fct_ChangeOrder[Status]` reference that had
never resolved. Nothing of value was lost.

Three orphaned worktree directories remain under `.claude/worktrees/` (`pbi-enhance`,
`cathal-scope-call`, `outbuild-api-docs`). Git no longer tracks them — Windows file locks
prevented deletion. They are inert; remove them by hand whenever convenient.

---

## Repo ↔ Fabric parity, verified 2026-08-03

Every item `main` defines, checked against the live workspace after consolidation.

| Item | In `main` | In Fabric | Verified by |
|---|---|---|---|
| `CD_Bronze` / `CD_Silver` / `CD_Gold` | yes | yes | `deploy.py --verify`, schema `dbo` |
| 8 notebooks (`cd_01`…`cd_90`) | yes | yes | `deploy.py --verify` |
| `CD_Master_Pipeline` | yes | yes | DAG compared activity-for-activity |
| `CD_Sage_Ingest` | yes | yes | deployed; **run blocked on gateway permission** |
| `Affect Project Report` model | yes | yes | 37 tables, **100 measures**, 45 relationships |
| `Monthly Progress Report` | yes | yes | 12 pages, 180 visuals, all 138 refs resolve |
| `Project Quality Plan` model | yes | yes | added 2026-08-19 — 19 tables plus `_Measures`, 42 measures, 23 relationships |
| `Project Quality Plan` report | yes | yes | added 2026-08-19 — 7 pages, 95 visuals |
| `CD_Manual_Ingest` | yes | **no** | deliberate — see below |

The semantic model was compared name-by-name against `deploy_model.MEASURES`: **zero drift
in either direction.** Not "the counts match" — the actual sets are identical, so a measure
renamed on one side would show up.

`CD_Manual_Ingest` is **correctly not deployed.** Its mashup carries
`SITE = "https://REPLACE-ME.sharepoint.com/..."`, so deploying it would create an item that
cannot run and would sit in the workspace looking like working ingestion. It goes in once
the SharePoint site exists and the URL is real.

**Verification run:** 13 offline suites and 17 live DAX checks, all passing, including
`[Current Contract] is a balance, not a running total of months` — the assertion that guards
the $4.85M defect. The offline suite is now **14** (`test_qc.py` added with the PQP work).

---

## Data quality: 6 failing expectations, 0 blocking

The gate is working as designed — these fail loudly and let the run through, which is
correct for coverage gaps as opposed to corruption.

| Expectation | Rows | Meaning |
|---|---:|---|
| cost codes parse to a CSI division | 1,000 | Procore free-text codes (`FINAL CLEAN`, `CONTINGENCY`); cannot roll up by division |
| every project is in Outbuild | 17 of 19 | No `OUTBUILD_API_TOKEN`. Outbuild is the **only** milestone source |
| every project is in Sage | 4 | 2 are test/template projects; 2 are real and read as zero revenue |

> **Superseded 2026-08-19 for the first row.** The cost-code explanation above was wrong, and
> in the direction that mattered: the codes were not Procore free text. Our parser required a
> two-digit CSI division and Affect writes divisions 1–9 **without** the leading zero, so
> `1-1000 GENERAL REQUIREMENTS` — Division **01** — read as unparseable. Of the 807 flagged at
> the 2026-08-19 re-read, **all 807 were fixable and none was genuinely malformed**; the
> expectation now returns **0**. This is the shape worth remembering: a data-quality finding
> that was our code being wrong about the client's conventions. See
> [`build-status.md`](build-status.md).

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

## Scorecard coverage

**59%** — the canonical figure and its history live in
[`build-status.md`](build-status.md); this section explains *why*. Four of nine categories
cannot be scored, and all four are blocked on data rather than code:

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
python foundation/charley-dev/_local/run_tests.py                        # 14 suites offline
python foundation/charley-dev/_local/deploy_gold.py --apply              # rebuild gold
python foundation/charley-dev/_local/validate_model.py                   # reframe + 17 DAX checks
```

Then re-run `cd_40_dq_checks` to refresh the gate and heartbeat. The full sequence, including
the **`deploy_manual.py` before `deploy_silver.py`** ordering, is in
[`build-status.md`](build-status.md#how-to-run-it).

**The `--source existing` foot-gun is closed.** `deploy_gold.py` used to default to
`--source existing`, so a bare `--apply` silently reverted gold to reading the legacy
`Silver_Lakehouse` instead of our own medallion — recommendation 4 below. `DEFAULT_SOURCE` is
now `cd`. Passing `--source cd` explicitly still works and is now redundant rather than
mandatory.

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
| **Key Vault role assignment** — the vault exists (`OneLake`, RG `Affect_KeyVault`) but is RBAC-mode and `cforey-c@affect-group.com` has only Contributor on the resource group, which cannot read or write secrets | Procore extraction runs on a laptop and lands files. **The nightly pipeline does not call the Procore API** — it re-processes whatever was last landed. Landing files were last written 04:44 on 2026-08-02. The ask is one role: **Key Vault Secrets Officer on vault `OneLake`** | Affect |
| On-prem gateway grant for Sage | `CD_Sage_Ingest` is **deployed** and inert — one *Can use* grant on `nc-affect-1\sage100con;Affect Group` away from running | Affect / their Sage consultant |
| Procore 403s on `punch_item_types` and `schedule` | Two report sections cannot be sourced | Affect |
| SharePoint decision | **17** `man_*` tables are deployed and empty (9 original plus 8 PQP registers); ~40% of the Monthly Progress Report and most of the Project Quality Plan. The CSV path in `Files/_manual/` works today, so this gates the *team* mechanism, not data entry | Affect |
| ~~No Azure subscription~~ | **RESOLVED 2026-08-19** — "Azure subscription 1" `0bee26ab-eeb7-4dc9-ab92-fb46d068f6b6` on tenant "Affect Build LLC" `b2a2225b-4b4e-42ec-ba52-c7e1c2dea580` | — |
| ~~`OUTBUILD_API_TOKEN` not issued~~ | **In transit** — Rebecca offered to send the token by email on Aug 11. Once it lands, milestones for 17 of 19 projects follow | Affect (in transit) |

---

## Recommended order

0. **Bind `CD_Sage_Ingest` to the existing gateway connection.** Highest value, needs no
   subscription, and can be done the day someone with connection permission says yes.
1. ~~Deploy the change-order fix.~~ **Done** — deployed and verified 2026-08-02 22:56.
1b. ~~Fix the two broken fields on Project Detail.~~ **Done** — deployed, and all 138 report
   field references are now checked offline on every run.
2. Fix the DQ persist gap: create `cd_dq_results`, move `_persist_rejects` out of the shared
   `try`, and put the persist outcome on the heartbeat. Until then a green gate does not
   mean the Data Quality page is current.
3. Merge `worktree-charley-dev-build` → `main`. The default branch is still 9 commits behind
   what is deployed, and does not contain this fix.
4. ~~Change `deploy_gold.py`'s default to `cd`, so a bare `--apply` cannot regress the
   source.~~ **Done 2026-08-19** — `DEFAULT_SOURCE = "cd"`.
5. Chase the Outbuild token to completion. Offered Aug 11, not yet received. It is the
   largest single coverage gain available — 17 of 19 projects have no milestones.
6. Put the insurance finding in front of Affect as a question, not a metric.
7. ~~**Fix the SharePoint list-name mismatch** before anyone runs the provisioning script.~~
   **Done 2026-08-19, at the source.** `_local/make_sharepoint.py` now generates the PS1, the
   mashup, `queryMetadata.json` and `deploy_manual.LISTS` from the `man_*` gold DDL, so one
   function decides a list name and `test_sharepoint.py` fails the build if the four writers
   drift. Detail in [`sharepoint-lists.md`](sharepoint-lists.md).

8. ~~**Ask Affect for the Procore trade → workbook `TradeKey` alias mapping.**~~ **Largely done
   2026-08-19.** `qc_seed_TradeAlias` (16 unambiguous pairs) recovered 464 rows: unmapped NCRs
   **459 → 215**, punch items **511 → 291**. Two narrower things still need Affect — three
   ambiguous labels (`Drywall/Carpentry` 255, `Concrete Superstructure` 110, `Concrete` 64), and
   a **scope** question rather than a mapping one: Roofing, Glazing, Windows, Structural Steel,
   Low Voltage and others have no equivalent trade in the 26-sheet library at all. See
   [`build-status.md`](build-status.md).

9. **Add `cd_06_land_manual` to `CD_Master_Pipeline`,** ahead of `Bronze To Silver`. The
   nightly run currently rebuilds silver and gold without refreshing manual bronze — harmless
   while every `man_*` table is empty, a staleness bug the day somebody enters a row.
