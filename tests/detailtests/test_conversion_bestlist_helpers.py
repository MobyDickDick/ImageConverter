from __future__ import annotations

from pathlib import Path

from src.iCCModules import imageCompositeConverterBestlist as bestlist_helpers


def test_candidate_better_when_no_previous() -> None:
    assert bestlist_helpers.isConversionBestlistCandidateBetterImpl(
        previous_row=None,
        candidate_row={"status": "composite_ok", "error_per_pixel": 0.2, "mean_delta2": 1.0},
        evaluate_candidate_fn=lambda _a, _b: (False, "", 0.0, 0.0, 0.0, 0.0),
    )


def test_candidate_prefers_semantic_ok() -> None:
    better = bestlist_helpers.isConversionBestlistCandidateBetterImpl(
        previous_row={"status": "semantic_mismatch", "error_per_pixel": 0.1, "mean_delta2": 1.0},
        candidate_row={"status": "semantic_ok", "error_per_pixel": 0.3, "mean_delta2": 4.0},
        evaluate_candidate_fn=lambda _a, _b: (False, "", 0.0, 0.0, 0.0, 0.0),
    )
    assert better is True


def test_bestlist_manifest_read_write_roundtrip(tmp_path: Path) -> None:
    manifest = tmp_path / "conversion_bestlist.csv"
    rows = {
        "AC0800_S": {
            "variant": "AC0800_S",
            "filename": "AC0800_S.jpg",
            "status": "semantic_ok",
            "best_iter": 4,
            "best_error": 123.5,
            "error_per_pixel": 0.11111111,
            "mean_delta2": 1.5,
            "std_delta2": 0.2,
        }
    }

    bestlist_helpers.writeConversionBestlistMetricsImpl(manifest, rows)
    loaded = bestlist_helpers.readConversionBestlistMetricsImpl(manifest)

    assert loaded["AC0800_S"]["status"] == "semantic_ok"
    assert float(loaded["AC0800_S"]["mean_delta2"]) == 1.5


def test_store_and_restore_bestlist_snapshot_roundtrip(tmp_path: Path) -> None:
    svg_out = tmp_path / "svg"
    reports = tmp_path / "reports"
    svg_out.mkdir()
    reports.mkdir()
    variant = "AC0800_S"

    (svg_out / f"{variant}.svg").write_text("<svg>best</svg>", encoding="utf-8")
    (reports / f"{variant}_element_validation.log").write_text("status=semantic_ok", encoding="utf-8")

    bestlist_helpers.storeConversionBestlistSnapshotImpl(
        variant=variant,
        row={"variant": variant, "status": "semantic_ok", "best_error": 1.23},
        svg_out_dir=str(svg_out),
        reports_out_dir=str(reports),
    )

    (svg_out / f"{variant}.svg").write_text("<svg>worse</svg>", encoding="utf-8")
    restored = bestlist_helpers.restoreConversionBestlistSnapshotImpl(
        variant=variant,
        svg_out_dir=str(svg_out),
        reports_out_dir=str(reports),
    )

    assert (svg_out / f"{variant}.svg").read_text(encoding="utf-8") == "<svg>best</svg>"
    assert isinstance(restored, dict)
    assert restored.get("status") == "semantic_ok"


def test_prune_bestlist_rows_without_existing_svg(tmp_path: Path) -> None:
    svg_out = tmp_path / "svg"
    svg_out.mkdir()
    (svg_out / "AC0800_S.svg").write_text("<svg/>", encoding="utf-8")

    rows = {
        "AC0800_S": {"variant": "AC0800_S", "filename": "AC0800_S.jpg"},
        "AC0834_S": {"variant": "AC0834_S", "filename": "AC0834_S.jpg"},
    }

    pruned = bestlist_helpers.pruneConversionBestlistRowsWithoutSvgImpl(rows, str(svg_out))

    assert list(pruned) == ["AC0800_S"]


def test_choose_conversion_bestlist_row_prefers_previous_and_restored_values() -> None:
    selected = bestlist_helpers.chooseConversionBestlistRowImpl(
        candidate_row={
            "variant": "AC0800_S",
            "best_iter": 7,
            "best_error": 10.0,
            "error_per_pixel": 0.1,
            "mean_delta2": 2.0,
            "std_delta2": 0.5,
            "status": "semantic_mismatch",
        },
        previous_row={
            "best_iter": 3,
            "best_error": 5.0,
            "error_per_pixel": 0.05,
            "status": "semantic_ok",
        },
        restored_row={
            "best_error": 4.0,
            "mean_delta2": 1.1,
        },
    )

    assert selected["best_iter"] == 3
    assert selected["best_error"] == 4.0
    assert selected["error_per_pixel"] == 0.05
    assert selected["mean_delta2"] == 1.1
    assert selected["status"] == "semantic_ok"
