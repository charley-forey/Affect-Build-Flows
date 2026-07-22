# Technical Deep Dive with Rebecca — Prep

**When:** TBD — proposed Thu/Fri (Jul 23–24), 7–9:30am or 4:30–7pm
**Format:** Call, Rebecca screen-sharing the Fabric environment
**Prerequisites:** NDA signed, Fabric access (Affect handling); requested the Excel tracker + any docs/diagrams ahead of the call

## Goal

Understand what exists today well enough to (a) validate/improve the Procore ETL, (b) scope the Sage 100 ingestion, and (c) define the first Power BI deliverable. This is discovery, not coding.

## A. Current architecture walkthrough

Have Rebecca draw/confirm this — determine what is *actual today* vs *aspirational*:

```text
Procore ──→ ETL/API ──→ Fabric Lakehouse ──→ Curated tables ──→ Power BI
Sage 100 ──→ (currently: live SQL query direct from Power BI — bypasses Lakehouse)
```

### Fabric / Lakehouse questions
- [ ] Fabric capacity/SKU, workspace structure, who administers it
- [ ] Lakehouse vs Warehouse — what artifacts exist? Any medallion structure (raw/bronze → curated/gold)?
- [ ] How is the Procore script hosted and scheduled (Fabric notebook, Data Pipeline, Azure Function)? Language?
- [ ] Refresh cadence — actual, and desired
- [ ] Any monitoring, failure alerting, retry logic?
- [ ] How are secrets/API credentials stored?

### Procore ETL questions
- [ ] Which Procore endpoints are pulled today (projects, budgets, commitments, change orders, invoices, RFIs...)?
- [ ] Full refresh or incremental? Any history/change tracking?
- [ ] Known data quality issues
- [ ] Auth method (OAuth app? service account?) and rate-limit handling

### Sage 100 questions
- [ ] What tables/views does the read-only SQL connection expose? Sage 100 *Contractor* schema specifics
- [ ] Which queries does Power BI run against it today?
- [ ] Where does the SQL Server live (on-prem?) — gateway needed for Fabric ingestion?
- [ ] Job cost structure: job numbers, cost codes, cost types — do these map to Procore projects/cost codes?

### Cross-system model
- [ ] What is the shared project identifier across Procore / Sage / Excel? (This is the linchpin.)
- [ ] Where do cost codes live and do they reconcile between systems?

## B. The Excel project tracker (most important artifact)

Ask: *"Walk me through the Excel file as if I were a new project manager. What does every major section represent, where does the data come from, and which fields are manually updated?"*

Classify every field:
- [ ] Manually entered
- [ ] Sourced from a system (which one?)
- [ ] Calculated/derived
- [ ] Historical/snapshot
- [ ] Exists in multiple systems (which wins?)
- [ ] **Exists nowhere except Excel** ← especially important; these need a home (new Lakehouse table, Power App input, etc.)

Goal is not to blindly replicate the spreadsheet — understand the business process it represents and build a better system around that process.

## C. The strategic question

> **"What is the single most valuable business decision this dashboard needs to improve?"**

Candidates: budget overruns, schedule slippage, unpaid invoices, missed change orders, commitments exceeding budget, PMs not updating data, leadership lacking real-time visibility. If "all of them" — push to narrow.

## D. Wrap-up / next steps to land on the call

- [ ] Agree the first deliverable: **Procore + Sage 100 → Lakehouse → curated model → Power BI dashboard replacing the Excel tracker**
- [ ] Agree that I'll produce a short written scope of work (Phase 1 discovery, est. 10–20 hrs @ $250/hr, then development scoped separately)
- [ ] Confirm bi-weekly sync cadence
- [ ] Confirm access checklist: Fabric workspace, Procore API credentials, Sage SQL read access, Excel tracker, SOP docs
