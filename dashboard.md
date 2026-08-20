# Project Dashboard — Affect Group

Single-page rollup of the engagement. Detail lives in `deliverables/` (one file per deliverable) and `hours-log.md` (time ledger). Update this page whenever a deliverable changes status.

**Current as of 2026-08-19, end of day.** Three blockers closed during the day — see **Blockers** below; the Aug 19 executive update was written that morning and is a point-in-time record. For the team-facing narrative — what was built, what it found, what we need from Affect — see [`status-update.md`](status-update.md). For the measured engineering state, [`foundation/charley-dev/_docs/build-status.md`](foundation/charley-dev/_docs/build-status.md).

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
| D2 | Procore ETL Validation & Hardening | 1 - Foundation | 🟢 **Complete** - 44 endpoints registered, 40 landing bronze tables (2 blocked by Procore 403s), registry-driven, incremental, tested. **Extraction still runs locally** - no longer for want of Key Vault (resolved 2026-08-19), but until the exposed Procore credentials are rotated | 6 | D1 | [D2](deliverables/02-procore-etl-validation.md) |
| D3 | Sage 100 Ingestion Pipeline | 1 - Foundation | 🔵 **Built & deployed, blocked** - `CD_Sage_Ingest` live and gateway-wired (verified in the Fabric item list 2026-08-19); needs one connection permission grant | 2 | Gateway grant | [D3](deliverables/03-sage100-ingestion.md) |
| D4 | Core Project Data Model | 1 - Foundation | 🟢 **Complete** - **54 gold tables published** to the semantic-model contract (was 45; the QC facts were missing from it), Direct Lake star schema, crosswalks resolve project/vendor/cost code | 4 | D2 | [D4](deliverables/04-project-data-model.md) |
| D5 | Power BI Project Dashboard (Excel replacement) | 2 - Project Intelligence | 🟡 **Built and live** - **two models and two reports now deployed**: `Monthly Progress Report` (12 pages, 180 visuals) over `Affect Project Report` (37 tables, 99 measures), and `Project Quality Plan` (7 pages, 95 visuals) over its own model (19 tables + `_Measures`, 42 measures, 23 relationships). Scorecard coverage 59%, gated on source data. [**See the pages**](resources/power-bi/monthly-progress-report/) | 5 | D4 | [D5](deliverables/05-powerbi-project-dashboard.md) |
| D6 | Power Automate - Payments Workflow | 3 - Automation | 🔴 Not started | - | Payments SOP finalized | [D6](deliverables/06-power-automate-payments.md) |
| D7 | Power Automate - Lien Waiver Workflow | 3 - Automation | 🔴 Not started | - | Lien waiver SOP finalized | [D7](deliverables/07-power-automate-lien-waivers.md) |
| D8 | Quick-win automation - vendor / insurance / contract list | 1 - Foundation | 🟡 **Delivered inside D5** - vendor and insurance data reaches the Monthly Progress Report; the standalone report was never built | 1 | - | [D8](deliverables/08-vendor-list-automation.md) |
| - | Mentoring & recorded walkthroughs (Rebecca) | All | 🔴 **Not yet started** - the one Phase 0 line item still outstanding. From Aug 13 the mechanism shifts to **async and recorded** rather than live pairing | 0 of 3 | Scheduling | Tracked in `hours-log.md` |

Four additions that were not in the original Phase 0 scope and were built anyway:

