# PQP — the Project Quality Plan subject area

The client's QA/QC workbook is 44 sheets. This is what it became, why it became that shape,
and what is still blocked.

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

### What was actually broken (four things, not one)

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
offers the **union** of the three paths' vocabularies (15 codes rather than 6 / 7 / 5). The
alternative was three lists differing only in a dropdown, which is what the workbook had.
`test_sharepoint.py` asserts this deliberately, so it reads as a decision rather than a bug.

---

## Part 3 — where each thing comes from

The single most important design decision in this subject area. **Procore is the client's
mandatory system of record for quality — their own workbook says so.** So anything Procore
already owns is read from the API and is *not* a list to type into. A SharePoint NCR log
next to a Procore NCR log is two answers to "how many are open", and the workbook already
demonstrates which one wins: neither, because nobody trusts either.

| Source | What | Where |
|---|---|---|
| **Seed** (identical on every project) | 26 trades, 625 checklist items, 93 gates, 101 DOH requirements, 141 status codes | `sql/gold/08_qc_seeds.sql`, generated from `seed/*.csv` by `_local/make_qc_seeds.py` |
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
work needed no new endpoint for them, which is the registry paying off. Added:

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
- `expectations.py` — **63 → 103 expectations** (80 blocking, 23 warning).

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

4. **The Procore trade → `TradeKey` mapping is exact-match only.** `fct_QcNcr` /
   `fct_QcPunch` resolve `'Concrete Formwork'` → `CONCRETE_FORMWORK` and leave anything else
   NULL beside a `HasUnmappedTrade` flag, because a fuzzy match attaches an NCR to the wrong
   trade — worse than attaching it to none. Marked `ponytail:` in `33_fct_qc.sql`; the
   upgrade is a `qc_seed_TradeAlias` table, and the DQ warning is what tells you when the
   unmapped count is worth it. **This needs live data to size** — the fixture has one
   unmapped trade because it was constructed to.

5. **Procore Inspections may make `man_QcChecklistResult` redundant.** A Procore checklist
   list *is* a per-project instance of a checklist template, which is exactly what the 26
   trade sheets are. `checklist_lists` and `checklist_list_items` are in the registry and
   `cd_silver_qc_inspection` parses, landed deliberately so the comparison can be made
   against real data rather than argued about. **Nothing reads it in gold yet** — that is the
   next decision, and it is the client's to make once they can see both.

6. **No semantic model or report changes.** The 8 new `man_Qc*`, the 5 seeds and the 3
   `fct_Qc*` tables have no TMDL and appear on no page. `04-semantic_models/` and
   `05-reports/` are owned elsewhere; the gold tables are the contract they bind to, and the
   column names are final.

7. **`deploy_gold.py --source existing` no longer builds the QC or manual halves.** The
   existing warehouse holds none of it — this data was invented as part of this build. Rather
   than hand it empty views that pretend a source exists, `GOLD_CD_ONLY` skips those three
   files under `--source existing`, and `DEFAULT_SOURCE` is now `cd`, which is what has been
   in production since 2026-08-02. The gold SQL is still byte-identical across both sources;
   only the selection differs.

**Nothing has been deployed.** Every change is dry-run by default and the whole suite passes
offline.
