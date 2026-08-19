# Status Update — Affect Group

**As of 2026-08-19.** Written to be handed to the team as-is.

Every figure on this page was read out of the live Fabric workspace on 2026-08-19, not
carried forward from a previous update. The engineering detail behind each claim is in
[`foundation/charley-dev/_docs/`](foundation/charley-dev/_docs/) — start with
[`solution-guide.md`](foundation/charley-dev/_docs/solution-guide.md).

---

## The one-paragraph version

The Excel Monthly Progress Report has been replaced by a working Microsoft Fabric platform.
It ingests Affect's **production** Procore tenant, types and validates the data through a
bronze → silver → gold medallion, and serves a 12-page Power BI report off a Direct Lake
star schema with 99 measures. It runs on a nightly schedule, it checks its own work with 103
data-quality expectations, and it found a **$4.85M understatement** of portfolio contract
value that the existing reporting had been carrying silently. None of it touches Rebecca's
existing warehouse — it was built alongside, in its own folder, and her reporting has run
untouched throughout.

Since then a **second subject area has been delivered: the Project Quality Plan**. The
client's 44-sheet QA/QC tracker is now a modelled part of the platform with its own semantic
model and its own 7-page report, joined to 4,564 live quality records read out of Procore.

The build is not the bottleneck any more. **Four access grants are**, and they are worth
about 41% of the report's coverage between them.

---

## What has been created

### The platform, live in Fabric

Workspace `Build`, folder `charley-dev`. Nothing outside that folder has been modified.

| Layer | State on 2026-08-19 |
|---|---|
| **Bronze** | 40 tables landing from Procore, plus 17 manual-input tables (9 original + 8 for the Quality Plan) |
| **Silver** | 15 typed tables. The last full row/reject count — **14,791 rows, 0 rejects** — was measured on 2026-08-02 and has not been re-read since the quality tables landed |
| **Gold** | **53 tables published** to the semantic-model contract — dimensions, facts, crosswalks, bridges, quality tables, manual placeholders |
| **Semantic models** | **Two.** `Affect Project Report` — Direct Lake, **37 tables, 99 measures**. `Project Quality Plan` — **19 tables plus a measure table, 42 measures, 23 relationships** |
| **Reports** | **Two.** `Monthly Progress Report` — **12 pages, 180 visuals**, drill-through, 3 bookmarks, themed and navigable ([**see every page**](resources/power-bi/monthly-progress-report/) without opening Fabric). `Project Quality Plan` — **7 pages, 95 visuals** |
| **Orchestration** | `CD_Master_Pipeline`, 5 activities. Pipeline 02:00 daily, model refresh 04:00 daily (Eastern) |
| **Data quality** | **103 expectations** — 80 blocking, 23 warning — gating the publish. A blocking violation keeps yesterday's numbers rather than publishing wrong ones |

### The ingestion

| Source | State |
|---|---|
| **Procore** | **44 endpoints registered, 40 landing bronze tables**, registry-driven — one shared extractor, not 25 near-identical notebooks. Adding an endpoint is a YAML entry. Two endpoints (`punch_item_types`, `schedule`) are blocked by Procore **403s** and are a permissions ask, not a build gap |
| **Sage 100** | `CD_Sage_Ingest` **deployed** to the workspace, wired to the existing gateway, 8 tables including the two AR/AP **line** tables the current dataflow explicitly discards. Blocked on one permission grant — see below |
| **Outbuild** | Built and verified across 16 endpoints. Cannot run — no API token issued |
| **Manual (~40% of the report)** | Two writers into one contract: a SharePoint path (provisioning script written and runnable) **and** a CSV path that works today with no admin ticket. **17** manual tables are now created and typed — the original 9, plus 8 for the Quality Plan's intake |

### The Project Quality Plan — new, and now visible

Affect's 44-sheet QA/QC tracker was the second-largest spreadsheet in the business. It is now
a modelled subject area with its own semantic model and its own report, so quality is
readable next to cost and schedule rather than in a separate workbook.

