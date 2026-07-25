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

## AI-assisted access — Fabric MCP server

[`ms-fabric-mcp-server`](https://pypi.org/project/ms-fabric-mcp-server/) exposes Fabric
operations (workspaces, items, notebooks, lakehouse files, pipelines, semantic models, and
SQL) as tools Claude Code can call directly. Configured for this repo in
[`../../.mcp.json`](../../.mcp.json).

**Why it matters here.** It reads the environment instead of relying on screen-share — on
the Jul 23 review Rebecca ran out of time before showing the schema. With access we can:

- `list_notebooks` / `get_notebook_definition` — read the Procore ETL as-is (D2)
- `get_semantic_model_details` / `execute_dax_query` — inspect the project→fact relationships
- `execute_sql_query` against the Lakehouse SQL endpoint — **test the vendor ↔ commitment ↔
  cost-code joins that are D4's open problem** before committing them to the model

**Auth.** `DefaultAzureCredential` — a plain `az login` with an account that has Fabric
access. No secrets in the repo. **Blocked until the NDA + Fabric access land** (pending, see
D1 log), so the config is inert today and works the moment access is granted.

**Guardrails.** Work read-first (`list_*`, `get_*`, `execute_sql_query`, `execute_dax_query`).
The package also ships destructive tools (`delete_item`, `delete_lakehouse_file`, arbitrary
Spark via Livy) and its maintainer flags it dev-only — so point it at a **non-production /
dev workspace** and every tool call is reviewed before it runs (Claude Code prompts per
call). The `[sql]` extra needs the Microsoft ODBC Driver for SQL Server (18 or 17) installed
locally; without it the server still starts with the 57 non-SQL tools.

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
