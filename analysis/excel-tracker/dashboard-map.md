# DASHBOARD Tab — Cell Map

The `DASHBOARD` tab is a **presentation canvas**, not a calculation layer. 53 columns ×
94 rows of narrow cells used as a layout grid. Nearly every populated cell is a
cross-sheet reference of the form `=+SHEET!CELL`.

It contains **exactly one native chart** and **six conditional-formatting rules**.
Everything else is text and numbers positioned by hand.

Values shown below are the cached results from the file as received (reporting month
`2025-05-01`).

## Layout overview

| Anchor | Section | Approx. extent |
|---|---|---|
| `B2` | Title — "Monthly Progress Report" | — |
| `AU4` | **Reporting month anchor** (`2025-05-01`) | single cell |
| `B7` | WINS (REALIZED) | B7:H32 |
| `J7` | SCHEDULE | J7:AN23 |
| `AQ7` | FINANCIAL | AQ7:AW42 |
| `J25` | RISKS (Ranked by Severity) | J25:AN43 |
| `B34` | FOCUS AREAS (UPCOMING MTH) | B34:H59 |
| `AQ44` | CRITICAL SUBMITTALS & RFIS | AQ44:AW60 (the chart) |
| `J46` | SAFETY | J46:AN60 |
| `B62` | SCORECARD | B62:H75 |
| `J62` | QUALITY | J62:AV75 |

---

## Section 1 — WINS / FOCUS AREAS

Header `B7` "WINS (REALIZED)" · `B34` "FOCUS AREAS (UPCOMING MTH)"

| Dashboard cell | Formula | Cached value |
|---|---|---|
| `C9` | `=IF(WINS!C3=0," ",WINS!C3)` | Topped Out Superstructure |
| `C15` | `=IF(WINS!C4=0," ",WINS!C4)` | Major Submittals Approved (Window Wall, Porcelain, Doors) |
| `C21` | `=IF(WINS!C5=0," ",WINS!C5)` | No accidents |
| `C27` | `=IF(WINS!C6=0," ",WINS!C6)` | Quickly Rescinded PSWO |
| `C36` | `=IF(WINS!C9=0," ",WINS!C9)` | Topped Out Superstructure |
| `C42` | `=IF(WINS!C10=0," ",WINS!C10)` | Major Submittals Approved (…) |
| `C48` | `=IF(WINS!C11=0," ",WINS!C11)` | No accidents |
| `C54` | `=IF(WINS!C12=0," ",WINS!C12)` | Quickly Rescinded PSWO |

Six-row spacing between entries is pure layout. The `IF(...=0," ",...)` guard blanks an
empty source row.

**Hard cap of 4 + 4.** Adding a 5th win to the `WINS` tab would not surface here.

---

## Section 2 — SCHEDULE (`J7`)

### Milestone date matrix

Columns: `M` = Start · `O` = Finish · `P` = MTM Delta · `Q`/`T` = baseline approval

| Row label | Cell | Formula | Cached |
|---|---|---|---|
| Header | `M9` / `O9` / `P9` / `T9` | Start · Finish · MTM Delta · Rev # | |
| Contract | `M10` | `=SCHEDULE!D4` | 2025-01-09 |
| | `O10` | `=SCHEDULE!E4` | 2026-05-07 |
| | `P10` | `=+SCHEDULE!E22` | 0 |
| Baseline | `M11` | `=SCHEDULE!F4` | 2025-01-08 |
| | `O11` | `=+SCHEDULE!G14` | 2026-06-25 |
| | `P11` | `=+SCHEDULE!G22` | 0 |
| | `Q11` | `=+IF(SCHEDULE!G16=0," ",SCHEDULE!G16)` | 🔴 N |
| | `T11` | `=+IF(SCHEDULE!G17=0," ",SCHEDULE!G17)` | Rev#1 |
| Currently Tracking | `M12` | `=+SCHEDULE!H4` | 2025-01-08 |
| | `O12` | `=+SCHEDULE!I4` | 2026-06-25 |
| | `P12` | `=+SCHEDULE!I22` | 0 |
| Actual | `M14` | `=SCHEDULE!J4` | 2025-01-08 |
| | `O14` | `=IF(SCHEDULE!K14="NA","TBD",SCHEDULE!K14)` | TBD |
| | `P14` | `=+SCHEDULE!K22` | TBD |

