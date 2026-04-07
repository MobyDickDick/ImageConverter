from __future__ import annotations

from src.iCCModules import imageCompositeConverterQualityThreshold as quality_threshold_helpers


def test_resolve_allowed_error_uses_successful_threshold_by_default() -> None:
    rows = [
        {"variant": "A", "error_per_pixel": 0.4},
        {"variant": "B", "error_per_pixel": 0.1},
        {"variant": "C", "error_per_pixel": 0.2},
    ]

    allowed, source, successful, initial = quality_threshold_helpers.resolveAllowedErrorPerPixelImpl(
        rows,
        {},
        quality_sort_key_fn=lambda row: float(row["error_per_pixel"]),
        successful_threshold_fn=lambda _rows: 0.25,
    )

    assert allowed == 0.25
    assert source == "successful-conversions-mean-plus-2std"
    assert successful == 0.25
    assert initial == 0.1


def test_resolve_allowed_error_falls_back_to_initial_and_manual_override() -> None:
    rows = [
        {"variant": "A", "error_per_pixel": 0.5},
        {"variant": "B", "error_per_pixel": 0.3},
        {"variant": "C", "error_per_pixel": 0.4},
    ]

    allowed_fallback, source_fallback, successful_fallback, initial_fallback = quality_threshold_helpers.resolveAllowedErrorPerPixelImpl(
        rows,
        {},
        quality_sort_key_fn=lambda row: float(row["error_per_pixel"]),
        successful_threshold_fn=lambda _rows: float("inf"),
    )
    assert allowed_fallback == 0.3
    assert source_fallback == "initial-first-tercile"
    assert successful_fallback == 0.3
    assert initial_fallback == 0.3

    allowed_manual, source_manual, *_ = quality_threshold_helpers.resolveAllowedErrorPerPixelImpl(
        rows,
        {"allowed_error_per_pixel": "0.42"},
        quality_sort_key_fn=lambda row: float(row["error_per_pixel"]),
        successful_threshold_fn=lambda _rows: float("inf"),
    )
    assert allowed_manual == 0.42
    assert source_manual == "manual-config"
