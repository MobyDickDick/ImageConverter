from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search
from src.iCCModules.imageCompositeConverterDescriptionLanguage import normalize_description
from src.iCCModules.imageCompositeConverterGradientTube import fit_gradient_tube, tube_contract, validate_tube_refinement
from tools.run_plan_b_variations import render, measure_quality


DESCRIPTION = ('Röhre oben und unten grau; vertikaler Verlauf von gelbgrün nach dunkelgrün. '
               'Gesamter Farbverlauf: links dunkel, Mitte hell, rechts dunkel (Röhreneffekt)')
ROOT = Path(__file__).resolve().parents[1]


def independent_raster(width=50, height=230, margin=0, fractional=False):
    """Analytic source pixels, independent of SVG generation and render adapters."""
    w, h = width-2*margin, height-2*margin
    top, bottom = margin+max(4, int(h*.05)), height-margin-max(4, int(h*.05))
    if fractional:
        top, bottom = top+.25, bottom-.25
    x = (np.arange(w)+.5)/w
    shading = np.interp(x, [0, .13, .63, 1], [.62, .64, 1, .76])
    t = np.clip((np.arange(margin, height-margin)+.5-top)/(bottom-top), 0, 1)
    body = ((1-t[:, None])*[40, 220, 230]+t[:, None]*[110, 165, 65])[:, None]*shading[None, :, None]
    cap = np.interp(x, [0, .13, .63, 1], [150, 160, 235, 180])[None, :, None]
    cap_alpha = np.clip(top-np.arange(margin, height-margin), 0, 1)
    cap_alpha += np.clip(np.arange(margin, height-margin)+1-bottom, 0, 1)
    body = body*(1-cap_alpha[:, None, None])+cap*cap_alpha[:, None, None]
    image = np.full((height, width, 3), 255, dtype=np.uint8)
    image[margin:height-margin, margin:width-margin] = np.round(body).astype(np.uint8)
    return image


def fit(image, description=DESCRIPTION, render_fn=render):
    h, w = image.shape[:2]
    return fit_gradient_tube(w, h, description=description, image=image, render_fn=render_fn,
        error_fn=lambda a, b: float(np.mean((a.astype(float)-b)**2)))


@pytest.mark.parametrize('size', [(30, 110), (50, 230), (72, 360)])
@pytest.mark.parametrize('margin,fractional', [(0, False), (3, True)])
def test_independent_pixels_keep_two_paint_axes_and_both_caps(size, margin, fractional):
    image = independent_raster(*size, margin=margin, fractional=fractional)
    result = fit(image)
    assert result is not None
    assert result['quality']['passed'] and result['details']['passed']
    assert measure_quality(image, result['svg'])['satisfactory']
    root = ET.fromstring(result['svg'])
    assert len(root.findall('{*}rect')) == 4
    assert len(root.findall('.//{*}stop')) == 14
    assert not root.findall('.//{*}path') and not root.findall('.//{*}image')


@pytest.mark.parametrize('suffix', [' Mit Text.', ' Mit einem Kreis rechts.', ' Ohne Kappen.',
                                   ' Der Verlauf ist umgekehrt.'])
def test_contract_does_not_discard_extra_objects_or_negations(suffix):
    assert not tube_contract(DESCRIPTION+suffix)


@pytest.mark.parametrize('damage', ['caps', 'vertical', 'horizontal', 'mark', 'color'])
def test_wrong_structure_and_paint_are_rejected(damage):
    image = independent_raster()
    if damage == 'caps':
        image[:12] = image[13]
        image[-12:] = image[-13]
    elif damage == 'vertical':
        image[11:219] = image[115]
    elif damage == 'horizontal':
        image[11:219] = image[11:219, 30:31]
    elif damage == 'mark':
        image[90:130, 20:30] = 0
    else:
        image = image[:, :, ::-1].copy()
    assert fit(image) is None


