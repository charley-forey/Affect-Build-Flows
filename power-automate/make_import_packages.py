"""Wrap the flow definitions into Power Automate legacy import packages (.zip).

    python make_import_packages.py            # write dist/*.zip
    python make_import_packages.py --check    # validate structure, write nothing

WHY THIS EXISTS.

flows/*.json are workflow DEFINITIONS - the `triggers` / `actions` / `parameters` object.
That is the right thing to keep in git: it is what you review in a diff, and it is what
test_flows.py asserts against.

It is not a thing Power Automate will import. The UI offers exactly two doors:

    Import Solution (Dataverse)   wants a Dataverse solution .zip
    Import Package (Legacy)       wants a legacy package .zip

and neither takes a bare definition. An earlier version of RUNBOOK.md said to paste the
definition into "the designer's code view", which does not exist in the current designer -
there is no way to paste a whole definition into a flow through the UI at all.

So this builds the second one. A legacy package is a zip of:

    manifest.json                                    what is in the package
    Microsoft.Flow/flows/<name>/definition.json      the flow itself

The Dataverse route was not taken because it needs a solution, a publisher and a Dataverse
database in the target environment - three things to get right before the first import,
where this needs none. If these flows later go into ALM, that is when the solution wrapper
earns its keep; it can be built from the same definitions.

NO ADMIN CONSENT IS INVOLVED. Importing a package is an ordinary user action. The consent
step in RUNBOOK.md belongs to PnP PowerShell and the SharePoint provisioning, which is a
separate problem - see step 0 there.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FLOWS = HERE / "flows"
DIST = HERE / "dist"

# The one connector both flows use. CreateCopyJobs is reached through "Send an HTTP request
# to SharePoint", which is part of this standard connector - NOT the premium HTTP connector.
# That is what keeps the whole solution off per-user premium licensing, and it is why this
# list has one entry rather than two.
SHAREPOINT_API = "/providers/Microsoft.PowerApps/apis/shared_sharepointonline"
SHAREPOINT_ICON = (
    "https://connectoricons-prod.azureedge.net/releases/v1.0.1664/1.0.1664.3477/"
    "sharepointonline/icon.png"
)

# Deterministic ids, uuid5 of the flow name, for the same reason make_sharepoint.py does it:
# regenerating produces a byte-identical package, so --check means something and a rebuilt
# zip is not a spurious change.
NS = uuid.UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")

PACKAGES = {
    "EstimatingSetup": "Estimating Setup",
    "ConvertToBidding": "Convert to Bidding",
}


def flow_id(stem: str) -> str:
    return str(uuid.uuid5(NS, f"affect-build-flows/{stem}"))


def manifest(stem: str, display: str, description: str) -> dict:
    """The package's table of contents.

    `creationType` lists what the import UI may offer; `suggestedCreationType` is what it
    preselects. The flow is "New" so an import cannot silently overwrite a flow somebody has
    since edited by hand - re-importing gives you a second flow to compare, which is
    recoverable, where an accidental Update is not.

    The connector is "Existing" because a connection is a credential. It cannot travel in a
    package and must be picked, or created, in the target tenant at import time.
    """
    return {
        "schema": "1.0",
        "details": {
            "displayName": display,
            "description": description,
            "createdTime": "2026-08-19T00:00:00.000Z",
            "packageTelemetryId": str(uuid.uuid5(NS, f"telemetry/{stem}")),
            "creator": "",
            "sourceEnvironment": "",
        },
        "resources": {
            str(uuid.uuid5(NS, f"res/flow/{stem}")): {
                "id": None,
                "name": flow_id(stem),
                "type": "Microsoft.Flow/flows",
                "suggestedCreationType": "New",
                "creationType": "New, Existing, Update",
                "details": {"displayName": display},
                "configurableBy": "User",
                "hierarchy": "Root",
                "dependsOn": [str(uuid.uuid5(NS, f"res/api/{stem}"))],
            },
            str(uuid.uuid5(NS, f"res/api/{stem}")): {
                "id": SHAREPOINT_API,
                "name": "shared_sharepointonline",
                "type": "Microsoft.PowerApps/apis",
                "suggestedCreationType": "Existing",
                "creationType": "Existing",
                "details": {
                    "displayName": "SharePoint",
                    "iconUri": SHAREPOINT_ICON,
                    "environmentName": "",
                    "type": "Microsoft.PowerApps/apis",
                },
                "configurableBy": "System",
                "hierarchy": "Child",
                "dependsOn": [],
            },
        },
    }


def flow_resource(stem: str, display: str, definition: dict) -> dict:
    """The flow itself, definition included verbatim.

    `source: "Invoker"` on the connection reference means "whoever imports this picks the
    connection", which is the only correct answer for a package crossing tenants.
    """
    return {
        "name": flow_id(stem),
        "id": f"/providers/Microsoft.Flow/flows/{flow_id(stem)}",
        "type": "Microsoft.Flow/flows",
        "properties": {
            "apiId": "/providers/Microsoft.PowerApps/apis/shared_logicflows",
            "displayName": display,
            "definition": definition,
            "connectionReferences": {
                "shared_sharepointonline": {
                    "connectionName": "shared_sharepointonline",
                    "source": "Invoker",
                    "id": SHAREPOINT_API,
                    "tier": "NotSpecified",
                },
            },
            "flowFailureAlertSubscribed": False,
        },
        "schemaVersion": "1.0.0.0",
    }


def check_definition(stem: str, definition: dict) -> list[str]:
    """Whatever the import UI will not tell you until after it has failed."""
    problems = []
    if "triggers" not in definition or not definition["triggers"]:
        problems.append(f"{stem}: no trigger")
    for name, trigger in definition.get("triggers", {}).items():
        # The setting the whole solution's correctness rests on. It lives inside the
        # definition, so it travels in the package - but only if it is still there.
        runs = (trigger.get("runtimeConfiguration", {})
                       .get("concurrency", {})
                       .get("runs"))
        if runs != 1:
            problems.append(
                f"{stem}: trigger {name} has concurrency {runs!r}, expected 1 - "
                f"two runs could issue the same job number"
            )
    params = definition.get("parameters", {})
    for required in ("$connections", "$authentication"):
        if required not in params:
            problems.append(f"{stem}: definition is missing the {required} parameter")
    return problems


def build(stem: str, display: str, site_url: str | None) -> tuple[dict, dict, dict]:
    source = json.loads((FLOWS / f"{stem}.json").read_text(encoding="utf-8"))
    description = source.get("description", display)
    # The package carries the workflow definition, which is the source file minus the
    # metadata keys that describe the FILE rather than the workflow.
    definition = {k: v for k, v in source.items()
                  if k not in ("description",)}

    # THE SITE URL HAS TO BE RIGHT BEFORE THE PACKAGE IS BUILT, not after the import.
    #
    # SiteUrl is a DEFINITION parameter, and the Power Automate designer gives you no way to
    # edit those - they are not the "flow parameters" the UI exposes. So a package built with
    # the placeholder imports cleanly, appears to work, and every run fails against a host
    # called REPLACE-ME with nowhere in the UI to correct it.
    if site_url is not None:
        definition["parameters"]["SiteUrl"]["defaultValue"] = site_url.rstrip("/")

    return (manifest(stem, display, description),
            flow_resource(stem, display, definition),
            definition)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="validate the definitions and the built package, write nothing")
    parser.add_argument("--site-url",
                        help="the real BUILD site, e.g. "
                             "https://contoso.sharepoint.com/sites/BUILD. Baked into the "
                             "package, because the designer cannot edit it afterwards")
    parser.add_argument("--allow-placeholder", action="store_true",
                        help="build with the REPLACE-ME site anyway (for offline checks)")
    args = parser.parse_args()

    # Same refusal as provision-sharepoint-build.ps1, for the same reason: shipping the
    # placeholder produces something that looks finished and cannot work.
    if not args.site_url and not (args.allow_placeholder or args.check):
        print("--site-url is required. The URL is baked into the package because the Power\n"
              "Automate designer cannot edit a definition parameter after import.\n"
              "Pass --allow-placeholder to build with REPLACE-ME anyway.")
        return 2

    problems: list[str] = []
    built: list[tuple[str, bytes]] = []

    for stem, display in PACKAGES.items():
        man, resource, definition = build(stem, display, args.site_url)
        problems += check_definition(stem, definition)

        import io
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            # TWO COPIES OF THE SAME MANIFEST, and this is not belt-and-braces.
            #
            # The import UI reads the ROOT manifest.json to render the review screen - it
            # showed the flow's name, description and "Create as new" correctly from it. The
            # import ITSELF then reads a second one and fails without it:
            #
            #   MissingPackageManifest: The package manifest file 'manifest.json' under
            #   'Microsoft.Flow' folder missing.
            #
            # Two code paths, two locations, same file. Writing the byte-identical content to
            # both is the whole fix; the content was never wrong.
            z.writestr("manifest.json", json.dumps(man, indent=2))
            z.writestr("Microsoft.Flow/manifest.json", json.dumps(man, indent=2))
            z.writestr(
                f"Microsoft.Flow/flows/{flow_id(stem)}/definition.json",
                json.dumps(resource, indent=2),
            )
        built.append((f"{stem}.zip", buf.getvalue()))

        # Read the zip back. A package that does not round-trip is one the import UI
        # rejects with "The package is invalid", which says nothing about why.
        with zipfile.ZipFile(io.BytesIO(buf.getvalue())) as z:
            names = set(z.namelist())
            expected = {"manifest.json",
                        "Microsoft.Flow/manifest.json",
                        f"Microsoft.Flow/flows/{flow_id(stem)}/definition.json"}
            if names != expected:
                problems.append(f"{stem}: package holds {sorted(names)}")
            for entry in names:
                json.loads(z.read(entry))  # raises if either file is not valid JSON

    if problems:
        for p in problems:
            print(f"  FAIL  {p}")
        return 1

    if args.check:
        print(f"{len(built)} package(s) valid")
        return 0

    DIST.mkdir(exist_ok=True)
    for name, data in built:
        (DIST / name).write_bytes(data)
        print(f"wrote dist/{name}  ({len(data):,} bytes)")
    print(f"\nsite: {args.site_url or 'REPLACE-ME (placeholder - these will not run)'}")
    print("Import each at: Power Automate -> My flows -> Import -> Import Package (Legacy)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
