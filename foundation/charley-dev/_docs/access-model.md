# Access model — what runs as whom, and what is still missing

**Verified live 2026-08-24 as `cforey-c@affect-group.com`.** Every ✅/❌ below is a call that
was actually made, not an assumption.

## The thing Key Vault does not solve

Key Vault answers *"where does a secret live?"* It does not answer *"who is allowed onto the
on-premises data gateway?"* Those are different problems with different owners, and conflating
them has cost this engagement weeks once already (see `keyvault-runbook.md` → "The correction
that mattered").

A Fabric dataflow reaching Sage 100 does **not** fetch a password from a vault. It hands the
query to the on-premises data gateway, and the gateway authenticates to
`NC-AFFECT-1\SAGE100CON` using the credential **stored inside the gateway connection object**.
Permission to *use* that connection is an ACL entry on the connection. There is no secret to
fetch, so there is nothing Key Vault can hold that would grant it.

This is why `Fabric-SQL-Login-*`, `Fabric-Gateway-Service-Account-*` and
`Sage-Data-Gateway-Recovery-Key` — all real, all now safely stored — move Sage exactly zero
distance. They close the expired-1Password gap, which was worth closing. They are not the key
to the gateway, because the gateway does not have a keyhole.

## What this account can and cannot do

| Capability | | Evidence |
|---|---|---|
| Read and write vault secrets | ✅ | custom role `KeyVault Permissions`, data-plane, RG `Affect_Data` |
| Create an Entra app registration (service principal) | ✅ | tenant `authorizationPolicy.allowedToCreateApps = true` |
| Assign an Azure RBAC role | ❌ | `Microsoft.Authorization/*/Write` sits in `notActions` on our Contributor grant |
| Add anyone to the `Build` workspace | ❌ | `GET /workspaces/…/roleAssignments` → **403 InsufficientWorkspaceRole** (we are Member/Contributor, not Admin) |
| See any gateway or connection | ❌ | `GET /gateways` → **0**, `GET /connections` → **0** |
| Change a Fabric tenant setting | ❌ | needs a Fabric tenant admin |

**We can create the service identity. We cannot grant it anything.** That is the whole problem
stated in one line, and it is why this is a permissions task rather than a build task — there
is no code change that routes around it.

## The two dependencies, separated

They are usually discussed as one thing. They are not, they have different fixes, and one of
them is nearly free.

### 1. "It runs on Charley's laptop" — closeable now, no grant required

Only Procore is affected. `cd_01_extract_procore` is a Fabric notebook that reads its
credentials from `AffectKeyVault`, and as of 2026-08-24 those credentials are **live and
verified** against `https://api.procore.com`. The only thing standing between us and a
laptop-free Procore feed is deploying the corrected `fabric_common.py` and adding the notebook
back to `CD_Master_Pipeline` — both ours to do.

### 2. "It runs as Charley's account" — needs grants, and there is a clean version

A scheduled Fabric notebook or pipeline runs as the **item owner**. Today that is
`cforey-c@affect-group.com`, so the vault read happens as a named consultant. That works and
it is not sustainable: the platform stops the day the account is disabled.

The fix is a non-human identity owning the items. Two forms, and the second is better:

- **A service principal** — an app registration we can create ourselves. Needs a client secret,
  which needs rotating, which is one more thing to forget.
- **A Fabric workspace identity** — Fabric issues and rotates the credential itself. Nothing to
  store, nothing to rotate, nothing to leak. **Prefer this.** It needs a workspace admin to
  enable, and a Key Vault role assignment so it can read secrets.

## What the Nerds That Care handoff document adds (read 2026-08-25)

The May 20 2026 handoff (Eric Roitman, Nerds That Care) is the first full description of the
Sage side we have had. Three things in it matter, and they are not the credentials.

### 1. The documented connection points at the WRONG DATABASE

| | Handoff document | What `CD_Sage_Ingest` queries |
|---|---|---|
| Connection | `Sage100-SQL-Connection` | datasource `835e72c8-…` |
| Database | **`ABMI`** | **`Affect Group`** |

`ABMI` was a guess, and the document says so — §12 records that it "was selected based on
Rebecca's references to *Affect Build*" and lists `Affect Group` among the alternatives. The
evidence is settled and it is not ABMI: querying `Affect Group` yields Sage job numbers that
resolve to **15 of the 16 real Procore projects, carrying $22.5M of AR**. A wrong database does
not join 15 of 16 projects.

**So being granted "Can use" on `Sage100-SQL-Connection` would not be enough** — it is bound to
ABMI, and a Fabric SQL connection is per (server, database). The grant has to name the
datasource for the **`Affect Group`** database, which is `835e72c8-7995-4171-91cb-2a32fbd2050a`
on gateway `1e798beb-…` — the one `Build_Sage_Test` already uses and the one our dataflow is
already bound to. Asking for the wrong one would burn another round trip and look like the
grant had failed.

### 2. The Sage database blocks anything not on a whitelist

§9: Sage 100 runs a **SQL Server logon trigger** that refuses any application not named in an
XML file, and the whitelist is three entries, each locked to login `FabricReader` from
`%LOCALHOST%`:

- `.Net SqlClient Data Provider`
- `Framework Microsoft SqlClient Data Provider`
- `Mashup Engine (TridentDataflowNative)`

Two consequences:

- **Dataflow Gen2 is the sanctioned path**, and `CD_Sage_Ingest` is a Dataflow Gen2. The
  architecture already committed to is the right one — that is now confirmed rather than
  assumed.
- **The "push from on-premises" fallback is dead** unless somebody edits that XML and restarts
  the SQL Server service. A Python job on the Sage box would be blocked by the logon trigger
  and would appear in the Event Viewer as Event ID 17063, not as a connection error. Option C
  below is struck out accordingly.

### 3. Nobody human appears to administer that gateway

The gateway is registered to **`fabricconnector@affect-group.com`** (§4), a service account with
no license and no admin role (§7, §10). In Fabric, the registering account is the gateway
admin. §14 hands "Gateway administration within Fabric" to Affect Group going forward — but
nothing in the document grants gateway-admin rights to Rebecca, to Cal, or to any named person.

If that is right, then the only identity that can grant "Can use" on this gateway is a service
account whose password lives in 1Password. That is a single point of failure worth fixing on
its own merits, independent of this engagement: **add Rebecca as a gateway admin.** She is
already the F2 capacity administrator, so it is a role she is expected to hold.

It also means "ask Rebecca to grant it" may simply fail for her, through no fault of hers, and
that is worth knowing before she is asked.

## Sage: the four honest options


| | Option | What it costs | Verdict |
|---|---|---|---|
| **A** | Grant **"Can use"** on connection `nc-affect-1\sage100con;Affect Group` to the **workspace identity** (not to a person) | One ACL entry, by whoever admins the gateway | **Do this.** Smallest, durable, survives us |
| **B** | Sign in as `fabricconnector@affect-group.com` — whose credentials are now in the vault — and make the grant ourselves | Nothing technical | **Ask before doing.** See below |
| ~~**C**~~ | ~~Skip the gateway: a scheduled job on-prem pushes to OneLake~~ | Also needs the Sage logon-trigger XML edited and the SQL service restarted | **Struck 2026-08-25.** The whitelist in §9 of the handoff blocks any client but the three named ones |
| **D** | VNet data gateway | ExpressRoute or site-to-site VPN into their network | No. Months of work to avoid one ACL entry |

### On option B

`fabricconnector@affect-group.com` is a real Entra account, display name *"Fabric Gateway
Service Account"*, and it is almost certainly the identity that owns the gateway connection.
Its password is in a vault we administer, put there by Affect's own technical lead.

That is *implied* authorisation, not stated authorisation, and the two are not the same thing.
Signing in as another identity to grant ourselves access we have been formally asking for is
the kind of shortcut that is completely defensible right up until the moment someone asks why
a consultant authenticated as a service account at 2am. **Get one sentence from Rebecca or
Cathal saying to use it, in writing, and then it is fine.** Do not skip that step to save a day.

It is also worth noting the pattern is worth retiring rather than extending: a human-shaped
account with a shared password administering production infrastructure is the thing option A
replaces.

## The ask — one email, four lines

Every open item on this engagement is now in this list. There is nothing else.

1. **Enable a workspace identity on the `Build` workspace** *(Fabric tenant admin + workspace admin)*
2. **Assign it `Key Vault Secrets User` on `AffectKeyVault`** *(needs Owner or User Access
   Administrator on RG `Affect_Data` — we hold neither)*
3. **Grant it "Can use" on connection `nc-affect-1\sage100con;Affect Group`** in *Manage
   connections and gateways* *(gateway admin — possibly Nerds That Care, since the Sage
   database is administered outside)*
4. **Make it the owner of `CD_Master_Pipeline` and `CD_Sage_Ingest`**

Grants 1, 2 and 4 retire the personal-credential dependency. Grant 3 turns Sage on. They are
independent — 3 can land first, or last, without blocking the others.

**Ask for the identity, not for Charley.** Every previous ask on this engagement has been
"give Charley X", which produces a grant that dies with the engagement and has to be re-asked
for the next person. This bundle is asked once and never again.
