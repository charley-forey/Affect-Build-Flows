# Field Inventory

Every field in the workbook: where it lives, how it's populated today, and which system
should own it in the target architecture.

**Type legend**

| Code | Meaning |
|---|---|
| `IN` | Manual input (blue text `#2334D4`) |
| `DD` | Manual input constrained by a drop-down list |
| `FX` | Formula — calculated within the input tabs |
| `DSP` | Display-only — a `DASHBOARD` cell that just references elsewhere |

**Source legend**

| Code | Meaning |
|---|---|
| `PROCORE` | Available from the Procore API today |
| `SAGE` | Available from Sage 100 Contractor |
| `EITHER` | Available in both — needs a system-of-record decision |
| `MANUAL` | Exists nowhere but this workbook — needs a new home |
| `DERIVED` | Computed from other fields; becomes a DAX measure |

---

## WINS

Grain: one row per win, max 4 realized + 4 upcoming, per project per month.

| Cell / Range | Field | Type | Source | Notes |
|---|---|---|---|---|
| `B3:B6` | WIN # (`WIN 1`–`WIN 4`) | fixed label | `DERIVED` | Just a row ordinal |
| `C3:C6` | Win description | `IN` | `MANUAL` | Free text. Header warns *"TEXT NEEDS TO FIT IN THE COLUM WIDTH AND HEIGHT"* — a pure layout constraint that disappears in Power BI |
| `B9:B12` | FA # (`FA 1`–`FA 4`) | fixed label | `DERIVED` | |
| `C9:C12` | Focus area description | `IN` | `MANUAL` | Next month's priorities |

**Fixed cap of 4 + 4.** The dashboard hard-references `WINS!C3`, `C4`, `C5`, `C6` — a
5th win would not appear. In Power BI this becomes an unbounded list visual.

---

## SCHEDULE

### Milestones — `Table5` (C3:M14)

Grain: one row per critical-path milestone. Row 14 is a **protected terminator**
(`Contractural Substaintial Completion [DO NOT DELETE THIS LINE]`). Row 4 is a locked
rollup. Sheet instructions: *"ALL BLANKS CELL SHOULD RECEIVE AN NA"*, *"NEVER HAVE ANY BLANK ROWS"*.

| Column | Field | Type | Source | Notes |
|---|---|---|---|---|
| `C` | TASK | `IN` | `PROCORE` | Milestone name. Procore Schedule tasks, or Outbuild |
| `D` | CONTRACT START | `IN` | `MANUAL` | Contract dates are not in Procore's schedule tool |
| `E` | CONTRACT FINISH | `IN` | `MANUAL` | |
| `F` | BASELINE START | `IN` | `PROCORE` | Procore schedule baseline, if baselines are maintained there |
| `G` | BASELINE FINISH | `IN` | `PROCORE` | |
| `H` | CURRENT START | `IN` | `PROCORE` | Current forecast |
| `I` | CURRENT FINISH | `IN` | `PROCORE` | |
| `J` | ACTUAL START | `IN` | `PROCORE` | `"NA"` string when not started |
| `K` | ACTUAL FINISH | `IN` | `PROCORE` | `"NA"` string when not finished |
| `L` | START VARIANCE | `FX` | `DERIVED` | `ACTUAL START − BASELINE START`, blank if `"NA"` |
| `M` | FINISH VARIANCE | `FX` | `DERIVED` | `CURRENT FINISH − BASELINE FINISH`, blank if `"NA"` |
| `D4:K4` | Project rollup | `FX` | `DERIVED` | `MIN` of starts, `MAX` of finishes over rows 5–14 |
| `N4:N14` | (blue, unlabeled) | `IN` | `MANUAL` | Appears unused — confirm with Affect |

> **`"NA"` as a sentinel in date columns** makes each column mixed-type. Every consumer
> formula has to `IF(...="NA", ...)` around it. In the model these become proper nulls.

### Baseline approval

| Cell | Field | Type | Source | Notes |
|---|---|---|---|---|
| `G16` | Baseline Approved by Client | `DD` | `MANUAL` | `DROPDOWN!F4:F15` → `🟢 Y` / `🔴 N` |
| `G17` | Baseline Revision | `DD` | `MANUAL` | `DROPDOWN!G4:G15` → `Rev#1`–`Rev#11` |

### Month-to-month milestone comparison (C20:K22)

