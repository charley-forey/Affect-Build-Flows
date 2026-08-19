# D4 — Core Project Data Model

**Status:** 🟢 **Live** (2026-08-02) | **Phase:** 1 — Foundation | **Billing:** 4 hrs in Phase 0 | **Target:** ✅ Met

> **Live.** **40 gold tables** in `CD_Gold_Lakehouse` — conformed dimensions, facts, crosswalks, bridges and the nine `man_*` placeholders — behind a Direct Lake semantic model of **37 tables, 99 measures and 45 relationships**, with no bidirectional filters anywhere. Dimensions UNION in the keys observed in the facts, so referential integrity holds by construction.
>
> **The linchpin is resolved.** `dim_ProjectCrosswalk` (19 rows) maps every project across Procore, Sage and Outbuild; `dim_VendorCrosswalk` and `dim_CostCodeCrosswalk` do the same for vendors and cost codes. `bridge_VendorCostCode` joins the direct-cost header (vendor, no cost code) to its line items (cost code, no vendor) — **407 rows over 398 distinct vendor↔cost-code pairs** (read out of Fabric 2026-08-19), a linkage that exists in no single Procore object. An earlier draft cited "114 distinct pairs covering $1.47M"; 114 is not the distinct-pair count and what it measured is unrecorded, so it has been dropped rather than restated.
>
> **What it found.** One material defect, fixed here: change orders were rolled up per month rather than cumulatively, understating portfolio contract value by **$4,848,379.90** — 16%. Fixed, deployed and regression-tested ([`assessment.md`](../foundation/charley-dev/_docs/assessment.md)). Also 2 projects with no Sage entry, 70 cost codes absent from master data, and 23 AR invoices pointing at a job that resolves to no project — all of which would have vanished silently from an Excel join.
>
> **Still open:** the nine `man_*` tables are typed and empty, and there is no silver → gold link for them yet — four column-spec questions have to be answered by Affect first ([`_docs/manual-input.md`](../foundation/charley-dev/_docs/manual-input.md)).

## Objective
A curated, relationally-mapped set of Lakehouse tables that unify Procore + Sage 100 (+ Excel-only fields) into a single project-centric model — the semantic foundation every report and automation builds on.

## Scope
**In:** Conformed dimensions (Project, Vendor, Cost Code, Date, ...), fact tables (budget, cost, commitments, change orders, invoices/payments), cross-system key mapping, history/change tracking, data quality rules, a home for Excel-only fields (e.g., a small input table or Power App).
**Out:** Visualization (D5).

## Key data
- **The project key:** how a Procore project maps to a Sage job — the linchpin identified in discovery
- Cost code reconciliation between systems
- Every Excel tracker field mapped to a modeled column (from D1 classification)
- Fields that exist nowhere except Excel → new managed input mechanism

## Integration approach
Raw Lakehouse tables (D2, D3) → curated/gold tables via Fabric notebooks or SQL, star-schema style, with documented lineage. Change tracking via snapshot or SCD approach where history matters (budget vs actual over time).

## Tasks
- [x] Design dimensional model from D1 findings — [`semantic-model.md`](../powerbi/semantic-model.md)
- [x] Build Project/Vendor/Cost Code mapping tables — `dim_ProjectCrosswalk`, `dim_VendorCrosswalk`, `dim_CostCodeCrosswalk`
- [x] Build curated fact/dimension tables — 40 gold tables, star schema
- [x] Implement history tracking where needed — `fct_FinancialPeriod` over a 7,670-day `dim_Date`; `snapshot_date` through the medallion
- [x] Data quality checks + reconciliation against source totals — 63 expectations, blocking gate; 66 gold assertions offline
- [x] Solve the Excel-only fields — nine `man_*` tables, deployed and typed, with two writers (CSV drop today, SharePoint dataflow later) into one bronze contract
- [ ] **Populate `man_*`** — the silver → gold link is not written; four column-spec questions need Affect
- [ ] Promote RFIs to gold — 616 rows sit in `cd_silver_rfis` and never reach `fct_RfiSubmittal`
- [ ] Extend `dim_ProjectCrosswalk` — 2 projects still have no Sage entry
- [ ] Model documentation + recorded walkthrough with Rebecca

## Acceptance criteria
- Every field on the Excel tracker is answerable from the curated model (or has a managed input home)
- Totals reconcile to Procore and Sage
- Model documented; Rebecca can add a column/table following the pattern

## Files & resources
- **[`powerbi/semantic-model.md`](../powerbi/semantic-model.md)** — the star schema: 11 fact tables, 8 dimensions, 6 manual/narrative tables, 2 config tables, with grain, keys, and relationship cardinality
- **[`powerbi/source-mapping.md`](../powerbi/source-mapping.md)** — every field → Procore endpoint / Sage table / manual input, including which pulls the Procore↔Sage connector makes redundant
- **[`powerbi/manual-input-template.md`](../powerbi/manual-input-template.md)** — the home for the ~40% of fields that exist nowhere but Excel
- **[`analysis/excel-tracker/field-inventory.md`](../analysis/excel-tracker/field-inventory.md)** — every tracker field classified input/formula/dropdown with its target source system
- (add: ERD export, notebook links)

## Log
| Date | Note |
|---|---|
| 2026-08-02 | **Live.** 40 gold tables, Direct Lake model of 37 tables / 99 measures / 45 relationships, all 99 measures evaluated against real data. `bridge_VendorCostCode` resolves Phase 0 item 3. The $4.85M change-order defect found, fixed, deployed and covered by three new regression assertions — the original fixture put all three change orders in one month, where a per-month and a cumulative roll-up are arithmetically identical, so the gate had been watching the right number through a fixture that could not express the bug. |
| 2026-08-19 | Model and gold tables unchanged and live. The `man_*` gap is unchanged and remains blocked on four questions for Affect rather than on effort. A **second** subject area — PQP (Project Quality Plan), seeded from the client's 44-sheet QA/QC tracker into `foundation/charley-dev/02-transformation/seed/` — is now **deployed**: 26 trades, 625 checklist items, 93 gates (46 TCO / 23 Fire Alarm / 24 Statutory), 141 statuses and 101 DOH items, alongside the live Procore facts `fct_QcSubmittal` 2,245, `fct_QcPunch` 1,469 and `fct_QcNcr` 850. **No PQP semantic model or report exists yet** — it gets its own model rather than extending this one. |
| 2026-07-23 | Vendor / cost-code linkage confirmed as the central modeling problem (`meeting-notes/2026-07-23-warehouse-review.md`). Coverage is uneven — some tables carry cost-code ID, some vendor ID, some neither. Resolution approach: **bridge via the tables that carry both** — e.g. commitments have no vendor ID, but invoices reference both commitment ID and vendor ID, so the invoice bridges vendor → commitment. Same pattern for cost-code vs vendor on requisition/invoice lines. Prerequisite: confirm the ID columns survive transformation (see D2 finding 5). Project↔Sage link exists today via project ID + Sage project ID on the Project dimension. |
