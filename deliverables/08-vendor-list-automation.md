# D8 — Quick-Win Automation: Vendor / Insurance / Contract List

**Status:** 🔴 Not started | **Phase:** 1 — Foundation | **Billing:** $125/hr — 3 hrs in Phase 0 | **Target:** Within the initial 20-hour month

> Proposed by Rebecca on the Jul 23 warehouse review as a fast, visible win to run alongside
> the ingestion review. Deliberately small: it proves the pipeline pattern end to end and
> gives Rebecca something she can extend herself.

## Objective
Give the team a single always-current vendor list — with insurance status and contract
details — replacing the manual lookup that happens today across Procore and email.

## Scope
**In:** Vendor/company data from Procore, insurance certificate status, associated
commitments and contract values, a refreshing output the team can actually open.
**Out:** Insurance expiry alerting, vendor onboarding workflow, Ramp/ADP vendor data. Those
become their own deliverables if wanted.

## Key data
- Procore **companies / vendors** — name, ID, contact, trade
- Procore **insurance** — certificate type, carrier, effective and expiration dates, status
- Procore **commitments** — contract value, executed status, per vendor
- The **vendor ID** — the same field that D4's bridging work depends on, which is why this
  doubles as a live test of that linkage

## Integration approach
Same unit as every other source: Procore API → notebook → bronze → transformation → silver
Lakehouse → Power BI. Reuses Rebecca's existing notebook pattern rather than inventing a new
one — the point is to prove the pattern, hardened per D2 (secrets out of cells, incremental
where it makes sense).

## Tasks
- [ ] Confirm which Procore endpoints expose insurance and certificate status
- [ ] Verify vendor ID lands intact through transformation (shared check with D4)
- [ ] Ingestion notebook — vendors + insurance + commitments
- [ ] Simple Power BI page or table output: vendor, trade, insurance status, expiry, contract value
- [ ] Record the walkthrough for Rebecca
- [ ] Hand over — Rebecca extends it to one additional field unaided

## Acceptance criteria
- List refreshes without manual intervention
- Insurance status is accurate against a spot-check of 5 vendors
- Rebecca can add a field to it without help — the real test

## Files & resources
- [`resources/procore/endpoints-cheatsheet.md`](../resources/procore/endpoints-cheatsheet.md)
- `meeting-notes/2026-07-23-warehouse-review.md` — where this was proposed
- (add: notebook, recording, Power BI page)

## Log
| Date | Note |
|---|---|
| 2026-07-23 | Proposed by Rebecca as a quick-value automation alongside the ingestion review |
| 2026-07-24 | Formalised as D8 and allocated 3 hrs within the Phase 0 twenty-hour scope |
