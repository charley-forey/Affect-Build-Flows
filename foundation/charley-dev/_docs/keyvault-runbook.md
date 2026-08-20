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
| `OutbuildToken` | Rebecca, 2026-08-19 18:27 UTC | **Live** — reads back, and authenticates against the Datahub API |
| `procore-client-id` | — | Pending rotation |
| `procore-client-secret` | — | Pending rotation |
| `procore-company-id` | — | Pending rotation |

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
the secret name**. `setup_keyvault.py` always knew this and wrote `procore-client-id`. The read
side did not: it passed `PROCORE_CLIENT_ID` straight to Key Vault, which is not a legal secret
name. Loading the secrets would not have been enough — the lookup would still have failed, and
the error ("secret not found") would have pointed at the loading step, not at the bug.

One function now owns the translation, `fabric_common.kv_secret_name`, and `setup_keyvault.py`
imports it rather than restating it so the two cannot drift:

| Environment variable | Key Vault secret |
|---|---|
| `PROCORE_CLIENT_ID` | `procore-client-id` |
| `PROCORE_CLIENT_SECRET` | `procore-client-secret` |
| `PROCORE_COMPANY_ID` | `procore-company-id` |
| `OUTBUILD_API_TOKEN` | `OutbuildToken` |

`OutbuildToken` breaks the rule because Rebecca created it by hand in the portal. It is
**mapped**, in `fabric_common.SECRET_NAMES`, not renamed — something else may already read it
under that name, and renaming a secret to satisfy a convention is not worth breaking a caller
we cannot see.

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
- **The 1Password share links in the Sage handoff document expired 2026-05-28.** The gateway
  recovery key, the `FabricReader` SQL login and the `fabricconnector@` service account
  credentials are all behind them. Nothing needs them today; the day something does will be a
  day when the gateway is already down. Ask Nerds That Care to re-share into somewhere durable.
