# Status Update — Affect Group

**As of 2026-08-19, end of day.** Written to be handed to the team as-is.

Every figure on this page was read out of the live Fabric workspace on 2026-08-19, not
carried forward from a previous update. **Three of the four access blockers closed during
that day** — the Outbuild token arrived, the Key Vault ask turned out to be aimed at the
wrong vault and was withdrawn, and a SharePoint site was provided. One remains.

The engineering detail behind each claim is in
[`foundation/charley-dev/_docs/`](foundation/charley-dev/_docs/) — start with
[`solution-guide.md`](foundation/charley-dev/_docs/solution-guide.md).

---

## The one-paragraph version

The Excel Monthly Progress Report has been replaced by a working Microsoft Fabric platform.
It ingests Affect's **production** Procore tenant, types and validates the data through a
bronze → silver → gold medallion, and serves a 12-page Power BI report off a Direct Lake
star schema with 99 measures. It runs on a nightly schedule, it checks its own work with 104
data-quality expectations, and it found a **$4.85M understatement** of portfolio contract
value that the existing reporting had been carrying silently. None of it touches Rebecca's
existing warehouse — it was built alongside, in its own folder, and her reporting has run
untouched throughout.

Since then a **second subject area has been delivered: the Project Quality Plan**. The
client's 44-sheet QA/QC tracker is now a modelled part of the platform with its own semantic
model and its own 7-page report, joined to 4,564 live quality records read out of Procore.

Late on the same day, three further things landed. A dead join was found and repaired that
had been attributing **$22.5M of accounts receivable to no project at all** while reporting
itself as fully mapped. **Outbuild went live** — 3,078 rows across 15 endpoints — closing the
milestone gap that had been open since the start. And the estimating→bidding folder
automation moved from committed files into Affect's actual tenant.

The build is not the bottleneck any more. **One access grant is** — the Sage gateway. It was
four this morning.

---

## What has been created

### The platform, live in Fabric

Workspace `Build`, folder `charley-dev`. Nothing outside that folder has been modified.

| Layer | State on 2026-08-19 |
|---|---|
| **Bronze** | 40 tables landing from Procore, plus 17 manual-input tables (9 original + 8 for the Quality Plan) |
| **Silver** | 15 typed tables. The last full row/reject count — **14,791 rows, 0 rejects** — was measured on 2026-08-02 and has not been re-read since the quality tables landed |
| **Gold** | **54 tables published** to the semantic-model contract — dimensions, facts, crosswalks, bridges, quality tables, manual placeholders |
| **Semantic models** | **Two.** `Affect Project Report` — Direct Lake, **37 tables, 99 measures**. `Project Quality Plan` — **19 tables plus a measure table, 42 measures, 23 relationships** |
| **Reports** | **Two.** `Monthly Progress Report` — **12 pages, 180 visuals**, drill-through, 3 bookmarks, themed and navigable ([**see every page**](resources/power-bi/monthly-progress-report/) without opening Fabric). `Project Quality Plan` — **7 pages, 95 visuals** |
| **Orchestration** | `CD_Master_Pipeline`, **6 activities** — *Land Manual Input* is in the nightly run, verified live 2026-08-19. Pipeline 02:00 daily, model refresh 04:00 daily (Eastern) |
| **Data quality** | **104 expectations** — 81 blocking, 23 warning — gating the publish. A blocking violation keeps yesterday's numbers rather than publishing wrong ones |

### The ingestion

