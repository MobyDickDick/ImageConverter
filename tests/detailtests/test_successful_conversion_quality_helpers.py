from __future__ import annotations

from pathlib import Path

import pytest

from src.iCCModules import imageCompositeConverterSuccessfulConversionQuality as quality_helpers


def test_load_iteration_log_rows_keys_by_variant(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "Iteration_Log.csv").write_text(
        "Dateiname;Best Iter;Status\n"
        "ac0800_l.jpg;3;semantic_ok\n"
        ";1;ignored\n",
        encoding="utf-8-sig",
    )

    rows = quality_helpers.loadIterationLogRowsImpl(str(reports))

    assert set(rows) == {"AC0800_L"}
    assert rows["AC0800_L"]["Best Iter"] == "3"


def test_find_image_path_by_variant_picks_existing_extension(tmp_path: Path) -> None:
    images = tmp_path / "images"
    images.mkdir()
    expected = images / "AC0831_M.png"
    expected.write_text("dummy", encoding="utf-8")

    found = quality_helpers.findImagePathByVariantImpl(str(images), "AC0831_M")

    assert found == str(expected)


def test_collect_metrics_requires_image_dependencies(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="cv2, numpy"):
        quality_helpers.collectSuccessfulConversionQualityMetricsImpl(
            folder_path=str(tmp_path),
            svg_out_dir=str(tmp_path),
            reports_out_dir=str(tmp_path),
            successful_variants=["AC0800_L"],
            successful_conversions=[],
            load_iteration_log_rows_fn=lambda _: {},
            find_image_path_by_variant_fn=lambda *_: None,
            read_validation_log_details_fn=lambda *_: {},
            render_svg_to_numpy_fn=lambda *_: None,
            cv2_module=None,
            np_module=None,
        )


def test_collect_metrics_reads_status_and_iteration_without_render(tmp_path: Path) -> None:
    images = tmp_path / "images"
    svg_out = tmp_path / "svg"
    reports = tmp_path / "reports"
    images.mkdir()
    svg_out.mkdir()
    reports.mkdir()
    (images / "AC0800_L.jpg").write_text("img", encoding="utf-8")
    (svg_out / "AC0800_L.svg").write_text("<svg />", encoding="utf-8")
    (reports / "AC0800_L_element_validation.log").write_text("log", encoding="utf-8")

    class _Cv2:
        @staticmethod
        def imread(_path: str) -> None:
            return None

    rows = quality_helpers.collectSuccessfulConversionQualityMetricsImpl(
        folder_path=str(images),
        svg_out_dir=str(svg_out),
        reports_out_dir=str(reports),
        successful_variants=["AC0800_L"],
        successful_conversions=[],
        load_iteration_log_rows_fn=lambda *_: {
            "AC0800_L": {"Beste Iteration": "4", "Diff-Score": "2,5", "FehlerProPixel": "1,25"}
        },
        find_image_path_by_variant_fn=lambda *_: str(images / "AC0800_L.jpg"),
        read_validation_log_details_fn=lambda *_: {"status": "semantic_ok"},
        render_svg_to_numpy_fn=lambda *_: None,
        cv2_module=_Cv2(),
        np_module=object(),
    )

    assert len(rows) == 1
    assert rows[0]["status"] == "semantic_ok"
    assert rows[0]["best_iteration"] == "4"
    assert rows[0]["pixel_count"] == 0
