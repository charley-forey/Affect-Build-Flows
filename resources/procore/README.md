# Procore

Project management, costing, and field data. **Integration status: ETL built by Rebecca
(API → Fabric Lakehouse), needs review.**

## In this folder

| File | What it is |
|---|---|
| [`endpoints-cheatsheet.md`](endpoints-cheatsheet.md) | The ~50 endpoints relevant to the Monthly Progress Report, extracted and verified from the OpenAPI spec |
| `combined_OAS.json` | Full Procore OpenAPI spec — **gitignored** (52 MB). See below to re-download |

### Re-downloading the spec

The full spec is 52 MB — over GitHub's 50 MB warning threshold and close to the 100 MB hard
limit, so it is not committed. Download from the Procore developer portal:

```
https://developers.procore.com/reference/rest/docs/rest-api-overview
```
(Look for the OpenAPI / Swagger download; the file identifies itself as
`Procore Rest API Documentation` v2.0 with an `x-created-at` timestamp.)

Save to `resources/procore/combined_OAS.json`. The cheatsheet is regenerated from it.

## Official documentation

| Resource | URL |
|---|---|
| Developer portal | https://developers.procore.com |
| REST API overview | https://developers.procore.com/reference/rest/docs/rest-api-overview |
| Authentication | https://developers.procore.com/documentation/oauth-introduction |
| Rate limiting | https://developers.procore.com/documentation/rate-limiting |
| Pagination | https://developers.procore.com/documentation/rest-api-pagination |
| Support site | https://support.procore.com |
| API support | apisupport@procore.com |

## Procore ↔ Sage 100 Contractor connector

**Affect has purchased this but has not rolled it out on a project yet** (Rebecca,
Jul 22 2026). It matters a lot to the integration scope.

| Resource | URL |
|---|---|
| Connector overview | https://support.procore.com/products/online/user-guide/company-level/erp-integrations/sage-100 |
| About Procore + Sage 100 Contractor | https://support.procore.com/products/online/user-guide/company-level/erp-integrations/sage-100/about-procore-sage-100 |
| **Detailed data mapping** | https://support.procore.com/products/online/user-guide/company-level/erp-integrations/sage-100/detailed-data-mapping |
| Tutorials | https://support.procore.com/products/online/user-guide/company-level/erp-integrations/sage-100/tutorials |
| On-demand sync | https://support.procore.com/products/online/user-guide/company-level/erp-integrations/sage-100/tutorials/perform-an-on-demand-sync-with-sage-100 |

### What syncs, and which way

Verified from Procore's documentation:

| Object | Direction | Notes |
|---|---|---|
| Jobs / Projects | ↔ | Export from Procore or import from Sage |
| Cost Codes | ↔ | Sage list imports as company-level standard codes |
| Budgets | ↔ | One-way after initial setup |
| Vendors / Companies | ↔ | Creatable in either system |
| Commitments | Procore → Sage | *"must always be created in Procore"* |
| Commitment Change Orders | Procore → Sage | Export only |
| Subcontractor Invoices | Procore → Sage | Export only |
| **Job Costs** | **Sage → Procore** | Transaction detail syncs automatically |
| Sub Jobs / Phases | Sage → Procore | Import only |

**Mechanics:** runs through an hh2 client. ~5-minute server sync, ~30-minute Procore poll.
Supports Sage 100 Contractor v20.5+.

**Limitations to know:** no project-specific cost codes, no UOM/quantity syncing, an
accounting-approver role must accept before export.

### Why this matters to the build

If job-cost actuals flow **Sage → Procore** once the connector is live, the Fabric
ingestion may not need a separate Sage job-cost pull at all — Sage narrows to **AR
invoices, cash receipts, retainage, and AR aging**, none of which the connector syncs.

That is a materially smaller P3. See
[`../../powerbi/build-plan.md`](../../powerbi/build-plan.md) and open question #4 in
[`../../analysis/excel-tracker/defects-and-questions.md`](../../analysis/excel-tracker/defects-and-questions.md).

## Engagement notes

**What the Excel tracker needs from Procore.** Roughly 30% of the Monthly Progress Report
maps to Procore data — RFIs, submittals, observations, punch list, incidents, manpower,
budget/forecast, change orders, commitments. Full mapping in
[`../../powerbi/source-mapping.md`](../../powerbi/source-mapping.md).

**Highest-value quick win:** `SUBMITTALS & RFI` — one small Excel table, feeding the
workbook's only chart, fully derivable from four endpoints. Good first pipeline to prove
end to end.

**Biggest hand-entry elimination:** the Quality tab. `avg days past due`, `avg days to
close`, and the "main offenders" ranking are **all typed in by hand** today and are all
computable from observation and punch-item timestamps.

## Open questions

1. **Which grant type does the existing ETL use?** A user-based OAuth token expires and
   will break the pipeline. Client-credentials / installation auth is what unattended ETL
   needs.
2. **Where do critical-path milestones live?** The spec has **no `milestone` path** —
   `/rest/v1.0/projects/{project_id}/schedule` returns metadata and tasks. Affect is also
   evaluating Outbuild. This determines whether `fct_Milestone` has a source at all.
3. **What defines "critical"** for the workbook's "Open Critical RFIs / Submittals"?
   `/rfis/filter_options/priority` is the likely candidate.
4. **Which incident types count as "recordable"?** Procore separates injuries, near misses,
   property damage, and environmental.
5. **Does Affect bill owners through Procore?** If so,
   `/prime_contracts/{id}/payment_applications` already holds billing data the workbook
   currently sources from Sage — which would shrink the Sage work further.
6. **Is the existing ETL incremental?** `filters[updated_at]` is available on most list
   endpoints. Full refreshes stop scaling as the portfolio grows.
7. **Do Procore cost codes reconcile with Sage cost codes?** Blocking for budget analysis.

## Gotchas

- **v2.0 requires the `Procore-Company-Id` header.** v1.0 generally takes `company_id` in
  the path or query. Mixing them is the most common cause of an unexplained 403.
- **Version mixing is normal.** RFIs are v1.0, submittals v1.1, commitment contracts v2.0.
  One pipeline will span all three.
- **Rate limits are per-app per-hour.** Honour `Retry-After` on `429`. One throttled call
  without a retry fails the entire nightly run.
- **`per_page` maxes at 1000** on most v1.0 list endpoints. Use the `Total` and `Link`
  response headers rather than assuming a page count.
- **Use the sandbox** for anything that writes.