`Q8` holds the static label "Approved by Client".

> Inconsistency worth noting: `O10` and `M11` read the **rollup row** (`SCHEDULE!E4` =
> `MAX` over all milestones) while `O11` reads the **substantial-completion row** directly
> (`SCHEDULE!G14`). They happen to agree today. If a milestone were ever added with a
> finish date beyond substantial completion, contract and baseline finish would be
> computed on different bases.

### Schedule KPIs

| Cell | Label | Formula | Cached |
|---|---|---|---|
| `L18` | COMPLETION VARIANCE (label) | | |
| `L16` | vs Contract | `=+IF((O12-O10)=0,"0 days",O12-O10)` | **49** |
| `M16` | vs Baseline | `=+IF((O12-O11)=0,"0 days",O12-O11)` | **"0 days"** ⚠️ text |
| `O16` | warning | `=IF(L16>0,"Warning, provide Recovery Plan","")` | Warning, provide Recovery Plan |
| `L20` | CRITICAL MISSED STARTS (label) | | |
| `L19` | value | `=COUNTIF(Table5[START VARIANCE],">=1")/COUNT(Table5[ACTUAL START])` | **0.4** |
| `O19` | warning | `=IF(L19>0.2,"Warning, provide Recovery Plan","")` | Warning, provide Recovery Plan |
| `L22` | PROJECT % COMPLETE (label) | | |
| `L21` | value | `=IF(M12>TODAY(),0,((TODAY()-M12))/(O12-M12))` | **0.7486** ⚠️ volatile |
| `O21` | warning | `=IF(L21<((TODAY()-M11))/(O11-M11),"Warning, slippage…","")` | (blank) |

`L17`/`M17` hold the column labels "Contract" / "Baseline" for the variance pair.

### Average daily manpower (`P17` header)

| Cell | Formula | Cached | | Cell | Formula | Cached |
|---|---|---|---|---|---|---|
| `P18` | `=+SCHEDULE!C26` | Sub 1 | | `T18` | `=+SCHEDULE!D26` | 0 |
| `P19` | `=+SCHEDULE!C27` | Sub 2 | | `T19` | `=+SCHEDULE!D27` | 0 |
| `P20` | `=+SCHEDULE!C28` | Sub 3 | | `T20` | `=+SCHEDULE!D28` | 0 |
| `P21` | `=+SCHEDULE!C29` | Sub 4 | | `T21` | `=+SCHEDULE!D29` | 0 |
| `P22` | `=+SCHEDULE!C30` | Sub 5 | | `T22` | `=+SCHEDULE!D30` | 0 |

### Priority items table (`Table3714`)

Header row 10 · data rows 12, 14, 16, 18, 20 (two-row spacing).

| Dashboard col | Header cell | Source | Data rows |
|---|---|---|---|
| `V` | `V10` = `=+Table3714[[#Headers],[STATUS SUMMARY]]` | `SCHEDULE!D35:D39` | `V12`, `V14`, `V16`, `V18`, `V20` |
| `W` | `W10` = `=+SCHEDULE!E34` | `SCHEDULE!E35:E39` | `W12`…`W20` |
| `AB` | `AB10` = `=+SCHEDULE!F34` | `SCHEDULE!F35:F39` | `AB12`…`AB20` |
| `AG` | `AG10` = `=+SCHEDULE!G34` | `SCHEDULE!G35:G39` | `AG12`…`AG20` |
| `AL` | `AL10` = `=+SCHEDULE!H34` | `SCHEDULE!H35:H39` | `AL12`…`AL20` |

Note the **schedule item name column (`SCHEDULE!C`) is never displayed** — only the status
and the four narrative columns. The dashboard shows recovery plans without saying which
item they belong to.

---

## Section 3 — RISKS (`J25`)

Header row 27 · data rows 28, 30, 32, 34, 36, 38, 40, 42.

| Dashboard col | Header | Source column | Data rows |
|---|---|---|---|
| `K` | `K27` = `=+RISKS!C2` | `RISKS!C3:C10` (description) | 28,30,32,34,36,38,40,42 |
| `T` | `T27` = `=+RISKS!D2` | `RISKS!D` (impact) | " |
| `V` | `V27` = `=+RISKS!E2` | `RISKS!E` (mitigation) | " |
| `AJ` | `AJ27` = `=+RISKS!F2` | `RISKS!F` (owner) | " |
| `AM` | `AM27` = `=+RISKS!G2` | `RISKS!G` (status) | " |

