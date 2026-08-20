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
- ✅ **The platform is built and running (Aug 1–2)** — three lakehouses, Procore ingestion from the production tenant, a nightly pipeline with a blocking DQ gate (now **107 expectations**, 83 blocking / 24 warning), a 37-table Direct Lake model and a 12-page Monthly Progress Report. See `foundation/charley-dev/`
- ✅ **`CD_Sage_Ingest` deployed (Aug 3)** — live in the `charley-dev` folder, bound to the existing on-prem gateway, inert until one *Can use* grant lands
- ✅ **$4.85M defect found, fixed and deployed** — portfolio contract value was understated 16% by a per-month rather than cumulative change-order roll-up
- ✅ **Fabric MCP** wired for the repo (`.mcp.json`) — used for live exploration (`execute_sql_query` / `execute_dax_query`); item creation stays on the committed REST deploy path
- ✅ **Platform review with Rebecca — Thu Aug 13** (`meeting-notes/2026-08-13-rebecca-platform-review.md`). Rebecca's workload has increased; Charley absorbs the build load, mentoring goes async/recorded
- ✅ **Azure subscription and Key Vault now exist (Aug 19)** — "Azure subscription 1" on tenant *Affect Build LLC*. The vault we actually use is **`AffectKeyVault`** (RG `Affect_Data`); `OneLake`, which the docs named until that evening, was the wrong one. The only purchasing decision on the blocker list is closed
- ✅ **PQP (Project Quality Plan) subject area delivered (Aug 19)** — the client's 44-sheet `026-025 SAUNA LOUNGE QA - QC TRACKER` extracted to seed data (26 trades, 625 checklist items, 93 statutory gates, 101 DOH items, 141 status-vocabulary rows), joined to the live Procore facts `fct_QcSubmittal` 2,245 / `fct_QcPunch` 1,469 / `fct_QcNcr` 850, and now **visible**: a second semantic model (`Project Quality Plan` — 19 tables + `_Measures`, 42 measures, 23 relationships) and a second report (7 pages, 95 visuals), both deployed
- ✅ **Two defects found and fixed (Aug 19)** — `deploy_gold.py` carried a hardcoded table list the QC tables were never added to, so the `fct_Qc*` facts were neither row-checked nor published to `gold_schema.json`, and a gold table missing from that file **silently cannot appear in any semantic model** (published tables 45 → **54**). And `20_fieldops_silver.sql` read `$.trade` as an object rather than `$.trade.name`, which broke every QC trade join **and put raw JSON into `fct_QualityItem.Trade` on the live Monthly Progress Report**
- ✅ **Four data-quality defects resolved (Aug 19)** — submittal statuses **223 → 0** (Procore sends `For Record`, the silver CASE only handled `FOR RECORD ONLY`; **222 of 2,245 submittals** were falling out of every status slicer); trade vocabulary **970 → 506 unmapped** via a new 16-row `qc_seed_TradeAlias` (NCRs 459 → 215, punch 511 → 291); cost-code CSI divisions **807 → 0** — Affect writes divisions 1–9 without a leading zero, so **807 codes, 15% of the 5,433-code master, were absent from every by-division rollup** and none was actually malformed; plus a new ERROR-severity guard so a typo'd alias cannot masquerade as an unmapped trade. Three of the four were our code being wrong about Affect's conventions, not Affect's data being wrong. See [`build-status.md`](foundation/charley-dev/_docs/build-status.md)
- ✅ **$22.5M of AR was being attributed to no project, and the check said it was fine (Aug 19)** — `dim_Project` read `SageJobNumber` from a view that returns `NULL` under our own medallion, so **122 of 122 AR invoices resolved to `UNMATCHED`** and $23,695,760.48 hung off no project. The row count never moved (it is a `LEFT JOIN`), which is exactly the check that had been run to prove the source switch was safe, and `IsInCrosswalk` — the flag whose whole job is catching this — was derived from the same wrong view and read TRUE for all 19 projects. **A broken join reported itself as fully mapped.** Fixed: projects resolving to a Sage job **0 → 15**, unmatched invoices **122 → 24**, AR attributed **$0 → $22,548,861.96**
- ✅ **Outbuild is live (Aug 19)** — Rebecca put the token in `AffectKeyVault` at 18:27 UTC and **3,078 rows across 15 endpoints** landed in bronze. Three bugs that only a live call could reveal were fixed first: the client had been written against the docs and never actually run
- ✅ **The Key Vault blocker is closed — and the ask was withdrawn, not granted (Aug 19)** — it had named the wrong vault. The one in use is **`AffectKeyVault`** (RG `Affect_Data`), where `cforey-c@affect-group.com` already held *Key Vault Administrator* inherited at resource-group scope. Three documents had been asking Affect for a role nobody needed to grant, since Aug 13. Two real defects sat behind it: secret names were never translated, and the secret helper **failed open** to an environment variable — a half-configured vault would have read a credential from an unaudited source and reported success
- ✅ **The estimating/bidding automation is in Affect's tenant (Aug 19)** — both flows created (stopped): `Estimating Setup` and `Convert to Bidding`. The BUILD site structure is provisioned on **`AFFECTBUILD1`**, a site Affect already had, and `CD_Manual_Ingest` is published with 19 queries. Getting there meant routing around a tenant where every direct write path is closed — SharePoint REST 401, Graph 403 for want of any `Sites.*` scope, PnP's shared app retired by Microsoft — by having Power Automate do the provisioning, since a flow's actions run as the connection rather than as the script
- ✅ **The reporting site's intake is provisioned (Aug 19–20)** — 18 lists on `AffectProjectReporting_main`, their **142 columns** and the 19 `CD Projects` rows, verified by reading the site back through Graph rather than trusting the run status. `CD_Manual_Ingest` is published against it with 19 queries and needs only its first sign-in
- 🟡 **`dim_Job` links the flows to the platform** — the Job Register had been *described* as the `dim_Job` source with no bronze table, no dataflow query, no silver parser and no gold DDL behind it. The chain is now built end to end, with a blocking DQ expectation on job-number uniqueness that catches somebody switching off the flows' concurrency guard in the designer
- 🔵 **One access grant left, down from four** — the Sage gateway "Can use". See `dashboard.md` → Blockers
- ⚠️ **Existing production reporting lags** — re-measured Aug 19: Sage now carries to Jul 31, up from the Jul 20 recorded on Aug 2, so her feed refreshed rather than stopped dead. Still ~19 days behind. Outbuild's Jul 14 is as measured Aug 2 and has not been re-verified. Lag, not a dead feed — but still a reason to fix the gateway

