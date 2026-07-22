# Project Dashboard — Affect Group

Single-page rollup of the engagement. Detail lives in `deliverables/` (one file per deliverable) and `hours-log.md` (time ledger). Update this page whenever a deliverable changes status.

**Status key:** 🔴 Not started · 🟡 In progress · 🔵 Blocked/waiting · 🟢 Complete

## Deliverables

| ID | Deliverable | Phase | Status | Billing | Depends on | Detail |
|----|-------------|-------|--------|---------|------------|--------|
| D1 | Discovery & Architecture Review | 1 — Foundation | 🟡 In progress | Hourly, est. 10–20 hrs | NDA, Fabric access | [D1](deliverables/01-discovery-architecture-review.md) |
| D2 | Procore ETL Validation & Hardening | 1 — Foundation | 🔴 Not started | TBD after D1 | D1 | [D2](deliverables/02-procore-etl-validation.md) |
| D3 | Sage 100 Ingestion Pipeline | 1 — Foundation | 🔴 Not started | TBD after D1 | D1 | [D3](deliverables/03-sage100-ingestion.md) |
| D4 | Core Project Data Model | 1 — Foundation | 🔴 Not started | TBD after D1 | D2, D3, Excel tracker analysis | [D4](deliverables/04-project-data-model.md) |
| D5 | Power BI Project Dashboard (Excel replacement) | 2 — Project Intelligence | 🔴 Not started | Scoped project | D4 | [D5](deliverables/05-powerbi-project-dashboard.md) |
| D6 | Power Automate — Payments Workflow | 3 — Automation | 🔴 Not started | Scoped project | Payments SOP finalized | [D6](deliverables/06-power-automate-payments.md) |
| D7 | Power Automate — Lien Waiver Workflow | 3 — Automation | 🔴 Not started | Scoped project | Lien waiver SOP finalized | [D7](deliverables/07-power-automate-lien-waivers.md) |
| — | Ongoing advisory / mentorship (Rebecca) | All | 🟡 Ongoing | Hourly $250 | — | Tracked in `hours-log.md` only |

## Integration status (data → Fabric Lakehouse)

| Source | Method | Status | Owner | Deliverable |
|---|---|---|---|---|
| Procore | API → ETL script → Lakehouse | 🟡 Built by Rebecca, needs review | Rebecca / Charley | D2 |
| Sage 100 Contractor | Read-only SQL (currently live-queried from Power BI) | 🔴 Ingestion to Lakehouse not built | Charley | D3 |
| Excel project tracker | Manual today; fields to be mapped to sources | 🔴 Analysis pending | Charley | D4/D5 |
| Outbuild | API (assumed) | 🔴 Future — next after core | — | Future |
| Ramp / ADP / Bluebeam / Navisworks / Outlook / OneDrive | — | 🔴 Future / backlog | — | Future |

## Hours summary

See `hours-log.md` for the ledger. **Billable to date: 0.0 hrs / $0** (billable time starts at NDA + agreed Phase 1 scope). Non-billable relationship/setup: 3.0 hrs.

## Blockers & waiting on

- [ ] NDA from Affect — sign and return
- [ ] Fabric workspace access provisioned
- [ ] Deep-dive call with Rebecca scheduled (proposed Thu/Fri Jul 23–24)
- [ ] Excel project tracker shared
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
