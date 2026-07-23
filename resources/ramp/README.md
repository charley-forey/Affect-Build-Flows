# Ramp

Vendor payments and corporate cards. **Integration status: not integrated.**

## Relevance to this engagement

Not required for the Monthly Progress Report replacement — nothing in the Excel tracker
sources from Ramp.

Relevant to [D6 — Power Automate payments](../../deliverables/06-power-automate-payments.md),
where it is a likely endpoint of the payment workflow.

## Documentation

| Resource | URL |
|---|---|
| Developer docs | https://docs.ramp.com |
| API reference | https://docs.ramp.com/developer-api/v1/overview |
| Product site | https://ramp.com |

> Ramp publishes a REST API with OAuth 2.0. Scopes and availability depend on the plan —
> verify what Affect's account supports before scoping anything against it.

## Open questions

1. What does Affect use Ramp for — vendor payments, cards, expenses, or all three?
2. Where does it sit in the AP process relative to Sage 100 Contractor? Which system is
   the source of truth for "paid"?
3. Is there an existing Ramp ↔ Sage sync, or is it reconciled manually?
4. Does the current API plan include the endpoints a payment flow would need?
