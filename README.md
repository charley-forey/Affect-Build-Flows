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

## Engagement status (as of Jul 24, 2026)

- ✅ Intro call with Rebecca (Jul 15)
- ✅ In-person discovery meeting with wider team (Tue Jul 21, 8:30am at their office)
- ✅ Excel project reporting template received (Jul 22) and **fully assessed** — see `analysis/excel-tracker/`
- ✅ Power BI build kit drafted — semantic model, DAX, report spec, theme (`powerbi/`)
- ✅ **Data warehouse review with Rebecca (Thu Jul 23)** — Fabric workspace walkthrough; findings in `meeting-notes/2026-07-23-warehouse-review.md`
- ✅ **Fabric MCP** wired for the repo (`.mcp.json`) to read notebooks/schema and test joins once access lands — see `resources/microsoft-fabric/`
- ✅ **Scope, terms & engagement agreed with Cathal — Fri Jul 24** (~20 min call). $125/hr, 9–10 months, 20 hrs initial scope, 5 hrs/wk ongoing — see `meeting-notes/2026-07-24-cathal-scope-call.md`
- 🟡 **Phase 0 planned** — the initial 20-hour month is scoped and ready to start (`dashboard.md` → Phase 0)
- ⏳ Affect working internally on **Fabric access + NDA** — the only thing gating the start

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
| Microsoft Fabric (Lakehouse) | Data warehouse | Live — Rebecca built it |
| Procore | Project management & costing | ETL built (API → Fabric Lakehouse) — needs review |
| Sage 100 Contractor | Accounting, invoicing, payroll | Read-only SQL Server connection, currently queried live from Power BI — **needs ingestion script into Lakehouse** |
| Outbuild | Scheduling (estimating per meeting notes) | Not integrated yet — likely next |
| Ramp | Vendor payments | Not integrated |
| ADP | Payroll | Not integrated |
| Bluebeam / Navisworks | Design & drawings | Not integrated |
| Outlook / OneDrive | Email & document management | Not integrated |
| Power BI | Reporting | In use (live Sage SQL queries today) |
| Power Automate | Workflow automation | Planned (payments, lien waivers) |
| Drones | Potential future | — |

## Files

- `dashboard.md` — **start here**: rollup of all deliverables, integration status, blockers, hours summary
- `hours-log.md` — append-only time ledger (billing/validation source of truth) + invoicing record
- `deliverables/` — one file per deliverable (D1–D7): objective, scope, key data, integration approach, tasks, acceptance criteria, files. New deliverables copy `_template.md`.
- `analysis/excel-tracker/` — **full teardown of the client's Monthly Progress Report workbook**: field inventory, decoded formulas, dashboard cell map, drop-down vocabulary, and 14 verified defects
- `src/` — **the pipeline code**. `src/procore/` takes RFIs & submittals from the Procore API through bronze → silver → gold and runs end to end today; `src/README.md` explains the layers and how to deploy into Fabric
- `powerbi/` — the build kit: semantic model, DAX measure library, report spec, theme, manual-input template, phased build plan, and `AffectProjectReport.pbip` (the TMDL model over the pipeline's gold tables)
- `resources/` — curated documentation and links, one folder per solution (Procore, Sage 100 Contractor, Fabric, Power BI, Power Automate, Outbuild, Ramp, ADP)
- `.mcp.json` — Fabric MCP server config for Claude Code (reads the live workspace once access is granted; see `resources/microsoft-fabric/`)
- `call-prep/2026-07-23-warehouse-review.md` — agenda, findings summary, and the information request for the warehouse review call
- `meeting-notes/` — notes from calls and meetings (discovery Jul 21, warehouse review Jul 23, **scope & terms Jul 24**)
- `internal/` — not client-facing: strategy, communications log, and sent-email drafts
- `YY-000 PROJECT NAME_InternalReport_YYMMDD.xlsx` — the client's reporting template (the spec for D5)
