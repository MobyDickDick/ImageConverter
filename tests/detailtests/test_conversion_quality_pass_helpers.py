from __future__ import annotations

from src.iCCModules import imageCompositeConverterConversionQualityPass as conversion_quality_pass_helpers


def test_run_quality_passes_updates_result_map_and_bestlist() -> None:
    result_map = {
        "AC0800_S.jpg": {"filename": "AC0800_S.jpg", "variant": "AC0800_S", "error_per_pixel": 0.8, "mean_delta2": 10.0}
    }
    quality_logs: list[dict[str, object]] = []
    conversion_bestlist_rows: dict[str, dict[str, object]] = {}
    store_calls: list[str] = []

    def _convert_one(filename: str, iteration_budget: int, badge_rounds: int):
        assert filename == "AC0800_S.jpg"
        assert iteration_budget == 7
        assert badge_rounds == 8
        return {
            "filename": filename,
            "variant": "AC0800_S",
            "error_per_pixel": 0.2,
            "mean_delta2": 5.0,
        }, False

    stop = conversion_quality_pass_helpers.runQualityPassesImpl(
        max_quality_passes=2,
        stop_after_failure=False,
        deterministic_order=True,
        rng=object(),
        base_iterations=5,
        allowed_error_per_pixel=0.5,
        skip_variants=set(),
        result_map=result_map,
        quality_logs=quality_logs,
        conversion_bestlist_rows=conversion_bestlist_rows,
        convert_one_fn=_convert_one,
        select_open_quality_cases_fn=lambda rows, **_kwargs: rows,
        select_middle_lower_tercile_fn=lambda _rows: [],
        iteration_strategy_for_pass_fn=lambda _pass_idx, _base: (7, 8),
        adaptive_iteration_budget_for_quality_row_fn=lambda _row, planned: planned,
        evaluate_quality_pass_candidate_fn=lambda _old, new: (True, "improved", 0.8, float(new["error_per_pixel"]), 10.0, 5.0),
        store_conversion_bestlist_snapshot_fn=lambda variant, _row: store_calls.append(variant),
        restore_conversion_bestlist_snapshot_fn=lambda _variant: None,
        before_pass_fn=lambda _pass_idx: None,
    )

    assert stop is False
    assert result_map["AC0800_S.jpg"]["error_per_pixel"] == 0.2
    assert conversion_bestlist_rows["AC0800_S"]["error_per_pixel"] == 0.2
    assert store_calls == ["AC0800_S", "AC0800_S"]
    assert len(quality_logs) == 2


def test_run_quality_passes_restores_snapshot_when_not_improved() -> None:
    result_map = {
        "AC0838_M.jpg": {"filename": "AC0838_M.jpg", "variant": "AC0838_M", "error_per_pixel": 0.4, "mean_delta2": 4.0}
    }
    restored: list[str] = []

    stop = conversion_quality_pass_helpers.runQualityPassesImpl(
        max_quality_passes=1,
        stop_after_failure=False,
        deterministic_order=True,
        rng=object(),
        base_iterations=4,
        allowed_error_per_pixel=0.6,
        skip_variants=set(),
        result_map=result_map,
        quality_logs=[],
        conversion_bestlist_rows={},
        convert_one_fn=lambda _filename, **_kwargs: (
            {"filename": "AC0838_M.jpg", "variant": "AC0838_M", "error_per_pixel": 0.5, "mean_delta2": 6.0},
            False,
        ),
        select_open_quality_cases_fn=lambda rows, **_kwargs: rows,
        select_middle_lower_tercile_fn=lambda _rows: [],
        iteration_strategy_for_pass_fn=lambda _pass_idx, _base: (4, 6),
        adaptive_iteration_budget_for_quality_row_fn=lambda _row, planned: planned,
        evaluate_quality_pass_candidate_fn=lambda _old, _new: (False, "kept", 0.4, 0.5, 4.0, 6.0),
        store_conversion_bestlist_snapshot_fn=lambda _variant, _row: None,
        restore_conversion_bestlist_snapshot_fn=lambda variant: restored.append(variant),
    )

    assert stop is False
    assert restored == ["AC0838_M"]


def test_run_quality_passes_continues_after_failed_candidate() -> None:
    result_map = {
        "AC0800_S.jpg": {"filename": "AC0800_S.jpg", "variant": "AC0800_S", "error_per_pixel": 0.8, "mean_delta2": 10.0},
        "AC0801_S.jpg": {"filename": "AC0801_S.jpg", "variant": "AC0801_S", "error_per_pixel": 0.9, "mean_delta2": 11.0},
    }

    def _convert_one(filename: str, **_kwargs):
        if filename == "AC0800_S.jpg":
            return None, True
        return ({"filename": filename, "variant": "AC0801_S", "error_per_pixel": 0.3, "mean_delta2": 4.0}, False)

    stop = conversion_quality_pass_helpers.runQualityPassesImpl(
        max_quality_passes=1,
        stop_after_failure=False,
        deterministic_order=True,
        rng=object(),
        base_iterations=5,
        allowed_error_per_pixel=0.5,
        skip_variants=set(),
        result_map=result_map,
        quality_logs=[],
        conversion_bestlist_rows={},
        convert_one_fn=_convert_one,
        select_open_quality_cases_fn=lambda rows, **_kwargs: rows,
        select_middle_lower_tercile_fn=lambda _rows: [],
        iteration_strategy_for_pass_fn=lambda _pass_idx, _base: (7, 8),
        adaptive_iteration_budget_for_quality_row_fn=lambda _row, planned: planned,
        evaluate_quality_pass_candidate_fn=lambda _old, new: (True, "improved", 0.9, float(new["error_per_pixel"]), 11.0, 4.0),
        store_conversion_bestlist_snapshot_fn=lambda _variant, _row: None,
        restore_conversion_bestlist_snapshot_fn=lambda _variant: None,
    )

    assert stop is True
    assert result_map["AC0801_S.jpg"]["error_per_pixel"] == 0.3


