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

## Engagement status (as of Aug 2, 2026)

**Phase 0 is delivered.** The Excel Monthly Progress Report has been replaced by a working
Microsoft Fabric platform, live and running nightly. Read
[`status-update.md`](status-update.md) for the full picture — it is written to be handed to
the team as-is.

- ✅ Intro call with Rebecca (Jul 15) · in-person discovery with the wider team (Jul 21)
- ✅ Excel project reporting template **fully assessed** — 14 defects found (`analysis/excel-tracker/`)
- ✅ **Data warehouse review with Rebecca (Jul 23)** — `meeting-notes/2026-07-23-warehouse-review.md`
- ✅ **Scope, terms & engagement agreed with Cathal (Jul 24).** $125/hr, 9–10 months, 20 hrs initial scope, 5 hrs/wk ongoing
- ✅ **Fabric access provisioned (Aug 1)** — the whole workspace backed up read-only, and **live credentials found in five notebooks** (`foundation/charley-dev/_docs/security-findings.md`)
- ✅ **Platform built and live (Aug 1–2)** — bronze → silver → gold medallion off Affect's production Procore tenant, Direct Lake semantic model (37 tables, 99 measures), 12-page report, nightly pipeline, 63-expectation DQ gate
- ✅ **Found and fixed a $4.85M understatement** of portfolio contract value the existing reporting had been carrying silently
- 🔴 **Mentoring with Rebecca not yet started** — the one Phase 0 line item still open
- 🔵 **Four access grants now gate ~41% of report coverage** — Sage gateway permission, Outbuild token, SharePoint lists, Azure subscription. All the pipework behind them is built and tested

### What Affect needs to action

| Priority | Ask | Effort |
|---|---|---|
| 🔴 **1** | **Rotate the Procore OAuth credentials** — live secrets in plaintext in a workspace notebook. Rotate first, edit second | Minutes |
| 🔴 **2** | Grant `cforey-c@affect-group.com` **"Can use"** on connection `nc-affect-1\sage100con;Affect Group` | One grant |
| 🔴 **3** | Check whether the existing reporting is stale — Rebecca's Sage data stops **2026-07-20**, Outbuild **2026-07-14** | Ten minutes |
| 🟡 4 | Issue `OUTBUILD_API_TOKEN` — the only milestone source anywhere | One token |
| 🟡 5 | Answer four manual-input definition questions | 30-min call |
| 🟡 6 | Confirm NDA status — billing depends on it (`hours-log.md`) | — |

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
| Procore | Project management & costing | 🟢 **36 endpoints live**, registry-driven, production tenant → bronze. Extraction currently runs locally pending Key Vault |
| Sage 100 Contractor | Accounting, invoicing, payroll | 🔵 `CD_Sage_Ingest` **deployed and gateway-wired**, 8 tables. Blocked on one connection permission grant |
| Outbuild | Scheduling & milestones | 🔵 16 endpoints **built and verified**, cannot run — no API token. The **only** milestone source anywhere |
| SharePoint | The ~40% of the report that lives in no system | 🟡 10-list provisioning script written; a CSV path works today with no admin ticket |
| Power BI | Reporting | 🟢 **Monthly Progress Report live** — 12 pages, 180 visuals, Direct Lake over the gold model |
| Ramp | Vendor payments | 🔴 Not integrated — API docs vendored in `resources/ramp/` |
| ADP | Payroll | 🔴 Not integrated |
| Bluebeam / Navisworks | Design & drawings | 🔴 Not integrated |
| Outlook / OneDrive | Email & document management | 🔴 Not integrated |
| Power Automate | Workflow automation | 🔴 Planned (payments, lien waivers) — blocked on SOPs |
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
- **`foundation/`** — **the build.** A read-only backup of the whole Fabric `Build` workspace, plus `foundation/charley-dev/`: our self-contained platform — ingestion, medallion SQL, lakehouse and semantic-model definitions, the report, the orchestration DAG, the offline test harness, and `_docs/` (10 documents; `solution-guide.md` first)
- `analysis/excel-tracker/` — full teardown of the client's Monthly Progress Report workbook: field inventory, decoded formulas, dashboard cell map, drop-down vocabulary, and the 14 verified defects
- `src/procore/` — the original RFI/submittal reference pipeline (Jul 26). Superseded by `foundation/charley-dev/` but kept: it is the smallest complete example of the pattern, and a good teaching artifact
- `powerbi/` — the design kit that preceded the build: semantic model, DAX measure library, report spec, theme, manual-input template, phased build plan
- `resources/` — vendored documentation, one folder per solution. Includes the **full Sage 100 Contractor and Outbuild API doc sets** as markdown, and a Procore endpoint cheatsheet verified against the 2,111-path OAS
- `.mcp.json` — Fabric MCP server config for Claude Code (live workspace exploration; see `resources/microsoft-fabric/`)
- `meeting-notes/` — notes from calls and meetings (discovery Jul 21, warehouse review Jul 23, scope & terms Jul 24)
- `call-prep/` — agendas and information requests prepared for calls
- `internal/` — not client-facing: strategy, communications log, and sent-email drafts
- `YY-000 PROJECT NAME_InternalReport_YYMMDD.xlsx` — the client's reporting template (the spec for D5)
