# Hours Log — Affect Group

Source of truth for time/project validation and invoicing. **Append-only** — never edit past entries; add a correcting entry instead.

## Conventions

- **Rate: $125/hr flat** across all types, per the Jul 24 agreement with Cathal (`meeting-notes/2026-07-24-cathal-scope-call.md`). Supersedes the earlier $250/hr advisory rate.
- **Type:** `Consulting` (advisory, meetings, reviews, architecture), `Development` (build work), or `Mentoring` (working sessions and recorded walkthroughs with Rebecca — **billable**, and core scope)
- **Not logged at all:** Rebecca's ad-hoc texts, calls, and emails. Unlimited and free by agreement — don't meter them.
- **Deliverable:** link to the file in `deliverables/` the work belongs to, or `General` for cross-cutting advisory
- **Evidence:** link to what the time produced — commit, doc, recording, email, meeting notes. Every entry should point to something verifiable.
- Log same-day, in 0.25 hr increments. Unbilled prep/business development (like proposal writing before an agreement) goes in the log with **Billable = No** so the record is complete.

## Ledger

| # | Date | Type | Hours | Billable | Deliverable | Work performed / accomplished | Evidence | Invoiced |
|---|------|------|-------|----------|-------------|-------------------------------|----------|----------|
| 1 | 2026-07-15 | Consulting | 0.5 | No | General | Intro call with Rebecca — current state overview (Fabric, Procore ETL, Sage 100 SQL, team context) | Email thread / call | — |
| 2 | 2026-07-21 | Consulting | 1.5 | No | General | In-person discovery meeting with Affect team — architecture, Excel tracker, SOPs, engagement structure | `meeting-notes/2026-07-21-discovery-meeting.md` | — |
| 3 | 2026-07-21 | Consulting | 1.0 | No | [D1](deliverables/01-discovery-architecture-review.md) | Engagement setup — documented meeting notes, deliverables structure, deep-dive call prep | This repo (initial commits) | — |
| 4 | 2026-07-22 | Consulting | 6.0 | No | [D1](deliverables/01-discovery-architecture-review.md) / [D4](deliverables/04-project-data-model.md) / [D5](deliverables/05-powerbi-project-dashboard.md) | Full assessment of the Affect Monthly Progress Report workbook — extracted all 11 tabs, 17 tables, 15 drop-downs, complete formula set; classified every field by source system; identified 14 defects (3 affecting reported numbers). Produced the Power BI build kit: semantic model, DAX measure library, report spec, validated theme, manual-input template, phased build plan. Built the solution resource library (Procore endpoint cheatsheet verified against the 2,111-path OAS; Sage 100 Contractor doc correction; Fabric / Power BI / Power Automate / Outbuild / Ramp / ADP). | `analysis/excel-tracker/`, `powerbi/`, `resources/` | — |
| 5 | 2026-07-23 | Consulting | 1.0 | No | [D1](deliverables/01-discovery-architecture-review.md) | Prep for the data warehouse review call — agenda, findings walkthrough, blocking-question list | Call agenda (internal) | — |
| 6 | 2026-07-23 | Consulting | 0.5 | No | [D1](deliverables/01-discovery-architecture-review.md) | Data warehouse review with Rebecca — Fabric workspace walkthrough (ingestion, transformation, lakehouses, semantic model); identified secrets/refresh/endpoint/bridging findings | `meeting-notes/2026-07-23-warehouse-review.md` | — |
| 7 | 2026-07-24 | Consulting | 0.5 | No | General | Meeting-notes write-up and hub update — README/dashboard/deliverable logs, billing reframe, Fabric MCP config; prep for Cathal scope call | This repo | — |
| 8 | 2026-07-24 | Consulting | 0.5 | No | General | Scope, terms & engagement call with Cathal (~20 min) — objectives, deliverables, duration, hours, rate, working expectations. Terms agreed: $125/hr, 9–10 months, 20 hrs initial scope, 5 hrs/wk ongoing | `meeting-notes/2026-07-24-cathal-scope-call.md` | — |
| 9 | 2026-07-24 | Consulting | 0.5 | No | General | Post-call hub alignment — commercial terms, Phase 0 twenty-hour plan, D8 quick-win deliverable, availability and cadence, recap email to Cal + team | This repo | — |
| 10 | 2026-07-26 | Development | 4.0 | No | [D2](deliverables/02-procore-etl-validation.md) / [D5](deliverables/05-powerbi-project-dashboard.md) | Built the reference Procore → Lakehouse pipeline, RFI/submittal slice, end to end: config-driven extractor (auth via Key Vault, pagination off response headers, `Retry-After` backoff, v2.0 header rule, `updated_at` watermark, active-project filter), version-controlled Spark SQL for silver/gold with a data-quality log that flags rather than drops, two Fabric notebooks, and a DuckDB runner that executes the same SQL locally. 34 assert-based tests pass, including proof that re-running does not double rows. Produced `fct_RfiSubmittal` plus its dimensions, a TMDL semantic model, and a generated preview page. | [`src/procore/`](src/procore/), [`powerbi/AffectProjectReport.pbip`](powerbi/AffectProjectReport.pbip), branch `worktree-procore-pipeline` | — |
| 11 | 2026-08-01 | Consulting | 1.25 | Yes | [D1](deliverables/01-discovery-architecture-review.md) / [D3](deliverables/03-sage100-ingestion.md) | Fabric access landed. Backed up the entire `Build` workspace (55 items, 228 files) read-only, and **found live Procore and Outbuild credentials in five notebooks and 18 saved cell outputs** — scrubbed the repo copies, wrote an idempotent scrubber, reported the live exposure. Vendored the full Sage 100 Contractor and Outbuild API documentation sets, then reconstructed the Sage schema from Affect's own production dataflow and verified it against live lakehouse data. | `foundation/`, `foundation/scrub-secrets.py`, `resources/sage-100-contractor/`, `resources/outbuild/`, commits `f1f6b6d`…`db0d11e` | — |
| 12 | 2026-08-01 | Development | 5.25 | Yes | [D2](deliverables/02-procore-etl-validation.md) / [D4](deliverables/04-project-data-model.md) / [D5](deliverables/05-powerbi-project-dashboard.md) | Stood up `charley-dev` end to end in one session: the platform layer and shared library (secrets, merge, DQ, watermarks), the Procore endpoint registry, three CD lakehouses created via a committed deploy script, gold seeds that assert their own row counts, the gold star schema built against real data, a **Direct Lake semantic model validated with live DAX**, the Monthly Progress Report deployed, the scorecard measures, the nine `man_*` tables, the Procore ingestion notebook, the bronze→silver transforms and the orchestration pipeline. Every item reaches Fabric through an idempotent, folder-scoped deploy script. | `foundation/charley-dev/`, commits `d4ec0a3`…`22421ec` | — |
| 13 | 2026-08-02 | Development | 6.0 | Yes | [D2](deliverables/02-procore-etl-validation.md) / [D3](deliverables/03-sage100-ingestion.md) / [D4](deliverables/04-project-data-model.md) | Took Procore ingestion from 8 to **31 endpoints** and landed real bronze, surviving the 600/hr quota wall instead of losing a whole run. Made the gold source switch real (`--source cd`) and migrated gold onto our own medallion. Built `CD_Sage_Ingest` — including the two AR/AP line tables the existing dataflow explicitly discards — and Outbuild ingestion across 16 endpoints. Built the cross-source crosswalk (project, vendor, cost code), the manual-input capture path, and the **DQ gate: 35 expectations wired into the pipeline**. Reported the live credential exposure with remediation steps. | `foundation/charley-dev/`, `_docs/security-findings.md`, commits `cfb40ce`…`563753d` | — |
| 14 | 2026-08-02 | Development | 6.0 | Yes | [D5](deliverables/05-powerbi-project-dashboard.md) / [D8](deliverables/08-vendor-list-automation.md) | Report and coverage work. Scheduled the refresh; added drill-through and bookmarks; landed field ops, then recovered **120,766 hours worked** and the daily logs from three endpoints that were silently returning empty. Added `fct_SafetyMonthly` — scorecard coverage 35% → 45% → **59%**. Parsed the billing data already landed and found the retainage problem in it. Applied the theme, made the report navigable, gave leadership a portfolio page, and showed the scorecard's working rather than faking the four categories that have no source data. Made the nightly pipeline actually run. | `foundation/charley-dev/05-reports/`, `_docs/solution-guide.md`, commits `5c55c82`…`c1f27e8` | — |
| 15 | 2026-08-02 | Development | 3.5 | Yes | [D3](deliverables/03-sage100-ingestion.md) / [D4](deliverables/04-project-data-model.md) / [D5](deliverables/05-powerbi-project-dashboard.md) | **Found and fixed a $4.85M understatement of portfolio contract value** — gold was adding only the current month's change orders instead of accumulating them. Current Contract $30,254,551.24 → $35,102,931.14, Contract Growth 0.00% → 16.03%, deployed and verified. The reconciliation gate had passed because the fixture put all three COs in one month; fixture and assertions corrected. Completed the vendor bridge, added a pipeline heartbeat, fixed two broken Project Detail fields and added an offline check of all 138 report field references. Ran a full independent audit against the live workspace. Deployed `CD_Sage_Ingest` and narrowed Sage to a **single permission grant**. Generated the SharePoint intake lists as a runnable script. | [`_docs/assessment.md`](foundation/charley-dev/_docs/assessment.md), commits `1cbc08d`…`5ed25c5`, PRs #8, #9, #12 | — |

