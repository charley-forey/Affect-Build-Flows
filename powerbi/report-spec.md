# Report Spec

Page layout, visuals, and formatting for the Power BI report replacing the Excel Monthly
Progress Report.

Model: [`semantic-model.md`](semantic-model.md) · Measures: [`measures.dax`](measures.dax)
· Theme: [`theme.json`](theme.json)

## Principle: rebuild the report, not the spreadsheet

The Excel layout — 53 narrow merged columns, hardcoded six-row spacing between wins,
Quality and Financial interleaved in the same column range — exists to fit one printable
page. None of it is design. Reproducing it literally would inherit every constraint for
none of the benefit.

What carries over: **the eight sections, the RAG vocabulary, and the scorecard weighting.**
That is the business logic Affect built and it is worth preserving exactly.

What changes: numeric tiles instead of text strings, unbounded tables instead of capped
lists, real charts where the Excel had one, and month-over-month trend where the Excel had
a single snapshot.

---

## Color

### Status (RAG) — reserved

Status colors are **never** used for series identity. Affect's existing red/amber/green
vocabulary is preserved semantically, but two of the three steps were corrected:

| Meaning | Workbook value | Report value | Why changed |
|---|---|---|---|
| Green / On Track | `#01AF00` | `#1B7F3B` | Original measured **2.87:1** contrast on a light surface — below the 3:1 floor |
| Amber / Watch | `#FFD800` | `#B26A00` | Original measured **1.36:1** — effectively invisible on white |
| Red / At Risk | `#DB1918` | `#C62828` | Adjusted for consistency with the other two steps |
| Neutral / Low / N/A | `#A6A6A6` | `#6B6B6B` | Contrast |

Dark-mode steps: `#3FA55F` · `#C98500` · `#EF5350` · `#9A9A96`. All four clear 3:1 against
the dark surface.

> **Verified by running the palette validator, not by eye.** Both the original and the
> corrected sets were measured. The finding on `#FFD800` is worth mentioning to Affect —
> the amber in their current workbook is genuinely hard to read, which is a plausible
> reason "Watch" status gets overlooked.

### The RAG accessibility rule — non-negotiable

**Red/amber/green cannot be made colorblind-safe as color alone.** Measured red↔green
separation is ΔE 7.1 under deuteranopia — below the ΔE 8 floor — and no re-stepping fixes
it, because the deficiency is in the hue pair itself. Roughly 1 in 12 men cannot reliably
tell the two apart.

**Therefore: every status indicator in this report ships with an icon or a text label
beside the color. Never color alone.**

Affect's workbook already does this — `🔴 High`, `🟢 On Track` — so this is not a new
constraint, it is their existing convention made explicit and enforced. In Power BI, use
a status **icon column** plus the text label; drive both from `dim_Status`.

### Series (categorical) — identity only

| Slot | Hex (light) | Hex (dark) | Used for |
|---|---|---|---|
| 1 | `#2a78d6` blue | `#3987e5` | Open Critical RFIs |
| 2 | `#eb6834` orange | `#d95926` | Open Critical Submittals |
| 3–8 | see `theme.json` | | Reserved for future series |

Slots 1 and 2 pass every validator check in both modes (CVD ΔE 24.7 light / 26.8 dark;
normal-vision ΔE 33.6 / 31.8; both ≥ 3:1 contrast). Assign in fixed order — a series keeps
its color when a filter changes the series count.

---

## Number formats

Carried from the workbook so the output is recognisable to its current readers.

| Type | Format | Example |
|---|---|---|
| Currency (tiles) | `$#,##0` | `$9,116,960` |
| Currency (detail) | `$#,##0.00` | `$299,746.97` |
| Percent | `0.0%` | `32.9%` |
| Percent (scorecard) | `0%` | `59%` |
| Days | `#,##0` + " days" suffix | `49 days` |
| Dates | `MM/DD/YYYY` | `05/07/2026` |
| Month header | `MMMM YYYY` | `May 2025` |
| Counts | `#,##0` | `4,635` |

**Never** concatenate a value and a percentage into one string (the Excel's
`"$2,997,804.2 / 32.9%"`). Use a card with the value as the callout and the percentage as
the subtitle — same visual result, and both stay numeric.

---

## Page structure

Six pages. The Excel's single canvas becomes an overview plus four detail pages and a
hidden diagnostics page.

### Page 1 — Overview (the one-page replacement)

