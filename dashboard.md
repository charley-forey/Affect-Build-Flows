# Project Dashboard — Affect Group

Single-page rollup of the engagement. Detail lives in `deliverables/` (one file per deliverable) and `hours-log.md` (time ledger). Update this page whenever a deliverable changes status.

**Current as of 2026-08-19.** For the team-facing narrative — what was built, what it found, what we need from Affect — see [`status-update.md`](status-update.md). For the measured engineering state, [`foundation/charley-dev/_docs/build-status.md`](foundation/charley-dev/_docs/build-status.md).

**Status key:** 🔴 Not started · 🟡 In progress · 🔵 Blocked/waiting · 🟢 Complete

## Deliverables

Status as of **2026-08-19**. Phase 0 was delivered Aug 1-2; the Aug 13 platform review with
Rebecca ([notes](meeting-notes/2026-08-13-rebecca-platform-review.md)) and the Aug 19 build
follow it. The build is audited in
[`build-status.md`](foundation/charley-dev/_docs/build-status.md) - every figure there was read
back out of Fabric, not carried forward from a doc. That page is also the single place two
recurring numbers are maintained: the endpoint registry (**44 registered, 40 bronze tables,
2 blocked by Procore 403s**) and **59% scorecard coverage**.

| ID | Deliverable | Phase | Status | Phase 0 hrs | Depends on | Detail |
|----|-------------|-------|--------|-------------|------------|--------|
| D1 | Discovery & Architecture Review | 1 - Foundation | 🟢 **Complete** - endpoint inventory generated from the registry, workspace audited, security findings reported | 4 | - | [D1](deliverables/01-discovery-architecture-review.md) |
| D2 | Procore ETL Validation & Hardening | 1 - Foundation | 🟢 **Complete** - 44 endpoints registered, 40 landing bronze tables (2 blocked by Procore 403s), registry-driven, incremental, tested. **Extraction still runs locally** pending the Key Vault role | 6 | D1 | [D2](deliverables/02-procore-etl-validation.md) |
| D3 | Sage 100 Ingestion Pipeline | 1 - Foundation | 🔵 **Built & deployed, blocked** - `CD_Sage_Ingest` live and gateway-wired (verified in the Fabric item list 2026-08-19); needs one connection permission grant | 2 | Gateway grant | [D3](deliverables/03-sage100-ingestion.md) |
| D4 | Core Project Data Model | 1 - Foundation | 🟢 **Complete** - **53 gold tables published** to the semantic-model contract (was 45; the QC facts were missing from it), Direct Lake star schema, crosswalks resolve project/vendor/cost code | 4 | D2 | [D4](deliverables/04-project-data-model.md) |
| D5 | Power BI Project Dashboard (Excel replacement) | 2 - Project Intelligence | 🟡 **Built and live** - **two models and two reports now deployed**: `Monthly Progress Report` (12 pages, 180 visuals) over `Affect Project Report` (37 tables, 99 measures), and `Project Quality Plan` (7 pages, 95 visuals) over its own model (19 tables + `_Measures`, 42 measures, 23 relationships). Scorecard coverage 59%, gated on source data. [**See the pages**](resources/power-bi/monthly-progress-report/) | 5 | D4 | [D5](deliverables/05-powerbi-project-dashboard.md) |
| D6 | Power Automate - Payments Workflow | 3 - Automation | 🔴 Not started | - | Payments SOP finalized | [D6](deliverables/06-power-automate-payments.md) |
| D7 | Power Automate - Lien Waiver Workflow | 3 - Automation | 🔴 Not started | - | Lien waiver SOP finalized | [D7](deliverables/07-power-automate-lien-waivers.md) |
| D8 | Quick-win automation - vendor / insurance / contract list | 1 - Foundation | 🟡 **Delivered inside D5** - vendor and insurance data reaches the Monthly Progress Report; the standalone report was never built | 1 | - | [D8](deliverables/08-vendor-list-automation.md) |
| - | Mentoring & recorded walkthroughs (Rebecca) | All | 🔴 **Not yet started** - the one Phase 0 line item still outstanding. From Aug 13 the mechanism shifts to **async and recorded** rather than live pairing | 0 of 3 | Scheduling | Tracked in `hours-log.md` |

Four additions that were not in the original Phase 0 scope and were built anyway:

