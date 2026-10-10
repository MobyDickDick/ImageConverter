"""Two-source circle/chord/T registration, holdouts and negative evidence."""
from pathlib import Path
import json
from xml.etree import ElementTree as ET

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterCircleLinework import fit_circle_linework
from src.iCCModules.imageCompositeConverterPerceptionReflection import Reflection
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
from tools.evaluate_circle_linework_recheck import symbol_semantics, measure, evaluate
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]
ET.register_namespace('', 'http://www.w3.org/2000/svg')
MANIFEST = json.loads((ROOT/'artifacts/evaluation/circle_linework_recheck_v1/manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['cases'][0]['description']


def render(svg, w, h):
    return render_svg_to_numpy_inprocess(svg, w, h, fitz_module=fitz, np_module=np, cv2_module=cv2)


def fit(image, description=DESCRIPTION, **kwargs):
    h, w = image.shape[:2]
    return fit_circle_linework(w, h, description=description, image=image,
                              render_fn=kwargs.get('render_fn', render),
                              error_fn=kwargs.get('error_fn', lambda a, b: normalized_mse(a, b)[0]))


def independent_svg(scale=1, shift=0, color='#315c94', radius=22, slope=.38):
    cx, cy = 36+shift, 32
    chords = []
    for sign in (-1, 1):
        a, b = -sign*slope, sign*radius*.6
        ys = np.sort(np.roots([1+a*a, 2*a*b, b*b-radius*radius]))
        chords.append([(cx+a*y+b, cy+y) for y in ys])
    top = cy-radius*.5
    segments = [*chords, [(cx-radius*.63, top), (cx+radius*.63, top)], [(cx, top), (cx, cy+radius*.77)]]
    lines = ''.join(f'<line x1="{a[0]*scale:g}" y1="{a[1]*scale:g}" x2="{b[0]*scale:g}" y2="{b[1]*scale:g}" '
                    f'stroke="#eef0da" stroke-width="{1.2*scale:g}"/>' for a, b in segments)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{80*scale:g}" height="{68*scale:g}">'
            f'<rect width="{80*scale:g}" height="{68*scale:g}" fill="#ffffff"/>'
            f'<circle cx="{cx*scale:g}" cy="{cy*scale:g}" r="{radius*scale:g}" '
            f'fill="{color}" stroke="#747474" stroke-width="{scale:g}"/>{lines}</svg>')


@pytest.mark.parametrize('case', MANIFEST['cases'], ids=lambda c: c['source'])
def test_all_catalog_variants_use_only_observed_pixels_and_description(case):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert'/case['source']))
    original = image.copy()
    result = fit(image)
    assert result is not None
    assert symbol_semantics(result['svg']) == 1
    assert result['error'] <= result['initial_error']
    assert normalized_mse(image, result['rendered'])[1] < .002
    assert result['evaluations'] <= 1+16*len(result['parameters'])
    np.testing.assert_array_equal(image, original)


@pytest.mark.parametrize('scale,shift,color,radius,slope', [
    (1, 0, '#315c94', 22, .38), (1, 8, '#913b28', 19, .48),
    (2, -5, '#39715f', 23, .3), (.5, 0, '#62497a', 22, .4),
    (1, .5, '#315c94', 23, .42), (1, .25, '#315c94', 23, .42)])
def test_independent_colors_position_geometry_and_resolution(scale, shift, color, radius, slope):
    source = independent_svg(scale, shift, color, radius, slope)
    image = render(source, int(80*scale), int(68*scale))
    result = fit(image)
    assert result is not None
    assert symbol_semantics(result['svg']) == symbol_semantics(source) == 1
    assert normalized_mse(image, result['rendered'])[1] < .004


@pytest.mark.parametrize('which', range(4))
def test_every_missing_line_is_rejected(which):
    root = ET.fromstring(independent_svg())
    root.remove([e for e in root if e.tag.endswith('line')][which])
    source = ET.tostring(root, encoding='unicode')
    assert symbol_semantics(source) == 0
    assert fit(render(source, 80, 68)) is None


@pytest.mark.parametrize('change', ['dot_inside', 'dot_outside', 'triangle', 'ellipse', 'upside_down', 'no_circle'])
def test_wrong_raster_topologies_are_rejected(change):
    source = independent_svg()
    if change in {'dot_inside', 'dot_outside'}:
        x, y = (30, 33) if change == 'dot_inside' else (72, 57)
        source = source.replace('</svg>', f'<circle cx="{x}" cy="{y}" r="3" fill="#111111"/></svg>')
    elif change == 'triangle':
        source = source.replace('</svg>', '<polygon points="22,23 50,23 36,48" fill="#eef0da"/></svg>')
    elif change == 'ellipse':
        source = source.replace('<circle cx="36" cy="32" r="22"', '<ellipse cx="36" cy="32" rx="22" ry="15"')
    elif change == 'no_circle':
        root = ET.fromstring(source)
        root.remove(next(e for e in root if e.tag.endswith('circle')))
        source = ET.tostring(root, encoding='unicode')
    else:
        source = source.replace('</svg>', '</g></svg>').replace('<circle', '<g transform="translate(0 68) scale(1 -1)"><circle', 1)
    assert fit(render(source, 80, 68)) is None


@pytest.mark.parametrize('description', ['', 'Ein Quadrat.', DESCRIPTION+' Zusätzlich ein Punkt.',
                                         DESCRIPTION.replace('nach unten', 'nach oben'), DESCRIPTION+' Ohne T.'])
def test_description_constraints_are_required(description):
    assert fit(render(independent_svg(), 80, 68), description) is None


@pytest.mark.parametrize('failure', ['render', 'nan', 'infinity'])
def test_measurement_failure_cannot_be_accepted(failure):
    kwargs = {'render_fn': lambda *args: None} if failure == 'render' else {'error_fn': lambda *args: float('nan' if failure == 'nan' else 'inf')}
    assert fit(render(independent_svg(), 80, 68), **kwargs) is None


def test_runtime_rename_and_parser_do_not_substitute_a_font_glyph(monkeypatch):
    image = render(independent_svg(), 80, 68)
    artifacts = []
    monkeypatch.setattr(runtime, '_try_load_sample_svg', lambda **kwargs: pytest.fail('reference SVG read'))
    for name in ('scene_7a19', 'unrelated_scene'):
        desc, params = Reflection({name: DESCRIPTION}).parse_description(name, name+'.png')
        assert params['mode'] == 'auto'
        result = runtime.runNonCompositeIterationImpl(mode=params['mode'], params=params, stripe_strategy=None,
            semantic_mode_visual_override=False, width=80, height=68, base_name=name, description=desc,
            perc_img=image, img_path=name+'.png', print_fn=lambda *args: None,
            render_embedded_raster_svg_fn=lambda *args: pytest.fail('embedded raster'),
            build_gradient_stripe_svg_fn=lambda *args, **kwargs: None,
            build_gradient_stripe_validation_log_lines_fn=lambda **kwargs: [], write_validation_log_fn=lambda *args: None,
            render_svg_to_numpy_fn=render, record_render_failure_fn=lambda *args, **kwargs: None,
            write_attempt_artifacts_fn=lambda svg, raster: artifacts.append((svg, raster)),
            calculate_error_fn=lambda a, b: normalized_mse(a, b)[0])
        assert result is not None
    assert artifacts[0][0] == artifacts[1][0]
    np.testing.assert_array_equal(artifacts[0][1], artifacts[1][1])


def test_perfect_independent_vector_calibrates_both_gates(tmp_path):
    source = independent_svg()
    (tmp_path/'perfect.svg').write_text(source, encoding='utf-8')
    assert cv2.imwrite(str(tmp_path/'source.png'), render(source, 80, 68))
    record = measure(tmp_path/'source.png', tmp_path/'perfect.svg', None)
    assert record['mean_delta2'] == 0
    assert all(value == 1 for key, value in record['metrics'].items() if key != 'error_per_pixel')
    manifest = {'provenance': {'commit': 'synthetic', 'seed': 0, 'toolchain': 'current'},
                'cases': [{'case_id': 'neutral', 'image': 'source.png', 'before_svg': 'perfect.svg', 'after_svg': 'perfect.svg'}]}
    assert evaluate(manifest, tmp_path)['satisfaction_gate']['cases'][0]['satisfactory']