A forwardable write-up of the build lives in [`status-update.md`](status-update.md).

### What is still to be completed

The build is not the bottleneck. Nothing below is blocked on engineering capacity.

**Affect's to give — one access grant, down from four:**

| | |
|---|---|
| 🔴 **Sage gateway "Can use"** on `nc-affect-1\sage100con;Affect Group` | The only access item left. Unlocks AR/AP detail, retainage, cost-by-cost-code and the AR scorecard category |
| 🔴 **Rotate the exposed Procore credential pair** | Security, and it also gates moving extraction into Fabric. Rotate first, edit the notebook second |
| 🟡 **The two folder templates' contents**, and a service account to own the SharePoint connection | The last things between the two flows and being switched on |
| 🟡 **Four manual-input definition questions**, three ambiguous trade labels, and whether the checklist library should cover the trades Procore has and it does not | One 30-minute call |
| 🟡 **Link the remaining Outbuild projects to Procore** | Only **3 of 15** carry a `procore_id`, so 280 of 406 critical activities cannot be attributed to a project and never reach the report. Configuration in Outbuild, not development — roughly triples schedule coverage |
| 🟡 **Procore 403s** on `punch_item_types` and `schedule` | Two report sections cannot be sourced |

**Ours to finish:**

| | |
|---|---|
| Sign `CD_Manual_Ingest` in and refresh it | Turns on the SharePoint path for the manual ~40%. The site is ready; the dataflow ships `connections: []` and needs one interactive sign-in |
| ~~Repoint `sv_outbuild_activities`~~ ✅ **Done Aug 20** | `fct_Milestone` reads our own ingestion — 52 → **126 milestones**, 2 → **3 projects**, 0 orphans. The ceiling now is Affect's: only 3 of 15 Outbuild projects carry a `procore_id`, so 280 critical activities stay unattributable until more are connected to Procore |
| Fix the DQ persist gap | Counts are trustworthy; the reject drill-through shows an older run |
| Explain the `Total Billed` / `Owner Billed To Date` gap on the report | Different grains, not a defect — but unexplained on the page |
| Wire the 8 `man_Qc*` intake tables silver → gold | Gated on the definition answers above |
| Add `cd_01_extract_procore` to the nightly DAG | After the credential rotation |

