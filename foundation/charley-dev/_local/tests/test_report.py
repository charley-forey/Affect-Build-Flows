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


def _lit(prop: dict) -> str:
    return prop["expr"]["Literal"]["Value"]


def _size(objects: dict, obj: str) -> float:
    return float(_lit(objects[obj][0]["properties"]["fontSize"]).rstrip("D"))


def test_text_fit() -> None:
    """Estimated rendered text against its container, so clipping fails offline.

    Every check in test_report passed while production clipped subtitles, section headers,
    card labels, table columns and the footer on nearly every page. On the canvas is not
    the same as legible. The estimate is deliberately simple (see deploy_report.text_px);
    what matters is that the generator and this check share it, so a longer note or a
    narrower card fails here instead of in a browser.
    """
    files = build_report()
    failures = []
    for pid, visuals in sorted(_pages(files).items()):
        for v in visuals:
            vis, pos = v["visual"], v["position"]
            w, h, vtype = pos["width"], pos["height"], vis["visualType"]
            where = f"{pid}/{vtype}"
            fail = failures.append

            if vtype == "textbox":
                run = vis["objects"]["general"][0]["properties"]["paragraphs"][0]["textRuns"][0]
                text, style = run["value"], run["textStyle"]
                size, bold = float(style["fontSize"].rstrip("pt")), style["fontWeight"] == "bold"
                need = dr.wrap_lines(text, size, w - 8, bold) * dr.line_px(size) + dr.TEXT_PAD
                if need > h or dr.longest_word_px(text, size, bold) > w - 8:
                    fail(f"{where} {text[:40]!r}: needs {need:.0f}px, box is {h}")
                continue

            title_props = vis.get("visualContainerObjects", {}).get("title", [{}])[0].get("properties")
            title = _lit(title_props["text"])[1:-1].replace("''", "'") if title_props else ""
            tsize = float(_lit(title_props["fontSize"]).rstrip("D")) if title_props else 0
            inner = w - dr.BOX_PAD
            title_lines = dr.wrap_lines(title, tsize, inner, bold=True) if title else 0
            if title and dr.longest_word_px(title, tsize, True) > inner:
                fail(f"{where} title {title!r}: a word is wider than the visual")

            if vtype == "card":
                name = vis["query"]["queryState"]["Values"]["projections"][0]["nativeQueryRef"]
                sample = dr.CARD_TEXT_SAMPLES.get(name, dr.NUMBER_SAMPLE)
                vsize = _size(vis["objects"], "labels")
                assert _lit(vis["objects"]["categoryLabels"][0]["properties"]["show"]) == "false"
                wraps = _lit(vis["objects"]["wordWrap"][0]["properties"]["show"]) == "true"
                value_lines = dr.wrap_lines(sample, vsize, inner) if wraps else 1
                if dr.longest_word_px(sample, vsize) > inner or (
                        not wraps and dr.text_px(sample, vsize) > inner):
                    fail(f"{where} {name}: value {sample!r} wider than the card")
                need = (dr.BOX_PAD + title_lines * dr.line_px(tsize)
                        + value_lines * dr.line_px(vsize))
                if need > h:
                    fail(f"{where} {title!r}: needs {need:.0f}px, card is {h}")
            elif vtype == "multiRowCard":
                names = [p["nativeQueryRef"] for p in vis["query"]["queryState"]["Values"]["projections"]]
                third = inner / len(names)
                vsize, lsize = _size(vis["objects"], "dataLabels"), _size(vis["objects"], "categoryLabels")
                for name in names:
                    sample = dr.CARD_TEXT_SAMPLES.get(name, "September 2026 - December 2026")
                    if dr.text_px(sample, vsize) > third or dr.text_px(name, lsize) > third:
                        fail(f"{where} footer {name}: wider than its third ({third:.0f}px)")
                if dr.BOX_PAD + dr.line_px(vsize) + dr.line_px(lsize) > h:
                    fail(f"{where} footer: value and label rows need more than {h}px")
            elif vtype == "slicer":
                assert _lit(vis["objects"]["data"][0]["properties"]["mode"]) == "'Dropdown'"
                if dr.BOX_PAD / 2 + dr.line_px(tsize) + dr.SLICER_BOX > h:
                    fail(f"{where} slicer {title!r}: title and dropdown need more than {h}px")
            else:
                if title_lines > 2:
                    fail(f"{where} title {title!r}: wraps to {title_lines} lines")
            if vtype in ("barChart", "clusteredBarChart") and h < 180:
                fail(f"{where} {title!r}: {h}px tall shows only a few bars")
            if vtype == "tableEx" and h < 150:
                fail(f"{where} {title!r}: {h}px tall shows only a few rows")

            if vtype in ("tableEx", "pivotTable") and "Columns" not in vis["query"]["queryState"]:
                widths = {c["selector"]["metadata"]: float(_lit(c["properties"]["value"]).rstrip("D"))
                          for c in vis["objects"]["columnWidth"]}
                groups = dr.table_columns(vis)
                total = sum(widths.get(g[0]["queryRef"], 0) for g in groups)
                if total > w - dr.TABLE_GUTTER:
                    fail(f"{where} {title!r}: columns total {total:.0f}px in {w}px")
                for p in (p for g in groups for p in g):
                    header = p.get("displayName", p["nativeQueryRef"])
                    if widths.get(p["queryRef"], 0) < dr.column_need(header):
                        fail(f"{where} {title!r}: column {header!r} narrower than its header")
    assert not failures, "text will clip:\n  " + "\n  ".join(failures)

    # The footer's worst-case status is the model's own longest literal, so the sample the
    # sizing uses cannot drift from what the DAX can actually return.
    import re
    import deploy_model as dm
    assert dr.CARD_TEXT_SAMPLES["Pipeline Status"] == max(
        re.findall(r'"([^"]*)"', dm.PIPELINE_STATUS_DAX), key=len)
    # Both reports print Last Refresh the same way (minutes, no seconds).
    here = Path(__file__).resolve().parent.parent
    fmts = {f: re.search(r'\("Last Refresh", [^\n]*?, (\'"[^"]+"\')', (here / f).read_text(encoding="utf-8")).group(1)
            for f in ("deploy_model.py", "deploy_model_qc.py")}
    assert len(set(fmts.values())) == 1, f"Last Refresh formats differ: {fmts}"
    print(f"  text fit: every textbox, title, card, slicer, footer and table column estimated to fit")


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
    # Written by the DQ gate from a schema string, not by SQL: take its columns from that string.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "00-platform" / "lib"))
    import dq
    known.setdefault(dq.SOURCE_FRESHNESS_TABLE, {c.split()[0] for c in dq.SOURCE_FRESHNESS_SCHEMA.split(",")})
    missing_tables = set(dm.MODEL_TABLES) - set(known) - {"meta_PipelineRun"}
    if missing_tables:
        from seedrunner import build
        con = build()
        try:
            if "fct_DailySnapshot" in missing_tables:
                # Written by the DQ gate, not the gold build: run its real capture SQL.
                import deploy_dq
                for statement in deploy_dq.snapshot_statements():
                    con.execute(statement.replace("{SNAPSHOT_DATE}", "2026-01-31").replace("{RUN_ID}", "test")
                                .replace(") USING DELTA", ")"))
            for table in missing_tables:
                known[table] = {r[0] for r in con.execute(f'DESCRIBE "{table}"').fetchall()}
        finally:
            con.close()

    # Measures come from the generator rather than the committed tmdl, so a measure added
    # to MEASURES counts immediately instead of only after the next deploy writes it out.
    known.setdefault("_Measures", set()).update(m[0] for m in dm.MEASURES)
    assert len({m[0] for m in dm.MEASURES}) == len(dm.MEASURES), "duplicate measure name"
    for child, fk, parent, pk in dm.RELATIONSHIPS + [r for r in dm.INACTIVE_RELATIONSHIPS
                                                     if r[0] in dm.MODEL_TABLES and r[2] in dm.MODEL_TABLES]:
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


