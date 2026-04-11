from __future__ import annotations

import binascii
import struct
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


def test_placeholder_diff_png_has_valid_chunk_crc() -> None:
    payload = conversion_execution_helpers._ONE_BY_ONE_TRANSPARENT_PNG
    assert payload.startswith(b"\x89PNG\r\n\x1a\n")

    cursor = 8
    while cursor < len(payload):
        chunk_len = struct.unpack(">I", payload[cursor : cursor + 4])[0]
        chunk_type = payload[cursor + 4 : cursor + 8]
        chunk_data = payload[cursor + 8 : cursor + 8 + chunk_len]
        expected_crc = struct.unpack(">I", payload[cursor + 8 + chunk_len : cursor + 12 + chunk_len])[0]
        actual_crc = binascii.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
        assert actual_crc == expected_crc
        cursor += 12 + chunk_len
        if chunk_type == b"IEND":
            break

    assert cursor == len(payload)


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
        render_embedded_raster_svg_fn=lambda _path: "<svg/>",
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
        render_embedded_raster_svg_fn=lambda _path: "<svg/>",
        append_batch_failure_fn=batch_failures.append,
        print_fn=lambda _msg: None,
    )

    assert row is None
    assert failed is True
    assert batch_failures and batch_failures[0]["status"] == "semantic_mismatch"
    assert (tmp_path / "Failed_AC0838_S.svg").read_text(encoding="utf-8") == "<svg/>"


def test_convert_one_impl_unknown_status_is_recorded_as_failure(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    batch_failures: list[dict[str, str]] = []

    row, failed = conversion_execution_helpers.convertOneImpl(
        filename="AC0840_M.jpg",
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
        read_validation_log_details_fn=lambda _path: {"status": "non_composite_embedded_svg"},
        render_svg_to_numpy_fn=lambda _svg, _w, _h: None,
        calculate_delta2_stats_fn=lambda _img, _rendered: (0.0, 0.0),
        get_base_name_from_file_fn=lambda stem: stem,
        cv2_module=_Cv2Stub(None),
        render_embedded_raster_svg_fn=lambda _path: "<svg/>",
        append_batch_failure_fn=batch_failures.append,
        print_fn=lambda _msg: None,
    )

    assert row is None
    assert failed is True
    assert batch_failures and batch_failures[0]["status"] == "non_composite_embedded_svg"
    assert (tmp_path / "Failed_AC0840_M.svg").read_text(encoding="utf-8") == "<svg/>"


def test_convert_one_impl_skipped_status_stays_non_failure(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    batch_failures: list[dict[str, str]] = []

    row, failed = conversion_execution_helpers.convertOneImpl(
        filename="AC0999_X.jpg",
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
        read_validation_log_details_fn=lambda _path: {"status": "skipped_manual_review"},
        render_svg_to_numpy_fn=lambda _svg, _w, _h: None,
        calculate_delta2_stats_fn=lambda _img, _rendered: (0.0, 0.0),
        get_base_name_from_file_fn=lambda stem: stem,
        cv2_module=_Cv2Stub(None),
        render_embedded_raster_svg_fn=lambda _path: "<svg/>",
        append_batch_failure_fn=batch_failures.append,
        print_fn=lambda _msg: None,
    )

    assert row is None
    assert failed is False
    assert batch_failures == []
    assert (tmp_path / "AC0999_X.svg").read_text(encoding="utf-8") == "<svg/>"


def test_convert_one_impl_non_composite_success_renames_svg_to_failed_prefix(tmp_path: Path) -> None:
    folder = tmp_path / "images"
    svg_out = tmp_path / "svg"
    diff_out = tmp_path / "diff"
    reports = tmp_path / "reports"
    for path in (folder, svg_out, diff_out, reports):
        path.mkdir()

    filename = "AC0704_S.jpg"
    (folder / filename).write_bytes(b"fake")
    (svg_out / "AC0704_S.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><image href="data:image/jpeg;base64,/9j/4AAQ"/></svg>',
        encoding="utf-8",
    )

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
        run_iteration_pipeline_fn=lambda *_args, **_kwargs: ("AC0704_S", "desc", {"mode": "non_composite"}, 1, 1.0),
        read_validation_log_details_fn=lambda _path: {"status": "non_composite_embedded_svg", "convergence": "n/a"},
        render_svg_to_numpy_fn=lambda _svg, _w, _h: object(),
        calculate_delta2_stats_fn=lambda _img, _rendered: (0.1, 0.0),
        get_base_name_from_file_fn=lambda stem: stem.split("_")[0],
        cv2_module=_Cv2Stub(_ImageStub((5, 7, 3))),
        render_embedded_raster_svg_fn=lambda _path: "<svg/>",
        append_batch_failure_fn=lambda _row: None,
        print_fn=lambda _msg: None,
    )

    assert failed is False
    assert row is not None
    assert (svg_out / "Failed_AC0704_S.svg").exists()
    assert not (svg_out / "AC0704_S.svg").exists()


def test_convert_one_impl_embedded_svg_uses_failed_prefix_independent_of_status(tmp_path: Path) -> None:
    folder = tmp_path / "images"
    svg_out = tmp_path / "svg"
    diff_out = tmp_path / "diff"
    reports = tmp_path / "reports"
    for path in (folder, svg_out, diff_out, reports):
        path.mkdir()

    filename = "AC0805_M.jpg"
    (folder / filename).write_bytes(b"fake")
    (svg_out / "AC0805_M.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><image href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA"/></svg>',
        encoding="utf-8",
    )

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
        run_iteration_pipeline_fn=lambda *_args, **_kwargs: ("AC0805_M", "desc", {"mode": "semantic_badge"}, 1, 1.0),
        read_validation_log_details_fn=lambda _path: {"status": "semantic_ok", "convergence": "stable"},
        render_svg_to_numpy_fn=lambda _svg, _w, _h: object(),
        calculate_delta2_stats_fn=lambda _img, _rendered: (0.1, 0.0),
        get_base_name_from_file_fn=lambda stem: stem.split("_")[0],
        cv2_module=_Cv2Stub(_ImageStub((8, 6, 3))),
        render_embedded_raster_svg_fn=lambda _path: "<svg/>",
        append_batch_failure_fn=lambda _row: None,
        print_fn=lambda _msg: None,
    )

    assert failed is False
    assert row is not None
    assert (svg_out / "Failed_AC0805_M.svg").exists()
    assert not (svg_out / "AC0805_M.svg").exists()


