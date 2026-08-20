# Affect Group, Data Platform: Executive Update

**Aug 19, 2026 — revised end of day. Charley Forey. Prepared for Rebecca Buckley to share
internally.**

> **This update was revised after it was first written.** Three of the four items it asked
> Affect for were closed during the same day, and one of them — the Key Vault permission —
> **turned out to be an ask that should never have been made.** Both are corrected below
> rather than quietly edited out.

Follows the [Aug 13 update](2026-08-13-executive-update.md) and the in-person session with
Rebecca and Chris that evening.

## Summary

The Project Quality Plan you walked me through on the 13th is built, running against your
production Procore data, and now readable in Power BI. It went from a 44-sheet spreadsheet to
nine tables, a semantic model and a seven-page report — without anyone retyping a row.

Building it also turned up **defects in the reporting you already have**, all of the same
silent kind as the $4.85M change-order error: things that produced clean-looking output while
being wrong. All are fixed, and all are verified against your live data rather than assumed.

Later the same day three more things landed, and they change what is being asked of Affect.
A dead join was found that had been attributing **$22.5M of your receivables to no project at
all** — while the check designed to catch exactly that reported everything as fine. **Outbuild
went live**, closing the schedule-milestone gap that has been open since the start. And the
estimating→bidding folder automation moved out of my repository and into your tenant.

**Of the six items that sat with Affect on the 13th, four are now closed and two remain.**
One of the four closed because it was never a real ask — see "A correction" below.

One commercial item needs a conversation: the twenty hours agreed for the initial scope are
spent, and the work since then was not in that scope.

## What has been built since the 13th

| | |
|---|---|
| Project Quality Plan — data | The 44-sheet QA/QC tracker rebuilt as nine tables. 625 trade checklist items, 93 statutory gates, 101 DOH items, held once as a versioned library rather than copied into every project's workbook |
| Project Quality Plan — reporting | A second Power BI report, seven pages: Quality Portfolio, Non-Conformance, Punch & Completion, Submittals & Mock-Ups, Statutory Gates, Trade Checklists, and a Data Quality page |
| Quality data, live | **4,564 quality records** already flowing from Procore — 2,245 submittals, 1,469 punch items, 850 observations. Nobody typed any of them |
| Schedule data, live | **3,078 records across 15 Outbuild endpoints**, landed the evening the token arrived. This is the only source of critical-path milestones anywhere in the business |
| Estimating → bidding automation | **Both workflows now exist in your Power Automate**, created switched off. The job-folder structure and the Job Register list are provisioned on `AFFECTBUILD1`. What is still needed is what goes *inside* the two folder templates |
| Intake forms | 17 SharePoint lists generated — the 9 that feed the Monthly Progress Report's manual fields, and 8 new ones for the quality registers. The reporting site now exists, all 18 lists are built with their 142 columns, and the loader that reads them is published against it. Connecting that loader is my remaining task, not yours |

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

**$22.5M of your receivables was attached to no project — and the check built to catch that
said everything was fine.** This is the most serious thing found today, and it is the same
shape as the $4.85M change-order error: clean-looking output, no error anywhere.

Invoices are matched to projects through the Sage job number. When the platform moved onto
its own data pipeline, that field started coming from a source that does not carry it, so it
was blank for every project. **All 122 accounts-receivable invoices — $23,695,760.48 — were
attributed to no project at all.**

Two reasons nobody would have spotted it:

- **Nothing was lost, so nothing looked wrong.** 117 invoices went in and 117 came out. That
  count is exactly the check that had been run to confirm the pipeline change was safe. The
  invoices survived; only their link to a project did not.
- **The mapping indicator was reading from the same broken source**, so it reported all 19
  projects as correctly mapped. A completely dead join was certifying itself as healthy.

Fixed and verified against your live data: **15 of 19 projects** now resolve to a Sage job,
unmatched invoices fall from **122 to 24**, and **$22,548,861.96 of receivables is attributed
to a project** where none was before. The four projects still without a Sage job are three
templates and City Harvest.

**Your schedule data is now flowing.** The Outbuild token arrived on the 19th and 3,078
records across 15 endpoints landed the same evening. Worth knowing: the connection had been
built and tested against Outbuild's documentation but never actually run, and the first real
call failed three different ways — one of which looked exactly like a rejected token. Had we
not been able to test it live, "the token doesn't work" is the answer you would have got.

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

**807 of your cost codes were missing from every cost-by-division view.** Your cost codes
carry CSI division numbers, and for divisions 1 through 9 Affect writes them without a
leading zero — `1-1000 GENERAL REQUIREMENTS` is Division 01. Our parser expected two digits,
so it read every one of those as unreadable. The effect: **807 cost codes, 15% of your
5,433-code master, absent from any report that groups cost by division** — quietly, with no
error and no visible gap. Every one of them turned out to be perfectly good data. Fixed;
those divisions now carry 2,941 codes, 1,540 of them in Division 01 alone.

Worth saying plainly: that looked like a data-quality problem on your side and it was our
code being wrong about how you write your codes. Same shape as the trade column showing raw
text, and exactly why each of these is checked against your live data rather than assumed.

**A tenth of the submittal register was invisible.** Procore records some submittals with the
status "For Record" where your QA/QC workbook's dropdown says "For Record Only" — a
difference in spelling, not in meaning — and our transform only recognised the workbook's
wording. **222 of your 2,245 submittals** were therefore dropping out of every status filter.
Not showing the wrong status: not appearing at all. Both spellings are now recognised, and
the count of submittals with an unrecognised status is **zero**.

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

