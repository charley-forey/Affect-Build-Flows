# charley-dev — what it is, how it works, and what is left

The one document to read first. Everything else in `_docs/` goes deeper on one area.

---

## What problem this solves

Affect runs monthly project reporting out of a hand-filled Excel workbook: 11 tabs, ~700
manual input cells, one chart, and 14 verified defects — three of which change the numbers
reported to leadership.

`charley-dev` is a complete, self-contained Microsoft Fabric platform that replaces it. It
has its own ingestion, its own lakehouses, its own semantic model and its own report. It
**does not modify anything that already exists** in the workspace; the existing reporting
keeps running untouched while this is proven alongside it.

---

## How it fits together

```
  Procore REST  ─┐
  Sage 100      ─┼─►  CD_Bronze  ─►  CD_Silver  ─►  CD_Gold  ─►  Semantic model ─► Report
  Outbuild      ─┤     raw JSON      typed +         star
  SharePoint    ─┘     + audit       validated       schema
                       columns       + rejects
                                                          ▲
                                                  DQ gate ─┘  (blocks a bad publish)
```

**Bronze** keeps the API payload unparsed. A transform bug is then a re-run, not a
re-extract — which matters most for manual input, where re-extracting means asking people to
retype a month of work.

**Silver** types, trims and validates. Anything that fails lands in `cd_dq_rejects` **with a
reason**. Nothing is ever silently dropped; silent drops are how the workbook's defects
survived for months.

**Gold** is a conformed star schema. Dimensions UNION in the keys observed in the facts, so
referential integrity holds by construction rather than by hope.

**The DQ gate** runs after gold and fails the pipeline on a blocking violation, so the model
is not refreshed and the report keeps yesterday's numbers. A stale report beats a wrong one.

---

## What is live right now

Row counts and model figures measured out of Fabric on 2026-08-02; the item inventory and
blocker position re-checked **2026-08-19**. `build-status.md` is the canonical page for
both.

| Layer | State |
|---|---|
| Bronze | 40 tables from Affect's **production** Procore tenant |
| Silver | 15 typed tables, 14,791 rows, **0 rejects** |
| Gold | 40 tables at the 2026-08-02 read plus the PQP tables landed 2026-08-19; `gold_schema.json` publishes **54** table schemas |
| Model A — `Affect Project Report` | 37 tables, 99 measures, 45 relationships, Direct Lake |
| Report A — `Monthly Progress Report` | **12 pages, 180 visuals**, drill-through, 3 bookmarks |
| Model B — `Project Quality Plan` | **19 tables plus `_Measures`, 42 measures, 23 relationships**, Direct Lake. New 2026-08-19 |
| Report B — `Project Quality Plan` | **7 pages, 95 visuals**. New 2026-08-19 |
| Schedule | Pipeline 02:00 daily, model 04:00 daily (Eastern) |
| Sage | `CD_Sage_Ingest` **deployed** and inert — one gateway connection grant away from running |
| PQP (Project Quality Plan) | **Deployed end to end 2026-08-19** — the client's 44-sheet QA/QC tracker as seeds, silver, gold, a DQ gate, its own model and its own report. [`pqp-solution.md`](pqp-solution.md) |

**Verification:** 14 offline suites, 14 live DAX checks, **107 DQ expectations** (83 blocking,
23 warning) — all passing, zero blocking violations. The pipeline has run end to end, all five
stages green; last run 2026-08-02 22:06.

**What the pipeline does not do:** it never calls the Procore API. Extraction runs on a
laptop and lands NDJSON; the nightly run merges whatever was last landed. Until the Key
Vault blocker clears, "the pipeline ran green" means the transforms are healthy — it does
not mean the data is fresh. As of 2026-08-19 that blocker is one role assignment rather
than a purchasing decision: the subscription and the vault both exist, and the vault is
RBAC-mode where our identity holds only resource-group Contributor.

### The data

