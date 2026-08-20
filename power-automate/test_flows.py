"""The two flows and the provisioning script have to agree, offline, before anyone imports them.

Everything these flows do that can go quietly wrong goes wrong the same way: a folder is
created, or is not, and the Job Register row says something that is not true. The checks
here are the ones where a mistake would look fine in review and only surface in the client's
tenant - a column the flow writes that the script never created, a padding width that turns
job 5 into 26-05, a sanitiser missing one forbidden character, a trigger whose concurrency
silently defaults back to unlimited.

Nothing here needs SharePoint, Power Automate or a network: it reads the committed files.

Run:  python power-automate/test_flows.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FLOWS = {
    "EstimatingSetup": HERE / "flows" / "EstimatingSetup.json",
    "ConvertToBidding": HERE / "flows" / "ConvertToBidding.json",
}
PS1 = HERE / "provision-sharepoint-build.ps1"

# Columns every SharePoint list has. The script does not create these and must not.
BUILT_IN = {"ID", "Title", "Created", "Modified", "Author", "Editor", "value"}

# The nine SharePoint forbids in a folder name. # and % are legal on modern SharePoint but
# still break older sync clients and hand-typed links, so they are stripped too.
FORBIDDEN = set('"*:<>?/\\|')
ALSO_STRIPPED = set("#%")

CHECKS: list[str] = []


def check(label: str) -> None:
    CHECKS.append(label)


def load(name: str) -> dict:
    return json.loads(FLOWS[name].read_text(encoding="utf-8"))


def walk(node, out: list[dict]) -> list[dict]:
    """Every action dict anywhere in the definition, scopes and conditions included."""
    if isinstance(node, dict):
        if "type" in node and isinstance(node.get("type"), str) and "inputs" in node:
            out.append(node)
        for v in node.values():
            walk(v, out)
    elif isinstance(node, list):
        for v in node:
            walk(v, out)
    return out


def find_action(flow: dict, name: str) -> dict:
    """Locate an action by key anywhere in the tree - actions nest inside scopes and ifs."""
    stack = [flow]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            if name in node and isinstance(node[name], dict) and "type" in node[name]:
                return node[name]
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    raise AssertionError(f"action {name} not found")


# ---------------------------------------------------------------------------
def test_both_flows_parse() -> None:
    for name, path in FLOWS.items():
        assert path.exists(), f"{path.name} does not exist"
        flow = load(name)
        for key in ("$schema", "contentVersion", "parameters", "triggers", "actions", "outputs"):
            assert key in flow, f"{name}: definition has no {key}"
        assert len(flow["triggers"]) == 1, f"{name}: expected exactly one trigger"
    check("both flow definitions parse and carry the workflow-definition keys")


def test_concurrency_is_one() -> None:
    """The single most likely production bug, and it is a setting rather than code.

    Two people request a job in the same minute, both runs read the same max(JobSeq), both
    get 25, and two different projects are called 26-025. Nothing errors. Nobody notices
    until someone opens the wrong folder. Degree of parallelism 1 serialises the runs, which
    is what makes the read-max-then-write pattern safe at all.
    """
    for name in FLOWS:
        trigger = next(iter(load(name)["triggers"].values()))
        runs = trigger.get("runtimeConfiguration", {}).get("concurrency", {}).get("runs")
        assert runs == 1, (
            f"{name}: trigger concurrency is {runs!r}, must be 1. "
            "Without it two requests race for the same JobSeq and both win."
        )
    check("trigger concurrency control is 1 on both flows")


def test_sanitiser_strips_every_forbidden_character() -> None:
    """Pull the replace() chain out of the flow and actually run it."""
    expr = find_action(load("EstimatingSetup"), "Sanitise_Project_Name")["inputs"]
    pairs = re.findall(r",'(.)',''", expr)
    assert pairs, "Sanitise_Project_Name has no replace(x, 'c', '') pairs"

    stripped = set(pairs)
    missing = FORBIDDEN - stripped
    assert not missing, f"sanitiser never strips {sorted(missing)}"
    assert not (ALSO_STRIPPED - stripped), f"sanitiser never strips {sorted(ALSO_STRIPPED - stripped)}"

    # Apply the extracted chain to a name containing every one of them.
    probe = '  .A" * : < > ? / \\ | # % Tower  '
    result = probe
    for c in pairs:
        result = result.replace(c, "")
    result = result.strip()
    assert not (set(result) & (FORBIDDEN | ALSO_STRIPPED)), f"survivors in {result!r}"
    assert "A" in result and "Tower" in result, f"sanitiser ate legitimate characters: {result!r}"
    assert not result.endswith(" ") and not result.startswith(" ")
    check(f"sanitiser strips all {len(FORBIDDEN | ALSO_STRIPPED)} forbidden characters and keeps the rest")


def test_leading_and_trailing_dots_are_handled() -> None:
    """Stripping the forbidden set leaves '.Tower.' intact, and SharePoint rejects it."""
    flow = load("EstimatingSetup")
    for i in (1, 2, 3):
        expr = find_action(flow, f"Strip_Dot_{i}")["inputs"]
        assert "endsWith" in expr and "'.'" in expr, f"Strip_Dot_{i} does not test for a trailing dot"

    guard = json.dumps(find_action(flow, "Validate_Name")["expression"])
    assert "endsWith" in guard and "startsWith" in guard, (
        "Validate_Name must reject a name that still starts or ends with a dot after three "
        "strip passes - otherwise SharePoint rejects the folder create mid-run"
    )
    check("trailing dots are stripped three deep, then a leading or trailing dot fails validation")


def test_job_number_format() -> None:
    """26-025, never 26-25 and never 26-0025. The padding width is the whole test."""
    expr = find_action(load("EstimatingSetup"), "Job_Number")["inputs"]
    assert "formatDateTime(utcNow(), 'yy')" in expr, "year is not the two-digit yy"
    assert "'000'" in expr, "sequence is not padded to exactly three digits"
    assert "'00'" not in expr.replace("'000'", ""), "found a second, wrong padding width"
    assert "', '-', '" in expr or "'-'" in expr, "no '-' separator between year and sequence"

    # Reproduce the format and hold it to the SOP's YY-### exactly.
    def job_number(yy: int, seq: int) -> str:
        return f"{yy:02d}-{seq:03d}"

    for yy, seq, want in ((26, 1, "26-001"), (26, 25, "26-025"), (26, 999, "26-999"), (7, 5, "07-005")):
        got = job_number(yy, seq)
        assert got == want, f"{got} != {want}"
        assert re.fullmatch(r"\d{2}-\d{3}", got), f"{got} is not YY-###"

    # Known ceiling: 1000 jobs in one year overflows the three-digit format. The SOP has no
    # answer for that and neither does this flow - it would produce 26-1000, which still
    # sorts and still parses, but is no longer YY-###.
    assert not re.fullmatch(r"\d{2}-\d{3}", job_number(26, 1000))
    check("job number is exactly YY-### for 1..999 (1000 in one year would overflow)")


def test_e_prefix_drop() -> None:
    """E-26-025-Riverside Depot -> 26-025-Riverside Depot. Offset 2, not 1 and not 3."""
    expr = find_action(load("ConvertToBidding"), "Project_Folder_Name")["inputs"]
    m = re.search(r"substring\(outputs\('Matching_Estimating_Folder'\)\?\['Name'\],\s*(\d+)\)", expr)
    assert m, f"Project_Folder_Name is not a substring of the estimating folder name: {expr}"
    offset = int(m.group(1))
    assert offset == 2, f"substring offset is {offset}, must be 2 to drop exactly 'E-'"

    for src, want in (
        ("E-26-025-Riverside Depot", "26-025-Riverside Depot"),
        ("E-07-001-A", "07-001-A"),
        ("E-26-999-Depot E-Wing", "26-999-Depot E-Wing"),  # only the LEADING E- goes
    ):
        assert src[offset:] == want, f"{src[offset:]} != {want}"

    guard = json.dumps(find_action(load("ConvertToBidding"), "Validate_Prefix")["expression"])
    assert "startsWith" in guard and "E-" in guard, (
        "Validate_Prefix must confirm the name starts with 'E-' before substring(name, 2) "
        "silently eats two real characters"
    )
    check("dropping the 'E-' prefix yields YY-###-Project Name, and the prefix is verified first")


def test_ps1_provisions_every_column_the_flows_write() -> None:
    script = PS1.read_text(encoding="utf-8")
    provisioned = set(re.findall(r"-InternalName ['\"](\w+)['\"]", script))
    assert provisioned, "no columns found in provision-sharepoint-build.ps1"

    referenced: set[str] = set()
    for name, path in FLOWS.items():
        text = path.read_text(encoding="utf-8")
        # Columns written: "item/JobNumber", "item/Stage/Value", "item/ProjectFolderUrl/Url"
        referenced |= set(re.findall(r'"item/(\w+)', text))
        # Columns read off the trigger: triggerOutputs()?['body/JobNumber']
        referenced |= set(re.findall(r"\['body/(\w+)'\]", text))
        # Columns used in OData: "JobYear eq ..." and "JobSeq desc"
        flow = json.loads(text)
        for action in walk(flow["actions"], []):
            inputs = action.get("inputs")
            if not isinstance(inputs, dict):
                continue  # Compose and Until take a bare expression
            params = inputs.get("parameters", {})
            if not isinstance(params, dict):
                continue
            if "$filter" in params:
                referenced |= set(re.findall(r"'(\w+) (?:eq|ne|gt|lt|ge|le) ", params["$filter"]))
            if "$orderby" in params:
                referenced.add(params["$orderby"].split()[0])

    missing = referenced - provisioned - BUILT_IN
    assert not missing, (
        f"the flows reference columns provision-sharepoint-build.ps1 never creates: {sorted(missing)}. "
        "A missing column does not error in Power Automate - the value simply never lands."
    )
    # And the other way: a column nobody uses is a column someone will fill in by hand and
    # wonder why nothing reads it.
    unused = provisioned - referenced
    assert not unused, f"provisioned but never referenced by either flow: {sorted(unused)}"
    check(f"all {len(referenced - BUILT_IN)} Job Register columns the flows use are provisioned, and none is dead")


def test_no_premium_connectors() -> None:
    """Send an HTTP request to SharePoint is a STANDARD connector. HTTP, and the Azure and
    Dataverse ones, are not. Reaching for a premium action here would put a per-user licence
    between the client and their own folder structure."""
    for name, path in FLOWS.items():
        used = set(re.findall(r'"connectionName": "(\w+)"', path.read_text(encoding="utf-8")))
        assert used == {"shared_sharepointonline"}, f"{name} uses non-SharePoint connectors: {used}"
    check("both flows use only the standard SharePoint connector")


def test_no_hardcoded_tenant() -> None:
    for path in list(FLOWS.values()) + [PS1]:
        for host in re.findall(r"https://([\w.-]+)\.sharepoint\.com", path.read_text(encoding="utf-8")):
            assert host == "REPLACE-ME", f"{path.name} hardcodes tenant {host!r}"
    check("no tenant URL is hardcoded - every one is the REPLACE-ME placeholder")


def test_copy_uses_createcopyjobs_not_the_connector_action() -> None:
    """The connector's Copy folder action walks the tree from the flow runtime, one call per
    item, and throttles on a template deep enough to matter. CreateCopyJobs hands the whole
    job to SharePoint's migration engine in one call."""
    for name, path in FLOWS.items():
        text = path.read_text(encoding="utf-8")
        assert "_api/site/CreateCopyJobs" in text, f"{name} does not use CreateCopyJobs"
        assert "_api/site/GetCopyJobProgress" in text, f"{name} never polls for completion"
        assert "CopyFolder" not in text and "CopyFileAsync" not in text, (
            f"{name} uses a connector copy action - see README, that is the documented "
            "failure mode for deep template trees"
        )
    check("both flows copy with CreateCopyJobs and poll GetCopyJobProgress")


