# Outbuild API documentation (mirror)

Local markdown mirror of <https://pp-docs.outbuild.com>, scraped 2026-08-01.
Every page carries a `<!-- Source: ... -->` comment with its origin URL.

Re-run `python refresh.py <out-dir>` to refresh from the live sitemap.

Outbuild publishes **two separate APIs** with different hosts, auth schemes and purposes.

## 1. Datahub API — read-only analytics feed

Host `https://datahub.outbuild.com` · header `authorizationToken` · GET only · paginated via
`?page=N` with `hasNextPage` in the body, sorted by ID descending. **Page size varies per
endpoint** — 100 for `/projects`, 500 for `/activities` — so check each page's own header note
rather than assuming. Explicitly positioned for Power BI / Tableau.
Access is requested through an Outbuild Customer Success rep — there is no self-serve key.

| Doc | Endpoints |
|---|---|
| [Introduction](DatahubAPI/Introduction.md) | auth, pagination, access |
| [Projects](DatahubAPI/Endpoints/Projects.md) | `/projects`, `/projects/{projectId}` |
| [Activities](DatahubAPI/Endpoints/Activities.md) | `/activities`, `/activities/project/{projectId}`, `…/schedule/{scheduleId}`, `/activities/schedule/{scheduleId}/historical-progress` |
| [Tasks](DatahubAPI/Endpoints/Tasks.md) | `/tasks`, `/tasks/project/{projectId}`, `…/schedule/{scheduleId}` |
| [Companies](DatahubAPI/Endpoints/Companies.md) | `/companies`, `/companies/project/{projectId}` |
| [User](DatahubAPI/Endpoints/User.md) | `/users`, `/users/project/{projectId}` |
| [Weekly Commitments](DatahubAPI/Endpoints/Weekly-Commitments.md) | `/commitments`, `/commitments/project/{projectId}`, `…/schedule/{scheduleId}` |
| [Roadblocks](DatahubAPI/Endpoints/Roadblocks.md) | `/roadblocks` (+ project/schedule variants) |
| [Roadblock Types](DatahubAPI/Endpoints/Roadblock-Types.md) | `/roadblocktypes`, `/roadblocktypes/project/{projectId}` |
| [RoadblockTasks](DatahubAPI/Endpoints/RoadblockTasks.md) | `/roadblock-tasks` (+ project/schedule variants) |
| [RFVs](DatahubAPI/Endpoints/RFVs.md) | `/rfvs` (+ project/schedule variants) |
| [RFV Types](DatahubAPI/Endpoints/RFV-Types.md) | `/rfvtypes`, `/rfvtypes/project/{projectId}` |
| [RFVTasks](DatahubAPI/Endpoints/RFVTasks.md) | `/rfv-tasks` (+ project/schedule variants) |
| [Schedule Impact Requests](DatahubAPI/Endpoints/Schedule-Impact-Requests.md) | `/scheduleimpactrequests/schedule/{scheduleId}` |
| [Tags](DatahubAPI/Endpoints/Tags.md) | `/tags`, `/tags/project/{projectId}` |
| [ActivityTags](DatahubAPI/Endpoints/ActivityTags.md) | `/activitytags` |
| [TaskTags](DatahubAPI/Endpoints/TaskTags.md) | `/tasktags` |

## 2. Public API — operational, older

Host `https://publicapi.outbuild.com/api` · `authorization: Basic YOUR_APP_KEY_AUTH` plus
`www-authenticate: Bearer YOUR_API_TOKEN` · POST-style. Organised around *sectors* rather
than schedules; sparser and rougher than the Datahub docs.

| Doc | Contents |
|---|---|
| [How-to](PublicAPI/How-to.md) | login flow, `sector_id` lookup order |
| [pp-docs](PublicAPI/pp-docs.md) | Activity, Company, Roadblocks, Sector, Weekly commitment |

## Fields that bear on the milestone question

`/activities` returns `is_critical`, `baseline_start_date`, `baseline_end_date`,
`baseline_duration`, `start_date`, `end_date`, `progress`, `parent_id` — i.e. **both baseline
and current dates on a critical-path flag**. `/projects` returns `procore_id`, so Outbuild
projects can be joined to Procore.

**There are no actual-date fields.** The tracker's four date pairs map only partly:

| Tracker date | Outbuild source |
|---|---|
| Baseline | `baseline_start_date` / `baseline_end_date` (from the active baseline version) |
| Current | `start_date` / `end_date` |
| Actual | **not exposed** — derivable only from `/activities/schedule/{scheduleId}/historical-progress`, which returns `date` + `progress` per record, so an actual finish means inferring when `progress` reached 100 |
| Contract | **not exposed** |

There is no `milestone` entity or endpoint. If Affect's 10 critical-path milestones live in
Outbuild, they are activities distinguished by `is_critical` or by naming/tagging convention,
not by a dedicated type — confirm which on the deep-dive call. See [../README.md](../README.md).

## Not mirrored

`/`, `/markdown-page` and `/docs/category/endpoints` are Docusaurus scaffolding (empty
homepage, template sample, auto-generated index) with no API content.
