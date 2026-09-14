# Affect reporting and data platform

Microsoft Fabric implementation for Affect Group's monthly project reporting and Project
Quality Plan. The maintained solution is in [foundation/charley-dev](foundation/charley-dev/README.md).
It brings Procore, Sage and Outbuild data through bronze, silver and gold layers into two
Power BI models and reports. Manual registers provide information that source systems do
not supply.

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