| Item | Status |
|---|---|
| **Outbuild ingestion** - 16 endpoints, registry-driven | 🟢 **Live 2026-08-19, feeding the report 2026-08-20.** Token landed in `AffectKeyVault` 18:27 UTC; **3,078 rows across 15 endpoints** in `cd_bronze_outbuild_*`. Three bugs only a live call could reveal were fixed first - missing User-Agent (Cloudflare 403), wrong envelope key, wrong paging rule. `fct_Milestone` now reads it: **52 → 126 milestones, 2 → 3 projects** |
| **Manual-input capture** - the ~40% that lives in no system | 🟡 Both paths built, and the dataflow is now **published**: `CD_Manual_Ingest` is live in `charley-dev` with 19 queries (18 reporting-site lists + the Job Register), bound to the real sites. Not yet authenticated or refreshed. The lists it reads are complete: the 18 lists landed 2026-08-19 and their **142 columns and 19 `CD Projects` rows** 2026-08-20. The CSV path works today with no admin ticket |
| **PQP (Project Quality Plan)** - the client's 44-sheet QA/QC tracker, collapsed to 9 tables | 🟢 **Deployed and visible 2026-08-19** - 26 trades, 625 checklist items, 93 statutory gates (46 TCO / 23 Fire Alarm / 24 Statutory), 101 DOH items and 141 status rows, plus the live Procore facts `fct_QcSubmittal` 2,245 / `fct_QcPunch` 1,469 / `fct_QcNcr` 850. Now readable: semantic model `Project Quality Plan` (19 tables + `_Measures`, 42 measures, 23 relationships) and a 7-page, 95-visual report. 8 `man_Qc*` tables typed and empty |
| **Power Automate - Estimating Setup & Convert to Bidding** | 🟡 **In Affect's tenant 2026-08-19, created stopped.** `Estimating Setup` (`98d2c411-…`) and `Convert to Bidding` (`d8a239e6-…`) both exist, and the BUILD site structure they trigger on is provisioned on `AFFECTBUILD1` - a site Affect already had, rather than a new one. Still to do before turning them on: the two folder templates' **contents**, which the SOP never specifies. 20 offline checks pass |

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
| Procore | API → registry-driven extractor → bronze | 🟡 **44 endpoints registered, 40 landing bronze tables**, production tenant; 2 blocked by Procore 403s (`punch_item_types`, `schedule`). Extraction runs **locally** and lands files; the Fabric notebook merges them. `cd_01_extract_procore` is **not** in the nightly DAG | **Rotating the exposed Procore credential pair.** The Key Vault blocker is closed - `AffectKeyVault` is readable and writable by our account today | D2 |
| Sage 100 Contractor | Dataflow Gen2 over the existing on-prem gateway → bronze | 🔵 **`CD_Sage_Ingest` deployed and gateway-wired**, 8 tables incl. the AR/AP line tables the current dataflow discards. First run failed in 5s — the identity cannot see any gateway in the tenant | **One "Can use" grant** on connection `nc-affect-1\sage100con;Affect Group` | D3 |
| Excel project tracker | Manual today; every field mapped to a source | 🟢 **Replaced** — 12-page Power BI report live over the gold model | — | D4/D5 |
| Manual-only fields (~40% of the report) | SharePoint lists **or** CSV upload → bronze (two writers, one contract) | 🟡 **Both paths built, and `CD_Manual_Ingest` is published** (2026-08-19) with 19 queries, bound to the real sites. `cd_06_land_manual` creates **17** manual bronze tables (9 original + 8 PQP); every `man_*` is deployed and empty. CSV path needs no admin ticket and works today | Nothing on the SharePoint side — the lists landed 2026-08-19, their **142 columns and 19 `CD Projects` rows** 2026-08-20. The dataflow still needs its first sign-in. **Or** somebody fills in a template. Plus 4 definition questions | D4 |
| Outbuild | API → registry-driven extractor, 16 endpoints | 🟢 **Live and consumed.** **3,078 rows across 15 endpoints** in `cd_bronze_outbuild_*`; `fct_Milestone` repointed onto it 2026-08-20 - **126 milestones across 3 projects**, up from 52 across 2. The **only** milestone source anywhere | Only 3 of 15 Outbuild projects carry a `procore_id`, so 280 critical activities cannot be attributed. That is a Procore-integration gap on Affect's side | D5 |
| Ramp / ADP / Bluebeam / Navisworks / Outlook / OneDrive | — | 🔴 Future / backlog | — | Future |