| Cell | Field | Type | Source | Notes |
|---|---|---|---|---|
| `E20`,`G20`,`I20`,`K20` | This Month | `FX` | `DERIVED` | `=+E14`, `=+G14`, `=+I14`, `=+K14` — the substantial-completion row |
| `E21`,`G21`,`I21`,`K21` | Previous Month | `IN` | `MANUAL` | **Paste-special by hand every month.** Replaced entirely by `dim_Date` + `DATEADD` |
| `E22`,`G22`,`I22` | MTM Change | `FX` | `DERIVED` | `This − Previous` |
| `K22` | MTM Change (actual finish) | `FX` | `DERIVED` | `IF(K20="NA","TBD",K20−K21)` |

### Average daily manpower — `Table14` (C25:D30)

| Column | Field | Type | Source | Notes |
|---|---|---|---|---|
| `C` | Company Name | `IN` | `PROCORE` | Currently placeholder `Sub 1`–`Sub 5`. Fixed cap of 5 |
| `D` | Avg Daily over past 30 days | `IN` | `PROCORE` | `/rest/v1.0/projects/{project_id}/manpower_logs/daily_totals` computes this exactly |

### Priority items — `Table3714` (C34:H39)

Grain: one row per priority schedule item, capped at 5. All narrative.

| Column | Field | Type | Source | Notes |
|---|---|---|---|---|
| `C` | SCHEDULE ITEM | `IN` | `MANUAL` | Placeholder `PRIORITY ITEM 1`–`5` |
| `D` | STATUS SUMMARY | `DD` | `MANUAL` | `DROPDOWN!E4:E15` → On Track / Behind / At Risk |
| `E` | CRITICAL DELAYS / VARIANCES | `IN` | `MANUAL` | |
| `F` | RECOVERY PLAN | `IN` | `MANUAL` | Sheet note: *"critical if you're off track—list actionable steps, not just 'monitoring.'"* |
| `G` | FORECAST IMPACT | `IN` | `MANUAL` | |
| `H` | NOTES / ACTION ITEMS | `IN` | `MANUAL` | |

---

## RISKS — `Table37` (B2:G10)

Grain: one row per risk, capped at 8. **Entirely manual — this register exists nowhere else.**

| Column | Field | Type | Source | Notes |
|---|---|---|---|---|
| `B` | RISK # | fixed label | `DERIVED` | `RISK 1`–`RISK 8` |
| `C` | RISK DESCRIPTION | `IN` | `MANUAL` | |
| `D` | IMPACT | `DD` | `MANUAL` | `DROPDOWN!B4:B15` → `🔴 High` / `🟡 Medium` / `⚪ Low` |
| `E` | MITIGATION STRATEGY | `IN` | `MANUAL` | |
| `F` | OWNER | `DD` | `MANUAL` | `DROPDOWN!C4:C15` — 9 roles |
| `G` | STATUS | `DD` | `MANUAL` | `DROPDOWN!D4:D15` → Not Started / Planned / In Progress / Complete |

The dashboard header says *"RISKS (Ranked by Severity)"* but **no sorting is applied** —
rows appear in entry order. In Power BI, sort by `dim_Status[SortOrder]`.

---

## SAFETY

### Monthly metrics — `Table1` (B2:F34)

Grain: one row per project month. 30 pre-built rows + a `TOTAL` row at 34.

| Column | Field | Type | Source | Notes |
|---|---|---|---|---|
| `B` | MONTH # | fixed label | `DERIVED` | `Month 1`–`Month 30` |
| `C3` | MONTH (first) | `IN` | `DERIVED` | Seed date, `2025-01-01` |
| `C4:C32` | MONTH | `FX` | `DERIVED` | `=EOMONTH(prev,0)+1` — chained first-of-month |
| `D` | HOURS WORKED THIS PERIOD | `IN` | `EITHER` | Sage 100 Contractor payroll, or ADP, or Procore timecards |
| `E` | RECORDABLE INCIDENTS THIS PERIOD | `IN` | `PROCORE` | `/rest/v1.0/projects/{project_id}/incidents` |
| `F` | ORIENTATIONS THIS PERIOD | `IN` | `MANUAL` | No obvious system of record |
| `D34:F34` | TOTAL | `FX` | `DERIVED` | `SUM` over rows 3–33 |

### Violations — `Table15` (H2:L27)

Grain: one row per violation, capped at 24.

| Column | Field | Type | Source | Notes |
|---|---|---|---|---|
| `H` | VLN # | fixed label | `DERIVED` | 1–23 |
| `I` | VLN Description | `IN` | `MANUAL` | **Currently entirely empty** across all rows |
| `J` | VLN Value | `IN` | `MANUAL` | Dollar value of the violation |
| `K` | Status | `DD` | `MANUAL` | Native list `"Open,Closed"` — the only non-`DROPDOWN`-sheet validation |
| `L` | VLN Value / Status | `FX` | `DERIVED` | `IF(Status="Open", Value, " ")` — returns a **space** not zero |
| `I27`,`J27`,`L27` | Totals | `FX` | `DERIVED` | `COUNTA`, `SUM`, `SUM` |

