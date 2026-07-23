# Drop-downs & Status Values

The `DROPDOWN` sheet backs every data validation in the workbook. 15 lists across
columns `B` through `Q`.

**These lists are business vocabulary.** They encode how Affect classifies risk, status,
trade, and category — worth preserving exactly, then normalising into proper dimensions.

## Where each list is used

Data validation is stored as `x14` extension entries in the sheet XML (not the standard
`dataValidation` element), which is why most tools show zero validations on this file.
Extracted from the raw XML:

| Target range | Source list | Purpose |
|---|---|---|
| `RISKS!D3:D10` | `DROPDOWN!B4:B15` | Risk impact |
| `RISKS!F3:F10` | `DROPDOWN!C4:C15` | Risk owner |
| `RISKS!G3:G10` | `DROPDOWN!D4:D15` | Risk status |
| `SCHEDULE!D35:D39` | `DROPDOWN!E4:E15` | Priority-item status summary |
| `SCHEDULE!G16` | `DROPDOWN!F4:F15` | Baseline approved by client |
| `SCHEDULE!G17` | `DROPDOWN!G4:G15` | Baseline revision |
| `SAFETY!B37:B41` | `DROPDOWN!H4:H19` | Timeframe |
| `SAFETY!C37:C41` | `DROPDOWN!I4:I19` | Safety activity category |
| `SAFETY!E37:E41` | `DROPDOWN!J4:J19` | Safety activity status |
| `SAFETY!G37:G41` | `DROPDOWN!C4:C19` | Responsible (reuses owner list) |
| `SAFETY!K3:K26` | *native list* `"Open,Closed"` | Violation status |
| `QUALITY!B48:B57` | `DROPDOWN!H4:H19` | Timeframe |
| `QUALITY!C48:C57` | `DROPDOWN!K4:K40` | Quality category |
| `QUALITY!F48:F57` | `DROPDOWN!L4:L19` | Quality status |
| `QUALITY!H48:H57` | `DROPDOWN!C4:C19` | Responsible |
| `SUBMITTALS & RFI!B3:B13` | `DROPDOWN!M4:M32` | Trade |
| `FINANCIALS!F19:F20` | `DROPDOWN!N4:N19` | Budget forecast status |
| `FINANCIALS!E65:E67` | `DROPDOWN!O4:O19` | Cost-management Y/N |
| `FINANCIALS!C8:D8` | `DROPDOWN!P4:P6` | Cash position |
| `FINANCIALS!C7:D7` | `DROPDOWN!Q4:Q6` | Profitability |

> **`QUALITY!C48:C57` points at `DROPDOWN!K4:K40`** but the category list only runs to
> `K14`. Rows 15–40 are empty, so the dropdown shows 11 values followed by 26 blanks.
> Harmless, but sloppy — same for every list declared as `4:15` or `4:19` against shorter
> data.

---

## The lists, verbatim

### B — Risk impact (`RISKS TAB`)
```
🔴 High
🟡 Medium
⚪ Low
```

### C — Owner / Responsible
```
Scheduler
PM
Asst. Super
Asst. PM
Super
Senior PM
PX
Dir. of Construction
Principal
```
Reused in three places (risk owner, safety responsible, quality responsible) — already a
shared dimension in everything but name.

### D — Risk status
```
🔴 Not Started
🟡 Planned
🟡 In Progress
🟢 Complete
```
Note `Planned` and `In Progress` share the same amber emoji — the colour does not uniquely
identify the status.

### E — Priority-item status summary (`SCHEDULE`)
```
🟢 On Track
🟡 Behind
🔴 At Risk
```

### F — Baseline approved
```
🟢 Y
🔴 N
```

### G — Baseline revision
```
Rev#1 … Rev#11
```

### H — Timeframe (`SAFETY`, `QUALITY`)
```
Lookback
Lookahead
```

### I — Safety activity category
```
High-Risk Item – Completed
High-Risk Item – Upcoming
Toolbox Talk – Completed
Toolbox Talk – Scheduled
Safety Standdown – Completed
Safety Standdown – Scheduled
Weekend/OT Work – Completed
Weekend/OT Work – Planned
Notable Visitor – DOB
Notable Visitor – FDNY
Notable Visitor – Client
Notable Visitor – OSHA
Notable Visitor – Other
Safety Win – Team Performance
Safety Win – Milestone with No Incidents
Safety Win – Inspection Success
```
16 values with an implicit two-level structure: `Type – Qualifier`. Splitting on the en
dash gives a clean parent/child hierarchy (`Toolbox Talk` / `Completed`), which makes the
categories filterable rather than just listable.

