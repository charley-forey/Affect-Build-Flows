# Production release audit

Offline review dated 2026-09-14. This document is code/evidence review, not a production certification. It performs no live queries, refreshes, jobs, or deployment.

## Proven release defects fixed in source

- Publication previously read only the heartbeat RunId before refreshing. An out-of-band invocation could refresh despite missing, blocking or mismatched DQ evidence. The shared notebook preflight now requires the exact current rule set, consistent nonnegative results, no blocking failures, and matching successful snapshot/heartbeat evidence before model mutation and before each refresh. Nonblocking warnings remain permitted and visible. This makes a failed snapshot block publication even though the DQ notebook records it without failing its own activity.
- Candidate final evidence was written before persistence and snapshot validation. It now writes a separately named immutable `*_evaluation_<run_id>.json` diagnostic first, preserving failure investigation, and writes `*_candidate_<run_id>.json` only after both snapshot phases and counts succeed. Candidate deployment requires complete, consistent main and both snapshot rule suites. Older certificates without snapshot proof intentionally fail this gate.

Focused regression checks cover missing coverage, mismatched runs, unexecuted/negative results, blocking violations, failed snapshots, accepted warnings, premature candidate certification, and the existing partial-model-publication behavior.

## Existing safeguards reviewed

- Generated pipeline dependencies require Succeeded. Silver waits for source ingestion; seeds follow silver; gold precedes DQ; publication follows DQ. Publication has no automatic retry, avoiding duplicate refresh submissions after uncertain timeout.
- Refresh polling follows the exact request ID. Both models are verified against the gate RunId and Status after refresh.
- Candidate model deployment verifies the job identity, run, isolated lakehouse, quality coverage and model definition identity. Subsequent model validation separately checks build counts and DAX results.
- Public evidence must exclude raw source rows, local customer PDF/images and signed download URLs. Local render artifacts remain ignored.

## Remaining production proof and design limits

| Area | Evidence still required / limit |
|---|---|
| Capacity | Measured recovery before further heavy Spark or broad DAX checks; export completion alone is insufficient. |
| Candidate | Latest recorded job `fd431d1234364ac4b3454f72dc23f4fe` reports Completed but lacks its run-specific final certificate. It is not certified. |
| Scheduled run | Successful full source-to-publication cycle with matching run evidence. Deployed activity definitions are not successful execution. |
| Reader isolation | Automatic update OFF was accepted by the API; browser setting verification and demonstrated isolation remain separate checks. |
| Concurrency | Diagnostic preflight detects mismatched runs, not every concurrent write. It does not lock Delta tables or bind every table version to a certificate. No concurrent gold writer should run during validation/publication. |
| Freshness | Matching static diagnostics can all be old. Source extraction manifests, timestamps and current gold state must be checked independently. |
| Two models | Refreshes are serial and not transactional. If the second fails, the models can show different releases; diagnostics must retain each request and visible run. |
| Rollback | Reverting Git alone does not restore Delta data, semantic framing, or deployed notebooks. Rebuild/restore a known data release, validate it and explicitly refresh both models. |
| Notification | Failure paths record notification success/failure, but delivery and recovery still require an authorized controlled test. |
| Render/UI | Server export success is not rendering success. Existing PDF error panels and interactive filters/drillthrough require separate verification. |
| Source truth | Passing DQ and reconciliation do not settle missing mappings, source permissions, empty manual registers or business interpretation. |

New source safeguards must be deployed and their definitions read back before they can be described as live. No production evidence was created by this offline audit.

## Additional source protections and live state

Candidate model validation now regenerates the full notebook and requires its fingerprint
to match the submitted handle before any remote call. Matching rule names alone cannot
authorize changed source code. Deterministic generation and changed/missing hash tests pass.

Snapshot replacement uses one Delta MERGE, replacing only the selected capture date and
preserving other dates. Tests cover obsolete project removal, null keys, repeat execution
and failed-write preservation. Runtime compatibility is documented in the SQL. This
removes the old DELETE/INSERT interruption gap; post-write validation cleanup remains a
separate recovery limitation. The new MERGE has not been executed on Fabric.

The publication guard definition was deployed and its cell contents matched readback
exactly ([evidence](production-publication-gate-deployment.json)); no refresh was started.
The subsequent monthly-model correction update and definition readback both failed for
capacity limits. Its final definition must be checked after recovery before retrying
([evidence](production-correction-deployment.json)). No gold rebuild or report deployment
was attempted after that failure.