| Source | Rows | Notes |
|---|---:|---|
| Cost codes | 5,433 | |
| Submittals | 2,245 | |
| Billing periods | 607 | **carries retainage — see below** |
| Direct costs | 418 | self-performed labour, in no other feed |
| Direct cost lines | 509 | **the vendor ↔ cost-code bridge** |
| Project–vendor pairs | 393 | 251 distinct vendors |
| Vendor↔cost-code pairs | 114 | $1.47M of spend, sliceable both ways |
| Insurance certificates | 105 | **every one expired — see below** |
| Punch items | 1,469 | **not in the existing warehouse** |
| Vendors | 1,098 | |
| Manpower (project-days) | 911 | 120,766 hours — **was reading as zero** |
| Observations | 850 | **not in the existing warehouse** |
| RFIs | 616 | **not in the existing warehouse** |
| Budget lines | 402 | vs 404 in the existing warehouse |
| Change orders | 307 | |
| Prime contracts / projects | 20 / 19 | |

---

## Two models over one gold layer, and why

There are now **two semantic models and two reports**, both Direct Lake over the same
`CD_Gold_Lakehouse`:

| | Model A | Model B |
|---|---|---|
| Name | `Affect Project Report` | `Project Quality Plan` |
| Report | `Monthly Progress Report` — 12 pages, 180 visuals | `Project Quality Plan` — 7 pages, 95 visuals |
| Audience | leadership, portfolio finance | the Q-Team, per-project quality |
| Shape | 37 tables, 99 measures, 45 relationships | 19 tables plus `_Measures`, 42 measures, 23 relationships |
| Replaces | the 11-tab monthly workbook | the 44-sheet QA/QC tracker |

**One lakehouse, two models — not two lakehouses.** `dim_Project` and `dim_Date` are
**conformed**: the same physical gold tables, one definition, bound by both models. A second
lakehouse would have duplicated them, and duplicated dimensions drift — quietly, and then the
two reports disagree about how many projects there are and nobody can say which is right.

**Model A was not touched.** It is live, audited, and 99 measures deep. Adding 19 tables and
42 measures to it to serve a different audience with a different grain would have put a
working model at risk for no gain — and the two audiences do not share a page, a filter
context, or a definition of "open".

**Rollback is deleting one item.** That is the property that made this the cheap choice. If
the PQP model is wrong, it is deleted and nothing else moves; the gold tables stay, Model A
never knew it existed, and the Monthly Progress Report does not blink.

The cost, stated: a measure needed by both audiences has to exist in both models. Today none
do. The day one does, it is written twice or promoted into a shared calculation group — and
that is a smaller problem than a shared model neither audience can safely change.

### How Model B was built — the pattern to copy

`_local/deploy_model_qc.py` and `_local/deploy_report_qc.py` are **~250 lines each**, not
copies of the 800-line and 1,171-line generators they sit on. Each imports the existing
module and overrides three module-level lists:

```python
import deploy_model as dm
dm.MODEL_NAME    = "Project Quality Plan"
dm.MODEL_TABLES  = [...]     # 19 tables
dm.RELATIONSHIPS = [...]     # 23
dm.MEASURES      = [...]     # 42
```

This works because every generator function reads those globals **at call time**. Everything
else — the TMDL emission, the Fabric introspection, the Direct Lake traps, the upload and
retry logic, the visual helpers, alt text, tab order, the synced slicers and footer, the id
stability that stops a redeploy churning every visual — is inherited rather than duplicated.

**This is how the next subject area gets added.** A copy would have rotted the day the
original changed, and the Direct Lake traps in `deploy_model.py` are exactly the knowledge a
copy loses first.

Two supporting scripts came with it: `_local/extract_pqp_workbook.py` (the client's workbook →
seed CSVs, asserting its own row counts so a silently short extract fails loudly) and
`_local/make_qc_seeds.py` (seed CSVs → `08_qc_seeds.sql`).

---

## The three things this does that the spreadsheet cannot

