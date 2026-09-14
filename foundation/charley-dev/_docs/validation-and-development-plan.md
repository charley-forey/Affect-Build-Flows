# Validation and development assessment — 2026-09-10

**The solution is not yet certified as complete, current, or safe to publish without qualification.** The latest completed integrated candidate, `a09823bcf0bd4a59b2ac7f15e86f64ef`, executed 124 rules: 117 passed and seven warned, with zero blocking failures. The next candidate, `9835a75b9243452c97f53fc443c97d1c`, is running with the complete native item transformations, model link keys and 134-rule suite. All 17 local test suites pass. Published models and reports have not been replaced. Historical findings below retain their original scope; dated evidence records subsequent fixes and their verification limits.

**Latest source result:** the filtered inspection repair completed and independently reconciled 21 inspections and 563 unique items across the 20 discovered active-project scopes. Every returned item matched its requested project/inspection and every header item total reconciled. The verified route and runtime parent guard are deployed. The earlier full extraction still has unresolved endpoint/scope gaps; this targeted success does not certify all sources or historical coverage.

**Current report scope:** two local report definitions contain 21 pages. Native inspection headers and items now have local gold/model/report definitions, explicit limitations, and regression checks. Captured real data replay passes, but the latest item-level code still needs Spark execution, model generation from the resulting schema, live DAX/filter verification, and rendered review. Inspector assignments are preserved as JSON but their reader-facing presentation remains unfinished.

## Evidence and limits

- `validation-evidence.json`: read-only queries against both deployed semantic models, timestamped. Includes measure evaluation, table counts, financial identities, mapping gaps and candidate status logic.
- `runtime-evidence.json`: recent Fabric pipeline/notebook job results and the last persisted DQ diagnostic payload. No source credentials were read or recorded.
- `report-lineage.json`: generated visual-to-field bindings for both reports, every configured DAX measure and format, model relationships, and SQL producer locations. This is declared lineage, not proof of complete source extraction or correct business meaning.
- `_local/run_tests.py`: offline library, parser, transformation, model-contract, report-structure and failure-path checks. DuckDB compatibility is not a substitute for executing the release on Fabric Spark. Report JSON checks do not prove browser rendering, PDF layout, accessibility in a screen reader, or service permissions.

Azure MCP subscription discovery succeeded after earlier timeouts whose root cause remains unknown. Fabric Core MCP was connected directly through its documented remote protocol and returned 31 items in charley-dev. Notebook definition updates through MCP succeeded and were read back, including the manual-input safeguards and inspection-parent guard. This is an isolated protocol connection, not an installed Codex connector. OneLake file uploads, job execution and SQL reads still use their respective APIs; they are not described as MCP operations. Neither connectivity nor a successful deployment proves data correctness.

## Findings verified against the deployed solution

| Finding | Evidence | Consequence |
|---|---|---|
| Nightly ingestion is failing | Recent master-pipeline runs failed; September 9 includes `GatewayDataSourceOpenConnectionTimeout`, September 5–8 include Procore HTTP 429 | A configured schedule is not evidence that the report is current |
| Latest recorded DQ notebook completion is August 28 | Fabric job history and `dq_run.json` batch `20260828T064735Z` | No claim of a validated September refresh is justified |
| 37 invoices remain unattributed | Model query: unmatched invoice amount **$1,474,973.01** | These amounts cannot be assigned to a project by guessing; portfolio and project-filtered totals need explicit coverage information |
| Open Submittals includes RFIs | Displayed 2,211; independent row filters find 2,156 submittals and 55 RFIs | The label and calculation disagree |
| Models have different visible validation histories | Monthly model exposes 33 heartbeat rows, PQP 28; candidate status evaluates to `Unvalidated - data built after last check` in both | A common gold source does not prove synchronized published versions |
| Refresh time advances without a gold build | Monthly model's anchor says September 9; gold's last successful job is August 28. The independent seed stage rewrites the anchor | The displayed timestamp is not evidence of a successful data refresh |
| Financial identities reconcile | Invoice total minus paid minus outstanding is within one cent; budget minus spent minus variance is zero | Necessary consistency checks pass, but the invoice identity is partly constructed from the same inputs and is not independent proof against Sage line detail |
| Manual tables have no visible rows in the queries | DAX `COUNTROWS` returns BLANK for the manual registers | Missing input cannot be interpreted as no risk, no work, or completed compliance |
| Snapshot count assertions are stale | Five deployed counts increased against the validator's August baseline | Investigate growth; do not silently rebase it or let it prevent every later validation from running |

## Corrections made locally

1. Unexecuted DQ rules block the run even when their configured business severity is warning. Missing evidence writes and heartbeat writes also fail the gate. The generated DQ notification cell now compiles.
2. Empty/all-null freshness inputs fail the freshness check instead of passing via SQL NULL comparison.
3. Both reports' status expressions distinguish unknown, unvalidated, blocked, late, stale and checked-with-warning states. A recent heartbeat is no longer automatically labelled `Current`.
4. Open Submittals and its overdue counterpart filter the combined RFI/submittal fact to the correct item type.
5. PQP footer collisions and duplicate visual IDs are removed. Bookmarks cannot point to missing pages in another report. The PQP Data Quality page is visible. Tests build into a temporary directory so placeholder model IDs cannot overwrite deployable report bindings.
6. Historical landing replay is removed from the nightly DAG. It remains an explicit backfill operation; concurrent replay must not overwrite fresh API extraction.
7. Fabric Procore extraction uses the existing rate-limit session and uploads that dependency. Its wait allowance covers a full hourly window. This addresses the missing transport protection, but restoration is unproven until a successful live extraction completes.
8. A missing CSV preserves existing manual bronze tables. Storage errors propagate. CSV parsing fails on malformed typed data and header/schema mismatch rather than quietly converting it to missing values. A deliberately supplied CSV is still a replacement snapshot; an empty supplied file needs explicit operational handling.
9. Missing paid/balance values no longer become an invented invoice total or a fully paid flag. Missing gold accounting amounts block validation.
10. Conflicting project mappings no longer select an arbitrary largest identifier. They remain unresolved and flagged. Multiple Procore projects sharing one Sage job are a blocking fan-out condition.
11. Outbuild coverage reads the same owned silver activity source as milestones, instead of an older external activity feed. The remaining external lookup dependencies are explicitly named in the source-view file.
12. Added an integrated raw-fixture → silver → source-view → gold → model-column test, execution of the DQ SQL against that integrated schema, notebook compilation checks, both-report binding/layout checks and failure-path tests.
13. The seed stage now preserves the build timestamp. A successful gold build stamps it only after verification; first-time creation leaves it unknown. Regression tests cover seeding after a prior build and failed-build suppression.
14. Change-order status charts aggregate the change-order fact instead of repeating a financial-period balance. Coverage charts count all projects in each coverage category instead of excluding incomplete projects. Shared header collisions and overlapping notes are corrected, and all visual rectangles are checked for overlap.

The integrated test covers **47 owned-source views, 55 model table contracts and 117 executable gold DQ rules**. It preserves the external warehouse lookup fixtures explicitly. The full offline harness passed **all 17 suites** after the timestamp, complete-reject-retention and conflicting-merge-key corrections. This includes the new failure-path regressions; no live Spark execution is implied. Separate reference extractor, reference SQL pipeline and Power Automate suites passed 21/21, 13/13 and 21 checks respectively. Both reports pass the expanded geometry and field-binding checks: 19 pages, 276 visuals. Actual browser/PDF rendering remains unverified.

`mapping-review.json` records the ten unmatched Sage job IDs behind the 37 invoices and evaluates the candidate submittal and change-order expressions against live data. Some unmatched jobs may be legitimately outside the active-project reporting population; that needs an explicit scope decision, not an invented association.

## Required acceptance by stage

| Stage | Required proof | Current gap / next work |
|---|---|---|
| Source scope | Enumerate source endpoints, projects, date windows, permissions, inactive/deleted records and intentional exclusions | Active-project extraction is not the complete historical estate. Confirm the intended reporting population and preserve exclusions explicitly |
| Extraction | Every requested scope records succeeded / empty / denied / skipped / failed, request counts, pages, source totals where available and retrieval time | Endpoint success alone does not prove all pages or all projects. Restore Procore extraction and diagnose the Sage gateway timeout |
| Bronze | Immutable raw evidence or versioned snapshots, unique source keys, batch identity, replay/idempotency and deletion behavior | Current merges retain latest state; there is no demonstrated end-to-end historical snapshot guarantee |
| Silver | Accepted + rejected + intentionally excluded records reconcile to input; reasons and original record identity survive | Some parsers filter invalid keys or inner-join line records. Quantify every exclusion and orphan rather than relying only on gold row counts |
| Mapping | Validated keys, collision detection in both directions, unresolved amount/count, mapping owner and effective dates | 37 invoices remain unmatched. Three lookup views still depend on the existing warehouse: vendor crosswalk, project crosswalk, Sage vendor names |
| Gold | Grain/key uniqueness; count and amount conservation; valid dates/units; header-line reconciliation; credits and nulls | Extend independent Sage AR/AP line reconciliation and explicit exclusions. DOUBLE arithmetic needs a documented monetary tolerance or a coordinated decimal migration |
| Quality gate | All checks execute; results, rejects and heartbeat share a run; write errors block; rejects are queryable for that run | Local persistence now retains every failed row, with a regression case exceeding 1,000 rows. Fabric execution, volume and retention-policy verification remain outstanding |
| Semantic model | Every table/column resolves; relationship uniqueness and filter paths are correct; all measures tested at project, month and portfolio scope | Successful DAX evaluation is weaker than correct meaning. Test non-additive balances, cross-fact filters, empty inputs, current versus historical semantics and both models' refresh/version alignment |
| Report | Each visual has the intended grain, formula, units, formatting, source date and coverage; slicers/bookmarks/drill-through are correct | Browser and PDF verification of all 21 currently declared pages is outstanding. Static canvas checks cannot establish text legibility or cross-filter behavior |
| Publication | Readers see one validated release; failure leaves prior validated release visible; both models advance together | Gold is replaced before DQ and no verified atomic publication barrier exists. Explicitly prove Direct Lake update behavior and failure isolation |
| Operations | Read-only access verified, service identity and gateway healthy, deployment diff scoped, run monitoring and rollback tested | Access works; live extraction/publication recovery and MCP availability are not proven |

## Additional input-loss safeguards

- Removed the silent 1,000-row reject cap. Check counts can now be reconciled against complete persisted rejection details; the test retains all 1,507 fixture rows. This does not retroactively recover previously sampled evidence.
- Ingestion and backfill now collapse only exact duplicate rows. Different rows sharing a merge key block the affected write, including on first table creation. The SQL merge builder no longer arbitrarily selects one payload with ROW_NUMBER. Tests include nullable project keys and both new/existing target tables.
- This conservative policy also treats differing audit metadata as a conflict. It requires resolution rather than assuming which source version wins. Durable failed-source batch retention and an approved version-selection policy remain outstanding.

## Extraction completeness changes

The generated Fabric extractor now records batch-addressable scope evidence at `Files/_diag/ingestion/<batch>.json`, plus the latest diagnostic. Evidence includes the active-project population, each attempted path/project, received and written row counts, source scope outcomes, and whether the watermark advanced.

- A failed parent endpoint blocks its children; partially fetched records are not offered to children before the parent write succeeds.
- HTTP 403/404 means an unavailable scope, not proven absence of a licensed tool. Unavailable scopes are recorded and the final notebook verdict blocks downstream processing. Permission fixes or explicitly justified source exclusions must precede release; no exclusions are invented here.
- A partial-page failure cannot be accepted as a successful empty/disabled scope. Its received-row count survives in the diagnostic.
- Endpoint watermarks do not advance when any scope or ancestor scope is unavailable. Other endpoints may still land successfully before the notebook returns a failure.
- Tests execute the actual generated extraction and final-verdict cells for a complete pull, unavailable scope, partial-page failure, failed bronze merge, and unavailable parent. They verify child propagation, watermark behavior, and persisted diagnostics.

