# Role: Dataflows and ingestion config

You own Dataflow Gen2 artifacts and the config-driven ingestion registries.

## The principle: config, not notebooks

`01-ingestion/Procore/procore_extract.py` implements auth, pagination, the v2.0
`Procore-Company-Id` header rule, retry and watermarking **generically**. Adding an endpoint
is a YAML entry in `config/endpoints.yml`, not a new notebook. That replaces ~25
near-identical notebooks in the existing foundation and is the teachable upgrade for the
client's own developer.

`00-platform/lib/procore_scope.py` adds `scope: parent` alongside the extractor rather than
forking it. `resolution_order()` uses Kahn's algorithm — which doubles as the cycle check —
and `validate_registry()` catches duplicate names, duplicate target tables, missing parents
and cycles at load time rather than mid-extraction.

## Procore registry

**44 endpoints** registered, every path cited to a line in
`resources/procore/endpoints-cheatsheet.md`. (It was 36 when this was written, then 42; the
Project Quality Plan work added `checklist_lists` and `checklist_list_items`.) Only a
handful declare `incremental: filters[updated_at]` — 7 of the original 36, and the count has
not been re-checked since; the rest are full pulls because Procore does not document a
reliable updated-at filter for them. **RFIs and submittals are
deliberately excluded from incremental** — they document `created_at` only, so an incremental
pull would silently miss status changes, which is exactly the data the report needs.

Procore throttles per hour and looping every project every run is heavy: honour `Retry-After`
on 429, and keep reference data on a slower cadence than active-project data.

## Sage — the current build

`CD_Sage_Ingest.Dataflow` follows `foundation/01-ingestion/Sage/Build_Sage_Test.Dataflow/mashup.pq`:
same `Sql.Database("NC-AFFECT-1\SAGE100CON","Affect Group")` source, on-prem gateway.

Tables: `acpinv`, `acrinv`, `acppmt`, `acrpmt`, `actpay`, `actrec`, **plus `apivln` and
`arivln`**. The line tables are the point. Two facts drive it:

- `jobnum` is a foreign key to `actrec.recnum`, not a readable job code — so
  `dim_projects_procoreXsage` *is* the Procore↔Sage join, not a convenience.
- **Retainage is a trap.** The `retain` column exists on the invoice header and is **zero
  across all 940 invoices** — verified, commit `db0d11e`. It is not held there for this
  company. Source it from `arivln`, `actrec.retain`, or progress billing, or the report
  silently shows $0 retainage and nobody notices until a client asks.

Build it and commit it. Binding to the on-prem gateway needs Affect, so it ships ready
rather than blocked — do not treat the missing gateway as a reason to defer the work.
**Done:** `CD_Sage_Ingest` is deployed to the workspace and still waits on the gateway
*Can use* grant.

## Outbuild

16 endpoints (Activities, ActivityTags, Companies, Projects, RFV-Types, RFVTasks, RFVs,
Roadblock-Types, RoadblockTasks, Roadblocks, Schedule-Impact-Requests, Tags, TaskTags, Tasks,
User, Weekly-Commitments) per `resources/outbuild/api/DatahubAPI/`. Auth is a token in a
header — that is **one auth mode added to the shared extractor, not a fork of it**.

Outbuild is the only source of milestone data anywhere in the estate: Procore's OAS has no
milestone endpoint. `fct_Milestone` has no other path to real numbers.
`OUTBUILD_API_TOKEN` is not available yet; build against the documented schema and let the
live run wait.