| | |
|---|---|
| **From the workbook** | 26 trades · **625 checklist items** · **93 statutory gates** (46 TCO, 23 Fire Alarm, 24 Statutory) · 101 DOH items · 141 status-vocabulary rows |
| **From production Procore** | **`fct_QcSubmittal` 2,245** · **`fct_QcPunch` 1,469** · **`fct_QcNcr` 850** |
| **Model** | `Project Quality Plan` — 19 tables plus a measure table, 42 measures, 23 relationships. Deliberately its own model, not an extension of the project model |
| **Report** | `Project Quality Plan` — 7 pages: Quality Portfolio, Non-Conformance, Punch & Completion, Submittals & Mock-Ups, Statutory Gates, Trade Checklists & DFOW, and a hidden Data Quality page |
| **Intake** | 8 `man_Qc*` tables typed and empty, waiting on the same SharePoint/CSV path as the rest of the manual data |

Five verified defects were found in the client's workbook along the way — most importantly
four register roll-ups whose `% Complete` can never reach 100%, and two CSI codes Excel
destroyed on the only Tier 4 Critical DFOWs. They are written up in
[`analysis/pqp-workbook/defects-and-questions.md`](analysis/pqp-workbook/defects-and-questions.md).

### The engineering discipline behind it

This is the part worth the team's attention, because it is what makes the numbers
trustworthy rather than merely present:

- **Everything deploys from git.** Every item in Fabric got there through a committed,
  idempotent, dry-run-by-default script that refuses to write outside `charley-dev`. A
  mis-deploy is fixed by re-running, not by clicking.
- **14 offline test suites, all passing, no Fabric, no network.** The production Spark SQL is executed
  through DuckDB, so the tests exercise the real transforms rather than a re-implementation.
  66 gold assertions. Mutation-tested: five deliberate regressions are each caught.
- **The runs assert themselves.** A notebook that builds empty tables still reports
  "Completed" — so each one checks its own row counts, orphans and date resolution, and
  fails the run otherwise. Proven by injecting a wrong expected count and confirming failure.
- **14 live DAX checks** reframe the deployed model and verify it against real data.
- **Nothing is silently dropped.** Rows that fail validation land in a reject table *with a
  reason*. Silent drops are exactly how the workbook's defects survived for months.

---

## What this has already found

### The $4.85M defect — found, fixed, deployed, verified

The dashboard reported Current Contract of **$30,254,551.24** — exactly equal to Original
Contract — and Contract Growth of **0.00%**, while 307 change orders sat in the model. The
gold layer was adding only the current month's change orders to the contract instead of
accumulating them.

Corrected figures, deployed and verified: **$35,102,931.14** and **16.03%**.

Worth noting *why* it survived: the reconciliation gate passed, because the test fixture had
all three change orders in a single month — which makes a per-month roll-up and a cumulative
one arithmetically identical. A passing gate is not the same as a watching gate. The fixture
now spans two months and three assertions cover the difference.

### Two more silent defects — found, fixed, deployed

Both were invisible from the report. Neither raised an error anywhere.

**1. Quality data could not reach any report, and nothing said so.** `deploy_gold.py` carried
a hardcoded list of tables to row-check and publish, and the new quality tables had never been
added to it. A gold table missing from the published `gold_schema.json` **silently cannot
appear in any semantic model** — the table exists, holds correct data, and is simply
unreachable. Fixed; published tables went from **45 to 53**.

**2. Raw JSON was being shown as a trade name on the live report.** The silver transform read
the Procore `trade` field as a whole object instead of `trade.name`, so the column held
`{"id":…,"name":"Electrical",…}` rather than `Electrical`. That broke every quality trade join
— **631 of 850 non-conformance records** resolved to no trade — **and it was putting raw JSON
into the `Trade` column of the live Monthly Progress Report**. Fixed by reading `trade.name`;
unmapped records fell from **631 to 459** and the report now reads e.g. `Windows`.