**The `RISK #` column is not displayed.** Header says "Ranked by Severity" but rows appear
in source order — no sort is applied anywhere.

---

## Section 4 — SAFETY (`J46`)

### Activity log (`Table20`)

Header row 48 · data rows 49, 51, 53, 55, 57.

| Dashboard col | Header | Source |
|---|---|---|
| `K` | `=SAFETY!B36` (TIMEFRAME) | `SAFETY!B37:B41` |
| `M` | `=SAFETY!C36` (CATEGORY) | `SAFETY!C37:C41` |
| `P` | `=SAFETY!D36` (DESCRIPTION/ACTIVITY) | `SAFETY!D37:D41` |
| `U` | `=SAFETY!E36` (STATUS) | `SAFETY!E37:E41` |
| `W` | `=SAFETY!F36` (NOTES/OUTCOME/ACTION) | `SAFETY!F37:F41` |
| `AE` | `=SAFETY!G36` (RESPONSIBLE) | `SAFETY!G37:G41` |

### KPI tiles

| Tile | This-period cell | To-date cell | Label cells | Cached |
|---|---|---|---|---|
| TOTAL HOURS WORKED | `AI48` (INDEX/MATCH + MTM %) | `AM48` = `=SAFETY!D34` | `AI50`, `AI49`, `AM49` | `4,635 / 9.7%` · `114,231` |
| RECORDABLE INCIDENTS | `AI51` = `INDEX(SAFETY!E3:E33, MATCH(AU4,…))` | `AM51` = `=SAFETY!E34` | `AI53`, `AI52`, `AM52` | `0` · `1` |
| TOTAL ORIENTATIONS | `AI54` (INDEX/MATCH + MTM %) | `AM54` = `=SAFETY!F34` | `AI56`, `AI55`, `AM55` | `17 / -29.2%` · `120` |
| VIOLATIONS | `AI57` = `=SAFETY!L27` ($ value) | `AM57` = `=COUNTIF(SAFETY!L3:L26,">1")` ⚠️ | `AI59`, `AI58`, `AM58` | `1000` · `1` |

`AI51` is the only tile returning a **raw number** rather than a text string — which is
why it is the one safety value the scorecard can consume.

---

## Section 5 — QUALITY (`J62`)

### KPI tiles

| Cell | Formula | Cached |
|---|---|---|
| `K64` | `=INDEX(QUALITY!D3:D34, MATCH(AU4, QUALITY!C3:C34, 0))` | 17 (observations this period) |
| `M64` | `=QUALITY!D35` | 77 (observations to date) |
| `O64` | `=INDEX(QUALITY!E3:E34, MATCH(AU4, QUALITY!C3:C34, 0))` | 0 (punchlist this period) |
| `P64` | `=QUALITY!E35` | 0 (punchlist to date) |
| `K67` | `=IF(QUALITY!D38=0,"N/A",QUALITY!D38)` | 1 (obs. avg days past due) |
| `M67` | `=IF(QUALITY!D39=0,"N/A",QUALITY!D39)` | 2 (obs. avg days to close) |
| `O67` | `=IF(QUALITY!E38=0,"N/A",QUALITY!E38)` | 3 (punch avg days past due) |
| `P67` | `=IF(QUALITY!E39=0,"N/A",QUALITY!E39)` | 4 (punch avg days to close) |

Labels: `K65`/`M65` "This Period"/"Total to Date" · `K66`/`O66` "OBSERVATIONS"/"PUNCHLIST"
· `K68`/`M68`/`O68`/`P68` "AVG. DAYS PAST DUE"/"AVG. DAYS TO CLOSE"

### Main offenders (`K70` / `O70` headers)

`K71:K75` ← `QUALITY!D40:D44` · `O71:O75` ← `QUALITY!E40:E44` → STNY, ABM, TRYSLER ×3

### Quality issue log (`Table16`)

Header row 64 · data rows 65–75, **contiguous** (no row spacing, unlike the other logs).

