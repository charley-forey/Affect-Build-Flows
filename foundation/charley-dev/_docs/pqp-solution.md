# PQP — the Project Quality Plan subject area

The client's QA/QC workbook is 44 sheets. This is what it became, why it became that shape,
and what is still blocked.

**Status: deployed end to end on 2026-08-19.** Seeds, silver, gold, the DQ gate, a semantic
model and a report are all live in the `charley-dev` folder. Part 6 covers the model and the
report; Part 5 is what is still blocked, and the honest answer is that nobody has typed a PQP
row yet.

Read `_docs/manual-input.md` first if you want the history of the manual pipeline — the
first half of this document is about fixing it, because the PQP work sits on top of it.

---

## Part 1 — the root cause that had to be fixed first

`manual-input.md:248` recorded that **`40_man_tables.sql` created empty typed placeholders
and nothing populated them from `cd_silver_man_*`**. Nine gold tables, bound to the semantic
model, permanently empty. The CSV templates, the loader notebook, the silver parsers and the
reject log all ran green and delivered nothing, because the last statement in the chain did
not exist.

Eight more manual tables were about to be added on that same path.

### What was actually broken (six things, not one)

**1. There were no `sv_man_*` source views.** Gold reads `sv_*` and nothing else. There was
no `sv_man_wins`, so `40_man_tables.sql` had nothing it *could* select from.
→ `sql/silver/01_source_views_cd.sql` now defines all nine, plus the eight new PQP ones.

**2. `30_manual_silver.sql` was excluded from the deploy.** `deploy_silver.py` skipped
prefix `30`, with a comment saying "add 30 the day the lists exist". The lists effectively
exist: `cd_06_land_manual` creates every `cd_bronze_man_*` table from CSV — empty and
correctly typed when nobody has uploaded anything, with `ProjectKey`/`Editor` already wrapped
in the `{Title: …}` struct the parsers read. So with `30` excluded, `cd_silver_man_*` never
got built at all.
→ The deny-list is now `("00", "01")`. `31_qc_manual_silver.sql` is picked up by the same
rule, which is why it is numbered 31.

**3. Four tables' columns had drifted, and it looked like a design question.**
`manual-input.md` framed this as four open questions for the client. It was not. The gold
DDL and the semantic model TMDL have agreed with each other all along; the *input* side had
drifted away from both:

| Table | Gold + TMDL always wanted | Silver + the CSV loader collected |
|---|---|---|
| `man_DailyLogCompliance` | `LogsMissedSameDay` | `LogsSubmitted` |
| `man_Milestones` | `ActivityKey`, Contract/Baseline **spans** | four single dates, no `ActivityKey` |
| `man_Flags` | `ContingencyRemaining`, `BaselineApproved`, `BaselineRevision`, `MonthEndClosedOut`, `ForecastingInLine`, `ResourcesUpdated` | `CostMgmtFlag`, `ScheduleFlag`, `Notes` |
| `man_Survey` | `SurveyedParty` | *(not collected)* |

Nothing had to be decided. The gold DDL is the contract the DAX reads by name, so the input
side was corrected to match it — and `deploy_manual.py` no longer keeps its own column list
at all, it derives it from the DDL.

**4. `deploy_gold.py` was about to overwrite the fix.** It carried a cell that loaded
`man_*` from `Files/manual/<table>.csv` with `mode("overwrite")` — a *third* manual input
path, separate from `cd_06_land_manual`'s `Files/_manual/` and from the SharePoint dataflow,
and it ran **after** `40_man_tables.sql`. The moment gold started populating from silver,
that cell would have wiped every row. It is now a materialise-only cell (Direct Lake needs
real Delta data files, which is the part of it that was load-bearing).

**5. `deploy_gold.py` carries a hardcoded `tables` list, and the QC tables were not in it.**
This is the one worth reading twice, because it is not a PQP problem — it is a property of
the build that will bite whoever adds the next gold table.

That list does two jobs: it drives the empty-table guard, and it drives the schema publish to
`gold_schema.json`. **A gold table missing from `gold_schema.json` cannot be typed by
`deploy_model.py`, and therefore silently cannot appear in any semantic model.** Nothing
errors. The SQL runs, the table holds rows, the model deploys and reports success, and the
table is simply absent from it — which looks exactly like forgetting to add it to
`MODEL_TABLES`, so the first hour of debugging is spent in the wrong file.

`fct_QcNcr`, `fct_QcPunch` and `fct_QcSubmittal` were therefore neither row-checked nor
published. Fixed: the three facts are in `tables`, and the five `qc_seed_*` plus
`dim_QcStatus` are in the schema-publish list. **45 → 54 tables published** (53 on the first
pass; `qc_seed_TradeAlias` took it to 54).

