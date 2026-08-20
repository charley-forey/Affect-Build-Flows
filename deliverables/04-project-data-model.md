# D4 — Core Project Data Model

**Status:** 🟢 **Live** (2026-08-02) | **Phase:** 1 — Foundation | **Billing:** 4 hrs in Phase 0 | **Target:** ✅ Met

> **Live.** **54 gold tables published** from `CD_Gold_Lakehouse` — conformed dimensions, facts, crosswalks, bridges, the QC tables and the manual placeholders — behind a Direct Lake semantic model of **37 tables, 99 measures and 45 relationships**, with no bidirectional filters anywhere. Dimensions UNION in the keys observed in the facts, so referential integrity holds by construction. A **second** model, `Project Quality Plan`, reads the QC tables (see D5).
>
> **The linchpin is resolved.** `dim_ProjectCrosswalk` (19 rows) maps every project across Procore, Sage and Outbuild; `dim_VendorCrosswalk` and `dim_CostCodeCrosswalk` do the same for vendors and cost codes. `bridge_VendorCostCode` joins the direct-cost header (vendor, no cost code) to its line items (cost code, no vendor) — **407 rows over 398 distinct vendor↔cost-code pairs** (read out of Fabric 2026-08-19), a linkage that exists in no single Procore object. An earlier draft cited "114 distinct pairs covering $1.47M"; 114 is not the distinct-pair count and what it measured is unrecorded, so it has been dropped rather than restated.
>
> **What it found.** One material defect, fixed here: change orders were rolled up per month rather than cumulatively, understating portfolio contract value by **$4,848,379.90** — 16%. Fixed, deployed and regression-tested ([`assessment.md`](../foundation/charley-dev/_docs/assessment.md)). Also 70 cost codes absent from master data, and AR invoices pointing at a job that resolves to no project — all of which would have vanished silently from an Excel join.
>
> **A second material defect, found 2026-08-19.** `dim_Project` read `SageJobNumber` from a view that returns `NULL` under `--source cd`, so **122 of 122 AR invoices resolved to `UNMATCHED`** and **$23,695,760.48 was attributed to no project**. The row count never moved — it is a `LEFT JOIN` — which is exactly the check that had been run to prove the source switch was safe, and `IsInCrosswalk` was derived from the same wrong view, so it read TRUE for all 19 projects: **a dead join certifying itself as healthy.** Fixed by joining `sv_project_crosswalk` explicitly, deduped so a duplicate cannot fan out the project spine. Measured live: projects with a Sage job **0 → 15**, `IsInCrosswalk` TRUE **19 → 15**, unmatched invoices **122 → 24**, AR attributed **$0 → $22,548,861.96**, `fct_FinancialPeriod` **130 → 142** rows (a correction, not a regression — while every invoice read `UNMATCHED`, all AR months collapsed onto one fake project key).
>
> **Still open:** all **17** `man_*` tables (the original 9, plus 8 `man_Qc*` for the PQP intake) are typed and empty, and there is no silver → gold link for them yet — four column-spec questions have to be answered by Affect first ([`_docs/manual-input.md`](../foundation/charley-dev/_docs/manual-input.md)).

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
- [x] Build curated fact/dimension tables — **54 published gold tables**, star schema
- [x] Implement history tracking where needed — `fct_FinancialPeriod` over a 7,670-day `dim_Date`; `snapshot_date` through the medallion
- [x] Data quality checks + reconciliation against source totals — **107 expectations (83 blocking, 24 warning)**, blocking gate; 66 gold assertions offline
- [x] Solve the Excel-only fields — `man_*` tables deployed and typed, with two writers (CSV drop today, SharePoint dataflow later) into one bronze contract. `cd_06_land_manual` now creates **17** (the original 9, plus 8 `man_Qc*` for the PQP intake)
- [ ] **Populate `man_*`** — the silver → gold link is not written; four column-spec questions need Affect
- [x] ~~Promote RFIs to gold~~ — **already done; the task was stale.** `sv_rfis` is defined in `01_source_views_cd.sql` and `23_fct_rfisubmittal.sql` reads it at line 95. Verified live: `fct_RfiSubmittal` = **2,861** = 2,245 submittals + **616 RFIs**. The claim was only ever true under the old `--source existing` default, where `sv_rfis` does not exist and the RFI arm resolves to nothing; that default changed to `cd`, and the task was never closed behind it
- [ ] Extend `dim_ProjectCrosswalk` — **4 of 19** projects have no Sage entry (three templates and City Harvest). The earlier "2" came from the broken `IsInCrosswalk` flag, corrected 2026-08-19
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
| 2026-08-19 | **Two figures on this page corrected and one task closed.** Published gold tables **53 → 54** — `qc_seed_TradeAlias`, a new seed table added by the trade-vocabulary fix — and the DQ gate **103 → 104 expectations** (81 blocking, 23 warning), the new one an ERROR-severity referential check on that table. Three data-quality defects fixed and verified live: submittal statuses **223 → 0**, unmapped trades **970 → 506** across `fct_QcNcr` (459 → **215**) and `fct_QcPunch` (511 → **291**), and unparseable cost codes **807 → 0** — Affect writes CSI divisions 1–9 without a leading zero, so **807 codes, 15% of the 5,433-code master, had been absent from every by-division rollup** and not one of them was actually malformed. Detail in [`build-status.md`](../foundation/charley-dev/_docs/build-status.md). Separately, the standing *"promote RFIs to gold"* task was **stale and is closed**: `fct_RfiSubmittal` reads **2,861** rows — 2,245 submittals plus all 616 RFIs — and has since `deploy_gold.py`'s default source became `cd`. |
| 2026-08-19 | Model live and unchanged. The `man_*` gap is unchanged and remains blocked on four questions for Affect rather than on effort. A **second** subject area — PQP (Project Quality Plan), seeded from the client's 44-sheet QA/QC tracker into `foundation/charley-dev/02-transformation/seed/` — is now **deployed and visible**: 26 trades, 625 checklist items, 93 gates (46 TCO / 23 Fire Alarm / 24 Statutory), 141 statuses and 101 DOH items, alongside the live Procore facts `fct_QcSubmittal` 2,245, `fct_QcPunch` 1,469 and `fct_QcNcr` 850, plus 8 `man_Qc*` tables typed and empty. It gets **its own** semantic model rather than extending this one — see D5. |
| 2026-08-19 | **The QC facts could not have reached any model, and nothing said so.** `deploy_gold.py` carried a **hardcoded `tables` list** that the QC tables had never been added to, so `fct_Qc*` were neither row-checked on deploy nor published into `gold_schema.json` — and a gold table absent from that file **silently cannot appear in any semantic model**. The table exists, holds correct data, and is simply unreachable. Fixed; published tables **45 → 54**. Same class of failure as everything else on this engagement: a green deploy over a missing table. |
| 2026-08-19 | `deploy_gold.py`'s `DEFAULT_SOURCE` changed from `existing` to **`cd`**. A bare re-deploy previously repointed gold at the legacy warehouse silently. |
| 2026-08-19 (evening) | **The dead Sage join, repaired.** `dim_Project` read `SageJobNumber` from a view returning `NULL` under `--source cd`, so **122 of 122 AR invoices resolved to `UNMATCHED`** — $23,695,760.48 attributed to no project — while `IsInCrosswalk`, derived from the same view, reported all 19 projects correctly mapped. Fixed by joining `sv_project_crosswalk` explicitly. Live: Sage jobs **0 → 15**, unmatched **122 → 24**, AR attributed **$0 → $22,548,861.96**, `fct_FinancialPeriod` **130 → 142** rows. |
| 2026-08-19 (evening) | **`dim_Job` built end to end**, closing a chain that had been *described* but never implemented — no bronze table, no dataflow query, no silver parser, no gold DDL. Silver deduplicates on the SharePoint item id rather than `JobNumber`, so two jobs wrongly issued the same number both survive and trip a blocking DQ expectation instead of one being silently discarded. `dim_Job` stops at gold — no visual asks for the job pipeline yet. |
| 2026-08-20 | DQ suite re-counted from `build_suite()`: **107 expectations** (83 blocking, 24 warning), up from 104 as the crosswalk, trade-alias and two `dim_Job` guards landed. The two `dim_Job` checks have not run live yet — the dataflow that fills the table has not been signed in. |
| 2026-07-23 | Vendor / cost-code linkage confirmed as the central modeling problem (`meeting-notes/2026-07-23-warehouse-review.md`). Coverage is uneven — some tables carry cost-code ID, some vendor ID, some neither. Resolution approach: **bridge via the tables that carry both** — e.g. commitments have no vendor ID, but invoices reference both commitment ID and vendor ID, so the invoice bridges vendor → commitment. Same pattern for cost-code vs vendor on requisition/invoice lines. Prerequisite: confirm the ID columns survive transformation (see D2 finding 5). Project↔Sage link exists today via project ID + Sage project ID on the Project dimension. |
