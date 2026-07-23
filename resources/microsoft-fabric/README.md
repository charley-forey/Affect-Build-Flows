# Microsoft Fabric

The data warehouse. **Integration status: live — Lakehouse built by Rebecca. Procore ETL
lands here; Sage currently bypasses it.**

## Documentation

All links verified to resolve, Jul 2026.

| Topic | URL |
|---|---|
| Lakehouse overview | https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-overview |
| Lakehouse tutorial (end to end) | https://learn.microsoft.com/en-us/fabric/data-engineering/tutorial-lakehouse-introduction |
| Data Factory / pipelines | https://learn.microsoft.com/en-us/fabric/data-factory/data-factory-overview |
| Direct Lake mode | https://learn.microsoft.com/en-us/fabric/fundamentals/direct-lake-overview |
| Deployment pipelines (CI/CD) | https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/intro-to-deployment-pipelines |
| On-premises data gateway | https://learn.microsoft.com/en-us/power-bi/connect-data/service-gateway-onprem |

## Architecture — what to confirm on the deep dive

Current understanding, to be validated:

```
Procore  ──API──▶  ETL (script)  ──▶  Fabric Lakehouse  ──▶  Power BI
Sage 100 ─────────── live SQL query ──────────────────────▶  Power BI   ⚠ bypasses Lakehouse
```

**Target:**

```
Procore   ──API──────▶┐
Sage 100  ──SQL──────▶├──▶ Lakehouse (bronze → silver → gold) ──▶ Semantic model ──▶ Power BI
SharePoint (manual) ─▶┘
```

Questions to answer while Rebecca screen-shares:

- Fabric **capacity / SKU**, workspace structure, who administers it
- Lakehouse vs Warehouse — which artifacts exist? Any medallion structure today?
- **How is the Procore script hosted and scheduled** — Fabric notebook, Data Pipeline, or
  Azure Function? What language?
- Refresh cadence — actual vs desired
- Monitoring, failure alerting, retry logic — anything?
- **How are API credentials stored?** (Key Vault, or in the notebook?)
- Is there any dev/test/prod separation, or one workspace?

## Recommendations for this build

**Medallion layout.** Even at this size it pays for itself:

| Layer | Contents |
|---|---|
| `bronze` | Raw API responses and SQL extracts, unmodified, with an ingestion timestamp |
| `silver` | Typed, trimmed, validated, deduplicated. Rejected rows logged, not dropped |
| `gold` | The `fct_*` / `dim_*` / `man_*` tables from [`../../powerbi/semantic-model.md`](../../powerbi/semantic-model.md) |

Keeping bronze raw means a transform bug is a re-run, not a re-extract.

**The validation gate belongs at silver.** Unmatched status codes, unmatched trades,
missing project keys, dates that fail sanity checks — reject the row and log it, then
surface the log on the report's hidden Data Quality page. The Excel had no equivalent, and
that is exactly how a `$200,000,000` buyout figure against a `$9.1M` contract reached a
leadership report unchallenged.

**Secrets in Azure Key Vault**, referenced from the pipeline. Not in notebook cells.

**Storage mode: Import.** Volume is tiny — one project produces ~30 monthly rows per fact.
Revisit Direct Lake once the portfolio grows and the Lakehouse tables are settled.

**Deployment pipelines** once there is more than one report worth protecting. Not day one.

## Gateway dependency

If the Sage SQL Server is on-premises, Fabric needs an **on-premises data gateway** to
reach it. That is an install plus a network conversation plus, potentially, procurement.

**Identify this in P0.** It is the kind of dependency that quietly adds two weeks if it
surfaces late.
