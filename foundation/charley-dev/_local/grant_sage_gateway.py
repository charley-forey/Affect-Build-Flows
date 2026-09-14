"""Grant "Can use" on the Sage gateway datasource, acting as the gateway's own admin.

    python grant_sage_gateway.py                    # READ-ONLY. List gateways/datasources.
    python grant_sage_gateway.py --take-ownership   # PREFERRED - see below
    python grant_sage_gateway.py --grant            # add "Can use" for GRANTEE

PREFER --take-ownership OVER --grant
------------------------------------
A Dataflow Gen2 runs as its OWNER. `fabricconnector@` already holds gateway rights, so
making it the owner of CD_Sage_Ingest dissolves the permission problem instead of answering
it: there is no ACL entry to maintain and no named person in the data path to break when
they leave the engagement. `--grant` ties Sage to whoever is named in --grantee, which is a
consultant's account by default, and that is a grant somebody has to redo later.

--take-ownership needs two things first, both the Affect reporting lead's to do and neither ours:

  1. the gateway service account added to the **Build** workspace (Contributor)
  2. a **Power BI Pro** license on it - section 10 of the handoff records it as having
     none, and on F2 (below F64) any account that runs shared content needs Pro, $14/month

Until those land, --take-ownership returns 401/403. That means "ask the Affect reporting lead", not "broken".

WHY THIS EXISTS
---------------
CD_Sage_Ingest is deployed, correct and inert. It fails in about five seconds because
The build account cannot see any gateway in the tenant - GET /gateways and
GET /connections both return 0 - so the dataflow asks to run through a gateway it has no
rights on. The fix is one ACL entry, and it has been the single outstanding ask since
2026-08-02.

The Nerds That Care handoff (2026-05-20) records that the gateway is registered to
the gateway service account. In Fabric the registering account IS the gateway admin,
and nothing in that document grants gateway-admin rights to any human - not the Affect reporting lead, not
any other Affect staff member. So this service account is, as far as we can tell, the only identity in the tenant
that can make the grant.

Its password is in AffectKeyVault, put there by Affect's own technical lead on 2026-08-22.

WHAT THIS TOUCHES, AND WHAT IT DOES NOT
---------------------------------------
Without --grant it is strictly read-only: acquire a token, list gateways and datasources.
Nothing is written. Run it that way first.

With --grant it makes exactly ONE write: adds GRANTEE as "Can use" (datasourceAccessRight
"Read") on the Affect Group datasource. It does not change the service account's password,
does not touch the gateway registration, does not modify the datasource credential, and
does not alter Build_Sage_Test or anything else.

THE ONE REAL RISK, STATED PLAINLY
---------------------------------
Section 7 of the handoff: if this account's password changes without the gateway being
reconfigured on the server, THE GATEWAY GOES OFFLINE - and the Affect reporting lead's existing Sage
reporting stops with it. This script never changes the password. But a service account's
first interactive sign-in can be met with a forced MFA-registration or password-change
prompt. If you see one: STOP. Do not complete it. Close it and tell Nerds That Care.
A refused sign-in costs nothing; a completed prompt costs the client's live reporting.

WHY THE DATASOURCE ID IS NOT THE ONE IN THE HANDOFF
---------------------------------------------------
The handoff documents `Sage100-SQL-Connection` against database ABMI. That database was a
guess and it is the wrong one - its own section 12 says so. `Affect Group` is correct on
the evidence: it yields Sage job numbers resolving to 15 of the 16 real Procore projects
carrying $22.5M of AR. So the grant targets the datasource CD_Sage_Ingest is actually
bound to, which is the one Build_Sage_Test already uses.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request

TENANT = "b2a2225b-4b4e-42ec-ba52-c7e1c2dea580"
VAULT = "AffectKeyVault"

# The public Azure CLI client id. Standard for a resource-owner password grant; using it
# means no new app registration has to be created just to make one ACL entry.
AZ_CLI_CLIENT = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"

GATEWAY_ID = "1e798beb-cc0f-4f72-bb1e-9c8fca8ba03e"
DATASOURCE_ID = "835e72c8-7995-4171-91cb-2a32fbd2050a"   # nc-affect-1\sage100con;Affect Group

WORKSPACE_ID = "1f7caed6-f88a-4e52-bc83-9a498a165301"    # Build
DATAFLOW_ID = "9d1dc6db-405b-4cc6-bd3e-a8fdb8795ab8"     # CD_Sage_Ingest

GRANTEE = "cforey-c@affect-group.com"

PBI = "https://api.powerbi.com/v1.0/myorg"


def az() -> str:
    for candidate in ("az", "az.cmd", "az.bat", "az.exe"):
        found = shutil.which(candidate)
        if found:
            return found
    raise SystemExit("Azure CLI not found on PATH.")


def secret(name: str) -> str:
    result = subprocess.run(
        [az(), "keyvault", "secret", "show", "--vault-name", VAULT,
         "--name", name, "--query", "value", "-o", "tsv"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"cannot read {name} from {VAULT}: {result.stderr.strip()[:300]}")
    return result.stdout.strip()


def token(username: str, password: str) -> str:
    """Sign in as the service account. The password is never printed or passed via argv."""
    body = urllib.parse.urlencode({
        "client_id": AZ_CLI_CLIENT,
        "scope": "https://analysis.windows.net/powerbi/api/.default",
        "username": username,
        "password": password,
        "grant_type": "password",
    }).encode()
    request = urllib.request.Request(
        f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/token",
        data=body, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read())["access_token"]
    except urllib.error.HTTPError as exc:
        err = json.loads(exc.read())
        code = err.get("error")
        print(f"\nSIGN-IN FAILED: {code}")
        print(f"  {err.get('error_description', '')[:500]}")
        if code == "invalid_grant":
            print("\n  If this mentions MFA or a required password change, STOP HERE.")
            print("  Do not satisfy the prompt interactively - completing a password change")
            print("  takes the gateway offline (handoff section 7) and stops Rebecca's Sage")
            print("  reporting. Hand this back to Nerds That Care instead.")
        raise SystemExit(1)


def call(method: str, path: str, tok: str, body: dict | None = None):
    request = urllib.request.Request(
        f"{PBI}{path}", method=method,
        data=json.dumps(body).encode() if body else None,
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode()
            return response.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"{method} {path} -> {exc.code}\n{exc.read().decode()[:400]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--grant", action="store_true",
                        help="make the ONE write: add the Can use grant")
    parser.add_argument("--grantee", default=GRANTEE)
    parser.add_argument("--take-ownership", action="store_true",
                        help="make this service account the OWNER of CD_Sage_Ingest, so the "
                             "dataflow runs as the identity that already holds gateway "
                             "rights and no named person is in the path at all")
    args = parser.parse_args()

    user = secret("Fabric-Gateway-Service-Account-Username")
    pwd = secret("Fabric-Gateway-Service-Account-Password")
    print(f"signing in as {user}  (password {len(pwd)} chars, not shown)")

    tok = token(user, pwd)
    print("  token acquired - no MFA or password-change prompt\n")

    status, body = call("GET", "/gateways", tok)
    gateways = body.get("value", [])
    print(f"gateways visible to this account: {len(gateways)}")
    for gateway in gateways:
        marker = "  <-- Sage" if gateway.get("id") == GATEWAY_ID else ""
        print(f"  {gateway.get('id')}  {gateway.get('name')}{marker}")

    if not any(g.get("id") == GATEWAY_ID for g in gateways):
        print(f"\nGateway {GATEWAY_ID} is NOT visible even to the registering account.")
        print("That contradicts the handoff document. Stop and re-check with Nerds That Care.")
        return 1

    status, body = call("GET", f"/gateways/{GATEWAY_ID}/datasources", tok)
    sources = body.get("value", [])
    print(f"\ndatasources on the Sage gateway: {len(sources)}")
    for source in sources:
        details = source.get("connectionDetails", "")
        marker = "  <-- CD_Sage_Ingest is bound to this" if source.get("id") == DATASOURCE_ID else ""
        print(f"  {source.get('id')}  {source.get('datasourceName', '')}  {details}{marker}")

    status, body = call("GET", f"/gateways/{GATEWAY_ID}/datasources/{DATASOURCE_ID}/users", tok)
    users = body.get("value", [])
    print(f"\ncurrent users on the Affect Group datasource: {len(users)}")
    for u in users:
        print(f"  {u.get('emailAddress') or u.get('identifier')}  {u.get('datasourceAccessRight')}")

    if any((u.get("emailAddress") or "").lower() == args.grantee.lower() for u in users):
        print(f"\n{args.grantee} ALREADY has access. Nothing to do.")
        return 0

    if args.take_ownership:
        # The durable answer, and the reason this beats --grant: a Dataflow Gen2 runs as its
        # OWNER. Make the owner the account that already holds gateway rights and the
        # permission question disappears rather than being answered - no "Can use" entry to
        # maintain, and no named consultant in the data path to break when they leave.
        #
        # Needs two things first, both the Affect reporting lead's to do and neither ours:
        #   1. fabricconnector@ added to the Build workspace (Contributor or Member)
        #   2. a Power BI Pro license on it - section 10 records it as having none, and on
        #      F2, which is below F64, any account that runs shared content needs Pro
        # Without those this returns 401 or 403, which means "ask the Affect reporting lead", not "broken".
        #
        # UNVERIFIED FOR GEN2. Default.Takeover is the Power BI dataflow API, and Gen2 items
        # do not appear on that surface at all: GET /groups/{id}/dataflows returns an empty
        # list for this workspace on 2026-08-25 while CD_Sage_Ingest plainly exists. So this
        # may well 404. The portal is the route that is known to work - workspace item list,
        # the item's "..." menu. Treat a failure here as "use the portal", not as a problem
        # with the account.
        status, _ = call("POST",
                         f"/groups/{WORKSPACE_ID}/dataflows/{DATAFLOW_ID}/Default.Takeover",
                         tok)
        print(f"\nOWNERSHIP TAKEN: CD_Sage_Ingest is now owned by {user}")
        print("The dataflow now runs as the identity that already holds gateway rights.")
        print("Nothing in the Sage path is tied to a named person.")
        return 0

    if not args.grant:
        print("\nREAD-ONLY. Nothing was written.")
        print(f"Re-run with --grant to add {args.grantee} as \"Can use\",")
        print("or --take-ownership to hand CD_Sage_Ingest to this service account instead")
        print("(preferred - see the module docstring).")
        return 0

    call("POST", f"/gateways/{GATEWAY_ID}/datasources/{DATASOURCE_ID}/users", tok, {
        "identifier": args.grantee,
        "datasourceAccessRight": "Read",     # "Read" is what the portal calls "Can use"
        "principalType": "User",
    })
    print(f"\nGRANTED: {args.grantee} -> Can use on the Affect Group datasource")

    status, body = call("GET", f"/gateways/{GATEWAY_ID}/datasources/{DATASOURCE_ID}/users", tok)
    print("users now:")
    for u in body.get("value", []):
        print(f"  {u.get('emailAddress') or u.get('identifier')}  {u.get('datasourceAccessRight')}")
    print("\nNext: refresh CD_Sage_Ingest. It has been correct and inert since 2026-08-02.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