| Source | State |
|---|---|
| **Procore** | **44 endpoints registered, 40 landing bronze tables**, registry-driven — one shared extractor, not 25 near-identical notebooks. Adding an endpoint is a YAML entry. Two endpoints (`punch_item_types`, `schedule`) are blocked by Procore **403s** and are a permissions ask, not a build gap |
| **Sage 100** | `CD_Sage_Ingest` **deployed** to the workspace, wired to the existing gateway, 8 tables including the two AR/AP **line** tables the current dataflow explicitly discards. Blocked on one permission grant — see below |
| **Outbuild** | **Live as of 2026-08-19.** Rebecca placed the token in `AffectKeyVault` at 18:27 UTC and **3,078 rows across 15 endpoints** landed in bronze, verified by reading the counts back out of Delta. Three bugs that only a live call could reveal were fixed first — the client had been written against the docs and never actually run. `fct_Milestone` does not consume it yet; silver still reads Rebecca's existing dataflow, and repointing it is its own change |
| **Manual (~40% of the report)** | Two writers into one contract: a SharePoint path and a CSV path that works today with no admin ticket. **17** manual tables are created and typed — the original 9, plus 8 for the Quality Plan's intake. The `CD_Manual_Ingest` dataflow is **published** as of 2026-08-19 with 19 queries, bound to the real sites; it is not yet authenticated. The lists it reads are complete — 18 lists created 2026-08-19, their **142 columns and 19 `CD Projects` rows** 2026-08-20 |

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
unreachable. Fixed; published tables went from **45 to 54**.

**2. Raw JSON was being shown as a trade name on the live report.** The silver transform read
the Procore `trade` field as a whole object instead of `trade.name`, so the column held
`{"id":…,"name":"Electrical",…}` rather than `Electrical`. That broke every quality trade join
— **631 of 850 non-conformance records** resolved to no trade — **and it was putting raw JSON
into the `Trade` column of the live Monthly Progress Report**. Fixed by reading `trade.name`;
unmapped records fell from **631 to 459** and the report now reads e.g. `Windows`.

The remaining **459** were a genuine vocabulary difference rather than a bug — and have since
been largely closed. See below.

### $22.5M of accounts receivable was attributed to no project, and the check said it was fine

This is the most consequential thing found on Aug 19, and it is the same shape as the $4.85M
change-order error: correct-looking output, no error anywhere.

`dim_Project` read its Sage job number from a view that, since the switch onto our own
medallion, returns `NULL` — the Procore project record simply does not carry a Sage id. So
the column was empty for all 19 projects, the invoice join matched nothing, and **122 of 122
AR invoices resolved to `UNMATCHED`**. **$23,695,760.48 of receivables was attributed to no
project at all.**

Two things made it survive:

- **The row count never moved.** It is a `LEFT JOIN`, so 117 invoices went in and 117 came
  out — which is precisely the check that had been run to prove the source switch was safe.
  The rows survived. The join did not.
- **The flag whose entire job is catching this reported success.** `IsInCrosswalk` was
  derived from the *same wrong view*, so it read TRUE for all 19 projects. A completely
  broken join was reporting itself as fully mapped.

Fixed by joining the crosswalk explicitly. Measured live after rebuilding gold:

| | Before | After |
|---|---:|---:|
| Projects resolving to a Sage job | 0 | **15** |
| `IsInCrosswalk` TRUE | 19 (wrongly) | **15** |
| Unmatched AR invoices | 122 | **24** |
| AR attributed to a project | $0 | **$22,548,861.96** |

The four projects still without a Sage job are three templates and City Harvest — a real and
much smaller gap than the 19 the old flag implied.

Three guards were added, because the offline suite had passed throughout: the test fixture
had been giving `sv_projects` a Sage id where production gives `NULL`, so the suite was
exercising a path that cannot exist live.

### Four more defects — found, fixed, verified against the live workspace

Three of the four had been sitting on the Data Quality page as findings *about Affect's
data*. They were our code being wrong about Affect's conventions. That distinction matters:
a data-quality flag is a claim about the client, and it has to survive being checked.

**1. A tenth of the submittal register was invisible. 223 → 0.** Procore sends the status
`For Record`; our transform only recognised the workbook's wording, `For Record Only`, and
did not recognise `Not Reviewed` at all. **222 of 2,245 submittals** carried a status that
matched nothing, so they dropped out of every status slicer — not shown wrong, not shown at
all. A spelling mismatch, not a vocabulary problem. Fixed.

