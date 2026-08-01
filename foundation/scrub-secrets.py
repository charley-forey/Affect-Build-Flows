"""One-shot: strip credentials out of foundation/ notebooks.

Two jobs:
  1. Replace hardcoded credential literals with a Key Vault lookup.
  2. Drop any cell output containing a JWT (saved access tokens).
Run from the repo root. Idempotent.
"""
import json
import pathlib
import re

ROOT = pathlib.Path("foundation")
JWT = re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+")

HELPER = '''def get_secret(name, vault_env="{vault_env}"):
    """Key Vault in Fabric, environment variable locally.

    Mirrors get_secret() in src/procore/procore_extract.py - credentials live in
    exactly one place and never in the notebook source.
    """
    import os
    vault = os.environ.get(vault_env)
    if vault:
        return notebookutils.credentials.getSecret(vault, name)
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Secret {{name!r}} not found. Set {{vault_env}} to your Key Vault URL, "
            f"or export {{name}} locally. See foundation/README.md."
        )
    return value
'''

PROCORE_AUTH = '''import requests
import json

''' + HELPER.format(vault_env="PROCORE_KEYVAULT_URL") + '''
CLIENT_ID = get_secret("PROCORE_CLIENT_ID")
CLIENT_SECRET = get_secret("PROCORE_CLIENT_SECRET")
COMPANY_ID = 562949953444705  # org identifier, not a credential

token_response = requests.post(
    "https://login.procore.com/oauth/token",
    data={
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
)
token = token_response.json()["access_token"]

# Pass both values back to calling notebook
mssparkutils.notebook.exit(json.dumps({
    "token": token,
    "company_id": COMPANY_ID
}))'''

OUTBUILD_TOKEN_LINE = HELPER.format(vault_env="OUTBUILD_KEYVAULT_URL") + '''
TOKEN = get_secret("OUTBUILD_API_TOKEN")'''

changed, outputs_stripped, cells_rewritten = [], 0, 0

for path in sorted(ROOT.rglob("*.ipynb")):
    nb = json.loads(path.read_text(encoding="utf-8"))
    dirty = False

    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))

        # 1. credential literals in source
        new = src
        if 'CLIENT_SECRET = "' in src and "login.procore.com" in src:
            new = PROCORE_AUTH
        elif re.search(r'TOKEN\s*=\s*"eyJ', src):
            new = re.sub(r'TOKEN\s*=\s*"eyJ[^"]+"', OUTBUILD_TOKEN_LINE.strip(), src)
        if new != src:
            cell["source"] = new.splitlines(keepends=True)
            dirty = True
            cells_rewritten += 1

        # 2. saved tokens in outputs
        kept = [o for o in cell.get("outputs", []) if not JWT.search(json.dumps(o))]
        if len(kept) != len(cell.get("outputs", [])):
            outputs_stripped += len(cell["outputs"]) - len(kept)
            cell["outputs"] = kept
            cell["execution_count"] = None
            dirty = True

    if dirty:
        path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        changed.append(str(path))

print(f"rewrote {cells_rewritten} credential cell(s), stripped {outputs_stripped} output(s)")
print(f"{len(changed)} notebook(s) changed:")
for c in changed:
    print("  " + c)
