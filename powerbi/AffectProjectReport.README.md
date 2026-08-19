# AffectProjectReport.pbip

> **Status — superseded design artifact (2026-08-19).** This local `.pbip` was written in
> July 2026 as the file-based proof of the model: five tables over parquet on disk. The
> platform has since shipped **two** semantic models to Fabric from TMDL in
> `foundation/charley-dev/04-semantic_models/` — *Affect Project Report* (37 tables,
> 99 measures, 45 relationships, Direct Lake) and *Project Quality Plan* (19 tables plus
> `_Measures`, 42 measures, 23 relationships) — driving the *Monthly Progress Report*
> (12 pages) and *Project Quality Plan* (7 pages) reports.
> Current truth: `foundation/charley-dev/_docs/`. Kept as the record of the starting point.

Power BI project format — the model is plain text (TMDL), so it diffs and reviews like
code instead of hiding inside a `.pbix` binary.

⚠️ **This local `.pbip` was never opened in Power BI Desktop.** Desktop is not installed on
the machine it was built on, so its TMDL is written to spec but unverified. That applies to
this file only — the Fabric models above were deployed and reframed from TMDL by
`foundation/charley-dev/_local/deploy_model.py` and are queryable.

## What is in it

| Path | What it is |
|---|---|
| `AffectProjectReport.SemanticModel/definition/tables/` | Five tables — `fct_RfiSubmittal`, `dim_Project`, `dim_Trade`, `dim_Status`, `dim_Date` |
| `.../relationships.tmdl` | Four relationships, all many-to-one, **single** cross-filter direction |
| `.../expressions.tmdl` | `GoldFolder` — the one thing you change per machine |
| `AffectProjectReport.Report/` | An empty page named *Submittals & RFI*, ready for visuals |

The three measures from [`measures.dax`](measures.dax) that apply to this slice are on
`fct_RfiSubmittal`: **Open Critical RFIs**, **Open Critical Submittals**, **Avg RFI Days
Open**. They are copied verbatim, so they stay the client's definitions rather than a
paraphrase.

## First open

1. `python src/procore/run_local.py` — writes the parquet the model reads.
2. Open `AffectProjectReport.pbip` in Power BI Desktop.
3. Set the `GoldFolder` parameter to the absolute path of `.local/gold` if the relative
   default does not resolve.
4. Refresh. Then build the *Submittals & RFI* visuals: `dim_Trade[TradeName]` on the
   axis, the two Open Critical measures as values.

Expected from the current fixtures: **HVAC 2, Electrical 1, Plumbing 1** — matching
[`.local/preview.html`](../src/procore/preview/template.html), which renders the same
gold tables without needing a Power BI licence.

## Moving to Fabric

Replace each table's M partition with the Lakehouse SQL endpoint. **Tables,
relationships and measures do not change** — that is the reason the model is bound to a
parameter rather than to hard-coded paths.

`dim_Date` is a DAX calculated table (`CALENDAR`, 2023-01-01 → 2030-12-31), so it needs
no lakehouse table at all. It is marked as the date table on `[Date]`.
