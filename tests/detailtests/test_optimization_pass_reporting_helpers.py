from __future__ import annotations

from src.iCCModules import imageCompositeConverterOptimizationPassReporting as reporting_helpers


def test_quality_pass_prefers_lower_spatial_score_over_lower_mean_alone() -> None:
    old_row = {
        "error_per_pixel": 2.0,
        "mean_delta2": 100.0,
        "spatial_quality_score": 130.0,
    }
    new_row = {
        "error_per_pixel": 1.9,
        "mean_delta2": 95.0,
        "spatial_quality_score": 160.0,
    }

    improved, decision, *_ = reporting_helpers.evaluateQualityPassCandidateImpl(old_row, new_row)

    assert improved is False
    assert decision == "rejected_spatial_regression"


def test_quality_pass_accepts_better_distributed_difference_pattern() -> None:
    old_row = {
        "error_per_pixel": 2.0,
        "mean_delta2": 100.0,
        "spatial_quality_score": 160.0,
    }
    new_row = {
        "error_per_pixel": 2.1,
        "mean_delta2": 102.0,
        "spatial_quality_score": 130.0,
    }

    improved, decision, *_ = reporting_helpers.evaluateQualityPassCandidateImpl(old_row, new_row)

    assert improved is True
    assert decision == "accepted_spatial_improvement"
