# Affect reporting and data platform

Microsoft Fabric implementation for Affect Group's monthly project reporting and Project
Quality Plan. The maintained solution is in [foundation/charley-dev](foundation/charley-dev/README.md).
It brings Procore, Sage and Outbuild data through bronze, silver and gold layers into two
Power BI models and reports. Manual registers provide information that source systems do
not supply.

## Current state — October 5, 2026

- **Nightly pipeline running again.** The `AffectKeyVault` subscription is enabled and its
  secrets read. The nightly runs failed 2026-09-30 to 10-02 at Ingest Sage because the
  on-premises gateway was offline. Affect IT set the gateway service to automatic and
  restarted it. The 10-03 and 10-04 runs completed, and the Sage connection was last used
  2026-10-04 06:01 UTC.
- **Sage outages no longer freeze Procore reporting.** Since 2026-10-05, Bronze To Silver runs
  once Ingest Sage *completes*, not only when it succeeds. Silver rebuilds from the last good
  Sage bronze, and the run still ends Failed so the outage stays visible.
- **Cost codes.** The new list now comes from the client's *COST CODE_WBS MASTER* (2026-09-30):
  291 codes uploaded to Sage, matching the Sage 6-5 export except three division headers.
  It adds 13160.010 and six other codes that were dropped from the first Sage upload. Old Sage
  codes map through workbook v1. Pre-2026 Procore codes map through the client's legacy map.
  The notebooks were deployed 2026-10-05 and the first production build was triggered
  2026-10-05 01:00 UTC. Until that build, production gold had no cost-code mapping. The
  model must be redeployed after the build (`deploy_model.py --apply`, then
  `deploy_publish.py --apply --run`) to expose the mapping columns. See the
  [solution guide](foundation/charley-dev/_docs/solution-guide.md).
- **SharePoint.** Both sites and all 18 lists are ready; `CD Projects` updated (26-056 added).
  `CD_Manual_Ingest` is signed in to both sites (reporting site and `AFFECTBUILD1`).
  Not yet in the nightly pipeline. Now that Key Vault is restored, it can be added.

## Verified state — September 14, 2026

**Production is not fully certified.** Read-only validation of actual production Delta
files reproduced all 211 quality rules: 197 passed, 14 warnings, no blocking failures or
execution errors. All 69 table versions stayed unchanged during the check. The 21 saved
snapshot rows also match recomputed values. These checks do not establish source completeness.

A deeper audit found calculation defects that the existing rules did not catch: punch
items contaminated the observation closure average, and missing original contracts could
appear as numeric current contracts. Corrections and regression tests are in source.
Fabric rejected the model update and subsequent readback for capacity limits, so those
corrections are **not verified live**. Gold and snapshot changes await controlled deployment.
The hardened publication notebook definition was deployed and read back, but not executed.
All 27 offline regression suites and generator checks pass.

The PDF export contains capacity errors on pages 6–11. Browser verification, a successful
scheduled publication, source mappings and empty manual registers remain unresolved.
See the [validation record](foundation/charley-dev/_docs/validation-and-development-plan.md)
for tested scope, deployment evidence and remaining acceptance criteria. A green CI run or
a completed export is not production certification.

## Start here

- [Current evidence, limits and next steps](foundation/charley-dev/_docs/validation-and-development-plan.md)
- [Measured build status](foundation/charley-dev/_docs/build-status.md)
- [Operations and deployment](foundation/charley-dev/_docs/operations-runbook.md)
- [Capacity limits and workload guidance](foundation/charley-dev/_docs/capacity-operations.md)
- [Generated data dictionary and lineage](foundation/charley-dev/_docs/data-dictionary.md)

Unmapped accounting and schedule records, stale insurance records and empty manual
registers remain explicit gaps. Unknown values must stay unknown; business mappings and
policy decisions require evidence and an accountable owner.

## Repository layout

| Path | Purpose |
|---|---|
| `foundation/charley-dev/` | Maintained implementation, tests, deployment scripts and evidence |
| `foundation/` outside `charley-dev/` | Historical workspace backup; not the current deployment inventory |
| `powerbi/` | Earlier report design and source-mapping material |
| `src/` | Source integration code and supporting tools |
| `resources/` and `analysis/` | Reference material and dated assessments |

Older documents and exports describe their recorded dates. Use the current status links
above for release decisions. This README intentionally omits personal contact details,
credentials and commercial engagement terms. Raw client exports and local deployment
backups must not be added to this public repository.

## Offline validation

```bash
python -m pip install -r foundation/charley-dev/_local/requirements-ci.txt
python foundation/charley-dev/_local/run_tests.py
```

See the operations runbook before any live run. Validation shares Fabric capacity with
production; do not repeatedly rebuild or run broad query sweeps during capacity rejection.
