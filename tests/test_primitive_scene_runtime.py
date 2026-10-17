"""Primitive scene reconstruction and independent missing-object counterexamples."""
import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterPrimitiveScene import fit_primitive_scene
from tools.evaluate_primitive_scene import make_cases, check_objects, damage_probe
from tools.run_plan_b_variations import render, measure_quality


def fit(image, description):
    h,w = image.shape[:2]
    return fit_primitive_scene(w,h,description=description,image=image,render_fn=render,
        error_fn=lambda a,b: float(np.mean((a.astype(float)-b.astype(float))**2)))


@pytest.mark.parametrize('case', make_cases(43123, 9), ids=lambda c:c['case_id'])
def test_independent_outline_scenes(case):
    image = render(case['svg'],case['width'],case['height'])
    original = image.copy()
    result = fit(image,case['description'])
    assert result is not None
    assert result['error'] <= result['initial_error']
    assert result['evaluations'] <= 1+32*8*len(case['expected_objects'])
    assert measure_quality(image,result['svg'])['satisfactory']
    assert check_objects(render(result['svg'],case['width'],case['height']),case['expected_objects'])['passed']
    np.testing.assert_array_equal(image,original)


@pytest.mark.parametrize('description', [
    'Zwei Kreise. Keine Beschriftung.', 'Ein Kreis und ein Rechteck. Ohne Text.',
    'Kein Kreis, ein Rechteck.', 'Ein Kreis mit Verlauf.',
    'Ein Kreis mit Buchstaben.', 'Vier Kreise.', 'Ein Kreis und weitere Kreise.',
    'Ein Kreis. Zusätzlich eine Linie.', 'Ein Kreis mit gefülltem Inneren.',
    'Ein Kreis ohne Kontur.', 'Ein Kreis ohne dunkle Kontur.',
])
def test_contradictions_and_unsupported_content_do_not_claim_success(description):
    case = dict(width=120,height=90,svg='<svg xmlns="http://www.w3.org/2000/svg" width="120" height="90"><rect width="120" height="90" fill="white"/><circle cx="60" cy="45" r="25" stroke="#333333" stroke-width="3" fill="none"/></svg>')
    assert fit(render(case['svg'],case['width'],case['height']),description) is None


def test_relative_layout_constraint():
    case = next(c for c in make_cases(43123,9) if len(c['expected_objects']) == 3)
    assert fit(render(case['svg'],case['width'],case['height']),case['description'].replace('nebeneinander','übereinander')) is None


def test_missing_small_object_can_pass_all_pixel_gates():
    result = damage_probe()
    assert result['satisfactory']
    assert not result['object_check']['passed']
    assert result['object_check']['expected_count'] == 2
    assert result['object_check']['detected_count'] == 1


def test_small_instance_is_retained_in_complete_scene():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="240" height="160"><rect width="240" height="160" fill="white"/><rect x="20" y="25" width="120" height="105" fill="none" stroke="#333333" stroke-width="4"/><circle cx="190" cy="78" r="5" fill="none" stroke="#333333" stroke-width="2"/></svg>'
    image = render(svg,240,160)
    fitted = fit(image,'Ein Rechteck und ein Kreis nebeneinander. Keine Beschriftung.')
    assert fitted is not None
    assert check_objects(fitted['rendered'],[dict(bbox=[18,23,124,109]),dict(bbox=[184,72,12,12])])['passed']


@pytest.mark.parametrize('kind',['circle','rectangle'])
def test_count_with_adjectives_keeps_distinct_instances(kind):
    shape = ('<circle cx="35" cy="40" r="20"/>' if kind == 'circle' else
             '<rect x="15" y="20" width="40" height="40"/>')
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="140" height="80"><rect width="140" height="80" fill="white"/><g fill="none" stroke="#333333" stroke-width="3">'+shape+shape.replace('cx="35"','cx="105"').replace('x="15"','x="85"')+'</g></svg>'
    noun = 'Kreise' if kind == 'circle' else 'Rechtecke'
    assert fit(render(svg,140,80),'Zwei voneinander getrennte '+noun+' nebeneinander. Keine Beschriftung.') is not None
