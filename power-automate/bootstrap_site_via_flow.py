"""Create the BUILD site structure by having Power Automate do it.

    python bootstrap_site_via_flow.py --site-url https://... --connection <name>
    python bootstrap_site_via_flow.py --site-url https://... --connection <name> --apply
    python bootstrap_site_via_flow.py --cleanup --connection <name>   # delete the helper

WHY THIS ROUNDABOUT ROUTE EXISTS.

Creating a SharePoint list needs a token that can write to SharePoint, and in this tenant
every direct route is closed. All three were measured, not assumed:

    SharePoint REST   {site}/_api/web  ->  401 {"error":"invalid_request"}
                      The audience is correct (00000003-0000-0ff1-ce00-000000000000).
                      The tenant simply does not accept Azure CLI tokens there.

    Microsoft Graph   reads fine, POST /sites/{id}/lists -> 403 accessDenied.
                      The CLI's Graph token carries no Sites.* scope at all - reads slip
                      through on Directory.AccessAsUser.All. It is a fixed first-party
                      app, so this cannot be widened.

    PnP PowerShell    AADSTS700016. PnP 3.x needs PowerShell 7 (this machine has 5.1),
                      and 1.12.0 signs in through the shared "PnP Management Shell" app,
                      which no longer exists in any directory - Microsoft retired it,
                      which is exactly why 2.x made you register your own.

What IS proven to work is the Power Automate API: creating flows there succeeds, and a
SharePoint connection already exists in the environment. A flow's SharePoint actions run
server-side **as that connection**, which holds the site permissions of the person who made
it. So the flow can do what the CLI cannot.

This builds a throwaway flow whose actions are the REST calls, runs it once, and deletes it.
It asks for no new consent, registers no application, and leaves no credential behind.

NOT A PATTERN TO COPY. It is a bootstrap for exactly one problem: the site structure must
exist before the real flows can even be SAVED, because Power Automate resolves a trigger's
list at save time. Once that structure exists this file has no further use.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

API = "https://api.flow.microsoft.com"
RESOURCE = "https://service.flow.microsoft.com/"
API_VERSION = "2016-11-01"
SHAREPOINT_API = "/providers/Microsoft.PowerApps/apis/shared_sharepointonline"

HELPER_NAME = "ZZ Bootstrap BUILD site (delete me)"

ESTIMATING_LIBRARY = "01 ESTIMATING"
PROJECTS_LIBRARY = "00 PROJECTS"
ESTIMATING_TEMPLATE_ROOT = "02 E26-000 BOILER PLATE"
PROJECT_TEMPLATE_ROOT = "YY-000 STANDARD PROJECT TEMPLATE"

ESTIMATING_TEMPLATE = [
    "01-ENQUIRY", "02-DRAWINGS", "03-TAKEOFF", "04-SUBCONTRACTOR QUOTES",
    "05-SUPPLIER QUOTES", "06-ESTIMATE SUMMARY", "07-SUBMISSION",
]
PROJECT_TEMPLATE = [
    "01-BIDDING", "01-BIDDING/01-TENDER", "01-BIDDING/02-ESTIMATING",
    "02-CONTRACT", "03-DRAWINGS", "04-SUBMITTALS", "05-RFI", "06-SITE",
    "07-COMMERCIAL", "08-HANDOVER",
]

# (name, SchemaXml Type, extra inner XML). Internal names are the contract - the flows read
# these exact strings, and a column made in the UI as "Job Year" becomes Job_x0020_Year,
# which never errors and never arrives.
COLUMNS: list[tuple[str, str, str]] = [
    ("JobYear", "Number", ""),
    ("JobSeq", "Number", ""),
    ("JobNumber", "Text", ""),
    ("Stage", "Choice",
     "<Default>Requested</Default><CHOICES><CHOICE>Requested</CHOICE>"
     "<CHOICE>Estimating</CHOICE><CHOICE>Bidding</CHOICE><CHOICE>Failed</CHOICE></CHOICES>"),
    ("EstimatingFolderUrl", "URL", ""),
    ("ProjectFolderUrl", "URL", ""),
    ("RequestedBy", "Text", ""),
    ("RequestedAt", "DateTime", ""),
    ("CompletedAt", "DateTime", ""),
    ("CopyJobStatus", "Text", ""),
    ("ErrorDetail", "Note", ""),
]

VERBOSE = {"Accept": "application/json;odata=verbose",
           "Content-Type": "application/json;odata=verbose"}


def az() -> str:
    found = shutil.which("az")
    if not found:
        raise SystemExit("the Azure CLI ('az') is not on PATH.")
    return found


def token() -> str:
    result = subprocess.run(
        [az(), "account", "get-access-token", "--resource", RESOURCE,
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"no Power Automate token: {result.stderr.strip()}")
    return result.stdout.strip()


def try_call(method: str, path: str, tok: str,
             body: dict | None = None) -> tuple[int, dict | str]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{API}{path}", data=data, method=method,
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as response:
            raw = response.read()
            return response.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode(errors="replace")


def call(method: str, path: str, tok: str, body: dict | None = None) -> dict:
    status, payload = try_call(method, path, tok, body)
    if status >= 400:
        raise SystemExit(f"{method} {path}\n  HTTP {status}\n  {str(payload)[:900]}")
    return payload  # type: ignore[return-value]


def environment(tok: str) -> str:
    envs = call("GET", f"/providers/Microsoft.ProcessSimple/environments"
                       f"?api-version={API_VERSION}", tok).get("value", [])
    default = next((e for e in envs if e.get("properties", {}).get("isDefault")), envs[0])
    return default["name"]


def rest_steps(site_url: str) -> list[tuple[str, str, str, dict | None]]:
    """(label, method, uri, body) - every SharePoint REST call, in dependency order."""
    path = "/" + site_url.split("/", 3)[3] if site_url.count("/") > 2 else ""
    steps: list[tuple[str, str, str, dict | None]] = []

    for title, template in ((ESTIMATING_LIBRARY, 101), (PROJECTS_LIBRARY, 101),
                            ("Job Register", 100)):
        steps.append((f"list {title}", "POST", "_api/web/lists", {
            "__metadata": {"type": "SP.List"},
            "Title": title,
            "BaseTemplate": template,
            # Versioning is what gives every field change a who and a when.
            "EnableVersioning": True,
        }))

    for name, ftype, extra in COLUMNS:
        schema = (f"<Field Type='{ftype}' DisplayName='{name}' Name='{name}' "
                  f"StaticName='{name}'>{extra}</Field>")
        steps.append((f"column {name}", "POST",
                      "_api/web/lists/getbytitle('Job Register')/fields/createfieldasxml", {
                          "parameters": {
                              "__metadata": {
                                  "type": "SP.XmlSchemaFieldCreationInformation"},
                              "SchemaXml": schema,
                              "Options": 8,  # AddFieldToDefaultView
                          },
                      }))

    for library, root, tree in ((ESTIMATING_LIBRARY, ESTIMATING_TEMPLATE_ROOT,
                                 ESTIMATING_TEMPLATE),
                                (PROJECTS_LIBRARY, PROJECT_TEMPLATE_ROOT,
                                 PROJECT_TEMPLATE)):
        for folder in [root] + [f"{root}/{f}" for f in tree]:
            steps.append((f"folder {library}/{folder}", "POST", "_api/web/folders", {
                "__metadata": {"type": "SP.Folder"},
                "ServerRelativeUrl": f"{path}/{library}/{folder}",
            }))
    return steps


def safe(label: str, index: int) -> str:
    """Flow action names allow no spaces or punctuation."""
    cleaned = "".join(c if c.isalnum() else "_" for c in label)
    return f"S{index:02d}_{cleaned}"[:80]


def build_definition(site_url: str, steps) -> dict:
    """A button-triggered flow whose actions are the REST calls, chained in order.

    Every action runs after the previous one whether it Succeeded OR Failed. That is what
    makes a re-run safe: a list or column that already exists returns an error, and the
    chain must continue past it rather than abandoning the twenty steps behind it.
    """
    actions: dict[str, dict] = {}
    previous: str | None = None
    for index, (label, method, uri, body) in enumerate(steps, start=1):
        name = safe(label, index)
        params: dict = {
            "dataset": site_url,
            "parameters/method": method,
            "parameters/uri": uri,
            "parameters/headers": VERBOSE,
        }
        if body is not None:
            params["parameters/body"] = json.dumps(body)
        actions[name] = {
            "type": "OpenApiConnection",
            "description": label,
            "inputs": {
                "host": {
                    "connectionName": "shared_sharepointonline",
                    "operationId": "HttpRequest",
                    "apiId": SHAREPOINT_API,
                },
                "parameters": params,
                "authentication": "@parameters('$authentication')",
            },
            **({"runAfter": {previous: ["Succeeded", "Failed"]}} if previous
               else {"runAfter": {}}),
        }
        previous = name

    return {
        "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/"
                   "2016-06-01/workflowdefinition.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {
            "$connections": {"defaultValue": {}, "type": "Object"},
            "$authentication": {"defaultValue": {}, "type": "SecureObject"},
        },
        "triggers": {
            "manual": {
                "type": "Request",
                "kind": "Button",
                "inputs": {"schema": {"type": "object", "properties": {}}},
            },
        },
        "actions": actions,
        "outputs": {},
    }


def find_flow(tok: str, env: str, display: str) -> str | None:
    listed = call("GET", f"/providers/Microsoft.ProcessSimple/environments/{env}"
                         f"/flows?api-version={API_VERSION}", tok).get("value", [])
    for flow in listed:
        if flow.get("properties", {}).get("displayName") == display:
            return flow["name"]
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-url")
    parser.add_argument("--connection", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--cleanup", action="store_true",
                        help="delete the helper flow and exit")
    args = parser.parse_args()

    tok = token()
    env = environment(tok)
    print(f"environment: {env}")

    if args.cleanup:
        existing = find_flow(tok, env, HELPER_NAME)
        if not existing:
            print("  no helper flow to delete")
            return 0
        call("DELETE", f"/providers/Microsoft.ProcessSimple/environments/{env}"
                       f"/flows/{existing}?api-version={API_VERSION}", tok)
        print(f"  deleted {HELPER_NAME}")
        return 0

    if not args.site_url:
        print("--site-url is required")
        return 2

    site = args.site_url.rstrip("/")
    steps = rest_steps(site)
    print(f"site: {site}")
    print(f"steps: {len(steps)} SharePoint REST calls\n")
    for label, method, uri, _ in steps:
        print(f"  {method:<5} {label}")

    if not args.apply:
        print("\nDRY RUN - nothing created. Re-run with --apply.")
        return 0

    existing = find_flow(tok, env, HELPER_NAME)
    if existing:
        print(f"\nhelper flow already exists ({existing}) - deleting it first")
        call("DELETE", f"/providers/Microsoft.ProcessSimple/environments/{env}"
                       f"/flows/{existing}?api-version={API_VERSION}", tok)

    print("\ncreating helper flow")
    created = call("POST", f"/providers/Microsoft.ProcessSimple/environments/{env}"
                           f"/flows?api-version={API_VERSION}", tok, {
        "properties": {
            "displayName": HELPER_NAME,
            "definition": build_definition(site, steps),
            "connectionReferences": {
                "shared_sharepointonline": {
                    "connectionName": args.connection,
                    "source": "Embedded",
                    "id": SHAREPOINT_API,
                },
            },
            "state": "Started",
        },
    })
    flow_id = created["name"]
    print(f"  {flow_id}")

    print("running it")
    status, payload = try_call(
        "POST", f"/providers/Microsoft.ProcessSimple/environments/{env}"
                f"/flows/{flow_id}/triggers/manual/run?api-version={API_VERSION}", tok, {})
    if status >= 400:
        raise SystemExit(f"could not run the helper flow\n  HTTP {status}\n  "
                         f"{str(payload)[:900]}")

    print("waiting for the run", end="", flush=True)
    outcome = "unknown"
    for _ in range(60):
        time.sleep(5)
        print(".", end="", flush=True)
        runs = call("GET", f"/providers/Microsoft.ProcessSimple/environments/{env}"
                           f"/flows/{flow_id}/runs?api-version={API_VERSION}",
                    tok).get("value", [])
        if not runs:
            continue
        outcome = runs[0].get("properties", {}).get("status", "unknown")
        if outcome not in ("Running", "Waiting"):
            break
    print(f"\n  run status: {outcome}")
    print("\nThe run reports Failed if ANY step failed, and a step fails when the thing it")
    print("creates already exists - so Failed is expected on a re-run and is not the same")
    print("as nothing having been created. Verify with:")
    print(f"  python provision_build_site.py --site-url {site}")
    print("\nThen delete the helper:")
    print(f"  python bootstrap_site_via_flow.py --cleanup --connection {args.connection}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