## A correction: one of the things I asked you for was not needed

**I have been asking for a Key Vault permission since August 13. It was the wrong vault, and
nobody needed to grant anything.**

The request named a vault called `OneLake`. The vault Affect actually uses is
**`AffectKeyVault`**, in a different subscription — and my account already had administrator
rights on it, inherited from the resource group. That ask appeared in three documents and in
the earlier version of this update. **It is withdrawn, not completed.** It would have solved a
problem that did not exist, and it took someone's attention for a week.

I found it by finally exercising the vault instead of reasoning about it — which also turned
up two genuine faults hiding behind it. The one worth telling you about: the code that reads
secrets **failed open**. If the vault lookup did not fire, it quietly fell back to reading the
credential from the machine's environment and reported success. A half-configured vault would
have pulled a credential from an unaudited source and told nobody, and the first sign would
have been an unattended 2am run. It now refuses and fails loudly instead.

## What is needed from Affect

**Down from six items to two**, and neither is a purchasing decision.

| # | What is needed | Why it matters | Effort |
|---|---|---|---|
| 1 | Grant "Can use" on the existing gateway connection `nc-affect-1\sage100con` | **The only access item left.** Turns on Sage — AR/AP, retainage, actual cost by cost code. Nothing new is built; this is the connection your team already uses. May need to route through your outside Sage consultant | One permission |
| 2 | What belongs inside the two folder templates | Both estimating/bidding workflows now exist in your Power Automate, switched off, pointing at the folder structure on `AFFECTBUILD1`. Your SOP names `02 E26-000 BOILER PLATE` and `YY-000 STANDARD PROJECT TEMPLATE` but never says what is inside them, so today they would copy a correct but empty skeleton. Worth deciding at the same time: `02 E26-000 BOILER PLATE` has the year `26` in its name, so it needs renaming each January unless we change it now | One decision |

**Closed since the earlier version of this update:** the Outbuild token (received — thank you,
3,078 records landed that evening), the Key Vault permission (withdrawn, above), and the
SharePoint site (you reused `AFFECTBUILD1` rather than creating a new one, which is fine —
the workflows point at it). Creating the 18 reporting intake lists is on me, not you.

**Two narrower questions rather than blockers.** Both of the items flagged here earlier today
have since been worked through, and what is left for Affect is smaller than it was.

The status mismatch is **fixed outright** — described above. The trade mapping is **largely
fixed**: where the meaning was unambiguous, Procore's trade names are now mapped to the
workbook's codes — "HVAC" to `HVAC_DUCTWORK`, "Sprinkler" to `FIRE_SPRINKLER`, and fourteen
more. That recovered **464 records**; unattached observations fell from 459 to **215**, and
unattached punch items from 511 to **291**.

Two things I still will not decide without you:

1. **Three trade labels that could mean more than one thing.** "Drywall/Carpentry" (255
   records), "Concrete Superstructure" (110) and "Concrete" (64). Framing or board or
   millwork; cast-in-place or formwork or slab-on-deck. Attaching a defect to the wrong trade
   is worse than leaving it unattached, so these stay unattached until someone who knows the
   trade breakdown says which is which. About twenty minutes.
2. **Trades in Procore that your QA/QC library has no sheet for.** Roofing, Glazing, Windows,
   Structural Steel, Low Voltage, Demolition, Housekeeping, Light Fixtures, Window Treatments
   and others. This is not a mapping gap — your Procore trade list is simply broader than the
   26-trade checklist library in the SaunaLounge tracker. The question is whether the library
   should cover them, which is a scope decision rather than a translation.

## One commercial item

The initial scope agreed with Cathal on July 24 was **20 hours**. Phase 0's five line items
were delivered by August 2 at roughly 22 hours, which was flagged at the time.

Since then: the Project Quality Plan as a second subject area, two Power Automate workflows
now deployed into your tenant, the reporting layer over both, and the defect work described
above. That is a further **18.5 hours**, bringing the total to **40.5**. (The earlier version
of this update said 34.5 — that was written this morning, before the day's later sessions.)
None of it was in the original twenty, and none of it was a Phase 0 overrun — it is work that
followed the request made at the August 13 session.

I would rather raise this than invoice it unremarked. Either it bills against the agreed
5 hrs/week ongoing cadence, or it is scoped as a second block. That is Cathal's call and I am
happy either way.

## Where this goes next

**Outbuild is now flowing**, so one of the two remaining data gaps closed today; connecting
its milestones through to the report is my next piece of work rather than an access question.
Once Sage joins it, the Monthly Progress Report covers itself without manual assembly, and
the scorecard's four unscored categories get real data. The quality platform now supplies
exactly the signal those categories were meant to measure — non-conformance ageing, punch
closure, hold-point compliance.

On the folder automation: both workflows are in your tenant and switched off. Turning them on
needs the template contents above, and a decision about **which account owns the SharePoint
connection** — the workflows run as whoever created it, so a named person's account means
they stop working when that person leaves. A service account is worth ten minutes now.

The nightly pipeline runs six stages and validates 107 expectations before anything publishes.
Everything is deployed from version-controlled scripts, so the repository is the source of
truth rather than the workspace, and any of it can be rebuilt or rolled back.

Mentoring remains the one item from the original scope not yet started. With Rebecca's
workload where it is, I am continuing to record walkthroughs as I build rather than waiting
for shared calendar time.

*Full technical detail, including the independent audit of every claim above, is in the
project repository under `foundation/charley-dev/_docs/`.*