**1. It shows you where the data is missing.** `dim_ProjectCrosswalk` maps every project
across Procore, Sage and Outbuild. Live result when last measured on 2026-08-02: **1 of 19
projects is in all three** — not re-measured since Outbuild began landing on 2026-08-19, and
it should move, because Outbuild is one of the three. Four
are missing from Sage — and a project missing from Sage contributes **zero revenue to every
financial measure without erroring**. It doesn't blank, it doesn't warn; it just looks like a
project that never billed. Nothing could surface that before, and nobody would have gone
looking.

**2. It lets you drill down.** The workbook has one row per project and no way down: a number
that looks wrong can only be checked by asking whoever typed it. Right-click any project →
Drill through opens that project's budget lines, change orders, RFIs and milestones.

**3. It refuses to publish bad numbers.** 107 expectations run between gold and the report —
83 blocking, 24 warning. Blocking failures stop the pipeline.

---

## The scheduled pipeline had never once succeeded

Worth stating first, because everything else was downstream of it.

`CD_Master_Pipeline` was scheduled, enabled, and reported itself as configured. It had run
once and **failed**, and it would have failed every night. `cd_01_extract_procore` was its
first stage and gated every other stage on `Succeeded` — and that notebook cannot
authenticate, because it needs a Procore secret and Key Vault needs an Azure subscription
this tenant does not have. It had failed **4 runs out of 4**.

So silver, gold and the DQ gate had only ever run when somebody triggered them by hand. The
04:00 model refresh then republished unchanged data with nothing saying so.

That is precisely the failure this platform exists to refuse: a schedule that exists, is
enabled, looks configured, and produces nothing.

**Fixed.** Extraction is out of the DAG until it can actually authenticate; in its place is
`cd_05_land_to_bronze`, which merges the landed files and needs no credential (8 runs, 8
successes). The pipeline has now completed end to end for the first time.

Leaving extraction in with a `Completed` condition would have been worse — the run would
still be marked Failed nightly, so the alert that is supposed to mean something would fire
every day and stop meaning anything.

**The honest consequence, which belongs in front of the client rather than in a footnote:**
the report is fresh to the last **landing**, not to the last Procore change. Until Key Vault
exists, somebody runs `extract_procore_local.py` to refresh the landing files. The nightly
run still earns its place — it re-applies every transform, rebuilds gold and re-runs the
104-expectation gate — but it does not fetch new data. Three freshness expectations now warn
when the newest billing, cost or field-ops record goes stale, so "nobody has run the
extractor in two months" is visible instead of silent.

---

## The change-order gap, resolved

Our gold reported **307** change orders where the existing warehouse reports **1,812**. A
lower number that nobody can explain is indistinguishable from a lost one, so this was the
highest-priority open risk.

It is resolved, and the resolution is that **their number is wrong**.

`procore_prime_change_orders` holds 1,812 rows for **454 distinct change orders** — each one
repeated **exactly four times**. The pattern is uniform inside every `batch_id` group: 4 rows
for 1 change order, 12 for 3, 52 for 13. That is a fan-out from a join that never
deduplicated, not an ingestion glitch.

| | Rows | Distinct COs | Total value |
|---|---:|---:|---:|
| Existing warehouse, as stored | 1,812 | 454 | **$20,152,671** |
| Existing warehouse, deduplicated | 454 | 454 | **$5,056,742** |
| charley-dev (`change_order_packages`) | 307 | 307 | **$4,907,551** |

**Nothing was lost.** Any measure summing `CO Value $` from that table overstates change
order value by roughly **4×**. Deduplicated, the two sources agree within **3%**.

The residual 454 vs 307 is grain, not error: `change_order_packages` groups change orders
into packages, and their table also carries statuses ours does not (`not_proceeding`,
`no_charge`, `rejected`, `pricing`). Package grain is accepted because the money agrees; if
change-order-level detail is wanted later that is a different endpoint, not a correction.