**2. The trade vocabulary is now largely mapped. 970 → 506 unmapped.** A 16-row alias table
(`qc_seed_TradeAlias`) maps the Procore spellings to the workbook's controlled keys —
`HVAC` → `HVAC_DUCTWORK`, `Sprinkler` → `FIRE_SPRINKLER`, and so on — applied only after the
exact match fails. **464 records recovered.** Unmapped non-conformances fell **459 → 215**
and punch items **511 → 291**.

Only unambiguous pairs were mapped. Three labels are deliberately still unmapped because
only Affect can settle them: **`Drywall/Carpentry` (255 records)**, **`Concrete
Superstructure` (110)** and **`Concrete` (64)** — framing vs board vs millwork, and
cast-in-place vs formwork vs slab-on-deck. Attributing a defect to the wrong trade is worse
than leaving it unattributed.

Separately, and this is a **scope** question rather than a mapping one: Roofing, Glazing,
Windows, Structural Steel, Low Voltage, Demolition, Housekeeping, Light Fixtures, Window
Treatments and others appear in Affect's Procore trade list and have **no equivalent trade
in the 26-sheet checklist library at all**. Affect's Procore vocabulary is broader than the
workbook's. Worth a decision about whether the library should cover them.

**3. 807 cost codes — 15% of the master — were missing from every by-division rollup.
807 → 0.** Our parser required a two-digit CSI division. Affect writes divisions 1 through 9
**without the leading zero**: `1-1000 GENERAL REQUIREMENTS` is Division 01, not a malformed
code. Every one of the 807 was parseable once the parser zero-padded; **not one was
genuinely bad data**. Divisions 01–09 now hold 2,941 codes, 1,540 of them in Division 01
alone. Until today, every cost in those divisions was silently absent from any budget or
cost view grouped by division.

**4. A new blocking check, so the alias table cannot rot quietly.** An alias pointing at a
trade key that does not exist would resolve to nothing and read as "unmapped" — a typo would
look identical to a trade nobody has mapped yet. That is now an error-severity check rather
than a warning.

The gate is at **104 expectations**, 8 warnings and **0 blocking**. The cost-code
expectation, which used to be the largest warning on the page, now passes.

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
2. ~~**2 projects have no Sage crosswalk entry**~~ — **superseded 2026-08-19.** The real
   number is **4 of 19**, and they are three templates plus City Harvest. The "2" came from
   the broken `IsInCrosswalk` flag described above, which was reading TRUE for every project.
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

### ⚠️ The existing reporting is running behind — by less than we first recorded

Re-measured live on **2026-08-19**: Rebecca's Sage data now runs to **2026-07-31**, up from
the **2026-07-20** we recorded on 2026-08-02. Her feed refreshed at some point in between —
it did not stop dead in July. It is still **~19 days behind today**, so the concern is *lag*,
not a dead feed. Outbuild's **2026-07-14** is as measured on 2026-08-02 and has **not been
re-verified since**; we are not claiming it moved, and we are not claiming it did not.

If those dataflows are lagging on the same gateway permission issue described below, the
current reporting is serving numbers nearly three weeks old and nothing has surfaced it.
Worth ten minutes of someone's time to confirm either way.

---

## What needs verification

Honest separation between "built" and "proven correct against reality".