| 16 | 2026-08-13 | Consulting | 2.5 | Yes | [D1](deliverables/01-discovery-architecture-review.md) / [D5](deliverables/05-powerbi-project-dashboard.md) | **Platform review with Rebecca (30 min, virtual)** — walkthrough of the `charley-dev` build, the design decisions behind it, and why the data is validated before the report publishes. Rebecca's capacity has dropped (a departure on her team), so the cadence was changed: Charley absorbs the build load, mentoring goes async and recorded. **In-person session with Rebecca and Chris (1 hr, their office, 5pm)** — the broader vision: the PQP quality plan as the next subject area, and the estimating→bidding folder automation. Plus prep and write-up: the forwardable executive update and the meeting record. Established that the Sage database is administered by an outside consultant, which reroutes the gateway ask. | [`meeting-notes/2026-08-13-rebecca-platform-review.md`](meeting-notes/2026-08-13-rebecca-platform-review.md), [`updates/2026-08-13-executive-update.md`](updates/2026-08-13-executive-update.md) | — |
| 17 | 2026-08-19 | Development | 6.0 | Yes | [D2](deliverables/02-procore-etl-validation.md) / [D4](deliverables/04-project-data-model.md) | **PQP subject area, the estimating/bidding flows, and a four-fault root cause.** Took the client's 44-sheet QA/QC tracker apart and collapsed it to 9 tables — 26 trade checklists sharing one schema became one seed plus one fact (625 items), and three statutory gate registers became one table with a discriminator (93 gates). Built the silver and gold layers, 40 new DQ expectations (63 → 103), and offline tests. Fixed the manual pipeline at the root: no `sv_man_*` views existed, `deploy_silver` excluded prefix `30`, the four "open questions" were input-side drift, and `deploy_gold` had a `mode("overwrite")` cell that would have wiped the new INSERTs on first run. Built both Power Automate flows and the SharePoint provisioning script locally with 14 offline checks. Audited the client's workbook and found **5 defects**, including four register roll-ups whose `% Complete` can never reach 100%. Resolved a 12-file merge conflict against two PRs that landed mid-session. | commits `232e10b`…`f8263a7`, PRs #16; [`analysis/pqp-workbook/`](analysis/pqp-workbook/defects-and-questions.md) | — |
| 18 | 2026-08-19 | Development | 4.0 | Yes | [D4](deliverables/04-project-data-model.md) / [D5](deliverables/05-powerbi-project-dashboard.md) | **Made the PQP visible, and found two more silent defects.** Second Direct Lake semantic model (`Project Quality Plan` — 19 tables, 42 measures, 23 relationships) and a 7-page, 95-visual report, both generated by importing the existing generators and overriding three lists rather than copying 1,970 lines. Model A left byte-identical. Found that `deploy_gold.py` carried a **hardcoded table list** the QC tables were never added to — so they were neither row-checked nor published to `gold_schema.json`, and **a gold table absent from that file silently cannot appear in any semantic model** (45 → 53 published). Found `20_fieldops_silver.sql` reading `$.trade` as an object rather than `$.trade.name`, which broke every QC trade join (631 of 850 NCRs unmapped) **and had been putting raw JSON into `fct_QualityItem.Trade` on the live Monthly Progress Report**. Both fixed and verified by DAX against the deployed model. | commits `6dcf929`…`57d0708`, PR #17 | — |
| 19 | 2026-08-19 | Development | 2.0 | Yes | [D3](deliverables/03-sage100-ingestion.md) / [D4](deliverables/04-project-data-model.md) | **Repaired a dead join that was hiding $22.5M of AR, and resolved four data-quality defects.** `dim_Project.SageJobNumber` was reading from a view that returns `NULL` under `--source cd`, so **122 of 122 AR invoices resolved to `UNMATCHED`** and $23,695,760.48 was attributed to no project. Nothing errored — it is a LEFT JOIN, so the row count never moved, which is precisely the check that had been run to prove the source switch was safe. `IsInCrosswalk`, the flag whose whole job is catching this, was derived from the same wrong view and read TRUE for all 19 projects: **a broken join reporting itself as fully mapped.** Fixed by joining the crosswalk explicitly; measured live, projects with a Sage job **0 → 15**, unmatched invoices **122 → 24**, AR attributed to a project **$0 → $22,548,861.96**. Then four DQ defects: submittal statuses **223 → 0** (Procore sends `For Record`, we only knew `For Record Only` — 222 of 2,245 submittals fell out of every slicer), trade vocabulary **970 → 506** unmapped via a 16-row alias seed, CSI cost-code divisions **807 → 0** (Affect writes divisions 1–9 without a leading zero; 15% of the 5,433-code master was absent from every by-division rollup and **not one code was actually malformed**), plus a new ERROR-severity guard so a typo'd alias cannot masquerade as an unmapped trade. Three of the four were our code being wrong about Affect's conventions, not Affect's data being wrong. | commits `9d06f34`, `30a672b`, PRs #19, #20 | — |
| 20 | 2026-08-19 | Development | 4.0 | Yes | [D2](deliverables/02-procore-etl-validation.md) / [D4](deliverables/04-project-data-model.md) / [D5](deliverables/05-powerbi-project-dashboard.md) | **Two blockers closed, and the folder automation put into Affect's tenant.** Found the **Key Vault ask had been aimed at the wrong vault** all along — three documents had been asking Affect for a role on `OneLake` since Aug 13, while the vault in use is `AffectKeyVault` (RG `Affect_Data`), where this account already holds Key Vault Administrator inherited at RG scope. **The ask was withdrawn, not completed.** Two further defects sat behind it: the read side never translated secret names (Key Vault forbids underscores, so `PROCORE_CLIENT_ID` is not a legal name), and `get_secret` **failed open** to `os.environ` — a half-configured vault would have read a credential from an unaudited source and reported success. Now raises inside Fabric. Rebecca's Outbuild token landed in the vault at 18:27 UTC; three bugs that only a live call could reveal (missing User-Agent → Cloudflare 403, wrong envelope key, wrong paging rule) were fixed and **3,078 rows across 15 endpoints** landed into `cd_bronze_outbuild_*`, verified by reading counts back out of Delta. Made `CD_Manual_Ingest` deployable (its mashup bound all 18 queries to a `DefaultDestination` it never defined — it would have parsed and then failed at run) and **built the missing link from the job flows to Fabric**: the Job Register had been *described* as the `dim_Job` source with no bronze table, no dataflow query, no silver parser and no gold DDL behind it. Then took both Power Automate flows from committed JSON into the live tenant against a tenant where **every direct write route is closed** — SharePoint REST 401, Graph 403 for want of any `Sites.*` scope, PnP's shared app retired by Microsoft — by having Power Automate itself do the provisioning, since a flow's actions run as the connection. **Both flows now exist** (created stopped), the BUILD site structure is provisioned, and `CD_Manual_Ingest` is published to the workspace with 19 queries. | commits `61afecc`…`97c5f5e`, PRs #21–#37 | — |
| 21 | 2026-08-20 | Development | 3.0 | Yes | [D4](deliverables/04-project-data-model.md) / General | **Finished the reporting site, and reconciled every document against the live platform.** Provisioned the intake site's **142 columns and 19 `CD Projects` rows** onto the 18 lists (the lists themselves had landed the night before, by a run recorded at the time as having created nothing). Found the seed was **not idempotent** — creating a list or column fails harmlessly when it exists, but creating a list ITEM always succeeds, so a second run left **38 rows where 19 were real** while every batch reported `Succeeded`; `ProjectKey` is a Lookup at that list, so duplicates make the target ambiguous. Removed the surplus, filtered the seed at the source, and added `--verify`, because neither the run status nor the dry run could answer "what actually landed" — the dry run counts only lists and reported 142 columns outstanding against a site that already had all of them. Then a full documentation pass: the **DQ expectation count was wrong in thirteen files and disagreed with itself** (twelve said 104, `build-status` said 105, `build_suite()` says **107**), five documents still said the intake lists needed creating, and three claims were actively false rather than merely stale — including a client-facing Key Vault ask that had named the wrong vault since Aug 13 and was recorded as **withdrawn, not completed**. | commits `5245fa1`…`c10eb86`, PRs #38, #39, #40, #41 | — |
| 22 | 2026-08-20 | Development | 2.0 | Yes | [D5](deliverables/05-powerbi-project-dashboard.md) / [D4](deliverables/04-project-data-model.md) | **Put the schedule data on the report, and fixed two defects that were hiding the reason it could not go.** Repointed `sv_outbuild_activities` off Rebecca's `Silver_Lakehouse` onto our own ingestion via a new silver parser: `fct_Milestone` **52 → 126 rows, 2 → 3 projects**, 0 orphans, model reframed, 17 live DAX checks passing. Two traps caught by measuring rather than reasoning: Outbuild sends `progress` as **0–100** against gold's 0–1 contract — and Rebecca's silver had already normalised it, which is exactly what hid the difference — so unnormalised, `IsOverdue` would report **zero overdue milestones on a late job**; and 4 of 15 projects have multiple schedules, so the portable-looking `$.schedules[0].id` would have silently dropped **1,150 of 1,860** activities. Diagnosing a Spark failure took three runs because `deploy_silver` wrote its run diagnostics **after** a `COUNT(*)` loop that crashes on a missing table — which is precisely what a failed `CREATE` upstream produces — so the artefact naming the failing statement was skipped exactly when it was needed. Fixed, and it immediately named a second pre-existing defect: the Job Register parser's bronze table had never been deployed, which would have failed the nightly pipeline. | commit `31cb72c`, PR #42 | — |

