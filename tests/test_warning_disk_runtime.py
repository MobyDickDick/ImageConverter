from pathlib import Path
import json
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import pytest

from src.iCCModules.imageCompositeConverterWarningDisk import fit_warning_disk
from src.iCCModules.imageCompositeConverterSemantic import apply_semantic_badge_description_rules
from tools.evaluate_warning_disk_recheck import symbol_semantics, evaluate
from tools.run_plan_b_variations import render, measure_quality, make_variations
from tools.review_conversion_quality import normalized_mse

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'artifacts/evaluation/warning_disk_recheck_v1'
MANIFEST = json.loads((EVIDENCE/'manifest.json').read_text(encoding='utf-8'))
DESCRIPTION = MANIFEST['description']
INDEPENDENT = (EVIDENCE/'independent.svg').read_text(encoding='utf-8')


def fit(image, description=DESCRIPTION, **kwargs):
    h,w = image.shape[:2]
    return fit_warning_disk(w,h,description=description,image=image,
        render_fn=kwargs.get('render_fn',render),
        error_fn=kwargs.get('error_fn',lambda a,b:normalized_mse(a,b)[0]))


@pytest.mark.parametrize('case',MANIFEST['cases'],ids=lambda c:c['source'])
def test_catalog_rasters_are_registered_without_mutation(case):
    image=cv2.imread(str(EVIDENCE/case['image'])); original=image.copy()
    result=fit(image)
    assert result is not None
    assert result['error']<=result['initial_error']
    assert result['evaluations']<=1+16*len(result['parameters'])
    assert symbol_semantics(result['svg'])==1
    assert measure_quality(image,result['svg'])['satisfactory']
    np.testing.assert_array_equal(image,original)


@pytest.mark.parametrize('scale,shift,color',[(.5,-3,'#245f7b'),(1,5,'#347b4f'),(2,2,'#a13b4c')])
def test_independent_resolution_position_palette(scale,shift,color):
    root=ET.fromstring(INDEPENDENT)
    root.set('width',str(128*scale));root.set('height',str(120*scale))
    root[0][0][0].set('stop-color',color)
    # Move the whole motif, keeping the canvas and gradient relationship.
    root[2].set('cx',str(66+shift))
    root[3].set('d',f'M {64+shift} 30 L {91+shift} 78 L {40+shift} 78 Z')
    root[4].set('x1',str(65+shift));root[4].set('x2',str(65+shift));root[5].set('cx',str(65+shift))
    image=render(ET.tostring(root,encoding='unicode'),round(128*scale),round(120*scale))
    result=fit(image)
    assert result is not None
    assert symbol_semantics(result['svg'])==1
    assert measure_quality(image,result['svg'])['satisfactory']


@pytest.mark.parametrize('case',make_variations(INDEPENDENT,DESCRIPTION,20261015),ids=lambda c:c['case_id'])
def test_independent_subpixel_variations(case):
    image=render(case['svg'],case['width'],case['height'])
    result=fit(image,case['description'])
    assert result is not None
    assert symbol_semantics(result['svg'])==1
    assert measure_quality(image,result['svg'])['satisfactory']


@pytest.mark.parametrize('mutation',['no_disk','no_triangle','no_bar','no_dot','extra','inside_mark','upside_down','joined_mark','cropped'])
def test_incompatible_raster_is_rejected(mutation):
    root=ET.fromstring(INDEPENDENT)
    if mutation=='no_disk':root.remove(root[2])
    elif mutation=='no_triangle':root.remove(root[3])
    elif mutation=='no_bar':root.remove(root[4])
    elif mutation=='no_dot':root.remove(root[5])
    elif mutation=='extra':ET.SubElement(root,'rect',x='1',y='1',width='6',height='6',fill='#000000')
    elif mutation=='inside_mark':ET.SubElement(root,'rect',x='81',y='45',width='7',height='7',fill='#000000')
    elif mutation=='upside_down':root[3].set('d','M 64 85 L 91 37 L 40 37 Z')
    elif mutation=='joined_mark':root[4].set('y2','69')
    elif mutation=='cropped':root[2].set('cx','35')
    assert fit(render(ET.tostring(root,encoding='unicode'),128,120)) is None


@pytest.mark.parametrize('description',['Ein Kreis.',DESCRIPTION+' ohne Ausrufezeichen.',DESCRIPTION+' Zusätzlich eine Linie.',
    DESCRIPTION.replace('senkrechten','waagerechten'),DESCRIPTION.replace('aufrechtes','abwärts gerichtetes')])
def test_conflicting_description_is_rejected(description):
    assert fit(render(INDEPENDENT,128,120),description) is None


@pytest.mark.parametrize('failure',['render','nan_error','infinite_error','dimensions','nan_image'])
def test_invalid_measurements_are_rejected(failure):
    image=render(INDEPENDENT,128,120);kwargs={}
    if failure=='render':kwargs['render_fn']=lambda *a:None
    elif failure.endswith('_error'):kwargs['error_fn']=lambda *a:float('nan' if failure=='nan_error' else 'inf')
    elif failure=='dimensions':image=image[:,:,:2]
    else:image=image.astype(float);image[0,0,0]=np.nan
    assert fit(image,**kwargs) is None


def test_semantic_checker_rejects_missing_dot_joined_ink_and_raster():
    assert symbol_semantics(INDEPENDENT)==1
    root=ET.fromstring(INDEPENDENT);root.remove(root[-1])
    assert symbol_semantics(ET.tostring(root,encoding='unicode'))==0
    root=ET.fromstring(INDEPENDENT);root[4].set('y2','69')
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
        entry=next(e for e in root.iter('entry') if e.get('key')=='GE0001')
        assert entry.findtext('beschreibung')==DESCRIPTION


def test_interior_warning_stroke_does_not_select_letter_badge_mode():
    params={}
    assert not apply_semantic_badge_description_rules(desc=DESCRIPTION,params=params)
    assert params.get('mode')!='semantic_badge'