| Item | Status | What would settle it |
|---|---|---|
| **The nightly pipeline does not call Procore** | Known limitation | `cd_01_extract_procore` is not in the nightly run. Extraction runs on a laptop and lands files; the pipeline merges whatever was last landed. "Ran green" means the transforms are healthy, **not** that the data is fresh. **Key Vault is no longer the gate** — resolved 2026-08-19. What is left is rotating the exposed Procore credentials, below |
| ~~**The nightly pipeline does not refresh manual input either**~~ | **Resolved 2026-08-19** | `cd_06_land_manual` does run in `CD_Master_Pipeline`, as the activity *Land Manual Input* — verified live. The pipeline is 6 activities, not 5. The earlier claim was wrong |
| **215 of 850 non-conformance records still have no trade** (was 459) | Needs a decision, not a fix | The alias table closed 464 records across the quality facts. What is left is three ambiguous labels — `Drywall/Carpentry`, `Concrete Superstructure`, `Concrete` — and a set of Procore trades with no equivalent in the checklist library at all, which is a scope question rather than a mapping one |
| **DQ reject detail is stale** | Diagnosed, not yet fixed | The gate reports success while silently failing to write reject detail, so the Data Quality page shows rows from an older run. **Counts are trustworthy; drill-through is not.** Two small fixes identified |
| **Source coverage is 5.26%** | Measured | Only 1 of 19 projects is present in all three systems. This is the single biggest limit on the report, and it is an access problem, not a build problem |
| **Scorecard coverage is 59%** | Measured | 4 of 9 categories cannot be scored — AR (Sage), Profitability (human judgement, stays manual by design), Completion Variance (Outbuild), Daily Reports (SharePoint). **Quote "Project Scorecard (Measured Only)" — 0.44** — or absent data reads as poor performance |
| **`Total Billed` $22.1M vs `Owner Billed To Date` $28.0M** | Expected to differ | Sage AR invoices against Procore payment applications, different grains. Not a defect, but the gap is not explained anywhere on the report yet |
| **`Vendors Missing From ERP` = 125 of 251** | Needs a human | Half the vendor master is unmatched |
| **`Expired Certificates` = 105 of 105** | Needs a human | Put this in front of Affect as a question, not a metric |
| **Four manual-input questions** | Blocking the manual silver → gold link | Whether daily-log compliance means "submitted" or "submitted same day"; whether a milestone is a date or a span; which attestations are monthly; whether the client survey is anonymous. Guessing produces an authoritative-looking number measuring the wrong thing |
| **Three gold tables invisible to the SQL endpoint** | Not a failure — do not "fix" | They hold data and serve the report correctly. Fabric's endpoint metadata sync lagging. Verify with DAX, not SQL |

---

## Roadblocks — one access grant left, down from four

**Three of the four closed on Aug 19**, and only one of them closed the way we expected.
They are recorded below the table, because *how* they closed matters more than that they did.

All the pipework behind each of these is built, committed and tested. Nothing here is
waiting on engineering.

| # | Blocker | Unlocks | Who can grant it | Effort |
|---|---|---|---|---|
| 1 | **Grant `cforey-c@affect-group.com` "Can use" on the connection `nc-affect-1\sage100con;Affect Group`** | Sage AR/AP detail, retainage, actual-cost-by-cost-code, AR scorecard category | Whoever administers the on-prem data gateway | **One grant, one refresh.** No subscription, no code change |
| ~~2~~ | ~~**Issue `OUTBUILD_API_TOKEN`**~~ | ✅ **CLOSED 2026-08-19.** Rebecca placed the token in `AffectKeyVault` at 18:27 UTC. **3,078 rows across 15 endpoints** now land in bronze | Done — thank you | — |
| ~~3~~ | ~~**Provision the SharePoint lists**~~ | ✅ **DONE.** Affect supplied the sites; the `Job Register` is provisioned on BUILD. On the reporting site the 18 lists were created 2026-08-19 and their **142 of 142 columns and 19 `CD Projects` rows** 2026-08-20 — verified by reading the site back through Graph, not from the run status. `CD_Manual_Ingest` is published against it and needs only its first sign-in | — | — |
| ~~4~~ | ~~**"Key Vault Secrets Officer" on vault `OneLake`**~~ | ❌ **WITHDRAWN 2026-08-19 — this ask should never have been made.** It named the wrong vault. The vault actually in use is **`AffectKeyVault`** (RG `Affect_Data`), where our account already held *Key Vault Administrator* inherited at resource-group scope. Nobody needed to grant anything, and this had been sitting in three documents since Aug 13 | Nobody | — |