| Item | Status |
|---|---|
| **Outbuild ingestion** - 16 endpoints, registry-driven | 🔵 Built and verified, cannot run - token offered by email Aug 11, **in transit** |
| **Manual-input capture** - the ~40% that lives in no system | 🟡 Both paths built: SharePoint provisioning script, **and** a CSV path that works today with no admin ticket |
| **PQP (Project Quality Plan)** - the client's 44-sheet QA/QC tracker, collapsed to 9 tables | 🟢 **Deployed and visible 2026-08-19** - 26 trades, 625 checklist items, 93 statutory gates (46 TCO / 23 Fire Alarm / 24 Statutory), 101 DOH items and 141 status rows, plus the live Procore facts `fct_QcSubmittal` 2,245 / `fct_QcPunch` 1,469 / `fct_QcNcr` 850. Now readable: semantic model `Project Quality Plan` (19 tables + `_Measures`, 42 measures, 23 relationships) and a 7-page, 95-visual report. 8 `man_Qc*` tables typed and empty |
| **Power Automate - Estimating Setup & Convert to Bidding** | 🟡 **Built, not deployed** - both flow definitions, the PnP provisioning script and 14 passing offline checks in `power-automate/`. No SharePoint site exists yet, and the `powerautomate-mcp` server currently fails to connect |

## Commercial terms

Agreed with Cathal Egan on the scope call, **Fri Jul 24, 2026** —
see [`meeting-notes/2026-07-24-cathal-scope-call.md`](meeting-notes/2026-07-24-cathal-scope-call.md).

| | |
|---|---|
| **Rate** | **$125/hr**, flat across advisory, development, and mentoring |
| **Term** | **9–10 months** |
| **Initial scoped work** | **20 hours over ~1 month** (Phase 0, below) |
| **Ongoing cadence** | **5 hrs/week** — workflow building + mentoring Rebecca |
| **Rebecca's access** | Text, call, email — **unlimited, not charged, not logged** |

- **One rate, no tiering.** Advisory, build work, and teaching all bill at $125/hr. This
  replaces the earlier $250/hr advisory + fixed-review + per-solution-quote structure.
- **Mentorship is core scope, not a freebie.** Sessions with Rebecca are billable work and
  are **video-recorded** so they become a durable internal asset.
- **Ad-hoc access is free.** Rebecca's questions by text/call/email aren't metered.
- **Pre-agreement work stays non-billable.** The **16.0 hrs** delivered before Aug 1 (tracker
  assessment, Power BI build kit, resource library, warehouse review, scope call) is goodwill
  — it shrinks Phase 0 rather than adding to it.
- **Billed on hours actually worked.** No projected total — scope is committed a block at a
  time, starting with Phase 0's twenty hours.

## Phase 0 — the initial 20 hours (~1 month)

Drawn from the Jul 23 warehouse review's agreed ingestion-first sequence. **Delivered Aug 1-2,
2026**, once Fabric access landed.

| # | Work | Deliverable | Budget | Status |
|---|---|---|---|---|
| 1 | **Endpoint inventory** — every Procore (then Sage) endpoint needed to reproduce the Excel report, mapped field by field | D1 | 4 | 🟢 Done — 44 endpoints registered, 40 landing bronze tables, 2 blocked by Procore 403s |
| 2 | **Notebook & transformation review** — confirm every required column/ID is pulled and not dropped; move hard-coded credentials to secure storage; design incremental refresh | D2 | 6 | 🟢 Done — and went further: the ETL was rebuilt registry-driven with a test harness, rather than patched |
| 3 | **Relational bridging** — resolve the vendor ↔ cost-code linkage (invoice as the bridge) so the model slices by both | D4 | 4 | 🟢 Done — `bridge_VendorCostCode` (407 rows), plus project and vendor crosswalks |
| 4 | **Quick-win automation** — vendor list with insurance and contract info, to demonstrate value early | D8 | 3 | 🟡 Data delivered inside the Monthly Progress Report; standalone report not built |
| 5 | **Mentoring + recorded walkthroughs** — working sessions with Rebecca on everything above | — | 3 | 🔴 **Not started — the one open Phase 0 item** |
| | | **Total** | **20** | **~22.0 consumed** |

**Exit criteria — met, with one exception.** Procore ingestion is trusted and hardened, the
vendor/cost-code model is resolved, and the platform is live end to end. What is not yet
true: *"Rebecca able to extend the pattern to a new endpoint herself."* No mentoring session
has happened. That is the gap to close first in the ongoing cadence.

**Scope note.** Phase 0 delivered materially more than the five lines above — a complete
medallion, a Direct Lake semantic model, a 12-page report, a nightly pipeline, a DQ gate,
Outbuild and Sage ingestion, and the manual-input path. The ~2 hour overrun bought all of
that, and the fixed $4.85M understatement pays for the block several times over. Flagging it
rather than absorbing it silently.

## Integration status (data → `CD_Bronze_Lakehouse`)

