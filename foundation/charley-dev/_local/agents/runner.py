"""The agent loop. One sub-agent, one area, one pass of review -> ... -> implement.

A hand-written loop rather than the SDK's beta tool runner, for three reasons: it works on
whatever anthropic version is installed (0.49 here, no pin, no beta dependency); every tool
call has to pass through tools.dispatch anyway, so the runner's auto-execute would be
something to work around rather than use; and an audit trail wants the call journaled
BEFORE it runs, not after it returns.

Streaming is on because max_tokens is large - a non-streaming request that size risks an
HTTP timeout well before the model is done thinking.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tools  # noqa: E402

HERE = Path(__file__).resolve().parent
ROLES = HERE / "roles"

MODEL = "claude-opus-5"
MAX_TOKENS = 64_000
EFFORT = "xhigh"          # agentic + coding; see the effort ladder in the migration guide
TASK_BUDGET = 200_000     # tokens per sub-agent turn, so a stuck agent stops paying
MAX_ITERATIONS = 60
WALL_CLOCK_SECONDS = 3600

# Everything below is context every sub-agent needs regardless of area. It is deliberately
# blunt about the gates: an agent that understands the gate spends its turns working with it
# instead of retrying against it.
SHARED = """\
You are one of five sub-agents improving `foundation/charley-dev/`, a Microsoft Fabric data
platform being built for Affect Group (a NYC general contractor) to replace a hand-filled
Excel workbook. You are working in a git worktree; every turn you take is committed
separately, so a bad change is one `git revert`.

# Your cycle

Work through these six steps in order, once, then stop and summarise:

1. REVIEW    - read the files in your area and call run_tests to get the current baseline.
2. IDEATE    - list candidate improvements. Do not write code yet.
3. EXPAND    - keep only the candidates that fix a verified defect or serve a stated client
               need. Drop the rest with a one-line reason. Speculative work is the failure
               mode here, not missing work.
4. DEVELOP   - write the changes with write_file.
5. VALIDATE  - call run_tests. If it fails, go back to step 4. You cannot skip this.
6. IMPLEMENT - deploy the relevant script with --apply, then verify with fabric_get.

# Hard limits (enforced in code - you cannot talk your way past them)

- write_file only accepts paths under `foundation/charley-dev/`. Everything Rebecca Buckley
  built - `foundation/01-ingestion/`, `03-lakehouses/`, `04-semantic_models/`, the existing
  Fabric items - is READ-ONLY. The whole engagement depends on her reporting continuing to
  run untouched. Read it freely; never write it.
- deploy is refused unless run_tests passed AFTER your most recent write_file.
- deploy only runs the nine allow-listed scripts in `_local/`.
- Files whose names suggest secrets cannot be read. Secrets reach notebooks through
  `lib/fabric_common.get_secret()` and Key Vault, never through a literal in a file.

# What already works - do not rebuild it

Live in Fabric: three CD_ lakehouses (schema-enabled), four `cd_*` notebooks, the
`Affect Project Report` semantic model (26 tables, 52 measures, 31 relationships, Direct
Lake), `Monthly Progress Report`, and `CD_Master_Pipeline`. Gold holds 16 populated tables.
The offline harness is 8 suites and passes.

# Failure modes we have already paid for - do not rediscover these

- `Current` is a reserved word in DAX. `VAR Current` does not parse, and the failure is
  silent: the service substitutes SYNTAXERROR and every measure in the model breaks at once.
- Direct Lake does not support calculated tables. A model using them deploys "successfully",
  loads zero tables, and every DAX query fails with "Failed to resolve name".
- `CREATE TABLE (cols)` with no rows writes no data files, so Direct Lake cannot bind to it.
  Write an empty DataFrame with `overwriteSchema` instead.
- Spark lowercases table names on write, so TMDL `entityName` must be lowercase.
- A semantic model is not queryable until it is reframed - deploy_model.py handles this.
- TMDL: `///` descriptions go BEFORE the object; multi-line DAX goes entirely below the `=`;
  files must be written with LF endings.