### Activity log — `Table20` (B36:G41)

Grain: one row per safety activity, capped at 5.

| Column | Field | Type | Source | Notes |
|---|---|---|---|---|
| `B` | TIMEFRAME | `DD` | `MANUAL` | `DROPDOWN!H` → `Lookback` / `Lookahead` |
| `C` | CATEGORY | `DD` | `MANUAL` | `DROPDOWN!I` — 16 values (toolbox talks, standdowns, visitors, safety wins) |
| `D` | DESCRIPTION/ACTIVITY | `IN` | `MANUAL` | |
| `E` | STATUS | `DD` | `MANUAL` | `DROPDOWN!J` — 6 values |
| `F` | NOTES/OUTCOME/ACTION | `IN` | `MANUAL` | |
| `G` | RESPONSIBLE | `DD` | `MANUAL` | `DROPDOWN!C` — reuses the risk-owner role list |

> Toolbox talks and site visits *could* live in Procore Daily Logs, but Affect isn't
> using them that way today. Confirm on the call.

---

## QUALITY

### Monthly metrics — `Table18` (B2:E35)

| Column | Field | Type | Source | Notes |
|---|---|---|---|---|
| `B` | MONTH # | fixed label | `DERIVED` | `Month 1`–`Month 31` |
| `C` | MONTH | `IN`/`FX` | `DERIVED` | Same `EOMONTH` chain, seeded `2025-01-01` |
| `D` | OBSERVATIONS THIS PERIOD | `IN` | `PROCORE` | `/rest/v1.0/observations/items`. ⚠️ Rows 5–6 wrongly reference `SAFETY!F` — see defect #5 |
| `E` | PUNCHLIST ITEM THIS PERIOD | `IN` | `PROCORE` | `/rest/v1.0/punch_items` |
| `D35:E35` | TOTAL | `FX` | `DERIVED` | `SUM` |

### Aging + offenders — `Table17` (C37:E44)

| Cell | Field | Type | Source | Notes |
|---|---|---|---|---|
| `D38`,`E38` | AVG. DAYS PAST DUE | `IN` | `DERIVED` | **Typed in by hand today**; Procore can compute it from due date vs. today |
| `D39`,`E39` | AVG. DAYS TO CLOSE | `IN` | `DERIVED` | Same — computable from created/closed timestamps |
| `D40:E44` | MAIN OFFENDER 1–5 | `IN` | `DERIVED` | Sub name. Procore can rank by open item count per vendor |

Row label `B40` spans C40:C44: *"RANGE BY ASCENDING OFFENCES"*.

### Issue log — `Table16` (B47:I57)

Grain: one row per quality issue, capped at 10.

| Column | Field | Type | Source | Notes |
|---|---|---|---|---|
| `B` | TIMEFRAME | `DD` | `MANUAL` | `DROPDOWN!H` |
| `C` | CATEGORY | `DD` | `PROCORE` | `DROPDOWN!K` — 11 values incl. Benchmark, Mockup, Delivery, Commissioning, Inspection–Special, Inspection–NCR |
| `D` | DESCRIPTION | `IN` | `PROCORE` | Observation / inspection description |
| `E` | TRADE | `IN` | `PROCORE` | Free text here; `DROPDOWN!M` has the canonical 29-trade list |
| `F` | STATUS | `DD` | `PROCORE` | `DROPDOWN!L` — Open / Passed / Scheduled / Rejected / NCR |
| `G` | OUTCOME / COMMENTS | `IN` | `PROCORE` | |
| `H` | RESPONSIBLE | `DD` | `MANUAL` | `DROPDOWN!C` |
| `I` | ACTION PLAN | `IN` | `MANUAL` | |

---

## SUBMITTALS & RFI — `Table22` (B2:D13)

Grain: one row per trade. **Fully automatable — the cleanest win in the workbook.**

| Column | Field | Type | Source | Notes |
|---|---|---|---|---|
| `B` | Trade | `DD` | `PROCORE` | `DROPDOWN!M4:M32` — 29 trades. ⚠️ `Metals` appears twice (B6, B9) |
| `C` | Open Critical RFIs | `IN` | `PROCORE` | `/rest/v1.0/projects/{project_id}/rfis` filtered open + priority |
| `D` | Open Critical Submittals | `IN` | `PROCORE` | `/rest/v1.1/projects/{project_id}/submittals` filtered open |

