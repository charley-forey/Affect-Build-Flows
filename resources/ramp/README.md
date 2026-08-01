# Ramp

Vendor payments and corporate cards. **Integration status: not integrated.**

## Relevance to this engagement

Not required for the Monthly Progress Report replacement — nothing in the Excel tracker
sources from Ramp.

Relevant to [D6 — Power Automate payments](../../deliverables/06-power-automate-payments.md),
where it is a likely endpoint of the payment workflow.

## Documentation

The full API documentation is **vendored in this repo** — see
[`endpoints-cheatsheet.md`](endpoints-cheatsheet.md) for all 246 operations, or
[`api-docs/`](api-docs/) for the raw sources.

| File | Size | What it is |
|---|---|---|
| [`endpoints-cheatsheet.md`](endpoints-cheatsheet.md) | 46 KB | **Start here.** All 246 operations grouped by resource, with OAuth scope, plan gating, and beta flags. Generated — do not hand-edit. |
| [`api-docs/developer-api.json`](api-docs/developer-api.json) | 2.1 MB | OpenAPI 3.0.2 spec. 169 paths, 246 operations, 72 scopes. Feed this to codegen or an API client. |
| [`api-docs/llms-api.txt`](api-docs/llms-api.txt) | 496 KB | Same endpoints as prose — request/response shapes, readable without a spec viewer. |
| [`api-docs/llms-guides.txt`](api-docs/llms-guides.txt) | 320 KB | All 45 narrative guides (auth, pagination, webhooks, ERP integrations, bill pay…). |
| [`api-docs/llms.txt`](api-docs/llms.txt) | 16 KB | Ramp's own index and integration-decision guidance. |

To refresh: `bash api-docs/refresh.sh` — re-downloads all four files and regenerates the
cheatsheet. Ramp publishes these machine-readable exports directly at `docs.ramp.com`
(`/openapi/developer-api.json`, `/llms*.txt`), so nothing is scraped and nothing needs
credentials. The rendered docs pages are JavaScript shells and are not worth fetching.

| Resource | URL |
|---|---|
| Developer docs | https://docs.ramp.com |
| API reference | https://docs.ramp.com/developer-api/v1/introduction |
| Product site | https://ramp.com |

### What the docs tell us before we ask anyone

- **Base URL** `https://api.ramp.com`, paths under `/developer/v1/`. OAuth 2.0
  authorization code flow; 72 scopes, granted per app.
- **44 of 246 operations require Ramp Plus** (`x-ramp-plus-required` in the spec). This is
  the concrete form of open question 4 below — the answer is a plan check, not a
  conversation with Ramp.
- **120 operations are flagged beta**, 3 deprecated. Anything load-bearing should avoid
  both.
- Pagination is cursor-based (`start` + `page_size`, max 100) — not offset. Matters for
  any incremental load.
- The **"Export To A Data Warehouse"** guide — the single most relevant one to this
  engagement — is an unwritten stub ("This Use case is being authored", tracked ADP-2477).
  There is no vendor-blessed warehouse export pattern to copy; we would build it from the
  transaction and accounting endpoints ourselves.

## The Ramp CLI

Ramp ships an open-source CLI ([github.com/ramp-public/ramp-cli](https://github.com/ramp-public/ramp-cli)).
**It is not a documentation tool** — it does not export or extract docs, so it played no
part in getting the files above into this repo. It authenticates a *person* via
`ramp auth login` and acts as that user against live data: `transactions list`,
`bills approve`, `receipts upload`, `reimbursements submit`, and so on.

Two consequences worth knowing before anyone reaches for it:

- **Actions are attributed to the logged-in user.** Approving a bill through the CLI looks
  in Ramp exactly like that person approving it in the dashboard. It is not a service
  account.
- **Visibility follows that user's role.** Non-admins see only their own records. If you
  can't see it in the dashboard, the CLI won't show it either.

Where it *is* useful for us: `--agent` mode emits JSON, and it defaults to the sandbox
environment, which makes it a fast way to eyeball real response shapes while scoping
[D6 — Power Automate payments](../../deliverables/06-power-automate-payments.md) without
writing an OAuth client first. For a scheduled, service-owned pipeline, use the Developer
API instead.

Ramp also publishes an MCP server (see the MCP guides in `api-docs/llms-guides.txt`) for
conversational access. Same attribution and permission caveats apply.

## Open questions

1. What does Affect use Ramp for — vendor payments, cards, expenses, or all three?
2. Where does it sit in the AP process relative to Sage 100 Contractor? Which system is
   the source of truth for "paid"?
3. Is there an existing Ramp ↔ Sage sync, or is it reconciled manually?
4. Does the current API plan include the endpoints a payment flow would need?
