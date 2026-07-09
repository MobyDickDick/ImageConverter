from __future__ import annotations

from src.iCCModules import imageCompositeConverterConversionFinalization as finalization_helpers


def test_run_conversion_finalization_executes_all_steps_and_returns_semantic_results(tmp_path):
    reports_out_dir = str(tmp_path / "reports")
    called: list[tuple[str, object]] = []
    expected_semantic_results = [{"variant": "AC0800_L"}]

    def _record(name: str):
        def _inner(*args, **kwargs):
            called.append((name, args or kwargs))
            if name == "write_iteration_log":
                return expected_semantic_results
            return None

        return _inner

    result = finalization_helpers.runConversionFinalizationImpl(
        reports_out_dir=reports_out_dir,
        quality_logs=[{"quality": 1}],
        conversion_bestlist_path=tmp_path / "bestlist.csv",
        conversion_bestlist_rows={"AC0800_L": {"error_per_pixel": 1.0}},
        batch_failures=[{"filename": "AC0800_L.jpg"}],
        strategy_logs=[{"variant": "AC0800_L"}],
        files=["AC0800_L.jpg"],
        result_map={"AC0800_L.jpg": {"params": {}}},
        folder_path="/tmp/in",
        csv_path="/tmp/in/mapping.csv",
        iterations=3,
        svg_out_dir="/tmp/svg",
        diff_out_dir="/tmp/diff",
        normalized_selected_variants={"AC0800_L"},
        write_quality_pass_report_fn=_record("quality_report"),
        write_conversion_bestlist_metrics_fn=_record("bestlist_metrics"),
        write_batch_failure_summary_fn=_record("batch_failure"),
        write_strategy_switch_template_transfers_report_fn=_record("strategy_switch"),
        write_iteration_log_and_collect_semantic_results_fn=_record("write_iteration_log"),
        harmonize_semantic_size_variants_fn=_record("harmonize"),
        run_post_conversion_reporting_fn=_record("post_reporting"),
    )

    assert result == expected_semantic_results
    step_names = [name for name, _ in called]
    assert step_names == [
        "quality_report",
        "bestlist_metrics",
        "batch_failure",
        "strategy_switch",
        "write_iteration_log",
        "harmonize",
        "post_reporting",
    ]


def test_run_conversion_finalization_skips_strategy_report_when_no_rows(tmp_path):
    called: list[str] = []

    def _marker(name: str):
        def _inner(*args, **kwargs):
            called.append(name)
            if name == "write_iteration_log":
                return []
            return None

        return _inner

    finalization_helpers.runConversionFinalizationImpl(
        reports_out_dir=str(tmp_path),
        quality_logs=[],
        conversion_bestlist_path=tmp_path / "bestlist.csv",
        conversion_bestlist_rows={},
        batch_failures=[],
        strategy_logs=[],
        files=[],
        result_map={},
        folder_path="in",
        csv_path="map.csv",
        iterations=1,
        svg_out_dir="svg",
        diff_out_dir="diff",
        normalized_selected_variants=set(),
        write_quality_pass_report_fn=_marker("quality_report"),
        write_conversion_bestlist_metrics_fn=_marker("bestlist_metrics"),
        write_batch_failure_summary_fn=_marker("batch_failure"),
        write_strategy_switch_template_transfers_report_fn=_marker("strategy_switch"),
        write_iteration_log_and_collect_semantic_results_fn=_marker("write_iteration_log"),
        harmonize_semantic_size_variants_fn=_marker("harmonize"),
        run_post_conversion_reporting_fn=_marker("post_reporting"),
    )

    assert "strategy_switch" not in called


def test_svg_embedded_raster_detection_supports_png_data_without_mime(tmp_path):
    svg_path = tmp_path / "AC0800_L.svg"
    svg_path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><image href="data:;base64,iVBORw0KGgoAAAANSUhEUgAA"/></svg>',
        encoding="utf-8",
    )

    assert finalization_helpers._svgContainsEmbeddedRaster(svg_path) is True


