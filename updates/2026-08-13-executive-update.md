# Affect Group, Data Platform: Executive Update

**Aug 13, 2026. Charley Forey. Prepared for Rebecca Buckley to share internally.**

## Summary

A complete replacement for the Monthly Progress Report workbook is built and running in your
Microsoft Fabric tenant. It pulls from your production Procore, transforms the data through a
tested pipeline, validates it against 63 checks every night, and publishes a 12 page Power BI
report. It was built in an isolated folder alongside Rebecca's existing work, which it reads
but has never written to, so nothing currently in production was changed or put at risk. Six
items now sit with Affect. Four of them are permission grants that cost nothing and take
minutes, and they are the difference between a platform that demonstrates well and one that
runs itself.

## What has been built

| | |
|---|---|
| Data platform | Three lakehouses (raw, cleaned, reporting) with 40 tables of production Procore data flowing through them |
| Nightly automation | A five step pipeline that refreshes everything without anyone touching it |
| Reporting model | 37 tables, 99 measures, 45 relationships. The full logic of the Excel workbook, rebuilt |
| The report | 12 pages, 180 visuals, with drill through from portfolio down to a single project |
| Quality gate | 63 automated checks that run before the report refreshes |
| Test suite | 12 offline test suites that prove every transformation without touching Fabric, costing capacity, or consuming API quota |

## What it has already found

Rebuilding the workbook meant checking its numbers rather than reproducing them.

**The portfolio contract value was understated by $4.85M, or 16%.** Change orders were being
counted for the current month only instead of accumulated. Current Contract read $30.25M
against a correct figure of $35.10M, and everything calculated against contract value, such
as billed percentages and balance to finish, was wrong in the same direction. This has been
found, fixed and deployed.

**The project scorecard had three categories disconnected from the data.** Schedule
Performance always scored 3 out of 3 and Completion Variance always scored 0 out of 3. Two of
the errors cancelled each other out, which is why the total looked reasonable and the fault
went unnoticed for so long. Fixed.

**Several broken joins that nobody could have seen.** Two projects have no link to Sage
financials, 70 cost codes are missing from master data, and 23 AR invoices point at a job
that resolves to no project. In Excel these rows are silently dropped from a lookup. Here
they are listed on a Data Quality page.

**Your current dashboards are running on stale data.** Sage data stops at July 20 and
Outbuild at July 14. Anyone reading those reports today is reading numbers three to four
weeks old. This is almost certainly the same gateway permission issue described below.

## Why the data is validated before the report publishes, every day

This is the design decision worth understanding, because it is what separates this from the
workbook it replaces.

A wrong number does not announce itself. The $4.85M error above produced a clean, plausible,
precisely formatted figure on a dashboard. Nothing errored and no log recorded a problem. It
was caught only because the numbers were independently recomputed and compared.

So the pipeline validates first and publishes second. Every night, 63 expectations run
against the data covering row counts, orphaned keys, date sanity and reconciliation totals.
If an expectation fails, the run stops rather than refreshing the report. The alternative is
publishing a number that looks right, being believed, and finding out weeks later. In
construction reporting the cost of that is not abstract, because a contract value, a billed
percentage or a retainage balance is what somebody invoices against.

## What is needed to get unblocked

Six items, all with Affect, in priority order.

| # | What is needed | Why it matters | Effort |
|---|---|---|---|
| 1 | Grant `cforey-c@affect-group.com` "Can use" on the existing gateway connection `nc-affect-1\sage100con` in Manage connections and gateways | Turns on Sage 100 ingestion, covering AR and AP, retainage, and actual cost by cost code. Affect already uses this connection, so nothing new is being built. Our dataflow is deployed and fails in five seconds because the account cannot see any gateway. This likely also fixes the stale data above. If the outside Sage consultant owns the connection, an introduction is all that is needed | One permission, about 2 minutes |
| 2 | Issue an Outbuild API token through Outbuild customer success | Outbuild is the only source of schedule milestones anywhere in the stack, and 17 of 19 projects currently have no schedule data. Ingestion is built and tested but cannot run | One request |
| 3 | Set up a Key Vault, which requires an Azure subscription on the tenant | Procore extraction currently runs from a laptop and lands files that Fabric picks up. It works, but the nightly pipeline does not call Procore itself. A Key Vault holds the credential inside your tenant and moves extraction fully into Fabric. This is the only item here that is a purchasing decision rather than a permission | Purchasing decision |
| 4 | Procore role permissions, currently returning 403 on `punch_item_types` and `schedule` | Two report sections cannot be populated without them | Permission change |
| 5 | A decision on manual inputs, then a SharePoint administrator runs the provided script | Roughly 40% of the report is typed by hand today. The nine intake lists and 61 columns are generated and ready, and the tables are already live and waiting. Until this lands, those fields stay blank | One decision, one script run |
| 6 | Two or three real completed project reports, and the six client satisfaction survey questions | The workbook received was a template with demo data. Real examples let the rebuilt figures be validated against known good ones | Two files |

Items 1, 2 and 4 are permission grants. None of them requires spend, procurement, or any
change to what is running today, and each one converts finished, tested work into working
automation.

## Where this goes next

Once Sage and Outbuild are flowing, the platform covers the full Monthly Progress Report
without manual assembly. From there the same foundation extends to the payments and lien
waiver workflows, vendor and insurance tracking, and the remaining systems such as Ramp and
ADP, without rebuilding anything underneath.

On capacity, with Rebecca's workload increasing I am taking on the build load directly.
Knowledge transfer continues through recorded walkthroughs rather than live sessions, so
progress does not depend on finding shared calendar time. Rebecca's access to me by text,
call and email remains unlimited and unbilled.

*Full technical detail, including the independent audit of every claim above, is in the
project repository under `foundation/charley-dev/_docs/`.*
