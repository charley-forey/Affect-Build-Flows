# Key Vault — state and runbook

**Verified against Azure and the live Outbuild API on 2026-08-19** as `cforey-c@affect-group.com`.

Blocker #3 from the Aug 13 executive update is **resolved**. It was never one blocker: it was
a vault we could not read plus a vault nobody had told us about. Secrets now load and are read
back end to end — proven, not assumed, by a live Outbuild pull of 3,078 rows.

## The correction that mattered

Every document in this repo pointed at the wrong vault.

| | Documented until 2026-08-19 | Actually used |
|---|---|---|
| Vault | `OneLake` | **`AffectKeyVault`** |
| Subscription | `0bee26ab-eeb7-4dc9-ab92-fb46d068f6b6` | **`73932b34-3bb6-4a94-bd4b-4b7623d4f7d6`** |
| Resource group | `Affect_KeyVault` | **`Affect_Data`** |
| Our access | none — 403, `Assignment: (not found)` | **Key Vault Administrator** |

The old runbook asked Rebecca for a Key Vault Secrets Officer grant on `OneLake`. That ask is
withdrawn — it would have solved a problem we do not have. Rebecca had already added the
Outbuild token to `AffectKeyVault`, in a different subscription, and the access we needed came
with it. **Nothing further is required from anyone to read or write secrets.**

`OneLake` still exists and is still unreadable by this account. It holds nothing we depend on.
Leave it alone, or have someone with Owner delete it — a vault named after Fabric's storage
layer, in RBAC mode with no data-plane assignments and purge protection off, is a trap for the
next person, not an asset.

## What exists now

| | |
|---|---|
| Vault name | **`AffectKeyVault`** |
| Vault URI | `https://affectkeyvault.vault.azure.net/` |
| Resource group | `Affect_Data` — East US |
| Subscription | `73932b34-3bb6-4a94-bd4b-4b7623d4f7d6` |
| Tenant | Affect Build LLC — `b2a2225b-4b4e-42ec-ba52-c7e1c2dea580` |
| Authorisation model | RBAC |
| Our role | **Key Vault Administrator**, inherited at resource-group scope |

Secrets held:

| Secret | Added | State |
|---|---|---|
| `OutbuildToken` | Rebecca, 2026-08-19 | **Live** — reads back, and authenticates against the Datahub API |
| `ProcoreClientID` | Rebecca, 2026-08-22 | **Live** — verified 2026-08-24 against `https://api.procore.com`, 19 active projects |
| `ProcoreClientSecret` | Rebecca, 2026-08-22 | **Live** — same probe |
| `ProcoreCompanyID` | Rebecca, 2026-08-22 | **Live** — same probe |
| `Fabric-SQL-Login-Username` | Rebecca, 2026-08-22 | Held, unused — the `FabricReader` SQL login |
| `Fabric-SQL-Login-Password` | Rebecca, 2026-08-22 | Held, unused |
| `Fabric-Gateway-Service-Account-Username` | Rebecca, 2026-08-22 | Held, unused — `fabricconnector@` |
| `Fabric-Gateway-Service-Account-Password` | Rebecca, 2026-08-22 | Held, unused |
| `Sage-Data-Gateway-Recovery-Key` | Rebecca, 2026-08-22 | Held, unused |

### The five Sage/gateway secrets do not unblock Sage

They close a **different** gap — the one at the bottom of this document: the 1Password share
links holding the gateway recovery key, the `FabricReader` SQL login and the `fabricconnector@`
credentials expired 2026-05-28, and those three things now live somewhere durable. That is
worth having.

They are not what `CD_Sage_Ingest` is waiting for. Sage 100 is **on-premises**
(`NC-AFFECT-1\SAGE100CON`); a Fabric notebook has no network route to it, and a dataflow
reaches it through the on-premises data gateway, which authenticates with the credential
**stored in the gateway connection** — not with anything in Key Vault. Re-checked
2026-08-24: `GET /gateways` and `GET /connections` both still return **0** for
`cforey-c@affect-group.com`. The ask is unchanged and is still one line: **"Can use" on
connection `nc-affect-1\sage100con;Affect Group`** in *Manage connections and gateways*.

