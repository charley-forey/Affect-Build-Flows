# Security findings

Findings from building charley-dev against the existing `Build` workspace. **Everything here
is reported, not changed.** charley-dev writes only inside its own folder, so none of the
remediation below has been applied — these are for Affect to action, and the first one should
not wait.

Verified 2026-08-02 against the live workspace `1f7caed6-f88a-4e52-bc83-9a498a165301`.
Re-checked 2026-08-19: **F1 is still open**, and is now actionable for the first time.

---

## F1 — Procore API credentials are hardcoded in a live notebook (high) — OPEN

> **Status 2026-08-19 — still open, and the fix is now unblocked.**
>
> The **repo** copies are clean. All five `foundation/` notebooks previously flagged for
> hardcoded Procore secrets were re-read on 2026-08-19: they use `get_secret()` throughout,
> carry no literal credentials, and hold no saved token output in their cell results.
>
> The **workspace** copy is not. Rebecca's `procore_auth` notebook running in Fabric still
> assigns the client id and secret as string literals. That is the copy that matters — a
> scrubbed file in git next to an unscrubbed notebook in the service is the most dangerous
> shape this finding can take, because the exposure reads as fixed and is not.
>
> What changed is that the remediation is now possible. An Azure subscription and the Key
> Vault `OneLake` both exist as of 2026-08-19, so there is somewhere for the new pair to
> go. One thing is still missing: `cforey-c@affect-group.com` has only **Contributor on the
> resource group**, and the vault is RBAC-mode, so no secret can be written or read yet.
> **The ask is one role assignment — "Key Vault Secrets Officer" on vault `OneLake`.**
>
> **Order matters: rotate first, then edit the notebook.** Editing the literal out does not
> un-expose a credential that has already been readable; only revoking it does. See the
> numbered remediation below, which is unchanged.

**What.** The notebook `procore_auth` (workspace `Build`, folder
`594bfe88-1c54-4530-8b3d-67677407b43d`) assigns the Procore OAuth client id and client secret
as string literals:

| Line | Variable | Length |
|---|---|---|
| 21 | `CLIENT_ID` | 43 chars |
| 23 | `CLIENT_SECRET` | 43 chars |

The values are deliberately not reproduced here, and were never printed while verifying this.
Re-check at any time with `Notebook -> ... -> View definition`, or programmatically via
`POST /v1/workspaces/{ws}/items/{id}/getDefinition`.

**Why it matters.** These are live production credentials for Affect's Procore tenant, sitting
in plaintext where several things can reach them:

- Anyone with **Viewer** on the workspace can open the notebook and read them. Fabric item
  permissions are not code-review permissions.
- They are captured in the workspace's item definition history, so deleting the cell does not
  retract them.
- If the workspace is ever git-synced, they land in the repository — and then in every clone.
- A notebook run logs its own source in some failure paths.

The repo copy of this notebook **was** scrubbed at some point
(`foundation/01-ingestion/Procore_APICalls/procore_auth.ipynb`). The live copy was not. That
mismatch is the most dangerous shape this can take: the exposure looks fixed when read from
git, and is not fixed in the service.

**Remediation.**

1. **Rotate first, edit second.** Issue a new client id/secret pair in Procore's Developer
   Portal and revoke the old one. Editing the notebook does not un-expose a credential that
   has already been readable — assume it is compromised and treat rotation as the fix.
2. Store the new pair in Azure Key Vault — the vault now exists (`OneLake`, RG
   `Affect_KeyVault`, `https://onelake.vault.azure.net/`). This step is gated on the one
   role assignment above; `_local/setup_keyvault.py` in this folder writes charley-dev's own
   copy and can be pointed at the same vault.
3. Replace the literals with a lookup. charley-dev's
   `00-platform/lib/fabric_common.get_secret()` already has the right contract — Key Vault
   inside Fabric, environment variable locally — and can be imported rather than rewritten:

   ```python
   CLIENT_ID     = get_secret("PROCORE_CLIENT_ID")
   CLIENT_SECRET = get_secret("PROCORE_CLIENT_SECRET")
   ```
4. Confirm no other notebook holds the old values before revoking, so nothing breaks
   unexpectedly. The sweep in step 1 of "How to re-run this check" below does that.

**Not a finding:** `COMPANY_ID = 562949953444705` in the same notebook is Affect's Procore
**organisation identifier**, not a credential. It appears in request headers by design. Do not
spend a rotation on it.

---

## F2 — No secret management for the existing pipelines (medium)

F1 is the instance; this is the pattern. There was no Key Vault, no workspace-level secret
store, and no convention for the existing ingestion notebooks — so the only place a
credential *could* go was a notebook cell. The next integration reproduces F1 unless the
pattern changes with it.

**Half of this is now fixed.** As of 2026-08-19 the vault exists. What has not changed is
the *convention*: nothing yet reads from it, because nobody has the role that lets them
write to it. The finding stays open until `get_secret()` is the accessor the existing
notebooks actually use.

Two vault settings worth deciding while it is empty: it is **RBAC-mode** (so access is role
assignments, not access policies — this is the better default, and it is why Contributor is
not enough) and **purge protection is disabled**. Turning purge protection on is a one-way
door, which is a reason to think about it now rather than after it holds live credentials.

**Remediation.** Stand up one vault for the workspace and adopt `get_secret()` as the single
accessor. charley-dev does this for its own notebooks
(`_local/setup_keyvault.py`, `_docs/keyvault.md`); the same vault and the same helper work for
the existing pipelines with no redesign. Doing it once, in one place, is what stops F1
recurring.

---

## F3 — The Sage dataflow's gateway credential is outside anyone's view (informational)

`foundation/01-ingestion/Sage/Build_Sage_Test.Dataflow` connects to
`NC-AFFECT-1\SAGE100CON` through an on-premises data gateway. The credential lives in the
gateway's connection configuration, not in source — which is the correct design, and is
called out here only so it is not mistaken for a gap during a future audit.

**Worth confirming** while the topic is open: which account the gateway connection runs as,
and whether it has more than read access to the Sage database. An ingestion connection should
be read-only.

---

## How to re-run this check

`_local/agents/tools.py` refuses to read secret-shaped paths, so the agent system cannot
surface these values into a transcript. To re-verify by hand:

1. Sweep every notebook definition in the workspace for `NAME = "literal"` assignments where
   `NAME` looks credential-ish and the value is not a `getenv` / `get_secret` call.
2. Report the variable name, line number and value **length** — never the value. A finding
   that leaks the secret while documenting it has made the problem worse.

The script used for this pass is not committed, because a working credential scanner pointed
at a live tenant is itself something to be careful with. The 20 lines above describe it
completely.

---

## Scope note

charley-dev creates only inside folder `25dd1e34-bd57-43ca-aa29-c8fd33013101` and writes only
to `CD_*` lakehouses. Reads of the existing `Bronze_`/`Silver_` lakehouses go through the SQL
endpoint, which is read-only by construction. `foundation/fabric_backup.py` re-run to a
scratch directory should diff clean outside `charley-dev/` — that check is an acceptance gate
on every phase, so "we changed nothing of yours" stays a test rather than a claim.
