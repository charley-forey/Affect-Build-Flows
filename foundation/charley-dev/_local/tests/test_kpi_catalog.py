"""KPI explanations: catalog coverage, TMDL descriptions, the seed, report binding, freshness.

A card with no definition does not fail anything - it just leaves the reader guessing what
period and source a number describes. These make that a test failure instead.

Monthly model/report first, then the PQP modules are imported, because they override the
shared generators' globals on import.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
LOCAL = HERE.parent
CHARLEY_DEV = LOCAL.parent
sys.path.insert(0, str(LOCAL))
sys.path.insert(0, str(CHARLEY_DEV / "00-platform" / "lib"))

import deploy_model as dm  # noqa: E402
import deploy_report as dr  # noqa: E402
import dq  # noqa: E402
import kpi_catalog as kc  # noqa: E402

GAP_SQL = (CHARLEY_DEV / "02-transformation" / "sql" / "gold" / "45_dq_datagap.sql").read_text(encoding="utf-8")


def bound_measures() -> dict[str, set[str]]:
    """Measure -> page ids, for every measure any visual on any page binds."""
    out: dict[str, set[str]] = {}
    for _, builder, _ in dr.PAGES:
        pid, visuals = builder()
        for v in visuals + dr.chrome(pid, slicers=pid not in dr.DRILLTHROUGH):
            for name in re.findall(r'"_Measures\.([^"]+)"', json.dumps(v)):
                out.setdefault(name, set()).add(pid)
    return out


def check_model(label: str) -> None:
    catalog = kc.CATALOG[dm.MODEL_NAME]
    bound = bound_measures()
    missing = sorted(f"{m} (on {', '.join(sorted(p))})" for m, p in bound.items() if m not in catalog)
    assert not missing, f"{label}: card/chart measures with no kpi_catalog entry:\n  " + "\n  ".join(missing)
    names = {m[0] for m in dm.MEASURES}
    stale = sorted(set(catalog) - names)
    assert not stale, f"{label}: catalog entries for measures the model does not have: {stale}"
    unbound = sorted(set(catalog) - set(bound))
    assert not unbound, f"{label}: catalog entries no visual shows (remove or bind): {unbound}"
    for name, e in catalog.items():
        assert all(e[k] for k in ("definition", "formula", "period", "sources")), f"{label}/{name}: incomplete"
        assert not e["gap"] or f"'{e['gap']}'" in GAP_SQL, f"{label}/{name}: unknown gap category {e['gap']!r}"

    # Catalog -> TMDL description: every catalogued measure's /// line carries its definition
    # and period and still ends with the workbook lineage; uncatalogued measures are unchanged.
    dm.folder_for.__defaults__[0].clear()   # folder cache is per MEASURES list
    tmdl = dm.measures_tmdl()
    descriptions = {name: text for text, name in re.findall(r"^\t/// (.*)\n\tmeasure '([^']+)'", tmdl, re.M)}
    assert len(descriptions) == len(dm.MEASURES), f"{label}: a measure lost its description line"
    for name, _, _, origin in dm.MEASURES:
        text = descriptions[name]
        assert text.endswith(f"Replaces {origin}"), f"{label}/{name}: lineage dropped"
        if name in catalog:
            assert text.startswith(catalog[name]["definition"]) and catalog[name]["period"] in text, name
        else:
            assert text == f"Replaces {origin}", f"{label}/{name}: description changed without a catalog entry"
    print(f"  {label}: {len(bound)} bound measures catalogued, {len(catalog)} TMDL descriptions generated")


def check_report(label: str) -> None:
    with tempfile.TemporaryDirectory() as tmp, patch.object(dr, "REPORT_DIR", Path(tmp)):
        files = dr.build("00000000-0000-0000-0000-000000000000")
    page = json.loads(files[f"definition/pages/{dr.DEFINITIONS}/page.json"])
    assert page["visibility"] == "HiddenInViewMode" and page["displayName"] == "KPI Definitions"
    pids = {json.loads(c)["name"] for r, c in files.items() if r.endswith("/page.json")}
    visuals = {r: json.loads(c) for r, c in files.items() if r.endswith("visual.json")}
    buttons = {r.split("/")[2]: v for r, v in visuals.items() if v["visual"]["visualType"] == "actionButton"}
    assert set(buttons) == pids, f"{label}: pages without the definitions button: {pids - set(buttons)}"
    for pid, b in buttons.items():
        link = b["visual"]["visualContainerObjects"]["visualLink"][0]["properties"]
        kind = link["type"]["expr"]["Literal"]["Value"]
        if pid == dr.DEFINITIONS:
            assert kind == "'Back'", f"{label}: definitions page needs a Back button"
        else:
            assert kind == "'PageNavigation'" and \
                link["navigationSection"]["expr"]["Literal"]["Value"] == f"'{dr.DEFINITIONS}'", pid
    catalog = next(v for r, v in visuals.items() if f"/{dr.DEFINITIONS}/" in r and "seed_KpiCatalog" in json.dumps(v))
    where = catalog["filterConfig"]["filters"][0]
    assert where["field"]["Column"]["Property"] == "ModelName"
    assert where["filter"]["Where"][0]["Condition"]["In"]["Values"] == [[{"Literal": {"Value": f"'{dr.MODEL_NAME}'"}}]]
    fresh = json.dumps([v for r, v in visuals.items() if f"/{dr.DEFINITIONS}/" in r])
    assert '"meta_SourceFreshness"' in fresh and '"LastSuccessAt"' in fresh
    assert {"seed_KpiCatalog", "meta_SourceFreshness"} <= set(dm.MODEL_TABLES)
    assert dm.MODEL_NAME in {r["ModelName"] for r in kc.rows()}
    print(f"  {label}: hidden KPI Definitions page, header button on {len(pids)} pages, catalog filtered to {dm.MODEL_NAME!r}")


def test_seed() -> None:
    result = subprocess.run([sys.executable, str(LOCAL / "make_qc_seeds.py"), "--check"],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    from seedrunner import build
    con = build()
    try:
        got = dict(con.execute("SELECT ModelName, COUNT(*) FROM seed_KpiCatalog GROUP BY 1").fetchall())
        assert got == {m: len(e) for m, e in kc.CATALOG.items()}, got
        caveat = con.execute("SELECT Caveats FROM seed_KpiCatalog WHERE KpiName = 'Recordable Incidents'").fetchone()[0]
        assert "system of record" in caveat
        assert con.execute("SELECT COUNT(DISTINCT ModelName || KpiName) FROM seed_KpiCatalog").fetchone()[0] == sum(got.values())
    finally:
        con.close()
    import deploy_seeds
    nb = json.dumps(deploy_seeds.build_notebook())
    assert f"'seed_KpiCatalog': {len(kc.rows())}" in nb, "seed notebook does not assert the catalog count"
    print(f"  seed_KpiCatalog: {sum(got.values())} rows, --check current, seed notebook asserts the count")


def test_freshness() -> None:
    rows = {r["Source"]: r for r in dq.source_freshness([
        {"batch": "20260914T040238Z", "source_scope": "active_projects", "status": "complete"},
        {"batch": "20260913T040000Z", "source_scope": "active_projects", "status": "incomplete_scope"},
        {"batch": "20260914T050000Z", "source": "outbuild", "status": "failed"},
        {"batch": "not-a-batch", "source": "outbuild", "status": "complete"},
    ], sage_last_write="2026-09-14 06:04:13")}
    assert set(rows) == set(kc.FRESHNESS_SOURCES)
    assert rows["Procore"]["Batch"] == "20260914T040238Z" and rows["Procore"]["Status"] == "complete"
    assert rows["Outbuild"]["LastSuccessAt"] is None and rows["Outbuild"]["Status"] == "no successful extraction on record"
    assert rows["Sage"]["LastSuccessAt"] == "2026-09-14 06:04:13"

    # persist: unreadable evidence still writes one row per source, and publishes the schema.
    written = {}

    class Frame:
        def __init__(self, data, schema):
            written.update(data=data, schema=schema)
            self.write = self
        def format(self, value): return self
        def mode(self, value):
            assert value == "overwrite"
            return self
        def saveAsTable(self, name): written["table"] = name

    class Spark:
        read = property(lambda self: (_ for _ in ()).throw(OSError("no such path")))
        def sql(self, statement): raise RuntimeError("not a delta table")
        def createDataFrame(self, data, schema): return Frame(data, schema)
        def table(self, name):
            fields = [type("F", (), {"name": c.split()[0], "dataType": type("T", (), {"simpleString": lambda self: "string"})()})()
                      for c in dq.SOURCE_FRESHNESS_SCHEMA.split(",")]
            return type("S", (), {"schema": type("X", (), {"fields": fields})()})()

    with tempfile.TemporaryDirectory() as diag:
        (Path(diag) / "gold_schema.json").write_text("{}")
        assert dq.persist_source_freshness(Spark(), "abfss://bronze", "run1", diag) == 3
        assert "meta_SourceFreshness" in json.loads((Path(diag) / "gold_schema.json").read_text())
    assert written["table"] == "meta_SourceFreshness" and len(written["data"]) == 3
    assert all(r[1] is None and r[6] == "run1" for r in written["data"])

    import deploy_dq
    import deploy_gold
    source = "\n".join("".join(c["source"]) for c in deploy_dq.build_notebook()["cells"])
    assert source.index("persist_source_freshness") < source.index("dq.persist_heartbeat"), \
        "freshness must be written before the heartbeat marks the run checked"
    assert deploy_dq.BRONZE_ROOT in source
    gold = json.dumps(deploy_gold.build_notebook(deploy_gold.SOURCES["cd"]))
    assert '\\"meta_SourceFreshness\\"' in gold and '\\"seed_KpiCatalog\\"' in gold, "gold_schema.json would omit them"
    print("  meta_SourceFreshness: last success per source, later failures named, unreadable evidence recorded")


if __name__ == "__main__":
    check_model("Monthly")
    check_report("Monthly")
    test_seed()
    test_freshness()
    import deploy_model_qc  # noqa: F401,E402 - overrides dm globals
    import deploy_report_qc  # noqa: F401,E402 - overrides dr globals
    check_model("PQP")
    check_report("PQP")
    print("kpi catalog checks passed")
