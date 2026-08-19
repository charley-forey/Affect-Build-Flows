# Project Dashboard — Affect Group

Single-page rollup of the engagement. Detail lives in `deliverables/` (one file per deliverable) and `hours-log.md` (time ledger). Update this page whenever a deliverable changes status.

**Status key:** 🔴 Not started · 🟡 In progress · 🔵 Blocked/waiting · 🟢 Complete

## Deliverables

Status as of **2026-08-19**, following the Aug 13 platform review with Rebecca
([notes](meeting-notes/2026-08-13-rebecca-platform-review.md)). The build itself is audited
in [`foundation/charley-dev/_docs/build-status.md`](foundation/charley-dev/_docs/build-status.md)
— every figure there was read back out of Fabric, not carried forward from a doc. That
page is also the single place two recurring numbers are maintained: the **42-endpoint**
registry and **59% scorecard coverage**.

| ID | Deliverable | Phase | Status | Phase 0 hours | Depends on | Detail |
|----|-------------|-------|--------|---------------|------------|--------|
| D1 | Discovery & Architecture Review | 1 — Foundation | 🟢 **Complete** — 42-endpoint inventory (generated from the registry), architecture built and audited | 4 | — | [D1](deliverables/01-discovery-architecture-review.md) |
| D2 | Procore ETL Validation & Hardening | 1 — Foundation | 🟢 Ingesting Affect's production tenant — 40 bronze / 15 silver tables, 0 rejects. **Extraction still runs locally** pending Key Vault | 6 | — | [D2](deliverables/02-procore-etl-validation.md) |
| D3 | Sage 100 Ingestion Pipeline | 1 — Foundation | 🔵 `CD_Sage_Ingest` **built and deployed** (verified live 2026-08-19) — inert, blocked on one gateway permission grant | — | Gateway grant | [D3](deliverables/03-sage100-ingestion.md) |
| D4 | Core Project Data Model | 1 — Foundation | 🟢 Live — 40 gold tables, star schema, crosswalks resolved | 4 | — | [D4](deliverables/04-project-data-model.md) |
| D5 | Power BI Project Dashboard (Excel replacement) | 2 — Project Intelligence | 🟢 **Deployed** — 12 pages, 180 visuals, 99 measures on Direct Lake. Scorecard coverage 59%: 4 of 9 categories unscored for want of source data | — | D3, Outbuild token | [D5](deliverables/05-powerbi-project-dashboard.md) |
| D6 | Power Automate — Payments Workflow | 3 — Automation | 🔴 Not started | — | Payments SOP finalized | [D6](deliverables/06-power-automate-payments.md) |
| D7 | Power Automate — Lien Waiver Workflow | 3 — Automation | 🔴 Not started | — | Lien waiver SOP finalized | [D7](deliverables/07-power-automate-lien-waivers.md) |
| D8 | Quick-win automation — vendor / insurance / contract list | 1 — Foundation | 🟡 **Delivered inside the Monthly Progress Report** (`fct_VendorInsurance`, 105 rows, plus a Vendor Insurance page); the standalone list was never built and is not planned | 3 | — | [D8](deliverables/08-vendor-list-automation.md) |
| — | Manual-input capture (SharePoint) | 1 — Foundation | 🔵 9 `man_*` tables live and empty; PnP script generated — awaiting Affect's decision + admin run. ⚠️ **Two code defects to fix before it runs** — see below | — | Affect decision | [`sharepoint-lists.md`](foundation/charley-dev/_docs/sharepoint-lists.md) |
| — | PQP (Project Quality Plan) subject area | 2 — Project Intelligence | 🟡 **In progress** — seed data extracted from the client's 44-sheet QA/QC tracker (26 trades, 625 checklist items, 93 statutory gates, 101 DOH items, 143 status-vocabulary rows); second semantic model + report to follow | — | — | `foundation/charley-dev/02-transformation/seed/` |
| — | Power Automate — Estimating Setup & Convert to Bidding | 3 — Automation | 🟡 **In progress** — two flows being built | — | — | `power-automate/` |
| — | Mentoring & recorded walkthroughs (Rebecca) | All | 🟡 Ongoing — **shifted to async/recorded** from Aug 13 (see cadence) | 3 | — | Tracked in `hours-log.md` |

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
- **Pre-agreement work stays non-billable.** The 12.0 hrs already delivered (tracker
  assessment, Power BI build kit, resource library, warehouse review) is goodwill — it
  shrinks Phase 0 rather than adding to it.
- **Billed on hours actually worked.** No projected total — scope is committed a block at a
  time, starting with Phase 0's twenty hours.

## Phase 0 — the initial 20 hours (~1 month)

Drawn straight from the Jul 23 warehouse review's agreed ingestion-first sequence. **Fabric
access landed and the work is substantially delivered** — items 1–3 are complete and went
well beyond their scope (a full medallion, semantic model and 12-page report rather than an
inventory and a review). Item 4's insurance data shipped inside the Monthly Progress Report
instead of as a standalone list.

