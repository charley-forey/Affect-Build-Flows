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
LIB = HERE.parent / "00-platform" / "lib"
TESTS = HERE / "tests"

SUITES = [
    ("fabric_common self-check", LIB / "fabric_common.py"),
    ("dq self-check", LIB / "dq.py"),
    ("watermark self-check", LIB / "watermark.py"),
    ("procore_scope self-check", LIB / "procore_scope.py"),
    ("gold seeds", TESTS / "test_seeds.py"),
    ("extractor compatibility", TESTS / "test_extractor_compat.py"),
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
