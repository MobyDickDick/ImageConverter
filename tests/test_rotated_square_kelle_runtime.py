from pathlib import Path

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from tools.review_conversion_quality import normalized_mse


DESCRIPTION = (
    "Kelle mit Quadrat anstelle von Kreis oben. "
    "Geometrische Variante: 180° gedreht."
)
ROOT = Path(__file__).resolve().parents[1]


def _convert(image, name, monkeypatch):
    height, width = image.shape[:2]
    artifacts = []
    logs = []

    def forbid_sample(**_kwargs):
        pytest.fail("Description-driven square geometry must bypass sample lookup")

    monkeypatch.setattr(runtime, "_try_load_sample_svg", forbid_sample)
    monkeypatch.setattr(runtime, "_output_variation_rng", lambda: None)
    result = runtime.runNonCompositeIterationImpl(
        mode="non_composite",
        params={"mode": "non_composite"},
        stripe_strategy=None,
        semantic_mode_visual_override=False,
        width=width,
        height=height,
        base_name=name,
        description=DESCRIPTION,
        perc_img=image,
        img_path=f"{name}.jpg",
        print_fn=lambda *_args: None,
        render_embedded_raster_svg_fn=lambda _path: None,
        build_gradient_stripe_svg_fn=lambda *_args, **_kwargs: None,
        build_gradient_stripe_validation_log_lines_fn=lambda **_kwargs: [],
        write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=lambda svg, w, h: render_svg_to_numpy_inprocess(
            svg, w, h, fitz_module=fitz, np_module=np, cv2_module=cv2
        ),
        record_render_failure_fn=lambda *_args, **_kwargs: None,
        write_attempt_artifacts_fn=lambda svg, raster: artifacts.append((svg, raster)),
        calculate_error_fn=lambda target, raster: normalized_mse(target, raster)[0],
    )
    assert result is not None
    return artifacts[-1], logs[-1]


@pytest.mark.parametrize("size", ["S", "M", "L"])
def test_rotated_square_runtime_registers_semantic_geometry_at_multiple_sizes(size, monkeypatch):
    image = cv2.imread(str(ROOT / f"artifacts/images_to_convert/AC0713_1_{size}.jpg"))
    assert image is not None
    (svg, rendered), logs = _convert(image, "anonymous_square", monkeypatch)
    assert "status=non_composite_description_geometry_ir" in logs
    assert "geometry_ir_raster_registration=1" in logs
    assert "non_composite_selection=semantic_description_geometry" in logs
    assert 'id="rotated_180_square_kelle_body"' in svg
    assert 'id="rotated_180_square_kelle_connector"' in svg
    assert "<circle" not in svg and "<text" not in svg and "<image" not in svg
    assert normalized_mse(image, rendered)[1] < 0.015


def test_rotated_square_runtime_is_invariant_to_filename(monkeypatch):
    image = cv2.imread(str(ROOT / "artifacts/images_to_convert/AC0713_1_S.jpg"))
    (original_svg, original_raster), _ = _convert(image, "AC0713_1_S", monkeypatch)
    (renamed_svg, renamed_raster), _ = _convert(image, "unrelated_holdout", monkeypatch)
    assert renamed_svg == original_svg
    np.testing.assert_array_equal(renamed_raster, original_raster)
