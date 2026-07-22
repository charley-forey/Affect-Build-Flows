# D4 — Core Project Data Model

**Status:** 🔴 Not started | **Phase:** 1 — Foundation | **Billing:** TBD after D1 | **Target:** TBD

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
- (add: ERD, mapping tables doc, notebook links)

## Log
| Date | Note |
|---|---|
| | |
