import copy

import pytest

from tools.evaluate_satisfaction_gate import (
    BASELINE_SCHEMA_VERSION,
    evaluate_satisfaction,
    seal_baseline_manifest,
)


def _baseline():
    return seal_baseline_manifest(
        {
            "schema_version": BASELINE_SCHEMA_VERSION,
            "provenance": {
                "commit": "abc123",
                "seed": 0,
                "toolchain": {"python": "3.10.20"},
                "input_hashes": {"image": "deadbeef", "description": "feedface"},
            },
            "cases": {
                "neutral": {
                    "dimensions": {"width": 64, "height": 64},
                    "metrics": {
                        "error_per_pixel": 0.04,
                        "edge_alignment": 0.80,
                        "object_mask_iou": 0.80,
                        "connector_continuity": 1.0,
                        "semantic_score": 1.0,
                        "dimension_match": 1.0,
                    },
                }
            },
        }
    )


def _candidate():
    return {
        "neutral": {
            "status": "completed",
            "metrics": {
                "error_per_pixel": 0.03,
                "edge_alignment": 0.85,
                "object_mask_iou": 0.82,
                "connector_continuity": 1.0,
                "semantic_score": 1.0,
                "dimension_match": 1.0,
            },
            "combined_score": 0.90,
            "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><circle cx="32" cy="32" r="20"/></svg>',
        }
    }


def test_report_separates_completion_improvement_and_satisfaction():
    report = evaluate_satisfaction(_baseline(), _candidate())
    decision = report["cases"][0]
    assert decision["technically_completed"] is True
    assert decision["improved"] is True
    assert decision["satisfactory"] is True
    assert report == evaluate_satisfaction(_baseline(), _candidate())


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (lambda row: row["metrics"].update(semantic_score=0.0), "semantic_score_below_min"),
        (lambda row: row.update(svg='<svg width="64" height="64"><image href="x.png"/></svg>'), "embedded_raster_copy"),
        (lambda row: row.update(svg='<svg width="32" height="64"><circle/></svg>'), "svg_dimension_mismatch"),
    ],
)
def test_hard_rejections_cannot_be_satisfactory(mutation, reason):
    candidate = _candidate()
    mutation(candidate["neutral"])
    decision = evaluate_satisfaction(_baseline(), candidate)["cases"][0]
    assert decision["satisfactory"] is False
    assert reason in (
        decision["hard_rejections"] + decision["good_solution_gate"]["reasons"]
    )


def test_any_metric_regression_blocks_satisfaction():
    candidate = _candidate()
    candidate["neutral"]["metrics"]["connector_continuity"] = 0.99
    decision = evaluate_satisfaction(_baseline(), candidate)["cases"][0]
    assert decision["regressed_metrics"] == ["connector_continuity"]
    assert decision["improved"] is False
    assert decision["satisfactory"] is False


def test_modified_baseline_is_rejected():
    baseline = copy.deepcopy(_baseline())
    baseline["provenance"]["seed"] = 1
    with pytest.raises(ValueError, match="baseline_sha256 mismatch"):
        evaluate_satisfaction(baseline, _candidate())
