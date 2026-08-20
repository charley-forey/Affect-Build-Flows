"""Create the BUILD site structure over Microsoft Graph - no PnP, no admin consent.

    python provision_build_site.py --site-url https://<tenant>.sharepoint.com/sites/<site>
    python provision_build_site.py --site-url ... --apply
    python provision_build_site.py --print-columns    # the spec, for building it by hand

WHY THIS EXISTS ALONGSIDE provision-sharepoint-build.ps1.

The PS1 does the same job and is the better tool if you can run it. It needs PnP.PowerShell,
which since 2.x needs `Register-PnPEntraIDAppForInteractiveLogin`, which needs a **tenant
admin to consent**. That consent was the blocker throughout, and it gates everything else:

    InvalidOpenApiFlow ... 'GetTable' failed with status code 'NotFound' ... "List not found"

That is what Power Automate returns when you SAVE a flow whose trigger points at a list that
does not exist. Without the site structure the flows cannot merely fail at runtime - they
cannot be CREATED. So this had to stop being blocked on an admin ticket.

WHY GRAPH RATHER THAN SHAREPOINT REST.

The obvious spelling is the SharePoint REST API, `{site}/_api/web`, and against this tenant
it returns:

    HTTP 401 {"error":"invalid_request"}

with a token whose audience is correct (00000003-0000-0ff1-ce00-000000000000, SharePoint's
own app id). The tenant does not accept Azure CLI tokens for SharePoint's legacy endpoint.
Microsoft Graph, with a token from the same CLI session, returns 200 for the same site. Both
were measured, not assumed - see the audiences in the commit message.

So: Graph. Same mechanism deploy_flows.py already proved works here - a token from the CLI
session you are signed in to. No new module, no new consent.

WHAT IT CREATES, matching provision-sharepoint-build.ps1 exactly:
    01 ESTIMATING       document library
    00 PROJECTS         document library
    Job Register        list, 11 columns, and the two template folder trees

DRY RUN BY DEFAULT. IDEMPOTENT: anything that exists is left alone, so re-running is how you
apply a change rather than something to avoid.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from urllib.parse import quote, urlparse

GRAPH = "https://graph.microsoft.com/v1.0"
GRAPH_RESOURCE = "https://graph.microsoft.com"

ESTIMATING_LIBRARY = "01 ESTIMATING"
PROJECTS_LIBRARY = "00 PROJECTS"
ESTIMATING_TEMPLATE_ROOT = "02 E26-000 BOILER PLATE"
PROJECT_TEMPLATE_ROOT = "YY-000 STANDARD PROJECT TEMPLATE"

# Placeholder structure, exactly as the PS1 ships it. Only 01-BIDDING/02-ESTIMATING is
# certain - the Convert-to-Bidding step copies the estimating folder into that literal path,
# so the project template must contain it. Everything else is a shape to be replaced with the
# client's real trees; the SOP names the folders and never says what is inside them.
ESTIMATING_TEMPLATE = [
    "01-ENQUIRY", "02-DRAWINGS", "03-TAKEOFF", "04-SUBCONTRACTOR QUOTES",
    "05-SUPPLIER QUOTES", "06-ESTIMATE SUMMARY", "07-SUBMISSION",
]
PROJECT_TEMPLATE = [
    "01-BIDDING", "01-BIDDING/01-TENDER", "01-BIDDING/02-ESTIMATING",
    "02-CONTRACT", "03-DRAWINGS", "04-SUBMITTALS", "05-RFI", "06-SITE",
    "07-COMMERCIAL", "08-HANDOVER",
]

# (name, Graph column facet). The facet decides the SharePoint type.
#
# INTERNAL NAMES ARE THE CONTRACT. The flows read these exact strings, and a column created
# through the SharePoint UI as "Job Year" gets the internal name Job_x0020_Year - which does
# not error, the value simply never arrives and the report shows a blank that reads exactly
# like nobody having filled it in.
COLUMNS: list[tuple[str, dict]] = [
    ("JobYear", {"number": {"decimalPlaces": "none"}}),
    ("JobSeq", {"number": {"decimalPlaces": "none"}}),
    ("JobNumber", {"text": {}}),
    ("Stage", {"choice": {"choices": ["Requested", "Estimating", "Bidding", "Failed"],
                          "displayAs": "dropDownMenu"},
               "defaultValue": {"value": "Requested"}}),
    ("EstimatingFolderUrl", {"hyperlinkOrPicture": {"isPicture": False}}),
    ("ProjectFolderUrl", {"hyperlinkOrPicture": {"isPicture": False}}),
    # Text, not Person. A Person column arrives in Fabric as a nested record that silver then
    # has to unpick, and the flow only ever has an email anyway.
    ("RequestedBy", {"text": {}}),
    ("RequestedAt", {"dateTime": {"format": "dateTime"}}),
    ("CompletedAt", {"dateTime": {"format": "dateTime"}}),
    ("CopyJobStatus", {"text": {}}),
    ("ErrorDetail", {"text": {"allowMultipleLines": True}}),
]

HUMAN_TYPE = {
    "number": "Number",
    "text": "Single line of text",
    "choice": "Choice",
    "dateTime": "Date and time",
    "hyperlinkOrPicture": "Hyperlink",
}


def az() -> str:
    found = shutil.which("az")
    if not found:
        raise SystemExit("the Azure CLI ('az') is not on PATH. Run this where `az` works.")
    return found


def token() -> str:
    result = subprocess.run(
        [az(), "account", "get-access-token", "--resource", GRAPH_RESOURCE,
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise SystemExit(
            "could not get a Microsoft Graph token from the Azure CLI.\n"
            f"  {result.stderr.strip()}\n\n"
            "Run 'az login' first. If that works and this still fails, build the list by\n"
            "hand instead: python provision_build_site.py --print-columns"
        )
    return result.stdout.strip()


def call(method: str, url: str, tok: str, body: dict | None = None) -> tuple[int, dict | str]:
    """(status, parsed body) or (status, error text). Never raises on an HTTP error."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url if url.startswith("http") else f"{GRAPH}{url}",
        data=data, method=method,
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as response:
            raw = response.read()
            return response.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode(errors="replace")