**6. `20_fieldops_silver.sql` read `$.trade` as an object.** Procore returns
`{"id":…,"name":"Electrical",…}` for that field, and the parser took the whole object rather
than `$.trade.name`, so the silver column held raw JSON. It parses, it is not NULL, and
nothing that checks for NULL would have caught it. Two consequences, one of them already
live: every `fct_Qc*` trade join failed — **631 of 850 NCRs** resolved to no trade — and
`fct_QualityItem.Trade` on the **live Monthly Progress Report** was showing raw JSON to
readers. Fixed: unmapped NCRs **631 → 459**, and `fct_QualityItem.Trade` now reads e.g.
`"Windows"`. What remained was a genuine vocabulary difference, now largely closed — Part 5.

**7. The submittal status `CASE` was written against the workbook, not against Procore.**
`24_qc_procore_silver.sql` mapped `'FOR RECORD ONLY'` — the workbook dropdown's wording.
Procore actually sends **`'For Record'`**, and `'Not Reviewed'` was not handled at all. A
`CASE` with no `ELSE` returns NULL, so **222 of 2,245 submittals** — a tenth of the register
— carried no status code and fell out of every status slicer on the Submittals & Mock-Ups
page. Not shown wrong: not shown. Fixed 2026-08-19, both spellings mapping to
`FOR_RECORD_ONLY` and `'Not Reviewed'` to `PENDING`; **223 → 0**. A spelling mismatch, not a
vocabulary problem — and worth separating from item 4 in Part 5, which genuinely is one.

### The list-name break, fixed at the source

`provision-sharepoint.ps1` created `CD PriorityItems`; `mashup.pq` read `CD Priority Items`.
Neither errors — SharePoint returns nothing for a list that does not exist under that name,
so the dataflow would have landed an empty table and the report a blank tile.

`_local/make_sharepoint.py` now generates **all three** artefacts from the `man_*` DDL:

```
sql/gold/40_man_tables.sql  ─┐
sql/gold/41_man_qc_tables.sql─┴─→  provision-sharepoint.ps1     (the lists and columns)
                                →  mashup.pq                    (SharePoint → bronze)
                                →  queryMetadata.json
                                →  deploy_manual.LISTS          (imported, not copied)
```

`list_name()` is the only place a list name is decided; `bronze_table()` the only place a
bronze table name is. `test_sharepoint.py` asserts all four writers still agree, and
`make_sharepoint.py --check` fails on a stale artefact.

### One more root cause found on the way

`split_statements` split on every `;` and stripped from every `--`, including inside string
literals. Fine while the SQL contains only identifiers; catastrophic the moment a literal
contains one — and `08_qc_seeds.sql` inlines 943 rows of workbook prose, 43 of which contain
a semicolon. There were four copies of that parser (`seedrunner`, `deploy_seeds`,
`deploy_silver`, `deploy_gold`). There is now one, quote-aware, in `seedrunner.py`; the
other three import it.

---

## Part 2 — the two structural collapses

Both were decided before this work started. Both are implemented; here is what they cost and
what they bought.

### 26 trade checklist sheets → one table

The workbook has 26 sheets — Excavation, Concrete Formwork, … Fire Alarm — with an
**identical** schema: a numbered item, its text, a pass/fail, a four-stage inspection cycle.

→ `qc_seed_ChecklistItem`: **625 items across 26 trades**, discriminated by `TradeKey`.
→ `man_QcChecklistResult`: one row per project per item.

Twenty-six tables would have meant twenty-six near-identical measures, and adding trade 27
would be a schema change rather than a row. The stage and result dropdowns live on the
Excavation sheet in the workbook but are the same two dropdowns on all 26 — which is the
evidence *for* the collapse, not an artefact of it.

### Three gate paths → one table

Path to TCO (46 steps), Path to Fire Alarm (23) and Statutory Inspections (24) are the same
shape: a numbered step with an authority, a prerequisite, a responsible party and a piece of
evidence.

→ `qc_seed_Gate`: **93 gates**, split 46 / 23 / 24, discriminated by `GateType`.
→ `man_QcGate`: one row per project per gate.

What this bought: `LinkedTcoGate` carries a statutory step back to the TCO step it gates —
21 of the 24 statutory steps do. In the workbook that relationship could only be expressed
by reading two sheets side by side; nobody could query it. It is now a join.