| # | Work | Deliverable | Hrs |
|---|---|---|---|
| 1 | **Endpoint inventory** — every Procore (then Sage) endpoint needed to reproduce the Excel report, mapped field by field | D1 | 4 |
| 2 | **Notebook & transformation review** — confirm every required column/ID is pulled and not dropped; move hard-coded credentials to secure storage; design incremental refresh | D2 | 6 |
| 3 | **Relational bridging** — resolve the vendor ↔ cost-code linkage (invoice as the bridge) so the model slices by both | D4 | 4 |
| 4 | **Quick-win automation** — vendor list with insurance and contract info, to demonstrate value early | D8 | 3 |
| 5 | **Mentoring + recorded walkthroughs** — working sessions with Rebecca on everything above | — | 3 |
| | | **Total** | **20** |

Exit criteria: Procore ingestion trusted and hardened, the vendor/cost-code model resolved,
one automation live, and Rebecca able to extend the pattern to a new endpoint herself.

## Integration status (data → Fabric Lakehouse)

| Source | Method | Status | Owner | Deliverable |
|---|---|---|---|---|
| Procore | API → config-driven extractor → `CD_Bronze` | 🟢 **Live against the production tenant.** Extraction runs locally and lands files; `cd_05_land_to_bronze` merges them in Fabric. 403 on `punch_item_types` and `schedule` | Charley | D2 |
| Sage 100 Contractor | On-prem SQL via data gateway → `CD_Bronze` (`CD_Sage_Ingest`) | 🔵 **Deployed and inert** — verified live in the `charley-dev` folder 2026-08-19. Needs one grant: `cforey-c@affect-group.com` → *Can use* on connection `nc-affect-1\sage100con;Affect Group` | Affect | D3 |
| Excel project tracker | Manual today; every field mapped to a source | 🟢 **Analysis complete** — see `analysis/excel-tracker/` | Charley | D4/D5 |
| Manual-only fields (~40% of the report) | CSV drop today (`Files/_manual/` → `cd_06_land_manual`), SharePoint lists later | 🔵 Tables live and empty. Ten lists specified — **nine data lists, 61 columns, plus the `CD Projects` lookup**. Two known code defects listed under *Blockers* | Affect | D4 |
| Outbuild | Datahub API → `CD_Bronze` | 🔵 Built and verified, **cannot run yet** — `OUTBUILD_API_TOKEN` offered by email Aug 11 and **in transit**. Only milestone source anywhere; 17 of 19 projects have no schedule data | Affect (in transit) | D5 |
| Ramp / ADP / Bluebeam / Navisworks / Outlook / OneDrive | — | 🔴 Future / backlog | — | Future |

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
| **Linchpin unknown** | ⚠️ The shared project identifier across Procore / Sage / the tracker. **Nothing joins without it** |

## Hours summary

See `hours-log.md` for the ledger. **Billable to date: 0.0 hrs / $0.** Non-billable
pre-agreement: **16.0 hrs**, delivered as goodwill (tracker assessment, Power BI build kit,
resource library, warehouse review, reference pipeline).

> ⚠️ **The ledger is behind the work.** It stops at Jul 26, and the platform build sprint of
> Aug 1–2 plus the Aug 13 review are not in it. Hours are the billing source of truth and
> only Charley can enter them — the ledger is append-only, and estimating retroactively
> would corrupt the record. Log them before the first invoice.

| | Hours | @ $125 |
|---|---|---|
| Phase 0 budget | 20 | $2,500 |
| Consumed | 0 | $0 |
| Remaining | 20 | $2,500 |

## Blockers & waiting on

**Re-checked live 2026-08-19.** Two blockers cleared since the Aug 13 update and one new,
smaller one took their place. Every remaining item is **with Affect**, and every one of them
is a permission grant or a decision — none is a purchasing decision any more, and none is
build work. Written up for sharing in
[`updates/2026-08-13-executive-update.md`](updates/2026-08-13-executive-update.md).

| # | Blocked item | The ask | Owner |
|---|---|---|---|
| 1 | Sage 100 ingestion (D3) | Grant `cforey-c@affect-group.com` **Can use** on gateway connection `nc-affect-1\sage100con;Affect Group`. `CD_Sage_Ingest` is **deployed and inert** — it runs on the next refresh once this lands. Affect already uses this connection, so nothing new is built: no subscription, no vault, no code change. **The Sage DB is managed by an outside consultant** — if they own the connection, the ask routes through them. Raised with IT support Aug 11 | Affect / their Sage consultant |
| 2 | **Key Vault secrets access** — runbook: [`keyvault-runbook.md`](foundation/charley-dev/_docs/keyvault-runbook.md) — so Procore extraction runs inside Fabric instead of on a laptop | **NEW, and it replaces the old subscription blocker.** The subscription and the vault both now exist — vault `OneLake`, RG `Affect_KeyVault`, East US, `https://onelake.vault.azure.net/`. It is **RBAC-mode**, and `cforey-c@affect-group.com` holds only **Contributor on the resource group**, which can neither read nor write a secret nor grant itself the right to. **The ask is one role assignment: "Key Vault Secrets Officer" on vault `OneLake`.** Until it lands, no secret can be written and extraction keeps running locally | Affect |
| 3 | Two report sections | Procore role permissions — 403 on `punch_item_types` and `schedule` | Affect |
| 4 | ~40% of the report (`man_*` tables, empty) | Decision on manual-input location, then a SharePoint admin runs the generated PnP script — **nine data lists, 61 columns, plus the `CD Projects` lookup; ten in total**, idempotent. **Two code defects must be fixed first** — see below. Note the CSV path in `Files/_manual/` works today, so this gates the *team* mechanism, not data entry | Affect |
| 5 | Validating the rebuilt numbers | 2–3 **real** completed project reports (the file received was a template with demo data) + the six client-satisfaction survey questions | Affect |
| 6 | Outbuild milestones (D5 scorecard) | **In transit, not blocked.** Rebecca offered to send `OUTBUILD_API_TOKEN` by email on Aug 11; it has not arrived. Chase rather than escalate | Affect (in transit) |

