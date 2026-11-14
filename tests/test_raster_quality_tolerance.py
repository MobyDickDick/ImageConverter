"""Accept threshold/JPEG noise, while retaining evidence for structural errors."""
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterAdaptiveSearch import pixel_quality
from src.iCCModules.imageCompositeConverterPrimitiveScene import _local_quality
from tools.run_plan_b_variations import measure_quality, render

FIXTURES = Path(__file__).parent/'fixtures/raster_quality'


@pytest.fixture(params=['mupdf', 'librsvg'])
def renderer(request):
    if request.param == 'mupdf':
        return render
    from tools.evaluate_svg_text_baseline import find_librsvg, render_librsvg
    try:
        executable = find_librsvg()
    except FileNotFoundError as error:
        pytest.skip(str(error))
    return lambda svg, w, h: render_librsvg(svg, w, h, executable=executable)


def check(reference, svg, renderer):
    independent = measure_quality(reference, svg, render_fn=renderer)
    raster = renderer(svg, reference.shape[1], reference.shape[0])
    search = pixel_quality(reference, raster)
    assert search['passed'] == independent['satisfactory']
    assert {k: v for k, v in search.items() if k != 'passed'} == independent['metrics']
    return independent


def test_clean_vector_of_jpeg_threshold_fill_passes_both_renderers(renderer):
    reference = cv2.imread(str(FIXTURES/'threshold_fill.png'))
    svg = (FIXTURES/'threshold_fill.svg').read_text()
    result = check(reference, svg, renderer)
    assert result['metrics']['foreground_iou_binary'] < .85
    assert result['metrics']['foreground_iou'] > .95
    assert result['satisfactory'], result
    local = _local_quality(reference, renderer(svg, 40, 40))
    assert local['passed']


@pytest.mark.parametrize('fault', [
    'missing_triangle', 'missing_rim', 'wrong_shape', 'wrong_direction',
    'shifted_symbol', 'shifted_triangle', 'wrong_color', 'blank',
])
def test_threshold_tolerance_does_not_accept_faulty_vectors(renderer, fault):
    reference = cv2.imread(str(FIXTURES/'threshold_fill.png'))
    root = ET.fromstring((FIXTURES/'threshold_fill.svg').read_text())
    group = next(iter(root))
    circle, triangle = list(group)
    if fault == 'missing_triangle':
        group.remove(triangle)
    elif fault == 'missing_rim':
        circle.set('stroke-width', '0')
    elif fault == 'wrong_shape':
        group.remove(triangle)
        ET.SubElement(group, 'rect', x='10', y='10', width='20', height='20', fill='#808080')
    elif fault == 'wrong_direction':
        triangle.set('points', '5.25,9 20.25,38.75 34.75,9')
    elif fault == 'shifted_symbol':
        group.set('transform', 'translate(3 0)')
    elif fault == 'shifted_triangle':
        triangle.set('transform', 'translate(1 0)')
    elif fault == 'wrong_color':
        circle.set('fill', '#b0b0b0')
    elif fault == 'blank':
        root.remove(group)
        ET.SubElement(root, 'rect', width='40', height='40', fill='white')
    result = check(reference, ET.tostring(root, encoding='unicode'), renderer)
    assert not result['satisfactory'], (fault, result)
    # The new overlap can only improve with very close pixel AND edge evidence.
    assert result['metrics']['foreground_iou'] == result['metrics']['foreground_iou_binary']


@pytest.mark.parametrize('background,fill', [(255, 230), (220, 194), (50, 76)])
def test_small_intensity_noise_near_cutoff_has_no_binary_cliff(background, fill):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48">'
           f'<rect width="48" height="48" fill="rgb({background},{background},{background})"/>'
           f'<rect x="8" y="8" width="32" height="32" fill="rgb({fill},{fill},{fill})"/></svg>')
    reference = render(svg, 48, 48)
    # Isolate fill-threshold noise from edge movement: the stricter rescue rule
    # deliberately requires the existing edge comparison to agree closely.
    noise = np.random.default_rng(7).integers(-2, 3, (28, 28, 1))
    reference[10:38, 10:38] = np.clip(reference[10:38, 10:38].astype(int)+noise, 0, 255)
    result = check(reference, svg, render)
    assert result['metrics']['foreground_iou_binary'] < .85
    assert result['satisfactory'], result


def test_missing_separate_low_contrast_object_still_fails_on_nonwhite_background():
    header = '<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50">'
    base = '<rect width="50" height="50" fill="#dcdcdc"/><rect x="5" y="5" width="14" height="12" fill="#b4b4b4"/>'
    reference = render(header+base+'<rect x="35" y="35" width="8" height="8" fill="#b4b4b4"/></svg>', 50, 50)
    result = check(reference, header+base+'</svg>', render)
    assert not result['satisfactory'], result


def test_empty_images_have_perfect_overlap_without_nan():
    svg = '<svg width="16" height="16"><rect width="16" height="16" fill="white"/></svg>'
    result = check(render(svg, 16, 16), svg, render)
    assert result['metrics']['foreground_iou'] == 1.
    assert result['metrics']['foreground_iou_binary'] == 1.
