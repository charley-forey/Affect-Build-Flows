# Defects & Open Questions

14 defects found by extraction and verified against the workbook's own cached values.

**None of these have been fixed.** The client's file is untouched — this is a findings
list, not a change log. Several are worth raising diplomatically: the workbook is clearly
a genuine, thoughtful piece of work, and most of these are the kind of drift any
hand-maintained spreadsheet accumulates.

Severity: 🔴 changes a reported number · 🟡 will break under normal use · ⚪ hygiene

---

## 🔴 1. Three of nine scorecard categories are not measuring anything

**42% of the total weight is disconnected from project reality.** Grouping the three
together because they share one root cause: the scorecard was written against cells whose
type or scale differs from what the band logic assumes.

### 1a. Schedule Performance — always awards full marks (weight 0.15)

`SCORECARD CALC!E19`:
```excel
=IF(DASHBOARD!L19<=5,'SCORECARD CALC'!C19,
 IF(DASHBOARD!L19<=9,'SCORECARD CALC'!C20,
 IF(DASHBOARD!L19>=10,'SCORECARD CALC'!C21,0)))
```

`DASHBOARD!L19` is a **fraction** — currently `0.4`, meaning 40% of started milestones
started late. The bands read `<5%` / `6–9%` / `10%+`, but they compare against the raw
numbers `5`, `9`, `10`.

`0.4 <= 5` is TRUE, so it scores 3 out of 3. It always will: the metric cannot exceed
`1.0`, so it can never reach even the second band. **A project with 100% missed starts
still scores full marks on schedule performance.**

*Verified:* cached `E19` = `3` with `L19` = `0.4`.

**Fix:** compare against `0.05`, `0.09`, `0.10`. The dashboard's own warning at `O19`
already does this correctly (`IF(L19>0.2,...)`), so the intent is not in doubt.

### 1b. Completion Variance — always awards zero (weight 0.15)

`SCORECARD CALC!E22`:
```excel
=IF(DASHBOARD!M16<=0,'SCORECARD CALC'!C22,
 IF(DASHBOARD!M16<=14,'SCORECARD CALC'!C23,
 IF(DASHBOARD!M16>=15,'SCORECARD CALC'!C24,0)))
```

`DASHBOARD!M16` is:
```excel
=+IF((O12-O11)=0,"0 days",O12-O11)
```

When the variance is zero it returns the **text** `"0 days"`. Excel ranks text above every
number, so all three comparisons fail and the formula falls through to the literal `0`.

**A project finishing exactly on baseline — the best possible outcome — scores 0 out of 3
on a 15%-weighted category.** That is this project's current state.

*Verified:* cached `E22` = `0` with `M16` = `"0 days"`.

**Fix:** keep `M16` numeric and format the zero for display instead of substituting text.

### 1c. Accounts Receivable — reads the wrong cell (weight 0.12)

`SCORECARD CALC!E4` reads `DASHBOARD!AT25`, which is `=+FINANCIALS!F57` — the **current
aging balance** (a dollar amount, currently `1`). The bands are `< 45` / `46–60` / `61–75`,
which are plainly **day counts**.

`DASHBOARD!AT27` (`=FINANCIALS!F56`, avg days for payment received, `8.82`) is almost
certainly the intended driver — it is a day count, it sits two cells away, and the
category is named "Accounts Receivable".

*Verified:* cached `E4` = `3` because `1 < 45`.

**Fix:** point at `AT27`. Worth confirming with Rebecca since this is her domain.

> **Combined effect today:** Schedule Performance contributes a spurious `+0.15`,
> Completion Variance a spurious `−0.15`. They roughly cancel, so the headline `0.59`
> looks plausible — which is exactly why this has gone unnoticed.

---

## 🔴 2. Quality observations are reading Safety orientations

`QUALITY!D5` = `=SAFETY!F5` and `QUALITY!D6` = `=SAFETY!F6`.

