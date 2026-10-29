"""Cross-renderer regression for fitted SVG baselines and real glyph positions."""
import copy
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules import imageCompositeConverterGeometryIr as geometry
from tools.evaluate_svg_text_baseline import (find_librsvg, render_librsvg,
    square_glyph_evidence, square_glyph_position)
from tools.run_plan_b_variations import measure_quality, render

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT/'artifacts/satisfactory_conversions'
T_CASES = [c for c in json.loads((ARCHIVE/'index.json').read_text())['cases']
           if c['variant'].startswith('AC0721')]


@pytest.fixture(scope='module', params=[None, 'Liberation Sans'], ids=['system-fonts', 'liberation-fallback'])
def independent(request):
    try:
        executable = find_librsvg()
    except FileNotFoundError as error:
        pytest.skip(str(error))
    def renderer(svg, width, height):
        if request.param:
            svg = svg.replace('Arial, Helvetica, sans-serif', request.param)
        return render_librsvg(svg, width, height, executable=executable)
    return renderer


@pytest.mark.parametrize('case', T_CASES, ids=lambda c:c['variant'])
def test_fresh_registered_t_matches_original_pixels_in_both_renderers(case, independent):
    from src.iCCModules.imageCompositeConverterLabeledSquare import fit_labeled_square
    from src.iCCModules.imageCompositeConverterDiffing import calculateErrorImpl
    image = cv2.imread(str(ARCHIVE/case['image']))
    h, w = image.shape[:2]
    fitted = fit_labeled_square(geometry.buildGeometryIrFromDescriptionImpl(case['description']),
        image=image, render_fn=lambda ir:render(geometry.renderGeometryIrToSvgImpl(w, h, ir), w, h),
        error_fn=lambda raster:calculateErrorImpl(image, raster, cv2_module=cv2, np_module=np))
    assert fitted is not None
    svg = geometry.renderGeometryIrToSvgImpl(w, h, fitted['geometry_ir'])
    assert 'dominant-baseline="alphabetic"' in svg
    for renderer in (render, independent):
        evidence = square_glyph_evidence(image, svg, renderer)
        assert evidence['passed'], evidence
    quality = measure_quality(image, svg, render_fn=independent)
    assert quality['satisfactory'], quality
    # The archive contains the independently checked coverage refinement too.
    old = (ARCHIVE/case['svg']).read_text()
    np.testing.assert_array_equal(render(old, w, h), render(svg, w, h))


def test_linux_font_fallback_reproduces_prior_failure_and_retains_strict_gates():
    evidence = ROOT/'artifacts/evaluation/labeled_t_square_recheck_v1'
    manifest = json.loads((evidence/'manifest.json').read_text())
    case = next(c for c in manifest['cases'] if c['source'] == 'AC0721_M.jpg')
    image = cv2.imread(str(evidence/case['image']))
    original = (evidence/case['after_svg']).read_text().replace(
        'dominant-baseline="middle"', 'dominant-baseline="alphabetic"')
    try:
        executable = find_librsvg()
    except FileNotFoundError as error:
        pytest.skip(str(error))
    fallback = lambda s, w, h: render_librsvg(
        s.replace('Arial, Helvetica, sans-serif', 'Liberation Sans'), w, h, executable=executable)
    old = measure_quality(image, original, render_fn=fallback)
    assert not old['satisfactory']
    assert old['failures'] == ['foreground_iou_outside_limit']
    fixed = (ARCHIVE/'svgs/AC0721_M.svg').read_text()
    new = measure_quality(image, fixed, render_fn=fallback)
    assert new['limits'] == old['limits']
    assert new['satisfactory'], new


def test_shifted_glyph_fails_despite_valid_anchor_and_exact_letter(independent, tmp_path):
    svg = (ARCHIVE/'svgs/AC0721_1_L.svg').read_text()
    fixed = svg.replace('dominant-baseline="middle"', 'dominant-baseline="alphabetic"')
    assert square_glyph_position(fixed, independent)
    # Reproduce the browser shift caused by the historical emitted convention.
    old = fixed.replace('dominant-baseline="alphabetic"', 'dominant-baseline="middle"')
    image = cv2.imread(str(ARCHIVE/'images/AC0721_1_L.jpg'))
    assert not square_glyph_evidence(image, old, independent)['passed']
    # A new explicit baseline can still be geometrically wrong. The anchor stays
    # inside the square (4.5 .. 28.5), but the actual glyph is displaced.
    shifted = fixed.replace('y="23.5"', 'y="28.25"')
    # The pale letter can overlap a similar-colored rim. Only the source-pixel
    # comparison establishes that its visible top edge has moved downward.
    from tools.evaluate_labeled_square_recheck import measure
    path = tmp_path/'shifted.svg'
    path.write_text(shifted, encoding='utf-8')
    assert measure(ARCHIVE/'images/AC0721_1_L.jpg', path, 'T')['metrics']['semantic_score'] == 0
    assert not square_glyph_evidence(image, shifted, independent)['passed']


def test_missing_or_invisible_text_has_no_acceptable_glyph():
    svg = (ARCHIVE/'svgs/AC0721_1_L.svg').read_text()
    assert not square_glyph_position(svg.replace('>T</text>', '></text>'))
    assert not square_glyph_position(svg.replace('<text ', '<text opacity="0" '))


@pytest.mark.parametrize('element', [
    {'kind':'UprightSquareKelleGlyph', 'label':'T'},
    {'kind':'VerticalTwoWayValveMotorGlyph', 'label':'M'},
    {'kind':'TextGlyph', 'text':'rF', 'bbox':[.1,.1,.8,.8]},
])
def test_geometry_emitters_use_alphabetic_coordinates(element):
    element = copy.deepcopy(element)
    element['id'] = 'anonymous'
    svg = geometry.renderGeometryIrToSvgImpl(60, 60, [element])
    texts = [e for e in ET.fromstring(svg).iter() if e.tag.endswith('text')]
    assert texts
    assert all(e.get('dominant-baseline') == 'alphabetic' for e in texts)


def test_audit_does_not_accept_missing_renderer():
    with pytest.raises((OSError, FileNotFoundError)):
        render_librsvg('<svg/>', 10, 10, executable='missing-rsvg-baseline-audit')


def test_archive_refresh_replays_all_six_verified_repairs_from_unchanged_evidence():
    from tools.refresh_satisfactory_archive import archived_svg_bytes
    evidence = ROOT/'artifacts/evaluation/labeled_t_square_recheck_v1'
    manifest = json.loads((evidence/'manifest.json').read_text())
    for case in manifest['cases']:
        historical = evidence/case['after_svg']
        archived = ARCHIVE/'svgs'/Path(case['source']).with_suffix('.svg')
        assert 'dominant-baseline="middle"' in historical.read_text()
        assert archived_svg_bytes(ROOT, historical) == archived.read_bytes()
