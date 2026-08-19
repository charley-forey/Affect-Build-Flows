# Procore ingestion

**Live against Affect's production tenant** (`api.procore.com`, Affect Build LLC,
19 active projects) as of 2026-08-02. Registry re-counted 2026-08-19: **44 endpoints** —
[`endpoint-inventory.md`](endpoint-inventory.md) is generated from it, and
[`build-status.md`](build-status.md) is where that count is maintained.

The pipeline is split in two, and the split is deliberate:

```
.env (local)  ->  extract_procore_local.py  ->  Procore REST
                                                     |
                              CD_Bronze_Lakehouse/Files/_landing/<batch>/*.jsonl
                                                     |
                                    cd_05_land_to_bronze   (no credentials)
                                                     v
                                          cd_bronze_procore_*  (Delta, MERGE)
```

## Why it is split

`cd_01_extract_procore` is the real, scheduled ingestion and it runs inside Fabric. It needs
a Procore secret, and the only safe way to give a Fabric notebook a secret is Key Vault.
Every alternative inside Fabric — a Spark property, a workspace environment variable, a
notebook cell — is plaintext-readable by any workspace member. That is exactly finding **F1**
in `security-findings.md`, and reproducing the finding we just reported would be an odd way
to fix it.

So: the half that needs a secret runs where the secret already lives, and the half that needs
Spark runs in Fabric, where it needs no secret at all. Nothing reaches the workspace except
data.

**This is a bridge, not the destination.** As of 2026-08-19 both the Azure subscription and
the vault (`OneLake`) exist — what is left is **one role assignment**, "Key Vault Secrets
Officer" on that vault, because it is RBAC-mode and our identity holds only resource-group
Contributor. Once it lands: `setup_keyvault.py --apply`, point `PROCORE_KEYVAULT_URL` at the
vault, and `cd_01_extract_procore` takes over on a schedule. `cd_05_land_to_bronze` keeps
working either way, because all it ever does is read files that are already there. Full
sequence in [`keyvault-runbook.md`](keyvault-runbook.md).

## Running it

```bash
cd foundation/charley-dev/_local
python extract_procore_local.py --list      # the 44-endpoint registry, in resolution order
python extract_procore_local.py --probe     # auth + project count, no extraction
python extract_procore_local.py             # full run, dry (nothing lands)
python extract_procore_local.py --apply     # full run, lands in OneLake
python deploy_landing.py --apply            # merge the files into cd_bronze_* Delta
```

The extractor itself is **not** reimplemented locally: `src/procore/procore_extract.py` is
imported whole — the same module `deploy_ingestion.py` uploads to `Files/lib/`. Auth,
pagination, retry and the bronze row shape are shared, so the local runner cannot drift from
what Fabric will eventually do.

## Credentials

Three values, from a Procore **Data Connector App** using the **client-credentials** grant:
`PROCORE_CLIENT_ID`, `PROCORE_CLIENT_SECRET`, `PROCORE_COMPANY_ID` (the last is an org
identifier, not a secret). `PROCORE_BASE_URL` defaults to the sandbox in the shared
extractor, so the local runner forces `https://api.procore.com` — a silent sandbox run would
land a convincing set of empty tables.

**Client credentials, not a user token.** A user-based (`authorization_code`) token expires
and breaks the pipeline at the worst moment — flagged in
`resources/procore/endpoints-cheatsheet.md:196-200` as the most common Procore ETL failure
mode.

## Three defects found by running it for real

None of these were visible without live credentials. Each cost endpoints.

### 1. `Procore-Company-Id` is required at every API version

The documented rule — and the cheatsheet at line 41 — says only v2.0+ needs this header,
because v1.x takes the company in the path or query. Affect's tenant disagrees. Same token,
same project, v1.0 RFIs:

| Request | Result |
|---|---|
| header + `per_page=1000` | 200, 32 rows |
| header, no params | 200, 32 rows |
| **no header** + `per_page=1000` | **404** |
| **no header**, no params | **404** |

Identical on v1.1 submittals, v1.0 incidents and v1.0 manpower_logs.

The failure is a **404, not a 403** — it reads as "this project has no RFI tool", not "you
forgot a header". That is why the first full run lost 28 of 36 endpoints and looked like a
permissions problem. `procore_scope.Endpoint.needs_company_header` now returns `True`
unconditionally, with an assertion pinning it so the documented-but-wrong rule cannot creep
back in.

### 2. Ten endpoints take `project_id` as a query parameter