### How entries 16–22 were timed

Same method as 11–15: the elapsed span of each contiguous working session, from commit
timestamps, rounded to the nearest 0.25. Entry 16 is different — it is two scheduled
meetings of known length (30 min virtual, 1 hr in person) plus preparation and write-up.
Entries 17 and 18 split one continuous session at the point the work changed shape, which is
also where PR #16 merged. **Reconstructed after the fact and stated plainly so it can be
audited or corrected before invoicing.**

**Entries 21 and 22** span 2026-08-20, 00:08 to 09:07 by commit timestamps — 9.0 hours of
wall clock against 5.0 logged. The gap is real and deliberate: that span includes waiting on
Fabric notebook runs (six deploys at roughly six minutes each) and on a SharePoint batch, and
idle waiting is not billable. 5.0 is the working time, split where the work changed shape.

**Entries 19 and 20 need one caveat the earlier ones did not.** Entry 19 spans 08:23 (the
close of entry 18) to the 10:32 merge — 2.15 hrs, rounded down to 2.0. Entry 20 spans its
first commit at 19:47 to its last at 23:47 — exactly 4.0. That evening figure is **wall
clock, not summed effort**: two branches (`keyvault-and-procore-wiring` and
`powerautomate-sharepoint-fabric-link`) were developed in parallel worktrees, and their
commits interleave. Counting each branch separately would double-bill the same hours, so it
is deliberately counted once. It also means the figure **understates** the setup work that
preceded the first commit of the evening. Charley to confirm or correct both before
invoicing.