The remaining **459** are a genuine vocabulary difference, not a bug: Procore says `HVAC` and
`Sprinkler` where the workbook says `HVAC_DUCTWORK` and `FIRE_SPRINKLER`. **We have
deliberately not guessed** — attributing a defect to the wrong trade is worse than leaving it
unattributed. It is an open question for Affect and it is shown on the Quality Plan's Data
Quality page rather than hidden.

### The 14 Excel defects — 7 structurally fixed, plus 2 structural issues

| Defect | Resolution |
|---|---|
| Schedule Performance always scored 3/3 | Bands are fractions, not integers |
| Completion Variance always scored 0 | 0 days now falls in the 3-point band |
| Three different month anchors | One contiguous date dimension, 7,670 days, no gaps |
| `TODAY()` non-reproducibility | Month offset against a real calendar |
| Inverted milestone dates never flagged | Flagged and surfaced on the Data Quality page |
| `"NA"` strings in date columns | Floored to real NULLs at the silver boundary |
| Trailing whitespace on 12 trades | Seeded pre-trimmed and asserted |

Between them, **42% of the scorecard weight** was previously disconnected from reality. Two
of the errors cancelled each other out, which is why nobody caught it.

Two structural problems in the existing pipeline were fixed at the same time: **full-reload
ingestion** (now an upsert on the natural key) and **hard-coded credentials** (now a secret
helper — Key Vault in Fabric, environment variable locally).

The remaining 7 of the 14 are either presentation-level or need a decision from Affect rather
than a code change; they are itemised in
[`analysis/excel-tracker/defects-and-questions.md`](analysis/excel-tracker/defects-and-questions.md).

### New findings, none previously recorded

1. **Sentinel dates before 1582-10-15** in the submittals data — Spark refuses to read them
   from Parquet at all. Placeholders for "unknown", now floored to NULL.
2. **2 projects have no Sage crosswalk entry** — they cannot join to any financial data.
3. **70 cost codes are absent from master data.**
4. **23 AR invoices reference a Sage job that resolves to no project.**
5. **Retainage reads as $0 across all 940 Sage invoices** on the invoice header. It is not
   held there for this company. A report built off the header would show zero retainage,
   silently, until a client asked where their retention was.
6. **Scorecard bands have holes** — Observations leaves the value 5 unscored, Daily Reports
   leaves 2. Closed so the bands tile; worth confirming intent.

Findings 2–4 would have been invisible in Excel: 22 facts referencing unmastered keys would
simply have vanished from a join, understating budgets and change orders with no error
anywhere.

### ⚠️ Security — needs action, not discussion

Live Procore OAuth credentials are **hardcoded in plaintext in a notebook in the live
workspace**, readable by anyone with Viewer access, and captured in the workspace's
definition history so deleting the cell does not retract them. The repository copy was
scrubbed; **the live copy was not** — which is the most dangerous shape this can take,
because it looks fixed when read from git.

**Rotate the credential pair in Procore's Developer Portal first, edit the notebook second.**
Full detail and remediation steps:
[`security-findings.md`](foundation/charley-dev/_docs/security-findings.md).

### ⚠️ The existing reporting may be running on two-week-old data

Rebecca's Sage data stops at **2026-07-20** and Outbuild at **2026-07-14**. If those
dataflows are failing on the same gateway permission issue described below, the current
reporting is serving stale numbers and nothing has surfaced it. Worth ten minutes of
someone's time to confirm either way.

---

## What needs verification

Honest separation between "built" and "proven correct against reality".