**Reported, not fixed** — it is a table in the existing warehouse, and this engagement does
not modify what is already there.


## Vendor ↔ cost code, and insurance

These were the two Phase 0 scope items still open.

**Item 3 — "resolve the vendor ↔ cost-code linkage (invoice as the bridge)".** The linkage
exists in no single Procore object: the direct cost *header* carries the vendor and no cost
code; its *line items* carry the cost code and no vendor. `bridge_VendorCostCode` joins them
on the line's `holder`. **407 rows over 398 distinct vendor↔cost-code pairs** (measured
2026-08-19), and the model can now slice spend by vendor and cost code together, which nothing
could before.

It covers direct costs only — subcontract spend flows through commitment line items, which
are a per-contract nested pull (hundreds of calls against a 600/hour limit) and are not yet
extracted. Every row carries `IsDirectCostOnly` so that limit is on the data, not in a
footnote.

**Item 4 — the vendor list "with insurance and contract info".** The list shipped without
insurance because nothing carried it. It does now, and what it says needs saying plainly:

| | |
|---|---:|
| Certificates on file | 105 |
| Certificates **not expired** | **0** |
| Most recent expiry | **2025-04-01** (16 months ago) |
| Vendors with any certificate | 23 of 251 |
| …of those, actually on a current project | **6** |

**This is not proof that Affect's subcontractors are uninsured.** The likelier reading is
that the Procore insurance module was populated once and abandoned, with current
certificates living in email or a shared drive. But "we stopped tracking it here" and "our
subs are uninsured" have very different consequences for a general contractor, and nothing
in the current reporting distinguishes them — or raises the question at all.

So the model keeps **coverage** (is there a certificate?) separate from **currency** (is it
in date?), and exempt separate from lapsed. A vendor with no record and a vendor with a
lapsed record both fail a single "compliant" flag and need completely different follow-up.

**This is a question for Affect, not a conclusion from us.**


## Retainage — an answer, not a blocker

The workbook has no retainage figure anywhere, and Sage cannot supply one: `retain` on the
invoice header is **zero across all 940 invoices**. The open question named three
candidates — `arivln`, `actrec.retain`, or progress billing — and the first two need the
on-prem gateway Affect has not bound.

It is progress billing, and it was already in our bronze:

| | |
|---|---:|
| Retainage held, owner (owed to Affect) | **$830,726** |
| Retainage held, subcontractor (held by Affect) | **$486,030** |
| **Net position** | **$344,696** |

**This closes the question without the Sage gateway.**

It also came with a trap worth stating plainly, because it is the most likely way for
somebody to get a wrong number out of this platform later. Procore's AIA G702 columns are
**running balances restated in full every period**, not period movements. Adding
`RetainageHeld` across all 607 rows gives **$9,046,212** — a figure that looks like a
plausible retainage number and is nearly **seven times** the real one. Nothing errors.

Two guards, both in `fct_Billing`:

- `IsLatestPeriod` marks the one row per contract carrying the current balance. Every
  measure over a cumulative column filters to it.
- `CurrentPaymentDue` is the only sum-safe money column, so the same answer is reachable a
  second, independent way.

That pair produces an identity the platform checks on every run: **completed-to-date minus
the sum of period payments must equal the retainage withheld**, because retainage is
exactly the completed work not paid out. Live, that is
`28,028,868.93 − 27,198,143.06 = 830,725.87` — the retainage figure, to the cent. If the
ranking ever picks the wrong row, this stops holding.

### The same bug, found in our own front page

Writing those guards prompted a check of every other balance in the model, and
`[Current Contract]` had the identical defect. `fct_FinancialPeriod` is one row per project
per **month**, and the contract amount is repeated on every one of those rows, so `SUM`
multiplied each project's contract by its month count. Unfiltered, the Overview card read
**$355,059,734** against prime contracts totalling about $34M — one project with 19 monthly
rows contributed $168M against a real $9.0M.

