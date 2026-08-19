"""Run every charley-dev check. One command, no framework, no network, no Fabric.

    python foundation/charley-dev/_local/run_tests.py

Covers the library self-checks and the offline SQL suites. What it deliberately does not
cover: Spark dialect edge cases and live Procore field names - both need a real tenant and
are listed as first-run checks in _docs/build-status.md.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHARLEY_DEV = HERE.parent
LIB = CHARLEY_DEV / "00-platform" / "lib"
TESTS = HERE / "tests"
AGENTS = HERE / "agents"

SUITES = [
    ("fabric_common self-check", LIB / "fabric_common.py"),
    ("dq self-check", LIB / "dq.py"),
    ("watermark self-check", LIB / "watermark.py"),
    ("procore_scope self-check", LIB / "procore_scope.py"),
    ("ratelimit self-check", LIB / "ratelimit.py"),
    ("dq expectation suite", CHARLEY_DEV / "02-transformation" / "dq" / "expectations.py"),
    # The agent gates guard autonomous Fabric deploys, so they are harness-critical: if a
    # gate stops firing, everything downstream of it is running unprotected.
    ("agent gates", AGENTS / "tools.py"),
    ("gold seeds", TESTS / "test_seeds.py"),
    ("bronze to silver", TESTS / "test_silver.py"),
    ("gold dimensions and facts", TESTS / "test_gold.py"),
    ("PQP quality plan", TESTS / "test_qc.py"),
    ("extractor compatibility", TESTS / "test_extractor_compat.py"),
    ("report accessibility and chrome", TESTS / "test_report.py"),
    ("sharepoint intake lists", TESTS / "test_sharepoint.py"),
]


def main() -> int:
    failures = []
    for label, path in SUITES:
        print(f"\n=== {label} ===")
        result = subprocess.run([sys.executable, str(path)], cwd=path.parent)
        if result.returncode != 0:
            failures.append(label)

    print("\n" + "=" * 46)
    if failures:
        print(f"FAILED: {', '.join(failures)}")
        return 1
    print(f"all {len(SUITES)} suites passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