| Source | Method | Status | Blocked on | Deliverable |
|---|---|---|---|---|
| Procore | API → registry-driven extractor → bronze | 🟡 **44 endpoints registered, 40 landing bronze tables**, production tenant; 2 blocked by Procore 403s (`punch_item_types`, `schedule`). Extraction runs **locally** and lands files; the Fabric notebook merges them. `cd_01_extract_procore` is **not** in the nightly DAG | One Key Vault role assignment, to move extraction into Fabric | D2 |
| Sage 100 Contractor | Dataflow Gen2 over the existing on-prem gateway → bronze | 🔵 **`CD_Sage_Ingest` deployed and gateway-wired**, 8 tables incl. the AR/AP line tables the current dataflow discards. First run failed in 5s — the identity cannot see any gateway in the tenant | **One "Can use" grant** on connection `nc-affect-1\sage100con;Affect Group` | D3 |
| Excel project tracker | Manual today; every field mapped to a source | 🟢 **Replaced** — 12-page Power BI report live over the gold model | — | D4/D5 |
| Manual-only fields (~40% of the report) | SharePoint lists **or** CSV upload → bronze (two writers, one contract) | 🟡 **Both paths built.** `cd_06_land_manual` now creates **17** manual bronze tables (9 original + 8 PQP); every `man_*` is deployed and empty. CSV path needs no admin ticket and works today | SharePoint provisioning, **or** somebody filling in a template. Plus 4 definition questions | D4 |
| Outbuild | API → registry-driven extractor, 16 endpoints | 🔵 **Built and verified, cannot run.** The **only** milestone source anywhere; 17 of 19 projects have none | `OUTBUILD_API_TOKEN` not issued | D5 |
| Ramp / ADP / Bluebeam / Navisworks / Outlook / OneDrive | — | 🔴 Future / backlog | — | Future |

**Source coverage is 5.26%** — 1 of 19 projects present in all three systems. This is the
single biggest limit on the report, and every part of it is an access grant rather than a
build task.

> ⚠️ **The existing production reporting is stale.** Sage data stops at **2026-07-20**,
> Outbuild at **2026-07-14** — read out of the existing `Silver_Lakehouse`, and almost
> certainly the same gateway problem blocking `CD_Sage_Ingest`. Eight of our gold source
> views still read that lakehouse for what Procore does not hold (Sage AR, Outbuild
> milestones, the Sage vendor crosswalk), so if Rebecca's dataflows stop, our financial and
> schedule data stops with them — silently.

## Excel tracker assessment — headline findings

Full detail in [`analysis/excel-tracker/`](analysis/excel-tracker/).

| | |
|---|---|
| **Structure** | 11 tabs · 17 Excel Tables · 15 drop-down lists · ~700 manual input cells · **1 chart** |
| **Data split** | ~40% manual-only · ~30% Procore · ~15% Sage · ~15% derived |
| **Defects found** | **14 verified** — 3 change reported numbers |
| **Biggest issue** | **42% of the scorecard weight is disconnected from reality** — Schedule Performance always scores 3/3, Completion Variance always 0/3, Accounts Receivable reads a dollar balance against day-count bands. The first two errors cancel, which is why it went unnoticed |
| **Cleanest win** | `SUBMITTALS & RFI` — one table, fully derivable from 4 Procore endpoints, feeds the only chart |
| **Linchpin unknown** | 🟢 **Resolved** — `dim_ProjectCrosswalk`, `dim_VendorCrosswalk` and `dim_CostCodeCrosswalk` are built and populated. 2 projects still have no Sage entry |

Of the 14 defects, **7 are structurally fixed** in the platform. See
[`status-update.md`](status-update.md) for the table.

## Hours summary

See [`hours-log.md`](hours-log.md) for the ledger - it is the billing source of truth and the
only place hours are maintained.

> ⚠️ **Two sessions are not yet logged**: the Aug 13 platform review and the Aug 19 build.
> The ledger is append-only and only Charley can write it; estimating retroactively would
> corrupt the record. Log both before the first invoice.

| | Hours | @ $125 |
|---|---|---|
| Phase 0 budget | 20.0 | $2,500 |
| Consumed (Aug 1–2 build) | 22.0 | $2,750 |
| **Remaining** | **−2.0** | **−$250** |

Non-billable pre-agreement goodwill: **16.0 hrs** (tracker assessment, Power BI build kit,
resource library, warehouse review, scope call).

⚠️ **Two things to confirm before invoicing** — see the note in `hours-log.md`:
1. **NDA status.** Terms said billable time starts at NDA *and* Fabric access. Fabric access
   landed and the work is delivered; the NDA has not been confirmed signed in this repo.