It reconciled perfectly when filtered to one project and one month, which is exactly what
the reconciliation gate does. That is why it survived.

Now **$30,254,551**, corroborated independently at $33.9M by the Procore billing side.
`[Original Contract]` and `[Pending Change Orders]` had it too.


## The scorecard, and why it differs from the workbook

Affect reports **0.59** to leadership. This model does not reproduce it, and that is
deliberate.

Two scoring bands in the workbook are wrong. Schedule Performance uses `5`/`10` where the
data is a fraction (`0.05`/`0.10`), so it **always** scored 3. Completion Variance never
matched any band, so it **always** scored 0. On the sample project the two errors cancel
exactly — which is why nobody noticed. On a project where they don't cancel, the workbook's
score is wrong by the difference.

The Scorecard page shows this arithmetic in full. **Affect decides when to switch the number
they report** — that is their call, not ours.

`[Scorecard Coverage %]` is currently **59%**: five of nine categories score from real data.
It went 35% → 45% → 59% as field ops landed. [`build-status.md`](build-status.md) is the
single place that figure is maintained. The measure exists because the workbook's 0.59
looked like a health score while 42% of its weight measured nothing — and because a missing
category scored 0 rather than blank, that was invisible.

---

## How to run it

```bash
cd foundation/charley-dev/_local

python run_tests.py                              # 14 offline suites - no Fabric, no network
python extract_procore_local.py --apply          # Procore -> OneLake landing files
python deploy_landing.py --apply                 # landing files -> bronze Delta
python deploy_seeds.py --apply                   # seed dimensions + the PQP seeds
python deploy_manual.py --apply                  # MUST run before deploy_silver.py
python deploy_silver.py --apply                  # bronze -> silver
python deploy_gold.py --apply                    # silver -> gold star schema
python deploy_dq.py --apply                      # the 104-expectation gate
python deploy_model.py --apply                   # Model A  (TMDL)
python deploy_report.py --apply                  # Report A (PBIR)
python deploy_model_qc.py --apply                # Model B  (PQP)
python deploy_report_qc.py --apply               # Report B (PQP)
python validate_model.py                         # live DAX checks
```

**`deploy_manual.py` before `deploy_silver.py` is load-bearing.** Silver parses the
`cd_bronze_man_*` tables and `cd_06_land_manual` is what creates them. Run silver first and
it fails with `System_Cancelled_Session_Statements_Failed` — an error that names no table and
reads like a Spark fault rather than a missing input.

`--source` selects gold's input: `cd` (**now the default**) builds from **our** medallion,
`existing` from the current warehouse. That one flag is the entire source migration — no gold
file, measure or visual changes between them. The default used to be `existing`, so a bare
`--apply` silently reverted the medallion to the legacy warehouse; that foot-gun is closed.
(Under `--source existing` the QC and manual halves are skipped rather than built empty — the
existing warehouse holds none of that data.)

Everything reaches Fabric through these scripts and the REST API, so every change is in git
and a mis-deploy is fixed by re-running rather than by clicking.

---

## Why extraction runs locally

`cd_01_extract_procore` is the real scheduled ingestion and it runs in Fabric — but it needs
a Procore secret, and the only safe way to give a Fabric notebook one is Key Vault. Every
in-Fabric alternative is plaintext-readable by any workspace member, which is exactly the
finding we reported (`security-findings.md`, F1).

So extraction runs where the secret already lives, and lands files; `cd_05_land_to_bronze`
merges them in Fabric with no credential at all. **A bridge, not the destination.**

**As of 2026-08-19 Key Vault is no longer a blocker at all.** The ask that sat here — a role
on vault `OneLake` — named the wrong vault and is withdrawn; `AffectKeyVault` (RG
`Affect_Data`) was already writable by this account. What is left is **rotating the exposed
Procore credential pair**, after which `setup_keyvault.py --apply` loads the secrets and the
notebook takes over. See [`keyvault-runbook.md`](keyvault-runbook.md).

