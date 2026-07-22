# Hours Log — Affect Group

Source of truth for time/project validation and invoicing. **Append-only** — never edit past entries; add a correcting entry instead.

## Conventions

- **Type:** `Consulting` (advisory, meetings, questions, reviews, videos, knowledge transfer — $250/hr) or `Development` (scoped build work — billed per the deliverable's agreed terms)
- **Deliverable:** link to the file in `deliverables/` the work belongs to, or `General` for cross-cutting advisory
- **Evidence:** link to what the time produced — commit, doc, recording, email, meeting notes. Every entry should point to something verifiable.
- Log same-day, in 0.25 hr increments. Unbilled prep/business development (like proposal writing before an agreement) goes in the log with **Billable = No** so the record is complete.

## Ledger

| # | Date | Type | Hours | Billable | Deliverable | Work performed / accomplished | Evidence | Invoiced |
|---|------|------|-------|----------|-------------|-------------------------------|----------|----------|
| 1 | 2026-07-15 | Consulting | 0.5 | No | General | Intro call with Rebecca — current state overview (Fabric, Procore ETL, Sage 100 SQL, team context) | Email thread / call | — |
| 2 | 2026-07-21 | Consulting | 1.5 | No | General | In-person discovery meeting with Affect team — architecture, Excel tracker, SOPs, engagement structure | `meeting-notes/2026-07-21-discovery-meeting.md` | — |
| 3 | 2026-07-21 | Consulting | 1.0 | No | [D1](deliverables/01-discovery-architecture-review.md) | Engagement setup — documented meeting notes, deliverables structure, deep-dive call prep | This repo (initial commits) | — |

## Running totals

| Category | Hours | Billable @ $250 |
|---|---|---|
| Consulting (billable) | 0.0 | $0 |
| Development (billable) | 0.0 | $0 |
| Non-billable (relationship/setup) | 3.0 | — |

*Update totals when adding entries. Billable time starts once the NDA is signed and the Phase 1 scope is agreed.*

## Invoicing record

| Invoice # | Period | Entries | Hours | Amount | Sent | Paid |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |
