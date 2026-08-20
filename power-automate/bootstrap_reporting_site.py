"""Provision the reporting site's 18 intake lists, through Power Automate.

    python bootstrap_reporting_site.py --site-url https://<tenant>.sharepoint.com/sites/<site> \
                                       --connection <name>
    ... --apply         # do it
    ... --cleanup       # delete the helper flow

Same trick and the same reason as bootstrap_site_via_flow.py: no token available to this
machine can write to SharePoint (REST 401, Graph 403 for want of Sites.*, PnP's shared app
retired), but a flow's SharePoint actions run as the CONNECTION, which has the site
permissions of whoever made it. The header of that file carries the measurements.

WHAT IS DIFFERENT HERE, and why this is a separate file rather than a flag.

  17 lists, 140 columns, from the gold DDL. The spec is NOT restated - it is imported from
  _local/make_sharepoint.py, the same generator that writes provision-sharepoint.ps1 and the
  dataflow. A second copy of 140 column definitions is a second thing to drift, and drift
  here does not error: a column whose name differs by one character simply stops arriving
  and the report shows a blank tile.

  ProjectKey is a LOOKUP at CD Projects, and a lookup needs the target list's GUID. That is
  not knowable before CD Projects exists, so this runs in phases: create the lists, read the
  GUID back through Graph (reads work), then create the columns with it baked in.

  ~180 REST calls is far too many for one flow, so each phase is chunked into flows of
  BATCH actions, run one after another.

NOTHING IS SEEDED. CD Projects is populated from cd-projects.csv because a mistyped project
id does not error - it creates a lookup entry no fact row ever joins to, and the project
silently reports zeros. Every other list is left empty on purpose.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
CHARLEY_DEV = HERE.parent / "foundation" / "charley-dev"
sys.path.insert(0, str(CHARLEY_DEV / "_local"))
sys.path.insert(0, str(HERE))

import make_sharepoint as ms  # noqa: E402
from bootstrap_site_via_flow import (  # noqa: E402
    SHAREPOINT_API, VERBOSE, build_definition, call, environment, find_flow, token, try_call,
)

HELPER_NAME = "ZZ Bootstrap reporting lists (delete me)"
PROJECTS_CSV = CHARLEY_DEV / "01-ingestion" / "Manual" / "cd-projects.csv"

# One flow per batch. Power Automate takes far more than this, but a failed run is easier to
# read at 40 actions than at 180, and each batch is independently re-runnable.
BATCH = 40


def field_schema(table: str, col: str, sql_type: str, projects_guid: str | None) -> str:
    """SharePoint SchemaXml for one column.

    The type decision is ms's, not this file's - vocab_choices(), CHOICES, MULTILINE and
    SQL_TO_PNP are imported so the lists this creates and the PS1 that Affect might run
    instead cannot disagree about a single column.
    """
    if col == "ProjectKey":
        # A free-text project name is how "1100 Fulton" and "1100 Fulton St" become two
        # projects in a report that then under-counts both. A lookup cannot be misspelled.
        return (f"<Field Type='Lookup' DisplayName='ProjectKey' Name='ProjectKey' "
                f"StaticName='ProjectKey' Required='TRUE' "
                f"List='{{{projects_guid}}}' ShowField='Title' />")

    values = ms.vocab_choices(table, col)
    if values is None and col in ms.CHOICES:
        spec = ms.CHOICES[col]
        values = spec[table] if isinstance(spec, dict) else spec
    if values:
        choices = "".join(f"<CHOICE>{escape(v)}</CHOICE>" for v in values)
        return (f"<Field Type='Choice' DisplayName='{col}' Name='{col}' StaticName='{col}'>"
                f"<CHOICES>{choices}</CHOICES></Field>")

    kind = "Note" if col in ms.MULTILINE else ms.SQL_TO_PNP[sql_type]
    required = " Required='TRUE'" if col == "MonthStart" else ""
    return (f"<Field Type='{kind}' DisplayName='{col}' Name='{col}' StaticName='{col}'"
            f"{required} />")


def create_field(list_title: str, schema: str) -> tuple[str, str, str, dict]:
    return (f"field on {list_title}", "POST",
            f"_api/web/lists/getbytitle('{list_title}')/fields/createfieldasxml", {
                "parameters": {
                    "__metadata": {"type": "SP.XmlSchemaFieldCreationInformation"},
                    "SchemaXml": schema,
                    "Options": 8,  # AddFieldToDefaultView
                },
            })


def site_steps(site_url: str, owner: str) -> list[tuple[str, str, str, dict | None]]:
    """Create the site itself, through SPSiteManager on the tenant root.

    STS#3 is a modern team site with NO Microsoft 365 group behind it. A group-backed site
    would also create a mailbox, a Teams-able group and a membership list nobody asked for,
    for a site whose entire job is to hold 18 intake lists.

    This runs against the tenant root rather than the site being created, for the obvious
    reason. It needs self-service site creation to be enabled, or an account that can create
    sites - if it 403s, make the site by hand in the SharePoint admin centre and re-run
    without --create-site; everything after this point only needs Manage Lists on it.
    """
    return [("create the site", "POST", "_api/SPSiteManager/create", {
        "request": {
            "Title": "Affect Project Reporting",
            "Url": site_url,
            "Lcid": 1033,
            "ShareByEmailEnabled": False,
            "Classification": "",
            "Description": "Manual intake for the Monthly Progress Report and the Project "
                           "Quality Plan. Lists here are generated - see "
                           "_docs/sharepoint-lists.md.",
            "WebTemplate": "STS#3",
            "SiteDesignId": "00000000-0000-0000-0000-000000000000",
            "Owner": owner,
        },
    })]


def list_steps() -> list[tuple[str, str, str, dict | None]]:
    """Phase 1: the 18 lists themselves. CD Projects first - everything points at it."""
    steps = []
    for title in [ms.LOOKUP_LIST] + [ms.list_name(t) for t in ms.tables()]:
        steps.append((f"list {title}", "POST", "_api/web/lists", {
            "__metadata": {"type": "SP.List"},
            "Title": title,
            "BaseTemplate": 100,
            # Versioning is what gives every field change a who and a when - the audit trail
            # the spreadsheet has never had.
            "EnableVersioning": True,
        }))
    return steps


def column_steps(projects_guid: str) -> list[tuple[str, str, str, dict | None]]:
    """Phase 2: 140 columns, plus CD Projects' own two."""
    steps = [
        create_field(ms.LOOKUP_LIST,
                     "<Field Type='Text' DisplayName='ProjectName' Name='ProjectName' "
                     "StaticName='ProjectName' />"),
        create_field(ms.LOOKUP_LIST,
                     "<Field Type='Boolean' DisplayName='IsActive' Name='IsActive' "
                     "StaticName='IsActive' />"),
    ]
    for table, cols in ms.tables().items():
        title = ms.list_name(table)
        for col, sql_type in cols:
            steps.append(create_field(title, field_schema(table, col, sql_type,
                                                          projects_guid)))
    return steps


def project_steps() -> list[tuple[str, str, str, dict | None]]:
    """Phase 3: the 19 real projects, from cd-projects.csv.

    Typing them by hand is 19 chances to transpose a digit, and a wrong id does not error -
    it creates a lookup entry no fact row ever joins to, so the project reports zeros.
    """
    if not PROJECTS_CSV.exists():
        return []
    steps = []
    with PROJECTS_CSV.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            steps.append((f"project {row['ProjectName']}", "POST",
                          f"_api/web/lists/getbytitle('{ms.LOOKUP_LIST}')/items", {
                              "__metadata": {"type": "SP.Data.CD_x0020_ProjectsListItem"},
                              "Title": row["ProjectKey"],
                              "ProjectName": row["ProjectName"],
                              "IsActive": row.get("IsActive", "TRUE").upper() == "TRUE",
                          }))
    return steps


def existing_project_keys(site_id: str, list_id: str, tok: str) -> set[str]:
    """The ProjectKeys already in CD Projects - so the seed does not double them.

    Creating a list or a column FAILS harmlessly when it already exists, which is what
    makes phases 1 and 2 safe to re-run. Creating a list ITEM always succeeds, so phase 3
    had no such protection: every re-run added a second copy of all 19 projects, the batch
    reported Succeeded, and nothing said a word. That happened on 2026-08-19 and left 38
    rows where 19 were real.

    Duplicates are not cosmetic here. ProjectKey is a Lookup at this list, so two rows per
    project make the lookup target ambiguous.
    """
    items = graph(f"/sites/{site_id}/lists/{list_id}/items"
                  f"?$expand=fields($select=Title)&$top=500", tok)
    return {str(x.get("fields", {}).get("Title")) for x in items.get("value", [])}