- PBIR is strict - `byConnection` accepts only `connectionString`, and `report.json`
  rejects `useNewFilterPaneExperience`.
- Procore submittals contain dates before 1582-10-15, which makes Spark refuse the read
  outright. Silver floors anything before 1990 to NULL.
- Bare `VARCHAR` is invalid in Spark SQL. Use `STRING`.
- Fabric's job API gives no per-cell detail, so notebooks write diagnostics to
  `Files/_diag/*.json` and the deploy scripts read them back over the OneLake DFS API.

# The one rule about numbers

Affect currently reports a project scorecard of 0.59 to their leadership, and it is wrong -
two band errors cancel out. We show the corrected number and the as-reported number side by
side with the arithmetic. Never silently ship a different number than the one they have been
reporting.

# Style

Match the surrounding code: these files carry comments that explain WHY a decision was made,
usually naming the defect or client need behind it. Keep that. Do not add abstractions,
config, or error handling for cases that cannot happen. The shortest change that is correct
and verified wins.
"""


def _client():
    import anthropic

    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        raise SystemExit(
            "No Anthropic credential found.\n"
            "  Set ANTHROPIC_API_KEY, or run `ant auth login` if you have the CLI.\n"
            "  Everything else (Fabric auth via `az`, the offline harness) works without it -\n"
            "  only the agent loop needs this."
        )
    return anthropic.Anthropic()


def _text(message) -> str:
    return "\n".join(b.text for b in message.content if b.type == "text")


def run_agent(role: str, task: str, *, dry_run: bool = False,
              max_iterations: int = MAX_ITERATIONS) -> tuple[str, tools.State]:
    """Run one sub-agent to completion. Returns (final text, state carrying the journal)."""
    role_file = ROLES / f"{role}.md"
    if not role_file.is_file():
        raise SystemExit(f"no role prompt at {role_file}")

    client = _client()
    state = tools.State(dry_run=dry_run)
    system = SHARED + "\n\n" + role_file.read_text(encoding="utf-8")
    messages = [{"role": "user", "content": task}]

    deadline = time.time() + WALL_CLOCK_SECONDS
    final = ""

    for iteration in range(max_iterations):
        if time.time() > deadline:
            final += f"\n\n[stopped: wall-clock cap of {WALL_CLOCK_SECONDS}s reached]"
            break

        with client.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=messages,
            tools=tools.SCHEMAS,
            thinking={"type": "adaptive"},
            # output_config is newer than the installed SDK's typed signature; extra_body is
            # the version-agnostic way to send it and works on new SDKs too.
            extra_body={"output_config": {
                "effort": EFFORT,
                "task_budget": {"type": "tokens", "total": TASK_BUDGET},
            }},
            extra_headers={"anthropic-beta": "task-budgets-2026-03-13"},
        ) as stream:
            message = stream.get_final_message()

        messages.append({"role": "assistant", "content": message.content})
        said = _text(message)
        if said:
            final = said
            print(f"\n--- {role} · turn {iteration + 1} ---\n{said[:1200]}")

        if message.stop_reason == "refusal":
            final += "\n\n[stopped: the model declined this request]"
            break

        if message.stop_reason == "pause_turn":
            # A server-side tool hit its iteration cap. Re-send to resume; do not add a
            # "continue" message, the API resumes from the trailing block on its own.
            continue

        calls = [b for b in message.content if b.type == "tool_use"]
        if not calls:
            break   # end_turn with no tool use - the agent is done

        results = []
        for call in calls:
            print(f"  [{call.name}] {str(call.input)[:160]}")
            out, is_error = tools.dispatch(state, call.name, dict(call.input))
            results.append({
                "type": "tool_result",
                "tool_use_id": call.id,
                "content": out,
                "is_error": is_error,
            })
        # All results go back in ONE user message - splitting them trains the model out of
        # making parallel calls.
        messages.append({"role": "user", "content": results})
    else:
        final += f"\n\n[stopped: hit the {max_iterations}-iteration cap]"

    return final, state