What it cost, stated plainly: one result table means one `StatusCode` choice column, so it
offers the **union** of the three paths' vocabularies — **15 codes** where the three
separately hold 6, 7 and 9. The alternative was three lists differing only in a dropdown,
which is what the workbook had. `test_sharepoint.py` asserts this deliberately, so it reads
as a decision rather than a bug.

---

## Part 3 — where each thing comes from

The single most important design decision in this subject area. **Procore is the client's
mandatory system of record for quality — their own workbook says so.** So anything Procore
already owns is read from the API and is *not* a list to type into. A SharePoint NCR log
next to a Procore NCR log is two answers to "how many are open", and the workbook already
demonstrates which one wins: neither, because nobody trusts either.

| Source | What | Where |
|---|---|---|
| **Seed** (identical on every project) | 26 trades, **16 trade aliases**, 625 checklist items, 93 gates, 101 DOH requirements, 141 status codes | `sql/gold/08_qc_seeds.sql`, generated from `seed/*.csv` by `_local/make_qc_seeds.py` |
| **Procore** (system of record) | NCRs ← observations, punch items, submittals, inspections | `sql/silver/24_qc_procore_silver.sql` → `sql/gold/33_fct_qc.sql` |
| **SharePoint / CSV** (no system holds it) | DFOW register, ITP, gate progress, special inspections, commissioning, inspector sign-in, checklist answers, DOH answers | `sql/silver/31_qc_manual_silver.sql` → `sql/gold/41_man_qc_tables.sql` |

### The Procore facts

`fct_QcNcr`, `fct_QcPunch`, `fct_QcSubmittal` — three facts, not one union. `fct_QualityItem`
already unions observations and punch items behind an `ItemType` and stays as-is for the
monthly report's counts. These three are the quality plan's working views, and each sheet
carries columns the others do not (root cause and disposition on an NCR, a category on a
punch item, a type and a responded date on a submittal). Unioning them would produce a table
two-thirds NULL and a measure set full of `ItemType` filters.

`24_qc_procore_silver.sql` reads the **already-typed** `cd_silver_*` tables rather than
re-parsing the same JSON — 20_fieldops_silver already did that, and two parsers over one
payload is two parsers to keep in step. What it adds is the mapping from Procore's
configurable status text onto the workbook's fixed vocabulary, with the raw text kept
alongside so an unmapped value is a visible row rather than an `ELSE` branch.

### Endpoints

`observations`, `punch_items` and `submittals` were **already in the registry** — the PQP
work needed no new endpoint for them, which is the registry paying off. Two were added,
taking the registry from 42 to **44** ([`endpoint-inventory.md`](endpoint-inventory.md) is
generated from it):

- `checklist_lists` — Procore Inspections, `/rest/v1.0/checklist/lists`
- `checklist_list_items` — parent-scoped on the above, one call per inspection

`punch_item_types` returns **403 on this tenant** and the entry is annotated rather than
deleted: silver derives the punch class from `punch_item_type.name` on the item itself, so
nothing downstream depends on it, and deleting the entry would turn a known permission gap
into an invisible one.

---

## Part 4 — what it is verified by

`python _local/run_tests.py` — 14 suites, no framework, no network, no Fabric. The engine is
DuckDB via `seedrunner.py`, which applies Spark→DuckDB compatibility macros and then runs the
**real production `.sql` files unchanged**. What passes here is the SQL that ships.

- `test_qc.py` — 27 checks: both collapses (625/26, 93 = 46/23/24, 101 DOH), unique keys on
  every seed and result table, no orphaned `ProjectKey` or `TradeKey`, every result resolving
  to its template, every code resolving to `dim_QcStatus`, and — the one that would have
  failed before any of this — **all 17 `man_*` tables reachable from silver**.
- `test_silver.py` — 40 checks, up from 29. The manual parsers are now exercised at all, with
  struct-shaped bronze fixtures generated from the same DDL the pipeline uses.
- `test_sharepoint.py` — 12 checks, including that all four writers agree on every list name
  and column, and that the PQP choice lists come from `qc_status_vocab.csv`.
- `expectations.py` — **63 → 104 expectations** (81 blocking, 23 warning). The newest is an
  ERROR-severity `referential` check on `qc_seed_TradeAlias.TradeKey` — see Part 5, item 4.

### Two data findings worth knowing

**`dim_QcStatus` holds 141 rows, not 143.** Two workbook dropdowns were extracted into one
domain each, so `STATUTORYINSPECTIONS_5` carried `N_A` twice and `SUBMITTALSMOCKUPS_6`
carried `APPROVED` twice. A choice column cannot offer the same value twice and a dimension
cannot have a duplicate key, so first occurrence wins. Marked `ponytail:` in
`make_qc_seeds.py` — the upgrade path is for `extract_pqp_workbook.py` to name a domain after
the *column* it came from rather than after its code count, and the two merged dropdowns
separate on their own.

