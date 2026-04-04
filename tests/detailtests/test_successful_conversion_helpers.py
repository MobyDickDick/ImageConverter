from __future__ import annotations

from pathlib import Path

from src.iCCModules import imageCompositeConverterSuccessfulConversions as success_helpers


def test_parse_successful_conversion_manifest_line_parses_metrics() -> None:
    variant, metrics = success_helpers.parseSuccessfulConversionManifestLineImpl(
        "ac0800_s ; status=semantic_ok ; mean_delta2=1,25 ; pixel_count=42 # note"
    )

    assert variant == "AC0800_S"
    assert metrics["status"] == "semantic_ok"
    assert metrics["mean_delta2"] == 1.25
    assert metrics["pixel_count"] == 42


def test_is_candidate_better_prefers_semantic_ok() -> None:
    previous = {"status": "semantic_mismatch", "mean_delta2": 0.1}
    candidate = {"status": "semantic_ok", "mean_delta2": 5.0}

    better = success_helpers.isSuccessfulConversionCandidateBetterImpl(
        previous_metrics=previous,
        candidate_metrics=candidate,
        metrics_available_fn=lambda m: bool(m),
        evaluate_candidate_fn=lambda _p, _c: (False, "", 0.0, 0.0, 0.0, 0.0),
    )

    assert better is True


def test_format_manifest_line_keeps_comment_and_appends_metrics() -> None:
    line = "AC0800_S # baseline"
    metrics = {"variant": "AC0800_S", "status": "semantic_ok", "mean_delta2": 1.2, "pixel_count": 11}

    rendered = success_helpers.formatSuccessfulConversionManifestLineImpl(
        existing_line=line,
        metrics=metrics,
        metrics_available_fn=lambda m: bool(m),
    )

    assert "status=semantic_ok" in rendered
    assert "mean_delta2=1.200000" in rendered
    assert "pixel_count=11" in rendered
    assert rendered.endswith("# baseline")


def test_store_and_restore_successful_snapshot_roundtrip(tmp_path: Path) -> None:
    svg_out = tmp_path / "svg"
    reports = tmp_path / "reports"
    svg_out.mkdir()
    reports.mkdir()
    variant = "AC0800_S"

    (svg_out / f"{variant}.svg").write_text("<svg>new</svg>", encoding="utf-8")
    (reports / f"{variant}_element_validation.log").write_text("status=semantic_ok", encoding="utf-8")

    success_helpers.storeSuccessfulConversionSnapshotImpl(
        variant=variant,
        metrics={"variant": variant, "status": "semantic_ok"},
        svg_out_dir=str(svg_out),
        reports_out_dir=str(reports),
    )

    (svg_out / f"{variant}.svg").write_text("<svg>changed</svg>", encoding="utf-8")
    restored = success_helpers.restoreSuccessfulConversionSnapshotImpl(
        variant=variant,
        svg_out_dir=str(svg_out),
        reports_out_dir=str(reports),
    )

    assert restored is True
    assert (svg_out / f"{variant}.svg").read_text(encoding="utf-8") == "<svg>new</svg>"


def test_latest_failed_manifest_entry_prefers_last_relevant_row(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "batch_failure_summary.csv").write_text(
        "filename;status;reason\n"
        "AC0800_L.jpg;ok;\n"
        "AC0838_S.jpg;semantic_mismatch;missing circle\n"
        "AC0839_M.jpg;batch_error;renderer crash\n",
        encoding="utf-8",
    )

    entry = success_helpers.latestFailedConversionManifestEntryImpl(str(reports))

    assert entry == {
        "variant": "AC0839_M",
        "status": "failed",
        "failure_reason": "renderer crash",
    }


def test_write_successful_conversion_csv_table_sorts_and_formats(tmp_path: Path) -> None:
    csv_path = tmp_path / "reports" / "successful_conversions.csv"
    rows = [
        {
            "variant": "AC0831_S",
            "status": "semantic_ok",
            "image_found": True,
            "svg_found": True,
            "log_found": True,
            "best_iteration": "12",
            "diff_score": 1.0,
            "error_per_pixel": 0.125,
            "pixel_count": 10,
            "total_delta2": 2.0,
            "mean_delta2": 0.2,
            "std_delta2": 0.05,
        },
        {
            "variant": "AC0800_M",
            "status": "semantic_ok",
            "image_found": True,
            "svg_found": True,
            "log_found": True,
            "best_iteration": "5",
            "diff_score": 0.5,
            "error_per_pixel": 0.02,
            "pixel_count": 20,
            "total_delta2": 1.0,
            "mean_delta2": 0.05,
            "std_delta2": 0.01,
        },
    ]

    success_helpers.writeSuccessfulConversionCsvTableImpl(csv_path, rows)
    written = csv_path.read_text(encoding="utf-8").splitlines()

    assert written[0].startswith("variant;status;image_found")
    assert written[1].startswith("AC0800_M;semantic_ok;1;1;1;5;0.500000;0.02000000")
    assert written[2].startswith("AC0831_S;semantic_ok;1;1;1;12;1.000000;0.12500000")


def test_successful_conversion_metrics_available_detects_payload_fields() -> None:
    assert success_helpers.successfulConversionMetricsAvailableImpl({}) is False
    assert success_helpers.successfulConversionMetricsAvailableImpl({"status": "semantic_ok"}) is True
    assert success_helpers.successfulConversionMetricsAvailableImpl({"best_iteration": "7"}) is True
    assert success_helpers.successfulConversionMetricsAvailableImpl({"pixel_count": 1}) is True
    assert success_helpers.successfulConversionMetricsAvailableImpl({"mean_delta2": 0.125}) is True
