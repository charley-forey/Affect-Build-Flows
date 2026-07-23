# Calculations Decoded

Every distinct formula in the workbook, in plain English, with its DAX equivalent.

Formulas are quoted **verbatim** from the file. Where a formula is defective, the defect
is flagged inline and cross-referenced to `defects-and-questions.md`.

The DAX assumes the model in [`../../powerbi/semantic-model.md`](../../powerbi/semantic-model.md).
The runnable library lives in [`../../powerbi/measures.dax`](../../powerbi/measures.dax) — this
document explains the *reasoning*; that file is the deliverable.

---

## 1. The month-anchor pattern

This single pattern accounts for ~15 formulas and drives every "this period" tile.

### 1a. Value for the reporting month

```excel
=INDEX(SAFETY!E3:E33, MATCH(AU4, SAFETY!C3:C33, 0))
```
*(`DASHBOARD!AI51` — recordable incidents this period)*

**Plain English:** find the row whose MONTH equals the anchor date in `AU4`, return that
row's metric.

**Why it's fragile:** `MATCH(...,0)` is an exact match. `AU4` must be the exact first-of-month
date, that date must exist in the month column, and the two must be the same data type. Any
miss returns `#N/A` on the printed report.

**DAX:**
```dax
Recordable Incidents =
SUM ( fct_SafetyMonthly[RecordableIncidents] )
```
Filter context from `dim_Date` does what `MATCH` was doing. `AU4` becomes a slicer.

### 1b. Month-to-month delta

```excel
=TEXT(INDEX(SAFETY!D3:D33,MATCH(AU4,SAFETY!C3:C33,0)),"#,###,###")
 & " / " &
 TEXT((INDEX(SAFETY!D3:D33,MATCH(AU4,SAFETY!C3:C33,0))
      -INDEX(SAFETY!D3:D33,MATCH((EDATE(AU4,-1)),SAFETY!C3:C33,0)))
      /INDEX(SAFETY!D3:D33,MATCH((EDATE(AU4,-1)),SAFETY!C3:C33,0)),"0.0%")
```
*(`DASHBOARD!AI48` — hours worked, renders as `4,635 / 9.7%`)*

**Plain English:** this month's value, then the percent change vs. last month, glued into
one text string.

**Two problems:** (1) the result is **text**, so it cannot be charted, sorted, or
conditionally formatted; (2) division by last month's value blows up to `#DIV/0!` when the
prior month is zero — which happens on any new project.

**DAX** — two separate measures so both are numeric and formattable:
```dax
Hours Worked = SUM ( fct_SafetyMonthly[HoursWorked] )

Hours Worked MoM % =
VAR Prior = CALCULATE ( [Hours Worked], DATEADD ( dim_Date[Date], -1, MONTH ) )
RETURN DIVIDE ( [Hours Worked] - Prior, Prior )
```
`DIVIDE` returns blank rather than erroring on a zero denominator — the fix for problem (2).

**Same pattern also at:** `AI54` (orientations), `AT40` (OT hours), `K64`/`O64` (quality
observations / punchlist).

### 1c. The month column itself

```excel
=EOMONTH(C3,0)+1
```
*(`SAFETY!C4:C32`, `QUALITY!C4:C33`, `FINANCIALS!C26:C54`, `FINANCIALS!I26:I54`)*

**Plain English:** last day of the previous row's month, plus one day = first of the next
month. A chained sequence seeded by a single hand-entered date.

**DAX:** replaced by `dim_Date`, a generated contiguous calendar. Nothing chains.

---

## 2. Schedule

### 2a. Project rollup

```excel
=+MIN(D5:D14)      ' D4 — earliest contract start
=+MAX(E5:E14)      ' E4 — latest contract finish
```
Applied across all four date-pair columns (`D4:K4`).

**Note:** `MIN`/`MAX` silently ignore the `"NA"` text sentinels, which is why this works
despite the mixed-type columns.

