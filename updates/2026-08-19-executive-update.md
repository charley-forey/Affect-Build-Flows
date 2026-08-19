# Affect Group, Data Platform: Executive Update

**Aug 19, 2026. Charley Forey. Prepared for Rebecca Buckley to share internally.**

Follows the [Aug 13 update](2026-08-13-executive-update.md) and the in-person session with
Rebecca and Chris that evening.

## Summary

The Project Quality Plan you walked me through on the 13th is built, running against your
production Procore data, and now readable in Power BI. It went from a 44-sheet spreadsheet to
nine tables, a semantic model and a seven-page report — without anyone retyping a row.

Building it also turned up **two defects in the reporting you already have**, both of the
same silent kind as the $4.85M change-order error: things that produced clean-looking output
while being wrong. Both are fixed.

Of the six items that sat with Affect on the 13th, one is closed, one is in transit, and the
largest — the Azure subscription — has shrunk to a single permission grant that takes about
two minutes.

One commercial item needs a conversation: the twenty hours agreed for the initial scope are
spent, and the work since then was not in that scope.

## What has been built since the 13th

| | |
|---|---|
| Project Quality Plan — data | The 44-sheet QA/QC tracker rebuilt as nine tables. 625 trade checklist items, 93 statutory gates, 101 DOH items, held once as a versioned library rather than copied into every project's workbook |
| Project Quality Plan — reporting | A second Power BI report, seven pages: Quality Portfolio, Non-Conformance, Punch & Completion, Submittals & Mock-Ups, Statutory Gates, Trade Checklists, and a Data Quality page |
| Quality data, live | **4,564 quality records** already flowing from Procore — 2,245 submittals, 1,469 punch items, 850 observations. Nobody typed any of them |
| Estimating → bidding automation | Both folder-provisioning workflows built and tested offline, ready to import once the SharePoint site exists |
| Intake forms | 17 SharePoint lists generated — the 9 that feed the Monthly Progress Report's manual fields, and 8 new ones for the quality registers |

**The reason the quality data was free.** Your own workbook says it on its cover page:
*"Procore is the mandatory system of record."* So non-conformances, punch items and submittals
are read from Procore directly rather than retyped. Only what Procore genuinely does not hold
— the statutory gate registers, the DFOW risk tiers, the inspection plan — needs entering by
hand, and those are the 8 new lists.

**Why 44 sheets became 9 tables.** 26 of the sheets are trade checklists with an identical
layout. In a spreadsheet they have to be 26 tabs; in a database they are one table plus a
trade column. Three more sheets — Path to TCO, Path to Fire Alarm, Statutory Inspections —
are the same shape as each other, so they became one register with a type column. Adding a
27th trade is now a row, not a new tab.

## What it found in the reporting you already have

**Your live dashboard was displaying raw code in a trade column.** The pipeline was reading
Procore's trade field as a whole object rather than its name, so instead of "Electrical" the
column held `{"id":562949953553773,"name":"Electrical",...}`. Fixed. This has been on the live
Monthly Progress Report since it was built.

**The nightly data-quality gate was not recording its results.** The gate itself worked
correctly every night — it checked the numbers and would have stopped a bad refresh. But the
table holding *which* checks ran and what they found was never being created, because of an
import error that the code caught and logged rather than raised. So the verdict was right and
the audit trail was missing, which is the harder of the two to notice. Fixed, and it
immediately surfaced nine things worth knowing — including 376 vendors on live projects with
no insurance certificate on file, and 105 certificates that are on file but out of date.

**Five defects in the QA/QC workbook itself.** The most consequential: on four of the
registers, the dashboard counts completions over a shorter range of rows than it counts
totals. Special Inspections totals 74 rows but only ever counts 39 of them as closed. Add a
40th inspection and close it — the total goes up, the closed count cannot. The percentage
falls, can never reach 100%, and moves in the direction that makes the project look *behind*.
It has not caused a problem yet only because the registers are not full. It breaks precisely
when the job gets busy.

Also: the CSI specification codes on the two highest-risk waterproofing items were destroyed
by Excel reading them as dates. `D-01` now stores `2009-03-07` where a spec reference belongs.
Those two are the only Tier 4 Critical items on the register.

Full detail: `analysis/pqp-workbook/defects-and-questions.md`.

## What is needed from Affect

Down from six items to four, and none of them is a purchasing decision any more.

| # | What is needed | Why it matters | Effort |
|---|---|---|---|
| 1 | **One role assignment: "Key Vault Secrets Officer" on vault `OneLake`** for `cforey-c@affect-group.com` | The subscription and vault now exist — thank you. But the account has only resource-group Contributor, which cannot read or write a secret in an RBAC vault, or grant itself the right to. Until this lands, Procore extraction runs from my machine rather than inside your tenant | ~2 minutes, someone with Owner |
| 2 | Grant "Can use" on the existing gateway connection `nc-affect-1\sage100con` | Turns on Sage — AR/AP, retainage, actual cost by cost code. Nothing new is built; this is the connection your team already uses. May need to route through your outside Sage consultant | One permission |
| 3 | The Outbuild API token | Offered by email on the 11th and not yet received. It is the only source of schedule milestones anywhere; 17 of 19 projects currently have none | One email |
| 4 | A SharePoint site, and what belongs in the two folder templates | The estimating/bidding workflows are built and tested. Your SOP names `02 E26-000 BOILER PLATE` and `YY-000 STANDARD PROJECT TEMPLATE` but never says what is inside them | One decision |

**Two questions rather than blockers.** Procore's trade names and the workbook's trade codes
are different vocabularies — Procore says "HVAC" and "Sprinkler" where the workbook says
`HVAC_DUCTWORK` and `FIRE_SPRINKLER`. 459 of 850 observations therefore attach to no trade.
I have deliberately not guessed the mapping: deciding whether "Concrete Superstructure" means
cast-in-place concrete or slab-on-deck attaches a defect to a trade, and getting that wrong is
worse than leaving it unattached. The same applies to 223 status values. Both need about
twenty minutes with someone who knows the trade breakdown.

## One commercial item

The initial scope agreed with Cathal on July 24 was **20 hours**. Phase 0's five line items
were delivered by August 2 at roughly 22 hours, which was flagged at the time.

Since then: the Project Quality Plan as a second subject area, two Power Automate workflows,
and the reporting layer over both. That is a further **12.5 hours**, bringing the total to
**34.5**. None of it was in the original twenty, and none of it was a Phase 0 overrun — it is
work that followed the request made at the August 13 session.

I would rather raise this than invoice it unremarked. Either it bills against the agreed
5 hrs/week ongoing cadence, or it is scoped as a second block. That is Cathal's call and I am
happy either way.

## Where this goes next

Once Sage and Outbuild are flowing, the Monthly Progress Report covers itself without manual
assembly, and the scorecard's four unscored categories get real data. The quality platform now
supplies exactly the signal those categories were meant to measure — non-conformance ageing,
punch closure, hold-point compliance.

The nightly pipeline runs six stages and validates 103 expectations before anything publishes.
Everything is deployed from version-controlled scripts, so the repository is the source of
truth rather than the workspace, and any of it can be rebuilt or rolled back.

Mentoring remains the one item from the original scope not yet started. With Rebecca's
workload where it is, I am continuing to record walkthroughs as I build rather than waiting
for shared calendar time.

*Full technical detail, including the independent audit of every claim above, is in the
project repository under `foundation/charley-dev/_docs/`.*
