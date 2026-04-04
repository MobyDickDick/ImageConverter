from __future__ import annotations

from pathlib import Path

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