def site_id(site_url: str, tok: str) -> str:
    host, _, path = site_url.replace("https://", "").partition("/")
    found = graph(f"/sites/{host}:/{path}", tok)
    if "id" not in found:
        raise SystemExit(f"cannot read {site_url} through Graph: {found}")
    return found["id"]


def verify(site_url: str, tok: str) -> int:
    """Read the site back and report what is actually there.

    This exists because neither the run status nor the dry run can answer it. A batch
    reports Succeeded as long as its LAST action did, and the dry run counts only lists -
    it prints every column and project row as outstanding whether or not they landed.
    """
    sid = site_id(site_url, tok)
    have = existing_lists(site_url, tok)
    wanted = {ms.list_name(t): [c for c, _ in cols] for t, cols in ms.tables().items()}
    wanted[ms.LOOKUP_LIST] = ["ProjectName", "IsActive"]

    total_want = total_have = 0
    gaps = []
    for title, cols in sorted(wanted.items()):
        lid = have.get(title)
        if not lid:
            print(f"  MISSING LIST  {title}")
            gaps.append(title)
            continue
        got = graph(f"/sites/{sid}/lists/{lid}/columns?$select=name,displayName", tok)
        names = {c.get("name") for c in got.get("value", [])}
        names |= {c.get("displayName") for c in got.get("value", [])}
        present = [c for c in cols if c in names]
        total_want += len(cols)
        total_have += len(present)
        mark = "ok " if len(present) == len(cols) else "GAP"
        if mark == "GAP":
            gaps.append(title)
        print(f"  {mark} {title:<28} {len(present):>3}/{len(cols)}")

    print(f"\ncolumns: {total_have} of {total_want}")

    lid = have.get(ms.LOOKUP_LIST)
    if lid:
        keys = existing_project_keys(sid, lid, tok)
        rows = graph(f"/sites/{sid}/lists/{lid}/items?$top=500", tok).get("value", [])
        print(f"{ms.LOOKUP_LIST}: {len(rows)} rows, {len(keys)} distinct ProjectKey")
        if len(rows) != len(keys):
            print(f"  DUPLICATES: {len(rows) - len(keys)} surplus row(s). A Lookup with two "
                  f"rows per project is ambiguous - remove the later ones.")
            gaps.append(ms.LOOKUP_LIST)

    print("\nEVERYTHING PRESENT" if not gaps else f"\nINCOMPLETE: {len(gaps)} list(s)")
    return 0 if not gaps else 1