2. **The ~2 hour overrun**, and whether Affect wants it billed or absorbed.

## Blockers & waiting on

**Access — all Affect's to grant, all pipework already built:**

- [ ] 🔴 **Grant `cforey-c@affect-group.com` "Can use"** on connection `nc-affect-1\sage100con;Affect Group` — **highest value per unit of effort.** One grant, one refresh
- [ ] 🟡 **`OUTBUILD_API_TOKEN`** — **in transit**, offered by email Aug 11. The only milestone source anywhere; 17 of 19 projects have none. Chase rather than escalate
- [ ] 🟡 **SharePoint lists provisioned** (script is written) — *or* somebody fills in a CSV template, which needs no ticket
- [ ] 🔴 **Key Vault role assignment** - the subscription and vault `OneLake` now both exist, but `cforey-c@affect-group.com` holds only *Contributor on the resource group*, which on an RBAC vault can neither read nor write a secret nor grant itself the right to. **The ask is one role: “Key Vault Secrets Officer” on vault `OneLake`.** Until then Procore extraction runs on a laptop - [`keyvault-runbook.md`](foundation/charley-dev/_docs/keyvault-runbook.md)
- [ ] 🟡 Procore permissions: `punch_item_types` and `schedule` both return **403**

**Decisions & information:**

- [ ] 🔴 **Four manual-input definition questions** — daily-log compliance, milestone as date or span, which attestations are monthly, survey anonymity. Blocks the manual silver → gold link. Needs one 30-minute call
- [ ] 🟡 `Expired Certificates` reads 105 of 105 — a question for Affect, not a metric
- [ ] 🟡 `Vendors Missing From ERP` = 125 of 251 — half the vendor master is unmatched
- [ ] 🟡 Scorecard band holes (Observations value 5, Daily Reports value 2) — closed so bands tile; confirm intent
- [ ] 🟡 The six client-satisfaction survey questions (only scores are stored in the workbook)
- [ ] 🟡 2–3 **real** completed project reports (the file received is a template with demo data)
- [ ] 🟡 **PQP workbook: 5 verified defects to report to Affect** — four register roll-ups whose `% Complete` can never reach 100%, and two CSI codes Excel destroyed on the only Tier 4 Critical DFOWs — [`analysis/pqp-workbook/`](analysis/pqp-workbook/defects-and-questions.md)
- [ ] 🟡 **PQP trade vocabulary: 459 of 850 NCRs resolve to no trade.** Procore says "HVAC" / "Sprinkler"; the client workbook says `HVAC_DUCTWORK` / `FIRE_SPRINKLER`. Deliberately **not** guessed — mapping a defect to the wrong trade is worse than leaving it unmapped. Surfaced on the PQP report's Data Quality page; needs one vocabulary decision from Affect
- [ ] 🟡 **SharePoint site URL and template folder contents** — the Power Automate SOP names both templates but never says what is inside them
- [ ] 🟡 Payments + lien waiver SOPs finalized (Chris) — blocks D6/D7

**Action items for Affect (not blockers on us):**

- [ ] 🔴 **Rotate the Procore OAuth credential pair.** Live secrets are in plaintext in a workspace notebook. Rotate first, edit second — [`security-findings.md`](foundation/charley-dev/_docs/security-findings.md)
- [ ] 🔴 **Check whether the existing reporting is stale.** Rebecca's Sage data stops 2026-07-20, Outbuild 2026-07-14 — possibly the same gateway issue

**Closed:**

- [x] Fabric workspace access provisioned — **Aug 1**
- [x] The shared project key across Procore / Sage / the tracker — **crosswalks built and populated**
- [x] Sage ingestion approach decided and built (not waiting on the Procore↔Sage connector)
- [x] Where critical-path milestones live — **Outbuild, confirmed as the only source**
- [x] Where the ~40% manual data lives — **decided: SharePoint lists, with a CSV path that works today**
- [x] Data warehouse review with Rebecca — **Thu Jul 23** (`meeting-notes/2026-07-23-warehouse-review.md`)
- [x] Scope, terms & engagement agreed with Cathal — **Fri Jul 24** (`meeting-notes/2026-07-24-cathal-scope-call.md`)
- [x] Excel project tracker shared (Jul 22) and assessed
- [x] **Azure subscription** - exists. “Azure subscription 1”, `0bee26ab-…`, tenant *Affect Build LLC*. The only purchasing decision on the list is closed
- [x] Platform review with Rebecca - **Thu Aug 13** (`meeting-notes/2026-08-13-rebecca-platform-review.md`)

