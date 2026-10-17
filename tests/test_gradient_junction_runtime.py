"""Pixel-driven T junctions: independent geometry, palettes, and contradictions."""
from pathlib import Path
import json

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterGradientJunction import fit_gradient_junction
from src.iCCModules.imageCompositeConverterDiffing import calculateErrorImpl
from tools.evaluate_gradient_junction_recheck import symbol_semantics, evaluate
from tools.run_plan_b_variations import render, measure_quality, make_variations

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'artifacts/evaluation/gradient_junction_recheck_v1'
MANIFEST=json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
DESCRIPTION=MANIFEST['description']
INDEPENDENT=(EVIDENCE/'independent.svg').read_text(encoding='utf-8')


def fit(image, description=DESCRIPTION, **kwargs):
    height,width=image.shape[:2]
    return fit_gradient_junction(width,height,description=description,image=image,
        render_fn=kwargs.get('render_fn',render),
        error_fn=kwargs.get('error_fn',lambda a,b:calculateErrorImpl(a,b,cv2_module=cv2,np_module=np)))


@pytest.mark.parametrize('phrase',['heller zentraler Zone','hellem Zentrum','aufgehellter Mitte'])
def test_bright_center_paraphrases_preserve_geometry(phrase):
    image=render(INDEPENDENT,128,96)
    description=DESCRIPTION.replace('heller Mitte',phrase)
    baseline=fit(image,DESCRIPTION)
    result=fit(image,description)
    assert baseline is not None and result is not None
    assert result['svg']==baseline['svg']


@pytest.mark.parametrize('phrase',['keine helle zentrale Zone','ohne helle Mitte','nicht aufgehellter Mitte'])
def test_negated_bright_center_is_not_accepted(phrase):
    image=render(INDEPENDENT,128,96)
    assert fit(image,DESCRIPTION.replace('heller Mitte',phrase)) is None


@pytest.mark.parametrize('case',MANIFEST['cases'],ids=lambda c:c['source'])
def test_anonymous_color_and_size_holdouts(case):
    image=cv2.imread(str(EVIDENCE/case['image']))
    original=image.copy()
    result=fit(image)
    assert result is not None
    assert result['error']<=result['initial_error']
    assert result['evaluations']<=3+32*len(result['parameters'])
    initial=render(result['initial_svg'],image.shape[1],image.shape[0])
    assert result['initial_error']==calculateErrorImpl(image,initial,cv2_module=cv2,np_module=np)
    assert symbol_semantics(result['svg'])==1
    assert measure_quality(image,result['svg'])['satisfactory']
    np.testing.assert_array_equal(image,original)
    np.testing.assert_array_equal(result['rendered'],render(result['svg'],image.shape[1],image.shape[0]))


@pytest.mark.parametrize('case',make_variations(INDEPENDENT,DESCRIPTION,20261016),ids=lambda c:c['case_id'])
def test_independent_subpixel_variations(case):
    image=render(case['svg'],case['width'],case['height'])
    result=fit(image,case['description'])
    assert result is not None
    assert result['error']<=result['initial_error']
    assert symbol_semantics(result['svg'])==1
    assert measure_quality(image,result['svg'])['satisfactory']


@pytest.mark.parametrize('scale,color',[(.5,'#216e45'),(1,'#a35328'),(2,'#304f93')])
def test_other_resolution_and_palette(scale,color):
    svg=INDEPENDENT.replace('width="128" height="96"','width="%g" height="%g"'%(128*scale,96*scale)).replace('#694080',color)
    image=render(svg,round(128*scale),round(96*scale))
    result=fit(image)
    assert result is not None
    assert measure_quality(image,result['svg'])['satisfactory']


@pytest.mark.parametrize('description',['','Ein Quadrat.',DESCRIPTION+' Zusätzlich ein Punkt.',
    DESCRIPTION.replace('nach oben','nach unten'),DESCRIPTION.replace('verbunden','getrennt'),
    DESCRIPTION.replace('senkrecht','waagerecht'),DESCRIPTION+' Zwei Schäfte.'])
def test_description_contradictions(description):
    assert fit(render(INDEPENDENT,128,96),description) is None


@pytest.mark.parametrize('change',['missing_bar','missing_stem','extra_dot','flat_gradient','hole','downward'])
def test_topology_contradictions(change):
    svg=INDEPENDENT
    if change=='missing_bar':
        svg=svg.replace('<rect x="12" y="48" width="104" height="16" fill="url(#h)"/>','')
    elif change=='missing_stem':
        svg=svg.replace('<polygon points="47,12 61,12 61,48 54,56 47,48" fill="url(#v)"/>','')
    elif change=='extra_dot':
        svg=svg.replace('</svg>','<circle cx="90" cy="20" r="5" fill="#333333"/></svg>')
    elif change=='flat_gradient':
        svg=svg.replace('#eee5f1','#694080')
    elif change=='hole':
        svg=svg.replace('</svg>','<rect x="49" y="24" width="10" height="12" fill="#ffffff"/></svg>')
    else:
        svg=svg.replace('47,12 61,12 61,48 54,56 47,48','47,90 61,90 61,64 54,56 47,64')
    assert fit(render(svg,128,96)) is None


def test_invalid_measurements_and_rendering():
    image=render(INDEPENDENT,128,96)
    assert fit(image,error_fn=lambda a,b:float('nan')) is None
    assert fit(image,render_fn=lambda *args:None) is None
    assert fit(np.full((20,20,3),np.nan)) is None
    assert fit(np.full((20,20,3),255,dtype=np.uint8)) is None
    assert fit_gradient_junction(50,40,description=DESCRIPTION,image=image,render_fn=render,error_fn=lambda a,b:0) is None


def test_saved_cli_evidence_passes_both_unchanged_gates():
    report=evaluate(MANIFEST,EVIDENCE)
    assert all(c['satisfactory'] for c in report['satisfaction_gate']['cases'])
    assert all(c['satisfactory'] for c in report['strict_pixel_gates'].values())
