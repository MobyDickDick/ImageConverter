from pathlib import Path

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
from src.iCCModules.imageCompositeConverterNestedPanel import fit_nested_panel
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from tools.review_conversion_quality import normalized_mse


DESCRIPTION = 'Rechteckfläche mit heller rechteckiger Innenfläche.'
ROOT = Path(__file__).resolve().parents[1]


def render(svg, width, height):
    return render_svg_to_numpy_inprocess(svg, width, height, fitz_module=fitz, np_module=np, cv2_module=cv2)


def convert(image, name, monkeypatch):
    height, width = image.shape[:2]
    artifacts, logs = [], []

    def forbid_sample(**kwargs):
        pytest.fail('Algorithmic panel conversion must bypass sample lookup')

    monkeypatch.setattr(runtime, '_try_load_sample_svg', forbid_sample)
    result = runtime.runNonCompositeIterationImpl(
        mode='non_composite', params={'mode': 'non_composite'}, stripe_strategy=None,
        semantic_mode_visual_override=False, width=width, height=height,
        base_name=name, description=DESCRIPTION, perc_img=image, img_path=f'{name}.jpg',
        print_fn=lambda *args: None, render_embedded_raster_svg_fn=lambda path: None,
        build_gradient_stripe_svg_fn=lambda *args, **kwargs: None,
        build_gradient_stripe_validation_log_lines_fn=lambda **kwargs: [],
        write_validation_log_fn=logs.append, render_svg_to_numpy_fn=render,
        record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, raster: artifacts.append((svg, raster)),
        calculate_error_fn=lambda target, raster: normalized_mse(target, raster)[0],
    )
    assert result is not None
    assert 'status=non_composite_raster_nested_rectangles' in logs[-1]
    return artifacts[-1]


@pytest.mark.parametrize('name', ['DLG0010', 'DLG0010_1'])
def test_panel_runtime_preserves_both_regions_without_samples(name, monkeypatch):
    image = cv2.imread(str(ROOT / f'artifacts/images_to_convert/{name}.JPG'))
    svg, raster = convert(image, name, monkeypatch)
    assert svg.count('<rect ') == 2
    assert '<image' not in svg
    assert normalized_mse(image, raster)[1] < .003
    renamed_svg, renamed_raster = convert(image, 'unrelated_rectangle', monkeypatch)
    assert renamed_svg == svg
    np.testing.assert_array_equal(raster, renamed_raster)


@pytest.mark.parametrize('scale', [1, 2])
def test_panel_registration_generalizes_color_position_and_size(scale, monkeypatch):
    width, height = 80*scale, 40*scale
    source = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
              f'<rect width="{width}" height="{height}" fill="#345599"/>'
              f'<rect x="{25*scale}" y="{4*scale}" width="{50*scale}" height="{32*scale}" fill="#f5eeda"/></svg>')
    image = render(source, width, height)
    svg, raster = convert(image, 'anonymous_panel', monkeypatch)
    assert normalized_mse(image, raster)[1] < .001
    assert '#345599' in svg and '#f5eeda' in svg


@pytest.mark.parametrize('description', [DESCRIPTION, 'Rechteck mit Text im Inneren'])
def test_panel_does_not_erase_holes_or_explicit_text(description):
    image = np.full((40, 80, 3), (40, 40, 220), dtype=np.uint8)
    image[3:37, 3:60] = 255
    image[15:25, 20:35] = 0
    assert fit_nested_panel(80, 40, description=description, image=image,
                            render_fn=render, error_fn=lambda a, b: normalized_mse(a, b)[0]) is None
