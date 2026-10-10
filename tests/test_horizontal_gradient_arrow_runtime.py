from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
from tests.test_gradient_arrow_runtime import render
from src.iCCModules.imageCompositeConverterGradientArrow import fit_gradient_arrow
from tools.evaluate_horizontal_gradient_arrow_recheck import horizontal_arrow_semantics, measure
from tools.review_conversion_quality import normalized_mse


ROOT = Path(__file__).resolve().parents[1]
DESCRIPTION = ('Nach links gerichteter Pfeil: gefüllte dreieckige Spitze links von einem schmaleren '
               'rechteckigen horizontalen Schaft. Zwischen Spitze und Schaft liegt ein weißer Abstand. '
               'Schaft mit vertikalem Farbverlauf, in der Mitte hell und zu beiden Seiten dunkler. Weißer Hintergrund.')


def source_svg(scale=1, color='#345577', direction='left', shift=.3):
    """Independent horizontal geometry; unequal shaft sides expose axis reversal."""
    tip, base, sx = (4+shift, 30+shift, 35+shift) if direction == 'left' else (87-shift, 61-shift, 9-shift)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{92*scale}" height="{48*scale}">'
            '<defs><linearGradient id="shade" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{color}"/><stop offset="0.48" stop-color="#eeeeee"/>'
            '<stop offset="1" stop-color="#553344"/></linearGradient></defs>'
            f'<rect width="{92*scale}" height="{48*scale}" fill="#ffffff"/>'
            f'<polygon points="{tip*scale},{23.7*scale} {base*scale},{4.2*scale} {base*scale},{43.2*scale}" fill="{color}"/>'
            f'<rect x="{sx*scale}" y="{14.2*scale}" width="{48*scale}" height="{19*scale}" fill="url(#shade)"/></svg>')


def fit(image, description=DESCRIPTION, error_fn=None, render_fn=render):
    h, w = image.shape[:2]
    return fit_gradient_arrow(w, h, description=description, image=image, render_fn=render_fn,
                              error_fn=error_fn or (lambda a, b: normalized_mse(a, b)[0]))


@pytest.mark.parametrize('variant', [f'GE9014_{i}{size}' for i in range(1, 8) for size in ('M', 'S')])
def test_all_catalog_colors_and_sizes(variant):
    image = cv2.imread(str(ROOT/f'artifacts/images_to_convert/{variant}.jpg'))
    snapshot = image.copy()
    result = fit(image)
    assert result is not None
    assert result['direction'] == 'left'
    assert result['error'] < result['initial_error']
    assert result['evaluations'] <= 121
    assert normalized_mse(image, result['rendered'])[1] < .005
    assert horizontal_arrow_semantics(result['svg']) == 1
    np.testing.assert_array_equal(image, snapshot)
    np.testing.assert_array_equal(result['rendered'], render(result['svg'], image.shape[1], image.shape[0]))


@pytest.mark.parametrize('direction', ['left', 'right'])
@pytest.mark.parametrize('scale', [1, 2])
@pytest.mark.parametrize('color', ['#345577', '#775533'])
@pytest.mark.parametrize('shift', [.3, 1.15])
def test_independent_geometry_colors_resolution_and_pixel_phase(direction, scale, color, shift):
    image = render(source_svg(scale, color, direction, shift), 92*scale, 48*scale)
    result = fit(image, DESCRIPTION.replace('links', 'rechts') if direction == 'right' else DESCRIPTION)
    assert result is not None
    assert horizontal_arrow_semantics(result['svg'], direction) == 1
    assert normalized_mse(image, result['rendered'])[1] < .003
    np.testing.assert_array_equal(result['rendered'], render(result['svg'], 92*scale, 48*scale))


@pytest.mark.parametrize('description', ['Hellgraues Quadrat.', DESCRIPTION+' Zusätzlich ein Kreis.',
    DESCRIPTION.replace('links', 'rechts'), DESCRIPTION+' mit Text', DESCRIPTION+' nach oben',
    DESCRIPTION+' rechts gerichtet', DESCRIPTION.replace('vertikalem Farbverlauf', 'horizontalem Farbverlauf'),
    DESCRIPTION+' Die Darstellung enthält zusätzlich einen Kreis.'])
def test_incompatible_descriptions(description):
    assert fit(render(source_svg(), 92, 48), description) is None


@pytest.mark.parametrize('mutation', ['head', 'shaft', 'hole', 'flat', 'extra'])
def test_missing_or_contradictory_raster_evidence(mutation):
    image = render(source_svg(), 92, 48)
    if mutation == 'head':
        image[:, :32] = 255
    elif mutation == 'shaft':
        image[:, 33:] = 255
    elif mutation == 'hole':
        image[18:30, 45:60] = 0
    elif mutation == 'flat':
        image[14:34, 35:84] = 80
    else:
        image[1:7, 55:65] = 0
    assert fit(image) is None


