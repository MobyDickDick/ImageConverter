from __future__ import annotations

import base64
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
    encoded = base64.b64encode(b"GIF89a").decode("ascii")
    assert f"data:image/gif;base64,{encoded}" in svg


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
