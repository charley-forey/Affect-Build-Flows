"""Create the two job flows directly, through the Power Automate API.

    python deploy_flows.py                                   # dry run
    python deploy_flows.py --site-url https://... --apply     # create them

WHY THIS EXISTS, given make_import_packages.py already exists.

The package route is the documented one and it does not work here. Two attempts, both
rejected with the same error and no further diagnosis available:

    MissingPackageManifest: The package manifest file 'manifest.json' under
    'Microsoft.Flow' folder missing.

- attempt 1: manifest.json at the package root. The review screen rendered the flow name,
  description and "Create as new" correctly out of it, so the CONTENT parses - the import
  step then wants another one somewhere else.
- attempt 2: the same bytes additionally at Microsoft.Flow/manifest.json. Identical error.

Somewhere a third path is expected and the message does not say which. Guessing at a zip
layout that can only be tested by a human clicking Import is a slow loop, so this takes the
door that does not involve a zip at all: the flow management API accepts the workflow
DEFINITION directly, which is exactly what flows/*.json already is.

If someone later exports a real flow from this tenant as a package, its layout answers the
question and make_import_packages.py can be corrected. Until then this is the working path.

AUTH. A token comes from the Azure CLI you are already signed in to - the same mechanism
_local/deploy_ingestion.py uses for OneLake. Nothing is stored, nothing is printed, and no
token is ever written to a file. If `az account get-access-token` fails for this resource,
your tenant has not consented the Azure CLI to the Power Automate API and this route is
closed; say so rather than working around it.

DRY RUN BY DEFAULT. Reads happen either way, so a dry run reports exactly what a real run
would do. Same convention as provision-sharepoint-build.ps1.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
FLOWS = HERE / "flows"

API = "https://api.flow.microsoft.com"
RESOURCE = "https://service.flow.microsoft.com/"
API_VERSION = "2016-11-01"
SHAREPOINT_API = "/providers/Microsoft.PowerApps/apis/shared_sharepointonline"

# Display names, and the order they must be created in is irrelevant - neither flow
# references the other. They are coupled only through the Job Register list.
FLOWS_TO_CREATE = {
    "EstimatingSetup": "Estimating Setup",
    "ConvertToBidding": "Convert to Bidding",
}


def token() -> str:
    """A Power Automate token from the CLI session you are already signed in to."""
    result = subprocess.run(
        ["az", "account", "get-access-token", "--resource", RESOURCE,
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise SystemExit(
            "could not get a Power Automate token from the Azure CLI.\n"
            f"  {result.stderr.strip()}\n\n"
            "Run 'az login' first. If it succeeds for Azure but fails for this resource,\n"
            "the tenant has not consented the Azure CLI to the Power Automate API, and\n"
            "this route is closed - use the package route or build the flows by hand."
        )
    return result.stdout.strip()


def call(method: str, path: str, tok: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{API}{path}", data=data, method=method,
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as response:
            raw = response.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        # The API's errors are specific and worth surfacing whole. The package importer's
        # were not, which is the reason this file exists.
        raise SystemExit(f"{method} {path}\n  HTTP {exc.code}\n  {detail}") from exc


def environment(tok: str, wanted: str | None) -> str:
    envs = call("GET", f"/providers/Microsoft.ProcessSimple/environments"
                       f"?api-version={API_VERSION}", tok).get("value", [])
    if not envs:
        raise SystemExit("no Power Automate environments visible to this account")
    names = [e["name"] for e in envs]
    if wanted:
        if wanted not in names:
            raise SystemExit(f"environment {wanted} not found. Visible: {', '.join(names)}")
        return wanted
    default = next((e for e in envs
                    if e.get("properties", {}).get("isDefault")), envs[0])
    return default["name"]


def sharepoint_connection(tok: str, env: str) -> tuple[str, str]:
    """(connection name, display name) of a SharePoint connection in this environment.

    A connection is a credential and cannot be created from a definition - it has to
    already exist, made by signing in once in the Power Automate UI. If there is more than
    one, the first is used and the rest are printed, because picking silently between
    somebody's personal connection and a service account is exactly the choice that should
    not be made quietly.
    """
    found = call("GET", f"{SHAREPOINT_API}/connections"
                        f"?api-version={API_VERSION}&$filter=environment eq '{env}'",
                 tok).get("value", [])
    if not found:
        raise SystemExit(
            "no SharePoint connection exists in this environment.\n"
            "Create one first: Power Automate -> Connections -> New connection ->\n"
            "SharePoint, and sign in as the account the flows should run as."
        )
    first = found[0]
    if len(found) > 1:
        print(f"  {len(found)} SharePoint connections; using the first:")
        for c in found:
            who = c.get("properties", {}).get("createdBy", {}).get("displayName", "?")
            print(f"    {c['name']}  ({who})")
    return first["name"], first.get("properties", {}).get("displayName", first["name"])


def definition(stem: str, site_url: str | None) -> dict:
    source = json.loads((FLOWS / f"{stem}.json").read_text(encoding="utf-8"))
    body = {k: v for k, v in source.items() if k != "description"}
    if site_url:
        body["parameters"]["SiteUrl"]["defaultValue"] = site_url.rstrip("/")
    return body


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-url", help="the BUILD site, e.g. "
                                           "https://contoso.sharepoint.com/sites/BUILD")
    parser.add_argument("--environment", help="environment id; default is your default one")
    parser.add_argument("--apply", action="store_true", help="actually create the flows")
    args = parser.parse_args()

    if args.apply and not args.site_url:
        print("--site-url is required with --apply. The flows read it as a definition\n"
              "parameter, which the designer cannot edit after the fact.")
        return 2

    if not args.apply:
        print("DRY RUN - nothing will be created. Re-run with --apply.\n")

    tok = token()
    env = environment(tok, args.environment)
    print(f"environment: {env}")

    conn_name, conn_display = sharepoint_connection(tok, env)
    print(f"connection:  {conn_display}  ({conn_name})")
    print(f"site:        {args.site_url or '(not set - required for --apply)'}\n")

    existing = {f.get("properties", {}).get("displayName"): f["name"]
                for f in call("GET", f"/providers/Microsoft.ProcessSimple/environments/{env}"
                                     f"/flows?api-version={API_VERSION}",
                              tok).get("value", [])}

    for stem, display in FLOWS_TO_CREATE.items():
        if display in existing:
            # Never overwrite. A flow somebody has since edited in the designer is not
            # something to silently replace from a file - and a second flow side by side is
            # recoverable where a clobbered one is not.
            print(f"  SKIP    {display} already exists ({existing[display]})")
            continue
        if not args.apply:
            print(f"  would create  {display}  from flows/{stem}.json")
            continue

        body = {
            "properties": {
                "displayName": display,
                "definition": definition(stem, args.site_url),
                "connectionReferences": {
                    "shared_sharepointonline": {
                        "connectionName": conn_name,
                        "source": "Embedded",
                        "id": SHAREPOINT_API,
                    },
                },
                # Created STOPPED. An Estimating Setup that goes live the instant it is
                # created starts issuing job numbers against a site whose libraries and
                # templates may not exist yet, and its first act is to create folders.
                "state": "Stopped",
            },
        }
        created = call("POST", f"/providers/Microsoft.ProcessSimple/environments/{env}"
                               f"/flows?api-version={API_VERSION}", tok, body)
        print(f"  created  {display}  ({created.get('name', '?')})")

    if args.apply:
        print("\nBoth flows are created STOPPED. Before turning them on:")
        print("  - confirm the trigger's Concurrency Control is on, degree 1")
        print("  - confirm 01 ESTIMATING, 00 PROJECTS, Job Register and both template")
        print("    folders exist in the site above")
    return 0


if __name__ == "__main__":
    sys.exit(main())