**Not started:** mentoring and recorded walkthroughs — the one Phase 0 line item still
outstanding — and D6/D7, which wait on Chris's SOPs.

**Commercial:** billable time stands at **45.5 hrs** against a 20-hour Phase 0. The overrun
is work past the end of Phase 0 that has not been re-scoped, not a Phase 0 overspend. It
needs a conversation with Cathal rather than an invoice — see [`hours-log.md`](hours-log.md).

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
| Procore | Project management & costing | 🟢 **44 endpoints registered, 40 landing bronze tables**, registry-driven, production tenant → bronze; **2 blocked by Procore 403s** (`punch_item_types`, `schedule`). Extraction still runs locally — no longer for want of Key Vault, but until the exposed credentials are rotated |
| Sage 100 Contractor | Accounting, invoicing, payroll | 🔵 `CD_Sage_Ingest` **deployed and gateway-wired**, 8 tables. Blocked on one connection permission grant |
| Outbuild | Scheduling & milestones | 🟢 **Live Aug 19, feeding the report Aug 20** — **3,078 rows across 15 endpoints**, and `fct_Milestone` now reads it: **126 milestones across 3 projects**, up from 52 across 2. The **only** milestone source anywhere |
| Azure Key Vault | Secret storage for ingestion | 🟢 **Working, Aug 19.** `AffectKeyVault` (RG `Affect_Data`), where our account already held *Key Vault Administrator* at RG scope. The vault every document had been naming, `OneLake`, was the wrong one and holds nothing we depend on |
| SharePoint | The ~40% of the report that lives in no system, plus estimating/bidding job folders | 🟡 **Sites exist, Aug 19.** `AFFECTBUILD1` carries the provisioned `Job Register` and both template trees; `AffectProjectReporting_main` carries all 18 intake lists (2026-08-19) with their **142 columns and 19 `CD Projects` rows** (2026-08-20). A CSV path works today with no admin ticket |
| Power BI | Reporting | 🟢 **Two reports live** — `Monthly Progress Report` (12 pages, 180 visuals) over `Affect Project Report`, and `Project Quality Plan` (7 pages, 95 visuals) over its own model. Both Direct Lake over the gold layer |
| Power Automate | Workflow automation | 🟡 **Both flows created in the tenant Aug 19, stopped** — Estimating Setup and Convert to Bidding. Waiting on the two folder templates' contents and a service account before they are turned on. Payments and lien waivers still gated on Chris's SOPs |
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
- `updates/` — dated, client-facing executive updates written to be forwarded as-is. Latest: [`2026-08-20`](updates/2026-08-20-executive-update.md); previous: [`2026-08-19`](updates/2026-08-19-executive-update.md), [`2026-08-13`](updates/2026-08-13-executive-update.md). These are point-in-time records and are not rewritten; [`status-update.md`](status-update.md) is the living version
- `power-automate/` — **the estimating/bidding job-folder automation**: both flow definitions, the API deployer, the SharePoint provisioning scripts, [`RUNBOOK.md`](power-automate/RUNBOOK.md) and the offline test suite. Both flows now exist in Affect's tenant, created stopped
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
