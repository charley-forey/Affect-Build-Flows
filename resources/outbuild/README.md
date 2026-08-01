# Outbuild

Construction scheduling / estimating. **Integration status: not integrated.**

## Why it matters more than its status suggests

The Excel tracker's `SCHEDULE` tab is the second-largest section of the report — 10
critical-path milestones with four date pairs each (contract, baseline, current, actual),
plus variance calculations that feed a **15%-weighted scorecard category**.

**The Procore OpenAPI spec contains no `milestone` path.**
`/rest/v1.0/projects/{project_id}/schedule` returns schedule metadata and tasks. So the
question of where Affect's critical-path milestone list actually lives is open — and if
the answer is Outbuild, this tool moves from "not integrated" to a dependency for
`fct_Milestone`.

Three possibilities, and we do not yet know which:

1. Milestones live in **Procore Schedule** → build from the Procore API
2. Milestones live in **Outbuild** → needs an Outbuild integration
3. Milestones live **only in the spreadsheet** → they stay manual, in the input workbook

**Resolve this on the deep-dive call.** It determines whether the Schedule Detail page has
a data source at all.

## Documentation

| Resource | URL |
|---|---|
| Product site | https://www.outbuild.com |
| API docs (upstream) | https://pp-docs.outbuild.com |
| **API docs (local mirror)** | [`api/`](api/README.md) — 19 pages, scraped 2026-08-01 |

**Outbuild does expose an API — two, in fact:**

- **Datahub API** (`datahub.outbuild.com`) — read-only, GET-only, paginated, `authorizationToken`
  header. Explicitly built for Power BI / Tableau. 17 endpoint groups covering projects,
  activities, tasks, commitments, roadblocks, RFVs and tags.
- **Public API** (`publicapi.outbuild.com/api`) — older, operational, sector-oriented,
  Basic + Bearer auth.

Access to Datahub is granted by an Outbuild Customer Success rep, not self-serve — **starting
that request is a lead-time item**, worth raising before it blocks scoping.

## Open questions

1. Is Outbuild in active use, or still being evaluated? (Meeting notes suggest estimating;
   the README says scheduling — worth clarifying which.)
2. **Does the critical-path milestone list live here?** The API has no `milestone` entity —
   if the list lives in Outbuild it is activities flagged `is_critical` or picked out by
   naming/tagging convention. Which convention does Affect use?
3. ~~Does Outbuild expose an API?~~ Yes — see above. Native Procore integration still unconfirmed,
   but `/projects` returns a `procore_id`, so the two systems are at least linkable.
4. ~~Does Outbuild hold baseline vs. current dates?~~ `/activities` returns `baseline_start_date`,
   `baseline_end_date` and `baseline_duration` alongside `start_date` / `end_date`.
   **Still open:** *actual* and *contract* dates are not exposed at all. Actuals could be
   inferred from the `historical-progress` endpoint (progress % by date); contract dates have
   no Outbuild source and would stay manual.
5. Who maintains the schedule day to day?
6. Who owns the Outbuild account relationship, i.e. who requests the Datahub token?