**The workbook writes an em dash for "none".** In `Prerequisite` (29 gates) and in
`LinkedTcoGate` (3 statutory steps that gate nothing). Carried literally, every join over
those columns dangles against a one-character string and reads as a broken reference rather
than as the absence it is. Both become NULL.

`RiskTier` runs **1–4**, not 1–3: five trades (waterproofing, electrical, plumbing, fire
sprinkler, fire alarm) carry tier 4 — the life-safety and water-ingress trades.

---

## Part 5 — what is still blocked

**Nobody has typed a PQP row yet, and that is the whole remaining cost.** Every table above
builds and is reachable; all of them are empty in Fabric until someone fills a template. The
plumbing was never the slow part.

1. **SharePoint provisioning still needs an administrator.** `provision-sharepoint.ps1` now
   creates 17 lists and 140 columns, and it still needs someone with SharePoint admin in
   Affect's tenant to run it once. The CSV path (`Files/_manual/<list>.csv` →
   `cd_06_land_manual`) works today and needs nobody, which is why data entry does not have
   to wait for this.

2. **`CD_Manual_Ingest` is not bound.** `SITE` in `mashup.pq` is still
   `https://REPLACE-ME.sharepoint.com/…`. It is generated now, so binding it is replacing one
   constant — but it cannot be bound until the lists exist.

3. **`punch_item_types` returns 403.** Needs a tool permission on the service account.
   Nothing downstream depends on it.

4. **The Procore trade → `TradeKey` mapping — aliased 2026-08-19, and what is left is two
   narrower questions.** The exact match resolves `'Concrete Formwork'` → `CONCRETE_FORMWORK`;
   `qc_seed_TradeAlias` (16 rows, `seed/qc_trade_alias.csv` → `make_qc_seeds.py`) now runs as
   a fallback **after** it, joined on the **raw** Procore label rather than the normalised key
   — an alias exists precisely because the label does not normalise to a key. The `ponytail:`
   marker in `33_fct_qc.sql` that predicted this table is resolved and removed.

   Live, against real data: **970 → 506 unmapped**, 464 rows recovered. `fct_QcNcr`
   **459 → 215**, `fct_QcPunch` **511 → 291**.

   Only unambiguous pairs were mapped — `HVAC` → `HVAC_DUCTWORK`, `Sprinkler` →
   `FIRE_SPRINKLER`, `Ceramic Tile` → `TILE_STONE`, `Millwork` and `Cabinetry` →
   `MILLWORK_CASEWORK`, `Masonry` → `UNIT_MASONRY`, `Carpet` and `Flooring` →
   `RESILIENT_FLOORING`, the `Doors` variants → `DOORS_HARDWARE`, `Drywall` →
   `DRYWALL_BOARD`. What is deliberately absent is two different problems:

   **(a) Three ambiguous labels.** `Drywall/Carpentry` (255 rows), `Concrete Superstructure`
   (110) and `Concrete` (64). Framing, board or millwork; cast-in-place, formwork or
   slab-on-deck. Only Affect can say. Attaching a defect to the wrong trade is worse than
   attaching it to none, so they stay NULL behind `HasUnmappedTrade`.

   **(b) A separate finding, and it is a scope question rather than a mapping one.** Roofing,
   Glazing, Windows, Structural Steel, Low Voltage, Demolition, Housekeeping, Light Fixtures,
   Window Treatments and others appear in Affect's Procore trade list and have **no equivalent
   trade in the 26-sheet checklist library at all**. Affect's Procore vocabulary is simply
   broader than the SaunaLounge workbook's. No alias can close that; the question is whether
   the checklist library should cover those trades.

   **A new ERROR-severity guard covers the alias table itself:**
   `referential("qc_seed_TradeAlias","TradeKey","qc_seed_Trade","TradeKey")`. An alias pointing
   at a `TradeKey` that does not exist resolves to NULL and reads as *unmapped* — so a typo in
   a CSV we control would look identical to a trade Affect never aliased. ERROR rather than
   warn, because an unmapped trade is a fact about Procore and a broken alias is our bug.

   The report still carries the counts on its Data Quality page rather than charting quality
   by trade — a by-trade chart would still leave a quarter of the NCR register out of its
   bars without saying so.