The full identity picture — what this account can and cannot do (verified, not assumed), why
a workspace identity beats a service principal here, the four honest Sage options, and the
one-email ask that closes all of it — is in [`access-model.md`](access-model.md).

### One thing worth knowing about `az`

`az keyvault show` cannot see this vault: it is a management-plane call scoped to the
subscriptions in the local `az` profile, and this machine has only ever logged into
`0bee26ab`. Data-plane calls resolve the vault by DNS and authorise from the inherited role,
so they work fine. **Do not pass `--subscription` to a data-plane command** — `az` rejects the
unknown subscription before it makes the call.

`setup_keyvault.py` now probes the data plane before concluding a vault is absent. Without
that check, `--apply` would have tried to create a *second* `AffectKeyVault` in the wrong
subscription.

## Secret naming — the defect that would have hidden here

Key Vault secret names cannot contain underscores, so **the environment-variable name is never
the secret name**. `setup_keyvault.py` assumed a mechanical kebab-case translation and would
have written `procore-client-id`; the read side originally passed `PROCORE_CLIENT_ID` straight
through, which is not a legal secret name at all.

Both were wrong about the same thing, and reality settled it on 2026-08-22: Rebecca created
every secret **by hand in the portal, in PascalCase** — `ProcoreClientID`, not
`procore-client-id`. So all four are now mapped explicitly rather than derived, and the
mechanical fallback survives only for a secret nobody has created yet. Mapped, not renamed:
something we cannot see may already read them under these names.

One function owns the translation, `fabric_common.kv_secret_name`, and `setup_keyvault.py`
imports it rather than restating it so the two cannot drift. `--verify` now asserts every
read-side lookup resolves to a name the vault actually holds, which is the check that would
have caught this on 2026-08-22 instead of at the next unattended 02:00 run:

| Environment variable | Key Vault secret |
|---|---|
| `PROCORE_CLIENT_ID` | `ProcoreClientID` |
| `PROCORE_CLIENT_SECRET` | `ProcoreClientSecret` |
| `PROCORE_COMPANY_ID` | `ProcoreCompanyID` |
| `OUTBUILD_API_TOKEN` | `OutbuildToken` |

All four are **mapped**, in `fabric_common.SECRET_NAMES`. Renaming a secret to satisfy a
convention is not worth breaking a caller we cannot see.

## The read path

`get_secret(name)` — Key Vault inside Fabric, environment variable locally.

Two changes on 2026-08-19, both of which had to be right before any secret was worth loading:

- **It translates the name.** See above.
- **It fails closed inside Fabric.** The old version fell through to `os.environ` whenever the
  vault lookup did not fire, so a misconfigured vault read the credential from somewhere else
  and reported success. It now raises. A wrong answer that looks healthy until the unattended
  02:00 run is worse than a loud failure at 14:00.

The vault URL is a **default in code**, not an environment variable to remember. It was
previously read from `PROCORE_KEYVAULT_URL` in five places and set in none, so the Key Vault
branch had never executed — not once, in any environment. `AFFECT_KEYVAULT_URL` still overrides
it if a future environment needs a different vault.

## Runbook — rotating the Procore credentials

Order matters. **Rotate in Procore first, then clear the notebook.** Editing the notebook first
leaves the live credential in Fabric's item-definition history with nothing revoked, which
reads as fixed and is not.

1. **Regenerate in Procore.** Developer Portal → the Data Connector app → regenerate the client
   secret. This invalidates the old one immediately, so expect Rebecca's `procore_auth`
   notebook to start failing from this moment — that is the point, and it is worth telling her
   before rather than after.

2. **Put the new values in `.env`** at `C:\Users\charl\Documents\Affect\.env`:
   ```
   PROCORE_CLIENT_ID=...
   PROCORE_CLIENT_SECRET=...
   PROCORE_COMPANY_ID=562949953444705
   ```
   `.env` is gitignored. `PROCORE_COMPANY_ID` is an org identifier, not a credential — it
   travels in request headers by design — but it lives with the others so one call site
   produces all three.

