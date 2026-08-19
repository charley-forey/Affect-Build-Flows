# D1 — Discovery & Architecture Review

**Status:** 🟢 **Complete** (2026-08-02) | **Phase:** 1 — Foundation | **Billing:** $125/hr — 4 hrs in Phase 0 (endpoint inventory); prior assessment work at no charge | **Target:** ✅ Met

> **Delivered.** The endpoint inventory is built and generated from the registry rather than hand-written — **42 endpoints**, every path cited to a line in the Procore cheatsheet ([`_docs/endpoint-inventory.md`](../foundation/charley-dev/_docs/endpoint-inventory.md)). The current-state assessment went well beyond a written review: the whole Fabric workspace was backed up read-only, and the architecture was built, audited and reported on — what is live ([`build-status.md`](../foundation/charley-dev/_docs/build-status.md)), the independent audit ([`assessment.md`](../foundation/charley-dev/_docs/assessment.md)), and [`security-findings.md`](../foundation/charley-dev/_docs/security-findings.md), which found **live Procore and Outbuild credentials in plaintext in five notebooks** and reported them for Affect to rotate. Roadmap and running status: [`status-update.md`](../status-update.md) and [`dashboard.md`](../dashboard.md). Most of the discovery work was given at no charge (`analysis/excel-tracker/`, `powerbi/`, the Jul 23 warehouse walkthrough).

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
- [x] Sign NDA, receive Fabric access — `cforey-c@affect-group.com`, workspace `Build`, folder `charley-dev`
- [x] Deep-dive call with Rebecca — architecture + ETL walkthrough (Jul 23)
- [x] Obtain and analyze Excel project tracker — [`analysis/excel-tracker/`](../analysis/excel-tracker/)
- [x] Document current-state architecture — [`solution-guide.md`](../foundation/charley-dev/_docs/solution-guide.md)
- [x] Field-by-field Excel classification — [`field-inventory.md`](../analysis/excel-tracker/field-inventory.md)
- [x] Data model recommendations — [`powerbi/semantic-model.md`](../powerbi/semantic-model.md)
- [x] **Endpoint inventory — 42 endpoints**, generated from `config/endpoints.yml` so it cannot drift — [`endpoint-inventory.md`](../foundation/charley-dev/_docs/endpoint-inventory.md)
- [x] Written Phase 1 findings — `build-status.md`, `assessment.md`, `security-findings.md`
- [x] Review findings with Rebecca — platform review Aug 13

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
| 2026-07-24 | Scope, terms & engagement call with Cathal (~8am, ~20 min). Terms agreed: $125/hr flat, 9–10 months, 20 hrs initial scope, 5 hrs/wk ongoing, mentorship as core billable scope. This deliverable's remaining work narrows to the endpoint inventory (4 hrs in Phase 0). Notes: `meeting-notes/2026-07-24-cathal-scope-call.md`. Fabric MCP wired to the repo. |
| 2026-08-02 | **Closed.** Endpoint inventory generated from the registry (42 endpoints, every path cited). Current-state assessment delivered as three documents rather than one: what is live (`build-status.md`), the independent audit (`assessment.md`), and the credential exposure found in the existing workspace (`security-findings.md`). |
| 2026-08-19 | Inventory regenerated after the registry grew; the count is **42**, not the 36 an earlier stale copy of the generated file reported. The registry is the source of truth and the document is generated from it. |