**Source coverage was 5.26% when last measured (2026-08-02)** — 1 of 19 projects present in
all three systems. **Not re-measured since Outbuild started landing on 2026-08-19**, and it
should move: Outbuild is one of the three systems. Re-measure before quoting it. This is the
single biggest limit on the report, and every part of it is an access grant rather than a
build task.

> ⚠️ **The existing production reporting lags.** Re-measured live on **2026-08-19**: Sage
> data now runs to **2026-07-31**, up from the **2026-07-20** recorded on 2026-08-02 — so
> Rebecca's feed refreshed at some point in between rather than stopping dead. It is still
> **~19 days behind**, so this is *lag*, not a dead feed. Outbuild's **2026-07-14** is as
> measured on 2026-08-02 and has **not been re-verified since**. Both read out of the
> existing `Silver_Lakehouse`, and a lagging feed is still a reason to fix the gateway
> problem blocking `CD_Sage_Ingest`. Eight of our gold source
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
| **Linchpin unknown** | 🟢 **Resolved, and the join was repaired 2026-08-19.** `dim_ProjectCrosswalk`, `dim_VendorCrosswalk` and `dim_CostCodeCrosswalk` are built and populated — but `dim_Project` had been reading `SageJobNumber` from the wrong view, so **122 of 122 AR invoices resolved to `UNMATCHED`** and $23.7M was attributed to no project. Fixed: **15 of 19** projects now resolve to a Sage job, unmatched invoices **122 → 24**, AR attributed **$0 → $22,548,861.96**. The 4 without a job are three templates and City Harvest |

Of the 14 defects, **7 are structurally fixed** in the platform. See
[`status-update.md`](status-update.md) for the table.

## Hours summary

See [`hours-log.md`](hours-log.md) for the ledger - it is the billing source of truth and the
only place hours are maintained.

> ⚠️ **All sessions through 2026-08-20 are now logged** — entries 16–22. Entries 19 and 20
> were reconstructed from commit timestamps after the fact and the method is stated in the
> ledger; **Charley to confirm or correct both before the first invoice.**

| | Hours | @ $125 |
|---|---|---|
| Phase 0 budget | 20.0 | $2,500 |
| Consumed (all billable to date) | 45.5 | $5,687.50 |
| **Remaining** | **−25.5** | **−$3,187.50** |

The overrun is **not** a Phase 0 overspend. Phase 0's five line items were delivered by Aug 2
at ~22 hrs; everything after that is a second subject area (the PQP), the folder automation,
and the Aug 19 defect work. It needs re-scoping with Cathal rather than invoicing unremarked
— see the callout in [`hours-log.md`](hours-log.md).

Non-billable pre-agreement goodwill: **16.0 hrs** (tracker assessment, Power BI build kit,
resource library, warehouse review, scope call).

⚠️ **Two things to confirm before invoicing** — see the note in `hours-log.md`:
1. **NDA status.** Terms said billable time starts at NDA *and* Fabric access. Fabric access
   landed and the work is delivered; the NDA has not been confirmed signed in this repo.
2. **The ~2 hour overrun**, and whether Affect wants it billed or absorbed.

## Blockers & waiting on

**Access — down from four items to one, after Aug 19 closed the Outbuild token, Key Vault
(withdrawn — wrong vault) and the SharePoint site:**

- [ ] 🔴 **Grant `cforey-c@affect-group.com` "Can use"** on connection `nc-affect-1\sage100con;Affect Group` — **highest value per unit of effort.** One grant, one refresh
- [x] 🟢 **The reporting site's intake lists are complete** — the 18 lists were created 2026-08-19; their **142 of 142 columns** and 19 `CD Projects` rows landed 2026-08-20. All read back through Graph rather than taken from the run status. What remains is signing `CD_Manual_Ingest` in and refreshing it
- [ ] 🟡 **Outbuild → Procore project links** — only **3 of 15** Outbuild projects carry a `procore_id`, so **280 of 406** critical-path activities cannot be attributed to a project and are absent from `fct_Milestone`. Configuration in Outbuild rather than a build task; roughly triples schedule coverage on the report
- [ ] 🟡 Procore permissions: `punch_item_types` and `schedule` both return **403**