def graph_token() -> str:
    import shutil
    import subprocess
    result = subprocess.run(
        [shutil.which("az"), "account", "get-access-token", "--resource",
         "https://graph.microsoft.com", "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit("no Graph token; run 'az login'")
    return result.stdout.strip()


def graph(url: str, tok: str) -> dict:
    import urllib.error
    import urllib.request
    req = urllib.request.Request(f"https://graph.microsoft.com/v1.0{url}",
                                 headers={"Authorization": f"Bearer {tok}"})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return {"_status": exc.code, "_body": exc.read().decode(errors="replace")[:300]}


def existing_lists(site_url: str, tok: str) -> dict[str, str]:
    """{displayName: list id} - read through Graph, whose reads are not blocked."""
    host, _, path = site_url.replace("https://", "").partition("/")
    site = graph(f"/sites/{host}:/{path}", tok)
    if "id" not in site:
        raise SystemExit(f"cannot read {site_url} through Graph: {site}")
    found = graph(f"/sites/{site['id']}/lists?$select=id,displayName", tok)
    return {x["displayName"]: x["id"] for x in found.get("value", [])}


def run_batch(tok: str, env: str, site: str, connection: str,
              steps: list, label: str) -> str:
    """One helper flow, run to completion, deleted. Returns the run status."""
    import time
    old = find_flow(tok, env, HELPER_NAME)
    if old:
        # REFUSE TO CLOBBER A LIVE RUN. Every batch reuses one helper flow name, so a second
        # copy of this script deletes the first one's flow mid-run - the surviving process
        # then polls a flow that no longer exists and reports FlowNotFound, while the work
        # it was doing is simply gone. That happened, and it looked like the SharePoint calls
        # were hanging when they were being deleted out from under.
        live = [r for r in call("GET", f"/providers/Microsoft.ProcessSimple/environments"
                                       f"/{env}/flows/{old}/runs?api-version=2016-11-01",
                                tok).get("value", [])
                if r.get("properties", {}).get("status") in ("Running", "Waiting")]
        if live:
            raise SystemExit(
                f"a helper flow run is still going ({live[0]['name']}).\n"
                "Another copy of this script is probably running - wait for it, or clear it\n"
                "with --cleanup if you know it is orphaned."
            )
        call("DELETE", f"/providers/Microsoft.ProcessSimple/environments/{env}"
                       f"/flows/{old}?api-version=2016-11-01", tok)
    created = call("POST", f"/providers/Microsoft.ProcessSimple/environments/{env}"
                           f"/flows?api-version=2016-11-01", tok, {
        "properties": {
            "displayName": HELPER_NAME,
            "definition": build_definition(site, steps),
            "connectionReferences": {"shared_sharepointonline": {
                "connectionName": connection, "source": "Embedded", "id": SHAREPOINT_API}},
            "state": "Started",
        }})
    flow_id = created["name"]
    status, payload = try_call(
        "POST", f"/providers/Microsoft.ProcessSimple/environments/{env}"
                f"/flows/{flow_id}/triggers/manual/run?api-version=2016-11-01", tok, {})
    if status >= 400:
        raise SystemExit(f"could not run {label}\n  HTTP {status}\n  {str(payload)[:600]}")

    outcome = "unknown"
    for _ in range(120):
        time.sleep(5)
        runs = call("GET", f"/providers/Microsoft.ProcessSimple/environments/{env}"
                           f"/flows/{flow_id}/runs?api-version=2016-11-01",
                    tok).get("value", [])
        if runs:
            outcome = runs[0].get("properties", {}).get("status", "unknown")
            if outcome not in ("Running", "Waiting"):
                break
    # THE RUN STATUS IS NOT THE ANSWER, and trusting it hid a whole batch doing nothing.
    #
    # Every action here runs after the previous one on Succeeded OR Failed, so that an
    # "already exists" error does not abandon the thirty steps behind it. The cost is that
    # the RUN reports Succeeded as long as the last action did - eighteen failures in a row
    # still come back green. So the per-action results are what get read.
    failed = []
    if runs:
        run_id = runs[0]["name"]
        detail = call("GET", f"/providers/Microsoft.ProcessSimple/environments/{env}"
                             f"/flows/{flow_id}/runs/{run_id}/actions"
                             f"?api-version=2016-11-01", tok).get("value", [])
        for action in detail:
            props = action.get("properties", {})
            # A connector action that keeps getting 502 sits in Running, not Failed - the
            # SharePoint connector retries BadGateway silently. Reported too, or a batch
            # that is quietly retrying looks identical to one making progress.
            if props.get("status") == "Running" and props.get("code"):
                failed.append(f"{action.get('name')}: still Running, last code "
                              f"{props.get('code')} - the connector is retrying")
            if props.get("status") == "Failed":
                err = props.get("error", {})
                failed.append(f"{action.get('name')}: "
                              f"{err.get('code', '?')} {str(err.get('message', ''))[:160]}")
    print(f"  {label}: {outcome}"
          + (f"  ({len(failed)}/{len(steps)} actions failed)" if failed else ""))
    for line in failed[:4]:
        print(f"      {line}")
    if len(failed) > 4:
        print(f"      ... and {len(failed) - 4} more")

    call("DELETE", f"/providers/Microsoft.ProcessSimple/environments/{env}"
                   f"/flows/{flow_id}?api-version=2016-11-01", tok)
    return outcome


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-url", required=True)
    parser.add_argument("--connection", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--verify", action="store_true",
                        help="read the site back through Graph and report what is actually "
                             "there - the run status and the dry run cannot tell you")
    parser.add_argument("--probe", action="store_true",
                        help="one GET against the site, to see whether SharePoint serves it "
                             "yet - answers in under a minute instead of ten")
    parser.add_argument("--create-site", action="store_true",
                        help="create the site first (needs rights to create sites)")
    parser.add_argument("--owner", help="site owner UPN, required with --create-site")
    args = parser.parse_args()

    tok = token()
    env = environment(tok)
    site = args.site_url.rstrip("/")
    print(f"environment: {env}")
    print(f"site:        {site}\n")

    if args.cleanup:
        old = find_flow(tok, env, HELPER_NAME)
        if old:
            call("DELETE", f"/providers/Microsoft.ProcessSimple/environments/{env}"
                           f"/flows/{old}?api-version=2016-11-01", tok)
            print("deleted the helper flow")
        else:
            print("no helper flow to delete")
        return 0

    if args.verify:
        # Reads only, through Graph, and no helper flow - so it is safe to run at any time,
        # including while another copy of this script is mid-batch.
        return verify(site, graph_token())

    if args.probe:
        # ONE call, not eighteen. A newly created site returns 502 from SharePoint while
        # Graph reads it perfectly well, and the connector retries 502 silently - so the
        # only cheap way to ask "is it serving yet" is to make one request and read the
        # action's code. A full batch takes ten minutes to report the same thing.
        outcome = run_batch(tok, env, site, args.connection,
                            [("probe the site", "GET", "_api/web", None)], "probe")
        print("\nSucceeded means SharePoint is serving the site and the real run will work.")
        print("A BadGateway code above means it is not ready yet - wait and probe again.")
        return 0

    gtok = graph_token()

    if args.create_site:
        if not args.owner:
            raise SystemExit("--owner is required with --create-site, e.g. "
                             "--owner someone@yourtenant.com")
        root = "/".join(site.split("/")[:3])
        if not args.apply:
            print(f"would create the site at {site} (owner {args.owner})\n")
        else:
            run_batch(tok, env, root, args.connection,
                      site_steps(site, args.owner), "create site")
            import time
            print("  waiting for the site to come up", end="", flush=True)
            host, _, path = site.replace("https://", "").partition("/")
            for _ in range(24):
                time.sleep(10)
                print(".", end="", flush=True)
                if "id" in graph(f"/sites/{host}:/{path}", gtok):
                    break
            print()

    site_ready = "id" in graph(
        f"/sites/{site.replace('https://', '').partition('/')[0]}:"
        f"/{site.replace('https://', '').partition('/')[2]}", gtok)
    if not site_ready:
        raise SystemExit(
            f"{site} does not exist yet.\n"
            "Create it with --create-site --owner <upn>, or make it by hand in SharePoint\n"
            "(Create site -> Team site) and re-run without --create-site.")

    have = existing_lists(site, gtok)
    lists = list_steps()
    wanted = [s[0].removeprefix("list ") for s in lists]
    missing = [t for t in wanted if t not in have]

    print(f"lists: {len(wanted)} wanted, {len(wanted) - len(missing)} already there")
    if not args.apply:
        print(f"\nwould create {len(missing)} list(s), "
              f"{len(column_steps('00000000-0000-0000-0000-000000000000'))} column(s), "
              f"{len(project_steps())} project row(s)")
        print("\nDRY RUN - nothing created. Re-run with --apply.")
        return 0

    if missing:
        todo = [s for s in lists if s[0].removeprefix("list ") in missing]
        for start in range(0, len(todo), BATCH):
            run_batch(tok, env, site, args.connection, todo[start:start + BATCH],
                      f"lists {start + 1}-{min(start + BATCH, len(todo))}")
        have = existing_lists(site, gtok)

    if ms.LOOKUP_LIST not in have:
        raise SystemExit(f"{ms.LOOKUP_LIST} still does not exist - the lookup columns "
                         f"cannot be built without it")
    # Graph's list id IS the SharePoint list GUID, which is what a Lookup field needs.
    projects_guid = have[ms.LOOKUP_LIST]
    print(f"\n{ms.LOOKUP_LIST} guid: {projects_guid}")

    columns = column_steps(projects_guid)
    print(f"columns: {len(columns)}")
    for start in range(0, len(columns), BATCH):
        run_batch(tok, env, site, args.connection, columns[start:start + BATCH],
                  f"columns {start + 1}-{min(start + BATCH, len(columns))}")

    projects = project_steps()
    already = existing_project_keys(site_id(site, gtok), projects_guid, gtok)
    if already:
        before = len(projects)
        projects = [s for s in projects if s[3]["Title"] not in already]
        print(f"\nprojects: {before - len(projects)} already present, skipped")
    if projects:
        print(f"\nprojects: {len(projects)}")
        for start in range(0, len(projects), BATCH):
            run_batch(tok, env, site, args.connection, projects[start:start + BATCH],
                      f"projects {start + 1}-{min(start + BATCH, len(projects))}")

    print("\nA batch reports Failed if ANY step in it failed, and a step fails when the")
    print("thing it creates already exists - so Failed is expected on a re-run.")
    print("\nThe run status is NOT the verification, and neither is the dry run: a batch")
    print("reports Succeeded as long as its last action did, and the dry run counts only")
    print("lists. Read the site back instead:")
    print(f"  python bootstrap_reporting_site.py --site-url {site} "
          f"--connection {args.connection} --verify")
    return 0


if __name__ == "__main__":
    sys.exit(main())