def test_mark_poor_conversions_renames_svg_when_embedded_png_detected(tmp_path):
    svg_dir = tmp_path / "svg"
    svg_dir.mkdir()
    (svg_dir / "AC0800_L.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><image xlink:href="data:;base64,iVBORw0KGgoAAAANSUhEUgAA"/></svg>',
        encoding="utf-8",
    )
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "successful_conversions.txt").write_text("", encoding="utf-8")

    finalization_helpers._markPoorConversionsWithFailedPrefix(
        svg_out_dir=str(svg_dir),
        result_map={"AC0800_L.jpg": {"variant": "AC0800_L", "mean_delta2": 0.0}},
        reports_out_dir=str(reports_dir),
    )

    assert (svg_dir / "Failed_AC0800_L.svg").exists()
    assert not (svg_dir / "AC0800_L.svg").exists()


def test_mark_poor_conversions_renames_svg_when_embedded_jpeg_detected(tmp_path):
    svg_dir = tmp_path / "svg"
    svg_dir.mkdir()
    (svg_dir / "AC0801_L.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><image href="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD"/></svg>',
        encoding="utf-8",
    )
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "successful_conversions.txt").write_text("", encoding="utf-8")

    finalization_helpers._markPoorConversionsWithFailedPrefix(
        svg_out_dir=str(svg_dir),
        result_map={"AC0801_L.jpg": {"variant": "AC0801_L", "mean_delta2": 0.0}},
        reports_out_dir=str(reports_dir),
    )

    assert (svg_dir / "Failed_AC0801_L.svg").exists()
    assert not (svg_dir / "AC0801_L.svg").exists()


def test_mark_poor_conversions_detects_embedded_raster_even_without_result_row(tmp_path):
    svg_dir = tmp_path / "svg"
    svg_dir.mkdir()
    (svg_dir / "GE9024_7S.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><image href="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD"/></svg>',
        encoding="utf-8",
    )
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "successful_conversions.txt").write_text("", encoding="utf-8")

    finalization_helpers._markPoorConversionsWithFailedPrefix(
        svg_out_dir=str(svg_dir),
        result_map={},
        reports_out_dir=str(reports_dir),
    )

    assert (svg_dir / "Failed_GE9024_7S.svg").exists()
    assert not (svg_dir / "GE9024_7S.svg").exists()


def test_mark_poor_conversions_detects_embedded_raster_for_lowercase_variant_names(tmp_path):
    svg_dir = tmp_path / "svg"
    svg_dir.mkdir()
    (svg_dir / "b_info.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><image href="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD"/></svg>',
        encoding="utf-8",
    )
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "successful_conversions.txt").write_text("", encoding="utf-8")

    finalization_helpers._markPoorConversionsWithFailedPrefix(
        svg_out_dir=str(svg_dir),
        result_map={},
        reports_out_dir=str(reports_dir),
    )

    assert (svg_dir / "Failed_B_INFO.svg").exists()
    assert not (svg_dir / "b_info.svg").exists()


def test_mark_poor_conversions_marks_skipped_manual_review_embedded_svg_as_failed(tmp_path):
    svg_dir = tmp_path / "svg"
    svg_dir.mkdir()
    (svg_dir / "AC0503_1M_sia.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><image href="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD"/></svg>',
        encoding="utf-8",
    )
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "successful_conversions.txt").write_text("", encoding="utf-8")
    (reports_dir / "AC0503_1M_sia_element_validation.log").write_text(
        "status=skipped_manual_review\n",
        encoding="utf-8",
    )

    finalization_helpers._markPoorConversionsWithFailedPrefix(
        svg_out_dir=str(svg_dir),
        result_map={},
        reports_out_dir=str(reports_dir),
    )

    assert not (svg_dir / "AC0503_1M_sia.svg").exists()
    assert (svg_dir / "Failed_AC0503_1M_SIA.svg").exists()


def test_mark_poor_conversions_removes_stale_failed_svg_after_successful_result(tmp_path):
    svg_dir = tmp_path / "svg"
    svg_dir.mkdir()
    (svg_dir / "AC0123.svg").write_text("<svg><rect width='10' height='10'/></svg>", encoding="utf-8")
    (svg_dir / "Failed_AC0123.svg").write_text("<svg><image href='data:image/png;base64,abc'/></svg>", encoding="utf-8")
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "successful_conversions.txt").write_text("", encoding="utf-8")

    finalization_helpers._markPoorConversionsWithFailedPrefix(
        svg_out_dir=str(svg_dir),
        result_map={"AC0123.jpg": {"variant": "AC0123", "mean_delta2": 0.0}},
        reports_out_dir=str(reports_dir),
    )

    assert (svg_dir / "AC0123.svg").exists()
    assert not (svg_dir / "Failed_AC0123.svg").exists()