5. **Procore Inspections may make `man_QcChecklistResult` redundant.** A Procore checklist
   list *is* a per-project instance of a checklist template, which is exactly what the 26
   trade sheets are. `checklist_lists` and `checklist_list_items` are in the registry and
   `cd_silver_qc_inspection` parses, landed deliberately so the comparison can be made
   against real data rather than argued about. **Nothing reads it in gold yet** — that is the
   next decision, and it is the client's to make once they can see both.

6. **`deploy_gold.py --source existing` no longer builds the QC or manual halves.** The
   existing warehouse holds none of it — this data was invented as part of this build. Rather
   than hand it empty views that pretend a source exists, `GOLD_CD_ONLY` skips those three
   files under `--source existing`, and `DEFAULT_SOURCE` is now `cd`, which is what has been
   in production since 2026-08-02. The gold SQL is still byte-identical across both sources;
   only the selection differs.

---

## Part 6 — the model and the report, deployed 2026-08-19

The item at the top of this list used to read *"no semantic model or report changes"*. Both
now exist in the workspace, which takes the `charley-dev` folder to **20 items**.

| | |
|---|---|
| `Project Quality Plan` (SemanticModel) | Direct Lake, **19 tables plus `_Measures`, 42 measures, 23 relationships** |
| `Project Quality Plan` (Report) | **7 pages, 95 visuals** |

### Why a second model rather than 19 more tables in the first

Both models are Direct Lake over the **same** `CD_Gold_Lakehouse`. `dim_Project` and
`dim_Date` are **conformed** — the same physical tables, one definition, two models. A second
lakehouse would have duplicated them, and duplicated dimensions drift until the two reports
disagree about how many projects there are.

Model A (`Affect Project Report`) is live, audited and 99 measures deep, and it serves
leadership portfolio finance. Model B serves the Q-Team at per-project quality grain. They
share no page, no filter context and no definition of "open". Adding 19 tables and 42
measures to a working model to serve a different audience would have risked the working one
for no gain — and **rollback here is deleting one item.** The gold tables stay, Model A never
knew it existed.

The cost, stated: a measure both audiences need has to exist in both models. Today none does.

### `TradeKey` resolves to `qc_seed_Trade`, not `dim_Trade`

Worth calling out because it looks like a mistake. The PQP uses the workbook's controlled
trade vocabulary (`EXCAVATION`, `WATERPROOFING`, …), which is a different key space from the
existing `dim_Trade`. Relating the two would have produced a blank unknown-member row that
renders as an empty category and nulls any total over it.

### The scripts are overrides, not copies

`_local/deploy_model_qc.py` and `_local/deploy_report_qc.py` are ~250 lines each. They
**import** `deploy_model` and `deploy_report` and override three module-level lists:

```python
import deploy_model as dm
dm.MODEL_NAME    = "Project Quality Plan"
dm.MODEL_TABLES  = [...]   # 19
dm.RELATIONSHIPS = [...]   # 23
dm.MEASURES      = [...]   # 42
```

…and `deploy_report_qc.py` overrides `dr.PAGES` (7) plus the report and model names. This
works because every generator function reads those globals **at call time**.

Everything else is inherited: the TMDL emission, the Fabric introspection, the Direct Lake
traps, the upload and retry logic, the visual helpers, alt text, tab order, the synced
slicers and footer, the id stability that stops a redeploy churning every visual. The
alternative was copying 800 and 1,171 lines, which would have rotted the day the originals
changed — and the Direct Lake traps are exactly the knowledge a copy loses first.

**This is the pattern for the next subject area.** Three lists and a name.

### What the report deliberately does not have

A "quality by trade" headline. With 215 of 850 NCRs still unmapped (Part 5, item 4) — down
from 459 — charting by trade would still leave a quarter of the register out of its bars
without saying so. The count sits on the Data Quality page instead, where it is the finding
rather than the footnote.

---

## Deploying it

**`deploy_manual.py` must run before `deploy_silver.py`.** Silver parses `cd_bronze_man_*`,
and `cd_06_land_manual` is what creates those **17** tables — typed and empty when no CSV has
been uploaded. Run silver first and the whole notebook fails with
`System_Cancelled_Session_Statements_Failed`: an error that names no table and reads like a
Spark fault rather than a missing input. Hit on the 2026-08-19 deploy; the fix is one earlier
step, not a code change. The full order is in
[`build-status.md`](build-status.md#how-to-run-it).

**Related and still open: `cd_06_land_manual` is not in `CD_Master_Pipeline`.** The nightly
run rebuilds silver and gold without refreshing manual bronze first. Harmless while every
`man_*` is empty; a real staleness bug the day somebody enters a row. It should join the DAG
ahead of `Bronze To Silver` before the SharePoint lists go live.
