from __future__ import annotations

from pathlib import Path

from src.iCCModules import imageCompositeConverterQualityConfig as quality_config_helpers


def test_svg_href_mime_type_defaults_to_octet_stream() -> None:
    assert quality_config_helpers.svgHrefMimeTypeImpl("foo.unknown") == "application/octet-stream"
    assert quality_config_helpers.svgHrefMimeTypeImpl("foo.PNG") == "image/png"


def test_render_embedded_raster_svg_uses_sniffed_size(tmp_path: Path) -> None:
    raster = tmp_path / "sample.gif"
    raster.write_bytes(b"GIF89a")

    svg = quality_config_helpers.renderEmbeddedRasterSvgImpl(
        raster,
        sniff_raster_size_fn=lambda _path: (7, 9),
    )

    assert 'width="7"' in svg
    assert 'height="9"' in svg
    assert "<image" in svg
    assert "data:image/gif;base64," in svg
    assert "Fallback (no embedded raster): sample.gif" not in svg


def test_load_and_write_quality_config_roundtrip(tmp_path: Path) -> None:
    reports_out_dir = str(tmp_path)

    quality_config_helpers.writeQualityConfigImpl(
        reports_out_dir,
        allowed_error_per_pixel=0.123,
        skipped_variants=["AC0800_S", "AC0800_S", "AC0811_L"],
        source="unit-test",
        quality_config_path_fn=quality_config_helpers.qualityConfigPathImpl,
    )

    loaded = quality_config_helpers.loadQualityConfigImpl(
        reports_out_dir,
        quality_config_path_fn=quality_config_helpers.qualityConfigPathImpl,
    )

    assert loaded["allowed_error_per_pixel"] == 0.123
    assert loaded["skip_variants"] == ["AC0800_S", "AC0811_L"]
    assert loaded["source"] == "unit-test"
    assert loaded["pixel_error_acceptance"] == {
        "max_mean_delta2": 300.0,
        "max_std_delta2": 3000.0,
        "basis": "strict-rgb-rmse-10",
    }


def test_load_quality_config_handles_invalid_payload(tmp_path: Path) -> None:
    path = tmp_path / "quality_tercile_config.json"
    path.write_text("[]", encoding="utf-8")

    loaded = quality_config_helpers.loadQualityConfigImpl(
        str(tmp_path),
        quality_config_path_fn=quality_config_helpers.qualityConfigPathImpl,
    )
    assert loaded == {}

    path.write_text("{invalid", encoding="utf-8")
    loaded_invalid = quality_config_helpers.loadQualityConfigImpl(
        str(tmp_path),
        quality_config_path_fn=quality_config_helpers.qualityConfigPathImpl,
    )
    assert loaded_invalid == {}


def test_write_quality_config_preserves_early_abort_tuning(tmp_path: Path) -> None:
    path = tmp_path / "quality_tercile_config.json"
    path.write_text(
        '{"early_abort":{"enabled":false,"probe_iterations":5,"threshold_multiplier":12.0}}',
        encoding="utf-8",
    )

    quality_config_helpers.writeQualityConfigImpl(
        str(tmp_path),
        allowed_error_per_pixel=0.5,
        skipped_variants=[],
        source="test",
        quality_config_path_fn=lambda _reports: str(path),
    )

    loaded = quality_config_helpers.loadQualityConfigImpl(
        str(tmp_path), quality_config_path_fn=lambda _reports: str(path)
    )
    assert loaded["early_abort"] == {
        "enabled": False,
        "probe_iterations": 5,
        "threshold_multiplier": 12.0,
    }


def test_write_quality_config_preserves_pixel_error_acceptance(tmp_path: Path) -> None:
    path = tmp_path / "quality_tercile_config.json"
    path.write_text(
        '{"pixel_error_acceptance":{"max_mean_delta2":125.0,"max_std_delta2":40.0}}',
        encoding="utf-8",
    )

    quality_config_helpers.writeQualityConfigImpl(
        str(tmp_path),
        allowed_error_per_pixel=0.5,
        skipped_variants=[],
        source="test",
        quality_config_path_fn=lambda _reports: str(path),
    )

    loaded = quality_config_helpers.loadQualityConfigImpl(
        str(tmp_path), quality_config_path_fn=lambda _reports: str(path)
    )
    assert loaded["pixel_error_acceptance"] == {
        "max_mean_delta2": 125.0,
        "max_std_delta2": 40.0,
        "basis": "user-configured",
    }


def test_global_converter_config_defaults_are_schema_valid() -> None:
    payload = quality_config_helpers.defaultGlobalConverterConfigV1Impl()

    validated = quality_config_helpers.validateGlobalConverterConfigV1Impl(payload)

    assert validated["valid"] is True
    assert payload["schema_version"] == "image_converter_global_config_v1"
    assert payload["primitive_thresholds"]["min_circle_confidence"] == 0.55
    assert payload["budgets"]["validation_time_budget_sec"] == 90.0


def test_global_converter_config_rejects_unknown_and_image_scoped_keys() -> None:
    valid = quality_config_helpers.defaultGlobalConverterConfigV1Impl()
    with_unknown = {**valid, "unexpected": True}
    with_image_scope = {**valid, "image_overrides": {"AC0001": {}}}

    assert quality_config_helpers.validateGlobalConverterConfigV1Impl(with_unknown)["valid"] is False
    rejected = quality_config_helpers.validateGlobalConverterConfigV1Impl(with_image_scope)

    assert rejected["valid"] is False
    assert any("image_overrides" in error for error in rejected["errors"])


def test_load_global_converter_config_falls_back_to_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "global_converter_config_v1.json"
    loaded_missing = quality_config_helpers.loadGlobalConverterConfigV1Impl(
        str(tmp_path), global_config_path_fn=lambda _root: str(config_path)
    )
    assert loaded_missing["source"] == "defaults"

    config_path.write_text('{"schema_version":"image_converter_global_config_v1","unknown":1}', encoding="utf-8")
    loaded_invalid = quality_config_helpers.loadGlobalConverterConfigV1Impl(
        str(tmp_path), global_config_path_fn=lambda _root: str(config_path)
    )
    assert loaded_invalid["source"] == "defaults"
    assert loaded_invalid["validation"]["valid"] is False
