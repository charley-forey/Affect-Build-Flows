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

## Running totals

| Category | Hours | Billable @ $125 |
|---|---|---|
| Consulting (billable) | 1.25 | $156.25 |
| Development (billable) | 20.75 | $2,593.75 |
| Mentoring (billable) | 0.0 | $0 |
| **Billable total** | **22.0** | **$2,750.00** |
| Non-billable (pre-agreement) | 16.0 | — |

### Phase 0 budget — 20 hrs / $2,500

| | Hours | Amount |
|---|---|---|
| Budget | 20.0 | $2,500 |
| Consumed | 22.0 | $2,750 |
| **Remaining** | **−2.0** | **−$250** |

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
