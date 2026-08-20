"""Put charley-dev's secrets in Azure Key Vault so no notebook has to hold one.

    python setup_keyvault.py                        # dry run - shows what WOULD happen
    python setup_keyvault.py --apply                # create/reuse the vault, push secrets
    python setup_keyvault.py --verify               # list secret NAMES that exist
    python setup_keyvault.py --apply --vault my-kv --resource-group my-rg

This is the other half of `lib/fabric_common.get_secret()`, which already looks up
`notebookutils.credentials.getSecret(vault, name)` inside Fabric and falls back to an
environment variable locally. That helper had nothing to read until now.

Fixes F2 in _docs/security-findings.md for OUR notebooks. It does not touch Rebecca's - F1
(hardcoded credentials in the live `procore_auth`) is hers to rotate, and rotating on her
behalf would break her running pipeline without warning.

WHAT IS AND IS NOT PUSHED
-------------------------
Only `PROCORE_*` goes in. `FABRIC_PASSWORD` is a named user's account password: it is not a
service credential, it should not be reachable by a pipeline, and putting it in a shared
vault would quietly widen who can use it. If Fabric needs non-interactive auth, that wants a
service principal, not a person's password.

Secret VALUES are never printed, never logged, and never passed as a command-line argument -
they go to `az` through a temp file that is deleted in a finally block, because argv is
visible in the process list.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deploy as dp  # noqa: E402  - reuse az_path(), the same auth everything else uses

HERE = Path(__file__).resolve().parent
CHARLEY_DEV = HERE.parent
REPO = CHARLEY_DEV.parent.parent


def find_env() -> Path | None:
    """Walk up looking for .env.

    Run from a git worktree, `REPO` is `.claude/worktrees/<name>/` and the .env sits in the
    main checkout several levels above. Walking up finds it either way, so the script works
    the same in a worktree and in the main tree.
    """
    for directory in [REPO, *REPO.parents]:
        candidate = directory / ".env"
        if candidate.is_file():
            return candidate
    return None

# The vault the platform actually uses. Not the one _docs/keyvault-runbook.md named until
# 2026-08-19: that was `OneLake` in subscription 0bee26ab, which this account cannot read
# (403, no role assignment). AffectKeyVault lives in resource group Affect_Data of
# subscription 73932b34 and already holds OutbuildToken, and cforey-c@affect-group.com has
# Key Vault Administrator on the resource group - so nothing here needs a new grant.
DEFAULT_VAULT = "AffectKeyVault"
DEFAULT_RESOURCE_GROUP = "Affect_Data"
LOCATION = "eastus"

# Allow-list, not "everything in .env". A vault is a shared surface; what goes in it is a
# decision, not a copy.
PUSH = ["PROCORE_CLIENT_ID", "PROCORE_CLIENT_SECRET", "PROCORE_COMPANY_ID"]
NEVER_PUSH = ["FABRIC_PASSWORD", "FABRIC_EMAIL"]

# Key Vault secret names cannot contain underscores. This MUST agree with the read side -
# fabric_common.kv_secret_name - or a secret gets written under a name nothing looks up.
# Imported rather than restated so the two cannot drift; the fallback keeps this script
# runnable from a checkout where 00-platform/lib is not on sys.path.
try:
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "00-platform" / "lib"))
    from fabric_common import kv_secret_name as kv_name  # noqa: F401
except ImportError:  # pragma: no cover
    def kv_name(env_name: str) -> str:
        return env_name.replace("_", "-").lower()


def az(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run([dp.az_path(), *args], capture_output=True, text=True, timeout=300)
    if check and result.returncode != 0:
        raise RuntimeError(f"az {' '.join(args[:3])} failed:\n{result.stderr.strip()[:500]}")
    return result


def read_env(env_file: Path) -> dict[str, str]:
    """Parse .env for the allow-listed keys. Values are held in memory only."""
    found = {}
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key in PUSH and value:
            found[key] = value
    return found


def ensure_vault(vault: str, resource_group: str, apply: bool) -> str:
    probe = az("keyvault", "show", "--name", vault, "-o", "json", check=False)
    if probe.returncode == 0:
        uri = json.loads(probe.stdout)["properties"]["vaultUri"]
        print(f"  vault {vault} exists -> {uri}")
        return uri

    # ARM could not see it, which is NOT the same as it being absent. `az keyvault show`
    # is a management-plane call scoped to the subscriptions in the local az profile, and
    # AffectKeyVault lives in one this profile has never been logged into. The data plane
    # resolves the vault by DNS and authorises from the inherited role, so it answers
    # correctly where ARM cannot. Without this check, --apply would try to CREATE a second
    # vault with the same name in the wrong subscription.
    data_probe = az("keyvault", "secret", "list", "--vault-name", vault,
                    "--query", "[].name", "-o", "tsv", check=False)
    if data_probe.returncode == 0:
        uri = f"https://{vault.lower()}.vault.azure.net/"
        print(f"  vault {vault} exists (visible on the data plane only) -> {uri}")
        return uri

    print(f"  vault {vault} does not exist")
    if not apply:
        return f"https://{vault.lower()}.vault.azure.net/"

    if not resource_group:
        raise SystemExit(
            "--resource-group is required to create a vault.\n"
            "  List them with: az group list --query '[].name' -o tsv"
        )
    print(f"  creating {vault} in {resource_group} ({LOCATION}) ...")
    az("keyvault", "create", "--name", vault, "--resource-group", resource_group,
       "--location", LOCATION, "--enable-rbac-authorization", "true", "-o", "none")
    uri = json.loads(az("keyvault", "show", "--name", vault, "-o", "json").stdout)
    return uri["properties"]["vaultUri"]


def push_secret(vault: str, env_name: str, value: str) -> None:
    """Set one secret via a temp file - argv is visible in the process list."""
    handle, path = tempfile.mkstemp(text=True)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as fh:
            fh.write(value)
        az("keyvault", "secret", "set", "--vault-name", vault,
           "--name", kv_name(env_name), "--file", path, "-o", "none")
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--vault", default=DEFAULT_VAULT)
    parser.add_argument("--resource-group", default="")
    parser.add_argument("--env-file", default="", help="override .env discovery")
    args = parser.parse_args()

    if args.verify:
        result = az("keyvault", "secret", "list", "--vault-name", args.vault,
                    "--query", "[].name", "-o", "tsv", check=False)
        if result.returncode != 0:
            print(f"cannot list {args.vault}: {result.stderr.strip()[:300]}")
            return 1
        names = [n for n in result.stdout.split() if n]
        print(f"{len(names)} secret(s) in {args.vault}:")
        for n in names:
            print(f"  {n}")
        return 0

    env_file = Path(args.env_file) if args.env_file else find_env()
    if not env_file or not env_file.is_file():
        raise SystemExit(
            f"no .env found walking up from {REPO}. Pass --env-file to point at one."
        )
    secrets = read_env(env_file)
    missing = [k for k in PUSH if k not in secrets]

    print(f"source: {env_file}")
    for key in PUSH:
        state = "present" if key in secrets else "MISSING"
        print(f"  {key:<24} -> {kv_name(key):<24} {state}")
    for key in NEVER_PUSH:
        print(f"  {key:<24} -> (deliberately not pushed - see the module docstring)")

    if missing:
        print(f"\n{len(missing)} secret(s) missing from .env: {', '.join(missing)}")
        return 1

    uri = ensure_vault(args.vault, args.resource_group, args.apply)

    if not args.apply:
        print("\nDRY RUN - nothing written. Re-run with --apply.")
        return 0

    print()
    for key, value in secrets.items():
        push_secret(args.vault, key, value)
        print(f"  set {kv_name(key)} ({len(value)} chars)")

    print(f"""
Done. Two things left, both outside what this script can do for you:

1. Set the workspace environment variable so get_secret() finds the vault:
       PROCORE_KEYVAULT_URL = {uri}
   (Fabric: Workspace settings -> Spark settings -> Environment -> Variables)

2. Grant the Fabric workspace identity read access. The object id has to come from the
   portal, so this is a copy-paste rather than an automation:
       az role assignment create \\
         --role "Key Vault Secrets User" \\
         --assignee <workspace-managed-identity-object-id> \\
         --scope $(az keyvault show --name {args.vault} --query id -o tsv)

Verify with:  python setup_keyvault.py --verify --vault {args.vault}
Then re-run:  python deploy_ingestion.py --apply
""")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
