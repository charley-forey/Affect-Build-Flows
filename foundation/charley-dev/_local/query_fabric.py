"""Run read-only Spark SQL against the lakehouses and print the result.

    python query_fabric.py "SELECT COUNT(*) FROM ex.procore_prime_change_orders"
    python query_fabric.py --file questions.sql

Investigation tool, not part of any pipeline. It exists because comparing our numbers
against the existing warehouse is a recurring need - "our change orders say 307 and theirs
say 1,812, which is right?" - and the alternative is hand-building a throwaway notebook
every time, which is slow enough that the comparison quietly stops being made.

THREE PREFIXES ARE PRE-REGISTERED as temporary views so a query can name any layer:

    ex.<table>   the EXISTING warehouse's Silver   (read-only, never written)
    cd.<table>   our silver
    <table>      our gold, which is the notebook's default lakehouse

READ-ONLY BY CONSTRUCTION. Anything that is not a SELECT or a WITH is refused before the
notebook is built - this reads Rebecca's lakehouse, and a tool that can casually write to
it has no business existing. That is a guard against a slip, not against an adversary;
anyone who wants to write can edit a deploy script.

This is deliberately NOT in the agents' allow-list. Arbitrary SQL is exactly the capability
an autonomous agent should not have against a live tenant.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import deploy as dp  # noqa: E402
import deploy_seeds as ds  # noqa: E402
import deploy_gold as dg  # noqa: E402
from make_notebooks import cell, notebook  # noqa: E402

NOTEBOOK_NAME = "cd_90_query"

# Statements that may begin a query. Everything else - INSERT, DROP, MERGE, CREATE, ALTER,
# REFRESH - is refused.
ALLOWED_STARTS = ("select", "with", "show", "describe", "explain")


def is_read_only(sql: str) -> bool:
    """True when every statement is a read.

    Comments are stripped first: `-- DROP TABLE x` is harmless, but a leading comment
    would otherwise hide the real first word from this check.
    """
    body = "\n".join(line.split("--", 1)[0] for line in sql.splitlines())
    statements = [s.strip() for s in body.split(";") if s.strip()]
    if not statements:
        return False
    return all(s.lower().startswith(ALLOWED_STARTS) for s in statements)


def build_notebook(sql: str) -> dict:
    statements = [s.strip() for s in
                  "\n".join(l.split("--", 1)[0] for l in sql.splitlines()).split(";")
                  if s.strip()]

    setup = f'''
import json

EX = "{dg.SILVER_ABFSS}"
CD = "{dg.CD_SILVER_ABFSS}"
DIAG = "/lakehouse/default/Files/_diag"

def register(prefix, root):
    """Expose a lakehouse's Delta tables as prefix_<name> temporary views."""
    try:
        names = [f.name.rstrip("/") for f in notebookutils.fs.ls(root)]
    except Exception as exc:
        print(f"  {{prefix}}: cannot list ({{exc}})")
        return 0
    n = 0
    for name in names:
        try:
            spark.sql(f"CREATE OR REPLACE TEMPORARY VIEW {{prefix}}_{{name}} "
                      f"AS SELECT * FROM delta.`{{root}}/{{name}}`")
            n += 1
        except Exception:
            pass          # not a Delta table, or unreadable - skip quietly
    print(f"  {{prefix}}: {{n}} table(s)")
    return n

register("ex", EX)
register("cd", CD)
results = []
'''

    cells = [cell(setup)]
    for i, statement in enumerate(statements):
        # `ex.foo` is friendlier to type than `ex_foo`; rewrite it here so the query text
        # reads like SQL against a schema.
        rewritten = statement.replace("ex.", "ex_").replace("cd.", "cd_")
        cells.append(cell(
            f'q = {json.dumps(rewritten)}\n'
            f'print("\\n--- query {i} ---")\n'
            'try:\n'
            '    df = spark.sql(q)\n'
            '    rows = [r.asDict() for r in df.limit(200).collect()]\n'
            '    results.append({"query": q[:400], "rows": rows})\n'
            '    for r in rows[:40]:\n'
            '        print("   ", r)\n'
            '    print(f"   ({len(rows)} row(s) shown)")\n'
            'except Exception as exc:\n'
            '    results.append({"query": q[:400], "error": str(exc)[:1000]})\n'
            '    print("   FAILED:", str(exc)[:400])\n'
        ))

    cells.append(cell(
        'import os\n'
        'os.makedirs(DIAG, exist_ok=True)\n'
        'with open(f"{DIAG}/query_result.json", "w", encoding="utf-8") as fh:\n'
        '    json.dump(results, fh, indent=1, default=str)\n'
        'print(f"\\nwrote {len(results)} result(s)")\n'
    ))
    return notebook(cells)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sql", nargs="?", help="SQL to run")
    parser.add_argument("--file", help="read SQL from a file instead")
    args = parser.parse_args()

    sql = Path(args.file).read_text(encoding="utf-8") if args.file else args.sql
    if not sql:
        parser.error("give SQL as an argument or --file")

    if not is_read_only(sql):
        print("REFUSED: only SELECT / WITH / SHOW / DESCRIBE / EXPLAIN are allowed here.")
        print("This tool reads the existing warehouse; it must not be able to write to it.")
        return 1

    tok = dp.token()
    lh = ds.lakehouse()          # gold, as the default lakehouse
    nb = ds.attach(build_notebook(sql), lh, dp.WORKSPACE_ID)

    definition = {"format": "ipynb", "parts": [
        {"path": "notebook-content.ipynb", "payload": ds.payload(nb),
         "payloadType": "InlineBase64"}]}

    existing = ds.find_item(tok, NOTEBOOK_NAME, "Notebook")
    if existing:
        status, _, headers = dp.call(
            "POST", f"/workspaces/{dp.WORKSPACE_ID}/items/{existing['id']}/updateDefinition",
            tok, {"definition": definition})
        if status == 202:
            dp.wait_for_operation(headers, tok)
        item_id = existing["id"]
    else:
        status, _, headers = dp.call(
            "POST", f"/workspaces/{dp.WORKSPACE_ID}/items", tok,
            {"displayName": NOTEBOOK_NAME, "type": "Notebook",
             "folderId": dp.FOLDER_ID, "definition": definition})
        if status == 202:
            dp.wait_for_operation(headers, tok)
        # Re-find rather than reading the operation result: a completed create operation
        # does not always carry the new item's id in its body, and the same pattern is
        # what every other deploy script here uses.
        item_id = ds.find_item(tok, NOTEBOOK_NAME, "Notebook")["id"]

    print(f"running {NOTEBOOK_NAME} ...", flush=True)
    ds.run_notebook(tok, item_id)

    results = dg.fetch_diagnostics(lh["id"], "query_result.json")
    if not results:
        print("no results file - check the notebook output in Fabric")
        return 1

    for i, r in enumerate(results):
        print(f"\n--- query {i} ---")
        if "error" in r:
            print("  FAILED:", r["error"][:500])
            continue
        rows = r.get("rows", [])
        if not rows:
            print("  (no rows)")
            continue
        for row in rows[:40]:
            print("  ", {k: v for k, v in row.items()})
        if len(rows) > 40:
            print(f"   ... {len(rows) - 40} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
