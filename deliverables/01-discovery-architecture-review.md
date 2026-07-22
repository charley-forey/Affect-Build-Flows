# D1 — Discovery & Architecture Review

**Status:** 🟡 In progress | **Phase:** 1 — Foundation | **Billing:** Hourly $250, est. 10–20 hrs | **Target:** ~2 weeks after access granted

## Objective
Understand and document Affect's current data environment well enough to validate the Procore ETL, scope the Sage 100 ingestion, and define the first Power BI deliverable — producing a written current-state assessment and prioritized roadmap.

## Scope
**In:** Fabric environment review, Procore ETL review, Sage 100 schema review, Excel tracker field-by-field analysis, data-source mapping, initial data model recommendations, roadmap, first-deliverable definition.
**Out:** Any build work (that becomes D2–D5).

## Key data
- Fabric workspace: capacity, Lakehouse artifacts, medallion structure (or lack of), scheduling, secrets handling
- Procore: endpoints pulled today (projects, budgets, commitments, change orders, invoices), refresh mode, auth
- Sage 100 Contractor: exposed tables/views, job cost structure (jobs, cost codes, cost types), server location (gateway needed?)
- Excel tracker: every field classified — manual / system-sourced / calculated / historical / Excel-only
- Cross-system: the shared project identifier and cost-code reconciliation between Procore and Sage

## Integration approach
N/A — assessment deliverable. Output informs D2–D4 designs.

## Tasks
- [x] Prep deep-dive agenda (`call-prep/technical-deep-dive-rebecca.md`)
- [ ] Sign NDA, receive Fabric access
- [ ] Deep-dive call with Rebecca — architecture + ETL walkthrough
- [ ] Obtain and analyze Excel project tracker
- [ ] Document current-state architecture (diagram + notes)
- [ ] Field-by-field Excel classification
- [ ] Data model recommendations
- [ ] Written Phase 1 findings + prioritized roadmap + scope of work for D2–D5
- [ ] Review findings with Rebecca/Chris; get sign-off on next scope

## Acceptance criteria
- Written current-state assessment delivered to Affect
- Excel tracker fully mapped to sources (including "Excel-only" fields with a proposed home)
- Roadmap and scope of work for the next deliverables agreed

## Files & resources
- `call-prep/technical-deep-dive-rebecca.md`
- `meeting-notes/2026-07-21-discovery-meeting.md`
- (add: architecture diagram, Excel field map, findings doc)

## Log
| Date | Note |
|---|---|
| 2026-07-21 | Discovery meeting held; NDA + Fabric access pending on Affect's side |
