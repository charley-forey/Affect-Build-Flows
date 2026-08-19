# Affect Group Engagement

Home base for the Affect Group consulting engagement (construction data & automation).

## Client

- **Affect Group** — General contractor, residential & commercial, ~14 years in business
- 389 Fifth Avenue, Suite 504, New York NY 10016 | affect-group.com

## Contacts

| Name | Role | Notes |
|---|---|---|
| Rebecca Buckley | Accounts Payable & Receivable | Primary contact & internal technical lead — built the Fabric data lake and Procore ETL. RBuckley@affect-group.com, O: 917-830-4204, C: 917-774-0635 |
| Chris Mayer | Fractional CTO | Ex-Suffolk Chief Innovation Officer. Developing SOPs for all business functions. In office Mon/Tue. |
| Bernard McNamee | Leadership | Copied on emails |
| Cathal Egan (Cal) | Leadership | **Commercial owner of the engagement** — agreed scope, terms and rate (Jul 24). C: 929-202-3638 |

## Engagement status (as of Aug 19, 2026)

- ✅ Intro call with Rebecca (Jul 15)
- ✅ In-person discovery meeting with wider team (Tue Jul 21, 8:30am at their office)
- ✅ Excel project reporting template received (Jul 22) and **fully assessed** — see `analysis/excel-tracker/`
- ✅ Power BI build kit drafted — semantic model, DAX, report spec, theme (`powerbi/`)
- ✅ **Data warehouse review with Rebecca (Thu Jul 23)** — Fabric workspace walkthrough; findings in `meeting-notes/2026-07-23-warehouse-review.md`
- ✅ **Scope, terms & engagement agreed with Cathal — Fri Jul 24** (~20 min call). $125/hr, 9–10 months, 20 hrs initial scope, 5 hrs/wk ongoing — see `meeting-notes/2026-07-24-cathal-scope-call.md`
- ✅ **Fabric access granted** (`cforey-c@affect-group.com`) — workspace `Build`, folder `charley-dev`
- ✅ **The platform is built and running (Aug 1–2)** — three lakehouses, Procore ingestion from the production tenant, a nightly pipeline with a 63-expectation DQ gate, a 37-table Direct Lake model and a 12-page Monthly Progress Report. See `foundation/charley-dev/`
- ✅ **`CD_Sage_Ingest` deployed (Aug 3)** — live in the `charley-dev` folder, bound to the existing on-prem gateway, inert until one *Can use* grant lands
- ✅ **$4.85M defect found, fixed and deployed** — portfolio contract value was understated 16% by a per-month rather than cumulative change-order roll-up
- ✅ **Fabric MCP** wired for the repo (`.mcp.json`) — used for live exploration (`execute_sql_query` / `execute_dax_query`); item creation stays on the committed REST deploy path
- ✅ **Platform review with Rebecca — Thu Aug 13** (`meeting-notes/2026-08-13-rebecca-platform-review.md`). Rebecca's workload has increased; Charley absorbs the build load, mentoring goes async/recorded
- ✅ **Azure subscription and Key Vault now exist (Aug 19)** — "Azure subscription 1" on tenant *Affect Build LLC*, and vault `OneLake`. The only purchasing decision on the blocker list is closed
- 🟡 **PQP (Project Quality Plan) subject area in progress** — the client's 44-sheet `026-025 SAUNA LOUNGE QA - QC TRACKER` extracted to seed data (26 trades, 625 checklist items, 93 statutory gates, 101 DOH items, 143 status-vocabulary rows); a second semantic model and report follow
- 🟡 **Two Power Automate flows in progress** — Estimating Setup, and Convert to Bidding
- 🔵 **Six items with Affect**, every one a permission grant or a decision — the largest is now a single Key Vault role assignment. See `dashboard.md` → Blockers
- ⚠️ **Existing production reporting is stale** — Sage stops Jul 20, Outbuild Jul 14, almost certainly the same gateway issue

## Engagement structure

Agreed with Cathal Egan, Jul 24, 2026. Full detail: `dashboard.md` → **Commercial terms**.

| | |
|---|---|
| **Rate** | **$125/hr** — flat across advisory, development, and mentoring |
| **Term** | **9–10 months** |
| **Initial scope** | **20 hours over ~1 month** (Phase 0) |
| **Ongoing** | **5 hrs/week** — workflow building + mentoring Rebecca |
| **Rebecca's access** | Text, call, email — unlimited and **not charged** |

- **Two things are being built at once:** the data platform, and Rebecca's ability to run it.
  Mentorship is core billable scope, delivered as collaborative working sessions and
  **recorded on video** so they become a reusable internal asset.