**Decisions & information:**

- [ ] 🔴 **Four manual-input definition questions** — daily-log compliance, milestone as date or span, which attestations are monthly, survey anonymity. Blocks the manual silver → gold link. Needs one 30-minute call
- [ ] 🟡 `Expired Certificates` reads 105 of 105 — a question for Affect, not a metric
- [ ] 🟡 `Vendors Missing From ERP` = 125 of 251 — half the vendor master is unmatched
- [ ] 🟡 Scorecard band holes (Observations value 5, Daily Reports value 2) — closed so bands tile; confirm intent
- [ ] 🟡 The six client-satisfaction survey questions (only scores are stored in the workbook)
- [ ] 🟡 2–3 **real** completed project reports (the file received is a template with demo data)
- [ ] 🟡 **PQP workbook: 5 verified defects to report to Affect** — four register roll-ups whose `% Complete` can never reach 100%, and two CSI codes Excel destroyed on the only Tier 4 Critical DFOWs — [`analysis/pqp-workbook/`](analysis/pqp-workbook/defects-and-questions.md)
- [ ] 🟡 **PQP trade vocabulary — largely closed, two narrower questions left.** `qc_seed_TradeAlias` (16 rows) recovered 464 rows; unmapped NCRs **459 → 215** and punch items **511 → 291**. What still needs Affect: (a) three ambiguous labels deliberately not guessed — `Drywall/Carpentry` (255 rows), `Concrete Superstructure` (110), `Concrete` (64); (b) a **scope** question, not a mapping one — Roofing, Glazing, Windows, Structural Steel, Low Voltage and others exist in Procore and have no equivalent trade in the 26-sheet checklist library at all. Both surfaced on the PQP report's Data Quality page — [`build-status.md`](foundation/charley-dev/_docs/build-status.md)
- [ ] 🟡 **Template folder contents** — the site question is answered (Affect reused `AFFECTBUILD1` rather than creating a `BUILD` site, and both flows now point at it), but the SOP names `02 E26-000 BOILER PLATE` and `YY-000 STANDARD PROJECT TEMPLATE` and **never says what is inside them**. Until that lands, the flows create a correct but empty skeleton. Also worth deciding: `02 E26-000 BOILER PLATE` bakes in the year `26`, so in January it needs renaming or the parameter editing
- [ ] 🟡 Payments + lien waiver SOPs finalized (Chris) — blocks D6/D7

**Action items for Affect (not blockers on us):**

- [ ] 🔴 **Rotate the Procore OAuth credential pair.** Live secrets are in plaintext in a workspace notebook. Rotate first, edit second — [`security-findings.md`](foundation/charley-dev/_docs/security-findings.md)
- [ ] 🔴 **Check how far behind the existing reporting is running.** Rebecca's Sage data reached 2026-07-31 when re-measured 2026-08-19 (it moved, from 2026-07-20 on 2026-08-02) but is still ~19 days behind; Outbuild's 2026-07-14 was measured 2026-08-02 and not re-verified since — possibly the same gateway issue

**Closed:**