Rows 12–13 hold zeros with no trade name — chart padding.

> "Critical" is undefined in the workbook. Procore has an RFI `priority` filter option;
> need to confirm what Affect means by critical.

---

## FINANCIALS

### Contract & billing summary — `Table8` (B2:E15)

Grain: one row per financial line item, this period vs. last period.

| Row | Field | Type | Source | Notes |
|---|---|---|---|---|
| 3 | Original Contract Amt. | `IN` | `EITHER` | `8,800,000`. Procore prime contract or Sage job contract |
| 4 | Current Contract Amt. | `IN` | `EITHER` | `9,116,960.48` |
| 5 | Pending CO's | `IN` | `PROCORE` | ⚠️ Entered as `=65000+3158.46+11550+4620` — arithmetic in a value cell |
| 6 | Age of oldest unapproved CO | `IN` | `PROCORE` | Computable from CO created date |
| 7 | Profitability | `DD` | `MANUAL` | `DROPDOWN!Q4:Q6` — a **human judgment**, not a number. Note in `G7`: *"Based on the original financial projection"* |
| 8 | Cash Position | `DD` | `MANUAL` | `DROPDOWN!P4:P6` — banded judgment. Note in `G8` gives the formula: `(Cash Collected + AR Outstanding) ÷ Remaining Forecasted Cost × 100`. **This is fully computable and should be a measure, not a dropdown** |
| 9 | Remaining in Contingency | `IN` | `MANUAL` | Currently `"N/A"` |
| 10 | Total Billed | `IN` | `SAGE` | ⚠️ Entered as `=3032804.23-35000` |
| 11 | Bill This Pay Period | `IN` | `SAGE` | No last-period comparison |
| 12 | Total Paid | `IN` | `SAGE` | |
| 13 | Remaining Balance | `IN` | `SAGE` | |
| 14 | Retainage | `IN` | `SAGE` | |
| 15 | Cost to Complete | `IN` | `EITHER` | Procore forecast or Sage job cost |
| `C` | THIS PERIOD | `IN` | | |
| `D` | LAST PERIOD | `IN` | | **Re-keyed by hand every month** |
| `E` | & DIF | `FX` | `DERIVED` | `(This − Last) / Last`, blank when This = `"N/A"` |

### GC/GR budget — `Table11011` (B18:F21)

⚠️ **Unfinished section** — only 2 data rows exist, and the column header reads
`SPENT TO DATE2`.

| Column | Field | Type | Source | Notes |
|---|---|---|---|---|
| `B` | MONTH | fixed label | | Actually holds `General Requirements` / `General Conditions` — mislabeled header |
| `C` | BUDGET | `IN` | `PROCORE` | Budget line items |
| `D` | FORECAST | `IN` | `PROCORE` | |
| `E` | SPENT TO DATE2 | `IN` | `EITHER` | Procore direct costs or Sage job cost actuals |
| `F` | STATUS | `DD` | `DERIVED` | `DROPDOWN!N4:N19`. Legend in `H18:J21` defines the rule: `≥0%` → On Track, `−0.01%..−5%` → Watch, `>−5%` → Over Budget. **Currently typed by hand despite being fully derivable** |

### Invoice aging — `Table11012` (B24:F56)

| Column | Field | Type | Source | Notes |
|---|---|---|---|---|
| `B` | MONTH # | fixed label | `DERIVED` | `Month 1`–`Month 30` |
| `C` | MONTH | `IN`/`FX` | `DERIVED` | ⚠️ Seeded `2025-11-01` while the invoice dates below are 2024 — see defect #7 |
| `D` | INVOICE SENT | `IN` | `SAGE` | AR invoice date |
| `E` | INVOICE PAID | `IN` | `SAGE` | Cash receipt date |
| `F` | DELTA | `FX` | `DERIVED` | `IF(Paid>0, Paid−Sent, "")` — days to payment |
| `F56` | TOTAL | `FX` | `DERIVED` | `AVERAGE(F25:F55)` = 8.82 days → dashboard "AVG. DAYS FOR PAYMENT RECEIVED" |
| `F57` | CURRENT AGING BALANCE | `IN` | `SAGE` | Currently `1`. Feeds the scorecard AR band — see defect #4 |

### OT hours — `Table110` (H24:J56)

