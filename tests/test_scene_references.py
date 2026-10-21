"""Named references must agree with independently generated geometry and pixels."""
from copy import deepcopy
from xml.etree import ElementTree as ET

import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterSceneReferences import color_role, parse_references, resolve_references
from src.iCCModules.imageCompositeConverterSceneVisibility import visibility_contract
from tests.test_scene_visibility import fit
from tools.evaluate_layered_scene import check_objects, local_checks
from tools.evaluate_real_scene import make_cases


@pytest.mark.parametrize('case', make_cases(871209, 12), ids=lambda c: c['case_id'])
def test_named_scene_is_grounded_in_raster_and_native_objects(case):
    image, result = fit(case)
    assert result is not None
    assert check_objects(result['svg'], case['expected_objects'])['passed']
    assert all(q['passed'] for q in local_checks(image, result['svg'], case['expected_objects']))


@pytest.mark.parametrize('bad', ['türkise', 'mittlere', 'nicht rote', 'rote und blaue'])
def test_unmodelled_role_is_not_erased(bad):
    assert visibility_contract(f'Zwei gefüllte Kreise überlappen teilweise. Die {bad} Form liegt vor der blauen Form.') is None


@pytest.mark.parametrize('replacement', [
    ('vor der blauen', 'hinter der blauen'),
    ('orange Form', 'grüne Form'),
    ('orange Form', 'blaue Form'),
])
def test_wrong_missing_or_aliased_color_reference_cannot_override_pixels(replacement):
    case = make_cases(871209, 1)[0]
    _, result = fit(case, case['description'].replace(*replacement))
    assert result is None


def test_duplicate_color_is_ambiguous_even_with_clear_sizes():
    case = deepcopy(make_cases(871209, 1)[0])
    root = ET.fromstring(case['svg'])
    root[2].set('fill', root[1].get('fill'))
    case['svg'] = ET.tostring(root, encoding='unicode')
    _, result = fit(case, case['description'].replace('orange Form', 'blaue Form'))
    assert result is None


@pytest.mark.parametrize('relation,passes', [('links von', True), ('rechts von', False), ('oberhalb', True), ('unterhalb', False)])
def test_explicit_position_relation_is_checked_during_refinement(relation, passes):
    case = make_cases(871209, 1)[0]
    description = case['description']+f' Die blaue Form liegt {relation} der orangen Form.'
    _, result = fit(case, description)
    assert (result is not None) == passes


def test_aligned_positions_do_not_resolve_left_and_right_from_noise():
    scene = [dict(kind='circle', geometry=[x, 10, 20, 20, 0], fill=np.array([150, 70, 30])) for x in (10, 12)]
    assert resolve_references(scene, [('linke', 'vor', 'rechte')]) is None


def test_color_only_depth_does_not_require_distinct_sizes():
    scene = [dict(kind='circle', geometry=[x, 10, 20, 20, 0], fill=np.array(c))
             for x, c in [(10, [172, 105, 49]), (20, [50, 128, 216])]]
    assert resolve_references(scene, [('orange', 'vor', 'blaue')]) == {'orange': 1, 'blaue': 0}


def test_uncertain_hue_and_gray_brightness_are_not_confident_labels():
    assert color_role([180, 180, 180]) == 'graue'
    assert color_role([180, 180, 20]) is None  # cyan is outside the vocabulary
    assert color_role([235, 235, 235]) is None
    assert parse_references('Die rote Form liegt nicht vor der blauen Form.') is None


@pytest.mark.parametrize('clause', ['Die rote Form schwebt über der blauen Form.',
                                   'Die Form befindet sich vorn.',
                                   'Die rote Form liegt neben der blauen Form.'])
def test_unknown_relation_predicate_cannot_be_silently_ignored(clause):
    assert visibility_contract('Zwei gefüllte Kreise überlappen teilweise. '+clause) is None
    case = make_cases(871209, 2)[1]  # unoutlined scene can otherwise reach legacy fusion
    description = 'Zwei einfarbig gefüllte Rechtecke überlappen teilweise. Keine Beschriftung. '+clause
    _, result = fit(case, description)
    assert result is None


def test_refinement_rechecks_color_parameters_instead_of_initial_palette(monkeypatch):
    from src.iCCModules import imageCompositeConverterLayeredScene as runtime
    register = runtime._register
    checked = []

    def probe(parameters, geometry_count, build, valid, *args, **kwargs):
        n = geometry_count//5
        swapped = parameters.copy()
        a, b = 5*n+3, 5*n+9
        swapped[a:a+3], swapped[b:b+3] = parameters[b:b+3], parameters[a:a+3]
        assert valid(parameters)
        assert not valid(swapped)
        checked.append(True)
        return register(parameters, geometry_count, build, valid, *args, **kwargs)

    monkeypatch.setattr(runtime, '_register', probe)
    _, result = fit(make_cases(871209, 1)[0])
    assert result is not None and checked


def test_global_motif_translation_does_not_become_an_object_reference():
    text = make_cases(871209, 1)[0]['description']
    for subject in ('Das gesamte Motiv', 'Die Darstellung'):
        clause = f' {subject} ist ein wenig größer dargestellt und etwas nach links und oben versetzt.'
        assert visibility_contract(text+clause) is not None
        assert visibility_contract(text+clause+' Die Form schwebt.') is None


def test_color_reference_uses_actual_svg_channels_even_when_search_leaves_rgb_range():
    assert color_role([-100, 50, 200]) == color_role([0, 50, 200])
    assert color_role([300, 110, 20]) == color_role([255, 110, 20])
