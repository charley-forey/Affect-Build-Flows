# Build Plan

> **Status — plan drafted July 2026, largely executed (2026-08-19).** P1–P4 are done: the
> medallion lakehouses, seed dimensions, Procore ingestion (44 registered endpoints), a gold
> layer publishing 53 table schemas, a DQ suite, and two semantic models with two reports,
> all live in Fabric. P5 (deployment pipeline, RLS, parallel run, handover) is not started.
> What still blocks the build is Affect-side access, not development work.
> Current truth: `foundation/charley-dev/_docs/build-status.md`.
> Kept as the record of the plan, its sequencing argument and its estimates — the phase
> tables below are the plan, not a status report.

Phased delivery of the Power BI dashboard replacing the Excel Monthly Progress Report.

Ties to [`../deliverables/05-powerbi-project-dashboard.md`](../deliverables/05-powerbi-project-dashboard.md)
and [`../deliverables/04-project-data-model.md`](../deliverables/04-project-data-model.md).

## Sequencing principle

**P0 is not optional and nothing parallelises around it.** The shared project key and the
manual-data decision gate everything else — building facts before the key is settled means
rebuilding them.

After P0, P1–P3 can overlap. P4 needs at least one fact stream landed.

Estimates assume Charley building with Rebecca as the internal counterpart, and are
deliberately ranged — several depend on answers not yet available.

---

## P0 — Access & key reconciliation

**Blocks everything.** Do not start P1 until the key question is answered.

| Task | Depends on |
|---|---|
| NDA signed | Affect (in progress) |
| Fabric workspace access | Affect (in progress) |
| Procore API credentials — confirm grant type | Rebecca |
| Sage 100 Contractor read-only SQL access | Affect |
| **Resolve the shared project identifier** across Procore / Sage / manual | Call |
| **Confirm cost codes reconcile** between Procore and Sage | Call / Cathal |
| Confirm the manual-data mechanism (SharePoint input workbook) | Call |
| Review Rebecca's existing Procore ETL — hosting, schedule, auth, endpoints, incrementality | Call |
| Decide: build the Sage job-cost pull now, or wait for the Procore↔Sage connector rollout? | Call |
| Obtain 2–3 completed real project reports (not the template) | Rebecca |
| Obtain the six client-satisfaction questions | Affect |

**Acceptance:** a written answer to "what value joins a Procore project, a Sage job, and a
row in the manual input file?" — and confirmation that the value is entered identically in
both systems today.

**Est. 6–10 hrs** (mostly the deep-dive call plus follow-up).

> The connector decision is worth real money. If job costs will flow Sage → Procore
> anyway, the Sage ingestion narrows to AR/AP/payments/retainage and P3 roughly halves.

---

## P1 — Foundation

Everything that can be built without a live integration. Start immediately after P0.

| Task | Output |
|---|---|
| Generate `dim_Date` (2023-01-01 → 2030-12-31), mark as date table | Kills the `AU4` `INDEX/MATCH` mechanic and defects #4, #5 |
| Seed `dim_Status` from `dropdowns-and-status.md` | Codes, labels, emoji, RAG, sort order, hex |
| Seed `dim_Trade` (29, **trimmed**), `dim_Owner` (9), `dim_ActivityCategory` (27 split) | Defect #9 fixed at source |
| Seed `dim_ScorecardWeight` + `dim_ScorecardBand` with the **corrected** bands | Fixes defect #1a–1c |
| Build `dim_Project` — even if only one row initially | Multi-project from day one |
| Build the SharePoint input workbook per `manual-input-template.md` | |
| Fabric pipeline: SharePoint → bronze → silver → gold `man_*` | With the validation gate |
| Apply `theme.json` | |

**Acceptance:**
- `dim_Date` marked as a date table; time intelligence works
- All dimension seeds load without unmatched values
- The input workbook round-trips: enter a win → appears in the Lakehouse next refresh
- Rejected rows appear in the diagnostics table rather than disappearing

**Est. 12–18 hrs.**

---

## P2 — Procore facts

Validate and extend Rebecca's existing ETL rather than replacing it — she built it, she
maintains it, and the engagement is explicitly about enabling her team.

