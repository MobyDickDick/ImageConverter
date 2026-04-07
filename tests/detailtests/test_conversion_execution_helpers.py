from __future__ import annotations

from pathlib import Path

from src.iCCModules import imageCompositeConverterConversionExecution as conversion_execution_helpers


class _Cv2Stub:
    def __init__(self, image):
        self._image = image

    def imread(self, _path: str):
        return self._image


class _ImageStub:
    def __init__(self, shape: tuple[int, int, int]) -> None:
        self.shape = shape


def test_convert_one_impl_success_reads_convergence_and_delta2(tmp_path: Path) -> None:
    folder = tmp_path / "images"
    svg_out = tmp_path / "svg"
    diff_out = tmp_path / "diff"
    reports = tmp_path / "reports"
    for path in (folder, svg_out, diff_out, reports):
        path.mkdir()

    filename = "AC0800_S.jpg"
    (folder / filename).write_bytes(b"fake")
    (svg_out / "AC0800_S.svg").write_text("<svg/>", encoding="utf-8")

    batch_failures: list[dict[str, str]] = []
    row, failed = conversion_execution_helpers.convertOneImpl(
        filename=filename,
        folder_path=str(folder),
        csv_path="descriptions.csv",
        iteration_budget=3,
        badge_rounds=5,
        svg_out_dir=str(svg_out),
        diff_out_dir=str(diff_out),
        reports_out_dir=str(reports),
        debug_ac0811_dir=None,
        debug_element_diff_dir=None,
        run_iteration_pipeline_fn=lambda *_args, **_kwargs: ("AC0800_S", "desc", {"mode": "semantic_badge"}, 2, 12.0),
        read_validation_log_details_fn=lambda _path: {"convergence": "plateau"},
        render_svg_to_numpy_fn=lambda _svg, _w, _h: object(),
        calculate_delta2_stats_fn=lambda _img, _rendered: (1.25, 0.75),
        get_base_name_from_file_fn=lambda stem: stem.split("_")[0],
        cv2_module=_Cv2Stub(_ImageStub((4, 3, 3))),
        append_batch_failure_fn=batch_failures.append,
        print_fn=lambda _msg: None,
    )

    assert failed is False
    assert row is not None
    assert row["convergence"] == "plateau"
    assert row["mean_delta2"] == 1.25
    assert row["error_per_pixel"] == 1.0
    assert batch_failures == []


def test_convert_one_impl_semantic_mismatch_is_reported_as_failure(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    batch_failures: list[dict[str, str]] = []

    row, failed = conversion_execution_helpers.convertOneImpl(
        filename="AC0838_S.jpg",
        folder_path=str(tmp_path),
        csv_path="descriptions.csv",
        iteration_budget=3,
        badge_rounds=6,
        svg_out_dir=str(tmp_path),
        diff_out_dir=str(tmp_path),
        reports_out_dir=str(reports),
        debug_ac0811_dir=None,
        debug_element_diff_dir=None,
        run_iteration_pipeline_fn=lambda *_args, **_kwargs: None,
        read_validation_log_details_fn=lambda _path: {"status": "semantic_mismatch", "issue": "circle missing"},
        render_svg_to_numpy_fn=lambda _svg, _w, _h: None,
        calculate_delta2_stats_fn=lambda _img, _rendered: (0.0, 0.0),
        get_base_name_from_file_fn=lambda stem: stem,
        cv2_module=_Cv2Stub(None),
        append_batch_failure_fn=batch_failures.append,
        print_fn=lambda _msg: None,
    )

    assert row is None
    assert failed is True
    assert batch_failures and batch_failures[0]["status"] == "semantic_mismatch"
