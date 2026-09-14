# Production report audit — 2026-09-14

Status: **not fully validated**. This is an offline definition and regression review; it does not certify live rendering, the current source population, or business approval of mappings.

## Confirmed defect corrected locally

`_local/scorecard.py` defined **Avg Observation Days To Close** as the average age of every closed `fct_QualityItem`, including punch items. The measure feeds the Safety & Quality card and **Score - Observations**, which contributes to weighted project health and Projects At Risk. The independent recomputation in `validate_model.py` repeated the omission, so agreement between those two implementations did not establish the intended meaning.

Both now require `ItemType = Observation`. A regression uses closed observations aged 4 and 8 days, a closed punch item aged 90 days, an open observation aged 100 days, and a closed observation with unknown age. The expected average is **6 days**, rather than the old **34 days**; a context containing only the open observation and punch item returns blank. The monthly `_Measures.tmdl` was regenerated with the existing local emitter. Live deployment and live filtered comparison remain pending; no production impact magnitude is asserted from this synthetic fixture.

## Evidence and its limits

| Check | Result | What it establishes |
|---|---|---|
| Monthly report suite | PASS: 12 pages, 187 visuals, 165 distinct field references | Generated bindings resolve; canvas geometry, estimated text fit, alt text, tab order, slicers, footer, and tested formats satisfy assertions |
| QC report suite | PASS: 9 pages, 110 visuals, 84 distinct field references | Same static guarantees, plus native inspection and manual-register disclosures |
| Monthly PDF screening | FAIL: pages 6–11 | Existing production export contains model/capacity error panels despite successful export status |
| Export page count | Expected: 11 visible pages | Project Detail is explicitly hidden in `deploy_report.PAGES`; absence from the default PDF is intentional |
| Integrated offline suites | PASS: 27 suites at final local integration | Includes report, candidate, publication, lineage and file-replay regressions; later changes require corresponding checks |

The two report suites were run with `python foundation/charley-dev/_local/tests/test_report.py` and the same command with `--qc`. They do not execute DAX on Power BI. The exact failed PDF hash and render evidence are in [report-export-verification.json](report-export-verification.json). Customer PDF content remains in the ignored local render directory.

## Remaining acceptance gaps

1. **Rendered production output:** After capacity recovery, export again and require no error panels, then visually inspect every visible page. Verify the hidden Project Detail page through an actual drillthrough with the selected project retained. A clean text screen alone remains REVIEW_REQUIRED, never a render pass.
2. **Data outside the viewport:** Existing Portfolio matrices/charts have scrollbars. The PDF is a page view and cannot be represented as a complete row-level register. Validate complete data through the underlying table/export path; separately inspect long names, all scorecard columns, and rows beyond the initial viewport interactively.
3. **Capture dates:** `(Month End)` measures take the last available capture within the selected month. This includes a partial current month and a month whose final-day capture is missing. The local chart title now says latest capture in month, and the generated model descriptions no longer assert prior-night source freshness. These changes still require production deployment. Exposing the actual capture date per plotted month remains a useful acceptance enhancement; the timestamp alone does not prove source freshness.
4. **Filter scenarios in the live engine:** Verify one project/month, all projects/month, all months, a project missing a source, a month before snapshot history, and an empty manual register. Compare displayed values with independently recomputed rows from the same run. Existing static tests cover selected cases but cannot prove browser interactions or service filter execution.
5. **Period and balance semantics:** Contract balances carry forward to the selected period end; budget cards use the last source snapshot; open counts show current state grouped by creation month; Total Paid refers to payments on invoices sent in the selected period. These existing disclosures must remain visible in the rendered report. Historical grouping must not be presented as reconstructed historical state.
6. **Cash measure limitation:** The currently unused **Cash Received** semantic measure sums payments on invoices fully settled in the selected period, using the first fully-paid date. It does not represent receipt-grain cash flow or partial payments received during that period. Its existing measure description documents this, but the friendly name alone is ambiguous. Do not introduce it to report visuals as cash flow without resolving the grain or labeling it explicitly.
7. **Source scope and health:** A queryable field and a populated visual do not establish full source coverage. Unmapped AP, unmatched AR, unattributed schedule activity, stale insurance, and empty manual registers remain explicit business/data acceptance gaps. Do not approve mappings by name similarity or turn unknowns into zero to obtain a green report.

Scorecard thresholds and weights are configurable and tested structurally. Whether they express the intended business policy still requires authoritative approval; this audit does not infer that approval from successful code execution.

## Snapshot replacement integrity

Same-date snapshot replacement previously issued separate DELETE and INSERT commits, allowing interruption to erase an existing capture. The source SQL now uses one MERGE with a date-scoped unmatched-source delete and null-safe project matching. Local SQL tests verify replay, changed/added/removed projects, null project keys, preservation of other dates, and an injected constraint failure leaving the previous rows intact. The full generated snapshot validation suite also passes.

Compatibility is supported by the documented [Delta SQL merge support from version 2.4](https://docs.delta.io/delta-update/#modify-all-unmatched-rows-using-merge) and [Fabric Runtime 1.3's Delta 3.2 engine](https://learn.microsoft.com/en-us/fabric/data-engineering/runtime-1-3). DuckDB execution establishes local SQL semantics, not a completed Fabric runtime test. Production execution remains required. Existing post-write failure cleanup can remove a failed new capture; this change does not implement restoration of an older capture after that separate verification failure.

## Actual production-file impact and deployment status

[Stable-version file comparison](production-measure-file-evidence.json) confirms the observation correction changes 23 of 58 project/creation-month groups. Across the available rows, the old average is 31.21 days and the corrected observation-only average is 35.06 days. Fourteen financial-period rows carry a numeric current contract despite an unknown original contract. These are actual stored-data findings, not a successful DAX execution.

The model update was rejected for capacity limits, and its subsequent definition readback was rejected too. The correction is **not verified live**, and preservation of the previous definition must not be assumed. The report label was not deployed after that failure. See [deployment evidence](production-correction-deployment.json).
