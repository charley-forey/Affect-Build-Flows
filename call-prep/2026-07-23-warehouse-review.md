# Data Warehouse Review — Agenda & Information Request

**Purpose:** walk the current Fabric environment and Procore ETL, review the Sage 100
Contractor connection, and agree the first deliverable.
**Length:** 60 min · **Format:** call, screen-share
**Attendees:** Rebecca Buckley + Charley Forey. Cathal may be useful for the operational
tabs of the reporting template — Rebecca's expertise is the financial inputs.

**Prep done:** the Monthly Progress Report template has been fully extracted and analysed.
Everything below is backed by [`../analysis/excel-tracker/`](../analysis/excel-tracker/).

---

## What we should come out with

Three answers, in priority order:

1. **What value joins a Procore project, a Sage job, and a row in the reporting template?**
2. **What does the existing Procore ETL already cover?**
3. **Where should the ~40% manual data live going forward?**

Everything else is useful. Those three unblock the build.

## Suggested time budget

| Min | Topic |
|---|---|
| 0–5 | Sage documentation correction + agree the agenda |
| 5–20 | Fabric + Procore ETL walkthrough (Rebecca screen-sharing) |
| 20–30 | Sage 100 Contractor — what the SQL connection exposes |
| 30–45 | The reporting template — findings + the manual-data question |
| 45–55 | The Procore↔Sage connector decision + open questions |
| 55–60 | Next steps, access checklist |

---

## 0. Sage documentation correction (2 min)

The Sage link circulated on Jul 22 — `help-sage100.na.sage.com/2023/FLOR/` — is the File
Layouts and Object Reference for **Sage 100 ERP**, not **Sage 100 Contractor**. Different
product, different schema. Procore's own connector page confirms the integration targets
Sage 100 Contractor v20.5+.

Correct references collected in
[`../resources/sage-100-contractor/README.md`](../resources/sage-100-contractor/README.md).

Worth handling first because it determines which schema the ingestion gets written against.

---

## 1. Fabric + Procore ETL (15 min)

**Fabric**
- [ ] Capacity / SKU, workspace structure, who administers
- [ ] Lakehouse vs Warehouse — which artifacts exist? Any medallion structure?
- [ ] Dev/test/prod separation, or one workspace?
- [ ] How are API credentials stored — Key Vault, or in the notebook?

**The ETL**
- [ ] How is it hosted and scheduled — Fabric notebook, Data Pipeline, Azure Function?
- [ ] What language?
- [ ] **Which Procore endpoints does it pull today?** (checklist in
      [`../resources/procore/endpoints-cheatsheet.md`](../resources/procore/endpoints-cheatsheet.md))
- [ ] Full refresh or incremental? Does it use `filters[updated_at]`?
- [ ] **Which OAuth grant?** ⚠️ A user-based token expires and will break the pipeline.
      Unattended ETL needs client-credentials / installation auth. This is the single most
      common Procore ETL failure mode and worth confirming early.
- [ ] Rate-limit / retry handling on `429`?
- [ ] Any monitoring or failure alerting?
- [ ] Known data quality issues?

The goal here is to validate and extend what already exists, not replace it.

---

## 2. Sage 100 Contractor (10 min)

- [ ] **Run `SELECT * FROM INFORMATION_SCHEMA.TABLES` live if possible** — 30 seconds and
      we have the real schema instead of working from assumptions
- [ ] Which queries does Power BI run against Sage today? These are the starting point for
      the ingestion and they encode logic that isn't written down anywhere else
- [ ] **Where does the SQL Server live?** On-prem means an **on-premises data gateway** is
      required for Fabric ingestion — a dependency with procurement lead time, so worth
      identifying now rather than later
- [ ] Are the **audit tables** accessible? They would give change tracking for free
- [ ] Job numbering scheme — does it match Procore project numbers?
- [ ] Cost code structure — segmented? Does it reconcile with Procore?
- [ ] Payroll: Sage or ADP for hours worked and OT hours?
- [ ] Which Sage 100 Contractor version? (Determines schema specifics and connector
      eligibility, v20.5+)

---

## 3. The reporting template (15 min)

### What it does well

- A **weighted, agreed definition of project health** across 9 categories, with weights
  summing to exactly 1.00. Most general contractors have nothing like this.
- Consistent RAG vocabulary and 15 controlled pick-lists — real data discipline.
- A slippage warning that compares actual pace against **baseline pace** rather than a
  fixed threshold (`DASHBOARD!O21`). That is a genuinely sophisticated calculation.

The scorecard is the most valuable thing in the file and the highest-leverage piece to
rebuild correctly.

### Findings — three that change reported numbers

Full detail and arithmetic in
[`../analysis/excel-tracker/defects-and-questions.md`](../analysis/excel-tracker/defects-and-questions.md).

**(a) Three of nine scorecard categories aren't currently measuring anything — 42% of the
total weight.**

| Category | Weight | What happens |
|---|---|---|
| Schedule Performance | 0.15 | `L19` is a fraction (`0.4` = 40%); the bands compare it to `5`/`9`/`10`. `0.4 <= 5` is always true → **always scores 3/3**, even at 100% missed starts |
| Completion Variance | 0.15 | `M16` returns the **text** `"0 days"` when variance is zero. Excel ranks text above numbers, so all three bands fail → **always scores 0/3**, even finishing exactly on baseline |
| Accounts Receivable | 0.12 | Reads `AT25` = aging **balance** (dollars) against bands that are **day counts**. `AT27` (8.82 avg days to payment) looks like the intended driver |

The first two errors are `+0.15` and `−0.15` — **they cancel**, netting to the same `0.59`.
That is why this hasn't surfaced before.