| Dashboard col | Source column |
|---|---|
| `R` | `QUALITY!B` (TIMEFRAME) |
| `U` | `QUALITY!C` (CATEGORY) |
| `AA` | `QUALITY!D` (DESCRIPTION) |
| `AJ` | `QUALITY!E` (TRADE) |
| `AM` | `QUALITY!F` (STATUS) |
| `AO` | `QUALITY!G` (OUTCOME / COMMENTS) |
| `AT` | `QUALITY!H` (RESPONSIBLE) |
| `AU` | `QUALITY!I` (ACTION PLAN) |

> `AT64:AU75` (quality log) and `AT36:AV38` (financial budget grid) occupy the same
> columns at different rows — the Quality and Financial sections **interleave** in
> column space. A real constraint on the Excel layout that vanishes in Power BI.

---

## Section 6 — FINANCIAL (`AQ7`)

### Money waterfall (`AR9:AU19`)

| Cell | Label | Value cell | Formula | Cached |
|---|---|---|---|---|
| `AR9` | Original Contract Amt. | `AT9` | `=FINANCIALS!C3` | 8,800,000 |
| `AR10` | Current Contract Amt. | `AT10` | `=FINANCIALS!C4` | 9,116,960.48 |
| | | `AU10` | `=FINANCIALS!E4` | 1.14% |
| `AR11` | Variance | `AT11` | `=(AT10-AT9)/AT9` | 3.60% |
| `AR12` | Pending CO's | `AT12` | `=FINANCIALS!C5` | 84,328.46 |
| | | `AU12` | `=FINANCIALS!E5` | −64.11% |
| `AR13` | Contingency Remaining | `AT13` | `=FINANCIALS!C9` | N/A |
| `AR14` | Billed this Month | `AT14` | `TEXT($) & " / " & TEXT(%)` | `$400,000.0 / 4.4%` |
| `AR15` | Total Billed | `AT15` | " | `$2,997,804.2 / 32.9%` |
| `AR16` | Total Paid | `AT16` | " | `$2,683,097.5 / 29.4%` |
| `AR17` | Remaining Balance | `AT17` | " | `$6,433,863.0 / 70.6%` |
| `AR18` | Retainage | `AT18` | " | `$127,441.6 / 1.4%` |
| `AR19` | Cost to Complete | `AT19` | " | `$6,786,492.3 / 74.4%` |

`AU9` holds the column header "MTM DELTA". Every `AT14:AT19` percentage is against
`FINANCIALS!C4` (current contract).

### Financial KPIs

| Value cell | Label cell | Formula | Cached |
|---|---|---|---|
| `AT21` | `AT22` AGE OF OLDEST UNAPPROVED CO | `=FINANCIALS!C6` | 1 |
| `AT23` | `AT24` RISK BOUGHT OUT | `=FINANCIALS!D62` | 0.95 |
| `AT25` | `AT26` AGING BALANCE | `=+FINANCIALS!F57` | 1 |
| `AT27` | `AT28` AVG. DAYS FOR PAYMENT RECEIVED | `=FINANCIALS!F56` | 8.818 |

> ⚠️ `AT25` (aging **balance**) is what `SCORECARD CALC!E4` reads for its "Accounts
> Receivable" day-count bands. `AT27` (avg **days**) is almost certainly the intended
> driver. See defect #4.

### Judgment tiles

| Cell | Formula | Cached |
|---|---|---|
| `AS30` | `="Profitability is " & FINANCIALS!C7` | Profitability is Margin fade but no plan |
| `AS31` | `=FINANCIALS!C8` | `< 50% = 🔴 Bad Cash Position` |

### Cost-management flags

| Value | Label | Formula | Cached |
|---|---|---|---|
| `AR32` | `AT32` MONTH END CLOSED OUT | `=FINANCIALS!E65` | 🟢 Y |
| `AR33` | `AT33` PROCORE FORECASTING IN LINE W/SCHEDULE | `=FINANCIALS!E66` | 🔴 N |
| `AR34` | `AT34` MONITORED RESOURCES UPDATED | `=FINANCIALS!E67` | 🔴 N |

### GC/GR budget grid

Headers `AS36` Budget · `AT36` Forecast · `AU36` Spent to Date / % · `AV36` Status

| Row | Label | Budget | Forecast | Spent | Status |
|---|---|---|---|---|---|
| 37 | `AR37` "GR's" | `AS37` = `=FINANCIALS!C19` → 299,746.97 | `AT37` → 89,149.77 | `AU37` → `$15,000.00 / 5.0%` | `AV37` → 🔴 Over Budget |
| 38 | `AR38` "GC's" | `AS38` = `=FINANCIALS!C20` → 850,018.69 | `AT38` → 323,265.39 | `AU38` → `$20,000.00 / 2.4%` | `AV38` → 🟢 On Track |

