# D1 — Discovery & Architecture Review

**Status:** 🟡 In progress | **Phase:** 1 — Foundation | **Billing:** Fixed review — $250/hr, not to exceed 10 hrs ($2,500); prior assessment work included at no charge | **Target:** ~2 weeks after access granted

> This review is priced small on purpose — it's what makes the build work scopable. The build (per-solution scripts + SQL + Lakehouse landing, then the dashboard) is quoted block-by-block from what this review finds, not committed up front. See `dashboard.md` → Billing approach.

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
- [x] Prep deep-dive agenda
- [ ] Sign NDA, receive Fabric access
- [ ] Deep-dive call with Rebecca — architecture + ETL walkthrough
- [x] Obtain and analyze Excel project tracker — [`analysis/excel-tracker/`](../analysis/excel-tracker/)
- [ ] Document current-state architecture (diagram + notes)
- [x] Field-by-field Excel classification — [`field-inventory.md`](../analysis/excel-tracker/field-inventory.md)
- [x] Data model recommendations — [`powerbi/semantic-model.md`](../powerbi/semantic-model.md)
- [ ] Written Phase 1 findings + prioritized roadmap + scope of work for D2–D5
- [ ] Review findings with Rebecca/Chris; get sign-off on next scope

## Acceptance criteria
- Written current-state assessment delivered to Affect
- Excel tracker fully mapped to sources (including "Excel-only" fields with a proposed home)
- Roadmap and scope of work for the next deliverables agreed

## Files & resources
- **[`analysis/excel-tracker/`](../analysis/excel-tracker/)** — full teardown of the reporting template: field inventory, decoded formulas, dashboard cell map, drop-down vocabulary, 14 verified defects, open questions
- **[`powerbi/`](../powerbi/)** — semantic model, DAX library, report spec, theme, manual-input template, phased build plan
- **[`resources/`](../resources/)** — curated documentation per solution
- **[`resources/microsoft-fabric/README.md`](../resources/microsoft-fabric/README.md#ai-assisted-access--fabric-mcp-server)** — Fabric MCP server for reading notebooks/schema and testing joins directly once access lands
- `meeting-notes/2026-07-21-discovery-meeting.md`
- (add: architecture diagram, written findings summary for Affect)

## Log
| Date | Note |
|---|---|
| 2026-07-21 | Discovery meeting held; NDA + Fabric access pending on Affect's side |
| 2026-07-22 | Excel reporting template received and fully assessed. 14 defects found, 3 affecting reported numbers — notably 42% of the scorecard weight is disconnected from project reality. Power BI build kit drafted. |
| 2026-07-23 | Data warehouse review held with Rebecca — Fabric workspace walkthrough (ingestion, transformation, lakehouses, semantic model). Notes: `meeting-notes/2026-07-23-warehouse-review.md`. Key findings: credentials hard-coded in a notebook, full-table reload (needs incremental refresh), endpoint coverage financial-only, vendor/cost-code bridging unresolved. Foundation is strong; remaining work is validation + relational bridging. |
| 2026-07-24 | Scope & deliverables call with Cathal (~8am). Billing reframed to fixed capped review + per-solution build. Fabric MCP wired to the repo. |