```dax
Contract Start = MIN ( fct_Milestone[ContractStart] )
Contract Finish = MAX ( fct_Milestone[ContractFinish] )
```

### 2b. Per-milestone variance

```excel
=IF(Table5[[#This Row],[ACTUAL START]]="NA","",
    Table5[[#This Row],[ACTUAL START]]-Table5[[#This Row],[BASELINE START]])
```
*(`SCHEDULE!L5:L14` — START VARIANCE)*

```excel
=IF(Table5[[#This Row],[CURRENT FINISH]]="NA","",
    Table5[[#This Row],[CURRENT FINISH]]-Table5[[#This Row],[BASELINE FINISH]])
```
*(`SCHEDULE!M5:M14` — FINISH VARIANCE)*

**Plain English:** days late vs. baseline. Positive = late. Blank if not yet actualised.

> **Asymmetry worth noting:** start variance uses **ACTUAL** start, finish variance uses
> **CURRENT** (forecast) finish. That is arguably correct — you know when you started, you
> only forecast when you'll finish — but it means the two columns are not comparable measures.

**DAX** — calculated columns on the fact, since they're row-level:
```dax
StartVariance  = DATEDIFF ( fct_Milestone[BaselineStart], fct_Milestone[ActualStart], DAY )
FinishVariance = DATEDIFF ( fct_Milestone[BaselineFinish], fct_Milestone[CurrentFinish], DAY )
```
`DATEDIFF` on a null returns blank — the `IF(...="NA","")` guard becomes unnecessary once
the sentinels are cleaned to real nulls at ingestion.

### 2c. Completion variance (two flavours)

```excel
=+IF((O12-O10)=0,"0 days",O12-O10)    ' L16 — vs CONTRACT finish  → 49
=+IF((O12-O11)=0,"0 days",O12-O11)    ' M16 — vs BASELINE finish  → "0 days"
```

**Plain English:** how many days later the current forecast finishes than the contract
(`L16`) or the baseline (`M16`) finish date.

> ⚠️ **The `"0 days"` string is a live defect.** When the variance is zero the cell holds
> *text*, and `SCORECARD CALC!E22` then does `IF(DASHBOARD!M16<=0, ...)`. In Excel, text
> ranks above every number, so `"0 days" <= 0` is FALSE — a project finishing exactly on
> baseline scores **0 out of 3** on a 15%-weighted category. See defect #3.

**DAX** — keep it numeric, format it in the visual:
```dax
Completion Variance vs Baseline =
DATEDIFF ( [Baseline Finish], [Current Finish], DAY )
```

### 2d. Critical missed starts

```excel
=COUNTIF(Table5[START VARIANCE],">=1")/COUNT(Table5[ACTUAL START])
```
*(`DASHBOARD!L19` → `0.4`, i.e. 40%)*

**Plain English:** of the milestones that have actually started, what fraction started at
least one day after baseline.

Two subtleties: the denominator is `COUNT(ACTUAL START)`, which counts only **numeric**
cells — so the `"NA"` rows are correctly excluded. And `>=1` means a milestone that started
exactly on baseline is not "missed", which is right.

```dax
Critical Missed Starts % =
VAR Started = FILTER ( fct_Milestone, NOT ISBLANK ( fct_Milestone[ActualStart] ) )
RETURN
DIVIDE (
    COUNTROWS ( FILTER ( Started, fct_Milestone[StartVariance] >= 1 ) ),
    COUNTROWS ( Started )
)
```

> ⚠️ This value is a **fraction** (`0.4`), but `SCORECARD CALC!E19` compares it to `5`,
> `9`, and `10` as if it were a percentage number. `0.4 <= 5` is always TRUE, so this
> 15%-weighted category **always awards full marks**. See defect #2.

### 2e. Project % complete

```excel
=IF(M12>TODAY(), 0, ((TODAY()-M12))/(O12-M12))
```
*(`DASHBOARD!L21` → `0.7486`)*