def test_failure_scope_runs_after_failure() -> None:
    for name in FLOWS:
        actions = load(name)["actions"]
        assert "Main" in actions and "Handle_Failure" in actions, f"{name}: missing Main/Handle_Failure"
        after = actions["Handle_Failure"]["runAfter"].get("Main", [])
        assert set(after) == {"Failed", "TimedOut", "Skipped"}, (
            f"{name}: Handle_Failure runs after {after}, must cover Failed, TimedOut and Skipped"
        )
        writes = json.dumps(actions["Handle_Failure"])
        assert '"item/Stage/Value": "Failed"' in writes, f"{name}: failure scope never sets Stage=Failed"
        assert '"item/ErrorDetail"' in writes, f"{name}: failure scope never writes ErrorDetail"
    check("both flows wrap the work in Main with a Handle_Failure scope writing Stage=Failed")


def test_convert_flow_cannot_loop() -> None:
    """ConvertToBidding is triggered by an item UPDATE and finishes by updating that item.
    Without a guard that is a flow that triggers itself forever."""
    guard = json.dumps(find_action(load("ConvertToBidding"), "Only_Unconverted_Bidding_Rows"))
    assert "ProjectFolderUrl" in guard and "empty" in guard, (
        "the update trigger has no ProjectFolderUrl-is-empty guard, so the flow's own final "
        "write re-triggers it"
    )
    assert "Terminate" in guard, "the guard does not terminate the run when it does not apply"
    check("ConvertToBidding guards against re-triggering on its own write")


