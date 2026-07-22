# Discovery Meeting — Affect Group (In Person)

**Date:** Tuesday, July 21, 2026, 8:30am
**Location:** 389 Fifth Avenue, Suite 504, NYC
**Attendees:** Charley (Build Flows), Rebecca Buckley, and the Affect team

*(Cleaned up from the recorded voice notes.)*

## Context

The Affect team assigned Rebecca to find an industry expert to help and support her in developing the data warehouse, operating dashboards, and reports for the business. She is the internal builder; I am being brought in as a mentor/collaborator and developer.

## Current state

- **Rebecca has built a Procore ETL**: a script in Azure/Fabric that polls Procore via API and stores the data in the **Fabric Lakehouse** (their data warehouse).
- **Sage 100 Contractor** is currently queried live via a read-only SQL Server connection **directly from Power BI** — no ingestion into the Lakehouse yet. **A Sage ingestion script needs to be built.**
- Systems in use: Procore (project management & costing), Sage 100 (accounting/invoicing/payroll), Outbuild (scheduling/estimating), Ramp (vendor payments), ADP (payroll), Bluebeam & Navisworks (design/drawings), Outlook & OneDrive (email/docs), possibly drones. AccuBid was also mentioned.
- They maintain a **manually updated Excel spreadsheet for all projects** — this is where all project data currently lives.
- They have **documented all their solutions** and outlined their **"nouns"** (standardized people/places/things), and SOPs are **~50% complete** (Chris Mayer driving these).

## What they want

1. **Replicate the Excel project tracker in Power BI**, pulling from source data automatically — no more manual updates. Curated per-project data in the warehouse, with change tracking / history over time.
2. Pull all source data into **Lakehouse tables**: build integrations, map correct API endpoints, query systematically, store in an organized fashion.
3. Reference the Lakehouse from Power BI for reports and analytics.
4. Then: **Power Automate workflows**, initially focused on **payment templates** and the **lien waiver process**. These need to be scoped and visually outlined (SOP/UI definition) before development.
5. Long-term: use good data to drive better business decisions, automations, and triggers.

## Working relationship

- Rebecca is the **key holder** — she will do much of the development and creation. My role: mentor, answer questions, review her work, and seed examples (dashboards, ETL scripts, Power Automate flows) she can expand on.
- I will also directly develop anything they specifically need built.
- Cadence: I can meet early mornings (~8–8:30am), respond to emails during the day, and record video walkthroughs/demonstrations. Proposed **bi-weekly sync** for deeper discussions.
- **NDA** to be signed; I'll then get access to their environment (Fabric/Azure, Procore, Sage) to collaborate directly.

## Engagement structure discussed

- Consulting & development time: **$250/hour**
- Automations can be quoted **per project with a defined deliverable** — after the full workflow is understood and visually outlined with the team.

## Next steps

1. ✅ Document resources and notes (this file)
2. Affect handles **NDA + Fabric access** internally
3. **Deep-dive call with Rebecca**: review her ETL scripts, the Lakehouse, schemas, endpoints, refresh cadence, data quality/cleansing, and relational mapping
4. Verify the Procore ETL; **build the Sage 100 ingestion**
5. Get access to the **Excel project tracker** and define the Power BI dashboard/report that replaces it (reusable across projects)
6. Finalize SOPs for **payments template** and **lien waivers**, then scope the Power Automate builds

## Things to verify on the deep dive

- Whether the transcribed "Azure lake house" is OneLake/Fabric Lakehouse specifically, and how the Procore script is hosted/scheduled (Fabric notebook? Data pipeline? Azure Function?)
- Actual refresh cadence and how historical change-tracking is (or isn't) handled today
- What "AccuBid" usage actually is (estimating?) and whether Outbuild handles scheduling, estimating, or both