They were declared `scope: project` with a company-shaped path, so `expand_paths` had no
`{project_id}` to substitute and dropped the project entirely — Procore then 400s because it
cannot tell which project is meant. Fixed in `endpoints.yml` by putting the placeholder in
the query string: `/rest/v1.0/commitments?project_id={project_id}`.

`cost_codes` was additionally mis-scoped as `company`. The company form 400s; the project
form returns **5,433 rows**.

### 3. One project's missing tool must not fail the endpoint

Across 19 projects not every tool is enabled everywhere, and a 403/404 on one project was
aborting the whole endpoint. It now skips that project and reports the count. Losing 18
projects' data to the 19th is not a useful failure mode.

## What comes back

| Endpoint | Rows | Note |
|---|---:|---|
| `cost_codes` | 5,433 | after the re-scope; 4,765 in the existing warehouse |
| `submittals` | 2,245 | existing warehouse has 2,242 |
| `punch_items` | 1,469 | not in the existing warehouse |
| `vendors` | 1,098 | existing warehouse has 1,075 |
| `potential_change_orders` | 1,050 | not in the existing warehouse |
| `observations` | 850 | not in the existing warehouse |
| `rfis` | 616 | **not in the existing warehouse at all** |
| `requisitions` | 473 | existing warehouse has 556 |
| `direct_costs` | 418 | |
| `project_vendors` | 393 | |
| `commitments` | 298 | existing warehouse has 264 |
| `work_order_contracts` | 189 | |
| `budget_views` | 100 | feeds `budget_detail_rows` |
| `rfi_statuses` / `rfi_priorities` | 95 / 76 | answers open question 2, "which RFIs are critical" |
| `observation_types` | 28 | |
| `projects` | 19 | existing warehouse has 18 |
| `budget` / `manpower_daily_totals` | 19 / 19 | |
| `incident_severity_levels` | 5 | |
| `incidents` | 3 | |

RFIs are the notable one: no RFI data exists anywhere in the current warehouse, so the RFI
half of the workbook's only chart has never been automated.

**One parsing defect over this payload is worth knowing about**, because it survived into a
live report. `20_fieldops_silver.sql` read Procore's `$.trade` as an **object** rather than
taking `$.trade.name`, so the silver column held `{"id":…,"name":"Electrical",…}`. It parses,
it is not NULL, and nothing that checks for NULL catches it. Consequences: every `fct_Qc*`
trade join failed (631 of 850 NCRs), and `fct_QualityItem.Trade` on the live Monthly Progress
Report showed raw JSON. Fixed 2026-08-19 — detail in
[`build-status.md`](build-status.md#two-structural-gotchas-found-on-the-2026-08-19-deploy).

**Two endpoints were added by the PQP work:** `checklist_lists`
(`/rest/v1.0/checklist/lists`) and `checklist_list_items`, parent-scoped on it. Procore
Inspections is a per-project instance of a checklist template, which is exactly what the QA/QC
workbook's 26 trade sheets are — landed deliberately so the comparison can be made against
real data. Nothing in gold reads it yet.

The row counts that differ from the existing warehouse are worth a look rather than a shrug —
they are either our extraction or theirs, and either is useful to know. That comparison is
the L2 parity check and a genuinely useful review artifact for D2.

## Still failing, and why

| Endpoint | Status | Cause |
|---|---|---|
| `punch_item_types` | 403 | Permission — the service account cannot read company-level punch item types. **Nothing downstream depends on it**: silver derives the punch class from `punch_item_type.name` on the item itself. The registry entry is annotated rather than deleted, so a known permission gap does not become an invisible one |
| `schedule` | 403 | Permission — same, on the project schedule tool |
| `standard_cost_codes` | 404 | Company-level standard cost codes are not configured for this tenant |
| `daily_log_headers` | 404 | Wrong path; the daily-log API needs a date range (`The Start Date and End Date parameters are required`) |
| `commitment_contracts` | 400 | v2.0 path shape needs revisiting |

The two 403s are **Affect's to grant**, not ours to fix — worth raising on the next call
alongside `OUTBUILD_API_TOKEN`. The rest is registry work.

## Incremental loading

Only 8 of 44 endpoints declare `incremental: filters[updated_at]`; the rest are full pulls,
because Procore does not document a reliable updated-at filter for them and a filter that
silently misses rows is worse than a full reload.

**RFIs and submittals are deliberately excluded from incremental** even though they are the
largest: they document `created_at` only, so an incremental pull would miss status changes —
precisely the data the report needs.

## Rate limits

The extractor honours `Retry-After` on 429 and backs off exponentially otherwise. Procore
throttles per hour, and the run pulls **active projects only** — the existing foundation
notebooks loop every project regardless of status, most of which are closed.