---

## Manual input can start today

The ~40% of the report that lives in no system was blocked on a SharePoint administrator.
It is not any more.

`cd_06_land_manual` reads CSVs from `Files/_manual/` and writes exactly the bronze tables
the SharePoint dataflow would have — same names, same shapes, same parsers downstream.
**Seventeen** templates with worked examples are generated on every run at
`Files/_manual/_templates/` — the 9 original registers plus the 8 PQP intake lists. Fill one
in, upload it, re-run.

The lists now exist — 18 of them on `AffectProjectReporting_main`, with their 142 columns
and the 19 `CD Projects` rows — and `CD_Manual_Ingest` is published against them. Once that
dataflow is signed in and refreshed it takes over, and nothing downstream changes. Neither
path is a workaround; they are two writers into one contract.

This matters because the slow part was never the plumbing — it is people typing a month of
history they have only ever kept in a spreadsheet, and that no longer waits on a ticket.

**The chain is now complete.** Until 2026-08-19 there was no silver → gold link for the
manual tables: `40_man_tables.sql` created empty typed placeholders and nothing populated
them, so nine gold tables bound to the model were permanently empty while every stage above
them reported green. That is fixed — gold now `INSERT`s from `sv_man_*` over
`cd_silver_man_*`, `30_manual_silver.sql` is no longer excluded from the deploy, and
`test_qc.py` asserts all 17 `man_*` tables are reachable from silver. With no input the
inserts move zero rows and the tables stay empty, which is correct — the platform never
invents a row.

The four column-spec differences that used to be framed as open questions for Affect were
not questions. The gold DDL and the semantic model TMDL had agreed all along; the *input*
side had drifted from both, and it was corrected to match. `deploy_manual.py` no longer
keeps its own column list — it derives it from the DDL. See
[`pqp-solution.md`](pqp-solution.md) Part 1.

**Affect no longer needs to do anything here.** The site question closed on 2026-08-19 and
the lists and columns were provisioned across the 19th and 20th. What is left is one
interactive step on our side: `CD_Manual_Ingest` ships `connections: []` — the honest
not-bound-yet state — and needs its first sign-in and a refresh before the dataflow path is
live. Until then the CSV path is the working one. `manual-input.md` has the detail.


## What blocks the remaining 41% of coverage

**One is left.** Three of the four closed on 2026-08-19 and only one closed the way it was
written — the Key Vault ask named the wrong vault and was withdrawn rather than granted. All
the pipework was built and tested throughout.

| Blocker | Unlocks | Owner |
|---|---|---|
| ~~**SharePoint lists**~~ | ✅ **Provisioned.** The 18 lists landed 2026-08-19 and their 142 columns and 19 `CD Projects` rows 2026-08-20, on `AffectProjectReporting_main`. What is left is signing `CD_Manual_Ingest` in — ours, not Affect's | — |
| ~~**`OUTBUILD_API_TOKEN`**~~ | ✅ **Received 2026-08-19** — 3,078 rows across 15 endpoints in bronze. Repointing `sv_outbuild_activities` off Rebecca's `Silver_Lakehouse` is ours to do | — |
| **Sage gateway connection grant** | AR/AP detail incl. `arivln`/`apivln` — no longer needed for retainage. The dataflow is deployed and inert | Affect IT |
| ~~**Key Vault role assignment** on vault `OneLake`~~ | ❌ **Withdrawn 2026-08-19 — wrong vault.** `AffectKeyVault` was already writable by this account. The remaining gate on running ingestion inside Fabric is the **Procore credential rotation** | — |

Plus two Procore permissions worth asking for in the same conversation: `punch_item_types`
and `schedule` both return **403**.

**The Sage gateway grant is now the only access item on this list.** The Azure subscription
stopped being a blocker on 2026-08-19, and the role assignment that briefly replaced it was
withdrawn the same evening as having named the wrong vault — `AffectKeyVault` had been
writable by this account all along. The remaining gate on running Procore ingestion inside
Fabric is not access at all: it is rotating the exposed credential pair
([`security-findings.md`](security-findings.md)).

