"""The tool surface the agents get, and the gates that constrain it.

EVERY GATE HERE IS CODE, NOT PROMPT TEXT. A role prompt telling an agent "only write inside
charley-dev" is advisory - the model can misread it, or a later turn can talk it out of it.
The checks below cannot be argued with, and they are the reason fully-autonomous Fabric
deploy is an acceptable setting rather than a gamble.

Five gates:

  1. write_file resolves the target and refuses anything outside foundation/charley-dev/.
     Resolution happens AFTER following symlinks, so a link pointing out of the tree is
     rejected on where it lands, not on how it looks.
  2. read_file refuses .env and anything whose name suggests a secret. Credentials reach
     notebooks through Key Vault; they must never reach a transcript.
  3. deploy refuses unless run_tests() has passed SINCE the last write. Writing then
     deploying without re-running the harness is the exact failure this exists to stop.
  4. deploy only runs the eight known scripts in _local/, with a small flag allow-list.
     No arbitrary subprocess, no shell, no `az`, no Livy.
  5. fabric_* is GET-only. Item creation goes through the deploy scripts, which already
     assert the folder id - so there is one audited path to Fabric writes, not two.

Every call is journaled with its arguments before it runs, so a run is reviewable after
the fact whether it succeeded or not.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import deploy as dp  # noqa: E402

HERE = Path(__file__).resolve().parent
LOCAL = HERE.parent
CHARLEY_DEV = LOCAL.parent
REPO = CHARLEY_DEV.parent.parent

# The only directory any agent may write to.
WRITE_ROOT = CHARLEY_DEV.resolve()

# Reading is wider than writing on purpose: agents need the analysis, the workbook notes and
# Rebecca's schemas to make good decisions. They just cannot change any of it.
READ_ROOT = REPO.resolve()

DEPLOY_SCRIPTS = {
    "deploy.py", "deploy_seeds.py", "deploy_gold.py", "deploy_model.py",
    "deploy_report.py", "deploy_ingestion.py", "deploy_silver.py",
    "deploy_pipeline.py", "deploy_landing.py", "validate_model.py",
    # Added 2026-08-19. These existed and were simply never allow-listed, so the harness
    # could build gold but not gate it, and could not land manual input at all - which
    # matters now that deploy_manual.py is load-bearing: silver PARSES cd_bronze_man_*,
    # so running deploy_silver.py without it first fails with
    # System_Cancelled_Session_Statements_Failed, an error that names no table.
    "deploy_dq.py", "deploy_manual.py", "deploy_schedule.py",
    # The PQP model and report. Both import the base generators and override three lists.
    "deploy_model_qc.py", "deploy_report_qc.py",
}
# extract_procore_local.py and setup_keyvault.py are DELIBERATELY absent. Both read the
# .env, and an agent that can run them can print a credential into its own transcript -
# which is the one thing read_file's secret guard exists to prevent. A human runs those two.
DEPLOY_FLAGS = {"--apply", "--run", "--verify", "--recreate", "--dry-run",
                # deploy_gold.py --source {existing,cd} - the source migration switch.
                "--source", "existing", "cd"}

# Substring match, lowercased. Deliberately broad - a false refusal costs one turn, a
# credential in a transcript costs a rotation.
SECRET_MARKERS = (".env", "secret", "credential", "password", "token", ".pem", ".pfx")


class Refused(Exception):
    """A gate said no. Returned to the model as an error tool_result, not raised to the top -
    an agent that gets refused should adjust and continue, not crash the run."""


@dataclass
class State:
    """Per-run state the gates read. One instance per sub-agent."""

    dry_run: bool = False
    writes: int = 0                      # monotonic count of successful write_file calls
    tests_passed_at: int | None = None   # value of `writes` when the harness last passed
    journal: list[dict] = field(default_factory=list)

    def record(self, tool: str, args: dict, outcome: str) -> None:
        self.journal.append({
            "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "tool": tool,
            "args": {k: (v[:300] + "..." if isinstance(v, str) and len(v) > 300 else v)
                     for k, v in args.items()},
            "outcome": outcome[:400],
        })

    @property
    def deploy_allowed(self) -> bool:
        # Passing before any write is fine (nothing changed); passing before the most recent
        # write is not. Equality is the whole check.
        return self.tests_passed_at == self.writes


def _resolve(rel: str, root: Path, *, for_write: bool) -> Path:
    """Resolve a model-supplied path and prove it lands inside `root`.

    strict=False so a not-yet-existing file still resolves; symlinks in existing parents are
    followed first, which is the point - we validate the destination, not the spelling.
    """
    if os.path.isabs(rel):
        candidate = Path(rel)
    else:
        candidate = (REPO / rel)

    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError:
        verb = "write" if for_write else "read"
        raise Refused(
            f"refusing to {verb} {rel!r}: resolves to {resolved}, outside {root}. "
            f"Agents may only write inside foundation/charley-dev/."
        ) from None
    return resolved


def _refuse_secrets(path: Path) -> None:
    low = str(path).lower()
    for marker in SECRET_MARKERS:
        if marker in low:
            raise Refused(
                f"refusing to read {path.name!r}: matches secret marker {marker!r}. "
                f"Secrets reach notebooks via get_secret()/Key Vault, never a transcript."
            )


# --------------------------------------------------------------------------- tool bodies

def read_file(state: State, path: str, max_bytes: int = 60_000) -> str:
    target = _resolve(path, READ_ROOT, for_write=False)
    _refuse_secrets(target)
    if not target.is_file():
        raise Refused(f"{path!r} does not exist or is not a file")
    text = target.read_text(encoding="utf-8", errors="replace")
    if len(text) > max_bytes:
        return text[:max_bytes] + f"\n\n... truncated at {max_bytes} bytes ({len(text)} total)"
    return text


def list_files(state: State, pattern: str = "**/*") -> str:
    hits = sorted(
        str(p.relative_to(REPO)) for p in CHARLEY_DEV.glob(pattern)
        if p.is_file() and "__pycache__" not in p.parts
    )
    return "\n".join(hits[:400]) or "(no matches)"


def write_file(state: State, path: str, content: str) -> str:
    target = _resolve(path, WRITE_ROOT, for_write=True)
    if state.dry_run:
        return f"DRY RUN: would write {len(content)} bytes to {target.relative_to(REPO)}"
    target.parent.mkdir(parents=True, exist_ok=True)
    # newline="" keeps LF endings on Windows. TMDL and PBIR both parse-fail on CRLF, which
    # is a genuinely painful thing to debug from a Fabric error message.
    target.write_text(content, encoding="utf-8", newline="")
    state.writes += 1
    return f"wrote {len(content)} bytes to {target.relative_to(REPO)}"


def run_tests(state: State) -> str:
    """The gate. Nothing deploys while this is failing."""
    result = subprocess.run(
        [sys.executable, str(LOCAL / "run_tests.py")],
        capture_output=True, text=True, cwd=str(LOCAL), timeout=900,
    )
    tail = (result.stdout or "")[-4000:] + (result.stderr or "")[-2000:]
    if result.returncode == 0:
        state.tests_passed_at = state.writes
        return f"HARNESS PASSED (deploy is now unlocked)\n\n{tail}"
    state.tests_passed_at = None
    return f"HARNESS FAILED with exit {result.returncode} - deploy stays locked.\n\n{tail}"


def deploy(state: State, script: str, flags: list[str] | None = None) -> str:
    flags = flags or []
    if script not in DEPLOY_SCRIPTS:
        raise Refused(
            f"{script!r} is not an allow-listed deploy script. "
            f"Allowed: {', '.join(sorted(DEPLOY_SCRIPTS))}"
        )
    bad = [f for f in flags if f not in DEPLOY_FLAGS]
    if bad:
        raise Refused(f"flag(s) {bad} not allowed. Allowed: {sorted(DEPLOY_FLAGS)}")

    if not state.deploy_allowed:
        raise Refused(
            "the harness has not passed since the last write_file. "
            "Call run_tests and get a pass before deploying. "
            f"(writes={state.writes}, last pass at={state.tests_passed_at})"
        )

    if state.dry_run:
        return f"DRY RUN: would run {script} {' '.join(flags)}"

    result = subprocess.run(
        [sys.executable, str(LOCAL / script), *flags],
        capture_output=True, text=True, cwd=str(LOCAL), timeout=3600,
    )
    tail = (result.stdout or "")[-5000:] + (result.stderr or "")[-2000:]
    return f"exit {result.returncode}\n\n{tail}"


def fabric_get(state: State, path: str) -> str:
    """Read-only Fabric REST. GET only - creation goes through the deploy scripts."""
    if not path.startswith("/"):
        raise Refused("path must start with '/', e.g. /workspaces/<id>/items")
    tok = dp.token()
    _, body, _ = dp.call("GET", path, tok)
    return json.dumps(body, indent=1)[:20_000]


def git_status(state: State) -> str:
    result = subprocess.run(
        ["git", "status", "--short", "--", "foundation/charley-dev"],
        capture_output=True, text=True, cwd=str(REPO), timeout=60,
    )
    diff = subprocess.run(
        ["git", "diff", "--stat", "--", "foundation/charley-dev"],
        capture_output=True, text=True, cwd=str(REPO), timeout=60,
    )
    return f"status:\n{result.stdout or '(clean)'}\n\ndiff --stat:\n{diff.stdout or '(none)'}"


# --------------------------------------------------------------------------- registry

HANDLERS = {
    "read_file": read_file,
    "list_files": list_files,
    "write_file": write_file,
    "run_tests": run_tests,
    "deploy": deploy,
    "fabric_get": fabric_get,
    "git_status": git_status,
}

SCHEMAS = [
    {
        "name": "read_file",
        "description": (
            "Read a file anywhere in the repo. Use this to review current code, the analysis "
            "in analysis/, the workbook notes, and Rebecca's existing schemas in foundation/. "
            "Refuses files whose names suggest secrets."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string",
                                    "description": "Repo-relative path, e.g. foundation/charley-dev/_local/deploy.py"}},
            "required": ["path"],
        },
    },
    {
        "name": "list_files",
        "description": "List files under foundation/charley-dev matching a glob pattern.",
        "input_schema": {
            "type": "object",
            "properties": {"pattern": {"type": "string",
                                       "description": "Glob relative to foundation/charley-dev, e.g. '02-transformation/**/*.sql'"}},
            "required": [],
        },
    },
    {
        "name": "write_file",
        "description": (
            "Create or overwrite a file. ONLY paths under foundation/charley-dev/ are "
            "accepted; anything else is refused. Writing invalidates the harness pass, so "
            "you must call run_tests again before you can deploy."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Repo-relative path under foundation/charley-dev/"},
                "content": {"type": "string", "description": "Full file content"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "run_tests",
        "description": (
            "Run the full offline harness (_local/run_tests.py - 8 suites). This is the "
            "validate step and the deploy gate: deploy is refused until this passes after "
            "your most recent write."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "deploy",
        "description": (
            "Run one allow-listed deploy script to push to Fabric. Requires a harness pass "
            "since your last write. Scripts: deploy.py, deploy_seeds.py, deploy_gold.py, "
            "deploy_model.py, deploy_report.py, deploy_ingestion.py, deploy_silver.py, "
            "deploy_pipeline.py, validate_model.py. Without --apply these are dry runs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "script": {"type": "string", "description": "e.g. deploy_gold.py"},
                "flags": {"type": "array", "items": {"type": "string"},
                          "description": "Subset of --apply, --run, --verify, --recreate, --dry-run"},
            },
            "required": ["script"],
        },
    },
    {
        "name": "fabric_get",
        "description": (
            "Read-only Fabric REST GET, for verifying what actually landed. "
            "e.g. /workspaces/1f7caed6-f88a-4e52-bc83-9a498a165301/items"
        ),
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "API path starting with /"}},
            "required": ["path"],
        },
    },
    {
        "name": "git_status",
        "description": "Show what you have changed so far in this run (status + diff --stat).",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


def dispatch(state: State, name: str, args: dict) -> tuple[str, bool]:
    """Run one tool call through its gate. Returns (result_text, is_error).

    A refusal comes back as an error tool_result rather than an exception, so the agent can
    correct course. Anything else unexpected is also returned rather than raised - a crashed
    run tells you less than a journaled failure.
    """
    handler = HANDLERS.get(name)
    if handler is None:
        state.record(name, args, "unknown tool")
        return f"unknown tool {name!r}", True
    try:
        out = handler(state, **args)
        state.record(name, args, out)
        return out, False
    except Refused as exc:
        state.record(name, args, f"REFUSED: {exc}")
        return f"REFUSED: {exc}", True
    except Exception as exc:  # noqa: BLE001 - surfaced to the model, journaled either way
        state.record(name, args, f"{type(exc).__name__}: {exc}")
        return f"{type(exc).__name__}: {exc}", True


# --------------------------------------------------------------------------- self-check

def _selfcheck() -> None:
    """The gates are the whole point, so they get asserted rather than trusted."""
    s = State(dry_run=True)

    # 1. Writes outside charley-dev are refused, including via traversal and absolute paths.
    for bad in ("foundation/README.md",
                "foundation/charley-dev/../README.md",
                "src/procore/procore_extract.py",
                str(REPO / "foundation" / "03-lakehouses" / "x.json")):
        out, err = dispatch(s, "write_file", {"path": bad, "content": "x"})
        assert err and "refusing to write" in out, f"escape not blocked: {bad} -> {out}"

    # ...and inside is allowed (dry run, so nothing lands).
    out, err = dispatch(s, "write_file", {"path": "foundation/charley-dev/_docs/_probe.md",
                                          "content": "x"})
    assert not err and "DRY RUN" in out, out

    # 2. Secrets are unreadable.
    out, err = dispatch(s, "read_file", {"path": ".env"})
    assert err and "secret marker" in out, out

    # 3. Deploy is locked until the harness passes after the latest write.
    live = State()
    live.writes = 1
    live.tests_passed_at = None
    out, err = dispatch(live, "deploy", {"script": "deploy_gold.py", "flags": ["--apply"]})
    assert err and "harness has not passed" in out, out

    live.tests_passed_at = 0          # passed BEFORE the write - still stale
    out, err = dispatch(live, "deploy", {"script": "deploy_gold.py", "flags": ["--apply"]})
    assert err and "harness has not passed" in out, out

    live.tests_passed_at = 1          # passed after the write
    assert live.deploy_allowed

    # 4. Only known scripts and flags.
    live2 = State(dry_run=True)
    live2.tests_passed_at = live2.writes
    out, err = dispatch(live2, "deploy", {"script": "rm.py"})
    assert err and "not an allow-listed" in out, out
    out, err = dispatch(live2, "deploy", {"script": "deploy.py", "flags": ["--delete"]})
    assert err and "not allowed" in out, out
    out, err = dispatch(live2, "deploy", {"script": "deploy.py", "flags": ["--verify"]})
    assert not err and "DRY RUN" in out, out

    # The two credential-reading scripts must stay unreachable, or the secret guard on
    # read_file is decorative - an agent could just run the extractor and read the output.
    for script in ("extract_procore_local.py", "setup_keyvault.py"):
        out, err = dispatch(live2, "deploy", {"script": script})
        assert err and "not an allow-listed" in out, f"{script} is reachable: {out}"

    # 5. Every advertised tool has a handler, and vice versa.
    assert {s["name"] for s in SCHEMAS} == set(HANDLERS), "schema/handler mismatch"

    print(f"  ok  writes outside foundation/charley-dev/ are refused (4 escape shapes)")
    print(f"  ok  secret-looking paths are unreadable")
    print(f"  ok  deploy is locked until the harness passes AFTER the latest write")
    print(f"  ok  deploy scripts and flags are allow-listed")
    print(f"  ok  {len(SCHEMAS)} tool schemas all have handlers")
    print(f"\ntools: 5 gate checks passed")


if __name__ == "__main__":
    _selfcheck()