**Plain English:** elapsed calendar days as a fraction of total forecast duration.

> **This is time-elapsed, not progress.** It says nothing about work put in place. A
> project 75% through its calendar with 30% of the work done reports 75% complete. Worth
> raising with Affect: Procore budget line items support **% complete by cost**, which is
> a far more honest measure.

Also: `TODAY()` makes the number **non-reproducible**. Reopening last month's saved file
shows a different % complete than it did when issued. See defect #9.

```dax
-- Faithful port (time-elapsed), reproducible against the selected month
Project % Complete (Time) =
VAR AsOf     = MAX ( dim_Date[Date] )
VAR Started  = [Current Start]
VAR Finishes = [Current Finish]
RETURN IF ( Started > AsOf, 0, DIVIDE ( AsOf - Started, Finishes - Started ) )

-- Recommended alternative once budget lines are in the model
Project % Complete (Cost) =
DIVIDE ( [Cost To Date], [Current Budget] )
```

### 2f. Slippage warnings

```excel
=IF(L16>0,"Warning, provide Recovery Plan","")                                   ' O16
=IF(L19>0.2,"Warning, provide Recovery Plan","")                                 ' O19
=IF(L21<((TODAY()-M11))/(O11-M11),"Warning, slippage, provide recovery plan","")  ' O21
```

**Plain English:**
- `O16` — flag if the forecast finish is later than the contract finish.
- `O19` — flag if more than 20% of started milestones started late.
- `O21` — flag if current % complete is behind where the **baseline** schedule says it
  should be. This is the sharpest calculation in the workbook: it compares actual pace
  against baseline pace, not against a fixed threshold.

> Note `O19` uses `0.2` (correct fraction handling) while the scorecard uses `5` for the
> same value. The dashboard author got it right; the scorecard author did not.

```dax
Schedule Slippage Flag =
VAR AsOf = MAX ( dim_Date[Date] )
VAR BaselinePace = DIVIDE ( AsOf - [Baseline Start], [Baseline Finish] - [Baseline Start] )
RETURN IF ( [Project % Complete (Time)] < BaselinePace, "Warning — slippage, provide recovery plan" )
```

### 2g. Month-to-month milestone change

```excel
=+E20-E21                              ' E22, G22, I22
=+IF(K20="NA","TBD",K20-K21)           ' K22 — actual finish
```
Where row 20 is this month (`=+E14`) and row 21 is **hand-pasted** from last month.

**DAX** — the manual paste disappears:
```dax
Substantial Completion MoM =
VAR Prior = CALCULATE ( [Contract Finish], DATEADD ( dim_Date[Date], -1, MONTH ) )
RETURN [Contract Finish] - Prior
```

---

## 3. Safety

### 3a. Totals

```excel
=SUM(D3:D33)    ' D34 hours   → 114,231
=SUM(E3:E33)    ' E34 incidents → 1
=SUM(F3:F33)    ' F34 orientations → 120
```
```dax
Total Hours Worked = CALCULATE ( SUM ( fct_SafetyMonthly[HoursWorked] ), ALL ( dim_Date ) )
```
`ALL(dim_Date)` reproduces "to date regardless of the selected month". Use
`DATESYTD` or a running total instead if Affect wants project-to-date rather than all-time.

### 3b. Open violation value

```excel
=IF(Table15[[#This Row],[Status]]="Open", Table15[[#This Row],[VLN Value]], " ")
```
*(`SAFETY!L3:L26`)*

**Plain English:** show the dollar value only while the violation is open.

> Note the false branch returns `" "` — a **space**, not blank and not zero. That's what
> makes the downstream `COUNTIF` in 3c misbehave.

```excel
=SUM(L3:L26)    ' L27 → 1000, the dashboard's "$ VALUE"
```

