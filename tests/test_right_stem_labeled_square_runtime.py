"""Right-handle registration must keep described text horizontal in native SVG."""
from pathlib import Path
import copy
import json

import cv2
import fitz
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterGeometryIr as geometry
from src.iCCModules import imageCompositeConverterNonCompositeRuntime as runtime
from src.iCCModules.imageCompositeConverterDiffing import calculateErrorImpl
from src.iCCModules.imageCompositeConverterLabeledSquare import fit_labeled_square
from src.iCCModules.imageCompositeConverterRendering import render_svg_to_numpy_inprocess
from tools.evaluate_labeled_square_recheck import labeled_square_semantics, measure, evaluate
from tools.run_plan_b_variations import measure_quality, make_variations

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/right_stem_labeled_square_recheck_v1'
MANIFEST = json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['description']


def render(svg, width, height):
    return render_svg_to_numpy_inprocess(svg, width, height, fitz_module=fitz, np_module=np, cv2_module=cv2)


def fit(image, description=DESCRIPTION, objective=None, renderer=None):
    h, w = image.shape[:2]
    return fit_labeled_square(geometry.buildGeometryIrFromDescriptionImpl(description), image=image,
        render_fn=renderer or (lambda ir: render(geometry.renderGeometryIrToSvgImpl(w, h, ir), w, h)),
        error_fn=objective or (lambda raster: calculateErrorImpl(image, raster, cv2_module=cv2, np_module=np)))


@pytest.mark.parametrize('case', MANIFEST['cases'], ids=lambda c: c['source'])
def test_catalog_holdouts_pass_regular_semantics_and_strict_pixel_limits(case):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert'/case['source']))
    result = fit(image)
    assert result is not None and result['final_error'] < result['initial_error']
    assert result['evaluations'] <= 204
    h, w = image.shape[:2]
    svg = geometry.renderGeometryIrToSvgImpl(w, h, result['geometry_ir'])
    assert labeled_square_semantics(svg, 'P', 'right') == 1
    assert measure_quality(image, svg)['satisfactory']
    assert '>P</text>' in svg and '<image' not in svg and 'transform=' not in svg


def synthetic(scale=1, shift=0, fill='#2458a0', label='P'):
    svg = (EVIDENCE/'independent.svg').read_text(encoding='utf-8')
    svg = svg.replace('width="64" height="44"', f'width="{64*scale}" height="{44*scale}" viewBox="0 0 64 44"')
    svg = svg.replace('x="8"', f'x="{8+shift}"').replace('M 38 22', f'M {38+shift} 22')
    svg = svg.replace('x="23"', f'x="{23+shift}"').replace('#2458a0', fill).replace('>P</text>', f'>{label}</text>')
    if fill == '#eeeeee':
        svg = svg.replace('#f3e9d7', '#505050')
    return svg, render(svg, 64*scale, 44*scale)


@pytest.mark.parametrize('scale,shift,fill', [(1,0,'#2458a0'), (1,3,'#eeeeee'), (2,2,'#a05020')])
@pytest.mark.parametrize('label', ['P', 'M', 'T', 'p'])
def test_independent_color_polarity_position_resolution_and_explicit_glyph(scale, shift, fill, label):
    _, image = synthetic(scale, shift, fill, label)
    result = fit(image, DESCRIPTION.replace('"P"', f'"{label}"'))
    assert result is not None
    h, w = image.shape[:2]
    svg = geometry.renderGeometryIrToSvgImpl(w, h, result['geometry_ir'])
    assert labeled_square_semantics(svg, label, 'right') == 1
    assert measure_quality(image, svg)['satisfactory']
    assert result['evaluations'] <= 204


def runtime_convert(image, name, label, monkeypatch):
    desc = DESCRIPTION.replace('"P"', f'"{label}"')
    h, w = image.shape[:2]
    artifacts, logs = [], []
    monkeypatch.setattr(runtime, '_try_load_sample_svg', lambda **kwargs: pytest.fail('reference SVG access'))
    params = {'mode':'non_composite', 'description_fragments':[{'text':desc}]}
    result = runtime.runNonCompositeIterationImpl(mode='non_composite', params=params, stripe_strategy=None,
        semantic_mode_visual_override=False, width=w, height=h, base_name=name,
        description=desc.lower(), perc_img=image, img_path=f'{name}.png', print_fn=lambda *args: None,
        render_embedded_raster_svg_fn=lambda path: pytest.fail('raster embedding'),
        build_gradient_stripe_svg_fn=lambda *args, **kwargs: None,
        build_gradient_stripe_validation_log_lines_fn=lambda **kwargs: [], write_validation_log_fn=logs.append,
        render_svg_to_numpy_fn=render, record_render_failure_fn=lambda *args, **kwargs: None,
        write_attempt_artifacts_fn=lambda svg, raster: artifacts.append((svg, raster)),
        calculate_error_fn=lambda target, raster: calculateErrorImpl(target, raster, cv2_module=cv2, np_module=np))
    assert result is not None and logs[-1] == ['status=non_composite_raster_labeled_square']
    assert params['labeled_square_registration']['source'] == 'raster_labeled_square_registration_v1'
    return artifacts[-1]