def test_mark_poor_conversions_renames_trivial_white_fallback_svg(tmp_path):
    svg_dir = tmp_path / "svg"
    svg_dir.mkdir()
    (svg_dir / "GE0111_S.svg").write_text(
        "\"\n<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1\" height=\"1\" viewBox=\"0 0 1 1\">"
        "<rect width=\"100%\" height=\"100%\" fill=\"#ffffff\"/></svg>\n\"",
        encoding="utf-8",
    )
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "successful_conversions.txt").write_text("", encoding="utf-8")

    finalization_helpers._markPoorConversionsWithFailedPrefix(
        svg_out_dir=str(svg_dir),
        result_map={},
        reports_out_dir=str(reports_dir),
    )

    assert (svg_dir / "Failed_GE0111_S.svg").exists()
    assert not (svg_dir / "GE0111_S.svg").exists()


def test_mark_poor_conversions_renames_image_only_svg_without_detectable_raster_href(tmp_path):
    svg_dir = tmp_path / "svg"
    svg_dir.mkdir()
    (svg_dir / "AC0414_2_M.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><image href="cid:inline-asset"/></svg>',
        encoding="utf-8",
    )
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "successful_conversions.txt").write_text("", encoding="utf-8")

    finalization_helpers._markPoorConversionsWithFailedPrefix(
        svg_out_dir=str(svg_dir),
        result_map={},
        reports_out_dir=str(reports_dir),
    )

    assert (svg_dir / "Failed_AC0414_2_M.svg").exists()
    assert not (svg_dir / "AC0414_2_M.svg").exists()


def test_canonicalize_failed_attempt_svg_names_from_suffix_format(tmp_path):
    svg_dir = tmp_path / "svg"
    svg_dir.mkdir()
    (svg_dir / "AC0302_2_M_failed.svg").write_text("<svg/>", encoding="utf-8")

    finalization_helpers._canonicalizeFailedAttemptSvgNames(svg_out_dir=str(svg_dir))

    assert (svg_dir / "Failed_AC0302_2_M.svg").exists()
    assert not (svg_dir / "AC0302_2_M_failed.svg").exists()


def test_canonicalize_failed_attempt_svg_names_from_lowercase_prefix(tmp_path):
    svg_dir = tmp_path / "svg"
    svg_dir.mkdir()
    (svg_dir / "failed_AC0302_2_M.svg").write_text("<svg/>", encoding="utf-8")

    finalization_helpers._canonicalizeFailedAttemptSvgNames(svg_out_dir=str(svg_dir))

    assert (svg_dir / "Failed_AC0302_2_M.svg").exists()
    assert not (svg_dir / "failed_AC0302_2_M.svg").exists()

def test_archive_successful_conversion_artifacts_moves_image_and_copies_svg(tmp_path):
    reports_dir = tmp_path / "src" / "artifacts" / "converted_images" / "reports"
    reports_dir.mkdir(parents=True)
    source_dir = tmp_path / "input"
    source_dir.mkdir()
    svg_dir = tmp_path / "svg"
    svg_dir.mkdir()

    (source_dir / "AC0831_L.jpg").write_text("img", encoding="utf-8")
    (svg_dir / "AC0831_L.svg").write_text("<svg/>", encoding="utf-8")

    finalization_helpers._archiveSuccessfulConversionArtifacts(
        folder_path=str(source_dir),
        svg_out_dir=str(svg_dir),
        reports_out_dir=str(reports_dir),
        result_map={"AC0831_L.jpg": {"variant": "AC0831_L", "status": "semantic_ok"}},
    )

    assert (reports_dir / "successful_conversions_bestlist" / "AC0831_L.svg").exists()
    assert (reports_dir / "archived_source_images" / "AC0831_L.jpg").exists()
    assert not (source_dir / "AC0831_L.jpg").exists()