```dax
Open Violation Value =
CALCULATE ( SUM ( fct_Violation[Value] ), fct_Violation[Status] = "Open" )
```

### 3c. Open violation count

```excel
=COUNTIF(SAFETY!L3:L26,">1")
```
*(`DASHBOARD!AM57`, labelled "Total Open" → `1`)*

> ⚠️ **Defective.** This counts violations whose *dollar value exceeds 1*, not violations
> whose *status is Open*. A `$0` open violation — a stop-work order with no fine, exactly
> the kind you most want counted — is invisible. See defect #6.

```dax
Open Violation Count =
CALCULATE ( COUNTROWS ( fct_Violation ), fct_Violation[Status] = "Open" )
```

---

## 4. Quality

```excel
=SUM(D3:D34)                              ' D35 total observations → 77
=IF(QUALITY!D38=0,"N/A",QUALITY!D38)      ' DASHBOARD!K67 — avg days past due
```

The `IF(...=0,"N/A",...)` wrapper appears on all four aging tiles (`K67`, `M67`, `O67`,
`P67`). It converts a real zero into text — the same class of bug as `"0 days"` in 2c, and
it feeds `SCORECARD CALC!E25`. It happens not to misfire today only because the current
values are non-zero.

```dax
Avg Days Past Due = AVERAGE ( fct_QualityItem[DaysPastDue] )
```
Blank when there's nothing to average — no sentinel needed. Handle the "N/A" display with
the visual's blank-value formatting.

> ⚠️ `QUALITY!D5` = `=SAFETY!F5` and `QUALITY!D6` = `=SAFETY!F6`. Quality *observations*
> pulling Safety *orientations*. Rows 3, 4, and 7+ are hand-entered numbers. See defect #5.

---

## 5. Financial

### 5a. Period-over-period difference

```excel
=IF(Table8[[#This Row],[THIS PERIOD]]="N/A","",
    (Table8[[#This Row],[THIS PERIOD]]-D4)/D4)
```
*(`FINANCIALS!E4:E15`)*

**Plain English:** percent change vs. last period, suppressed when this period is `"N/A"`.

Note the guard checks *this* period for `"N/A"` but then divides by *last* period — so a
row where last period is `"N/A"` or zero still errors.

```dax
Current Contract MoM % =
VAR Prior = CALCULATE ( [Current Contract], DATEADD ( dim_Date[Date], -1, MONTH ) )
RETURN DIVIDE ( [Current Contract] - Prior, Prior )
```

### 5b. Contract variance

```excel
=(AT10-AT9)/AT9
```
*(`DASHBOARD!AT11` → `3.60%` — growth from original to current contract)*

```dax
Contract Growth % = DIVIDE ( [Current Contract] - [Original Contract], [Original Contract] )
```

### 5c. The money waterfall — dollars and percent in one string

```excel
=TEXT(FINANCIALS!C10,"$#,##0.0") & " / " & TEXT(FINANCIALS!C10/FINANCIALS!C4,"0.0%")
```
*(`DASHBOARD!AT15` → `$2,997,804.2 / 32.9%`)*

Applied identically to `AT14` (billed this month), `AT15` (total billed), `AT16` (total
paid), `AT17` (remaining balance), `AT18` (retainage), `AT19` (cost to complete) — each
divided by `FINANCIALS!C4`, the **current contract amount**.