| Item | Status | What would settle it |
|---|---|---|
| **The nightly pipeline does not call Procore** | Known limitation | `cd_01_extract_procore` is not in the nightly run. Extraction runs on a laptop and lands files; the pipeline merges whatever was last landed. "Ran green" means the transforms are healthy, **not** that the data is fresh. Resolved by the Key Vault role assignment |
| **The nightly pipeline does not refresh manual input either** | Known limitation | `cd_06_land_manual` is not in `CD_Master_Pipeline`, so the nightly run rebuilds silver and gold without refreshing manual bronze. Harmless while every manual table is empty; a silent staleness bug the day somebody enters data. **Must land before SharePoint goes live** |
| **459 of 850 non-conformance records have no trade** | Needs a decision, not a fix | Procore's trade vocabulary and the workbook's do not match (`HVAC` vs `HVAC_DUCTWORK`). Guessing a mapping would attribute defects to the wrong trades. One vocabulary decision from Affect settles it |
| **DQ reject detail is stale** | Diagnosed, not yet fixed | The gate reports success while silently failing to write reject detail, so the Data Quality page shows rows from an older run. **Counts are trustworthy; drill-through is not.** Two small fixes identified |
| **Source coverage is 5.26%** | Measured | Only 1 of 19 projects is present in all three systems. This is the single biggest limit on the report, and it is an access problem, not a build problem |
| **Scorecard coverage is 59%** | Measured | 4 of 9 categories cannot be scored — AR (Sage), Profitability (human judgement, stays manual by design), Completion Variance (Outbuild), Daily Reports (SharePoint). **Quote "Project Scorecard (Measured Only)" — 0.44** — or absent data reads as poor performance |
| **`Total Billed` $22.1M vs `Owner Billed To Date` $28.0M** | Expected to differ | Sage AR invoices against Procore payment applications, different grains. Not a defect, but the gap is not explained anywhere on the report yet |
| **`Vendors Missing From ERP` = 125 of 251** | Needs a human | Half the vendor master is unmatched |
| **`Expired Certificates` = 105 of 105** | Needs a human | Put this in front of Affect as a question, not a metric |
| **Four manual-input questions** | Blocking the manual silver → gold link | Whether daily-log compliance means "submitted" or "submitted same day"; whether a milestone is a date or a span; which attestations are monthly; whether the client survey is anonymous. Guessing produces an authoritative-looking number measuring the wrong thing |
| **Three gold tables invisible to the SQL endpoint** | Not a failure — do not "fix" | They hold data and serve the report correctly. Fabric's endpoint metadata sync lagging. Verify with DAX, not SQL |

---

## Roadblocks — four access grants, all Affect's to give

All the pipework behind each of these is built, committed and tested. Nothing here is
waiting on engineering.

| # | Blocker | Unlocks | Who can grant it | Effort |
|---|---|---|---|---|
| 1 | **Grant `cforey-c@affect-group.com` "Can use" on the connection `nc-affect-1\sage100con;Affect Group`** | Sage AR/AP detail, retainage, actual-cost-by-cost-code, AR scorecard category | Whoever administers the on-prem data gateway | **One grant, one refresh.** No subscription, no code change |
| 2 | **Issue `OUTBUILD_API_TOKEN`** | Milestones — Outbuild is the **only** source of these anywhere. 17 of 19 projects currently have none. Largest single coverage gain available | Affect via Outbuild CS rep | One token |
| 3 | **Provision the SharePoint lists** (or start with the CSV path today) | The ~40% of the report that lives in no system — wins, risks, priority items, client survey, milestone dates — plus the 8 Quality Plan intake lists and the `Job Register` | SharePoint admin | Provisioning script is written and runnable, but **no site exists yet**. **The CSV path works today with no ticket at all** |
| 4 | **One role assignment: "Key Vault Secrets Officer" on vault `OneLake`** for `cforey-c@affect-group.com` | Key Vault, so Procore ingestion runs *inside* Fabric on a schedule instead of on a laptop | Whoever owns the Azure subscription | **The subscription and the vault now both exist.** Our identity holds only *Contributor on the resource group*, which on an RBAC vault can neither read nor write a secret nor grant itself the right to. One role, then one script — [`keyvault-runbook.md`](foundation/charley-dev/_docs/keyvault-runbook.md) |