These changes are local and have not run on Fabric. The manifest is evidence of attempted extraction, not an upstream source-count reconciliation or proof that an interrupted notebook saved its final diagnostic. The subsequent archive change below adds decoded-record retention, subject to its stated limits. Those remain separate acceptance requirements.

## Silver source-read and verification safeguards

The generated silver notebook no longer substitutes an empty temporary view when a bronze read fails. It attempts every declared source, records missing/unreadable inputs in `silver_run.json`, and blocks before running any silver table replacement. First-run setup must provide real source tables; this check cannot be bypassed by treating absent data as an empty population.

Failed silver table-count reads now produce failed verification results and block the notebook. An all-empty result is described without guessing that credentials or extraction caused it. Regression tests execute the generated cells with a source permission failure and a silver count-read failure, and verify the saved diagnostics.

These safeguards do not provide atomic multi-table publication. A source that becomes unavailable after preflight or a transformation failure can still leave partially replaced silver tables. Sage line tables now retain unmatched lines; the additional reconciliation checks below block unresolved detail. Live execution and source exception review remain outstanding.

## Sage invoice-detail reconciliation

AR and AP line transformations now use left joins to headers, preserving orphan detail with unresolved header fields. Twelve additional blocking silver predicates check header and line key validity/uniqueness, orphan lines, bronze-to-silver row conservation for headers and lines, and per-invoice header-versus-line amounts. These are additional to the 117 gold checks. Their SQL and violation counts are recorded in the silver diagnostic; an unexecutable rule fails the run.

The amount check uses an explicit one-cent per-invoice tolerance. Missing line detail, unknown header amounts, or any unknown line amount fail instead of being treated as zero. Credit amounts can reconcile normally. Source-specific tax, adjustment, rounding or no-detail exceptions must be established from evidence before any exception is added; none is presumed here.

The local silver tests include preserved AR/AP orphan lines, unknown money, lost rows, duplicate keys, valid credits, and offsetting invoice errors whose portfolio sum still matches. The integrated input-to-model test passes. These tests establish behavior on controlled fixtures, not that the deployed Sage population passes the new rules. Historic aggregate agreement is not a substitute for this per-invoice live reconciliation.

## Live Sage reconciliation evidence

`_docs/sage-reconciliation-evidence.json` now contains direct read-only Fabric SQL results, query text and timestamps. `_local/validate_sage_live.ps1` runs the shared twelve silver rules plus eight bronze reconciliation and source-to-silver diagnostic queries and exits unsuccessfully when any rule returns violations or cannot execute.

- All 20 live queries executed successfully: 16 passed and four identified the same AP propagation gap. AR keys, header/line row conservation, orphan checks and per-invoice amount reconciliation pass for the currently visible data. Both AR and AP bronze invoice amounts independently reconcile against their bronze line totals, including the four AP invoices absent from silver.
- AP silver's existing headers reconcile to their existing lines, but bronze has **879 headers / 909 lines** versus silver's **875 headers / 905 lines**.
- Four AP invoices, IDs **876–879**, totaling **$6,997.56**, exist in bronze but are absent from silver. They are recorded fully paid and have no Sage job association. Their source update dates run from August 28 through September 9.
- Their four lines link to actual bronze headers: this is a bronze-to-silver coverage gap, not proof of missing source headers. The dates are consistent with the previously observed stalled transformation, but do not independently prove its cause.
- This establishes a concrete incomplete stage even though the subset already in silver reconciles. It does not certify upstream Sage extraction completeness, SQL endpoint synchronization, or the final reports.

No notebooks, tables, models or reports were changed by these live queries. The stage mismatch remains unresolved pending a controlled transformation run with the new checks and the required publication isolation.

## Invoice traceability and report coverage

The owned AR source view and gold invoice fact now preserve `InvoiceKey`, `InvoiceID` and `InvoiceNumber`. The model column contract includes them, and the Data Quality table shows invoice ID/number, Sage job, mapping status and billed amount. Two additional blocking gold checks require a non-null unique invoice key (117 gold rules total). The legacy warehouse view explicitly returns unknown identity because its existing contract does not establish those fields; it must not pass invoice traceability certification until an authoritative identity is supplied.

The Monthly Data Quality page is visible. Its unmatched AR count and amount ignore the project selector while retaining the month filter; the page explains that scope and that its other visuals remain project-filtered. This prevents a mapped-project selection from hiding the unattributed monetary exposure in the headline checks.

`data-quality-ui-candidates.json` records live evaluation of the candidate DAX expressions without deployment: both portfolio and selected-project contexts return 37 unmatched invoices and $1,474,973.01. The full 17-suite offline harness passes; an additional integration assertion verifies invoice identifiers survive from Sage bronze to gold. The generated lineage inventory covers 19 pages and 276 visuals. Runtime report rendering and month-filter interaction still require verification after controlled deployment.

## Business definitions that must remain explicit

- Paid date is unavailable in the current invoice fact. Due date is not payment date; days-to-payment and its score must remain unmeasured until supported.
- “Critical” RFI/submittal is not a confirmed rule. Preserve unknown rather than infer it from words or priority names.
- Outbuild baseline dates are landed, but a maintained baseline is not yet established. Do not sell current-versus-imported dates as verified schedule variance.
- Current status grouped by creation month is not a historical month-end snapshot. Past-due/open counts can change when a record closes. Historical reporting requires event history or saved monthly snapshots.
  - Saved snapshots are built and tested offline but not deployed. `cd_40_dq_checks` appends `fct_DailySnapshot` (`02-transformation/sql/snapshot/fct_dailysnapshot.sql`) in the cell after `assert_no_blocking`, so only passing runs write history. It stores one row-set per ProjectKey per UTC run date, and a re-run on the same date replaces that date's rows. After capture, three rules run: the key must be unique, values must equal the live facts, and the RunId must belong to a passing run. If any rule fails, that run's rows are deleted and the run fails. The `(Month End)` measures take the last capture in the selected month. They are BLANK before the first capture, and nothing is backfilled. The Schedule & Quality page states where history starts. Deploying this and the first live capture are still to do.
- Approved/rejected/void/closed change-order semantics require source-specific confirmation; “not pending” must not become a proxy for financially approved without evidence.
- A trade alias needs an approved mapping. Missing aliases, multiple system links and excluded schedule activities must remain visible.
- Expired certificates on file establish the state of the recorded documents, not that a subcontractor is uninsured.
- Empty manual registers and missing scorecard categories are missing coverage. A measured-only score is conditional on the available categories and does not make differently covered projects automatically comparable.

## User experience and useful capabilities

Prioritize visibility of evidence over additional headline metrics:

1. Put source freshness and coverage beside each affected financial, schedule and quality metric. Show “unknown”, “not connected”, “no records received” and measured zero as separate states.
2. Add a measure explanation showing definition, grain, period interpretation, source, formula, exclusions, validation run and last successful source pull. `report-lineage.json` supplies the technical inventory; business definitions still require review.
3. Add an unresolved-record worklist grouped by source job/project/trade, with counts and monetary impact. Suggested mappings may be reviewed, but never auto-accepted on name similarity.
4. Separate invoice billing, progress applications, committed cost and actual spend. Show a reconciliation bridge instead of presenting different grains as competing totals.
5. Show full versus measured-only score with category coverage and missing drivers. Avoid a green “healthy” status for an unmeasured category.
6. Add validated month-end snapshots and variance explanations before predictive insights. A forecast needs demonstrated historical accuracy and explicit uncertainty.
7. After data coverage is proven, add baseline schedule variance, cash collection aging, approval-cycle bottlenecks, vendor exposure and quality recurrence by confirmed trade. Each needs its own denominator, scope, evidence and acceptance tests.

## Release sequence and proof still needed

1. Complete the offline suites after the final changes; preserve the output and revision/diff identity.
2. Generate and review the notebook, model and report artifacts. Do not use placeholder model IDs or overwrite unrelated Fabric items. Preserve the existing workspace outside `charley-dev`.
3. Capture deployed definitions and lakehouse versions before applying the release. Verify item folder IDs and the service identity actually used by the scheduled jobs.
4. Restore source ingestion. A retry policy does not repair an unhealthy gateway; inspect gateway/SQL connectivity and a subsequent successful Sage job. Record endpoint-level Procore coverage after quota handling.
5. Run the changed code on Fabric with a controlled dataset, including malformed input, unavailable storage, ambiguous keys, duplicates, partial extraction, and DQ-write failure. Verify that no invalid release becomes reader-visible.
6. Establish publication isolation, then refresh/reframe both models only after validation. Test rollback and failure interruption between every stage.
7. Reconcile live source → bronze → silver → gold → DAX at project/month and portfolio grain. Keep unlinked records and unresolved business definitions visible.
8. Verify all pages interactively and in export, including empty, partial and stale cases, currency/percentage formats, keyboard access, slicer synchronization and drill-through context.

