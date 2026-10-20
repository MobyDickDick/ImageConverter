"""Filled/nested composition, semantic contradictions and independent damage controls."""
from xml.etree import ElementTree as ET
import json

import numpy as np
import cv2
import pytest

from src.iCCModules.imageCompositeConverterLayeredScene import scene_contract, detect_instances
from src.iCCModules.imageCompositeConverterPrimitiveScene import fit_primitive_scene
from src.iCCModules.imageCompositeConverterAdaptiveSearch import ImageSearch, SearchPolicy, image_search
from tools.evaluate_layered_scene import make_cases, check_objects, local_checks
from tools.run_plan_b_variations import render, measure_quality
from tools.run_plan_b_variations import sha256, write_cases
from tools.evaluate_layered_scene import verify_report


def fit(case, description=None):
    image = render(case['svg'], case['width'], case['height'])
    original = image.copy()
    result = fit_primitive_scene(case['width'], case['height'], image=image,
        description=description or case['description'], render_fn=render,
        error_fn=lambda a, b: float(np.mean((a.astype(float)-b.astype(float))**2)))
    np.testing.assert_array_equal(image, original)
    return image, result


@pytest.mark.parametrize('case', make_cases(89021, 12), ids=lambda c:c['case_id'])
def test_independent_flat_and_nested_families(case):
    image, result = fit(case)
    assert result is not None
    assert result['source'] == 'primitive_layered_scene_v1'
    assert result['error'] <= result['initial_error']
    assert check_objects(result['svg'], case['expected_objects'])['passed']
    assert measure_quality(image, result['svg'])['satisfactory']
    assert all(q['passed'] for q in local_checks(image, result['svg'], case['expected_objects']))


@pytest.mark.parametrize('text', [
    'Ein Kreis und vier Rechtecke. Alle Formen sind gefüllt.',
    'Ein Kreis und ein Rechteck. Nicht verschachtelt. Gefüllt.',
    'Ein Kreis und ein Rechteck. Nicht nebeneinander. Gefüllt.',
    'Ein Kreis ohne dunkle Kontur. Gefüllt.',
    'Kein gefüllter Kreis und ein Rechteck.',
    'Ein gefüllter Kreis mit Beschriftung.',
    'Ein gefüllter Kreis mit Schrift.',
    'Ein gefüllter Kreis. Nicht ohne Text.',
    'Ein gefüllter Kreis ist nicht unbeschriftet.',
    'Zwei gefüllte Kreise berühren sich.',
    'Zwei gefüllte Kreise mit Verlauf.',
    'Ein Kreis und ein Rechteck ineinander, getrennt nebeneinander.',
])
def test_unsupported_and_negative_constraints_are_not_erased(text):
    assert scene_contract(text) is None


def test_nested_objects_do_not_satisfy_separate_layout():
    case = make_cases()[3]
    _, result = fit(case, case['description'].replace('ineinander verschachtelt', 'getrennt nebeneinander'))
    assert result is None


def test_an_extra_small_instance_cannot_be_dropped():
    case = make_cases()[3]
    _, result = fit(case, 'Ein Kreis und ein Rechteck. Alle Formen sind gefüllt.')
    assert result is None


def test_filled_requirement_cannot_accept_a_white_outline():
    case = dict(width=100, height=100, svg='<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect width="100" height="100" fill="white"/><circle cx="50" cy="50" r="30" fill="none" stroke="#333333" stroke-width="3"/></svg>', description='Ein gefüllter Kreis. Keine Beschriftung.')
    assert fit(case)[1] is None


def test_duplicate_color_and_foreground_detections_are_grouped():
    case = make_cases()[11]
    image = render(case['svg'], case['width'], case['height'])
    groups = detect_instances(image)
    assert len(groups) == len(case['expected_objects'])
    assert sum(len(g) for g in groups) <= 4*len(case['expected_objects'])


@pytest.mark.parametrize('damage', ['delete', 'move', 'reorder', 'hidden_extra'])
def test_independent_oracle_rejects_damaged_nested_scene(damage):
    case = make_cases()[3]
    root = ET.fromstring(case['svg'])
    child = list(root)[-1]
    if damage == 'delete':
        root.remove(child)
    elif damage == 'move':
        name = 'cx' if child.tag.endswith('circle') else 'x'
        child.set(name, str(float(child.get(name))+8))
    elif damage == 'reorder':
        root.remove(child)
        root.insert(1, child)
    else:
        root.insert(1, ET.fromstring('<circle cx="100" cy="80" r="2" fill="red"/>'))
    assert not check_objects(ET.tostring(root, encoding='unicode'), case['expected_objects'])['passed']


def test_small_nested_child_missing_is_rejected_locally_even_when_global_gate_passes():
    prefix = '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="160"><rect width="200" height="160" fill="white"/>'
    parent = '<rect x="20" y="20" width="160" height="120" fill="#3e9866"/>'
    child = '<circle cx="100" cy="80" r="4" fill="#d88032"/>'
    original, damaged = prefix+parent+child+'</svg>', prefix+parent+'</svg>'
    image = render(original, 200, 160)
    assert measure_quality(image, damaged)['satisfactory']
    assert not local_checks(image, damaged, [dict(bbox=[96, 76, 8, 8])])[0]['passed']


