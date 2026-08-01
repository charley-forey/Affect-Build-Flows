"""Create charley-dev's Fabric items from this repo.

Git is the source of truth; this pushes it to Fabric. A mis-created item is fixed by
re-running, not by clicking.

    python deploy.py                 # dry run - shows what WOULD change (default)
    python deploy.py --apply         # actually create
    python deploy.py --verify        # report what exists, change nothing

Auth is `az account get-access-token` - the same DefaultAzureCredential the Fabric MCP
server would use, and what foundation/fabric_backup.py already relies on. No secret is
read or stored here.

SAFETY - this script is deliberately hard to point at the wrong thing:

1. It only ever creates inside folder charley-dev (25dd1e34-...). The id is asserted
   against the live folder listing before anything is written.
2. It never issues an update or delete against an existing item. If a target name is
   already taken it reports and skips - so a second run is a no-op, not an overwrite.
3. It refuses to run if a target name collides with an item OUTSIDE the charley-dev
   folder, which would mean the workspace layout is not what we think it is.
4. Dry run is the default. --apply is required to write anything.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

CHARLEY_DEV = Path(__file__).resolve().parent.parent

API = "https://api.fabric.microsoft.com/v1"
WORKSPACE_ID = "1f7caed6-f88a-4e52-bc83-9a498a165301"   # Build
FOLDER_ID = "25dd1e34-bd57-43ca-aa29-c8fd33013101"      # charley-dev
FOLDER_NAME = "charley-dev"

# Items to create, in dependency order. Lakehouses first: notebooks and semantic models
# reference them.
#
# enableSchemas matches the existing Bronze_Lakehouse / Silver_Lakehouse, which both
# report defaultSchema "dbo". It can ONLY be set at creation - there is no API to enable
# schemas on an existing lakehouse - so getting it wrong means dropping and recreating.
# foundation/README.md:78-81 notes the consequence: Fabric's list-tables API rejects
# schema-enabled lakehouses, so the backup reads INFORMATION_SCHEMA instead.
LAKEHOUSE_PAYLOAD = {"enableSchemas": True}

TARGETS = [
    ("CD_Bronze_Lakehouse", "Lakehouse"),
    ("CD_Silver_Lakehouse", "Lakehouse"),
    ("CD_Gold_Lakehouse", "Lakehouse"),
]


class FabricError(RuntimeError):
    pass


def az_path() -> str:
    """Resolve the az executable.

    On Windows `az` is a .cmd shim, which subprocess will not find from a bare name -
    PATHEXT resolution is a shell feature, and we do not run through a shell.
    """
    import shutil

    for candidate in ("az", "az.cmd", "az.bat", "az.exe"):
        found = shutil.which(candidate)
        if found:
            return found
    raise FabricError("Azure CLI not found on PATH. Install it, then run `az login`.")


def token() -> str:
    result = subprocess.run(
        [az_path(), "account", "get-access-token",
         "--resource", "https://api.fabric.microsoft.com",
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise FabricError(f"az token failed - run `az login`.\n{result.stderr.strip()}")
    return result.stdout.strip()


def call(method: str, path: str, tok: str, body: dict | None = None) -> tuple[int, dict, dict]:
    request = urllib.request.Request(
        f"{API}{path}",
        method=method,
        data=json.dumps(body).encode() if body else None,
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read().decode()
            return response.status, (json.loads(raw) if raw else {}), dict(response.headers)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        raise FabricError(f"{method} {path} -> {exc.code}\n{raw[:500]}") from exc


def wait_for_operation(headers: dict, tok: str, timeout: int = 180) -> None:
    """Fabric returns 202 + Location for long-running creates. Poll until it settles."""
    location = headers.get("Location")
    if not location:
        return
    path = location.replace(API, "")
    deadline = time.time() + timeout
    while time.time() < deadline:
        _, body, _ = call("GET", path, tok)
        status = body.get("status", "")
        if status in ("Succeeded", "Completed"):
            return
        if status == "Failed":
            raise FabricError(f"operation failed: {body.get('error')}")
        time.sleep(3)
    raise FabricError(f"operation did not finish within {timeout}s")


def list_items(tok: str) -> list[dict]:
    _, body, _ = call("GET", f"/workspaces/{WORKSPACE_ID}/items", tok)
    return body.get("value", [])


def assert_folder(tok: str) -> None:
    """The folder id must resolve, and it must be the folder we think it is."""
    _, body, _ = call("GET", f"/workspaces/{WORKSPACE_ID}/folders", tok)
    folders = {f["id"]: f["displayName"] for f in body.get("value", [])}
    name = folders.get(FOLDER_ID)
    if name is None:
        raise FabricError(f"folder {FOLDER_ID} not found in workspace {WORKSPACE_ID}")
    if name != FOLDER_NAME:
        raise FabricError(f"folder {FOLDER_ID} is named {name!r}, expected {FOLDER_NAME!r}")
    print(f"  folder ok: {name} ({FOLDER_ID})")


def plan(items: list[dict]) -> tuple[list[tuple[str, str]], list[str], list[str]]:
    """Split targets into create / already-there / blocked-by-a-collision."""
    inside = {i["displayName"] for i in items if i.get("folderId") == FOLDER_ID}
    outside = {i["displayName"] for i in items if i.get("folderId") != FOLDER_ID}

    to_create, existing, collisions = [], [], []
    for name, kind in TARGETS:
        if name in inside:
            existing.append(name)
        elif name in outside:
            # Never adopt or modify an item we did not create.
            collisions.append(name)
        else:
            to_create.append((name, kind))
    return to_create, existing, collisions


def create(name: str, kind: str, tok: str, attempts: int = 12, delay: int = 20) -> None:
    """Create one item, retrying while Fabric still holds a just-deleted name.

    Deleting an item does not free its display name immediately; Fabric returns 409
    ItemDisplayNameNotAvailableYet with isRetriable=true for a few minutes afterwards.
    Delete-then-recreate is a normal workflow, so this belongs in the tool rather than
    in the operator's patience.
    """
    body = {"displayName": name, "type": kind, "folderId": FOLDER_ID}
    if kind == "Lakehouse":
        body["creationPayload"] = LAKEHOUSE_PAYLOAD

    for attempt in range(attempts):
        try:
            status, _, headers = call("POST", f"/workspaces/{WORKSPACE_ID}/items", tok, body)
            if status == 202:
                wait_for_operation(headers, tok)
            return
        except FabricError as exc:
            retriable = "NotAvailableYet" in str(exc) or "isRetriable\":true" in str(exc)
            if not retriable or attempt == attempts - 1:
                raise
            print(f"name still held, retry {attempt + 1}/{attempts - 1} ...", end=" ", flush=True)
            time.sleep(delay)


def check_schemas(tok: str) -> int:
    """Every CD_ lakehouse must be schema-enabled, like the two Rebecca built.

    Checked rather than assumed because it is unfixable in place: a lakehouse created
    without it has to be dropped and recreated, which is free today and expensive once
    tables exist.
    """
    _, body, _ = call("GET", f"/workspaces/{WORKSPACE_ID}/lakehouses", tok)
    wrong = []
    for lh in body.get("value", []):
        if not lh["displayName"].startswith("CD_"):
            continue
        schema = lh.get("properties", {}).get("defaultSchema")
        marker = "ok" if schema else "NOT SCHEMA-ENABLED"
        print(f"  {lh['displayName']:<24} defaultSchema={schema!r:<8} {marker}")
        if not schema:
            wrong.append(lh["displayName"])
    if wrong:
        print(f"\n{len(wrong)} lakehouse(s) not schema-enabled: {', '.join(wrong)}")
        print("This cannot be changed in place - drop and recreate while they are empty.")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="actually create items")
    parser.add_argument("--verify", action="store_true", help="report state, change nothing")
    args = parser.parse_args()

    tok = token()
    print(f"workspace {WORKSPACE_ID}")
    assert_folder(tok)

    items = list_items(tok)
    in_folder = [i for i in items if i.get("folderId") == FOLDER_ID]

    if args.verify:
        print(f"\ncharley-dev contains {len(in_folder)} item(s):")
        for i in sorted(in_folder, key=lambda x: (x["type"], x["displayName"])):
            print(f"  {i['type']:<16} {i['displayName']}")
        print(f"\nworkspace total: {len(items)} items")
        print("\nschema check:")
        return check_schemas(tok)

    to_create, existing, collisions = plan(items)

    if collisions:
        print("\nREFUSING TO RUN - these names exist OUTSIDE charley-dev:")
        for name in collisions:
            print(f"  {name}")
        print("The workspace layout is not what this script expects. Investigate first.")
        return 1

    print(f"\n{len(existing)} already present, {len(to_create)} to create")
    for name in existing:
        print(f"  = {name}")
    for name, kind in to_create:
        print(f"  + {name} ({kind})")

    if not to_create:
        print("\nnothing to do")
        return 0

    if not args.apply:
        print("\nDRY RUN - nothing written. Re-run with --apply to create.")
        return 0

    print()
    for name, kind in to_create:
        print(f"  creating {name} ...", end=" ", flush=True)
        create(name, kind, tok)
        print("ok")

    after = [i for i in list_items(tok) if i.get("folderId") == FOLDER_ID]
    print(f"\ncharley-dev now contains {len(after)} item(s)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FabricError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