Same pattern on the GC/GR grid:
```excel
=TEXT(FINANCIALS!E19,"$#,##0.00") & " / " & TEXT(FINANCIALS!E19/FINANCIALS!C19,"0.0%")
```
*(`DASHBOARD!AU37`, `AU38` — spent to date as % of that line's budget)*

> All of these produce **text**. Nothing here can be charted or trended. In Power BI, keep
> the amount and the ratio as separate numeric measures and show both in a card — you get
> the same visual with none of the dead ends.

```dax
Total Billed     = SUM ( fct_FinancialPeriod[TotalBilled] )
Total Billed %   = DIVIDE ( [Total Billed], [Current Contract] )
```

### 5d. Invoice aging

```excel
=IF(Table11012[[#This Row],[INVOICE PAID]]>0,
    Table11012[[#This Row],[INVOICE PAID]]-Table11012[[#This Row],[INVOICE SENT]], "")
```
*(`FINANCIALS!F25:F55` — days from invoice sent to paid)*

```excel
=AVERAGE(F25:F55)    ' F56 → 8.818 days
```

```dax
Avg Days To Payment = AVERAGEX ( fct_Invoice, DATEDIFF ( fct_Invoice[SentDate], fct_Invoice[PaidDate], DAY ) )
```
`AVERAGEX` skips rows where `PaidDate` is blank, matching the `IF(...>0)` guard.

### 5e. Buyout

```excel
=D61/D60
```
*(`FINANCIALS!D62` → `95.0%` — committed ÷ budgeted trade costs)*

```dax
Percent Bought Out = DIVIDE ( [Trade Costs Committed], [Trade Costs Budgeted] )
```

### 5f. Cash position — the formula hiding in a comment

`FINANCIALS!C8` is a *dropdown*, but the note in `G8` spells out the actual calculation:

> `Cash Position % = (Cash Collected + AR Outstanding) ÷ Remaining Forecasted Cost × 100`
> Worked example: `($2,000,000 + $400,000) ÷ $1,500,000 × 100 = 160%`
> Bands: `≥ 100%` 🟢 · `50–99%` 🟡 · `< 50%` 🔴

**This is fully computable from Sage data and should not be a human judgment.** Converting
it from a dropdown to a measure removes one of the three subjective inputs to the scorecard.

```dax
Cash Position % =
DIVIDE ( [Total Paid] + [AR Outstanding], [Cost To Complete] )
```

### 5g. GC/GR budget status

Currently a hand-picked dropdown, but the rule is written out in `H18:J21`:

| Variance (Budget − Actual) | Status |
|---|---|
| `≥ 0%` | 🟢 On Track / Positive |
| `−0.01%` to `−5%` | 🟡 Watch |
| `> −5%` | 🔴 Over Budget |

```dax
Budget Status =
VAR V = DIVIDE ( [Budget] - [Spent To Date], [Budget] )
RETURN SWITCH ( TRUE(), V >= 0, "On Track", V >= -0.05, "Watch", "Over Budget" )
```

---

## 6. Scorecard

### 6a. The band lookup

Each of the nine categories resolves a score through nested `IF`s. Two shapes:

**Numeric bands** —
```excel
=IF(DASHBOARD!AI51=0,'SCORECARD CALC'!C16,
 IF(DASHBOARD!AI51<=1,'SCORECARD CALC'!C17,
 IF(DASHBOARD!AI51>=2,'SCORECARD CALC'!C18,0)))
```
*(`E16` — safety incidents: 0 → 3 pts, ≤1 → 2 pts, ≥2 → 0 pts)*

**Dropdown-value bands** —
```excel
=IF(FINANCIALS!C7=DROPDOWN!Q4,'SCORECARD CALC'!C7,
 IF(FINANCIALS!C7=DROPDOWN!Q5,'SCORECARD CALC'!C8,
 IF(FINANCIALS!C7=DROPDOWN!Q6,'SCORECARD CALC'!C9,0)))
```
*(`E7` — profitability, matched against the pick-list text)*

```dax
Score - Safety Incidents =
SWITCH ( TRUE(), [Recordable Incidents] = 0, 3, [Recordable Incidents] <= 1, 2, 0 )
```
`SWITCH(TRUE(), …)` is the idiomatic DAX for nested `IF` bands — flat and readable.

### 6b. Weighting and total

```excel
=((E4*F4))/3        ' G4:G30, per category
=SUM(G4:G30)        ' G31 → 0.59
```

**Plain English:** score (0–3) × weight, normalised to a 0–1 scale by dividing by the max
score of 3. Summing all nine gives a 0–1 project health index.

```dax
Project Scorecard =
DIVIDE (
      [Score - Accounts Receivable]   * 0.12
    + [Score - Profitability]         * 0.12
    + [Score - Cash Position]         * 0.12
    + [Score - Change Orders]         * 0.08
    + [Score - Safety Incidents]      * 0.14
    + [Score - Schedule Performance]  * 0.15
    + [Score - Completion Variance]   * 0.15
    + [Score - Observations]          * 0.10
    + [Score - Daily Reports]         * 0.02,
    3
)
```
Weights belong in a `dim_ScorecardWeight` table so Affect can retune them without a model
change — see `../../powerbi/semantic-model.md`.

### 6c. Verified reconciliation

Recomputed from the workbook's own cached values:

| Category | Weight | Resolved score | Contribution | Why |
|---|---|---|---|---|
| Accounts Receivable | 0.12 | 3 | 0.12 | `AT25` = 1, `1 < 45` ✓ — but wrong driver cell (defect #4) |
| Profitability | 0.12 | 0 | 0.00 | "Margin fade but no plan" |
| Cash Position | 0.12 | 0 | 0.00 | "< 50% 🔴 Bad Cash Position" |
| Change Orders | 0.08 | 3 | 0.08 | `AT21` = 1 day |
| Safety incidents | 0.14 | 3 | 0.14 | `AI51` = 0 |
| Schedule Performance | 0.15 | 3 | 0.15 | **always 3** — dead band (defect #2) |
| Completion Variance | 0.15 | 0 | 0.00 | **always 0** — dead band (defect #3) |
| Observations | 0.10 | 3 | 0.10 | `M67` = 2 days |
| Daily Reports | 0.02 | 0 | 0.00 | manual, left at 0 |
| **Total** | **1.00** | | **0.59** | ✅ matches `G31` exactly |

**Three of the nine categories are not measuring anything.** Schedule Performance always
awards full marks, Completion Variance always awards zero, and Accounts Receivable reads
an aging *balance* against day-count bands. Together that is **42% of the total weight**
producing a number unconnected to project reality.

### 6d. Client satisfaction

```excel
=SUM(C36:C41)/(COUNTA(B36:B41)*5)
```
*(`C42` → `18 / (6 × 5)` = `0.60`)*

**Plain English:** total score over maximum possible, where each of six questions is
scored 1–5. `COUNTA` on the question labels means unanswered questions still count toward
the denominator — a blank answer is scored as zero, not excluded.

```dax
Client Satisfaction =
DIVIDE ( SUM ( man_Survey[Score] ), COUNTROWS ( man_Survey ) * 5 )
```

---

## 7. Conditional formatting

The only conditional formatting in the workbook is on the two scorecard tiles:

| Range | Bands |
|---|---|
| `DASHBOARD!C65:G67` (project scorecard) | `0–0.5` · `0.5–0.75` · `0.75–1` |
| `DASHBOARD!C72:G73` (client satisfaction) | `0–0.5` · `0.5–0.75` · `0.75–1` |

Every other status colour in the file comes from the **emoji embedded in the text value**
(`🔴 High`, `🟢 On Track`) rather than from formatting rules. That is why
`dropdowns-and-status.md` proposes splitting code, label, and colour into a real dimension.

---

## 8. Formulas that are not formulas

Three value cells contain arithmetic instead of a number — someone did mental maths in
the cell and never wrote down what the components were:

```excel
FINANCIALS!C5  =65000+3158.46+11550+4620        ' Pending CO's → 84,328.46
SAFETY!D7      =4001+16+178+356+84              ' Hours worked → 4,635
SAFETY!D8      99999                            ' Hours worked → placeholder
```

Each addend is presumably a real change order or a real crew's hours. That detail is lost
the moment someone edits the cell. In the target model these are rows in a fact table.
