"""Create the BUILD site structure over SharePoint REST - no PnP, no admin consent.

    python provision_build_site.py --site-url https://<tenant>.sharepoint.com/sites/<site>
    python provision_build_site.py --site-url ... --apply

WHY THIS EXISTS ALONGSIDE provision-sharepoint-build.ps1.

The PS1 does the same job and is the better tool if you can run it. It needs PnP.PowerShell,
which since 2.x needs `Register-PnPEntraIDAppForInteractiveLogin`, which needs a **tenant
admin to consent**. That consent has been the blocker throughout, and it is a blocker on a
step that turns out to gate everything else:

    InvalidOpenApiFlow ... 'GetTable' failed with status code 'NotFound' ... "List not found"

That is what Power Automate returns when you try to SAVE a flow whose trigger points at a
list that does not exist. The flows cannot merely fail at runtime without the site structure
- they cannot be CREATED without it. So this had to stop being blocked on an admin ticket.

This uses the same mechanism deploy_flows.py already proved works in this tenant: a token
from the Azure CLI session you are already signed in to. No new consent, no new module.

WHAT IT CREATES, matching the PS1 exactly:
    01 ESTIMATING       document library
    00 PROJECTS         document library
    Job Register        list, 11 columns, versioning on
    two template folder trees

DRY RUN BY DEFAULT. Reads happen either way, so a dry run reports what a real run would do.
IDEMPOTENT: anything that already exists is left alone, so re-running is how you apply a
change rather than something to avoid.
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

API_VERSION_HEADERS = {
    "Accept": "application/json;odata=verbose",
    "Content-Type": "application/json;odata=verbose",
}

ESTIMATING_LIBRARY = "01 ESTIMATING"
PROJECTS_LIBRARY = "00 PROJECTS"
ESTIMATING_TEMPLATE_ROOT = "02 E26-000 BOILER PLATE"
PROJECT_TEMPLATE_ROOT = "YY-000 STANDARD PROJECT TEMPLATE"

# Placeholder structure, exactly as the PS1 ships it. Only 01-BIDDING/02-ESTIMATING is
# certain - the Convert-to-Bidding step copies the estimating folder into that literal path,
# so the project template must contain it. Everything else is a shape to be replaced with
# the client's real trees; the SOP names the folders and never says what is in them.
ESTIMATING_TEMPLATE = [
    "01-ENQUIRY", "02-DRAWINGS", "03-TAKEOFF", "04-SUBCONTRACTOR QUOTES",
    "05-SUPPLIER QUOTES", "06-ESTIMATE SUMMARY", "07-SUBMISSION",
]
PROJECT_TEMPLATE = [
    "01-BIDDING", "01-BIDDING/01-TENDER", "01-BIDDING/02-ESTIMATING",
    "02-CONTRACT", "03-DRAWINGS", "04-SUBMITTALS", "05-RFI", "06-SITE",
    "07-COMMERCIAL", "08-HANDOVER",
]

# (name, SchemaXml type, extra XML). Created with createfieldasxml so one code path handles
# Number, Text, Note, DateTime, URL and Choice alike, and Options=8 adds each to the default
# view in the same call.
#
# INTERNAL NAMES ARE THE CONTRACT. The flows read these exact strings, and a column created
# through the SharePoint UI as "Job Year" gets the internal name Job_x0020_Year - which does
# not error, it just never arrives. Name and DisplayName are set identically here.
COLUMNS: list[tuple[str, str, str]] = [
    ("JobYear", "Number", ""),
    ("JobSeq", "Number", ""),
    ("JobNumber", "Text", ""),
    ("Stage", "Choice",
     "<Default>Requested</Default>"
     "<CHOICES><CHOICE>Requested</CHOICE><CHOICE>Estimating</CHOICE>"
     "<CHOICE>Bidding</CHOICE><CHOICE>Failed</CHOICE></CHOICES>"),
    ("EstimatingFolderUrl", "URL", ""),
    ("ProjectFolderUrl", "URL", ""),
    # Text, not Person. A Person column arrives in Fabric as a nested record that silver
    # then has to unpick, and the flow only ever has an email anyway.
    ("RequestedBy", "Text", ""),
    ("RequestedAt", "DateTime", ""),
    ("CompletedAt", "DateTime", ""),
    ("CopyJobStatus", "Text", ""),
    ("ErrorDetail", "Note", ""),
]


def az() -> str:
    found = shutil.which("az")
    if not found:
        raise SystemExit("the Azure CLI ('az') is not on PATH. Run this where `az` works.")
    return found


def token(site_url: str) -> str:
    """A SharePoint token for this tenant, from your existing CLI session.

    The resource is the tenant's SharePoint host - not a Graph or Azure scope. If the tenant
    has not consented the Azure CLI to SharePoint, this is where it says so, and the fallback
    is the PS1 or building the list by hand.
    """
    host = f"{urlparse(site_url).scheme}://{urlparse(site_url).netloc}"
    result = subprocess.run(
        [az(), "account", "get-access-token", "--resource", host,
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise SystemExit(
            f"could not get a SharePoint token for {host}.\n"
            f"  {result.stderr.strip()}\n\n"
            "This tenant has not consented the Azure CLI to SharePoint. Two ways on:\n"
            "  - run provision-sharepoint-build.ps1 (needs PnP and a tenant admin), or\n"
            "  - create 'Job Register' by hand; --print-columns lists exactly what it needs."
        )
    return result.stdout.strip()


def call(method: str, url: str, tok: str, body: dict | None = None) -> tuple[int, str]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Authorization": f"Bearer {tok}", **API_VERSION_HEADERS},
    )
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, response.read().decode(errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode(errors="replace")


def exists(site: str, tok: str, path: str) -> bool:
    status, _ = call("GET", f"{site}/_api/{path}", tok)
    return status == 200


def ensure_list(site: str, tok: str, title: str, template: int, apply: bool) -> None:
    """A list (100) or document library (101). Left alone if it is already there."""
    if exists(site, tok, f"web/lists/getbytitle('{quote(title)}')"):
        print(f"  exists   {title}")
        return
    if not apply:
        print(f"  would create  {title}")
        return
    status, detail = call("POST", f"{site}/_api/web/lists", tok, {
        "__metadata": {"type": "SP.List"},
        "Title": title,
        "BaseTemplate": template,
        # Versioning is what gives every field change a who and a when - the difference
        # between "the flow failed" and "the flow failed at 14:02 for Sam on job 26-025".
        "EnableVersioning": True,
    })
    if status >= 400:
        raise SystemExit(f"creating {title}\n  HTTP {status}\n  {detail[:800]}")
    print(f"  created  {title}")


def ensure_column(site: str, tok: str, list_title: str,
                  name: str, ftype: str, extra: str, apply: bool) -> None:
    lst = f"web/lists/getbytitle('{quote(list_title)}')"
    if exists(site, tok, f"{lst}/fields/getbyinternalnameortitle('{name}')"):
        print(f"    exists   {name}")
        return
    if not apply:
        print(f"    would create  {name} ({ftype})")
        return
    schema = (f"<Field Type='{ftype}' DisplayName='{name}' Name='{name}' "
              f"StaticName='{name}'>{extra}</Field>")
    status, detail = call("POST", f"{site}/_api/{lst}/fields/createfieldasxml", tok, {
        "parameters": {
            "__metadata": {"type": "SP.XmlSchemaFieldCreationInformation"},
            "SchemaXml": schema,
            "Options": 8,  # AddFieldToDefaultView
        },
    })
    if status >= 400:
        raise SystemExit(f"creating column {name}\n  HTTP {status}\n  {detail[:800]}")
    print(f"    created  {name}")


def ensure_folder(site: str, tok: str, server_relative: str, apply: bool) -> None:
    if exists(site, tok, f"web/getfolderbyserverrelativeurl('{quote(server_relative)}')"):
        print(f"    exists   {server_relative}")
        return
    if not apply:
        print(f"    would create  {server_relative}")
        return
    status, detail = call("POST", f"{site}/_api/web/folders", tok, {
        "__metadata": {"type": "SP.Folder"},
        "ServerRelativeUrl": server_relative,
    })
    if status >= 400:
        raise SystemExit(f"creating folder {server_relative}\n  HTTP {status}\n  {detail[:800]}")
    print(f"    created  {server_relative}")


def print_columns() -> None:
    print("Job Register - create these with EXACTLY these names (internal names are the")
    print("contract; 'Job Year' becomes Job_x0020_Year and simply never arrives):\n")
    print(f"  {'Column':<22} Type")
    print(f"  {'-' * 22} {'-' * 40}")
    print(f"  {'Title':<22} Single line of text  (rename to 'Project Name', required)")
    for name, ftype, extra in COLUMNS:
        kind = {"Number": "Number", "Text": "Single line of text",
                "Note": "Multiple lines of text", "DateTime": "Date and time",
                "URL": "Hyperlink", "Choice": "Choice"}[ftype]
        note = ""
        if ftype == "Choice":
            note = "  Requested / Estimating / Bidding / Failed, default Requested"
        print(f"  {name:<22} {kind}{note}")
    print("\nAlso turn on versioning: List settings -> Versioning settings -> Create a")
    print("version each time you edit an item = Yes.")


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
    print(f"site: {site}\n")

    tok = token(site)
    if not exists(site, tok, "web"):
        raise SystemExit(
            f"cannot read {site}.\n"
            "Check the URL is the SITE, not a page in it - a link ending in /SitePages/"
            "Something.aspx\nnames a page, and the site is the part up to /sites/<name>."
        )

    path = urlparse(site).path.rstrip("/")

    print("libraries")
    ensure_list(site, tok, ESTIMATING_LIBRARY, 101, args.apply)
    ensure_list(site, tok, PROJECTS_LIBRARY, 101, args.apply)

    print("\nJob Register")
    ensure_list(site, tok, "Job Register", 100, args.apply)
    for name, ftype, extra in COLUMNS:
        ensure_column(site, tok, "Job Register", name, ftype, extra, args.apply)

    print(f"\ntemplate: {ESTIMATING_LIBRARY}/{ESTIMATING_TEMPLATE_ROOT}")
    ensure_folder(site, tok, f"{path}/{ESTIMATING_LIBRARY}/{ESTIMATING_TEMPLATE_ROOT}",
                  args.apply)
    for folder in ESTIMATING_TEMPLATE:
        ensure_folder(site, tok,
                      f"{path}/{ESTIMATING_LIBRARY}/{ESTIMATING_TEMPLATE_ROOT}/{folder}",
                      args.apply)

    print(f"\ntemplate: {PROJECTS_LIBRARY}/{PROJECT_TEMPLATE_ROOT}")
    ensure_folder(site, tok, f"{path}/{PROJECTS_LIBRARY}/{PROJECT_TEMPLATE_ROOT}", args.apply)
    for folder in PROJECT_TEMPLATE:
        ensure_folder(site, tok,
                      f"{path}/{PROJECTS_LIBRARY}/{PROJECT_TEMPLATE_ROOT}/{folder}",
                      args.apply)

    if args.apply:
        print("\nDone. Now create the flows:")
        print(f"  python deploy_flows.py --site-url {site} --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