### J — Safety activity status
```
🟢 Completed
🟢 Positive
🟡 Scheduled
🟡 Planned
🔴 High Risk
🔴 Delayed
```

### K — Quality category
```
Quality – High-Risk Observation
Benchmark – Completed
Benchmark – Scheduled
Mockup – Completed
Mockup – Scheduled
Delivery – Rejected
Delivery – Upcoming
Commissioning – Completed
Commissioning – Upcoming
Inspection – Special
Inspection – NCR
```
Same `Type – Qualifier` structure.

### L — Quality status
```
🔴  Open
🟢  Passed
🟡  Scheduled
🔴  Rejected
🟢  Passed
🔴  NCR
```
> ⚠️ `🟢  Passed` appears **twice** (`L5` and `L9`) and every value carries a **double
> space** after the emoji — unlike every other list, which uses a single space. Text
> matching against these values is fragile.

### M — Trades (29 values)
```
Existing Conditions ␣ · Concrete ␣ · Foundation · Superstructure · Masonry ␣ · Metals ␣
Drywall & Carpentry · Roofing · Millwork · Finishes ␣ · Specialties ␣ · Equipment ␣
Doors & Frames · Glass & Glazing · Conveying Equipment ␣ · Sprinkler · Plumbing ␣ · HVAC
Building Automation Systems ␣ · Electrical ␣ · Low Voltage · Utilities ␣ · Painting ␣
Flooring · Self Levelling · Windows · Lighting · Exterior Improvements
```
> ⚠️ **Twelve of the 29 have trailing whitespace** (marked `␣` above). `"Metals  "` will
> never equal `"Metals"` in a join. Must be trimmed at ingestion.

Roughly CSI-aligned but not strictly — worth asking whether Affect wants these mapped to
CSI MasterFormat divisions, which would let them join directly to Procore cost codes.

### N — Budget forecast status
```
🟢 On Track
🟡 Watch
🔴 Over Budget
```
Derivable from the variance rule in `FINANCIALS!H18:J21` — see `calculations.md` §5g.

### O — Cost-management Y/N
```
🟢 Y
🔴 N
```

### P — Cash position
```
≥ 100% = 🟢 Good Cash Position
50% – 99% = 🟡 Medium / Watch Zone
< 50% = 🔴 Bad Cash Position
```
The band *and* its meaning are baked into one string. `SCORECARD CALC!E10` matches these
strings exactly to resolve a score — so a single character change anywhere silently
zeroes a 12%-weighted category.

### Q — Profitability
```
Within Range
Out of Range, but has a plan
Margin fade but no plan
```
The only status list with no emoji. Matched exactly by `SCORECARD CALC!E7`.

---

## The core problem: status is a text string with an emoji in it

Every status value conflates three things:

| | Example |
|---|---|
| severity/RAG signal | `🔴` |
| human label | `High` |
| implied sort order | (none — alphabetical only) |

Consequences in the current file:
- Colour must be re-derived by reading the first character of a string.
- No sort order exists, so "Ranked by Severity" on the dashboard doesn't actually rank.
- Two lists have duplicate entries (`L`), twelve trade values have trailing whitespace (`M`).
- Scorecard scores depend on **exact string equality** against `DROPDOWN` cells.
- Emoji render inconsistently across Excel versions, Power BI, and PDF export.

## Proposed `dim_Status`

One conformed dimension for every status-like value, keyed by a stable code. The emoji
stays as a display column so exports can still match the current look, but nothing depends
on it.