| Column | Field | Type | Source | Notes |
|---|---|---|---|---|
| `H` | MONTH # | fixed label | `DERIVED` | |
| `I` | MONTH | `IN`/`FX` | `DERIVED` | Seeded `2025-01-01` |
| `J` | OT HOURS WORKED THIS PERIOD | `IN` | `EITHER` | Sage payroll or ADP |
| `J56` | TOTAL | `FX` | `DERIVED` | `SUM` = 112.5 |

### Project buyout (B59:E62)

| Cell | Field | Type | Source | Notes |
|---|---|---|---|---|
| `D60` | Total Trade Costs Budgeted | `IN` | `PROCORE` | ⚠️ `200,000,000` — placeholder against a `$9.1M` contract |
| `D61` | Total Trade Costs Committed | `IN` | `PROCORE` | ⚠️ `190,000,001`. Label says *"(Use budget dollar value)"* |
| `D62` | % Bought out | `FX` | `DERIVED` | `D61/D60` = 95.0% |

### Cost management flags (B64:E67)

| Cell | Field | Type | Source | Notes |
|---|---|---|---|---|
| `E65` | MONTH END CLOSED OUT | `DD` | `MANUAL` | `DROPDOWN!O4:O19` → `🟢 Y` / `🔴 N` |
| `E66` | PROCORE FORECASTING IN LINE W/SCHEDULE | `DD` | `MANUAL` | Process-compliance attestation |
| `E67` | MONITORED RESOURCES UPDATED BASED ON ACTUALS | `DD` | `MANUAL` | |

---

## SCORECARD CALC

### Weighted score grid (B2:G31)

Nine categories. `C` holds the three score values (3/2/0), `D` the band descriptions,
`E` the resolved score, `F` the weight, `G` the weighted contribution.

| Category | Weight | Driver | Type | Source |
|---|---|---|---|---|
| Accounts Receivable | 0.12 | `DASHBOARD!AT25` | `FX` | `SAGE` |
| Profitability | 0.12 | `FINANCIALS!C7` | `FX` | `MANUAL` |
| Cash Position | 0.12 | `DASHBOARD!AS31` | `FX` | `MANUAL` (should be `DERIVED`) |
| Change Orders (Avg Days Open) | 0.08 | `DASHBOARD!AT21` | `FX` | `PROCORE` |
| Safety incidents | 0.14 | `DASHBOARD!AI51` | `FX` | `PROCORE` |
| Schedule Performance | 0.15 | `DASHBOARD!L19` | `FX` | `DERIVED` |
| Completion Variance | 0.15 | `DASHBOARD!M16` | `FX` | `DERIVED` |
| Observations (Avg Days Open) | 0.10 | `DASHBOARD!M67` | `FX` | `PROCORE` |
| Daily Reports | 0.02 | `E28` | `IN` | `PROCORE` |
| **Total** | **1.00** | `G31` | `FX` | `DERIVED` |

Weights sum to exactly `1.00`. Per-row: `(Score × Weight) / 3`. Total = `SUM(G4:G30)` = **0.59**.

The scores stored in column `C` are `3` / `2` / `0` — note the bottom band is **zero, not
one**, so a failing category contributes nothing rather than partial credit.

### Client satisfaction (B33:D42)

| Cell | Field | Type | Source | Notes |
|---|---|---|---|---|
| `C34` | WHO WAS SURVEYED | `IN` | `MANUAL` | Currently `ANONYMOUS` |
| `C36:C41` | Q1–Q6 score (1–5) | `IN` | `MANUAL` | Question text is not stored anywhere in the file |
| `C42` | Score | `FX` | `DERIVED` | `SUM(C36:C41) / (COUNTA(B36:B41) × 5)` = **0.60** |

> The six survey **questions themselves are not in the workbook** — only the scores.
> Ask Affect for the questionnaire; it needs to be captured in the new input template.

---

## Summary: where the data has to come from

| Source | Approx. field count | Notes |
|---|---|---|
| `MANUAL` | ~40% | Wins, focus areas, full risk register, priority-item narratives, safety activity log, contract dates, baseline approval, profitability judgment, contingency, cost-mgmt flags, client survey |
| `PROCORE` | ~30% | RFIs, submittals, observations, punch list, incidents, manpower, budget/forecast, change orders, commitments, cost codes, trades, vendors |
| `SAGE` | ~15% | Billing, payments, retainage, remaining balance, invoice aging, payroll hours |
| `DERIVED` | ~15% | Every variance, %, average, total, and status band |

**The single most important open question:** what is the shared project identifier
across Procore, Sage 100 Contractor, and the manual input file? Nothing joins without it.
See `defects-and-questions.md`.
