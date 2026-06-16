from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("numpy")

import numpy as np

from tools.perception_detection_contract import (
    PerceptionPrimitiveCandidate,
    fuse_description_constraints_with_perception_candidates,
)


def _constraints(kind: str, *, bbox: list[float] | None = None) -> dict[str, Any]:
    element: dict[str, Any] = {
        "id": "description_element_1",
        "kind": kind,
        "source": "description",
        "confidence": 0.8,
    }
    if bbox is not None:
        element["bbox"] = bbox
    return {
        "schema_version": "description_geometry_constraints_v1",
        "source": "description",
        "elements": [element],
        "relations": [],
        "uncertainty": {"status": "ok", "reasons": [], "confidence": 0.8},
    }


def _candidate(
    kind: str, *, confidence: float = 0.9, bbox: dict[str, float] | None = None
) -> PerceptionPrimitiveCandidate:
    bbox = bbox or {"x": 20.0, "y": 20.0, "width": 40.0, "height": 40.0}
    return PerceptionPrimitiveCandidate(
        schema_version="perception_primitive_candidate_v1",
        kind=kind,
        bbox=bbox,
        center={
            "x": bbox["x"] + bbox["width"] / 2.0,
            "y": bbox["y"] + bbox["height"] / 2.0,
        },
        geometry={
            "geometry_ir_bbox": [
                bbox["x"] / 100.0,
                bbox["y"] / 100.0,
                bbox["width"] / 100.0,
                bbox["height"] / 100.0,
            ],
            "stroke_width_px": 2.0,
        },
        color={
            "fill_hex": "#dddddd",
            "stroke_hex": "#555555",
            "fill_rgb": None,
            "stroke_rgb": None,
            "fill_confidence": 0.7,
            "stroke_confidence": 0.7,
        },
        confidence=confidence,
        roi={
            "type": "image",
            "hint": "synthetic",
            "bbox": {"x": 0.0, "y": 0.0, "width": 100.0, "height": 100.0},
        },
        evidence={"detector": "synthetic_neutral_detector"},
        source="ido08_neutral_fixture",
    )


def test_ido08_fusion_matches_agreeing_description_and_image_candidate() -> None:
    image = np.full((100, 100, 3), 255, dtype=np.uint8)

    fused = fuse_description_constraints_with_perception_candidates(
        image,
        _constraints("CircleBackground", bbox=[0.2, 0.2, 0.4, 0.4]),
        [_candidate("circle")],
    )

    assert fused["schema_version"] == "description_perception_fusion_v1"
    assert fused["status"] == "matched"
    assert fused["decisions"][0]["status"] == "matched"
    assert fused["geometry_ir"][0]["kind"] == "CircleBackground"
    assert fused["geometry_ir"][0]["fusion"]["confidence"] > 0.8


def test_ido08_fusion_keeps_description_constraint_when_image_evidence_is_missing() -> (
    None
):
    image = np.full((100, 100, 3), 255, dtype=np.uint8)

    fused = fuse_description_constraints_with_perception_candidates(
        image, _constraints("TextGlyph"), []
    )

    assert fused["status"] == "partial"
    assert fused["decisions"][0]["status"] == "missing_image_evidence"
    assert fused["geometry_ir"][0]["kind"] == "TextGlyph"


def test_ido08_fusion_marks_conflicting_description_and_image_evidence() -> None:
    image = np.full((100, 100, 3), 255, dtype=np.uint8)

    fused = fuse_description_constraints_with_perception_candidates(
        image,
        _constraints("CircleBackground", bbox=[0.0, 0.0, 0.15, 0.15]),
        [
            _candidate(
                "circle", bbox={"x": 70.0, "y": 70.0, "width": 20.0, "height": 20.0}
            )
        ],
    )

    assert fused["status"] == "contradiction"
    assert fused["decisions"][0]["status"] == "contradiction"
    assert fused["geometry_ir"][0]["fusion"]["confidence"] == 0.0


def test_ido08_fusion_reports_multiple_plausible_candidates_as_ambiguous() -> None:
    image = np.full((100, 100, 3), 255, dtype=np.uint8)
    candidates = [
        _candidate(
            "rectangle",
            confidence=0.9,
            bbox={"x": 10.0, "y": 10.0, "width": 20.0, "height": 20.0},
        ),
        _candidate(
            "rectangle",
            confidence=0.88,
            bbox={"x": 11.0, "y": 10.0, "width": 20.0, "height": 20.0},
        ),
    ]

    fused = fuse_description_constraints_with_perception_candidates(
        image, _constraints("RectBorder"), candidates
    )

    assert fused["status"] == "ambiguous"
    assert fused["decisions"][0]["status"] == "ambiguous"
    assert len(fused["decisions"][0]["alternatives"]) == 1
