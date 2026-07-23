# ADP

Payroll. **Integration status: not integrated.**

## Relevance to this engagement

Two fields in the Monthly Progress Report may source from here rather than Sage:

| Excel field | Cells |
|---|---|
| `HOURS WORKED THIS PERIOD` | `SAFETY!D3:D33` — feeds total hours and the TRIR calculation |
| `OT HOURS WORKED THIS PERIOD` | `FINANCIALS!J25:J55` |

Both are typed in by hand today. **Sage 100 Contractor also runs payroll**, so there is a
system-of-record decision to make: Sage or ADP?

Worth resolving because hours worked feeds `[TRIR]` — a standard industry safety rate that
Affect could report but currently does not, and which becomes free once hours and incidents
are both in the model.

## Documentation

| Resource | URL |
|---|---|
| Developer portal | https://developers.adp.com |
| API documentation | https://developers.adp.com/articles/api |
| Marketplace | https://apps.adp.com |

> ADP's API requires certificate-based authentication and a partner/marketplace
> registration. It is meaningfully more involved to integrate than Procore or a SQL
> connection — **do not assume this is a quick win.**

## Open questions

1. **Sage or ADP** — which is the source of truth for hours worked by job?
2. Are hours tracked **by job/project** in ADP, or only by employee? (If only by employee,
   it cannot feed a per-project report at all.)
3. Is there an existing ADP ↔ Sage sync?
4. Would Procore Timesheets be a better source, given Procore is already integrated?
   `/rest/v1.0/projects/{project_id}/timecard_entries` exists.
5. What is the ADP account tier, and does it include API access?