| Task | Endpoints |
|---|---|
| Review existing ETL; document what it already pulls | — |
| `fct_RfiSubmittal` | `/rest/v1.0/projects/{project_id}/rfis`, `/rest/v1.1/projects/{project_id}/submittals` |
| `fct_QualityItem` | `/rest/v1.0/observations/items`, `/rest/v1.0/punch_items` |
| `fct_QualityMonthly` | aggregate of the above |
| `fct_SafetyMonthly[RecordableIncidents]` | `/rest/v1.0/projects/{project_id}/incidents` |
| `fct_ManpowerDaily` | `/rest/v1.0/projects/{project_id}/manpower_logs/daily_totals` |
| `fct_BudgetLine` | `/rest/v1.0/projects/{project_id}/budget`, `/rest/v2.0/…/budget_line_items/{id}` |
| `fct_ChangeOrder` | `/rest/v1.0/potential_change_orders`, `/rest/v2.0/…/prime_change_orders` |
| `fct_Milestone` (Procore portion) | `/rest/v1.0/projects/{project_id}/schedule` — ⚠️ or Outbuild |
| `fct_DailyLog` | `/rest/v1.0/projects/{project_id}/daily_log_headers` |
| `dim_Vendor`, `dim_CostCode` | `/rest/v1.0/projects/{project_id}/vendors`, `/rest/v1.0/cost_codes` |
| Incremental loading via `filters[updated_at]` | all |
| Retry on `429` honouring `Retry-After` | all |

**Start with `fct_RfiSubmittal`.** It is the cleanest win in the workbook — one Excel
table, fully automatable, and it feeds the one chart that already exists. It proves the
pipeline end-to-end on the lowest-risk data.

**Acceptance:**
- RFI/submittal counts by trade reconcile against a Procore screen export
- Incremental load runs twice without duplicating rows
- A deliberately failed call retries and logs

**Est. 20–30 hrs** — highly dependent on what the existing ETL already covers.

---

## P3 — Sage 100 Contractor facts

⚠️ **Scope depends on the P0 connector decision.**

| Task | Notes |
|---|---|
| Document the tables/views the read-only account exposes | Against the **Contractor** schema, not the ERP one |
| Capture the queries Power BI runs against Sage today | These encode undocumented knowledge |
| Determine gateway requirement | On-prem SQL ⇒ on-premises data gateway, real lead time |
| `fct_Invoice` | AR invoices + cash receipts |
| `fct_FinancialPeriod` — billing fields | Billed, paid, retainage, remaining, AR outstanding, aging |
| `fct_FinancialPeriod` — job cost | **Skip if the connector will supply it via Procore** |
| Payroll hours for `fct_SafetyMonthly[HoursWorked]` and `[OtHours]` | Sage or ADP — decide |

**Acceptance:** total billed / paid / retainage for one project and one month reconcile to
the penny against the current Excel and against Sage directly.

**Est. 15–25 hrs**, or **8–12** if the connector removes the job-cost pull.

---

## P4 — Measures & report

| Task | Output |
|---|---|
| Load `measures.dax` into a `_Measures` table | |
| Validate every measure against the Excel's cached values | The reconciliation gate |
| Build page 1 — Overview | The one-page replacement |
| Build pages 2–4 — Schedule, Financial, Safety & Quality detail | |
| Build page 6 — Data Quality (hidden) | |
| Drill-through, tooltips, bookmarks, sync slicers | |
| Accessibility pass per `report-spec.md` | Icon+label on every status; greyscale print test |

**Acceptance — the reconciliation gate.** Set the report to `2025-05-01` for the sample
project and confirm against the workbook's own cached values:

| Measure | Expected |
|---|---|
| `[Current Contract]` | `9,116,960.48` |
| `[Total Billed]` / `%` | `2,997,804.23` / `32.9%` |
| `[Total Paid]` / `%` | `2,683,097.46` / `29.4%` |
| `[Retainage]` / `%` | `127,441.56` / `1.4%` |
| `[Contract Growth %]` | `3.60%` |
| `[Percent Bought Out]` | `95.0%` |
| `[Avg Days To Payment]` | `8.82` |
| `[Critical Missed Starts %]` | `0.40` |
| `[Recordable Incidents]` (May 2025) | `0` |
| `[Hours Worked To Date]` | `114,231` |
| `[Observations]` (May 2025) | `17` |
| `[Client Satisfaction]` | `0.60` |