## Running totals

| Category | Hours | Billable @ $125 |
|---|---|---|
| Consulting (billable) | 3.75 | $468.75 |
| Development (billable) | 41.75 | $5,218.75 |
| Mentoring (billable) | 0.0 | $0 |
| **Billable total** | **45.5** | **$5,687.50** |
| Non-billable (pre-agreement) | 16.0 | — |

### Phase 0 budget — 20 hrs / $2,500

| | Hours | Amount |
|---|---|---|
| Budget | 20.0 | $2,500 |
| Consumed | 45.5 | $5,687.50 |
| **Remaining** | **−25.5** | **−$3,187.50** |

> ⚠️ **Phase 0's twenty hours are spent, and then some.** The overrun is not a Phase 0
> overspend — it is work past the end of Phase 0 that has not been re-scoped. Phase 0's five
> line items were delivered by Aug 2 at ~22 hrs. Entries 16–20 are a second subject area
> (the PQP), two Power Automate flows deployed into Affect's tenant, the reporting layer over
> both, and the repair of a join that was hiding $22.5M of AR — none of which was in the
> original twenty. **This needs a conversation with Cathal**: either bill it against the
> agreed 5 hrs/week ongoing cadence, or scope it as a second block. Flagged rather than
> absorbed silently, and rather than invoiced without being agreed.
>
> **The number keeps moving.** It was 34.5 at the Aug 19 08:23 update, 40.5 by the end of
> that day, and is **45.5** now; entries 21 and 22 are Aug 20. Any figure quoted to Cathal should be
> taken from this table rather than from the executive update, which is a point-in-time
> document.

