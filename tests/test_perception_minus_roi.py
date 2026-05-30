from __future__ import annotations

from pathlib import Path

import pytest

cv2 = pytest.importorskip("cv2")
pytest.importorskip("numpy")

from tools.perception_detection_contract import detect_minus_candidates, description_hint_to_roi, run_minus_roi_report
from tools.shape_detection_eval import make_synthetic_image


def test_description_hint_limits_minus_detection_to_top_center_roi() -> None:
    image = make_synthetic_image("minus", "synthetic")
    roi = description_hint_to_roi(image, 'oben mittig ist ein "-"-Zeichen')

    assert roi["hint"] == "top+center"
    assert roi["bbox"]["y"] == 0
    assert roi["bbox"]["x"] > 0
    assert roi["bbox"]["width"] < image.shape[1]

    candidates = detect_minus_candidates(image, description='oben mittig ist ein "-"-Zeichen')
    assert candidates
    top = candidates[0].to_dict()
    assert top["kind"] == "horizontal_rule"
    assert top["geometry"]["orientation"] == "horizontal"
    assert top["geometry"]["text_equivalent"] == "-"
    assert top["geometry"]["geometry_ir_kind"] == "HorizontalRule"
    assert top["confidence"] > 0.7
    assert top["roi"]["hint"] == "top+center"


def test_real_ac0120_image_emits_horizontal_rule_candidate() -> None:
    image_path = Path("artifacts/images_to_convert/AC0120_L.jpg")
    image = cv2.imread(str(image_path))
    assert image is not None

    candidates = detect_minus_candidates(
        image,
        description='oben auf der vertikalen Symmetrieachse ein "+"- und ein "-"-Zeichen',
        source="test_real_ac0120",
    )

    assert candidates
    top = candidates[0].to_dict()
    assert top["kind"] == "horizontal_rule"
    assert top["bbox"]["width"] >= 8
    assert top["bbox"]["height"] <= 5
    assert top["roi"]["hint"] == "top+center"
    assert top["source"] == "test_real_ac0120"


def test_run_minus_roi_report_writes_synthetic_and_real_samples(tmp_path: Path) -> None:
    summary = run_minus_roi_report(tmp_path)

    assert summary["samples"] == 2
    assert summary["all_matched"] is True
    report = tmp_path / "perception_minus_roi_report_v1.json"
    assert report.exists()
