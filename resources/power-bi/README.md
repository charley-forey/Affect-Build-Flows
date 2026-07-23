# Power BI

Reporting layer. **Integration status: in use — currently running live SQL queries against
Sage 100 Contractor.**

## Documentation

All links verified to resolve, Jul 2026.

| Topic | URL |
|---|---|
| DAX function reference | https://learn.microsoft.com/en-us/dax/ |
| **Star schema guidance** | https://learn.microsoft.com/en-us/power-bi/guidance/star-schema |
| Report themes (the `theme.json` schema) | https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-report-themes |
| Incremental refresh | https://learn.microsoft.com/en-us/power-bi/connect-data/incremental-refresh-overview |
| Row-level security | https://learn.microsoft.com/en-us/power-bi/enterprise/service-admin-rls |
| On-premises data gateway | https://learn.microsoft.com/en-us/power-bi/connect-data/service-gateway-onprem |

Community references worth having: DAX Guide (`dax.guide`), SQLBI's articles on time
intelligence, and Tabular Editor / DAX Studio for model inspection and performance work.

## Build assets in this repo

Everything needed to build the report lives in [`../../powerbi/`](../../powerbi/):

| File | What it is |
|---|---|
| `semantic-model.md` | Star schema — facts, dimensions, grain, keys, relationships |
| `measures.dax` | Runnable DAX for every KPI, traceable to the Excel cell it replaces |
| `report-spec.md` | Page layout, visuals, number formats, accessibility rules |
| `theme.json` | Validated Power BI theme — drop into Desktop via *View → Themes → Browse* |
| `source-mapping.md` | Every field → Procore endpoint / Sage table / manual input |
| `manual-input-template.md` | Spec for the SharePoint input workbook |
| `build-plan.md` | Phased delivery, estimates, reconciliation gate |

## Theme notes

`theme.json` separates two palettes that the Excel workbook conflates:

- **Status (RAG)** — reserved. Never used for series identity.
- **Categorical** — series identity only. Never uses the RAG colors.

Two of Affect's three RAG steps were corrected after measuring them:

| | Workbook | Report | Measured contrast (light surface) |
|---|---|---|---|
| Amber | `#FFD800` | `#B26A00` | **1.36:1** → passes 3:1 |
| Green | `#01AF00` | `#1B7F3B` | **2.87:1** → passes 3:1 |
| Red | `#DB1918` | `#C62828` | adjusted for consistency |

The original amber is effectively invisible on white. That is a plausible reason "Watch"
status gets overlooked in the current report — worth mentioning to Affect.

**Red/amber/green cannot be made colorblind-safe as color alone** (measured red↔green
separation is ΔE 7.1 under deuteranopia, below the ΔE 8 floor, and no re-stepping fixes
it — the deficiency is in the hue pair). The mitigation is an **icon or label beside every
status color, always**. Affect's workbook already does this with emoji, so this is their
existing convention made explicit rather than a new constraint.

Full rationale: [`../../powerbi/report-spec.md`](../../powerbi/report-spec.md).

## Practices for this build

**Star schema, no snowflaking.** Facts join to dimensions directly; dimensions join
nothing. See the Microsoft guidance link above — it is short and worth Rebecca reading it.

**No bidirectional filters.** They create ambiguity and hurt performance. Use
`CROSSFILTER` inside a specific measure if a case genuinely needs it.

**No dual-axis charts.** Two measures at different scales get two charts, small multiples,
or indexing to a common base — never two y-scales on one plot.

**Mark `dim_Date` as a date table.** Time intelligence silently misbehaves otherwise. This
single step is what replaces the workbook's entire `INDEX/MATCH` + `AU4` mechanic.

**Measures in a dedicated `_Measures` table** so they sort to the top of the field list.

**`DIVIDE()` over `/`.** Returns blank instead of erroring on a zero denominator — which
is exactly the failure the Excel's month-over-month tiles hit on any new project.

**Incremental refresh** once fact volumes justify it. Not day one.

## Current state to unwind

Power BI queries Sage **live over SQL today**, bypassing the Lakehouse. That works for one
report and stops working the moment there are several — every report re-queries the
accounting system, there is no shared model, and no single definition of "total billed".

Moving Sage behind the Lakehouse is part of P3 in
[`../../powerbi/build-plan.md`](../../powerbi/build-plan.md). Worth capturing the existing
live queries before they are replaced — they encode business logic that exists nowhere
else in writing.