Microsoft documents that Direct Lake can update automatically; therefore a notebook failure alone is not proof that readers retain the prior validated release: [How Direct Lake works](https://learn.microsoft.com/en-us/fabric/fundamentals/direct-lake-how-it-works). The missing-CSV check uses the documented [NotebookUtils filesystem API](https://learn.microsoft.com/en-us/fabric/data-engineering/notebookutils/notebookutils-file-system).

**Completion remains unproven** until the outstanding stage-level, business-definition, live-runtime and rendered-report evidence exists. The current improvements are a concrete step toward that objective, not a smaller substitute for it.

## Publication boundary investigation

`publication-evidence.json` records `EVALUATE TABLETRAITS()` against both deployed models. All 37 Monthly model tables and all 20 PQP tables report DirectLake storage; fallback information is null. This establishes the reported storage mode at capture time, not the automatic-update setting, a guaranteed absence of future fallback, or a validated release boundary.

Microsoft documents that automatic updates are enabled by default and can reframe modified tables individually. Disabling them permits an explicit refresh after preparation finishes; SQL-endpoint DirectQuery fallback can nevertheless read the latest data outside that frame. See [How Direct Lake works](https://learn.microsoft.com/en-us/fabric/fundamentals/direct-lake-how-it-works).

The portal inspection reached the Power BI sign-in page. No automatic-update setting was read or changed. The next acceptance experiment is:

1. Inspect and record automatic-update, scheduled-refresh and fallback settings for each actual model. Do not infer settings from TMDL omissions or an old refresh timestamp.
2. In an isolated validation model, retain a known validated frame; change its source to a deliberately failing candidate. Prove queries remain on the validated frame before and after the gate failure, including queries after cache eviction.
3. After a passing gate, refresh explicitly and verify the same release identifier in both models. Separate refresh operations are not an atomic two-model commit; record and handle a one-model failure explicitly.
4. Repeat with a missing table, permission failure, model refresh failure and overlapping pipeline run. Verify recovery without exposing a mixed release.
5. Only after this evidence exists should the controlled process replace the current in-place publication flow.

Generator comments and gate messages no longer claim that Direct Lake needs no refresh or that passing DQ alone makes publication safe. The publication-control implementation and live failure-isolation experiment remain outstanding.

## Received-payload preservation

The generated Procore extractor now creates an exclusive JSONL archive per endpoint under `Files/_diag/ingestion/<batch>/<endpoint>.jsonl`. It records the decoded source record and request scope before project normalization or bronze merging. Archives must close successfully before a merge or watermark write; existing archives and batch manifests are never overwritten. The batch diagnostic identifies the archive path, received/archived/written counts and whether archival completed.

The generated-cell tests verify that partial-page and merge failures retain received records, unavailable archive storage blocks writes and watermarks, successful captures preserve the original decoded record before normalization, and replay with the same batch cannot replace an earlier archive. The targeted validation suite and compilation of 67 generated notebook code cells pass.

This is decoded-record capture, not original HTTP response bytes or a guarantee that every source record was fetched. An abrupt host/storage failure may leave an incomplete file; the archive-complete marker must be checked. Retention policy, access review, storage sizing, deletion-event semantics and a controlled replay procedure still need operational validation. The new archive behavior has not been deployed or exercised on Fabric's mounted filesystem.

## Incremental parent/child completeness

The Procore registry configures `prime_contracts` with an updated-at filter, while prime-contract line items and payment applications derive their request scopes from that pull. Filtering parent discovery to changed contracts can omit changed/new children of an unchanged contract; there is no established source guarantee that every child change updates the parent timestamp.

The generated extractor now performs a full parent-discovery pull for every endpoint used by another endpoint as a parent. Children retain their own supported incremental filters. The batch manifest records `full_parent_discovery` and the effective watermark so the broader pull is inspectable. Current parent endpoints have no configured date window that would independently truncate discovery.

The generated-cell regression simulates an unchanged parent and new child data. Both are fetched and written, while the child's previous watermark is preserved in its request parameters. The targeted validation suite and 67 generated-code compilation checks pass. This increases parent API traffic and archive volume; live rate-limit behavior remains to be validated. The active-project-only scope and source deletion handling are unchanged outstanding coverage limitations.

## Isolated Fabric Spark candidate run

A validation-only notebook, `cd_91_validate_sage`, has been created inside `charley-dev`. It reads the five existing Sage bronze Delta tables, evaluates the revised silver SQL as temporary views, and runs the twelve Sage reconciliation predicates. It does not write persistent data tables or refresh semantic models. The notebook writes a uniquely named diagnostic containing source-SQL hash, query text, full violation rows and source/candidate counts.

`_local/validate_sage_spark.py --status` polls the saved job handle in `sage-spark-job.json`; it does not start another run. Starting another run is refused while the saved job is active. This validates Spark query semantics against current bronze data, not persistent Delta write behavior, source completeness or report publication isolation. The latest recorded job state is authoritative; success must not be inferred from notebook creation or compilation.

The first isolated Spark run completed successfully on September 10, 2026 (job `c1e7864c-d694-47d8-95eb-7c244077df65`). All twelve reconciliation checks passed, and the stored source-SQL hash matches the current transformation file. Candidate AP contains all 879 bronze headers and 909 lines, including the four headers/lines absent from published silver. Candidate AR preserves 148 headers and 258 lines. Full evidence is in `sage-spark-evidence.json`. Published silver/gold data and reports remain unchanged; the AP gap is resolved in the evaluated candidate, not yet in the deployed tables.

## Full gold candidate on Fabric

`CD_Validation_Lakehouse` (ID `0c26a970-705b-44c2-8366-9101cd6f4e7f`) and `cd_92_validate_gold` were created inside `charley-dev` for isolated validation. The notebook composes the existing seed and gold builders, writes actual Delta tables only in that lakehouse, and evaluates all 117 gold rules with results/reject persistence enabled. Published silver sources and the three external lookups are read-only inputs. No published model/report is rebound or refreshed.

The runner rejects a published lakehouse ID or a target outside `charley-dev`. The saved job handle is `gold-spark-job.json`; `validate_sage_spark.py --gold --status` polls that run without starting a replacement. Target-isolation tests pass, and 110 generated Python cells compile across nine notebook builds. Runtime success remains unproven until the terminal job state and its diagnostic results are inspected. This run uses currently published silver, so it does not repair its known AP freshness gap or establish end-to-end source freshness.

The full local 17-suite harness passed after adding the candidate runner and isolation checks. The first full-gold candidate job (`eb0a05b0-b61a-4aff-a030-3028e07e9895`) completed on September 10, 2026 at 07:06:44 UTC. Retrieved diagnostics confirm successful seed counts and all gold build steps, with no build-verification findings. The gold candidate contains 19 projects, 148 AR invoices, 327 change orders and 2,905 combined RFI/submittal records. These counts describe the candidate; they do not establish completeness against upstream systems.

All 117 quality rules executed: 110 passed, seven produced warnings, and none blocked. Evidence is preserved in `gold-spark-evidence.json`, `candidate-seed_run.json`, `candidate-gold_run.json` and `candidate-gold_schema.json`.

| Warning rule | Failing rows |
| --- | ---: |
| Every project is in Sage | 4 |
| Every project is in Outbuild | 16 |
| Cumulative billing never exceeds the current contract | 2 |
| Retainage released rather than withheld | 6 |
| Vendors on a project have a certificate on file | 394 |
| Certificates on file are in date | 105 |
| Procore trades resolve to a seeded trade | 221 |

Failing-row counts are specific to each rule's grain; they must not be summed as a count of distinct projects, vendors or incidents. Warnings require record-level review before interpreting them as business exceptions. For example, absence from the available certificate data does not establish that a vendor has no insurance, and stale source data may affect expiration findings.

This is verified Fabric execution of isolated seed/gold writes and quality checks against existing silver data. It does not certify upstream freshness, deploy the repaired silver transformations, validate report rendering, establish a safe publication boundary, or demonstrate deployment through Fabric/Azure MCP. The published AP propagation gap and the remaining stage-level acceptance criteria above remain open.

## Full silver candidate on Fabric

The validation runner now accepts `--silver`, composing the unchanged production silver notebook builder and attaching it to `CD_Validation_Lakehouse`. Notebook `cd_93_validate_silver` reads existing bronze tables and writes the candidate silver tables in that isolated lakehouse. It exercises persistent Delta writes, all configured parsers, table counts, and the twelve Sage reconciliation predicates. The generated-code and isolation checks pass (123 Python cells across ten notebook builds).

Job `d429b79e-8317-48d3-9841-b612ff9c0519` started at 07:11:47 UTC on September 10, 2026. The first API poll confirmed `InProgress`. Its definition hash and authoritative handle are saved in `silver-spark-job.json`; poll with `validate_sage_spark.py --silver --status`. Do not infer success until terminal status and `silver_run.json` are inspected. On success, the uniquely named candidate diagnostic also records the run identity and full transformation results.

Code inspection confirms that the core `cd_dq_rejects` table currently records missing IDs for only projects, vendors, submittals and RFIs. Cost-code, contract and change-order key rejections are not represented there. Budget parsing also filters rows without the configured view signature and selects one row per project/cost-code by ingestion time; excluded and superseded rows are not accounted for in that ledger, and equal-time conflicting rows have no proven resolution. These are outstanding record-accounting and grain-validation gaps even if the current runtime completes. Separate QC reject handling does not close those core-parser gaps.

The subsequent local fix adds cost-code, prime-contract and prime-change-order missing-ID records to the same reject ledger, retaining payload and batch ID. A regression injects a missing-ID record into each of the seven core ID-filtered inputs, executes the actual SQL, and proves source count equals accepted plus rejected count for each target and that the rejected payload survives unchanged. All 67 silver checks pass, as does the end-to-end contract suite (47 source views, 55 model table contracts, 117 gold rules). This is fixture evidence for these seven paths, not a completeness claim for every parser or field. The active silver Fabric job was submitted before this fix and cannot validate it; its saved definition hash identifies that earlier snapshot. Budget exclusions, tie handling and other parser reject paths remain open.

## Confirmed live budget grain defect

A read-only SQL-endpoint capture at 07:18:14 UTC on September 10, 2026 retrieved all 480 visible budget bronze records (`budget-bronze-evidence.json`). Contrary to the old SQL comments, every current record has the configured CM signature. There are 404 distinct project/source-key pairs, with 76 extra duplicate records and no differing raw payloads within a repeated source key. Reducing these to project/cost-code produces 402 groups: two groups contain distinct source lines with different categories. The evidence and decimal totals are summarized in `budget-grain-summary.json`.

- Project `562949954973730`, cost code `562950355920640`: Labor line `562949970796244` has updated budget $26,685.63; Hard Costs line `562949971817381` has $3,780.13 and $2,031.62 invoiced. Both are real distinct source lines. Selecting one loses the other.
- Project `562949955286476`, cost code `562950458358764`: Subcontract line `562949972796645` has $33,960.74 updated budget and $57,449.00 invoiced; Material line `562949973755776` has zero amounts. Both should remain identifiable.

The 404 distinct source lines total $30,209,672.18 original budget, $34,031,395.20 updated budget and $19,160,549.83 invoiced. These are totals over captured bronze records, not certified upstream balances. The current transformation's project/cost-code ROW_NUMBER selection is a confirmed implementation defect, not merely a hypothetical tie risk. Repair must preserve source budget-line identity through silver and gold, remove only proven duplicates, reject conflicting versions rather than choose arbitrarily, and test category preservation and amount reconciliation. The fact's historical-snapshot claim also exceeds the current retained data and must be corrected until snapshot capture is implemented and validated.

The local repair now carries `budget_line_id` from the bronze source key through the owned source view to gold `BudgetLineID` and the Monthly model column declaration. The parser retains distinct projected records instead of selecting one cost-code row. Two blocking gold rules require a non-null source-line ID and uniqueness within project; conflicting projected versions remain present and fail that rule. The legacy source view explicitly returns an unknown ID rather than inventing one. Gold comments now describe current-state ingestion dates without claiming validated month-end history.

The regression exercises separate categories sharing a cost code, identical duplicate copies, and a conflicting same-ID record through actual silver and gold SQL. It verifies preserved IDs/categories, conserved updated-budget amounts, and blocking conflict detection. The integrated contract suite executes 119 gold rules. Running revised silver SQL locally against all 480 captured live inputs produces 404 lines and matches the three decimal source totals within $0.001, with no conflicting keys (`budget-candidate-evidence.json`). This is DuckDB evidence against live-captured data, not execution of the revised code in Fabric. Amounts remain DOUBLE in the existing schema; the stored evidence shows floating-point representation and does not claim exact decimal storage.

The earlier full silver Fabric candidate completed at 07:19:21 UTC with 65 successful diagnostic steps, counts for all 47 silver tables, and all twelve Sage reconciliation rules passing (`silver-spark-evidence.json`). AP has 879 headers/909 lines and AR has 148 headers/258 lines. That earlier snapshot still produces 402 budget rows and lacks the subsequently added three reject paths. A new isolated run is required for the latest code; published silver, gold and semantic models have not been updated.

## Integrated revised candidate run

The `--full` validation mode now executes the actual silver builder, seeds, gold builder and 119-rule gold suite sequentially in `CD_Validation_Lakehouse`. Gold's owned-source paths point to the silver tables produced in that same validation lakehouse; the three external lookup inputs remain explicit external dependencies. Offline assertions check that the published silver path is absent from the combined notebook, its initial cells are the same silver candidate code, and its default write lakehouse is the isolated target. Generated-code checks pass for 176 Python cells across eleven notebook builds. The runner checks all known isolated validation handles before starting another job, refusing if any remain active.

Notebook `cd_94_validate_full` (`77fe4969-f886-47c1-b1fa-750f5bebc2df`) started job `456e992b-9ef8-4e12-a04d-9157d1726b1b` on September 10, 2026 at 07:25:47 UTC. The API confirms `InProgress`; no runtime pass is yet claimed. Run ID, definition hash and job URL are saved in `full-spark-job.json`. Poll the same handle with `validate_sage_spark.py --full --status`. Terminal diagnostics use `full-spark-evidence.json` and `full-candidate-*` names so the earlier separate-stage evidence is preserved. This run includes the budget source-line repair and expanded core reject ledger. Upstream ingestion, semantic-model refresh, dashboard rendering and reader isolation are outside this run and remain unverified.

Budget rows excluded by the project/signature filter are now retained locally in `cd_dq_rejects`, with their original payload, batch ID and distinct reasons for missing project, missing CM signature, or both. The regression covers all three cases, proves accepted-plus-rejected conservation for these inputs, and verifies that a row failing both predicates is recorded once. All 68 silver checks and the integrated 119-rule contract test pass. Exact duplicate accepted rows remain intentionally collapsed as described above; this reject check does not count those copies or certify all parser paths. This ledger addition postdates the running combined notebook definition and has not yet been exercised in Fabric.

## Semantic-model validation preparation

The shared model generator previously accepted a lakehouse ID for its connection expression but always fetched schema metadata from the published gold lakehouse. That could produce a validation model whose declared columns/types did not describe its actual source. `write_files` now passes its target lakehouse ID to schema introspection. Optional output-directory and display-name arguments let the same generator emit reviewable validation definitions without replacing the published definition files. Defaults preserve the existing deployment path, and the PQP generator reuses the same shared functions.

The focused regression verifies that the supplied lakehouse ID reaches schema inspection and the connection expression, the requested display name appears in metadata, and every generated file is written to the specified temporary directory. The validation suite passes. No candidate semantic model has yet been created or queried; live DAX reconciliation and report rendering remain outstanding after the integrated Spark result is inspected.

## Additional Procore reject coverage

The core reject ledger now also retains filtered inputs from observations, punch items, incidents, requisitions, payment applications, direct costs, direct-cost lines, inspections, both commitment-header endpoints, both commitment-line endpoints, manpower logs, project vendors and company insurance. Reasons match the existing parser predicates: missing ID, missing date, missing project, missing vendor ID, or combined missing fields. Unioned source endpoints are identified in the missing-ID reason to distinguish billing and commitment inputs. Original payload and batch ID remain intact.

The regression injects an invalid input into each of these fifteen source paths, executes the real silver SQL, and checks that its original payload appears once with a missing-field reason and original batch ID. All 69 silver checks and the end-to-end contract suite pass. These additions postdate the active Fabric notebook and require a later runtime validation. This closes the inspected raw-input filter omissions, not all downstream exclusions: QC derived tables still filter records without a project, typed-field validity and record-level association checks need broader coverage, and aggregates require reconciliation at their own grain.

The combined run's unique silver-stage diagnostic has now been retrieved as `full-candidate-silver-evidence.json`. Its run ID matches `85055bed31d24f9695b5fdad26bb936f`; all diagnostic steps passed and all 47 silver table counts completed. Fabric produced 404 budget lines, confirming the corrected source-line grain at runtime. Its submitted reject ledger reported zero rows, which does not cover the later ledger additions. The full job still reports `InProgress`; silver success alone does not establish gold/DQ success or semantic-model correctness.

The live model validator no longer uses historical hardcoded table counts or the incorrect assertion that reducing 404 budget lines to 402 was legitimate deduplication. It reads expected counts from the target lakehouse's successful gold/seed diagnostics and refuses missing, failed or inconsistent evidence. The focused test verifies target selection, changing budget counts and failed-evidence rejection. Measure evaluation now enumerates the full model measure definition list instead of a hand-maintained subset of 26. The local validation suite passes; these revised live checks have not yet been run against a candidate model. Diagnostics still lack a unified release ID, so this is model-to-build count reconciliation, not proof of an atomic release or complete upstream ingestion.

## First-build heartbeat schema defect

The revised gold schema is now available in the isolated lakehouse and includes `BudgetLineID`. Attempting to generate a candidate Monthly model correctly stopped because `meta_PipelineRun` was absent from that schema; no model was deployed. Gold records schemas before the DQ gate creates the runtime heartbeat table, and the candidate DQ wrapper had evaluated/persisted checks without writing the production heartbeat at all.

The local fix moves heartbeat persistence into the shared DQ library and calls it from both the production DQ notebook and the candidate wrapper. After appending the evaluated status, it reads the runtime table's actual Spark schema and updates `gold_schema.json`, preserving the existing table schemas. It does not invent missing column types or require a second full gold run merely to discover the heartbeat. Persistence/schema-publication errors propagate. A regression verifies blocked status for an unexecuted warning, append behavior, actual-schema publication and preservation of prior schema entries; the validation suite passes. The running notebook predates this fix, so its completion alone will not prove the corrected heartbeat path or make the candidate model ready.

## Integrated run failure and correction

Job `456e992b-9ef8-4e12-a04d-9157d1726b1b` failed at 07:45:18 UTC. Seeds, all silver transformations and gold build verification succeeded; the gold candidate contains 20 projects, 404 budget lines, 330 change orders, 148 invoices and 3,125 combined RFI/submittal records. The changed counts compared with published gold must be reconciled at record level, not attributed to source completeness without evidence.

The driver stdout traceback identifies a Delta schema mismatch in `_persist_rejects`: the existing table had silver's `target_table/reason/payload/_batch_id` schema, while gold DQ tried to append `_dq_expectation/_dq_reason/_batch_id/_row`. Production separates these ledgers by lakehouse; the combined validation target had accidentally co-located them under `cd_dq_rejects`. This is a validation-runner defect. No complete 119-rule result is claimed because persistence interrupted evaluation and the final diagnostic was absent.

The candidate now writes gold quality rejects to `cd_validation_gold_rejects`, leaving the silver ledger intact. It evaluates all rules without persistence, writes the unique evaluation diagnostic, then persists results/rejects and the shared heartbeat. A fault-injection regression proves the evaluation survives a persistence error and the error still propagates. The validation suite passes. Failed-run artifacts and logs are preserved under `validation-history/85055bed31d24f9695b5fdad26bb936f/`; a corrected full run is being submitted with the latest reject-ledger and heartbeat fixes. Check `full-spark-job.json` for the new authoritative handle rather than reusing the failed job's state.

The corrected job is `cab25d32-03c2-443a-ae26-36c102443354`, started at 07:53:34 UTC on September 10, 2026. Its first status poll confirms `InProgress` with no failure reason; the prior failure has not been treated as a pass.

## Budget trace in the financial report

The financial matrix definition now expands from division/cost code through category, project ID and `BudgetLineID`. Users can inspect distinct source lines instead of seeing only a combined cost-code amount. The title and accessibility text explain the expanded detail. Project ID remains part of the trace because the validated line key is scoped to project; source-line ID alone is not assumed globally unique. The report suite passes for 12 pages, 181 visuals and 146 valid field references, and the declared lineage inventory has been regenerated. This is definition/layout validation, not proof of rendered matrix expansion or correct live filtering. Power BI remains at its sign-in page, so interactive and export verification are still pending. No report has been deployed by this change.

## Explaining the additional project

A read-only bronze-to-published-silver anti-join found one project absent from published silver: `562949955455437`, **360 Lexington 15th Floor Fitout**, active in the payload, ingested September 10, 2026 at 06:11:32 UTC under batch `20260910T061113-68bc9642`. The full query, timestamp and row are in `project-propagation-evidence.json`. This explains the candidate's twentieth project as a real available bronze record. It does not prove that every upstream project was fetched or identify the cause of every other changed fact count.

The bronze `Files/_diag/ingest_run.json` currently contains a sandbox OAuth 401 with missing-secret flags. A separate OneLake HEAD request shows that diagnostic was last modified **August 25, 2026 at 01:36:14 UTC**, so it is stale relative to the September 10 bronze batch and cannot establish the latest ingestion outcome. Captured content and file metadata are in `latest-ingestion-evidence.json` and `latest-ingestion-evidence-metadata.json`; “latest” here denotes the current retrieved file, not a verified current batch. A run-linked ingestion manifest or authoritative job history is still needed for the September 10 batch. Source record timestamps and a stale mutable diagnostic must not be combined into a claim that the current ingestion passed or failed.

Authoritative job history and driver stdout now resolve this uncertainty. `CD_Sage_Ingest` job `27888c53-3654-4606-8052-ada28827a09e` completed September 10 at 06:04:13 UTC. This supersedes the September 9 failure as the latest observed refresh outcome; it does not prove permanent gateway reliability or source-row completeness. Procore job `5dbfd2bd-58bd-4343-817a-b2fb5d7e366a` ran 06:10:30–06:25:44 UTC and its stdout identifies **batch `20260910T061113-68bc9642`**, exactly matching the new project's bronze record. It failed on 13 of 44 endpoints with HTTP 429 responses: incidents, incident injuries/near misses/severity levels, manpower daily totals/logs, daily log headers, schedule, prime-contract lines, payment applications, work-order lines, purchase-order lines and budget detail rows. Retry job `ee44157a-50d3-4544-9ae3-9c36d1bb60ac` also failed with HTTP 429 while fetching the active-project list.

Evidence is in `ingestion-job-history.json`, `procore-september10-sessions.json` and the two `procore-<job-id>-stdout.txt` files. September 10 bronze is therefore partially refreshed, not a certified complete extraction. A passing downstream candidate built from it cannot establish complete source coverage. The local rate-limit-aware extractor and scope/manifest fixes still require controlled deployment and runtime validation; the stale August 25 OAuth diagnostic is not the current failure's root cause.

## Procore repair deployed, extraction not yet run

The deployed notebook definition was retrieved and confirmed to lack `RateLimitedSession`. The repaired wrapper's six quota tests pass. Before deployment, both the bronze lakehouse and notebook folder IDs were verified as `charley-dev`, and returned ingestion job history showed no active job. The original notebook definition is saved in `procore-definition-before-validation.json`; all six previous library/config file states are backed up under `ingestion-before-deployment/` with presence flags and hashes.

`deploy_ingestion.py --apply` uploaded the six dependencies/config files and updated `cd_01_extract_procore`. Read-back proves each uploaded file matches the local bytes and the notebook contains rate-limit handling, full parent discovery and raw-archive completion tracking (`ingestion-deployment-evidence.json`, `procore-definition-after-validation.json`). This was performed using Fabric REST/OneLake, not Fabric MCP; MCP deployment remains unproven. The notebook was not executed by this deployment. Runtime quota handling, secret resolution, complete endpoint coverage and resulting source-to-report reconciliation still require validation. Starting extraction is deferred until the active isolated run has finished reading bronze, to avoid changing its input mid-stage.

The corrected combined run's unique silver diagnostic now confirms successful completion for run `78ea309feb6047cabfc7cf58f7521997`, including 404 budget lines. Its remaining gold/DQ work consumes isolated silver tables. After this boundary and a fresh check that no Procore notebook job was active, the repaired extractor was submitted. Job `f310bd55-4b1f-4418-b3d5-b3153fe22978` was accepted at 08:08:53 UTC on September 10, 2026; the first poll reports `NotStarted`, not completed or failed. Its authoritative handle is in `procore-repair-job.json`. Poll that handle; do not resubmit because it is queued or waiting on quota. This extraction does not trigger a model refresh or certify the previously captured downstream candidate against newly arriving inputs. A subsequent reconciliation is required after extraction completes.

## Integrated candidate and semantic validation completed — September 10

Fabric job `cab25d32-03c2-443a-ae26-36c102443354` completed at **08:11:23 UTC** for run `78ea309feb6047cabfc7cf58f7521997`. All **119** quality rules executed: **112 passed, seven warned, zero blocked**. Evidence: `full-spark-job.json`, `full-spark-evidence.json`, and `full-candidate-*` diagnostics. The heartbeat schema was published successfully. This candidate consumed the existing partially refreshed bronze; it cannot certify the repaired extraction subsequently started against the source APIs.

The warning rule counts are: five projects missing Sage coverage; 17 missing Outbuild coverage; two cumulative billings exceeding current contract; six retainage-release cases; 405 project/vendor certificate coverage findings; 105 expired certificates; and 236 unresolved trade findings. These are counts at each rule's grain, not unique entities across the entire report. They remain visible findings, not silently waived business approvals.

Two isolated models were deployed in `charley-dev`, both bound to the validation lakehouse:

| Candidate | Model ID | Measures evaluated | Model-to-build count comparisons |
|---|---|---:|---:|
| CD_Validation_Monthly | 93a87eef-e5fa-4626-bd32-ca61233a351d | 103 | 26 |
| CD_Validation_PQP | See `candidate-model-qc.json` | 42 | 10 |

All measures evaluated without errors at portfolio, project and month scope. Both models were refreshed before querying. `candidate-monthly-dax-evidence.json` and `candidate-qc-dax-evidence.json` retain the actual query results, including NULLs, and identify tables without independent build-count comparisons. Monthly has nine manual tables plus heartbeat without such a comparison; PQP has eight manual tables plus heartbeat. Queryability is verified for these tables, but full count reconciliation is not claimed. The project/month grouped results include the blank/unassigned member; it must not be relabelled as an additional real project or silently removed to make totals look cleaner.

`candidate-reconciliation.json` records **17 passing comparisons**: additive project/month totals agree with portfolio totals for budget, spent, variance, billed, paid, AR outstanding and open submittals; current contract reconciles across projects only; budget **$34,031,395.20** and spent **$19,160,549.83** match the captured distinct bronze budget lines within one cent. Current contract is not summed across months. These checks establish agreement at the tested grains, not approved business meaning for every measure.

Repeatable candidate checks are now available through `_local/validate_candidate_model.py --check` and `--qc --check`. They refuse a mismatched build/model definition or an incomplete/blocked Fabric run, retain query errors, preserve unknown values, compare available build counts, and explicitly list unpaired table counts. Regression tests cover incomplete quality evidence, failed month-level calculations, missing/mismatched counts and NULL preservation. The full offline harness again passed **all 17 suites**.

The latest repaired Procore job status is **InProgress**. No complete extraction claim is justified yet. Published report/model definitions remain unchanged by these candidate deployments. Fabric REST/OneLake was used; Fabric/Azure MCP deployment is still unverified. Browser/PDF verification, source-population decisions, unresolved mappings, independent manual-table reconciliation, historical/deletion handling and atomic publication remain open acceptance work.

## Missing count coverage: independently checked and future gate tightened

A direct, read-only SQL endpoint query against **CD_Validation_Lakehouse** now independently counts all 17 manual tables and `meta_PipelineRun`. All manual tables have zero rows; heartbeat has one. These 18 distinct table counts agree with all 19 corresponding model/table comparisons across the two saved DAX result sets. The repeated heartbeat comparison accounts for the difference between 18 and 19. Evidence is in `candidate-independent-counts.json`; the exact SQL is retained in `candidate-missing-counts-query.sql`. SQL identifiers use Spark's lowercase physical table names. Query capture times are explicit: these are separate current-state reads, not an atomic snapshot or source-intake completeness proof. Empty registers remain missing input evidence, not proof that there are no risks, inspections or obligations.

The repeatable validator previously listed unpaired tables without failing. This gap is corrected locally: missing independent count coverage now fails the candidate check. Gold diagnostics will include post-materialisation counts for every manual table and compare them with counts before materialisation, so unexpected loss or duplication blocks the build. Legitimately empty manual tables are allowed and recorded as empty without speculating why. The DQ heartbeat writer now persists its row count with the run ID; the candidate checker rejects missing or mismatched heartbeat evidence and invalid expected count types.

Regression tests cover empty and nonempty manual tables, row loss during materialisation, missing model count coverage and run-linked heartbeat counts. **All 17 local suites passed** after these changes. These newer generator/library changes have not yet run in Fabric: the existing integrated candidate remains valid evidence for its earlier scope, but does not satisfy the expanded automatic count gate. The next integrated build must produce the new diagnostics before candidate checks can pass under the strengthened contract. No historical diagnostic is rewritten to pretend these checks executed previously.

The repaired Procore run is still active. Its matched live session log identifies batch `20260910T081211-fb70763e`, successful authentication and 20 active projects. Spark monitoring returned recent successful jobs through 08:28:16 UTC. This proves ongoing execution, not completion of all 44 endpoints. See `procore-repair-sessions.json`, `procore-repair-stdout.txt` and `procore-repair-spark-jobs.json`. Continue polling job `f310bd55-4b1f-4418-b3d5-b3153fe22978`; do not restart it because observation ends or logs are buffered.

## Financial checks now compare balances instead of assuming portfolio size

The legacy model validator contained two unsupported historical assertions: all-period retainage had to exceed owner retainage by more than three times, and current contract value had to stay below $100 million. Neither is a validity rule: a new contract can have only one billing period, retainage can be released or negative, and legitimate portfolio growth can exceed the dollar limit. These assertions have been removed.

The shared validator now compares owner and subcontractor retainage with the fact rows flagged as the latest issued period, net retainage with its component balances, and current contract with each project's last nonblank contract period. This catches aggregation differences without assuming a historic ratio or portfolio ceiling. It rejects missing or nonfinite evidence rather than converting it into a valid zero. Zero and negative amounts remain valid values when they reconcile. The candidate model checker reuses these checks for the monthly model.

The new DAX query executed successfully against `CD_Validation_Monthly` at **08:34 UTC on September 10**. All four comparisons agree within one cent: owner retainage **$889,664.45**, subcontractor retainage **$404,444.70**, net **$485,219.75**, and current contract **$35,451,887.39**. `candidate-balance-evidence.json` records the query, results, model ID and candidate run ID. This is semantic aggregation evidence over the candidate facts; it neither independently certifies Procore balances nor proves that the latest-period flags have correct upstream inputs. Those remain covered by separate source/transformation checks.

Regression cases accept a correctly reconciled $250 million contract, zero owner retainage and a negative subcontractor balance, while rejecting missing, nonfinite and overstated contract values. The full 17-suite harness passed after the change. The active Procore extraction was re-polled and remains `InProgress`; no new extraction or downstream rebuild was started.

## Partial Power BI query responses cannot pass silently

Microsoft's [Execute Queries API documentation](https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/execute-queries) states that an HTTP 200 response can carry limited rows and an error, with error fields at response, query-result or table level. The shared `validate_model.dax` helper previously returned the first table's rows without checking these error fields. This was a latent validation gap, not evidence that any recorded candidate query actually returned partial rows.

The helper now rejects embedded errors at all three levels, malformed/missing row collections and unexpected result/table multiplicity. Both candidate validation and the read-only audit already use this helper, so the correction applies to all callers. Genuine empty result sets remain empty; explicit NULL remains unknown and zero remains zero. Regression tests inject HTTP-200 partial-data errors at each level and verify these failures, plus structural failures and null/zero preservation.

Live candidate queries confirm the service returns an explicit empty rows list for an empty DAX result, and that the corrected helper preserves empty, NULL and zero results. The four live balance comparisons also pass through the corrected transport. See `dax-empty-response-evidence.json` and `dax-response-validation-evidence.json`. This does not change the still-open upstream completeness, publication and rendered-report acceptance requirements.

## Manual-register coverage message corrected and tested

`DQ Registers Awaiting Input` previously checked just three of the eight manual quality registers, asserted that no data had been entered, and returned an empty message once any of those three had rows. This could conceal seven unpopulated registers and confuse unavailable data with absent submissions.

The revised expression counts empty tables across all eight registers in the current filter context and always retains the qualification **completeness unverified**. Read-only synthetic DAX scenarios with zero, one and eight populated registers return 8/8, 7/8 and 0/8 empty respectively; all three pass. Evaluating the revised expression against the actual candidate returns **8/8 registers empty; completeness unverified**. Evidence and complete fixture queries are in `manual-register-coverage-evidence.json`. The reusable `check_register_coverage` check is now part of candidate PQP validation. No source records were inserted for these tests.

Report copy now distinguishes missing Sage coverage from established zero revenue, avoids inventing reasons for unmatched vendors, and states that empty gate registers neither prove completion nor non-applicability. The quality data page describes filter scope and submission completeness explicitly. These are local model/report changes; they have not been deployed or visually certified. Existing report binding/geometry tests are the available layout evidence.

A further issue remains to resolve before meaningful quality input is published: Gate Readiness and Checklist Completion currently divide project-result counts by one shared template count. Multiple-project selections can therefore overstate percentages once registers are populated. Project applicability is also unverified. These measures require filter-scope guards and tests against multi-project fixtures, with template-based completion clearly distinguished from certified readiness.

## Quality percentage scope corrected locally

The issue above is now corrected in the model/report generators. The measures are named **Gate Template Completion** and **Checklist Template Completion**. Each requires exactly one known project, positive recorded input and a positive template denominator. Recorded rows cannot exceed the template count, and completed/passed rows cannot exceed recorded rows. Invalid or absent evidence leaves the percentage blank; recorded input with no completed/passed rows returns a valid zero. No cap is applied to conceal over-counting.

The gate report card uses the new name and explains that these are recorded results against a template, not certified readiness or confirmed project applicability. The model measure renames and corresponding report bindings must be released together; existing deployed definitions have not changed. Project-specific applicability still needs authoritative inputs before readiness or compliance can be certified.

`check_template_completion` now runs as part of candidate PQP validation. Its live DAX fixtures tested ten scenarios for each measure: no project, multiple projects, blank/unknown project, missing input, zero completions, partial completion, full completion, excess recorded rows, excess completed rows and a missing template denominator. **All 20 scenarios passed** against the candidate service using revised expressions and real project filter contexts, without source writes or model deployment. Evidence: `template-completion-evidence.json`. These tests replace the expressions' input measures with synthetic counts, so they establish percentage and selection behavior; they do not certify the underlying register sources.

Declared lineage was regenerated for both models and all 19 report pages. The full offline harness passed all 17 suites, including report field bindings and layout checks. Actual browser rendering and export checks remain outstanding, and the live Procore extraction is still `InProgress` on its original job handle.

## Endpoint evidence survives later extraction failure

The active batch's final manifest currently returns HTTP 404 while its authoritative Fabric job remains `InProgress`. A read-only OneLake directory listing found raw JSONL captures for **31 of the 44 configured endpoints**, including submittals, RFIs, cost codes, contracts and incidents. `procore-repair-archive-list.json` preserves file sizes and capture time. A file may still be open, and an empty file does not prove an empty source. No endpoint is certified complete from this listing alone.

The extractor previously held endpoint audit records in memory until the final batch manifest was written. A later process/session failure could therefore leave raw captures without durable completed-endpoint outcomes. The notebook generator now writes an exclusive, batch-linked `<endpoint>.audit.json` checkpoint after every attempted endpoint, including failed and parent-skipped endpoints. It records the same status, source-scope outcomes, received/archived/written counts and watermark state retained in the final manifest. It does not turn a partially processed batch into a successful one.

Checkpoint-write failure propagates and stops further extraction. Replay cannot overwrite prior checkpoint, raw capture or final manifest files. Generated-notebook regression tests verify success, denied scope, partial-page failure, merge failure, unavailable parent, archive failure, checkpoint failure and replay preservation. These are local generator changes and have not been deployed into the currently running job. Evidence for that job must still come from its original version's final manifest, authoritative job status and raw captures.

## Model refresh success is matched to its own request

The shared model refresh helper previously polled only the latest refresh-history entry. A delayed history update or another refresh could therefore allow an unrelated completed run to satisfy validation. The helper now captures the refresh ID from the accepted response and matches only that request in history. It returns the matched run record, including timestamps, for candidate evidence. Missing tracking IDs and ambiguous matches fail; a timeout remains unverified and can be resumed with `wait_refresh` using the same ID, without another submission. This uses Microsoft's documented [refresh response headers](https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/refresh-dataset) and [history requestId](https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/get-refresh-history).

Regression tests present an older completed request and a newer unrelated completed request while the target is pending, then verify only the target's completion succeeds. Failed, cancelled and disabled target states fail despite an unrelated success. An unobserved timeout cannot pass.

Live validation refreshed only `CD_Validation_Monthly`. Request **481eeeaf-dff2-4fa6-9a35-6e511fb311c3** started at 08:49:43 UTC and completed at 08:49:51 UTC on September 10. Its matched history record is in `candidate-refresh-identity-evidence.json`. This proves that specific refresh completed, not that source extraction or cross-model publication is complete. The Procore extraction remains on its original active handle.

## Spend status no longer implies a final-cost forecast

The Budget Status expression used the existing budget-minus-spend percentage to say **On Track**, even though that calculation does not consider forecast cost or remaining work. The calculation and inherited 5% band boundary remain explicit; the labels now say **Spend within budget**, **Spend over budget up to 5%**, or **Spend over budget above 5%**. Unknown variance still returns BLANK. The financial matrix's accessible description also states that this is a spend comparison, not a final-cost forecast.

The reusable `check_spend_status` check evaluates the revised DAX expression with missing input, zero gap, positive remaining budget, a small overrun, exactly 5% overrun and an overrun above that boundary. All six live scenarios passed; `spend-status-evidence.json` retains the query and results. The candidate monthly validator now includes this check. These are local model/report changes and have not replaced the deployed definitions. Forecast validity and historical accuracy remain separate open requirements.

The latest extraction poll still reports `InProgress` and the current raw-capture listing still has 31 endpoint files. Neither observation establishes full source coverage; the existing job has not been restarted.

## Validation status states its actual scope

The shared status expression used by both reports now says **Gold checked with warnings; source completeness unverified** or **Gold checks passed; source completeness unverified** for the corresponding recent validation outcomes. A completed gold quality run must not be read as evidence of a complete upstream extraction. Blocking, missing, newer-than-check and stale-data states retain their existing precedence.

Read-only evaluation of the revised expression in both candidate models returned the qualified warning status expected from their recorded checks. `validation-scope-status-evidence.json` preserves both queries and results. Both report binding/layout suites passed, covering 19 pages and 276 visuals, and declared lineage was regenerated. This is a local wording correction, not a model deployment or proof of browser text rendering.

## Exact-duplicate removal is accounted for explicitly

The extraction audit now records `duplicate_rows_removed` after a successful merge, making the intended count identity explicit: received/archived rows equal distinct upsert input rows plus removed exact duplicates. The shared merge helper rejects conflicting versions of one key; only exact repeated rows are collapsed. A failed or unattempted merge leaves the duplicate count unknown rather than inventing a reconciled value. The final manifest states that `written_rows` counts distinct input rows submitted to a successful upsert, not separate inserted/updated totals or a full target-table row count.

Generated-extractor tests now replay repeated identical source records, verify both copies remain in the raw archive, verify the explicit duplicate count and count identity, and retain replay-protection checks. The full 17-suite harness passed. These audit additions are local and have not been installed into the active extraction. At the latest observation, 09:04 UTC, that run remained `InProgress` with 31 raw-capture files; no final completeness claim is justified.

## MCP access rechecked

A fresh Azure MCP `subscription_list` call using tenant `b2a2225b-4b4e-42ec-ba52-c7e1c2dea580` again timed out after 300 seconds. The actual tool response is saved in `azure-mcp-retry-evidence.json`. Current tool discovery still exposes no Microsoft Fabric MCP tools; Azure Service Fabric is a different service. Existing authenticated Fabric REST/OneLake and SQL evidence must not be described as MCP deployment validation.

Microsoft's [Azure MCP troubleshooting guide](https://github.com/microsoft/mcp/blob/main/servers/Azure.Mcp.Server/TROUBLESHOOTING.md) was consulted again. It documents credential-chain and host-environment checks, but the observed timeout alone does not establish which cause applies here. No credentials, global authentication settings or application processes were changed. MCP deployment readiness remains unproven; this does not invalidate the separately observed REST/SQL access or completed candidate checks.

### Azure MCP read access subsequently succeeded

The installed Azure MCP executable (3.0.0-beta.42), run separately with a process-local `AZURE_TOKEN_CREDENTIALS=AzureCliCredential`, initially reported an Azure CLI authentication timeout after 14.84 seconds. A direct CLI token check then succeeded in 2.11 seconds; token contents were not logged. The isolated MCP retry succeeded, followed by a successful call through the app's actual Azure MCP `subscription_list` tool. Both identified subscription `73932b34-3bb6-4a94-bd4b-4b7623d4f7d6` as the default. Evidence is in `azure-mcp-isolated-evidence.json`, `azure-mcp-isolated-retry.json`, and `azure-mcp-success-evidence.json`.

No global configuration was changed and no existing server process was restarted. The earlier timeout's underlying cause is still unestablished. This proves current subscription discovery through Azure MCP, not deployment permission or a completed deployment. Fabric MCP remains unavailable in the exposed tools.

## Candidate count evidence belongs to one build

Candidate model reconciliation previously read mutable `gold_run.json` and `seed_run.json` files, so a later run could replace part of the expected-count evidence. The candidate build now captures seed counts and gold verification results in memory immediately after their successful stages, then writes `candidate_counts_<run_id>.json` exclusively after quality persistence and the blocking gate succeed. This snapshot includes the run ID, validation lakehouse ID and heartbeat count. The model validator requires the corresponding snapshot and rejects an incorrect run or lakehouse. It no longer falls back to the mutable stage files.

Regression checks verify snapshot contents, preservation after later in-memory changes, rejection of mismatched run/lakehouse evidence, missing table-count coverage, and persistence failures. These changes are local and require a new completed candidate build before live certification; the older candidate is not retroactively assigned new evidence.

The full 17-suite harness passed after this change (`latest-test-run.txt`). The existing Procore extraction still reports `InProgress`; its latest observed Spark job, 1330, succeeded at 09:19:01 UTC on September 10. The final ingestion manifest is still absent. This is progress evidence, not source-completeness evidence, and no downstream build was started against the changing bronze tables.

## Schedule timeline preserves individual activities

A live candidate query found repeated milestone names within a project (`milestone-grain-before.json`). The prior chart grouped only by name and used minimum start / maximum finish, which could merge separate activities into one apparent duration. Its generated type was `stackedBarChart`, and its title still instructed the user to make the offset transparent manually. Microsoft's [Cartesian report-authoring reference](https://github.com/microsoft/skills-for-fabric/blob/main/skills/powerbi-report-authoring/references/cartesian.md) identifies the native stacked horizontal type as `barChart` and documents active category levels and per-measure transparency selectors.

The generator now uses that native type, activates project/activity/name category levels, and sets the offset series' `fillTransparency` to 100 using its exact query reference. Duration and offset require exactly one fact row with nonmissing, ordered dates; the origin excludes invalid date pairs. Aggregated groups return BLANK rather than a fabricated milestone span. The adjacent detail table retains project/activity IDs, dates and inversion flags. Same-day milestones have a legitimate zero duration and remain readable in the table. Baseline variance remains unavailable.

Before-change live evidence showed DAX already returned BLANK for either missing date, while an inverted pair returned -9 (`milestone-missing-date-before.json`); missing dates were not falsely reported as a reproduced numeric defect. New live checks evaluated all 16 geometry scenarios, including visual grouping, multiple records, empty scope, missing dates, inverted dates, valid durations and a valid zero (`milestone-geometry-evidence.json`). Independent date subtraction also matched revised durations for all 126 candidate project/activity groups (`milestone-live-grain-evidence.json`). Offline regression tests check the native type, full category grain, series selector/transparency and retained detail fields. All 17 suites passed, and lineage was regenerated for both models and 19 pages.

These are local definition changes and read-only evaluations of generated expressions in the isolated candidate. They do not prove that the revised report has been deployed or rendered correctly in the browser. The source extraction still reports `InProgress` with no final manifest, so a new integrated candidate build remains pending.

## Deployment lookup validates complete inventory and ownership

The shared item lookup previously searched only the first response page and returned the first matching name/type anywhere in the workspace. Several deployment callers did not independently reject a target outside `charley-dev`. The shared lookup now reads all pages, rejects duplicate matching names and rejects a unique match outside the owned folder. Missing or malformed collections, repeated IDs, looping continuations and links leaving the original endpoint fail instead of being interpreted as absence. Folder verification uses the same paginated reader. This follows Microsoft's [item pagination](https://learn.microsoft.com/en-us/rest/api/fabric/core/items/list-items) and [folder listing](https://learn.microsoft.com/en-us/rest/api/fabric/core/folders/list-folders) contracts.

Regression tests exercise a target on page two, token-only continuation, encoded token characters, duplicate names, wrong-folder ownership, malformed/duplicate records and unsafe/repeated continuation links. The live read-only helper returned 86 workspace items, including 30 in `charley-dev`, and verified the configured folder's name and ID. `deployment-lookup-evidence.json` retains the timestamp and owned item IDs. No resources were deployed or moved by this check. This protects shared name-based lookup; it is not a claim that every ID-based upload or release operation has been independently audited.

## Full source repair failed transparently; checklist defect reproduced

Job `f310bd55-4b1f-4418-b3d5-b3153fe22978` ended `Failed` at 09:33:12 UTC. Its final immutable batch manifest is saved as `procore-repair-manifest.json`; `procore-repair-summary.json` records its hash and totals. Across 44 endpoints and 20 active projects, 34 endpoints completed, seven had incomplete scope and three failed. The manifest reports 21,673 received/archived source records and 21,663 distinct upsert inputs. Per-scope received counts reconcile to the endpoint counts. These are different concepts from inserted/updated target totals or complete historical source coverage.

The seven scope gaps are standard cost codes, prime contracts, change-order requests, punch-item types, schedule, prime-contract line items and payment applications. The last two inherit incomplete parent coverage. HTTP 403/404 observations do not establish whether the cause is permissions, endpoint availability, or tool configuration. They have not been dismissed as empty data or an approved exclusion.

`checklist_lists` failed before merging because the source returned template groups, each containing a `lists` array, instead of individual inspection records with a top-level `id`. The raw capture proves ten groups contain **21 distinct project/inspection keys**. The shared normalization helper now expands only this observed grouped response, retains template metadata on each normalized inspection, accepts an already-flat inspection, and rejects malformed shapes. Both Fabric and local extraction paths use it. Raw Fabric archives retain the original source groups. Audit counts now distinguish received/archived source groups from normalized rows; after a successful merge, normalized rows equal distinct upsert inputs plus removed exact duplicates. Child discovery now receives the actual inspection IDs with their projects.

The raw-capture replay and key conservation passed (`checklist-normalization-evidence.json`). The observed payload also supplies `list_template_name` and `due_at`, whereas the old silver parser expected different fields. The parser now uses the observed fields with legacy fallbacks; missing completion percentages remain unknown. All 17 offline suites passed, including malformed group, parent association and live-shaped parser regressions. Inspector arrays and the business interpretation of completion counts still require mapping review; this fix does not certify those fields.

The other direct failure was a request timeout in `incident_injuries`; `checklist_list_items` failed because its parent failed. A separate owned notebook, `cd_95_repair_procore_scopes`, was deployed with the updated helper and started as job `83e5228a-7c67-41e5-86c7-1edc0c15597e`. It requests only these three endpoints, labels its manifest scope `active_projects_selected_endpoints`, and leaves the original full extraction definition intact. Its handle and definition/library hashes are in `procore-scope-repair-job.json`; the generated notebook is retained. At the latest check it is `InProgress`. This is a targeted REST deployment, not Fabric MCP deployment or resolution of the seven other scope gaps.

An independent OneLake read parsed all 43 created raw archives and reconciled each file's row count and per-request/project counts to the manifest: **21,673 archived records matched**. Each file's SHA-256 is retained in `procore-raw-archive-validation.json`. The unattempted checklist child has no archive. This proves the recorded captures were retained and readable, including partial/failed endpoint captures; it does not prove inaccessible scopes were captured, source pagination was exhaustive, or every captured row reached a target table.

### Targeted repair result and incorrect checklist-item route

The targeted job ended `Failed` at 09:42:47 UTC because its final scope gate rejected unavailable checklist-item requests. Its manifest, `procore-scope-repair-manifest.json`, identifies batch `20260910T093949-7db12c99`. Checklist normalization succeeded remotely: 10 archived source groups, 21 normalized inspections, 21 successful distinct upsert inputs and zero removed duplicates across 20 completed project scopes. Incident injuries completed across all 20 projects and returned zero records for the requested scope; this does not establish absence outside that scope.

All 21 attempted checklist-child URLs returned 403/404. Procore's [Checklist Items API reference](https://developers.procore.com/reference/rest/checklist-items?version=1.0) documents the list operation as `/rest/v1.0/projects/{project_id}/checklist/list_items`, with `list_id` on returned records. The previous nested URL was not that list operation. The registry now uses the project-scoped list endpoint and retains returned inspection associations; it no longer needs parent-driven requests for this endpoint. Regression coverage asserts the corrected path and scope. Live validation of this path is the next step, not yet a success claim.

All 17 suites passed after the registry correction. The owned full extractor definition and its six runtime/configuration files were updated through Fabric REST/OneLake without starting a full run. This deploys the grouped-record normalization and current audit fields for future full runs. The separate repair notebook was then updated to request only `checklist_list_items` and started as job `71782d52-87fb-4d8a-938d-5f55213fb2e0`; `procore-items-repair-job.json` retains its handle and definition hash. This is a new run for an evidenced route correction, not a restart triggered by an observation timeout. Its result is pending.

Independent OneLake read-back confirmed all six deployed runtime/configuration files match the local SHA-256 values (`ingestion-current-deployment-evidence.json`). This proves file deployment consistency, not a completed full extraction or source coverage.

### Checklist-item route works; transport timeout remains distinct

The corrected item route returned 80 records with `id` and `list_id`, preserved in `procore-checklist-items-raw.jsonl`, before a read timeout at project `562949955064640` stopped batch `20260910T094747-57011dfb`. Its endpoint did not upsert those partial rows. Six project scopes completed and the seventh timed out; this is not an empty result or a successful refresh. The job's terminal failure and manifest are saved in `procore-items-repair-job.json` and `procore-items-repair-manifest.json`.

The existing rate-limit session now retries transport timeouts/connection failures only for GET, using the identical URL and request parameters, at most three attempts with one- and two-second backoff. Quota gating remains active, failed attempts are counted, and persistent errors propagate. Token POSTs are not retried by this change. Regression checks cover recovery, same-page identity, exhaustion, and no POST retry. The rate-limit self-check also passes. The updated runtime file was uploaded and independently hash-verified. Targeted job `00b17e0a-9fd5-44cd-a520-3e595613ded8` ended `Failed` at 09:54:59 UTC; its manifest again records 80 archived rows, zero upserted rows and a `ReadTimeout` on the same project. Handles and manifest are retained as `procore-items-retry-*`.

No further identical whole-project request has been submitted. The documented `filters[list_id]` option provides a bounded diagnostic: request each known inspection separately while preserving complete parent discovery and accounting for every parent. The implementation and pending run are recorded below; the underlying server/network cause of the persistent whole-project timeout remains unknown.

Inspection headers currently stop at silver; no gold/model/report object reads them, and inspection items are not yet transformed downstream. The checklist report note now explicitly distinguishes manual-register counts from unlinked Procore inspection results. It does not claim those results satisfy the controlled trade templates. The read-only audit's boolean is now named `gold_checks_recent`, with current qualified status wording, rather than suggesting end-to-end validation is current. Its status cases and report bindings are tested.

### Additional request-contract gaps found

The [Punch Item Types reference](https://developers.procore.com/reference/rest/punch-item-types) requires a project ID. The former company-scoped request omitted it; the local registry now requests each active project. The [Change Order Requests reference](https://developers.procore.com/reference/rest/change-order-requests?version=1.0) requires a contract ID as well as a project ID. The local registry now discovers prime-contract/project pairs and supplies both through the existing parent-scope helper. Missing prime-contract scope still prevents a completeness claim. Path-expansion regressions pass for both corrections. These two registry changes are local and have not been deployed into the active item-only job.

The [Standard Cost Codes reference](https://developers.procore.com/reference/rest/cost-codes?version=latest) also requires `standard_cost_code_list_id`, absent from the current request. Its old list-discovery endpoint is deprecated in favor of WBS segment-item lists. Discovery/migration remains unresolved; the observed 403/404 must not be labelled a confirmed permission failure. No list IDs, contracts, applicability rules or permissions were guessed.

## Inspection-filtered diagnostic and empty manual snapshots

The checklist-item configuration now uses the documented project list route with `filters[list_id][]` for each discovered inspection. The shared parent-path helper substitutes the project from the parent/project pair and rejects a missing project when the URL requires it. It does not infer a project from the portfolio list. Existing query-parameter parent routes keep their behavior. Regression checks verify two inspections from different projects, missing-project rejection and all 44 registered endpoint call shapes. The compatibility fixture now supplies the same parent/project pair used by production. The full 17-suite harness passed after that fixture correction.

Diagnostic job `c369b3aa-d255-45ec-898c-28cfcaf6ba99` first discovers all active-project inspection parents, then requests their items. It uses a dedicated `endpoints-inspection-repair.yml` configuration and the existing owned repair notebook; the full extractor's deployed registry was not replaced by this experiment. Its definition, runtime/configuration hashes and handle are retained in `procore-items-filtered*`. The latest authoritative job check remains `InProgress`. A pass will still require reviewing every parent request and comparing returned `list_id` values to the requested inspection, not just accepting the job status.

The manual CSV generator now rejects a supplied empty file when its destination already contains rows, before any overwrite of that table. This closes the gap where a header-only export could erase an existing register. Empty initial data and nonempty replacement snapshots retain their previous behavior. The existing missing-file preservation and storage-error behavior remain intact. Generated-code tests cover empty-to-populated rejection, empty-to-empty acceptance and nonempty input. This guard is local, not yet deployed; deliberate clearing of a populated register still requires an explicit operational deletion path rather than treating an empty export as proof.

All 17 suites passed again with the manual empty-snapshot guard included (`latest-test-run.txt`).


### Fabric Core MCP connection verified (2026-09-10)

The documented remote endpoint `https://api.fabric.microsoft.com/v1/mcp/core` accepted the existing Fabric bearer identity through the actual MCP initialize and tools/list protocol. An MCP tools/call to list_items returned 31 items, all in the authorized charley-dev folder, without a continuation token. Evidence: fabric-core-mcp-probe.json, fabric-core-mcp-tools.json, and fabric-core-mcp-folder-evidence.json. This is an isolated protocol connection, not an installed Codex connector. No global configuration or remote items were changed.

The discovered tools include get_item_definition and update_item_definition, so definition deployment is a supported capability. A write through MCP is not yet verified; existing deployment evidence remains REST/OneLake. Notebook job execution and OneLake file upload were not exposed in this discovered tool inventory. Azure MCP subscription discovery has separately succeeded. Neither connection proves data correctness or deployment completion. Official setup: https://learn.microsoft.com/en-us/rest/api/fabric/articles/mcp-servers/core-remote/get-started-core

The filtered inspection job c369b3aa-d255-45ec-898c-28cfcaf6ba99 remains InProgress at this check. No success, full item coverage, or correct parent association is inferred until terminal evidence and raw-record reconciliation are available.


### First verified definition deployment through Fabric MCP (2026-09-10 10:14 UTC)

Updated only cd_06_land_manual in charley-dev through the remote MCP update_item_definition tool. Backed up the previous definition through MCP before writing. Operation 198e5187-6f21-4044-bb4b-d44b26800d4a reached Succeeded; a separate MCP get_item_definition operation retrieved the deployed notebook. All five cells and lakehouse dependencies match the locally generated intended definition. No notebook execution was requested and no input data was changed.

The deployed changes preserve an existing manual table when its CSV is absent, propagate filesystem failures, use FAILFAST with header/schema validation, and reject an empty CSV replacing populated data. Targeted validation tests passed before deployment. These tests and definition readback do not prove runtime Spark behavior against real malformed CSVs; that remains a separate validation task.

Evidence: manual-mcp-before.json, manual-mcp-backup.json, manual-mcp-definition.diff, manual-mcp-intended.ipynb, manual-mcp-deployment.json, manual-mcp-readback.json. This supersedes the earlier statement that no MCP write has been verified, specifically for notebook definition deployment. Notebook job execution and OneLake uploads still use the existing REST/OneLake paths.

Inspection diagnostic c369b3aa-d255-45ec-898c-28cfcaf6ba99 remains InProgress, with both batch-specific endpoint completion checkpoints absent (404). No new job was submitted and no downstream candidate build was started while its writes remain active.


### Inspection source fields preserved through silver (2026-09-10)

The local inspection transform and its source view now retain the complete inspectors JSON array, source template ID, item count, conforming, deficient, not-inspected, not-applicable, and neutral response counts. The legacy singular inspector field remains for legacy-shaped payloads; array assignments are not collapsed to an arbitrary first person. Missing counts remain NULL and actual zero remains zero. Closed status does not imply completion: the captured source includes a closed inspection with 15 of 16 items uninspected. No completion percentage is derived.

A two-inspector fixture verifies every assignment survives; counts, template ID, missing neutral count and closed-but-incomplete behavior are checked against the real transform. All 70 silver checks and all 17 test suites passed. File hashes and limits are recorded in inspection-field-validation.json. These SQL changes are local and require a new Spark candidate build. The native inspections still have no gold/model/report consumer and no approved mapping to manual checklist templates; preserving fields in silver does not close that reporting gap.


### Filtered inspection extraction completed and independently reconciled

Job c369b3aa-d255-45ec-898c-28cfcaf6ba99 completed at 2026-09-10 10:16:22 UTC. Batch 20260910T095953-d161e967 retrieved 10 template groups containing 21 inspections and 563 inspection items. All 20 active-project parent scopes and all 21 discovered inspection scopes completed. Both raw archives were read independently from OneLake and hashed. Every returned item list_id matches its requested inspection filter and a parent within the same project; all 563 project/item keys are unique; each of the 21 parent item_count values matches its independently counted child records. Source, archive, normalized and written totals reconcile at their respective grains. Evidence: procore-items-filtered-manifest.json and inspection-association-evidence.json.

This resolves the timeout/route gap for this active-project inspection batch. It does not establish deleted/historical record coverage, future extraction reliability, or a manual-template equivalence. The full extractor config still needs the verified filtered route deployed; this run used the dedicated repair config. Other source gaps remain recorded above.

### New integrated candidate started

The prior completed candidate evidence was copied to validation-history/78ea309feb6047cabfc7cf58f7521997 before starting run 4a59bed595504fd69a859e78121e507c. Its exact job handle is recorded in full-spark-job.json. The existing runner verified prior validation jobs were terminal and started the new run only after inspection ingestion completed. This run validates current silver/gold transformations in the isolated validation lakehouse and generates immutable run-specific count evidence. No success is inferred from submission; published report validation remains outstanding.


### Mock-up metric qualification

The PQP measure previously called Mock-Ups Registered counts a heuristic: submittal subjects containing MOCK. That label overstated the evidence and could be mistaken for the workbook confirmed register. The local model and report generators now call it Possible Mock-Ups, and the page note explicitly states that text matches can be wrong or incomplete and are not a confirmed register. The measure description documents the exact matching criterion. The underlying heuristic is unchanged and remains unsuitable for certification without an approved source field or mapping. Published artifacts remain unchanged pending candidate validation.


### Observation population and time-axis disclosure

The QC fact historically named fct_QcNcr contains all retrieved Procore observations, not a verified NCR-only population. The local PQP measures, cards, page navigation and register title now identify these as observations, preserving the population rather than inventing an exclusion rule. The page explicitly says that NCR classification requires review. Internal fact names remain unchanged for compatibility.

The observation chart is filtered through fct_QcNcr.MonthStart, derived from created_date. Its note now states that it groups currently open observations by creation month, not historical month-end backlog. Generated PQP checks passed for 7 pages, 95 visuals and all 58 field bindings. These are structural checks; rendering and live renamed-measure validation remain outstanding. The isolated Spark job e345fcbb-4555-4b4b-802e-0554cf7c81e7 was rechecked and remains InProgress.


### Disclosure regression checks and refreshed lineage

The report regression test now requires the observation-population, creation-month versus historical-backlog, and inferred mock-up disclosures. It rejects the former Total NCRs and Mock-Ups Registered measure labels while requiring Total Observations and Possible Mock-Ups. The generated PQP report tests pass. The declared lineage inventory was regenerated for both models and all 19 pages after these renames; it remains declared lineage rather than a completeness certificate.

Integrated validation job e345fcbb-4555-4b4b-802e-0554cf7c81e7 remains InProgress. Its matching live Spark session and driver output were retrieved into full-current-session.json and full-current-stdout.txt. The current output shows session initialization only, so no transform-completion claim is made.


### Verified inspection route promoted to regular extraction

The regular extractor Files/config/endpoints.yml now uses the same checklist_list_items parent-filtered route that completed with 563 independently reconciled items. The existing full-extractor notebook and bronze lakehouse were resolved by unique name/type within charley-dev; its live notebook sessions showed no active extraction before the config write. The previous config was backed up. Parsed before/after comparison confirms checklist_list_items is the only changed endpoint; pending punch/COR scope edits were not bundled. Readback matches the promoted bytes and the deployed shared procore_scope helper matches the tested local helper.

Evidence: inspection-config-before.yml, inspection-config-promoted.yml, inspection-config-promotion.json. This file deployment used OneLake REST, not MCP; no job execution was requested. It closes the dedicated-repair versus regular-config gap for inspections, but a future full regular run remains unverified.


### Inspection parent association enforced during extraction

Both local and generated Fabric extraction now pass the actual request path into the shared normalization helper. For checklist_list_items, it requires exactly one inspection filter and an equal returned list_id before records can reach the merge. Missing, conflicting, or multiple parent filters fail rather than attaching a returned item to the wrong inspection. The Fabric raw archive is written before validation, preserving rejected input for diagnosis.

Targeted validation and extractor compatibility tests pass, including mismatched/missing/multiple-filter failure cases. All 563 independently archived records from the successful batch pass the new guard unchanged. This helper and its caller changes are local only and must be deployed together; the currently deployed helper remains the prior version. The active integrated candidate does not contain this extraction change because it reads already-landed bronze.


### Inspection parent guard deployed and read back

All 17 test suites passed with the parent-association guard. Both inactive extraction notebooks were backed up, then their existing definitions were changed only to pass the request path to normalization. Definition updates used Fabric Core MCP; readback through the Fabric definition API confirmed all cells match. The shared helper was then uploaded through OneLake and its bytes read back exactly. No extraction was run. Evidence: inspection-guard-backups.json and inspection-guard-deployment.json.

The initial MCP update failed terminally with PyToIPynbFailure because the exported definition omitted explicit format. The corrected request sets format=ipynb; both notebook updates and helper deployment subsequently completed and verified. This supersedes the earlier local-only guard status. The current integrated Spark validation still reads the already-landed data and is not a runtime test of the newly deployed extraction guard.


### Current silver stage completed; SQL endpoint schema lag observed

The run-specific silver checkpoint for 4a59bed595504fd69a859e78121e507c reports completion at 10:25:53 UTC, with no failed recorded transform steps. The integrated job remains InProgress; full_candidate and candidate_counts files are not yet available. Driver stdout still shows initialization only, so it is not a reliable stage-progress indicator for this run.

An independent SQL endpoint query rejected all newly added inspection columns as invalid column names. Direct inspection of the latest Delta metadata confirms those columns exist in the underlying candidate table, including inspectors_json, template_id and response counts. Evidence: inspection-delta-schema-evidence.json. Thus the underlying schema update is verified but SQL endpoint visibility is not synchronized at this observation. The live row-by-row inspection comparison has not passed and is not claimed. The next step is to verify SQL endpoint synchronization and then reconcile the actual silver values against the archived source.


### Inspection values reconciled through the SQL endpoint

The SQL endpoint now exposes the new inspection schema. A scoped metadata-refresh request (recreateTables=false) returned HTTP 200 with per-table status NotRun and last successful sync 10:35:46 UTC; it is not counted as a successful explicit refresh or proof that the request caused recovery. The following direct SQL query succeeded and returned 21 inspection rows.

All 21 project/inspection keys match the archived source exactly and are unique. Every source template ID, complete inspector array, and seven count/completion fields match the corresponding raw values, including NULL versus zero. No mismatches were found. Evidence: inspection-sql-refresh.json, inspection-silver-live.json, inspection-silver-reconciliation.json. This closes the observed SQL schema-visibility gap and verifies these fields from archive through candidate silver to SQL endpoint; it does not verify their display because there is still no gold/model/report consumer.

The integrated job e345fcbb-4555-4b4b-802e-0554cf7c81e7 remains InProgress. Official scoped refresh API reference: https://learn.microsoft.com/en-us/rest/api/fabric/sqlendpoint/items/refresh-sql-endpoint-metadata


### Integrated candidate completed: 4a59bed595504fd69a859e78121e507c

Job e345fcbb-4555-4b4b-802e-0554cf7c81e7 completed at 10:39:43 UTC. Its final 119-rule evidence contains 112 passes, seven warnings and zero blocking failures. Warnings remain: Sage project coverage (5), Outbuild coverage (17), billing exceeding contract (2), retainage released (6), project vendors without certificates (405), expired certificates (105), and unmapped Procore trades (236). Immutable candidate_counts_4a59bed595504fd69a859e78121e507c.json was retrieved and matches the run ID, with gold, seed and heartbeat snapshots. This is the first completed run with that new count-proof artifact. Candidate model count comparisons and updated report/model deployment still remain.

### Native inspection report integration started

Added local fct_ProcoreInspection as a direct, unfiltered projection of the owned inspection source view. It retains project and inspection identity, source template IDs, complete inspector JSON, dates, raw status and source response counts without inferring completion or mapping native templates to manual ones. The gold verifier now includes its count and schema. The actual SQL passes the native-field preservation check, all 31 QC checks, and the raw-to-model contract suite. Model binding and report page are not yet implemented.

This new gold table was added after the completed candidate definition was submitted and is not represented by run 4a59bed595504fd69a859e78121e507c. A subsequent candidate build and DQ coverage for the native register are required before publishing it.


### Native inspection quality gate and new candidate

Added five blocking rules: unique project/inspection pairs, non-null project and inspection keys, valid project relationship, and bidirectional EXCEPT ALL conservation of all 19 projected source fields. EXCEPT ALL retains multiplicity, so duplicate rows cannot hide behind matching distinct sets. Mutation tests prove altered counts, deleted rows and duplicate rows fail the conservation rule. All 32 QC checks, 124 executable quality rules in the raw-to-model test, and all 17 suites pass locally.

The previous completed candidate evidence was archived under validation-history/4a59bed595504fd69a859e78121e507c. New isolated run a09823bcf0bd4a59b2ac7f15e86f64ef was started with the native gold register and the expanded 124-rule suite; its exact handle is full-spark-job.json. No prior live job was restarted. Model and report integration remain outstanding; native templates are not mapped to manual templates.


### Native inspection model and report draft

The PQP generator now declares fct_ProcoreInspection, links its ProjectKey to dim_Project and InspectionDate to dim_Date, and adds Native Inspections as an observed-row count. A separate Procore Inspections page displays source identifiers, template, dates, raw status and response counts. Its note explicitly denies equivalence to manual templates and status-based completion, and states that dated filters exclude undated records.

Generated report structural checks pass for 8 pages, 102 visuals and 70 field bindings. For the new table, local binding checks execute the actual SQL to obtain columns while waiting for the candidate Spark schema; this is not live TMDL validation. The production model generator still requires Fabric-published schema and has no fallback. The declared lineage inventory now covers 2 models and 20 pages. No model or report was deployed. Rendering, live DAX, inspector-assignment presentation and the full child-item register remain outstanding.


### Native inspection item transformations and quality rules

Added cd_silver_qc_inspection_item, sv_qc_inspection_item and fct_ProcoreInspectionItem. All raw rows are retained, including malformed identities for blocking checks. Fields preserve project/item/inspection/section identity, item name, source status and response text, response category/type, and both response JSON payloads. Captured responses include multiple-choice, open text and signatures; no universal pass/fail interpretation is applied.

Six new blocking rules check item uniqueness, non-null identity, the composite project/inspection relationship and bidirectional row/value conservation. A mutation test proves moving an item to a different project fails both parent linkage and conservation. Silver tests pass 71 checks; the raw-to-model test executes all 48 source views and 130 DQ rules; QC checks pass 33 checks. The source-view count guard was explicitly updated from 47 to 48 for this new view.

These changes are local and are not in active run a09823bcf0bd4a59b2ac7f15e86f64ef, which was submitted with the 124-rule header-only definition. They require a later live build, child model/report binding, and raw-to-live reconciliation. No overlapping validation run was started.


### Native item model relationship and report page

Both native gold tables now expose InspectionLinkKey, formed with a length-prefixed project ID followed by the inspection ID. This avoids delimiter ambiguity and prevents repeated inspection IDs across projects from collapsing in the semantic relationship. Items relate only through the parent inspection, inheriting its project and inspection-date filters. Source identity columns remain visible. Added blocking checks for unique header link keys, child link resolution and exact derivation of both tables' model link keys. Corrupt-link mutation testing passes.

The new Inspection Items page retains original status/response labels, response category and type, and project/inspection/item identifiers. It explicitly says No Response is not a failed check and explains the undated-record filter limitation. Local QC checks pass; generated report checks pass for 9 pages, 109 visuals and 79 field references; raw-to-model checks execute 133 quality rules. Lineage now covers 21 pages across both reports. All new child/link-key changes remain local and outside the active 124-rule run. Live schema generation, DAX/filter behavior and rendering remain unverified.


### Inspection relationship collision regression

A new test executes the actual native gold SQL with the same inspection ID in two projects and with delimiter-bearing project/inspection pairs that would collide under naive concatenation. It verifies four distinct relationship keys and exactly four item-to-header joins, each within its original project. Corrupt-key tests remain in place. All 17 local suites pass after the item model/report additions and expanded 133-rule suite.

The active 124-rule candidate run a09823bcf0bd4a59b2ac7f15e86f64ef has a run-specific silver completion checkpoint at 10:52:33 UTC with no failed steps. The new item transformations and model key additions are outside that submitted definition and still need a subsequent live build.


### Inspection header/item completeness check

Added a blocking rule comparing each non-null source header item count with the actual number of child records under the same project and inspection. A missing child group compares as zero retrieved records; a missing source total remains unverified, not coerced to zero. Tests prove 16 expected/15 retrieved and 16 expected/0 retrieved both fail, while a NULL source total is not falsely called a mismatch. The fixture now contains all 16 distinct items, and the relationship-collision test confirms 64 items still produce exactly 64 joins across four identities.

All 35 QC checks pass and the raw-to-model test executes all 134 rules. These are local changes outside active 124-rule run a09823bcf0bd4a59b2ac7f15e86f64ef. The previously archived live source already independently reconciled 563 items to 21 header counts; this new rule makes that invariant repeatable in future gold validation.


### Captured full inspection batch replayed through current SQL

The actual archived batch 20260910T095953-d161e967 was loaded into local bronze-shaped tables, normalized with the shared extraction helper, and processed through the current silver and native gold SQL. All 21 inspections and 563 unique items survived. Every item identity, source status/response, response category/type and both response JSON values were compared directly to the archive and match. All 14 native rules applicable without the live project dimension pass, including header/item totals and relationship-key integrity. SQL hashes and results are in inspection-archive-replay.json.

The comparison uses raw database tuples to preserve SQL NULL rather than dataframe NaN coercion. This is an offline DuckDB execution of captured live data, not a fresh Spark/DAX/report verification. The live dim_Project reference check was explicitly excluded from this replay and remains part of the next candidate build.


### Header candidate completed; full native-item candidate started

Run a09823bcf0bd4a59b2ac7f15e86f64ef completed at 11:03:03 UTC with 124 checks: 117 passed, seven warnings, zero blocking failures. The five native inspection-header checks passed, and its immutable count artifact was retrieved and matched to the run. Prior evidence was archived in validation-history/a09823bcf0bd4a59b2ac7f15e86f64ef.

New run 9835a75b9243452c97f53fc443c97d1c uses the current native item transforms, composite relationship keys and 134-rule suite. The runner revalidated that previous jobs were terminal before submission. Its exact job location is in full-spark-job.json. This is a new definition following completed validation, not a restart of an active job. Model deployment and live report tests await this run's evidence.


### Source completion formatting remains unverified

The model generator now marks fct_ProcoreInspection.SourcePercentComplete as non-additive instead of its default numeric sum. Its description explicitly says the source unit and scale require confirmation; the format displays the raw number without percentage scaling or an asserted percent suffix. Captured inspection records have no populated percent_complete values, so a 0-100 interpretation is not proven by this data. No derived completion value was introduced. A generated-TMDL regression check passes along with the 9-page PQP report checks. This model-only change is local pending live schema/model generation.
