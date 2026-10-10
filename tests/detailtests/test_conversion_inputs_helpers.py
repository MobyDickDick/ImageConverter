from __future__ import annotations

from src.iCCModules import imageCompositeConverterConversionInputs as conversion_input_helpers


def test_list_requested_image_files_filters_extension_range_and_variants(monkeypatch) -> None:
    monkeypatch.setattr(
        conversion_input_helpers.os,
        "listdir",
        lambda _folder: [
            "AC0800_L.jpg",
            "AC0800_S.jpg",
            "AC0801_M.jpeg",
            "AC0811_M.png",
            "AC0812_M.gif",
            "AR0101.jpg",
            "readme.txt",
        ],
    )

    normalized_variants, files = conversion_input_helpers.listRequestedImageFilesImpl(
        folder_path="input",
        start_ref="AC0800",
        end_ref="AC0811",
        selected_variants={"ac0800_l", "AC0811_M", "   "},
        in_requested_range_fn=lambda filename, start, end: start <= filename[:6] <= end,
    )

    assert normalized_variants == {"AC0800_L", "AC0811_M"}
    assert files == ["AC0800_L.jpg", "AC0811_M.png"]


def test_list_requested_image_files_returns_all_in_range_when_no_selection(monkeypatch) -> None:
    monkeypatch.setattr(
        conversion_input_helpers.os,
        "listdir",
        lambda _folder: ["AC0800_L.jpg", "AC0800_M.jpeg", "AC0900_M.jpg", "ignored.bmp.tmp"],
    )

    normalized_variants, files = conversion_input_helpers.listRequestedImageFilesImpl(
        folder_path="ignored",
        start_ref="AC0800",
        end_ref="AC0899",
        selected_variants=None,
        in_requested_range_fn=lambda filename, start, end: start <= filename[:6] <= end,
    )

    assert normalized_variants == set()
    assert files == ["AC0800_L.jpg", "AC0800_M.jpeg"]


def test_input_selection_summary_contains_hints() -> None:
    summary = conversion_input_helpers.inputSelectionSummaryImpl(
        folder_path="input",
        start_ref="AC0800",
        end_ref="AC0899",
        selected_variants={"ac0801_l"},
        matched_files=[],
    )

    assert "Keine Eingabedateien für die Konvertierung gefunden." in summary
    assert "Range: AC0800..AC0899" in summary
    assert "Ausgewählte Varianten: AC0801_L" in summary
    assert ".jpeg" in summary


def test_regression_selection_includes_archived_sources_without_duplicates(tmp_path):
    archive=tmp_path/'succesessfulConvertedImages'
    archive.mkdir()
    for path in (tmp_path/'one.jpg',archive/'one.jpg',archive/'two.jpg'):
        path.write_bytes(b'image')
    _,ordinary=conversion_input_helpers.listRequestedImageFilesImpl(str(tmp_path),'A','Z',
        selected_variants=None,in_requested_range_fn=lambda *args:True)
    _,regression=conversion_input_helpers.listRequestedImageFilesImpl(str(tmp_path),'A','Z',
        selected_variants={'ONE','TWO'},in_requested_range_fn=lambda *args:True)
    assert ordinary==['one.jpg']
    assert regression==['one.jpg',str(__import__('pathlib').Path('succesessfulConvertedImages')/'two.jpg')]
