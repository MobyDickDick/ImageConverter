from __future__ import annotations

from src.iCCModules import imageCompositeConverterOptimizationPasses as pass_helpers


def test_select_open_quality_cases_filters_and_orders_descending() -> None:
    rows = [
        {"variant": "AC0800_S", "error_per_pixel": 0.8},
        {"variant": "AC0800_M", "error_per_pixel": 1.2},
        {"variant": "AC0800_L", "error_per_pixel": 2.4},
        {"variant": "AC0899_S", "error_per_pixel": float("inf")},
    ]

    selected = pass_helpers.selectOpenQualityCasesImpl(
        rows,
        allowed_error_per_pixel=1.0,
        skip_variants={"AC0800_L"},
    )

    assert [entry["variant"] for entry in selected] == ["AC0800_M"]


def test_compute_successful_conversions_error_threshold_uses_mean_plus_two_sigma() -> None:
    rows = [
        {"variant": "ac0800_s", "error_per_pixel": 1.0},
        {"variant": "AC0800_M", "error_per_pixel": 3.0},
        {"variant": "AC0800_L", "error_per_pixel": 11.0},
    ]

    threshold = pass_helpers.computeSuccessfulConversionsErrorThresholdImpl(
        rows,
        successful_variants=["AC0800_S", "AC0800_M"],
    )

    assert threshold == 4.0
