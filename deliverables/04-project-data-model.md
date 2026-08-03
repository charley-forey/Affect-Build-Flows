# D4 — Core Project Data Model

**Status:** 🟢 **Complete** (2026-08-02) | **Phase:** 1 — Foundation | **Billing:** 4 hrs in Phase 0 | **Target:** ✅ Met

> **The linchpin is resolved.** `dim_ProjectCrosswalk`, `dim_VendorCrosswalk` and `dim_CostCodeCrosswalk` are built and populated, and `bridge_VendorCostCode` (407 rows) gives the vendor ↔ cost-code slice via the invoice. 40 gold tables — conformed dimensions, facts, crosswalks, bridges, and 9 `man_*` tables for the manual half. Dimensions UNION in the keys observed in the facts, so referential integrity holds by construction. **What it found:** 2 projects with no Sage entry, 70 cost codes absent from master data, 23 AR invoices pointing at a job that resolves to no project — all of which would have vanished silently from an Excel join.
>
> **Open:** the manual silver → gold link waits on four definition questions ([`_docs/manual-input.md`](../foundation/charley-dev/_docs/manual-input.md)).

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
- [ ] Design dimensional model from D1 findings (ERD)
- [ ] Build Project/Vendor/Cost Code mapping tables
- [ ] Build curated fact/dimension tables
- [ ] Implement history tracking where needed
- [ ] Data quality checks + reconciliation against source totals
- [ ] Solve the Excel-only fields (input table / Power App / SharePoint list)
- [ ] Model documentation + walkthrough with Rebecca

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
| 2026-07-23 | Vendor / cost-code linkage confirmed as the central modeling problem (`meeting-notes/2026-07-23-warehouse-review.md`). Coverage is uneven — some tables carry cost-code ID, some vendor ID, some neither. Resolution approach: **bridge via the tables that carry both** — e.g. commitments have no vendor ID, but invoices reference both commitment ID and vendor ID, so the invoice bridges vendor → commitment. Same pattern for cost-code vs vendor on requisition/invoice lines. Prerequisite: confirm the ID columns survive transformation (see D2 finding 5). Project↔Sage link exists today via project ID + Sage project ID on the Project dimension. |