3. **Push to the vault and confirm:**
   ```bash
   python foundation/charley-dev/_local/setup_keyvault.py --apply
   python foundation/charley-dev/_local/setup_keyvault.py --verify
   ```
   `--verify` lists names only, never values. Expect four secrets afterwards.

4. **Prove the credential works before wiring anything to it:**
   ```bash
   python foundation/charley-dev/_local/extract_procore_local.py --probe
   ```
   Check the host in the output is `https://api.procore.com`. The extractor's default is the
   **sandbox**, and a sandbox run lands convincingly empty tables rather than failing.

5. **Run the Fabric notebook**, which is where the vault path is actually exercised:
   ```
   cd_01_extract_procore
   ```
   Its last four runs all failed on `Secret 'PROCORE_CLIENT_ID' not found` (2026-08-02). A
   green run here is the real proof — steps 3 and 4 do not touch `notebookutils`.

6. **Only then, clear the literals from Rebecca's `procore_auth` notebook** — finding F1 in
   `security-findings.md`. Workspace `1f7caed6-…`, folder `594bfe88-…`, lines 21 and 23. The
   old secret is dead by now, so this is tidying rather than remediation, but leaving a
   credential-shaped string in a live notebook trains everyone who reads it that this is normal.

7. **Add `cd_01_extract_procore` back to `CD_Master_Pipeline`.** It was deliberately held out
   of the DAG so its guaranteed failure would not redden the nightly run. Once step 5 is green
   it belongs ahead of `Bronze To Silver`, and `deploy_pipeline.py` is where that is declared —
   not the portal.

## Outbuild — done, and what it took

The token loads from the vault and pulls live data: 3,078 rows across 15 endpoints.

The client had never been run against the real API, and had three bugs that only a live call
could reveal. Recorded here because each one failed in a way that pointed somewhere else:

- **No `User-Agent`.** Cloudflare answered `403 Error 1010: access denied based on your
  browser's signature` before the request reached Outbuild. This is indistinguishable from a
  rejected token, and the token was the thing we had just been given. urllib's default UA is
  the trigger; the client now sends a descriptive one.
- **Wrong envelope key.** The real shape is `{"<entity>": [...], "page": N, "hasNextPage": …}`
  — keyed by entity name, not `data`. The old code looked for `data`/`items`/`results`, missed,
  and returned `[envelope]`: one row per page holding the entire payload, with nothing raising.
- **Wrong paging rule.** It stopped on a page shorter than 500, but `/projects` returns 15 per
  page — so it would have stopped after page one on most endpoints. It now uses the API's own
  `hasNextPage`.

`schedule_impact_requests` is declared but skipped: the real path is
`/scheduleimpactrequests/schedule/{scheduleId}`, which needs per-schedule expansion, and
nothing downstream reads it yet.

**Still not wired:** `sv_outbuild_activities` reads Rebecca's `Silver_Lakehouse/Outbuild_activities`
dataflow, not our `cd_bronze_outbuild_*`. `fct_Milestone`'s 52 rows come from her path.
Repointing it is a real change with real regression risk — milestones could go to zero — and is
its own piece of work, not a footnote to this one.

## Gaps this does not close

- **No rotation schedule, no expiry tracking, no owner list.** The Procore ordering rule above
  is the only rotation process that exists anywhere.
- **`OutbuildToken` is a `superadmin` token valid until 2036-06-09.** A ten-year credential with
  the widest available role is worth questioning with Outbuild — a read-only, shorter-lived
  token would do everything the Datahub API is used for here.
- ~~**The 1Password share links in the Sage handoff document expired 2026-05-28.**~~
  **CLOSED 2026-08-22** — Rebecca put all three in `AffectKeyVault`: the gateway recovery key,
  the `FabricReader` SQL login and the `fabricconnector@` service account credentials. Nothing
  reads them, which is correct; they exist so the day the gateway is down is not also the day
  nobody can find the recovery key.