**(b) Quality observations are reading Safety orientations.**
`QUALITY!D5` = `=SAFETY!F5` and `D6` = `=SAFETY!F6`. Two of 31 rows; every other row is
hand-entered. An isolated copy-paste.

**(c) Open violations are counted by dollar value, not status.**
`DASHBOARD!AM57` = `COUNTIF(SAFETY!L3:L26,">1")`. A **$0 open violation** — a stop-work
order, an unfined citation — is currently invisible.

Eleven further findings in the doc: mixed month anchors across tabs, `TODAY()` making saved
reports non-reproducible, two inverted milestone date pairs, placeholder buyout figures, and
trailing whitespace on 12 trade names.

### The manual-data question

**~40% of the report exists nowhere but the workbook** — wins, the full risk register,
recovery-plan narratives, client survey, cost-management flags, profitability judgment. No
amount of Procore or Sage integration produces these.

Proposal: a **slim, locked-down input workbook on SharePoint** that Fabric ingests
nightly. Lowest change-management cost — PMs keep working the way they already do. Spec
ready at [`../powerbi/manual-input-template.md`](../powerbi/manual-input-template.md).

Alternatives if that doesn't fit: Power App / Dataverse forms (better data quality, more
build effort plus licensing), or Procore custom fields (best single-source-of-truth story,
requires config work and a change in PM habits).

### Request: real project data

The file received is a **template** — `Kitchen Cabinet Design` ×5, `Critical Path Item 1–9`,
`Sub 1–5`, a `$200M` buyout against a `$9.1M` contract, `99999` hours. **2–3 completed real
project reports** would let us seed history and confirm the schema survives contact with
actual data.

---

## 4. The Procore ↔ Sage connector decision (5 min)

Affect has purchased the Procore ↔ Sage 100 Contractor connector but hasn't rolled it out.
Verified sync directions:

- Jobs, Cost Codes, Budgets, Vendors — **bidirectional**
- Commitments, Commitment COs, Sub Invoices — **Procore → Sage**
- **Job Costs, Sub Jobs/Phases — Sage → Procore**

**The question:** if job costs will flow Sage → Procore anyway, do we build a separate Sage
job-cost pull now, or wait for the rollout?

If we wait, the Sage ingestion narrows to **AR invoices, cash receipts, retainage, and
aging** — none of which the connector syncs. That roughly halves that phase of the work.
What does the rollout timeline look like?

---

## 5. Open questions

1. ⚠️ **What is the shared project identifier across Procore, Sage, and the reporting
   template?** The `YY-000` filename convention suggests a job number — is that the Procore
   project number, the Sage job number, or a third thing? **Nothing in the data model joins
   without this.**
2. **Do cost codes reconcile** between Procore and Sage?
3. **Where do critical-path milestones live?** ⚠️ The Procore API has **no `milestone`
   endpoint** — `/schedule` returns tasks. Is it Procore, Outbuild, or only the
   spreadsheet? This determines whether the Schedule page has a data source at all.
4. **What defines "critical"** for RFIs and Submittals? Procore has a priority field.
5. **Is % complete meant to be time-elapsed or work-in-place?** The current formula is
   purely calendar days. Procore supports % complete by cost, which is more defensible —
   and this feeds a 15%-weighted scorecard category.
6. **Should cash position stay a dropdown?** The formula is already written out in
   `FINANCIALS!G8` and is computable from Sage. Deriving it removes one of three subjective
   inputs to the scorecard.
7. **Are the scorecard weights settled, or still being tuned?**
8. **What was `DASHBOARD!AU2`?** It holds a live `#VALUE!` error and the original formula
   isn't recoverable from the file.
9. **What are the six client-satisfaction questions?** Only the scores are stored.
10. **Is the GC/GR budget section abandoned or mid-build?** Two rows, a `SPENT TO DATE2`
    header, and a status column that contradicts its own legend.
11. **How many active projects** should the dashboard cover?

---

## 6. Next steps

**Proposed first deliverable:** `fct_RfiSubmittal` end to end — Procore API → Lakehouse →
one chart. It's the cleanest table in the workbook, it feeds the only chart that already
exists, and it proves the whole pipeline on the lowest-risk data. Something visible and
working quickly.

**Access checklist**
- [ ] NDA
- [ ] Fabric workspace
- [ ] Procore API credentials
- [ ] Sage read-only SQL
- [ ] SharePoint site for the input workbook
- [ ] 2–3 real completed project reports
- [ ] Client-satisfaction questionnaire

**Also to confirm:** bi-weekly sync cadence, and that a written scope follows this call.

---

## Reference material

| Doc | Covers |
|---|---|
| [`../analysis/excel-tracker/README.md`](../analysis/excel-tracker/README.md) | How the workbook is structured and how the monthly cycle works |
| [`../analysis/excel-tracker/defects-and-questions.md`](../analysis/excel-tracker/defects-and-questions.md) | All 14 findings with cell references, plus the open questions |
| [`../analysis/excel-tracker/field-inventory.md`](../analysis/excel-tracker/field-inventory.md) | Every field: manual / calculated / which system should own it |
| [`../powerbi/semantic-model.md`](../powerbi/semantic-model.md) | The proposed data model |
| [`../powerbi/manual-input-template.md`](../powerbi/manual-input-template.md) | The manual-data proposal |
| [`../resources/procore/endpoints-cheatsheet.md`](../resources/procore/endpoints-cheatsheet.md) | Procore endpoints, for checking ETL coverage |
| [`../resources/sage-100-contractor/README.md`](../resources/sage-100-contractor/README.md) | Sage documentation, corrected |
| [`../powerbi/build-plan.md`](../powerbi/build-plan.md) | Phases, estimates, reconciliation gate |
