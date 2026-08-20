# Dashboard assessment

Where the Monthly Progress Report stands, what changed, what it still cannot show, and who
is holding each missing piece. Written 2026-08-02.

Companion to [`build-status.md`](build-status.md), which covers the pipeline. This one is
about the report.

**Blockers re-checked 2026-08-19** and corrected below; the report measurements are
unchanged from 2026-08-02. **A second report shipped on 2026-08-19** over the PQP (Project
Quality Plan) subject area — the client's 44-sheet QA/QC tracker — with its own semantic
model: `Project Quality Plan`, 7 pages, 95 visuals, over 19 tables and 42 measures. It is a
separate model and report, **not a change to this one** — `dim_Project` and `dim_Date` are
conformed across both, Model A was not touched, and rollback is deleting one item. See
[`pqp-solution.md`](pqp-solution.md).

One defect on **this** report was fixed in the same pass, and it was visible to readers:
`fct_QualityItem.Trade` was showing raw JSON — `{"id":…,"name":"Electrical",…}` — because
`20_fieldops_silver.sql` read Procore's `$.trade` as an object rather than taking
`$.trade.name`. It now reads e.g. `"Windows"`. Nothing errored, nothing was NULL, and no
test that only checks for NULL would have caught it.

---

## The finding

The platform was not the problem. The semantic model has a real star schema, 42
relationships with **no bidirectional filters anywhere**, `discourageImplicitMeasures` set,
auto date/time off, a 7,670-day marked date table, and a data-quality gate that fails the
run rather than publishing empty tables. Three of the four semantic models elsewhere in the
workspace get at least one of those wrong.

**The report layer had not caught up with the model underneath it.** Measured, before this
pass:

| | |
|---|---|
| Cards and textboxes | **76%** of visuals — 55 cards, 22 textboxes, of 101 |
| Actual charts | 10, across nine pages |
| Line charts in the entire report | **1** |
| Visuals with alt text | 22 of 101 |
| Pages setting tab order | 0 of 9 |
| Month slicers anywhere in a report called "Monthly" | **0** |
| Visuals partly off the canvas | 5, on 3 pages |
| Measures with display folders | 0 of 75 |

And `powerbi/theme.json` — a palette whose eight categorical slots were checked for
colour-vision separation and contrast in both light and dark, with contrast-corrected RAG
steps — had been sitting in the repo unused while the report ran bare Power BI defaults.

The design work was already done. It had just never been applied.

---

## What changed

### Anyone can now navigate it

- **Two synced slicers on every page** — project and month. There was no month slicer
  anywhere, so the report could not be set to a reporting period; and each page carried its
  own project slicer or none, so a selection did not survive a page change.
- **A footer on every page** naming the reporting period, the time gold was built, and
  whether the pipeline that built it has run recently enough to trust. The build time is
  stamped into the anchor table, not read from `NOW()` — `NOW()` is when the report was
  *viewed*, which is the workbook's `TODAY()` defect in a new place. The pipeline status is
  text, never colour alone, and it reads "STALE" rather than going quiet: the nightly
  pipeline once failed every night for a month while reporting itself as enabled.
- **Alt text on all 180 visuals**, generated from what each visual is bound to, so it
  cannot drift when a field changes.
- **Tab order on every visual**, assigned in reading order. Setting it on *some* visuals is
  worse than none: the rest fall back to z-order and a keyboard user jumps around.
- **The validated theme applied**, layered over the Microsoft base.

### It now answers "which way is it moving"

- **Portfolio page** — new, and first. A matrix of project × scorecard category, plus
  contract/billed/paid per job and AR ranked. Leadership had no cross-project view at all;
  the Excel is one workbook per job, and every page of the report had inherited that shape.
- **Billing S-curve** — cumulative billing against the contract line. The chart a GC reads
  to know whether billing is keeping pace, and the one thing a monthly snapshot
  structurally cannot show.
- **Schedule timeline** — a stacked-bar Gantt. See the limitation below.
- **Budget as a matrix** rolling up by division, instead of a flat table over 4,837 cost
  codes.
- **Vendor Insurance page**, and vendor spend sliced by cost code — a linkage that exists
  in no single Procore object. The insurance page leads with the bad news deliberately:
  all 105 certificates in Procore are past expiry and only 23 of 268 vendors have one on
  file at all. Coverage ("is there a certificate") and currency ("is it in date") are
  counted separately throughout, because a missing document and a lapsed one need
  different follow-up. That is far more likely an abandoned module than 245 uninsured
  subcontractors — but a compliance page that renders it as a green tick is worse than no
  page.
- **Insurance exposure on the Portfolio page**, so "which jobs are running subs with no
  certificate on file" is one screen rather than seventeen.

### The scorecard shows its working