Column `QUALITY!D` is "OBSERVATIONS THIS PERIOD". Column `SAFETY!F` is "ORIENTATIONS THIS
PERIOD". Two of the 31 month rows pull the wrong metric from the wrong sheet.

Every other row in that column (3, 4, 7 onward) is a hand-entered number, so this is an
isolated copy-paste, not a designed link. It feeds `QUALITY!D35` (total observations) and
therefore `DASHBOARD!M64`.

**Fix:** replace with manual entry, or wire the whole column to Procore observations.

---

## 🔴 3. Open violations are counted by dollar value, not status

`DASHBOARD!AM57`, labelled "Total Open":
```excel
=COUNTIF(SAFETY!L3:L26,">1")
```

`SAFETY!L` is `IF(Status="Open", Value, " ")`. So this counts violations whose **dollar
value exceeds 1** — not violations that are open.

A `$0` open violation is invisible. That includes stop-work orders, warnings, and any
citation not yet assessed a fine — arguably the ones you most want on a dashboard.

*Verified:* cached `AM57` = `1`, matching the single violation with a non-zero value
(VLN #2, `$1,000`), while several other rows are also `Open` with value `0`.

**Fix:** `COUNTIFS(SAFETY!K3:K26,"Open")`.

---

## 🟡 4. Three different month anchors in one workbook

The `INDEX/MATCH` scheme requires every monthly table to contain the exact date in `AU4`.
They do not agree:

| Table | Seed month | Note |
|---|---|---|
| `SAFETY!C3` | `2025-01-01` | |
| `QUALITY!C3` | `2025-01-01` | |
| `FINANCIALS!I25` (OT hours) | `2025-01-01` | |
| `FINANCIALS!C25` (invoices) | `2025-11-01` | ⚠️ 10 months adrift |

Worse, the invoice table's **month labels and its own data disagree**: `C25` says
`2025-11-01` while `D25`/`E25` hold invoice dates of `2024-11-07` / `2024-11-14` — a full
year apart.

Any `INDEX/MATCH` that reaches across a mismatch returns `#N/A`, on a report going to
leadership, with no warning.

**Fix:** in Power BI this cannot happen — one `dim_Date` serves every fact table.

---

## 🟡 5. `TODAY()` makes the report non-reproducible

`DASHBOARD!L21` (project % complete) and `O21` (slippage warning) both call `TODAY()`.

Reopening a saved report shows different numbers than it did when issued. Last month's
archived file is not a record of last month — it silently re-reports itself as of today.
For a monthly progress report that is later referenced in disputes or claims, that is a
real problem.

**Fix:** anchor to the selected reporting date, not the system clock. See
`../../powerbi/measures.dax` → `Project % Complete (Time)`.

---

## 🟡 6. Milestone dates are inverted on two rows

| Row | Contract Start | Contract Finish |
|---|---|---|
| `SCHEDULE` 12 | `2026-05-14` | `2026-05-07` ⚠️ finishes 7 days before it starts |
| `SCHEDULE` 13 | `2026-06-11` | `2026-05-07` ⚠️ finishes 35 days before it starts |

Row 13's baseline (`2026-06-25`) is also later than its current forecast (`2026-04-30`),
implying the milestone was pulled forward by ~8 weeks.

Nothing in the workbook validates start ≤ finish, so these flow straight into the `MIN`/
`MAX` rollups. **Fix:** add a `StartAfterFinish` data-quality flag in the model.

---

## 🟡 7. `"NA"` sentinels make date columns mixed-type

`SCHEDULE!D:K` use the string `"NA"` for unknown dates, per the sheet's own instruction:
*"ALL BLANKS CELL SHOULD RECEIVE AN NA"*.

Every downstream formula must then guard with `IF(...="NA",...)`. It works, but it is why
`DASHBOARD!O14` and `P14` display `"TBD"` instead of a value, and it is why the variance
columns return `""` rather than blank.

**Fix:** convert to real nulls at ingestion. `DATEDIFF` handles nulls natively.

---

## 🟡 8. Dashboard tiles are text strings

Every money tile (`AT14:AT19`), the OT hours tile (`AT40`), and three of four safety tiles
(`AI48`, `AI54`, `AI57`) are built with `TEXT(...) & " / " & TEXT(...)`.

The result cannot be charted, sorted, trended, conditionally formatted, or compared. It is
the reason the workbook has one chart.

Also: the MoM percentage divides by the prior month's value with no guard, so any month
following a zero produces `#DIV/0!`. On a new project the first several months are zero.

**Fix:** two numeric measures per tile. `DIVIDE()` returns blank instead of erroring.

---

## 🟡 9. Twelve trade names have trailing whitespace

`DROPDOWN!M` — `"Existing Conditions  "`, `"Concrete  "`, `"Metals  "`, `"Masonry  "`,
`"Finishes  "`, `"Specialties  "`, `"Equipment  "`, `"Conveying Equipment  "`,
`"Plumbing  "`, `"Building Automation Systems  "`, `"Electrical  "`, `"Utilities  "`,
`"Painting "`.

`"Metals  "` will never equal `"Metals"` in a join to Procore or Sage. Also `DROPDOWN!L`
(quality status) has `"🟢  Passed"` twice and uses a **double** space after every emoji,
unlike every other list.

**Fix:** `TRIM()` at ingestion; dedupe in `dim_Trade` / `dim_Status`.

---

## ⚪ 10. `DASHBOARD!AU2` is a live `#VALUE!` error

An error sits directly above the reporting-month anchor with no visible label. The cell
stores the literal error string, so the original formula is **not recoverable from the
file** — only Affect knows what it was.

**Question for the call:** what was `AU2` meant to show?

---

## ⚪ 11. Arithmetic entered into value cells

```excel
FINANCIALS!C5  =65000+3158.46+11550+4620     ' Pending CO's → 84,328.46
SAFETY!D7      =4001+16+178+356+84           ' Hours worked → 4,635
SAFETY!D8      99999                         ' Hours worked → obvious placeholder
```

Each addend is presumably a real change order or a real crew's hours, and that detail is
lost the moment someone edits the cell. In the target model these are rows in a fact table
that roll up automatically.

---

## ⚪ 12. Placeholder data left in the buyout section

`FINANCIALS!D60` = `$200,000,000` budgeted, `D61` = `$190,000,001` committed — against a
`$9,116,960` contract. The resulting **95% bought out** flows to `DASHBOARD!AT23` and is
presented as real.

`SAFETY!D8` = `99999` hours is the same class of leftover.

---

## ⚪ 13. Unfinished GC/GR budget section

`Table11011` (`FINANCIALS!B18:F21`) has:
- Only **two data rows** (General Requirements, General Conditions)
- A column header reading **`SPENT TO DATE2`** — a stray suffix
- A `MONTH` header over a column that actually holds cost-category names
- A status column that is **hand-picked** despite the derivation rule being written out
  two columns away in `H18:J21`

The two current values also look inverted relative to that rule: GR's at 5% of budget spent
is flagged 🔴 Over Budget; GC's at 2.4% is 🟢 On Track. See `dashboard-map.md` §6.

**Question:** is this section abandoned, or mid-build? It is the only place the report
touches cost codes at all.

---

## ⚪ 14. Cosmetic and naming inconsistencies

- `INSTRUCTIONS` refers to a *"Scorecard Tab"* and an *"RFIs & Submittals Tab"*; the actual
  tabs are `SCORECARD CALC` and `SUBMITTALS & RFI`.
- `SUBMITTALS & RFI` lists **`Metals` twice** (`B6`, `B9`); rows 12–13 are unnamed zeros.
- `SCORECARD CALC!B19` reads *"Critcal Missed Starts"* (typo).
- `RISKS!C6:C10` all read *"Kitchen Cabinet Design"* — clearly demo data.
- `SCHEDULE!N4:N14` are blue (input-marked) but unlabelled and empty.
- Three source columns are never displayed on the dashboard: `RISKS!B` (risk #),
  `SCHEDULE!C` (schedule item name — so recovery plans appear with no item attached),
  `SAFETY!I` (VLN description, which is empty in every row anyway).
- Every list has a hard cap: 4 wins, 4 focus areas, 8 risks, 5 priority items, 5 subs,
  5 safety entries, 10 quality entries, 11 trades, 24 violations.

---

# Open questions for Affect

Ordered by how much they block the build.

## Blocking — nothing gets built without these

1. **What is the shared project identifier across Procore, Sage 100 Contractor, and this
   workbook?** The filename convention `YY-000 PROJECT NAME` suggests a `YY-000` job
   number. Is that the Procore project number, the Sage job number, or a third thing? Is
   it entered identically in both systems? *This is the linchpin — nothing joins without it.*

2. **Do cost codes reconcile between Procore and Sage?** Same list, same format, same
   segmentation? Or does each system have its own and someone maps them by hand?

3. **Where should the ~40% manual data live?** Recommendation is a locked-down input
   workbook on SharePoint that Fabric ingests on a schedule — lowest change-management
   cost, PMs keep working the way they do today. See
   [`../../powerbi/manual-input-template.md`](../../powerbi/manual-input-template.md).

## High value — changes what we build

4. **Once the Procore ↔ Sage 100 Contractor connector is live, does the Lakehouse still
   need a separate Sage job-cost pull?** The connector pushes job costs Sage → Procore. If
   actuals land in Procore anyway, the Sage ingestion narrows to AR/AP/payments/retainage —
   materially less work. (Rebecca noted the connector is bought but not yet rolled out.)

5. **What does "critical" mean for RFIs and Submittals?** Procore has a priority field —
   is that the criterion, or is it a judgment call by the PM?

6. **Is project % complete meant to be time-elapsed or work-in-place?** The current formula
   is purely calendar-based. Procore budget line items support % complete by cost, which is
   a much more defensible number. Which does Affect want on the scorecard?

7. **Should cash position stay a dropdown?** The formula is already written out in
   `FINANCIALS!G8` and is fully computable from Sage. Converting it to a measure removes one
   of three subjective inputs to the scorecard.

8. **Is the scorecard weighting settled, or still being tuned?** Building it as a
   `dim_ScorecardWeight` table lets Affect retune without a model change — worth doing
   either way, but especially if the weights are still moving.

## Clarifying — needed for completeness

9. What was `DASHBOARD!AU2` meant to show?
10. What are the six client-satisfaction questions? Only the scores are stored, not the
    questions.
11. Is the GC/GR budget section abandoned or mid-build? Should it expand to full cost-code
    coverage?
12. Are toolbox talks, standdowns, and notable visitors tracked anywhere else (Procore
    Daily Logs?), or is this workbook the only record?
13. Where do safety orientations get recorded today?
14. Should the 29 trades map to CSI MasterFormat divisions? That would let them join
    directly to Procore cost codes.
15. Is the intended reporting cadence strictly monthly, or would Affect want weekly or
    live once it is in Power BI?
16. Is one workbook per project the model — and if so, how many active projects would the
    dashboard need to cover?

## Correction to carry into the call

> The Sage documentation link in the Jul 22 email
> (`help-sage100.na.sage.com/2023/FLOR/…`) is the **File Layouts and Object Reference for
> Sage 100 ERP** (Standard/Advanced/Premium) — a different product from **Sage 100
> Contractor**, which is what Affect runs and what Procore's connector supports.
>
> The correct schema references are the *Sage 100 Contractor Database and Company
> Administration Guide* PDFs on `docs.sage.com`. Links collected in
> [`../../resources/sage-100-contractor/README.md`](../../resources/sage-100-contractor/README.md).
>
> Worth raising early — it determines which schema the ingestion is written against.
