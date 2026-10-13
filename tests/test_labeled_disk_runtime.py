"""Raster, semantic and replay contracts for described outlined letter disks."""
from pathlib import Path
import hashlib
import json
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterLabeledDisk import fit_labeled_disk
from tools.evaluate_labeled_disk_recheck import symbol_semantics
from tools.run_plan_b_variations import render, measure_quality

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/labeled_disk_recheck_v1'
MANIFEST = json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['description']


def fit(image, description=DESCRIPTION, render_fn=render):
    h, w = image.shape[:2]
    return fit_labeled_disk(w, h, description=description, image=image, render_fn=render_fn,
        error_fn=lambda a,b: float(np.mean(np.abs(a.astype(float)-b.astype(float)))))


def synthetic(label='Q', width=96, height=88, shift=0):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
            f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
            f'<circle cx="{width/2+shift}" cy="{height/2}" r="{height*.35}" fill="#d5e9df" stroke="#497361" stroke-width="{height*.023}"/>'
            f'<text x="{width/2+shift-1}" y="{height*.66}" font-family="Arial" font-weight="700" font-size="{height*.43}" text-anchor="middle" fill="#315841">{label}</text></svg>')


@pytest.mark.parametrize('case', MANIFEST['cases'], ids=lambda c: c['role']+'-'+c['case_id'])
def test_catalog_pixels_register_with_native_text(case):
    image_path=EVIDENCE/case['image']
    assert hashlib.sha256(image_path.read_bytes()).hexdigest() == case['source_sha256']
    image=cv2.imread(str(image_path))
    result=fit(image)
    assert result is not None
    assert symbol_semantics(result['svg']) == 1
    assert measure_quality(image,result['svg'])['satisfactory']
    assert result['error'] <= result['initial_error']
    assert result['evaluations'] <= 257


@pytest.mark.parametrize('label', ['Q','R','P','D','A'])
@pytest.mark.parametrize('size', [(48,44,0),(96,88,6),(192,176,-8)])
def test_independent_letters_sizes_and_positions(label,size):
    svg=synthetic(label,*size)
    image=render(svg,size[0],size[1])
    result=fit(image,DESCRIPTION.replace('"Q"',f'"{label}"'))
    assert result is not None
    assert symbol_semantics(result['svg'],label) == 1
    assert measure_quality(image,result['svg'])['satisfactory']


@pytest.mark.parametrize('description', ['', 'Ein Quadrat.', DESCRIPTION+' Zusätzlich ein Punkt.',
    DESCRIPTION.replace('"Q"','"QQ"'), DESCRIPTION.replace('dunkle Großbuchstabe','helle Großbuchstabe'),
    DESCRIPTION.replace('Keine Anschlüsse','Ein Griff'), DESCRIPTION+' Ein Farbverlauf.',
    DESCRIPTION+' Der einzelne dunkle Buchstabe "R".'])
def test_unsupported_or_conflicting_description_rejected(description):
    assert fit(render(synthetic(),96,88),description) is None


@pytest.mark.parametrize('kind', ['missing_letter','wrong_letter','similar_letter','extra_mark','square','missing_rim','background'])
def test_conflicting_raster_rejected(kind):
    svg=synthetic()
    if kind=='missing_letter':
        ET.register_namespace('', 'http://www.w3.org/2000/svg')
        root=ET.fromstring(svg); root.remove(next(e for e in root if e.tag.endswith('text'))); svg=ET.tostring(root,encoding='unicode')
    elif kind=='wrong_letter': svg=svg.replace('>Q<','>R<')
    elif kind=='similar_letter': svg=svg.replace('>Q<','>O<')
    elif kind=='extra_mark': svg=svg.replace('</svg>','<rect x="5" y="5" width="5" height="5" fill="#111111"/></svg>')
    elif kind=='square': svg=svg.replace('<circle cx="48.0" cy="44.0" r="30.799999999999997"','<rect x="17" y="13" width="62" height="62"')
    elif kind=='missing_rim': svg=svg.replace('stroke="#497361"','stroke="#d5e9df"')
    elif kind=='background': svg=svg.replace('#ffffff','#bbbbbb')
    assert fit(render(svg,96,88)) is None


def test_missing_render_and_nonfinite_pixels_rejected():
    image=render(synthetic(),96,88)
    assert fit(image,render_fn=lambda *args:None) is None
    image=image.astype(float); image[20,20]=np.nan
    assert fit(image) is None


def test_semantic_gate_rejects_wrong_text_and_extra_shapes():
    result=fit(render(synthetic(),96,88))
    assert result is not None
    svg=result['svg']
    for bad in [svg.replace('>Q<','>R<'),svg.replace('font-size="','font-size="nan'),
                svg.replace('</svg>','<path d="M 1 1 L 2 2"/></svg>'),svg.replace('stroke-width="','stroke-width="nan')]:
        assert symbol_semantics(bad)==0


@pytest.mark.parametrize('size', ['S', 'M', 'L'])
def test_motor_disk_catalog_sizes_with_described_m(size):
    """Include the large tightly cropped disk that rejected its initial fit."""
    image = cv2.imread(str(ROOT/f'artifacts/images_to_convert/AC1000_{size}.jpg'))
    result = fit(image, DESCRIPTION.replace('"Q"', '"M"'))
    assert result is not None
    assert symbol_semantics(result['svg'], 'M') == 1
    assert measure_quality(image, result['svg'])['satisfactory']


@pytest.mark.parametrize('size', [30, 60, 90])
def test_independent_tightly_cropped_letter_disks(size):
    # The visible outer contour nearly fills the viewport. Its radius cannot
    # be reused as a stroke centre radius when constructing the first fit.
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">'
           f'<rect width="{size}" height="{size}" fill="#ffffff"/>'
           f'<circle cx="{size/2}" cy="{size/2}" r="{size/2-size*.04}" '
           f'fill="#dae8d2" stroke="#54703d" stroke-width="{size*.06}"/>'
           f'<text x="{size/2}" y="{size*.72}" font-family="Arial" '
           f'font-weight="700" font-size="{size*.6}" text-anchor="middle" fill="#3b5429">M</text></svg>')
    image = render(svg, size, size)
    result = fit(image, DESCRIPTION.replace('"Q"', '"M"'))
    assert result is not None
    assert symbol_semantics(result['svg'], 'M') == 1
    assert measure_quality(image, result['svg'])['satisfactory']


def test_motor_semantics_requires_m_instead_of_default_q():
    from tools.evaluate_labeled_disk_recheck import measure
    evidence = ROOT/'artifacts/evaluation/motor_disk_recheck_v1'
    manifest = json.loads((evidence/'manifest.json').read_text(encoding='utf-8'))
    case = manifest['cases'][0]
    assert measure(evidence/case['image'], evidence/case['after_svg'], 'M')['metrics']['semantic_score'] == 1
    assert measure(evidence/case['image'], evidence/case['after_svg'])['metrics']['semantic_score'] == 0