It had two tables that could not be read against each other: weights in one, raw band rows
in the other keyed by `CategoryKey` — an integer surrogate being rendered to readers. The
band table now carries `CategoryName` as its own column, so the two stay unrelated. (A
relationship was tried first and deploying it showed why not — see the deployment note
below.)

One table now gives **category · score · band · weight · contribution**, and the
contribution column sums to `[Project Scorecard]` exactly, because it is driven by the same
`SWITCH` as the headline measure. `validate_model.py` asserts that sum.

This is the view in which the workbook's three dead bands would have been obvious.

---

## What it still cannot show

Honest list. Most of it is other people's turnaround, not build effort.

| Missing | What it blocks | Owner |
|---|---|---|
| **Milestone baselines** | The Gantt shows the schedule as it stands and **cannot show drift**. `fct_Milestone` has `CurrentStart`/`CurrentFinish` only — no baseline, no actual | Affect — Outbuild |
| ~~**Outbuild token**~~ | ✅ **Received 2026-08-19** — 3,078 rows across 15 endpoints now land in `cd_bronze_outbuild_*`. Milestones still read Rebecca's `Silver_Lakehouse` dataflow, so repointing `sv_outbuild_activities` is the remaining step, and it is ours | — |
| **Manual / narrative tables** (wins, risks, priority items, survey, flags) | ~40% of the report | Affect — the SharePoint decision |
| **Safety**: incidents, hours, orientations, violations | The whole safety domain; `[TRIR]` is not computable | Affect — Procore credentials |
| **Quality**: observations, punch items | Both now land — 850 and 1,469 rows, as `fct_QcNcr` and `fct_QcPunch` on the PQP model. `punch_item_types` still 403s, but silver derives the punch class from the item itself so nothing downstream depends on it | Affect — Procore permissions, for completeness |
| **Quality by trade** | Largely resolved 2026-08-19 — `qc_seed_TradeAlias` (16 pairs) recovered 464 rows; **215 of 850** NCRs and **291 of 1,469** punch items still resolve to no trade. Two things left: three ambiguous labels deliberately not guessed (`Drywall/Carpentry` 255, `Concrete Superstructure` 110, `Concrete` 64), and a **scope** question — Roofing, Glazing, Windows, Structural Steel, Low Voltage and others have no equivalent trade in the 26-sheet library at all. Counts sit on the PQP Data Quality page rather than being charted | Affect — one mapping decision, one scope decision |
| **Daily logs** | `Score - Daily Reports`; Procore 403 on `schedule` | Affect — Procore permissions |
| **Sage AP/AR, retainage, aging, job cost** | Cash position, aging, cost-to-complete | Affect — one *Can use* grant on the gateway connection; `CD_Sage_Ingest` is deployed and inert |
| **Payment dates in Sage AR** | `[Avg Days To Payment]` returns BLANK by design — the AR header carries the amount paid but not the date | Affect — confirm whether it exists elsewhere in Sage |
| **The six client-satisfaction questions** | Satisfaction breakdown; not stored anywhere | Affect |
| **Manpower daily** | Manpower trend by vendor | Us, once ingestion runs |
| **Key Vault role assignment** — the subscription and the vault (`OneLake`) both exist as of 2026-08-19; the vault is RBAC-mode and our identity holds only resource-group Contributor, which cannot read or write secrets | Extraction runs locally as a bridge. One role: **Key Vault Secrets Officer on `OneLake`** | Affect |

**Scorecard coverage is 59%** — maintained in [`build-status.md`](build-status.md), quoted
here. Four of nine categories score BLANK — deliberately, never zero, because scoring a
missing input as zero is exactly how the workbook silently cost every project 15% of its
score. Coverage rises toward 100% as safety, quality, daily logs
and Sage land. The categories are independent, so this is incremental.

### Four of these are one grant each

Outbuild token (sent, awaiting arrival) · Procore permissions for `punch_item_types` and
`schedule` · the *Can use* grant on the Sage gateway connection · the SharePoint decision.
Those four unlock roughly half the missing report. A fifth, new and equally small, is the
Key Vault Secrets Officer role that moves Procore extraction off a laptop.

---

## Can we validate the data?

Yes, and most of it already runs.

**Offline — 14 suites, no network, no Fabric.** `python _local/run_tests.py`. The `.sql`
runs through DuckDB via three macros, so the tests exercise the *production* Spark SQL
rather than a re-implementation. Two suites reproduce the reconciliation gate exactly:
Current Contract 9,116,960.48 and Contract Growth 3.60%. Mutation-tested — five deliberate
regressions are each caught.

**New in this pass:** `test_report.py` asserts the things that fail silently — alt text on
every visual, unique tab order, both slicers present and synced, a footer on every page,
nothing running off the canvas, nothing hidden under the footer, and that the registered
theme still carries the corrected RAG steps. It found all five off-canvas visuals.

