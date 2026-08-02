"""Report generation checks - the accessibility and chrome guarantees, asserted.

These are the properties that are invisible when they break. A missing alt text does not
error, a page without a month slicer looks fine, and a duplicated tabOrder just makes
keyboard navigation quietly wrong. Nothing here needs Fabric: build() is pure.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import deploy_report as dr  # noqa: E402


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
    files = dr.build("00000000-0000-0000-0000-000000000000")
    pages = _pages(files)
    assert len(pages) == len(dr.PAGES), f"{len(pages)} pages built, expected {len(dr.PAGES)}"

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
            assert right <= 1280 and bottom <= 720, (
                f"{pid}: visual {v['name']} runs off canvas "
                f"(to {right}x{bottom}, canvas is 1280x720)")

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


if __name__ == "__main__":
    test_report()
    print("report checks passed")
