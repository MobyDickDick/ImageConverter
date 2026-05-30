from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("cv2")
pytest.importorskip("numpy")

from tools.perception_detection_contract import detect_perception_candidates, run_contract_report
from tools.shape_detection_eval import make_synthetic_image


def test_contract_serializes_line_circle_and_rectangle_candidates() -> None:
    for primitive in ["line", "circle", "rectangle"]:
        image = make_synthetic_image(primitive, "synthetic")
        candidates = detect_perception_candidates(image, source="test_fixture")
        matching = [candidate for candidate in candidates if candidate.kind == primitive]
        assert matching, primitive
        serialized = matching[0].to_dict()
        assert serialized["schema_version"] == "perception_primitive_candidate_v1"
        assert serialized["kind"] == primitive
        assert serialized["confidence"] > 0
        assert set(serialized) == {
            "schema_version",
            "kind",
            "bbox",
            "center",
            "geometry",
            "color",
            "confidence",
            "roi",
            "evidence",
            "source",
        }


def test_run_contract_report_writes_json_report(tmp_path: Path) -> None:
    summary = run_contract_report(tmp_path)
    assert summary["samples"] == 3
    assert summary["all_matched"] is True
    assert (tmp_path / "perception_detection_contract_v1_report.json").exists()
