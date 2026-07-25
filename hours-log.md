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

## Running totals

| Category | Hours | Billable @ $125 |
|---|---|---|
| Consulting (billable) | 0.0 | $0 |
| Development (billable) | 0.0 | $0 |
| Mentoring (billable) | 0.0 | $0 |
| Non-billable (pre-agreement) | 12.0 | — |

### Phase 0 budget — 20 hrs / $2,500

| | Hours | Amount |
|---|---|---|
| Budget | 20.0 | $2,500 |
| Consumed | 0.0 | $0 |
| **Remaining** | **20.0** | **$2,500** |

> All 12.0 hours logged to date are **non-billable by choice** — the tracker assessment,
> Power BI build kit, resource library, warehouse review, and the scope call itself were
> delivered before terms were agreed. They stay at $0: goodwill that shrinks the Phase 0
> estimate rather than adding to the bill.

*Update totals when adding entries. Billable time starts once the NDA is signed and Fabric access is provisioned.*

## Invoicing record

| Invoice # | Period | Entries | Hours | Amount | Sent | Paid |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |
