"""Derive an observed Sage 100 Contractor schema from our own Power Query.

Sage publishes no table schema (see ../INTEGRATION-NOTES.md). But the dataflow in
foundation/01-ingestion/Sage names real tables and, because every step enumerates the
columns it drops or renames, it also names most of their columns. This reads that M
code and emits OBSERVED-SCHEMA.md.

    python derive_schema.py [path/to/mashup.pq] [-o OBSERVED-SCHEMA.md]

"Observed" is the operative word: a column absent here just means our queries never
touched it. INFORMATION_SCHEMA on the live database remains the authority.
"""

import argparse
import collections
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PQ = os.path.normpath(
    os.path.join(HERE, "..", "..", "..", "foundation", "01-ingestion", "Sage",
                 "Build_Sage_Test.Dataflow", "mashup.pq")
)

# What each confirmed table is, read off the queries that select from it.
TABLE_NOTES = {
    "acpinv": "Accounts Payable invoices — header. Screen 4-2 Payable Invoices.",
    "acrinv": "Accounts Receivable invoices — header. Screen 3-2 Receivable Invoices.",
    "acppmt": "Accounts Payable payments (vendor payments). Screen 4-3.",
    "acrpmt": "Accounts Receivable payments / cash receipts. Screen 3-3-1.",
    "actpay": "Vendor master. Screen 4-4 Vendors.",
    "actrec": "Job / project master. Screen 3-5 Jobs.",
}


def queries(pq):
    """Split the M into (query_name, body) pairs."""
    parts = re.split(r"^shared\s+([A-Za-z_][\w]*)\s*=\s*", pq, flags=re.M)
    return list(zip(parts[1::2], parts[2::2]))


def source_table(body):
    m = re.search(r'Item\s*=\s*"([^"]+)"', body)
    return m.group(1) if m else None


