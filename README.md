# Affect reporting and data platform

Microsoft Fabric implementation for Affect Group's monthly project reporting and Project
Quality Plan. The maintained solution is in [foundation/charley-dev](foundation/charley-dev/README.md).
It brings Procore, Sage and Outbuild data through bronze, silver and gold layers into two
Power BI models and reports. Manual registers provide information that source systems do
not supply.

## Verified state — September 14, 2026

Production model fixes and the guarded manual-register schema migration are deployed.
The monthly model's 130 measures evaluate and its 18 checks pass; all 48 quality-plan
measures evaluate. The production quality gate recorded 211 rules: 197 passed, 14 warnings,
and no blocking violations. These checks do not establish complete source coverage.

All 21 offline suites and generator checks passed in
[GitHub CI](https://github.com/charley-forey/Affect-Build-Flows/actions/runs/34861048213).
A commit or successful CI run is not proof of a production deployment.

**The platform is not fully certified.** Fabric rejected additional queries because of
capacity limits. The expanded candidate lacks its final run-specific gate evidence, the
PDF export was unfinished at the last check, and a successful scheduled cycle remains
unverified. Both models accepted automatic updates being disabled; browser confirmation
of that setting is outstanding. These are dated observations, not a live health monitor.

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
