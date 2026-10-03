from pathlib import Path

from tools.evaluate_semantic_only_quality import _render_svg, evaluate_quality


SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">
<rect width="64" height="64" fill="white"/>
<circle cx="25" cy="32" r="18" fill="none" stroke="#333" stroke-width="3"/>
<text x="20" y="36" fill="#222">F</text>
<line x1="43" y1="32" x2="63" y2="32" stroke="#333" stroke-width="3"/>
</svg>"""


def _case(tmp_path: Path, svg: str = SVG) -> tuple[Path, Path]:
    candidate = tmp_path / "candidate.svg"
    candidate.write_text(svg, encoding="utf-8")
    rendered = _render_svg(candidate, 64, 64)
    from PIL import Image
    image = tmp_path / "input.png"
    Image.fromarray(rendered).save(image)
    return image, candidate


def test_perfect_saved_svg_reaches_ideal_metrics(tmp_path: Path) -> None:
    image, candidate = _case(tmp_path)
    report = evaluate_quality(image, candidate, "circle+text+connector")

    assert report["schema_version"] == "semantic_only_quality_report_v1"
    assert report["status"] == "measured"
    assert report["metrics"] == {
        "error_per_pixel": 0.0,
        "edge_alignment": 1.0,
        "object_mask_iou": 1.0,
        "connector_continuity": 1.0,
        "semantic_score": 1.0,
        "dimension_match": 1.0,
    }
    assert report["worst_error_region"]["bbox"] is None
    assert report["objects"]


def test_wrong_dimension_fails_only_dimension_metric(tmp_path: Path) -> None:
    image, _ = _case(tmp_path)
    wrong = SVG.replace('width="64" height="64"', 'width="32" height="64"')
    candidate = tmp_path / "wrong-dimension.svg"
    candidate.write_text(wrong, encoding="utf-8")

    report = evaluate_quality(image, candidate, "circle+text+connector")
    assert report["metrics"]["dimension_match"] == 0.5
    assert report["metrics"]["semantic_score"] == 1.0


def test_missing_primitive_fails_semantic_metric(tmp_path: Path) -> None:
    image, _ = _case(tmp_path)
    candidate = tmp_path / "missing.svg"
    candidate.write_text(SVG.replace('<text x="20" y="36" fill="#222">F</text>', ""), encoding="utf-8")

    report = evaluate_quality(image, candidate, "circle+text+connector")
    assert report["metrics"]["semantic_score"] == 2 / 3
    assert report["missing_semantics"] == ["text"]


def test_disconnected_connector_fails_continuity_metric(tmp_path: Path) -> None:
    image, _ = _case(tmp_path)
    candidate = tmp_path / "disconnected.svg"
    candidate.write_text(SVG.replace('x1="43"', 'x1="50"'), encoding="utf-8")

    report = evaluate_quality(image, candidate, "circle+text+connector")
    assert report["metrics"]["connector_continuity"] < 1.0


def test_unrenderable_svg_reports_unavailable_metrics_as_none(tmp_path: Path) -> None:
    image, _ = _case(tmp_path)
    invalid = tmp_path / "invalid.svg"
    invalid.write_text("<svg>", encoding="utf-8")

    report = evaluate_quality(image, invalid, "circle+text+connector")
    assert report["status"] == "not_reachable"
    assert set(report["metrics"].values()) == {None}