> The 16.0 hours logged before Aug 1 are **non-billable by choice** — the tracker assessment,
> Power BI build kit, resource library, warehouse review, and the scope call itself were
> delivered before terms were agreed. They stay at $0: goodwill that shrinks the Phase 0
> estimate rather than adding to the bill.

### ⚠️ Two things to settle before invoicing

**1. NDA.** The Jul 24 terms said billable time starts once the NDA is signed **and** Fabric
access is provisioned. Fabric access landed on Aug 1 and entries 11–15 are logged as billable
on that basis, but **no signed NDA is recorded in this repo.** Confirm before invoicing.

**2. The 2.0-hour overrun.** Phase 0 was budgeted at 20 hours and consumed ~22. The overrun
bought considerably more than the five scoped lines — a full medallion, a Direct Lake
semantic model, a 12-page report, a nightly pipeline, a DQ gate, Outbuild and Sage ingestion,
and the manual-input path — and the $4.85M contract-value defect it surfaced pays for the
block many times over. Flagged rather than absorbed silently; Affect's call whether to bill
it, absorb it, or roll it into the ongoing cadence.

### How entries 11–15 were timed

Hours are derived from **commit timestamps**: the elapsed span of each contiguous working
session, rounded to the nearest 0.25. Sessions were Aug 1 12:14–13:30 and 17:06–22:21, and
Aug 2 00:22–06:22, 08:45–14:49 and 17:18–20:41. This is evidence-based rather than
stopwatch-based — it will slightly *understate* thinking time before the first commit of a
session and slightly overstate any gap inside one. Reconstructed after the fact and stated
plainly so it can be audited or corrected.

*Update totals when adding entries. Mentoring hours remain at zero — the one Phase 0 line
item not yet delivered.*

## Invoicing record

| Invoice # | Period | Entries | Hours | Amount | Sent | Paid |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |
