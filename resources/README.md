# Resources

Curated documentation, links, and reference material for every solution in the Affect
Group stack. One folder per solution.

Links here have been **fetched and verified**, not copied from memory. Where a widely
circulated link is wrong for Affect's situation, that is called out explicitly.

## Index

| Solution | Status in the stack | Folder |
|---|---|---|
| **Procore** | Project management & costing — ETL built, needs review | [`procore/`](procore/) |
| **Sage 100 Contractor** | Accounting, AR/AP, payroll — read-only SQL, queried live from Power BI | [`sage-100-contractor/`](sage-100-contractor/) |
| **Microsoft Fabric** | Data warehouse (Lakehouse) — live, built by Rebecca | [`microsoft-fabric/`](microsoft-fabric/) |
| **Power BI** | Reporting — in use. **The built report, page by page:** [`power-bi/monthly-progress-report/`](power-bi/monthly-progress-report/) | [`power-bi/`](power-bi/) |
| **Power Automate** | Workflow automation — planned (D6 payments, D7 lien waivers) | [`power-automate/`](power-automate/) |
| **Outbuild** | Scheduling — not integrated | [`outbuild/`](outbuild/) |
| **Ramp** | Vendor payments — not integrated | [`ramp/`](ramp/) |
| **ADP** | Payroll — not integrated | [`adp/`](adp/) |

## Two things worth knowing before the deep dive

**1. The Sage documentation link in circulation is for the wrong product.**
`help-sage100.na.sage.com/2023/FLOR/` is the File Layouts and Object Reference for
**Sage 100 ERP** (Standard / Advanced / Premium). Affect runs **Sage 100 *Contractor***
— a different product with a different schema. Correct references are in
[`sage-100-contractor/`](sage-100-contractor/).

**2. The Procore ↔ Sage 100 Contractor connector changes the integration scope.**
Affect has purchased it but not rolled it out. Once live, job costs flow Sage → Procore,
which may remove the need for a separate Sage job-cost pull entirely. Sync directions are
documented in [`procore/README.md`](procore/README.md).

## Convention

Each folder has a `README.md` with:
- What the tool does in Affect's stack and its current integration status
- Verified official documentation links
- Notes and gotchas specific to this engagement
- Open questions

Large generated artifacts (API specs, schema dumps) are **gitignored** and re-derivable —
each README says how. Extracted cheatsheets are committed because they are small and are
what actually gets read.

Related: [`../analysis/excel-tracker/`](../analysis/excel-tracker/) (assessment of the
current reporting template) · [`../powerbi/`](../powerbi/) (the build kit) ·
[`power-bi/monthly-progress-report/`](power-bi/monthly-progress-report/) (**what the finished
dashboard looks like** — all ten pages as screenshots).
