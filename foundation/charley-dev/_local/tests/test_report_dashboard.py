"""AFFECT Weekly Dashboard (deploy_report_dashboard.py): accessibility, layout and bindings.

The generic report suite assumes a 1280 x 720 page and no overlaps at all. This report is
the deck's 1360 x 880 and deliberately layers values over card panels, so the same intents
are checked here against its own contract:

  - every visual has alt text and a unique tab position
  - everything sits on the 1360 x 880 canvas
  - FOREGROUND visuals never collide (decorative panels and bars sit underneath, z < 2000,
    and the text they carry is not a query)
  - every field and every pill colour measure exists in the model
  - the load contract: every page in pageOrder, every query alias declared, drill-through bound
  - every page states the week it reports and when the data is from
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import deploy_model as dm  # noqa: E402
import deploy_report as dr  # noqa: E402
import deploy_report_dashboard as rd  # noqa: E402
import test_report  # noqa: E402

CHECKS: list[str] = []


def build() -> dict[str, str]:
    with tempfile.TemporaryDirectory() as tmp, patch.object(rd, "REPORT_DIR", Path(tmp)):
        return rd.build("00000000-0000-0000-0000-000000000000")


def main() -> int:
    files = build()
    pages = test_report._pages(files)
    assert set(pages) == {pid for pid, _ in (b() for _, b, _ in rd.PAGES)}, sorted(pages)

    measures = {m[0] for m in dm.MEASURES}
    for pid, visuals in pages.items():
        names = [v["name"] for v in visuals]
        assert len(names) == len(set(names)), f"{pid}: duplicate visual ids"
        orders = [v["position"].get("tabOrder") for v in visuals]
        assert None not in orders and len(set(orders)) == len(orders), f"{pid}: tab order missing or repeated"
        for v in visuals:
            alt = v["visual"]["visualContainerObjects"]["general"][0]["properties"]["altText"]["expr"]["Literal"]["Value"]
            assert len(alt) > 4, f"{pid}: {v['name']} has no alt text"
            pos = v["position"]
            assert pos["x"] >= 0 and pos["y"] >= 0 and pos["x"] + pos["width"] <= rd.W \
                and pos["y"] + pos["height"] <= rd.H, f"{pid}: {v['name']} runs off the 1360 x 880 canvas"
        fg = [v for v in visuals if v["position"]["z"] >= 2000]
        for i, a in enumerate(fg):
            for b in fg[i + 1:]:
                pa, pb = a["position"], b["position"]
                if (pa["x"] < pb["x"] + pb["width"] and pa["x"] + pa["width"] > pb["x"]
                        and pa["y"] < pb["y"] + pb["height"] and pa["y"] + pa["height"] > pb["y"]):
                    raise AssertionError(f"{pid}: {a['name']} and {b['name']} overlap")
        refs = json.dumps(visuals)
        assert "Week Header" in refs, f"{pid}: the page does not say which week it reports"
        for m in re.findall(r'"Entity": "_Measures"\}\}, "Property": "([^"]+)"', refs):
            assert m in measures, f"{pid}: unknown measure {m}"
    CHECKS.append("alt text, unique tab order, canvas bounds and no foreground collisions on every page")

    exec_refs = json.dumps(pages["dsexec"])
    assert "Data As Of Header" in exec_refs, "executive page does not say when the data was built"
    assert "Portfolio Header" in json.dumps(pages["dsportfolio"]), "portfolio page has no header line"
    CHECKS.append("headers state the week and, on the executive page, when the data was built")

    # Bindings and load contract, with the generic suite's own checks pointed at this report.
    with patch.object(test_report, "build_report", build), patch.object(sys, "argv", [sys.argv[0], "--scorecard"]):
        test_report.test_report_refs()
        test_report.test_load_contract()
    CHECKS.append("every field resolves against the model; load contract and drill-through binding hold")

    # Pills: every conditional-format colour measure exists, and pairs a fill with an ink.
    pills = 0
    for visuals in pages.values():
        for v in visuals:
            for entry in v["visual"].get("objects", {}).get("values", []):
                props = entry.get("properties", {})
                if "backColor" in props:
                    for key in ("backColor", "fontColor"):
                        name = props[key]["solid"]["color"]["expr"]["Measure"]["Property"]
                        assert name in measures, name
                    pills += 1
    assert pills >= 8, pills
    CHECKS.append(f"{pills} pill columns: fill and text colour both from model measures")

    # The deck's TBD callouts stay honest: no sample number from the deck appears anywhere.
    blob = json.dumps(files)
    for sample in ("$74.8M", "$126.4M", "$89.2M", "Hudson Medical", "Eastside Residences", "0.62"):
        assert sample not in blob, f"deck sample value {sample} leaked into the report"
    CHECKS.append("no illustrative value from the deck appears in the report")

    for label in CHECKS:
        print(f"  ok  {label}")
    print(f"\ntest_report_dashboard: {len(CHECKS)} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
