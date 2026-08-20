# Affect Group, Data Platform: Executive Update

**Aug 20, 2026. Charley Forey. Prepared for Rebecca Buckley to share internally.**

Follows the [Aug 19 update](2026-08-19-executive-update.md). Short, because the day was
finishing things rather than starting them.

## Summary

Two of the four things that were outstanding yesterday are now done, and both were ours to
finish rather than yours.

**Your schedule data is on the report.** The Outbuild token you sent on the 19th got the
data into the platform; yesterday it was sitting in the warehouse without reaching any
visual. It does now — the Monthly Progress Report's milestone count went from 52 to **126**,
covering **3 projects instead of 2**.

**The intake forms are finished.** All 18 SharePoint lists on the reporting site now have
their columns — 142 of them — and the project lookup is populated. Nothing further is needed
from anyone to start entering data.

**One thing still needs Affect**, unchanged from yesterday: the Sage gateway permission. It
is now the only access item on the list.

## Something worth knowing about your Outbuild setup

This is the useful finding of the day, and it is about configuration rather than software.

Outbuild activities do not carry a project reference of their own. The only way to tell which
Affect project a schedule belongs to is the **Procore link** on the Outbuild project — and
**only 3 of your 15 Outbuild projects have that link set**.

The consequence, in plain terms: we can see **406 critical-path activities** in your Outbuild
account, and we can only attribute **126** of them to a project. The other 280 are real
schedule data on real projects, and they cannot appear on any report because nothing connects
them to the rest of the business.

That is not something I can fix from this side. Connecting the remaining Outbuild projects to
their Procore counterparts would roughly triple the schedule coverage on the report, and it
is configuration in Outbuild rather than development work. **Worth asking whoever administers
your Outbuild account how those links get set.**

## What is still outstanding

| # | What | Who |
|---|---|---|
| 1 | **Sage gateway "Can use" permission** on the existing connection | Affect — the only access item left |
| 2 | Rotate the exposed Procore credentials | Affect — security, and it also unblocks moving data collection into your tenant |
| 3 | What goes inside the two job-folder templates, and a service account to own the SharePoint connection | Affect — the last things before the estimating/bidding workflows are switched on |
| 4 | Link the remaining Outbuild projects to Procore | Affect — see above; roughly triples schedule coverage |
| 5 | Four definition questions on the manual fields, and three ambiguous trade labels | Affect — one 30-minute call |
| 6 | Connect the intake dataflow and refresh it | Mine |

## One thing that has not moved, and why

**The scorecard still reads 59% coverage**, and the schedule data arriving does not change
that. Completion Variance is not scored by knowing when milestones *are* — it needs the
contract dates to compare them against, and those exist in neither Procore nor Outbuild. They
come off the signed contract, so they stay a manual entry.

Outbuild does hold baseline dates, but whether they are genuinely maintained — as opposed to
copied from the schedule when it was first imported — is not something the data can tell me.
Computing a variance from those without knowing would produce a confident number that means
nothing, which is the failure mode this platform is built to avoid. **A question for whoever
maintains the schedules.**

## Commercial

Unchanged in substance from yesterday, and the number has moved with the work: billable time
now stands at **45.5 hours** against the 20 agreed for the initial scope. As before, that is
not a Phase 0 overrun — Phase 0's five line items were delivered by August 2 — it is work
that followed the August 13 session and has not been re-scoped. It needs a conversation with
Cathal rather than an invoice, and I would rather raise it each time it moves than present it
once at the end.

*Full technical detail is in the project repository under `foundation/charley-dev/_docs/`.*