def need(method: str, url: str, tok: str, body: dict | None = None, what: str = "") -> dict:
    status, payload = call(method, url, tok, body)
    if status >= 400:
        raise SystemExit(f"{what or method} {url}\n  HTTP {status}\n  {str(payload)[:900]}")
    return payload  # type: ignore[return-value]


def site_id(site_url: str, tok: str) -> str:
    parsed = urlparse(site_url)
    status, payload = call("GET", f"/sites/{parsed.netloc}:{parsed.path.rstrip('/')}", tok)
    if status >= 400:
        hint = {
            401: "the Graph token was rejected. Run 'az login' again.",
            403: "authenticated but not authorised on this site.",
            404: "no site at this path. The URL must be the SITE - the part up to\n"
                 "  /sites/<name> - not a page inside it.",
        }.get(status, "the response body above is the whole answer.")
        raise SystemExit(f"GET /sites/{parsed.netloc}:{parsed.path}\n"
                         f"  HTTP {status}\n  {str(payload)[:500]}\n\n  {hint}")
    return payload["id"]  # type: ignore[index]


def lists_by_name(sid: str, tok: str) -> dict[str, dict]:
    found = need("GET", f"/sites/{sid}/lists?$select=id,displayName,name", tok)
    return {item["displayName"]: item for item in found.get("value", [])}


def ensure_list(sid: str, tok: str, title: str, template: str, apply: bool,
                existing: dict[str, dict]) -> str | None:
    if title in existing:
        print(f"  exists   {title}")
        return existing[title]["id"]
    if not apply:
        print(f"  would create  {title}")
        return None
    created = need("POST", f"/sites/{sid}/lists", tok, {
        "displayName": title,
        "list": {"template": template},
    }, what=f"create {title}")
    print(f"  created  {title}")
    return created["id"]


def ensure_columns(sid: str, list_id: str | None, tok: str, apply: bool) -> None:
    have: set[str] = set()
    if list_id:
        have = {c["name"] for c in
                need("GET", f"/sites/{sid}/lists/{list_id}/columns?$select=name",
                     tok).get("value", [])}
    for name, facet in COLUMNS:
        if name in have:
            print(f"    exists   {name}")
            continue
        if not apply or not list_id:
            print(f"    would create  {name}")
            continue
        body = {"name": name, "displayName": name, **facet}
        need("POST", f"/sites/{sid}/lists/{list_id}/columns", tok, body,
             what=f"create column {name}")
        print(f"    created  {name}")


