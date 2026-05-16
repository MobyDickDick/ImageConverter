from __future__ import annotations

from pathlib import Path

from src.iCCModules import imageCompositeConverterLegacyApi as legacy


def test_convert_image_svg_falls_back_to_failed_prefix(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("IMAGE_CONVERTER_VECTORIZE_BACKEND", raising=False)
    out = legacy.convertImageImpl(
        input_path="sample.jpg",
        output_path=str(tmp_path / "out.svg"),
        render_embedded_raster_svg_fn=lambda _: "<svg/>",
        detect_relevant_regions_fn=lambda _: {},
        annotate_image_regions_fn=lambda img, regions: img,
        cv2_module=None,
        np_module=None,
    )
    assert out.name == "Failed_out.svg"
    assert out.read_text(encoding="utf-8") == "<svg/>"


def test_try_vectorize_with_vtracer_opt_in(tmp_path: Path, monkeypatch):
    class _FakeVtracer:
        @staticmethod
        def convert_image_to_svg_py(src: str, dst: str, **kwargs):
            Path(dst).write_text("<svg id='vtracer'/>", encoding="utf-8")
            assert kwargs["mode"] == "spline"

    monkeypatch.setenv("IMAGE_CONVERTER_VECTORIZE_BACKEND", "vtracer")
    monkeypatch.setattr(legacy, "import_module", lambda name: _FakeVtracer())

    out = legacy.convertImageImpl(
        input_path="sample.jpg",
        output_path=str(tmp_path / "vector.svg"),
        render_embedded_raster_svg_fn=lambda _: "<svg id='fallback'/>",
        detect_relevant_regions_fn=lambda _: {},
        annotate_image_regions_fn=lambda img, regions: img,
        cv2_module=None,
        np_module=None,
    )
    assert out.name == "vector.svg"
    assert out.read_text(encoding="utf-8") == "<svg id='vtracer'/>"