def test_remove_successful_variants_from_open_tasks_only_removes_open_checkboxes(tmp_path):
    reports_dir = tmp_path / "src" / "artifacts" / "converted_images" / "reports"
    reports_dir.mkdir(parents=True)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True)
    open_tasks = docs_dir / "open_tasks.md"
    open_tasks.write_text(
        "- [ ] todo AC0831_L\n- [x] done AC0831_L\n- [ ] todo AC0836_L\n",
        encoding="utf-8",
    )

    finalization_helpers._removeSuccessfulVariantsFromOpenTasks(
        reports_out_dir=str(reports_dir),
        result_map={"AC0831_L.jpg": {"variant": "AC0831_L", "status": "semantic_ok"}},
    )

    content = open_tasks.read_text(encoding="utf-8")
    assert "- [ ] todo AC0831_L" not in content
    assert "- [x] done AC0831_L" in content
    assert "- [ ] todo AC0836_L" in content


def test_remove_successful_variants_from_open_tasks_ignores_external_reports_dir(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    finalization_helpers._removeSuccessfulVariantsFromOpenTasks(
        reports_out_dir=str(reports_dir),
        result_map={"AC0831_L.jpg": {"variant": "AC0831_L", "status": "semantic_ok"}},
    )

    assert not (tmp_path / "docs" / "open_tasks.md").exists()


def test_append_failure_followup_tasks_adds_missing_failure_variants(tmp_path):
    reports_dir = tmp_path / "src" / "artifacts" / "converted_images" / "reports"
    reports_dir.mkdir(parents=True)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True)
    open_tasks = docs_dir / "open_tasks.md"
    open_tasks.write_text(
        "# Aufgaben\n\n## Session-Log\n- bisheriger Eintrag\n",
        encoding="utf-8",
    )

    finalization_helpers._appendFailureFollowUpTasks(
        reports_out_dir=str(reports_dir),
        batch_failures=[
            {"filename": "AC0840_L.jpg", "status": "conversion_failed", "reason": "no_result"},
            {"filename": "AC0841_M.jpg", "status": "semantic_mismatch", "reason": "semantic_mismatch"},
        ],
    )

    content = open_tasks.read_text(encoding="utf-8")
    assert "## Automatisch erzeugte Folgeaufgaben (Konvertierungsfehler)" in content
    assert "AUFGABE: Fehleranalyse `AC0840_L` (status=conversion_failed, reason=no_result)" in content
    assert "AUFGABE: Fehleranalyse `AC0841_M` (status=semantic_mismatch, reason=semantic_mismatch)" in content
    assert content.index("## Automatisch erzeugte Folgeaufgaben (Konvertierungsfehler)") < content.index("## Session-Log")


def test_append_failure_followup_tasks_skips_existing_variant_entries(tmp_path):
    reports_dir = tmp_path / "src" / "artifacts" / "converted_images" / "reports"
    reports_dir.mkdir(parents=True)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True)
    open_tasks = docs_dir / "open_tasks.md"
    open_tasks.write_text(
        "- [ ] Bereits offen: AC0840_L\n",
        encoding="utf-8",
    )

    finalization_helpers._appendFailureFollowUpTasks(
        reports_out_dir=str(reports_dir),
        batch_failures=[
            {"filename": "AC0840_L.jpg", "status": "conversion_failed", "reason": "no_result"},
        ],
    )

    content = open_tasks.read_text(encoding="utf-8")
    assert "Automatisch erzeugte Folgeaufgaben" not in content