def test_powershell_parses() -> None:
    """A stray quote produces a script that reads fine and fails at the console in front of
    whoever we handed it to. PowerShell's own parser settles it.

    Skipped where powershell is not on PATH, so the suite still runs on a non-Windows box.
    """
    import shutil
    import subprocess

    exe = shutil.which("powershell") or shutil.which("pwsh")
    if not exe:
        check("powershell not available - parse check skipped")
        return

    script = str(PS1).replace("'", "''")
    probe = (
        "$e=$null; "
        f"[System.Management.Automation.Language.Parser]::ParseFile('{script}',"
        "[ref]$null,[ref]$e) | Out-Null; "
        "if ($e.Count) { $e | ForEach-Object { $_.Message }; exit 1 } else { exit 0 }"
    )
    result = subprocess.run([exe, "-NoProfile", "-Command", probe], capture_output=True, text=True)
    assert result.returncode == 0, f"provision-sharepoint-build.ps1 does not parse:\n{result.stdout}"
    check("provision-sharepoint-build.ps1 parses as valid PowerShell")


def test_ps1_is_dry_run_by_default() -> None:
    script = PS1.read_text(encoding="utf-8")
    assert "[switch]$Apply" in script, "no -Apply switch"
    assert "if ($Apply)" in script, "nothing is gated on -Apply"
    assert "DRY RUN" in script, "a dry run does not say so"
    check("provisioning script is dry-run by default with an -Apply switch")