> The two status values look inverted relative to the numbers — GR's is at 5% of budget
> spent and flagged **Over Budget**; GC's at 2.4% is **On Track**. Because `F19`/`F20` are
> hand-picked dropdowns rather than derived from the variance rule in `H18:J21`, nothing
> catches this. Confirm with Affect whether the flag means something other than what the
> legend says.

### OT hours

| Cell | Formula | Cached |
|---|---|---|
| `AT40` | `TEXT(INDEX(FINANCIALS!J25:J55, MATCH(AU4,…)),"#,###,###") & " / " & TEXT(MoM %,"0%")` | `44 / 107%` |
| `AU40` | `=FINANCIALS!J56` | 112.5 |
| `AT41`/`AU41` | labels "This Period / MTM Delta" · "Total to Date" | |
| `AT42` | label " OT HOURS" | |

---

## Section 7 — CRITICAL SUBMITTALS & RFIS (`AQ44`)

**The workbook's only chart.**

| Property | Value |
|---|---|
| Type | `BarChart` (clustered) |
| Anchored at | column 42 (`AQ`), row 44 |
| Series 1 | `'SUBMITTALS & RFI'!$C$3:$C$13` — Open Critical RFIs |
| Series 2 | `'SUBMITTALS & RFI'!$D$3:$D$13` — Open Critical Submittals |
| Categories | `'SUBMITTALS & RFI'!$B$3:$B$13` — Trade |

Range extends to row 13 but only rows 3–11 hold trades; rows 12–13 are zero-padding.

---

## Section 8 — SCORECARD (`B62`)

| Cell | Content | Formula | Cached |
|---|---|---|---|
| `C64` | Label | "PROJECT SCORECARD" | |
| `C65` | Score | `='SCORECARD CALC'!G31` | **0.59** |
| `C71` | Label | `="CLIENT SATISFACTION FROM: " & 'SCORECARD CALC'!C34` | CLIENT SATISFACTION FROM: ANONYMOUS |
| `C72` | Score | `='SCORECARD CALC'!C42` | **0.60** |

### Conditional formatting (the only rules in the workbook)

| Range | Rule | Band |
|---|---|---|
| `C65:G67` | `cellIs between` | `0` – `0.5` |
| `C65:G67` | `cellIs between` | `0.5` – `0.75` |
| `C65:G67` | `cellIs between` | `0.75` – `1` |
| `C72:G73` | `cellIs between` | `0` – `0.5` |
| `C72:G73` | `cellIs between` | `0.5` – `0.75` |
| `C72:G73` | `cellIs between` | `0.75` – `1` |

Both current values (`0.59`, `0.60`) land in the **middle amber band**.

> Overlapping bounds: `0.5` and `0.75` each appear in two rules. Excel applies the
> first matching rule in priority order, so the behaviour is deterministic but the intent
> is ambiguous. Define the bands as `[0, 0.5)`, `[0.5, 0.75)`, `[0.75, 1]` in Power BI.

---

## Orphan cell

| Cell | Value |
|---|---|
| `AU2` | **`#VALUE!`** |

An error sits above the reporting-month anchor with no visible label. The formula is
stored as the literal error string, so its original expression is not recoverable from the
file. Ask Affect what it was meant to be. See defect #1.

---

## What this means for the Power BI report

1. **The layout is a workaround, not a design.** Narrow merged columns, hardcoded row
   spacing, sections interleaved in column space — all consequences of fitting a report
   onto one printable sheet. None of it should be reproduced literally.
2. **Most tiles are text strings.** `"$2,997,804.2 / 32.9%"` cannot be charted, sorted, or
   compared. Splitting each into two numeric measures gives the same card visual and makes
   trending possible for free.
3. **Every list has a hard cap** — 4 wins, 8 risks, 5 priority items, 5 subs, 5 safety
   entries, 10 quality entries. Every one of these is a table visual in Power BI with no
   cap at all.
4. **Three source columns are never displayed** (risk #, schedule item name, VLN
   description). Worth confirming these are genuinely unwanted rather than accidentally
   dropped.