def test_append_failure_followup_tasks_ignores_shallow_external_reports_dir(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    finalization_helpers._appendFailureFollowUpTasks(
        reports_out_dir=str(reports_dir),
        batch_failures=[
            {"filename": "AC0844_S.jpg", "status": "conversion_failed", "reason": "no_result"},
        ],
    )

    assert not (tmp_path / "docs" / "open_tasks.md").exists()


def test_move_failed_conversion_artifacts_to_failed_dirs_moves_svg_and_png(tmp_path):
    output_root = tmp_path / "converted_images"
    svg_dir = output_root / "converted_svgs"
    png_dir = output_root / "converted_images_png"
    svg_dir.mkdir(parents=True)
    png_dir.mkdir(parents=True)
    (svg_dir / "Failed_AC0800_L.svg").write_text("<svg/>", encoding="utf-8")
    (png_dir / "AC0800_L.png").write_text("png", encoding="utf-8")
    result_map = {"AC0800_L.jpg": {"variant": "AC0800_L", "status": "semantic_ok"}}

    failed_variants = finalization_helpers._moveFailedConversionArtifactsToFailedDirs(
        svg_out_dir=str(svg_dir),
        result_map=result_map,
    )

    assert failed_variants == {"AC0800_L"}
    assert (output_root / "converted_svg_failed" / "AC0800_L.svg").exists()
    assert (output_root / "converted_images_png_failed" / "AC0800_L.png").exists()
    assert not (svg_dir / "Failed_AC0800_L.svg").exists()
    assert not (png_dir / "AC0800_L.png").exists()
    assert result_map["AC0800_L.jpg"]["status"] == "quality_failed"
    assert result_map["AC0800_L.jpg"]["failure_reason"] == "unsatisfactory_result"


def test_run_conversion_finalization_quarantines_unsatisfactory_artifacts_before_archive(tmp_path):
    output_root = tmp_path / "converted_images"
    svg_dir = output_root / "converted_svgs"
    png_dir = output_root / "converted_images_png"
    reports_dir = output_root / "reports"
    source_dir = tmp_path / "input"
    svg_dir.mkdir(parents=True)
    png_dir.mkdir(parents=True)
    reports_dir.mkdir(parents=True)
    source_dir.mkdir()
    (reports_dir / "successful_conversions.txt").write_text("", encoding="utf-8")
    (source_dir / "AC0801_L.jpg").write_text("source", encoding="utf-8")
    (svg_dir / "AC0801_L.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><image href="data:image/png;base64,abc"/></svg>',
        encoding="utf-8",
    )
    (png_dir / "AC0801_L.png").write_text("png", encoding="utf-8")
    result_map = {"AC0801_L.jpg": {"variant": "AC0801_L", "status": "semantic_ok", "mean_delta2": 0.0}}

    finalization_helpers.runConversionFinalizationImpl(
        reports_out_dir=str(reports_dir),
        quality_logs=[],
        conversion_bestlist_path=tmp_path / "bestlist.csv",
        conversion_bestlist_rows={},
        batch_failures=[],
        strategy_logs=[],
        files=["AC0801_L.jpg"],
        result_map=result_map,
        folder_path=str(source_dir),
        csv_path="map.csv",
        iterations=1,
        svg_out_dir=str(svg_dir),
        diff_out_dir="diff",
        normalized_selected_variants=set(),
        write_quality_pass_report_fn=lambda *args, **kwargs: None,
        write_conversion_bestlist_metrics_fn=lambda *args, **kwargs: None,
        write_batch_failure_summary_fn=lambda *args, **kwargs: None,
        write_strategy_switch_template_transfers_report_fn=lambda *args, **kwargs: None,
        write_iteration_log_and_collect_semantic_results_fn=lambda *args, **kwargs: [],
        harmonize_semantic_size_variants_fn=lambda *args, **kwargs: None,
        run_post_conversion_reporting_fn=lambda *args, **kwargs: None,
    )

    assert (output_root / "converted_svg_failed" / "AC0801_L.svg").exists()
    assert (output_root / "converted_images_png_failed" / "AC0801_L.png").exists()
    assert not (svg_dir / "AC0801_L.svg").exists()
    assert not (reports_dir / "successful_conversions_bestlist" / "AC0801_L.svg").exists()
    assert (source_dir / "AC0801_L.jpg").exists()
    assert result_map["AC0801_L.jpg"]["status"] == "quality_failed"


def test_mark_poor_conversions_renames_svg_when_error_per_pixel_exceeds_fallback_gate(tmp_path):
    svg_dir = tmp_path / "svg"
    svg_dir.mkdir()
    (svg_dir / "AC0999_L.svg").write_text("<svg><rect width='10' height='10'/></svg>", encoding="utf-8")
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    # Fewer than three successful AC08 rows means no dynamic mean-delta threshold can be computed.
    (reports_dir / "successful_conversions.txt").write_text("", encoding="utf-8")

    finalization_helpers._markPoorConversionsWithFailedPrefix(
        svg_out_dir=str(svg_dir),
        result_map={
            "AC0999_L.jpg": {
                "variant": "AC0999_L",
                "mean_delta2": 0.0,
                "error_per_pixel": 18.5,
            }
        },
        reports_out_dir=str(reports_dir),
    )

    assert (svg_dir / "Failed_AC0999_L.svg").exists()
    assert not (svg_dir / "AC0999_L.svg").exists()
