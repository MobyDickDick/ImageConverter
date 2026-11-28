"""Verify the downloadable teaching artifact using real rendering in CI."""
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from html.parser import HTMLParser

import cv2
import numpy as np
import pytest

from src.exploratory import Scene
from src.exploratory import adapters
from tools.exploratory_demo import generate


@pytest.mark.per_test_timeout(60, fail_on_timeout=True)
def test_gallery_preserves_measured_drafts_and_working_offline_links(tmp_path):
    report = generate(tmp_path)
    assert json.loads((tmp_path / "report.json").read_text(encoding="utf-8")) == report
    primitives, edits, automatic = report["examples"]
    assert primitives["pixel_quality_passed"]
    assert [d["scene_file"] for d in edits["drafts"]] == [
        f"draft-{i}-scene.json" for i in range(1, 6)]
    scenes = [Scene.from_dict(json.loads((tmp_path / "edits" / d["scene_file"]).read_text(
        encoding="utf-8"))) for d in edits["drafts"]]
    assert [len(s.objects) for s in scenes] == [2, 1, 2, 2, 2]
    assert scenes[2].object("panel").kind == "ellipse"
    assert scenes[3].object("panel").kind == "rect"
    assert [o.id for o in scenes[4].objects] == ["disk", "panel"]
    assert edits["pixel_quality_passed"] and edits["drafts"][-1]["best"]
    assert any(not d["quality"]["passed"] for d in edits["drafts"])
    assert not automatic["scripted"] and automatic["evaluated"] == 2
    assert not automatic["pixel_quality_passed"]
    assert automatic["stop_reason"] == "sources_exhausted"

    for example in report["examples"]:
        assert not example["released"] and not example["errors"]
        assert example["renderings"] == example["evaluated"] == len(example["drafts"])
        assert sum(d["best"] for d in example["drafts"]) == 1
        folder = tmp_path / example["key"]
        original = cv2.imread(str(folder / "original.png"))
        for draft in example["drafts"]:
            stem = draft["stem"]
            svg = (folder / f"{stem}.svg").read_text(encoding="utf-8")
            assert not any(n.tag.endswith("image") for n in ET.fromstring(svg).iter())
            raster = adapters.render(svg, original.shape[1], original.shape[0])
            np.testing.assert_array_equal(cv2.imread(str(folder / f"{stem}.png")), raster)
            quality, score = adapters.evaluate(original, raster, svg)
            assert quality == draft["quality"] and score == draft["score"]
            difference = np.clip(np.abs(original.astype(np.int16) - raster.astype(np.int16))
                                 * 4, 0, 255).astype(np.uint8)
            np.testing.assert_array_equal(
                cv2.imread(str(folder / f"{stem}-difference.png")), difference)
            if draft["best"]:
                assert (folder / "best.svg").read_text(encoding="utf-8") == svg

    class Links(HTMLParser):
        def handle_starttag(self, tag, attrs):
            for key, value in attrs:
                if key in {"src", "href"}:
                    assert not Path(value).is_absolute()
                    assert (tmp_path / value).is_file(), value

    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    Links().feed(html)
    assert "Nicht freigegeben" in html and "unzureichender Entwurf" in html
