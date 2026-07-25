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
| Cathal Egan | Leadership | Copied on emails |

## Engagement status (as of Jul 24, 2026)

- ✅ Intro call with Rebecca (Jul 15)
- ✅ In-person discovery meeting with wider team (Tue Jul 21, 8:30am at their office)
- ✅ Excel project reporting template received (Jul 22) and **fully assessed** — see `analysis/excel-tracker/`
- ✅ Power BI build kit drafted — semantic model, DAX, report spec, theme (`powerbi/`)
- ✅ **Data warehouse review with Rebecca (Thu Jul 23)** — Fabric workspace walkthrough; findings in `meeting-notes/2026-07-23-warehouse-review.md`
- ✅ Billing reframed to a **fixed capped review + per-solution build** model — see `dashboard.md` → Billing approach
- ✅ **Fabric MCP** wired for the repo (`.mcp.json`) to read notebooks/schema and test joins once access lands — see `resources/microsoft-fabric/`
- 📅 **Scope & deliverables call with Cathal — Fri Jul 24, ~8am**
- ⏳ Affect working internally on **Fabric access + NDA**

## Engagement structure

- **Discovery / architecture review first:** one small, **fixed capped fee** — the only thing quoted up front, because it's what makes the build scopable and correct
- **Build work:** scoped **per solution** from the review's findings (connect → format → validate SQL → land in Lakehouse), then the dashboard on top — committed block-by-block, never as a lump sum
- **Advisory / mentorship / learning:** $250/hr for advisory; teaching Rebecca and evening/learning time logged non-billable
- Full detail: `dashboard.md` → **Billing approach**
- Role: **architect + accelerator + expert resource** — enabling Rebecca and the Affect team to build and maintain their own data platform

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
- `powerbi/` — the build kit: semantic model, DAX measure library, report spec, theme, manual-input template, phased build plan
- `resources/` — curated documentation and links, one folder per solution (Procore, Sage 100 Contractor, Fabric, Power BI, Power Automate, Outbuild, Ramp, ADP)
- `.mcp.json` — Fabric MCP server config for Claude Code (reads the live workspace once access is granted; see `resources/microsoft-fabric/`)
- `call-prep/2026-07-23-warehouse-review.md` — agenda, findings summary, and the information request for the warehouse review call
- `meeting-notes/` — notes from calls and meetings (discovery Jul 21, warehouse review Jul 23)
- `YY-000 PROJECT NAME_InternalReport_YYMMDD.xlsx` — the client's reporting template (the spec for D5)
