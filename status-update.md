# Status Update — Affect Group

**As of 2026-08-02.** Written to be handed to the team as-is.

Every figure on this page was read out of the live Fabric workspace on 2026-08-02, not
carried forward from a previous update. The engineering detail behind each claim is in
[`foundation/charley-dev/_docs/`](foundation/charley-dev/_docs/) — start with
[`solution-guide.md`](foundation/charley-dev/_docs/solution-guide.md).

---

## The one-paragraph version

The Excel Monthly Progress Report has been replaced by a working Microsoft Fabric platform.
It ingests Affect's **production** Procore tenant, types and validates the data through a
bronze → silver → gold medallion, and serves a 12-page Power BI report off a Direct Lake
star schema with 99 measures. It runs on a nightly schedule, it checks its own work with 63
data-quality expectations, and it found a **$4.85M understatement** of portfolio contract
value that the existing reporting had been carrying silently. None of it touches Rebecca's
existing warehouse — it was built alongside, in its own folder, and her reporting has run
untouched throughout.

The build is not the bottleneck any more. **Four access grants are**, and they are worth
about 41% of the report's coverage between them.

---

## What has been created

### The platform, live in Fabric

Workspace `Build`, folder `charley-dev`. Nothing outside that folder has been modified.

| Layer | State on 2026-08-02 |
|---|---|
| **Bronze** | 40 tables, raw payload from Affect's production Procore tenant |
| **Silver** | 15 typed tables, **14,791 rows, 0 rejects** |
| **Gold** | 40 tables — dimensions, facts, crosswalks, bridges, manual placeholders |
| **Semantic model** | `Affect Project Report` — Direct Lake, **37 tables, 99 measures, 45 relationships** |
| **Report** | `Monthly Progress Report` — **12 pages, 180 visuals**, drill-through, 3 bookmarks, themed and navigable. [**See every page**](resources/power-bi/monthly-progress-report/) without opening Fabric |
| **Orchestration** | `CD_Master_Pipeline`, 5 activities. Pipeline 02:00 daily, model refresh 04:00 daily (Eastern) |
| **Data quality** | 63 expectations, gating the publish. A blocking violation keeps yesterday's numbers rather than publishing wrong ones |

### The ingestion

| Source | State |
|---|---|
| **Procore** | **36 endpoints** live, registry-driven — one shared extractor, not 25 near-identical notebooks. Adding an endpoint is a YAML entry |
| **Sage 100** | `CD_Sage_Ingest` **deployed** to the workspace, wired to the existing gateway, 8 tables including the two AR/AP **line** tables the current dataflow explicitly discards. Blocked on one permission grant — see below |
| **Outbuild** | Built and verified across 16 endpoints. Cannot run — no API token issued |
| **Manual (~40% of the report)** | Two writers into one contract: a SharePoint path (10 lists, provisioning script written and runnable) **and** a CSV path that works today with no admin ticket. Nine templates with worked examples generate on every run |

### The engineering discipline behind it

This is the part worth the team's attention, because it is what makes the numbers
trustworthy rather than merely present:

- **Everything deploys from git.** Every item in Fabric got there through a committed,
  idempotent, dry-run-by-default script that refuses to write outside `charley-dev`. A
  mis-deploy is fixed by re-running, not by clicking.
- **12 offline test suites, no Fabric, no network.** The production Spark SQL is executed
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
| **The nightly pipeline does not call Procore** | Known limitation | Extraction runs on a laptop and lands files; the pipeline merges whatever was last landed. "Ran green" means the transforms are healthy, **not** that the data is fresh. Resolved by the Azure subscription → Key Vault |
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
| 3 | **Provision the 10 SharePoint lists** (or start with the CSV path today) | The ~40% of the report that lives in no system — wins, risks, priority items, client survey, milestone dates | SharePoint admin | Provisioning script is written and runnable. **The CSV path works today with no ticket at all** |
| 4 | **An Azure subscription on the tenant** | Key Vault, so Procore ingestion runs *inside* Fabric on a schedule instead of on a laptop | Affect IT | Subscription, then one script |

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
| 2 | Change `deploy_gold.py`'s default source to `cd` | Nothing. Current default silently reverts gold to the legacy warehouse on a bare re-deploy — a live foot-gun |
| 3 | Explain the `Total Billed` / `Owner Billed To Date` gap on the report itself | Nothing |
| 4 | Land Sage silver, settle the retainage question, repoint the AR views at our own medallion | Blocker #1 |
| 5 | Land Outbuild milestones, close Completion Variance | Blocker #2 |
| 6 | Answer the four manual-input questions, then wire manual silver → gold | A 30-minute call |
| 7 | Retire the local extraction bridge; ingestion moves into Fabric | Blocker #4 |
| 8 | Mentoring sessions with Rebecca — recorded, on the extractor registry pattern first | Scheduling |

Reaching ~100% scorecard coverage needs items 4, 5 and 6. All three are gated on access or a
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
