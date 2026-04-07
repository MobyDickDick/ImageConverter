from __future__ import annotations

from pathlib import Path

from src.iCCModules import imageCompositeConverterConversionReporting as helpers


def test_run_post_conversion_reporting_writes_reports_and_manifest(tmp_path: Path):
    calls: list[tuple[str, object]] = []

    manifest_path = tmp_path / "successful_conversions.txt"
    manifest_path.write_text("AC0800_S\n", encoding="utf-8")

    def _record(name: str):
        def _fn(*args, **kwargs):
            calls.append((name, {"args": args, "kwargs": kwargs}))
            if name == "write_ac08_success":
                return {"gate": "ok"}
            if name == "generate_overviews":
                return {"overview": str(tmp_path / "overview.png")}
            return None

        return _fn

    printed: list[str] = []
    result = helpers.runPostConversionReportingImpl(
        folder_path="images",
        csv_path="descriptions.csv",
        iterations=3,
        svg_out_dir="out/svg",
        diff_out_dir="out/diff",
        reports_out_dir="out/reports",
        normalized_selected_variants={"AC0800_S"},
        result_map={"AC0800_S.jpg": {"params": {"semantic_audit": {"variant": "AC0800_S"}}}},
        write_semantic_audit_report_fn=_record("write_semantic_audit"),
        write_pixel_delta2_ranking_fn=_record("write_ranking"),
        write_ac08_weak_family_status_report_fn=_record("write_weak_status"),
        write_ac08_regression_manifest_fn=_record("write_manifest"),
        write_ac08_success_criteria_report_fn=_record("write_ac08_success"),
        emit_ac08_success_gate_status_fn=_record("emit_gate"),
        successful_conversions_manifest=manifest_path,
        update_successful_conversions_manifest_fn=_record("update_success_manifest"),
        generate_conversion_overviews_fn=_record("generate_overviews"),
        print_fn=printed.append,
    )

    call_names = [name for name, _payload in calls]
    assert "update_success_manifest" in call_names
    assert result == {"overview": str(tmp_path / "overview.png")}
    assert any("Übersichts-Kacheln erzeugt" in line for line in printed)


def test_run_post_conversion_reporting_skips_manifest_refresh_when_missing(tmp_path: Path):
    called_update = False

    def _update_manifest(*_args, **_kwargs):
        nonlocal called_update
        called_update = True

    helpers.runPostConversionReportingImpl(
        folder_path="images",
        csv_path="descriptions.csv",
        iterations=1,
        svg_out_dir="out/svg",
        diff_out_dir="out/diff",
        reports_out_dir="out/reports",
        normalized_selected_variants=set(),
        result_map={},
        write_semantic_audit_report_fn=lambda *_args, **_kwargs: None,
        write_pixel_delta2_ranking_fn=lambda *_args, **_kwargs: None,
        write_ac08_weak_family_status_report_fn=lambda *_args, **_kwargs: None,
        write_ac08_regression_manifest_fn=lambda *_args, **_kwargs: None,
        write_ac08_success_criteria_report_fn=lambda *_args, **_kwargs: None,
        emit_ac08_success_gate_status_fn=lambda *_args, **_kwargs: None,
        successful_conversions_manifest=tmp_path / "missing_manifest.txt",
        update_successful_conversions_manifest_fn=_update_manifest,
        generate_conversion_overviews_fn=lambda *_args, **_kwargs: {},
    )

    assert called_update is False
