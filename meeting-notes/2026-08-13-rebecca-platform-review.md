# Platform review with Rebecca — Thu Aug 13, 2026 (morning)

First working session since the `charley-dev` platform went live in Fabric on Aug 2.
Rebecca back from vacation. Walkthrough of what was built, why it was built that way, and
what is still blocked.

## Attendees

- Rebecca Buckley (Affect — AP/AR, internal technical lead)
- Charley Forey

## What we covered

### 1. The build, and the reasoning behind it

Walked the `charley-dev` solution end to end — three lakehouses, ingestion, transformation,
semantic model, report. Detail: [`foundation/charley-dev/_docs/solution-guide.md`](../foundation/charley-dev/_docs/solution-guide.md),
audited in [`assessment.md`](../foundation/charley-dev/_docs/assessment.md).

Design decisions and the reasoning given for each:

| Decision | Why |
|---|---|
| Built in an isolated `charley-dev` folder, reading the existing workspace but never writing to it | Rebecca's reporting keeps running untouched while a replacement is proven alongside it. Rollback is deleting a folder. |
| Bronze holds raw, unparsed payload | Bronze cannot drop a column it never parsed, so a transform bug is a re-run, not a re-extract against a rate-limited API. |
| Silver logs rejected rows with a reason instead of dropping them | A dropped row is invisible; a logged one is a question someone can answer. |
| Gold column names match the semantic model exactly | The DAX reads them by name — a rename is otherwise a silent blank tile. |
| Transformations live in `.sql` files, not in Power Query steps | SQL is diffable in a pull request, testable offline through DuckDB with no gateway or credential, and re-runnable against data already pulled. A Power Query step is none of the three. |
| One config-driven extractor, not one notebook per endpoint | Adding a Procore endpoint is a YAML entry. Auth, pagination, the v2.0 header rule, retry and watermarking are implemented once. This is the pattern for Rebecca to take over. |
| Everything deploys from committed scripts, idempotent and dry-run by default | The repo is the source of truth, not the workspace. Deploys refuse to write outside `charley-dev`. |

### 2. Why the data is validated before the report is generated, every day

The point Rebecca and I spent the most time on, and the one worth repeating to the team.

**A wrong number does not look wrong.** The dashboard reported Current Contract of
$30,254,551.24 — a clean, plausible figure — while the true value was $35,102,931.14.
$4.85M, 16% of portfolio contract value, missing because change orders were being summed per
month rather than to date. Every ratio dividing by contract value inherited it, and each of
those also looked plausible. Nothing errored. No log recorded a problem.

So the nightly pipeline runs `cd_40_dq_checks` — **63 expectations** — *before* the semantic
model refreshes. A failing expectation fails the run rather than publishing bad numbers. The
notebooks also assert their own output, because a notebook that builds empty tables still
reports "Completed".

Three real examples of what the gate catches, all invisible in the Excel:

- 2 projects have no Sage crosswalk entry — they join to no financial data at all
- 70 cost codes are absent from master data
- 23 AR invoices reference a Sage job that resolves to no project

In the workbook, facts referencing an unmastered key are simply dropped from the lookup.
Budgets and change orders quietly understate, and nobody finds out.

We also discussed the limit of a gate: the reconciliation test passed the whole time the
$4.85M was missing, because its fixture put all change orders in one month — where per-month
and cumulative are arithmetically identical. A gate passing is not the same as a gate
watching.

### 3. Transformations

Bronze → silver → gold, as ordered `.sql`. Covered typing and trimming at the silver
boundary, the sentinel-date problem (dates before 1582-10-15 that Spark refuses to read at
all, used as "unknown" placeholders — now floored to NULL), the `"NA"` string sentinels, and
`merge_delta` upserting on the natural key so a re-run does not double rows. Silver is
currently 15 tables, 14,791 rows, **0 rejects**.

### 4. Notebooks

Walked the run order — extract → land → bronze-to-silver → seed gold → build gold → DQ gate —
and the shared library in `00-platform/lib`. Secrets go through `get_secret()` (Key Vault in
Fabric, environment variable locally); nothing in a notebook cell. This is the mechanic
Rebecca takes over first.

### 5. Fabric MCP

Demonstrated the MCP server wired into the repo (`.mcp.json`). Where it earns its keep is
exploration against the live workspace — `execute_sql_query` and `execute_dax_query` to check
a number without opening the portal. Item *creation* stays on the committed REST path in
`deploy.py`, because that is idempotent, reviewable as a diff, and folder-scoped. MCP is the
inspection tool; the repo is the deployment tool.

### 6. Solutions being integrated

**The Sage database is administered by an outside consultant**, not by Affect directly.
Rebecca and the team use an established gateway connection to it, which is the same
connection `CD_Sage_Ingest` needs. That changes the ask from "build us a connection" to "add
one account to the one you already run", and it means the request may need to route through
the consultant rather than Affect's own admins. Worth confirming who holds it before the
evening session.

Procore (live, production tenant), Sage 100 Contractor (built, one permission grant away),
Outbuild (built, waiting on a token), SharePoint (generated intake lists, awaiting the
decision). Ramp, ADP, Bluebeam/Navisworks remain backlog.

## Rebecca's capacity

Rebecca is back from vacation into a heavier load — someone has left the team and that work
has landed on her. She has materially less time for this project than the weekly-session
cadence assumed.

**Agreed:** Charley absorbs the build load. The cadence changes from "working sessions where
Rebecca builds alongside" to "Charley builds, Rebecca reviews" — mentoring continues, but
async and recorded, so it does not depend on finding a shared hour. Rebecca's ad-hoc access
stays unlimited and unmetered.

## Actions

| # | Action | Owner |
|---|---|---|
| 1 | Short executive update Rebecca can forward to her team | Charley — [`updates/2026-08-13-executive-update.md`](../updates/2026-08-13-executive-update.md) |
| 2 | Grant `cforey-c@affect-group.com` **Can use** on gateway connection `nc-affect-1\sage100con;Affect Group` — the connection Affect already uses. Route through their outside Sage consultant if he owns it | Affect / Sage consultant |
| 3 | Issue `OUTBUILD_API_TOKEN` via Outbuild CS | Affect |
| 4 | **Stand up a Key Vault** (needs an Azure subscription on the tenant) so the Procore credential lives in Affect's tenant, not on a laptop | Affect |
| 5 | Procore role permissions — currently 403 on `punch_item_types` and `schedule` | Affect |
| 6 | Decide the manual-input location; SharePoint admin runs the generated PnP script | Affect |
| 7 | In-person session with Chris — options offered, awaiting confirmation | Rebecca |

## Raised, needs a decision from Affect

**Existing production reporting is running on stale data.** Sage stops at **2026-07-20** and
Outbuild at **2026-07-14** — roughly three and four weeks respectively. The likely cause is
the same gateway issue blocking `CD_Sage_Ingest`. Whoever is reading the current dashboards is
reading month-old numbers, and this had not been noticed.
