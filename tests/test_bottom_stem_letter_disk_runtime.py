"""Independent raster and negative contracts for a labeled disk with lower stem."""
from pathlib import Path
import json
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterLabeledDisk import fit_labeled_disk
from tools.evaluate_labeled_disk_recheck import symbol_semantics
from tools.run_plan_b_variations import render, measure_quality

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT/'artifacts/evaluation/bottom_stem_letter_disk_recheck_v1'
MANIFEST = json.loads((FOLDER/'manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['description']


def synthetic(label='R', scale=1, shift=0):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{96*scale}" height="{120*scale}">'
            f'<rect width="{96*scale}" height="{120*scale}" fill="#ffffff"/>'
            f'<line x1="{(46+shift)*scale}" y1="{76*scale}" x2="{(46+shift)*scale}" y2="{109*scale}" stroke="#497361" stroke-width="{3*scale}"/>'
            f'<circle cx="{(46+shift)*scale}" cy="{45*scale}" r="{31*scale}" fill="#d5e9df" stroke="#497361" stroke-width="{2*scale}"/>'
            f'<text x="{(45+shift)*scale}" y="{60*scale}" font-family="Arial" font-weight="700" font-size="{40*scale}" text-anchor="middle" fill="#315841">{label}</text></svg>')


def fit(image, description=DESCRIPTION, render_fn=render):
    h, w = image.shape[:2]
    return fit_labeled_disk(w, h, description=description, image=image, render_fn=render_fn,
                           error_fn=lambda a,b: float(np.mean(np.abs(a.astype(float)-b.astype(float)))))


@pytest.mark.parametrize('case', MANIFEST['cases'], ids=lambda c: c['source'])
def test_catalog_and_saved_acceptance(case):
    image = cv2.imread(str(FOLDER/case['image']))
    result = fit(image)
    assert result is not None
    assert symbol_semantics(result['svg'], bottom_stem=True) == 1
    assert measure_quality(image, result['svg'])['satisfactory']
    assert result['error'] <= result['initial_error']
    assert result['evaluations'] <= 337


@pytest.mark.parametrize('label', ['Q', 'R', 'P'])
@pytest.mark.parametrize('scale,shift', [(.5,0), (1,7), (2,-5)])
def test_independent_geometry_palette_and_letter(label, scale, shift):
    image = render(synthetic(label,scale,shift), int(96*scale), int(120*scale))
    result = fit(image, DESCRIPTION.replace('"Q"', f'"{label}"'))
    assert result is not None
    assert symbol_semantics(result['svg'], label, bottom_stem=True) == 1
    assert measure_quality(image, result['svg'])['satisfactory']


@pytest.mark.parametrize('kind', ['no_stem', 'detached', 'off_axis', 'wide', 'extra_mark', 'wrong_letter', 'square'])
def test_conflicting_raster_rejected(kind):
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    root = ET.fromstring(synthetic('Q'))
    line, circle, text = (next(e for e in root if e.tag.endswith(tag)) for tag in ('line','circle','text'))
    if kind == 'no_stem': root.remove(line)
    elif kind == 'detached': line.set('y1','84')
    elif kind == 'off_axis': line.set('x1','52'); line.set('x2','52')
    elif kind == 'wide': line.set('stroke-width','19')
    elif kind == 'extra_mark': ET.SubElement(root, 'rect', x='4', y='4', width='5', height='5', fill='#111111')
    elif kind == 'wrong_letter': text.text = 'R'
    elif kind == 'square':
        root.remove(circle)
        ET.SubElement(root, 'rect', x='15', y='14', width='62', height='62', fill='#d5e9df', stroke='#497361')
    assert fit(render(ET.tostring(root,encoding='unicode'),96,120)) is None


@pytest.mark.parametrize('suffix', [' Ohne Griff.', ' Keine Anschlüsse.', ' Ein Griff nach oben.',
                                  ' Zusätzlich ein Punkt.', ' Ein Farbverlauf.'])
def test_conflicting_description_rejected(suffix):
    assert fit(render(synthetic('Q'),96,120), DESCRIPTION+suffix) is None


def test_independent_semantics_reject_missing_detached_or_wrong_stem_and_label():
    svg = synthetic('Q')
    assert symbol_semantics(svg, bottom_stem=True) == 1
    assert symbol_semantics(svg) == 0
    for replacement in [svg.replace('y1="76"','y1="84"'), svg.replace('>Q<','>R<'),
                        svg.replace('x2="46"','x2="52"'), svg.replace('stroke-width="3"','stroke-width="20"')]:
        assert symbol_semantics(replacement, bottom_stem=True) == 0
