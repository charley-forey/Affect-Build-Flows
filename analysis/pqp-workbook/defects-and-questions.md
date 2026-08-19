# PQP workbook — defects and open questions

Source: `resources/026-025 SAUNA LOUNGE QA - QC TRACKER DRAFT 2026-7-5.xlsx`
Reviewed 2026-08-19, against the file as received. 44 sheets.

Same method as the Monthly Progress Report teardown in `analysis/excel-tracker/`: rebuild the
numbers independently, then compare. Every finding below was reproduced by script, not spotted
by eye, and each names the cells so it can be checked.

---

## D1 — Four register roll-ups count their numerator over a shorter range than their denominator

**Severity: high (latent — it starts producing wrong numbers as the registers fill up).**

On the DASHBOARD, "Total" and "Complete" for four registers are counted over different row
ranges. The totals count a long range; the completions count a short one.

| Register | Total counts rows | Complete counts rows | Blind rows |
|---|---|---|---|
| Special Inspections | 7–80 | 7–45 | **35** |
| Statutory Inspections | 7–60 | 7–40 | **20** |
| Commissioning | 7–60 | 7–50 | **10** |
| Path to TCO | 9–71 | 9–70 | 1 |

Cells: `DASHBOARD!B9` → `'Special Inspections'!B4` = `COUNTA($A$7:$A$80)`, against
`DASHBOARD!C9` = `COUNTIF('Special Inspections'!P7:P45,"Closed")`. The other three follow the
same pattern (`C8`, `C11`/`E11`, `E6`).

**What it does.** Add a special inspection beyond row 45 and close it. The total goes up. The
closed count cannot. `% Complete` falls, and can never reach 100% no matter how much work is
finished. The failure is silent, produces a clean plausible percentage, and moves in the
direction that makes the project look *behind* — so the likely response is someone overriding
the figure by hand, which removes the last link between the dashboard and the registers.

**Why it hasn't bitten yet.** Current volumes sit under the numerator ceilings — 24 statutory
inspections against a ceiling of 34, and so on. This breaks precisely when the project gets
busy, which is when the dashboard matters most.

**In the rebuild:** a percentage is computed from the rows themselves, so there is no range to
get wrong. A DQ expectation asserts that every register's completed count is a subset of its
total.

**By contrast:** all 26 trade checklist tabs were checked for the same defect and all 26 are
correct — their roll-up ranges match their item extents exactly.

---

## D2 — Two CSI spec references destroyed by Excel's date coercion, both on Tier 4 Critical items

**Severity: medium (data already lost in the file as received).**

`DFOW Risk Register` column F ("CSI Div / Spec"). Of 32 DFOWs, 30 are intact and **2 are
corrupted**, because the column is General-formatted and Excel read the spec code as a date:

| DFOW | Should be a CSI code | Actually stored |
|---|---|---|
| **D-01** Wet-area waterproofing — pool deck, locker rooms, showers, kitchen | e.g. `07 21 00` | `2009-03-07 00:00:00` |
| **D-02** Waterproofing interface w/ Owner's pool, sauna & cold plunge assemblies | e.g. `07 00 00` | `7` |

These are not two random rows. **D-01 and D-02 are the only Tier 4 "Critical" waterproofing
DFOWs** — the highest-risk items in the register, carrying HOLD points before cover-up and a
joint inspection with the Owner's vendor. Their spec references are the ones that got lost.

The original values are not recoverable from the file; they need to be re-entered from the
spec. **The fix is to format the column as Text before entry** — otherwise it recurs on the
next project, and only ever on codes that happen to look like dates.

*In the rebuild:* CSI codes are typed as strings end to end, and the extractor
(`_local/extract_pqp_workbook.py`) detects and reports this coercion rather than importing a
date into a spec field.

---

## D3 — The NCR Log sheet is hidden

**Severity: medium (process, not arithmetic).**

`NCR Log` has `sheet_state = hidden`. It is the only hidden sheet in the workbook.

The workbook treats it as central: COVER A45 makes NCRs a governing process ("Seven-step NCR
process; NCRs closed before the next progress billing is approved"), and DASHBOARD rows 22–24
report open NCRs, NCRs past target close date, and average days to close — all reading from the
hidden sheet. A register that gates progress billing should not be one unhide away from
existence.

Most likely accidental. Worth confirming it was not hidden deliberately to suppress something.

---

## D4 — The workbook carries no job number

**Severity: high for integration (this is the join key).**

`COVER!B17` (*Affect Build Job Number*) and `COVER!B18` (*DOB Job / Filing Number*) are both
**empty**.

The job number is how this workbook connects to everything else. Procore project names in the
production tenant embed it directly — `26-025 - SaunaLounge 45 South 3 Street, Brooklyn, NY`,
`25-016 - 1100 Fulton Street`. The filename says `026-025`. The SharePoint folder convention
in the Power Automate SOP is `YY-###-Project Name`. All four are the same key.

We have inferred **`26-025`** from the filename and matched it to the Procore project. That
inference should be **confirmed, not assumed** — and the field should be filled in on the
template so the next project does not need inferring.

---

## D5 — The COVER description miscounts its own register

**Severity: low.**

`COVER!B53` describes Path to TCO as "45 sequenced statutory gates from permit issuance to
Certificate of Occupancy". The tab contains **46** (A1–A7, B1–B7, C1–C5, D1–D11, E1–E3, F1–F8,
G1–G5 = 7+7+5+11+3+8+5).

Trivial in itself, and listed only because it is the reason the seed extractor asserts counts
it measured rather than counts the workbook claims — the same discipline that surfaced D1.

---

## Structural findings (not defects — these shape the rebuild)

**44 sheets collapse to 9 tables.** 26 of the 44 are trade checklists sharing one identical
11-column schema (625 items total). Three more — Path to TCO (46), Path to Fire Alarm (23),
Statutory Inspections (24) — share a second common shape. In Excel these must be separate tabs;
in a relational model they are two tables with a discriminator column.

**Procore is already the system of record for much of this.** COVER A47 states it outright:
*"Procore is the mandatory system of record. This workbook is the project control and reporting
mirror."* The `Project Identifiers` tab then maps each QA activity to its Procore tool —
Observations, Punchlists, Submittals, Inspections, Photo Documentation. So the NCR log, punch
list and submittal register should be **read from the Procore API**, not retyped. Only what
Procore does not hold (statutory gates, DFOW risk tiers, the ITP, DOH checklist, inspector
sign-in, commissioning) needs manual capture.

**25 controlled vocabularies** are defined as data-validation lists across the workbook. They
become one status dimension, generated once and used by both the SharePoint choice columns and
the report — so the two cannot drift.

---

## Open questions for Affect

1. **Confirm the job number is `26-025`** and fill `COVER!B17` on the template.
2. **Are the 625 trade checklist items Affect's standard library, or written for SaunaLounge?**
   We have built them as a versioned standard library that every project instantiates against.
   If they are per-project, that decision reverses cheaply now and expensively later.
3. **Was the NCR Log hidden deliberately?**
4. **D-01 / D-02 CSI codes** — supply the correct spec references.
5. **Who owns entry for each register?** The workbook names a Q-Team (PM, Superintendent, APM,
   Director of Construction) but not who types what, which determines the SharePoint permissions.
6. **Is "PEP" this workbook, or a separate document?** The request referred to a PEP; the
   artifact is titled Project Quality Plan (PQP). Treated as the same thing here.
