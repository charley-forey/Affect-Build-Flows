# D8 — Quick-Win Automation: Vendor / Insurance / Contract List

**Status:** 🟡 **Data delivered inside D5; standalone report not built** | **Phase:** 1 — Foundation | **Billing:** $125/hr — ~1 of 3 hrs in Phase 0 | **Target:** Build the standalone view if still wanted

> **The data shipped; the deliverable changed shape.** The vendor, insurance and contract data all landed — `fct_VendorInsurance` (**105 rows**), `dim_Vendor` (126), `bridge_ProjectVendor` (393), `bridge_VendorCostCode` (407) — and reached leadership as a **Vendor Insurance page in the Monthly Progress Report** plus insurance exposure on the Portfolio page, rather than as the standalone always-current list this deliverable described. A separate `Vendor & Insurance List` report was named in an early README and **never built**; that reference has been removed, and the ~2 unspent hours cover it if Affect still wants it as its own artifact.
>
> Shipping it inside the report was the right call once the report existed — one place to look, one refresh, one set of permissions — but it does mean the acceptance criterion "Rebecca can add a field to it without help" has not been tested.
>
> **Two findings that need a human, not a fix — and they matter more than the deliverable.** All **105 of 105** certificates on file are expired, the most recent expiry is 2025-04-01, and only 23 of 251 vendors have a certificate at all — of those, 6 are on a current project. And `Vendors Missing From ERP` reads **125 of 251**: half the vendor master is unmatched. The likelier reading of the insurance number is that Procore's insurance module was populated once and abandoned, not that Affect's subcontractors are uninsured. Those are very different facts for a general contractor and nothing in the current reporting distinguishes them. The model therefore keeps **coverage** (is there a certificate?) separate from **currency** (is it in date?). **These are questions for Affect, not conclusions from us.**

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
- [x] Confirm which Procore endpoints expose insurance and certificate status
- [x] Verify vendor ID lands intact through transformation — bronze stores the unparsed payload, so it structurally cannot drop the ID
- [x] Ingestion — vendors, insurance and commitments land through the shared extractor, not a bespoke notebook
- [x] Power BI output — a Vendor Insurance page in the Monthly Progress Report, plus insurance exposure on the Portfolio page
- [ ] **Put the all-expired finding in front of Affect as a question** — the highest-value item on this deliverable
- [ ] Record the walkthrough for Rebecca
- [ ] Hand over — Rebecca extends it to one additional field unaided (the real acceptance test, still untested)

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
| 2026-08-02 | Data landed and shipped **inside the Monthly Progress Report** rather than as a standalone list: `fct_VendorInsurance` 105 rows, a Vendor Insurance page, and vendor spend sliced by cost code — a linkage that exists in no single Procore object. Every certificate on file is expired; raised as a question, not rendered as a green tick. |
| 2026-08-19 | Status corrected from "Not started". The standalone list was never built and is not planned; the `Vendor & Insurance List` report named in an early README never existed and the reference has been removed. |