def test_production_mae_and_supervision_keep_a_locally_valid_refinement():
    case = make_cases()[4]
    image = render(case['svg'], case['width'], case['height'])
    session = ImageSearch(SearchPolicy(seconds=5, max_seconds=5))
    with image_search(session):
        result = fit_primitive_scene(case['width'], case['height'], image=image,
            description=case['description'], render_fn=render,
            error_fn=lambda a, b: float(np.mean(cv2.absdiff(a, b))))
    assert result is not None
    assert result['error'] < result['initial_error']
    assert all(q['passed'] for q in result['object_quality'])
    assert check_objects(result['svg'], case['expected_objects'])['passed']


@pytest.mark.parametrize('damage', ['none', 'output', 'input', 'budget', 'missing_case'])
def test_saved_cli_evidence_is_rechecked_and_tampering_rejected(tmp_path, damage):
    case = make_cases(211, 1)[0]
    svg = case['svg']
    inputs, output = tmp_path/'inputs', tmp_path/'output'
    inputs.mkdir()
    write_cases([case], inputs)
    (inputs/'manifest.json').write_text(json.dumps([case]), encoding='utf-8')
    folder = output/case['case_id']
    reports = folder/'conversion/reports'
    reports.mkdir(parents=True)
    path = folder/'result.svg'
    path.write_text(svg, encoding='utf-8')
    (folder/'reference_access.json').write_text(json.dumps(dict(blocked_svg_reads=[])), encoding='utf-8')
    row = dict(reference_access=dict(blocked_svg_reads=[]),
               params=dict(adaptive_search=dict(isolated=True, limit_seconds=5, max_seconds=4 if damage == 'budget' else 5)))
    (reports/'conversion_result_map.json').write_text(json.dumps({'case.png': row}), encoding='utf-8')
    result = dict(case, output_svg=str(path.relative_to(output)), output_sha256=sha256(path.read_bytes()),
                  accepted=True, returncode=0)
    (output/'report.json').write_text(json.dumps(dict(cases=[] if damage == 'missing_case' else [result])), encoding='utf-8')
    if damage == 'output':
        path.write_text(svg.replace('<circle', '<ellipse'), encoding='utf-8')
    if damage == 'input':
        (inputs/case['case_id']/'input'/(case['case_id']+'.png')).write_bytes(b'changed')
    if damage == 'none':
        assert verify_report(inputs, output, require_all=True)['accepted'] == 1
    else:
        with pytest.raises(ValueError):
            verify_report(inputs, output, require_all=True)


def test_an_empty_matrix_cannot_claim_acceptance(tmp_path):
    (tmp_path/'manifest.json').write_text('[]', encoding='utf-8')
    (tmp_path/'report.json').write_text('{"cases": []}', encoding='utf-8')
    with pytest.raises(ValueError, match='Incomplete CLI matrix'):
        verify_report(tmp_path, tmp_path, require_all=True)


@pytest.mark.parametrize('ratio', [.6, .7, .75])
@pytest.mark.parametrize('kind', ['circle', 'rectangle'])
def test_large_concentric_child_does_not_erase_solid_parent_alternative(ratio, kind):
    if kind == 'circle':
        shapes = '<circle cx="80" cy="80" r="60" fill="#3169ac"/>' + f'<circle cx="80" cy="80" r="{60*ratio}" fill="#d88032"/>'
        noun = 'Kreise'
    else:
        size = 120*ratio
        shapes = '<rect x="20" y="20" width="120" height="120" fill="#3169ac"/>' + f'<rect x="{80-size/2}" y="{80-size/2}" width="{size}" height="{size}" fill="#d88032"/>'
        noun = 'Rechtecke'
    case = dict(width=160, height=160, svg='<svg xmlns="http://www.w3.org/2000/svg" width="160" height="160"><rect width="160" height="160" fill="white"/>'+shapes+'</svg>', description=f'Zwei unbeschriftete gefüllte {noun} ineinander.')
    image, result = fit(case)
    assert result is not None
    assert len(result['object_kinds']) == 2
    assert measure_quality(image, result['svg'])['satisfactory']


def test_circle_radius_can_refine_without_shifting_its_center():
    from tools.evaluate_primitive_scene import rotate_cases
    case = rotate_cases(make_cases(197320, 18, wide_nesting=True))[15]
    image = render(case['svg'], case['width'], case['height'])
    with image_search(ImageSearch(SearchPolicy(seconds=5, max_seconds=5))):
        result = fit_primitive_scene(case['width'], case['height'], image=image,
            description=case['description'], render_fn=render,
            error_fn=lambda a, b: float(np.mean(cv2.absdiff(a, b))))
    assert result is not None
    assert check_objects(result['svg'], case['expected_objects'])['passed']
    assert all(q['passed'] for q in local_checks(image, result['svg'], case['expected_objects']))


def test_large_child_does_not_replace_parent_fill_seed():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="160" height="160"><rect width="160" height="160" fill="white"/><circle cx="80" cy="80" r="60" fill="#3169ac" stroke="#303030" stroke-width="2.5"/><circle cx="80" cy="80" r="45" fill="#d88032" stroke="#303030" stroke-width="2.5"/></svg>'
    groups = detect_instances(render(svg,160,160))
    outer = max(groups, key=lambda g:max(c['geometry'][2] for c in g))
    np.testing.assert_allclose(outer[0]['fill'], [172,105,49], atol=1)