Plus two Procore permissions worth asking for in the same conversation: `punch_item_types`
and `schedule` both return **403**.

**If only one thing gets done this week, make it #1.** It is the highest value per unit of
effort by a wide margin, and it may also explain the stale-data finding above.

---

## What comes next

Ordered by value per unit of effort, engineering side.

| # | Work | Depends on |
|---|---|---|
| 1 | Fix the DQ persist gap — create the results table, move reject persistence out of the shared exception handler, record the outcome on the heartbeat | Nothing |
| 2 | ✅ **Done.** `deploy_gold.py`'s default source is now `cd`, so a bare re-deploy no longer silently reverts gold to the legacy warehouse, and its hardcoded publish list is gone | — |
| 3 | Add `cd_06_land_manual` (and, once the vault role lands, `cd_01_extract_procore`) to `CD_Master_Pipeline` | Nothing / Blocker #4 |
| 4 | Explain the `Total Billed` / `Owner Billed To Date` gap on the report itself | Nothing |
| 5 | Land Sage silver, settle the retainage question, repoint the AR views at our own medallion | Blocker #1 |
| 6 | Land Outbuild milestones, close Completion Variance | Blocker #2 |
| 7 | Answer the four manual-input questions and the quality trade vocabulary, then wire manual silver → gold | A 30-minute call |
| 8 | Retire the local extraction bridge; ingestion moves into Fabric | Blocker #4 |
| 9 | Mentoring sessions with Rebecca — recorded, on the extractor registry pattern first | Scheduling |

Reaching ~100% scorecard coverage needs items 5, 6 and 7. All three are gated on access or a
conversation, not on build time.

---

## The recurring lesson, and why it matters commercially

Nearly every defect found in this engagement failed **silently** — a valid-looking API call
returning nothing, or a parse producing NULL:

- A missing company-id header → **404**, reading as "this project has no RFI tool". Cost 28
  of 36 endpoints.
- `manpower_logs` without a date range → **200 with zero rows**, reading as "no manpower
  logged". Cost 120,766 hours.
- A JSON key containing `(` → **NULL**, so every budget money column parsed blank while the
  model looked healthy.
- A per-project balance summed across months → **$355M** on the front page instead of $30M,
  and it reconciled perfectly whenever anyone filtered to one project to check it.
- A scheduled pipeline whose first stage could never authenticate → **4 failed runs out of
  4**, with a status page reading "enabled".

None raised an error. Not one. This is why the platform is built to prefer a loud failure to
a plausible number — why rejects carry reasons, why the DQ gate blocks rather than warns, and
why "the report looks fine" was never sufficient evidence that it was.

---

## Where to read more

| Document | Covers |
|---|---|
| [`dashboard.md`](dashboard.md) | Deliverable rollup, hours, blockers, roadmap |
| [`solution-guide.md`](foundation/charley-dev/_docs/solution-guide.md) | What the platform is and how it works — read first |
| [`build-status.md`](foundation/charley-dev/_docs/build-status.md) | What exists in Fabric right now, measured |
| [`assessment.md`](foundation/charley-dev/_docs/assessment.md) | Independent audit of the above, against the live workspace |
| [`security-findings.md`](foundation/charley-dev/_docs/security-findings.md) | Credential exposure — report only, nothing changed |
| [`sage-ingestion.md`](foundation/charley-dev/_docs/sage-ingestion.md) | The dataflow and why the AR/AP line tables matter |
| [`sharepoint-lists.md`](foundation/charley-dev/_docs/sharepoint-lists.md) | Build sheet to hand to a SharePoint admin |
| [`manual-input.md`](foundation/charley-dev/_docs/manual-input.md) | The design for the ~40% that lives in no system |
| [`analysis/excel-tracker/`](analysis/excel-tracker/) | The original workbook teardown and its 14 defects |
| [`analysis/pqp-workbook/`](analysis/pqp-workbook/) | The QA/QC tracker teardown — 5 verified defects and the open questions for Affect |
