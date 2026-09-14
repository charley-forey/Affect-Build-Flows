# Production lineage audit — 2026-09-14

Status: local SQL review and synthetic execution complete for the changes below. **Deployment and live validation are pending.** No live Fabric compute was requested by this audit. Passing fixtures do not certify the source population or the deployed report.

## Corrected defects

| Priority | Finding and evidence | Correction and verification |
| --- | --- | --- |
| High | The project spine observed only five fact sources. A synthetic RFI whose exact project ID was absent from the project list produced one source record but no dimension member. Native inspection, field operations, billing and manual-only projects had the same omission. Existing orphan rules could block these legitimate records. | `02-transformation/sql/gold/10_dim_project.sql:36` now reads `sv_observed_projects`. Both source adapters define that union using their actual available Procore project identities; Sage job IDs are not substituted. Tests isolate each declared source, keep its exact identity and check deduplication. |
| High | `02-transformation/sql/gold/30_fct_financialperiod.sql` converted a missing original contract to zero. The existing unmatched-project fixture produced `CurrentContract = 0` despite having no contract source. Approved changes alone could also be represented as the complete contract. | The calculation now preserves NULL through addition. Tests cover absent original with approved changes, absent original on unmatched AR, and a known zero original which remains calculable. No stored column or model type changed. |

Source adapters: [legacy source union](../02-transformation/sql/silver/00_source_views.sql), [owned source union](../02-transformation/sql/silver/01_source_views_cd.sql). Regression checks: [test_gold.py](../_local/tests/test_gold.py). The offline fixture imports the actual owned union rather than maintaining a second list.

## Remaining acceptance gaps

- **Source deletions and historical scope:** `00-platform/lib/fabric_common.py:204` builds an update/insert merge, with no deletion reconciliation. A completed full pull is not proof that records no longer present upstream have been removed from reporting. Active-project scope and deletion-event semantics remain unverified; do not delete unseen records until a complete authorized source snapshot and scope are established.
- **Snapshot replacement corrected in source:** a single MERGE now replaces the selected date atomically, including removal of obsolete same-date projects and preservation of other dates. Local tests cover interrupted/failed statement behavior; Fabric runtime execution remains unverified. Existing post-write validation cleanup can still remove a failed capture, so this is not a full historical rollback guarantee. The hardened publication guard now blocks a failed snapshot instead of allowing it to frame readers. See the release audit.
- **Source completeness is distinct from row conservation:** bidirectional EXCEPT ALL rules establish that selected silver records reach gold, with intentional exclusions surfaced separately. They do not prove that an upstream API supplied every accessible or historically relevant source record. Retain endpoint/scope/page evidence and compare against authoritative source totals where available.
- **Business associations:** reviewed Sage/Procore mappings, Outbuild attribution and empty manual registers remain external evidence gaps. No mapping was inferred or manual value invented in this audit.
- **Publication:** refresh success, a passing local suite, and a job marked Completed do not establish that both production reports expose the same verified release. The unfinished run-specific candidate certificate, scheduled cycle and rendered report errors must be resolved separately.

## Local validation

`python _local/tests/test_gold.py`: 96 checks passed, including per-source isolation and unknown-contract regressions.

`python _local/tests/test_end_to_end.py`: 55 owned physical source adapters, 61 model table contracts and 211 executable quality rules; zero blocking failures on the clean fixture. The derived project union adds no physical source dependency or new model column.

These are synthetic checks. The production impact and final displayed values must be compared after controlled deployment and refresh; capacity recovery must precede further compute.

## Production file evidence

[Production lineage file evidence](production-lineage-file-evidence.json) is produced by `python _local/validate_lineage_files.py`. It reads individual Delta table versions through OneLake and evaluates identity coverage locally; it does not invoke Spark, a SQL endpoint or a model query. The Outbuild project adapter is evaluated with its actual DISTINCT and non-null Outbuild-ID predicate, so activity counts are not mislabeled as project counts.

The gate fails on read errors, versions changing during inspection, dimension null/duplicate keys, missing non-null project identities, native inspection key differences, or null/duplicate inspection identities. Null source project rows are separately visible as unresolved attribution; a PASS for the checked identity mappings does not certify those rows or complete source scope. Raw source IDs and client names are not stored in this artifact.
