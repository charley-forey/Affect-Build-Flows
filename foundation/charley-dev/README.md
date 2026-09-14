# Affect reporting solution (`charley-dev`)

The maintained Fabric implementation for the Monthly Progress Report and Project Quality
Plan, deployed inside the Build workspace's `charley-dev` folder. Two semantic models read
one gold layer. Source completeness and operational reliability are still being validated.

## Current state — September 14, 2026

- Actual production-file DQ replay: 211 rules, 197 passed, 14 warnings, zero blocking or
  execution errors; all 69 table versions stable during the read.
- Snapshot file replay: 21 rows match recomputation; all eight checks pass. Native
  inspection lineage conserves 26 headers and 705 items with exact compound identities.
- Production data exposes two defects: observation averages include closed punch items,
  and 14 financial-period rows make unknown originals appear numeric. Source corrections
  and regression tests are present; the capacity-limited model update/readback failed.
- Project-source coverage, candidate fingerprint/snapshot gates and atomic snapshot
  replacement are improved in source. Their live data/runtime validation remains pending.
- The hardened publication notebook definition is deployed and matches readback. It has
  not been executed. Both models previously accepted automatic update OFF; browser
  confirmation and a successful scheduled publication remain unverified.
- PDF render validation fails on pages 6–11. All 17 manual registers remain empty;
  unmatched source records and business mappings remain explicit gaps.

These are dated results, not a claim of complete data coverage or current availability.
The file checks do not execute the Power BI engine or prove a common upstream source batch.
See [measured status](_docs/build-status.md), the [validation record](_docs/validation-and-development-plan.md),
and the three [lineage](_docs/production-lineage-audit.md), [report](_docs/production-report-audit.md)
and [release](_docs/production-release-audit.md) audits.

## Data flow and boundaries

```text
Procore / Sage / Outbuild / manual registers
  -> bronze inputs and audit fields
  -> silver typing, validation and rejects
  -> gold facts, dimensions and gap register
  -> quality gate and snapshot capture
  -> controlled model refresh
  -> Monthly Progress Report / Project Quality Plan
```

Raw API payloads are retained where the ingestion contract provides them. Manual inputs
use a flat schema. Tests reconcile accepted, rejected and duplicate rows at defined grains.
This is not a universal no-loss guarantee: for example, unlinked Outbuild critical
activities remain in silver but are excluded from the milestone fact and flagged by DQ.
Missing inputs and mappings must be disclosed, not presented as zero or guessed.

Deployment scripts create and update owned items in `charley-dev`; other workspace items
are outside the write scope. The validation lakehouse is separate from production data,
but **shares compute capacity**. This is data isolation, not performance isolation.

## Layout

| Directory | Purpose |
|---|---|
| `00-platform/` | Shared ingestion, secret access and validation code |
| `01-ingestion/` | Source and manual intake definitions |
| `02-transformation/` | Silver/gold SQL, seeds, snapshots and DQ rules |
| `03-lakehouses/` | Lakehouse definitions |
| `04-semantic_models/` | Monthly and quality-plan model definitions |
| `05-reports/` | Report definitions: 12 monthly pages and 9 QC pages |
| `06-orchestration/` | Pipeline definition and scheduling material |
| `_local/` | Generators, deployment tools and offline tests |
| `_docs/` | Evidence, data dictionary, operating guidance and dated history |

## Validate and operate

```bash
python -m pip install -r foundation/charley-dev/_local/requirements-ci.txt
python foundation/charley-dev/_local/run_tests.py
```

Offline checks exercise production SQL with compatibility helpers; they do not substitute
for Fabric execution, independent source reconciliation, or visual verification.
Follow the [operations runbook](_docs/operations-runbook.md) for deployment and recovery,
and [capacity guidance](_docs/capacity-operations.md) before live validation. A successful
job status without matching gate evidence is not a pass. Updating a model definition alone
does not prove its tables are queryable: verify its controlled refresh and live checks.

Credentials belong in the approved secret store, never source control. Local raw exports
and deployment backups are excluded from public Git. Start with the
[data dictionary](_docs/data-dictionary.md) for field mappings and the
[validation record](_docs/validation-and-development-plan.md) for business decisions still needed.
