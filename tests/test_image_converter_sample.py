"""Uploaded SVGs are real optimization inputs, with a measured no-regression contract."""
from __future__ import annotations

import io

from PIL import Image
import pytest

from src.imageConverterSample import prepare_sample, refine, render_svg

SAMPLE = b'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><circle cx="28" cy="33" r="17" fill="#884466" stroke="black" stroke-width="2"/></svg>'


@pytest.mark.parametrize("content", [
    b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
    b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>',
    b'<svg xmlns="http://www.w3.org/2000/svg"><image href="file:///C:/secret.png"/></svg>',
    b'<svg xmlns="http://www.w3.org/2000/svg"><rect fill="url(https://example.org/x)"/></svg>',
    b'<!DOCTYPE svg [<!ENTITY x "hello">]><svg/>',
    b'<html/>',
    b'not an svg',
])
def test_samples_reject_active_external_or_invalid_content(content):
    with pytest.raises((ValueError, SyntaxError)):
        prepare_sample(content, 64, 64)


def test_sample_uses_original_canvas_and_keeps_shapes():
    import xml.etree.ElementTree as ET
    root = ET.fromstring(prepare_sample(SAMPLE, 128, 96))
    assert root.get("width") == "128"
    assert root.get("height") == "96"
    assert root.get("viewBox") == "0 0 64 64"
    assert len(list(root)) == 1


def test_sample_refinement_measurably_improves_pixels_and_preserves_input(tmp_path):
    source, sample, output = (tmp_path / name for name in ("source.png", "sample.svg", "result.svg"))
    target_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><circle cx="32" cy="32" r="20" fill="#287ec4" stroke="black" stroke-width="2"/></svg>'
    Image.fromarray(render_svg(target_svg, 64, 64)).save(source)
    sample.write_bytes(SAMPLE)
    report = refine(source, sample, output, "Ein blauer Kreis mit schwarzem Rand.", 2)
    assert report["improved"]
    assert report["final_mse"] < report["initial_mse"] * 0.5
    assert report["accepted"] > 0
    assert output.is_file() and output.with_suffix(".json").is_file()
    assert sample.read_bytes() == SAMPLE
    assert "circle" in output.read_text()


def test_matching_sample_never_gets_worse_and_reports_description_conflict(tmp_path):
    source, sample, output = (tmp_path / name for name in ("source.png", "sample.svg", "result.svg"))
    sample.write_bytes(SAMPLE)
    Image.fromarray(render_svg(SAMPLE.decode(), 64, 64)).save(source)
    report = refine(source, sample, output, "Das Motiv enthält genau zwei Kreise, ohne Text.", 1)
    assert report["final_mse"] <= report["initial_mse"]
    assert report["description_error"]
    assert not report["passed"]


def test_gui_attaches_sample_and_carries_it_into_retry(tmp_path, monkeypatch):
    from src import imageConverterGui as gui
    monkeypatch.setattr(gui, "catalog_descriptions", lambda: {})
    manager = gui.Jobs(tmp_path / "jobs")
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), "white").save(buffer, "PNG")
    original = manager.upload("original.png", buffer.getvalue())
    attached = manager.attach_sample(original["id"], "vorher.svg", SAMPLE)
    assert attached["sample"] and attached["sample_name"] == "vorher.svg"
    manager.jobs[attached["id"]]["status"] = "done"
    monkeypatch.setattr(manager, "run", lambda job_id: None)
    retry = manager.start(attached["id"], "Ein Kreis", "quick")
    assert retry["id"] != attached["id"]
    assert retry["sample"]
    assert (manager.folder(retry["id"]) / "sample.svg").is_file()
    manager.cancel(retry["id"])
    removed = manager.attach_sample(retry["id"], "", None)
    assert not removed["sample"]
    assert (manager.folder(original["id"]) / "sample.svg").exists()
    manager.close()