**`[Project Scorecard]` will NOT match `0.59` — and that is the point.** The Excel's `0.59`
includes a spurious `+0.15` from a schedule band that always scores 3 and a spurious
`−0.15` from a completion-variance band that always scores 0. With the corrected bands the
same inputs give:

| Category | Excel | Corrected | Note |
|---|---|---|---|
| Schedule Performance | 3 → 0.15 | 0 → 0.00 | 40% missed starts is not `<5%` |
| Completion Variance | 0 → 0.00 | 3 → 0.15 | Finishing on baseline is the best outcome |
| Accounts Receivable | 3 → 0.12 | 3 → 0.12 | 8.82 days still `< 45` — same score, right driver |

Net `0.59` either way *for this project* — the errors cancel here, which is exactly why
they went unnoticed. **Show Affect both numbers side by side and explain the difference.**
Do not silently "fix" a number they have been reporting.

**Est. 25–35 hrs.**

---

## P5 — Operationalise

| Task |
|---|
| Refresh schedule (nightly) + failure alerting |
| Deployment pipeline: dev → test → prod workspaces |
| Row-level security if PMs should see only their own projects |
| Parallel run against the Excel for one full monthly cycle |
| Handover: recorded walkthrough + written runbook for Rebecca |
| Retire the Excel |

**Acceptance:** one full month produced from Power BI, reconciled against the Excel, signed
off by the PM and by Rebecca.

**Est. 12–18 hrs.**

---

## Total

| Phase | Hours |
|---|---|
| P0 Access & keys | 6–10 |
| P1 Foundation | 12–18 |
| P2 Procore facts | 20–30 |
| P3 Sage facts | 8–25 |
| P4 Measures & report | 25–35 |
| P5 Operationalise | 12–18 |
| **Total** | **83–136** |

Wide because three variables are unresolved: how much Rebecca's ETL already covers, whether
the connector removes the Sage job-cost pull, and whether milestones live in Procore or
Outbuild. **P0 narrows all three.** Re-estimate after the deep-dive call rather than
committing to a number now.

Per the engagement structure (agreed Jul 24): **$125/hr flat**, with development scoped as
defined milestones. This plan's P0 overlaps the engagement's Phase 0 — see `dashboard.md` →
Phase 0 for the 20-hour breakdown actually committed. P1–P5 are scopeable once P0 lands, and
run against the ~5 hrs/week ongoing cadence.

---

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| **No clean shared project key** | Nothing joins | P0 gate. If none exists, a mapping table is the fallback — ugly but workable |
| Procore/Sage cost codes don't reconcile | Budget analysis unusable | Surface early; a mapping dimension is the fallback |
| Milestones live only in the spreadsheet | Schedule page has no source | Outbuild integration, or milestones stay manual in the input workbook |
| Sage SQL is on-prem | Gateway lead time | Identify in P0, start procurement immediately |
| PMs don't adopt the input workbook | 40% of the report goes stale | Parallel run; watch one PM use it; keep it genuinely slimmer than what they fill in today |
| Existing ETL is undocumented / fragile | P2 becomes a rewrite | Review it in P0 before estimating P2 |
| Scorecard correction reads as criticism | Trust | Present as a finding with the arithmetic shown, not as a fix already applied. Show both numbers |
| Sample data is a template, not real | Schema misses edge cases | Get 2–3 real completed reports in P0 |

---

## First three things after the call

1. Write up the P0 answers and re-estimate P2/P3 against them.
2. Build `dim_Date` + the seed dimensions — no dependencies, immediate progress, and it
   makes the model tangible for Rebecca.
3. Build `fct_RfiSubmittal` end to end as the pipeline proof. One Excel table in, one
   chart out, fully automated — the shortest path to something Affect can see working.