| StatusKey | Domain | Code | Label | Emoji | RAG | SortOrder | HexColor |
|---|---|---|---|---|---|---|---|
| 1 | RiskImpact | HIGH | High | 🔴 | Red | 1 | `#DB1918` |
| 2 | RiskImpact | MEDIUM | Medium | 🟡 | Amber | 2 | `#FFD800` |
| 3 | RiskImpact | LOW | Low | ⚪ | Neutral | 3 | `#A6A6A6` |
| 10 | RiskStatus | NOT_STARTED | Not Started | 🔴 | Red | 1 | `#DB1918` |
| 11 | RiskStatus | PLANNED | Planned | 🟡 | Amber | 2 | `#FFD800` |
| 12 | RiskStatus | IN_PROGRESS | In Progress | 🟡 | Amber | 3 | `#FFD800` |
| 13 | RiskStatus | COMPLETE | Complete | 🟢 | Green | 4 | `#01AF00` |
| 20 | ScheduleStatus | ON_TRACK | On Track | 🟢 | Green | 1 | `#01AF00` |
| 21 | ScheduleStatus | BEHIND | Behind | 🟡 | Amber | 2 | `#FFD800` |
| 22 | ScheduleStatus | AT_RISK | At Risk | 🔴 | Red | 3 | `#DB1918` |
| 30 | SafetyStatus | COMPLETED | Completed | 🟢 | Green | 1 | `#01AF00` |
| 31 | SafetyStatus | POSITIVE | Positive | 🟢 | Green | 2 | `#01AF00` |
| 32 | SafetyStatus | SCHEDULED | Scheduled | 🟡 | Amber | 3 | `#FFD800` |
| 33 | SafetyStatus | PLANNED | Planned | 🟡 | Amber | 4 | `#FFD800` |
| 34 | SafetyStatus | HIGH_RISK | High Risk | 🔴 | Red | 5 | `#DB1918` |
| 35 | SafetyStatus | DELAYED | Delayed | 🔴 | Red | 6 | `#DB1918` |
| 40 | QualityStatus | OPEN | Open | 🔴 | Red | 1 | `#DB1918` |
| 41 | QualityStatus | PASSED | Passed | 🟢 | Green | 2 | `#01AF00` |
| 42 | QualityStatus | SCHEDULED | Scheduled | 🟡 | Amber | 3 | `#FFD800` |
| 43 | QualityStatus | REJECTED | Rejected | 🔴 | Red | 4 | `#DB1918` |
| 44 | QualityStatus | NCR | NCR | 🔴 | Red | 5 | `#DB1918` |
| 50 | BudgetStatus | ON_TRACK | On Track | 🟢 | Green | 1 | `#01AF00` |
| 51 | BudgetStatus | WATCH | Watch | 🟡 | Amber | 2 | `#FFD800` |
| 52 | BudgetStatus | OVER_BUDGET | Over Budget | 🔴 | Red | 3 | `#DB1918` |
| 60 | CashPosition | GOOD | Good (≥ 100%) | 🟢 | Green | 1 | `#01AF00` |
| 61 | CashPosition | WATCH | Watch (50–99%) | 🟡 | Amber | 2 | `#FFD800` |
| 62 | CashPosition | BAD | Bad (< 50%) | 🔴 | Red | 3 | `#DB1918` |
| 70 | Profitability | IN_RANGE | Within Range | 🟢 | Green | 1 | `#01AF00` |
| 71 | Profitability | OUT_WITH_PLAN | Out of Range, but has a plan | 🟡 | Amber | 2 | `#FFD800` |
| 72 | Profitability | MARGIN_FADE | Margin fade but no plan | 🔴 | Red | 3 | `#DB1918` |
| 80 | YesNo | Y | Yes | 🟢 | Green | 1 | `#01AF00` |
| 81 | YesNo | N | No | 🔴 | Red | 2 | `#DB1918` |

Hex values are sampled from the actual font colours on the `DROPDOWN` sheet
(`#DB1918` red, `#FFD800` amber, `#01AF00` green) so the Power BI report matches what
Affect already recognises. They carry through to `../../powerbi/theme.json`.

**Sort by `SortOrder`, colour by `HexColor`, filter by `Code`, display `Label`.** The
"Ranked by Severity" header on the risk table finally becomes true.

## Companion dimensions

**`dim_Owner`** — the 9 roles from list `C`, with a `SortOrder` reflecting seniority
(Principal → PX → Senior PM → Dir. of Construction → PM → Asst. PM → Super → Asst. Super
→ Scheduler). Confirm the hierarchy with Affect.

**`dim_Trade`** — the 29 trades from list `M`, **trimmed**, deduplicated, with an optional
`CsiDivision` column to bridge to Procore cost codes.

**`dim_ActivityCategory`** — lists `I` (16 safety) and `K` (11 quality) split on the en
dash into `CategoryType` + `CategoryQualifier`, with a `Domain` column separating safety
from quality.

## Ingestion rules

Whatever the manual-input mechanism ends up being, these apply:

1. **`TRIM()` every text value on the way in.** Twelve trade values need it today.
2. **Strip the leading emoji and space** before matching to `dim_Status[Label]`.
3. **Reject unmatched values loudly** rather than dropping the row — an unmatched status
   should surface as a data-quality flag, not disappear.
4. **Store codes, not display strings**, in the new input template. See
   [`../../powerbi/manual-input-template.md`](../../powerbi/manual-input-template.md).