---

## The recurring lesson

Almost every defect found here failed **silently** — a valid-looking call returning nothing,
or a parse producing NULL:

- `Procore-Company-Id` missing → **404**, reading as "this project has no RFI tool". Cost 28
  of the 36 endpoints the registry held at the time (it now holds 44 — see
  [`build-status.md`](build-status.md), which is where that count is maintained).
- `manpower_logs` without a date range → **200 with zero rows**, reading as "no manpower
  logged". Cost 120,766 hours.
- `get_json_object` on a key containing `(` or `=` → **NULL**, so every budget money column
  parsed blank and the model looked healthy while reporting nothing.
- A company-level parent deduped on its id → **one project's budget** instead of nineteen.
- `sv_cost_codes` exposing the name but not the code → **5,429 of 5,433** divisions unparsed.
- `percent_complete` written as `"9.28%"` on one endpoint and `"25.07"` on the next → the
  first casts to **NULL**, which on a card reads as a job that has not started.
- A per-project balance summed across months → **$355M** on the front page instead of $30M,
  and it reconciled perfectly whenever anyone filtered to one project to check it.
- A scheduled pipeline whose first stage could never authenticate → **4 failed runs out of
  4**, no medallion on any schedule, and a status page that said "enabled".
- A brand-new gold table that Direct Lake had not yet bound → the model deploys with no
  error, and every measure over it fails only when a visual renders. `validate_model.py`
  now COUNTROWS all 35 model tables for exactly this reason.
- A gold table left out of `deploy_gold.py`'s hardcoded `tables` list → its schema is never
  published to `gold_schema.json`, so `deploy_model.py` cannot type it and Direct Lake
  cannot bind it. The SQL runs, the table holds data, the model deploys — and the table is
  simply **absent**. Cost the three `fct_Qc*` tables until 2026-08-19.
- `get_json_object(payload, '$.trade')` where the field is an **object** → the column holds
  `{"id":…,"name":"Electrical",…}` rather than `Electrical`. Every trade join fails (631 of
  850 NCRs), and `fct_QualityItem.Trade` on the **live** Monthly Progress Report showed raw
  JSON. It parses, it is not NULL, and no test that only checks for NULL would have caught
  it.
- A submittal status `CASE` written against the **workbook's** wording rather than Procore's
  → `'FOR RECORD ONLY'` matched, Procore's actual `'For Record'` did not, and a `CASE` with no
  `ELSE` returns NULL. **222 of 2,245 submittals** — a tenth of the register — carried no
  status and left every status slicer. Not shown wrong: not shown.
- A CSI division parse requiring **two** leading digits, against a client who writes divisions
  1–9 without the leading zero → `1-1000 GENERAL REQUIREMENTS` is Division 01 and read as
  unparseable. **807 cost codes, 15% of the 5,433-code master**, silently absent from every
  by-division rollup — and every one of them was fixable, so the "data quality problem" was
  ours the whole time.

None raised an error. This is why the platform prefers a loud failure to a plausible number,
why rejects are recorded with reasons, and why the DQ gate blocks rather than warns.

---

## Where to read next

| Document | Covers |
|---|---|
| `build-status.md` | What exists in Fabric right now |
| `procore-ingestion.md` | The endpoint registry, the split pipeline, the defects found |
| `sage-ingestion.md` | The dataflow and why `arivln`/`apivln` matter |
| `manual-input.md` | The design for the ~40% that lives in no system |
| `pqp-solution.md` | The Project Quality Plan subject area — Model B end to end |
| `sharepoint-lists.md` | Build sheet to hand to a SharePoint admin |
| `security-findings.md` | Credential exposure in the existing workspace — report only |
| `_local/agents/README.md` | The multi-agent system and its enforced gates |