@pytest.mark.parametrize('label', ['P', 'M', 'T', 'p'])
def test_runtime_preserves_case_and_filename_invariance_without_sample_access(label, monkeypatch):
    _, image = synthetic(label=label)
    svg, raster = runtime_convert(image, 'anonymous', label, monkeypatch)
    renamed, other = runtime_convert(image, 'unrelated', label, monkeypatch)
    assert svg == renamed and f'>{label}</text>' in svg
    np.testing.assert_array_equal(raster, other)


def test_small_pale_catalog_symbol_precedes_panel_fallback(monkeypatch):
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/AC0734_S.jpg'))
    svg, _ = runtime_convert(image, 'pale_holdout', 'P', monkeypatch)
    assert measure_quality(image, svg)['satisfactory']


@pytest.mark.parametrize('mutation', ['handle', 'text', 'circle', 'extra', 'disconnected'])
def test_missing_parts_wrong_topology_and_unclaimed_objects_are_rejected(mutation):
    from xml.etree import ElementTree as ET
    svg, _ = synthetic()
    root = ET.fromstring(svg)
    if mutation in {'handle', 'text'}:
        tag = 'path' if mutation == 'handle' else 'text'
        root.remove(next(e for e in root if e.tag.endswith(tag)))
    elif mutation == 'circle':
        e = next(e for e in root if e.tag.endswith('rect'))
        e.tag = '{http://www.w3.org/2000/svg}circle'
        e.attrib.update(cx='23', cy='22', r='15')
    elif mutation == 'extra':
        ET.SubElement(root, '{http://www.w3.org/2000/svg}circle', cx='56', cy='37', r='2', fill='black')
    else:
        next(e for e in root if e.tag.endswith('path')).set('d', 'M 43 22 L 60 22')
    image = render(ET.tostring(root, encoding='unicode'), 64, 44)
    assert fit(image) is None


@pytest.mark.parametrize('value', [float('nan'), float('inf'), 1.])
def test_nonfinite_and_constant_objectives_do_not_accept_or_mutate(value):
    _, image = synthetic()
    ir = geometry.buildGeometryIrFromDescriptionImpl(DESCRIPTION)
    before = copy.deepcopy(ir)
    assert fit_labeled_square(ir, image=image, render_fn=lambda _: image, error_fn=lambda _: value) is None
    assert ir == before


def test_invalid_rasters_and_missing_rendering_are_rejected():
    _, image = synthetic()
    assert fit(image, renderer=lambda _: None) is None
    assert fit(np.full(image.shape, np.nan)) is None
    assert fit(image, DESCRIPTION.replace('Text "P"', 'Text "rF"')) is None


def test_semantic_checker_calibrates_perfect_svg_and_rejects_mutations(tmp_path):
    svg, image = synthetic()
    source, vector = tmp_path/'source.png', tmp_path/'vector.svg'
    assert cv2.imwrite(str(source), image)
    vector.write_text(svg, encoding='utf-8')
    result = measure(source, vector, 'P', 'right')
    assert result['mean_delta2'] == 0 and all(v == 1 for k,v in result['metrics'].items() if k != 'error_per_pixel')
    assert labeled_square_semantics(svg.replace('>P</text>', '>T</text>'), 'P', 'right') == 0
    assert labeled_square_semantics(svg.replace('M 38 22', 'M 43 22'), 'P', 'right') == 0
    assert labeled_square_semantics(svg.replace('</svg>', '<circle r="2"/></svg>'), 'P', 'right') == 0
    assert labeled_square_semantics(svg, 'P', 'bottom') == 0


def test_frozen_cli_evidence_passes_both_gates_without_metric_regression():
    report = evaluate(MANIFEST, EVIDENCE)
    assert report['satisfaction_gate']['summary']['satisfactory'] == 6
    assert all(not c['regressed_metrics'] for c in report['satisfaction_gate']['cases'])


@pytest.mark.parametrize('case', make_variations((EVIDENCE/'independent.svg').read_text(), DESCRIPTION, 20261011), ids=lambda c:c['case_id'])
def test_fractional_pixel_phases_from_independent_seed(case):
    image = render(case['svg'], case['width'], case['height'])
    result = fit(image, case['description'])
    assert result is not None
    svg = geometry.renderGeometryIrToSvgImpl(case['width'], case['height'], result['geometry_ir'])
    assert measure_quality(image, svg)['satisfactory']