**Cleared since Aug 13:**

- [x] **Azure subscription** — exists. "Azure subscription 1", `0bee26ab-eeb7-4dc9-ab92-fb46d068f6b6`, on tenant "Affect Build LLC" `b2a2225b-4b4e-42ec-ba52-c7e1c2dea580`. This was the only ask on the list that was a purchasing decision. Blocker #2 above is what is left of it.
- [x] **A Key Vault exists** — `OneLake`, soft-delete on with 90-day retention. **Purge protection is disabled**; worth turning on before the vault holds live credentials, since without it a deleted vault can be purged inside the retention window.

Also open, lower priority:

- [ ] **SharePoint list names do not match what reads them** — `provision-sharepoint.ps1` creates `CD PriorityItems` / `CD SafetyMonthly` / `CD QualityMonthly` / `CD DailyLogCompliance`, while `CD_Manual_Ingest`'s `mashup.pq` reads the spaced forms. Four of nine queries would return nothing and render as blank tiles — indistinguishable from "nobody filled this in". A latent runtime break; fix in progress. Detail in [`sharepoint-lists.md`](foundation/charley-dev/_docs/sharepoint-lists.md)
- [x] ~~No silver → gold link for `man_*`~~ — **written.** `40_man_tables.sql` now `INSERT`s from `sv_man_*` rather than stopping at nine empty placeholders. With no input the inserts move zero rows, so the tables stay empty until somebody types something — which is correct
- [ ] **Four `man_*` column-spec questions still need Affect** — the gold DDL and the silver parsers disagree on `man_Flags`, `man_Milestones`, `man_Survey` and `man_DailyLogCompliance`. Each is a real question about what the scorecard should measure, not a typo: is daily-log compliance "submitted" or "submitted the same day"? Is a milestone a date or a span? [`manual-input.md`](foundation/charley-dev/_docs/manual-input.md)
- [ ] Payments + lien waiver SOPs finalized (Chris, ~50% complete as of Jul 21) — gates D6/D7
- [ ] Decision: keep the Sage job-cost pull, or defer to the Procore↔Sage connector rollout
- [ ] Confirm intent on the scorecard band holes — Observations leaves the value 5 unscored, Daily Reports leaves 2
- [ ] Fix `_persist_results` writing to a non-existent `cd_dq_results` table — DQ counts are trustworthy, drill-through is stale (diagnosed, not fixed; see `assessment.md`)
- [ ] `deploy_gold.py` defaults to `--source existing` — re-deploying without `--source cd` silently reverts the medallion to the legacy warehouse
- [ ] **Rotate the Procore credential, then edit the notebook** — in that order. Rebecca's `procore_auth` notebook in the workspace still holds the client id and secret as literals (F1). The repo copies are clean; the live one is not. Now actionable once the vault role lands — [`security-findings.md`](foundation/charley-dev/_docs/security-findings.md)
- [ ] Row-level security before the Portfolio page is shared — it is the first page showing every PM each other's jobs

Closed:

- [x] ⚠️ **The shared project key** — resolved via `dim_ProjectCrosswalk` (19 rows); 2 projects still have no Sage entry
- [x] Fabric workspace access provisioned — `cforey-c@affect-group.com`
- [x] Where critical-path milestones live — **Outbuild**, and it is the only source
- [x] Data warehouse review with Rebecca — **Thu Jul 23** (`meeting-notes/2026-07-23-warehouse-review.md`)
- [x] **Scope, terms & engagement agreed with Cathal — Fri Jul 24** (`meeting-notes/2026-07-24-cathal-scope-call.md`)
- [x] Excel project tracker shared (Jul 22) and assessed
- [x] Platform review with Rebecca — **Thu Aug 13** (`meeting-notes/2026-08-13-rebecca-platform-review.md`)

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
- Code/scripts → keep in this repo where possible (`src/<source-system>/`, e.g. [`src/procore/`](src/procore/)), so commits become billing evidence. New sources copy the Procore shape: config-driven extractor + `.sql` transforms + a local runner
- Later, if the ledger gets big: the hours table converts cleanly to CSV → Power BI for engagement-level reporting