**In Fabric — the runs assert themselves.** A notebook that builds empty tables still
reports Completed, so both notebooks check their own output and fail the run otherwise.

**Live DAX —** `python _local/validate_model.py` reframes the model and queries it. Now
also asserts that the scorecard audit table sums to the headline score, that every category
resolves a band label including the unmeasured ones, and that the S-curve ends at the total
of period movement.

**Deployed and verified in Fabric, 2026-08-02.** Silver, gold, seeds, the DQ gate, the
model and the report are all live in `charley-dev`: **37 tables, 99 measures, 12 pages, 180
visuals**. `validate_model.py` reframes the deployed model and passes **17 checks**.
`[Last Refresh]` returns the real gold build time and the scorecard audit table sums to the
headline score against live data. On 2026-08-19 a second model and report joined them —
`Project Quality Plan`, 19 tables plus `_Measures`, 42 measures, 7 pages, 95 visuals.

One deployment trap worth writing down, because it cost a rebuild: `deploy_gold.py` **used
to** default to `--source existing`, which reads the legacy warehouse. Under that source the
direct-cost line, insurance and commitment views are deliberately **empty typed stubs** — the
legacy warehouse does not hold those objects. Running the default against a lakehouse fed by
our own ingestion silently emptied seven gold tables. The verification step inside the
notebook caught it and failed the run, which is exactly what it is for. **`DEFAULT_SOURCE` is
now `cd`**, so the trap is closed; `--source cd` is redundant rather than mandatory.

A second trap, closed in the same pass and worth more attention because nothing caught it:
`deploy_gold.py` carries a **hardcoded `tables` list** that drives the schema publish to
`gold_schema.json`. A gold table missing from that file cannot be typed by `deploy_model.py`,
so it **silently cannot appear in any semantic model** — the SQL runs, the table holds rows,
the model deploys and reports success, and the table is simply absent. Cost the three
`fct_Qc*` tables until 2026-08-19. **45 → 54 tables published.**

One thing the deployment caught that offline testing could not: relating the two scorecard
config tables so the band table could show a category name made Power BI add a blank
unknown-member row to `dim_ScorecardWeight`. It rendered as an empty row on the Scorecard
page and an empty column on the Portfolio heatmap, and it nulled the "weights sum to 1.00"
assertion. `dim_ScorecardBand` now carries `CategoryName` as its own column and the two
tables stay unrelated. A blank member is invisible in a screenshot and wrong in a total -
exactly the class of thing that only shows up against the real service.

**What is not yet automated:** a reconciliation *page* in the report showing each measure
against its known Excel value. The values are asserted in CI; they are not visible to
Affect. That needs a seed table of expected values — worth doing, not done here.

---

## What I would do next, ranked

1. ~~**Promote RFIs to gold.**~~ **Already done — this entry was stale.** `sv_rfis` is defined
   in `01_source_views_cd.sql` and `23_fct_rfisubmittal.sql` reads it; verified live,
   `fct_RfiSubmittal` holds **2,861** rows = 2,245 submittals + **616 RFIs**, so the chart the
   workbook had is complete. It was only ever missing under the old `--source existing`
   default, where `sv_rfis` does not exist; that default is now `cd`.
2. **Take the four unblocking items to the next Affect call.** Highest ratio of report
   unlocked to effort spent, by a wide margin.
3. **Reconciliation page**, so the numbers Affect can check are on screen rather than in CI.
4. **Row-count parity bronze → silver → gold as a visual.** This is what would have caught
   the legacy estate's `procore_commitment_change_orders` reading 0 rows in Silver against
   548 in Bronze, and `procore_vendors_raw` dropping 1,075 → 94.
5. **Row-level security** before the Portfolio page is shared — it is the first page that
   shows every PM each other's jobs.
6. **Best Practice Analyzer** over the TMDL in `run_tests.py`, so unformatted measures and
   unused columns get caught automatically from here on.

---

## One thing worth raising directly

The amber in Affect's workbook — `#FFD800` — measures **1.36:1 contrast** on white. That is
effectively invisible. Green measures 2.87:1, below the 3:1 floor. Both were re-stepped
here after measuring, not by eye.

It is a plausible reason "Watch" status gets overlooked in the spreadsheet today, and it is
worth saying out loud rather than quietly fixing, because they have been reading that
colour for years.

Related: red/green cannot be made colourblind-safe as colour alone — measured separation
under deuteranopia is ΔE 7.1, below the ΔE 8 floor, and no re-stepping fixes the hue pair.
Roughly 1 in 12 men cannot reliably tell the two apart. Every status in this report
therefore carries its text label beside the colour, which is Affect's own existing
convention (`🔴 High`, `🟢 On Track`) made explicit and enforced.
