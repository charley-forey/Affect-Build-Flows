"""Main orchestrator. Dispatches the sub-agents, journals every run, commits per turn.

    python orchestrate.py --list                 # what agents exist and what they own
    python orchestrate.py --dry-run              # full cycle, writes and deploys stubbed
    python orchestrate.py --agent sql            # one area
    python orchestrate.py --all                  # every area, in dependency order

RUN --dry-run FIRST. It exercises the whole loop with write_file and deploy stubbed, which
proves the gates fire before they are load-bearing. That is the difference between
"autonomous because we checked" and "autonomous because we hoped".

Order matters and is not alphabetical: lakehouse shape constrains the SQL, the SQL
constrains the notebooks, and the model can only be built on gold that exists. Dataflows are
independent of all of it, so they run last and cannot block anything.

Each sub-agent gets its own commit. Reviewing a run is reading one journal directory;
undoing one is `git revert <sha>`.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import runner  # noqa: E402
import tools  # noqa: E402

HERE = Path(__file__).resolve().parent
JOURNAL = HERE / "journal"
REPO = tools.REPO

# (name, one-line ownership, default task)
AGENTS = [
    ("lakehouse",
     "lakehouse shape, watermarks, cd_meta_* / cd_dq_*",
     "Review the lakehouse layer. The medallion exists and gold is populated, but the "
     "metadata tables the plan calls for (cd_meta_watermark, cd_dq_results) are not built "
     "yet and incremental loads have nothing to read. Close that gap."),

    ("sql",
     "02-transformation/sql/** - silver parsers, gold star schema, DQ suite",
     "Review the SQL layer. Gold is currently sourced from Rebecca's Silver via "
     "00_source_views.sql; 01_source_views_cd.sql is the switch to our own medallion and is "
     "written but unused. Check the two are contract-identical, and build the DQ expectation "
     "suite (sql/dq/*.sql) that the pipeline is supposed to fail on."),

    ("notebooks",
     "the four cd_* notebooks and make_notebooks.py generation",
     "Review the notebooks. cd_01_extract_procore stops at load_settings because it has no "
     "credentials - make it read from Key Vault via get_secret() with a clear, actionable "
     "failure when the secret is absent, rather than a silent stop."),

    ("dashboard",
     "TMDL semantic model, measures, PBIR report pages",
     "Review the report. Six pages exist and render. Work the depth items: RAG status as "
     "icon plus label rather than colour alone, drill-through from portfolio to project to "
     "line item, and the scorecard page showing the corrected and as-reported numbers side "
     "by side with the arithmetic visible."),

    ("dataflows",
     "Sage Dataflow Gen2 mashup.pq, Procore + Outbuild ingestion configs",
     "Build 01-ingestion/Sage/CD_Sage_Ingest.Dataflow on the pattern of the existing "
     "foundation/01-ingestion/Sage/Build_Sage_Test.Dataflow/mashup.pq. Include arivln and "
     "apivln - the line tables nobody queries today, and where cost codes and the real "
     "retainage live, because the invoice header retain column is zero across all 940 rows."),
]


def commit(agent: str, run_id: str, dry_run: bool) -> str | None:
    """One commit per sub-agent turn. Nothing staged means nothing changed - that is a
    normal outcome for a review-only turn, not an error."""
    if dry_run:
        return None
    subprocess.run(["git", "add", "foundation/charley-dev"], cwd=str(REPO), check=False)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(REPO))
    if staged.returncode == 0:
        return None
    subprocess.run(
        ["git", "commit", "-m",
         f"agent({agent}): {run_id}\n\nAutomated turn from _local/agents/orchestrate.py.\n"
         f"Journal: foundation/charley-dev/_local/agents/journal/{run_id}/{agent}.json\n\n"
         f"Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"],
        cwd=str(REPO), check=False, capture_output=True,
    )
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                         cwd=str(REPO), capture_output=True, text=True).stdout.strip()
    return sha


def isolation_gate() -> bool:
    """Nothing outside charley-dev may have moved. Cheap to check, expensive to miss."""
    out = subprocess.run(
        ["git", "status", "--porcelain"], cwd=str(REPO), capture_output=True, text=True
    ).stdout
    stray = [ln for ln in out.splitlines()
             if ln[3:].strip() and not ln[3:].strip().startswith("foundation/charley-dev")]
    if stray:
        print("\nISOLATION GATE FAILED - changes outside charley-dev:")
        for ln in stray:
            print(f"  {ln}")
        return False
    print("\n  isolation gate ok - no changes outside foundation/charley-dev/")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--dry-run", action="store_true",
                        help="stub write_file and deploy; prove the gates fire")
    parser.add_argument("--agent", help="run one agent by name")
    parser.add_argument("--all", action="store_true", help="run every agent in order")
    parser.add_argument("--task", help="override the default task for --agent")
    parser.add_argument("--max-iterations", type=int, default=runner.MAX_ITERATIONS)
    args = parser.parse_args()

    names = {a[0] for a in AGENTS}

    if args.list or not (args.agent or args.all):
        print(f"{len(AGENTS)} sub-agents:\n")
        for name, owns, task in AGENTS:
            print(f"  {name:<12} {owns}")
            print(f"  {'':<12} default task: {task[:96]}...\n")
        print("Run one:  python orchestrate.py --agent sql --dry-run")
        print("Run all:  python orchestrate.py --all")
        return 0

    if args.agent and args.agent not in names:
        print(f"unknown agent {args.agent!r}. Known: {', '.join(sorted(names))}")
        return 1

    selected = [a for a in AGENTS if (args.all or a[0] == args.agent)]
    run_id = time.strftime("%Y%m%d-%H%M%S") + ("-dry" if args.dry_run else "")
    outdir = JOURNAL / run_id
    outdir.mkdir(parents=True, exist_ok=True)

    # ASCII only in console output - the Windows console is cp1252 and mangles the rest.
    print(f"run {run_id}  |  {len(selected)} agent(s)  |  "
          f"{'DRY RUN (writes and deploys stubbed)' if args.dry_run else 'LIVE'}")

    summary = []
    for name, owns, default_task in selected:
        task = args.task if (args.task and args.agent == name) else default_task
        print(f"\n{'=' * 70}\n{name} - {owns}\n{'=' * 70}")

        try:
            final, state = runner.run_agent(
                name, task, dry_run=args.dry_run, max_iterations=args.max_iterations)
        except SystemExit:
            raise
        except Exception as exc:  # noqa: BLE001 - one agent failing must not kill the run
            print(f"  agent {name} raised {type(exc).__name__}: {exc}")
            summary.append({"agent": name, "error": f"{type(exc).__name__}: {exc}"})
            continue

        sha = commit(name, run_id, args.dry_run)
        (outdir / f"{name}.json").write_text(json.dumps({
            "agent": name, "owns": owns, "task": task, "dry_run": args.dry_run,
            "commit": sha, "writes": state.writes,
            "harness_passed_after_last_write": state.deploy_allowed,
            "final": final, "calls": state.journal,
        }, indent=1), encoding="utf-8", newline="")

        summary.append({"agent": name, "commit": sha, "writes": state.writes,
                        "calls": len(state.journal),
                        "harness_ok": state.deploy_allowed})
        print(f"\n  {len(state.journal)} tool call(s), {state.writes} write(s), "
              f"commit {sha or '(nothing to commit)'}")

    (outdir / "summary.json").write_text(json.dumps(summary, indent=1),
                                         encoding="utf-8", newline="")
    print(f"\n{'=' * 70}\njournal: {outdir.relative_to(REPO)}")
    for row in summary:
        print(f"  {row}")

    return 0 if isolation_gate() else 1


if __name__ == "__main__":
    raise SystemExit(main())