## Roadmap

Phase 0 is delivered. What follows, in value order. Nothing in Phase 1 is gated on build
time — it is gated on access and one conversation.

| Phase | Work | Gate | Rough size |
|---|---|---|---|
| **1 — Close the coverage gap** | Sage silver + retainage question settled; AR views repointed to our medallion | Gateway grant | 4–6 hrs |
| | Outbuild milestones landed; Completion Variance scored | `OUTBUILD_API_TOKEN` | 2–3 hrs |
| | Manual input wired silver → gold; Daily Reports scored | 4 definition answers | 3–4 hrs |
| | **Target: scorecard coverage 59% → ~100%, source coverage 5% → meaningful** | | |
| **1 — Harden** | DQ persist gap fixed; billed-vs-billed gap explained on the report. `deploy_gold.py` default **already changed to `cd`**, and its hardcoded publish list **already fixed** (45 → 53 tables) | Nothing | 2 hrs |
| | **`cd_06_land_manual` added to `CD_Master_Pipeline`** - the nightly run currently rebuilds silver and gold without refreshing manual bronze. Harmless while every `man_*` is empty; a silent staleness bug the day somebody enters data. Must land before SharePoint goes live | Nothing | 1 hr |
| | **`cd_01_extract_procore` added to `CD_Master_Pipeline`** - Procore extraction still runs locally and lands files | Key Vault role | 1 hr |
| **1 — Finish the PQP** | Model and report are **deployed**. What is left is the trade-vocabulary answer from Affect - 459 of 850 NCRs still resolve to no trade - and wiring the 8 `man_Qc*` intake tables | One answer from Affect | 1-2 hrs |
| **1 — Go live on folders** | SharePoint site provisioned, both Power Automate flows imported and tested, `dim_Job` built from the Job Register | Site URL + template contents | 2-3 hrs |
| | Retire the local extraction bridge — ingestion moves into Fabric on a schedule | Key Vault role (the subscription and vault now exist) | 2 hrs |
| **1 — Transfer** | **Mentoring with Rebecca, recorded.** Extractor registry pattern first, then the deploy scripts, then the DQ gate | Scheduling | 3 hrs to start, then ongoing |
| **2 — Project intelligence** | Report iteration with leadership; real completed-project validation; standalone Vendor & Insurance list if still wanted | Real project data | TBD |
| **3 — Automation** | D6 payments, D7 lien waivers | SOPs from Chris | Quote per SOP |
| **Backlog** | Ramp, ADP, Bluebeam / Navisworks, Outlook / OneDrive | — | — |

## Reporting cadence

Changed at the Aug 13 review. Rebecca is back from vacation into a heavier load — a
departure on her team has landed on her — so the weekly live working session is no longer a
realistic dependency.

- **Charley absorbs the build load.** Delivery does not wait on a shared calendar hour.
- **Mentoring goes async** — recorded walkthroughs instead of live pairing, still billable,
  still core scope, still a reusable internal asset. Live sessions when Rebecca has time,
  not as the mechanism.
- **Rebecca's ad-hoc access is unchanged** — text, call, email, unlimited, unmetered.
- **Per session:** log hours + evidence in `hours-log.md`, update deliverable checklists
- **Bi-weekly:** review this dashboard, update statuses, agree next priorities
- **Per invoice:** ledger entries roll up into the invoicing record in `hours-log.md`

### Availability

| | |
|---|---|
| Meetings (video / in-person) | M–F **7–9am** and **5–7pm**; weekends on request |
| Text / email / call | Throughout the day, **1–4 hr response** |
| Build & recording | Evenings |
| On-site | Encouraged — discovery, working sessions, presentations, implementation |
| Rebecca's ad-hoc access | Unlimited, **not charged** |

## How this structure grows

- New deliverable → copy `deliverables/_template.md`, assign next ID, add a row here
- New data source → add a row to the integration table; when work starts, it becomes a deliverable
- Meeting → new file in `meeting-notes/` + hours entry pointing to it
- **New Procore endpoint → a YAML entry in `foundation/charley-dev/01-ingestion/Procore/config/endpoints.yml`.** Not a new notebook. Auth, pagination, the v2.0 header rule, retry and watermarking are implemented once in the shared extractor — that is the pattern worth teaching Rebecca first
- New *source system* → copy the Procore shape: registry-driven extractor + `.sql` transforms + offline DuckDB tests. Outbuild and Sage both followed it
- Everything reaches Fabric through a committed deploy script, so every change is a diff and a mis-deploy is fixed by re-running
- Later, if the ledger gets big: the hours table converts cleanly to CSV → Power BI for engagement-level reporting
