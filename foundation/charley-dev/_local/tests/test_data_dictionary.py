"""The data dictionary must match the code it is generated from.

Fails when _docs/data-dictionary.md is stale (a SQL, DQ rule, model or lineage change without
re-running make_data_dictionary.py), and pins a few parsed facts so a parser regression
cannot pass by producing a quietly emptier document.

Run:  python test_data_dictionary.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import make_data_dictionary as mdd  # noqa: E402


def main() -> int:
    built = mdd.build()
    committed = mdd.OUT.read_text(encoding="utf-8").replace("\r\n", "\n") if mdd.OUT.exists() else ""
    assert committed == built, "data-dictionary.md is stale - run _local/make_data_dictionary.py"
    print("  ok  committed dictionary matches the generator")

    budget = built.split("### fct_BudgetLine\n", 1)[1].split("\n### ", 1)[0]
    assert "(ProjectKey, BudgetLineID) (DQ unique rule)" in budget
    assert "`cd_bronze_procore_budget_detail_rows`" in budget, "upstream lost bronze"
    assert "| BudgetAmount | double | TMDL |" in budget
    assert "Financial (" in budget, "report usage lost"
    print("  ok  key, bronze lineage, TMDL types and report usage parsed for fct_BudgetLine")

    for area in mdd.AREAS:
        assert f"### {area}\n\n```mermaid" in built, f"no diagram for {area}"
    assert "| Unmatched AR invoice | Sage |" in built
    assert "| 1 | Map Sage job" in built, "open decisions table not copied"
    print("  ok  subject-area diagrams, gap categories and open decisions present")
    print("\ndata dictionary: 3 checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