Fits the Excel's eight sections onto one 16:9 canvas. This is the page that gets exported
to PDF and circulated.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Affect Group — Monthly Progress Report      [Project ▾] [Month ▾]        │
├─────────────┬────────────────────────────────┬───────────────────────────┤
│ SCORECARD   │  SCHEDULE                      │  FINANCIAL                │
│             │  ┌──────┬──────┬──────┐        │  Current Contract  $9.1M  │
│    59%      │  │Cmpl. │Missed│  %   │        │  Variance          +3.6%  │
│  ▓▓▓░░ Watch│  │Var.  │Starts│Compl.│        │  Total Billed  $3.0M/32.9%│
│             │  │  0d  │ 40%  │ 74.9%│        │  Total Paid    $2.7M/29.4%│
│ Client Sat  │  └──────┴──────┴──────┘        │  Retainage     $127K/1.4% │
│    60%      │  ⚠ Warning — provide Recovery  │  Cost to Complete  $6.8M  │
│  ▓▓▓░░ Watch│                                │  ──────────────────────── │
│             │  Contract  01/09/25 → 05/07/26 │  Bought Out         95.0% │
├─────────────┤  Baseline  01/08/25 → 06/25/26 │  Avg Days to Pay      8.8 │
│ WINS        │  Current   01/08/25 → 06/25/26 │  Cash Position    🔴 Bad  │
│ • Topped Out│  Actual    01/08/25 → TBD      │  Profitability 🔴 Margin  │
│ • Submittals│                                │              fade, no plan│
│ • No accid. ├────────────────────────────────┼───────────────────────────┤
│ • PSWO      │  SAFETY                        │  CRITICAL RFIs & SUBMITTALS│
├─────────────┤  Hours  4,635 ▲9.7% │ 114,231  │  ▇▇▇▇▇▇▇▇ Electrical      │
│ FOCUS AREAS │  Incidents      0   │       1  │  ▇▇▇▇▇ HVAC               │
│ • …         │  Orient.   17 ▼29%  │     120  │  ▇▇▇▇ Windows             │
│ • …         │  Violations $1,000  │  1 open  │  ▇▇▇▇ Metals              │
├─────────────┼────────────────────────────────┤  ■ RFIs  ■ Submittals     │
│ QUALITY     │  RISKS (Ranked by Severity)    │                           │
│ Obs.  17/77 │  🔴 High   Kitchen Cabinet …   │                           │
│ Punch  0/0  │  🟡 Medium Change Orders …     │                           │
│ Days due  1 │  🟡 Medium Access Agreements…  │                           │
│ Days close 2│  ⚪ Low    Kitchen Cabinet …   │                           │
└─────────────┴────────────────────────────────┴───────────────────────────┘
```

**Slicers** (top right, one row): `dim_Project[ProjectName]` single-select ·
`dim_Date[MonthStart]` single-select. These two replace `DASHBOARD!AU4` entirely.

**Visuals**

| Section | Visual | Notes |
|---|---|---|
| Scorecard | KPI card + horizontal band | `[Project Scorecard]`, colored by `[Scorecard Color]`, **with the band label beside it** |
| Client Satisfaction | KPI card + band | `[Client Satisfaction]` |
| Wins / Focus Areas | Table, no header, single column | `man_Wins` / `man_FocusAreas`. **No 4-item cap** |
| Schedule KPI row | 3 cards | Completion variance, missed starts %, % complete |
| Schedule warnings | Text box, conditional | `[Completion Variance Flag]`, `[Missed Starts Flag]`, `[Schedule Slippage Flag]` |
| Schedule date matrix | Matrix, 4 rows × 2 cols | Contract / Baseline / Current / Actual × Start / Finish |
| Financial waterfall | Multi-row card | Value + % subtitle per line |
| Financial judgments | Cards with status icon | Cash position, profitability — **icon + label, per the RAG rule** |
| Safety | Multi-row card, 4 rows | This period / MoM / to date |
| Risks | Table | **Sorted by `dim_Status[SortOrder]`** — makes the header honest for the first time |
| RFIs & Submittals | Clustered bar | The one visual carried over. Series slots 1–2, sorted descending by total |

### Page 2 — Schedule Detail

- Milestone table: `fct_Milestone` — all four date pairs, both variance columns, conditional
  formatting on variance, **including `MilestoneName`** (never shown on the Excel dashboard).
- **Gantt or timeline visual** — baseline vs. current vs. actual bars per milestone. The
  Excel could not do this at all; it is the single biggest visual gain.
- Priority items table: `man_PriorityItems`, **with the item name attached** to each
  recovery plan (the Excel showed the narrative without saying which item it belonged to).
- Manpower: line chart of `[Avg Daily Manpower]` by day, legend by vendor. No 5-sub cap.
- Baseline approval + revision cards.
- **Trend:** `[Completion Variance vs Baseline]` by month — shows whether the finish date
  is drifting, which a single-month snapshot cannot.

### Page 3 — Financial Detail

- Budget vs forecast vs spent by cost code: `fct_BudgetLine`, with `[Budget Status]`
  **derived** rather than hand-picked (fixes the GC/GR inconsistency in the workbook).
- Invoice aging: `fct_Invoice`, scatter of days-to-payment over time + `[Avg Days To Payment]`.
- Change orders: `fct_ChangeOrder`, with `[Age Of Oldest Unapproved CO]`.
- Contract movement: line chart, original vs current contract by month.
- Cash position over time — line chart of `[Cash Position %]` with the 100% / 50% band
  thresholds as reference lines.

### Page 4 — Safety & Quality Detail

- Safety monthly trend: hours worked (bars) with incidents overlaid. **Two charts, not a
  dual axis** — different scales never share a y-axis.
- `[TRIR]` card — standard industry rate, free once hours and incidents are in the model.
- Violations table: `fct_Violation`, filtered by **status** (fixes defect #3).
- Safety activity log: `fct_ActivityLog`, split by Lookback / Lookahead.
- Observations & punchlist trend by month.
- Main offenders: bar chart ranked by `[Open Quality Items]` — replaces the hand-typed list.
- Quality issue log: `fct_QualityItem` with drill-through to the item.

### Page 5 — Scorecard Detail

- The nine categories as a table: category · driver value · band · score · weight ·
  weighted contribution. Makes the score **auditable**, which the Excel's nested `IF`s were
  not — and is how the three dead bands would have been caught.
- `[Project Scorecard MoM]` — trend over time. New capability.
- Client satisfaction breakdown by question. **Requires the question text**, which is not
  stored anywhere in the workbook (open question #10).
- Weight table from `dim_ScorecardWeight`, shown read-only so reviewers can see what the
  score is actually weighting.

### Page 6 — Data Quality (hidden)

Not for the client — for whoever maintains the model.

- `[Data Quality Issues]`, `[Milestones With Date Inversion]`
- Rows failing referential integrity (unmatched status codes, unmatched trades)
- Months present in a fact but missing from `dim_Date`
- Last refresh timestamp and row counts per table

The Excel had no equivalent. That is precisely how the inverted milestone dates and the
$200M placeholder buyout survived into a report going to leadership.

---

## Interaction

- **Cross-filtering on**, cross-highlighting off — highlighting on a status-colored visual
  produces washed-out colors that break the RAG reading.
- **Drill-through** to Schedule Detail from any milestone; to Financial Detail from any
  money card; to the quality item from any offender bar.
- **Tooltips** on every chart. Report-page tooltips for the milestone bars showing all four
  date pairs.
- **Bookmarks** for Monthly View (default) and Trend View.
- **Sync slicers** across all pages so project and month selection persists.

## Export

The workbook's current output is a printed/PDF'd sheet. Page 1 must export cleanly:

- Canvas 16:9, "Fit to page"
- No visual dependent on hover to be readable
- Every status carries its icon and label so the PDF works in **greyscale** — which is the
  same rule as the CVD rule, satisfied by the same design
- `[Last Refresh]` and `[Report Month Label]` in the footer so a printed copy states what
  it is a snapshot of. The Excel could not, because `TODAY()` meant a saved file silently
  re-reported itself (defect #5).

## Accessibility checklist

- [ ] Every status: icon or label alongside color, never color alone
- [ ] Alt text on every visual
- [ ] Tab order set on each page
- [ ] Two series ⇒ legend present; ≤ 4 series ⇒ also direct-labeled
- [ ] No dual-axis charts anywhere
- [ ] Table view available for every chart (Power BI's "Show as table")
- [ ] Theme validated in both light and dark
- [ ] Greyscale print test on page 1

## Deliberate omissions from the Excel

| Not carried over | Why |
|---|---|
| `DASHBOARD!AU2` `#VALUE!` | An error; the original formula is unrecoverable from the file |
| The `"$X / Y%"` string tiles | Split into numeric pairs — same look, chartable |
| Hand-pasted "Previous Month" row | `DATEADD` does it |
| `FINANCIALS` "LAST PERIOD" column | Rows over time replace a column pair |
| Hand-typed quality averages | Computed from `fct_QualityItem` |
| Hand-typed "main offenders" | `RANKX` |
| Hand-picked budget status | Derived from the rule already in `FINANCIALS!H18:J21` |
| Emoji embedded in status strings | `dim_Status` — emoji retained as a display column for export parity |
| Every list cap (4/5/8/10) | Table visuals, unbounded |
| `TODAY()` | Anchored to the selected reporting month |