def test_convert_one_impl_skipped_status_with_result_keeps_normal_svg_name(tmp_path: Path) -> None:
    folder = tmp_path / "images"
    svg_out = tmp_path / "svg"
    diff_out = tmp_path / "diff"
    reports = tmp_path / "reports"
    for path in (folder, svg_out, diff_out, reports):
        path.mkdir()

    filename = "AC0503_1M_sia.jpeg"
    (folder / filename).write_bytes(b"fake")
    (svg_out / "AC0503_1M_sia.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><image href="data:image/jpeg;base64,/9j/4AAQ"/></svg>',
        encoding="utf-8",
    )

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
        run_iteration_pipeline_fn=lambda *_args, **_kwargs: ("AC0503_1M_sia", "desc", {"mode": "semantic_badge"}, 1, 1.0),
        read_validation_log_details_fn=lambda _path: {"status": "skipped_manual_review", "convergence": "n/a"},
        render_svg_to_numpy_fn=lambda _svg, _w, _h: object(),
        calculate_delta2_stats_fn=lambda _img, _rendered: (0.1, 0.0),
        get_base_name_from_file_fn=lambda stem: stem.split("_")[0],
        cv2_module=_Cv2Stub(_ImageStub((8, 6, 3))),
        render_embedded_raster_svg_fn=lambda _path: "<svg/>",
        append_batch_failure_fn=lambda _row: None,
        print_fn=lambda _msg: None,
    )

    assert row is None
    assert failed is False
    assert (svg_out / "AC0503_1M_sia.svg").exists()
    assert not (svg_out / "Failed_AC0503_1M_sia.svg").exists()


def test_convert_one_impl_trivial_placeholder_svg_is_marked_failed(tmp_path: Path) -> None:
    folder = tmp_path / "images"
    svg_out = tmp_path / "svg"
    diff_out = tmp_path / "diff"
    reports = tmp_path / "reports"
    for path in (folder, svg_out, diff_out, reports):
        path.mkdir()

    filename = "AC0535_1S_sia.jpeg"
    (folder / filename).write_bytes(b"fake")
    (svg_out / "AC0535_1S_sia.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1" viewBox="0 0 1 1"><rect width=\'100%\' height=\'100%\' fill=\'#ffffff\'/></svg>',
        encoding="utf-8",
    )
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
        run_iteration_pipeline_fn=lambda *_args, **_kwargs: ("AC0535_1S_sia", "desc", {"mode": "semantic_badge"}, 1, 999.0),
        read_validation_log_details_fn=lambda _path: {"status": "semantic_ok", "convergence": "stable"},
        render_svg_to_numpy_fn=lambda _svg, _w, _h: object(),
        calculate_delta2_stats_fn=lambda _img, _rendered: (99.0, 0.0),
        get_base_name_from_file_fn=lambda stem: stem.split("_")[0],
        cv2_module=_Cv2Stub(_ImageStub((8, 6, 3))),
        render_embedded_raster_svg_fn=lambda _path: "<svg/>",
        append_batch_failure_fn=batch_failures.append,
        print_fn=lambda _msg: None,
    )

    assert row is None
    assert failed is True
    assert (svg_out / "Failed_AC0535_1S_sia.svg").exists()


def test_convert_one_impl_marks_image_only_svg_without_raster_extension_as_failed(tmp_path: Path) -> None:
    folder = tmp_path / "images"
    svg_out = tmp_path / "svg"
    diff_out = tmp_path / "diff"
    reports = tmp_path / "reports"
    for path in (folder, svg_out, diff_out, reports):
        path.mkdir()

    filename = "AC0414_2_M.jpeg"
    (folder / filename).write_bytes(b"fake")
    (svg_out / "AC0414_2_M.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><image href="cid:inline-asset"/></svg>',
        encoding="utf-8",
    )

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
        run_iteration_pipeline_fn=lambda *_args, **_kwargs: ("AC0414_2_M", "desc", {"mode": "semantic_badge"}, 1, 1.0),
        read_validation_log_details_fn=lambda _path: {"status": "semantic_ok", "convergence": "stable"},
        render_svg_to_numpy_fn=lambda _svg, _w, _h: object(),
        calculate_delta2_stats_fn=lambda _img, _rendered: (0.1, 0.0),
        get_base_name_from_file_fn=lambda stem: stem.split("_")[0],
        cv2_module=_Cv2Stub(_ImageStub((8, 6, 3))),
        render_embedded_raster_svg_fn=lambda _path: "<svg/>",
        append_batch_failure_fn=lambda _row: None,
        print_fn=lambda _msg: None,
    )

    assert failed is False
    assert row is not None
    assert (svg_out / "Failed_AC0414_2_M.svg").exists()
    assert not (svg_out / "AC0414_2_M.svg").exists()
