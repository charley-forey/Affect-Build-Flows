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

> API documentation availability is **unverified**. Not yet confirmed whether Outbuild
> offers a public REST API, a Procore integration, or export-only. To be established
> before any scoping — do not assume an API exists.

## Open questions

1. Is Outbuild in active use, or still being evaluated? (Meeting notes suggest estimating;
   the README says scheduling — worth clarifying which.)
2. **Does the critical-path milestone list live here?**
3. Does Outbuild expose an API? Does it have a native Procore integration?
4. If milestones live here, does Outbuild also hold baseline vs. current vs. actual dates —
   or only the current plan?
5. Who maintains the schedule day to day?