def drive_id(sid: str, list_id: str, tok: str) -> str:
    """A document library's drive, which is how Graph addresses its folders."""
    return need("GET", f"/sites/{sid}/lists/{list_id}/drive?$select=id", tok)["id"]


def ensure_folder(drive: str, tok: str, path: str, apply: bool) -> None:
    status, _ = call("GET", f"/drives/{drive}/root:/{quote(path)}", tok)
    if status == 200:
        print(f"    exists   {path}")
        return
    if not apply:
        print(f"    would create  {path}")
        return
    parent, _, leaf = path.rpartition("/")
    target = (f"/drives/{drive}/root:/{quote(parent)}:/children" if parent
              else f"/drives/{drive}/root/children")
    need("POST", target, tok,
         {"name": leaf, "folder": {}, "@microsoft.graph.conflictBehavior": "fail"},
         what=f"create folder {path}")
    print(f"    created  {path}")


def print_columns() -> None:
    print("Job Register - create these with EXACTLY these names. Internal names are the")
    print("contract: 'Job Year' becomes Job_x0020_Year and simply never arrives.\n")
    print(f"  {'Column':<22} Type")
    print(f"  {'-' * 22} {'-' * 46}")
    print(f"  {'Title':<22} Single line of text  (rename to 'Project Name', required)")
    for name, facet in COLUMNS:
        kind = next(HUMAN_TYPE[k] for k in facet if k in HUMAN_TYPE)
        note = ""
        if "choice" in facet:
            note = "  Requested / Estimating / Bidding / Failed, default Requested"
        elif facet.get("text", {}).get("allowMultipleLines"):
            kind = "Multiple lines of text"
        print(f"  {name:<22} {kind}{note}")
    print("\nAlso: List settings -> Versioning settings -> Create a version each time you")
    print("edit an item = Yes. That is what gives every field change a who and a when.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-url", help="e.g. https://contoso.sharepoint.com/sites/BUILD")
    parser.add_argument("--apply", action="store_true", help="actually create things")
    parser.add_argument("--print-columns", action="store_true",
                        help="print the Job Register spec for creating it by hand, and exit")
    args = parser.parse_args()

    if args.print_columns:
        print_columns()
        return 0
    if not args.site_url:
        print("--site-url is required (or --print-columns to build it by hand).")
        return 2

    site = args.site_url.rstrip("/")
    if not args.apply:
        print("DRY RUN - nothing will be created. Re-run with --apply.\n")
    print(f"site: {site}")

    tok = token()
    sid = site_id(site, tok)
    print(f"  resolved: {sid.split(',')[0]}\n")

    existing = lists_by_name(sid, tok)

    print("libraries")
    est_id = ensure_list(sid, tok, ESTIMATING_LIBRARY, "documentLibrary", args.apply, existing)
    prj_id = ensure_list(sid, tok, PROJECTS_LIBRARY, "documentLibrary", args.apply, existing)

    print("\nJob Register")
    reg_id = ensure_list(sid, tok, "Job Register", "genericList", args.apply, existing)
    ensure_columns(sid, reg_id, tok, args.apply)

    for label, list_id, root, tree in (
        (ESTIMATING_LIBRARY, est_id, ESTIMATING_TEMPLATE_ROOT, ESTIMATING_TEMPLATE),
        (PROJECTS_LIBRARY, prj_id, PROJECT_TEMPLATE_ROOT, PROJECT_TEMPLATE),
    ):
        print(f"\ntemplate: {label}/{root}")
        if not list_id:
            print(f"    (library not created yet - folders come with it)")
            continue
        drive = drive_id(sid, list_id, tok)
        ensure_folder(drive, tok, root, args.apply)
        for folder in tree:
            ensure_folder(drive, tok, f"{root}/{folder}", args.apply)

    if args.apply:
        print("\nDone. Now create the flows:")
        print(f"  python deploy_flows.py --site-url {site} --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
