from __future__ import annotations

from src.iCCModules import imageCompositeConverterConversionInitialPass as initial_pass_helpers


def test_initial_pass_prefers_template_transfer_and_updates_bestlist() -> None:
    result_map: dict[str, dict[str, object]] = {}
    conversion_bestlist_rows: dict[str, dict[str, object]] = {}
    snapshotted: list[tuple[str, dict[str, object]]] = []

    def _convert_one(_filename: str, *, iteration_budget: int, badge_rounds: int):
        assert iteration_budget == 3
        assert badge_rounds == 6
        return (
            {
                "filename": "AC0800_S.jpg",
                "variant": "AC0800_S",
                "error_per_pixel": 10.0,
            },
            False,
        )

    def _try_transfer(**_kwargs):
        return (
            {
                "filename": "AC0800_S.jpg",
                "variant": "AC0800_S",
                "error_per_pixel": 2.0,
            },
            {"decision": "accepted"},
        )

    stop_after_failure = initial_pass_helpers.runInitialConversionPassImpl(
        process_files=["AC0800_S.jpg"],
        result_map=result_map,
        existing_donor_rows=[{"filename": "AC0811_S.jpg", "error_per_pixel": 5.0}],
        conversion_bestlist_rows=conversion_bestlist_rows,
        folder_path="in",
        svg_out_dir="svg",
        diff_out_dir="diff",
        rng=object(),
        deterministic_order=True,
        base_iterations=3,
        convert_one_fn=_convert_one,
        try_template_transfer_fn=_try_transfer,
        is_conversion_bestlist_candidate_better_fn=lambda _previous, candidate: float(candidate["error_per_pixel"]) < 5.0,
        store_conversion_bestlist_snapshot_fn=lambda variant, row: snapshotted.append((variant, dict(row))),
        restore_conversion_bestlist_snapshot_fn=lambda _variant: None,
        choose_conversion_bestlist_row_fn=lambda row, _previous, _restored: row,
    )

    assert stop_after_failure is False
    assert result_map["AC0800_S.jpg"]["error_per_pixel"] == 2.0
    assert conversion_bestlist_rows["AC0800_S"]["error_per_pixel"] == 2.0
    assert snapshotted and snapshotted[0][0] == "AC0800_S"


def test_initial_pass_uses_restored_bestlist_row_when_candidate_not_better() -> None:
    restored = {"filename": "AC0800_S.jpg", "variant": "AC0800_S", "error_per_pixel": 1.0}

    result_map: dict[str, dict[str, object]] = {}
    conversion_bestlist_rows = {"AC0800_S": dict(restored)}
    restored_variants: list[str] = []

    stop_after_failure = initial_pass_helpers.runInitialConversionPassImpl(
        process_files=["AC0800_S.jpg"],
        result_map=result_map,
        existing_donor_rows=[],
        conversion_bestlist_rows=conversion_bestlist_rows,
        folder_path="in",
        svg_out_dir="svg",
        diff_out_dir="diff",
        rng=object(),
        deterministic_order=False,
        base_iterations=2,
        convert_one_fn=lambda _filename, *, iteration_budget, badge_rounds: (
            {"filename": "AC0800_S.jpg", "variant": "AC0800_S", "error_per_pixel": 4.0},
            False,
        ),
        try_template_transfer_fn=lambda **_kwargs: (None, None),
        is_conversion_bestlist_candidate_better_fn=lambda _previous, _candidate: False,
        store_conversion_bestlist_snapshot_fn=lambda _variant, _row: None,
        restore_conversion_bestlist_snapshot_fn=lambda variant: restored_variants.append(variant) or dict(restored),
        choose_conversion_bestlist_row_fn=lambda _row, _previous, restored_row: restored_row,
    )

    assert stop_after_failure is False
    assert restored_variants == ["AC0800_S"]
    assert result_map["AC0800_S.jpg"]["error_per_pixel"] == 1.0
