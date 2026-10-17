"""Left handles preserve horizontal glyphs and ignore whole-scene translations."""
from pathlib import Path
import copy
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterGeometryIr as geometry
from src.iCCModules.imageCompositeConverterDiffing import calculateErrorImpl
from src.iCCModules.imageCompositeConverterLabeledSquare import fit_labeled_square
from tools.evaluate_labeled_square_recheck import labeled_square_semantics
from tools.run_plan_b_variations import make_variations, measure_quality, render

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/left_stem_labeled_square_recheck_v1'
DESCRIPTION = (EVIDENCE/'description.txt').read_text(encoding='utf-8').strip()
REFERENCE = (EVIDENCE/'independent.svg').read_text(encoding='utf-8')


def fit(image, description=DESCRIPTION, *, error_fn=None, render_fn=None):
    h, w = image.shape[:2]
    return fit_labeled_square(geometry.buildGeometryIrFromDescriptionImpl(description), image=image,
        render_fn=render_fn or (lambda ir: render(geometry.renderGeometryIrToSvgImpl(w, h, ir), w, h)),
        error_fn=error_fn or (lambda raster: calculateErrorImpl(image, raster, cv2_module=cv2, np_module=np)))


@pytest.mark.parametrize('label', ['P', 'p', 'M', 'T'])
@pytest.mark.parametrize('scale,fill', [(1, '#e7ceaa'), (2, '#dce5ec'), (.5, '#e7ceaa')])
def test_asymmetric_text_remains_upright_at_other_sizes_and_colors(label, scale, fill):
    svg = REFERENCE.replace('>P</text>', f'>{label}</text>').replace('#e7ceaa', fill)
    svg = svg.replace('width="86" height="62"',
                      f'width="{86*scale}" height="{62*scale}" viewBox="0 0 86 62"')
    image = render(svg, int(86*scale), int(62*scale))
    result = fit(image, DESCRIPTION.replace('"M"', f'"{label}"'))
    assert result is not None and result['evaluations'] <= 204
    h, w = image.shape[:2]
    output = geometry.renderGeometryIrToSvgImpl(w, h, result['geometry_ir'])
    assert labeled_square_semantics(output, label, 'left') == 1
    assert measure_quality(image, output)['satisfactory']
    assert 'transform=' not in output and '<image' not in output


@pytest.mark.parametrize('case', make_variations(REFERENCE, DESCRIPTION.replace('"M"', '"P"'), 20261017),
                         ids=lambda c: c['case_id'])
def test_whole_scene_translation_does_not_change_handle_direction(case):
    image = render(case['svg'], case['width'], case['height'])
    result = fit(image, case['description'])
    assert result is not None
    output = geometry.renderGeometryIrToSvgImpl(case['width'], case['height'], result['geometry_ir'])
    assert labeled_square_semantics(output, 'P', 'left') == 1
    assert measure_quality(image, output)['satisfactory']


def test_catalog_raster_passes_strict_gate_and_semantic_contract():
    image = cv2.imread(str(ROOT/'artifacts/images_to_convert/SE0082.jpg'))
    result = fit(image)
    assert result is not None and result['final_error'] < result['initial_error']
    output = geometry.renderGeometryIrToSvgImpl(image.shape[1], image.shape[0], result['geometry_ir'])
    assert measure_quality(image, output)['satisfactory']
    assert labeled_square_semantics(output, 'M', 'left') == 1


def test_wrong_small_letter_is_rejected_despite_good_global_pixel_similarity():
    image = render(REFERENCE, 86, 62)  # P in the image, M in the description.
    assert fit(image) is None


def test_render_counter_includes_font_calibration_and_blank_glyph_validation():
    image = render(REFERENCE, 86, 62)
    calls = []
    def renderer(ir):
        calls.append(None)
        return render(geometry.renderGeometryIrToSvgImpl(86, 62, ir), 86, 62)
    result = fit(image, DESCRIPTION.replace('"M"', '"P"'), render_fn=renderer)
    assert result is not None
    assert result['render_evaluations'] == len(calls)
    assert result['render_evaluations'] > result['evaluations']


@pytest.mark.parametrize('mutation', ['handle', 'text', 'disconnected', 'extra', 'circle'])
def test_missing_parts_and_unclaimed_objects_are_rejected(mutation):
    root = ET.fromstring(REFERENCE)
    if mutation in {'handle', 'text'}:
        root.remove(next(e for e in root if e.tag.endswith('path' if mutation == 'handle' else 'text')))
    elif mutation == 'disconnected':
        next(e for e in root if e.tag.endswith('path')).set('d', 'M 28 29 L 7 29')
    elif mutation == 'extra':
        ET.SubElement(root, '{http://www.w3.org/2000/svg}circle', cx='14', cy='53', r='3', fill='black')
    else:
        element = next(e for e in root if e.tag.endswith('rect'))
        element.tag = '{http://www.w3.org/2000/svg}circle'
        element.attrib.update(cx='53', cy='29', r='19')
    assert fit(render(ET.tostring(root, encoding='unicode'), 86, 62),
               DESCRIPTION.replace('"M"', '"P"')) is None


@pytest.mark.parametrize('suffix', [' Ohne Beschriftung.', ' Griff nach rechts.', ' Griff nach oben.', ' Griff nach unten.'])
def test_contradictory_description_does_not_select_left_labeled_path(suffix):
    ir = geometry.buildGeometryIrFromDescriptionImpl(DESCRIPTION+suffix)
    assert not (len(ir) == 1 and ir[0].get('kind') == 'LeftRotatedSquareKelleTGlyph')


@pytest.mark.parametrize('score', [float('nan'), float('inf'), 1.])
def test_failed_measurement_and_renderer_leave_input_unchanged(score):
    image = render(REFERENCE, 86, 62)
    ir = geometry.buildGeometryIrFromDescriptionImpl(DESCRIPTION)
    original = copy.deepcopy(ir)
    assert fit_labeled_square(ir, image=image, render_fn=lambda _: image, error_fn=lambda _: score) is None
    assert ir == original
    assert fit(image, render_fn=lambda _: None) is None


def test_independent_semantics_reject_wrong_text_direction_and_mirroring():
    assert labeled_square_semantics(REFERENCE, 'P', 'left') == 1
    assert labeled_square_semantics(REFERENCE, 'M', 'left') == 0
    assert labeled_square_semantics(REFERENCE, 'P', 'right') == 0
    assert labeled_square_semantics(REFERENCE.replace('M 34 29', 'M 28 29'), 'P', 'left') == 0
    assert labeled_square_semantics(REFERENCE.replace('<text ', '<text transform="scale(-1 1)" '), 'P', 'left') == 0