- **Rebecca's trajectory** — growing into an Operations role focused on technology, bringing
  deep accounting domain knowledge and a process-driven approach. Knowledge transfer runs
  both directions.
- Role: **architect + accelerator + teacher** — enabling Affect to build and maintain their
  own data platform, not becoming a permanent dependency.

### Availability

| | |
|---|---|
| Meetings (video / in-person) | M–F **7–9am** and **5–7pm**; weekends on request |
| Text / email / call | Throughout the day, **1–4 hr response** |
| Build & recording | Evenings |
| On-site | Encouraged — discovery, working sessions, presentations, implementation |

## Their tech stack

| System | Purpose | Integration status |
|---|---|---|
| Microsoft Fabric (Lakehouse) | Data warehouse | Live — Rebecca's, plus our isolated `charley-dev` medallion alongside it |
| Procore | Project management & costing | 🟢 **Live** — 42-endpoint config-driven extractor → `CD_Bronze`, production tenant. 403 on `punch_item_types` / `schedule` |
| Sage 100 Contractor | Accounting, invoicing, payroll | 🔵 `CD_Sage_Ingest` **deployed** and inert — one gateway permission grant away |
| Outbuild | Scheduling / milestones | 🔵 Built and verified, cannot run yet — `OUTBUILD_API_TOKEN` offered by email Aug 11, **in transit**. The only milestone source anywhere |
| Azure Key Vault | Secret storage for ingestion | 🔵 Vault `OneLake` **exists**; RBAC-mode, and our identity needs one role — *Key Vault Secrets Officer* — before a secret can be written |
| Ramp | Vendor payments | Not integrated |
| ADP | Payroll | Not integrated |
| Bluebeam / Navisworks | Design & drawings | Not integrated |
| Outlook / OneDrive | Email & document management | Not integrated |
| Power BI | Reporting | In use (live Sage SQL queries today) |
| Power Automate | Workflow automation | 🟡 **In progress** — Estimating Setup and Convert to Bidding. Payments and lien waivers still gated on Chris's SOPs |
| Drones | Potential future | — |

## Files

- `dashboard.md` — **start here**: rollup of all deliverables, integration status, blockers, hours summary
- `foundation/charley-dev/` — **the platform**. `_docs/solution-guide.md` explains what it is and how it works; `_docs/build-status.md` is what is live, measured out of Fabric; `_docs/assessment.md` is the independent audit
- `updates/` — client-facing status updates written to be forwarded (`2026-08-13-executive-update.md`)
- `hours-log.md` — append-only time ledger (billing/validation source of truth) + invoicing record
- `deliverables/` — one file per deliverable (D1–D8): objective, scope, key data, integration approach, tasks, acceptance criteria, files. New deliverables copy `_template.md`.
- `analysis/excel-tracker/` — **full teardown of the client's Monthly Progress Report workbook**: field inventory, decoded formulas, dashboard cell map, drop-down vocabulary, and 14 verified defects
- `analysis/pqp-workbook/` — **teardown of the QA/QC tracker (Project Quality Plan)**: 5 verified defects, the 44-sheets-to-9-tables structure, and the open questions for Affect
- `power-automate/` — **the estimating/bidding folder automation**: SharePoint provisioning script, both flow definitions, and the offline test suite
- `src/` — **the pipeline code**. `src/procore/` takes RFIs & submittals from the Procore API through bronze → silver → gold and runs end to end today; `src/README.md` explains the layers and how to deploy into Fabric
- `powerbi/` — the build kit: semantic model, DAX measure library, report spec, theme, manual-input template, phased build plan, and `AffectProjectReport.pbip` (the TMDL model over the pipeline's gold tables)
- `resources/` — curated documentation and links, one folder per solution (Procore, Sage 100 Contractor, Fabric, Power BI, Power Automate, Outbuild, Ramp, ADP)
- `.mcp.json` — Fabric MCP server config for Claude Code. Access is granted and it reads the live workspace; used for exploration (`execute_sql_query` / `execute_dax_query`) while item creation stays on the committed REST deploy path. See `resources/microsoft-fabric/`
- `call-prep/2026-07-23-warehouse-review.md` — agenda, findings summary, and the information request for the warehouse review call
- `meeting-notes/` — notes from calls and meetings (discovery Jul 21, warehouse review Jul 23, **scope & terms Jul 24**, **platform review Aug 13**)
- `internal/` — not client-facing: strategy, communications log, and sent-email drafts
- `YY-000 PROJECT NAME_InternalReport_YYMMDD.xlsx` — the client's reporting template (the spec for D5)
