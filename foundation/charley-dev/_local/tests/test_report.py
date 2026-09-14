"""Report generation checks - the accessibility and chrome guarantees, asserted.

These are the properties that are invisible when they break. A missing alt text does not
error, a page without a month slicer looks fine, and a duplicated tabOrder just makes
keyboard navigation quietly wrong. Nothing here needs Fabric: build() is pure.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import deploy_report as dr  # noqa: E402


def build_report():
    # Generation writes files; test IDs must never overwrite a deployable report binding.
    with tempfile.TemporaryDirectory() as tmp, patch.object(dr, "REPORT_DIR", Path(tmp)):
        return dr.build("00000000-0000-0000-0000-000000000000")


def _pages(files: dict[str, str]) -> dict[str, list[dict]]:
    """page id -> its visuals, from the generated file set."""
    out: dict[str, list[dict]] = {}
    for rel, content in files.items():
        parts = rel.split("/")
        # definition/pages/<pid>/visuals/<name>/visual.json
        if len(parts) == 6 and parts[1] == "pages" and parts[-1] == "visual.json":
            out.setdefault(parts[2], []).append(json.loads(content))
    return out


def test_report() -> None:
    files = build_report()
    pages = _pages(files)
    assert len(pages) == len(dr.PAGES), f"{len(pages)} pages built, expected {len(dr.PAGES)}"
    for _, builder, _ in dr.PAGES:
        pid, visuals = builder()
        names = [v["name"] for v in visuals + dr.chrome(pid, slicers=pid not in dr.DRILLTHROUGH)]
        assert len(names) == len(set(names)), f"{pid}: duplicate visual IDs overwrite content"
    for rel, content in files.items():
        if rel.endswith(".bookmark.json"):
            target = json.loads(content)["explorationState"]["activeSection"]
            assert target in pages, f"{rel}: bookmark targets missing page {target}"

    drill = set(dr.DRILLTHROUGH)
    total = 0
    for pid, visuals in sorted(pages.items()):
        total += len(visuals)

        # 1. Alt text on every visual. This was missing on 79 of 101 while the report's own
        #    accessibility checklist required it.
        for v in visuals:
            general = v["visual"].get("visualContainerObjects", {}).get("general", [])
            alt = general[0]["properties"]["altText"]["expr"]["Literal"]["Value"] if general else ""
            assert len(alt) > 4, f"{pid}: visual {v['name']} has no alt text"

        # 2. Tab order: present on every visual, and unique. Setting it on only some is
        #    worse than none - the rest fall back to z-order and the reader jumps around.
        orders = [v["position"].get("tabOrder") for v in visuals]
        assert all(o is not None for o in orders), f"{pid}: a visual has no tabOrder"
        assert len(set(orders)) == len(orders), f"{pid}: duplicate tabOrder"

        # 3. Every page a reader can navigate to carries BOTH slicers, synced. A report
        #    called "Monthly" with no month slicer cannot be set to a month.
        syncs = {v["visual"].get("syncGroup", {}).get("groupName") for v in visuals}
        if pid in drill:
            assert syncs == {None}, f"{pid}: drill-through page must not carry slicers"
        else:
            assert {"project", "month"} <= syncs, f"{pid}: missing a synced slicer"

        # 4. Everything fits on the canvas. A visual running off the bottom is invisible in
        #    a PDF export and silently clipped in the service - it does not error, it just
        #    is not there. Page 1 of this report is meant to be printed and circulated.
        for v in visuals:
            pos = v["position"]
            right, bottom = pos["x"] + pos["width"], pos["y"] + pos["height"]
            assert pos["x"] >= 0 and pos["y"] >= 0 and pos["width"] > 0 and pos["height"] > 0
            assert right <= 1280 and bottom <= 720, (
                f"{pid}: visual {v['name']} runs off canvas "
                f"(to {right}x{bottom}, canvas is 1280x720)")
        for i, left in enumerate(visuals):
            a = left["position"]
            for right in visuals[i + 1:]:
                b = right["position"]
                overlaps = (a["x"] < b["x"] + b["width"] and a["x"] + a["width"] > b["x"]
                            and a["y"] < b["y"] + b["height"] and a["y"] + a["height"] > b["y"])
                assert not overlaps, f"{pid}: overlapping visuals {left['name']} and {right['name']}"

        # 5. The footer, so an exported page states what it is a snapshot of - and nothing
        #    sitting underneath it. The footer is new, so any visual already occupying that
        #    corner would be silently covered rather than reported as a clash.
        refs = json.dumps(visuals)
        assert "Report Month Label" in refs and "Last Refresh" in refs, f"{pid}: no footer"
        foot = next(v for v in visuals if "Report Month Label" in json.dumps(v))
        fp = foot["position"]
        for v in visuals:
            if v is foot:
                continue
            pos = v["position"]
            overlaps = (pos["x"] < fp["x"] + fp["width"] and pos["x"] + pos["width"] > fp["x"]
                        and pos["y"] < fp["y"] + fp["height"]
                        and pos["y"] + pos["height"] > fp["y"])
            assert not overlaps, f"{pid}: visual {v['name']} sits under the footer"

    # 6. The validated theme is registered, not just sitting in the repo unused.
    report = json.loads(files["definition/report.json"])
    assert report["themeCollection"]["customTheme"]["type"] == "RegisteredResources"
    theme_path = f"StaticResources/RegisteredResources/{dr.THEME_NAME}.json"
    assert theme_path in files, "custom theme referenced but not written"
    theme = json.loads(files[theme_path])
    # The corrected RAG steps specifically - the point of registering it at all.
    assert (theme["good"], theme["neutral"], theme["bad"]) == ("#1B7F3B", "#B26A00", "#C62828")
    assert dr.AMBER == theme["neutral"], "generator amber drifted from the theme's"

    # 7. Apostrophes survive. 'the Excel's defects' unescaped truncates the literal.
    assert dr.lit("the Excel's")["expr"]["Literal"]["Value"] == "'the Excel''s'"

    print(f"  {len(pages)} pages, {total} visuals: alt text, tab order, slicers, footer, theme")


def test_report_refs() -> None:
    """Every field a visual asks for must exist in the model.

    A visual bound to a name the model does not have does not fail the deploy, does not
    fail the refresh, and does not appear in any log - it renders in the report as "There's
    something wrong with one or more fields". So it is invisible to everything except a
    person looking at that page.

    Two were live when this check was written: fct_ChangeOrder[Status], which has always
    been StatusLabel in gold, and [Approved Change Orders], a measure the Project Detail
    table asked for by name that had never been written. Both on the same visual.
    """
    import re

    import deploy_model as dm

    model = dm.MODEL_DIR / "definition" / "tables"
    known: dict[str, set[str]] = {}
    for tmdl in model.glob("*.tmdl"):
        text = tmdl.read_text(encoding="utf-8")
        table = re.search(r"^table\s+(.+)$", text, re.M)
        if not table:
            continue
        known[table.group(1).strip().strip("'")] = set(
            re.findall(r"^\tcolumn\s+(.+)$", text, re.M)
        )

    # New model tables can be reviewed before a live build publishes their Spark schema.
    # Validate their bindings against executed local SQL; live TMDL generation still
    # requires the actual Fabric schema and is checked separately.
    missing_tables = set(dm.MODEL_TABLES) - set(known) - {"meta_PipelineRun"}
    if missing_tables:
        from seedrunner import build
        con = build()
        try:
            for table in missing_tables:
                known[table] = {r[0] for r in con.execute(f'DESCRIBE "{table}"').fetchall()}
        finally:
            con.close()

    # Measures come from the generator rather than the committed tmdl, so a measure added
    # to MEASURES counts immediately instead of only after the next deploy writes it out.
    known.setdefault("_Measures", set()).update(m[0] for m in dm.MEASURES)
    assert len({m[0] for m in dm.MEASURES}) == len(dm.MEASURES), "duplicate measure name"
    for child, fk, parent, pk in dm.RELATIONSHIPS:
        assert fk in known.get(child, set()), f"missing relationship field {child}[{fk}]"
        assert pk in known.get(parent, set()), f"missing relationship field {parent}[{pk}]"
    for name, expression, _, _ in dm.MEASURES:
        for quoted, bare, prop in re.findall(r"(?:'([^']+)'|\b([A-Za-z_]\w*))\[([^\]]+)\]", expression):
            entity = quoted or bare
            assert prop in known.get(entity, set()), f"{name}: unknown field {entity}[{prop}]"

    files = build_report()
    pattern = re.compile(
        r'"Entity"\s*:\s*"([^"]+)"[^}]*\}\s*\}\s*,\s*"Property"\s*:\s*"([^"]+)"'
    )
    seen, broken = set(), []
    for rel, content in files.items():
        if not rel.endswith("visual.json"):
            continue
        page = rel.split("/")[2]
        for entity, prop in pattern.findall(content):
            seen.add((entity, prop))
            if entity not in known:
                broken.append(f"{page}: {entity} is not a table in the model")
            elif prop not in known[entity]:
                broken.append(f"{page}: {entity}[{prop}] does not exist")

    assert not broken, "report references fields the model does not have:\n  " + "\n  ".join(
        sorted(set(broken))
    )
    minimum = 50 if "--qc" in sys.argv else 100
    assert len(seen) > minimum, f"only {len(seen)} refs found - the pattern stopped matching"
    print(f"  {len(seen)} field references, all resolve against the model")


def test_schedule_grain():
    _, items = dr.page_schedule_quality()
    timeline = next(v["visual"] for v in items if v["name"] == dr.oid("schedule", "gantt"))
    assert timeline["visualType"] == "barChart"
    categories = timeline["query"]["queryState"]["Category"]["projections"]
    assert [p["field"]["Column"]["Property"] for p in categories] == ["ProjectKey", "ActivityKey", "MilestoneName"]
    assert all(p["active"] for p in categories)
    offset = timeline["objects"]["dataPoint"][0]
    assert offset["selector"]["metadata"] == timeline["query"]["queryState"]["Y"]["projections"][0]["queryRef"]
    assert offset["properties"]["fillTransparency"]["expr"]["Literal"]["Value"] == "100D"
    table = next(v["visual"] for v in items if v["name"] == dr.oid("schedule", "milestones"))
    columns = {p["field"]["Column"]["Property"] for p in table["query"]["queryState"]["Values"]["projections"]}
    assert {"ProjectKey", "ActivityKey", "CurrentStart", "CurrentFinish", "HasDateInversion"} <= columns


def test_qc_disclosures():
    import deploy_report_qc as qc
    import deploy_model as dm
    observations = json.dumps(qc.page_ncr())
    mockups = json.dumps(qc.page_submittals())
    assert "not only confirmed NCRs" in observations
    assert "not historical month-end backlog" in observations
    assert "not a confirmed mock-up register" in mockups
    names = {m[0] for m in dm.MEASURES}
    assert {"Total Observations", "Possible Mock-Ups"} <= names
    assert not {"Total NCRs", "Mock-Ups Registered"} & names
    native = json.dumps(qc.page_native_inspections())
    assert "not mapped to manual checklist templates" in native
    assert "exclude undated records" in native
    assert ("fct_ProcoreInspection", "InspectionDate", "dim_Date", "Date") in dm.RELATIONSHIPS
    assert ("fct_ProcoreInspectionItem", "InspectionLinkKey", "fct_ProcoreInspection", "InspectionLinkKey") in dm.RELATIONSHIPS
    assert "not a failed check" in json.dumps(qc.page_native_inspection_items())
    completion = dm.table_tmdl("fct_ProcoreInspection", [("SourcePercentComplete", "double")])
    assert "summarizeBy: none" in completion and "formatString: 0.##\n" in completion
    assert "unit and scale require confirmation" in completion


if __name__ == "__main__":
    if "--qc" in sys.argv:
        import deploy_model_qc
        import deploy_report_qc
    test_report()
    test_report_refs()
    if "--qc" not in sys.argv:
        test_schedule_grain()
    else:
        test_qc_disclosures()
    print("report checks passed")