Plus two Procore permissions worth asking for in the same conversation: `punch_item_types`
and `schedule` both return **403**.

**#1 is now the only one left, so it is also the whole list.** It remains the highest value
per unit of effort by a wide margin, and it may also explain the data-lag finding above.

### How the other three closed, because two of them are worth reading

**The Key Vault ask was wrong, and we made it four times.** Every document here named vault
`OneLake` and recorded the blocker as a missing role assignment on it. The vault Affect
actually uses is `AffectKeyVault`, in a different subscription, where this account already
held administrator rights inherited from the resource group. The ask was **withdrawn, not
completed** — it would have solved a problem that did not exist. Two real defects were
sitting behind it and were only found once the vault was actually exercised: secret names
were never being translated (Key Vault forbids underscores, so `PROCORE_CLIENT_ID` is not a
legal secret name), and the secret helper **failed open** — when a vault lookup did not fire
it silently fell through to an environment variable and reported success. A half-configured
vault would have read a credential from an unaudited source and nobody would have known
until an unattended 02:00 run. It now raises instead.

**The Outbuild client had never actually been run.** It was written against the
documentation and verified against the documentation. The first live call revealed three
faults at once: no User-Agent header, so Cloudflare rejected the request before it reached
Outbuild — indistinguishable from a bad token, which is exactly what we had just been handed;
the wrong response envelope key, which returned one row per page containing the whole page;
and a paging rule that stopped after page one on most endpoints. All three fixed, 3,078 rows
landed and verified by reading counts back out of Delta rather than trusting the run status.

**Affect supplied a site by reusing one they already had.** `AFFECTBUILD1`, not a new site
called `BUILD` — which is fine, and is what the flows now point at.

---

## What comes next

Ordered by value per unit of effort, engineering side.

| # | Work | Depends on |
|---|---|---|
| 1 | Fix the DQ persist gap — create the results table, move reject persistence out of the shared exception handler, record the outcome on the heartbeat | Nothing |
| 2 | ✅ **Done.** `deploy_gold.py`'s default source is now `cd`, so a bare re-deploy no longer silently reverts gold to the legacy warehouse, and its hardcoded publish list is gone | — |
| 3 | ✅ **Half done.** `cd_06_land_manual` is in `CD_Master_Pipeline` as *Land Manual Input*. `cd_01_extract_procore` is still held out, now waiting on the Procore credential rotation rather than on Key Vault | Credential rotation |
| 4 | Explain the `Total Billed` / `Owner Billed To Date` gap on the report itself | Nothing |
| 5 | Land Sage silver, settle the retainage question, repoint the AR views at our own medallion | Blocker #1 |
| 6 | **Unblocked — Outbuild is landing.** What is left is repointing `sv_outbuild_activities` off Rebecca's `Silver_Lakehouse` onto our own bronze, which could take `fct_Milestone` to zero if done carelessly and so is its own change. Then Completion Variance can be scored | Nothing |
| 7 | Answer the four manual-input questions and the quality trade vocabulary, then wire manual silver → gold | A 30-minute call |
| 8 | Retire the local extraction bridge; ingestion moves into Fabric | Procore credential rotation |
| 9 | Mentoring sessions with Rebecca — recorded, on the extractor registry pattern first | Scheduling |
| 10 | ✅ **Intake lists complete** — the 18 lists landed 2026-08-19, their 142/142 columns and 19 project rows 2026-08-20. What is left is signing `CD_Manual_Ingest` in and refreshing it, after which the manual half of the report has a live path | Nothing |
| 11 | Turn the two job flows on: template contents from Affect, a service account to own the SharePoint connection, then smoke-test with a real job | Template contents |

Reaching ~100% scorecard coverage needs items 5, 6 and 7. **Item 6 is no longer gated on
anything but our own work**; 5 needs the one remaining grant, and 7 needs a 30-minute call.

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
