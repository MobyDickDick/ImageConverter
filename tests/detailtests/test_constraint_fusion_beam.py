from __future__ import annotations

from copy import deepcopy

import pytest

from tools.constraint_fusion_beam import build_constraint_fusion_beam


def _constraints(kind: str = "circle", **extra):
    return {
        "schema_version": "description_geometry_constraints_v1",
        "elements": [{"id": "shape", "kind": kind, **extra}],
        "relations": [],
    }


def _candidate(kind: str, x: int, confidence: float, pixel_error: float, **geometry):
    return {
        "kind": kind,
        "bbox": {"x": x, "y": 4, "width": 12, "height": 12},
        "center": {"x": x + 6, "y": 10},
        "geometry": {"x": x, **geometry},
        "confidence": confidence,
        "pixel_error": pixel_error,
        "source": "neutral_detector",
    }


def test_beam_retains_three_ranked_semantically_valid_hypotheses() -> None:
    candidates = [
        _candidate("circle", 20, 0.8, 0.1),
        _candidate("ring", 10, 0.9, 0.2),
        _candidate("circle", 30, 0.7, 0.05),
        _candidate("rectangle", 40, 0.99, 0.0),
    ]

    record = build_constraint_fusion_beam(_constraints(), candidates)

    assert record["schema_version"] == "constraint_fusion_beam_v1"
    assert record["status"] == "resolved"
    assert [item["rank"] for item in record["hypotheses"]] == [1, 2, 3]
    assert all(item["primitive_type"] == "circle" for hypothesis in record["hypotheses"] for item in hypothesis["assignments"])
    assert record["hypotheses"][0]["confidence"] == 0.9
    assert any("primitive_type:rectangle!=circle" in item["reasons"] for item in record["rejected_candidates"])


def test_connector_direction_is_a_hard_constraint_not_a_pixel_tradeoff() -> None:
    candidates = [
        _candidate("line", 10, 0.8, 0.4, direction="right"),
        _candidate("line", 20, 1.0, 0.0, direction="left"),
        _candidate("line", 30, 0.7, 0.5, direction="right"),
        _candidate("line", 40, 0.6, 0.6, direction="right"),
    ]

    record = build_constraint_fusion_beam(
        _constraints("line", connector_direction="right"), candidates
    )

    assert len(record["hypotheses"]) == 3
    selected = record["hypotheses"][0]["assignments"][0]["candidate_id"]
    wrong = next(
        item["candidate_id"]
        for item in record["rejected_candidates"]
        if "connector_direction:left!=right" in item["reasons"]
    )
    assert selected != wrong


def test_missing_required_text_signal_is_reproducible_semantic_conflict() -> None:
    record = build_constraint_fusion_beam(
        _constraints("TextGlyph"), [_candidate("circle", 10, 1.0, 0.0)]
    )

    assert record["status"] == "semantic_conflict"
    assert record["hypotheses"] == []
    assert record["selected_hypothesis_id"] is None
    assert record["conflicts"] == ["missing_compatible_evidence:shape"]


def test_source_filename_does_not_change_hypothesis_order() -> None:
    candidates = [
        _candidate("rectangle", 10, 0.9, 0.2),
        _candidate("rectangle", 20, 0.8, 0.1),
        _candidate("rectangle", 30, 0.7, 0.05),
    ]
    renamed = deepcopy(candidates)
    for candidate in renamed:
        candidate["source"] = "renamed_input.png"
        candidate["filename"] = "renamed_input.png"

    original_record = build_constraint_fusion_beam(_constraints("RectBorder"), candidates)
    renamed_record = build_constraint_fusion_beam(_constraints("RectBorder"), renamed)

    assert original_record["hypotheses"] == renamed_record["hypotheses"]


def test_beam_width_cannot_hide_the_three_hypothesis_contract() -> None:
    with pytest.raises(ValueError, match="at least three"):
        build_constraint_fusion_beam(_constraints(), [], beam_width=2)
