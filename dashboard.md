# Project Dashboard — Affect Group

Single-page rollup of the engagement. Detail lives in `deliverables/` (one file per deliverable) and `hours-log.md` (time ledger). Update this page whenever a deliverable changes status.

**Status key:** 🔴 Not started · 🟡 In progress · 🔵 Blocked/waiting · 🟢 Complete

## Deliverables

| ID | Deliverable | Phase | Status | Billing | Depends on | Detail |
|----|-------------|-------|--------|---------|------------|--------|
| D1 | Discovery & Architecture Review | 1 — Foundation | 🟡 In progress | Fixed review — ≤10 hrs ($2,500) | NDA, Fabric access | [D1](deliverables/01-discovery-architecture-review.md) |
| D2 | Procore ETL Validation & Hardening | 1 — Foundation | 🔴 Not started | Scoped from D1 review | D1 | [D2](deliverables/02-procore-etl-validation.md) |
| D3 | Sage 100 Ingestion Pipeline | 1 — Foundation | 🔴 Not started | Scoped from D1 review | D1 | [D3](deliverables/03-sage100-ingestion.md) |
| D4 | Core Project Data Model | 1 — Foundation | 🟡 Model designed, pending key resolution | Scoped from D1 review | D2, D3 | [D4](deliverables/04-project-data-model.md) |
| D5 | Power BI Project Dashboard (Excel replacement) | 2 — Project Intelligence | 🟡 Spec + DAX + theme drafted | Scoped project | D4 | [D5](deliverables/05-powerbi-project-dashboard.md) |
| D6 | Power Automate — Payments Workflow | 3 — Automation | 🔴 Not started | Scoped project | Payments SOP finalized | [D6](deliverables/06-power-automate-payments.md) |
| D7 | Power Automate — Lien Waiver Workflow | 3 — Automation | 🔴 Not started | Scoped project | Lien waiver SOP finalized | [D7](deliverables/07-power-automate-lien-waivers.md) |
| — | Ongoing advisory / mentorship (Rebecca) | All | 🟡 Ongoing | Hourly $250 | — | Tracked in `hours-log.md` only |

## Billing approach

Priced to stay small and fair — you pay for specific outcomes, not an open-ended roadmap:

- **The deep review comes first, and it's the only thing quoted up front** — fixed and
  capped. Reviewing the current build (Procore implementation, schema, SQL, Lakehouse) is
  cheap on purpose: it's what makes everything after it scopable and correct.
- **Build work is scoped per solution, from what the review finds.** Each source follows
  the same unit — connect script → format & validate the SQL → land it in the Lakehouse —
  quoted as its own small block when we reach it. You choose how many connectors and in what
  order. There's no lump-sum "everything" number to commit to.
- **The dashboard sits on top** of whatever data has landed, quoted as its own block.
- **Mentorship and learning are non-billable.** Teaching Rebecca, evening build time, and
  working out new tooling are logged at $0 — see [`hours-log.md`](hours-log.md).

Net: a small fixed review, then pay only for the specific solutions you decide to build.

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

See `hours-log.md` for the ledger. **Billable to date: 0.0 hrs / $0** (billable time starts at NDA + agreed Phase 1 scope). Non-billable relationship/setup/pre-NDA: **11.0 hrs** — 7.0 of which is the tracker assessment and Power BI build kit, worth revisiting once the engagement is formalised.

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
- [x] Data warehouse review with Rebecca held — **Thu Jul 23** (`meeting-notes/2026-07-23-warehouse-review.md`)
- [x] Excel project tracker shared (Jul 22) and assessed
- [ ] Payments + lien waiver SOPs finalized (Chris, ~50% complete)

## Reporting cadence

- **Per session:** log hours + evidence in `hours-log.md`, update deliverable checklists
- **Bi-weekly sync with Rebecca:** review this dashboard, update statuses, agree next priorities
- **Per invoice:** ledger entries roll up into the invoicing record in `hours-log.md`

## How this structure grows

- New deliverable → copy `deliverables/_template.md`, assign next ID, add a row here
- New data source → add a row to the integration table; when work starts, it becomes a deliverable
- Meeting → new file in `meeting-notes/` + hours entry pointing to it
- Code/scripts → keep in this repo where possible (e.g., `src/sage100/`), so commits become billing evidence
- Later, if the ledger gets big: the hours table converts cleanly to CSV → Power BI for engagement-level reporting