def excludes_unmatched(v: dict) -> bool:
    """True if v carries the visual-level filter dim_Project[ProjectKey] <> "UNMATCHED"."""
    for f in v.get("filterConfig", {}).get("filters", []):
        condition = f["filter"]["Where"][0]["Condition"]
        if (f["field"]["Column"]["Expression"]["SourceRef"]["Entity"] == "dim_Project"
                and f["field"]["Column"]["Property"] == "ProjectKey"
                and condition.get("Not", {}).get("Expression", {}).get("In", {}).get("Values")
                == [[{"Literal": {"Value": "'UNMATCHED'"}}]]):
            return True
    return False


def test_report_formats():
    """Display fixes from the report-format audit: each one rendered a wrong number silently."""
    import deploy_model as dm
    visuals = {}
    for _, builder, _ in dr.PAGES:
        pid, items = builder()
        visuals.update({v["name"]: v for v in items})
    get = lambda page, key: visuals[dr.oid(page, key)]
    # Unlike measures side by side, never stacked into one bar.
    for page, key in (("overview", "budget_by_code"), ("costsvendors", "c_topcodes"), ("billing", "b_by_project")):
        assert get(page, key)["visual"]["visualType"] == "clusteredBarChart", key
    matrix = get("costsvendors", "c_matrix")["visual"]
    assert matrix["visualType"] == "pivotTable" and "Columns" not in matrix["query"]["queryState"]
    # The UNMATCHED project member is not a job: filtered from the project slicer and the
    # per-project portfolio comparisons, kept on the data-gap visuals that are about it.
    for key in ("pf_heatmap", "pf_money", "pf_ar_rank", "pf_coverage", "pf_uninsured"):
        assert excludes_unmatched(get("portfolio", key)), key
    slicer = dr.chrome("overview")[0]
    assert slicer["name"] == dr.oid("overview", "slicer_project") and excludes_unmatched(slicer)
    gaps = [v for v in visuals.values() if '"HasUnmatchedProject"' in json.dumps(v)]
    assert gaps and not any(excludes_unmatched(v) for v in gaps)
    overdue = get("safetyquality", "sq_overdue")
    assert overdue["filterConfig"]["filters"][0]["field"]["Column"]["Property"] == "IsPastDue"
    assert overdue["visual"]["query"]["sortDefinition"]["sort"][0]["direction"] == "Descending"
    assert overdue["visual"]["objects"]["total"][0]["properties"]["totals"]["expr"]["Literal"]["Value"] == "false"
    # Semantic fixes: remaining vs forecast variance, retainage sign, billing and insurance labels.
    financial = json.dumps(get("financial", "budget_table"))
    assert all(f'"{m}"' in financial for m in ("Budget Remaining", "Forecast Variance", "Forecast Status", "Budget Status"))
    assert "Budget Variance" not in json.dumps(visuals)
    assert "negative = Affect holds more" in json.dumps(get("billing", "b_net"))
    assert "Owner billed (net of retainage)" in json.dumps(get("billing", "b_period"))
    assert '"InsuranceCategory"' in json.dumps(get("insurance", "i_by_type"))
    assert "Latest Certificate Expiration" in json.dumps(get("insurance", "i_latest"))
    assert dr.CARD_TITLES["Total Paid"] == "Total Paid (on invoices sent in period)"
    assert "USERELATIONSHIP ( fct_Invoice[PaidDate], dim_Date[Date] )" in {m[0]: m[1] for m in dm.MEASURES}["Cash Received"]
    assert "isActive: false\n\tfromColumn: fct_Invoice.PaidDate" in dm.relationships_tmdl()
    co = json.dumps(get("projectdetail", "pd_co"))
    assert "Change Order Amount" in co, "pending change orders drop out of an approved-only table"
    # Month labels sort chronologically; day counts and fractions are never summed.
    date = dm.table_tmdl("dim_Date", [("MonthYear", "string"), ("MonthYearSort", "int64"), ("Year", "int64")])
    assert "sortByColumn: MonthYearSort" in date and "summarizeBy: sum" not in date
    milestone = dm.table_tmdl("fct_Milestone", [("PercentComplete", "double"), ("DaysPastDue", "int64"),
                                                ("Amount", "double")])
    assert milestone.count("summarizeBy: none") == 2 and "formatString: 0%" in milestone
    names = {m[0] for m in dm.MEASURES}
    assert {"Milestones Overdue %", "Avg Observation Days To Close", "Unmatched Billed Amount - All Projects"} <= names
    assert not {"Schedule Performance %", "Avg Observation Days Open", "Unmatched AR Amount - All Projects"} & names
    exprs = {m[0]: m[1] for m in dm.MEASURES}
    assert "COALESCE" not in exprs["Hours Worked"] and "All months" in exprs["Report Month Label"]

    # The independent expectations encode the same semantics: unmeasured safety is BLANK,
    # insurance follows a selected project's vendors, and With + Without = On Project.
    import validate_model as vm
    E = vm.monthly_expected()
    jan = "2026-01-01T00:00:00"
    data = dict(dim_Project=[{"ProjectKey": "a"}, {"ProjectKey": "b"}], dim_Date=[{"Date": jan, "MonthStart": jan}],
                dim_Vendor=[{"VendorKey": v} for v in (1, 2, 3)],
                fct_SafetyMonthly=[{"ProjectKey": "a", "MonthStart": jan, "RecordableIncidents": 0, "HoursWorked": 0.0}],
                bridge_ProjectVendor=[{"ProjectKey": "a", "VendorKey": 1}, {"ProjectKey": "a", "VendorKey": 2},
                                      {"ProjectKey": "b", "VendorKey": 3}],
                fct_VendorInsurance=[{"VendorKey": 1, "ExpiryStatus": "Expired"}, {"VendorKey": 3, "ExpiryStatus": "Expired"}])
    c = vm.Recompute(data, dm.RELATIONSHIPS)
    a = vm.Scope("a", None, None)
    assert E["Hours Worked"](c, a) is None and E["Recordable Incidents"](c, a) is None
    assert E["Certificates On File"](c, vm.PORTFOLIO) == 2 and E["Certificates On File"](c, a) == 1
    assert E["Vendors With Insurance"](c, a) + E["Vendors Without Insurance"](c, a) == E["Vendors On Project"](c, a)
    assert E["Report Month Label"](c, a) == "All months"

    # AP reconciliation: mapped job cost only, month ignored, BLANK variance when a side is blank.
    feb = "2026-02-01T00:00:00"
    ap = dict(dim_Project=[{"ProjectKey": "a"}, {"ProjectKey": "b"}],
              dim_Date=[{"Date": jan, "MonthStart": jan}, {"Date": feb, "MonthStart": feb}],
              fct_BudgetLine=[{"ProjectKey": "a", "MonthStart": jan, "SpentToDate": 100.0}],
              fct_ApInvoice=[
                  {"ProjectKey": "a", "MonthStart": jan, "LineTotal": 70.0, "IsJobCost": True, "IsErpOnlyVendor": False},
                  {"ProjectKey": "a", "MonthStart": feb, "LineTotal": 60.0, "IsJobCost": True, "IsErpOnlyVendor": True},
                  {"ProjectKey": "a", "MonthStart": jan, "LineTotal": 9.0, "IsJobCost": False, "IsErpOnlyVendor": False},
                  {"ProjectKey": None, "MonthStart": jan, "LineTotal": 500.0, "IsJobCost": True, "IsErpOnlyVendor": False},
                  {"ProjectKey": "b", "MonthStart": feb, "LineTotal": 5.0, "IsJobCost": True, "IsErpOnlyVendor": True}])
    c = vm.Recompute(ap, dm.RELATIONSHIPS)
    b, jan_only = vm.Scope("b", None, None), vm.Scope("a", jan, None)
    assert E["AP Job Cost"](c, a) == 130.0 and E["AP Job Cost"](c, jan_only) == 130.0
    assert E["AP Job Cost"](c, vm.PORTFOLIO) == 135.0, "unmapped AP must not reach the portfolio figure"
    assert E["ERP-only Vendor Cost"](c, a) == 60.0
    assert E["AP vs Procore Spent Variance"](c, a) == 30.0 and E["AP / Procore Spent Ratio"](c, a) == 1.3
    assert E["AP vs Procore Spent Variance"](c, b) is None and E["AP / Procore Spent Ratio"](c, b) is None
    exprs = {m[0]: m[1] for m in dm.MEASURES}
    assert "Spent To Date" not in exprs["AP Job Cost"] and "fct_ApInvoice" not in exprs["Spent To Date"]

    # Held sub retainage, recomputed without the gold flag: each commitment's latest approved
    # pay app, carried past a later unapproved one; owner rows and unapproved-only contracts
    # contribute nothing.
    def bill(key, contract, n, status, retainage, kind="Subcontractor"):
        return {"ProjectKey": "a", "MonthStart": jan, "BillingKey": key, "BillingType": kind,
                "ContractId": contract, "PeriodNumber": n, "PeriodEnd": f"2025-0{n + 4}-28T00:00:00",
                "StatusLabel": status, "RetainageHeld": retainage}
    billing = dict(dim_Project=[{"ProjectKey": "a"}], dim_Date=[{"Date": jan, "MonthStart": jan}],
                   fct_Billing=[bill("S1", "SC7", 1, "APPROVED", 4000.0), bill("S2", "SC7", 2, "APPROVED_AS_NOTED", 6000.0),
                                bill("S3", "SC7", 3, "UNDER_REVIEW", 9000.0), bill("S5", "SC8", 1, "PENDING_OWNER_APPROVAL", 700.0),
                                bill("O1", "SC7", 3, "APPROVED", 50.0, kind="Owner")])
    assert E["Retainage Held Sub"](vm.Recompute(billing, dm.RELATIONSHIPS), vm.PORTFOLIO) == 6000.0
    assert "IsLatestApprovedPeriod" in exprs["Retainage Held Sub"]


def test_qc_disclosures():
    import deploy_report_qc as qc
    import deploy_model as dm
    slicer = qc.chrome("qcportfolio")[0]
    assert slicer["name"] == dr.oid("qcportfolio", "slicer_project") and excludes_unmatched(slicer)
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
    test_text_fit()
    test_report_refs()
    if "--qc" not in sys.argv:
        test_schedule_grain()
        test_report_formats()
    else:
        test_qc_disclosures()
    print("report checks passed")
