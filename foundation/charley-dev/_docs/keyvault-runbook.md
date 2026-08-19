# Key Vault — state, blocker and runbook

**Verified against Azure on 2026-08-19** by `az` as `cforey-c@affect-group.com`.

Blocker #3 from the Aug 13 executive update is **partly resolved**: the Azure subscription and
the vault both now exist. One permission grant remains before a single secret can be written.

## What exists

| | |
|---|---|
| Subscription | `Azure subscription 1` — `0bee26ab-eeb7-4dc9-ab92-fb46d068f6b6` |
| Tenant | Affect Build LLC — `b2a2225b-4b4e-42ec-ba52-c7e1c2dea580` (`affect-group.com`) |
| Vault name | **`OneLake`** |
| Resource group | `Affect_KeyVault` |
| Region | East US |
| Vault URI | `https://onelake.vault.azure.net/` |
| Authorisation model | **RBAC** (`enableRbacAuthorization: true`) |
| Soft delete | Enabled, 90-day retention |
| Purge protection | **Disabled** |
| Access policies | 0 (correct — RBAC mode ignores them) |

## The blocker

`cforey-c@affect-group.com` holds **Contributor on the resource group** and nothing else:

```
Role         Scope
-----------  ----------------------------------------------------------------
Contributor  /subscriptions/0bee26ab-…/resourcegroups/Affect_KeyVault
```

In an RBAC-mode vault, Contributor is a **management-plane** role. It can see that the vault
exists, change its settings, even delete it — but it cannot read or write a single secret, and
it cannot grant itself the role that would. Listing secrets returns:

```
(Forbidden) Caller is not authorized to perform action on resource.
Action: 'Microsoft.KeyVault/vaults/secrets/readMetadata/action'
Assignment: (not found)
```

`Assignment: (not found)` is the whole story — there is no data-plane role assignment.

### The ask — one role assignment, ~2 minutes

Someone with **Owner** or **User Access Administrator** on the vault or resource group grants:

> **Key Vault Secrets Officer** → `cforey-c@affect-group.com` → scope: vault `OneLake`

Portal: *Key Vault `OneLake` → Access control (IAM) → Add role assignment → Key Vault Secrets
Officer → cforey-c@affect-group.com*. Or:

```bash
az role assignment create \
  --role "Key Vault Secrets Officer" \
  --assignee cforey-c@affect-group.com \
  --scope "/subscriptions/0bee26ab-eeb7-4dc9-ab92-fb46d068f6b6/resourceGroups/Affect_KeyVault/providers/Microsoft.KeyVault/vaults/OneLake"
```

*Secrets Officer* (read + write) is what's needed to load the secrets. If Affect would rather
load them itself, **Key Vault Secrets User** (read only) is sufficient for everything after
that, and is the better long-term grant.

### A deliberate non-action

Contributor *can* switch the vault from RBAC to legacy access-policy mode and then add itself
a policy. That is a documented privilege-escalation path and it would have worked. It was not
done: it silently downgrades the client's security posture on a vault they just created, and
that is their decision, not ours. The role assignment above is the correct fix.

## Two things worth changing while the vault is still empty

1. **The vault is named `OneLake`.** OneLake is also the name of Fabric's storage layer, which
   this platform uses constantly. Every future reader will have to disambiguate
   "onelake.vault.azure.net" from OneLake-the-Fabric-thing. Renaming is free today and
   impossible later (vault names are immutable — it means create-new, migrate, delete-old).
   Suggested: `kv-affect-platform`.
2. **Purge protection is disabled.** With it off, a deleted vault or secret can be purged
   before the soft-delete window expires, which defeats the recovery guarantee. Standard
   practice for a vault holding production credentials is on. It is **irreversible once
   enabled** — which is exactly why it should be a deliberate decision now rather than a
   default nobody revisited.

## Runbook — once the role lands

Everything below is already written and tested; none of it is new work.

### 1. Load the secrets

```bash
cd foundation/charley-dev
python _local/setup_keyvault.py --vault OneLake --resource-group Affect_KeyVault           # dry run
python _local/setup_keyvault.py --vault OneLake --resource-group Affect_KeyVault --apply
python _local/setup_keyvault.py --vault OneLake --resource-group Affect_KeyVault --verify  # names only
```

Reads `.env`, pushes `PROCORE_CLIENT_ID`, `PROCORE_CLIENT_SECRET`, `PROCORE_COMPANY_ID`.
Values never touch argv or a log — they go to `az` via a temp file deleted in a `finally`.
`FABRIC_PASSWORD` is deliberately excluded: a named user's password is not a service
credential and does not belong in a shared vault. If Fabric needs non-interactive auth, that
wants a service principal.

Add `OUTBUILD_API_TOKEN` the same way once Rebecca sends it.

### 2. Wire Fabric to the vault — the two steps that get missed

**a. Set the environment variable.** *Fabric workspace → Settings → Spark → Environment →
Variables*:

```
PROCORE_KEYVAULT_URL = https://onelake.vault.azure.net/
```

**b. Grant the workspace identity read access:**

```bash
az role assignment create --role "Key Vault Secrets User" \
  --assignee <fabric-workspace-managed-identity-object-id> \
  --scope "/subscriptions/0bee26ab-…/resourceGroups/Affect_KeyVault/providers/Microsoft.KeyVault/vaults/OneLake"
```

> **Why this is the dangerous step.** `lib/fabric_common.get_secret()` tries Key Vault *only*
> if `PROCORE_KEYVAULT_URL` is set, and otherwise **falls through to an environment
> variable**. Locally the env var is present, so a half-configured vault looks like it works
> — and fails only in the unattended 02:00 pipeline run, where nobody is watching. Verify by
> running `cd_01_extract_procore` in Fabric *after* the wiring, not before.

### 3. Then, and only then, move extraction into Fabric

`cd_01_extract_procore` is currently out of the nightly DAG — it failed 4/4 runs without a
vault, so extraction runs locally and lands files that `cd_05_land_to_bronze` merges. Once
step 2 verifies, add it back as the head of `STAGES` in `_local/deploy_pipeline.py` and
redeploy. That closes the last "runs on Charley's laptop" gap.

## Related: security finding F1 is now actionable, and the order matters

`_docs/security-findings.md` F1 (high): the Procore client id and secret are **string literals
in the live `procore_auth` notebook in the workspace**. The repo copy was scrubbed; the
workspace copy was not — so it reads as fixed from git and is not fixed in the service. It is
readable by anyone with Viewer and is captured in item-definition history.

**Rotate the Procore secret first, then edit the notebook.** Editing first leaves the live
credential in version history with nothing revoked. Rotating first makes the exposed value
worthless the moment it is replaced. The vault's arrival is what makes the second half
possible — but the rotation does not depend on it and can happen today.

This is Rebecca's notebook and her running pipeline; rotating on her behalf would break it
without warning. It needs to be coordinated, not done unilaterally.