def test_import_packages_build() -> None:
    """The definitions still wrap into a legacy import package.

    flows/*.json cannot be imported into Power Automate directly - the UI offers only
    "Import Solution (Dataverse)" and "Import Package (Legacy)", and neither takes a bare
    workflow definition. make_import_packages.py builds the second. This asserts it still
    builds, and that the site URL substitution reaches the parameter the flow actually
    reads - if it silently missed, every imported flow would run against REPLACE-ME with no
    way to correct it in the designer.
    """
    import make_import_packages as mip  # noqa: PLC0415

    for stem, display in mip.PACKAGES.items():
        man, resource, definition = mip.build(stem, display,
                                              "https://example.sharepoint.com/sites/BUILD")
        assert not mip.check_definition(stem, definition), \
            f"{stem}: definition did not survive packaging"
        assert definition["parameters"]["SiteUrl"]["defaultValue"] \
            == "https://example.sharepoint.com/sites/BUILD"
        assert man["resources"], f"{stem}: manifest lists no resources"
        assert resource["properties"]["definition"]["triggers"], f"{stem}: trigger lost"
        # The connection is deliberately NOT carried - it is a credential, and it must be
        # picked in the importing tenant.
        refs = resource["properties"]["connectionReferences"]
        assert refs["shared_sharepointonline"]["source"] == "Invoker"
    check(f"both flows wrap into a legacy import package with the site URL baked in")