def literal_lists(body, func):
    """Every {...} brace list passed to `func` in this query body."""
    out = []
    for m in re.finditer(re.escape(func) + r"\(", body):
        i = body.find("{", m.end())
        if i < 0:
            continue
        depth, j = 0, i
        while j < len(body):
            if body[j] == "{":
                depth += 1
            elif body[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        out.append(body[i:j + 1])
    return out


def columns_of(body):
    """Physical column names this query referenced, plus rename mappings.

    Original (physical) names are the ones dropped by RemoveColumns and the
    left-hand side of each RenameColumns pair. Right-hand sides are our labels,
    so they are reported separately rather than mistaken for schema.
    """
    physical, renames = set(), {}
    for lst in literal_lists(body, "Table.RemoveColumns"):
        physical |= set(re.findall(r'"([^"]+)"', lst))
    for lst in literal_lists(body, "Table.RenameColumns"):
        for old, new in re.findall(r'\{"([^"]+)",\s*"([^"]+)"\}', lst):
            physical.add(old)
            renames[old] = new
    # ExpandRecordColumn/ExpandTableColumn field lists are columns of the *related*
    # table reached through a navigation property, so they are real column names too.
    for func in ("Table.ExpandRecordColumn", "Table.ExpandTableColumn"):
        for lst in literal_lists(body, func):
            physical |= set(re.findall(r'"([^"]+)"', lst))

    # Reorder/Select lists enumerate the whole column set at that point in the
    # pipeline -- the richest source, and for actrec the only one. But by then some
    # columns carry our labels, so subtract anything we renamed to or added.
    ours = set(renames.values())
    ours |= set(re.findall(r'Table\.AddColumn\([^,]+,\s*"([^"]+)"', body))
    for func in ("Table.ReorderColumns", "Table.SelectColumns"):
        for lst in literal_lists(body, func):
            for n in re.findall(r'"([^"]+)"', lst):
                if n not in ours:
                    physical.add(n)

    # Power Query disambiguates expansion collisions as `name.1`; the base is real.
    physical = {re.sub(r"\.\d+$", "", n) for n in physical}
    return physical - ours, renames


def classify(names, known_tables=frozenset()):
    """Split observed names into scalar columns vs. navigation properties.

    The SQL Server connector surfaces foreign-key relationships as extra columns
    named `table(key)`, or bare `table` when the relationship is table-valued. That
    is how we learn table names we never queried directly. A bare name is treated as
    a navigation property only when it is a table we have seen named elsewhere --
    otherwise it stays a scalar column.
    """
    nav, scalar = {}, set()
    for n in sorted(names):
        m = re.fullmatch(r"([a-z_][a-z0-9_]{1,9})\(([^)]+)\)", n)
        if m:
            nav.setdefault(m.group(1), set()).add(m.group(2))
        elif n in known_tables:
            nav.setdefault(n, set()).add("table-valued")
        else:
            scalar.add(n)
    return scalar, nav


def known_table_names(tables, pq):
    """Every name we have evidence is a table, not a column."""
    known = set(tables)
    for names in tables.values():
        for n in names:
            m = re.fullmatch(r"([a-z_][a-z0-9_]{1,9})\(([^)]+)\)", n)
            if m:
                known.add(m.group(1))
    # ExpandTableColumn proves its target is a table-valued navigation property.
    known |= set(re.findall(r'Table\.ExpandTableColumn\([^,]+,\s*"([^"]+)"', pq))
    return known


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pq", nargs="?", default=DEFAULT_PQ)
    ap.add_argument("-o", "--out", default=os.path.join(HERE, "OBSERVED-SCHEMA.md"))
    args = ap.parse_args()

    pq = open(args.pq, encoding="utf8").read()
    server = re.search(r'Sql\.Database\("([^"]+)",\s*"([^"]+)"\)', pq)

    tables = collections.defaultdict(set)     # physical table -> observed names
    renames = collections.defaultdict(dict)
    used_by = collections.defaultdict(list)   # physical table -> query names
    nav_tables = collections.Counter()        # related table -> times referenced

    for name, body in queries(pq):
        tbl = source_table(body)
        if not tbl:
            continue
        cols, ren = columns_of(body)
        tables[tbl] |= cols
        renames[tbl].update(ren)
        used_by[tbl].append(name)

    known = known_table_names(tables, pq)
    for tbl in tables:
        _, nav = classify(tables[tbl], known)
        for related in nav:
            nav_tables[related] += 1

    lines = [
        "# Sage 100 Contractor — observed schema",
        "",
        "**Generated by `derive_schema.py`. Do not edit by hand.**",
        "",
        f"Derived from `{os.path.relpath(args.pq, os.path.join(HERE, '..', '..', '..')).replace(os.sep, '/')}` "
        "— the Power Query that already reads Sage in production.",
        "",
    ]
    if server:
        lines += [
            f"Source instance: `{server.group(1)}`, database `{server.group(2)}`, schema `dbo`.",
            "",
        ]
    lines += [
        "> **Observed, not complete.** A column missing here only means our queries never",
        "> touched it. `INFORMATION_SCHEMA` on the live database is still the authority —",
        "> see [../INTEGRATION-NOTES.md](../INTEGRATION-NOTES.md).",
        ">",
        "> Classification is deliberately conservative: a name is called a navigation",
        "> property only when we have proof (it appears as `table(key)`, or is expanded as a",
        "> table). Short names in the wider tables — `budget`, `jobcst`, `emptme`, `schedl`",
        "> and similar on `actrec` — are listed as scalar columns but are very likely",
        "> table-valued relationships too. `INFORMATION_SCHEMA.COLUMNS` settles it.",
        "",
        "## Confirmed tables",
        "",
        "| Table | What it holds | Scalar columns seen | Referenced by |",
        "|---|---|---|---|",
    ]
    for tbl in sorted(tables):
        scalar, _ = classify(tables[tbl], known)
        note = TABLE_NOTES.get(tbl, "")
        lines.append(f"| `dbo.{tbl}` | {note} | {len(scalar)} | {', '.join(sorted(used_by[tbl]))} |")

    lines += ["", "## Columns by table", ""]
    for tbl in sorted(tables):
        scalar, nav = classify(tables[tbl], known)
        lines += [f"### `dbo.{tbl}`", ""]
        if TABLE_NOTES.get(tbl):
            lines += [TABLE_NOTES[tbl], ""]
        lines += ["Observed columns:", "", "```"]
        row = []
        for c in sorted(scalar):
            row.append(c)
            if len(row) == 8:
                lines.append("  ".join(f"{x:<12}" for x in row).rstrip())
                row = []
        if row:
            lines.append("  ".join(f"{x:<12}" for x in row).rstrip())
        lines += ["```", ""]
        if renames[tbl]:
            lines += ["Names our model gives them:", "", "| Sage column | Our label |", "|---|---|"]
            lines += [f"| `{k}` | {v} |" for k, v in sorted(renames[tbl].items())]
            lines.append("")
        if nav:
            lines += [
                "Navigation properties (foreign keys the SQL connector exposes — each names a related table):",
                "",
                "| Related table | Via |",
                "|---|---|",
            ]
            lines += [f"| `{k}` | {', '.join(sorted(v))} |" for k, v in sorted(nav.items())]
            lines.append("")

    lines += [
        "## Related tables discovered through foreign keys",
        "",
        "Never queried directly, but named by navigation properties on the tables above.",
        "This is the closest thing we have to a table catalogue for the rest of the database.",
        "",
        "| Table | Reached from N confirmed tables |",
        "|---|---|",
    ]
    for tbl, n in sorted(nav_tables.items()):
        lines.append(f"| `{tbl}` | {n} |")
    lines.append("")

    with open(args.out, "w", encoding="utf8", newline="\n") as f:
        f.write("\n".join(lines))
    print(f"{args.out}: {len(tables)} confirmed tables, {len(nav_tables)} discovered via FKs")


def _selftest():
    """Smallest thing that fails if the M parsing breaks."""
    body = '''let
      Source = Sql.Database("HOST\\INST", "DB"),
      #"Navigation 1" = Source{[Schema = "dbo", Item = "acpinv"]}[Data],
      #"Removed columns" = Table.RemoveColumns(#"Navigation 1", {"_idnum", "jobphs", "jobphs(_idnum)"}),
      #"Renamed columns" = Table.RenameColumns(#"Removed columns", {{"vndnum", "Vendor_ID"}}),
      #"Expanded" = Table.ExpandRecordColumn(x, "y", {"apivln(recnum)"}, {"z"}),
      #"Added custom" = Table.AddColumn(x, "Entity", each "Build"),
      #"Reordered" = Table.ReorderColumns(x, {"invttl", "Vendor_ID", "Entity", "dscrpt.1"})
    in x;'''
    assert source_table(body) == "acpinv"
    cols, ren = columns_of(body)
    assert {"_idnum", "jobphs", "vndnum", "apivln(recnum)"} <= cols, cols
    # picked up from the reorder list...
    assert "invttl" in cols
    # ...but our own label and our added column must not be mistaken for Sage columns
    assert "Entity" not in cols and "Vendor_ID" not in cols, cols
    # collision suffix stripped back to the real name
    assert "dscrpt" in cols and "dscrpt.1" not in cols
    assert ren == {"vndnum": "Vendor_ID"}, ren
    known = known_table_names({"acpinv": cols}, body)
    scalar, nav = classify(cols, known)
    assert "apivln" in nav and "apivln(recnum)" not in scalar
    # bare "jobphs" is a table-valued nav property, not a scalar column
    assert "jobphs" in nav and "jobphs" not in scalar
    assert "vndnum" in scalar
    # "Vendor_ID" is our label, not a Sage column -- must not leak into the schema
    assert "Vendor_ID" not in cols
    print("selftest ok")


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        _selftest()
    else:
        main()
