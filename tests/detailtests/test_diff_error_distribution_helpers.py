from __future__ import annotations

from src.iCCModules import imageCompositeConverterConversionExecution as conversion_execution_helpers


def test_diff_error_distribution_flags_connected_error_cluster() -> None:
    status, reason = conversion_execution_helpers._classifyDiffErrorDistribution(
        {
            "error_pixel_count": 12.0,
            "largest_error_pixel_cluster_fraction": 0.75,
            "error_pixel_cluster_excess": 0.65,
            "localized_error_fraction": 0.55,
        }
    )

    assert status == "structured"
    assert reason == "upper_quartile_error_pixels_form_large_connected_component"


def test_diff_error_distribution_accepts_random_like_residuals() -> None:
    status, reason = conversion_execution_helpers._classifyDiffErrorDistribution(
        {
            "error_pixel_count": 12.0,
            "largest_error_pixel_cluster_fraction": 0.16,
            "error_pixel_cluster_excess": 0.04,
            "localized_error_fraction": 0.42,
        }
    )

    assert status == "random_like"
    assert reason == "no_dominant_error_cluster_detected"
