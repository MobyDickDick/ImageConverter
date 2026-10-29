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


def test_inkscape_editor_metadata_is_removed_without_losing_geometry_or_styles():
    from xml.etree import ElementTree as ET
    content = b'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
      xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd" width="30" height="40" inkscape:version="1.4">
      <sodipodi:namedview><inkscape:grid/></sodipodi:namedview>
      <metadata><foreign xmlns="urn:editor">inert editor metadata</foreign></metadata>
      <rect x="3" y="4" width="8" height="8" transform="translate(1 2)" style="fill:#123456;stroke:#778899;stroke-width:0.3"/>
      </svg>'''
    prepared = prepare_sample(content, 30, 40)
    root = ET.fromstring(prepared)
    assert len(root) == 1
    assert 'inkscape' not in prepared and 'namedview' not in prepared and 'metadata' not in prepared
    rect = root[0]
    assert rect.get('transform') == 'translate(1 2)'
    assert rect.get('fill') == '#123456' and rect.get('stroke-width') == '0.3'


def test_foreign_visual_nodes_are_still_rejected():
    with pytest.raises(ValueError, match='nicht unterstütztes Element'):
        prepare_sample(b'<svg xmlns="http://www.w3.org/2000/svg"><rect xmlns="urn:unknown"/></svg>', 20, 40)


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
    assert report['evaluations'] == 1
    assert report['stop_reason'] == 'quality_target_reached'


def test_accepted_redraw_keeps_its_square_and_connected_geometry(tmp_path):
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    sample = root/'artifacts/converted_images/converted_svgs/AC0501_S_sia.svg'
    source = root/'artifacts/images_to_convert/AC0501_S_sia.jpg'
    output = tmp_path/'result.svg'
    report = refine(source, sample, output, 'Quadratische Kelle mit beiden Diagonalen und rundem Gelenk.', 2)
    assert report['passed'] and report['evaluations'] == 1
    assert output.read_text() == prepare_sample(sample.read_bytes(), 20, 40)


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
