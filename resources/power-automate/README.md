# Power Automate

Workflow automation. **Integration status: planned — not yet built.**

Two deliverables depend on it:
[D6 payments](../../deliverables/06-power-automate-payments.md) ·
[D7 lien waivers](../../deliverables/07-power-automate-lien-waivers.md)

## Documentation

| Topic | URL |
|---|---|
| Getting started | https://learn.microsoft.com/en-us/power-automate/getting-started |
| Cloud flows overview | https://learn.microsoft.com/en-us/power-automate/overview-cloud |
| Approvals | https://learn.microsoft.com/en-us/power-automate/get-started-approvals |
| Connector reference | https://learn.microsoft.com/en-us/connectors/connector-reference/ |
| Custom connectors | https://learn.microsoft.com/en-us/connectors/custom-connectors/ |
| Licensing | https://learn.microsoft.com/en-us/power-platform/admin/power-automate-licensing/types |

## Relevant connectors

| Connector | Use |
|---|---|
| SharePoint | The manual input workbook — trigger on modify |
| Outlook / Office 365 | Notifications, approval routing |
| Approvals | Payment and lien-waiver approval chains |
| SQL Server | Sage 100 Contractor (read-only), via gateway |
| Teams | Notifications where Affect already works |
| **Procore** | ⚠️ Verify whether a certified connector exists, or whether this needs a custom connector over the REST API |

## Notes for this engagement

**Procore connector availability is the first thing to check.** If there is no certified
connector, a custom connector wrapping the REST API is the path — and it can reuse the
same OAuth app as the ETL, which is worth designing for up front.

**Sage 100 Contractor is read-only.** Any flow that appears to "write to Sage" is really
writing to Procore and letting the connector sync it — see the sync directions in
[`../procore/README.md`](../procore/README.md). Worth being explicit about this when
scoping D6, because it constrains what is possible.

**Where the manual input workbook fits.** A SharePoint trigger on the input file can drive
notifications ("PM hasn't updated risks this month") without any additional infrastructure.
Cheap, useful, and it directly addresses one of the failure modes of the manual-input
approach — that people stop filling it in.

**Licensing.** Premium connectors (SQL Server, custom connectors) require per-user or
per-flow premium licensing. Confirm what Affect has before designing a flow that depends
on one.

## Open questions

1. Does a certified Procore connector exist, or is a custom connector needed?
2. What does Affect's current payment approval process look like end to end, manually?
3. Same for lien waivers — who signs, in what order, and what triggers the request?
4. Where do Ramp and ADP fit into the payment flow?
5. What Power Platform licensing is in place?