def test_run_quality_passes_refines_single_below_threshold_row() -> None:
    row = {
        "filename": "AC0820_L.jpg",
        "variant": "AC0820_L",
        "error_per_pixel": 0.25,
        "mean_delta2": 8.0,
    }
    converted: list[str] = []
    quality_logs: list[dict[str, object]] = []

    stop = conversion_quality_pass_helpers.runQualityPassesImpl(
        max_quality_passes=1,
        stop_after_failure=False,
        deterministic_order=True,
        rng=object(),
        base_iterations=5,
        allowed_error_per_pixel=1.0,
        skip_variants=set(),
        result_map={"AC0820_L.jpg": row},
        quality_logs=quality_logs,
        conversion_bestlist_rows={},
        convert_one_fn=lambda filename, **_kwargs: (
            converted.append(filename)
            or {**row, "error_per_pixel": 0.20, "mean_delta2": 6.0},
            False,
        ),
        select_open_quality_cases_fn=lambda _rows, **_kwargs: [],
        select_middle_lower_tercile_fn=lambda _rows: [],
        iteration_strategy_for_pass_fn=lambda _pass_idx, base: (base + 1, 7),
        adaptive_iteration_budget_for_quality_row_fn=lambda _row, planned: planned,
        evaluate_quality_pass_candidate_fn=lambda _old, _new: (True, "accepted_improvement", 0.25, 0.20, 8.0, 6.0),
        store_conversion_bestlist_snapshot_fn=lambda _variant, _row: None,
        restore_conversion_bestlist_snapshot_fn=lambda _variant: None,
    )

    assert stop is False
    assert converted == ["AC0820_L.jpg"]
    assert quality_logs[0]["decision"] == "accepted_improvement"


def test_run_quality_passes_does_not_force_isolated_skipped_variant() -> None:
    row = {
        "filename": "AC0820_L.jpg",
        "variant": "AC0820_L",
        "error_per_pixel": 0.25,
        "mean_delta2": 8.0,
    }

    stop = conversion_quality_pass_helpers.runQualityPassesImpl(
        max_quality_passes=1,
        stop_after_failure=False,
        deterministic_order=True,
        rng=object(),
        base_iterations=5,
        allowed_error_per_pixel=1.0,
        skip_variants={"AC0820_L"},
        result_map={"AC0820_L.jpg": row},
        quality_logs=[],
        conversion_bestlist_rows={},
        convert_one_fn=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("skipped variant retried")),
        select_open_quality_cases_fn=lambda _rows, **_kwargs: [],
        select_middle_lower_tercile_fn=lambda _rows: [],
        iteration_strategy_for_pass_fn=lambda _pass_idx, base: (base, 7),
        adaptive_iteration_budget_for_quality_row_fn=lambda _row, planned: planned,
        evaluate_quality_pass_candidate_fn=lambda _old, _new: (False, "rejected_regression", 0.25, 0.30, 8.0, 9.0),
        store_conversion_bestlist_snapshot_fn=lambda _variant, _row: None,
        restore_conversion_bestlist_snapshot_fn=lambda _variant: None,
    )

    assert stop is False


def test_run_quality_passes_extends_after_configured_max_until_first_non_improvement() -> None:
    row = {
        "filename": "AC0821_L.jpg",
        "variant": "AC0821_L",
        "error_per_pixel": 1.0,
        "mean_delta2": 10.0,
    }
    result_map = {"AC0821_L.jpg": row}
    quality_logs: list[dict[str, object]] = []
    errors = iter([0.8, 0.7, 0.75])

    def _convert_one(filename: str, **_kwargs):
        return {
            "filename": filename,
            "variant": "AC0821_L",
            "error_per_pixel": next(errors),
            "mean_delta2": 9.0,
        }, False

    def _evaluate(old, new):
        old_error = float(old["error_per_pixel"])
        new_error = float(new["error_per_pixel"])
        improved = new_error < old_error
        return (
            improved,
            "accepted_improvement" if improved else "rejected_regression",
            old_error,
            new_error,
            float(old["mean_delta2"]),
            float(new["mean_delta2"]),
        )

    stop = conversion_quality_pass_helpers.runQualityPassesImpl(
        max_quality_passes=2,
        stop_after_failure=False,
        deterministic_order=True,
        rng=object(),
        base_iterations=5,
        allowed_error_per_pixel=0.5,
        skip_variants=set(),
        result_map=result_map,
        quality_logs=quality_logs,
        conversion_bestlist_rows={},
        convert_one_fn=_convert_one,
        select_open_quality_cases_fn=lambda rows, **_kwargs: rows,
        select_middle_lower_tercile_fn=lambda _rows: [],
        iteration_strategy_for_pass_fn=lambda pass_idx, base: (base + pass_idx, 7),
        adaptive_iteration_budget_for_quality_row_fn=lambda _row, planned: planned,
        evaluate_quality_pass_candidate_fn=_evaluate,
        store_conversion_bestlist_snapshot_fn=lambda _variant, _row: None,
        restore_conversion_bestlist_snapshot_fn=lambda _variant: None,
        continue_after_max_if_improved=True,
    )

    assert stop is False
    assert [entry["pass"] for entry in quality_logs] == [1, 2, 3]
    assert quality_logs[-1]["improved"] is False
    assert result_map["AC0821_L.jpg"]["error_per_pixel"] == 0.7
