from pathlib import Path
import json
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterDiagonalCrossDisk import fit_diagonal_cross_disk
from tools.evaluate_diagonal_cross_disk_recheck import symbol_semantics, evaluate
from tools.run_plan_b_variations import render, measure_quality, make_variations
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/diagonal_cross_disk_recheck_v1'
MANIFEST = json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['description']
INDEPENDENT = (EVIDENCE/'independent.svg').read_text(encoding='utf-8')


def fit(image, description=DESCRIPTION, **kwargs):
    h,w = image.shape[:2]
    return fit_diagonal_cross_disk(w,h,description=description,image=image,
        render_fn=kwargs.get('render_fn',render),
        error_fn=kwargs.get('error_fn',lambda a,b:normalized_mse(a,b)[0]))


def test_catalog_raster_passes_without_changing_input():
    image = cv2.imread(str(EVIDENCE/MANIFEST['cases'][0]['image']))
    original = image.copy()
    result = fit(image)
    assert result is not None
    assert result['error']<=result['initial_error']
    assert result['evaluations']<=1+16*len(result['parameters'])
    assert symbol_semantics(result['svg'])==1
    assert measure_quality(image,result['svg'])['satisfactory']
    np.testing.assert_array_equal(image,original)


@pytest.mark.parametrize('scale,shift,color',[(.5,-2,'#305f91'),(1,5,'#347b4f'),(2,2,'#a13b4c')])
def test_independent_resolution_position_palette(scale,shift,color):
    root = ET.fromstring(INDEPENDENT)
    root.set('width',str(100*scale));root.set('height',str(92*scale))
    root[1].set('cx',str(48+shift));root[1].set('fill',color)
    for line in root[2:]:
        for key in ('x1','x2'):line.set(key,str(float(line.get(key))+shift))
    result = fit(render(ET.tostring(root,encoding='unicode'),round(100*scale),round(92*scale)))
    assert result is not None
    assert symbol_semantics(result['svg'])==1
    assert measure_quality(render(ET.tostring(root,encoding='unicode'),round(100*scale),round(92*scale)),result['svg'])['satisfactory']


@pytest.mark.parametrize('case',make_variations(INDEPENDENT,DESCRIPTION,20261015),ids=lambda c:c['case_id'])
def test_independent_subpixel_variations(case):
    image=render(case['svg'],case['width'],case['height'])
    result=fit(image,case['description'])
    assert result is not None
    assert symbol_semantics(result['svg'])==1
    assert measure_quality(image,result['svg'])['satisfactory']


@pytest.mark.parametrize('mutation',['no_disk','one_line','extra','inside_mark','gap','plus','square_caps'])
def test_incompatible_raster_is_rejected(mutation):
    root=ET.fromstring(INDEPENDENT)
    if mutation=='no_disk':root.remove(root[1])
    elif mutation=='one_line':root.remove(root[-1])
    elif mutation=='extra':ET.SubElement(root,'rect',x='1',y='1',width='5',height='5',fill='#000000')
    elif mutation=='inside_mark':ET.SubElement(root,'rect',x='44',y='14',width='8',height='5',fill='#000000')
    elif mutation=='gap':ET.SubElement(root,'rect',x='45',y='22',width='5',height='47',fill='#763da5')
    elif mutation=='plus':
        root[2].set('x1','23');root[2].set('y1','45');root[2].set('x2','73');root[2].set('y2','45')
        root[3].set('x1','48');root[3].set('y1','20');root[3].set('x2','48');root[3].set('y2','70')
    else:
        for line in root[2:]:line.set('stroke-linecap','square')
    assert fit(render(ET.tostring(root,encoding='unicode'),100,92)) is None


@pytest.mark.parametrize('description',['Ein Kreis.',DESCRIPTION+' ohne Kreuz.',DESCRIPTION+' Zusätzlich eine Linie.',
    DESCRIPTION.replace('diagonales','waagerechtes'),DESCRIPTION.replace('abgerundeten','eckigen')])
def test_conflicting_description_is_rejected(description):
    assert fit(render(INDEPENDENT,100,92),description) is None


@pytest.mark.parametrize('failure',['render','nan_error','infinite_error','dimensions','nan_image'])
def test_invalid_measurements_are_rejected(failure):
    image=render(INDEPENDENT,100,92);kwargs={}
    if failure=='render':kwargs['render_fn']=lambda *a:None
    elif failure.endswith('_error'):kwargs['error_fn']=lambda *a:float('nan' if failure=='nan_error' else 'inf')
    elif failure=='dimensions':image=image[:,:,:2]
    else:image=image.astype(float);image[0,0,0]=np.nan
    assert fit(image,**kwargs) is None


def test_semantics_reject_missing_or_nonintersecting_line_and_raster():
    assert symbol_semantics(INDEPENDENT)==1
    separated=ET.fromstring(INDEPENDENT)
    for line,coords in zip(separated[2:],[(25,27,42,44),(49,63,68,44)]):
        for key,value in zip(('x1','y1','x2','y2'),coords):line.set(key,str(value))
    assert symbol_semantics(ET.tostring(separated,encoding='unicode'))==0
    root=ET.fromstring(INDEPENDENT);root.remove(root[-1])
    assert symbol_semantics(ET.tostring(root,encoding='unicode'))==0
    ET.SubElement(root,'image',href='fake.png')
    assert symbol_semantics(ET.tostring(root,encoding='unicode'))==0


def test_saved_cli_evidence_passes_unchanged_gates():
    report=evaluate(MANIFEST,EVIDENCE)
    assert all(c['satisfactory'] and not c['regressed_metrics'] for c in report['satisfaction_gate']['cases'])
    assert all(c['satisfactory'] for c in report['strict_pixel_gates'].values())


def test_both_catalogs_have_the_independent_description():
    for folder in ('descriptions','images_to_convert'):
        root=ET.parse(ROOT/'artifacts'/folder/'Finale_Wurzelformen_V3.xml')
        entry=next(e for e in root.iter('entry') if e.get('key')=='GE0017')
        assert entry.findtext('beschreibung')==DESCRIPTION
