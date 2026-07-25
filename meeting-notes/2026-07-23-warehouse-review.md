# Data Warehouse Review — Affect Group (Rebecca, screen-share)

**Date:** Thursday, July 23, 2026, ~7:30–8:10am (~30 min)
**Format:** Teams call — Rebecca screen-shared her Microsoft Fabric workspace
**Attendees:** Charley (Build Flows), Rebecca Buckley

*(Cleaned up from the call recording.)*

## Purpose

Walk through Rebecca's Fabric build end to end — ingestion → transformation → lakehouses → semantic model → reports — to understand the current foundation and identify what to review, correct, and expand before building the dashboards.

## Workspace structure

Organized in layers: **build / ingestion → transformation → lakehouses → semantic models → reports**. Notebooks are grouped by entity, with Procore dimensions and fact tables in separate folders. The **bronze** layer holds raw data.

## Ingestion (Procore)

- Notebooks call Procore via API: build the request + auth headers, **paginate through all pages**, and pull financial endpoints (commitments, change orders, payment applications). Each notebook **loops over every project** and writes to the Lakehouse.
- **Credentials are hard-coded in a notebook cell.** First fix — move to environment variables / secure secret storage so they aren't rendered in the notebook.
- **Endpoint coverage is financial-first.** Rebecca has focused on financial endpoints and started one for submittals. More will be needed — RFIs, submittals, etc.
- **Rate limits / scope.** Looping every project on every run is heavy; Procore's limits are high but real. Consider pulling only **active** projects and being deliberate about cadence.

## Refresh strategy

- Notebooks currently **replace the whole table on each run** (full reload). Needs to move to **incremental refresh** — pull only new/changed rows.
- Cadence is TBD and likely **per-table** (active jobs change often; some data rarely). Options discussed: daily sync vs. live/webhook updates.

## Transformation

- Dataflows handle cleanup — rename, trim, parse, reshape — and land results in the **silver** lakehouse. Structure looks sound.

## Semantic model

- A **Project dimension** related to all fact tables via **project ID** (Procore ID); a **Sage project ID** also links Sage data to the same project. Currently slices by project only; **no visuals built yet**.

## The core modeling problem — vendor & cost-code linkage

The bulk of the call, and the key blocker to reporting the way they want (slice by **cost code** and by **vendor** across line items):

- Coverage is uneven — **some tables have cost-code ID, some don't; some have vendor ID, some don't.**
- Example: the **commitments** table has a commitment ID but **no vendor ID**; **invoices** reference *both* commitment ID and vendor ID → use the invoice as the **bridge** so selecting a vendor resolves to their commitments.
- Same pattern on requisition/invoice line tables: one has cost-code ID but not vendor, another has vendor but not cost code → needs proper **relational bridging** in the model.
- Likely root cause to check first: **transformations may be dropping the ID columns** the model needs. Fix at ingestion/transformation before modeling.

## Lakehouse

- Two lakehouses (bronze/silver); one exposes a **SQL endpoint**. Tables + files present. Structure is fine — the work is upstream (right fields landing) and downstream (relationships).

## Sage 100

- Currently **live direct query** from Power BI. Plan: once Procore is validated, **mirror the same pattern for Sage** — script → Lakehouse → Power BI queries the Lakehouse instead of live SQL.

## Scheduling / Outbuild

- There's a scheduling tab they'd like to pull, but **Outbuild isn't rolled out yet**, and only one project has complete data.

## Agreed approach — iterative, ingestion-first

1. **Once-over review** of the notebooks/scripts — make sure every needed column/ID is pulled and not dropped in transformation.
2. Then the **relational data model** — resolve the vendor / cost-code bridges.
3. Then **dashboards / reports**.
4. Alongside the review, possibly build **one quick automation** to demonstrate value (e.g., a vendor list with insurance / contract info).

## Action items

- **Charley** — produce the Procore (and Sage) **endpoint inventory** needed to reproduce the Excel report, starting with Procore.
- **Charley** — record video walkthroughs of anything built; share the recordings.
- **Rebecca** — review the deliverables in the hub and validate / correct them.
- **Rebecca** — share the schema details (didn't get to on the call).
- **Both** — Cathal (Cal) + Chris to discuss scope, quote, and engagement housekeeping.

## Overall read

Foundation is genuinely strong — ingestion, transformation layers, and a project-centric semantic model are already in place. The remaining work is validation (correct fields landing, incremental refresh, secrets) and the relational bridging, then reporting sits right on top.
