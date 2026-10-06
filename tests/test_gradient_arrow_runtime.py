from pathlib import Path

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
from src.iCCModules.imageCompositeConverterGradientArrow import fit_gradient_arrow
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from tools.evaluate_gradient_arrow_recheck import gradient_arrow_semantics, measure
from tools.review_conversion_quality import normalized_mse


DESCRIPTION = ('Nach oben gerichteter Pfeil: gefüllte dreieckige Spitze über einem schmaleren '
               'rechteckigen vertikalen Schaft. Zwischen Spitze und Schaft liegt ein weißer Abstand. '
               'Schaft mit horizontalem Farbverlauf, in der Mitte hell und zu beiden Seiten dunkler. Weißer Hintergrund.')
ROOT = Path(__file__).resolve().parents[1]


def render(svg, width, height):
    return render_svg_to_numpy_inprocess(svg, width, height, fitz_module=fitz, np_module=np, cv2_module=cv2)


def fit(image, description=DESCRIPTION, error_fn=None):
    h, w = image.shape[:2]
    return fit_gradient_arrow(w, h, description=description, image=image, render_fn=render,
                              error_fn=error_fn or (lambda a, b: normalized_mse(a, b)[0]))


def source_svg(scale=1, color='#345577'):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{50*scale}" height="{80*scale}">'
            '<defs><linearGradient id="shade" x1="0" y1="0" x2="1" y2="0">'
            f'<stop offset="0" stop-color="{color}"/><stop offset="0.5" stop-color="#eeeeee"/>'
            f'<stop offset="1" stop-color="{color}"/></linearGradient></defs>'
            f'<rect width="{50*scale}" height="{80*scale}" fill="#ffffff"/>'
            f'<polygon points="{24*scale},{2*scale} {45*scale},{29*scale} {3*scale},{29*scale}" fill="{color}"/>'
            f'<rect x="{14*scale}" y="{33*scale}" width="{20*scale}" height="{42*scale}" fill="url(#shade)"/></svg>')


@pytest.mark.parametrize('variant', [f'GE9011_{i}{size}' for i in range(1, 8) for size in ('M', 'S')])
def test_arrow_fits_all_colors_and_sizes_from_pixels(variant):
    image = cv2.imread(str(ROOT/f'artifacts/images_to_convert/{variant}.jpg'))
    snapshot = image.copy()
    result = fit(image)
    assert result is not None
    assert result['error'] < result['initial_error']
    assert normalized_mse(image, result['rendered'])[1] < .005
    assert gradient_arrow_semantics(result['svg']) == 1
    assert result['evaluations'] <= 73
    np.testing.assert_array_equal(image, snapshot)


@pytest.mark.parametrize('scale', [1, 2])
@pytest.mark.parametrize('color', ['#345577', '#775533'])
def test_arrow_generalizes_position_size_and_color(scale, color):
    image = render(source_svg(scale, color), 50*scale, 80*scale)
    result = fit(image)
    assert result is not None
    assert normalized_mse(image, result['rendered'])[1] < .003
    assert gradient_arrow_semantics(result['svg']) == 1


def test_runtime_rename_invariance_and_forbidden_samples(monkeypatch):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/GE9011_6M.jpg'))
    h, w = image.shape[:2]

    def forbidden(*args, **kwargs):
        pytest.fail('Arrow registration must bypass sample SVGs and raster embedding')

    monkeypatch.setattr(runtime, '_try_load_sample_svg', forbidden)
    outputs = []
    for name in ('unrelated_arrow', 'another_filename'):
        logs = []
        result = runtime.runNonCompositeIterationImpl(
            mode='non_composite', params={}, stripe_strategy=None, semantic_mode_visual_override=False,
            width=w, height=h, base_name=name, description=DESCRIPTION, perc_img=image, img_path=name+'.jpg',
            print_fn=lambda *args: None, render_embedded_raster_svg_fn=forbidden,
            build_gradient_stripe_svg_fn=forbidden, build_gradient_stripe_validation_log_lines_fn=forbidden,
            write_validation_log_fn=logs.append, render_svg_to_numpy_fn=render,
            record_render_failure_fn=forbidden, write_attempt_artifacts_fn=lambda svg, raster: outputs.append(svg),
            calculate_error_fn=lambda a, b: normalized_mse(a, b)[0])
        assert result is not None
        assert logs == [['status=non_composite_raster_gradient_arrow']]
    assert outputs[0] == outputs[1]
    assert '<image' not in outputs[0]


@pytest.mark.parametrize('description', ['Hellgraues Quadrat.', DESCRIPTION+' Zusätzlich ein Kreis.',
                                         DESCRIPTION.replace('oben', 'unten'), DESCRIPTION+' mit Text'])
def test_incompatible_descriptions_do_not_select_arrow(description):
    assert fit(render(source_svg(), 50, 80), description) is None


@pytest.mark.parametrize('mutation', ['head', 'shaft', 'hole', 'flat'])
def test_missing_or_incompatible_raster_evidence_is_rejected(mutation):
    image = render(source_svg(), 50, 80)
    if mutation == 'head':
        image[:30] = 255
    elif mutation == 'shaft':
        image[30:] = 255
    elif mutation == 'hole':
        image[45:60, 18:30] = 0
    else:
        image[33:75, 14:34] = (80, 80, 80)
    assert fit(image) is None


@pytest.mark.parametrize('value', [42., float('nan'), float('inf')])
def test_non_improving_or_nonfinite_search_is_rejected(value):
    assert fit(render(source_svg(), 50, 80), error_fn=lambda a, b: value) is None


def test_gate_metrics_calibrate_perfect_saved_svg(tmp_path):
    svg = source_svg()
    image, vector = tmp_path/'input.png', tmp_path/'output.svg'
    assert cv2.imwrite(str(image), render(svg, 50, 80))
    vector.write_text(svg, encoding='utf-8')
    assert measure(image, vector)['metrics'] == {
        'error_per_pixel': 0., 'edge_alignment': 1., 'object_mask_iou': 1.,
        'semantic_score': 1., 'dimension_match': 1.}


@pytest.mark.parametrize('wrong', [
    lambda s: s.replace('y="33"', 'y="20"'),
    lambda s: s.replace('x2="1" y2="0"', 'x2="0" y2="1"'),
    lambda s: s.replace('stop-color="#eeeeee"', 'stop-color="#345577"'),
    lambda s: s.replace('24,2 45,29 3,29', '24,29 45,2 3,2'),
    lambda s: s.replace('</svg>', '<image href="data:image/png;base64,AA=="/></svg>'),
    lambda s: s.replace('<polygon ', '<polygon transform="translate(1 0)" '),
])
def test_semantics_rejects_wrong_topology_gradient_and_embedding(wrong):
    assert gradient_arrow_semantics(wrong(source_svg())) == 0.
