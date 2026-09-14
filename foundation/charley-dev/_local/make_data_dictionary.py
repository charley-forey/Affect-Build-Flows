"""Generate _docs/data-dictionary.md from the code that defines the data.

    python make_data_dictionary.py            # write _docs/data-dictionary.md
    python make_data_dictionary.py --check    # fail if the committed dictionary is stale

Nothing here is typed by hand, so nothing here can drift from what actually runs:

  purpose, grain      the comment block above each CREATE in sql/gold and sql/snapshot
  primary key         unique_key rules in 02-transformation/dq/expectations.py
  columns, types      the committed TMDL; else the SQL DDL; else the SQL projection aliases
                      (marked "type unverified")
  upstream            FROM/JOIN identifiers, followed through source views into silver and
                      bronze. 01_source_views_cd.sql is the view file in use, so 00 is ignored.
  DQ rules            every expectation whose table is this table
  models, relations,  deploy_model.py and deploy_model_qc.py (the TMDL generators)
  measures            Table[Column] references parsed from the generators' DAX
  report usage        _docs/report-lineage.json visual bindings (regenerate it with
                      audit_solution.py; this script only reads it)
  known gaps          GapCategory literals in 45_dq_datagap.sql and the open decisions table
                      in _docs/validation-and-development-plan.md

Offline: no Fabric, no network. The output carries no timestamp so --check is meaningful.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHARLEY_DEV = HERE.parent
SQL = CHARLEY_DEV / "02-transformation" / "sql"
DOCS = CHARLEY_DEV / "_docs"
OUT = DOCS / "data-dictionary.md"
PLAN = DOCS / "validation-and-development-plan.md"
LINEAGE = DOCS / "report-lineage.json"
DATAGAP = SQL / "gold" / "45_dq_datagap.sql"

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(CHARLEY_DEV / "02-transformation" / "dq"))

# Readable diagrams need a human grouping; a gold table not listed here lands under
# "Shared and platform tables" in the index, so a new table is visible, never silently lost.
AREAS = {
    "Procore financial": ["dim_Project", "dim_Vendor", "dim_CostCode", "fct_BudgetLine",
                          "fct_ChangeOrder", "fct_Billing", "fct_DirectCost",
                          "fct_FinancialPeriod", "bridge_ProjectVendor",
                          "bridge_VendorCostCode", "fct_VendorInsurance"],
    "Sage AR/AP": ["fct_Invoice", "fct_ApInvoice", "seed_ProjectCrosswalk",
                   "dim_ProjectCrosswalk", "dim_VendorCrosswalk", "dim_CostCodeCrosswalk",
                   "dq_CrosswalkCandidate"],
    "Quality": ["fct_QualityItem", "fct_SafetyMonthly", "fct_RfiSubmittal", "fct_QcNcr",
                "fct_QcPunch", "fct_QcSubmittal", "fct_ProcoreInspection",
                "fct_ProcoreInspectionItem"],
    "Schedule": ["fct_Milestone"],
    "Manual registers": ["dim_Job"],  # plus every man_* table, added below
}
SHARED = "Shared and platform tables"

TARGET = re.compile(
    r"^(CREATE\s+(?:OR\s+REPLACE\s+)?(TEMP(?:ORARY)?\s+VIEW|TABLE)(?:\s+IF\s+NOT\s+EXISTS)?"
    r"|INSERT\s+(?:INTO|OVERWRITE)(?:\s+TABLE)?|MERGE\s+INTO)\s+(\w+)", re.I)
REFS = re.compile(r"\b(?:FROM|JOIN)\s+(?:delta\.`[^`]*/)?(\w+)", re.I)
SQL_TYPES = {"STRING", "INT", "BIGINT", "SMALLINT", "DOUBLE", "FLOAT", "DATE", "TIMESTAMP",
             "BOOLEAN", "DECIMAL", "SELECT", "WITH"}  # the last two follow CREATE TABLE x AS


def rel(path: Path) -> str:
    return path.relative_to(CHARLEY_DEV).as_posix()


def strip_comments(text: str) -> str:
    return re.sub(r"--[^\n]*", "", text)


def comment_block_above(text: str, pos: int) -> list[str]:
    """Contiguous `--` lines directly above `pos`, top to bottom, without the `--`."""
    lines = text[:pos].rstrip("\n").split("\n")
    block = []
    while lines and lines[-1].lstrip().startswith("--"):
        block.append(lines.pop().lstrip()[2:].strip())
    block.reverse()
    return [l for l in block if not l.startswith(("--", "=="))]  # drop ---- section rules ----


def first_paragraph(block: list[str]) -> str:
    para = []
    for line in block:
        if not line:
            if para:
                break
            continue
        para.append(line)
    text = " ".join(para)
    return re.sub(r"^(gold|snapshot):\s*(\S+\s+-\s+)?", "", text).strip()


def grain_of(block: list[str]) -> str:
    text = " ".join(l for l in block if l)
    m = re.search(r"\bgrain:\s*(.+?(?:\.(?=\s|$)|$))", text, re.I)
    if m:
        return m.group(1).strip()
    m = (re.search(r"\b(one row per .+?)(?:\.(?=\s|$)|\s-\s|,|$)", text, re.I)
         or re.search(r"\bat (?:the )?(\w+ grain)\b", text, re.I)
         or re.search(r"(?:^|,\s)((?:per|x) [\w ]+?)(?:\.(?=\s|$)|$)", first_paragraph(block)))
    return m.group(1).strip() if m else ""


def parse_sql() -> dict:
    """name -> {kind, files, refs, ddl, aliases, purpose, grain} for every SQL-produced object."""
    files = sorted((SQL / "gold").glob("*.sql")) + sorted((SQL / "snapshot").glob("*.sql"))
    files += [p for p in sorted((SQL / "silver").glob("*.sql")) if p.name != "00_source_views.sql"]
    objects: dict = {}
    for path in files:
        raw = path.read_text(encoding="utf-8")
        header = []
        for line in raw.split("\n"):
            if not line.startswith("--"):
                break
            header.append(line[2:].strip())
        created = []
        for stmt in strip_comments(raw).split(";"):
            m = TARGET.match(stmt.strip())
            if not m:
                continue
            verb, kind, name = m.group(1), m.group(2), m.group(3)
            obj = objects.setdefault(name, dict(kind="table", files=[], refs=set(), ddl=[],
                                                aliases=[], purpose="", grain=""))
            if verb.upper().startswith("CREATE"):
                obj["kind"] = "view" if kind and "VIEW" in kind.upper() else "table"
                created.append(name)
                body = stmt.strip()[m.end():]
                if body.lstrip().startswith("("):  # typed DDL
                    inner = body[body.index("(") + 1:body.rfind(")")]
                    obj["ddl"] = re.findall(r"^\s*(\w+)\s+([A-Z]+(?:\(\d+,\s*\d+\))?)", inner, re.M)
                else:
                    for alias in re.findall(r"\bAS\s+([A-Z]\w*)\b(?!\s*\()", body):
                        if alias.upper() not in SQL_TYPES and alias not in obj["aliases"]:
                            obj["aliases"].append(alias)
            if rel(path) not in obj["files"]:
                obj["files"].append(rel(path))
            obj["refs"] |= set(REFS.findall(stmt)) - {name}
        for name in created:
            obj = objects[name]
            if obj["purpose"]:
                continue
            pos = re.search(rf"CREATE[^;]*?\b{name}\b", raw).start()
            block = comment_block_above(raw, pos) if len(created) > 1 else []
            obj["purpose"] = first_paragraph(block) or first_paragraph(header)
            obj["grain"] = grain_of(block) or (grain_of(header) if len(created) == 1 else "")
    return objects


def layer(name: str) -> str:
    if name.startswith("cd_bronze_"):
        return "bronze"
    if name.startswith(("cd_silver_", "cd_dq_rejects")):
        return "silver"
    if name.startswith("sv_"):
        return "view"
    return "gold"


def direct_deps(name: str, objects: dict, seen: frozenset = frozenset()) -> set[str]:
    """Known dependencies of `name`, looking straight through intermediate (non sv_) views."""
    out = set()
    for ref in objects.get(name, {}).get("refs", ()):
        if ref in seen:
            continue
        known = ref in objects or ref.startswith("cd_bronze_")
        if not known:
            continue  # a CTE, an alias, or a word in a string
        if objects.get(ref, {}).get("kind") == "view" and not ref.startswith("sv_"):
            out |= direct_deps(ref, objects, seen | {name})
        else:
            out.add(ref)
    return out


def upstream(name: str, objects: dict) -> dict[str, set[str]]:
    found: dict[str, set[str]] = defaultdict(set)
    stack, seen = list(direct_deps(name, objects)), set()
    while stack:
        dep = stack.pop()
        if dep in seen:
            continue
        seen.add(dep)
        found[layer(dep)].add(dep)
        if layer(dep) != "gold":  # stop at other gold tables; they have their own section
            stack.extend(direct_deps(dep, objects))
    return found


def load_models() -> list[dict]:
    import deploy_model as dm

    def snapshot() -> dict:
        return dict(name=dm.MODEL_NAME, tables=list(dm.MODEL_TABLES),
                    relationships=[tuple(r[:4]) for r in dm.RELATIONSHIPS],
                    measures=[(m[0], m[1]) for m in dm.MEASURES], dir=Path(dm.MODEL_DIR))

    models = [snapshot()]
    import deploy_model_qc  # noqa: F401  rebinds deploy_model's globals to Model B
    models.append(snapshot())
    for model in models:
        model["types"] = {}
        for tmdl in sorted((model["dir"] / "definition" / "tables").glob("*.tmdl")):
            text = tmdl.read_text(encoding="utf-8")
            model["types"][tmdl.stem] = re.findall(
                r"^\tcolumn '?([^'\n]+?)'?\n(?:\t\t[^\n]*\n)*?\t\tdataType: (\w+)", text, re.M)
        model["refs"] = defaultdict(set)  # table -> measure names
        for mname, expr in model["measures"]:
            for quoted, bare, _col in re.findall(r"(?:'([^']+)'|\b([A-Za-z_]\w*))\s*\[([^\]]+)\]", expr):
                model["refs"][quoted or bare].add(mname)
    return models


def dq_rules() -> tuple[dict, dict]:
    import expectations
    rules, keys = defaultdict(list), defaultdict(list)
    for e in expectations.build_suite().expectations:
        rules[e.table].append((e.name, e.severity))
        if e.name.endswith(".unique"):
            m = re.search(r"GROUP BY (.+?) HAVING", e.failing_sql)
            if m:
                keys[e.table].append("(" + ", ".join(c.strip(" `") for c in m.group(1).split(",")) + ")")
    return rules, keys


def gold_tables(objects: dict, models: list[dict]) -> list[str]:
    src = (HERE / "deploy_gold.py").read_text(encoding="utf-8")
    listed = ast.literal_eval(re.search(r"^tables = (\[.*?\])\n", src, re.S | re.M).group(1))
    names = {n for n, o in objects.items()
             if o["kind"] == "table" and layer(n) == "gold"
             and any(f.startswith(("02-transformation/sql/gold", "02-transformation/sql/snapshot"))
                     for f in o["files"])}
    names |= set(listed)
    for model in models:
        names |= set(model["tables"])
    return sorted(names, key=str.lower)


def area_of(name: str) -> str:
    if name.startswith("man_"):
        return "Manual registers"
    return next((a for a, tables in AREAS.items() if name in tables), SHARED)


def mermaid(area: str, tables: list[str], objects: dict) -> list[str]:
    nodes: dict[str, set[str]] = defaultdict(set)
    edges: set[tuple[str, str]] = set()
    stack, seen = list(tables), set()
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        nodes[layer(node)].add(node)
        for dep in direct_deps(node, objects):
            if layer(dep) == "gold" and dep not in tables:
                continue  # other areas' gold tables would swamp the picture
            edges.add((dep, node))
            stack.append(dep)
    out = ["```mermaid", "flowchart LR"]
    for key, label in (("bronze", "Bronze"), ("silver", "Silver"), ("view", "Source views"),
                       ("gold", "Gold")):
        if nodes[key]:
            out.append(f'  subgraph {key}_layer["{label}"]')
            out += [f"    {n}" for n in sorted(nodes[key])]
            out.append("  end")
    out += [f"  {a} --> {b}" for a, b in sorted(edges)]
    out.append("```")
    return out


def datagap_categories() -> list[tuple[str, str, str]]:
    raw = DATAGAP.read_text(encoding="utf-8")
    found: dict[str, list] = {}
    for m in re.finditer(r"^(?:UNION ALL\s+)?SELECT\s+'([^']+)'(?:\s+AS GapCategory)?,\s*('([^']+)'|CASE)",
                         raw, re.M):
        category = m.group(1)
        source = m.group(3) or "varies by row"
        note = first_paragraph(comment_block_above(raw, m.start()))
        entry = found.setdefault(category, [set(), note])
        entry[0].add(source)
        entry[1] = entry[1] or note
    return [(c, ", ".join(sorted(s)), n) for c, (s, n) in found.items()]


def open_decisions() -> list[str]:
    text = PLAN.read_text(encoding="utf-8")
    m = re.search(r"^## Open business decisions.*?\n(.*?)(?=^## )", text, re.S | re.M)
    return [l for l in m.group(1).splitlines() if l.startswith("|")] if m else []


def cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def build() -> str:
    objects = parse_sql()
    models = load_models()
    rules, keys = dq_rules()
    tables = gold_tables(objects, models)
    lineage = json.loads(LINEAGE.read_text(encoding="utf-8"))
    bindings = {m["model"]: (m["report"], m["visual_bindings"]) for m in lineage["models"]}

    by_area: dict[str, list[str]] = defaultdict(list)
    for t in tables:
        by_area[area_of(t)].append(t)

    out = ["# Data dictionary", "",
           "Generated by `_local/make_data_dictionary.py` - do not edit by hand. CI runs "
           "`--check`, so a SQL, DQ or model change without regenerating fails the build.", "",
           f"{len(tables)} gold tables, {sum(len(m['measures']) for m in models)} measures across "
           f"{len(models)} semantic models, {sum(len(r) for r in rules.values())} DQ rules.", "",
           "Sources: SQL header comments (purpose, grain), `02-transformation/dq/expectations.py` "
           "(keys, rules), committed TMDL (types), `deploy_model*.py` (models, relationships, DAX), "
           "`_docs/report-lineage.json` (visual bindings - regenerate with `audit_solution.py`).", "",
           "## Contents", ""]
    for area in list(AREAS) + [SHARED]:
        out.append(f"- **{area}**: " + ", ".join(f"[{t}](#{t.lower()})" for t in by_area[area]))
    out += ["- [Known gaps and business decisions](#known-gaps-and-business-decisions)", "",
            "## Lineage by subject area", "",
            "Layers left to right: bronze, silver, source views (`sv_*`), gold. Intermediate "
            "silver views are collapsed; gold tables from other subject areas are omitted "
            "(see each table's upstream list).", ""]
    for area in AREAS:
        out += [f"### {area}", ""] + mermaid(area, by_area[area], objects) + [""]

    out += ["## Tables", ""]
    for t in tables:
        obj = objects.get(t, {})
        in_models = [m for m in models if t in m["tables"]]
        out += [f"### {t}", ""]
        out.append(f"- **Subject area:** {area_of(t)}")
        out.append(f"- **Purpose:** {obj.get('purpose') or 'Not produced by gold SQL (built by a seed, gate or pipeline step).'}")
        out.append(f"- **Grain:** {obj.get('grain') or 'Not stated in the SQL comments.'}")
        out.append("- **Primary key:** " + ("; ".join(keys[t]) + " (DQ unique rule)" if keys[t]
                                              else "No DQ unique rule."))
        out.append("- **Produced by:** " + (", ".join(f"`{f}`" for f in obj.get("files", [])) or "no SQL file"))
        up = upstream(t, objects) if obj else {}
        parts = [f"{label}: " + ", ".join(f"`{n}`" for n in sorted(up[key]))
                 for key, label in (("gold", "gold"), ("view", "source views"),
                                    ("silver", "silver"), ("bronze", "bronze")) if up.get(key)]
        out.append("- **Upstream:** " + ("; ".join(parts) if parts else "none (inline values or no SQL)"))
        out.append("- **Semantic models:** " + (", ".join(m["name"] for m in in_models) or "none"))
        rels = sorted({f"{a}[{b}] -> {c}[{d}]" for m in in_models
                       for a, b, c, d in m["relationships"] if t in (a, c)})
        out.append("- **Relationships:** " + ("; ".join(rels) if rels else "none"))
        for m in in_models:
            # the model exposes measures_anchor as '_Measures'
            measures = sorted(m["refs"].get("_Measures" if t == "measures_anchor" else t, set()))
            if measures:
                out.append(f"- **Measures referencing it ({m['name']}):** " + ", ".join(measures))
            report, visuals = bindings.get(m["name"], ("", []))
            pages: dict[str, set[str]] = defaultdict(set)
            for v in visuals:
                if (v["kind"] == "Column" and v["table"] == t) or (v["kind"] == "Measure" and v["field"] in measures):
                    pages[v["page"]].add(v["visual"])
            if pages:
                out.append(f"- **Report usage ({report}):** " +
                           ", ".join(f"{p} ({len(v)} visual{'s' if len(v) != 1 else ''})"
                                     for p, v in sorted(pages.items())))
        if rules[t]:
            out += ["", "| DQ rule | Severity |", "|---|---|"]
            out += [f"| {cell(n)} | {s} |" for n, s in sorted(rules[t])]
        typed = next((dict(m["types"][t]) for m in in_models if t in m["types"]), None)
        out += ["", "| Column | Type | Type source |", "|---|---|---|"]
        if typed:
            out += [f"| {c} | {ty} | TMDL |" for c, ty in typed.items()]
        elif obj.get("ddl"):
            out += [f"| {c} | {ty} | SQL DDL |" for c, ty in obj["ddl"]]
        elif obj.get("aliases"):
            out += [f"| {c} | - | type unverified (SQL projection) |" for c in obj["aliases"]]
        else:
            out.append("| - | - | no TMDL or SQL columns found |")
        out.append("")

    out += ["## Known gaps and business decisions", "",
            "### Data gap categories", "",
            f"Every `GapCategory` emitted by `{rel(DATAGAP)}` into `dq_DataGap`.", "",
            "| Category | Source system | Note |", "|---|---|---|"]
    out += [f"| {cell(c)} | {cell(s)} | {cell(n)} |" for c, s, n in datagap_categories()]
    out += ["", "### Open business decisions", "",
            f"Copied from `{rel(PLAN)}`.", ""] + open_decisions() + [""]
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="fail if the committed dictionary is stale")
    args = parser.parse_args()
    content = build()
    if args.check:
        current = OUT.read_text(encoding="utf-8").replace("\r\n", "\n") if OUT.exists() else ""
        if current != content:
            print(f"STALE: {rel(OUT)} - re-run make_data_dictionary.py without --check")
            return 1
        print(f"{rel(OUT)} up to date")
        return 0
    OUT.write_text(content, encoding="utf-8", newline="\n")
    print(f"wrote {rel(OUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