@pytest.mark.parametrize('value', [42., float('nan'), float('inf')])
def test_non_improving_or_nonfinite_error(value):
    assert fit(render(source_svg(), 92, 48), error_fn=lambda a, b: value) is None


def test_missing_render_and_invalid_image():
    image = render(source_svg(), 92, 48)
    assert fit(image, render_fn=lambda *a: None) is None
    assert fit(image[:, :, 0]) is None


def test_runtime_filename_invariance_and_no_reference_access(monkeypatch):
    image = render(source_svg(), 92, 48)
    def forbidden(*a, **kw):
        pytest.fail('Horizontal arrow must use only input pixels and description')
    monkeypatch.setattr(runtime, '_try_load_sample_svg', forbidden)
    outputs = []
    for name in ('independent_shape', 'renamed_shape'):
        result = runtime.runNonCompositeIterationImpl(
            mode='non_composite', params={}, stripe_strategy=None, semantic_mode_visual_override=False,
            width=92, height=48, base_name=name, description=DESCRIPTION, perc_img=image, img_path=name+'.png',
            print_fn=lambda *a: None, render_embedded_raster_svg_fn=forbidden,
            build_gradient_stripe_svg_fn=forbidden, build_gradient_stripe_validation_log_lines_fn=forbidden,
            write_validation_log_fn=lambda lines: None, render_svg_to_numpy_fn=render,
            record_render_failure_fn=forbidden, write_attempt_artifacts_fn=lambda svg, raster: outputs.append(svg),
            calculate_error_fn=lambda a, b: normalized_mse(a, b)[0])
        assert result is not None
    assert outputs[0] == outputs[1]
    assert '<image' not in outputs[0]
    assert not any(e.get('transform') for e in ET.fromstring(outputs[0]).iter())


def test_perfect_saved_pair_calibrates_metrics(tmp_path):
    image, vector = tmp_path/'input.png', tmp_path/'output.svg'
    svg = source_svg()
    cv2.imwrite(str(image), render(svg, 92, 48))
    vector.write_text(svg, encoding='utf-8')
    assert measure(image, vector)['metrics'] == {
        'error_per_pixel': 0., 'edge_alignment': 1., 'object_mask_iou': 1.,
        'semantic_score': 1., 'dimension_match': 1.}


@pytest.mark.parametrize('wrong', [
    lambda s: s.replace('x="35.3"', 'x="25.3"'),
    lambda s: s.replace('x2="0" y2="1"', 'x2="1" y2="0"'),
    lambda s: s.replace('#eeeeee', '#345577'),
    lambda s: s.replace('4.3,23.7', '90,23.7'),
    lambda s: s.replace('</svg>', '<image href="data:image/png;base64,AA=="/></svg>'),
    lambda s: s.replace('<polygon ', '<polygon transform="translate(1 0)" '),
])
def test_independent_semantics_rejects_wrong_outputs(wrong):
    assert horizontal_arrow_semantics(wrong(source_svg())) == 0.


@pytest.mark.parametrize('index', [0, 4, 10, 14])
def test_shift_wording_and_observed_contours_from_plan_b_regressions(index):
    from tools.run_plan_b_variations import make_variations, measure_quality
    from src.iCCModules.imageCompositeConverterDiffing import calculateErrorImpl
    case = make_variations(source_svg(), DESCRIPTION, 20261010)[index]
    image = render(case['svg'], case['width'], case['height'])
    result = fit(image, case['description'], error_fn=lambda a, b:
                 calculateErrorImpl(a, b, cv2_module=cv2, np_module=np))
    assert result is not None
    assert measure_quality(image, result['svg'])['satisfactory']


def test_recheck_refuses_nonfresh_output_and_source_drift(tmp_path, monkeypatch):
    import json
    from tools.run_horizontal_gradient_arrow_recheck import main
    package = ROOT/'artifacts/evaluation/horizontal_gradient_arrow_recheck_v1'
    monkeypatch.setattr('sys.argv', ['runner', str(package/'manifest.json'), '--output-dir', str(tmp_path)])
    with pytest.raises(ValueError, match='fresh output'):
        main()
    manifest = json.loads((package/'manifest.json').read_text())
    manifest['cases'][0]['image'] = str((package/manifest['cases'][0]['image']).resolve())
    manifest['cases'][0]['source_sha256'] = 'wrong'
    path = tmp_path/'manifest.json'
    path.write_text(json.dumps(manifest))
    monkeypatch.setattr('sys.argv', ['runner', str(path), '--output-dir', str(tmp_path/'fresh')])
    with pytest.raises(ValueError, match='Source hash mismatch'):
        main()
