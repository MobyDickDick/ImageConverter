from __future__ import annotations

from pathlib import Path

from src.iCCModules.imageCompositeConverterFallback import runEmbeddedRasterFallbackImpl


def test_run_embedded_raster_fallback_writes_failed_prefixed_svg(tmp_path: Path) -> None:
    images_dir = tmp_path / "images"
    svg_dir = tmp_path / "svg"
    diff_dir = tmp_path / "diff"
    reports_dir = tmp_path / "reports"
    images_dir.mkdir()
    svg_dir.mkdir()
    diff_dir.mkdir()
    reports_dir.mkdir()

    image_name = "AC0812_L.jpg"
    (images_dir / image_name).write_bytes(b"dummy")

    calls: dict[str, str] = {}

    def fake_overviews(diff: str, svg: str, reports: str):
        calls["diff"] = diff
        calls["svg"] = svg
        calls["reports"] = reports

    runEmbeddedRasterFallbackImpl(
        files=[image_name],
        folder_path=str(images_dir),
        svg_out_dir=str(svg_dir),
        diff_out_dir=str(diff_dir),
        reports_out_dir=str(reports_dir),
        render_embedded_raster_svg_fn=lambda _path: "<svg/>",
        create_diff_image_without_cv2_fn=lambda *_args, **_kwargs: None,
        generate_conversion_overviews_fn=fake_overviews,
        fitz_module=None,
    )

    assert (svg_dir / "Failed_AC0812_L.svg").read_text(encoding="utf-8") == "<svg/>"
    assert not (svg_dir / "AC0812_L.svg").exists()
    assert calls["reports"] == str(reports_dir)