- [x] Fabric workspace access provisioned — **Aug 1**
- [x] The shared project key across Procore / Sage / the tracker — **crosswalks built and populated**
- [x] Sage ingestion approach decided and built (not waiting on the Procore↔Sage connector)
- [x] Where critical-path milestones live — **Outbuild, confirmed as the only source**, and as of 2026-08-19 **landing live**
- [x] Where the ~40% manual data lives — **decided: SharePoint lists, with a CSV path that works today**
- [x] Data warehouse review with Rebecca — **Thu Jul 23** (`meeting-notes/2026-07-23-warehouse-review.md`)
- [x] Scope, terms & engagement agreed with Cathal — **Fri Jul 24** (`meeting-notes/2026-07-24-cathal-scope-call.md`)
- [x] Excel project tracker shared (Jul 22) and assessed
- [x] **Azure subscription** - exists. “Azure subscription 1”, `0bee26ab-…`, tenant *Affect Build LLC*. The only purchasing decision on the list is closed
- [x] Platform review with Rebecca - **Thu Aug 13** (`meeting-notes/2026-08-13-rebecca-platform-review.md`)
- [x] **`OUTBUILD_API_TOKEN`** - **received 2026-08-19.** Rebecca placed it in `AffectKeyVault` at 18:27 UTC. 3,078 rows across 15 endpoints now land in bronze
- [x] **Key Vault access** - **closed 2026-08-19, and the ask was withdrawn rather than granted.** It had been aimed at the wrong vault. The vault in use is **`AffectKeyVault`** (RG `Affect_Data`, subscription `73932b34-…`), where `cforey-c@affect-group.com` already holds *Key Vault Administrator* inherited at resource-group scope. Nobody needed to grant anything. `OneLake`, which three documents had been naming since Aug 13, holds nothing we depend on - [`keyvault-runbook.md`](foundation/charley-dev/_docs/keyvault-runbook.md)
- [x] **A SharePoint site for the job flows** - **resolved 2026-08-19.** Affect reused an existing site, `AFFECTBUILD1`, rather than creating a dedicated `BUILD` one; both flows point at it and its structure is provisioned

## Roadmap

Phase 0 is delivered. What follows, in value order. Nothing in Phase 1 is gated on build
time — it is gated on access and one conversation.

| Phase | Work | Gate | Rough size |
|---|---|---|---|
| **1 — Close the coverage gap** | Sage silver + retainage question settled; AR views repointed to our medallion | Gateway grant | 4–6 hrs |
| | Outbuild milestones landed; Completion Variance scored | `OUTBUILD_API_TOKEN` | 2–3 hrs |
| | Manual input wired silver → gold; Daily Reports scored | 4 definition answers | 3–4 hrs |
| | **Target: scorecard coverage 59% → ~100%, source coverage 5% → meaningful** | | |
| **1 — Harden** | DQ persist gap fixed; billed-vs-billed gap explained on the report. `deploy_gold.py` default **already changed to `cd`**, and its hardcoded publish list **already fixed** (45 → 54 tables) | Nothing | 2 hrs |
| | 🟢 **Done.** `cd_06_land_manual` runs in `CD_Master_Pipeline` as *Land Manual Input* - verified live 2026-08-19. The pipeline is 6 activities, not 5 | — | — |
| | **`cd_01_extract_procore` added to `CD_Master_Pipeline`** - Procore extraction still runs locally and lands files. Key Vault is no longer the gate; the credential rotation is | Procore credential rotation | 1 hr |
| **1 — Finish the PQP** | Model and report are **deployed**, and the trade vocabulary is largely resolved - `qc_seed_TradeAlias` took unmapped NCRs 459 → 215 and punch items 511 → 291. What is left is Affect's answer on three ambiguous labels plus the trades with no library equivalent, and wiring the 8 `man_Qc*` intake tables | One answer from Affect | 1-2 hrs |
| **1 — Go live on folders** | 🟡 **Mostly done.** Site provisioned on `AFFECTBUILD1`, both flows created in the tenant (stopped), `dim_Job` built end to end from the Job Register. What is left: the template **contents**, a service account to own the connection, then turn the triggers on and smoke-test | Template contents | 1 hr |
| | Retire the local extraction bridge — ingestion moves into Fabric on a schedule | Procore credential rotation (Key Vault itself is no longer a blocker) | 2 hrs |
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