def test_deploy_script_substitutes_the_site() -> None:
    """deploy_flows.py imports, and its definition() reaches the parameter that matters.

    Nothing here touches the network - `definition()` is pure. The check exists because the
    site URL is a DEFINITION parameter that the Power Automate designer cannot edit after
    the fact, so a substitution that silently missed would produce two flows pointed at
    REPLACE-ME with no way to correct them short of deleting and recreating.
    """
    import deploy_flows as df  # noqa: PLC0415

    for stem in df.FLOWS_TO_CREATE:
        body = df.definition(stem, "https://example.sharepoint.com/sites/BUILD")
        assert body["parameters"]["SiteUrl"]["defaultValue"] \
            == "https://example.sharepoint.com/sites/BUILD"
        assert body["triggers"], f"{stem}: trigger lost"
        trigger = next(iter(body["triggers"].values()))
        assert trigger["runtimeConfiguration"]["concurrency"]["runs"] == 1
        # `description` describes the file, not the workflow, and the API rejects unknown
        # top-level keys in a definition.
        assert "description" not in body
    check("deploy_flows.py builds a definition with the site URL and concurrency intact")

    # The Azure CLI is resolved to a full path, never invoked as a bare "az".
    #
    # On Windows the CLI is az.cmd - a batch file - and CreateProcess cannot launch one from
    # a bare name. subprocess then raises FileNotFoundError [WinError 2], which reads like
    # THIS script is missing rather than the thing it is calling. It cost a round trip.
    try:
        resolved = df.az()
        assert Path(resolved).exists(), f"az() returned {resolved!r}, which does not exist"
        assert resolved != "az", "az() must resolve a path, not return the bare name"
    except SystemExit:
        # No Azure CLI on this machine. That is a legitimate state, and raising SystemExit
        # with an explanation is exactly the required behaviour - the bug was raising
        # FileNotFoundError from inside subprocess instead.
        pass
    check("the Azure CLI is resolved to a full path, so az.cmd launches on Windows")

    # No request path carries a raw space. urllib refuses to send one at all -
    # `InvalidURL: URL can't contain control characters`, raised before the request leaves -
    # and the OData $filter value ("environment eq '...'") is full of them. The error names
    # the whole URL, so it reads like a bad endpoint rather than an unescaped argument.
    env = "Default-b2a2225b-4b4e-42ec-ba52-c7e1c2dea580"
    candidates = df.connection_paths(env)
    assert len(candidates) >= 2, "one candidate is a guess; the point is not to guess once"
    # The HOST has to vary, not just the path. Three paths on one host is what failed:
    # `flows` works on api.flow.microsoft.com, so the path was never what was wrong.
    hosts = {host for _, host, _ in candidates}
    assert len(hosts) >= 2, f"all candidates share a host ({hosts}) - that was the bug"
    assert df.POWERAPPS_API == candidates[0][1], "the Power Apps host must be tried first"
    for label, host, path in candidates:
        assert host.startswith("https://"), f"{label}: {host!r} is not a host"
        assert " " not in path, f"unencoded space in {label}: {path!r}"
        assert "'" not in path, f"unencoded quote in {label}: {path!r}"
        assert env in path, f"{label} does not scope to the environment"
        if "$filter" in path:
            # The key stays OData-spelled; only the value is escaped. urlencode() would
            # turn the key itself into %24filter, which is the mistake the obvious fix makes.
            assert "%24filter" not in path
    check("connections candidates vary the HOST, and try Power Apps first")


def main() -> int:
    test_both_flows_parse()
    test_concurrency_is_one()
    test_sanitiser_strips_every_forbidden_character()
    test_leading_and_trailing_dots_are_handled()
    test_job_number_format()
    test_e_prefix_drop()
    test_ps1_provisions_every_column_the_flows_write()
    test_no_premium_connectors()
    test_no_hardcoded_tenant()
    test_copy_uses_createcopyjobs_not_the_connector_action()
    test_failure_scope_runs_after_failure()
    test_convert_flow_cannot_loop()
    test_ps1_is_dry_run_by_default()
    test_powershell_parses()
    test_import_packages_build()
    test_deploy_script_substitutes_the_site()
    for c in CHECKS:
        print(f"  ok  {c}")
    print(f"\ntest_flows: {len(CHECKS)} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