@pytest.mark.parametrize('size', 'LMS')
def test_original_jpeg_variants_pass_without_loading_the_sample(size):
    image = cv2.imread(str(ROOT/f'artifacts/images_to_convert/AC0151_{size}.jpg'))
    result = fit(image)
    assert result is not None
    assert result['error'] < 4
    assert measure_quality(image, result['svg'])['satisfactory']


def test_expired_budget_prevents_any_render():
    session = ImageSearch(SearchPolicy(), clock=lambda: 0)
    session.spent = 120
    def forbidden(*args):
        raise AssertionError('Budget is exhausted')
    with image_search(session):
        assert fit(independent_raster(), render_fn=forbidden) is None


def test_reference_render_preserves_transformed_translucent_paint():
    svg = (ROOT/'artifacts/samples/AC0151_L.svg').read_text(encoding='utf-8')
    actual = render(svg, 80, 400)
    for x, y in [(15, 80), (40, 200), (65, 320)]:
        t = (y+.5-13.333333)/373.33334
        base = (1-t)*np.array([226, 216, 54])+t*np.array([88, 167, 119])
        u = (x+.5)/80
        offsets = [0, .64004254, .65851969, 1]
        sheen = np.interp(u, offsets, [0, 230, 230, 0])
        alpha = np.interp(u, offsets, [.3137255, .25098041, .25098041, .1254902])
        expected = (base*(1-alpha)+sheen*alpha)[::-1]
        assert np.max(abs(actual[y, x].astype(float)-expected)) <= 3


@pytest.mark.parametrize('damage', [None, 'erase_cap', 'extra_object', 'remove_shading'])
def test_polished_output_requires_native_structure_and_local_cap_paint(damage):
    image = independent_raster()
    result = fit(image)
    root = ET.fromstring(result['svg'])
    if damage == 'erase_cap':
        root.findall('{*}rect')[-1].set('height', '0')
    elif damage == 'extra_object':
        # An invisible extra object cannot be certified by pixel similarity.
        ET.SubElement(root, '{http://www.w3.org/2000/svg}circle', cx='1', cy='1', r='1', fill='none')
    elif damage == 'remove_shading':
        for gradient in root.findall('.//{*}linearGradient'):
            if gradient.get('id') == 'tubeShade':
                for stop in gradient:
                    stop.set('stop-opacity', '0')
    candidate = ET.tostring(root, encoding='unicode')
    refined = dict(svg=candidate, rendered=render(candidate, 50, 230))
    assert validate_tube_refinement(refined, image, result) is (damage is None)


@pytest.mark.parametrize('mode', ['auto', 'insufficient_description'])
def test_runtime_dispatches_original_and_normalized_improved_description(mode):
    from src.iCCModules.imageCompositeConverterNonCompositeRuntime import runNonCompositeIterationImpl
    improved = next(e.findtext('beschreibung') for e in ET.parse(
        ROOT/'artifacts/images_to_convert/Finale_Wurzelformen_V3.xml').getroot().iter('entry')
        if e.get('key') == 'AC0151')
    description = normalize_description(improved) if mode == 'auto' else DESCRIPTION
    assert tube_contract(description)
    image = independent_raster()
    logs, artifacts, params = [], [], {}
    result = runNonCompositeIterationImpl(mode=mode, params=params, stripe_strategy=None,
        semantic_mode_visual_override=False, width=50, height=230, base_name='neutral',
        description=description, perc_img=image, img_path='neutral.jpg', print_fn=lambda *a: None,
        render_embedded_raster_svg_fn=None, build_gradient_stripe_svg_fn=None,
        build_gradient_stripe_validation_log_lines_fn=None, write_validation_log_fn=logs.extend,
        render_svg_to_numpy_fn=render, record_render_failure_fn=None,
        write_attempt_artifacts_fn=lambda *a: artifacts.append(a),
        calculate_error_fn=lambda a, b: float(np.mean((a.astype(float)-b)**2)))
    assert result is not None and len(artifacts) == 1
    assert logs == ['status=non_composite_raster_gradient_tube']
    assert 'gradient_tube_registration' in params
