# Project Dashboard — Affect Group

Single-page rollup of the engagement. Detail lives in `deliverables/` (one file per deliverable) and `hours-log.md` (time ledger). Update this page whenever a deliverable changes status.

**Status key:** 🔴 Not started · 🟡 In progress · 🔵 Blocked/waiting · 🟢 Complete

## Deliverables

| ID | Deliverable | Phase | Status | Phase 0 hours | Depends on | Detail |
|----|-------------|-------|--------|---------------|------------|--------|
| D1 | Discovery & Architecture Review | 1 — Foundation | 🟡 In progress | 4 (endpoint inventory) | NDA, Fabric access | [D1](deliverables/01-discovery-architecture-review.md) |
| D2 | Procore ETL Validation & Hardening | 1 — Foundation | 🔴 Not started | 6 | D1 | [D2](deliverables/02-procore-etl-validation.md) |
| D3 | Sage 100 Ingestion Pipeline | 1 — Foundation | 🔴 Not started | — (post Phase 0) | D1 | [D3](deliverables/03-sage100-ingestion.md) |
| D4 | Core Project Data Model | 1 — Foundation | 🟡 Model designed, pending key resolution | 4 | D2, D3 | [D4](deliverables/04-project-data-model.md) |
| D5 | Power BI Project Dashboard (Excel replacement) | 2 — Project Intelligence | 🟡 Spec + DAX + theme drafted | — (post Phase 0) | D4 | [D5](deliverables/05-powerbi-project-dashboard.md) |
| D6 | Power Automate — Payments Workflow | 3 — Automation | 🔴 Not started | — | Payments SOP finalized | [D6](deliverables/06-power-automate-payments.md) |
| D7 | Power Automate — Lien Waiver Workflow | 3 — Automation | 🔴 Not started | — | Lien waiver SOP finalized | [D7](deliverables/07-power-automate-lien-waivers.md) |
| D8 | Quick-win automation — vendor / insurance / contract list | 1 — Foundation | 🔴 Not started | 3 | Fabric access | [D8](deliverables/08-vendor-list-automation.md) |
| — | Mentoring & recorded walkthroughs (Rebecca) | All | 🟡 Ongoing | 3 | — | Tracked in `hours-log.md` |

## Commercial terms

Agreed with Cathal Egan on the scope call, **Fri Jul 24, 2026** —
see [`meeting-notes/2026-07-24-cathal-scope-call.md`](meeting-notes/2026-07-24-cathal-scope-call.md).

| | |
|---|---|
| **Rate** | **$125/hr**, flat across advisory, development, and mentoring |
| **Term** | **9–10 months** |
| **Initial scoped work** | **20 hours over ~1 month** (Phase 0, below) |
| **Ongoing cadence** | **5 hrs/week** — workflow building + mentoring Rebecca |
| **Envelope discussed** | ~$50,000 over the full term |
| **Rebecca's access** | Text, call, email — **unlimited, not charged, not logged** |

- **One rate, no tiering.** Advisory, build work, and teaching all bill at $125/hr. This
  replaces the earlier $250/hr advisory + fixed-review + per-solution-quote structure.
- **Mentorship is core scope, not a freebie.** Sessions with Rebecca are billable work and
  are **video-recorded** so they become a durable internal asset.
- **Ad-hoc access is free.** Rebecca's questions by text/call/email aren't metered.
- **Pre-agreement work stays non-billable.** The 12.0 hrs already delivered (tracker
  assessment, Power BI build kit, resource library, warehouse review) is goodwill — it
  shrinks Phase 0 rather than adding to it.

> ⚠️ **Open — to confirm with Cal.** 5 hrs/week ≈ 21.7 hrs/month ≈ $27k over 10 months, but
> the $50,000 figure implies ~40 hrs/month. Working assumption: 5 hrs/week is the
> steady-state baseline, build phases flex upward, $50,000 is the outer envelope. Raised in
> the Jul 24 recap email.

## Phase 0 — the initial 20 hours (~1 month)

Drawn straight from the Jul 23 warehouse review's agreed ingestion-first sequence. Starts
when NDA + Fabric access land.

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
| Procore | API → ETL script → Lakehouse | 🟡 Built by Rebecca, needs review | Rebecca / Charley | D2 |
| Sage 100 Contractor | Read-only SQL (currently live-queried from Power BI) | 🔴 Ingestion to Lakehouse not built | Charley | D3 |
| Excel project tracker | Manual today; every field mapped to a source | 🟢 **Analysis complete** — see `analysis/excel-tracker/` | Charley | D4/D5 |
| Manual-only fields (~40% of the report) | SharePoint input workbook → Fabric (proposed) | 🔴 Awaiting Affect decision | Charley | D4 |
| Outbuild | API unverified | 🔵 **May be blocking** — Procore API has no `milestone` endpoint | — | D5 |
| Ramp / ADP / Bluebeam / Navisworks / Outlook / OneDrive | — | 🔴 Future / backlog | — | Future |

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

See `hours-log.md` for the ledger. **Billable to date: 0.0 hrs / $0** — billable time starts at NDA + Fabric access. Non-billable pre-agreement: **12.0 hrs**, delivered as goodwill (tracker assessment, Power BI build kit, resource library, warehouse review).

| | Hours | @ $125 |
|---|---|---|
| Phase 0 budget | 20 | $2,500 |
| Consumed | 0 | $0 |
| Remaining | 20 | $2,500 |

## Blockers & waiting on

- [ ] ⚠️ **The shared project key** across Procore / Sage / the tracker — blocks D4 and everything downstream
- [ ] NDA from Affect — sign and return
- [ ] Fabric workspace access provisioned
- [ ] Sage 100 Contractor read-only SQL access (+ gateway if on-prem)
- [ ] Decision: where the ~40% manual data lives (SharePoint input workbook proposed)
- [ ] Decision: build the Sage job-cost pull now, or wait for the Procore↔Sage connector rollout?
- [ ] Where critical-path milestones live — Procore, Outbuild, or spreadsheet-only
- [ ] 2–3 **real** completed project reports (the file received is a template with demo data)
- [ ] The six client-satisfaction survey questions (only scores are stored in the workbook)
- [ ] **Cal to confirm** the weekly-hours vs $50k-envelope reading (see Commercial terms)
- [x] Data warehouse review with Rebecca held — **Thu Jul 23** (`meeting-notes/2026-07-23-warehouse-review.md`)
- [x] **Scope, terms & engagement agreed with Cathal — Fri Jul 24** (`meeting-notes/2026-07-24-cathal-scope-call.md`)
- [x] Excel project tracker shared (Jul 22) and assessed
- [ ] Payments + lien waiver SOPs finalized (Chris, ~50% complete)

## Reporting cadence

- **Per session:** log hours + evidence in `hours-log.md`, update deliverable checklists
- **Weekly with Rebecca (5 hrs/wk):** working session + mentoring, **video-recorded**
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
- Code/scripts → keep in this repo where possible (e.g., `src/sage100/`), so commits become billing evidence
- Later, if the ledger gets big: the hours table converts cleanly to CSV → Power BI for engagement-level reporting
