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

A forwardable write-up of the build lives in [`status-update.md`](status-update.md).

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
| Microsoft Fabric | Data platform | **Live.** Rebecca's original warehouse, untouched; our `charley-dev` medallion alongside it — 3 lakehouses, 8 notebooks, a nightly pipeline |
| Procore | Project management & costing | 🟢 **42 endpoints live**, registry-driven, production tenant → bronze. Extraction currently runs locally pending Key Vault. 403 on `punch_item_types` / `schedule` |
| Sage 100 Contractor | Accounting, invoicing, payroll | 🔵 `CD_Sage_Ingest` **deployed and gateway-wired**, 8 tables. Blocked on one connection permission grant |
| Outbuild | Scheduling & milestones | 🔵 16 endpoints **built and verified**, cannot run — `OUTBUILD_API_TOKEN` offered by email Aug 11, **in transit**. The **only** milestone source anywhere |
| Azure Key Vault | Secret storage for ingestion | 🔵 Vault `OneLake` **exists**; RBAC-mode, and our identity needs one role — *Key Vault Secrets Officer* — before a secret can be written |
| SharePoint | The ~40% of the report that lives in no system, plus estimating/bidding job folders | 🟡 Provisioning scripts written — manual-input lists, the 8 PQP intake lists, and the `Job Register`. A CSV path works today with no admin ticket. **No site exists yet** |
| Power BI | Reporting | 🟢 **Monthly Progress Report live** — 12 pages, 180 visuals, Direct Lake over the gold model. The PQP report is not built yet |
| Power Automate | Workflow automation | 🟡 **Built, not deployed** — Estimating Setup and Convert to Bidding in `power-automate/`. Payments and lien waivers still gated on Chris's SOPs |
| Ramp | Vendor payments | 🔴 Not integrated — API docs vendored in `resources/ramp/` |
| ADP | Payroll | 🔴 Not integrated |
| Bluebeam / Navisworks | Design & drawings | 🔴 Not integrated |
| Outlook / OneDrive | Email & document management | 🔴 Not integrated |
| Drones | Potential future | — |

## Files

**Read in this order:**

| # | File | What it is |
|---|---|---|
| 1 | [`status-update.md`](status-update.md) | **The team update.** What was built, what it found, what needs verification, what is blocked, what comes next. Written to be handed over as-is |
| 2 | [`dashboard.md`](dashboard.md) | Deliverable rollup, integration status, hours, blockers, **roadmap** |
| 3 | [`foundation/charley-dev/_docs/solution-guide.md`](foundation/charley-dev/_docs/solution-guide.md) | How the platform actually works — the engineering read |
| 4 | [`foundation/charley-dev/_docs/assessment.md`](foundation/charley-dev/_docs/assessment.md) | Independent audit of the above, checked against the live workspace |

**Everything else:**

- `hours-log.md` — append-only time ledger (billing/validation source of truth) + invoicing record
- `deliverables/` — one file per deliverable (D1–D8): objective, scope, key data, integration approach, tasks, acceptance criteria. New deliverables copy `_template.md`
- **`foundation/`** — **the build.** A read-only backup of the whole Fabric `Build` workspace, plus `foundation/charley-dev/`: our self-contained platform — ingestion, medallion SQL, lakehouse and semantic-model definitions, the report, the orchestration DAG, the offline test harness, and `_docs/` (`solution-guide.md` first; `keyvault-runbook.md` for the vault position)
- `updates/` — client-facing status updates written to be forwarded (`2026-08-13-executive-update.md`)
- `power-automate/` — **the estimating/bidding job-folder automation**: SharePoint provisioning script, both flow definitions, and the offline test suite. Built, not yet deployed
- `analysis/excel-tracker/` — full teardown of the client's Monthly Progress Report workbook: field inventory, decoded formulas, dashboard cell map, drop-down vocabulary, and the 14 verified defects
- `analysis/pqp-workbook/` — teardown of the QA/QC tracker (Project Quality Plan): 5 verified defects, the 44-sheets-to-9-tables structure, and the open questions for Affect
- `src/procore/` — the original RFI/submittal reference pipeline (Jul 26). Superseded by `foundation/charley-dev/` but kept: it is the smallest complete example of the pattern, and a good teaching artifact
- `powerbi/` — the design kit that preceded the build: semantic model, DAX measure library, report spec, theme, manual-input template, phased build plan
- `resources/` — vendored documentation, one folder per solution. Includes the **full Sage 100 Contractor and Outbuild API doc sets** as markdown, a Procore endpoint cheatsheet verified against the 2,111-path OAS, and [`resources/power-bi/monthly-progress-report/`](resources/power-bi/monthly-progress-report/) — **the built dashboard, page by page**, if you want to see the deliverable before reading how it was built
- `.mcp.json` — Fabric MCP server config for Claude Code (live workspace exploration; see `resources/microsoft-fabric/`)
- `meeting-notes/` — notes from calls and meetings (discovery Jul 21, warehouse review Jul 23, **scope & terms Jul 24**, **platform review Aug 13**)
- `call-prep/` — agendas and information requests prepared for calls
- `internal/` — not client-facing: strategy, communications log, and sent-email drafts
- `YY-000 PROJECT NAME_InternalReport_YYMMDD.xlsx` — the client's reporting template (the spec for D5)
