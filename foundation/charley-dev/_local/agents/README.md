# The agent system

Five sub-agents, each owning one area of charley-dev, each running the same cycle:
**review → ideate → expand → develop → validate → implement**. A main orchestrator dispatches
them, journals every tool call, and commits per turn.

```
python orchestrate.py --list                 # what exists and what it owns
python orchestrate.py --agent sql --dry-run  # full cycle, writes and deploys stubbed
python orchestrate.py --agent sql            # live, one area
python orchestrate.py --all                  # every area, in dependency order
```

Needs `ANTHROPIC_API_KEY` (or `ant auth login`). Fabric auth is separate and already works
via `az`.

**Run `--dry-run` before the first live run.** It exercises the whole loop with `write_file`
and `deploy` stubbed, which proves the gates fire before they are load-bearing.

## Why this is safe to run autonomously

Five gates, all in `tools.py`, all asserted by `python tools.py` (which is suite 5 of
`run_tests.py`, so a broken gate fails the harness):

| Gate | What it stops |
|---|---|
| `write_file` resolves and rejects anything outside `foundation/charley-dev/` | An agent touching Rebecca's work. Checked after symlink resolution, so a link pointing out of the tree is judged on where it lands |
| `read_file` refuses `.env` and secret-shaped names | A credential reaching a transcript |
| `deploy` requires a harness pass **since the last write** | Deploying code that has not been tested. A pass from before the write is stale and is rejected |
| `deploy` allow-lists nine scripts and five flags | Arbitrary subprocess, shell, `az`, Livy |
| Fabric access is GET-only from the agent | Two paths to Fabric writes. There is one: the deploy scripts, which already assert the folder id |

Plus: one git commit per sub-agent turn, and an isolation check at the end of every run that
fails if anything outside `charley-dev/` moved.

## Reviewing a run

`journal/<run-id>/` holds one JSON per agent — the task, every tool call with its arguments,
the outcome, the commit SHA, and whether the harness was green at the end. Reviewing a run is
reading one directory. Undoing one is `git revert <sha>`.

## Why five and not one loop

They map to five artifact types with genuinely different failure modes, and each role prompt
carries the traps we have already hit in that area so the agents do not rediscover them at
Fabric's pace:

| Agent | Owns | Characteristic failure |
|---|---|---|
| `lakehouse` | shape, `lib/`, `cd_meta_*` / `cd_dq_*` | Expensive to reverse (`enableSchemas` is creation-only) |
| `sql` | `02-transformation/sql/**` | Fails offline in DuckDB — cheap and fast |
| `notebooks` | the eight `cd_*` notebooks | Fails at run time in Fabric with no per-cell detail |
| `dashboard` | TMDL + PBIR | Fails **silently** — a model that loads zero tables looks deployed |
| `dataflows` | Sage `mashup.pq`, ingestion configs | Fails on the on-prem gateway |
